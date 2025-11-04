"""
Test Weekly algorithm
"""
import sys
sys.path.insert(0, '.')

import Globals
from Weekly import handle_weekly, is_sunday
from datetime import datetime
import pytz

print("Testing Weekly Algorithm")
print("=" * 60)

# Test 1: Check if is_sunday() works
print("\nTest 1: is_sunday() function")
print(f"  Current day (MT5 time): {is_sunday()}")
tz = pytz.timezone('Europe/Helsinki')
current_time = datetime.now(tz)
day_name = current_time.strftime('%A')
print(f"  Day name: {day_name}")

# Test 2: liveMode = True (should bypass all checks)
print("\nTest 2: liveMode = True (should execute)")
Globals.liveMode = True
Globals.symbolsToTrade = {"XAUUSD"}
Globals._Symbols_ = {
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.01, "TP": 100, "SL": 100, 
               "manual_position": "BUY"}
}

mock_stats = {"replies": 1}
result = handle_weekly("test_client", mock_stats)
print(f"  Result: {result}")
print(f"  Expected: True (liveMode bypasses all checks)")

# Test 3: liveMode = False, not Sunday
print("\nTest 3: liveMode = False, not Sunday (should not execute)")
Globals.liveMode = False
Globals.timeStart = 0
Globals.timeEnd = 23

# Only execute if it's actually not Sunday
if not is_sunday():
    result = handle_weekly("test_client", mock_stats)
    print(f"  Result: {result}")
    print(f"  Expected: False (not Sunday)")
else:
    print(f"  Skipped: Today is Sunday")

# Test 4: Test with manual_position = "X" (should skip)
print("\nTest 4: Symbol with manual_position='X' (should skip)")
Globals.liveMode = True
Globals._Symbols_["XAUUSD"]["manual_position"] = "X"
result = handle_weekly("test_client", mock_stats)
print(f"  Result: {result}")
print(f"  Expected: False (manual_position is X)")

# Test 5: Multiple symbols with mixed positions
print("\nTest 5: Multiple symbols")
Globals.liveMode = True
Globals.symbolsToTrade = {"XAUUSD", "USDJPY"}
Globals._Symbols_ = {
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.01, "TP": 100, "SL": 100, 
               "manual_position": "BUY"},
    "USDJPY": {"symbol": "USDJPY", "lot": 0.02, "TP": 200, "SL": 200, 
               "manual_position": "SELL"}
}
result = handle_weekly("test_client", mock_stats)
print(f"  Result: {result}")
print(f"  Expected: True (should open 2 positions)")

# Test 6: Only executes on first reply
print("\nTest 6: Reply count check")
Globals.liveMode = True
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"
mock_stats_reply2 = {"replies": 2}
result = handle_weekly("test_client", mock_stats_reply2)
print(f"  Result with replies=2: {result}")
print(f"  Expected: False (only executes on reply #1)")

print("\n✓ Weekly algorithm tests complete!")
