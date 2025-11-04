"""
Weekly.py
Simple weekly trading algorithm.
Opens trades on Sunday at a specific time, or anytime if liveMode=False.
"""

import Globals
from Functions import enqueue_command, checkTime
from datetime import datetime
import pytz


def is_sunday() -> bool:
    """
    Check if current day is Sunday based on timeType timezone.
    
    Returns:
        bool: True if Sunday, False otherwise
    """
    time_type = getattr(Globals, "timeType", "MT5")
    
    # Get current time based on timeType
    if time_type == "NY":
        tz = pytz.timezone('America/New_York')
    else:
        # MT5 timezone
        tz = pytz.timezone('Europe/Helsinki')
    
    current_time = datetime.now(tz)
    # Sunday is 6 in Python's weekday() (Monday=0, Sunday=6)
    return current_time.weekday() == 6


def handle_weekly(client_id, stats):
    """
    Handle weekly trading mode logic for a client.
    Simple logic: Open trades on Sunday during trading hours.
    If liveMode=False, skip all time constraints and just open trades.
    
    Args:
        client_id: The MT5 client ID
        stats: Dictionary containing client statistics including 'replies' count
        
    Returns:
        bool: True if a command was injected, False otherwise
    """
    # Get the reply count
    try:
        replies = int(stats.get("replies", 0))
    except Exception:
        replies = 0
    
    # Only trade on first reply
    if replies != 1:
        return False
    
    # Get liveMode setting
    live_mode = getattr(Globals, "liveMode", False)
    
    # If liveMode is False, skip all time constraints and just open trades
    if not live_mode:
        should_trade = True
    else:
        # Check if it's Sunday
        is_sunday_today = is_sunday()
        
        if not is_sunday_today:
            return False
        
        # Check time restrictions
        checkTime()
        time_to_trade = getattr(Globals, "timeToTrade", False)
        
        if not time_to_trade:
            return False
        
        should_trade = True
    
    # Open trades
    symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
    symbols_config = getattr(Globals, "_Symbols_", {})
    
    if not symbols_to_trade:
        return False
    
    injected_any = False
    for symbol in symbols_to_trade:
        if symbol not in symbols_config:
            continue
        
        config = symbols_config[symbol]
        manual_pos = config.get("manual_position", "X")
        
        if manual_pos == "BUY":
            state = 1
        elif manual_pos == "SELL":
            state = 2
        else:
            continue
        
        enqueue_command(
            client_id,
            state,
            {
                "symbol": config["symbol"],
                "volume": config["lot"],
                "comment": f"WEEKLY {symbol}",
                "tpPips": config["TP"],
                "slPips": config["SL"]
            }
        )
        injected_any = True
    
    return injected_any
