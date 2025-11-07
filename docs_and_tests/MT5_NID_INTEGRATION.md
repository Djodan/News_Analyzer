# MT5 NID Tracking Integration

## Overview
The MT5 Expert Advisor has been enhanced to automatically send trade outcome notifications (TP/SL) to the Python server, enabling the NID (News ID) tracking system to record complete performance metrics for each news event.

## Implementation Details

### 1. HTTP Communication (Http.mqh)

**New Function: `SendTradeOutcome()`**
```cpp
bool SendTradeOutcome(string symbol, string outcome, string serverIP, int serverPort)
```

**Purpose:** Sends a POST request to the Python server when a trade closes at TP or SL.

**Parameters:**
- `symbol`: Trading pair (e.g., "EURUSD", "GBPAUD")
- `outcome`: Either "TP" or "SL"
- `serverIP`: Python server IP address (from `ServerIP` input parameter)
- `serverPort`: Python server port (from `ServerPort` input parameter)

**Endpoint:** `POST http://{serverIP}:{serverPort}/trade_outcome`

**Payload:**
```json
{
    "symbol": "EURUSD",
    "outcome": "TP"
}
```

**Response Codes:**
- `200`: Success - NID metrics updated
- `400`: Error - trade not found, no NID, or invalid payload
- Other: Network or server error

### 2. TP/SL Detection (Trades.mqh)

**New Function: `DetectTPSLClosure()`**
```cpp
string DetectTPSLClosure(string symbol, ulong positionId, double closePrice, string comment)
```

**Purpose:** Intelligently detects whether a trade closed at Take Profit or Stop Loss using multiple methods.

**Detection Methods (in order of precedence):**

1. **Comment Analysis (Primary)**
   - Checks for MT5's automatic `[tp]` or `[sl]` markers
   - Looks for standalone "tp" or "sl" keywords in comment
   - Case-insensitive with word boundary detection

2. **Price Comparison (Fallback)**
   - Compares close price with original TP/SL values
   - Uses 10-point tolerance to account for slippage
   - Only triggers if TP/SL was set (> 0)

3. **Manual Close Detection**
   - Returns empty string `""` if neither method matches
   - Prevents false positives for manually closed trades

**Returns:**
- `"TP"` - Trade hit Take Profit
- `"SL"` - Trade hit Stop Loss
- `""` - Manual close or undetermined

### 3. Trade Event Handler (News_Analyzer.mq5)

**Modified Function: `OnTradeTransaction()`**

**Flow:**
```
1. Trade closes (DEAL_ENTRY_OUT detected)
   ↓
2. Get deal details (symbol, price, comment, positionId)
   ↓
3. Call DetectTPSLClosure()
   ↓
4. If outcome is "TP" or "SL":
   - Print notification to Experts tab
   - Call SendTradeOutcome()
   - Python server updates NID_TP or NID_SL counter
   ↓
5. Add to closed trades tracking
```

**Example Console Output:**
```
Trade closed at TP: EURUSD at price 1.08500
Trade outcome sent: EURUSD -> TP (NID tracking updated)
```

## Data Flow

### Complete Lifecycle Example

**Event: EUR Unemployment Rate (NID_5)**

1. **Event Processing (Python)**
   ```python
   NID = 5 assigned
   Event: EUR Unemployment Rate
   Forecast: 4.5%, Actual: 4.8%
   Affect: NEGATIVE
   ```

2. **Signal Generation (Python)**
   ```python
   EURUSD: SHORT → NID_Affect = 1
   EURJPY: SHORT → NID_Affect = 2
   ```

3. **Trade Execution (Python → MT5)**
   ```python
   EURUSD: Queued → NID_Affect_Executed = 1
   EURJPY: Queued → NID_Affect_Executed = 2
   ```

4. **MT5 Opens Trades**
   ```
   Open EURUSD SELL 0.1 lots
   TP: 1.0850, SL: 1.0900
   Comment: "News:NID_5_Unemployment Rate"
   ```

5. **Trade Closure (MT5 → Python)**
   ```
   EURUSD hits TP at 1.0850
   → OnTradeTransaction() triggered
   → DetectTPSLClosure() returns "TP"
   → SendTradeOutcome("EURUSD", "TP")
   
   Python receives: POST /trade_outcome
   → record_trade_outcome() called
   → NID_TP incremented: NID_TP = 1
   ```

6. **Final Metrics (Python)**
   ```python
   _Currencies_["EUR_2025-11-03_04:10"] = {
       'NID': 5,
       'NID_Affect': 2,
       'NID_Affect_Executed': 2,
       'NID_TP': 1,
       'NID_SL': 1
   }
   # Win Rate: 50%
   ```

## Configuration

### MT5 Settings Required

1. **WebRequest Permissions**
   - Go to: Tools → Options → Expert Advisors
   - Enable: "Allow WebRequest for listed URL"
   - Add: `http://127.0.0.1:5000` (or your server URL)

2. **Input Parameters**
   ```cpp
   ServerIP = "127.0.0.1"
   ServerPort = 5000
   SendToServer = true  // Must be enabled
   ```

### Python Server Settings

Ensure server is running on the configured host/port:
```python
# Globals.py
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
```

Start server:
```bash
python Server.py
```

## Error Handling

### MT5 Side

**HTTP Request Failures:**
```cpp
Failed to send trade outcome: code=0 symbol=EURUSD outcome=TP
```
**Causes:**
- WebRequest not allowed for URL
- Server not running
- Network issues

