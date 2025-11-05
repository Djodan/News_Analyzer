# Quick Reference: Multiple Events Rule

## The Rule (News_Rules.txt STEP 2)

**When 2+ events for same currency at same time:**

### 1️⃣ All Same Direction?
```
Both POSITIVE → Use POSITIVE
Both NEGATIVE → Use NEGATIVE
```

### 2️⃣ Events Conflict?
**Use Impact Hierarchy:**
```
Monetary > Inflation > Jobs > GDP > Trade > Activity > Sentiment
          (highest)                                    (lowest)
```

### 3️⃣ Equal Impact + Conflict?
```
→ NEUTRAL (no trade)
```

### 4️⃣ Some Events N/A?
```
→ Ignore incomplete, use only complete events
```

---

## Examples

### ✅ Example 1: Both Positive
```
GBP Unemployment: 4.5% → 4.2% (POSITIVE)
GBP Employment: 50K → 75K (POSITIVE)
───────────────────────────────────
Result: POSITIVE → GBP strengthens → BUY GBP pairs
```

### ✅ Example 2: Monetary Wins
```
GBP Interest Rate: 5.00% → 5.25% (POSITIVE - Monetary)
GBP Retail Sales: 0.5% → 0.1% (NEGATIVE - Activity)
───────────────────────────────────
Conflict! Monetary beats Activity
Result: POSITIVE → BUY GBP pairs
```

### ✅ Example 3: Equal Impact = Neutral
```
GBP Manufacturing PMI: 50 → 52.5 (POSITIVE - Activity)
GBP Services PMI: 53 → 49.0 (NEGATIVE - Activity)
───────────────────────────────────
Same category, conflict
Result: NEUTRAL → No trade
```

---

## Testing

**Manual Test:**
1. Copy News_Rules.txt
2. Add: "MULTIPLE EVENTS AT SAME TIME: [events]"
3. Send to ChatGPT
4. Verify output

**Files:**
- `test_multiple_events_manual.md` - 7 test cases
- `IMPLEMENTATION_GUIDE_MultipleEvents.md` - Code to add

---

## Impact Hierarchy (Quick)

```
1. Monetary    ← Rate decisions (HIGHEST IMPACT)
2. Inflation   ← CPI, PPI
3. Jobs        ← Employment, Unemployment
4. GDP         ← Growth
5. Trade       ← Trade Balance
6. Activity    ← PMI, Retail Sales
7. Sentiment   ← Confidence (LOWEST IMPACT)
```

---

## AI Prompt Format

```
MULTIPLE EVENTS AT SAME TIME:

- [CURRENCY] [EVENT_1]: Forecast=[F], Actual=[A]
- [CURRENCY] [EVENT_2]: Forecast=[F], Actual=[A]

Available trading pairs: [PAIRS]

Remember STEP 2: Multiple Events at the Same Time rules.
```

---

## Expected Behavior

### Before Fix
```
❌ Event 1 → Queue trades
❌ Event 2 → Queue trades (DUPLICATE!)
```

### After Fix
```
✅ Detect multiple events
✅ Aggregate using rules
✅ Queue trades ONCE
```

---

## Real Example (Nov 11, 2025)

**GBP @ 02:00:**
- Unemployment Rate
- Employment Change

**Without rule:** 2 separate signals (might conflict)
**With rule:** 1 aggregated signal (consistent)

---

## Quick Check

| Scenario | Action |
|----------|--------|
| All POSITIVE | → Use POSITIVE |
| All NEGATIVE | → Use NEGATIVE |
| Conflict, different impact | → Use highest impact |
| Conflict, same impact | → NEUTRAL |
| All N/A | → NEUTRAL |
| Mixed N/A + complete | → Ignore N/A |
