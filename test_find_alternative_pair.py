#!/usr/bin/env python3
"""
Test script for find_available_pair_for_currency() function.
Demonstrates the alternative pair finding logic for news events.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Globals
from Functions import find_available_pair_for_currency, update_currency_count, extract_currencies

def print_separator():
    print("\n" + "="*60)

def print_currency_counts():
    print("\n📊 Current Currency Counts:")
    for currency, count in Globals._CurrencyCount_.items():
        if count > 0:
            print(f"  {currency}: {count}/{Globals.news_filter_maxTradePerCurrency}")

def reset_state():
    """Reset all currency counts and system variables."""
    for currency in Globals._CurrencyCount_:
        Globals._CurrencyCount_[currency] = 0
    Globals._Trades_ = {}
    Globals.system_news_event = False

def test_scenario_1():
    """
    Scenario 1: EUR news event, EURUSD rejected (USD at limit)
    Expected: Find EURCHF or EURNZD as alternative
    """
    print_separator()
    print("TEST 1: EUR News Event - EURUSD Rejected")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    
    # Simulate existing positions: XAUUSD, GBPUSD (USD at limit)
    print("\n📌 Setup: Opening XAUUSD and GBPUSD")
    update_currency_count("XAUUSD", "add")  # XAU=1, USD=1
    update_currency_count("GBPUSD", "add")  # GBP=1, USD=2
    
    print_currency_counts()
    
    # EUR news event occurs
    print("\n🔔 EUR News Event Detected")
    Globals.system_news_event = "EUR"
    print(f"   system_news_event = '{Globals.system_news_event}'")
    
    # Try to find alternative pair for EUR
    print("\n🔍 EURUSD would be rejected (USD at 2/2)")
    print("   Searching for alternative pair...")
    
    alternative = find_available_pair_for_currency("EUR")
    
    if alternative:
        print(f"\n✅ Result: Use {alternative} instead")
        currencies = extract_currencies(alternative)
        print(f"   Currencies in {alternative}: {currencies}")
    else:
        print("\n❌ Result: No alternative found")
    
    # Cleanup
    Globals.system_news_event = False
    print(f"\n🧹 Cleanup: system_news_event = {Globals.system_news_event}")

def test_scenario_2():
    """
    Scenario 2: CHF news event, all CHF pairs at limit
    Expected: No alternative found (return None)
    """
    print_separator()
    print("TEST 2: CHF News Event - All CHF Pairs at Limit")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    
    # Simulate: CHF already at limit in 2 pairs
    print("\n📌 Setup: Opening NZDCHF and GBPCHF")
    update_currency_count("NZDCHF", "add")  # NZD=1, CHF=1
    update_currency_count("GBPCHF", "add")  # GBP=1, CHF=2
    
    print_currency_counts()
    
    # CHF news event occurs
    print("\n🔔 CHF News Event Detected")
    Globals.system_news_event = "CHF"
    print(f"   system_news_event = '{Globals.system_news_event}'")
    
    # Try to find alternative pair for CHF
    print("\n🔍 All CHF pairs would be rejected (CHF at 2/2)")
    print("   Searching for alternative pair...")
    
    alternative = find_available_pair_for_currency("CHF")
    
    if alternative:
        print(f"\n✅ Result: Use {alternative} instead")
    else:
        print("\n❌ Result: No alternative found (CHF fully exposed)")
    
    # Cleanup
    Globals.system_news_event = False
    print(f"\n🧹 Cleanup: system_news_event = {Globals.system_news_event}")

def test_scenario_3():
    """
    Scenario 3: USD news event, multiple options available
    Expected: Find first valid USD pair (e.g., USDJPY)
    """
    print_separator()
    print("TEST 3: USD News Event - Multiple Alternatives Available")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    
    # Simulate: Only EUR and GBP have counts, USD is free
    print("\n📌 Setup: Opening EURCHF and GBPAUD")
    update_currency_count("EURCHF", "add")  # EUR=1, CHF=1
    update_currency_count("GBPAUD", "add")  # GBP=1, AUD=1
    
    print_currency_counts()
    
    # USD news event occurs
    print("\n🔔 USD News Event Detected")
    Globals.system_news_event = "USD"
    print(f"   system_news_event = '{Globals.system_news_event}'")
    
    # Try to find alternative pair for USD
    print("\n🔍 Searching for USD pair...")
    
    alternative = find_available_pair_for_currency("USD")
    
    if alternative:
        print(f"\n✅ Result: Use {alternative}")
        currencies = extract_currencies(alternative)
        print(f"   Currencies in {alternative}: {currencies}")
        for curr in currencies:
            count = Globals._CurrencyCount_.get(curr, 0)
            print(f"   {curr} exposure: {count}/2")
    else:
        print("\n❌ Result: No alternative found")
    
    # Cleanup
    Globals.system_news_event = False
    print(f"\n🧹 Cleanup: system_news_event = {Globals.system_news_event}")

def test_workflow_simulation():
    """
    Simulate complete news trading workflow with fallback logic.
    """
    print_separator()
    print("TEST 4: Complete News Trading Workflow Simulation")
    print_separator()
    
    reset_state()
    Globals.news_filter_maxTradePerCurrency = 2
    Globals.news_filter_findAvailablePair = True
    
    # Setup existing positions
    print("\n📌 Initial State: XAUUSD and EURUSD open")
    update_currency_count("XAUUSD", "add")   # XAU=1, USD=1
    update_currency_count("EURUSD", "add")   # EUR=1, USD=2 (at limit)
    print_currency_counts()
    
    # Simulate EUR news event
    print("\n" + "="*60)
    print("EUR NEWS EVENT: Unemployment Rate Better Than Expected")
    print("="*60)
    
    Globals.system_news_event = "EUR"
    print(f"\n1️⃣  Set system_news_event = '{Globals.system_news_event}'")
    
    # Try primary affected pair
    primary_pair = "EURUSD"
    print(f"\n2️⃣  Try primary affected pair: {primary_pair}")
    
    from Functions import can_open_trade
    if can_open_trade(primary_pair):
        print(f"   ✅ {primary_pair} accepted - opening trade")
        trade_opened = True
    else:
        print(f"   ❌ {primary_pair} rejected by filters")
        
        # Check if alternative search is enabled
        if Globals.news_filter_findAvailablePair and Globals.system_news_event:
            print(f"\n3️⃣  Alternative pair search enabled")
            print(f"   system_news_event = '{Globals.system_news_event}'")
            
            alternative = find_available_pair_for_currency(Globals.system_news_event)
            
            if alternative:
                print(f"\n4️⃣  ✅ Opening alternative pair: {alternative}")
                update_currency_count(alternative, "add")
                trade_opened = True
                print_currency_counts()
            else:
                print(f"\n4️⃣  ❌ No alternative pair found - trade skipped")
                trade_opened = False
    
    # Cleanup
    print(f"\n5️⃣  Cleanup: Reset system_news_event")
    Globals.system_news_event = False
    print(f"   system_news_event = {Globals.system_news_event}")
    
    print("\n" + "="*60)
    print("Workflow Complete")
    print("="*60)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ALTERNATIVE PAIR FINDER TESTS")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  news_filter_maxTradePerCurrency = 2")
    print(f"  news_filter_findAvailablePair = True")
    
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    test_workflow_simulation()
    
    print_separator()
    print("✅ ALL TESTS COMPLETED")
    print_separator()
    print()
