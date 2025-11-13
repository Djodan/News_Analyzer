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
import csv
import os
import StrategyPresets

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


def write_trade_to_csv(trade_data):
    """
    Append a closed trade to trades_log.csv for structured analysis.
    Expected fields: tid, ticket, symbol, type, volume, entry_price, exit_price, 
                     entry_time, exit_time, profit, mae, mfe, close_reason, strategy
    """
    csv_file = os.path.join("_dictionaries", "trades_log.csv")
    fieldnames = [
        'tid', 'ticket', 'symbol', 'type', 'volume', 
        'entry_price', 'exit_price', 'entry_time', 'exit_time',
        'profit_usd', 'pips', 'mae_pips', 'mfe_pips', 'close_reason', 'strategy'
    ]
    
    try:
        # Ensure _dictionaries folder exists
        os.makedirs("_dictionaries", exist_ok=True)
        
        # Check if file exists and has content
        file_exists = os.path.isfile(csv_file)
        needs_header = not file_exists or os.path.getsize(csv_file) == 0
        
        # Calculate pips (5-digit broker: 0.0001 for EUR/USD, 0.01 for JPY pairs)
        symbol = trade_data.get('symbol', '')
        entry_price = float(trade_data.get('entry_price', 0))
        exit_price = float(trade_data.get('exit_price', 0))
        trade_type = trade_data.get('type', 'BUY')
        
        # Determine pip multiplier based on symbol type
        # BITCOIN, gold (XAU), and other exotics use 1.0 (points = pips)
        # JPY pairs use 100 (2-decimal)
        # Standard pairs use 10000 (5-decimal like 1.12345)
        if 'BITCOIN' in symbol or 'XAU' in symbol or 'XAG' in symbol:
            pip_multiplier = 1.0  # Points = pips for Bitcoin/metals
        elif 'JPY' in symbol:
            pip_multiplier = 100  # 2-decimal JPY pairs
        else:
            pip_multiplier = 10000  # 5-decimal standard pairs
        
        # Calculate pips based on trade direction
        if trade_type == 'BUY':
            pips = (exit_price - entry_price) * pip_multiplier
        else:  # SELL
            pips = (entry_price - exit_price) * pip_multiplier
        
        # Get MAE/MFE from trade data
        mae = float(trade_data.get('mae', 0))
        mfe = float(trade_data.get('mfe', 0))
        
        # Prepare row data
        row = {
            'tid': trade_data.get('tid', ''),
            'ticket': trade_data.get('ticket', ''),
            'symbol': symbol,
            'type': trade_type,
            'volume': trade_data.get('volume', ''),
            'entry_price': f"{entry_price:.5f}",
            'exit_price': f"{exit_price:.5f}",
            'entry_time': trade_data.get('entry_time', ''),
            'exit_time': trade_data.get('exit_time', ''),
            'profit_usd': f"{float(trade_data.get('profit', 0)):.2f}",
            'pips': f"{pips:.1f}",
            'mae_pips': f"{mae:.1f}",
            'mfe_pips': f"{mfe:.1f}",
            'close_reason': trade_data.get('close_reason', 'Unknown'),
            'strategy': trade_data.get('strategy', 'Unknown')
        }
        
        # Write to CSV
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if needs_header:
                writer.writeheader()
            writer.writerow(row)
            
        print(f"  ✅ Trade logged to CSV: {symbol} {trade_type} Ticket={row['ticket']} Pips={row['pips']} MAE={row['mae_pips']} MFE={row['mfe_pips']} Profit={row['profit_usd']}")
        
    except Exception as exc:
        print(f"[WARN {now_iso()}] Failed to write trade to CSV: {exc}")


def record_client_snapshot(client_id: str, open_list: List[dict], closed_online: List[dict]) -> None:
    # Replace snapshot per incoming payload to reflect current EA state
    with _LOCK:
        _CLIENT_OPEN[client_id] = deepcopy(open_list) if open_list is not None else []
        _CLIENT_CLOSED_ONLINE[client_id] = deepcopy(closed_online) if closed_online is not None else []
    _CLIENT_LAST_SEEN[client_id] = _time.time()


