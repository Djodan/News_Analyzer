# Forecast Retry Logic - Implementation Summary

## Problem Solved
When AI returns only the **Actual** value without **Forecast**, the system now:
1. Detects the missing Forecast
2. Immediately queries again (no delay) specifically for Forecast
3. Retrieves the previously saved Actual from dictionary
4. Processes both values together OR proceeds with Actual only if Forecast unavailable

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Fetch Forecast + Actual (request_type="both")          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │ Parse Response                        │
        │  - Check for Forecast value           │
        │  - Check for Actual value             │
        └───────────────────────────────────────┘
                            ↓
    ┌──────────────────────────────────────────────┐
    │ Actual Found? Forecast Found?                │
    └──────────────────────────────────────────────┘
         │                    │                  │
    YES + YES           YES + NO           NO + ?
         │                    │                  │
         ↓                    ↓                  ↓
    ✅ SUCCESS          🔄 RETRY          ❌ FAILED
    Process both       Forecast          Skip event
    values                  ↓
                   ┌─────────────────────────────────┐
                   │ Check: forecast_retry_attempted?│
                   └─────────────────────────────────┘
                            │              │
                         False          True
                            │              │
                            ↓              ↓
                  ┌──────────────────┐  Skip retry
                  │ Query Forecast   │  (already tried)
                  │ request_type=    │       ↓
                  │ "forecast"       │  ⚠️ MOVING ON
                  │                  │  (Proceed without
                  │ Set flag=True    │   Forecast)
                  └──────────────────┘
                            ↓
                   Parse Forecast response
                            ↓
                  ┌──────────────────┐
                  │ Forecast Found?  │
                  └──────────────────┘
                     │            │
                   YES           NO
                     │            │
                     ↓            ↓
              ✅ SUCCESS    ⚠️ MOVING ON
              Both values  (Actual only,
              retrieved    affect=NEUTRAL)
```

## Code Changes

### 1. News.py - Added Forecast Retry Logic
**Location:** Lines 848-920 (fetch_forecast_and_actual function)

**Key Changes:**
- Added `forecast_found` and `actual_found` boolean flags
- Check if `actual_found=True` AND `forecast_found=False` AND `forecast_retry_attempted=False`
- If true, query again with `request_type="forecast"`
- Set `forecast_retry_attempted=True` to prevent infinite loops
- Retrieve saved Actual value from `_Currencies_` dictionary
- Process both values OR proceed with Actual only

### 2. News.py - Added forecast_retry_attempted Field
**Location:** Lines 410 and 456 (_Currencies_ initialization)

**Added field:**
```python
'forecast_retry_attempted': False  # Flag to prevent multiple forecast retries
```

This flag ensures the retry only happens ONCE per event.

## Test Results

### ✅ Test 1: Successful Forecast Retry
**File:** `test_forecast_retry.py`
- Initial query returns: "Actual : -2.5"
- Retry query returns: "Forecast : -11.25"
- **Result:** Both values retrieved, 2 AI calls total

### ✅ Test 2: Forecast Unavailable After Retry
**File:** `test_forecast_retry_fail.py`
- Initial query returns: "Actual : -2.5"
- Retry query returns: "Forecast : N/A"
- **Result:** Proceeds with Actual only (affect=NEUTRAL), 2 AI calls total

### ✅ Test 3: Single Retry Only (No Loops)
**File:** `test_forecast_single_retry.py`
- Initial query returns: "Actual : -2.5"
- Retry query returns: "Actual : -2.5" (still no Forecast)
- Second heartbeat checks retry condition
- **Result:** Retry skipped (flag=True), exactly 2 AI calls total

## Log Output Examples

### Successful Retry:
```
  [OK] Actual: -2.5
  Stored actual value in _Currencies_[USD_2025-11-18_08:15_abc123]
  [ERROR] No forecast found in response
  [PARTIAL DATA] Going back to query for Forecast because response only contained Actual: -2.5
  Actual value is already saved, now fetching missing Forecast...
  [FORECAST RETRY] Response: Forecast : -11.25
  [OK] Forecast retrieved: -11.25
  [SUCCESS] Both Forecast and Actual retrieved
```

### Failed Retry (Forecast Unavailable):
```
  [OK] Actual: -2.5
  [ERROR] No forecast found in response
  [PARTIAL DATA] Going back to query for Forecast because response only contained Actual: -2.5
  [FORECAST RETRY] Response: Forecast : N/A
  [N/A] Forecast still not available
  [MOVING ON] Proceeding without Forecast (Actual: -2.5, Forecast: N/A)
  Reason: Forecast not available after dedicated query attempt
```

## Benefits

1. **Handles Reversed Data:** When AI accidentally swaps Forecast/Actual positions
2. **No Delays:** Immediate retry (no 2-minute wait)
3. **Single Retry:** Flag prevents infinite loops
4. **Data Preservation:** Actual value saved and reused
5. **Graceful Degradation:** Proceeds with partial data if Forecast unavailable

## API Call Efficiency

- **Before:** 1 call per event (might fail with partial data)
- **After:** 1-2 calls per event (2 only when Forecast missing)
- **Max calls:** 2 per event (protected by forecast_retry_attempted flag)
