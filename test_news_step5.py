"""
Test script for News.py STEP 5 - Generate Trading Signals
Tests ChatGPT signal generation with News_Rules.txt
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import initialize_news_forecasts, fetch_actual_value

print("=== TESTING NEWS.PY STEP 5 - GENERATE TRADING SIGNALS ===\n")

# Enable test mode to process ONLY past events
Globals.news_test_mode = True
Globals.csv_count = 2

print(f"Settings: test_mode={Globals.news_test_mode}, csv_count={Globals.csv_count}\n")

# Run initialization
initialize_news_forecasts()

print("\n" + "="*70)
print("PROCESSING EVENTS")
print("="*70 + "\n")

# Process each event
for currency in list(Globals._Currencies_.keys()):
    fetch_actual_value(currency)
    print()

print("="*70)
print("RESULTS")
print("="*70 + "\n")

# Display results
for currency, data in Globals._Currencies_.items():
    print(f"{currency}: {data['event']}")
    print(f"  Forecast: {data['forecast']}, Actual: {data['actual']}")
    print(f"  Affect: {data['affect']}")
    print()

print("="*70)
print("DICTIONARIES")
print("="*70 + "\n")

print("_Currencies_:")
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
print("\n_Affected_:")
print("-" * 70)
if Globals._Affected_:
    for pair, data in Globals._Affected_.items():
        print(f"\n{pair}:")
        print(f"  date: {data['date']}")
        print(f"  event: {data['event']}")
        print(f"  position: {data['position']}")
else:
    print("  (empty - will be populated in STEP 6)")

print("\n" + "="*70)
print("=== TEST COMPLETE ===")
