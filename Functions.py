#!/usr/bin/env python3
"""
Shared utilities and state for the News Analyzer Python server.
Keeps per-client (id) open positions and closed-online snapshots.
"""
from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, UTC
from typing import Any, Dict, List, Tuple, Optional
import uuid
import time as _time
import pytz

LOG_FILE = "received_log.jsonl"

# In-memory stores keyed by client id (string)
_LOCK = threading.Lock()
_CLIENT_OPEN: Dict[str, List[dict]] = {}
_CLIENT_CLOSED_ONLINE: Dict[str, List[dict]] = {}
_CLIENT_COMMANDS: Dict[str, List[dict]] = {}
_CLIENT_STATS: Dict[str, Dict[str, int]] = {}  # { id: { replies: int, last_action: int } }
_CLIENT_MODE: Dict[str, str] = {}  # { id: mode }
_CLIENT_LAST_SEEN: Dict[str, float] = {}  # { id: epoch_seconds }


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def append_log(entry: dict) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[WARN {now_iso()}] Failed to write log: {exc}")


def record_client_snapshot(client_id: str, open_list: List[dict], closed_online: List[dict]) -> None:
    # Replace snapshot per incoming payload to reflect current EA state
    with _LOCK:
        _CLIENT_OPEN[client_id] = deepcopy(open_list) if open_list is not None else []
        _CLIENT_CLOSED_ONLINE[client_id] = deepcopy(closed_online) if closed_online is not None else []
    _CLIENT_LAST_SEEN[client_id] = _time.time()


def ingest_payload(data: dict) -> Tuple[dict, dict]:
    """
    Process an incoming EA payload: update per-client stores and build a small echo summary.
    Returns: (summary_dict, identity_dict)
    """
    import Globals
    
    client_id = str(data.get("id")) if data.get("id") is not None else "unknown"
    mode = data.get("mode")
    open_list = data.get("open", [])
    closed_offline = data.get("closed_offline", [])
    closed_online = data.get("closed_online", [])
    symbols_currently_open = data.get("symbolsCurrentlyOpen", [])

    # Persist full payload to JSONL with server timestamp
    append_log({"ts": now_iso(), **data})

    # Update in-memory per-client snapshots
    record_client_snapshot(client_id, open_list, closed_online)
    # Store/refresh client mode label for logging
    with _LOCK:
        _CLIENT_MODE[client_id] = str(mode) if mode is not None else ""
    
    # Update global symbolsCurrentlyOpen in Globals
    Globals.symbolsCurrentlyOpen = symbols_currently_open

    summary = {
        "open": len(open_list),
        "closed_offline": len(closed_offline),
        "closed_online": len(closed_online),
    }
    identity = {"id": client_id, "mode": mode}
    return summary, identity


def get_client_open(client_id: str) -> List[dict]:
    with _LOCK:
        return deepcopy(_CLIENT_OPEN.get(str(client_id), []))


def get_client_closed_online(client_id: str) -> List[dict]:
    with _LOCK:
        return deepcopy(_CLIENT_CLOSED_ONLINE.get(str(client_id), []))


def list_clients() -> List[str]:
    with _LOCK:
        # Union keys across both maps in case one side hasn't reported yet
        base = set(_CLIENT_OPEN.keys()) | set(_CLIENT_CLOSED_ONLINE.keys())
        return sorted(base)


def get_client_mode(client_id: str) -> str:
    with _LOCK:
        return _CLIENT_MODE.get(str(client_id), "")


# ---------------------- Command queue (server -> EA) ----------------------

def enqueue_command(client_id: str, state: int, payload: Optional[dict] = None) -> dict:
    """Add a command for a specific client id. Returns the stored command."""
    cmd = {
        "cmdId": str(uuid.uuid4()),
        "id": str(client_id),
        "state": int(state),  # 0..3 per contract
        "payload": payload or {},
        "status": "queued",  # queued|sent|ack
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }
    with _LOCK:
        _CLIENT_COMMANDS.setdefault(str(client_id), []).append(cmd)
    return cmd


