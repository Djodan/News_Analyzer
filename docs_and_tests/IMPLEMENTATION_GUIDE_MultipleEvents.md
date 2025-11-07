# Implementation Guide: Multiple Events at Same Time

This guide shows how to integrate the **STEP 2: Multiple Events at Same Time** logic from News_Rules.txt into News.py.

---

## Overview

**Problem:** When multiple high-impact news events occur at the same timestamp for the same currency (e.g., GBP Unemployment + Employment Change both at 02:00), the system currently:
- Processes each event separately
- May generate conflicting signals
- Could queue multiple trades for the same currency

**Solution:** Aggregate events at the same timestamp and apply the impact hierarchy rules to produce ONE consolidated decision.

---

## Architecture Changes

### Current Flow
```
Event 1 (GBP 02:00) → Fetch Actual → Calculate Affect → Generate Signals → Queue Trades
Event 2 (GBP 02:00) → Fetch Actual → Calculate Affect → Generate Signals → Queue Trades
                                                                              ↓
                                                                    DUPLICATE TRADES!
```

### New Flow
```
Event 1 (GBP 02:00) ┐
Event 2 (GBP 02:00) ├─→ Group → Aggregate → Single Decision → Queue Once
Event 3 (GBP 02:00) ┘
```

---

## Implementation Steps

### STEP 1: Add Helper Function to Group Events by Timestamp

Add this function to News.py:

```python
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
```

### STEP 2: Add Function to Categorize Events by Impact

```python
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
    if any(word in event_lower for word in ['interest rate', 'monetary policy', 'central bank', 'fomc', 'fed']):
        return "Monetary"
    
    # Inflation
    if any(word in event_lower for word in ['cpi', 'ppi', 'pce', 'inflation', 'price index']):
        return "Inflation"
    
    # Jobs
    if any(word in event_lower for word in ['employment', 'unemployment', 'jobless', 'payroll', 'nfp']):
        return "Jobs"
    
    # GDP
    if any(word in event_lower for word in ['gdp', 'gross domestic']):
        return "GDP"
    
    # Trade
    if any(word in event_lower for word in ['trade balance', 'current account', 'exports', 'imports']):
        return "Trade"
    
    # Activity
    if any(word in event_lower for word in ['pmi', 'manufacturing', 'industrial', 'retail sales', 'production']):
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
```

### STEP 3: Add Function to Aggregate Multiple Events

```python
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
```

### STEP 4: Modify generate_trading_decisions() to Use Aggregation

Replace the current `generate_trading_decisions()` function with:

```python
def generate_trading_decisions(event_key):
    """
    STEP 5: GENERATE TRADING SIGNALS
    Uses ChatGPT with News_Rules.txt to determine BUY/SELL signals for all pairs.
    Now handles multiple events at the same time.
    
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
                    'actual': e['actual']
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
    
    # Parse the response (same logic as before)
    trading_signals = {}
    
    if "NEUTRAL" in response.upper() and ":" not in response:
        print(f"    → No trading signals (NEUTRAL)")
        return {}
    
    try:
        pairs = response.split(",")
        for pair_action in pairs:
            pair_action = pair_action.strip()
            if ":" in pair_action:
                parts = pair_action.split(":")
                pair = parts[0].strip()
                action = parts[1].strip().upper()
                
                if action in ["BUY", "SELL"]:
                    trading_signals[pair] = action
                    print(f"    → {pair}: {action}")
        
        if trading_signals:
            print(f"    Generated {len(trading_signals)} trading signal(s)")
            
    except Exception as e:
        print(f"    [ERROR] Failed to parse response: {e}")
        return {}
    
    return trading_signals
```

### STEP 5: Add New AI Function for Multiple Events