def check_and_apply_strategy(strategy_str: str) -> None:
    """
    Check if incoming strategy differs from current Globals.news_strategy.
    If different, apply the new strategy preset.
    
    Args:
        strategy_str: Strategy string like "S0", "S1", "S2", "S3", "S4", "S5"
    """
    import Globals
    
    if not strategy_str or strategy_str == "Unknown":
        return
    
    # Extract strategy ID from string (e.g., "S3" -> 3)
    try:
        if strategy_str.startswith("S"):
            strategy_id = int(strategy_str[1:])
        else:
            strategy_id = int(strategy_str)
    except (ValueError, IndexError):
        print(f"[WARN] Invalid strategy format: {strategy_str}")
        return
    
    # Validate strategy ID (0-5)
    if strategy_id not in [0, 1, 2, 3, 4, 5]:
        print(f"[WARN] Invalid strategy ID: {strategy_id} (must be 0-5)")
        return
    
    # Check if strategy changed
    current_strategy = Globals.news_strategy
    if strategy_id != current_strategy:
        print(f"\n{'='*60}")
        print(f"🔄 STRATEGY CHANGE DETECTED: S{current_strategy} → S{strategy_id}")
        print(f"{'='*60}")
        
        # Apply new strategy preset
        success = StrategyPresets.apply_strategy_preset(strategy_id, verbose=True)
        
        if success:
            print(f"{'='*60}\n")
        else:
            print(f"[ERROR] Failed to apply strategy preset S{strategy_id}")
            print(f"{'='*60}\n")


