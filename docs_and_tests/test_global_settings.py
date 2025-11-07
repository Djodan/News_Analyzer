import sys
sys.path.insert(0, '..')

"""
Test script to verify global settings and alternative finder behavior
"""
import Globals

print("=" * 60)
print("CURRENT GLOBAL SETTINGS")
print("=" * 60)
print(f"news_filter_findAvailablePair: {Globals.news_filter_findAvailablePair}")
print(f"system_news_event: {Globals.system_news_event}")
print(f"news_filter_findAllPairs: {Globals.news_filter_findAllPairs}")
print(f"news_filter_maxTradePerCurrency: {Globals.news_filter_maxTradePerCurrency}")
print()

print("=" * 60)
print("ALTERNATIVE FINDER ACTIVATION LOGIC")
print("=" * 60)
print(f"Will alternative finder activate?")
print(f"  news_filter_findAvailablePair = {Globals.news_filter_findAvailablePair}")
print(f"  system_news_event = {Globals.system_news_event}")
print(f"  Both conditions met? {Globals.news_filter_findAvailablePair and Globals.system_news_event}")
print()

print("=" * 60)
print("EXPECTED BEHAVIOR")
print("=" * 60)

if not Globals.system_news_event:
    print("✅ CORRECT: system_news_event = False")
    print("   → TestingMode will show: 'Opening symbols from symbolsToTrade normally...'")
    print("   → Alternative finder will NOT activate")
    print()
    print("To enable alternative finder testing:")
    print("   1. Set system_news_event to a currency (e.g., 'JPY', 'EUR', 'USD')")
    print("   2. Set news_filter_findAvailablePair = True")
elif not Globals.news_filter_findAvailablePair:
    print("✅ CORRECT: news_filter_findAvailablePair = False")
    print(f"   → System news event is set to: {Globals.system_news_event}")
    print("   → Alternative finder is DISABLED by global setting")
    print("   → Even if primary pair is rejected, NO alternative will be searched")
    print()
    print("To enable alternative finder:")
    print("   Set news_filter_findAvailablePair = True in Globals.py")
else:
    print("✅ ALTERNATIVE FINDER ENABLED")
    print(f"   → System news event: {Globals.system_news_event}")
    print("   → Alternative finder: Enabled")
    print("   → If primary pair is rejected, alternative will be searched")
    print()
    if Globals.news_filter_findAllPairs:
        print("   → Search hierarchy: symbolsToTrade → _Symbols_")
    else:
        print("   → Search scope: symbolsToTrade only")

print("=" * 60)
