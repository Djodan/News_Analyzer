import sys
sys.path.insert(0, '..')

"""
End-to-End Test: Complete News Algorithm (All 7 Steps)
Demonstrates the full flow from initialization to trade execution
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import handle_news
from Functions import _CLIENT_COMMANDS, _LOCK

def display_summary():
    """Display summary of all dictionaries and queued trades"""
    print("\n" + "="*80)
    print("FINAL STATE SUMMARY")
    print("="*80)
    
    # _Currencies_ summary
    currencies_count = len(Globals._Currencies_)
    print(f"\n_Currencies_: {currencies_count} event(s)")
    for currency, data in Globals._Currencies_.items():
        affect = data.get('affect', 'None')
        print(f"  {currency}: {affect}")
    
    # _Affected_ summary
    affected_count = len(Globals._Affected_)
    print(f"\n_Affected_: {affected_count} pair(s)")
    for pair, data in Globals._Affected_.items():
        position = data.get('position')
        print(f"  {pair}: {position}")
    
    # _Symbols_ verdicts summary
    verdicts = {pair: data.get('verdict_GPT', '') for pair, data in Globals._Symbols_.items() if data.get('verdict_GPT')}
    print(f"\n_Symbols_ verdicts: {len(verdicts)}")
    for pair, verdict in verdicts.items():
        print(f"  {pair}: {verdict}")
    
    print("="*80 + "\n")

def main():
    print("="*80)
    print("END-TO-END TEST: Complete News Algorithm")
    print("="*80)
    
    # Test client ID
    test_client_id = "E2E_TEST_CLIENT"
    
    # Clear any existing state
    print("\n[SETUP] Clearing state...")
    Globals._Currencies_ = {}
    Globals._Affected_ = {}
    for pair in Globals._Symbols_:
        Globals._Symbols_[pair]["verdict_GPT"] = ""
    
    with _LOCK:
        _CLIENT_COMMANDS.clear()
    
    # Set test mode
    Globals.news_test_mode = True
    Globals.csv_count = 2  # Process 2 events
    
    print(f"[SETUP] Test mode: ON (process ONLY past events)")
    print(f"[SETUP] CSV count limit: {Globals.csv_count}")
    
    # Simulate stats for handle_news
    test_stats = {"replies": 1}
    
    print("\n" + "="*80)
    print("CALLING handle_news() - Complete Algorithm Flow")
    print("="*80)
    print("\nThis will execute:")
    print("  STEP 1: Initialize forecasts from CSV")
    print("  STEP 2: Monitor for ready events")
    print("  STEP 3: Fetch actual values (with retry)")
    print("  STEP 4: Validate data format")
    print("  STEP 4A: Calculate affect (BULL/BEAR/NEUTRAL)")
    print("  STEP 5: Generate trading signals via ChatGPT")
    print("  STEP 6: Update _Affected_ and _Symbols_")
    print("  STEP 7: Execute trades via enqueue_command")
    
    print("\n" + "-"*80)
    
    # Call handle_news (full pipeline)
    result = handle_news(test_client_id, test_stats)
    
    print("\n" + "-"*80)
    print(f"\nhandle_news() returned: {result}")
    
    # Display final state
    display_summary()
    
    # Show queued trades
    print("\n" + "="*80)
    print("QUEUED TRADES:")
    print("="*80)
    
    with _LOCK:
        queue = _CLIENT_COMMANDS.get(test_client_id, [])
        
        if not queue:
            print("  (no trades queued)")
        else:
            for i, cmd in enumerate(queue, 1):
                state = cmd.get("state")
                state_name = {1: "BUY", 2: "SELL"}.get(state, "UNKNOWN")
                payload = cmd.get("payload", {})
                
                print(f"\n  Trade {i}: {state_name} {payload.get('symbol')}")
                print(f"    Volume: {payload.get('volume')}")
                print(f"    TP/SL: {payload.get('tpPips')}/{payload.get('slPips')} pips")
                print(f"    Comment: {payload.get('comment')}")
    
    print("\n" + "="*80)
    print("END-TO-END TEST COMPLETE")
    print("="*80)
    
    # Verification
    with _LOCK:
        trades_count = len(_CLIENT_COMMANDS.get(test_client_id, []))
    
    print(f"\nResults:")
    print(f"  - Processed {len(Globals._Currencies_)} event(s)")
    print(f"  - Affected {len(Globals._Affected_)} pair(s)")
    print(f"  - Queued {trades_count} trade(s)")
    
    if trades_count > 0:
        print(f"\n[SUCCESS] News algorithm working end-to-end!")
        print(f"          Events → Analysis → Signals → Trades")
    else:
        print(f"\n[INFO] No trades queued")
        print(f"       This could be due to:")
        print(f"       - All events resulted in NEUTRAL affect")
        print(f"       - Actual values not available yet")
        print(f"       - No events ready to process")

if __name__ == "__main__":
    main()
