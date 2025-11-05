"""
TestingMode_Examples.py
Example usage of TestingMode functions for managing multiple positions per symbol.
"""

import TestingMode
import Globals


# Example 1: Check if positions are open
def example_check_positions(client_id):
    """Check what positions are open for a symbol."""
    
    # Check if ANY position is open for XAUUSD
    if TestingMode.is_position_open(client_id, "XAUUSD"):
        print("XAUUSD has at least one position open")
    
    # Check if BUY positions are open for XAUUSD
    if TestingMode.is_position_open(client_id, "XAUUSD", position_type=0):
        print("XAUUSD has at least one BUY position open")
    
    # Check if SELL positions are open for XAUUSD
    if TestingMode.is_position_open(client_id, "XAUUSD", position_type=1):
        print("XAUUSD has at least one SELL position open")
    
    # Count total positions
    total = TestingMode.get_position_count(client_id, "XAUUSD")
    print(f"XAUUSD has {total} total position(s) open")
    
    # Count BUY positions only
    buy_count = TestingMode.get_position_count(client_id, "XAUUSD", position_type=0)
    print(f"XAUUSD has {buy_count} BUY position(s) open")
    
    # Count SELL positions only
    sell_count = TestingMode.get_position_count(client_id, "XAUUSD", position_type=1)
    print(f"XAUUSD has {sell_count} SELL position(s) open")


# Example 2: Get detailed position information
def example_get_position_details(client_id):
    """Get all positions for a symbol with full details."""
    
    positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
    
    print(f"Found {len(positions)} position(s) for XAUUSD:")
    for pos in positions:
        ticket = pos.get("ticket")
        pos_type = "BUY" if pos.get("type") == 0 else "SELL"
        volume = pos.get("volume")
        price = pos.get("price")
        tp = pos.get("tp")
        sl = pos.get("sl")
        profit = pos.get("profit", 0)
        
        print(f"  Ticket: {ticket} | {pos_type} {volume} lots @ {price}")
        print(f"    TP: {tp} | SL: {sl} | P&L: ${profit:.2f}")


# Example 3: Open multiple positions on same symbol
def example_open_multiple_positions(client_id):
    """Open multiple positions on the same symbol with different parameters."""
    
    # Open first BUY position
    TestingMode.open_position(
        client_id,
        symbol="XAUUSD",
        position_type="BUY",
        volume=0.08,
        tp_pips=5000,
        sl_pips=5000,
        comment="XAUUSD Position #1"
    )
    
    # Open second BUY position with different TP/SL
    TestingMode.open_position(
        client_id,
        symbol="XAUUSD",
        position_type="BUY",
        volume=0.05,
        tp_pips=3000,
        sl_pips=2000,
        comment="XAUUSD Position #2"
    )
    
    # Open a SELL position as well
    TestingMode.open_position(
        client_id,
        symbol="XAUUSD",
        position_type="SELL",
        volume=0.03,
        tp_pips=2000,
        sl_pips=1000,
        comment="XAUUSD Hedge Position"
    )
    
    print("Opened 3 positions on XAUUSD (2 BUY, 1 SELL)")


# Example 4: Close specific position by ticket
def example_close_specific_position(client_id):
    """Close a specific position by its ticket number."""
    
    # Get all XAUUSD positions
    positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
    
    if positions:
        # Close the first position
        first_ticket = positions[0].get("ticket")
        TestingMode.close_position_by_ticket(client_id, first_ticket)
        print(f"Closed position with ticket {first_ticket}")
    else:
        print("No XAUUSD positions to close")


# Example 5: Close all positions of a specific type
def example_close_by_type(client_id):
    """Close all BUY positions for a symbol, keep SELL positions open."""
    
    # Close all BUY positions for XAUUSD
    commands = TestingMode.close_positions_by_symbol(
        client_id,
        symbol="XAUUSD",
        position_type=0  # 0 = BUY
    )
    
    print(f"Closed {len(commands)} BUY position(s) for XAUUSD")
    
    # SELL positions remain open


# Example 6: Close only some positions (partial closure)
def example_partial_closure(client_id):
    """Close only the first 2 positions, keep the rest open."""
    
    # Close maximum 2 positions for XAUUSD
    commands = TestingMode.close_positions_by_symbol(
        client_id,
        symbol="XAUUSD",
        max_count=2
    )
    
    print(f"Closed {len(commands)} position(s) for XAUUSD, others remain open")


# Example 7: Close all positions for a symbol
def example_close_all(client_id):
    """Close all positions for a symbol regardless of type."""
    
    commands = TestingMode.close_positions_by_symbol(
        client_id,
        symbol="XAUUSD"
    )
    
    print(f"Closed all {len(commands)} position(s) for XAUUSD")


# Example 8: Advanced - Manage positions based on profit
def example_manage_by_profit(client_id):
    """Close profitable positions, keep losing ones."""
    
    positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
    
    closed_count = 0
    for pos in positions:
        profit = pos.get("profit", 0)
        ticket = pos.get("ticket")
        
        # Close if profit > $50
        if profit > 50:
            TestingMode.close_position_by_ticket(client_id, ticket)
            print(f"Closed profitable position {ticket}: ${profit:.2f}")
            closed_count += 1
    
    print(f"Closed {closed_count} profitable position(s)")


