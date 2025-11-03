# Shared globals for the Python server
# Two-way communication test value

test_message = "HELLO"

# Live mode flag - controls behavior for testing vs live trading
# When True, bypasses:
#   - Time restrictions (timeToTrade always True)
liveMode = True

# Testing mode flag
TestingMode = True

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
    # Add more algorithms here as they are created
    # Example: "LiveTrading", "NewsTrading", "ScalpingMode"
]

# Selected algorithm - must match a name in ModesList
ModeSelect = "TestingMode"

# Currently open symbols - updated from client data
symbolsCurrentlyOpen = []

# Symbols to trade with their configuration
symbolsToTrade = {"XAUUSD", "USDJPY"}
# symbolsToTrade = {"BITCOIN", "TRUMP", "LITECOIN", "DOGECOIN", "ETHEREUM"}

# Symbol configuration dictionary
_Symbols_ = {
    "XAUUSD": {"symbol": "XAUUSD", "lot": 0.08, "TP": 5000, "SL": 5000, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "USDJPY": {"symbol": "USDJPY", "lot": 0.65, "TP": 1000, "SL": 1000, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "NZDCHF": {"symbol": "NZDCHF", "lot": 1.80, "TP": 200, "SL": 200, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "GBPAUD": {"symbol": "GBPAUD", "lot": 1.40, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "AUDCAD": {"symbol": "AUDCAD", "lot": 1.20, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "EURCHF": {"symbol": "EURCHF", "lot": 1.20, "TP": 300, "SL": 300, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "CADJPY": {"symbol": "CADJPY", "lot": 1.30, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "EURNZD": {"symbol": "EURNZD", "lot": 1.6, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"},
    "GBPCHF": {"symbol": "GBPCHF", "lot": 0.75, "TP": 500, "SL": 500, "last_update": 0, "ma_position": 0, "currently_open": False, "verdict_GPT": "", "manual_position": "X"}
}

