# TestingMode - Multiple Positions Management

## Overview
Enhanced TestingMode now supports managing multiple positions on the same symbol simultaneously. Each position is tracked independently by its ticket number, allowing precise control over opening, closing, and monitoring individual trades.

## Key Features

### ✅ Multiple Positions Per Symbol
- Open multiple BUY positions on the same pair
- Open multiple SELL positions on the same pair
- Mix BUY and SELL positions (hedging)
- Each position tracked by unique ticket number

### ✅ Position Queries
- Check if any positions are open for a symbol
- Count positions by symbol and type (BUY/SELL)
- Get detailed information for all positions
- Filter by position type

### ✅ Selective Closing
- Close specific position by ticket number
- Close all positions of a specific type (BUY or SELL)
- Close limited number of positions
- Close all positions for a symbol

## API Reference

### Position Queries

#### `get_open_positions_by_symbol(client_id, symbol)`
Get all open positions for a specific symbol.

**Parameters:**
- `client_id` (str): MT5 client ID
- `symbol` (str): Trading symbol (e.g., "XAUUSD")

**Returns:**
- `list`: List of position dictionaries with full details

**Example:**
```python
positions = TestingMode.get_open_positions_by_symbol("1", "XAUUSD")
for pos in positions:
    print(f"Ticket: {pos['ticket']}, Type: {pos['type']}, Volume: {pos['volume']}")
```

---

#### `is_position_open(client_id, symbol, position_type=None)`
Check if any position is open for a symbol.

**Parameters:**
- `client_id` (str): MT5 client ID
- `symbol` (str): Trading symbol
- `position_type` (int, optional): Filter by type - 0 for BUY, 1 for SELL, None for any

**Returns:**
- `bool`: True if at least one matching position exists

**Examples:**
```python
# Check if ANY position is open
if TestingMode.is_position_open("1", "XAUUSD"):
    print("XAUUSD has open positions")

# Check for BUY positions only
if TestingMode.is_position_open("1", "XAUUSD", position_type=0):
    print("XAUUSD has BUY positions")

# Check for SELL positions only
if TestingMode.is_position_open("1", "XAUUSD", position_type=1):
    print("XAUUSD has SELL positions")
```

---

#### `get_position_count(client_id, symbol, position_type=None)`
Count how many positions are open for a symbol.

**Parameters:**
- `client_id` (str): MT5 client ID
- `symbol` (str): Trading symbol
- `position_type` (int, optional): Filter by type - 0 for BUY, 1 for SELL, None for all

**Returns:**
- `int`: Number of open positions

**Examples:**
```python
# Count all positions
total = TestingMode.get_position_count("1", "XAUUSD")
print(f"Total: {total}")

# Count BUY positions only
buy_count = TestingMode.get_position_count("1", "XAUUSD", position_type=0)
print(f"BUY: {buy_count}")

# Count SELL positions only
sell_count = TestingMode.get_position_count("1", "XAUUSD", position_type=1)
print(f"SELL: {sell_count}")
```

---

### Opening Positions

#### `open_position(client_id, symbol, position_type, volume, tp_pips=None, sl_pips=None, comment="")`
Open a new position for a symbol.

**Parameters:**
- `client_id` (str): MT5 client ID
- `symbol` (str): Trading symbol
- `position_type` (int or str): 0/"BUY" for long, 1/"SELL" for short
- `volume` (float): Lot size
- `tp_pips` (int, optional): Take profit in pips
- `sl_pips` (int, optional): Stop loss in pips
- `comment` (str, optional): Trade comment

**Returns:**
- `dict`: The command that was enqueued

**Examples:**
```python
# Open BUY position
TestingMode.open_position(
    "1",
    symbol="XAUUSD",
    position_type="BUY",
    volume=0.08,
    tp_pips=5000,
    sl_pips=5000,
    comment="Long Gold #1"
)

# Open SELL position
TestingMode.open_position(
    "1",
    symbol="EURUSD",
    position_type=1,  # Can use int instead of string
    volume=0.5,
    tp_pips=1000,
    sl_pips=500,
    comment="Short EUR"
)

# Open without TP/SL
TestingMode.open_position(
    "1",
    symbol="USDJPY",
    position_type="BUY",
    volume=0.3,
    comment="Manual exit"
)
```

