"""
News.py - Clean Version
News-based trading algorithm with minimal logging.
"""

import Globals
from Functions import enqueue_command, checkTime
import csv
import re
from datetime import datetime, timedelta
from AI_Perplexity import get_news_data
from AI_ChatGPT import validate_news_data, generate_trading_signals


# Global flag to track if initialization has been completed
_initialization_complete = False

# Global dictionary to track event times (for monitoring)
# Format: currency → datetime object
_event_times = {}


def initialize_news_forecasts():
    """
    STEP 1: INITIALIZATION
    Reads calendar_statement.csv and pre-fetches all forecast values for upcoming events.
    """
    global _initialization_complete
    
    if _initialization_complete:
        return
    
    current_time = datetime.now()
    test_mode = getattr(Globals, 'news_test_mode', False)
    process_past_events = getattr(Globals, 'news_process_past_events', False)
    
    csv_path = "calendar_statement.csv"
    all_events = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                date_str = row.get('Date', '').strip()
                event_name = row.get('Event', '').strip()
                impact = row.get('Impact', '').strip()
                currency = row.get('Currency', '').strip()
                
                if not all([date_str, event_name, currency]):
                    continue
                
                try:
                    event_time = datetime.strptime(date_str, "%Y, %B %d, %H:%M")
                    is_past = event_time <= current_time
                    
                    # Filter based on mode
                    if test_mode and not is_past:
                        continue  # Test mode: skip future
                    if not test_mode and is_past and not process_past_events:
                        continue  # Normal mode: skip past
                    
                    all_events.append({
                        'date': date_str,
                        'event': event_name,
                        'currency': currency,
                        'impact': impact,
                        'event_time': event_time
                    })
                except Exception:
                    continue
        
        # Apply csv_count limit for testing
        events = all_events
        if not Globals.liveMode:
            limit = getattr(Globals, 'csv_count', 4)
            events = events[:limit] if len(events) > limit else events
        
        # Pre-fetch forecasts
        for event in events:
            currency = event['currency']
            date_str = event['date']
            event_name = event['event']
            
            # Fetch forecast
            perplexity_response = get_news_data(event_name, currency, date_str, "forecast")
            validation_response = validate_news_data(perplexity_response)
            
            # Parse forecast
            forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+)", perplexity_response, re.IGNORECASE)
            if forecast_match:
                try:
                    forecast = float(forecast_match.group(1))
                    
                    # Store in _Currencies_
                    Globals._Currencies_[currency] = {
                        'date': date_str,
                        'event': event_name,
                        'forecast': forecast,
                        'actual': None,
                        'affect': None,
                        'retry_count': 0
                    }
                    
                    # Store event time
                    _event_times[currency] = event['event_time']
                except ValueError:
                    continue
    
    except FileNotFoundError:
        print(f"ERROR: {csv_path} not found!")
        return
    except Exception as e:
        print(f"ERROR during initialization: {e}")
        return
    
    _initialization_complete = True


def monitor_news_events():
    """
    STEP 2: TIME MONITORING LOOP
    Returns currency code if event is ready to process, None otherwise.
    """
    if not _initialization_complete:
        return None
    
    current_time = datetime.now()
    
    for currency, event_time in _event_times.items():
        if currency not in Globals._Currencies_:
            continue
        
        currency_data = Globals._Currencies_[currency]
        
        # Check if event time passed and not yet processed
        if current_time >= event_time and currency_data['actual'] is None:
            return currency
    
    return None


def fetch_actual_value(currency):
    """
    STEP 3: FETCH ACTUAL WITH RETRY MECHANISM
    Returns True if successful, False if retry needed or failed.
    """
    if currency not in Globals._Currencies_:
        return False
    
    currency_data = Globals._Currencies_[currency]
    event_name = currency_data['event']
    date_str = currency_data['date']
    retry_count = currency_data.get('retry_count', 0)
    
    try:
        # Fetch actual
        perplexity_response = get_news_data(event_name, currency, date_str, "actual")
        validation_response = validate_news_data(perplexity_response)
        
        # Check if not ready yet
        if "FALSE" in perplexity_response.upper():
            retry_count += 1
            Globals._Currencies_[currency]['retry_count'] = retry_count
            
            if retry_count >= 3:
                Globals._Currencies_[currency]['actual'] = None
                return False
            return False
        
        # Parse actual
        actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+)", perplexity_response, re.IGNORECASE)
        if actual_match:
            actual = float(actual_match.group(1))
            Globals._Currencies_[currency]['actual'] = actual
            
            # Continue pipeline
            calculate_affect(currency)
            trading_signals = generate_trading_decisions(currency)
            update_affected_symbols(currency, trading_signals)
            
            return True
        
        return False
            
    except Exception:
        return False


