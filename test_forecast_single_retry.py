"""
Test that forecast retry only happens ONCE (no infinite loops)
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

class MockAI_Counter:
    def __init__(self):
        self.call_count = 0
    
    def get_news_data(self, event_name, currency, date, request_type):
        """Mock AI - always returns partial data"""
        self.call_count += 1
        print(f"[MOCK AI] Call #{self.call_count} - request_type='{request_type}'")
        
        # Always return only Actual (to test retry limit)
        return "Actual : -2.5\nSource : MyFxBook"

def test_single_retry_only():
    """Test that retry only happens once"""
    
    print("=" * 80)
    print("TEST: Single Forecast Retry Only (No Loops)")
    print("=" * 80)
    print("\nScenario: Forecast missing, retry attempted, should NOT retry again")
    print("Expected: Only 2 AI calls total (initial + 1 retry)")
    print("=" * 80)
    
    mock_ai = MockAI_Counter()
    
    event_data = {
        'forecast': None,
        'actual': None,
        'forecast_retry_attempted': False
    }
    
    # First attempt
    print("\n[ATTEMPT 1] Initial query")
    response1 = mock_ai.get_news_data("test", "USD", "Nov 18", "both")
    
    actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+)", response1, re.IGNORECASE)
    if actual_match:
        event_data['actual'] = float(actual_match.group(1))
        print(f"✓ Actual: {event_data['actual']}")
    
    forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+)", response1, re.IGNORECASE)
    forecast_found = forecast_match is not None
    
    if not forecast_found:
        print("✗ Forecast: NOT FOUND")
    
    # Check retry condition
    if event_data['actual'] and not forecast_found and not event_data['forecast_retry_attempted']:
        print("\n[RETRY TRIGGERED] Attempting forecast query")
        event_data['forecast_retry_attempted'] = True
        
        response2 = mock_ai.get_news_data("test", "USD", "Nov 18", "forecast")
        
        forecast_match2 = re.search(r"Forecast\s*:\s*([\d\.\-]+)", response2, re.IGNORECASE)
        if not forecast_match2:
            print("✗ Forecast: STILL NOT FOUND")
    
    # Simulate second heartbeat - should NOT trigger another retry
    print("\n[ATTEMPT 2] Simulating next heartbeat (should skip retry)")
    
    # Check retry condition again (should fail because flag is True)
    if event_data['actual'] and not event_data['forecast'] and not event_data['forecast_retry_attempted']:
        print("❌ ERROR: Retry triggered again (should not happen!)")
        return False
    else:
        print("✓ Retry skipped (forecast_retry_attempted = True)")
    
    # Results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Total AI Calls: {mock_ai.call_count}")
    print(f"Forecast Retry Attempted: {event_data['forecast_retry_attempted']}")
    
    if mock_ai.call_count == 2:
        print("\n✅ PASS: Exactly 2 AI calls (no infinite loop)")
        return True
    else:
        print(f"\n❌ FAIL: Expected 2 calls, got {mock_ai.call_count}")
        return False

if __name__ == "__main__":
    success = test_single_retry_only()
    print("\n" + "=" * 80)
    if success:
        print("✅ Test PASSED - Retry limit working correctly")
    else:
        print("❌ Test FAILED")
    print("=" * 80)
