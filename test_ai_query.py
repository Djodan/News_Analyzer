"""
Test AI query for ADP Employment Change Weekly event
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from AI_Perplexity import get_news_data

# Test the exact event that failed
event_name = "(United States) ADP Employment Change Weekly"
currency = "USD"
date = "November 18, 2025"
request_type = "both"

print("=" * 60)
print("Testing AI Query for News Event")
print("=" * 60)
print(f"Event: {event_name}")
print(f"Currency: {currency}")
print(f"Date: {date}")
print(f"Request Type: {request_type}")
print("=" * 60)
print("\nQuerying Perplexity AI...")
print("-" * 60)

try:
    response = get_news_data(event_name, currency, date, request_type)
    print("\n" + "=" * 60)
    print("PERPLEXITY RESPONSE:")
    print("=" * 60)
    print(response)
    print("=" * 60)
    
    # Parse the response
    import re
    
    print("\nPARSING RESULTS:")
    print("-" * 60)
    
    forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A|FALSE)", response, re.IGNORECASE)
    if forecast_match:
        print(f"Forecast: {forecast_match.group(1)}")
    else:
        print("Forecast: NOT FOUND")
    
    actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+|N/A|FALSE)", response, re.IGNORECASE)
    if actual_match:
        print(f"Actual: {actual_match.group(1)}")
    else:
        print("Actual: NOT FOUND")
    
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
