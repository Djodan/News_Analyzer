"""
Test trade tracking and retry logic
"""
import sys
sys.path.insert(0, '.')

import Globals
from Functions import (
    is_symbol_tradeable,
    mark_pending_trade,
    clear_pending_trade,
    retry_pending_trades,
    reset_session_tracking
)

print("Testing Trade Tracking System")
print("=" * 60)

# Reset tracking for clean test
reset_session_tracking()

# Test 1: Check if new symbol is tradeable
print("\nTest 1: New symbol should be tradeable")
result = is_symbol_tradeable("XAUUSD")
print(f"  is_symbol_tradeable('XAUUSD'): {result}")
print(f"  Expected: True")
assert result == True, "New symbol should be tradeable"

# Test 2: Mark symbol as traded (via traded_this_session field)
print("\nTest 2: Mark symbol as traded")
Globals._Symbols_["XAUUSD"]["traded_this_session"] = True
result = is_symbol_tradeable("XAUUSD")
print(f"  is_symbol_tradeable('XAUUSD') after marking: {result}")
print(f"  Expected: False")
assert result == False, "Traded symbol should not be tradeable again"

# Test 3: Symbol currently open should not be tradeable
print("\nTest 3: Currently open symbol should not be tradeable")
reset_session_tracking()
Globals.symbolsCurrentlyOpen = ["USDJPY"]
result = is_symbol_tradeable("USDJPY")
print(f"  is_symbol_tradeable('USDJPY') when open: {result}")
print(f"  Expected: False")
print(f"  traded_this_session: {Globals._Symbols_['USDJPY']['traded_this_session']}")
assert result == False, "Open symbol should not be tradeable"
assert Globals._Symbols_["USDJPY"]["traded_this_session"] == True, "Open symbol should be marked as traded"

# Test 4: Mark pending trade
print("\nTest 4: Mark pending trade")
reset_session_tracking()
Globals.symbolsCurrentlyOpen = []
mark_pending_trade("XAUUSD", 1, "TEST")
print(f"  pending_trade: {Globals._Symbols_['XAUUSD']['pending_trade']}")
assert Globals._Symbols_["XAUUSD"]["pending_trade"] is not None, "Symbol should have pending trade"
assert Globals._Symbols_["XAUUSD"]["pending_trade"]["state"] == 1, "Pending trade state should be 1"

# Test 5: Retry pending trades (should fail - trading time False)
print("\nTest 5: Retry when timeToTrade=False (should clear pending)")
Globals.timeToTrade = False
Globals.liveMode = False
mark_pending_trade("USDJPY", 2, "TEST2")
result = retry_pending_trades("test_client")
print(f"  retry_pending_trades() result: {result}")
print(f"  XAUUSD pending_trade: {Globals._Symbols_['XAUUSD']['pending_trade']}")
print(f"  USDJPY pending_trade: {Globals._Symbols_['USDJPY']['pending_trade']}")
print(f"  Expected: False, all pending should be None")
assert result == False, "Should not retry when trading time is over"
assert Globals._Symbols_["XAUUSD"]["pending_trade"] is None, "Pending should be cleared"
assert Globals._Symbols_["USDJPY"]["pending_trade"] is None, "Pending should be cleared"

# Test 6: Retry pending trades (should work - trading time True)
print("\nTest 6: Retry when timeToTrade=True")
reset_session_tracking()
Globals.timeToTrade = True
Globals.liveMode = True
mark_pending_trade("XAUUSD", 1, "RETRY1")
mark_pending_trade("USDJPY", 2, "RETRY2")
print(f"  XAUUSD pending before: {Globals._Symbols_['XAUUSD']['pending_trade']}")
print(f"  USDJPY pending before: {Globals._Symbols_['USDJPY']['pending_trade']}")
result = retry_pending_trades("test_client")
print(f"  retry_pending_trades() result: {result}")
print(f"  Expected: True")
assert result == True, "Should retry pending trades during trading time"

# Test 7: Pending trade becomes open (auto-clear)
print("\nTest 7: Pending trade becomes open (auto-clear)")
reset_session_tracking()
Globals.liveMode = True
Globals.timeToTrade = True
mark_pending_trade("XAUUSD", 1, "TEST")
print(f"  XAUUSD pending before: {Globals._Symbols_['XAUUSD']['pending_trade']}")

# Simulate symbol becoming open
Globals.symbolsCurrentlyOpen = ["XAUUSD"]
result = retry_pending_trades("test_client")
print(f"  symbolsCurrentlyOpen: {Globals.symbolsCurrentlyOpen}")
print(f"  XAUUSD pending after: {Globals._Symbols_['XAUUSD']['pending_trade']}")
print(f"  XAUUSD traded_this_session: {Globals._Symbols_['XAUUSD']['traded_this_session']}")
assert Globals._Symbols_["XAUUSD"]["pending_trade"] is None, "Open symbol should be cleared from pending"
assert Globals._Symbols_["XAUUSD"]["traded_this_session"] == True, "Open symbol should be marked as traded"

# Test 8: Multiple symbols - mixed states
print("\nTest 8: Multiple symbols with mixed states")
reset_session_tracking()
Globals.liveMode = True
Globals.timeToTrade = True
Globals.symbolsCurrentlyOpen = ["USDJPY"]  # Already open

# XAUUSD should be tradeable
result1 = is_symbol_tradeable("XAUUSD")
# USDJPY should not be tradeable (open)
result2 = is_symbol_tradeable("USDJPY")
# NZDCHF should be tradeable
result3 = is_symbol_tradeable("NZDCHF")

print(f"  XAUUSD tradeable: {result1} (Expected: True)")
print(f"  USDJPY tradeable: {result2} (Expected: False)")
print(f"  NZDCHF tradeable: {result3} (Expected: True)")

assert result1 == True, "XAUUSD should be tradeable"
assert result2 == False, "USDJPY should not be tradeable (open)"
assert result3 == True, "NZDCHF should be tradeable"

# Test 9: Clear pending trade
print("\nTest 9: Clear pending trade")
reset_session_tracking()
mark_pending_trade("XAUUSD", 1, "TEST")
print(f"  XAUUSD pending before clear: {Globals._Symbols_['XAUUSD']['pending_trade']}")
clear_pending_trade("XAUUSD")
print(f"  XAUUSD pending after clear: {Globals._Symbols_['XAUUSD']['pending_trade']}")
print(f"  XAUUSD traded_this_session: {Globals._Symbols_['XAUUSD']['traded_this_session']}")
assert Globals._Symbols_["XAUUSD"]["pending_trade"] is None, "Pending should be cleared"
assert Globals._Symbols_["XAUUSD"]["traded_this_session"] == True, "Should be marked as traded"

print("\n" + "=" * 60)
print("✓ All trade tracking tests passed!")
print("=" * 60)
