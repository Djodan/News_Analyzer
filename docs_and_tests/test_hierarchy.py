#!/usr/bin/env python3
"""
Test script for find_available_pair_for_currency() with hierarchy.
Tests symbolsToTrade → _Symbols_ search order.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Globals
from Functions import find_available_pair_for_currency, update_currency_count

def print_separator():
    print("\n" + "="*60)

def reset_state():
    """Reset all currency counts and system variables."""
    for currency in Globals._CurrencyCount_:
        Globals._CurrencyCount_[currency] = 0
    Globals._Trades_ = {}
    Globals.system_news_event = False

def test_hierarchy_symbolsToTrade_only():
    """
    Test: EUR in symbolsToTrade (EURCHF available)
    news_filter_findAllPairs = False
    Expected: Find EURCHF from symbolsToTrade
    """
    print_separator()
    print("TEST 1: Search symbolsToTrade Only (Default)")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    Globals.news_filter_findAllPairs = False  # Only symbolsToTrade
    
    # Setup: XAUUSD and GBPCHF open
    print("\n📌 Setup:")
    print(f"   symbolsToTrade = {Globals.symbolsToTrade}")
    print(f"   news_filter_findAllPairs = {Globals.news_filter_findAllPairs}")
    
    print("\n   Opening: XAUUSD, GBPCHF")
    update_currency_count("XAUUSD", "add")   # XAU=1, USD=1
    update_currency_count("GBPCHF", "add")   # GBP=1, CHF=1
    
    # EUR news event
    print("\n🔔 EUR News Event")
    Globals.system_news_event = "EUR"
    
    print("\n🔍 Searching for EUR pair...")
    result = find_available_pair_for_currency("EUR")
    
    if result:
        print(f"\n✅ Result: {result}")
        print(f"   Should be from symbolsToTrade: {result in Globals.symbolsToTrade}")
    else:
        print("\n❌ No pair found")
    
    Globals.system_news_event = False

def test_hierarchy_expand_to_all_symbols():
    """
    Test: JPY NOT in symbolsToTrade, but USDJPY in _Symbols_
    news_filter_findAllPairs = False → Should fail
    news_filter_findAllPairs = True → Should find USDJPY
    """
    print_separator()
    print("TEST 2: Expand Search to All _Symbols_")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    
    print("\n📌 Setup:")
    print(f"   symbolsToTrade = {Globals.symbolsToTrade}")
    print("   (Note: No JPY pairs in symbolsToTrade)")
    print("\n   _Symbols_ contains: USDJPY, CADJPY (with JPY)")
    
    # JPY news event
    print("\n🔔 JPY News Event")
    Globals.system_news_event = "JPY"
    
    # Test A: news_filter_findAllPairs = False
    print("\n" + "-"*60)
    print("Test 2A: news_filter_findAllPairs = False")
    print("-"*60)
    Globals.news_filter_findAllPairs = False
    
    result = find_available_pair_for_currency("JPY")
    
    if result:
        print(f"\n❌ Unexpected: Found {result} (should not expand search)")
    else:
        print("\n✅ Correct: No pair found (only searched symbolsToTrade)")
    
    # Test B: news_filter_findAllPairs = True
    print("\n" + "-"*60)
    print("Test 2B: news_filter_findAllPairs = True")
    print("-"*60)
    Globals.news_filter_findAllPairs = True
    
    result = find_available_pair_for_currency("JPY")
    
    if result:
        print(f"\n✅ Correct: Found {result} from _Symbols_")
        print(f"   Is in _Symbols_: {result in Globals._Symbols_}")
        print(f"   Is in symbolsToTrade: {result in Globals.symbolsToTrade}")
    else:
        print("\n❌ Unexpected: Should have found JPY pair in _Symbols_")
    
    Globals.system_news_event = False

def test_hierarchy_priority_order():
    """
    Test: Add USDJPY to symbolsToTrade
    Verify it's found in Step 1 before searching _Symbols_
    """
    print_separator()
    print("TEST 3: Verify symbolsToTrade Priority")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    Globals.news_filter_findAllPairs = True
    
    # Temporarily add USDJPY to symbolsToTrade
    original_symbols = Globals.symbolsToTrade.copy()
    Globals.symbolsToTrade.add("USDJPY")
    
    print("\n📌 Setup:")
    print(f"   symbolsToTrade = {Globals.symbolsToTrade}")
    print(f"   news_filter_findAllPairs = {Globals.news_filter_findAllPairs}")
    
    # JPY news event
    print("\n🔔 JPY News Event")
    Globals.system_news_event = "JPY"
    
    print("\n🔍 Searching for JPY pair...")
    print("   Expected: Find USDJPY in Step 1 (symbolsToTrade)")
    print("   Should NOT reach Step 2 (_Symbols_)")
    
    result = find_available_pair_for_currency("JPY")
    
    if result == "USDJPY":
        print(f"\n✅ Correct: Found {result} in symbolsToTrade (Step 1)")
    else:
        print(f"\n❌ Unexpected: {result}")
    
    # Restore original
    Globals.symbolsToTrade = original_symbols
    Globals.system_news_event = False

def test_hierarchy_both_sources_at_limit():
    """
    Test: CHF at limit in both symbolsToTrade and _Symbols_
    Expected: None (no available pair anywhere)
    """
    print_separator()
    print("TEST 4: Currency at Limit Everywhere")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    Globals.news_filter_findAllPairs = True
    
    print("\n📌 Setup:")
    print("   Opening: NZDCHF, GBPCHF (CHF at 2/2 limit)")
    update_currency_count("NZDCHF", "add")  # NZD=1, CHF=1
    update_currency_count("GBPCHF", "add")  # GBP=1, CHF=2
    
    # CHF news event
    print("\n🔔 CHF News Event")
    Globals.system_news_event = "CHF"
    
    print("\n🔍 Searching for CHF pair...")
    print("   Expected: No pair found (CHF at limit everywhere)")
    
    result = find_available_pair_for_currency("CHF")
    
    if result is None:
        print("\n✅ Correct: No pair found (CHF fully exposed)")
    else:
        print(f"\n❌ Unexpected: Found {result} (CHF should be at limit)")
    
    Globals.system_news_event = False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("HIERARCHY TEST: symbolsToTrade → _Symbols_")
    print("="*60)
    
    test_hierarchy_symbolsToTrade_only()
    test_hierarchy_expand_to_all_symbols()
    test_hierarchy_priority_order()
    test_hierarchy_both_sources_at_limit()
    
    print_separator()
    print("✅ ALL HIERARCHY TESTS COMPLETED")
    print_separator()
    print()
