"""
News.py
News-based trading algorithm.
Opens trades based on news events and market conditions.
"""

import Globals
from Functions import enqueue_command, checkTime
import csv
import re
from datetime import datetime, timedelta
from AI_Perplexity import get_news_data
from AI_ChatGPT import validate_news_data


# Global flag to track if initialization has been completed
_initialization_complete = False

# Global dictionary to track event times (for monitoring)
# Format: currency → datetime object
_event_times = {}


def initialize_news_forecasts():
    """
    STEP 1: INITIALIZATION
    Reads calendar_statement.csv and pre-fetches all forecast values for upcoming events.
    Stores them in Globals._Currencies_ with actual=None.
    Only runs once at startup.
    """
    global _initialization_complete
    
    if _initialization_complete:
        return
    
    print("\n=== NEWS ALGORITHM INITIALIZATION ===")
    print("Reading calendar_statement.csv and pre-fetching forecasts...\n")
    
    # Get current time for filtering
    current_time = datetime.now()
    print(f"Current time: {current_time}\n")
    
    # Get test mode setting
    test_mode = getattr(Globals, 'news_test_mode', False)
    process_past_events = getattr(Globals, 'news_process_past_events', False)
    
    if test_mode:
        print(f"TEST MODE: ON (Processing ONLY past events for testing)")
        print(f"           Future events will be skipped\n")
    else:
        print(f"NORMAL MODE: Processing future events")
        print(f"             Process past events: {process_past_events}\n")
    
    # Read CSV file
    csv_path = "calendar_statement.csv"
    all_events = []
    skipped_events = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Parse event time
                date_str = row.get('Date', '').strip()
                event_name = row.get('Event', '').strip()
                impact = row.get('Impact', '').strip()
                currency = row.get('Currency', '').strip()
                
                if not all([date_str, event_name, currency]):
                    continue
                
                try:
                    # Parse date format: "2025, November 11, 08:15"
                    event_time = datetime.strptime(date_str, "%Y, %B %d, %H:%M")
                    
                    # Check if event is in the past
                    is_past = event_time <= current_time
                    
                    # TEST MODE: Skip future events, only process past
                    if test_mode:
                        if not is_past:
                            skipped_events.append({
                                'date': date_str,
                                'event': event_name,
                                'currency': currency,
                                'event_time': event_time,
                                'reason': 'FUTURE'
                            })
                            continue
                    # NORMAL MODE: Skip past events unless news_process_past_events is True
                    else:
                        if is_past and not process_past_events:
                            skipped_events.append({
                                'date': date_str,
                                'event': event_name,
                                'currency': currency,
                                'event_time': event_time,
                                'reason': 'PAST'
                            })
                            continue
                    
                    # Include event for processing
                    all_events.append({
                        'date': date_str,
                        'event': event_name,
                        'currency': currency,
                        'impact': impact,
                        'event_time': event_time,
                        'is_past': is_past
                    })
                except Exception as e:
                    print(f"Error parsing date '{date_str}': {e}")
                    continue
        
        # Display skipped events
        if skipped_events:
            reason_text = "PAST" if not test_mode else "FUTURE (test mode)"
            print(f"Skipped {len(skipped_events)} {reason_text} event(s)")
        
        print(f"Found {len(all_events)} event(s) to process")
        
        # Apply csv_count limit if not in live mode (only count events being processed)
        events = all_events
        if not Globals.liveMode:
            limit = getattr(Globals, 'csv_count', 4)
            if len(events) > limit:
                events = events[:limit]
                print(f"Limited to {limit} events (csv_count) for testing")
        
        # Pre-fetch forecasts for all upcoming events
        for idx, event in enumerate(events, 1):
            currency = event['currency']
            date_str = event['date']
            event_name = event['event']
            
            print(f"\n[{idx}/{len(events)}] Processing: {currency} - {event_name}")
            print(f"  Date: {date_str}")
            
            # Call Perplexity to get forecast
            print("  Fetching forecast from MyFxBook...")
            perplexity_response = get_news_data(event_name, currency, date_str, "forecast")
            
            # Validate format with ChatGPT
            print("  Validating format...")
            validation_response = validate_news_data(perplexity_response)
            
            # Parse forecast value using regex
            forecast = None
            forecast_match = re.search(r"Forecast\s*:\s*([\d\.\-]+|N/A)", perplexity_response, re.IGNORECASE)
            
            if forecast_match:
                forecast_str = forecast_match.group(1)
                if forecast_str != "N/A":
                    try:
                        forecast = float(forecast_str)
                        print(f"  [OK] Forecast: {forecast}")
                    except ValueError:
                        print(f"  [ERROR] Could not parse forecast: {forecast_str}")
                else:
                    print(f"  [N/A] Forecast not available")
            else:
                print(f"  [ERROR] No forecast found in response")
            
            # Store in _Currencies_ dictionary
            Globals._Currencies_[currency] = {
                'date': date_str,
                'event': event_name,
                'forecast': forecast,
                'actual': None,
                'affect': None,
                'retry_count': 0
            }
            
            # Store event time for monitoring
            _event_times[currency] = event['event_time']
            
            print(f"  Stored in _Currencies_[{currency}]")
    
    except FileNotFoundError:
        print(f"ERROR: {csv_path} not found!")
        return
    except Exception as e:
        print(f"ERROR during initialization: {e}")
        return
    
    _initialization_complete = True
    print(f"\n=== INITIALIZATION COMPLETE ===")
    print(f"Pre-fetched forecasts for {len(Globals._Currencies_)} currencies")
    print("Ready to monitor for event releases...\n")


