import sys
sys.path.insert(0, '..')

"""
Test STEP 6: Update _Affected_ and _Symbols_ dictionaries
Tests with manually injected data to ensure STEP 6 works correctly
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import update_affected_symbols

def display_dictionaries():
    """Display all three dictionaries"""
    print("\n" + "="*80)
    print("DICTIONARIES STATE:")
    print("="*80)
    
    print("\n_Currencies_:")
    if Globals._Currencies_:
        for currency, data in Globals._Currencies_.items():
            print(f"  {currency}:")
            print(f"    Date: {data.get('date')}")
            print(f"    Event: {data.get('event')}")
            print(f"    Forecast: {data.get('forecast')}")
            print(f"    Actual: {data.get('actual')}")
            print(f"    Affect: {data.get('affect')}")
    else:
        print("  (empty)")
    
    print("\n_Affected_:")
    if Globals._Affected_:
        for pair, data in Globals._Affected_.items():
            print(f"  {pair}:")
            print(f"    Date: {data.get('date')}")
            print(f"    Event: {data.get('event')}")
            print(f"    Position: {data.get('position')}")
    else:
        print("  (empty)")
    
    print("\n_Symbols_ (verdict_GPT field only):")
    if Globals._Symbols_:
        for pair, data in Globals._Symbols_.items():
            verdict = data.get('verdict_GPT', '')
            if verdict:  # Only show pairs with a verdict
                print(f"  {pair}: verdict_GPT = '{verdict}'")
        
        # Count how many have verdicts
        verdicts_count = sum(1 for data in Globals._Symbols_.values() if data.get('verdict_GPT'))
        if verdicts_count == 0:
            print("  (no verdicts set)")
    else:
        print("  (empty)")
    
    print("="*80 + "\n")

def main():
    print("="*80)
    print("TESTING STEP 6: Update _Affected_ and _Symbols_ (Manual Data)")
    print("="*80)
    
    # Manually populate _Currencies_ with test data
    print("\n[SETUP] Manually populating _Currencies_ with test data...")
    
    # EUR - BEAR scenario (unemployment increased)
    Globals._Currencies_["EUR"] = {
        "date": "2025, November 03, 04:10",
        "event": "(Austria) Unemployment Rate",
        "forecast": 7.0,
        "actual": 7.2,
        "affect": "BEAR",
        "retry_count": 0
    }
    
    # GBP - BULL scenario (PMI increased)
    Globals._Currencies_["GBP"] = {
        "date": "2025, November 03, 04:30",
        "event": "(United Kingdom) S&P Global Manufacturing PMI",
        "forecast": 49.6,
        "actual": 49.9,
        "affect": "BULL",
        "retry_count": 0
    }
    
    # USD - BEAR scenario (unemployment increased)
    Globals._Currencies_["USD"] = {
        "date": "2025, November 11, 08:15",
        "event": "(United States) ADP Employment Change",
        "forecast": 100.0,
        "actual": 95.0,
        "affect": "BEAR",
        "retry_count": 0
    }
    
    print("Populated 3 currencies with test data")
    
    # Display initial state
    print("\nBefore STEP 6:")
    display_dictionaries()
    
    # Test STEP 6 with EUR (BEAR - should generate SELL signals)
    print("\n" + "="*80)
    print("TEST 1: EUR BEAR (Unemployment increased)")
    print("="*80)
    
    eur_signals = {
        "EURAUD": "SELL",
        "EURNZD": "SELL",
        "EURUSD": "SELL"
    }
    
    print(f"\nCalling update_affected_symbols('EUR', {eur_signals})")
    update_affected_symbols("EUR", eur_signals)
    
    # Test STEP 6 with GBP (BULL - should generate BUY signals)
    print("\n" + "="*80)
    print("TEST 2: GBP BULL (PMI increased)")
    print("="*80)
    
    gbp_signals = {
        "GBPAUD": "BUY",
        "GBPNZD": "BUY"
    }
    
    print(f"\nCalling update_affected_symbols('GBP', {gbp_signals})")
    update_affected_symbols("GBP", gbp_signals)
    
    # Test STEP 6 with USD (BEAR - affects XAU and JPY pairs)
    print("\n" + "="*80)
    print("TEST 3: USD BEAR (Employment decreased)")
    print("="*80)
    
    usd_signals = {
        "XAUUSD": "BUY",  # Gold benefits from weak USD
        "USDJPY": "SELL"
    }
    
    print(f"\nCalling update_affected_symbols('USD', {usd_signals})")
    update_affected_symbols("USD", usd_signals)
    
    # Display final state
    print("\n" + "="*80)
    print("AFTER STEP 6:")
    display_dictionaries()
    
    # Verify results
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    affected_count = len(Globals._Affected_)
    symbols_verdicts = sum(1 for data in Globals._Symbols_.values() if data.get('verdict_GPT'))
    
    print(f"_Affected_ pairs: {affected_count}")
    print(f"_Symbols_ verdicts set: {symbols_verdicts}")
    
    # Expected results
    expected_affected = 7  # 3 EUR + 2 GBP + 2 USD
    expected_symbols = 7   # Same pairs should have verdicts
    
    print(f"\nExpected:")
    print(f"  _Affected_: {expected_affected} pairs")
    print(f"  _Symbols_ verdicts: {expected_symbols}")
    
    if affected_count == expected_affected and symbols_verdicts == expected_symbols:
        print("\n[OK] STEP 6 working correctly!")
        print(f"     - All {affected_count} pairs stored in _Affected_")
        print(f"     - All {symbols_verdicts} verdicts set in _Symbols_")
    else:
        print("\n[ERROR] STEP 6 verification failed")
        if affected_count != expected_affected:
            print(f"  - _Affected_: got {affected_count}, expected {expected_affected}")
        if symbols_verdicts != expected_symbols:
            print(f"  - _Symbols_ verdicts: got {symbols_verdicts}, expected {expected_symbols}")
    
    # Detailed verification
    print("\n" + "="*80)
    print("DETAILED VERIFICATION:")
    print("="*80)
    
    # Check EUR signals
    print("\nEUR signals:")
    for pair in ["EURAUD", "EURNZD", "EURUSD"]:
        affected_ok = pair in Globals._Affected_ and Globals._Affected_[pair]["position"] == "SELL"
        symbols_ok = pair in Globals._Symbols_ and Globals._Symbols_[pair]["verdict_GPT"] == "SELL"
        status = "[OK]" if (affected_ok and symbols_ok) else "[WRONG]"
        print(f"  {status} {pair}: _Affected_={affected_ok}, _Symbols_={symbols_ok}")
    
    # Check GBP signals
    print("\nGBP signals:")
    for pair in ["GBPAUD", "GBPNZD"]:
        affected_ok = pair in Globals._Affected_ and Globals._Affected_[pair]["position"] == "BUY"
        symbols_ok = pair in Globals._Symbols_ and Globals._Symbols_[pair]["verdict_GPT"] == "BUY"
        status = "[OK]" if (affected_ok and symbols_ok) else "[WRONG]"
        print(f"  {status} {pair}: _Affected_={affected_ok}, _Symbols_={symbols_ok}")
    
    # Check USD signals
    print("\nUSD signals:")
    for pair, expected_action in [("XAUUSD", "BUY"), ("USDJPY", "SELL")]:
        affected_ok = pair in Globals._Affected_ and Globals._Affected_[pair]["position"] == expected_action
        symbols_ok = pair in Globals._Symbols_ and Globals._Symbols_[pair]["verdict_GPT"] == expected_action
        status = "[OK]" if (affected_ok and symbols_ok) else "[WRONG]"
        print(f"  {status} {pair}: _Affected_={affected_ok}, _Symbols_={symbols_ok}")

if __name__ == "__main__":
    main()