def calculate_affect(currency):
    """
    STEP 4A: CALCULATE AFFECT
    Determines BULL, BEAR, or NEUTRAL.
    """
    if currency not in Globals._Currencies_:
        return
    
    currency_data = Globals._Currencies_[currency]
    forecast = currency_data.get('forecast')
    actual = currency_data.get('actual')
    event_name = currency_data.get('event', '').upper()
    
    if forecast is None or actual is None:
        Globals._Currencies_[currency]['affect'] = "NEUTRAL"
        return
    
    # Check for inverse indicators
    is_inverse = any(word in event_name for word in ["UNEMPLOYMENT", "JOBLESS", "CLAIMS"])
    
    # Calculate affect
    if actual > forecast:
        affect = "BEAR" if is_inverse else "BULL"
    elif actual < forecast:
        affect = "BULL" if is_inverse else "BEAR"
    else:
        affect = "NEUTRAL"
    
    Globals._Currencies_[currency]['affect'] = affect


def generate_trading_decisions(currency):
    """
    STEP 5: GENERATE TRADING SIGNALS
    Returns dict of pair → action.
    """
    if currency not in Globals._Currencies_:
        return {}
    
    currency_data = Globals._Currencies_[currency]
    event_name = currency_data.get('event')
    forecast = currency_data.get('forecast')
    actual = currency_data.get('actual')
    affect = currency_data.get('affect')
    
    # Skip if NEUTRAL or missing data
    if affect == "NEUTRAL" or forecast is None or actual is None:
        return {}
    
    # Call ChatGPT
    response = generate_trading_signals(currency, event_name, forecast, actual)
    
    # Parse response
    trading_signals = {}
    
    if "NEUTRAL" in response.upper() and ":" not in response:
        return {}
    
    try:
        for pair_action in response.split(","):
            pair_action = pair_action.strip()
            if ":" in pair_action:
                parts = pair_action.split(":")
                pair = parts[0].strip()
                action = parts[1].strip().upper()
                
                if action in ["BUY", "SELL"]:
                    trading_signals[pair] = action
    except Exception:
        pass
    
    return trading_signals


def update_affected_symbols(currency, trading_signals):
    """
    STEP 6: UPDATE _Affected_ AND _Symbols_ DICTIONARIES
    """
    if not trading_signals or currency not in Globals._Currencies_:
        return
    
    currency_data = Globals._Currencies_[currency]
    event_date = currency_data.get('date')
    event_name = currency_data.get('event')
    
    for pair_name, action in trading_signals.items():
        # Store in _Affected_
        Globals._Affected_[pair_name] = {
            "date": event_date,
            "event": event_name,
            "position": action
        }
        
        # Update _Symbols_ if exists
        if pair_name in Globals._Symbols_:
            Globals._Symbols_[pair_name]["verdict_GPT"] = action


def execute_news_trades(client_id):
    """
    STEP 7: EXECUTE TRADES
    Returns number of trades queued.
    """
    trades_queued = 0
    
    for pair_name, pair_config in Globals._Symbols_.items():
        verdict = pair_config.get("verdict_GPT", "")
        
        if verdict not in ["BUY", "SELL"]:
            continue
        
        # Only queue pairs that are in symbolsToTrade
        if pair_name not in Globals.symbolsToTrade:
            continue
        
        # Check if this pair already has a queued or executed trade
        if pair_name in Globals._Trades_:
            existing_status = Globals._Trades_[pair_name].get("status")
            if existing_status in ["queued", "executed"]:
                continue  # Skip pairs that already have trades queued or executed
        
        symbol = pair_config.get("symbol")
        lot = pair_config.get("lot")
        tp = pair_config.get("TP")
        sl = pair_config.get("SL")
        
        state = 1 if verdict == "BUY" else 2
        
        # Generate trade record
        from datetime import datetime
        now = datetime.now().isoformat()
        
        # Store in Globals._Trades_ with pair name as key
        Globals._Trades_[pair_name] = {
            "client_id": str(client_id),
            "symbol": symbol,
            "action": verdict,
            "volume": lot,
            "tp": tp,
            "sl": sl,
            "comment": f"NEWS {pair_name}",
            "status": "queued",
            "createdAt": now,
            "updatedAt": now
        }
        
        try:
            enqueue_command(
                client_id,
                state,
                {
                    "symbol": symbol,
                    "volume": lot,
                    "comment": f"NEWS {pair_name}",
                    "tpPips": tp,
                    "slPips": sl
                }
            )
            trades_queued += 1
        except Exception:
            pass
    
    return trades_queued


def handle_news(client_id, stats):
    """
    Main handler - integrates all 7 steps.
    Returns True if trades were queued.
    """
    # STEP 1: Initialize
    initialize_news_forecasts()
    
    # STEP 2: Monitor events
    currency_to_process = monitor_news_events()
    
    if currency_to_process:
        # STEP 3-6: Process event
        fetch_actual_value(currency_to_process)
    
    # STEP 7: Execute trades
    trades_queued = execute_news_trades(client_id)
    
    return trades_queued > 0