def get_next_command(client_id: str) -> dict:
    """Return the next pending command for the client without losing it until acked.
    If none pending, return a no-op state=0.
    """
    with _LOCK:
        queue = _CLIENT_COMMANDS.get(str(client_id), [])
        for cmd in queue:
            if cmd.get("status") != "ack":
                # mark as sent (first delivery)
                if cmd.get("status") == "queued":
                    cmd["status"] = "sent"
                    cmd["updatedAt"] = now_iso()
                # Build the precise message for EA
                state = int(cmd.get("state", 0))
                msg = {"id": str(client_id), "state": state, "cmdId": cmd["cmdId"]}
                payload = cmd.get("payload") or {}
                # shape by state
                if state == 1:  # Open BUY
                    # expected: symbol, volume, optional comment and SL/TP (absolute or pip distances)
                    msg.update({
                        "symbol": payload.get("symbol"),
                        "volume": payload.get("volume"),
                        "comment": payload.get("comment", ""),
                    })
                    # propagate optional SL/TP fields
                    if "sl" in payload: msg["sl"] = payload.get("sl")
                    if "tp" in payload: msg["tp"] = payload.get("tp")
                    if "slPips" in payload: msg["slPips"] = payload.get("slPips")
                    if "tpPips" in payload: msg["tpPips"] = payload.get("tpPips")
                elif state == 2:  # Open SELL
                    msg.update({
                        "symbol": payload.get("symbol"),
                        "volume": payload.get("volume"),
                        "comment": payload.get("comment", ""),
                    })
                    # propagate optional SL/TP fields
                    if "sl" in payload: msg["sl"] = payload.get("sl")
                    if "tp" in payload: msg["tp"] = payload.get("tp")
                    if "slPips" in payload: msg["slPips"] = payload.get("slPips")
                    if "tpPips" in payload: msg["tpPips"] = payload.get("tpPips")
                elif state == 3:  # Close trade
                    # expected: ticket or symbol/volume
                    msg.update({
                        "ticket": payload.get("ticket"),
                        "symbol": payload.get("symbol"),
                        "volume": payload.get("volume"),
                        "type": payload.get("type"),  # optional: 0 buy, 1 sell
                    })
                # state 0: do nothing
                return msg
    # No pending command
    return {"id": str(client_id), "state": 0}


def ack_command(client_id: str, cmd_id: str, success: bool, details: Optional[dict] = None) -> dict:
    """Mark a command as acknowledged and store result details."""
    with _LOCK:
        queue = _CLIENT_COMMANDS.get(str(client_id), [])
        for cmd in queue:
            if cmd.get("cmdId") == cmd_id:
                cmd["status"] = "ack"
                cmd["updatedAt"] = now_iso()
                cmd["result"] = {"success": bool(success), **(details or {})}
                
                # Update Globals._Trades_ status to "executed" if successful
                if success:
                    import Globals
                    symbol = cmd.get("payload", {}).get("symbol")
                    if symbol:
                        # Find the trade in _Trades_ by matching symbol
                        for pair_name, trade in Globals._Trades_.items():
                            if trade.get("symbol") == symbol and trade.get("status") == "queued":
                                trade["status"] = "executed"
                                trade["updatedAt"] = now_iso()
                                break
                
                return {"ok": True, "cmdId": cmd_id}
    return {"ok": False, "error": "cmd_not_found", "cmdId": cmd_id}


def record_trade_outcome(symbol: str, outcome: str) -> dict:
    """
    Record when a trade hits TP or SL.
    Updates NID_TP or NID_SL counters in _Currencies_.
    
    Args:
        symbol: The trading pair (e.g., "GBPAUD")
        outcome: Either "TP" or "SL"
        
    Returns:
        dict: Status of the update
    """
    import Globals
    
    # Find the trade in _Trades_
    if symbol not in Globals._Trades_:
        return {"ok": False, "error": "trade_not_found", "symbol": symbol}
    
    trade = Globals._Trades_[symbol]
    nid = trade.get("NID")
    
    if nid is None:
        return {"ok": False, "error": "no_nid", "symbol": symbol}
    
    # Update trade status
    trade["status"] = outcome
    trade["updatedAt"] = now_iso()
    
    # Find the event with this NID and increment counter
    for event_key, event_data in Globals._Currencies_.items():
        if event_data.get('NID') == nid:
            if outcome == "TP":
                event_data['NID_TP'] = event_data.get('NID_TP', 0) + 1
                print(f"[NID_{nid}] TP hit! Total TPs: {event_data['NID_TP']}")
            elif outcome == "SL":
                event_data['NID_SL'] = event_data.get('NID_SL', 0) + 1
                print(f"[NID_{nid}] SL hit! Total SLs: {event_data['NID_SL']}")
            
            return {"ok": True, "symbol": symbol, "NID": nid, "outcome": outcome}
    
    return {"ok": False, "error": "event_not_found", "symbol": symbol, "NID": nid}