def ingest_payload(data: dict) -> Tuple[dict, dict]:
    """
    Process an incoming EA payload: update per-client stores and build a small echo summary.
    Returns: (summary_dict, identity_dict)
    """
    import Globals
    
    client_id = str(data.get("id")) if data.get("id") is not None else "unknown"
    mode = data.get("mode")
    packet_type = data.get("packetType", "A")  # Default to A if not specified
    open_list = data.get("open", [])
    closed_offline = data.get("closed_offline", [])
    closed_online = data.get("closed_online", [])
    symbols_currently_open = data.get("symbolsCurrentlyOpen", [])
    
    # Check and apply strategy from main payload (applies to all packet types)
    strategy_str = data.get("strategy", "Unknown")
    if strategy_str and strategy_str != "Unknown":
        check_and_apply_strategy(strategy_str)
    
    # Print packet reception confirmation with FULL DATA (only if not in live mode)
    if not Globals.liveMode:
        print(f"[PACKET-{packet_type}] Received from Client [{client_id}]")
    
    # Show complete packet-specific data
    if packet_type == "A":
        if not Globals.liveMode:
            print(f"  Trade State: {len(open_list)} open, {len(closed_offline)} closed offline, {len(closed_online)} closed online")
            if open_list:
                print("  Open Positions:")
                for pos in open_list:
                    print(f"    Ticket={pos.get('ticket')} {pos.get('symbol')} {pos.get('type')} Vol={pos.get('volume')} Price={pos.get('openPrice')} P&L={pos.get('profit')}")
    elif packet_type == "B":
        balance = data.get("balance", 0)
        equity = data.get("equity", 0)
        if not Globals.liveMode:
            print(f"  Account Info: Balance=${balance:.2f}, Equity=${equity:.2f}")
        
        # Update system balance and equity
        Globals.systemBalance = balance
        Globals.systemEquity = equity
        
        # Calculate and set weekly targets
        set_targets()
    elif packet_type == "C":
        symbols = data.get("symbols", [])
        if not Globals.liveMode:
            print(f"  Symbol Data: {len(symbols)} pairs received")
            print("  ============================================")
            for sym in symbols:
                print(f"    {sym.get('symbol'):8s} | ATR={sym.get('atr'):8.5f} | Spread={sym.get('spread'):5.1f} | Bid={sym.get('bid'):10.5f} | Ask={sym.get('ask'):10.5f}")
            print("  ============================================")
    elif packet_type == "D":
        positions = data.get("positions", [])
        print(f"  Position Analytics: {len(positions)} positions tracked")
        if positions:
            for pos in positions:
                mae = pos.get('mae')  # Changed from 'mae_pips' to 'mae'
                mfe = pos.get('mfe')  # Changed from 'mfe_pips' to 'mfe'
                unrealized = pos.get('unrealizedPnL')  # Changed from 'unrealized_pnl_pips'
                mae_str = f"{mae:.1f}" if mae is not None else "N/A"
                mfe_str = f"{mfe:.1f}" if mfe is not None else "N/A"
                unrealized_str = f"{unrealized:.1f}" if unrealized is not None else "N/A"
                print(f"    {pos.get('symbol')}: Ticket={pos.get('ticket')} | Unrealized={unrealized_str} pips | MAE={mae_str} pips | MFE={mfe_str} pips")
    elif packet_type == "E":
        trade = data.get("trade", {})
        profit = trade.get('profit')
        mae = trade.get('mae')  # Changed from 'mae_pips' to 'mae'
        mfe = trade.get('mfe')  # Changed from 'mfe_pips' to 'mfe'
        duration = trade.get('duration')  # Changed from 'duration_seconds'
        
        profit_str = f"{profit:.2f}" if profit is not None else "N/A"
        mae_str = f"{mae:.1f}" if mae is not None else "N/A"
        mfe_str = f"{mfe:.1f}" if mfe is not None else "N/A"
        duration_str = f"{duration}s" if duration is not None else "N/A"
        
        print(f"  Close Details: {trade.get('symbol')} Ticket={trade.get('ticket')}")
        print(f"    Profit={profit_str} | MAE={mae_str} pips | MFE={mfe_str} pips")
        print(f"    Open={trade.get('openPrice')} | Close={trade.get('closePrice')} | Duration={duration_str}")
        
        # Log trade to CSV for structured analysis
        ticket = trade.get('ticket')
        if ticket:
            # Try to find TID from Globals._Trades_
            trade_record = get_trade_by_ticket(ticket)
            tid = trade_record.get('TID', '') if trade_record else ''
            
            # If no TID found (e.g., TestingMode), generate one from ticket
            if not tid:
                tid = f"T_{ticket}"
            
            # Determine trade type (convert MT5 type to BUY/SELL)
            trade_type_int = trade.get('type', 0)
            trade_type = 'BUY' if trade_type_int == 0 else 'SELL'
            
            # Get strategy from Packet E (passed from EA input)
            strategy = trade.get('strategy', 'Unknown')
            
            # Check if strategy changed and apply new preset if needed
            check_and_apply_strategy(strategy)
            
            # Prepare trade data for CSV (including MAE/MFE)
            csv_trade_data = {
                'tid': tid,
                'ticket': ticket,
                'symbol': trade.get('symbol', ''),
                'type': trade_type,
                'volume': trade.get('volume', 0),
                'entry_price': trade.get('openPrice', 0),
                'exit_price': trade.get('closePrice', 0),
                'entry_time': trade.get('openTime', ''),
                'exit_time': trade.get('closeTime', ''),
                'profit': profit if profit is not None else 0,
                'mae': mae if mae is not None else 0,
                'mfe': mfe if mfe is not None else 0,
                'close_reason': trade.get('close_reason', 'Unknown'),
                'strategy': strategy
            }
            
            write_trade_to_csv(csv_trade_data)

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
    
    # Update currency count ONLY if trade was successful
    if success and sym:
        import Globals
        update_currency_count(sym, "add")
        print(f"  📊 Currency counts: {Globals._CurrencyCount_}")
    
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


