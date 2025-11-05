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
from AI_ChatGPT import validate_news_data, generate_trading_signals, generate_trading_signals_multiple


# Global flag to track if initialization has been completed
_initialization_complete = False

# Global dictionary to track event times (for monitoring)
# Format: currency → datetime object
_event_times = {}


# ═══════════════════════════════════════════════════════════════════════════════
# MULTIPLE EVENTS HANDLING (STEP 2 from News_Rules.txt)
# ═══════════════════════════════════════════════════════════════════════════════

def get_events_at_same_time(event_key):
    """
    Find all events for the same currency at the same timestamp.
    
    Args:
        event_key: The event key (e.g., "GBP_202511110200")
        
    Returns:
        list: List of event_keys that share the same currency and timestamp
    """
    if event_key not in Globals._Currencies_:
        return [event_key]
    
    event_data = Globals._Currencies_[event_key]
    currency = event_data['currency']
    event_time = event_data['event_time']
    
    # Find all events for this currency at this exact time
    same_time_events = []
    
    for key, data in Globals._Currencies_.items():
        if (data['currency'] == currency and 
            data['event_time'] == event_time):
            same_time_events.append(key)
    
    return same_time_events


def categorize_event(event_name):
    """
    Determine the impact category of a news event.
    
    Args:
        event_name: The name of the event (e.g., "Interest Rate Decision")
        
    Returns:
        str: Category name (Monetary, Inflation, Jobs, GDP, Trade, Activity, Sentiment)
    """
    event_lower = event_name.lower()
    
    # Monetary
    if any(word in event_lower for word in ['interest rate', 'monetary policy', 'central bank', 'fomc', 'fed', 'boe', 'ecb', 'rba', 'rbnz']):
        return "Monetary"
    
    # Inflation
    if any(word in event_lower for word in ['cpi', 'ppi', 'pce', 'inflation', 'price index', 'consumer price', 'producer price']):
        return "Inflation"
    
    # Jobs
    if any(word in event_lower for word in ['employment', 'unemployment', 'jobless', 'payroll', 'nfp', 'non-farm', 'labor', 'labour']):
        return "Jobs"
    
    # GDP
    if any(word in event_lower for word in ['gdp', 'gross domestic']):
        return "GDP"
    
    # Trade
    if any(word in event_lower for word in ['trade balance', 'current account', 'exports', 'imports']):
        return "Trade"
    
    # Activity
    if any(word in event_lower for word in ['pmi', 'manufacturing', 'industrial', 'retail sales', 'production', 'services']):
        return "Activity"
    
    # Sentiment
    if any(word in event_lower for word in ['sentiment', 'confidence', 'expectations']):
        return "Sentiment"
    
    # Default to Activity if unknown
    return "Activity"


def get_impact_level(category):
    """
    Get the numeric impact level for a category.
    Lower number = higher impact.
    
    Args:
        category: The category name
        
    Returns:
        int: Impact level (1=highest, 7=lowest)
    """
    impact_hierarchy = {
        "Monetary": 1,
        "Inflation": 2,
        "Jobs": 3,
        "GDP": 4,
        "Trade": 5,
        "Activity": 6,
        "Sentiment": 7
    }
    
    return impact_hierarchy.get(category, 99)