def get_command_queue(client_id: str) -> List[dict]:
    with _LOCK:
        return deepcopy(_CLIENT_COMMANDS.get(str(client_id), []))


def record_command_delivery(client_id: str, state: int) -> Dict[str, int]:
    with _LOCK:
        stats = _CLIENT_STATS.setdefault(str(client_id), {"replies": 0, "last_action": 0})
        stats["replies"] += 1
        stats["last_action"] = int(state)
        return deepcopy(stats)


def get_client_stats(client_id: str) -> Dict[str, int]:
    with _LOCK:
        return deepcopy(_CLIENT_STATS.get(str(client_id), {"replies": 0, "last_action": 0}))


def get_client_last_seen(client_id: str) -> float:
    with _LOCK:
        return float(_CLIENT_LAST_SEEN.get(str(client_id), 0.0))


def is_client_online(client_id: str, timeout_seconds: int = 10) -> bool:
    try:
        last = get_client_last_seen(client_id)
        if last <= 0:
            return False
        return (_time.time() - last) <= timeout_seconds
    except Exception:
        return False


def process_ack_response(client_id: str, cmd_id: str, success: bool, details: Optional[dict] = None) -> dict:
    """
    Process ACK from EA and format response with trade details for logging.
    Returns a dict with formatted trade information for logging.
    """
    result = ack_command(client_id, cmd_id, success, details)
    
    # Extract trade details for logging
    paid = None
    typestr = None
    vol = None
    tp = None
    sl = None
    sym = None
    
    if isinstance(details, dict):
        paid = details.get("retcode")
        typestr = details.get("type")
        vol = details.get("volume")
        tp = details.get("tp")
        sl = details.get("sl")
        sym = details.get("symbol")
        # paid price if present
        try:
            price_paid = details.get("paid")
            if price_paid is not None:
                paid = price_paid
        except Exception:
            pass
    
    return {
        "result": result,
        "trade_info": {
            "client_id": client_id,
            "cmd_id": cmd_id,
            "success": success,
            "symbol": sym,
            "type": typestr,
            "volume": vol,
            "price": paid,
            "tp": tp,
            "sl": sl
        }
    }


def checkTime() -> bool:
    """
    Check if current time is within trading hours based on Globals settings.
    Updates Globals.timeToTrade and returns the value.
    If liveMode is True, always returns True (bypasses time restrictions).
    
    Returns:
        bool: True if within trading hours or if liveMode is True, False otherwise
    """
    import Globals
    
    # Bypass time check if in live mode
    live_mode = getattr(Globals, "liveMode", False)
    if live_mode:
        Globals.timeToTrade = True
        return True
    
    time_type = getattr(Globals, "timeType", "MT5")
    time_start = getattr(Globals, "timeStart", 0)
    time_end = getattr(Globals, "timeEnd", 23)
    
    # Get current time based on timeType
    if time_type == "NY":
        # New York timezone
        tz = pytz.timezone('America/New_York')
        current_time = datetime.now(tz)
    else:
        # MT5 (EET - Eastern European Time, UTC+2/+3 with DST)
        tz = pytz.timezone('Europe/Helsinki')  # MT5 server time
        current_time = datetime.now(tz)
    
    current_hour = current_time.hour
    
    # Check if current hour is within trading range
    if time_start <= time_end:
        # Normal range (e.g., 18 to 20)
        in_range = time_start <= current_hour < time_end
    else:
        # Overnight range (e.g., 22 to 2)
        in_range = current_hour >= time_start or current_hour < time_end
    
    # Update global variable
    Globals.timeToTrade = in_range
    
    return in_range


