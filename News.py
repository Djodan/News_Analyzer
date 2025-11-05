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
    Stores them in Globals._Currencies_ with actual=None.
    Only runs once at startup.
    """
    global _initialization_complete
    
    if _initialization_complete:
        return
    
    # Get current time for filtering
    current_time = datetime.now()
    
    # Get test mode setting
    test_mode = getattr(Globals, 'news_test_mode', False)
    process_past_events = getattr(Globals, 'news_process_past_events', False)
    
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
            
            # Create unique key: currency + event time
            import hashlib
            event_key = f"{currency}_{event['event_time'].strftime('%Y%m%d%H%M')}"
            
            # Store in _Currencies_ dictionary with unique key
            Globals._Currencies_[event_key] = {
                'currency': currency,
                'date': date_str,
                'event': event_name,
                'forecast': forecast,
                'actual': None,
                'affect': None,
                'retry_count': 0
            }
            
            # Store event time for monitoring
            _event_times[event_key] = event['event_time']
            
            print(f"  Stored in _Currencies_[{event_key}]")
    
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
    Returns the event key if an event is ready, None otherwise.
    
    An event is considered "ready" when:
    - Current time >= event time
    - Actual value hasn't been fetched yet (actual is None)
    
    Returns:
        str or None: Event key if event is ready, None if no events ready
    """
    if not _initialization_complete:
        return None
    
    current_time = datetime.now()
    
    # Check each event for ready status
    for event_key, event_time in _event_times.items():
        # Skip if not in _Currencies_ (shouldn't happen, but safety check)
        if event_key not in Globals._Currencies_:
            continue
        
        event_data = Globals._Currencies_[event_key]
        
        # Check if event time has passed and actual hasn't been fetched yet
        if current_time >= event_time and event_data['actual'] is None:
            return event_key
    
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


def fetch_actual_value(event_key):
    """
    STEP 3: FETCH ACTUAL WITH RETRY MECHANISM
    Attempts to fetch the actual value for a news event.
    Implements 3-retry mechanism with 2-minute intervals.
    
    Args:
        event_key: The event key to fetch actual for
        
    Returns:
        bool: True if actual was successfully fetched, False if max retries reached
    """
    if event_key not in Globals._Currencies_:
        print(f"ERROR: Event {event_key} not found in _Currencies_")
        return False
    
    event_data = Globals._Currencies_[event_key]
    currency = event_data['currency']
    event_name = event_data['event']
    date_str = event_data['date']
    retry_count = event_data.get('retry_count', 0)
    
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
            Globals._Currencies_[event_key]['retry_count'] = retry_count
            
            if retry_count >= 3:
                print(f"  [MAX RETRIES] Reached maximum retry attempts (3)")
                print(f"  Setting actual to None (data unavailable)")
                Globals._Currencies_[event_key]['actual'] = None
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
                    Globals._Currencies_[event_key]['actual'] = actual
                    print(f"  Stored actual value in _Currencies_[{event_key}]")
                    
                    # STEP 4A: Calculate affect (pass event_key, function will extract currency)
                    calculate_affect(event_key)
                    
                    # STEP 5: Generate trading signals (pass event_key, function will extract currency)
                    trading_signals = generate_trading_decisions(event_key)
                    
                    # STEP 6: Update _Affected_ and _Symbols_ (pass event_key so it can access the data)
                    update_affected_symbols(event_key, trading_signals)
                    
                    return True
                    
                except ValueError:
                    print(f"  [ERROR] Could not parse actual: {actual_str}")
                    return False
            else:
                print(f"  [N/A] Actual not available")
                Globals._Currencies_[event_key]['actual'] = None
                return False
        else:
            print(f"  [ERROR] No actual value found in response")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Exception during fetch: {e}")
        return False


