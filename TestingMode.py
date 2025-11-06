"""
TestingMode.py
Logic for testing mode when enabled in Globals.py
"""

import Globals
from Functions import enqueue_command, get_client_open, can_open_trade, update_currency_count, find_available_pair_for_currency
from datetime import datetime, UTC
import time


def test_scaled_positions_with_closure(client_id):
    """
    Advanced test: Open 4 scaled positions for each symbol, then close specific ones.
    
    This demonstrates:
    1. Opening multiple positions on the same symbol
    2. Tracking each position independently
    3. Closing specific positions by their order
    
    Process:
    - Opens 4 positions per symbol immediately (no time delays)
    - Each position has increasing lot size (1x, 2x, 3x, 4x base lot)
    - After all open, closes positions #2 and #3
    - Leaves positions #1 and #4 open
    
    Args:
        client_id: The MT5 client ID
        
    Returns:
        dict: Summary of opened and closed positions
    """
    symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
    symbols_config = getattr(Globals, "_Symbols_", {})
    
    print("\n" + "=" * 60)
    print("SCALED POSITIONS TEST - Opening 4 positions per symbol")
    print("=" * 60)
    
    # Track all opened positions for later closure
    opened_positions = {}  # symbol → [cmd1, cmd2, cmd3, cmd4]
    
    for symbol in symbols_to_trade:
        if symbol not in symbols_config:
            continue
        
        config = symbols_config[symbol]
        base_lot = config.get("lot")
        tp_pips = config.get("TP")
        sl_pips = config.get("SL")
        
        # Determine position type
        manual_pos = config.get("manual_position", "X")
        position_type = "BUY" if manual_pos == "BUY" else "SELL" if manual_pos == "SELL" else "BUY"
        
        print(f"\n{symbol}: Opening 4 scaled positions ({position_type})")
        symbol_positions = []
        
        # Open 4 positions with increasing lot sizes
        for i in range(1, 5):
            lot_multiplier = i
            position_volume = base_lot * lot_multiplier
            
            cmd = open_position(
                client_id,
                symbol=symbol,
                position_type=position_type,
                volume=position_volume,
                tp_pips=tp_pips,
                sl_pips=sl_pips,
                comment=f"SCALE_TEST {symbol} #{i} ({lot_multiplier}x)"
            )
            
            if cmd:
                symbol_positions.append(cmd)
                cmd_id = cmd.get("cmdId", "")
                print(f"  Position #{i}: {position_volume:.2f} lots | cmdId: {cmd_id[:8] if cmd_id else 'N/A'}...")
        
        opened_positions[symbol] = symbol_positions
        print(f"  ✓ All 4 positions opened for {symbol}")
    
    # Summary of opened positions
    total_opened = sum(len(positions) for positions in opened_positions.values())
    print("\n" + "=" * 60)
    print(f"OPENED: {total_opened} total positions ({len(opened_positions)} symbols × 4)")
    print("=" * 60)
    
    # Now close positions #2 and #3 for each symbol
    print("\n" + "=" * 60)
    print("CLOSING: Positions #2 and #3 for each symbol")
    print("=" * 60)
    
    closed_count = 0
    
    for symbol, positions in opened_positions.items():
        if len(positions) < 4:
            print(f"{symbol}: Not enough positions, skipping closure")
            continue
        
        print(f"\n{symbol}: Closing positions #2 and #3")
        
        # Get positions from MT5 to find their ticket numbers
        # Wait a moment for positions to be opened on MT5 side
        time.sleep(2)
        
        open_positions = get_open_positions_by_symbol(client_id, symbol)
        
        if len(open_positions) >= 2:
            # Close by comment pattern to identify the right positions
            # We'll look for positions with comments containing "#2" and "#3"
            
            positions_to_close = []
            for pos in open_positions:
                comment = pos.get("comment", "")
                if "#2" in comment or "#3" in comment:
                    positions_to_close.append(pos)
            
            for pos in positions_to_close:
                ticket = pos.get("ticket")
                comment = pos.get("comment", "")
                
                if ticket:
                    result = close_position_by_ticket(client_id, ticket)
                    if result:
                        print(f"  ✓ Closed: {comment} (Ticket: {ticket})")
                        closed_count += 1
                    else:
                        print(f"  ✗ Failed to close: {comment} (Ticket: {ticket})")
        else:
            print(f"  ⚠️  Warning: Expected 4 positions, found {len(open_positions)}")
            print(f"     Skipping closure for {symbol}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("TEST COMPLETE - Summary")
    print("=" * 60)
    print(f"Total positions opened: {total_opened}")
    print(f"Positions closed: {closed_count}")
    print(f"Positions remaining: {total_opened - closed_count}")
    print("\nExpected result:")
    print(f"  - Each symbol should have 2 positions open (#1 and #4)")
    print(f"  - Positions #2 and #3 should be closed")
    print("=" * 60)
    
    return {
        "opened": total_opened,
        "closed": closed_count,
        "remaining": total_opened - closed_count,
        "symbols_tested": len(opened_positions)
    }


def get_open_positions_by_symbol(client_id, symbol):
    """
    Get all open positions for a specific symbol.
    
    Args:
        client_id: The MT5 client ID
        symbol: The trading symbol (e.g., "XAUUSD")
        
    Returns:
        list: List of position dictionaries with ticket, type, volume, etc.
    """
    open_positions = get_client_open(client_id)
    return [pos for pos in open_positions if pos.get("symbol") == symbol]


def is_position_open(client_id, symbol, position_type=None):
    """
    Check if any position is open for a symbol, optionally filtered by type.
    
    Args:
        client_id: The MT5 client ID
        symbol: The trading symbol
        position_type: Optional filter - 0 for BUY, 1 for SELL, None for any
        
    Returns:
        bool: True if at least one matching position is open
    """
    positions = get_open_positions_by_symbol(client_id, symbol)
    
    if position_type is not None:
        positions = [p for p in positions if p.get("type") == position_type]
    
    return len(positions) > 0


def get_position_count(client_id, symbol, position_type=None):
    """
    Count how many positions are open for a symbol.
    
    Args:
        client_id: The MT5 client ID
        symbol: The trading symbol
        position_type: Optional filter - 0 for BUY, 1 for SELL, None for any
        
    Returns:
        int: Number of open positions
    """
    positions = get_open_positions_by_symbol(client_id, symbol)
    
    if position_type is not None:
        positions = [p for p in positions if p.get("type") == position_type]
    
    return len(positions)


def close_position_by_ticket(client_id, ticket, volume=None):
    """
    Close a specific position by ticket number.
    
    Args:
        client_id: The MT5 client ID
        ticket: The position ticket number
        volume: Optional partial close volume (None = close all)
        
    Returns:
        dict: The command that was enqueued
    """
    # Get the position details to verify it exists
    open_positions = get_client_open(client_id)
    position = None
    for pos in open_positions:
        if pos.get("ticket") == ticket:
            position = pos
            break
    
    if position is None:
        print(f"[TestingMode] Warning: Ticket {ticket} not found in open positions")
        return None
    
    # Prepare close command
    payload = {
        "ticket": ticket,
        "symbol": position.get("symbol"),
        "type": position.get("type"),
    }
    
    if volume is not None:
        payload["volume"] = volume
    
    # Enqueue close command (state=3)
    cmd = enqueue_command(client_id, 3, payload)
    
    print(f"[TestingMode] Closing position: Ticket={ticket} Symbol={position.get('symbol')} "
          f"Type={'BUY' if position.get('type')==0 else 'SELL'}")
    
    return cmd


def close_positions_by_symbol(client_id, symbol, position_type=None, max_count=None):
    """
    Close all positions (or a subset) for a specific symbol.
    
    Args:
        client_id: The MT5 client ID
        symbol: The trading symbol
        position_type: Optional filter - 0 for BUY, 1 for SELL, None for all
        max_count: Maximum number of positions to close (None = close all)
        
    Returns:
        list: List of commands that were enqueued
    """
    positions = get_open_positions_by_symbol(client_id, symbol)
    
    if position_type is not None:
        positions = [p for p in positions if p.get("type") == position_type]
    
    if max_count is not None:
        positions = positions[:max_count]
    
    commands = []
    for pos in positions:
        cmd = close_position_by_ticket(client_id, pos.get("ticket"))
        if cmd:
            commands.append(cmd)
    
    print(f"[TestingMode] Closing {len(commands)} position(s) for {symbol}")
    return commands


def open_position(client_id, symbol, position_type, volume, tp_pips=None, sl_pips=None, comment=""):
    """
    Open a new position for a symbol.
    
    Args:
        client_id: The MT5 client ID
        symbol: The trading symbol
        position_type: 0 for BUY, 1 for SELL (or "BUY"/"SELL" strings)
        volume: Lot size
        tp_pips: Take profit in pips (optional)
        sl_pips: Stop loss in pips (optional)
        comment: Trade comment
        
    Returns:
        dict: The command that was enqueued, or None if rejected by filters
    """
    # Check risk management filters BEFORE opening position
    if not can_open_trade(symbol):
        print(f"[TestingMode] ❌ Position rejected by risk filters: {symbol}")
        print(f"  📊 Currency counts: {Globals._CurrencyCount_}")
        return None
    
    # Convert string to state number
    if position_type == "BUY" or position_type == 0:
        state = 1
        type_str = "BUY"
    elif position_type == "SELL" or position_type == 1:
        state = 2
        type_str = "SELL"
    else:
        print(f"[TestingMode] Error: Invalid position_type: {position_type}")
        return None
    
    payload = {
        "symbol": symbol,
        "volume": volume,
        "comment": comment or f"TESTING {symbol}",
    }
    
    if tp_pips is not None:
        payload["tpPips"] = tp_pips
    if sl_pips is not None:
        payload["slPips"] = sl_pips
    
    cmd = enqueue_command(client_id, state, payload)
    
    # Update currency count after successfully enqueuing
    update_currency_count(symbol, "add")
    
    # Uniform output format
    print(f"[TestingMode] ✅ Opening position: {type_str} {symbol} {volume} lots "
          f"(TP={tp_pips}, SL={sl_pips})")
    print(f"  ✓ Opened: {symbol} - {volume} lots")
    print(f"  📊 Currency counts: {Globals._CurrencyCount_}")
    
    return cmd


def open_all_symbols_simple(client_id):
    """
    Simple function: Open ONE position for each symbol in Globals.symbolsToTrade.
    Uses the symbol configuration from _Symbols_ dictionary.
    
    Args:
        client_id: The MT5 client ID
        
    Returns:
        int: Number of positions opened
    """
    symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
    symbols_config = getattr(Globals, "_Symbols_", {})
    
    opened_count = 0
    
    print(f"\n[TestingMode] === Opening positions for {len(symbols_to_trade)} symbols ===")
    
    for symbol in symbols_to_trade:
        if symbol in symbols_config:
            config = symbols_config[symbol]
            
            # Determine position type based on manual_position
            manual_pos = config.get("manual_position", "X")
            if manual_pos == "BUY":
                position_type = "BUY"
            elif manual_pos == "SELL":
                position_type = "SELL"
            else:
                # If manual_position is "X" or anything else, default to BUY for testing
                position_type = "BUY"
            
            print(f"\n[TestingMode] Opening {symbol}...")
            
            cmd = open_position(
                client_id,
                config.get("symbol"),
                position_type,
                config.get("lot"),
                tp_pips=config.get("TP"),
                sl_pips=config.get("SL"),
                comment=f"TESTING {symbol}"
            )
            
            if cmd:
                opened_count += 1
                cmd_id = cmd.get("cmdId", "")
                print(f"  ✓ Opened: {config.get('lot')} lots | cmdId: {cmd_id}")
    
    print(f"\n[TestingMode] Auto-opened {opened_count} position(s) from symbolsToTrade")
    return opened_count


def open_with_alternative_finder(client_id):
    """
    Advanced function: Test alternative pair finder with realistic News algorithm scenario.
    
    Simulates:
    1. Pre-existing positions that set currency limits
    2. News event occurs with primary affected pair
    3. Primary pair rejected due to currency limits
    4. Alternative finder searches for viable alternative
    5. Opens alternative if found
    
    This demonstrates the full risk management + alternative finder workflow.
    
    Args:
        client_id: The MT5 client ID
        
    Returns:
        int: Number of positions opened (including both pre-existing simulation and news trades)
    """
    symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
    symbols_config = getattr(Globals, "_Symbols_", {})
    system_news_event = getattr(Globals, "system_news_event", False)
    news_filter_findAvailablePair = getattr(Globals, "news_filter_findAvailablePair", False)
    
    opened_count = 0
    
    print(f"\n[TestingMode - Alternative Finder] ==========================================")
    print(f"[TestingMode - Alternative Finder] SIMULATION START")
    print(f"[TestingMode - Alternative Finder] ==========================================")
    
    # STEP 1: Simulate pre-existing positions
    print(f"\n[TestingMode - Alternative Finder] STEP 1: Simulating pre-existing positions...")
    print(f"[TestingMode - Alternative Finder] (This sets up currency limits)")
    
    # Simulate positions based on scenario
    # For JPY news scenario: Open EURUSD and GBPUSD to set USD at limit
    pre_existing = [
        {"symbol": "EURUSD", "comment": "PRE-EXISTING #1"},
        {"symbol": "GBPUSD", "comment": "PRE-EXISTING #2"}
    ]
    
    for pre_pos in pre_existing:
        symbol = pre_pos["symbol"]
        if symbol in symbols_config:
            config = symbols_config[symbol]
            manual_pos = config.get("manual_position", "X")
            position_type = "BUY" if manual_pos == "BUY" else "SELL" if manual_pos == "SELL" else "BUY"
            
            print(f"\n[TestingMode - Alternative Finder] Opening pre-existing: {symbol}...")
            
            cmd = open_position(
                client_id,
                symbol,
                position_type,
                config.get("lot"),
                tp_pips=config.get("TP"),
                sl_pips=config.get("SL"),
                comment=pre_pos["comment"]
            )
            
            if cmd:
                opened_count += 1
                # open_position() now prints success message and currency counts
    
    # STEP 2: News event occurs
    print(f"\n[TestingMode - Alternative Finder] ==========================================")
    print(f"[TestingMode - Alternative Finder] STEP 2: News Event Occurs")
    print(f"[TestingMode - Alternative Finder] ==========================================")
    
    if not system_news_event:
        print(f"[TestingMode - Alternative Finder] ⚠️  No news event set (system_news_event = False)")
        print(f"[TestingMode - Alternative Finder] Opening symbols from symbolsToTrade normally...")
        
        # Fall back to normal behavior
        for symbol in symbols_to_trade:
            if symbol in symbols_config:
                config = symbols_config[symbol]
                manual_pos = config.get("manual_position", "X")
                position_type = "BUY" if manual_pos == "BUY" else "SELL" if manual_pos == "SELL" else "BUY"
                
                cmd = open_position(
                    client_id,
                    symbol,
                    position_type,
                    config.get("lot"),
                    tp_pips=config.get("TP"),
                    sl_pips=config.get("SL"),
                    comment=f"TESTING {symbol}"
                )
                
                if cmd:
                    opened_count += 1
    else:
        print(f"\n[TestingMode - Alternative Finder] 📰 News Event: {system_news_event}")
        print(f"[TestingMode - Alternative Finder] symbolsToTrade: {symbols_to_trade}")
        
        # Try to open each symbol from symbolsToTrade
        for symbol in symbols_to_trade:
            if symbol not in symbols_config:
                continue
            
            config = symbols_config[symbol]
            manual_pos = config.get("manual_position", "X")
            position_type = "BUY" if manual_pos == "BUY" else "SELL" if manual_pos == "SELL" else "BUY"
            
            print(f"\n[TestingMode - Alternative Finder] 🎯 Attempting primary pair: {symbol}...")
            
            cmd = open_position(
                client_id,
                symbol,
                position_type,
                config.get("lot"),
                tp_pips=config.get("TP"),
                sl_pips=config.get("SL"),
                comment=f"NEWS_PRIMARY {symbol}"
            )
            
            if cmd:
                opened_count += 1
                # open_position() now prints success message and currency counts
            else:
                # Primary pair rejected - try alternative finder
                # open_position() already printed rejection message
                
                # STEP 3: Alternative Finder
                if news_filter_findAvailablePair and system_news_event:
                    print(f"\n[TestingMode - Alternative Finder] ==========================================")
                    print(f"[TestingMode - Alternative Finder] STEP 3: Alternative Finder Activated")
                    print(f"[TestingMode - Alternative Finder] ==========================================")
                    print(f"[TestingMode - Alternative Finder] 🔍 Searching for alternative {system_news_event} pair...")
                    
                    alternative = find_available_pair_for_currency(system_news_event)
                    
                    if alternative:
                        print(f"\n[TestingMode - Alternative Finder] ✅ ALTERNATIVE FOUND: {alternative}")
                        
                        # Open the alternative
                        if alternative in symbols_config:
                            alt_config = symbols_config[alternative]
                            alt_manual_pos = alt_config.get("manual_position", "X")
                            alt_position_type = "BUY" if alt_manual_pos == "BUY" else "SELL" if alt_manual_pos == "SELL" else "BUY"
                            
                            print(f"[TestingMode - Alternative Finder] Opening alternative: {alternative}...")
                            
                            alt_cmd = open_position(
                                client_id,
                                alternative,
                                alt_position_type,
                                alt_config.get("lot"),
                                tp_pips=alt_config.get("TP"),
                                sl_pips=alt_config.get("SL"),
                                comment=f"NEWS_ALTERNATIVE {alternative}"
                            )
                            
                            if alt_cmd:
                                opened_count += 1
                                # open_position() now prints success message and currency counts
                            else:
                                # open_position() already printed rejection
                                pass
                        else:
                            print(f"  ⚠️  Alternative {alternative} not in _Symbols_ config")
                    else:
                        print(f"\n[TestingMode - Alternative Finder] ❌ No alternative found for {system_news_event}")
                        print(f"[TestingMode - Alternative Finder] All {system_news_event} pairs at limit or unavailable")
                else:
                    if not news_filter_findAvailablePair:
                        print(f"  ⚠️  Alternative finder disabled (news_filter_findAvailablePair = False)")
                    if not system_news_event:
                        print(f"  ⚠️  No news currency set (system_news_event = False)")
    
    print(f"\n[TestingMode - Alternative Finder] ==========================================")
    print(f"[TestingMode - Alternative Finder] SIMULATION COMPLETE")
    print(f"[TestingMode - Alternative Finder] Total positions opened: {opened_count}")
    print(f"[TestingMode - Alternative Finder] ==========================================")
    
    return opened_count


def open_all_symbols_from_config(client_id, positions_per_symbol=4, close_positions=[2, 3]):
    """
    Open multiple positions for all symbols in Globals.symbolsToTrade using their configuration.
    This opens multiple positions on the same symbol to test multi-position handling.
    After all positions are opened, closes specific positions by number.
    
    Args:
        client_id: The MT5 client ID
        positions_per_symbol: Number of positions to open per symbol (default: 4)
        close_positions: List of position numbers to close after opening (default: [2, 3])
        
    Returns:
        int: Number of positions opened
    """
    symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
    symbols_config = getattr(Globals, "_Symbols_", {})
    
    opened_count = 0
    opened_positions = {}  # Track positions by symbol for later closure
    
    for symbol in symbols_to_trade:
        if symbol in symbols_config:
            config = symbols_config[symbol]
            
            # Determine position type based on manual_position
            manual_pos = config.get("manual_position", "X")
            if manual_pos == "BUY":
                position_type = "BUY"
            elif manual_pos == "SELL":
                position_type = "SELL"
            else:
                # If manual_position is "X" or anything else, default to BUY for testing
                position_type = "BUY"
            
            # Open multiple positions for this symbol
            print(f"\n[TestingMode] === Opening {positions_per_symbol} positions for {symbol} ===")
            symbol_commands = []
            
            for i in range(1, positions_per_symbol + 1):
                lot_multiplier = i  # 1x, 2x, 3x, 4x
                position_volume = config.get("lot") * lot_multiplier
                
                print(f"[TestingMode] Opening position {i}...")
                
                cmd = open_position(
                    client_id,
                    config.get("symbol"),
                    position_type,
                    position_volume,
                    tp_pips=config.get("TP"),
                    sl_pips=config.get("SL"),
                    comment=f"TESTING {symbol} #{i} ({lot_multiplier}x)"
                )
                
                if cmd:
                    opened_count += 1
                    symbol_commands.append((i, cmd))  # Store position number and command
                    cmd_id = cmd.get("cmdId", "")
                    print(f"  ✓ Position {i} opened: {position_volume:.2f} lots | cmdId: {cmd_id}")
            
            opened_positions[symbol] = symbol_commands
    
    print(f"[TestingMode] Auto-opened {opened_count} position(s) from symbolsToTrade ({len(symbols_to_trade)} symbols × {positions_per_symbol} positions)")
    
    # Now close specific positions if requested
    if close_positions:
        print(f"\n[TestingMode] Waiting 3 seconds for positions to register in MT5...")
        time.sleep(3)
        
        closed_count = 0
        print(f"[TestingMode] Closing positions {close_positions} for each symbol")
        
        for symbol, commands in opened_positions.items():
            print(f"\n{symbol}: Closing positions {close_positions}")
            
            # Get all open positions for this symbol
            open_pos = get_open_positions_by_symbol(client_id, symbol)
            
            if len(open_pos) > 0:
                # Close positions by comment pattern
                for pos in open_pos:
                    comment = pos.get("comment", "")
                    # Check if this position matches one we want to close
                    for pos_num in close_positions:
                        if f"#{pos_num}" in comment:
                            ticket = pos.get("ticket")
                            if ticket:
                                close_cmd = close_position_by_ticket(client_id, ticket)
                                if close_cmd:
                                    closed_count += 1
                                    print(f"  ✓ Closed: {comment} (Ticket: {ticket})")
                                break
        
        print(f"\n[TestingMode] Closed {closed_count} position(s)")
    
    return opened_count


def handle_testing_mode(client_id, stats):
    """
    Handle testing mode logic for a client.
    - Reply 1: Opens positions using selected algorithm
    
    Available algorithms:
    - open_all_symbols_simple(): Opens ONE position per symbol (basic test)
    - open_with_alternative_finder(): Tests alternative finder with News scenario (advanced)
    - open_all_symbols_from_config(): Opens MULTIPLE positions per symbol (stress test)
    
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
    
    # On first reply, run selected testing algorithm
    if replies == 1:
        # Switch between algorithms here:
        # opened_count = open_all_symbols_simple(client_id)  # Basic: ONE position per symbol
        opened_count = open_with_alternative_finder(client_id)  # Advanced: Alternative finder test
        # opened_count = open_all_symbols_from_config(client_id, 4, [2, 3])  # Stress: Multiple positions + closures
        
        return opened_count > 0
    
    return False