def set_targets() -> None:
    """
    Calculate and set weekly goal system targets based on current balance and settings.
    
    Sets the following Globals:
        - systemBaseBalance: Prop firm account tier (5k, 10k, 25k, 50k, 100k, 200k)
        - lot_multiplier: Lot size scaling factor (5k→0.05x, 10k→0.1x, 25k→0.25x, 50k→0.5x, 100k→1.0x, 200k→2.0x)
        - systemStartOfWeekBalance: Starting balance (only if currently 0)
        - systemEquityTarget: Target equity (starting balance + weekly goal based on base tier)
        
    This function should be called when:
        1. Balance/Equity data is received from EA (Packet B)
        2. Weekly reset occurs
        
    Example:
        If systemBalance = 56,843 then systemBaseBalance = 50,000 (within 25% deviation)
        lot_multiplier = 50,000 / 100,000 = 0.5x
        If EURUSD base lot = 0.50, actual lot sent = 0.50 × 0.5 = 0.25 lots
        
        If systemBalance = 104,462 then systemBaseBalance = 100,000
        lot_multiplier = 100,000 / 100,000 = 1.0x (no change)
        
        If systemBalance = 204,000 then systemBaseBalance = 200,000
        lot_multiplier = 200,000 / 100,000 = 2.0x
        If EURUSD base lot = 0.50, actual lot sent = 0.50 × 2.0 = 1.00 lots
    """
    import Globals
    
    # Track if this is the first time setting up targets
    first_time_setup = Globals.systemStartOfWeekBalance == 0.0 and Globals.systemBalance > 0.0
    
    # Determine base balance tier based on current balance with 25% deviation tolerance
    # Example: 104,462 → 100,000 | 56,843 → 50,000
    if Globals.systemBalance > 0.0:
        predefined_tiers = [5000, 10000, 25000, 50000, 100000, 200000]
        
        for tier in predefined_tiers:
            # Calculate 25% deviation range: tier ± 25%
            lower_bound = tier * 0.75  # 25% below
            upper_bound = tier * 1.25  # 25% above
            
            if lower_bound <= Globals.systemBalance <= upper_bound:
                Globals.systemBaseBalance = tier
                break
        else:
            # If no tier matches, use the actual balance as base
            Globals.systemBaseBalance = Globals.systemBalance
        
        # Calculate lot multiplier based on base balance tier
        # Default lot sizes in _Symbols_ are calibrated for 100k accounts
        # 5k → 0.05x, 10k → 0.1x, 25k → 0.25x, 50k → 0.5x, 100k → 1.0x, 200k → 2.0x
        reference_balance = 100000.0
        if Globals.systemBaseBalance > 0:
            Globals.lot_multiplier = Globals.systemBaseBalance / reference_balance
        else:
            Globals.lot_multiplier = 1.0
    
    # Set starting balance only once (when it's 0)
    if first_time_setup:
        Globals.systemStartOfWeekBalance = Globals.systemBalance
    
    # Calculate target equity: starting balance + weekly goal (based on base tier)
    # Example: Starting balance 104,462 with base tier 100,000 and 1.0% goal
    #          Target = 104,462 + (100,000 × 1.0 / 100) = 105,462 (fixed $1,000 goal)
    if Globals.systemStartOfWeekBalance > 0.0 and Globals.systemBaseBalance > 0.0:
        weekly_goal_amount = Globals.systemBaseBalance * (Globals.UserWeeklyGoalPercentage / 100)
        Globals.systemEquityTarget = Globals.systemStartOfWeekBalance + weekly_goal_amount
        
        # Print all variables once during first setup
        if first_time_setup:
            print("=" * 60)
            print("[SET_TARGETS] WEEKLY GOAL SYSTEM INITIALIZED")
            print("=" * 60)
            print(f"systemBalance:             ${Globals.systemBalance:,.2f}")
            print(f"systemEquity:              ${Globals.systemEquity:,.2f}")
            print(f"systemBaseBalance:         ${Globals.systemBaseBalance:,.2f}")
            print(f"lot_multiplier:            {Globals.lot_multiplier:.2f}x (calibrated for 100k = 1.0x)")
            print(f"systemStartOfWeekBalance:  ${Globals.systemStartOfWeekBalance:,.2f}")
            print(f"UserWeeklyGoalPercentage:  {Globals.UserWeeklyGoalPercentage}%")
            print(f"Weekly Goal Amount:        ${weekly_goal_amount:,.2f}")
            print(f"systemEquityTarget:        ${Globals.systemEquityTarget:,.2f}")
            print(f"systemWeeklyGoalReached:   {Globals.systemWeeklyGoalReached}")
            print("=" * 60)
        
        # Check if goal is already reached
        if Globals.systemEquity >= Globals.systemEquityTarget and not Globals.systemWeeklyGoalReached:
            Globals.systemWeeklyGoalReached = True
            print(f"\n{'=' * 60}")
            print(f"[SET_TARGETS] ✓ WEEKLY GOAL REACHED!")
            print(f"{'=' * 60}")
            print(f"Current Equity:   ${Globals.systemEquity:,.2f}")
            print(f"Target Equity:    ${Globals.systemEquityTarget:,.2f}")
            print(f"Profit Made:      ${Globals.systemEquity - Globals.systemStartOfWeekBalance:,.2f}")
            print(f"{'=' * 60}\n")
        elif Globals.systemEquity < Globals.systemEquityTarget and Globals.systemWeeklyGoalReached:
            # Reset if equity drops below target
            Globals.systemWeeklyGoalReached = False
            print(f"[SET_TARGETS] Goal status reset - Equity dropped below target")


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
    Also updates S5 positions_opened counter in _CurrencySentiment_.
    
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
                
                # S5 SCALING: Decrement positions_opened counter when position closes
                if Globals.news_filter_allowScaling and currency in Globals._CurrencySentiment_:
                    sentiment = Globals._CurrencySentiment_[currency]
                    positions_opened = sentiment.get('positions_opened', 0)
                    if positions_opened > 0:
                        Globals._CurrencySentiment_[currency]['positions_opened'] = positions_opened - 1
                        # If all positions closed, reset sentiment tracker
                        if Globals._CurrencySentiment_[currency]['positions_opened'] == 0:
                            # Keep direction and count, just reset positions
                            pass  # Allow re-scaling if more signals arrive


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


