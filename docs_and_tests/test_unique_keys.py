"""
Test to demonstrate unique event keys supporting multiple events per currency
"""

import sys
sys.path.insert(0, '..')

import Globals
from News import initialize_news_forecasts, monitor_news_events

# Clear existing data
Globals._Currencies_ = {}

# Initialize (will create unique keys for events)
print("Initializing news forecasts with unique keys...")
print("=" * 80)
initialize_news_forecasts()

print("\n" + "=" * 80)
print("CURRENCIES DICTIONARY (with unique keys):")
print("=" * 80)

for event_key, event_data in Globals._Currencies_.items():
    currency = event_data.get('currency', 'N/A')
    event_name = event_data.get('event', 'N/A')
    date = event_data.get('date', 'N/A')
    forecast = event_data.get('forecast', 'N/A')
    actual = event_data.get('actual', 'N/A')
    
    print(f"\nKey: {event_key}")
    print(f"  Currency: {currency}")
    print(f"  Event: {event_name}")
    print(f"  Date: {date}")
    print(f"  Forecast: {forecast}")
    print(f"  Actual: {actual}")

print("\n" + "=" * 80)
print(f"Total events stored: {len(Globals._Currencies_)}")
print("=" * 80)

# Check for ready events
print("\nChecking for ready events...")
ready_event = monitor_news_events()

if ready_event:
    print(f"✓ Found ready event: {ready_event}")
    event_data = Globals._Currencies_[ready_event]
    print(f"  Currency: {event_data.get('currency')}")
    print(f"  Event: {event_data.get('event')}")
else:
    print("✗ No events ready to process")
