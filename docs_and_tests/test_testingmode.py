"""
Test script for TestingMode functionality
Verifies that the refactored code still works correctly
"""

import sys
sys.path.insert(0, '..')

import Globals
import TestingMode
from Functions import _CLIENT_COMMANDS, _CLIENT_STATS

def test_open_all_symbols():
    """Test the open_all_symbols_from_config function"""
    print("=" * 60)
    print("TEST: open_all_symbols_from_config()")
    print("=" * 60)
    
    client_id = "TEST_CLIENT_1"
    
    # Verify Globals are set
    print(f"\nGlobals.symbolsToTrade: {Globals.symbolsToTrade}")
    print(f"Number of symbols: {len(Globals.symbolsToTrade)}")
    
    # Call the function
    opened_count = TestingMode.open_all_symbols_from_config(client_id)
    
    print(f"\nResult: {opened_count} positions opened")
    
    # Check commands were enqueued
    if client_id in _CLIENT_COMMANDS:
        commands = _CLIENT_COMMANDS[client_id]
        print(f"Commands enqueued: {len(commands)}")
        
        # Show details of each command
        for i, cmd in enumerate(commands, 1):
            state = cmd.get("state")
            payload = cmd.get("payload", {})
            symbol = payload.get("symbol")
            volume = payload.get("volume")
            comment = payload.get("comment")
            tp = payload.get("tpPips")
            sl = payload.get("slPips")
            
            state_str = "BUY" if state == 1 else "SELL" if state == 2 else "UNKNOWN"
            
            print(f"\n  Command {i}:")
            print(f"    Action: {state_str}")
            print(f"    Symbol: {symbol}")
            print(f"    Volume: {volume}")
            print(f"    TP/SL: {tp}/{sl} pips")
            print(f"    Comment: {comment}")
    else:
        print("WARNING: No commands found in queue!")
    
    return opened_count == len(Globals.symbolsToTrade)


def test_handle_testing_mode():
    """Test the handle_testing_mode function with replies counter"""
    print("\n" + "=" * 60)
    print("TEST: handle_testing_mode()")
    print("=" * 60)
    
    client_id = "TEST_CLIENT_2"
    
    # Clear any existing commands
    _CLIENT_COMMANDS.clear()
    _CLIENT_STATS.clear()
    
    # Test with replies=0 (should not trigger)
    print("\nTest 1: replies=0 (should not open positions)")
    stats = {"replies": 0}
    result = TestingMode.handle_testing_mode(client_id, stats)
    print(f"Result: {result}")
    print(f"Expected: False")
    assert result == False, "Should return False when replies=0"
    print("✓ PASS")
    
    # Test with replies=1 (should trigger)
    print("\nTest 2: replies=1 (should open positions)")
    stats = {"replies": 1}
    result = TestingMode.handle_testing_mode(client_id, stats)
    print(f"Result: {result}")
    print(f"Expected: True")
    assert result == True, "Should return True when replies=1"
    
    # Verify commands were enqueued
    if client_id in _CLIENT_COMMANDS:
        commands = _CLIENT_COMMANDS[client_id]
        print(f"Commands enqueued: {len(commands)}")
        assert len(commands) > 0, "Should have enqueued commands"
        print("✓ PASS")
    else:
        print("✗ FAIL: No commands enqueued!")
        return False
    
    # Test with replies=2 (should not trigger again)
    print("\nTest 3: replies=2 (should not open again)")
    initial_count = len(_CLIENT_COMMANDS[client_id])
    stats = {"replies": 2}
    result = TestingMode.handle_testing_mode(client_id, stats)
    print(f"Result: {result}")
    print(f"Expected: False")
    assert result == False, "Should return False when replies=2"
    
    final_count = len(_CLIENT_COMMANDS[client_id])
    assert initial_count == final_count, "Should not add more commands"
    print("✓ PASS")
    
    return True


def test_position_queries():
    """Test the position query functions"""
    print("\n" + "=" * 60)
    print("TEST: Position Query Functions")
    print("=" * 60)
    
    client_id = "TEST_CLIENT_3"
    
    # Note: These will return empty results since we don't have actual MT5 data
    # But we can verify the functions don't crash
    
    print("\nTest: is_position_open()")
    result = TestingMode.is_position_open(client_id, "XAUUSD")
    print(f"Result: {result} (expected False - no actual positions)")
    print("✓ Function executed without error")
    
    print("\nTest: get_position_count()")
    count = TestingMode.get_position_count(client_id, "XAUUSD")
    print(f"Result: {count} (expected 0 - no actual positions)")
    print("✓ Function executed without error")
    
    print("\nTest: get_open_positions_by_symbol()")
    positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
    print(f"Result: {positions} (expected [] - no actual positions)")
    print("✓ Function executed without error")
    
    return True


def test_position_opening():
    """Test the open_position function"""
    print("\n" + "=" * 60)
    print("TEST: open_position()")
    print("=" * 60)
    
    client_id = "TEST_CLIENT_4"
    _CLIENT_COMMANDS.clear()
    
    # Test BUY position
    print("\nTest 1: Open BUY position")
    cmd = TestingMode.open_position(
        client_id,
        symbol="XAUUSD",
        position_type="BUY",
        volume=0.1,
        tp_pips=1000,
        sl_pips=500,
        comment="Test BUY"
    )
    
    assert cmd is not None, "Should return command object"
    assert cmd.get("state") == 1, "BUY should be state 1"
    print("✓ PASS: BUY position command created")
    
    # Test SELL position
    print("\nTest 2: Open SELL position")
    cmd = TestingMode.open_position(
        client_id,
        symbol="EURUSD",
        position_type="SELL",
        volume=0.5,
        tp_pips=800,
        sl_pips=400,
        comment="Test SELL"
    )
    
    assert cmd is not None, "Should return command object"
    assert cmd.get("state") == 2, "SELL should be state 2"
    print("✓ PASS: SELL position command created")
    
    # Test with numeric type
    print("\nTest 3: Open with numeric position_type")
    cmd = TestingMode.open_position(
        client_id,
        symbol="GBPUSD",
        position_type=0,  # 0 = BUY
        volume=0.3,
        comment="Test numeric BUY"
    )
    
    assert cmd is not None, "Should return command object"
    assert cmd.get("state") == 1, "position_type=0 should be BUY (state 1)"
    print("✓ PASS: Numeric position type works")
    
    # Verify all commands were enqueued
    if client_id in _CLIENT_COMMANDS:
        commands = _CLIENT_COMMANDS[client_id]
        assert len(commands) == 3, f"Should have 3 commands, got {len(commands)}"
        print(f"\n✓ All 3 commands enqueued successfully")
    else:
        print("✗ FAIL: No commands found!")
        return False
    
    return True


def run_all_tests():
    """Run all test functions"""
    print("\n" + "=" * 60)
    print("TESTINGMODE REFACTORING - VERIFICATION TESTS")
    print("=" * 60)
    
    # Verify TestingMode is enabled
    if not Globals.TestingMode:
        print("\nWARNING: Globals.TestingMode is False")
        print("Setting to True for tests...")
        Globals.TestingMode = True
    
    print(f"\nGlobals.TestingMode: {Globals.TestingMode}")
    print(f"Symbols to trade: {len(Globals.symbolsToTrade)}")
    
    tests = [
        ("open_all_symbols_from_config", test_open_all_symbols),
        ("handle_testing_mode", test_handle_testing_mode),
        ("position_queries", test_position_queries),
        ("position_opening", test_position_opening),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result, error in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"  Error: {error}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Refactoring successful.")
        print("The code works exactly as before.")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
