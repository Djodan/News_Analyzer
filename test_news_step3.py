"""
Test script for News.py STEP 3 - Fetch Actual with Retry
Tests fetching actual values for past events (test mode)
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import initialize_news_forecasts, monitor_news_events, fetch_actual_value

print("=== TESTING NEWS.PY STEP 3 - FETCH ACTUAL ===\n")

# Enable test mode to process ONLY past events
Globals.news_test_mode = True
Globals.csv_count = 2  # Limit to 2 past events

print(f"Settings: liveMode={Globals.liveMode}, csv_count={Globals.csv_count}, test_mode={Globals.news_test_mode}\n")

# Run initialization (will fetch forecasts for past events in test mode)
initialize_news_forecasts()

print("\n" + "="*70)
print("PROCESSING EVENTS")
print("="*70 + "\n")

# Process each event to fetch actual values
events_processed = []
for currency in list(Globals._Currencies_.keys()):
    success = fetch_actual_value(currency)
    events_processed.append({
        'currency': currency,
        'success': success
    })

print("\n" + "="*70)
print("RESULTS")
print("="*70 + "\n")

# Display results for each processed event
for event in events_processed:
    currency = event['currency']
    data = Globals._Currencies_[currency]
    status = "SUCCESS" if event['success'] else "FAILED/NOT READY"
    
    print(f"{currency}: [{status}]")
    print(f"  Event: {data['event']}")
    print(f"  Date: {data['date']}")
    print(f"  Forecast: {data['forecast']}")
    print(f"  Actual: {data['actual']}")
    print(f"  Retry Count: {data['retry_count']}")
    
    # Show comparison if both forecast and actual available
    if data['forecast'] is not None and data['actual'] is not None:
        diff = data['actual'] - data['forecast']
        pct = (diff / data['forecast'] * 100) if data['forecast'] != 0 else 0
        print(f"  Difference: {diff:+.2f} ({pct:+.2f}%)")
    print()

# Display both dictionaries
print("="*70)
print("DICTIONARIES STATE")
print("="*70 + "\n")

print("_Currencies_ Dictionary:")
print("-" * 70)
if Globals._Currencies_:
    for currency, data in Globals._Currencies_.items():
        print(f"\n{currency}:")
        print(f"  date: {data['date']}")
        print(f"  event: {data['event']}")
        print(f"  forecast: {data['forecast']}")
        print(f"  actual: {data['actual']}")
        print(f"  affect: {data['affect']}")
        print(f"  retry_count: {data['retry_count']}")
else:
    print("  (empty)")

print("\n" + "-" * 70)
print("\n_Affected_ Dictionary:")
print("-" * 70)
if Globals._Affected_:
    for pair, data in Globals._Affected_.items():
        print(f"\n{pair}:")
        print(f"  date: {data['date']}")
        print(f"  event: {data['event']}")
        print(f"  position: {data['position']}")
else:
    print("  (empty)")

print("\n" + "="*70)
print("=== TEST COMPLETE ===")

