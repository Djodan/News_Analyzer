# ConnectionAbortedError Replication Test

## Purpose
This test environment is set up to replicate the `ConnectionAbortedError: [WinError 10053]` that occurred across multiple strategy tests (S2, S3, S4).

## Error Pattern Observed
The error occurs when the Python server tries to send a response to MT5 EA:
```
Exception occurred during processing of request from ('127.0.0.1', 64083)
Traceback (most recent call last):
  ...
  File "Server.py", line 238, in _send_json
    self.wfile.write(json.dumps(payload).encode("utf-8"))
ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine
```

## Current Configuration

**Globals.py:**
- `liveMode = False` ✓
- `TestingMode = True` ✓
- `ModeSelect = "TestingMode"` ✓ (BYPASSES News algorithm entirely)
- `news_strategy = 0` (S0 - ignored when using TestingMode)
- `symbolsToTrade`: 30 pairs configured (USD majors, crosses, gold)
- **NO calendar_statement.csv needed** - TestingMode injects trades directly

**TestingMode.py:**
- Configured to open ONE position per symbol in `symbolsToTrade`
- Will trigger on first EA heartbeat (reply count = 1)
- Bypasses all News logic (no AI calls, no event processing)
- Uses `open_all_symbols_simple(client_id)` function

**How It Works:**
TestingMode completely bypasses the News algorithm. When EA connects:
1. EA sends first heartbeat (reply count = 1)
2. Server detects `ModeSelect = "TestingMode"`
3. Executes `open_all_symbols_simple(client_id)`
4. Opens 30 positions (one per symbol)
5. Sends 30 trading commands via single HTTP response
6. **This large response is where ConnectionAbortedError occurred**

## Test Procedure

### ⚡ Quick Start (Everything Already Configured)

**NO MANUAL SETUP REQUIRED** - Just run the server:

```powershell
cd "C:\Users\dmavi\AppData\Roaming\MetaQuotes\Terminal\36A64B8C79A6163D85E6173B54096685\MQL5\Experts\News_Analyzer"
python Server.py
```

Then start your MT5 EA with matching client ID.

### What Happens Automatically
Then start your MT5 EA with matching client ID.

### What Happens Automatically

When EA connects (first heartbeat):
1. Server logs: `TESTING MODE: ConnectionAbortedError Replication Test`
2. Opens 30 positions (one per symbol in `symbolsToTrade`)
3. Each position: BUY/SELL based on `manual_position` in `_Symbols_`
4. Sends all commands in single HTTP response
5. **Watch for ConnectionAbortedError during response transmission**

### Monitor Output
### Monitor Output

Watch the terminal for:

✅ **Normal Flow:**
```
================================================================================
TESTING MODE: ConnectionAbortedError Replication Test
================================================================================
Opening ONE position per symbol to test for ConnectionAbortedError
Monitor the output log for any exceptions during HTTP response
================================================================================

[TestingMode] === Opening positions for 30 symbols ===
[TestingMode] Opening EURUSD...
[TestingMode] ✅ Opening position: BUY EURUSD 1.2 lots (TP=400, SL=200)
  ✓ Opened: EURUSD - 1.2 lots
[TestingMode] Opening GBPUSD...
... (repeat for all 30 symbols)

[TestingMode] Auto-opened 30 position(s) from symbolsToTrade
Server: Sending BUY command to Client: [4] - EURUSD Vol=1.2 TP=400 SL=200
... (repeat for all commands)
```

❌ **Error Pattern:**
```
Server: Sending BUY command to Client: [4] - SYMBOL Vol=X TP=X SL=X
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', XXXXX)
Traceback (most recent call last):
  ...
  File "Server.py", line 238, in _send_json
    self.wfile.write(json.dumps(payload).encode("utf-8"))
ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine
```

### Analyze Results

**If error DOES occur:**
- ✅ Confirms it's a reproducible issue
- Likely causes:
  1. MT5 EA timeout during response wait
  2. Network buffer overflow (too much data in response)
  3. EA socket closure before Python finishes sending
  4. Windows firewall/antivirus interference
- Next steps:
  - Add retry logic to server response
  - Implement chunked responses for large payloads
  - Add connection keepalive

**If error DOES NOT occur:**
- ✅ It was likely a transient network glitch
- ✅ Current error handling is adequate (already logs exception)
- No code changes needed

## Modifying the Test

### Test More Positions
Edit `TestingMode.py` line ~670:
```python
# Change from:
opened_count = open_all_symbols_simple(client_id)

# To stress test with multiple positions:
opened_count = open_all_symbols_from_config(client_id, 4, [2, 3])
```

### Test Alternative Finder Scenario
Edit `TestingMode.py` line ~670:
```python
# Change from:
opened_count = open_all_symbols_simple(client_id)

# To test alternative finder:
opened_count = open_with_alternative_finder(client_id)
```

## Reset After Test

To return to normal operation:
```python
# In Globals.py
TestingMode = False
liveMode = True  # If going live
```

## Notes
- The error was seen across S2, S3, S4 tests, suggesting it's not strategy-specific
- It occurs during HTTP response transmission (not request reception)
- Python server's exception handler already logs it properly
- The error is benign (doesn't crash server, just logs exception)
- EA should have its own timeout/retry logic to handle this

## Expected Outcome
This test will determine if the ConnectionAbortedError is:
1. **Reproducible** → Requires code fix (better error handling, retry logic)
2. **One-time glitch** → No action needed (already handled gracefully)
