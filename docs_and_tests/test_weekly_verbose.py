"""
Test Weekly algorithm with detailed logging
"""
import sys
sys.path.insert(0, '.')

import Globals
from Functions import reset_session_tracking
from Weekly import handle_weekly

print("Testing Weekly Algorithm with Detailed Logging")
print("\n")

# Scenario 1: liveMode=True, symbolsToTrade has symbols with manual_position="X"
print("SCENARIO 1: liveMode=True, all symbols have manual_position='X'")
print("-" * 80)
reset_session_tracking()
Globals.liveMode = True
Globals.timeToTrade = True
Globals.symbolsToTrade = {"XAUUSD", "USDJPY"}
Globals.symbolsCurrentlyOpen = []
Globals._Symbols_["XAUUSD"]["manual_position"] = "X"
Globals._Symbols_["USDJPY"]["manual_position"] = "X"

stats = {"replies": 1}
result = handle_weekly("client1", stats)

# Scenario 2: liveMode=True, some symbols with BUY/SELL
print("\n\nSCENARIO 2: liveMode=True, symbols with BUY/SELL positions")
print("-" * 80)
reset_session_tracking()
Globals.liveMode = True
Globals.timeToTrade = True
Globals.symbolsToTrade = {"XAUUSD", "USDJPY"}
Globals.symbolsCurrentlyOpen = []
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"
Globals._Symbols_["USDJPY"]["manual_position"] = "SELL"

stats = {"replies": 1}
result = handle_weekly("client1", stats)

# Scenario 3: One symbol already open
print("\n\nSCENARIO 3: XAUUSD already open")
print("-" * 80)
reset_session_tracking()
Globals.liveMode = True
Globals.timeToTrade = True
Globals.symbolsToTrade = {"XAUUSD", "USDJPY"}
Globals.symbolsCurrentlyOpen = ["XAUUSD"]  # Already open
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"
Globals._Symbols_["USDJPY"]["manual_position"] = "SELL"

stats = {"replies": 1}
result = handle_weekly("client1", stats)

# Scenario 4: Not Sunday, liveMode=False
print("\n\nSCENARIO 4: Not Sunday, liveMode=False (should block)")
print("-" * 80)
reset_session_tracking()
Globals.liveMode = False
Globals.timeToTrade = True
Globals.symbolsToTrade = {"XAUUSD"}
Globals.symbolsCurrentlyOpen = []
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"

stats = {"replies": 1}
result = handle_weekly("client1", stats)

# Scenario 5: timeToTrade=False
print("\n\nSCENARIO 5: timeToTrade=False (should block)")
print("-" * 80)
reset_session_tracking()
Globals.liveMode = True
Globals.timeToTrade = False
Globals.symbolsToTrade = {"XAUUSD"}
Globals.symbolsCurrentlyOpen = []
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"

stats = {"replies": 1}
result = handle_weekly("client1", stats)

# Scenario 6: Second poll (retry pending)
print("\n\nSCENARIO 6: Second poll - should only retry pending")
print("-" * 80)
reset_session_tracking()
Globals.liveMode = True
Globals.timeToTrade = True
Globals.symbolsToTrade = {"XAUUSD", "USDJPY"}
Globals.symbolsCurrentlyOpen = []
Globals._Symbols_["XAUUSD"]["manual_position"] = "BUY"
Globals._Symbols_["USDJPY"]["manual_position"] = "SELL"

# First poll
stats = {"replies": 1}
handle_weekly("client1", stats)

# Second poll
print("\n" + "="*80)
print("NOW RUNNING SECOND POLL")
print("="*80 + "\n")
stats = {"replies": 2}
result = handle_weekly("client1", stats)

print("\n" + "="*80)
print("✓ All scenarios complete!")
print("="*80)
