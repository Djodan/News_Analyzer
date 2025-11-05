# NID Tracking System - Implementation Summary

## Overview
The NID (News ID) tracking system enables comprehensive performance analytics for each news event processed by the algorithm. Every event receives a unique identifier that tracks the complete lifecycle from signal generation to trade outcome.

## System Components

### 1. Global Variables (Globals.py)
```python
_News_ID_Counter_ = 0  # Auto-incrementing counter for NID assignment
```

### 2. Data Structures

#### _Currencies_ (Event Storage)
```python
_Currencies_[event_key] = {
    'currency': "EUR",
    'event': "Unemployment Rate",
    'date': "2025, November 03, 04:10",
    'forecast': 4.5,
    'actual': 4.8,
    'affect': "NEGATIVE",
    'retry_count': 0,
    'NID': 5,                    # Unique event identifier
    'NID_Affect': 3,             # Total signals generated
    'NID_Affect_Executed': 2,    # Total trades executed
    'NID_TP': 1,                 # Trades hitting take profit
    'NID_SL': 1                  # Trades hitting stop loss
}
```

#### _Affected_ (Signal Tracking)
```python
_Affected_[pair] = {
    'date': "2025, November 03, 04:10",
    'event': "Unemployment Rate",
    'position': "SHORT",
    'NID': 5                     # Links signal to event
}
```

#### _Trades_ (Trade Tracking)
```python
_Trades_[pair] = {
    'client_id': "DEMO_123",
    'symbol': "EURUSD",
    'action': "SELL",
    'volume': 0.1,
    'tp': 1.0850,
    'sl': 1.0900,
    'comment': "News:NID_5_Unemployment Rate",  # Human-readable NID reference
    'status': "executed",
    'createdAt': "2025-01-15T04:12:00Z",
    'updatedAt': "2025-01-15T04:12:30Z",
    'NID': 5                     # Links trade to event
}
```

## Tracking Lifecycle

### Phase 1: NID Assignment (News.py - calculate_affect)
```python
Globals._News_ID_Counter_ += 1
nid = Globals._News_ID_Counter_
event_data['NID'] = nid
event_data['NID_Affect'] = 0
event_data['NID_Affect_Executed'] = 0
event_data['NID_TP'] = 0
event_data['NID_SL'] = 0
```

### Phase 2: Signal Tracking (News.py - update_affected_symbols)
```python
# For each pair receiving a signal
_Affected_[pair] = {
    'date': event_date,
    'event': event_name,
    'position': position,
    'NID': nid
}

# Update counter
_Currencies_[event_key]['NID_Affect'] += 1
```

### Phase 3: Execution Tracking (News.py - execute_news_trades)
```python
# For each trade actually executed
_Trades_[pair] = {
    ...,
    'comment': f"News:NID_{nid}_{event_name}",
    'NID': nid
}

# Update counter
_Currencies_[event_key]['NID_Affect_Executed'] += 1
```

### Phase 4: Outcome Tracking (Functions.py - record_trade_outcome)
```python
# Called when MT5 reports trade closure
if outcome == "TP":
    _Currencies_[event_key]['NID_TP'] += 1
elif outcome == "SL":
    _Currencies_[event_key]['NID_SL'] += 1
```

## API Integration

### Endpoint: POST /trade_outcome
MT5 must call this endpoint when a trade closes.

**Request:**
```json
{
    "symbol": "EURUSD",
    "outcome": "TP"    // "TP" or "SL"
}
```

**Success Response:**
```json
{
    "ok": true,
    "symbol": "EURUSD",
    "NID": 5,
    "outcome": "TP"
}
```

**Error Responses:**
```json
// Trade not found in _Trades_
{
    "ok": false,
    "error": "trade_not_found",
    "symbol": "EURUSD"
}

// Trade has no NID assigned
{
    "ok": false,
    "error": "no_nid",
    "symbol": "EURUSD"
}

// Event not found in _Currencies_
{
    "ok": false,
    "error": "event_not_found",
    "symbol": "EURUSD",
    "NID": 5
}
```

## Example Flow

### Scenario: EUR Unemployment Rate Event

1. **Event Processed**
   ```
   NID = 5 assigned
   Event: EUR Unemployment Rate
   Forecast: 4.5%, Actual: 4.8%
   Affect: NEGATIVE (worse than expected)
   ```

2. **Signals Generated**
   ```
   EURUSD: SHORT → NID_Affect = 1
   EURJPY: SHORT → NID_Affect = 2
   EURGBP: SHORT → NID_Affect = 3
   ```

3. **Trades Executed**
   ```
   EURUSD: ✓ Allowed → NID_Affect_Executed = 1
   EURJPY: ✓ Allowed → NID_Affect_Executed = 2
   EURGBP: ✗ Already open → Skipped
   ```

4. **Trade Outcomes**
   ```
   EURUSD: Hits TP → NID_TP = 1
   EURJPY: Hits SL → NID_SL = 1
   ```

