"""
Test STEP 7: Execute Trades
Tests trade execution via enqueue_command with manually populated data
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import execute_news_trades, update_affected_symbols
from Functions import _CLIENT_COMMANDS, _LOCK

def display_queued_trades(client_id):
    """Display all queued trades for a client"""
    print("\n" + "="*80)
    print("QUEUED TRADES:")
    print("="*80)
    
    with _LOCK:
        queue = _CLIENT_COMMANDS.get(client_id, [])
        
        if not queue:
            print("  (no trades queued)")
        else:
            for i, cmd in enumerate(queue, 1):
                state = cmd.get("state")
                state_name = {0: "NO_OP", 1: "OPEN_BUY", 2: "OPEN_SELL", 3: "CLOSE"}.get(state, "UNKNOWN")
                payload = cmd.get("payload", {})
                
                print(f"\n  Trade {i}:")
                print(f"    Command ID: {cmd.get('cmdId')}")
                print(f"    State: {state} ({state_name})")
                print(f"    Symbol: {payload.get('symbol')}")
                print(f"    Volume: {payload.get('volume')}")
                print(f"    Comment: {payload.get('comment')}")
                print(f"    TP Pips: {payload.get('tpPips')}")
                print(f"    SL Pips: {payload.get('slPips')}")
                print(f"    Status: {cmd.get('status')}")
    
    print("="*80 + "\n")

def main():
    print("="*80)
    print("TESTING STEP 7: Execute Trades")
    print("="*80)
    
    # Test client ID
    test_client_id = "TEST_CLIENT_123"
    
    # Clear any existing commands
    with _LOCK:
        _CLIENT_COMMANDS.clear()
    
    # Manually populate _Currencies_ and _Symbols_ with test data
    print("\n[SETUP] Manually populating test data...")
    
    # EUR - BEAR scenario (unemployment increased)
    Globals._Currencies_["EUR"] = {
        "date": "2025, November 03, 04:10",
        "event": "(Austria) Unemployment Rate",
        "forecast": 7.0,
        "actual": 7.2,
        "affect": "BEAR",
        "retry_count": 0
    }
    
    # GBP - BULL scenario (PMI increased)
    Globals._Currencies_["GBP"] = {
        "date": "2025, November 03, 04:30",
        "event": "(United Kingdom) S&P Global Manufacturing PMI",
        "forecast": 49.6,
        "actual": 49.9,
        "affect": "BULL",
        "retry_count": 0
    }
    
    # USD - BEAR scenario (employment decreased)
    Globals._Currencies_["USD"] = {
        "date": "2025, November 11, 08:15",
        "event": "(United States) ADP Employment Change",
        "forecast": 100.0,
        "actual": 95.0,
        "affect": "BEAR",
        "retry_count": 0
    }
    
    print("Populated 3 currencies")
    
    # Clear verdict_GPT from all symbols
    for pair in Globals._Symbols_:
        Globals._Symbols_[pair]["verdict_GPT"] = ""
    
    print("\nBefore STEP 6 & 7:")
    print(f"  _Symbols_ verdicts: {sum(1 for d in Globals._Symbols_.values() if d.get('verdict_GPT'))}")
    print(f"  Queued trades: 0")
    
    # Generate trading signals for EUR (BEAR)
    print("\n" + "="*80)
    print("STEP 6: Updating dictionaries with EUR BEAR signals")
    print("="*80)
    
    eur_signals = {
        "EURNZD": "SELL",  # This one exists in _Symbols_
    }
    
    update_affected_symbols("EUR", eur_signals)
    
    # Generate trading signals for GBP (BULL)
    print("\n" + "="*80)
    print("STEP 6: Updating dictionaries with GBP BULL signals")
    print("="*80)
    
    gbp_signals = {
        "GBPAUD": "BUY",  # This one exists in _Symbols_
    }
    
    update_affected_symbols("GBP", gbp_signals)
    
    # Generate trading signals for USD (BEAR)
    print("\n" + "="*80)
    print("STEP 6: Updating dictionaries with USD BEAR signals")
    print("="*80)
    
    usd_signals = {
        "XAUUSD": "BUY",   # Gold benefits from weak USD
        "USDJPY": "SELL"   # USDJPY exists in _Symbols_
    }
    
    update_affected_symbols("USD", usd_signals)
    
    # Display verdicts before execution
    print("\n" + "="*80)
    print("VERDICTS SET IN _Symbols_:")
    print("="*80)
    for pair, data in Globals._Symbols_.items():
        verdict = data.get('verdict_GPT', '')
        if verdict:
            print(f"  {pair}: {verdict}")
    
    verdicts_count = sum(1 for d in Globals._Symbols_.values() if d.get('verdict_GPT'))
    print(f"\nTotal verdicts: {verdicts_count}")
    
    # Execute STEP 7
    print("\n" + "="*80)
    print("STEP 7: Executing Trades")
    print("="*80)
    
    trades_queued = execute_news_trades(test_client_id)
    
    # Display queued trades
    display_queued_trades(test_client_id)
    
    # Verify results
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    with _LOCK:
        actual_queue_size = len(_CLIENT_COMMANDS.get(test_client_id, []))
    
    expected_trades = verdicts_count  # Should queue 1 trade per verdict
    
    print(f"Trades queued by execute_news_trades(): {trades_queued}")
    print(f"Actual commands in queue: {actual_queue_size}")
    print(f"Expected trades: {expected_trades}")
    
    if trades_queued == expected_trades and actual_queue_size == expected_trades:
        print(f"\n[OK] STEP 7 working correctly!")
        print(f"     - {trades_queued} trade(s) queued")
        print(f"     - All verdicts converted to trade commands")
    else:
        print(f"\n[ERROR] STEP 7 verification failed")
        if trades_queued != expected_trades:
            print(f"  - Trades queued: got {trades_queued}, expected {expected_trades}")
        if actual_queue_size != expected_trades:
            print(f"  - Queue size: got {actual_queue_size}, expected {expected_trades}")
    
    # Detailed verification
    print("\n" + "="*80)
    print("DETAILED TRADE VERIFICATION:")
    print("="*80)
    
    with _LOCK:
        queue = _CLIENT_COMMANDS.get(test_client_id, [])
        
        # Expected trades
        expected_trade_details = [
            {"pair": "EURNZD", "state": 2, "comment": "NEWS EURNZD"},  # SELL
            {"pair": "GBPAUD", "state": 1, "comment": "NEWS GBPAUD"},  # BUY
            {"pair": "XAUUSD", "state": 1, "comment": "NEWS XAUUSD"},  # BUY
            {"pair": "USDJPY", "state": 2, "comment": "NEWS USDJPY"},  # SELL
        ]
        
        for expected in expected_trade_details:
            pair = expected["pair"]
            
            # Find matching trade in queue
            matching_trade = None
            for cmd in queue:
                if cmd.get("payload", {}).get("comment") == expected["comment"]:
                    matching_trade = cmd
                    break
            
            if matching_trade:
                state_ok = matching_trade.get("state") == expected["state"]
                symbol_ok = matching_trade.get("payload", {}).get("symbol") == pair
                
                if state_ok and symbol_ok:
                    state_name = "BUY" if expected["state"] == 1 else "SELL"
                    print(f"  [OK] {pair}: {state_name} command queued correctly")
                else:
                    print(f"  [WRONG] {pair}: Found but details incorrect")
            else:
                print(f"  [MISSING] {pair}: No matching command found")

if __name__ == "__main__":
    main()
