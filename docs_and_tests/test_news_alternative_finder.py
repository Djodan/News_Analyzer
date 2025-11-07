import sys
sys.path.insert(0, '..')

"""
Test News.py behavior with news_filter_findAvailablePair = False
This simulates a news event scenario without the alternative finder enabled
"""
import Globals
from News import execute_news_trades
from Functions import can_open_trade, update_currency_count

print("=" * 80)
print("TEST: News.py Alternative Finder Behavior")
print("=" * 80)
print()

# Display current settings
print("Current Settings:")
print(f"  news_filter_findAvailablePair: {Globals.news_filter_findAvailablePair}")
print(f"  news_filter_maxTradePerCurrency: {Globals.news_filter_maxTradePerCurrency}")
print(f"  system_news_event: {Globals.system_news_event}")
print()

# Setup test scenario
print("=" * 80)
print("SETUP: Simulating EUR news event scenario")
print("=" * 80)
print()

# Reset currency counts
for currency in Globals._CurrencyCount_:
    Globals._CurrencyCount_[currency] = 0

# Clear dictionaries
Globals._Currencies_ = {}
Globals._Affected_ = {}
Globals._Trades_ = {}
Globals._News_ID_Counter_ = 0

print("Step 1: Simulate pre-existing positions to set EUR at limit...")
# Simulate EURUSD and EURGBP already open (EUR at 2/2 limit)
update_currency_count("EURUSD", "add")
update_currency_count("EURGBP", "add")
print(f"  Added EURUSD: {Globals._CurrencyCount_}")
print(f"  Added EURGBP: {Globals._CurrencyCount_}")
print()

print("Step 2: Create fake EUR news event...")
# Create a fake EUR news event
Globals._News_ID_Counter_ = 1
event_key = "EUR_2025-11-05_12:00"
Globals._Currencies_[event_key] = {
    "currency": "EUR",
    "date": "2025, November 05, 12:00",
    "event": "ECB Interest Rate Decision",
    "forecast": 4.0,
    "actual": 4.5,
    "affect": "POSITIVE",
    "retry_count": 0,
    "NID": 1,
    "NID_Affect": 0,
    "NID_Affect_Executed": 0,
    "NID_TP": 0,
    "NID_SL": 0
}
print(f"  Created event: {event_key}")
print(f"  Currency: EUR, Affect: POSITIVE, NID: 1")
print()

print("Step 3: Set verdicts for EUR pairs...")
# Set verdicts for EUR pairs in symbolsToTrade
test_pairs = ["EURUSD", "EURGBP", "EURCHF"]  # EURCHF is in _Symbols_ but might not be in symbolsToTrade

for pair in test_pairs:
    if pair in Globals._Symbols_:
        Globals._Symbols_[pair]["verdict_GPT"] = "BUY"
        Globals._Affected_[pair] = {
            "date": "2025, November 05, 12:00",
            "event": "ECB Interest Rate Decision",
            "position": "BUY",
            "NID": 1
        }
        print(f"  {pair}: verdict_GPT = BUY, NID = 1")

print()
print(f"symbolsToTrade: {Globals.symbolsToTrade}")
print()

# Check which pairs can open
print("=" * 80)
print("FILTER CHECK: Which EUR pairs can open?")
print("=" * 80)
print()

for pair in test_pairs:
    if pair in Globals._Symbols_:
        can_open = can_open_trade(pair)
        in_symbols_to_trade = pair in Globals.symbolsToTrade
        print(f"  {pair}:")
        print(f"    In symbolsToTrade: {in_symbols_to_trade}")
        print(f"    Can open trade: {can_open}")
        if not can_open:
            # Show why it was rejected
            from Functions import extract_currencies
            currencies = extract_currencies(pair)
            for currency in currencies:
                count = Globals._CurrencyCount_.get(currency, 0)
                max_limit = Globals.news_filter_maxTradePerCurrency
                if max_limit > 0 and count >= max_limit:
                    print(f"    → Rejected: {currency} at {count}/{max_limit} limit")

print()

# Run the actual News execution
print("=" * 80)
print("EXECUTION: Running execute_news_trades() with client_id=1")
print("=" * 80)
print()

trades_queued = execute_news_trades(client_id="1")

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Trades queued: {trades_queued}")
print(f"Trades dictionary: {len(Globals._Trades_)} entries")
print()

if Globals._Trades_:
    print("Queued Trades:")
    for tid, trade_data in Globals._Trades_.items():
        print(f"  {tid}: {trade_data.get('action')} {trade_data.get('symbol')} {trade_data.get('volume')} lots")
else:
    print("No trades were queued (as expected with EUR at limit and alternative finder disabled)")

print()
print("=" * 80)
print("EXPECTED BEHAVIOR")
print("=" * 80)
print("With news_filter_findAvailablePair = False:")
print("  ✅ EURUSD should be rejected (EUR at 2/2 limit)")
print("  ✅ EURGBP should be rejected (EUR at 2/2 limit)")
print("  ✅ No alternative search should occur")
print("  ✅ Console should show: 'Alternative finder disabled'")
print("  ✅ No trades should be queued")
print()
print("If alternative finder was enabled:")
print("  → Would search for alternative EUR pairs")
print("  → Might find EURCHF or EURNZD (if in symbolsToTrade)")
print("=" * 80)
