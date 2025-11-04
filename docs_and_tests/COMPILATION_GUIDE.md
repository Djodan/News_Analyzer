# News Analyzer - Compilation Guide

## Files Converted for News_Analyzer Project

### Main Expert Advisor
- **News_Analyzer.mq5** - Main EA file (replaces MQL5X.mq5)

### Include Files (Updated)
All `.mqh` files have been updated with new header guards and branding:

1. **Inputs.mqh** 
   - Header guard: `NEWS_ANALYZER_INPUTS_MQH`
   - Description: Inputs for News Analyzer Expert Advisor

2. **GlobalVariables.mqh**
   - Contains global variables for the EA

3. **Trades.mqh**
   - Header guard: `NEWS_ANALYZER_TRADES_MQH`
   - Helpers to manage open/closed trade collections

4. **TestingMode.mqh**
   - Header guard: `NEWS_ANALYZER_TESTINGMODE_MQH`
   - Testing hooks and utilities for News Analyzer
   - Updated reference from MQL5X.mq5 to News_Analyzer.mq5

5. **Server.mqh**
   - Header guard: `NEWS_ANALYZER_SERVER_MQH`
   - HTTP communication for News Analyzer

6. **Json.mqh**
   - Header guard: `NEWS_ANALYZER_JSON_MQH`
   - JSON helpers and payload builders

7. **Http.mqh**
   - HTTP communication utilities

## Compilation Steps

### In MetaTrader 5:

1. Open MetaEditor (press F4 in MT5 or Tools -> MetaQuotes Language Editor)

2. Navigate to: 
   ```
   File -> Open Data Folder -> MQL5 -> Experts -> News_Analyzer
   ```

3. Open **News_Analyzer.mq5**

4. Compile by pressing F7 or clicking Compile button

5. If successful, **News_Analyzer.ex5** will be created

### Expected Output:
```
0 error(s), 0 warning(s)
```

## Running the EA

1. In MT5, go to Navigator panel (Ctrl+N)
2. Expand "Expert Advisors"
3. Find "News_Analyzer"
4. Drag and drop onto a chart
5. Configure inputs:
   - **ID**: Unique identifier for this client
   - **Mode**: Sender (default)
   - **TestingMode**: true/false
   - **SendToServer**: true
   - **ServerIP**: 127.0.0.1
   - **ServerPort**: 5000

## Server Communication

The EA will communicate with the Python server at:
- URL: `http://127.0.0.1:5000/`
- Endpoints:
  - `POST /` - Send trade snapshots
  - `GET /command/{id}` - Poll for commands
  - `POST /ack/{id}` - Acknowledge command execution

## Testing Mode

When `TestingMode = true`, the server will automatically inject a BUY trade on the first client poll:
- Symbol: XAUUSD
- Volume: 1.00
- Comment: "auto BUY TestingMode"

## Communication Logging

Both MT5 and Python server will print detailed communication logs:
- **MT5**: Check the Experts tab in Terminal window
- **Python**: Check the console where Server.py is running

### Example MT5 Output:
```
→ MT5 TO SERVER: Sending snapshot with 0 open trades
← SERVER RESPONSE: OK (200)
← SERVER TO MT5: Received command state=1 (OPEN BUY) cmdId=abc-123
TRADE PLACED: BUY XAUUSD Vol=1.00 Price=2650.50 TP=0.0 SL=0.0
→ MT5 TO SERVER: Sent ACK cmdId=abc-123 success=true code=200
```

### Example Python Server Output:
```
[2025-10-28...] ← MT5 CLIENT 123: Sent snapshot with 0 open, 0 closed online
[2025-10-28...] → INJECTED BUY command for client 123 (TestingMode, reply #1)
[2025-10-28...] → SERVER TO MT5 123: BUY XAUUSD Vol=1.0 TP=None SL=None (state=1)
[2025-10-28...] ← MT5 CLIENT 123: ACK cmdId=abc-123 success=True Symbol=XAUUSD Type=BUY Vol=1.0
```

## Troubleshooting

### Compilation Errors
- Ensure all `.mqh` files are in the same directory as `News_Analyzer.mq5`
- Check header guards match in all files

### WebRequest Errors
In MT5, go to: **Tools -> Options -> Expert Advisors**
- Enable "Allow WebRequest for listed URL"
- Add: `http://127.0.0.1:5000`

### Python Server Not Starting
Navigate to News_Analyzer folder and run:
```powershell
python Server.py --host 127.0.0.1 --port 5000
```

## File Structure
```
News_Analyzer/
├── News_Analyzer.mq5       # Main EA
├── News_Analyzer.ex5       # Compiled EA (generated)
├── Inputs.mqh              # Input parameters
├── GlobalVariables.mqh     # Global variables
├── Trades.mqh              # Trade management
├── TestingMode.mqh         # Testing mode logic
├── Server.mqh              # HTTP communication
├── Json.mqh                # JSON helpers
├── Http.mqh                # HTTP utilities
├── Server.py               # Python server
├── Functions.py            # Server functions
└── Globals.py              # Server globals
```
