import sys
sys.path.insert(0, '..')

#!/usr/bin/env python3
"""
Test script to trigger TestingMode and verify risk management filters.
Simulates an MT5 client sending data to the server.
"""

import requests
import json
import time

def send_payload(reply_count=1):
    """Send a test payload to the server to trigger TestingMode."""
    
    url = "http://127.0.0.1:5000/"
    
    payload = {
        "id": "TEST_CLIENT_1",
        "open": [],
        "closedOnline": [],
        "symbolsCurrentlyOpen": []
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"SENDING REQUEST #{reply_count} TO SERVER")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\n{'='*60}")
        print(f"SERVER RESPONSE")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        return response
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RISK MANAGEMENT FILTER INTEGRATION TEST")
    print("="*60)
    print("\nConfiguration:")
    print("  symbolsToTrade = {XAUUSD, NZDCHF, EURCHF}")
    print("  news_filter_maxTradePerCurrency = 2")
    print("  positions_per_symbol = 4")
    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("="*60)
    print("XAUUSD:")
    print("  Position 1: XAU=1, USD=1 ✅ ALLOWED")
    print("  Position 2: XAU=2, USD=2 ✅ ALLOWED (at limit)")
    print("  Position 3: Would make XAU=3, USD=3 ❌ REJECTED")
    print("  Position 4: Would make XAU=4, USD=4 ❌ REJECTED")
    print("\nNZDCHF:")
    print("  Position 1: NZD=1, CHF=1 ✅ ALLOWED")
    print("  Position 2: NZD=2, CHF=2 ✅ ALLOWED (at limit)")
    print("  Position 3: Would make NZD=3, CHF=3 ❌ REJECTED")
    print("  Position 4: Would make NZD=4, CHF=4 ❌ REJECTED")
    print("\nEURCHF:")
    print("  Position 1: EUR=1, CHF=3 ❌ REJECTED (CHF already at 2)")
    print("  Position 2-4: ❌ REJECTED")
    print("\n" + "="*60)
    
    # Send first request (this should trigger auto-open on reply #1)
    print("\n⏳ Sending request to trigger TestingMode...")
    time.sleep(1)
    
    response = send_payload(reply_count=1)
    
    if response:
        print("\n✅ Test completed!")
        print("\nCheck the server terminal output for detailed filter messages.")
    else:
        print("\n❌ Test failed - could not connect to server")
        print("Make sure the server is running: python Server.py")