def monitor_news_events():
    """
    STEP 2: TIME MONITORING LOOP
    Checks if any news events are ready to be processed (event time has passed).
    Returns the currency code if an event is ready, None otherwise.
    
    An event is considered "ready" when:
    - Current time >= event time
    - Actual value hasn't been fetched yet (actual is None)
    
    Returns:
        str or None: Currency code if event is ready, None if no events ready
    """
    if not _initialization_complete:
        return None
    
    current_time = datetime.now()
    
    # Check each currency for ready events
    for currency, event_time in _event_times.items():
        # Skip if not in _Currencies_ (shouldn't happen, but safety check)
        if currency not in Globals._Currencies_:
            continue
        
        currency_data = Globals._Currencies_[currency]
        
        # Check if event time has passed and actual hasn't been fetched yet
        if current_time >= event_time and currency_data['actual'] is None:
            return currency
    
    return None


def get_next_event_info():
    """
    Gets information about the next upcoming event that hasn't been processed yet.
    
    Returns:
        dict or None: Dictionary with 'currency', 'event', 'time' keys, or None if no events
    """
    if not _initialization_complete:
        return None
    
    current_time = datetime.now()
    next_event = None
    next_time = None
    
    # Find the earliest upcoming event that hasn't been processed
    for currency, event_time in _event_times.items():
        if currency not in Globals._Currencies_:
            continue
        
        currency_data = Globals._Currencies_[currency]
        
        # Skip if already processed (actual is not None)
        if currency_data['actual'] is not None:
            continue
        
        # Check if this is the earliest event
        if next_time is None or event_time < next_time:
            next_time = event_time
            next_event = {
                'currency': currency,
                'event': currency_data['event'],
                'time': event_time
            }
    
    return next_event


def fetch_actual_value(currency):
    """
    STEP 3: FETCH ACTUAL WITH RETRY MECHANISM
    Attempts to fetch the actual value for a news event.
    Implements 3-retry mechanism with 2-minute intervals.
    
    Args:
        currency: The currency code to fetch actual for
        
    Returns:
        bool: True if actual was successfully fetched, False if max retries reached
    """
    if currency not in Globals._Currencies_:
        print(f"ERROR: Currency {currency} not found in _Currencies_")
        return False
    
    currency_data = Globals._Currencies_[currency]
    event_name = currency_data['event']
    date_str = currency_data['date']
    retry_count = currency_data.get('retry_count', 0)
    
    print(f"\n[STEP 3] Fetching actual value for {currency}")
    print(f"  Event: {event_name}")
    print(f"  Date: {date_str}")
    print(f"  Retry attempt: {retry_count + 1}/3")
    
    # Call Perplexity to get actual
    print("  Querying MyFxBook for actual value...")
    try:
        perplexity_response = get_news_data(event_name, currency, date_str, "actual")
        
        # Validate format with ChatGPT
        print("  Validating format with ChatGPT...")
        validation_response = validate_news_data(perplexity_response)
        
        # Check if data is not available yet (FALSE response)
        if "FALSE" in perplexity_response.upper():
            print("  [NOT READY] Actual value not released yet")
            
            # Increment retry count
            retry_count += 1
            Globals._Currencies_[currency]['retry_count'] = retry_count
            
            if retry_count >= 3:
                print(f"  [MAX RETRIES] Reached maximum retry attempts (3)")
                print(f"  Setting actual to None (data unavailable)")
                Globals._Currencies_[currency]['actual'] = None
                return False
            else:
                print(f"  Will retry in 2 minutes... ({retry_count}/3 attempts used)")
                return False
        
        # Parse actual value using regex
        actual = None
        actual_match = re.search(r"Actual\s*:\s*([\d\.\-]+|N/A)", perplexity_response, re.IGNORECASE)
        
        if actual_match:
            actual_str = actual_match.group(1)
            if actual_str != "N/A":
                try:
                    actual = float(actual_str)
                    print(f"  [OK] Actual: {actual}")
                    
                    # Store actual value in _Currencies_
                    Globals._Currencies_[currency]['actual'] = actual
                    print(f"  Stored actual value in _Currencies_[{currency}]")
                    
                    # STEP 4A: Calculate affect
                    calculate_affect(currency)
                    
                    return True
                    
                except ValueError:
                    print(f"  [ERROR] Could not parse actual: {actual_str}")
                    return False
            else:
                print(f"  [N/A] Actual not available")
                Globals._Currencies_[currency]['actual'] = None
                return False
        else:
            print(f"  [ERROR] No actual value found in response")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Exception during fetch: {e}")
        return False


