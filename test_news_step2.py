"""
Test script for News.py STEP 2 - Time Monitoring
Tests the event monitoring functionality with simulated event times
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import initialize_news_forecasts, monitor_news_events, _event_times

print("=== TESTING NEWS.PY STEP 2 - TIME MONITORING ===\n")

# First, run initialization (this will use real API calls with csv_count=2)
print("Step 1: Running initialization...\n")
initialize_news_forecasts()

print("\n" + "="*60)
print("Step 2: Testing time monitoring logic")
print("="*60 + "\n")

# Display current event times
print("Current event times stored:")
for currency, event_time in _event_times.items():
    print(f"  {currency}: {event_time}")

current_time = datetime.now()
print(f"\nCurrent time: {current_time}\n")

# Test 1: Check monitoring with real times (events in future)
print("TEST 1: Monitoring with real event times (should return None - events in future)")
print("-" * 60)
ready_currency = monitor_news_events()
if ready_currency:
    print(f"✗ ERROR: Found ready event: {ready_currency} (should be None)")
else:
    print("✓ PASS: No events ready (as expected - all events are in future)")

# Test 2: Simulate an event that just occurred by modifying event time
print("\n\nTEST 2: Simulate first event occurred (modify event time to past)")
print("-" * 60)

# Get first currency
first_currency = list(_event_times.keys())[0]
print(f"Simulating event for: {first_currency}")

# Set event time to 5 minutes ago
past_time = current_time - timedelta(minutes=5)
_event_times[first_currency] = past_time
print(f"Modified event time to: {past_time} (5 minutes ago)")

# Check monitoring again
ready_currency = monitor_news_events()
if ready_currency == first_currency:
    print(f"✓ PASS: Detected ready event: {ready_currency}")
else:
    print(f"✗ ERROR: Expected {first_currency}, got {ready_currency}")

# Test 3: Simulate fetching actual (should no longer be ready)
print("\n\nTEST 3: Simulate actual value fetched (should no longer be ready)")
print("-" * 60)

# Set actual value (simulating STEP 3 completed)
Globals._Currencies_[first_currency]['actual'] = 3.5
print(f"Set actual value for {first_currency}: 3.5")

# Check monitoring again
ready_currency = monitor_news_events()
if ready_currency is None:
    print(f"✓ PASS: Event no longer ready (actual already fetched)")
elif ready_currency == first_currency:
    print(f"✗ ERROR: Event still showing as ready (should be filtered out)")
else:
    print(f"✓ PASS: Different event ready: {ready_currency}")

# Test 4: Simulate second event occurred
print("\n\nTEST 4: Simulate second event occurred")
print("-" * 60)

if len(_event_times) > 1:
    second_currency = list(_event_times.keys())[1]
    print(f"Simulating event for: {second_currency}")
    
    # Set event time to 3 minutes ago
    past_time_2 = current_time - timedelta(minutes=3)
    _event_times[second_currency] = past_time_2
    print(f"Modified event time to: {past_time_2} (3 minutes ago)")
    
    # Check monitoring
    ready_currency = monitor_news_events()
    if ready_currency == second_currency:
        print(f"✓ PASS: Detected ready event: {ready_currency}")
    else:
        print(f"✗ ERROR: Expected {second_currency}, got {ready_currency}")
else:
    print("⚠ SKIP: Only one event in test data")

# Display final state
print("\n\n" + "="*60)
print("FINAL STATE")
print("="*60 + "\n")

print("_Currencies_ dictionary:")
for currency, data in Globals._Currencies_.items():
    print(f"\n{currency}:")
    print(f"  Event: {data['event']}")
    print(f"  Forecast: {data['forecast']}")
    print(f"  Actual: {data['actual']}")
    print(f"  Event Time: {_event_times.get(currency, 'N/A')}")
    
    if _event_times.get(currency):
        time_diff = _event_times[currency] - current_time
        status = "READY" if time_diff.total_seconds() < 0 and data['actual'] is None else "WAITING"
        print(f"  Status: {status}")

print("\n=== TEST COMPLETE ===")
