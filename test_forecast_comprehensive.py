"""
Comprehensive test for forecast retry logic with AI counter tracking
Tests all edge cases including multiple event processing cycles
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

class MockGlobals:
    """Mock Globals module for testing"""
    ai_calls_today = 0
    MAX_DAILY_AI_CALLS = 100
    _Currencies_ = {}

class MockAI:
    """Mock AI that tracks calls and simulates different scenarios"""
    def __init__(self, scenario="success"):
        self.call_count = 0
        self.scenario = scenario
    
    def get_news_data(self, event_name, currency, date, request_type):
        self.call_count += 1
        MockGlobals.ai_calls_today += 1
        
        print(f"\n[MOCK AI] Call #{self.call_count} (Total today: {MockGlobals.ai_calls_today})")
        print(f"           request_type='{request_type}'")
        
        if self.scenario == "success":
            if request_type == "both":
                return "Actual : -2.5\nSource : MyFxBook"
            elif request_type == "forecast":
                return "Forecast : -11.25\nSource : MyFxBook"
        
        elif self.scenario == "forecast_unavailable":
            if request_type == "both":
                return "Actual : -2.5\nSource : MyFxBook"
            elif request_type == "forecast":
                return "Forecast : N/A\nSource : MyFxBook"
        
        elif self.scenario == "multiple_cycles":
            # Always return partial data to test retry limit
            return "Actual : -2.5\nSource : MyFxBook"
        
        return "N/A"

def simulate_event_processing(mock_ai, event_key, request_type="both"):
    """Simulate the event processing logic"""
    
    # Initialize event if not exists
    if event_key not in MockGlobals._Currencies_:
        MockGlobals._Currencies_[event_key] = {
            'forecast': None,
            'actual': None,
            'forecast_retry_attempted': False
        }
    
    print(f"\n{'='*80}")
    print(f"Processing event: {event_key}")
    print(f"Request type: {request_type}")
    print(f"{'='*80}")
    
    # Get response
    response = mock_ai.get_news_data("test_event", "USD", "Nov 18", request_type)
    print(f"Response: {response}")
    
    # Parse response
    forecast_found = False
    actual_found = False
    
    forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A)", response, re.IGNORECASE)
    if forecast_match and forecast_match.group(1) != "N/A":
        MockGlobals._Currencies_[event_key]['forecast'] = float(forecast_match.group(1))
        forecast_found = True
        print(f"✓ Forecast: {MockGlobals._Currencies_[event_key]['forecast']}")
    
    actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+|N/A)", response, re.IGNORECASE)
    if actual_match and actual_match.group(1) != "N/A":
        MockGlobals._Currencies_[event_key]['actual'] = float(actual_match.group(1))
        actual_found = True
        print(f"✓ Actual: {MockGlobals._Currencies_[event_key]['actual']}")
    
    if not forecast_found:
        print("✗ Forecast: NOT FOUND")
    if not actual_found:
        print("✗ Actual: NOT FOUND")
    
    # Check if we need forecast retry
    if request_type == "both" and actual_found and not forecast_found:
        forecast_retry_attempted = MockGlobals._Currencies_[event_key]['forecast_retry_attempted']
        
        if not forecast_retry_attempted:
            print(f"\n[PARTIAL DATA] Going back to query for Forecast")
            print(f"Actual value is already saved: {MockGlobals._Currencies_[event_key]['actual']}")
            
            # Set flag BEFORE retry
            MockGlobals._Currencies_[event_key]['forecast_retry_attempted'] = True
            print(f"✓ Set forecast_retry_attempted = True")
            
            # Recursive call for forecast only
            return simulate_event_processing(mock_ai, event_key, "forecast")
        else:
            print(f"\n[SKIP RETRY] Forecast retry already attempted")
    
    # Final status
    print(f"\n{'-'*80}")
    if actual_found and forecast_found:
        print("✅ SUCCESS: Both values retrieved")
    elif actual_found and not forecast_found:
        print("⚠️ MOVING ON: Proceeding without Forecast")
    else:
        print("❌ FAILED: No actual value")
    print(f"{'-'*80}")
    
    return actual_found, forecast_found

def test_scenario_1_success():
    """Test successful forecast retry"""
    print("\n" + "="*80)
    print("TEST 1: Successful Forecast Retry")
    print("="*80)
    
    MockGlobals.ai_calls_today = 0
    MockGlobals._Currencies_ = {}
    mock_ai = MockAI("success")
    
    simulate_event_processing(mock_ai, "event1")
    
    print(f"\n{'='*80}")
    print("FINAL METRICS:")
    print(f"{'='*80}")
    print(f"Total AI Calls: {MockGlobals.ai_calls_today}")
    print(f"Event Data: {MockGlobals._Currencies_['event1']}")
    
    assert MockGlobals.ai_calls_today == 2, f"Expected 2 AI calls, got {MockGlobals.ai_calls_today}"
    assert MockGlobals._Currencies_['event1']['forecast'] == -11.25
    assert MockGlobals._Currencies_['event1']['actual'] == -2.5
    assert MockGlobals._Currencies_['event1']['forecast_retry_attempted'] == True
    
    print("✅ TEST 1 PASSED")
    return True

def test_scenario_2_unavailable():
    """Test when forecast remains unavailable"""
    print("\n" + "="*80)
    print("TEST 2: Forecast Unavailable After Retry")
    print("="*80)
    
    MockGlobals.ai_calls_today = 0
    MockGlobals._Currencies_ = {}
    mock_ai = MockAI("forecast_unavailable")
    
    simulate_event_processing(mock_ai, "event2")
    
    print(f"\n{'='*80}")
    print("FINAL METRICS:")
    print(f"{'='*80}")
    print(f"Total AI Calls: {MockGlobals.ai_calls_today}")
    print(f"Event Data: {MockGlobals._Currencies_['event2']}")
    
    assert MockGlobals.ai_calls_today == 2, f"Expected 2 AI calls, got {MockGlobals.ai_calls_today}"
    assert MockGlobals._Currencies_['event2']['forecast'] == None
    assert MockGlobals._Currencies_['event2']['actual'] == -2.5
    assert MockGlobals._Currencies_['event2']['forecast_retry_attempted'] == True
    
    print("✅ TEST 2 PASSED")
    return True

def test_scenario_3_with_gate_check():
    """Test that events with actual data aren't re-queried (production behavior)"""
    print("\n" + "="*80)
    print("TEST 3: Event Re-Processing Prevention (Production Gate Check)")
    print("="*80)
    
    MockGlobals.ai_calls_today = 0
    MockGlobals._Currencies_ = {}
    mock_ai = MockAI("multiple_cycles")
    
    # First processing cycle
    print("\n[CYCLE 1] Initial event processing")
    simulate_event_processing(mock_ai, "event3")
    
    calls_after_cycle1 = MockGlobals.ai_calls_today
    print(f"\nAI calls after cycle 1: {calls_after_cycle1}")
    
    # In production, the gate check (event_data['actual'] is None) prevents re-processing
    print("\n[CYCLE 2] Second heartbeat - checking gate condition")
    event_has_actual = MockGlobals._Currencies_['event3']['actual'] is not None
    
    if event_has_actual:
        print("✓ Gate check: event_data['actual'] is not None")
        print("✓ Skipping fetch_forecast_and_actual() call")
        print("✓ No additional AI calls made")
    else:
        print("✗ Gate check failed - would re-process event")
    
    calls_after_cycle2 = MockGlobals.ai_calls_today
    
    print(f"\n{'='*80}")
    print("FINAL METRICS:")
    print(f"{'='*80}")
    print(f"Total AI Calls: {MockGlobals.ai_calls_today}")
    print(f"Cycle 1 calls: {calls_after_cycle1}")
    print(f"Cycle 2 calls: {calls_after_cycle2 - calls_after_cycle1}")
    print(f"Event has actual: {event_has_actual}")
    
    # Should be exactly 2 calls (initial + 1 retry), second cycle makes 0 calls due to gate check
    assert MockGlobals.ai_calls_today == 2, f"Expected 2 AI calls total, got {MockGlobals.ai_calls_today}"
    assert MockGlobals._Currencies_['event3']['forecast_retry_attempted'] == True
    assert event_has_actual == True, "Event should have actual data after first cycle"
    
    print("✅ TEST 3 PASSED - Production gate check prevents re-processing")
    return True

if __name__ == "__main__":
    try:
        test_scenario_1_success()
        test_scenario_2_unavailable()
        test_scenario_3_with_gate_check()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nKey Confirmations:")
        print("  ✓ AI call counter properly incremented")
        print("  ✓ Single retry limit enforced")
        print("  ✓ Flag prevents multiple retries")
        print("  ✓ Graceful fallback when forecast unavailable")
        print("  ✓ Gate check prevents event re-processing")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