def calculate_affect(event_key):
    """
    STEP 4A: CALCULATE AFFECT
    Determines if the news event strengthens (BULL) or weakens (BEAR) the currency.
    
    Logic:
    - For most indicators: Higher = Better = BULL, Lower = Worse = BEAR
    - For UNEMPLOYMENT: Higher = Worse = BEAR, Lower = Better = BULL (inverse)
    
    Args:
        event_key: The event key (or currency code for backwards compatibility)
    """
    if event_key not in Globals._Currencies_:
        print(f"  [ERROR] Event {event_key} not found in _Currencies_")
        return
    
    event_data = Globals._Currencies_[event_key]
    currency = event_data.get('currency', event_key)  # Extract currency or use key if old format
    forecast = event_data.get('forecast')
    actual = event_data.get('actual')
    event_name = event_data.get('event', '').upper()
    
    print(f"  [STEP 4A] Calculating affect...")
    
    # Check if we have both values
    if forecast is None or actual is None:
        Globals._Currencies_[event_key]['affect'] = "NEUTRAL"
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
    Globals._Currencies_[event_key]['affect'] = affect
    print(f"    {comparison}: {forecast} → {actual} | Type: {'INVERSE' if is_inverse else 'NORMAL'} → Affect: {affect}")


def generate_trading_decisions(event_key):
    """
    STEP 5: GENERATE TRADING SIGNALS
    Uses ChatGPT with News_Rules.txt to determine BUY/SELL signals for all pairs.
    
    Args:
        event_key: The event key (or currency code for backwards compatibility)
        
    Returns:
        dict: Dictionary of pair → action (e.g., {"XAUUSD": "BUY", "EURUSD": "SELL"})
    """
    if event_key not in Globals._Currencies_:
        print(f"  [ERROR] Event {event_key} not found in _Currencies_")
        return {}
    
    event_data = Globals._Currencies_[event_key]
    currency = event_data.get('currency', event_key)  # Extract currency or use key if old format
    event_name = event_data.get('event')
    forecast = event_data.get('forecast')
    actual = event_data.get('actual')
    affect = event_data.get('affect')
    
    print(f"  [STEP 5] Generating trading signals...")
    
    # Check if we should skip (NEUTRAL affect or missing data)
    if affect == "NEUTRAL" or forecast is None or actual is None:
        print(f"    Affect is {affect} - No trading signals")
        return {}
    
    # Call ChatGPT to generate trading signals
    print(f"    Querying ChatGPT with News_Rules.txt...")
    response = generate_trading_signals(currency, event_name, forecast, actual)
    
    print(f"    Response: {response}")
    
    # Parse the response
    trading_signals = {}
    
    # Check if response is NEUTRAL
    if "NEUTRAL" in response.upper() and ":" not in response:
        print(f"    → No trading signals (NEUTRAL)")
        return {}
    
    # Parse format: "PAIR : ACTION, PAIR : ACTION"
    try:
        pairs = response.split(",")
        for pair_action in pairs:
            pair_action = pair_action.strip()
            if ":" in pair_action:
                parts = pair_action.split(":")
                pair = parts[0].strip()
                action = parts[1].strip().upper()
                
                # Validate action
                if action in ["BUY", "SELL"]:
                    trading_signals[pair] = action
                    print(f"    → {pair}: {action}")
                else:
                    print(f"    [WARN] Invalid action '{action}' for {pair}")
        
        if trading_signals:
            print(f"    Generated {len(trading_signals)} trading signal(s)")
        else:
            print(f"    No valid trading signals found")
            
    except Exception as e:
        print(f"    [ERROR] Failed to parse response: {e}")
        return {}
    
    return trading_signals


def update_affected_symbols(event_key, trading_signals):
    """
    STEP 6: UPDATE _Affected_ AND _Symbols_ DICTIONARIES
    Stores trading signals in both dictionaries for trade execution.
    
    Args:
        event_key: The event key (or currency code for backwards compatibility)
        trading_signals: Dictionary of pair → action (e.g., {"XAUUSD": "BUY"})
    """
    if not trading_signals:
        print(f"  [STEP 6] No trading signals to update")
        return
    
    if event_key not in Globals._Currencies_:
        print(f"  [ERROR] Event {event_key} not found in _Currencies_")
        return
    
    event_data = Globals._Currencies_[event_key]
    currency = event_data.get('currency', event_key)  # Extract currency or use key if old format
    event_date = event_data.get('date')
    event_name = event_data.get('event')
    
    print(f"  [STEP 6] Updating _Affected_ and _Symbols_ dictionaries...")
    
    # Process each pair in trading signals
    for pair_name, action in trading_signals.items():
        # Store in _Affected_ dictionary
        Globals._Affected_[pair_name] = {
            "date": event_date,
            "event": event_name,
            "position": action
        }
        print(f"    _Affected_[{pair_name}] = {action}")
        
        # Update _Symbols_ if pair exists
        if pair_name in Globals._Symbols_:
            Globals._Symbols_[pair_name]["verdict_GPT"] = action
            print(f"    _Symbols_[{pair_name}]['verdict_GPT'] = {action}")
        else:
            print(f"    [WARN] {pair_name} not found in _Symbols_ (stored in _Affected_ only)")
    
    print(f"    Updated {len(trading_signals)} pair(s)")