def aggregate_simultaneous_events(event_keys):
    """
    Apply STEP 2 from News_Rules.txt: Aggregate multiple events at same time.
    
    Args:
        event_keys: List of event keys that occur at the same timestamp
        
    Returns:
        str: Aggregated outcome ("POSITIVE", "NEGATIVE", or "NEUTRAL")
    """
    if len(event_keys) == 1:
        # Single event - use its affect directly
        return Globals._Currencies_[event_keys[0]].get('affect', 'NEUTRAL')
    
    print(f"\n  [AGGREGATION] Processing {len(event_keys)} events at same time")
    
    # Filter out incomplete events (N/A or None)
    complete_events = []
    for key in event_keys:
        event_data = Globals._Currencies_[key]
        forecast = event_data.get('forecast')
        actual = event_data.get('actual')
        affect = event_data.get('affect')
        
        if forecast is not None and actual is not None and affect != 'NEUTRAL':
            complete_events.append(key)
            print(f"    - {event_data['event']}: {affect}")
        else:
            print(f"    - {event_data['event']}: SKIPPED (incomplete or neutral)")
    
    if not complete_events:
        print(f"    → No complete events, result: NEUTRAL")
        return "NEUTRAL"
    
    # Get affects
    affects = [Globals._Currencies_[key]['affect'] for key in complete_events]
    
    # Check if all same direction
    if all(a == "POSITIVE" for a in affects):
        print(f"    → All events POSITIVE, result: POSITIVE")
        return "POSITIVE"
    
    if all(a == "NEGATIVE" for a in affects):
        print(f"    → All events NEGATIVE, result: NEGATIVE")
        return "NEGATIVE"
    
    # Conflict detected - use impact hierarchy
    print(f"    → Conflict detected, using impact hierarchy")
    
    # Categorize each event and find highest impact
    event_categories = []
    for key in complete_events:
        event_name = Globals._Currencies_[key]['event']
        category = categorize_event(event_name)
        impact = get_impact_level(category)
        event_categories.append({
            'key': key,
            'category': category,
            'impact': impact,
            'affect': Globals._Currencies_[key]['affect']
        })
        print(f"      {event_name}: {category} (impact={impact})")
    
    # Sort by impact (lowest number = highest priority)
    event_categories.sort(key=lambda x: x['impact'])
    
    # Get highest impact level
    highest_impact = event_categories[0]['impact']
    
    # Get all events at highest impact level
    highest_events = [e for e in event_categories if e['impact'] == highest_impact]
    
    if len(highest_events) == 1:
        # Single highest impact event
        result = highest_events[0]['affect']
        print(f"    → {highest_events[0]['category']} wins: {result}")
        return result
    
    # Multiple events at same impact level
    highest_affects = [e['affect'] for e in highest_events]
    
    if len(set(highest_affects)) == 1:
        # All same direction at highest level
        result = highest_affects[0]
        print(f"    → All {highest_events[0]['category']} events agree: {result}")
        return result
    
    # Equal impact conflict
    print(f"    → Equal impact conflict, result: NEUTRAL")
    return "NEUTRAL"


