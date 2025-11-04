"""
Integration test showing full workflow:
1. Symbols are attempted to trade
2. Failed trades are retried
3. Once open, symbols are not traded again
4. Trading stops when timeToTrade becomes False
"""
import sys
sys.path.insert(0, '.')

import Globals
from Functions import reset_session_tracking
from Weekly import handle_weekly

print("Integration Test: Trade Tracking & Retry Logic")
print("=" * 60)

# Setup: Configure for trading
reset_session_tracking()
Globals.liveMode = True  # Bypass Sunday/time checks for testing
Globals.timeToTrade = True
Globals.symbolsToTrade = {"XAUUSD", "USDJPY"}
Globals.symbolsCurrentlyOpen = []

# Configure manual positions
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"
Globals._Symbols_["USDJPY"]["manual_position"] = "SELL"

print("\n--- Initial State ---")
print(f"symbolsToTrade: {Globals.symbolsToTrade}")
print(f"symbolsCurrentlyOpen: {Globals.symbolsCurrentlyOpen}")
for sym in Globals.symbolsToTrade:
    config = Globals._Symbols_[sym]
    print(f"{sym}: traded={config['traded_this_session']}, pending={config['pending_trade'] is not None}")

# Scenario 1: First poll - attempt to open both symbols
print("\n--- Poll #1: Initial trade attempts ---")
stats = {"replies": 1}
result = handle_weekly("client1", stats)
print(f"handle_weekly() returned: {result}")
for sym in Globals.symbolsToTrade:
    config = Globals._Symbols_[sym]
    print(f"{sym}: traded={config['traded_this_session']}, pending={config['pending_trade'] is not None}")

# Scenario 2: Second poll - symbols still not open (retrying)
print("\n--- Poll #2: Symbols not open yet (should retry) ---")
stats = {"replies": 2}
result = handle_weekly("client1", stats)
print(f"handle_weekly() returned: {result}")
for sym in Globals.symbolsToTrade:
    config = Globals._Symbols_[sym]
    print(f"{sym}: traded={config['traded_this_session']}, pending={config['pending_trade'] is not None}")

# Scenario 3: Third poll - XAUUSD opens (should retry only USDJPY)
print("\n--- Poll #3: XAUUSD opens (only retry USDJPY) ---")
Globals.symbolsCurrentlyOpen = ["XAUUSD"]
stats = {"replies": 3}
result = handle_weekly("client1", stats)
print(f"handle_weekly() returned: {result}")
print(f"symbolsCurrentlyOpen: {Globals.symbolsCurrentlyOpen}")
for sym in Globals.symbolsToTrade:
    config = Globals._Symbols_[sym]
    print(f"{sym}: traded={config['traded_this_session']}, pending={config['pending_trade'] is not None}")

# Scenario 4: Fourth poll - USDJPY opens (no more retries needed)
print("\n--- Poll #4: USDJPY opens (no more pending) ---")
Globals.symbolsCurrentlyOpen = ["XAUUSD", "USDJPY"]
stats = {"replies": 4}
result = handle_weekly("client1", stats)
print(f"handle_weekly() returned: {result}")
print(f"symbolsCurrentlyOpen: {Globals.symbolsCurrentlyOpen}")
for sym in Globals.symbolsToTrade:
    config = Globals._Symbols_[sym]
    print(f"{sym}: traded={config['traded_this_session']}, pending={config['pending_trade'] is not None}")

# Scenario 5: Fifth poll - both open, no duplicates should be created
print("\n--- Poll #5: Both open (should not trade again) ---")
stats = {"replies": 5}
result = handle_weekly("client1", stats)
print(f"handle_weekly() returned: {result}")
print(f"Expected: False (no new trades)")

# Scenario 6: Trading time ends with pending trades (liveMode bypasses)
print("\n--- Scenario: Trading time ends (but liveMode=True bypasses) ---")
reset_session_tracking()
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"
Globals.symbolsCurrentlyOpen = []
Globals.timeToTrade = True
Globals.liveMode = True

# Create pending trade
stats = {"replies": 1}
handle_weekly("client1", stats)
print(f"XAUUSD pending before: {Globals._Symbols_['XAUUSD']['pending_trade'] is not None}")

# Time "ends" but liveMode bypasses the check
Globals.timeToTrade = False
stats = {"replies": 2}
result = handle_weekly("client1", stats)
print(f"handle_weekly() returned: {result}")
print(f"XAUUSD pending after (liveMode=True): {Globals._Symbols_['XAUUSD']['pending_trade'] is not None}")
print(f"Note: liveMode=True bypasses timeToTrade check, so retries continue")

# Scenario 7: Trading time ends with liveMode=False (should clear pending)
print("\n--- Scenario: Trading time ends with liveMode=False ---")
reset_session_tracking()
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"
Globals.symbolsCurrentlyOpen = []
Globals.timeToTrade = True
Globals.liveMode = True

# Create pending trade
stats = {"replies": 1}
handle_weekly("client1", stats)
print(f"XAUUSD pending before: {Globals._Symbols_['XAUUSD']['pending_trade'] is not None}")

# Turn off liveMode and end trading time
Globals.liveMode = False
Globals.timeToTrade = False
# Call retry_pending_trades directly to show clearing behavior
from Functions import retry_pending_trades
result = retry_pending_trades("client1")
print(f"retry_pending_trades() returned: {result}")
print(f"XAUUSD pending after (liveMode=False): {Globals._Symbols_['XAUUSD']['pending_trade']}")
print(f"Expected: None (pending cleared when trading time ends)")

print("\n" + "=" * 60)
print("✓ Integration test complete!")
print("=" * 60)
print("\nSummary:")
print("- Trades are attempted on first poll")
print("- Failed trades are retried on subsequent polls")
print("- Once open, symbols are marked as traded (no duplicates)")
print("- When trading time ends, pending trades are cleared")
