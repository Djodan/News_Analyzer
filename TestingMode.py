"""
TestingMode.py
Logic for testing mode when enabled in Globals.py
"""

import Globals
from Functions import enqueue_command


def handle_testing_mode(client_id, stats):
    """
    Handle testing mode logic for a client.
    
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
    
    # On first reply, open a BUY position
    if replies == 1:
        enqueue_command(
            client_id,
            1,  # State 1 = OPEN BUY
            {
                "symbol": "XAUUSD",
                "volume": 0.01,
                "comment": "TESTING POSITION",
                "tpPips": 10000,
                "slPips": 10000
            }
        )
        return True
    
    return False
