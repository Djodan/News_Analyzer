# S5 Scaling Implementation Guide
**Strategy:** S5 - Adaptive Hybrid (Confirmation + Scaling)  
**Implemented:** November 12, 2025  
**Status:** ✅ Fully implemented and prop firm compliant

---

## Overview

S5 now combines **confirmation mode** with **intelligent scaling** to build positions as confidence increases while maintaining strict prop firm compliance (max 1% exposure per currency).

### Key Features:
1. **Confirmation Required:** Waits for 2+ agreeing signals before opening first position
2. **Adaptive Scaling:** Opens additional positions (up to 4 total) as more agreeing signals arrive
3. **Conflict Handling:** Resets counter and optionally closes positions on conflicting signals
4. **Prop Firm Compliant:** Max 4 positions × 0.25% = 1.00% exposure per currency

---

## How It Works

### Phase 1: Confirmation (Signals 1-2)
**Goal:** Confirm market direction before risking capital

**Signal 1 (EUR BULLISH):**
```
⏳ S5: EUR BULLISH signal 1/2, waiting for confirmation
_CurrencySentiment_["EUR"] = {
    'direction': 'BULLISH',
    'count': 1,
    'positions_opened': 0
}
→ NO TRADE (waiting for confirmation)
```

**Signal 2 (EUR BULLISH):**
```
✅ S5: EUR BULLISH confirmed (2/2), opening first position
_CurrencySentiment_["EUR"] = {
    'direction': 'BULLISH',
    'count': 2,
    'positions_opened': 1  ← Incremented after opening
}
→ Opens EURUSD BUY 0.25 lots
→ EUR: 1, USD: 1
```

---

### Phase 2: Scaling (Signals 3-5)
**Goal:** Increase exposure as more confirming signals arrive

**Signal 3 (EUR BULLISH):**
```
📈 S5: EUR BULLISH signal 3 → Opening position #2/4
_CurrencySentiment_["EUR"] = {
    'direction': 'BULLISH',
    'count': 3,
    'positions_opened': 2  ← Incremented
}
→ Opens EURGBP BUY 0.25 lots (alternative pair)
→ EUR: 2, USD: 1, GBP: 1
```

**Signal 4 (EUR BULLISH):**
```
📈 S5: EUR BULLISH signal 4 → Opening position #3/4
_CurrencySentiment_["EUR"] = {
    'direction': 'BULLISH',
    'count': 4,
    'positions_opened': 3  ← Incremented
}
→ Opens EURJPY BUY 0.25 lots
→ EUR: 3, USD: 1, GBP: 1, JPY: 1
```

**Signal 5 (EUR BULLISH):**
```
📈 S5: EUR BULLISH signal 5 → Opening position #4/4
_CurrencySentiment_["EUR"] = {
    'direction': 'BULLISH',
    'count': 5,
    'positions_opened': 4  ← MAX REACHED
}
→ Opens EURCHF BUY 0.25 lots
→ EUR: 4 ← AT PROP FIRM LIMIT, USD: 1, GBP: 1, JPY: 1, CHF: 1
```

**Signal 6 (EUR BULLISH):**
```
⏭️  S5: EUR already at max positions (4/4), skipping
→ NO TRADE (at limit)
```

---

### Phase 3: Position Closes & Counter Decrements

**Position 1 Closes (EURUSD hits TP):**
```
update_currency_count("EURUSD", "remove")
→ EUR: 3, USD: 0
→ positions_opened: 4 → 3  ← Decremented in update_currency_count()

_CurrencySentiment_["EUR"] = {
    'direction': 'BULLISH',
    'count': 5,
    'positions_opened': 3  ← Now can scale again
}
```

**Signal 7 (EUR BULLISH - after close):**
```
📈 S5: EUR BULLISH signal 7 → Opening position #4/4
→ Opens EURAUD BUY 0.25 lots (fills the gap)
→ EUR: 4, AUD: 1
→ positions_opened: 3 → 4
```

---

### Phase 4: Conflicting Signal (Direction Change)

**Signal 8 (EUR BEARISH):**
```
⚠️  S5: EUR direction changed (BULLISH → BEARISH), resetting
   🔄 Closing 4 existing BULLISH position(s)

_CurrencySentiment_["EUR"] = {
    'direction': 'BEARISH',  ← Changed
    'count': 1,              ← Reset to 1
    'positions_opened': 0    ← Reset to 0
}
→ Closes all 4 EUR BULLISH positions (via S3 reversal logic)
→ NO NEW TRADE (need 2+ signals for confirmation)
```

**Signal 9 (EUR BEARISH):**
```
✅ S5: EUR BEARISH confirmed (2/2), opening first position
→ Opens EURUSD SELL 0.25 lots
→ EUR: 1
→ positions_opened: 0 → 1
```

---

## Configuration

