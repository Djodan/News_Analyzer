# TestingMode - Quick Reference

## Import
```python
import TestingMode
```

## Query Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_open_positions_by_symbol(client_id, symbol)` | Get all positions for symbol | `list[dict]` |
| `is_position_open(client_id, symbol, type=None)` | Check if position exists | `bool` |
| `get_position_count(client_id, symbol, type=None)` | Count positions | `int` |

### Position Type Constants
- `0` or `None` = BUY positions
- `1` = SELL positions
- `None` (default) = ALL positions

## Opening Positions

```python
TestingMode.open_position(
    client_id,
    symbol="XAUUSD",
    position_type="BUY",  # or "SELL", 0, 1
    volume=0.08,
    tp_pips=5000,        # optional
    sl_pips=5000,        # optional
    comment="My Trade"   # optional
)
```

## Closing Positions

### By Ticket (Specific Position)
```python
TestingMode.close_position_by_ticket(client_id, ticket_number)
```

### By Symbol (Multiple Positions)
```python
# Close ALL positions
TestingMode.close_positions_by_symbol(client_id, "XAUUSD")

# Close BUY positions only
TestingMode.close_positions_by_symbol(client_id, "XAUUSD", position_type=0)

# Close SELL positions only
TestingMode.close_positions_by_symbol(client_id, "XAUUSD", position_type=1)

# Close first 2 positions
TestingMode.close_positions_by_symbol(client_id, "XAUUSD", max_count=2)
```

## Common Patterns

### Check Before Open
```python
if not TestingMode.is_position_open(client_id, "XAUUSD"):
    TestingMode.open_position(client_id, "XAUUSD", "BUY", 0.1)
```

### Count Positions
```python
total = TestingMode.get_position_count(client_id, "XAUUSD")
buys = TestingMode.get_position_count(client_id, "XAUUSD", position_type=0)
sells = TestingMode.get_position_count(client_id, "XAUUSD", position_type=1)
```

### Get Position Details
```python
positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
for pos in positions:
    print(f"Ticket: {pos['ticket']}, P&L: ${pos['profit']:.2f}")
```

### Close Profitable Positions
```python
positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
for pos in positions:
    if pos['profit'] > 100:
        TestingMode.close_position_by_ticket(client_id, pos['ticket'])
```

### Close All Before New Strategy
```python
if TestingMode.is_position_open(client_id, "XAUUSD"):
    TestingMode.close_positions_by_symbol(client_id, "XAUUSD")
# Now open fresh positions
```

## Position Dictionary Keys

```python
position = {
    'ticket': 12345,           # Unique ID
    'symbol': 'XAUUSD',
    'type': 0,                 # 0=BUY, 1=SELL
    'volume': 0.08,
    'price': 2595.50,          # Open price
    'currentPrice': 2598.20,   # Current price
    'sl': 2590.50,
    'tp': 2600.50,
    'profit': 23.60,           # P&L in account currency
    'comment': 'My Trade',
    'openTime': '2025-11-05T10:30:00'
}
```

## Examples

### Multiple Positions Same Symbol
```python
# Open 3 BUY positions with different TPs
TestingMode.open_position(client_id, "XAUUSD", "BUY", 0.03, tp_pips=2000)
TestingMode.open_position(client_id, "XAUUSD", "BUY", 0.03, tp_pips=4000)
TestingMode.open_position(client_id, "XAUUSD", "BUY", 0.02, tp_pips=6000)
```

### Hedging
```python
# Open BUY and SELL on same symbol
TestingMode.open_position(client_id, "EURUSD", "BUY", 0.1)
TestingMode.open_position(client_id, "EURUSD", "SELL", 0.05)  # Half hedge
```

### Scale Out
```python
# Close positions one at a time as profit grows
positions = TestingMode.get_open_positions_by_symbol(client_id, "XAUUSD")
positions.sort(key=lambda p: p['profit'], reverse=True)  # Most profitable first

if positions[0]['profit'] > 50:
    TestingMode.close_position_by_ticket(client_id, positions[0]['ticket'])
```

### Risk Limit
```python
MAX_POSITIONS = 3
if TestingMode.get_position_count(client_id, symbol) >= MAX_POSITIONS:
    print(f"Max positions reached for {symbol}")
else:
    TestingMode.open_position(client_id, symbol, "BUY", volume)
```

## See Also
- `TESTINGMODE_DOCUMENTATION.md` - Full documentation
- `TestingMode_Examples.py` - Complete code examples
- `TestingMode.py` - Source code
