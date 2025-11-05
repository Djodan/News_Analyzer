"""
Test STEP 6: Update _Affected_ and _Symbols_ dictionaries
Tests that trading signals are properly stored in both dictionaries
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import initialize_news_forecasts, fetch_actual_value

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
            print(f"    Retry Count: {data.get('retry_count', 0)}")
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
    print("TESTING STEP 6: Update _Affected_ and _Symbols_")
    print("="*80)
    
    # Set test mode to process only past events
    Globals.news_test_mode = True
    Globals.csv_count = 2  # Process 2 events
    
    print("\n[SETUP] Test mode: Process ONLY past events")
    print(f"[SETUP] CSV count limit: {Globals.csv_count}")
    
    # Initialize forecasts
    print("\n[STEP 1] Initializing forecasts...")
    initialize_news_forecasts()
    
    print(f"\nLoaded {len(Globals._Currencies_)} currency events")
    
    # Display initial state
    print("\nBefore processing:")
    display_dictionaries()
    
    # Process each currency
    print("\n" + "="*80)
    print("PROCESSING EVENTS:")
    print("="*80)
    
    for currency in list(Globals._Currencies_.keys()):
        print(f"\n{'='*80}")
        print(f"PROCESSING: {currency}")
        print(f"{'='*80}")
        
        # Fetch actual (includes STEP 3, 4A, 5, 6)
        success = fetch_actual_value(currency)
        
        if success:
            print(f"\n[OK] Successfully processed {currency}")
        else:
            print(f"\n[FAILED] Could not process {currency}")
    
    # Display final state
    print("\n" + "="*80)
    print("AFTER PROCESSING:")
    display_dictionaries()
    
    # Verify results
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    affected_count = len(Globals._Affected_)
    symbols_verdicts = sum(1 for data in Globals._Symbols_.values() if data.get('verdict_GPT'))
    
    print(f"_Affected_ pairs: {affected_count}")
    print(f"_Symbols_ verdicts set: {symbols_verdicts}")
    
    if affected_count > 0 and symbols_verdicts > 0:
        print("\n[OK] STEP 6 working correctly!")
        print(f"     - {affected_count} pair(s) stored in _Affected_")
        print(f"     - {symbols_verdicts} verdict(s) set in _Symbols_")
    else:
        print("\n[ERROR] STEP 6 may have issues")
        if affected_count == 0:
            print("  - _Affected_ is empty")
        if symbols_verdicts == 0:
            print("  - No verdicts set in _Symbols_")

if __name__ == "__main__":
    main()
