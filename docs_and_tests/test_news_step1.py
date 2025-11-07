"""
Test script for News.py STEP 1 - Initialization
Tests the forecast pre-fetching functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, '..')

import Globals
from News import initialize_news_forecasts

print("=== TESTING NEWS.PY STEP 1 ===\n")
print(f"liveMode: {Globals.liveMode}")
print(f"csv_count: {Globals.csv_count}")
print(f"Initial _Currencies_: {Globals._Currencies_}\n")

# Run initialization
initialize_news_forecasts()

# Display results
print("\n=== RESULTS ===")
print(f"\nCurrencies stored: {len(Globals._Currencies_)}")
for currency, data in Globals._Currencies_.items():
    print(f"\n{currency}:")
    print(f"  Date: {data['date']}")
    print(f"  Event: {data['event']}")
    print(f"  Forecast: {data['forecast']}")
    print(f"  Actual: {data['actual']}")
    print(f"  Affect: {data['affect']}")
    print(f"  Retry Count: {data['retry_count']}")

print("\n=== TEST COMPLETE ===")