### Globals.py
```python
# S5 Scaling Settings
news_filter_allowScaling = True              # Enable scaling
news_filter_maxScalePositions = 4            # Max 4 positions (1% compliance)
news_filter_scalingFactor = 1.0              # Equal sizing (0.25% each)
news_filter_confirmationRequired = True      # Require confirmation
news_filter_confirmationThreshold = 2        # Need 2 signals for first position
news_filter_conflictHandling = "reverse"     # Close on conflict

# Prop Firm Compliance
news_filter_maxTradePerCurrency = 4          # Max 4 positions per currency
```

### StrategyPresets.py
```python
def _apply_s5_preset():
    Globals.news_filter_maxTradePerCurrency = 4  # Allows scaling to 4
    Globals.news_filter_allowScaling = True      # Enables scaling
    Globals.news_filter_confirmationRequired = True
    # ... other settings
```

---

## Position Sizing

### Equal Sizing (scalingFactor = 1.0)
All positions are the same size for simplicity and maximum exposure.

| Position | Risk % | Lot Size (100k) | Lot Size (50k) | Lot Size (200k) |
|----------|--------|-----------------|----------------|-----------------|
| 1        | 0.25%  | 0.25            | 0.125          | 0.50            |
| 2        | 0.25%  | 0.25            | 0.125          | 0.50            |
| 3        | 0.25%  | 0.25            | 0.125          | 0.50            |
| 4        | 0.25%  | 0.25            | 0.125          | 0.50            |
| **Total**| **1.00%** | **1.00**      | **0.50**       | **2.00**        |

### Alternative: Decreasing Sizing (scalingFactor = 0.6)
If you prefer pyramiding (larger base, smaller additions):

```python
news_filter_scalingFactor = 0.6  # 60% of previous
```

| Position | Risk % | Lot Size (100k) | Total Exposure |
|----------|--------|-----------------|----------------|
| 1        | 0.25%  | 0.25            | 0.25%          |
| 2        | 0.15%  | 0.15            | 0.40%          |
| 3        | 0.09%  | 0.09            | 0.49%          |
| 4        | 0.054% | 0.054           | 0.544%         |

*Note: Decreasing sizing uses less capital but still scales exposure.*

---

## Implementation Details

### Code Location: News.py (Lines 650-730)

**Key Logic:**
1. Track `positions_opened` in `_CurrencySentiment_` dictionary
2. First 2 signals: Confirm direction, open position 1
3. Signals 3+: If `allowScaling=True` and `positions_opened < maxScalePositions`, open more
4. Conflicting signal: Reset counter, close positions if `conflictHandling="reverse"`

**Sentinel Values:**
- `positions_opened = 0`: No positions yet (in confirmation phase)
- `positions_opened = 1-3`: Scaling in progress (can add more)
- `positions_opened = 4`: At maximum (reject new signals)

### Code Location: Functions.py (Line 951)

**update_currency_count() Enhancement:**
```python
if operation == "remove":
    Globals._CurrencyCount_[currency] -= 1
    
    # S5 SCALING: Decrement positions_opened
    if Globals.news_filter_allowScaling:
        if currency in Globals._CurrencySentiment_:
            positions_opened = Globals._CurrencySentiment_[currency]['positions_opened']
            if positions_opened > 0:
                Globals._CurrencySentiment_[currency]['positions_opened'] -= 1
```

This ensures when a position closes, the counter decrements and allows new scaling.

---

## Prop Firm Compliance

### Maximum Exposure Calculation
```
Max Positions × Risk Per Trade = Total Exposure
4 positions × 0.25% risk = 1.00% exposure ✅
```

### Enforcement Layers

**Layer 1: can_open_trade() Function**
```python
if current_count >= news_filter_maxTradePerCurrency:  # 4
    return False  # Reject
```

**Layer 2: S5 Scaling Logic**
```python
if positions_opened >= maxScalePositions:  # 4
    print("Already at max positions, skipping")
    return {}  # Skip trade
```

**Layer 3: _CurrencyCount_ Real-time Tracking**
```python
_CurrencyCount_ = {"EUR": 4, ...}  # Live counter
```

### Compliance Guarantee
Even if scaling logic has a bug, `can_open_trade()` will **hard reject** any 5th position attempt. Double protection ensures prop firm rules are never violated.

---

## Testing Scenarios

### Test 1: Full Scaling Cycle
**Setup:** 6 EUR BULLISH signals in sequence

**Expected:**
```
Signal 1: Wait (1/2)
Signal 2: Open position #1 (EUR: 1)
Signal 3: Open position #2 (EUR: 2)
Signal 4: Open position #3 (EUR: 3)
Signal 5: Open position #4 (EUR: 4) ← AT LIMIT
Signal 6: Rejected (already at max)
```

**Validation:**
- `_CurrencyCount_["EUR"]` = 4 ✅
- `positions_opened` = 4 ✅
- Signal 6 shows "⏭️ already at max positions" ✅

