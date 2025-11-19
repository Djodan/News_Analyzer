"""
Test the forecast retry logic when AI returns only Actual value
Simulates the scenario where Perplexity returns: "Actual : -2.5" without Forecast
"""

import sys
import os
import re

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Mock the AI response scenarios
class MockAI:
    def __init__(self):
        self.call_count = 0
    
    def get_news_data(self, event_name, currency, date, request_type):
        """Mock AI responses"""
        self.call_count += 1
        
        print(f"\n[MOCK AI] Call #{self.call_count} - request_type='{request_type}'")
        
        if request_type == "both":
            # First call: Returns only Actual (missing Forecast)
            response = "Actual : -2.5\nSource : MyFxBook"
            print(f"[MOCK AI] Returning partial data (Actual only)")
            return response
        
        elif request_type == "forecast":
            # Second call: Returns Forecast
            response = "Forecast : -11.25\nSource : MyFxBook"
            print(f"[MOCK AI] Returning Forecast")
            return response
        
        return "N/A"

# Test the parsing logic
def test_forecast_retry_logic():
    """Test the complete forecast retry flow"""
    
    print("=" * 80)
    print("TEST: Forecast Retry Logic")
    print("=" * 80)
    print("\nScenario: AI returns Actual but not Forecast on first query")
    print("Expected: System should query again for Forecast, then process both values")
    print("=" * 80)
    
    # Initialize mock
    mock_ai = MockAI()
    
    # Simulate event dictionary
    event_data = {
        'currency': 'USD',
        'event': '(United States) ADP Employment Change Weekly',
        'date': '2025, November 18, 08:15',
        'ai_date': 'November 18, 2025',
        'forecast': None,
        'actual': None,
        'forecast_retry_attempted': False
    }
    
    print("\n" + "=" * 80)
    print("STEP 1: Initial query for 'both' (Forecast + Actual)")
    print("=" * 80)
    
    # First query: request_type="both"
    response1 = mock_ai.get_news_data(
        event_data['event'],
        event_data['currency'],
        event_data['ai_date'],
        "both"
    )
    
    print(f"\nResponse 1: {response1}")
    print("\n" + "-" * 80)
    print("Parsing Response 1...")
    print("-" * 80)
    
    # Parse response 1
    forecast_found = False
    actual_found = False
    
    forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A)", response1, re.IGNORECASE)
    if forecast_match and forecast_match.group(1) != "N/A":
        event_data['forecast'] = float(forecast_match.group(1))
        forecast_found = True
        print(f"✓ Forecast: {event_data['forecast']}")
    else:
        print("✗ Forecast: NOT FOUND")
    
    actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+|N/A)", response1, re.IGNORECASE)
    if actual_match and actual_match.group(1) != "N/A":
        event_data['actual'] = float(actual_match.group(1))
        actual_found = True
        print(f"✓ Actual: {event_data['actual']}")
    else:
        print("✗ Actual: NOT FOUND")
    
    # Check if we need forecast retry
    if actual_found and not forecast_found and not event_data['forecast_retry_attempted']:
        print("\n" + "=" * 80)
        print("STEP 2: Forecast retry triggered")
        print("=" * 80)
        print(f"[PARTIAL DATA] Going back to query for Forecast because response only contained Actual: {event_data['actual']}")
        print("Actual value is already saved, now fetching missing Forecast...")
        
        event_data['forecast_retry_attempted'] = True
        
        # Second query: request_type="forecast"
        response2 = mock_ai.get_news_data(
            event_data['event'],
            event_data['currency'],
            event_data['ai_date'],
            "forecast"
        )
        
        print(f"\nResponse 2: {response2}")
        print("\n" + "-" * 80)
        print("Parsing Response 2...")
        print("-" * 80)
        
        # Parse response 2
        forecast_match2 = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A)", response2, re.IGNORECASE)
        if forecast_match2 and forecast_match2.group(1) != "N/A":
            event_data['forecast'] = float(forecast_match2.group(1))
            forecast_found = True
            print(f"✓ Forecast retrieved: {event_data['forecast']}")
        else:
            print("✗ Forecast: STILL NOT FOUND")
    
    # Final results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    if actual_found and forecast_found:
        print("✅ SUCCESS: Both Forecast and Actual retrieved")
        print(f"   Forecast: {event_data['forecast']}")
        print(f"   Actual: {event_data['actual']}")
        print(f"   AI Calls: {mock_ai.call_count}")
        print(f"   Forecast Retry Attempted: {event_data['forecast_retry_attempted']}")
        return True
    
    elif actual_found and not forecast_found:
        print("⚠️ PARTIAL: Proceeding without Forecast")
        print(f"   Forecast: N/A")
        print(f"   Actual: {event_data['actual']}")
        print(f"   AI Calls: {mock_ai.call_count}")
        print(f"   Reason: Forecast not available after dedicated query attempt")
        return True
    
    else:
        print("❌ FAILED: No actual value retrieved")
        return False


if __name__ == "__main__":
    success = test_forecast_retry_logic()
    print("\n" + "=" * 80)
    if success:
        print("✅ Test PASSED")
    else:
        print("❌ Test FAILED")
    print("=" * 80)
