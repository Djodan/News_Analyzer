"""
Isolated Test: ChatGPT Trading Signal Generation (STEP 5 + 6)
Tests that ChatGPT properly generates trading decisions and populates _Affected_
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, '..')

import Globals
from News import calculate_affect, generate_trading_decisions, update_affected_symbols

def test_scenario(currency, event_name, forecast, actual, expected_affect, description):
    """Test a single scenario"""
    print("\n" + "="*80)
    print(f"SCENARIO: {description}")
    print("="*80)
    
    # Clear previous state
    Globals._Currencies_.clear()
    Globals._Affected_.clear()
    for pair in Globals._Symbols_:
        Globals._Symbols_[pair]["verdict_GPT"] = ""
    
    # Populate _Currencies_ with test data
    Globals._Currencies_[currency] = {
        "date": "2025, November 03, 04:10",
        "event": event_name,
        "forecast": forecast,
        "actual": actual,
        "affect": None,
        "retry_count": 0
    }
    
    print(f"\nInput:")
    print(f"  Currency: {currency}")
    print(f"  Event: {event_name}")
    print(f"  Forecast: {forecast}")
    print(f"  Actual: {actual}")
    print(f"  Expected Affect: {expected_affect}")
    
    # STEP 4A: Calculate affect
    print(f"\n[STEP 4A] Calculating affect...")
    calculate_affect(currency)
    
    calculated_affect = Globals._Currencies_[currency]['affect']
    print(f"  Calculated: {calculated_affect}")
    
    if calculated_affect != expected_affect:
        print(f"  [ERROR] Expected {expected_affect}, got {calculated_affect}")
        return False
    
    # STEP 5: Generate trading signals
    print(f"\n[STEP 5] Generating trading signals via ChatGPT...")
    trading_signals = generate_trading_decisions(currency)
    
    print(f"  Signals returned: {trading_signals}")
    
    # STEP 6: Update dictionaries
    print(f"\n[STEP 6] Updating _Affected_ and _Symbols_...")
    update_affected_symbols(currency, trading_signals)
    
    # Display results
    print(f"\nResults:")
    print(f"  _Affected_ pairs: {len(Globals._Affected_)}")
    for pair, data in Globals._Affected_.items():
        print(f"    {pair}: {data.get('position')}")
    
    verdicts = {pair: data.get('verdict_GPT', '') for pair, data in Globals._Symbols_.items() if data.get('verdict_GPT')}
    print(f"  _Symbols_ verdicts: {len(verdicts)}")
    for pair, verdict in verdicts.items():
        print(f"    {pair}: {verdict}")
    
    success = len(Globals._Affected_) > 0
    if success:
        print(f"\n[SUCCESS] Generated {len(Globals._Affected_)} trading signal(s)")
    else:
        print(f"\n[WARNING] No trading signals generated")
    
    return success

def main():
    print("="*80)
    print("ISOLATED TEST: ChatGPT Trading Signal Generation")
    print("="*80)
    print("\nThis test focuses on STEP 5 & 6:")
    print("  - Generate trading signals via ChatGPT")
    print("  - Update _Affected_ dictionary with signals")
    print("\nUsing fresh ChatGPT prompts for each scenario")
    
    results = []
    
    # Test 1: EUR BEAR (Unemployment increased)
    results.append(test_scenario(
        currency="EUR",
        event_name="(Austria) Unemployment Rate",
        forecast=7.0,
        actual=7.5,  # Higher unemployment = BEAR
        expected_affect="BEAR",
        description="EUR BEAR - Unemployment Increased (7.0 → 7.5)"
    ))
    
    # Test 2: GBP BULL (PMI increased)
    results.append(test_scenario(
        currency="GBP",
        event_name="(United Kingdom) S&P Global Manufacturing PMI",
        forecast=49.6,
        actual=51.2,  # Higher PMI = BULL
        expected_affect="BULL",
        description="GBP BULL - PMI Increased (49.6 → 51.2)"
    ))
    
    # Test 3: USD BEAR (Employment decreased)
    results.append(test_scenario(
        currency="USD",
        event_name="(United States) Non-Farm Payrolls",
        forecast=200.0,
        actual=150.0,  # Lower employment = BEAR
        expected_affect="BEAR",
        description="USD BEAR - Employment Decreased (200.0 → 150.0)"
    ))
    
    # Test 4: JPY BULL (GDP increased)
    results.append(test_scenario(
        currency="JPY",
        event_name="(Japan) GDP Growth Rate",
        forecast=0.5,
        actual=1.2,  # Higher GDP = BULL
        expected_affect="BULL",
        description="JPY BULL - GDP Increased (0.5 → 1.2)"
    ))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nScenarios passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All scenarios generated trading signals correctly!")
        print("          ChatGPT is properly interpreting News_Rules.txt")
        print("          _Affected_ dictionary is being populated")
    else:
        print(f"\n[WARNING] {total - passed} scenario(s) did not generate signals")
        print("          This could indicate:")
        print("          - ChatGPT returned NEUTRAL")
        print("          - Response parsing failed")
        print("          - News_Rules.txt not being applied correctly")

if __name__ == "__main__":
    main()