```python
def generate_trading_signals_multiple(currency, events):
    """
    Call ChatGPT with MULTIPLE events at the same time.
    
    Args:
        currency: The currency code (e.g., "GBP")
        events: List of dicts with keys: event, forecast, actual
        
    Returns:
        str: Trading signals in format "PAIR : ACTION, PAIR : ACTION"
    """
    # Load News_Rules.txt
    try:
        with open("News_Rules.txt", "r", encoding="utf-8") as f:
            rules = f.read()
    except FileNotFoundError:
        print("ERROR: News_Rules.txt not found")
        return "NEUTRAL"
    
    # Build events description
    events_desc = "\n".join([
        f"- {currency} {e['event']}: Forecast={e['forecast']}, Actual={e['actual']}"
        for e in events
    ])
    
    # Get available pairs
    pairs = list(Globals._Symbols_.keys())
    pairs_str = ", ".join(pairs)
    
    # Build prompt
    prompt = f"""
{rules}

═══════════════════════════════════════════════════════════════════════════════

MULTIPLE EVENTS AT SAME TIME:

{events_desc}

Available trading pairs: {pairs_str}

Remember STEP 2: Multiple Events at the Same Time rules.

Output your trading decision:
"""
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=Globals.API_KEY_GPT)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a forex trading signal generator. Follow the rules exactly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"ERROR calling ChatGPT: {e}")
        return "NEUTRAL"
```

---

## Testing the Implementation

### Test Case 1: Same Direction Events
```python
# Setup: Two positive GBP events at 02:00
Globals._Currencies_['GBP_202511110200_1'] = {
    'currency': 'GBP',
    'event': 'Unemployment Rate',
    'event_time': datetime(2025, 11, 11, 2, 0),
    'forecast': 4.5,
    'actual': 4.2,
    'affect': 'POSITIVE'
}

Globals._Currencies_['GBP_202511110200_2'] = {
    'currency': 'GBP',
    'event': 'Employment Change',
    'event_time': datetime(2025, 11, 11, 2, 0),
    'forecast': 50000,
    'actual': 75000,
    'affect': 'POSITIVE'
}

# Expected: aggregate_simultaneous_events returns "POSITIVE"
# Expected: AI generates BUY signals for GBPAUD, GBPJPY, etc.
```

### Test Case 2: Conflicting Events
```python
# Setup: Monetary vs Activity conflict
Globals._Currencies_['GBP_202511110200_1'] = {
    'currency': 'GBP',
    'event': 'Interest Rate Decision',
    'event_time': datetime(2025, 11, 11, 2, 0),
    'forecast': 5.00,
    'actual': 5.25,
    'affect': 'POSITIVE',
    'category': 'Monetary'
}

Globals._Currencies_['GBP_202511110200_2'] = {
    'currency': 'GBP',
    'event': 'Retail Sales',
    'event_time': datetime(2025, 11, 11, 2, 0),
    'forecast': 0.5,
    'actual': 0.1,
    'affect': 'NEGATIVE',
    'category': 'Activity'
}

# Expected: Monetary wins (impact level 1 beats 6)
# Expected: aggregate returns "POSITIVE"
# Expected: BUY signals
```

---

## Integration Checklist

- [ ] Add `get_events_at_same_time()` function
- [ ] Add `categorize_event()` function
- [ ] Add `get_impact_level()` function
- [ ] Add `aggregate_simultaneous_events()` function
- [ ] Add `generate_trading_signals_multiple()` function
- [ ] Modify `generate_trading_decisions()` to use aggregation
- [ ] Test with real calendar events (e.g., Nov 11 02:00 GBP events)
- [ ] Verify only ONE set of trades queued per currency per timestamp
- [ ] Verify impact hierarchy works correctly
- [ ] Verify NEUTRAL returned for equal-impact conflicts

---

## Expected Behavior After Implementation

### Before
```
[02:00] GBP Unemployment Rate: POSITIVE → Queue GBPAUD BUY
[02:00] GBP Employment Change: POSITIVE → Queue GBPAUD BUY (DUPLICATE!)
```

### After
```
[02:00] Found 2 GBP events at same time
[02:00] Aggregating: Unemployment POSITIVE, Employment POSITIVE
[02:00] Result: POSITIVE (all agree)
[02:00] Queue: GBPAUD BUY, GBPJPY BUY, GBPUSD BUY (ONE TIME)
```

---

## Notes

- The aggregation happens BEFORE calling the AI
- The AI receives ALL events at once so it can apply STEP 2 rules
- Events are grouped by currency + timestamp (not just currency)
- Incomplete events (N/A) are filtered out before aggregation
- If all events incomplete → NEUTRAL (no trade)
- Impact hierarchy prevents random decisions when events conflict