# Example 9: Scale in/out strategy
def example_scale_strategy(client_id):
    """
    Example scaling strategy:
    - Open 3 positions with increasing TP levels
    - Close them one by one as price moves in favor
    """
    
    # Entry: Open 3 positions with staggered TPs
    TestingMode.open_position(
        client_id, "XAUUSD", "BUY", 0.03,
        tp_pips=2000, sl_pips=1000, comment="Scale #1 (TP1)"
    )
    
    TestingMode.open_position(
        client_id, "XAUUSD", "BUY", 0.03,
        tp_pips=4000, sl_pips=1000, comment="Scale #2 (TP2)"
    )
    
    TestingMode.open_position(
        client_id, "XAUUSD", "BUY", 0.02,
        tp_pips=6000, sl_pips=1000, comment="Scale #3 (TP3)"
    )
    
    print("Opened scaled positions: 3 entries with staggered TPs")
    
    # Later: Close first profitable position (simulating TP1 hit)
    positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
    buy_positions = [p for p in positions if p.get("type") == 0]  # BUY only
    
    if buy_positions:
        # Close the one with lowest TP (first to profit)
        first_position = buy_positions[0]
        TestingMode.close_position_by_ticket(client_id, first_position.get("ticket"))
        print("Closed first scaled position (TP1 reached)")


# Example 10: Complete workflow
def example_complete_workflow(client_id):
    """Complete example showing full position management."""
    
    symbol = "XAUUSD"
    
    # Step 1: Check if any positions exist
    if TestingMode.is_position_open(client_id, symbol):
        print(f"{symbol} already has positions, closing all first...")
        TestingMode.close_positions_by_symbol(client_id, symbol)
    
    # Step 2: Open initial positions
    print(f"\nOpening new positions for {symbol}...")
    TestingMode.open_position(
        client_id, symbol, "BUY", 0.08,
        tp_pips=5000, sl_pips=5000, comment="Main Position"
    )
    
    # Step 3: Add hedge if needed
    if TestingMode.get_position_count(client_id, symbol, position_type=0) > 0:
        print("Adding hedge position...")
        TestingMode.open_position(
            client_id, symbol, "SELL", 0.04,
            tp_pips=3000, sl_pips=3000, comment="Hedge"
        )
    
    # Step 4: Monitor and report
    total = TestingMode.get_position_count(client_id, symbol)
    buy_count = TestingMode.get_position_count(client_id, symbol, position_type=0)
    sell_count = TestingMode.get_position_count(client_id, symbol, position_type=1)
    
    print(f"\n{symbol} Status:")
    print(f"  Total positions: {total}")
    print(f"  BUY positions: {buy_count}")
    print(f"  SELL positions: {sell_count}")
    
    # Step 5: Get detailed info
    positions = TestingMode.get_open_positions_by_symbol(client_id, symbol)
    for pos in positions:
        ticket = pos.get("ticket")
        pos_type = "BUY" if pos.get("type") == 0 else "SELL"
        volume = pos.get("volume")
        comment = pos.get("comment", "")
        print(f"  [{ticket}] {pos_type} {volume} lots - {comment}")


# Example 11: Integration with News trading
def example_news_integration(client_id):
    """
    Example: When news affects a symbol that already has positions open.
    """
    
    symbol = "EURUSD"
    
    # Check existing positions before news trade
    existing_count = TestingMode.get_position_count(client_id, symbol)
    print(f"{symbol} has {existing_count} existing position(s)")
    
    # News says: SELL EUR
    news_direction = "SELL"
    
    # Check if we already have positions in the same direction
    existing_sells = TestingMode.get_position_count(client_id, symbol, position_type=1)
    
    if existing_sells > 0:
        print(f"Already have {existing_sells} SELL position(s), adding to position...")
    else:
        print("No existing SELL positions, opening new one...")
    
    # Open the news-based trade
    TestingMode.open_position(
        client_id, symbol, news_direction, 0.1,
        tp_pips=1000, sl_pips=500, comment="News Trade: EUR Weak"
    )
    
    # Now we can track this position independently
    new_total = TestingMode.get_position_count(client_id, symbol)
    print(f"Total {symbol} positions: {existing_count} → {new_total}")


if __name__ == "__main__":
    # Demo mode - shows usage (won't actually execute without real client)
    print("=== TestingMode Function Examples ===\n")
    print("Example 1: Check if positions are open")
    print("  TestingMode.is_position_open(client_id, 'XAUUSD')")
    print("  TestingMode.get_position_count(client_id, 'XAUUSD')\n")
    
    print("Example 2: Get position details")
    print("  positions = TestingMode.get_open_positions_by_symbol(client_id, 'XAUUSD')\n")
    
    print("Example 3: Open multiple positions")
    print("  TestingMode.open_position(client_id, 'XAUUSD', 'BUY', 0.08, ...)")
    print("  TestingMode.open_position(client_id, 'XAUUSD', 'BUY', 0.05, ...)\n")
    
    print("Example 4: Close specific position")
    print("  TestingMode.close_position_by_ticket(client_id, ticket_number)\n")
    
    print("Example 5: Close positions by type")
    print("  TestingMode.close_positions_by_symbol(client_id, 'XAUUSD', position_type=0)\n")
    
    print("Example 6: Close limited number")
    print("  TestingMode.close_positions_by_symbol(client_id, 'XAUUSD', max_count=2)\n")
    
    print("Example 7: Close all positions")
    print("  TestingMode.close_positions_by_symbol(client_id, 'XAUUSD')\n")
    
    print("\nSee function definitions above for complete implementation examples.")