def calculate_affect(currency):
    """
    STEP 4A: CALCULATE AFFECT
    Determines if the news event strengthens (BULL) or weakens (BEAR) the currency.
    
    Logic:
    - For most indicators: Higher = Better = BULL, Lower = Worse = BEAR
    - For UNEMPLOYMENT: Higher = Worse = BEAR, Lower = Better = BULL (inverse)
    
    Args:
        currency: The currency code to calculate affect for
    """
    if currency not in Globals._Currencies_:
        print(f"  [ERROR] Currency {currency} not found in _Currencies_")
        return
    
    currency_data = Globals._Currencies_[currency]
    forecast = currency_data.get('forecast')
    actual = currency_data.get('actual')
    event_name = currency_data.get('event', '').upper()
    
    print(f"  [STEP 4A] Calculating affect...")
    
    # Check if we have both values
    if forecast is None or actual is None:
        Globals._Currencies_[currency]['affect'] = "NEUTRAL"
        print(f"    → Affect: NEUTRAL (missing data)")
        return
    
    # Determine if this is an inverse indicator (higher = worse)
    is_inverse = "UNEMPLOYMENT" in event_name or "JOBLESS" in event_name or "CLAIMS" in event_name
    
    # Calculate affect based on comparison
    if actual > forecast:
        affect = "BEAR" if is_inverse else "BULL"
        comparison = "Higher"
    elif actual < forecast:
        affect = "BULL" if is_inverse else "BEAR"
        comparison = "Lower"
    else:
        affect = "NEUTRAL"
        comparison = "Equal"
    
    # Store affect
    Globals._Currencies_[currency]['affect'] = affect
    print(f"    {comparison}: {forecast} → {actual} | Type: {'INVERSE' if is_inverse else 'NORMAL'} → Affect: {affect}")


def handle_news(client_id, stats):
    """
    Handle news trading mode logic for a client.
    Opens positions based on news events and analysis.
    
    Args:
        client_id: The MT5 client ID
        stats: Dictionary containing client statistics including 'replies' count
        
    Returns:
        bool: True if a command was injected, False otherwise
    """
    # STEP 1: Initialize forecasts on first run
    initialize_news_forecasts()
    
    # Get the reply count
    try:
        replies = int(stats.get("replies", 0))
    except Exception:
        replies = 0
    
    # Only trade on first reply
    if replies != 1:
        return False
    
    # Get liveMode setting
    live_mode = getattr(Globals, "liveMode", False)
    
    # If liveMode is True, check time restrictions
    if live_mode:
        checkTime()
        time_to_trade = getattr(Globals, "timeToTrade", False)
        
        if not time_to_trade:
            return False
    
    # Open trades based on news analysis
    symbols_to_trade = getattr(Globals, "symbolsToTrade", set())
    symbols_config = getattr(Globals, "_Symbols_", {})
    
    if not symbols_to_trade:
        return False
    
    injected_any = False
    for symbol in symbols_to_trade:
        if symbol not in symbols_config:
            continue
        
        config = symbols_config[symbol]
        manual_pos = config.get("manual_position", "X")
        
        if manual_pos == "BUY":
            state = 1
        elif manual_pos == "SELL":
            state = 2
        else:
            continue
        
        enqueue_command(
            client_id,
            state,
            {
                "symbol": config["symbol"],
                "volume": config["lot"],
                "comment": f"NEWS {symbol}",
                "tpPips": config["TP"],
                "slPips": config["SL"]
            }
        )
        injected_any = True
    
    return injected_any
