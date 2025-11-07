# Scaled Positions Test - Documentation

## Overview
`test_scaled_positions_with_closure()` is an advanced testing function that demonstrates precise control over multiple positions on the same symbol, including opening with different lot sizes and selective closure.

## Function Signature
```python
def test_scaled_positions_with_closure(client_id):
    """
    Advanced test: Open 4 scaled positions for each symbol, then close specific ones.
    
    Args:
        client_id (str): MT5 client ID
        
    Returns:
        dict: {
            'opened': int,          # Total positions opened
            'closed': int,          # Total positions closed
            'remaining': int,       # Positions still open
            'symbols_tested': int   # Number of symbols processed
        }
    """
```

## What It Does

### Phase 1: Opening Scaled Positions
For each symbol in `Globals.symbolsToTrade`:

1. **Position #1**: Base lot size (1x)
   - Volume: `base_lot × 1`
   - Comment: `"SCALE_TEST {symbol} #1 (1x)"`
   - Prints command ID

2. **Position #2**: Double lot size (2x)
   - Volume: `base_lot × 2`
   - Comment: `"SCALE_TEST {symbol} #2 (2x)"`
   - Prints command ID

3. **Position #3**: Triple lot size (3x)
   - Volume: `base_lot × 3`
   - Comment: `"SCALE_TEST {symbol} #3 (3x)"`
   - Prints command ID

4. **Position #4**: Quadruple lot size (4x)
   - Volume: `base_lot × 4`
   - Comment: `"SCALE_TEST {symbol} #4 (4x)"`
   - Prints command ID

**Result**: 4 positions per symbol opened instantly, each with unique lot size and comment

### Phase 2: Selective Closure
After all positions are opened:

1. Waits 2 seconds for positions to register in MT5
2. Retrieves all open positions for each symbol
3. Identifies positions #2 and #3 by their comment tags
4. Closes those specific positions using `close_position_by_ticket()`
5. Prints closure confirmation for each

**Result**: Positions #1 and #4 remain open, #2 and #3 are closed

## Example Output

```
============================================================
SCALED POSITIONS TEST - Opening 4 positions per symbol
============================================================

XAUUSD: Opening 4 scaled positions (BUY)
[TestingMode] Opening position: BUY XAUUSD 0.08 lots (TP=5000, SL=5000)
  Position #1: 0.08 lots | cmdId: a1b2c3d4...
[TestingMode] Opening position: BUY XAUUSD 0.16 lots (TP=5000, SL=5000)
  Position #2: 0.16 lots | cmdId: e5f6g7h8...
[TestingMode] Opening position: BUY XAUUSD 0.24 lots (TP=5000, SL=5000)
  Position #3: 0.24 lots | cmdId: i9j0k1l2...
[TestingMode] Opening position: BUY XAUUSD 0.32 lots (TP=5000, SL=5000)
  Position #4: 0.32 lots | cmdId: m3n4o5p6...
  ✓ All 4 positions opened for XAUUSD

USDJPY: Opening 4 scaled positions (BUY)
[TestingMode] Opening position: BUY USDJPY 0.65 lots (TP=1000, SL=1000)
  Position #1: 0.65 lots | cmdId: q7r8s9t0...
[TestingMode] Opening position: BUY USDJPY 1.30 lots (TP=1000, SL=1000)
  Position #2: 1.30 lots | cmdId: u1v2w3x4...
[TestingMode] Opening position: BUY USDJPY 1.95 lots (TP=1000, SL=1000)
  Position #3: 1.95 lots | cmdId: y5z6a7b8...
[TestingMode] Opening position: BUY USDJPY 2.60 lots (TP=1000, SL=1000)
  Position #4: 2.60 lots | cmdId: c9d0e1f2...
  ✓ All 4 positions opened for USDJPY

============================================================
OPENED: 8 total positions (2 symbols × 4)
============================================================

============================================================
CLOSING: Positions #2 and #3 for each symbol
============================================================

XAUUSD: Closing positions #2 and #3
[TestingMode] Closing position: Ticket=12345 Symbol=XAUUSD Type=BUY
  ✓ Closed: SCALE_TEST XAUUSD #2 (2x) (Ticket: 12345)
[TestingMode] Closing position: Ticket=12346 Symbol=XAUUSD Type=BUY
  ✓ Closed: SCALE_TEST XAUUSD #3 (3x) (Ticket: 12346)

USDJPY: Closing positions #2 and #3
[TestingMode] Closing position: Ticket=12347 Symbol=USDJPY Type=BUY
  ✓ Closed: SCALE_TEST USDJPY #2 (2x) (Ticket: 12347)
[TestingMode] Closing position: Ticket=12348 Symbol=USDJPY Type=BUY
  ✓ Closed: SCALE_TEST USDJPY #3 (3x) (Ticket: 12348)

============================================================
TEST COMPLETE - Summary
============================================================
Total positions opened: 8
Positions closed: 4
Positions remaining: 4

Expected result:
  - Each symbol should have 2 positions open (#1 and #4)
  - Positions #2 and #3 should be closed
============================================================
```

