# Shared globals for the Python server
# Two-way communication test value

test_message = "HELLO"

# Testing mode flag
TestingMode = True

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
