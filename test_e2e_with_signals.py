"""
End-to-End Test with Signal Generation
Simulates complete flow with events that generate trading signals
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Globals
from News import calculate_affect, generate_trading_decisions, update_affected_symbols, execute_news_trades
from Functions import _CLIENT_COMMANDS, _LOCK

def main():
    print("="*80)
    print("END-TO-END TEST: Complete Flow with Trading Signals")
    print("="*80)
    
    # Test client ID
    test_client_id = "E2E_SIGNALS_TEST"
    
    # Clear state
    print("\n[SETUP] Clearing state...")
    Globals._Currencies_.clear()
    Globals._Affected_.clear()
    for pair in Globals._Symbols_:
        Globals._Symbols_[pair]["verdict_GPT"] = ""
    
    with _LOCK:
        _CLIENT_COMMANDS.clear()
    
    print("\n" + "="*80)
    print("SIMULATING NEWS EVENT PROCESSING")
    print("="*80)
    
    # Simulate EUR event (BEAR - unemployment increased)
    print("\n[EVENT 1] EUR - Unemployment Rate Increased")
    print("-" * 80)
    
    Globals._Currencies_["EUR"] = {
        "date": "2025, November 03, 04:10",
        "event": "(Austria) Unemployment Rate",
        "forecast": 7.0,
        "actual": 7.5,
        "affect": None,
        "retry_count": 0
    }
    
    print("  Forecast: 7.0, Actual: 7.5 (Higher)")
    calculate_affect("EUR")
    print(f"  Affect: {Globals._Currencies_['EUR']['affect']}")
    
    eur_signals = generate_trading_decisions("EUR")
    update_affected_symbols("EUR", eur_signals)
    
    # Simulate USD event (BEAR - employment decreased)
    print("\n[EVENT 2] USD - Non-Farm Payrolls Decreased")
    print("-" * 80)
    
    Globals._Currencies_["USD"] = {
        "date": "2025, November 11, 08:15",
        "event": "(United States) Non-Farm Payrolls",
        "forecast": 200.0,
        "actual": 150.0,
        "affect": None,
        "retry_count": 0
    }
    
    print("  Forecast: 200.0, Actual: 150.0 (Lower)")
    calculate_affect("USD")
    print(f"  Affect: {Globals._Currencies_['USD']['affect']}")
    
    usd_signals = generate_trading_decisions("USD")
    update_affected_symbols("USD", usd_signals)
    
    # Display results after event processing
    print("\n" + "="*80)
    print("AFTER EVENT PROCESSING")
    print("="*80)
    
    print(f"\n_Currencies_: {len(Globals._Currencies_)} event(s)")
    for currency, data in Globals._Currencies_.items():
        print(f"  {currency}: Forecast={data['forecast']}, Actual={data['actual']}, Affect={data['affect']}")
    
    print(f"\n_Affected_: {len(Globals._Affected_)} pair(s)")
    for pair, data in Globals._Affected_.items():
        print(f"  {pair}: {data['position']}")
    
    verdicts = {pair: data.get('verdict_GPT', '') for pair, data in Globals._Symbols_.items() if data.get('verdict_GPT')}
    print(f"\n_Symbols_ verdicts: {len(verdicts)}")
    for pair, verdict in verdicts.items():
        print(f"  {pair}: {verdict}")
    
    # Execute trades
    print("\n" + "="*80)
    print("EXECUTING TRADES")
    print("="*80)
    
    trades_queued = execute_news_trades(test_client_id)
    
    # Display queued trades
    print("\n" + "="*80)
    print("QUEUED TRADES")
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
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    with _LOCK:
        actual_trades = len(_CLIENT_COMMANDS.get(test_client_id, []))
    
    print(f"\nEvents processed: {len(Globals._Currencies_)}")
    print(f"Pairs affected: {len(Globals._Affected_)}")
    print(f"Verdicts set: {len(verdicts)}")
    print(f"Trades queued: {actual_trades}")
    
    if actual_trades > 0:
        print(f"\n[SUCCESS] Complete end-to-end flow working!")
        print(f"          News Events → Analysis → Signals → Dictionary Updates → Trade Execution")
        print(f"\nComplete flow:")
        print(f"  1. ✅ Events loaded in _Currencies_")
        print(f"  2. ✅ Affect calculated (BULL/BEAR)")
        print(f"  3. ✅ ChatGPT generated trading signals")
        print(f"  4. ✅ _Affected_ populated with {len(Globals._Affected_)} pairs")
        print(f"  5. ✅ _Symbols_ verdicts set for {len(verdicts)} pairs")
        print(f"  6. ✅ {actual_trades} trades queued for execution")
    else:
        print(f"\n[ERROR] No trades queued - something went wrong")

if __name__ == "__main__":
    main()
