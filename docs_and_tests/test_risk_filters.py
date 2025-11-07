#!/usr/bin/env python3
"""
Test script for risk management filter functions.
Demonstrates extract_currencies(), update_currency_count(), and can_open_trade().
"""

# Direct imports to avoid running Server.py
from typing import List

# Mock Globals module
class MockGlobals:
    _CurrencyCount_ = {
        "XAU": 0,
        "EUR": 0,
        "USD": 0,
        "JPY": 0,
        "CHF": 0,
        "NZD": 0,
        "CAD": 0,
        "GBP": 0,
        "AUD": 0,
        "BTC": 0
    }
    _Trades_ = {}
    news_filter_maxTrades = 0
    news_filter_maxTradePerCurrency = 0

# Copy functions directly to avoid imports
def extract_currencies(symbol: str) -> List[str]:
    """Extract individual currencies from a trading symbol."""
    currencies = []
    known_currencies = ["XAU", "EUR", "USD", "JPY", "CHF", "NZD", "CAD", "GBP", "AUD", "BTC"]
    
    if "BITCOIN" in symbol.upper():
        return ["BTC"]
    if "ETHEREUM" in symbol.upper():
        return ["BTC"]
    if "LITECOIN" in symbol.upper():
        return ["BTC"]
    if "DOGECOIN" in symbol.upper():
        return ["BTC"]
    
    for currency in known_currencies:
        if currency in symbol.upper():
            currencies.append(currency)
    
    return currencies

def update_currency_count(symbol: str, operation: str) -> None:
    """Update the _CurrencyCount_ dictionary when opening or closing a trade."""
    currencies = extract_currencies(symbol)
    
    for currency in currencies:
        if currency in MockGlobals._CurrencyCount_:
            if operation == "add":
                MockGlobals._CurrencyCount_[currency] += 1
                print(f"[CURRENCY COUNT] {currency} → {MockGlobals._CurrencyCount_[currency]} (added {symbol})")
            elif operation == "remove":
                MockGlobals._CurrencyCount_[currency] = max(0, MockGlobals._CurrencyCount_[currency] - 1)
                print(f"[CURRENCY COUNT] {currency} → {MockGlobals._CurrencyCount_[currency]} (removed {symbol})")

def can_open_trade(symbol: str) -> bool:
    """Check if a trade can be opened based on risk management filters."""
    # Check 1: Maximum total trades
    if MockGlobals.news_filter_maxTrades > 0:
        current_total_trades = len(MockGlobals._Trades_)
        if current_total_trades >= MockGlobals.news_filter_maxTrades:
            print(f"[FILTER REJECT] Cannot open {symbol}: Max trades limit reached ({current_total_trades}/{MockGlobals.news_filter_maxTrades})")
            return False
    
    # Check 2: Maximum trades per currency
    if MockGlobals.news_filter_maxTradePerCurrency > 0:
        currencies = extract_currencies(symbol)
        
        for currency in currencies:
            current_count = MockGlobals._CurrencyCount_.get(currency, 0)
            
            if current_count >= MockGlobals.news_filter_maxTradePerCurrency:
                print(f"[FILTER REJECT] Cannot open {symbol}: Currency {currency} at max limit ({current_count}/{MockGlobals.news_filter_maxTradePerCurrency})")
                return False
    
    return True

def print_separator():
    print("\n" + "="*60)

def test_extract_currencies():
    print_separator()
    print("TEST 1: extract_currencies()")
    print_separator()
    
    test_symbols = ["GBPJPY", "EURUSD", "XAUUSD", "AUDCAD", "BITCOIN", "NZDCHF"]
    
    for symbol in test_symbols:
        currencies = extract_currencies(symbol)
        print(f"{symbol:12} → {currencies}")

