"""
TestingMode.py
Logic for testing mode when enabled in Globals.py
"""

import Globals
from Functions import enqueue_command


def handle_testing_mode(client_id, stats):
    """
    Handle testing mode logic for a client.
    Opens positions for all symbols in symbolsToTrade using their configuration from _Symbols_.
    
    Args:
        client_id: The MT5 client ID
        stats: Dictionary containing client statistics including 'replies' count
        
    Returns:
        bool: True if a command was injected, False otherwise
    """
    if not getattr(Globals, "TestingMode", False):
        return False
    
    # Get the reply count
    try:
        replies = int(stats.get("replies", 0))
    except Exception:
        replies = 0
    
    # On first reply, open positions for all symbols in symbolsToTrade
    if replies == 1:
        symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
        symbols_config = getattr(Globals, "_Symbols_", {})
        
        injected_any = False
        for symbol in symbols_to_trade:
            if symbol in symbols_config:
                config = symbols_config[symbol]
                
                # Determine position type based on manual_position
                manual_pos = config.get("manual_position", "X")
                if manual_pos == "BUY":
                    state = 1  # OPEN BUY
                elif manual_pos == "SELL":
                    state = 2  # OPEN SELL
                else:
                    # If manual_position is "X" or anything else, default to BUY for testing
                    state = 1
                
                enqueue_command(
                    client_id,
                    state,
                    {
                        "symbol": config.get("symbol"),
                        "volume": config.get("lot"),
                        "comment": f"TESTING {symbol}",
                        "tpPips": config.get("TP"),
                        "slPips": config.get("SL")
                    }
                )
                injected_any = True
        
        return injected_any
    
    return False
