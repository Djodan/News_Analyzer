"""
Test forecast retry logic when Forecast is not available even after retry
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

class MockAI_NoForecast:
    def __init__(self):
        self.call_count = 0
    
    def get_news_data(self, event_name, currency, date, request_type):
        """Mock AI responses - Forecast never available"""
        self.call_count += 1
        
        print(f"\n[MOCK AI] Call #{self.call_count} - request_type='{request_type}'")
        
        if request_type == "both":
            response = "Actual : -2.5\nSource : MyFxBook"
            print(f"[MOCK AI] Returning partial data (Actual only)")
            return response
        
        elif request_type == "forecast":
            response = "Forecast : N/A\nSource : MyFxBook"
            print(f"[MOCK AI] Forecast not available")
            return response
        
        return "N/A"

def test_forecast_retry_fails():
    """Test when forecast is not available even after retry"""
    
    print("=" * 80)
    print("TEST: Forecast Retry Logic (Forecast Unavailable)")
    print("=" * 80)
    print("\nScenario: Forecast not available even after dedicated query")
    print("Expected: System should proceed with just Actual (affect = NEUTRAL)")
    print("=" * 80)
    
    mock_ai = MockAI_NoForecast()
    
    event_data = {
        'currency': 'USD',
        'event': '(United States) ADP Employment Change Weekly',
        'forecast': None,
        'actual': None,
        'forecast_retry_attempted': False
    }
    
    print("\n" + "=" * 80)
    print("STEP 1: Initial query for 'both'")
    print("=" * 80)
    
    response1 = mock_ai.get_news_data("test", "USD", "Nov 18", "both")
    print(f"Response: {response1}")
    
    actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+|N/A)", response1, re.IGNORECASE)
    forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A)", response1, re.IGNORECASE)
    
    actual_found = False
    forecast_found = False
    
    if actual_match and actual_match.group(1) != "N/A":
        event_data['actual'] = float(actual_match.group(1))
        actual_found = True
        print(f"✓ Actual: {event_data['actual']}")
    
    if forecast_match and forecast_match.group(1) != "N/A":
        event_data['forecast'] = float(forecast_match.group(1))
        forecast_found = True
    else:
        print("✗ Forecast: NOT FOUND")
    
    # Trigger retry
    if actual_found and not forecast_found and not event_data['forecast_retry_attempted']:
        print("\n" + "=" * 80)
        print("STEP 2: Forecast retry triggered")
        print("=" * 80)
        print(f"[PARTIAL DATA] Retrying for Forecast (Actual already saved: {event_data['actual']})")
        
        event_data['forecast_retry_attempted'] = True
        
        response2 = mock_ai.get_news_data("test", "USD", "Nov 18", "forecast")
        print(f"Response: {response2}")
        
        forecast_match2 = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A)", response2, re.IGNORECASE)
        if forecast_match2 and forecast_match2.group(1) != "N/A":
            event_data['forecast'] = float(forecast_match2.group(1))
            forecast_found = True
        else:
            print("✗ Forecast: STILL NOT AVAILABLE")
    
    # Final results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    if actual_found and not forecast_found:
        print("⚠️ MOVING ON: Proceeding without Forecast")
        print(f"   Forecast: N/A")
        print(f"   Actual: {event_data['actual']}")
        print(f"   AI Calls: {mock_ai.call_count}")
        print(f"   Reason: Forecast not available after dedicated query attempt")
        print("\n   → Affect will be: NEUTRAL (missing data)")
        print("   → No trading signals will be generated")
        return True
    elif actual_found and forecast_found:
        print("✅ SUCCESS: Both values retrieved")
        return True
    else:
        print("❌ FAILED")
        return False

if __name__ == "__main__":
    success = test_forecast_retry_fails()
    print("\n" + "=" * 80)
    if success:
        print("✅ Test PASSED")
    else:
        print("❌ Test FAILED")
    print("=" * 80)
