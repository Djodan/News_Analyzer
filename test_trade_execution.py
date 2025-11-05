"""
Test script to verify trades status changes to "executed" when acknowledged
"""

import Globals
from News import execute_news_trades
from Functions import ack_command, get_command_queue
import json

# Clear any existing data
Globals._Trades_ = {}
Globals._Symbols_['XAUUSD']['verdict_GPT'] = 'BUY'
Globals._Symbols_['USDJPY']['verdict_GPT'] = 'SELL'

# Execute trades
print("Step 1: Executing trades...")
count = execute_news_trades('test_client_123')
print(f"  Queued {count} trades\n")

# Show initial state
print("Step 2: Initial _Trades_ status:")
for pair, trade in Globals._Trades_.items():
    print(f"  {pair}: {trade['status']}")

# Get the command queue to find cmdIds
print("\nStep 3: Getting command queue...")
queue = get_command_queue('test_client_123')
print(f"  Found {len(queue)} commands in queue\n")

# Acknowledge the first trade (XAUUSD)
if len(queue) > 0:
    cmd_id = queue[0]['cmdId']
    print(f"Step 4: Acknowledging XAUUSD trade (cmdId: {cmd_id})...")
    result = ack_command('test_client_123', cmd_id, True, {"ticket": 12345})
    print(f"  ACK result: {result}\n")

# Check updated status
print("Step 5: Updated _Trades_ status:")
for pair, trade in Globals._Trades_.items():
    print(f"  {pair}: {trade['status']}")

print("\n" + "=" * 80)
print("Full _Trades_ dictionary:")
print(json.dumps(Globals._Trades_, indent=2))
