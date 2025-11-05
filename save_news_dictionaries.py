"""
save_news_dictionaries.py
Saves news-related dictionaries to a text file for monitoring.
"""

import Globals
from datetime import datetime
import json


def save_news_dictionaries():
    """
    Save all news-related dictionaries to news_dictionaries.txt.
    Overwrites the file each time to show only the latest state.
    
    Dictionaries saved:
    - _Currencies_: News event tracking
    - _Affected_: News-affected pairs
    - _Trades_: Queued trades tracking
    - _CurrencyCount_: Currency exposure counter
    """
    
    try:
        with open("news_dictionaries.txt", "w", encoding="utf-8") as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("NEWS ANALYZER - DICTIONARIES SNAPSHOT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # _Currencies_ Dictionary
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 25 + "_Currencies_ Dictionary" + " " * 30 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            if Globals._Currencies_:
                f.write(f"Total Events: {len(Globals._Currencies_)}\n\n")
                for event_key, event_data in Globals._Currencies_.items():
                    f.write(f"Event Key: {event_key}\n")
                    f.write(f"  Currency: {event_data.get('currency', 'N/A')}\n")
                    f.write(f"  Date: {event_data.get('date', 'N/A')}\n")
                    f.write(f"  Event: {event_data.get('event', 'N/A')}\n")
                    f.write(f"  Forecast: {event_data.get('forecast', 'N/A')}\n")
                    f.write(f"  Actual: {event_data.get('actual', 'N/A')}\n")
                    f.write(f"  Affect: {event_data.get('affect', 'N/A')}\n")
                    f.write(f"  Retry Count: {event_data.get('retry_count', 0)}\n")
                    
                    nid = event_data.get('NID')
                    if nid:
                        f.write(f"  NID: {nid}\n")
                        f.write(f"  NID_Affect: {event_data.get('NID_Affect', 0)}\n")
                        f.write(f"  NID_Affect_Executed: {event_data.get('NID_Affect_Executed', 0)}\n")
                        f.write(f"  NID_TP: {event_data.get('NID_TP', 0)}\n")
                        f.write(f"  NID_SL: {event_data.get('NID_SL', 0)}\n")
                    
                    f.write("\n")
            else:
                f.write("(Empty)\n\n")
            
            f.write("\n")
            
            # _Affected_ Dictionary
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 26 + "_Affected_ Dictionary" + " " * 31 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            if Globals._Affected_:
                f.write(f"Total Affected Pairs: {len(Globals._Affected_)}\n\n")
                for pair, affected_data in Globals._Affected_.items():
                    f.write(f"Pair: {pair}\n")
                    f.write(f"  Date: {affected_data.get('date', 'N/A')}\n")
                    f.write(f"  Event: {affected_data.get('event', 'N/A')}\n")
                    f.write(f"  Position: {affected_data.get('position', 'N/A')}\n")
                    f.write(f"  NID: {affected_data.get('NID', 'N/A')}\n")
                    f.write("\n")
            else:
                f.write("(Empty)\n\n")
            
            f.write("\n")
            
            # _Trades_ Dictionary
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 28 + "_Trades_ Dictionary" + " " * 31 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            if Globals._Trades_:
                f.write(f"Total Trades: {len(Globals._Trades_)}\n\n")
                for tid, trade_data in Globals._Trades_.items():
                    f.write(f"TID: {tid}\n")
                    f.write(f"  Client ID: {trade_data.get('client_id', 'N/A')}\n")
                    f.write(f"  Symbol: {trade_data.get('symbol', 'N/A')}\n")
                    f.write(f"  Action: {trade_data.get('action', 'N/A')}\n")
                    f.write(f"  Volume: {trade_data.get('volume', 'N/A')}\n")
                    f.write(f"  TP: {trade_data.get('tp', 'N/A')}\n")
                    f.write(f"  SL: {trade_data.get('sl', 'N/A')}\n")
                    f.write(f"  Comment: {trade_data.get('comment', 'N/A')}\n")
                    f.write(f"  Status: {trade_data.get('status', 'N/A')}\n")
                    f.write(f"  Created At: {trade_data.get('createdAt', 'N/A')}\n")
                    f.write(f"  Updated At: {trade_data.get('updatedAt', 'N/A')}\n")
                    f.write(f"  NID: {trade_data.get('NID', 'N/A')}\n")
                    f.write(f"  Ticket: {trade_data.get('ticket', 'N/A')}\n")
                    f.write("\n")
            else:
                f.write("(Empty)\n\n")
            
            f.write("\n")
            
            # _CurrencyCount_ Dictionary
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 24 + "_CurrencyCount_ Dictionary" + " " * 28 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            if Globals._CurrencyCount_:
                max_limit = getattr(Globals, 'news_filter_maxTradePerCurrency', 0)
                f.write(f"Max Per Currency Limit: {max_limit if max_limit > 0 else 'No Limit'}\n\n")
                
                # Show currencies with exposure
                active_currencies = {k: v for k, v in Globals._CurrencyCount_.items() if v > 0}
                
                if active_currencies:
                    f.write("Active Exposures:\n")
                    for currency, count in active_currencies.items():
                        status = ""
                        if max_limit > 0:
                            if count >= max_limit:
                                status = " (AT LIMIT)"
                            else:
                                status = f" ({count}/{max_limit})"
                        
                        f.write(f"  {currency}: {count}{status}\n")
                    f.write("\n")
                
                # Show all currencies
                f.write("All Currencies:\n")
                for currency, count in Globals._CurrencyCount_.items():
                    f.write(f"  {currency}: {count}\n")
            else:
                f.write("(Empty)\n\n")
            
            f.write("\n")
            
            # Summary Statistics
            f.write("=" * 80 + "\n")
            f.write("SUMMARY STATISTICS\n")
            f.write("=" * 80 + "\n\n")
            
            total_events = len(Globals._Currencies_)
            processed_events = sum(1 for e in Globals._Currencies_.values() if e.get('actual') is not None)
            pending_events = total_events - processed_events
            
            f.write(f"Total Events Tracked: {total_events}\n")
            f.write(f"  - Processed: {processed_events}\n")
            f.write(f"  - Pending: {pending_events}\n")
            f.write(f"\n")
            
            f.write(f"Total Affected Pairs: {len(Globals._Affected_)}\n")
            f.write(f"Total Trades Queued: {len(Globals._Trades_)}\n")
            f.write(f"\n")
            
            # Trade status breakdown
            if Globals._Trades_:
                status_counts = {}
                for trade in Globals._Trades_.values():
                    status = trade.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                f.write("Trade Status Breakdown:\n")
                for status, count in status_counts.items():
                    f.write(f"  - {status}: {count}\n")
                f.write(f"\n")
            
            # Currency exposure summary
            active_count = sum(1 for v in Globals._CurrencyCount_.values() if v > 0)
            f.write(f"Currencies with Exposure: {active_count}/{len(Globals._CurrencyCount_)}\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("END OF SNAPSHOT\n")
            f.write("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save news dictionaries: {e}")
        return False