---

### Closing Positions

#### `close_position_by_ticket(client_id, ticket, volume=None)`
Close a specific position by ticket number.

**Parameters:**
- `client_id` (str): MT5 client ID
- `ticket` (int): Position ticket number
- `volume` (float, optional): Partial close volume (None = close all)

**Returns:**
- `dict`: The command that was enqueued, or None if ticket not found

**Example:**
```python
# Close entire position
TestingMode.close_position_by_ticket("1", 12345)

# Partial close (close 0.05 lots out of 0.1)
TestingMode.close_position_by_ticket("1", 12345, volume=0.05)
```

---

#### `close_positions_by_symbol(client_id, symbol, position_type=None, max_count=None)`
Close multiple positions for a symbol with filtering options.

**Parameters:**
- `client_id` (str): MT5 client ID
- `symbol` (str): Trading symbol
- `position_type` (int, optional): Filter - 0 for BUY, 1 for SELL, None for all
- `max_count` (int, optional): Maximum positions to close (None = all)

**Returns:**
- `list`: List of commands that were enqueued

**Examples:**
```python
# Close ALL positions for XAUUSD
TestingMode.close_positions_by_symbol("1", "XAUUSD")

# Close only BUY positions
TestingMode.close_positions_by_symbol("1", "XAUUSD", position_type=0)

# Close only SELL positions
TestingMode.close_positions_by_symbol("1", "XAUUSD", position_type=1)

# Close first 2 positions only
TestingMode.close_positions_by_symbol("1", "XAUUSD", max_count=2)

# Close first 3 BUY positions only
TestingMode.close_positions_by_symbol("1", "XAUUSD", position_type=0, max_count=3)
```

---

## Use Cases

### Use Case 1: Scale In/Out Strategy
```python
# Entry: Open 3 positions with staggered TPs
TestingMode.open_position("1", "XAUUSD", "BUY", 0.03, tp_pips=2000, sl_pips=1000, comment="TP1")
TestingMode.open_position("1", "XAUUSD", "BUY", 0.03, tp_pips=4000, sl_pips=1000, comment="TP2")
TestingMode.open_position("1", "XAUUSD", "BUY", 0.02, tp_pips=6000, sl_pips=1000, comment="TP3")

# Exit: Close positions as TPs are hit
positions = TestingMode.get_open_positions_by_symbol("1", "XAUUSD")
for pos in positions:
    if pos['profit'] > 50:  # Close if profit > $50
        TestingMode.close_position_by_ticket("1", pos['ticket'])
```

### Use Case 2: Hedging Strategy
```python
# Check current exposure
buy_count = TestingMode.get_position_count("1", "EURUSD", position_type=0)
sell_count = TestingMode.get_position_count("1", "EURUSD", position_type=1)

# If too many BUY positions, add hedge
if buy_count > 2 and sell_count == 0:
    TestingMode.open_position("1", "EURUSD", "SELL", 0.1, comment="Hedge")
```

### Use Case 3: News Trading with Existing Positions
```python
symbol = "GBPUSD"

# Check existing positions before news trade
existing = TestingMode.get_position_count("1", symbol)
print(f"Existing positions: {existing}")

# News signal: SELL GBP
news_direction = "SELL"

# Add to position if same direction, or hedge if opposite
existing_sells = TestingMode.get_position_count("1", symbol, position_type=1)

if existing_sells > 0:
    print("Adding to existing SELL positions")
else:
    print("Opening new SELL position")

TestingMode.open_position("1", symbol, news_direction, 0.1, comment="News Trade")
```

### Use Case 4: Risk Management - Close Losing Positions
```python
positions = TestingMode.get_open_positions_by_symbol("1", "XAUUSD")

for pos in positions:
    profit = pos.get("profit", 0)
    ticket = pos.get("ticket")
    
    # Close if loss exceeds -$100
    if profit < -100:
        TestingMode.close_position_by_ticket("1", ticket)
        print(f"Closed losing position {ticket}: ${profit:.2f}")
```

