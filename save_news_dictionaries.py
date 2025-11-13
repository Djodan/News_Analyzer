"""
save_news_dictionaries.py
Saves news-related dictionaries to individual CSV files for monitoring.
All CSV files are stored in the _dictionaries folder.
"""

import Globals
from datetime import datetime
import csv
import os


def save_news_dictionaries():
    """
    Save all news-related dictionaries to individual CSV files.
    Each dictionary gets its own CSV file starting with underscore.
    Files are stored in _dictionaries folder and OVERWRITE (not append) each time.
    
    CSV Files created in _dictionaries/:
    - _currencies.csv: News event tracking
    - _affected.csv: News-affected pairs
    - _trades.csv: Queued trades tracking
    - _currency_count.csv: Currency exposure counter
    - _pair_count.csv: Pair exposure counter
    - _currency_positions.csv: S3 strategy currency positions
    - _pairs_traded_week.csv: S4 strategy weekly tracking
    - _currency_sentiment.csv: S5 strategy sentiment tracking
    """
    
    try:
        # Ensure _dictionaries folder exists
        os.makedirs("_dictionaries", exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. Save _Currencies_ Dictionary
        save_currencies_csv(timestamp)
        
        # 2. Save _Affected_ Dictionary
        save_affected_csv(timestamp)
        
        # 3. Save _Trades_ Dictionary
        save_trades_csv(timestamp)
        
        # 4. Save _CurrencyCount_ Dictionary
        save_currency_count_csv(timestamp)
        
        # 5. Save _PairCount_ Dictionary
        save_pair_count_csv(timestamp)
        
        # 6. Save _CurrencyPositions_ Dictionary (S3)
        save_currency_positions_csv(timestamp)
        
        # 7. Save _PairsTraded_ThisWeek_ Dictionary (S4)
        save_pairs_traded_week_csv(timestamp)
        
        # 8. Save _CurrencySentiment_ Dictionary (S5)
        save_currency_sentiment_csv(timestamp)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save news dictionaries: {e}")
        return False


def save_currencies_csv(timestamp):
    """Save _Currencies_ dictionary to _dictionaries/_currencies.csv"""
    csv_file = os.path.join("_dictionaries", "_currencies.csv")
    fieldnames = ['timestamp', 'event_key', 'currency', 'date', 'event', 'forecast', 
                  'actual', 'affect', 'retry_count', 'nid', 'nid_affect', 
                  'nid_affect_executed', 'nid_tp', 'nid_sl']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            if Globals._Currencies_:
                for event_key, event_data in Globals._Currencies_.items():
                    row = {
                        'timestamp': timestamp,
                        'event_key': event_key,
                        'currency': event_data.get('currency', ''),
                        'date': event_data.get('date', ''),
                        'event': event_data.get('event', ''),
                        'forecast': event_data.get('forecast', ''),
                        'actual': event_data.get('actual', ''),
                        'affect': event_data.get('affect', ''),
                        'retry_count': event_data.get('retry_count', 0),
                        'nid': event_data.get('NID', ''),
                        'nid_affect': event_data.get('NID_Affect', 0),
                        'nid_affect_executed': event_data.get('NID_Affect_Executed', 0),
                        'nid_tp': event_data.get('NID_TP', 0),
                        'nid_sl': event_data.get('NID_SL', 0)
                    }
                    writer.writerow(row)
    except Exception as e:
        # Commented out - file access errors are expected when file is open in Excel/editor
        # print(f"[ERROR] Failed to save _currencies.csv: {e}")
        pass


def save_affected_csv(timestamp):
    """Save _Affected_ dictionary to _dictionaries/_affected.csv"""
    csv_file = os.path.join("_dictionaries", "_affected.csv")
    fieldnames = ['timestamp', 'pair', 'date', 'event', 'position', 'nid']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            if Globals._Affected_:
                for pair, affected_data in Globals._Affected_.items():
                    row = {
                        'timestamp': timestamp,
                        'pair': pair,
                        'date': affected_data.get('date', ''),
                        'event': affected_data.get('event', ''),
                        'position': affected_data.get('position', ''),
                        'nid': affected_data.get('NID', '')
                    }
                    writer.writerow(row)
    except Exception as e:
        print(f"[ERROR] Failed to save _affected.csv: {e}")


def save_trades_csv(timestamp):
    """Save _Trades_ dictionary to _dictionaries/_trades.csv"""
    csv_file = os.path.join("_dictionaries", "_trades.csv")
    fieldnames = ['timestamp', 'tid', 'client_id', 'symbol', 'action', 'volume', 
                  'tp', 'sl', 'comment', 'status', 'created_at', 'updated_at', 
                  'nid', 'ticket']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            if Globals._Trades_:
                for tid, trade_data in Globals._Trades_.items():
                    row = {
                        'timestamp': timestamp,
                        'tid': tid,
                        'client_id': trade_data.get('client_id', ''),
                        'symbol': trade_data.get('symbol', ''),
                        'action': trade_data.get('action', ''),
                        'volume': trade_data.get('volume', ''),
                        'tp': trade_data.get('tp', ''),
                        'sl': trade_data.get('sl', ''),
                        'comment': trade_data.get('comment', ''),
                        'status': trade_data.get('status', ''),
                        'created_at': trade_data.get('createdAt', ''),
                        'updated_at': trade_data.get('updatedAt', ''),
                        'nid': trade_data.get('NID', ''),
                        'ticket': trade_data.get('ticket', '')
                    }
                    writer.writerow(row)
    except Exception as e:
        print(f"[ERROR] Failed to save _trades.csv: {e}")


def save_currency_count_csv(timestamp):
    """Save _CurrencyCount_ dictionary to _dictionaries/_currency_count.csv"""
    csv_file = os.path.join("_dictionaries", "_currency_count.csv")
    fieldnames = ['timestamp', 'currency', 'count', 'max_limit', 'status']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            if Globals._CurrencyCount_:
                max_limit = getattr(Globals, 'news_filter_maxTradePerCurrency', 0)
                
                for currency, count in Globals._CurrencyCount_.items():
                    status = ''
                    if max_limit > 0 and count >= max_limit:
                        status = 'AT_LIMIT'
                    elif count > 0:
                        status = 'ACTIVE'
                    else:
                        status = 'AVAILABLE'
                    
                    row = {
                        'timestamp': timestamp,
                        'currency': currency,
                        'count': count,
                        'max_limit': max_limit if max_limit > 0 else '',
                        'status': status
                    }
                    writer.writerow(row)
    except Exception as e:
        print(f"[ERROR] Failed to save _currency_count.csv: {e}")


def save_pair_count_csv(timestamp):
    """Save _PairCount_ dictionary to _dictionaries/_pair_count.csv"""
    csv_file = os.path.join("_dictionaries", "_pair_count.csv")
    fieldnames = ['timestamp', 'pair', 'count', 'max_limit', 'status']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            if Globals._PairCount_:
                max_limit = getattr(Globals, 'news_filter_maxTradePerPair', 0)
                
                for pair, count in Globals._PairCount_.items():
                    status = ''
                    if max_limit > 0 and count >= max_limit:
                        status = 'AT_LIMIT'
                    elif count > 0:
                        status = 'ACTIVE'
                    else:
                        status = 'AVAILABLE'
                    
                    row = {
                        'timestamp': timestamp,
                        'pair': pair,
                        'count': count,
                        'max_limit': max_limit if max_limit > 0 else '',
                        'status': status
                    }
                    writer.writerow(row)
    except Exception as e:
        print(f"[ERROR] Failed to save _pair_count.csv: {e}")


def save_currency_positions_csv(timestamp):
    """Save _CurrencyPositions_ dictionary to _dictionaries/_currency_positions.csv (S3 strategy)"""
    csv_file = os.path.join("_dictionaries", "_currency_positions.csv")
    fieldnames = ['timestamp', 'currency', 'pair', 'action', 'ticket', 'tid', 'nid', 'entry_time']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            currency_positions = getattr(Globals, '_CurrencyPositions_', {})
            
            if currency_positions:
                for currency, position_data in currency_positions.items():
                    row = {
                        'timestamp': timestamp,
                        'currency': currency,
                        'pair': position_data.get('pair', ''),
                        'action': position_data.get('action', ''),
                        'ticket': position_data.get('ticket', ''),
                        'tid': position_data.get('TID', ''),
                        'nid': position_data.get('NID', ''),
                        'entry_time': position_data.get('entry_time', '')
                    }
                    writer.writerow(row)
    except Exception as e:
        print(f"[ERROR] Failed to save _currency_positions.csv: {e}")


def save_pairs_traded_week_csv(timestamp):
    """Save _PairsTraded_ThisWeek_ dictionary to _dictionaries/_pairs_traded_week.csv (S4 strategy)"""
    csv_file = os.path.join("_dictionaries", "_pairs_traded_week.csv")
    fieldnames = ['timestamp', 'pair', 'status']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            pairs_traded_week = getattr(Globals, '_PairsTraded_ThisWeek_', {})
            
            if pairs_traded_week:
                for pair, is_locked in pairs_traded_week.items():
                    row = {
                        'timestamp': timestamp,
                        'pair': pair,
                        'status': 'LOCKED' if is_locked else 'AVAILABLE'
                    }
                    writer.writerow(row)
    except Exception as e:
        print(f"[ERROR] Failed to save _pairs_traded_week.csv: {e}")


def save_currency_sentiment_csv(timestamp):
    """Save _CurrencySentiment_ dictionary to _dictionaries/_currency_sentiment.csv (S5 strategy)"""
    csv_file = os.path.join("_dictionaries", "_currency_sentiment.csv")
    fieldnames = ['timestamp', 'currency', 'direction', 'confidence', 'events', 'positions', 'last_update']
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            currency_sentiment = getattr(Globals, '_CurrencySentiment_', {})
            
            if currency_sentiment:
                for currency, sentiment_data in currency_sentiment.items():
                    # Convert lists to comma-separated strings
                    events = ','.join(map(str, sentiment_data.get('events', [])))
                    positions = ','.join(map(str, sentiment_data.get('positions', [])))
                    
                    row = {
                        'timestamp': timestamp,
                        'currency': currency,
                        'direction': sentiment_data.get('direction', ''),
                        'confidence': sentiment_data.get('confidence', 0),
                        'events': events,
                        'positions': positions,
                        'last_update': sentiment_data.get('last_update', '')
                    }
                    writer.writerow(row)
    except Exception as e:
        print(f"[ERROR] Failed to save _currency_sentiment.csv: {e}")