**Solution:**
- Check WebRequest permissions
- Verify server is running: `python Server.py`
- Check firewall settings

### Python Side

**Trade Not Found:**
```json
{"ok": false, "error": "trade_not_found", "symbol": "EURUSD"}
```
**Cause:** Symbol not in `_Trades_` dictionary

**No NID:**
```json
{"ok": false, "error": "no_nid", "symbol": "EURUSD"}
```
**Cause:** Trade was opened before NID system was implemented

**Event Not Found:**
```json
{"ok": false, "error": "event_not_found", "symbol": "EURUSD", "NID": 5}
```
**Cause:** Event removed from `_Currencies_` or NID mismatch

## Testing

### Manual Testing

1. **Start Python Server**
   ```bash
   cd News_Analyzer
   python Server.py
   ```

2. **Attach EA to Chart**
   - Enable "SendToServer" in inputs
   - Verify server connection in Experts tab

3. **Execute Test Trade**
   ```cpp
   // Manually open a trade with TP/SL
   // Wait for TP or SL to hit
   // Check Experts tab for output
   ```

4. **Verify Output**
   
   **MT5 Console:**
   ```
   Trade closed at TP: EURUSD at price 1.08500
   Trade outcome sent: EURUSD -> TP (NID tracking updated)
   ```
   
   **Python Console:**
   ```
   [NID_5] TP hit! Total TPs: 1
   Server: Trade EURUSD closed at TP (NID_5)
   ```

### Automated Testing

**Test TP Detection:**
```python
# Create test event
event_key = "EUR_2025-11-05_10:00"
_Currencies_[event_key] = {
    'NID': 999,
    'NID_TP': 0,
    'NID_SL': 0
}

# Create test trade
_Trades_["EURUSD"] = {
    'NID': 999,
    'status': 'executed'
}

# Simulate TP hit
result = record_trade_outcome("EURUSD", "TP")
assert result['ok'] == True
assert _Currencies_[event_key]['NID_TP'] == 1
```

## Debugging

### Enable Verbose Logging

**MT5 Side (Http.mqh):**
```cpp
// Uncomment for debugging
Print("Sending trade outcome: ", symbol, " -> ", outcome);
Print("Request URL: ", url);
Print("Response code: ", code, " body: ", respBody);
```

**Python Side (Functions.py):**
```python
# Already included in record_trade_outcome()
print(f"[DEBUG] Trade outcome: {symbol} -> {outcome}")
print(f"[DEBUG] Found NID: {nid}")
print(f"[DEBUG] Event key: {event_key}")
```

### Common Issues

**Issue:** Trade outcomes not being sent
**Check:**
- Is `SendToServer = true`?
- Is trade closing naturally (not manual)?
- Check MT5 Experts tab for errors

**Issue:** Server receiving but not updating
**Check:**
- Symbol name matches exactly (case-sensitive)
- Trade exists in `_Trades_`
- NID is not null
- Event still exists in `_Currencies_`

**Issue:** TP/SL detection failing
**Check:**
- Are TP/SL values set when opening trade?
- Is tolerance sufficient (10 points)?
- Check deal comment for MT5 indicators

## Performance Metrics Available

With NID tracking fully implemented, you can now query:

1. **Event Performance**
   ```python
   event = _Currencies_["EUR_2025-11-03_04:10"]
   win_rate = event['NID_TP'] / (event['NID_TP'] + event['NID_SL'])
   print(f"Win Rate: {win_rate:.1%}")
   ```

2. **Execution Rate**
   ```python
   exec_rate = event['NID_Affect_Executed'] / event['NID_Affect']
   print(f"Execution Rate: {exec_rate:.1%}")
   ```

3. **Overall Statistics**
   ```python
   total_tp = sum(e.get('NID_TP', 0) for e in _Currencies_.values())
   total_sl = sum(e.get('NID_SL', 0) for e in _Currencies_.values())
   overall_wr = total_tp / (total_tp + total_sl) if (total_tp + total_sl) > 0 else 0
   print(f"Overall Win Rate: {overall_wr:.1%}")
   ```

4. **Best Events**
   ```python
   # Sort events by win rate
   events = []
   for key, data in _Currencies_.items():
       tp = data.get('NID_TP', 0)
       sl = data.get('NID_SL', 0)
       if tp + sl > 0:
           wr = tp / (tp + sl)
           events.append((data['event'], wr, tp, sl))
   
   events.sort(key=lambda x: x[1], reverse=True)
   for event, wr, tp, sl in events[:5]:
       print(f"{event}: {wr:.1%} ({tp}W/{sl}L)")
   ```

## Files Modified

1. **Http.mqh**
   - Added `SendTradeOutcome()` function

2. **Trades.mqh**
   - Added `DetectTPSLClosure()` function
   - Added `IsAlpha()` helper function

3. **News_Analyzer.mq5**
   - Enhanced `OnTradeTransaction()` to detect and send TP/SL outcomes

## Next Steps

1. **Analytics Dashboard**
   - Create GUI to display NID metrics
   - Real-time win rate tracking
   - Event performance comparison

2. **Export Functionality**
   - Save NID data to CSV
   - Generate performance reports
   - Historical analysis tools

3. **ML Integration**
   - Train models on successful events
   - Predict event profitability
   - Optimize signal generation

## Support

For issues or questions:
1. Check MT5 Experts tab for error messages
2. Check Python console for server logs
3. Verify WebRequest permissions
4. Ensure server is running and accessible
5. Test with manual trades first