def generate_tid(nid: int) -> str:
    """
    Generate a unique Trade ID (TID) for a position.
    Format: TID_{NID}_{position_number}
    
    Args:
        nid: News ID that triggered this trade
        
    Returns:
        str: Unique Trade ID
    """
    import Globals
    
    # Get or initialize the counter for this NID
    if nid not in Globals._Trade_ID_Counter_:
        Globals._Trade_ID_Counter_[nid] = 0
    
    # Increment and generate TID
    Globals._Trade_ID_Counter_[nid] += 1
    position_number = Globals._Trade_ID_Counter_[nid]
    
    return f"TID_{nid}_{position_number}"


def create_trade(client_id: str, symbol: str, action: str, volume: float, 
                 tp: float, sl: float, comment: str, nid: int) -> dict:
    """
    Create a new trade entry with a unique TID.
    
    Args:
        client_id: MT5 client ID
        symbol: Trading pair
        action: "BUY" or "SELL"
        volume: Lot size
        tp: Take profit in pips
        sl: Stop loss in pips
        comment: Trade comment
        nid: News ID that triggered this trade
        
    Returns:
        dict: The created trade with TID
    """
    import Globals
    
    tid = generate_tid(nid)
    
    trade = {
        "TID": tid,
        "client_id": client_id,
        "symbol": symbol,
        "action": action,
        "volume": volume,
        "tp": tp,
        "sl": sl,
        "comment": comment,
        "status": "queued",
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
        "NID": nid,
        "ticket": None
    }
    
    Globals._Trades_[tid] = trade
    print(f"[Trade] Created {tid} for {symbol} {action} {volume} lots (NID: {nid})")
    
    return trade


def update_trade_ticket(tid: str, ticket: int) -> bool:
    """
    Update a trade with its MT5 ticket number after execution.
    
    Args:
        tid: Trade ID
        ticket: MT5 ticket number
        
    Returns:
        bool: True if updated successfully
    """
    import Globals
    
    if tid not in Globals._Trades_:
        return False
    
    Globals._Trades_[tid]["ticket"] = ticket
    Globals._Trades_[tid]["status"] = "executed"
    Globals._Trades_[tid]["updatedAt"] = now_iso()
    
    print(f"[Trade] {tid} executed with ticket {ticket}")
    return True


def get_trade_by_ticket(ticket: int) -> Optional[dict]:
    """
    Find a trade by its MT5 ticket number.
    
    Args:
        ticket: MT5 ticket number
        
    Returns:
        dict or None: Trade data if found
    """
    import Globals
    
    for tid, trade in Globals._Trades_.items():
        if trade.get("ticket") == ticket:
            return trade
    
    return None


def get_trade_by_tid(tid: str) -> Optional[dict]:
    """
    Get a trade by its TID.
    
    Args:
        tid: Trade ID
        
    Returns:
        dict or None: Trade data if found
    """
    import Globals
    
    return Globals._Trades_.get(tid)


def close_trade_by_tid(client_id: str, tid: str) -> Optional[dict]:
    """
    Close a specific trade by its TID.
    
    Args:
        client_id: MT5 client ID
        tid: Trade ID
        
    Returns:
        dict or None: Close command if successful
    """
    import Globals
    
    trade = get_trade_by_tid(tid)
    if not trade:
        print(f"[Trade] TID {tid} not found")
        return None
    
    ticket = trade.get("ticket")
    if not ticket:
        print(f"[Trade] TID {tid} has no ticket (not executed yet)")
        return None
    
    # Create close command
    payload = {
        "ticket": ticket,
        "symbol": trade["symbol"]
    }
    
    cmd = enqueue_command(client_id, 3, payload)  # state 3 = CLOSE
    
    print(f"[Trade] Closing {tid} (Ticket: {ticket})")
    
    return cmd


