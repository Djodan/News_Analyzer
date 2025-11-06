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
# Testing scenario: JPY news event - Only USDJPY in symbolsToTrade
# Expected: USDJPY opens → Alternative finder searches _Symbols_ → finds CADJPY or EURJPY
symbolsToTrade = {"EURUSD", "EURGBP", "GBPUSD", "USDJPY", "CADJPY", "AUDCAD"}
# symbolsToTrade = {"BITCOIN", "TRUMP", "LITECOIN", "DOGECOIN", "ETHEREUM"}

# Symbol configuration dictionary
_Symbols_ = {
    "EURUSD": {"symbol": "EURUSD", "lot": 0.50, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "EURGBP": {"symbol": "EURGBP", "lot": 0.50, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "GBPUSD": {"symbol": "GBPUSD", "lot": 0.50, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "USDJPY": {"symbol": "USDJPY", "lot": 0.65, "TP": 1000, "SL": 1000, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},  # ← Will open first
    "CADJPY": {"symbol": "CADJPY", "lot": 1.30, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},  # ← Alternative (Step 2)
    "EURCHF": {"symbol": "EURCHF", "lot": 1.20, "TP": 300, "SL": 300, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "EURNZD": {"symbol": "EURNZD", "lot": 1.60, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "NZDCHF": {"symbol": "NZDCHF", "lot": 1.80, "TP": 200, "SL": 200, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "GBPAUD": {"symbol": "GBPAUD", "lot": 1.40, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "AUDCAD": {"symbol": "AUDCAD", "lot": 1.20, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "EURCHF": {"symbol": "EURCHF", "lot": 1.20, "TP": 300, "SL": 300, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "CADJPY": {"symbol": "CADJPY", "lot": 1.30, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "EURNZD": {"symbol": "EURNZD", "lot": 1.6, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "GBPCHF": {"symbol": "GBPCHF", "lot": 0.75, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"}
}

# News event tracking - stores currency news results
# Format: event_key → {currency, date, event, forecast, actual, affect, retry_count, NID, NID_Affect, NID_Affect_Executed, NID_TP, NID_SL}
# Example: "EUR_2025-11-03_04:10" → {
#   "currency": "EUR", 
#   "date": "2025, November 03, 04:10", 
#   "event": "Unemployment Rate", 
#   "forecast": 4.5, 
#   "actual": 4.2, 
#   "affect": "POSITIVE", 
#   "retry_count": 0,
#   "NID": 1,                    ← Unique News ID
#   "NID_Affect": 3,             ← How many pairs were affected/signaled
#   "NID_Affect_Executed": 2,    ← How many pairs were actually executed
#   "NID_TP": 0,                 ← How many hit TP (updated by MT5)
#   "NID_SL": 0                  ← How many hit SL (updated by MT5)
# }
# Note: During initialization, actual=None, affect=None, NID assigned when event processed
_Currencies_ = {}

# News-affected pairs tracking - stores trading decisions per pair
# Format: pair → {date, event, position, NID}
# Example: "XAUUSD" → {"date": "2025, November 11, 08:15", "event": "(United States) ADP Employment...", "position": "BUY", "NID": 5}
_Affected_ = {}

# Queued trades tracking - stores all trades to be executed
# Format: TID → {TID, client_id, symbol, action, volume, tp, sl, comment, status, createdAt, updatedAt, NID, ticket}
# Example: "TID_5_1" → {
#   "TID": "TID_5_1",           ← Unique Trade ID (NID_PositionNumber)
#   "client_id": "1", 
#   "symbol": "XAUUSD", 
#   "action": "BUY", 
#   "volume": 0.08, 
#   "tp": 5000, 
#   "sl": 5000, 
#   "comment": "News:NID_5_EUR_Unemployment", 
#   "status": "queued",         ← "queued" → "executed" → "TP"/"SL"
#   "createdAt": "2025-11-04T10:30:00", 
#   "updatedAt": "2025-11-04T10:30:00",
#   "NID": 5,                   ← Links to event in _Currencies_
#   "ticket": None              ← MT5 ticket number (set when executed)
# }
_Trades_ = {}

# Trade ID counter - auto-increments for each position per NID
# Format: NID → position_count
# Example: 5 → 3  (means NID 5 has had 3 positions opened)
_Trade_ID_Counter_ = {}

# News ID counter - auto-increments for each processed news event
_News_ID_Counter_ = 0

# ========== RISK MANAGEMENT FILTERS ==========

# News filter: Enable hedging logic (placeholder for future implementation)
news_filter_hedge = False

# News filter: Maximum total trades allowed (0 = no limit)
news_filter_maxTrades = 0

# News filter: Maximum trades per currency allowed (0 = no limit)
# Example: If set to 4, a currency like GBP cannot appear in more than 4 open positions
news_filter_maxTradePerCurrency = 2

# News filter: Find alternative pair when original is rejected (False = disabled, True = enabled)
# When enabled, if a pair is rejected due to currency limits, the system will search for
# an alternative pair containing the same currency that passes risk management filters.
# Only activates when system_news_event is set to a currency code.
news_filter_findAvailablePair = True

# News filter: Search all pairs in _Symbols_ for alternatives (False = only symbolsToTrade, True = all _Symbols_)
# When False: Only searches pairs in symbolsToTrade for alternatives
# When True: Searches symbolsToTrade first, then expands to all pairs in _Symbols_ if needed
# Hierarchy: symbolsToTrade → _Symbols_ (if enabled)
news_filter_findAllPairs = True

# System variable: Current news event currency being traded
# Set to currency code (e.g., "EUR", "USD", "GBP") during news event processing
# Reset to False after trade attempt completes
# Used by find_available_pair_for_currency() to search for alternative pairs
system_news_event = False

# Currency exposure counter - tracks how many positions each currency appears in
# Format: currency → count
# Example: {"EUR": 2, "USD": 3, "GBP": 1, "JPY": 2}
# Updated when trades open/close. Each currency in a pair is counted once per trade.
# For EURUSD: EUR +1, USD +1. For GBPJPY: GBP +1, JPY +1.
_CurrencyCount_ = {
    "XAU": 0,
    "EUR": 0,
    "USD": 0,
    "JPY": 0,
    "CHF": 0,
    "NZD": 0,
    "CAD": 0,
    "GBP": 0,
    "AUD": 0,
    "BTC": 0
}

# Testing Mode: Position tracking by ticket
# Format: ticket → {symbol, action, volume, tp, sl, comment, status, opened_at}
# This allows multiple positions on the same symbol to be tracked independently
# Example: 12345 → {
#   "symbol": "XAUUSD",
#   "action": "BUY",
#   "volume": 0.08,
#   "tp": 2600.0,
#   "sl": 2590.0,
#   "comment": "TESTING XAUUSD #1",
#   "status": "open",  # "open", "closed", "pending_close"
#   "opened_at": "2025-11-05T10:30:00Z"
# }
_Test_Positions_ = {}
