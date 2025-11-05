"""
Test alternative pair finder in a live scenario.
Simulates News algorithm behavior: Primary pair rejected → Find alternative.
"""

import sys
import Globals
from Functions import can_open_trade, update_currency_count, find_available_pair_for_currency

def simulate_news_algorithm():
    """
    Simulate News algorithm with alternative finder.
    
    Scenario:
    - JPY news event occurs
    - Primary affected pair is USDJPY
    - But USD is at limit (2/2) from previous trades, JPY is NOT at limit
    - USDJPY gets rejected due to USD limit
    - Alternative finder searches for another JPY pair without USD
    - Should find CADJPY in _Symbols_ (Step 2) ✅
    """
    print("\n" + "=" * 80)
    print("ALTERNATIVE PAIR FINDER - NEWS ALGORITHM SIMULATION")
    print("=" * 80)
    
    print("\n📋 Configuration:")
    print(f"  symbolsToTrade: {Globals.symbolsToTrade}")
    print(f"  news_filter_maxTradePerCurrency: {Globals.news_filter_maxTradePerCurrency}")
    print(f"  news_filter_findAvailablePair: {Globals.news_filter_findAvailablePair}")
    print(f"  news_filter_findAllPairs: {Globals.news_filter_findAllPairs}")
    print(f"  system_news_event: {Globals.system_news_event}")
    
    print("\n" + "=" * 80)
    print("STEP 1: Simulate previous trades (pre-fill USD to limit, NOT JPY)")
    print("=" * 80)
    
    # Reset currency counts
    for currency in Globals._CurrencyCount_:
        Globals._CurrencyCount_[currency] = 0
    
    # Simulate that USD is at limit from previous non-JPY trades
    print("\n💼 Simulating existing positions:")
    print("   - EURUSD (EUR: 1, USD: 1)")
    print("   - GBPUSD (GBP: 1, USD: 2) ← USD at limit")
    update_currency_count("EURUSD", "add")
    update_currency_count("GBPUSD", "add")
    print(f"📊 Currency counts after simulation: {Globals._CurrencyCount_}")
    print(f"   ⚠️  USD at limit (2/2), but JPY still free (0/2)")
    
    print("\n" + "=" * 80)
    print("STEP 2: JPY News Event Occurs")
    print("=" * 80)
    
    # News algorithm determines USDJPY is the primary affected pair
    primary_pair = "USDJPY"
    print(f"\n📰 JPY news event detected!")
    print(f"🎯 Primary affected pair: {primary_pair}")
    print(f"   (Contains JPY which is news currency, and USD which is at limit)")
    
    print(f"\n🔄 Attempting to open primary pair: {primary_pair}...")
    
    if can_open_trade(primary_pair):
        print(f"  ✅ Filter passed - Opening {primary_pair}")
        update_currency_count(primary_pair, "add")
        primary_opened = True
    else:
        print(f"  ❌ Filter rejected - Cannot open {primary_pair}")
        print(f"  Reason: USD at limit ({Globals._CurrencyCount_['USD']}/{Globals.news_filter_maxTradePerCurrency})")
        print(f"         (JPY is free: {Globals._CurrencyCount_['JPY']}/{Globals.news_filter_maxTradePerCurrency})")
        primary_opened = False
    
    print("\n" + "=" * 80)
    print("STEP 3: Alternative Pair Finder")
    print("=" * 80)
    
    if not primary_opened and Globals.system_news_event and Globals.news_filter_findAvailablePair:
        currency = Globals.system_news_event
        print(f"\n🔍 Primary pair rejected! Activating alternative finder for currency: {currency}")
        
        alternative = find_available_pair_for_currency(currency)
        
        if alternative:
            print(f"\n✅ ALTERNATIVE FOUND: {alternative}")
            print(f"   Verifying with can_open_trade()...")
            
            if can_open_trade(alternative):
                print(f"   ✅ Filter passed - Opening {alternative}")
                update_currency_count(alternative, "add")
                print(f"   📊 Currency counts: {Globals._CurrencyCount_}")
                alternative_opened = True
            else:
                print(f"   ❌ Filter rejected - Cannot open {alternative}")
                alternative_opened = False
        else:
            print(f"\n❌ NO ALTERNATIVE FOUND")
            print(f"   All {currency} pairs are at limit or unavailable")
            alternative_opened = False
    else:
        print("\n⚠️  Alternative finder not activated")
        if primary_opened:
            print("   Reason: Primary pair was successfully opened")
        if not Globals.system_news_event:
            print("   Reason: system_news_event not set")
        if not Globals.news_filter_findAvailablePair:
            print("   Reason: news_filter_findAvailablePair disabled")
        alternative_opened = False
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    print(f"\n📊 Summary:")
    print(f"   Primary pair ({primary_pair}): {'✅ OPENED' if primary_opened else '❌ REJECTED'}")
    print(f"   Alternative pair: {'✅ OPENED' if alternative_opened else '❌ NOT OPENED'}")
    
    print(f"\n💰 Final currency counts:")
    for currency, count in Globals._CurrencyCount_.items():
        if count > 0:
            limit = Globals.news_filter_maxTradePerCurrency
            status = "AT LIMIT" if count >= limit else f"{count}/{limit}"
            print(f"   {currency}: {count} ({status})")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    print("\n🎯 Expected outcome:")
    print("   1. Pre-existing: EURUSD + GBPUSD (USD: 2/2, EUR: 1, GBP: 1)")
    print("   2. News event: JPY news → Primary USDJPY → REJECTED (USD at limit, but JPY free)")
    print("   3. Alternative finder:")
    print("      - Step 1: Search symbolsToTrade (USDJPY only) → Contains USD, rejected")
    print("      - Step 2: Expand to _Symbols_ → Find CADJPY ✅ (CAD + JPY, no USD)")
    print("   4. Result: CADJPY opened (CAD: 1, JPY: 1, USD still 2)")
    print("\n💡 Key insight: Alternative finder finds pairs with target currency (JPY)")
    print("   that DON'T contain the limiting currency (USD)")
    
    if alternative_opened:
        print("\n✅ SUCCESS: Alternative finder worked!")
        return 0
    else:
        print("\n❌ FAILED: Alternative not opened")
        return 1


if __name__ == "__main__":
    exit_code = simulate_news_algorithm()
    sys.exit(exit_code)