def test_currency_counting():
    print_separator()
    print("TEST 2: update_currency_count()")
    print_separator()
    
    # Reset counts
    for currency in MockGlobals._CurrencyCount_:
        MockGlobals._CurrencyCount_[currency] = 0
    
    print("\nOpening EURUSD...")
    update_currency_count("EURUSD", "add")
    
    print("\nOpening GBPJPY...")
    update_currency_count("GBPJPY", "add")
    
    print("\nOpening CADJPY...")
    update_currency_count("CADJPY", "add")
    
    print("\n📊 Current Currency Counts:")
    for currency, count in MockGlobals._CurrencyCount_.items():
        if count > 0:
            print(f"  {currency}: {count}")
    
    print("\nClosing GBPJPY...")
    update_currency_count("GBPJPY", "remove")
    
    print("\n📊 Updated Currency Counts:")
    for currency, count in MockGlobals._CurrencyCount_.items():
        if count > 0:
            print(f"  {currency}: {count}")

def test_can_open_trade():
    print_separator()
    print("TEST 3: can_open_trade() - Max Total Trades")
    print_separator()
    
    # Reset
    for currency in MockGlobals._CurrencyCount_:
        MockGlobals._CurrencyCount_[currency] = 0
    MockGlobals._Trades_ = {}
    
    # Set max trades to 2
    MockGlobals.news_filter_maxTrades = 2
    MockGlobals.news_filter_maxTradePerCurrency = 0  # Disable currency limit
    
    print(f"\nFilter Settings:")
    print(f"  news_filter_maxTrades = {MockGlobals.news_filter_maxTrades}")
    print(f"  news_filter_maxTradePerCurrency = {MockGlobals.news_filter_maxTradePerCurrency}")
    
    # Simulate 2 trades
    MockGlobals._Trades_["TID_1_1"] = {"symbol": "EURUSD"}
    MockGlobals._Trades_["TID_1_2"] = {"symbol": "GBPJPY"}
    
    print(f"\nCurrent open trades: {len(MockGlobals._Trades_)}")
    
    print("\nAttempting to open XAUUSD:")
    result = can_open_trade("XAUUSD")
    print(f"Result: {'✅ ALLOWED' if result else '❌ REJECTED'}")

def test_can_open_trade_currency_limit():
    print_separator()
    print("TEST 4: can_open_trade() - Max Trades Per Currency")
    print_separator()
    
    # Reset
    for currency in MockGlobals._CurrencyCount_:
        MockGlobals._CurrencyCount_[currency] = 0
    MockGlobals._Trades_ = {}
    
    # Set max trades per currency to 2
    MockGlobals.news_filter_maxTrades = 0  # Disable total limit
    MockGlobals.news_filter_maxTradePerCurrency = 2
    
    print(f"\nFilter Settings:")
    print(f"  news_filter_maxTrades = {MockGlobals.news_filter_maxTrades}")
    print(f"  news_filter_maxTradePerCurrency = {MockGlobals.news_filter_maxTradePerCurrency}")
    
    # Simulate currency counts
    print("\nSimulating open positions:")
    print("  EURUSD opened → EUR: 1, USD: 1")
    MockGlobals._CurrencyCount_["EUR"] = 1
    MockGlobals._CurrencyCount_["USD"] = 1
    
    print("  GBPUSD opened → GBP: 1, USD: 2")
    MockGlobals._CurrencyCount_["GBP"] = 1
    MockGlobals._CurrencyCount_["USD"] = 2
    
    print("\n📊 Current Currency Counts:")
    for currency, count in MockGlobals._CurrencyCount_.items():
        if count > 0:
            print(f"  {currency}: {count}")
    
    print("\nAttempting to open USDJPY (would make USD = 3):")
    result = can_open_trade("USDJPY")
    print(f"Result: {'✅ ALLOWED' if result else '❌ REJECTED'}")
    
    print("\nAttempting to open GBPJPY (GBP: 1→2, JPY: 0→1):")
    result = can_open_trade("GBPJPY")
    print(f"Result: {'✅ ALLOWED' if result else '❌ REJECTED'}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RISK MANAGEMENT FILTER TESTS")
    print("="*60)
    
    test_extract_currencies()
    test_currency_counting()
    test_can_open_trade()
    test_can_open_trade_currency_limit()
    
    print_separator()
    print("✅ ALL TESTS COMPLETED")
    print_separator()
    print()
