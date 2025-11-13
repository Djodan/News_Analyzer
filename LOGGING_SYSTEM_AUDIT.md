# News Analyzer - Logging System Audit & Implementation Plan
**Date**: November 12, 2025  
**Purpose**: Comprehensive event logging for strategy debugging and performance analysis

---

## 📊 Current Logging Status

### ✅ **WHAT WE HAVE** (Existing Logs)

#### 1. **Output.txt** (Server Console Log)
- **Location**: Root folder
- **Content**: All `print()` statements from Server.py
- **Method**: TeeOutput class redirects stdout
- **Rotation**: Overwrites each server session
- **Coverage**: 
  - ✅ Server startup/shutdown
  - ✅ MT5 client communications (Packets A-E)
  - ✅ Trade execution commands
  - ✅ Trade acknowledgments
  - ✅ Strategy changes
  - ✅ Weekly goal tracking
  - ✅ Error messages

#### 2. **received_log.jsonl** (Raw MT5 Data)
- **Location**: Root folder
- **Content**: All incoming HTTP POST payloads from MT5
- **Method**: `append_log()` in Functions.py
- **Rotation**: Appends indefinitely
- **Coverage**:
  - ✅ Full Packet A (open/closed positions)
  - ✅ Full Packet B (account balance/equity)
  - ✅ Full Packet C (symbol data: ATR, spread, bid/ask)
  - ✅ Full Packet D (position analytics: MAE/MFE/unrealized)
  - ✅ Full Packet E (trade close details)
  - ✅ Timestamps for all events

#### 3. **trades_log.csv** (Trade Performance Data)
- **Location**: `_dictionaries/trades_log.csv`
- **Content**: Closed trade analytics
- **Method**: `write_trade_to_csv()` in Functions.py
- **Rotation**: Appends on trade close
- **Coverage**:
  - ✅ TID, Ticket, Symbol, Type
  - ✅ Entry/Exit prices & times
  - ✅ Profit (USD & pips)
  - ✅ MAE/MFE (pips)
  - ✅ Close reason (TP/SL/Manual)
  - ✅ Strategy ID

#### 4. **Dictionary Snapshots** (State Tracking CSVs)
- **Location**: `_dictionaries/` folder
- **Content**: 8 CSV files with current state
- **Method**: `save_news_dictionaries()` called after events
- **Rotation**: Overwrites on each snapshot
- **Coverage**:
  - ✅ `_currencies.csv` - News events (NID tracking)
  - ✅ `_affected.csv` - Pairs affected by news
  - ✅ `_trades.csv` - Queued/executed trades
  - ✅ `_currency_count.csv` - Currency exposure
  - ✅ `_pair_count.csv` - Pair exposure
  - ✅ `_currency_positions.csv` - S3 rolling positions
  - ✅ `_pairs_traded_week.csv` - S4 weekly locks
  - ✅ `_currency_sentiment.csv` - S5 sentiment tracking

---

## ❌ **WHAT WE'RE MISSING** (Critical Gaps)

### 1. **Strategy Decision Logging** ⚠️ CRITICAL
**Problem**: Cannot trace WHY a strategy made a specific decision

