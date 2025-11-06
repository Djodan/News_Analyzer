# MQL5 Client Auto-Reset Implementation Guide

## Overview
The News Analyzer EA now automatically detects server disconnection and performs cleanup operations without manual intervention.

## Features Implemented

### 1. **Server Disconnection Detection**
The EA monitors HTTP error codes to detect when the Python server is unavailable:

**Error Codes Monitored:**
- `code=1001` + `lastError=4006` - Connection error (primary indicator)
- `code=0` + `lastError=4006` - No connection
- `code=0` + `lastError=5203` - Cannot connect to server
- `lastError=4014` - Function not confirmed
- `lastError=5203` - Cannot connect to server

**Detection Points:**
- `SendArrays()` - When sending trade snapshots fails
- `ProcessServerCommand()` - When polling for commands fails

### 2. **Automatic Cleanup (PerformAutoReset)**
When server disconnection is detected, the EA automatically:

1. **Closes All Open Positions**
   - Iterates through all tracked positions
   - Closes each position using `ClosePositionByTicket()`
   - Logs each closure with ticket, symbol, type, and volume
   - Reports total positions closed

2. **Resets All Tracking Variables**
   - **Open trades arrays** (11 arrays):
     - `openTickets[]`, `openSymbols[]`, `openTypes[]`, `openVolumes[]`
     - `openOpenPrices[]`, `openCurrentPrices[]`, `openSLs[]`, `openTPs[]`
     - `openOpenTimes[]`, `openMagics[]`, `openComments[]`
   
   - **Closed offline arrays** (10 arrays):
     - `closedOfflineDeals[]`, `closedOfflineSymbols[]`, `closedOfflineTypes[]`
     - `closedOfflineVolumes[]`, `closedOfflineOpenPrices[]`, `closedOfflineClosePrices[]`
     - `closedOfflineProfits[]`, `closedOfflineSwaps[]`, `closedOfflineCommissions[]`
     - `closedOfflineCloseTimes[]`
   
   - **Closed online arrays** (10 arrays):
     - `closedOnlineDeals[]`, `closedOnlineSymbols[]`, `closedOnlineTypes[]`
     - `closedOnlineVolumes[]`, `closedOnlineOpenPrices[]`, `closedOnlineClosePrices[]`
     - `closedOnlineProfits[]`, `closedOnlineSwaps[]`, `closedOnlineCommissions[]`
     - `closedOnlineCloseTimes[]`

3. **Logs Cleanup Actions**
   - Detailed console output showing each step
   - Position closure confirmations
   - Array reset confirmations
   - Final completion message

### 3. **Automatic Reconnection Support**
The EA can automatically reconnect when the server comes back online:

- Sets `g_ServerDisconnected = true` when disconnection detected
- Resets `g_ServerDisconnected = false` on successful HTTP requests
- Prevents redundant auto-reset calls
- Allows seamless server restart without EA removal

## Usage Workflow

### Testing Cycle (Before Auto-Reset)
1. Start Python server
2. Attach News Analyzer EA to chart
3. Test trades open
4. Stop server to make changes
5. **Manually remove EA from chart** ❌
6. **Manually close all positions** ❌
7. Restart server
8. Re-attach EA

### Testing Cycle (With Auto-Reset)
1. Start Python server
2. Attach News Analyzer EA to chart
3. Test trades open
4. Stop server to make changes
5. **EA automatically closes positions and resets** ✅
6. Restart server
7. **EA automatically reconnects** ✅

## Console Output Example

When server disconnection is detected:

```
SendArrays FAILED: code=1001 lastError=4006
Detected server disconnection - triggering auto-reset
========================================
SERVER DISCONNECTED - PERFORMING AUTO-RESET
========================================
Closing 3 open position(s)...
  Closing position: Ticket=12345 Symbol=EURUSD Type=BUY Volume=0.10
  >> Position closed successfully
  Closing position: Ticket=12346 Symbol=GBPUSD Type=BUY Volume=0.10
  >> Position closed successfully
  Closing position: Ticket=12347 Symbol=CADJPY Type=BUY Volume=0.10
  >> Position closed successfully
Closed 3/3 position(s)
Resetting internal tracking variables...
All tracking arrays cleared
========================================
AUTO-RESET COMPLETE
Server can be restarted without manual EA removal
========================================
```

When server reconnects:

```
Server: Response OK
Resetting server connection flag - ready for reconnection
```

## Code Architecture

### New Components in `Server.mqh`:

1. **Global State Variable**
   ```mql5
   bool g_ServerDisconnected = false;
   ```

2. **Detection Function**
   ```mql5
   bool IsServerDisconnectionError(int httpCode, int lastError)
   ```

3. **Cleanup Function**
   ```mql5
   void PerformAutoReset()
   ```

4. **Reconnection Helper**
   ```mql5
   void ResetServerConnectionFlag()
   ```

### Integration Points:

1. **SendArrays() - Line ~279**
   - Detects HTTP failure
   - Checks if error indicates disconnection
   - Calls `PerformAutoReset()` if disconnected
   - Resets flag on successful response

2. **ProcessServerCommand() - Line ~335**
   - Detects HTTP failure
   - Checks if error indicates disconnection
   - Calls `PerformAutoReset()` if disconnected
   - Resets flag on successful response

## Benefits

1. **Development Efficiency**
   - No manual EA removal needed
   - No manual position closure needed
   - Faster testing iteration cycles

2. **Safety**
   - Prevents orphaned positions when server is down
   - Clean state on server restart
   - Automatic cleanup reduces human error

3. **Reliability**
   - Consistent reset behavior
   - Comprehensive variable cleanup
   - Detailed logging for debugging

## Testing Recommendations

1. **Basic Test:**
   - Attach EA, open 1-2 positions
   - Stop Python server
   - Verify positions close automatically
   - Verify console shows auto-reset messages

2. **Reconnection Test:**
   - After auto-reset completes
   - Restart Python server
   - Verify EA reconnects automatically
   - Verify new trades can be opened

3. **Multiple Position Test:**
   - Open 5+ positions across different symbols
   - Stop server
   - Verify all positions close
   - Check for any position closure failures

4. **Edge Case Test:**
   - Simulate network interruption (firewall block)
   - Verify appropriate error detection
   - Verify cleanup still occurs

## Notes

- Auto-reset only triggers ONCE per disconnection
- Flag resets automatically on successful reconnection
- Position closure uses standard MT5 close logic
- Array cleanup is comprehensive (31 arrays total)
- Works with both SendArrays() and ProcessServerCommand() failures

## Error Code Reference

| Code | Last Error | Meaning |
|------|-----------|---------|
| 1001 | 4006 | Connection error (primary indicator) |
| 0 | 4006 | No connection established |
| 0 | 5203 | Cannot connect to server |
| Any | 4014 | Function not confirmed |
| Any | 5203 | Cannot connect to server |

## Related Files

- `Server.mqh` - Main implementation file
- `GlobalVariables.mqh` - Array declarations
- `Trades.mqh` - Position closure functions
- `News_Analyzer.mq5` - Main EA file

---

**Version:** 1.0  
**Last Updated:** 2024  
**Author:** Implementation based on user requirements
