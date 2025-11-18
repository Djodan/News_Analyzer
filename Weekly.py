"""
Weekly.py
Simple weekly trading algorithm.
Opens trades on Sunday at a specific time, or anytime if liveMode=False.
Monitors 1% weekly profit target and closes all positions when reached.
"""

import Globals
from Functions import enqueue_command, checkTime, get_client_open
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
    
    Logic:
    1. Opens 6 positions on Sunday 6pm (market open) - one-time per week
    2. Monitors for 1% weekly profit target
    3. Closes all positions when target reached
    4. Individual positions can also close via TP/SL
    
    Args:
        client_id: The MT5 client ID
        stats: Dictionary containing client statistics including 'replies' count
        
    Returns:
        bool: True if a command was injected, False otherwise
    """
    # PRIORITY 1: Check if weekly goal has been reached
    if Globals.systemWeeklyGoalReached:
        # Check if there are open positions that need to be closed
        open_positions = get_client_open(client_id)
        
        if open_positions and len(open_positions) > 0:
            # Close all open positions
            if stats.get('replies', 0) % 10 == 0:  # Print every 10th request
                print(f"\n[WEEKLY GOAL REACHED] Closing {len(open_positions)} open position(s)")
                print(f"Target: ${Globals.systemEquityTarget:,.2f} | Current: ${Globals.systemEquity:,.2f}")
            
            # Send close command for each open position
            for pos in open_positions:
                symbol = pos.get('symbol', 'Unknown')
                ticket = pos.get('ticket', 0)
                
                # Enqueue close command (state=3)
                enqueue_command(
                    client_id=client_id,
                    state=3,  # CLOSE command
                    payload={
                        "symbol": symbol,
                        "ticket": ticket,
                        "comment": "Weekly goal reached"
                    }
                )
            
            return True  # Command was injected
        else:
            # No positions to close, just wait
            if stats.get('replies', 0) % 30 == 0:  # Print every 30th request to avoid spam
                print(f"\n[WEEKLY GOAL REACHED] Trading stopped - Target: ${Globals.systemEquityTarget:,.2f} | Current: ${Globals.systemEquity:,.2f}")
            return False
    
    # PRIORITY 2: Open positions on Sunday 6pm (only on first reply)
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
    
    # Open trades using Weekly-specific configuration
    symbols_config = getattr(Globals, "symbolsToTradeWeekly", {})
    
    if not symbols_config:
        return False
    
    injected_any = False
    for symbol, config in symbols_config.items():
        manual_pos = config.get("manual_position", "X")
        
        if manual_pos == "BUY":
            state = 1
        elif manual_pos == "SELL":
            state = 2
        else:
            continue
        
        # Apply lot multiplier based on account tier
        volume = config["lot"]
        if Globals.lot_multiplier != 1.0:
            volume = volume * Globals.lot_multiplier
            volume = round(volume, 2)  # Round to 2 decimals for MT5
        
        enqueue_command(
            client_id,
            state,
            {
                "symbol": config["symbol"],
                "volume": volume,
                "comment": f"WEEKLY {symbol}",
                "tpPips": config["TP"],
                "slPips": config["SL"]
            }
        )
        injected_any = True
    
    return injected_any
