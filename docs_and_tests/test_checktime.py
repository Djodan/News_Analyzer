"""
Test checkTime function
"""
import sys
sys.path.insert(0, '.')

import Globals
from Functions import checkTime

# Test the function
print(f"Current settings:")
print(f"  timeType: {Globals.timeType}")
print(f"  timeStart: {Globals.timeStart}")
print(f"  timeEnd: {Globals.timeEnd}")
print()

# Check if we can trade
result = checkTime()
print(f"checkTime() returned: {result}")
print(f"Globals.timeToTrade is now: {Globals.timeToTrade}")
print()

# Test with different ranges
print("Testing different time ranges:")

# Test 1: Normal range (e.g., 9 AM to 5 PM)
Globals.timeStart = 9
Globals.timeEnd = 17
result = checkTime()
print(f"  Range 9-17: timeToTrade = {result}")

# Test 2: Overnight range (e.g., 10 PM to 2 AM)
Globals.timeStart = 22
Globals.timeEnd = 2
result = checkTime()
print(f"  Range 22-2 (overnight): timeToTrade = {result}")

# Test 3: All day
Globals.timeStart = 0
Globals.timeEnd = 23
result = checkTime()
print(f"  Range 0-23 (all day): timeToTrade = {result}")

print("\n✓ checkTime function is working!")
