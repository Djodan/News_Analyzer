# Multiple Events at Same Time - Test Cases

This document provides test scenarios to verify that the AI correctly handles multiple events occurring at the same timestamp for the same currency according to **News_Rules.txt STEP 2**.

---

## Test Setup

**Available Trading Pairs:** GBPAUD, GBPCHF, GBPJPY, GBPUSD, EURGBP, GBPNZD, GBPCAD

**Testing Currency:** GBP (affects all pairs listed above)

---

## TEST 1: All Events Same Direction (POSITIVE)
### Scenario
Two GBP events at the same time, both POSITIVE:

| Event | Forecast | Actual | Outcome |
|-------|----------|--------|---------|
| Unemployment Rate | 4.5% | 4.2% | POSITIVE (lower unemployment) |
| Employment Change | 50K | 75K | POSITIVE (higher employment) |

### Expected AI Analysis
1. **STEP 1:** Both events → POSITIVE outcomes
2. **STEP 2:** All events same direction (both POSITIVE) → Use shared direction
3. **Result:** GBP STRENGTHENS
4. **STEP 3:** GBP is BASE in all pairs → BUY all pairs

### Expected Output
```
GBPAUD : BUY, GBPCHF : BUY, GBPJPY : BUY, GBPUSD : BUY, EURGBP : SELL, GBPNZD : BUY, GBPCAD : BUY
```

Note: EURGBP is SELL because GBP is QUOTE (EUR/GBP), so GBP strengthens → SELL

---

## TEST 2: All Events Same Direction (NEGATIVE)
### Scenario
Two GBP events at the same time, both NEGATIVE:

| Event | Forecast | Actual | Outcome |
|-------|----------|--------|---------|
| GDP Growth Rate | 0.5% | 0.2% | NEGATIVE (lower GDP) |
| Manufacturing PMI | 52.0 | 48.5 | NEGATIVE (below 50) |

### Expected AI Analysis
1. **STEP 1:** Both events → NEGATIVE outcomes
2. **STEP 2:** All events same direction (both NEGATIVE) → Use shared direction
3. **Result:** GBP WEAKENS
4. **STEP 3:** GBP is BASE in most pairs → SELL

### Expected Output
```
GBPAUD : SELL, GBPCHF : SELL, GBPJPY : SELL, GBPUSD : SELL, EURGBP : BUY, GBPNZD : SELL, GBPCAD : SELL
```

---

## TEST 3: Conflicting Events → Monetary Wins (Highest Impact)
### Scenario
Two GBP events conflict, Monetary vs Activity:

| Event | Category | Forecast | Actual | Outcome |
|-------|----------|----------|--------|---------|
| Interest Rate Decision | Monetary | 5.00% | 5.25% | POSITIVE (rate increase) |
| Retail Sales | Activity | 0.5% | 0.1% | NEGATIVE (lower sales) |

### Expected AI Analysis
1. **STEP 1:** Rate Decision → POSITIVE, Retail Sales → NEGATIVE
2. **STEP 2:** Conflicting events → Use impact hierarchy
   - **Impact Hierarchy:** Monetary > Inflation > Jobs > GDP > Trade > Activity
   - Monetary (POSITIVE) beats Activity (NEGATIVE)
3. **Result:** Use Monetary outcome → GBP STRENGTHENS
4. **STEP 3:** GBP is BASE → BUY

### Expected Output
```
GBPAUD : BUY, GBPCHF : BUY, GBPJPY : BUY, GBPUSD : BUY, EURGBP : SELL, GBPNZD : BUY, GBPCAD : BUY
```

**Key Point:** Monetary decision overrides Activity-level data

---

## TEST 4: Conflicting Events → Inflation Wins Over Jobs
### Scenario
Two GBP events conflict, Inflation vs Jobs:

| Event | Category | Forecast | Actual | Outcome |
|-------|----------|----------|--------|---------|
| CPI (Consumer Price Index) | Inflation | 2.5% | 3.1% | POSITIVE (higher inflation strengthens) |
| Unemployment Rate | Jobs | 4.0% | 4.5% | NEGATIVE (higher unemployment) |

### Expected AI Analysis
1. **STEP 1:** CPI → POSITIVE, Unemployment → NEGATIVE
2. **STEP 2:** Conflicting events → Use impact hierarchy
   - **Impact Hierarchy:** Monetary > Inflation > Jobs
   - Inflation (POSITIVE) beats Jobs (NEGATIVE)
3. **Result:** Use Inflation outcome → GBP STRENGTHENS
4. **STEP 3:** GBP is BASE → BUY

### Expected Output
```
GBPAUD : BUY, GBPCHF : BUY, GBPJPY : BUY, GBPUSD : BUY, EURGBP : SELL, GBPNZD : BUY, GBPCAD : BUY
```

**Key Point:** Inflation data takes precedence over Jobs data

---

## TEST 5: Equal Impact Conflict → NEUTRAL
### Scenario
Two GBP events conflict, both at Activity level:

| Event | Category | Forecast | Actual | Outcome |
|-------|----------|----------|--------|---------|
| Manufacturing PMI | Activity | 50.0 | 52.5 | POSITIVE (above 50) |
| Services PMI | Activity | 53.0 | 49.0 | NEGATIVE (below 50) |