def update_trade_outcome_by_ticket(ticket: int, outcome: str) -> dict:
    """
    Update trade status when TP or SL is hit.
    Uses ticket number to find the trade.
    
    Args:
        ticket: MT5 ticket number
        outcome: "TP" or "SL"
        
    Returns:
        dict: Status of the update
    """
    import Globals
    
    trade = get_trade_by_ticket(ticket)
    if not trade:
        return {"ok": False, "error": "trade_not_found", "ticket": ticket}
    
    tid = trade["TID"]
    nid = trade["NID"]
    symbol = trade["symbol"]
    
    # Update trade status
    trade["status"] = outcome
    trade["updatedAt"] = now_iso()
    
    # Find the event with this NID and increment counter
    for event_key, event_data in Globals._Currencies_.items():
        if event_data.get('NID') == nid:
            if outcome == "TP":
                event_data['NID_TP'] = event_data.get('NID_TP', 0) + 1
                print(f"[{tid}] TP hit! NID_{nid} Total TPs: {event_data['NID_TP']}")
            elif outcome == "SL":
                event_data['NID_SL'] = event_data.get('NID_SL', 0) + 1
                print(f"[{tid}] SL hit! NID_{nid} Total SLs: {event_data['NID_SL']}")
            
            return {"ok": True, "TID": tid, "ticket": ticket, "symbol": symbol, "NID": nid, "outcome": outcome}
    
    return {"ok": False, "error": "event_not_found", "TID": tid, "ticket": ticket, "NID": nid}


# ========== RISK MANAGEMENT FUNCTIONS ==========

def extract_currencies(symbol: str) -> List[str]:
    """
    Extract individual currencies from a trading symbol.
    
    Args:
        symbol: Trading pair symbol (e.g., "GBPJPY", "XAUUSD", "BITCOIN")
        
    Returns:
        list: List of currency codes found in the symbol
        
    Examples:
        extract_currencies("GBPJPY") → ["GBP", "JPY"]
        extract_currencies("XAUUSD") → ["XAU", "USD"]
        extract_currencies("EURUSD") → ["EUR", "USD"]
        extract_currencies("BITCOIN") → ["BTC"]
    """
    import Globals
    
    currencies = []
    known_currencies = ["XAU", "EUR", "USD", "JPY", "CHF", "NZD", "CAD", "GBP", "AUD", "BTC"]
    
    # Special handling for single-currency symbols
    if "BITCOIN" in symbol.upper():
        return ["BTC"]
    if "ETHEREUM" in symbol.upper():
        return ["BTC"]  # Treat crypto similarly
    if "LITECOIN" in symbol.upper():
        return ["BTC"]
    if "DOGECOIN" in symbol.upper():
        return ["BTC"]
    
    # Extract currencies by checking if known currency codes appear in symbol
    for currency in known_currencies:
        if currency in symbol.upper():
            currencies.append(currency)
    
    return currencies


def update_currency_count(symbol: str, operation: str) -> None:
    """
    Update the _CurrencyCount_ dictionary when opening or closing a trade.
    
    Args:
        symbol: Trading pair symbol (e.g., "GBPJPY")
        operation: "add" to increment counts, "remove" to decrement counts
        
    Examples:
        update_currency_count("GBPJPY", "add")    # GBP +1, JPY +1
        update_currency_count("EURUSD", "remove") # EUR -1, USD -1
    """
    import Globals
    
    currencies = extract_currencies(symbol)
    
    for currency in currencies:
        if currency in Globals._CurrencyCount_:
            if operation == "add":
                Globals._CurrencyCount_[currency] += 1
                # Removed verbose logging - currency counts shown after position opens
            elif operation == "remove":
                Globals._CurrencyCount_[currency] = max(0, Globals._CurrencyCount_[currency] - 1)
                # Removed verbose logging - currency counts shown after position closes


