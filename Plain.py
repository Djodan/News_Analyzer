"""
Plain.py
Empty mode for communication and testing purposes.
No trading algorithm - just maintains connection with clients.
"""


def handle_plain(client_id, stats):
    """
    Plain mode handler - does nothing.
    Used for communication testing and debugging without any trading logic.
    
    Args:
        client_id: The MT5 client ID
        stats: Dictionary containing client statistics including 'replies' count
        
    Returns:
        bool: Always returns False (no commands injected)
    """
    # No trading logic - just maintain connection
    return False