def display_idle_screen(client_id: str, open_count: int, closed_count: int):
    """
    Display clean idle screen with next event countdown and position status.
    Clears terminal and shows:
    - Next pending event with countdown
    - Open/Closed position counts
    
    Args:
        client_id: Client identifier
        open_count: Number of open positions
        closed_count: Number of closed positions
    """
    import Globals
    import os
    from datetime import datetime, timezone
    
    # Only show idle screen in live mode
    if not Globals.liveMode:
        return
    
    # Clear terminal (Windows: cls, Unix: clear)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Find next pending event
    next_event = None
    next_event_time = None
    currencies_dict = getattr(Globals, "_Currencies_", {})
    
    now = datetime.now(timezone.utc)
    
    for event_key, event_data in currencies_dict.items():
        event_datetime = event_data.get('datetime')
        if event_datetime and event_datetime > now:
            if next_event is None or event_datetime < next_event_time:
                next_event = event_data
                next_event_time = event_datetime
    
    # Display header
    print("=" * 60)
    print("NEWS ANALYZER - LIVE MODE")
    print("=" * 60)
    
    # Display next event info
    if next_event:
        currency = next_event.get('currency', 'Unknown')
        event_name = next_event.get('event', 'Unknown Event')
        time_until = next_event_time - now
        
        hours = int(time_until.total_seconds() // 3600)
        minutes = int((time_until.total_seconds() % 3600) // 60)
        seconds = int(time_until.total_seconds() % 60)
        
        print(f"\n📰 NEXT EVENT: {currency} - {event_name}")
        print(f"⏰ Time Until Event: {hours:02d}h {minutes:02d}m {seconds:02d}s")
        print(f"🕐 Event Time: {next_event_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        print("\n📰 NEXT EVENT: No upcoming events")
    
    # Display position status
    print(f"\n📊 POSITIONS")
    print(f"   Open: {open_count}")
    print(f"   Closed: {closed_count}")
    
    # Get symbols currently open
    symbols_open = getattr(Globals, "symbolsCurrentlyOpen", [])
    if symbols_open:
        symbols_str = ", ".join(symbols_open)
        print(f"   Symbols: {symbols_str}")
    else:
        print(f"   Symbols: None")
    
    print("=" * 60)



