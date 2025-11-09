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
ModeSelect = "TestingMode"

# Currently open symbols - updated from client data
symbolsCurrentlyOpen = []

# Symbols to trade with their configuration
# Testing scenario: JPY news event - Only USDJPY in symbolsToTrade
# Expected: USDJPY opens → Alternative finder searches _Symbols_ → finds CADJPY or EURJPY
# symbolsToTrade = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"}
symbolsToTrade = {"BITCOIN"}
# symbolsToTrade = {"BITCOIN", "TRUMP", "LITECOIN", "DOGECOIN", "ETHEREUM"}

# Symbol configuration dictionary
# ========== ACCOUNT & POSITION SIZING ==========

# Account balance for dynamic lot sizing (updated by MT5 client)
accBalance = 100000  # Default account balance

# Dynamic lot size percentage of account balance
lot_size_percentage = 0.0025  # 0.25% of account balance (0.0025)

# Weekly profit target - stop opening new positions after reaching this cumulative return
weekly_profit_target = 1.0  # 1.0% weekly target (0.01)

# Weekly cumulative return tracker (resets Monday 00:00)
weekly_cumulative_return = 0.0  # Running profit/loss for current week

# Weekly target reached flag
weekly_target_reached = False  # Set to True when weekly_cumulative_return >= weekly_profit_target

