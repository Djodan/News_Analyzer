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
    - _PairCount_: Pair exposure counter
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
            
            # _PairCount_ Dictionary
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 26 + "_PairCount_ Dictionary" + " " * 30 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            if Globals._PairCount_:
                max_limit = getattr(Globals, 'news_filter_maxTradePerPair', 0)
                f.write(f"Max Per Pair Limit: {max_limit if max_limit > 0 else 'No Limit'}\n\n")
                
                # Show pairs with exposure
                active_pairs = {k: v for k, v in Globals._PairCount_.items() if v > 0}
                
                if active_pairs:
                    f.write("Active Exposures:\n")
                    for pair, count in active_pairs.items():
                        status = ""
                        if max_limit > 0:
                            if count >= max_limit:
                                status = " (AT LIMIT)"
                            else:
                                status = f" ({count}/{max_limit})"
                        
                        f.write(f"  {pair}: {count}{status}\n")
                    f.write("\n")
                
                # Show all pairs
                f.write("All Pairs:\n")
                for pair, count in Globals._PairCount_.items():
                    f.write(f"  {pair}: {count}\n")
            else:
                f.write("(Empty)\n\n")
            
            f.write("\n")
            
            # _CurrencyPositions_ Dictionary (S3 Rolling Mode)
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 21 + "_CurrencyPositions_ Dictionary (S3)" + " " * 22 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            currency_positions = getattr(Globals, '_CurrencyPositions_', {})
            
            if currency_positions:
                f.write(f"Active Currency Positions: {len(currency_positions)}\n\n")
                for currency, position_data in currency_positions.items():
                    f.write(f"Currency: {currency}\n")
                    f.write(f"  Pair: {position_data.get('pair', 'N/A')}\n")
                    f.write(f"  Action: {position_data.get('action', 'N/A')}\n")
                    f.write(f"  Ticket: {position_data.get('ticket', 'N/A')}\n")
                    f.write(f"  TID: {position_data.get('TID', 'N/A')}\n")
                    f.write(f"  NID: {position_data.get('NID', 'N/A')}\n")
                    f.write(f"  Entry Time: {position_data.get('entry_time', 'N/A')}\n")
                    f.write("\n")
            else:
                f.write("(Empty - No active currency positions)\n\n")
            
            f.write("\n")
            
            # _PairsTraded_ThisWeek_ Dictionary (S4 Timed Portfolio)
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 20 + "_PairsTraded_ThisWeek_ Dictionary (S4)" + " " * 21 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            pairs_traded_week = getattr(Globals, '_PairsTraded_ThisWeek_', {})
            
            if pairs_traded_week:
                locked_pairs = {k: v for k, v in pairs_traded_week.items() if v}
                
                if locked_pairs:
                    f.write(f"Locked Pairs (Already Traded This Week): {len(locked_pairs)}\n\n")
                    for pair, status in locked_pairs.items():
                        f.write(f"  {pair}: LOCKED\n")
                    f.write("\n")
                else:
                    f.write("(No pairs locked yet this week)\n\n")
                
                # Show available pairs
                available_pairs = {k: v for k, v in pairs_traded_week.items() if not v}
                if available_pairs:
                    f.write(f"Available Pairs: {len(available_pairs)}\n")
                    for pair in available_pairs.keys():
                        f.write(f"  {pair}: AVAILABLE\n")
                    f.write("\n")
            else:
                f.write("(Empty - Weekly tracking not initialized)\n\n")
            
            f.write("\n")
            
            # _CurrencySentiment_ Dictionary (S5 Adaptive Hybrid)
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 20 + "_CurrencySentiment_ Dictionary (S5)" + " " * 23 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            currency_sentiment = getattr(Globals, '_CurrencySentiment_', {})
            
            if currency_sentiment:
                f.write(f"Active Currency Sentiments: {len(currency_sentiment)}\n\n")
                for currency, sentiment_data in currency_sentiment.items():
                    f.write(f"Currency: {currency}\n")
                    f.write(f"  Direction: {sentiment_data.get('direction', 'N/A')}\n")
                    f.write(f"  Confidence: {sentiment_data.get('confidence', 0)}\n")
                    f.write(f"  Events (NIDs): {sentiment_data.get('events', [])}\n")
                    f.write(f"  Positions (TIDs): {sentiment_data.get('positions', [])}\n")
                    f.write(f"  Last Update: {sentiment_data.get('last_update', 'N/A')}\n")
                    f.write("\n")
            else:
                f.write("(Empty - No active currency sentiments)\n\n")
            
            f.write("\n")
            
            # Strategy Configuration Section
            f.write("┌" + "─" * 78 + "┐\n")
            f.write("│" + " " * 24 + "STRATEGY CONFIGURATION" + " " * 32 + "│\n")
            f.write("└" + "─" * 78 + "┘\n\n")
            
            news_strategy = getattr(Globals, 'news_strategy', 2)
            strategy_names = {1: "S1 (Sequential Same-Pair)", 
                             2: "S2 (Multi-Pair with Alternatives)",
                             3: "S3 (Rolling Currency Mode)",
                             4: "S4 (Timed Portfolio Mode)",
                             5: "S5 (Adaptive Hybrid)"}
            
            f.write(f"Active Strategy: {strategy_names.get(news_strategy, 'Unknown')}\n")
            f.write(f"Strategy ID: {news_strategy}\n\n")
            
            strategy_risk = getattr(Globals, 'strategy_risk', {})
            if news_strategy in strategy_risk:
                f.write(f"Risk Per Trade: {strategy_risk[news_strategy] * 100:.2f}%\n")
            
            strategy_tp_sl = getattr(Globals, 'strategy_tp_sl', {})
            if news_strategy in strategy_tp_sl:
                tp = strategy_tp_sl[news_strategy].get('TP', 0)
                sl = strategy_tp_sl[news_strategy].get('SL', 0)
                if tp == 0 and sl == 0:
                    f.write(f"TP/SL: ATR-based (2×ATR TP, 1×ATR SL)\n")
                else:
                    f.write(f"TP: {tp} points, SL: {sl} points\n")
            
            # Weekly target tracking
            weekly_cumulative = getattr(Globals, 'weekly_cumulative_return', 0.0)
            weekly_target = getattr(Globals, 'weekly_profit_target', 1.0)
            weekly_reached = getattr(Globals, 'weekly_target_reached', False)
            
            f.write(f"\nWeekly Progress:\n")
            f.write(f"  Target: {weekly_target:.2f}%\n")
            f.write(f"  Current: {weekly_cumulative:.2f}%\n")
            f.write(f"  Status: {'✅ TARGET REACHED' if weekly_reached else f'⏳ In Progress ({weekly_cumulative/weekly_target*100:.1f}%)'}\n")
            
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
            
            # Pair exposure summary
            active_pairs = sum(1 for v in Globals._PairCount_.values() if v > 0)
            f.write(f"Pairs with Exposure: {active_pairs}/{len(Globals._PairCount_)}\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("END OF SNAPSHOT\n")
            f.write("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save news dictionaries: {e}")
        return False
