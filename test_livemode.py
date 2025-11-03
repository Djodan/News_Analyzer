"""
Test checkTime function with liveMode
"""
import sys
sys.path.insert(0, '.')

import Globals
from Functions import checkTime

print("Testing checkTime with liveMode")
print("=" * 50)

# Test 1: liveMode = True (should always return True)
print("\nTest 1: liveMode = True")
Globals.liveMode = True
Globals.timeStart = 18
Globals.timeEnd = 20
result = checkTime()
print(f"  timeStart: {Globals.timeStart}, timeEnd: {Globals.timeEnd}")
print(f"  liveMode: {Globals.liveMode}")
print(f"  checkTime() returned: {result}")
print(f"  Globals.timeToTrade: {Globals.timeToTrade}")
assert result == True, "Should be True when liveMode is True"

# Test 2: liveMode = False with time outside range
print("\nTest 2: liveMode = False (outside trading hours)")
Globals.liveMode = False
Globals.timeStart = 2
Globals.timeEnd = 4
result = checkTime()
print(f"  timeStart: {Globals.timeStart}, timeEnd: {Globals.timeEnd}")
print(f"  liveMode: {Globals.liveMode}")
print(f"  checkTime() returned: {result}")
print(f"  Globals.timeToTrade: {Globals.timeToTrade}")

# Test 3: liveMode = False with all-day trading
print("\nTest 3: liveMode = False (all day trading)")
Globals.liveMode = False
Globals.timeStart = 0
Globals.timeEnd = 23
result = checkTime()
print(f"  timeStart: {Globals.timeStart}, timeEnd: {Globals.timeEnd}")
print(f"  liveMode: {Globals.liveMode}")
print(f"  checkTime() returned: {result}")
print(f"  Globals.timeToTrade: {Globals.timeToTrade}")
assert result == True, "Should be True for all-day range"

print("\n✓ All tests passed! liveMode bypass working correctly.")