# ═══════════════════════════════════════════════════════════════════════════════
# END MULTIPLE EVENTS HANDLING
# ═══════════════════════════════════════════════════════════════════════════════


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
            
            # Create unique key: currency + event time (readable format)
            # Format: EUR_2025-11-03_04:10
            import hashlib
            event_key = f"{currency}_{event['event_time'].strftime('%Y-%m-%d_%H:%M')}"
            
            # Store in _Currencies_ dictionary with unique key
            Globals._Currencies_[event_key] = {
                'currency': currency,
                'date': date_str,
                'event': event_name,
                'forecast': forecast,
                'actual': None,
                'affect': None,
                'retry_count': 0,
                'NID': None,                 # Assigned when event is processed
                'NID_Affect': 0,             # Count of pairs affected
                'NID_Affect_Executed': 0,    # Count of pairs executed
                'NID_TP': 0,                 # Count of pairs that hit TP
                'NID_SL': 0                  # Count of pairs that hit SL
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
    Gets information about the next upcoming event(s) that hasn't been processed yet.
    
    Returns:
        dict or None: Dictionary with 'events' (list), 'time' keys, or None if no events
    """
    if not _initialization_complete:
        return None
    
    current_time = datetime.now()
    next_time = None
    events_at_next_time = []
    
    # Find the earliest upcoming event time
    for event_key, event_time in _event_times.items():
        if event_key not in Globals._Currencies_:
            continue
        
        event_data = Globals._Currencies_[event_key]
        
        # Skip if already processed (actual is not None)
        if event_data['actual'] is not None:
            continue
        
        # Check if this is the earliest event
        if next_time is None or event_time < next_time:
            next_time = event_time
    
    # If we found a next time, gather all events at that time
    if next_time is not None:
        for event_key, event_time in _event_times.items():
            if event_time == next_time:
                if event_key in Globals._Currencies_:
                    event_data = Globals._Currencies_[event_key]
                    if event_data['actual'] is None:  # Not yet processed
                        events_at_next_time.append({
                            'event_key': event_key,
                            'currency': event_data.get('currency', event_key),
                            'event': event_data['event']
                        })
        
        return {
            'events': events_at_next_time,
            'time': next_time,
            'count': len(events_at_next_time)
        }
    
    return None


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
    
    # Assign NID if not already assigned
    if Globals._Currencies_[event_key].get('NID') is None:
        Globals._News_ID_Counter_ += 1
        nid = Globals._News_ID_Counter_
        Globals._Currencies_[event_key]['NID'] = nid
        print(f"    Assigned NID: {nid}")
    
    print(f"    {comparison}: {forecast} → {actual} | Type: {'INVERSE' if is_inverse else 'NORMAL'} → Affect: {affect}")


def generate_trading_decisions(event_key):
    """
    STEP 5: GENERATE TRADING SIGNALS
    Uses ChatGPT with News_Rules.txt to determine BUY/SELL signals for all pairs.
    Now handles multiple events at the same time using STEP 2 aggregation rules.
    
    Args:
        event_key: The event key
        
    Returns:
        dict: Dictionary of pair → action (e.g., {"XAUUSD": "BUY", "EURUSD": "SELL"})
    """
    if event_key not in Globals._Currencies_:
        print(f"  [ERROR] Event {event_key} not found in _Currencies_")
        return {}
    
    event_data = Globals._Currencies_[event_key]
    currency = event_data.get('currency', event_key)
    
    print(f"  [STEP 5] Generating trading signals...")
    
    # Get all events at the same time
    same_time_events = get_events_at_same_time(event_key)
    
    if len(same_time_events) > 1:
        print(f"    Found {len(same_time_events)} events at same time - aggregating...")
        
        # Aggregate to get final decision
        aggregated_affect = aggregate_simultaneous_events(same_time_events)
        
        if aggregated_affect == "NEUTRAL":
            print(f"    Aggregated result: NEUTRAL - No trading signals")
            return {}
        
        # Build combined event description for AI
        events_desc = []
        for key in same_time_events:
            e = Globals._Currencies_[key]
            if e.get('forecast') is not None and e.get('actual') is not None:
                events_desc.append({
                    'event': e['event'],
                    'forecast': e['forecast'],
                    'actual': e['actual'],
                    'country': e.get('country', 'N/A')
                })
        
        # Call ChatGPT with ALL events
        print(f"    Querying ChatGPT with {len(events_desc)} events...")
        response = generate_trading_signals_multiple(currency, events_desc)
        
    else:
        # Single event - use original logic
        event_name = event_data.get('event')
        forecast = event_data.get('forecast')
        actual = event_data.get('actual')
        affect = event_data.get('affect')
        
        if affect == "NEUTRAL" or forecast is None or actual is None:
            print(f"    Affect is {affect} - No trading signals")
            return {}
        
        print(f"    Querying ChatGPT with News_Rules.txt...")
        response = generate_trading_signals(currency, event_name, forecast, actual)
    
    print(f"    Response: {response}")
    
    # Parse the response (same logic for both single and multiple events)
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
    nid = event_data.get('NID')  # Get the NID for this event
    
    print(f"  [STEP 6] Updating _Affected_ and _Symbols_ dictionaries...")
    
    # Update NID_Affect count
    Globals._Currencies_[event_key]['NID_Affect'] = len(trading_signals)
    print(f"    NID_{nid} affected {len(trading_signals)} pair(s)")
    
    # Process each pair in trading signals
    for pair_name, action in trading_signals.items():
        # Store in _Affected_ dictionary with NID
        Globals._Affected_[pair_name] = {
            "date": event_date,
            "event": event_name,
            "position": action,
            "NID": nid
        }
        print(f"    _Affected_[{pair_name}] = {action} (NID_{nid})")
        
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
    Links each trade to its originating news event via NID.
    
    Args:
        client_id: The MT5 client ID to execute trades for
        
    Returns:
        int: Number of trades queued
    """
    
    trades_queued = 0
    nid_executed_counts = {}  # Track executions per NID
    
    # Process each pair in _Symbols_ that has a verdict_GPT
    for pair_name, pair_config in Globals._Symbols_.items():
        verdict = pair_config.get("verdict_GPT", "")
        
        if not verdict or verdict not in ["BUY", "SELL"]:
            continue  # Skip pairs without valid verdict
        
        # Only queue pairs that are in symbolsToTrade
        if pair_name not in Globals.symbolsToTrade:
            continue  # Skip pairs not in symbolsToTrade
        
        # Check if this pair already has a queued or executed trade
        if pair_name in Globals._Trades_:
            existing_status = Globals._Trades_[pair_name].get("status")
            if existing_status in ["queued", "executed"]:
                continue  # Skip pairs that already have trades queued or executed
        
        # Get NID from _Affected_ dictionary
        nid = None
        event_name = "Unknown"
        if pair_name in Globals._Affected_:
            nid = Globals._Affected_[pair_name].get("NID")
            event_name = Globals._Affected_[pair_name].get("event", "Unknown")
        
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
        
        # Build comment with NID
        comment = f"News:NID_{nid}_{event_name[:20]}" if nid else f"NEWS_{pair_name}"
        
        # Create trade record using pair name as key
        trade_record = {
            "client_id": str(client_id),
            "symbol": symbol,
            "action": verdict,
            "volume": lot,
            "tp": tp,
            "sl": sl,
            "comment": comment,
            "status": "queued",
            "createdAt": now,
            "updatedAt": now,
            "NID": nid  # Link to news event
        }
        
        # Store in Globals._Trades_ with pair name as key
        Globals._Trades_[pair_name] = trade_record
        
        # Track NID execution count
        if nid is not None:
            nid_executed_counts[nid] = nid_executed_counts.get(nid, 0) + 1
        
        # Also enqueue command for MT5 execution
        try:
            enqueue_command(
                client_id,
                state,
                {
                    "symbol": symbol,
                    "volume": lot,
                    "comment": comment,
                    "tpPips": tp,
                    "slPips": sl
                }
            )
            print(f"    Queued {verdict} for {pair_name} (NID_{nid}, lot={lot}, TP={tp}, SL={sl})")
            trades_queued += 1
            
        except Exception as e:
            print(f"    [ERROR] Failed to queue {pair_name}: {e}")
    
    # Update NID_Affect_Executed counts in _Currencies_
    for nid, count in nid_executed_counts.items():
        # Find the event with this NID
        for event_key, event_data in Globals._Currencies_.items():
            if event_data.get('NID') == nid:
                Globals._Currencies_[event_key]['NID_Affect_Executed'] = count
                print(f"  [NID_{nid}] Executed {count} trade(s)")
                break
    
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
    else:
        # Show what event(s) we're waiting for
        next_event_info = get_next_event_info()
        if next_event_info and stats.get('replies', 0) % 10 == 0:  # Print every 10th request to avoid spam
            event_count = next_event_info['count']
            events = next_event_info['events']
            event_time = next_event_info['time']
            from datetime import datetime
            now = datetime.now()
            time_diff = event_time - now
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            
            # Show count in the header
            print(f"\n[WAITING] Next event [{event_count} event(s) at same time]:")
            print(f"  Time until event: {hours}h {minutes}m")
            
            # List all events at that time
            for event in events:
                currency = event['currency']
                event_name = event['event']
                print(f"  - {currency}: {event_name}")
    
    # STEP 7: Execute trades for all pairs with verdicts
    # This happens every time handle_news is called (not just when event is ready)
    # so that trades are executed even if multiple events update different pairs
    trades_queued = execute_news_trades(client_id)
    
    # Return True if we queued any trades
    return trades_queued > 0

