"""
News.py
News-based trading algorithm.
Opens trades based on news events and market conditions.
"""

import Globals
from Functions import enqueue_command, checkTime


def handle_news(client_id, stats):
    """
    Handle news trading mode logic for a client.
    Opens positions based on news events and analysis.
    
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
    
    # If liveMode is True, check time restrictions
    if live_mode:
        checkTime()
        time_to_trade = getattr(Globals, "timeToTrade", False)
        
        if not time_to_trade:
            return False
    
    # Open trades based on news analysis
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
                "comment": f"NEWS {symbol}",
                "tpPips": config["TP"],
                "slPips": config["SL"]
            }
        )
        injected_any = True
    
    return injected_any