---

### Test 2: Position Close + Re-scale
**Setup:** 5 signals → 4 positions → 1 closes → 1 new signal

**Expected:**
```
Signals 1-2: Open position #1
Signals 3-5: Open positions #2, #3, #4 (EUR: 4)
Position #2 closes: EUR: 3, positions_opened: 3
Signal 6: Open position #4 again (EUR: 4)
```

**Validation:**
- After close: `positions_opened` = 3 ✅
- After signal 6: `positions_opened` = 4 ✅
- Never exceeds 4 positions ✅

---

### Test 3: Conflict Handling
**Setup:** 4 BULLISH positions → 1 BEARISH signal

**Expected:**
```
4 EUR BULLISH positions open (EUR: 4)
EUR BEARISH signal arrives:
  ⚠️ Direction changed (BULLISH → BEARISH)
  🔄 Closing 4 existing BULLISH positions
  ⏳ EUR BEARISH signal 1/2, waiting
  
All 4 positions closed (EUR: 0)
positions_opened reset to 0
```

**Validation:**
- Conflicting signal resets `positions_opened` to 0 ✅
- Closes existing positions (if `conflictHandling="reverse"`) ✅
- Requires 2 new signals for opposite direction ✅

---

### Test 4: Prop Firm Limit Enforcement
**Setup:** Try to open 5th position via bug/exploit

**Expected:**
```
Signal forcing 5th position:
  can_open_trade("EURUSD") → False
  ❌ Position rejected by risk filters
  📊 Currency counts: {'EUR': 4, ...}
```

**Validation:**
- `can_open_trade()` hard rejects 5th position ✅
- Log shows rejection reason ✅
- Counter stays at 4 ✅

---

## Strategy Comparison

| Feature | S1 (Stack) | S5 (Confirm+Scale) |
|---------|------------|---------------------|
| **Confirmation** | ❌ No | ✅ Yes (2+ signals) |
| **Scaling** | ✅ Immediate | ✅ After confirmation |
| **Max Positions** | 4 | 4 |
| **Pair Restriction** | ❌ No (same pair) | ✅ Yes (1 per pair) |
| **Conflict Handling** | ❌ None | ✅ Reset/Reverse |
| **Signal Quality** | Low (any signal) | High (confirmed) |
| **Best For** | Strong trends | High-confidence setups |

**S1 vs S5 Example:**

**S1 Behavior (EURUSD only):**
```
Signal 1 → EURUSD BUY #1
Signal 2 → EURUSD BUY #2
Signal 3 → EURUSD BUY #3
Signal 4 → EURUSD BUY #4
(All on same pair, no confirmation needed)
```

**S5 Behavior (Multiple pairs):**
```
Signal 1 → Wait (1/2)
Signal 2 → EURUSD BUY #1 (confirmed)
Signal 3 → EURGBP BUY #2 (scaling)
Signal 4 → EURJPY BUY #3 (scaling)
Signal 5 → EURCHF BUY #4 (scaling)
(Different pairs, confirmation required)
```

---

## Configuration Options

### Conservative (Confirmation Only)
```python
news_filter_allowScaling = False              # Disable scaling
news_filter_maxTradePerCurrency = 1           # Only 1 position
news_filter_confirmationThreshold = 2         # Require 2 signals
```
**Result:** Max 0.25% exposure, very selective

### Balanced (Confirmation + Partial Scaling)
```python
news_filter_allowScaling = True
news_filter_maxScalePositions = 2             # Max 2 positions
news_filter_scalingFactor = 0.6               # Decreasing size
news_filter_confirmationThreshold = 2
```
**Result:** Max ~0.40% exposure, quality + scaling

### Aggressive (Full Scaling)
```python
news_filter_allowScaling = True
news_filter_maxScalePositions = 4             # Max 4 positions ← CURRENT
news_filter_scalingFactor = 1.0               # Equal size
news_filter_confirmationThreshold = 2
```
**Result:** Max 1.00% exposure, maximum conviction trades

---

## Advantages Over S1

1. **Quality Filter:** Only trades confirmed setups (2+ signals)
2. **Diversification:** Forces different pairs instead of stacking one
3. **Conflict Aware:** Handles opposing signals intelligently
4. **Position Tracking:** Knows exactly how many positions per currency
5. **Adaptive:** Scales based on incoming signal strength

---

## Summary

✅ **S5 Scaling is now fully implemented and prop firm compliant**

**Key Points:**
- Requires 2+ signals before first position (confirmation)
- Scales up to 4 positions as more signals arrive (adaptive)
- Equal sizing: 0.25% × 4 = 1.00% max exposure
- Decrements counter when positions close (allows re-scaling)
- Resets on conflicting signals (handles reversals)
- Double-protected by `can_open_trade()` enforcement

**Ready for live trading with full compliance! 🎯**