def execute_news_trades(client_id):
    """
    STEP 7: EXECUTE TRADES
    Executes trades for all pairs with verdict_GPT set via enqueue_command.
    
    Args:
        client_id: The MT5 client ID to execute trades for
        
    Returns:
        int: Number of trades queued
    """
    
    trades_queued = 0
    
    # Process each pair in _Symbols_ that has a verdict_GPT
    for pair_name, pair_config in Globals._Symbols_.items():
        verdict = pair_config.get("verdict_GPT", "")
        
        if not verdict or verdict not in ["BUY", "SELL"]:
            continue  # Skip pairs without valid verdict
        
        # Check if this pair already has a queued or executed trade
        if pair_name in Globals._Trades_:
            existing_status = Globals._Trades_[pair_name].get("status")
            if existing_status in ["queued", "executed"]:
                continue  # Skip pairs that already have trades queued or executed
        
        # Get pair configuration
        symbol = pair_config.get("symbol")
        lot = pair_config.get("lot")
        tp = pair_config.get("TP")
        sl = pair_config.get("SL")
        
        # Determine state based on verdict
        if verdict == "BUY":
            state = 1  # OPEN_BUY
        elif verdict == "SELL":
            state = 2  # OPEN_SELL
        else:
            continue  # Skip invalid verdicts
        
        # Generate trade ID and create trade record
        from datetime import datetime
        
        now = datetime.now().isoformat()
        
        # Create trade record using pair name as key
        trade_record = {
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
        
        # Store in Globals._Trades_ with pair name as key
        Globals._Trades_[pair_name] = trade_record
        
        # Also enqueue command for MT5 execution
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
            print(f"    Queued {verdict} for {pair_name} (lot={lot}, TP={tp}, SL={sl})")
            trades_queued += 1
            
        except Exception as e:
            print(f"    [ERROR] Failed to queue {pair_name}: {e}")
    
    if trades_queued > 0:
        print(f"  [STEP 7] Queued {trades_queued} trade(s)")
    
    return trades_queued


def handle_news(client_id, stats):
    """
    Handle news trading mode logic for a client.
    Integrates all 7 steps of the News algorithm.
    
    Args:
        client_id: The MT5 client ID
        stats: Dictionary containing client statistics including 'replies' count
        
    Returns:
        bool: True if a command was injected, False otherwise
    """
    # STEP 1: Initialize forecasts on first run
    initialize_news_forecasts()
    
    # STEP 2: Monitor for events ready to process
    event_to_process = monitor_news_events()
    
    if event_to_process:
        event_data = Globals._Currencies_.get(event_to_process, {})
        currency = event_data.get('currency', event_to_process)
        event_name = event_data.get('event', 'Unknown Event')
        print(f"\n[EVENT READY] {currency} - {event_name}")
        
        # STEP 3-6: Fetch actual, calculate affect, generate signals, update dictionaries
        success = fetch_actual_value(event_to_process)
        
        if success:
            print(f"[SUCCESS] Completed processing for {currency}")
        else:
            print(f"[PENDING] Will retry {currency} later")
    
    # STEP 7: Execute trades for all pairs with verdicts
    # This happens every time handle_news is called (not just when event is ready)
    # so that trades are executed even if multiple events update different pairs
    trades_queued = execute_news_trades(client_id)
    
    # Return True if we queued any trades
    return trades_queued > 0