### Final Metrics for NID_5:
```
Total Signals: 3 pairs
Execution Rate: 2/3 = 66.7%
Win Rate: 1/2 = 50%
TP Count: 1
SL Count: 1
```

## Analytics Capabilities

### 1. Find Specific Event Performance
```python
def get_event_performance(nid):
    for event_key, data in Globals._Currencies_.items():
        if data.get('NID') == nid:
            executed = data.get('NID_Affect_Executed', 0)
            tp = data.get('NID_TP', 0)
            sl = data.get('NID_SL', 0)
            win_rate = tp / (tp + sl) if (tp + sl) > 0 else 0
            
            return {
                'event': data['event'],
                'currency': data['currency'],
                'signals': data.get('NID_Affect', 0),
                'executed': executed,
                'tp': tp,
                'sl': sl,
                'win_rate': win_rate
            }
    return None
```

### 2. Overall System Win Rate
```python
def calculate_overall_winrate():
    total_tp = sum(d.get('NID_TP', 0) for d in Globals._Currencies_.values())
    total_sl = sum(d.get('NID_SL', 0) for d in Globals._Currencies_.values())
    total_trades = total_tp + total_sl
    
    if total_trades == 0:
        return 0
    
    return (total_tp / total_trades) * 100
```

### 3. Best Performing Event Types
```python
from collections import defaultdict

def analyze_event_types():
    event_stats = defaultdict(lambda: {'tp': 0, 'sl': 0, 'count': 0})
    
    for data in Globals._Currencies_.values():
        event_type = data.get('event')
        event_stats[event_type]['tp'] += data.get('NID_TP', 0)
        event_stats[event_type]['sl'] += data.get('NID_SL', 0)
        event_stats[event_type]['count'] += 1
    
    results = []
    for event_type, stats in event_stats.items():
        total = stats['tp'] + stats['sl']
        win_rate = stats['tp'] / total if total > 0 else 0
        results.append({
            'event': event_type,
            'occurrences': stats['count'],
            'tp': stats['tp'],
            'sl': stats['sl'],
            'win_rate': win_rate
        })
    
    return sorted(results, key=lambda x: x['win_rate'], reverse=True)
```

### 4. Currency Performance
```python
def analyze_currency_performance():
    currency_stats = defaultdict(lambda: {'tp': 0, 'sl': 0, 'events': 0})
    
    for data in Globals._Currencies_.values():
        currency = data.get('currency')
        currency_stats[currency]['tp'] += data.get('NID_TP', 0)
        currency_stats[currency]['sl'] += data.get('NID_SL', 0)
        currency_stats[currency]['events'] += 1
    
    for currency, stats in currency_stats.items():
        total = stats['tp'] + stats['sl']
        win_rate = stats['tp'] / total if total > 0 else 0
        print(f"{currency}: {stats['events']} events, Win Rate: {win_rate:.1%}")
```

## Console Output Examples

### Event Processing
```
[NID_5] EUR Unemployment Rate: NEGATIVE
[NID_5] Generated 3 signal(s)
```

### Trade Execution
```
[NID_5] Executed 2 trade(s)
```

### Trade Outcomes
```
[NID_5] TP hit! Total TPs: 1
[NID_5] SL hit! Total SLs: 1
Server: Trade EURUSD closed at TP (NID_5)
```

## Testing Checklist

- [ ] NID assigned when event processed
- [ ] NID_Affect increments for each signal
- [ ] NID_Affect_Executed increments for each trade
- [ ] NID included in trade comment
- [ ] NID_TP increments when TP hit
- [ ] NID_SL increments when SL hit
- [ ] Analytics functions work correctly
- [ ] MT5 integration sends /trade_outcome correctly
- [ ] Server logs NID information properly

## Files Modified

1. **Globals.py**
   - Added `_News_ID_Counter_`
   - Updated `_Currencies_` documentation
   - Updated `_Affected_` documentation
   - Updated `_Trades_` documentation

2. **News.py**
   - Modified `calculate_affect()` - NID assignment
   - Modified `update_affected_symbols()` - NID_Affect tracking
   - Modified `execute_news_trades()` - NID_Affect_Executed tracking

3. **Functions.py**
   - Added `record_trade_outcome()` - TP/SL tracking

4. **Server.py**
   - Added `/trade_outcome` endpoint

5. **NEWS_ALGORITHM_FLOW.txt**
   - Added comprehensive NID documentation

## Benefits

1. **Performance Tracking**: Know which events are profitable
2. **Event Analysis**: Identify best/worst event types
3. **Currency Analysis**: See which currencies trade better
4. **Execution Rate**: Track signal-to-execution conversion
5. **Win Rate**: Calculate TP/SL ratio per event
6. **Debugging**: Link trades back to originating events
7. **Optimization**: Data-driven strategy refinement

## Next Steps

1. Implement MT5 side to send `/trade_outcome` requests
2. Create analytics dashboard/report
3. Add NID to log files for auditing
4. Export NID metrics to CSV for analysis
5. Build performance visualization tools