def can_open_trade(symbol: str) -> bool:
    """
    Check if a trade can be opened based on risk management filters.
    
    This is the main validation function that all algorithms should call before opening a trade.
    Checks:
    1. news_filter_maxTrades: Maximum total open trades (0 = no limit)
    2. news_filter_maxTradePerCurrency: Maximum trades per currency (0 = no limit)
    
    Args:
        symbol: Trading pair symbol (e.g., "GBPJPY")
        
    Returns:
        bool: True if trade can be opened, False if rejected by filters
        
    Examples:
        if can_open_trade("GBPJPY"):
            # Open the trade
        else:
            # Trade rejected by filters
    """
    import Globals
    
    # Check 1: Maximum total trades
    if Globals.news_filter_maxTrades > 0:
        current_total_trades = len(Globals._Trades_)
        if current_total_trades >= Globals.news_filter_maxTrades:
            # Removed verbose logging - rejection shown in calling function
            return False
    
    # Check 2: Maximum trades per currency
    if Globals.news_filter_maxTradePerCurrency > 0:
        currencies = extract_currencies(symbol)
        
        for currency in currencies:
            current_count = Globals._CurrencyCount_.get(currency, 0)
            
            # If opening this trade would exceed the limit for any currency, reject
            if current_count >= Globals.news_filter_maxTradePerCurrency:
                # Removed verbose logging - rejection shown in calling function
                return False
    
    # All checks passed
    return True


def find_available_pair_for_currency(currency: str) -> Optional[str]:
    """
    Find an available trading pair containing the specified currency
    that won't be rejected by risk management filters.
    
    This function is used as a fallback when:
    1. news_filter_findAvailablePair = True
    2. system_news_event is set to a currency
    3. The original affected pair was rejected by filters
    
    Search hierarchy:
    1. First searches symbolsToTrade for available pairs
    2. If news_filter_findAllPairs = True and no pair found, expands to all _Symbols_
    
    Args:
        currency: Currency code (e.g., "EUR", "USD", "GBP")
        
    Returns:
        str: Symbol name if valid pair found, None otherwise
        
    Examples:
        # USD at limit, EUR available in symbolsToTrade
        find_available_pair_for_currency("EUR") → "EURCHF"
        
        # No EUR pairs in symbolsToTrade, but EURJPY in _Symbols_
        find_available_pair_for_currency("EUR") → "EURJPY" (if news_filter_findAllPairs=True)
        
        # CHF at limit, no alternatives anywhere
        find_available_pair_for_currency("CHF") → None
    """
    import Globals
    
    symbols_config = getattr(Globals, "_Symbols_", {})
    symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
    find_all_pairs = getattr(Globals, "news_filter_findAllPairs", False)
    
    print(f"[FIND PAIR] Searching for alternative pair containing {currency}...")
    
    # STEP 1: Search in symbolsToTrade first (priority)
    print(f"[FIND PAIR] Step 1: Searching in symbolsToTrade ({len(symbols_to_trade)} symbols)...")
    
    for symbol in symbols_to_trade:
        if symbol in symbols_config:
            # Check if this symbol contains the target currency
            currencies = extract_currencies(symbol)
            
            if currency in currencies:
                # Test if we can open this pair
                if can_open_trade(symbol):
                    print(f"[FIND PAIR] ✅ Found in symbolsToTrade: {symbol}")
                    return symbol
                else:
                    print(f"[FIND PAIR] ❌ {symbol} (symbolsToTrade) rejected by filters")
    
    # STEP 2: If not found and news_filter_findAllPairs enabled, search all _Symbols_
    if find_all_pairs:
        print(f"[FIND PAIR] Step 2: Expanding search to all _Symbols_ ({len(symbols_config)} symbols)...")
        
        for symbol, config in symbols_config.items():
            # Skip symbols already checked in symbolsToTrade
            if symbol in symbols_to_trade:
                continue
            
            # Check if this symbol contains the target currency
            currencies = extract_currencies(symbol)
            
            if currency in currencies:
                # Test if we can open this pair
                if can_open_trade(symbol):
                    print(f"[FIND PAIR] ✅ Found in _Symbols_: {symbol}")
                    return symbol
                else:
                    print(f"[FIND PAIR] ❌ {symbol} (_Symbols_) rejected by filters")
    else:
        print(f"[FIND PAIR] Step 2: Skipped (news_filter_findAllPairs = False)")
    
    print(f"[FIND PAIR] ⚠️  No available pair found for {currency}")
    return None



