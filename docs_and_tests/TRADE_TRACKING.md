# Trade Tracking & Retry System

## Overview
This system prevents duplicate trades and automatically retries failed trades until they succeed or trading time ends.

## Key Features

### 1. Duplicate Prevention
- Each symbol tracks `traded_this_session` in `_Symbols_` dictionary
- Once a symbol is traded (or detected as open), it won't be traded again
- Prevents accidental duplicate positions on the same symbol

### 2. Automatic Retry Logic
- Failed trades are marked with `pending_trade` in `_Symbols_`
- System automatically retries pending trades on every poll
- Retries continue until:
  - Symbol successfully opens (detected via `symbolsCurrentlyOpen`)
  - Trading time ends (`timeToTrade` becomes `False`)

### 3. Clean Integration
- All tracking data stored in `_Symbols_` dictionary
- No separate tracking dictionaries or sets needed
- Uses existing symbol configuration structure

## Data Structure

Each symbol in `_Symbols_` has these tracking fields:

```python
{
    "symbol": "XAUUSD",
    "lot": 0.08,
    "TP": 5000,
    "SL": 5000,
    "manual_position": "X",  # "BUY", "SELL", or "X"
    
    # Tracking fields:
    "traded_this_session": False,  # True once traded/open
    "pending_trade": None  # or {"state": 1/2, "comment": "...", "added_at": "..."}
}
```

## Key Functions

### `is_symbol_tradeable(symbol: str) -> bool`
- Checks if symbol can be traded
- Returns `False` if already traded or currently open
- Auto-marks open symbols as traded

### `mark_pending_trade(symbol: str, state: int, comment: str)`
- Marks a symbol for retry
- Stores trade details in `_Symbols_[symbol]["pending_trade"]`

### `retry_pending_trades(client_id: str) -> bool`
- Retries all pending trades
- Auto-clears symbols that become open
- Clears all pending trades when `timeToTrade=False`

### `clear_pending_trade(symbol: str)`
- Clears pending status
- Marks symbol as traded (prevents future trades)

### `reset_session_tracking()`
- Resets all tracking for new session
- Clears `traded_this_session` and `pending_trade` for all symbols

## Workflow Example

```
Poll #1: Initial attempt
  - Check is_symbol_tradeable("XAUUSD") → True
  - Enqueue trade command
  - mark_pending_trade("XAUUSD", 1, "WEEKLY")
  - Status: traded=False, pending=True

Poll #2: Trade still processing
  - retry_pending_trades() finds XAUUSD pending
  - Symbol not in symbolsCurrentlyOpen yet
  - Enqueue retry command
  - Status: traded=False, pending=True

Poll #3: Trade succeeded
  - retry_pending_trades() finds XAUUSD pending
  - Symbol IS in symbolsCurrentlyOpen
  - clear_pending_trade("XAUUSD") called
  - Status: traded=True, pending=False

Poll #4: No action needed
  - is_symbol_tradeable("XAUUSD") → False (already traded)
  - retry_pending_trades() → False (no pending trades)
```

## Integration with Algorithms

Both `TestingMode.py` and `Weekly.py` follow this pattern:

```python
def handle_algorithm(client_id, stats):
    # First, retry any pending trades
    retried = retry_pending_trades(client_id)
    
    # On first poll, attempt initial trades
    if replies == 1:
        for symbol in symbolsToTrade:
            # Check if tradeable
            if not is_symbol_tradeable(symbol):
                continue
            
            # Enqueue command
            enqueue_command(client_id, state, {...})
            
            # Mark as pending
            mark_pending_trade(symbol, state, comment)
    
    # Return True if any commands were injected
    return retried or injected_any
```

## Time Management

- `liveMode=True`: Bypasses `timeToTrade` check (retries continue indefinitely)
- `liveMode=False`: When `timeToTrade=False`, all pending trades are cleared
- This ensures retries don't continue outside trading hours

## Testing

Run tests to verify functionality:

```bash
python test_trade_tracking.py  # Unit tests for tracking functions
python test_integration.py      # Full workflow integration test
```

## Benefits

1. **No Duplicates**: Same symbol never traded twice in one session
2. **Reliability**: Failed trades automatically retry until success
3. **Clean Code**: All data in one place (`_Symbols_` dictionary)
4. **Automatic Cleanup**: Pending trades cleared when time ends
5. **Observable**: Clear logging shows trade lifecycle
