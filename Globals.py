# Shared globals for the Python server
# Two-way communication test value

test_message = "HELLO"

# Server configuration
SERVER_HOST = "127.0.0.1"  # Bind address (default: 127.0.0.1 for local only, use 0.0.0.0 for all interfaces)
SERVER_PORT = 5000          # Port to listen on (default: 5000)

# API Keys - imported from config.py (not committed to git)
try:
    from config import API_KEY_GPT, API_KEY_PPXT
except ImportError:
    print("WARNING: config.py not found. Copy config_template.py to config.py and add your API keys.")
    API_KEY_GPT = ""
    API_KEY_PPXT = ""

# Live mode flag - controls behavior for testing vs live trading
# When True, bypasses:
#   - Time restrictions (timeToTrade always True)
liveMode = False

# Testing mode flag
TestingMode = True

# CSV event limit - only used when liveMode=False
# Limits the number of events parsed from calendar_statement.csv to reduce token usage during testing
csv_count = 6

# News processing control - determines if past events should be processed
# When False: Skip past events, only process future events
# When True: Process all events including past ones
news_process_past_events = True

# News test mode - for testing STEP 3, process ONLY past events (inverse of normal mode)
# When True: Skip future events, only process past events (for testing actual fetching)
# When False: Normal behavior (skip past, process future)
news_test_mode = False

# Time configuration
timeType = "MT5"  # "MT5" or "NY"
timeToTrade = False  # Set by checkTime() function
timeStart = 18  # Start hour in military time (0-23)
timeEnd = 20  # End hour in military time (0-23)

# Available trading algorithms/modes
ModesList = [
    "Plain",         # Empty mode for communication/testing only
    "TestingMode",   # Testing mode with auto BUY injection
    "Weekly",        # Weekly trading strategy
    "News",          # News-based trading strategy
    # Add more algorithms here as they are created
    # Example: "LiveTrading", "ScalpingMode"
]

# Selected algorithm - must match a name in ModesList
ModeSelect = "News"

# Currently open symbols - updated from client data
symbolsCurrentlyOpen = []

# Symbols to trade with their configuration
symbolsToTrade = {"XAUUSD", "USDJPY", "GBPAUD"}
# symbolsToTrade = {"BITCOIN", "TRUMP", "LITECOIN", "DOGECOIN", "ETHEREUM"}

# Symbol configuration dictionary
_Symbols_ = {
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.08, "TP": 5000, "SL": 5000, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "USDJPY": {"symbol": "USDJPY", "lot": 0.65, "TP": 1000, "SL": 1000, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "NZDCHF": {"symbol": "NZDCHF", "lot": 1.80, "TP": 200, "SL": 200, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "GBPAUD": {"symbol": "GBPAUD", "lot": 1.40, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "AUDCAD": {"symbol": "AUDCAD", "lot": 1.20, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "EURCHF": {"symbol": "EURCHF", "lot": 1.20, "TP": 300, "SL": 300, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "CADJPY": {"symbol": "CADJPY", "lot": 1.30, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "EURNZD": {"symbol": "EURNZD", "lot": 1.6, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "GBPCHF": {"symbol": "GBPCHF", "lot": 0.75, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"}
}

# News event tracking - stores currency news results
# Format: currency → {date, event, forecast, actual, affect, retry_count}
# Example: "USD" → {"date": "2025, November 11, 08:15", "event": "(United States) ADP Employment...", "forecast": 43.7, "actual": 43.5, "affect": "BULL", "retry_count": 0}
# Note: During initialization, actual=None, affect=None. Updated when event occurs.
_Currencies_ = {}

# News-affected pairs tracking - stores trading decisions per pair
# Format: pair → {date, event, position}
# Example: "XAUUSD" → {"date": "2025, November 11, 08:15", "event": "(United States) ADP Employment...", "position": "BUY"}
_Affected_ = {}

# Queued trades tracking - stores all trades to be executed
# Format: pair → {client_id, symbol, action, volume, tp, sl, comment, status, createdAt, updatedAt}
# Example: "XAUUSD" → {"client_id": "1", "symbol": "XAUUSD", "action": "BUY", "volume": 0.08, "tp": 5000, "sl": 5000, "comment": "News:USD BEAR", "status": "queued", "createdAt": "2025-11-04T10:30:00", "updatedAt": "2025-11-04T10:30:00"}
# Status: "queued" → "executed"
_Trades_ = {}