## Usage

### Manual Execution
```python
import TestingMode

client_id = "YOUR_CLIENT_ID"
result = TestingMode.test_scaled_positions_with_closure(client_id)

print(f"Opened: {result['opened']}")
print(f"Closed: {result['closed']}")
print(f"Remaining: {result['remaining']}")
```

### Run Test Script
```bash
python test_scaled_positions.py
```

The test script will:
1. Ask for confirmation before starting
2. Use only 2 symbols (XAUUSD, USDJPY) for faster testing
3. Display detailed progress
4. Verify expected vs actual results
5. Show all enqueued commands

## Timing

- **Per Symbol**: Instant (no delays between positions)
- **2 Symbols**: < 5 seconds
- **9 Symbols**: < 10 seconds (full symbolsToTrade)
- **Note**: 2-second wait added before closure phase for MT5 registration

## What It Proves

✅ **Multiple Positions**: Can open 4+ positions on same symbol
✅ **Independent Tracking**: Each position tracked by unique ticket
✅ **Lot Size Scaling**: Correctly applies 1x, 2x, 3x, 4x multipliers
✅ **Identification**: Comments allow position identification
✅ **Selective Closure**: Can close specific positions (#2, #3)
✅ **Command Control**: Precise control over which positions to close

## Use Cases

1. **Scaling In**: Open larger positions as price moves favorably
2. **Pyramid Strategy**: Add to winning positions with increasing size
3. **Partial Profit Taking**: Close some positions while letting others run
4. **Testing Infrastructure**: Verify position management capabilities

## Expected Results

For 2 symbols (XAUUSD, USDJPY):
- **Opened**: 8 positions (2 symbols × 4 positions)
- **Closed**: 4 positions (2 symbols × 2 closures)
- **Remaining**: 4 positions (2 symbols × 2 remaining)

For all 9 symbols:
- **Opened**: 36 positions (9 symbols × 4 positions)
- **Closed**: 18 positions (9 symbols × 2 closures)
- **Remaining**: 18 positions (9 symbols × 2 remaining)

## Lot Size Examples

### XAUUSD (base: 0.08)
- Position #1: 0.08 lots (1x)
- Position #2: 0.16 lots (2x) ← **Closed**
- Position #3: 0.24 lots (3x) ← **Closed**
- Position #4: 0.32 lots (4x)

### USDJPY (base: 0.65)
- Position #1: 0.65 lots (1x)
- Position #2: 1.30 lots (2x) ← **Closed**
- Position #3: 1.95 lots (3x) ← **Closed**
- Position #4: 2.60 lots (4x)

## Integration

Can be called from `handle_testing_mode()` or run independently:

```python
# In handle_testing_mode():
if replies == 2:  # Different trigger than auto-open
    test_scaled_positions_with_closure(client_id)
    return True
```

## Files
- **Function**: `TestingMode.py` → `test_scaled_positions_with_closure()`
- **Test**: `test_scaled_positions.py`
- **Docs**: `SCALED_POSITIONS_TEST.md` (this file)
