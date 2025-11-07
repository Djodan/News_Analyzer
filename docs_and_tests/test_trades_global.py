import sys
sys.path.insert(0, '..')

"""
Test script to verify trades are stored in Globals._Trades_
"""

import Globals
from News import execute_news_trades
import json

# Clear any existing data
Globals._Trades_ = {}
Globals._Symbols_['XAUUSD']['verdict_GPT'] = 'BUY'
Globals._Symbols_['USDJPY']['verdict_GPT'] = 'SELL'

# Execute trades
print("Executing trades...")
count = execute_news_trades('test_client_123')

print(f"\nTrades queued: {count}")
print(f"\n_Trades_ dictionary has {len(Globals._Trades_)} entries:")
print("=" * 80)

for trade_id, trade_data in Globals._Trades_.items():
    print(f"\nTrade ID: {trade_id}")
    print(f"  Symbol: {trade_data['symbol']}")
    print(f"  Action: {trade_data['action']}")
    print(f"  Volume: {trade_data['volume']}")
    print(f"  TP: {trade_data['tp']}")
    print(f"  SL: {trade_data['sl']}")
    print(f"  Comment: {trade_data['comment']}")
    print(f"  Status: {trade_data['status']}")
    print(f"  Created: {trade_data['createdAt']}")

print("\n" + "=" * 80)
print("Full JSON output:")
print(json.dumps(Globals._Trades_, indent=2))