### Expected AI Analysis
1. **STEP 1:** Manufacturing → POSITIVE, Services → NEGATIVE
2. **STEP 2:** Conflicting events, both Activity level → Equal impact
   - Cannot use hierarchy (same category)
   - Equal impact + conflict = NEUTRAL
3. **Result:** NEUTRAL

### Expected Output
```
NEUTRAL
```

**Key Point:** Same-category conflicts with equal weight result in no trade

---

## TEST 6: Ignore Incomplete Event (N/A)
### Scenario
Two GBP events, one incomplete:

| Event | Forecast | Actual | Status |
|-------|----------|--------|--------|
| GDP Growth Rate | N/A | 0.5% | INCOMPLETE (Forecast N/A) |
| Unemployment Rate | 4.5% | 4.2% | COMPLETE (POSITIVE) |

### Expected AI Analysis
1. **STEP 1:** 
   - GDP → N/A detected → NEUTRAL (skip)
   - Unemployment → POSITIVE
2. **STEP 2:** Ignore incomplete events → Use only complete data
3. **Result:** Only Unemployment counts → GBP STRENGTHENS
4. **STEP 3:** GBP is BASE → BUY

### Expected Output
```
GBPAUD : BUY, GBPCHF : BUY, GBPJPY : BUY, GBPUSD : BUY, EURGBP : SELL, GBPNZD : BUY, GBPCAD : BUY
```

**Key Point:** N/A events are ignored; decision based on complete data only

---

## TEST 7: All Events Incomplete → NEUTRAL
### Scenario
Two GBP events, both incomplete:

| Event | Forecast | Actual | Status |
|-------|----------|--------|--------|
| GDP Growth Rate | N/A | 0.5% | INCOMPLETE |
| Trade Balance | 5.0B | N/A | INCOMPLETE |

### Expected AI Analysis
1. **STEP 1:** Both events have N/A → Both NEUTRAL
2. **STEP 2:** No complete events available
3. **Result:** NEUTRAL

### Expected Output
```
NEUTRAL
```

**Key Point:** When no complete data exists, no trade is made

---

## How to Test

### Manual Testing
1. Copy one test case prompt from below
2. Send to ChatGPT (GPT-4)
3. Verify output matches expected result

### Test Prompt Template
```
[Paste entire News_Rules.txt here]

═══════════════════════════════════════════════════════════════════════════════

MULTIPLE EVENTS AT SAME TIME:

- GBP (United Kingdom) [EVENT_1]: Forecast=[FORECAST], Actual=[ACTUAL]
- GBP (United Kingdom) [EVENT_2]: Forecast=[FORECAST], Actual=[ACTUAL]

Available trading pairs: GBPAUD, GBPCHF, GBPJPY, GBPUSD, EURGBP, GBPNZD, GBPCAD

Remember STEP 2: Multiple Events at the Same Time rules.

Output your trading decision:
```

---

## Success Criteria

✅ **PASS:** AI output matches expected output for each test case

❌ **FAIL:** AI output deviates from expected (indicates rule not followed)

### Common Failure Patterns
- AI provides explanation instead of just output → Format violation
- AI ignores impact hierarchy → Logic error
- AI doesn't aggregate same-direction events → Rule not understood
- AI doesn't return NEUTRAL for equal-impact conflicts → Edge case missed

---

## Implementation in News.py

The Python code should implement these same rules when processing multiple events:

```python
# When multiple events for same currency at same timestamp:
def aggregate_events(events_at_same_time):
    """
    Apply STEP 2 from News_Rules.txt
    """
    # 1. Filter out incomplete events (N/A)
    complete_events = [e for e in events_at_same_time 
                       if e['forecast'] != 'N/A' and e['actual'] != 'N/A']
    
    if not complete_events:
        return "NEUTRAL"
    
    # 2. Calculate outcomes
    outcomes = [calculate_outcome(e) for e in complete_events]
    
    # 3. Check if all same direction
    if all(o == "POSITIVE" for o in outcomes):
        return "POSITIVE"
    if all(o == "NEGATIVE" for o in outcomes):
        return "NEGATIVE"
    if all(o == "NEUTRAL" for o in outcomes):
        return "NEUTRAL"
    
    # 4. Conflict detected → Use impact hierarchy
    impact_order = {
        "Monetary": 1,
        "Inflation": 2,
        "Jobs": 3,
        "GDP": 4,
        "Trade": 5,
        "Activity": 6,
        "Sentiment": 7
    }
    
    # Find highest impact event
    highest_impact_event = min(complete_events, 
                               key=lambda e: impact_order.get(e['category'], 99))
    
    # 5. Check if multiple events at same impact level
    highest_impact = impact_order[highest_impact_event['category']]
    same_impact_events = [e for e in complete_events 
                          if impact_order.get(e['category'], 99) == highest_impact]
    
    if len(same_impact_events) > 1:
        same_impact_outcomes = [calculate_outcome(e) for e in same_impact_events]
        if len(set(same_impact_outcomes)) > 1:  # Conflicting outcomes
            return "NEUTRAL"
    
    # 6. Use highest impact event's outcome
    return calculate_outcome(highest_impact_event)
```

---

## Notes

- This test suite ensures consistent behavior when multiple news events occur simultaneously
- The impact hierarchy prevents random/inconsistent trading decisions
- NEUTRAL is returned when no clear direction can be determined
- This prevents over-trading and reduces risk from conflicting signals