### Use Case 5: Clear All Before New Strategy
```python
symbol = "XAUUSD"

# Close all existing positions
if TestingMode.is_position_open("1", symbol):
    print(f"Closing all {symbol} positions...")
    TestingMode.close_positions_by_symbol("1", symbol)

# Wait for clean slate, then start new strategy
print("Starting fresh strategy...")
TestingMode.open_position("1", symbol, "BUY", 0.1, tp_pips=5000, sl_pips=5000)
```

## Position Data Structure

Each position returned by `get_open_positions_by_symbol()` contains:

```python
{
    "ticket": 12345,           # Unique position identifier
    "symbol": "XAUUSD",        # Trading symbol
    "type": 0,                 # 0 = BUY, 1 = SELL
    "volume": 0.08,            # Lot size
    "price": 2595.50,          # Open price
    "currentPrice": 2598.20,   # Current market price
    "sl": 2590.50,             # Stop loss
    "tp": 2600.50,             # Take profit
    "profit": 23.60,           # Current profit/loss
    "swap": 0.00,              # Swap fees
    "comment": "TESTING XAUUSD", # Trade comment
    "magic": 0,                # Magic number
    "openTime": "2025-11-05T10:30:00" # Open timestamp
}
```

## Integration with News Trading

When integrating with News.py, you can:

1. **Check existing exposure before opening news trades**
```python
if TestingMode.get_position_count(client_id, symbol, position_type=0) >= 3:
    print(f"Already have 3 BUY positions on {symbol}, skipping")
    return
```

2. **Close conflicting positions when news reverses**
```python
# News says BUY, but we have SELL positions
if news_direction == "BUY":
    sell_count = TestingMode.get_position_count(client_id, symbol, position_type=1)
    if sell_count > 0:
        # Close all SELL positions
        TestingMode.close_positions_by_symbol(client_id, symbol, position_type=1)
```

3. **Add to winning positions**
```python
positions = TestingMode.get_open_positions_by_symbol(client_id, symbol)
profitable = [p for p in positions if p['profit'] > 0]

if len(profitable) >= 2:
    # Have 2+ profitable positions, add to the trend
    TestingMode.open_position(client_id, symbol, direction, volume)
```

## Best Practices

1. **Always check before closing**
```python
if TestingMode.is_position_open(client_id, symbol):
    # Safe to close
    TestingMode.close_positions_by_symbol(client_id, symbol)
```

2. **Use position type filters to avoid conflicts**
```python
# Close only BUY, keep SELL as hedge
TestingMode.close_positions_by_symbol(client_id, symbol, position_type=0)
```

3. **Track position counts for risk limits**
```python
total = TestingMode.get_position_count(client_id, symbol)
if total >= MAX_POSITIONS_PER_SYMBOL:
    print(f"Max positions reached for {symbol}")
    return
```

4. **Use meaningful comments for identification**
```python
TestingMode.open_position(
    client_id, symbol, "BUY", volume,
    comment=f"News:{event_name}:Entry1"
)
```

## Testing

Run the examples:
```python
python TestingMode_Examples.py
```

Or import and use in your code:
```python
from TestingMode_Examples import example_complete_workflow

# Execute complete workflow example
example_complete_workflow(client_id)
```

## Changes from Original

### Before (Single Position per Symbol)
```python
# Could only track one position per symbol
_Trades_["XAUUSD"] = {...}  # Only one entry

# Had to close by symbol name
close_trade(symbol="XAUUSD")  # Closes ALL positions
```

### After (Multiple Positions per Symbol)
```python
# Can track many positions per symbol by ticket
positions = get_open_positions_by_symbol(client_id, "XAUUSD")
# Returns: [
#   {ticket: 123, ...},
#   {ticket: 124, ...},
#   {ticket: 125, ...}
# ]

# Can close specific position
close_position_by_ticket(client_id, 124)  # Only closes ticket 124

# Or close with filters
close_positions_by_symbol(client_id, "XAUUSD", position_type=0, max_count=1)
# Closes only 1 BUY position
```

## Summary

The enhanced TestingMode provides:
- ✅ Full support for multiple positions per symbol
- ✅ Independent tracking by ticket number
- ✅ Flexible querying (by symbol, type, count)
- ✅ Selective closing (by ticket, type, limit)
- ✅ Ready for complex strategies (scaling, hedging, pyramiding)
- ✅ Compatible with News trading logic
- ✅ Production-ready with proper error handling

**Status: READY FOR USE** 🎯