# _Symbols_ dictionary - comprehensive pair configuration
_Symbols_ = {
    "EURUSD": {
        "symbol": "EURUSD",
        "lot": 0.50,                    # Base lot size (overridden by dynamic sizing)
        "TP": 500,                      # Take-profit in points (overridden by strategy_tp_sl)
        "SL": 250,                      # Stop-loss in points (overridden by strategy_tp_sl)
        "ATR": 0,                       # 14-period ATR on 30-minute chart (updated by MT5)
        "current_price": 0.0,           # Current market price (updated by MT5)
        "spread": 0.0,                  # Current spread in pips (updated by MT5)
        "point_value": 10.0,            # Dollar value per pip (for lot sizing calculation)
        "ma_position": 0,               # Moving average position indicator
        "currently_open": False,        # Whether pair has open position
        "verdict_GPT": "",              # Latest GPT verdict (BULL/BEAR/NEUTRAL)
        "manual_position": "BUY",       # Manual override position
        "weekly_gain": 0.0,             # Running profit this week for this pair
        "weekly_drawdown": 0.0,         # Max drawdown this week for this pair
        "traded_this_week": False,      # S4 weekly lock flag
    },
    "EURGBP": {
        "symbol": "EURGBP",
        "lot": 0.50,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 12.5,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "BUY",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "GBPUSD": {
        "symbol": "GBPUSD",
        "lot": 0.50,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 10.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "BUY",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "USDJPY": {
        "symbol": "USDJPY",
        "lot": 0.65,
        "TP": 1000,
        "SL": 1000,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 9.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "BUY",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "CADJPY": {
        "symbol": "CADJPY",
        "lot": 1.30,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 9.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "BUY",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "EURCHF": {
        "symbol": "EURCHF",
        "lot": 1.20,
        "TP": 300,
        "SL": 300,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 11.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "BUY",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "EURNZD": {
        "symbol": "EURNZD",
        "lot": 1.60,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 6.5,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "BUY",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "NZDCHF": {
        "symbol": "NZDCHF",
        "lot": 1.80,
        "TP": 200,
        "SL": 200,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 11.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "X",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "GBPAUD": {
        "symbol": "GBPAUD",
        "lot": 1.40,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 7.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "X",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "AUDCAD": {
        "symbol": "AUDCAD",
        "lot": 1.20,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 7.5,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "X",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "USDCHF": {
        "symbol": "USDCHF",
        "lot": 1.6,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 11.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "X",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "GBPCHF": {
        "symbol": "GBPCHF",
        "lot": 0.75,
        "TP": 500,
        "SL": 500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 11.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "X",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    },
    "BITCOIN": {
        "symbol": "BITCOIN",
        "lot": 1.0,
        "TP": 2500,
        "SL": 2500,
        "ATR": 0,
        "current_price": 0.0,
        "spread": 0.0,
        "point_value": 10.0,
        "ma_position": 0,
        "currently_open": False,
        "verdict_GPT": "",
        "manual_position": "X",
        "weekly_gain": 0.0,
        "weekly_drawdown": 0.0,
        "traded_this_week": False,
    }
}

# Symbol configuration dictionary
_WeeklySymbols_ = {
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.50, "TP": 500, "SL": 500, "ATR": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "EURUSD": {"symbol": "EURUSD", "lot": 0.50, "TP": 500, "SL": 500, "ATR": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.50, "TP": 500, "SL": 500, "ATR": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.50, "TP": 500, "SL": 500, "ATR": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.50, "TP": 500, "SL": 500, "ATR": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"},
    "EURUSD": {"symbol": "EURUSD", "lot": 0.50, "TP": 500, "SL": 500, "ATR": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "BUY"}
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
# Format: TID → {TID, client_id, symbol, action, volume, tp, sl, comment, status, createdAt, updatedAt, NID, ticket, ...analytics}
# Example: "TID_5_1" → {
#   "TID": "TID_5_1",                        ← Unique Trade ID (NID_PositionNumber)
#   "client_id": "1",
#   "symbol": "XAUUSD",
#   "action": "BUY",
#   "volume": 0.08,
#   "tp": 5000,
#   "sl": 5000,
#   "comment": "News:NID_5_EUR_Unemployment",
#   "status": "queued",                      ← "queued" → "executed" → "TP"/"SL"
#   "createdAt": "2025-11-04T10:30:00",
#   "updatedAt": "2025-11-04T10:30:00",
#   "NID": 5,                                ← Links to event in _Currencies_
#   "ticket": None,                          ← MT5 ticket number (set when executed)
#   
#   # Data Capture Fields (28 total for CSV logging)
#   "strategy": "S2",                        ← Which strategy opened this (S1-S5)
#   "currency": "EUR",                       ← Primary affected currency
#   "event_type": "CPI",                     ← News category
#   "event_time": "2025-11-07T08:30:00",    ← News release timestamp
#   "entry_time": None,                      ← When trade actually opened (from MT5)
#   "exit_time": None,                       ← When trade closed (from MT5)
#   "entry_price": 0.0,                      ← Actual entry price (from MT5)
#   "exit_price": 0.0,                       ← Actual exit price (from MT5)
#   "duration_min": 0,                       ← Hold time in minutes
#   "reaction_delay_sec": 0.0,               ← Entry time - Event time
#   "pl_pips": 0.0,                          ← Profit/loss in pips
#   "return_pct": 0.0,                       ← % return
#   "result": "",                            ← "WIN" | "LOSS" | "BREAKEVEN"
#   "sl_hit": False,                         ← True if closed via SL
#   "tp_hit": False,                         ← True if closed via TP
#   "close_type": "",                        ← "TP" | "SL" | "Reversal" | "WeekEnd" | "Manual"
#   "surprise_strength": 0.0,                ← (Actual - Forecast) / Forecast
#   "market_volatility": 0.0,                ← High - Low range during trade (pips)
#   "mae": 0.0,                              ← Max Adverse Excursion (pips)
#   "mfe": 0.0,                              ← Max Favorable Excursion (pips)
#   "entry_atr": 0.0,                        ← ATR at entry (S4/S5 only)
#   "position_count": 1,                     ← 1st, 2nd position for currency (S5)
#   "sentiment_agreement": True,             ← Does this agree with prior signal? (S5)
# }
_Trades_ = {}

# Trade ID counter - auto-increments for each position per NID
# Format: NID → position_count
# Example: 5 → 3  (means NID 5 has had 3 positions opened)
_Trade_ID_Counter_ = {}

# News ID counter - auto-increments for each processed news event
_News_ID_Counter_ = 0

# ========== STRATEGY SELECTION & CONFIGURATION ==========

# Active news trading strategy
# 1 = S1 (Sequential Same-Pair)
# 2 = S2 (Multi-Pair with Alternatives) 
# 3 = S3 (Rolling Currency Mode)
# 4 = S4 (Timed Portfolio Mode)
# 5 = S5 (Adaptive Hybrid with Sentiment Scaling)
news_strategy = 2  # Currently running S2

# Strategy-specific risk percentages (overrides lot_size_percentage)
strategy_risk = {
    1: 0.0025,  # S1: 0.25%
    2: 0.0025,  # S2: 0.25%
    3: 0.0030,  # S3: 0.30% (higher for rolling agility)
    4: 0.0025,  # S4: 0.25%
    5: 0.0025,  # S5: 0.25% base (scales to 0.50% on agreement)
}

# Strategy-specific TP/SL settings (in points, 0 = use ATR-based)
strategy_tp_sl = {
    1: {"TP": 500, "SL": 250},   # S1: Static
    2: {"TP": 500, "SL": 250},   # S2: Static
    3: {"TP": 500, "SL": 250},   # S3: Static
    4: {"TP": 0, "SL": 0},       # S4: ATR-based (2×ATR TP, 1×ATR SL)
    5: {"TP": 0, "SL": 0},       # S5: ATR-based (2×ATR TP, 1×ATR SL)
}

# ========== RISK MANAGEMENT FILTERS ==========

# News filter: Enable hedging logic (placeholder for future implementation)
news_filter_hedge = False

# News filter: Maximum total trades allowed (0 = no limit)
news_filter_maxTrades = 0

# News filter: Maximum trades per currency allowed (0 = no limit)
# Example: If set to 4, a currency like GBP cannot appear in more than 4 open positions
news_filter_maxTradePerCurrency = 0

# News filter: Maximum trades per pair allowed (0 = no limit)
# Example: If set to 1, only one EURUSD position can be open at a time
news_filter_maxTradePerPair = 0

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

# Pair exposure counter - tracks how many open positions exist per trading pair
# Format: pair → count
# Example: {"EURUSD": 1, "GBPUSD": 2, "USDJPY": 0}
# Updated when trades open/close. Tracks individual pair exposure for per-pair limits.
_PairCount_ = {}

# ========== S3 (ROLLING MODE) TRACKING ==========

# Currency-level position tracking for S3 rolling logic
# Tracks the ONE active position per currency for reversal detection
# Format: currency → {pair, action, ticket, TID, NID, entry_time}
# Example: "EUR" → {
#   "pair": "EURUSD",
#   "action": "BUY",
#   "ticket": 12345,
#   "TID": "TID_5_1",
#   "NID": 5,
#   "entry_time": "2025-11-07T08:30:03"
# }
# When new EUR signal arrives with opposite direction, close this position and open new one
_CurrencyPositions_ = {}

# Rolling mode enable flag (S3 only)
news_filter_rollingMode = False  # Set to True when news_strategy = 3

# ========== S4 (TIMED PORTFOLIO) TRACKING ==========

# Weekly pair lock tracking - prevents repeat trading of same pair within week
# Format: pair → bool (True = already traded this week, False = available)
# Example: {"EURUSD": True, "GBPUSD": False, "USDJPY": True}
# Reset every Monday 00:00 to unlock all pairs for new week
_PairsTraded_ThisWeek_ = {}

# Weekly first-only flag (S4 only)
news_filter_weeklyFirstOnly = False  # Set to True when news_strategy = 4

# Last weekly reset timestamp (to detect Monday boundary)
last_weekly_reset = None  # datetime object, checked every heartbeat

# ========== S5 (ADAPTIVE HYBRID) TRACKING ==========

# Currency sentiment aggregation for S5 adaptive scaling
# Tracks consensus direction + confidence level per currency
# Format: currency → {direction, confidence, events, positions, last_update}
# Example: "EUR" → {
#   "direction": "BULL",                    # Current consensus: BULL or BEAR
#   "confidence": 2,                         # Number of agreeing events
#   "events": [5, 7],                        # NIDs that contributed to sentiment
#   "positions": ["TID_5_1", "TID_7_1"],    # Active trades for this sentiment
#   "last_update": "2025-11-07T10:30:00"    # When sentiment last changed
# }
_CurrencySentiment_ = {}

# Sentiment scaling enable flag (S5 only)
news_filter_allowScaling = False  # Set to True when news_strategy = 5

# Maximum positions to stack when events agree (S5 only)
news_filter_maxScalePositions = 2  # Max 2 positions per currency (base + 1 scaled)

# Scaling factor for additional positions (S5 only)
# Position 1: 0.25%, Position 2: 0.25% × 0.6 = 0.15%
news_filter_scalingFactor = 0.6  # 60% of previous position size

# Conflict handling mode for S5 (S5 only)
# "ignore" = keep existing positions, skip conflicting signal
# "reverse" = close all existing, open new position in opposite direction
# "reduce" = reduce position size, wait for tie-breaker
news_filter_conflictHandling = "reverse"  # Default: reverse like S3

# ========== DATA CAPTURE VARIABLES ==========

# CSV logging enable flag
data_capture_enabled = True  # Set to False to disable CSV logging

# CSV file path (auto-generated with session timestamp)
csv_file_path = None  # Set during initialization: "trades_log_20251107_083000.csv"

# Trade record buffer - temporary storage before writing to CSV
# Format: list of dictionaries with 28 fields per trade
_TradeRecords_ = []

# Session start time (for CSV filename and session tracking)
session_start_time = None  # datetime object, set during initialization

# ========== MT5 DATA PACKAGE STRUCTURE ==========

# MT5 client sends this data structure on every heartbeat (30 seconds)
# Python server stores values in _Symbols_ and accBalance
# Structure:
# {
#     "account_balance": 100000.00,
#     "symbols": {
#         "EURUSD": {
#             "ATR": 45.0,                    # 14-period ATR on 30-minute chart
#             "current_price": 1.0850,
#             "spread": 1.5,
#             "high": 1.0870,                 # For volatility calculation
#             "low": 1.0835                   # For volatility calculation
#         },
#         # ... all pairs in _Symbols_
#     },
#     "open_positions": [
#         {
#             "ticket": 12345,
#             "symbol": "EURUSD",
#             "action": "BUY",
#             "entry_price": 1.0850,
#             "current_price": 1.0865,
#             "unrealized_pnl": 15.0,         # In pips
#             "mae": -8.0,                    # Max Adverse Excursion (pips)
#             "mfe": 28.0,                    # Max Favorable Excursion (pips)
#             "open_time": "2025-11-07T08:30:03",
#             "TID": "TID_5_1"               # Link back to _Trades_
#         }
#     ],
#     "closed_positions": [
#         {
#             "ticket": 12345,
#             "symbol": "EURUSD",
#             "action": "BUY",
#             "entry_price": 1.0850,
#             "exit_price": 1.0873,
#             "pl_pips": 23.0,
#             "open_time": "2025-11-07T08:30:03",
#             "close_time": "2025-11-07T14:45:12",
#             "close_reason": "TP",           # TP, SL, Manual
#             "TID": "TID_5_1"
#         }
#     ]
# }

# Last MT5 heartbeat timestamp (to detect connection issues)
last_mt5_heartbeat = None  # datetime object, updated on every MT5 data package

# MT5 connection status
mt5_connected = False  # Set to True when heartbeat received within last 60 seconds

# ========== TESTING MODE TRACKING ==========
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
