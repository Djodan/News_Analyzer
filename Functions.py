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
                return {"ok": True, "cmdId": cmd_id}
    return {"ok": False, "error": "cmd_not_found", "cmdId": cmd_id}


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