**Missing Events**:
- ❌ S1: When currency hits 4-position limit (rejection reason)
- ❌ S2: Alternative pair search process (what was tried, why rejected)
- ❌ S3: Reversal decisions (old position vs new signal)
- ❌ S4: Weekly lock rejections (pair already traded this week)
- ❌ S5: Confirmation phase progress (signal 1/2, 2/2, etc.)
- ❌ S5: Scaling decisions (why opened position #2, #3, #4)
- ❌ S5: Conflict handling (opposing signals, reset logic)

**Impact**: 
- Cannot debug why S5 didn't scale when expected
- Cannot see if S2 tried alternatives before giving up
- Cannot trace S3 reversal logic flow

---

### 2. **Risk Filter Rejections** ⚠️ CRITICAL
**Problem**: Trades rejected by `can_open_trade()` are logged minimally

**Missing Events**:
- ❌ Which filter rejected (maxTrades vs maxTradePerCurrency)
- ❌ Current exposure snapshot at rejection time
- ❌ Attempted symbol and currency breakdown
- ❌ Timeline of rejections (pattern analysis)

**Impact**:
- Cannot see if hitting 1% limit too early
- Cannot analyze if filter settings are too restrictive
- Cannot debug why valid signals were rejected

---

### 3. **News Processing Events** ⚠️ IMPORTANT
**Problem**: Limited visibility into news event lifecycle

**Missing Events**:
- ❌ STEP 1: Forecast fetch from Perplexity (response content)
- ❌ STEP 2: Event monitoring loop (time until next event)
- ❌ STEP 3: Actual fetch attempts (retry logic, failures)
- ❌ STEP 4: Affect calculation details (inverse indicators)
- ❌ STEP 5: ChatGPT signal generation (full prompt & response)
- ❌ STEP 6: Multi-event aggregation (conflict resolution)

**Impact**:
- Cannot debug why forecast was wrong
- Cannot see if ChatGPT gave unexpected signals
- Cannot trace aggregation logic for simultaneous events

---

### 4. **Performance Metrics** ⚠️ IMPORTANT
**Problem**: No strategy comparison analytics

**Missing Metrics**:
- ❌ Strategy win rate (S1 vs S2 vs S3 vs S4 vs S5)
- ❌ Average hold time per strategy
- ❌ Average MAE/MFE per strategy
- ❌ Correlation: NID affect vs trade outcome
- ❌ Time from news release to trade execution
- ❌ S5 confirmation accuracy (did waiting improve win rate?)

**Impact**:
- Cannot determine which strategy performs best
- Cannot optimize confirmation threshold for S5
- Cannot justify scaling vs single-position approaches

---

### 5. **Session Analytics** ⚠️ NICE-TO-HAVE
**Problem**: No historical session tracking

**Missing Events**:
- ❌ Server uptime per session
- ❌ Total trades executed per session
- ❌ Net profit/loss per session
- ❌ API call counts (Perplexity + ChatGPT)
- ❌ Error rate per session

**Impact**:
- Cannot track long-term performance trends
- Cannot optimize API usage to reduce costs

---

### 6. **Error Tracking** ⚠️ IMPORTANT
**Problem**: Errors printed to console but not structured

**Missing Events**:
- ❌ Exception stack traces (lost when Output.txt overwrites)
- ❌ Error frequency analysis
- ❌ Specific failure points (Perplexity timeout, ChatGPT rate limit)

**Impact**:
- Cannot debug recurring errors
- Cannot identify failure patterns

---

## 🎯 **Recommended Implementation**

### **Option A: Enhanced Structured Logging** (RECOMMENDED)
Create a centralized logging system with multiple outputs:

1. **event_log.jsonl** (Structured Events)
   ```json
   {
     "timestamp": "2025-11-12T10:30:05",
     "level": "INFO",
     "category": "STRATEGY",
     "strategy": "S5",
     "event": "CONFIRMATION_PROGRESS",
     "data": {
       "currency": "EUR",
       "direction": "BULLISH",
       "count": 1,
       "threshold": 2,
       "positions_opened": 0,
       "status": "WAITING"
     }
   }
   ```

2. **strategy_decisions.csv** (Human-Readable Strategy Log)
   ```csv
   timestamp,strategy,event_type,currency,symbol,decision,reason,exposure_before,exposure_after
   2025-11-12 10:30:05,S5,CONFIRMATION,EUR,EURUSD,WAIT,"Signal 1/2",0,0
   2025-11-12 10:35:12,S5,CONFIRMATION,EUR,EURUSD,OPEN,"Signal 2/2 confirmed",0,1
   2025-11-12 10:40:23,S5,SCALING,EUR,EURGBP,OPEN,"Signal 3 - Position #2/4",1,2
   ```

3. **rejection_log.csv** (Trade Rejections)
   ```csv
   timestamp,strategy,symbol,rejected_by,current_exposure,limit,attempted_volume
   2025-11-12 11:00:00,S2,EURUSD,maxTradePerCurrency,4,4,0.25
   ```

4. **news_events.csv** (News Processing Log)
   ```csv
   timestamp,event_key,currency,event_name,forecast,actual,affect,nid,pairs_affected,pairs_executed,tp_count,sl_count
   2025-11-12 08:30:00,EUR_2025-11-12_08:30,EUR,Unemployment Rate,4.5,4.2,POSITIVE,5,6,4,2,2
   ```

---

### **Option B: Logging Class Architecture**
Create `Logger.py` with centralized logging:

```python
class NewsLogger:
    def __init__(self):
        self.event_log = "logs/event_log.jsonl"
        self.strategy_log = "logs/strategy_decisions.csv"
        self.rejection_log = "logs/rejection_log.csv"
        self.news_log = "logs/news_events.csv"
    
    def log_strategy_decision(self, strategy, event_type, data):
        """Log strategy-specific decisions"""
        
    def log_rejection(self, strategy, symbol, rejected_by, exposure, limit):
        """Log trade rejections with context"""
        
    def log_news_event(self, event_key, event_data):
        """Log news event processing"""
        
    def log_s5_confirmation(self, currency, count, threshold, status):
        """S5-specific confirmation tracking"""
```

---

## 📋 **Implementation Checklist**

### Phase 1: Critical Logging (Week 1)
- [ ] Create `Logger.py` with centralized logging class
- [ ] Add strategy decision logging (S1-S5)
- [ ] Add risk filter rejection logging
- [ ] Add S5 confirmation/scaling progress tracking
- [ ] Add news event lifecycle logging

### Phase 2: Analytics & Metrics (Week 2)
- [ ] Create `Analytics.py` for performance metrics
- [ ] Add strategy comparison reports
- [ ] Add win rate tracking per strategy
- [ ] Add MAE/MFE analysis per strategy
- [ ] Add correlation analysis (NID affect → outcome)

### Phase 3: Visualization (Week 3)
- [ ] Create `ReportGenerator.py` for HTML reports
- [ ] Generate daily strategy performance dashboard
- [ ] Generate weekly comparison charts
- [ ] Export to Excel with pivot tables

---

## 🔍 **Specific Use Cases**

### Use Case 1: "Why didn't S5 scale to 4 positions?"
**Current State**: Check `_currency_sentiment.csv` → see count=3, positions_opened=1  
**Problem**: No log of WHY it stopped scaling  

**With New Logging**:
```
[event_log.jsonl]
{"event": "S5_SCALING", "currency": "EUR", "count": 3, "positions_opened": 1, "decision": "SKIP", "reason": "Already at max (news_filter_maxScalePositions=1)"}
```

---

### Use Case 2: "Why was EURUSD rejected for EUR news?"
**Current State**: Console shows "Position rejected by risk filters"  
**Problem**: Don't know which filter or current exposure  

**With New Logging**:
```csv
[rejection_log.csv]
timestamp,strategy,symbol,rejected_by,currency_exposure,limit,attempted_currency
2025-11-12 10:30:00,S2,EURUSD,maxTradePerCurrency,EUR:4,4,EUR
```

---

### Use Case 3: "Did S2 try alternative pairs?"
**Current State**: No visibility into alternative search  
**Problem**: Can't see if search worked or failed  

**With New Logging**:
```
[event_log.jsonl]
{"event": "S2_ALTERNATIVE_SEARCH", "currency": "EUR", "original": "EURUSD", "tried": ["EURGBP", "EURJPY", "EURCHF"], "selected": "EURGBP", "reason": "GBP exposure = 2/4"}
```

---

## ⚡ **Quick Win: Minimal Implementation**

If full logging is too much work, start with these **3 critical additions**:

1. **Add to News.py (S5 confirmation)**:
   ```python
   print(f"[S5-LOG] {currency} {affect} | Count: {count}/{threshold} | Opened: {positions_opened}/{max} | Action: {decision}")
   ```

2. **Add to Functions.py (risk rejections)**:
   ```python
   if current_count >= max:
       print(f"[REJECT-LOG] {symbol} | Filter: maxTradePerCurrency | {currency}: {current_count}/{max}")
   ```

3. **Add to News.py (trade signals)**:
   ```python
   print(f"[SIGNAL-LOG] NID_{nid} | {currency} {affect} | Signals: {trading_signals}")
   ```

---

## 📊 **Summary**

### Current Coverage: **60%** ✅
- ✅ Trade execution (Output.txt, received_log.jsonl, trades_log.csv)
- ✅ State snapshots (_dictionaries/*.csv)
- ✅ Basic console output

### Missing Coverage: **40%** ❌
- ❌ Strategy decision reasoning
- ❌ Risk filter rejection details
- ❌ News processing lifecycle
- ❌ Performance analytics
- ❌ Error tracking

### Recommended Action:
**Implement Option A (Enhanced Structured Logging)** with Phase 1 critical items first. This will provide:
- Full strategy decision traceability
- Risk filter rejection analysis
- S5 confirmation/scaling debugging
- News event lifecycle tracking

**Estimated Time**: 2-3 hours for Phase 1 implementation
