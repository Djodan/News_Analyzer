"""
Test script for News.py with live monitoring loop
Tests past event skipping and displays next event information
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import initialize_news_forecasts, monitor_news_events, get_next_event_info

print("=== TESTING NEWS.PY - LIVE MONITORING ===\n")
print(f"Settings:")
print(f"  liveMode: {Globals.liveMode}")
print(f"  csv_count: {Globals.csv_count}")
print(f"  news_process_past_events: {Globals.news_process_past_events}")
print()

# Run initialization (this will skip past events and fetch forecasts for future events)
initialize_news_forecasts()

print("\n" + "="*70)
print("INITIALIZED DICTIONARIES")
print("="*70 + "\n")

print("_Currencies_ Dictionary:")
print("-" * 70)
if Globals._Currencies_:
    for currency, data in Globals._Currencies_.items():
        print(f"\n{currency}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
else:
    print("  (empty)")

print("\n" + "-" * 70)
print("\n_Affected_ Dictionary:")
print("-" * 70)
if Globals._Affected_:
    for pair, data in Globals._Affected_.items():
        print(f"\n{pair}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
else:
    print("  (empty)")

print("\n" + "="*70)
print("LIVE MONITORING LOOP")
print("="*70 + "\n")

print("Monitoring for news events...")
print("Press Ctrl+C to stop\n")

try:
    loop_count = 0
    while True:
        loop_count += 1
        current_time = datetime.now()
        
        # Check if any event is ready
        ready_currency = monitor_news_events()
        
        if ready_currency:
            print(f"\n🔔 EVENT READY: {ready_currency}")
            print(f"  Event: {Globals._Currencies_[ready_currency]['event']}")
            print(f"  Current Time: {current_time}")
            print(f"  This is where STEP 3 would fetch the actual value...\n")
            
            # For testing, mark as processed to avoid infinite loop
            Globals._Currencies_[ready_currency]['actual'] = 0.0
            print(f"  (Marked as processed for testing purposes)\n")
        
        # Get next event info
        next_event = get_next_event_info()
        
        if next_event:
            time_until = next_event['time'] - current_time
            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)
            seconds = int(time_until.total_seconds() % 60)
            
            print(f"\r[Loop {loop_count}] Next event: {next_event['currency']} - {next_event['event'][:50]}... | "
                  f"Event Time: {next_event['time'].strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"Time Until: {hours}h {minutes}m {seconds}s", end='', flush=True)
        else:
            print(f"\r[Loop {loop_count}] No more events to process. | "
                  f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}", end='', flush=True)
        
        # Sleep for 5 seconds between checks
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\n\n=== MONITORING STOPPED ===")
    print(f"Total loops: {loop_count}")
    print("\nFinal state of _Currencies_:")
    for currency, data in Globals._Currencies_.items():
        print(f"\n{currency}:")
        print(f"  Event: {data['event']}")
        print(f"  Date: {data['date']}")
        print(f"  Forecast: {data['forecast']}")
        print(f"  Actual: {data['actual']}")
        print(f"  Status: {'PROCESSED' if data['actual'] is not None else 'PENDING'}")
    
    print("\n=== TEST COMPLETE ===")
