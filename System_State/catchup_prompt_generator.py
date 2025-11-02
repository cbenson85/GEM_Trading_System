# GEM Trading System - AI Catch-Up Prompt
**Last Updated**: 2025-11-02 21:00:00
**System Version**: 5.1.0-SCANNER-APPROACH
**Current Phase**: Phase 3: Data Collection - Running Scanner for Complete Dataset

---

## 🚨 CRITICAL CONTEXT FOR AI

### What You're Walking Into
After extensive filter evolution and enrichment attempts, we discovered the ROOT CAUSE of all issues: **CLEAN.json doesn't have complete data** (no entry_date, entry_price, peak_date, peak_price). The original scanner DOES capture all this data, but it was stripped during the COVID filter process.

### The Solution
**Re-run the scanner for 2010-2024 (excluding COVID years)** to get complete data from the start. Then enrichment/filtering becomes trivial.

### Current Status
- User is testing 2022-2024 scanner run right now
- If successful, will run 2010-2019 next
- Both outputs are cumulative to CLEAN.json
- After scans: add drawdown velocity → filter → done!

---

## 📊 COMPLETE HISTORY & CONTEXT

### Original Problem
Started with 200 stocks in CLEAN.json that only had:
```json
{
  "ticker": "ABVC",
  "year": 2014,
  "gain_percent": 900,
  "days_to_peak": 28
}
```

**Missing:** entry_date, entry_price, peak_date, peak_price

### What We Tried (And Why It Failed)

**Attempt 1: Enrichment Script**
- Tried to "find" the explosive windows using Polygon API
- Failed because we were guessing where to look
- Only enriched 109/200 stocks (54.5%)
- 91 stocks failed with "Could not find explosive window"

**Why It Failed:**
- Without entry_date, script had to search entire years
- Searched for exact gain match (90% tolerance)
- Many stocks had windows outside search range
- Data source mismatches between original scan and enrichment

**Attempt 2: Widened Search**
- Changed to accept ANY 500%+ window
- Still only 109/200 enriched
- Same 91 stocks still failing

**Why It Failed:**
- Fundamental issue: guessing where windows are
- Some stocks delisted/changed symbols
- Polygon data gaps for old stocks
- No way to verify we found the SAME window as original scan

### Filter Evolution (All Failed Due to Missing Data)

1. **V1.0**: 90% retention, 30 days → All failed
2. **V2.0**: 80% retention, 21 days from peak → 17/200 (8.5%)
3. **V3.0**: 120-day window, speed-adjusted → 0/200 (all failed - no enriched data)
4. **V4.0**: Drawdown velocity + realistic thresholds → Ready but needs complete data

---

## ✅ THE ACTUAL SOLUTION: RE-RUN SCANNER

### Why This Works

The **explosive_stock_scanner.py** already captures EVERYTHING:
```python
stock_data = {
    'ticker': ticker,
    'year_discovered': year,
    'entry_date': best_window['entry_date'],      # ✅ Has it!
    'entry_price': best_window['entry_price'],    # ✅ Has it!
    'peak_date': best_window['peak_date'],        # ✅ Has it!
    'peak_price': best_window['peak_price'],      # ✅ Has it!
    'gain_percent': best_window['gain_percent'],  # ✅ Has it!
    'days_to_peak': best_window['days_to_peak'],  # ✅ Has it!
    'data_source': best_window['data_source']
}
```

**The data was there all along!** It just got stripped somewhere in the pipeline.

### The Plan

**Step 1: Run Scanner (IN PROGRESS)**
- Test: 2022-2024 (user running now)
- Full: 2010-2019 (after test succeeds)
- Skip: 2020-2021 (COVID era)
- Output: CLEAN.json with COMPLETE data

**Step 2: Add Drawdown Velocity**
- Run enrichment to add velocity analysis only
- No window finding needed (already have dates/prices)
- Just calculate max single-day drops

**Step 3: Run Realistic Filter V4.0**
- Test tradeability (35% trailing stop)
- Test profitability (200%+ gain)
- Expected: 90-100 tradeable stocks

**Step 4: Begin Phase 3**
- Pre-catalyst data collection
- Pattern discovery
- Build screening criteria

---

## 🎯 SCANNER DETAILS

### File: explosive_stock_scanner.py

**Location:** `/explosive_stock_scanner.py` (root)

**How It Works:**
1. Gets stock universe for each year from Polygon
2. Fetches historical data (Polygon primary, Yahoo backup)
3. Scans every possible 180-day window for 500%+ gains
4. Captures best window with complete data
5. Outputs to explosive_stocks_catalog.json
6. filter_covid_era.py processes it → CLEAN.json

**Environment Variables:**
- `START_YEAR`: Starting year (e.g., 2010)
- `END_YEAR`: Ending year (e.g., 2019)
- `SCAN_MODE`: 'full' or 'test'

**Current Test Run:**
```bash
START_YEAR=2022
END_YEAR=2024
SCAN_MODE=full
```

**Next Full Run:**
```bash
START_YEAR=2010
END_YEAR=2019
SCAN_MODE=full
```

### Output Format

Scanner outputs to `explosive_stocks_catalog.json`:
```json
{
  "scan_info": { ... },
  "stocks": [
    {
      "ticker": "EXAMPLE",
      "year_discovered": 2022,
      "entry_date": "2022-01-15",
      "entry_price": 10.50,
      "peak_date": "2022-06-20",
      "peak_price": 63.00,
      "gain_percent": 500,
      "days_to_peak": 156,
      "data_source": "Polygon API"
    }
  ]
}
```

Then `filter_covid_era.py` removes 2020-2021 stocks and outputs to CLEAN.json (cumulative).

---

## 🔧 DRAWDOWN VELOCITY SYSTEM

After scanner completes, we need to add drawdown velocity analysis:

### Purpose
Ensure we can actually EXIT positions (35% trailing stop must fill).

### What It Tests
- Max single-day drop during explosive window
- Multi-day drawdown velocity
- Tradeability classification

### Classifications
- **IDEAL**: 0% max drop → Plenty of time to exit
- **TRADEABLE**: <25% max drop → 35% stop should fill
- **RISKY**: 25-35% max drop → Might gap through
- **UNTRADEABLE**: >35% max drop → Would gap past stop

### Script
`enrich_stock_data.py` - Modified to ONLY add drawdown analysis (not find windows)

---

## 📋 REALISTIC FILTER V4.0

### File: filter_sustainability.py

### Criteria
1. **TRADEABLE**: Max single-day drop <35%
2. **PROFITABLE**: Captured 200%+ gain
3. **REALISTIC**: Within 120 days OR sustained growth

### What Gets Filtered
- ❌ Stocks with >35% single-day drops (can't exit)
- ❌ Stocks with <200% gains (not profitable enough)

### Expected Results
- 90-100 stocks pass (45-50% of ~200)
- Filters only obvious untradeable situations
- Realistic criteria based on actual trading

---

## 🗂️ FILE STATUS

### Core Scripts
- `/explosive_stock_scanner.py` - ✅ READY (has all data fields)
- `/filter_covid_era.py` - ✅ READY (makes output cumulative)
- `/enrich_stock_data.py` - ✅ READY (adds drawdown velocity only)
- `/filter_sustainability.py` - ✅ READY (V4.0 realistic filter)

### Data Files
- `/Verified_Backtest_Data/explosive_stocks_CLEAN.json` - PENDING (being rebuilt)
- `/Verified_Backtest_Data/enrichment_log.json` - Will track drawdown additions
- `/Verified_Backtest_Data/explosive_stocks_UNTRADEABLE.json` - Filter output

### Workflows
- `/.github/workflows/explosive_stock_scan_workflow.yml` - Scanner workflow
- `/.github/workflows/enrich_stock_data_workflow.yml` - Enrichment workflow
- `/.github/workflows/sustainability_filter_workflow.yml` - Filter workflow

---

## 📊 EXPECTED TIMELINE & RESULTS

### Scanner Runs
**Test (2022-2024):**
- Time: ~30-45 minutes
- Stocks: ~80-100 expected
- Purpose: Verify data structure

**Full (2010-2019):**
- Time: 2-4 hours
- Stocks: ~120-150 expected
- Purpose: Complete pre-COVID dataset

**Total After Both:**
- ~200-250 stocks with COMPLETE data
- All have entry_date, entry_price, peak_date, peak_price
- Ready for enrichment/filtering

### After Enrichment
- Add drawdown velocity to all stocks (~15-20 min)
- No stocks fail (already have all price data)
- 100% enrichment success rate

### After Filtering
- 90-100 tradeable stocks (45-50%)
- 100-110 filtered out (gaps/low gains)
- Ready for Phase 3 analysis

---

## 🎯 KEY LEARNINGS

### What Went Wrong
1. ❌ CLEAN.json had incomplete data from the start
2. ❌ Tried to "fix" with enrichment (impossible without entry dates)
3. ❌ Multiple filter iterations failed due to missing data
4. ❌ Spent hours on complex solutions to wrong problem

### The Real Issue
**Data was captured correctly by scanner but stripped during processing.**

### The Fix
**Re-run scanner with complete output pipeline.**

### Why This Works
- Scanner finds actual explosive windows (not guessing)
- Captures complete data at source
- No enrichment guesswork needed
- Just add velocity analysis and filter

---

## 🚀 IMMEDIATE NEXT STEPS

### Right Now (User Testing)
1. ✅ User running 2022-2024 scanner
2. ⏳ Wait for completion (~30-45 min)
3. ⏳ Verify CLEAN.json has complete data fields
4. ⏳ Check entry_date, entry_price, peak_date, peak_price

### If Test Succeeds
1. Run 2010-2019 scanner (2-4 hours)
2. Both runs will cumulatively populate CLEAN.json
3. Run enrichment (add drawdown velocity only)
4. Run realistic filter V4.0
5. Get 90-100 tradeable stocks
6. Begin Phase 3 pre-catalyst analysis

### If Test Fails
1. Debug scanner output format
2. Check filter_covid_era.py processing
3. Ensure cumulative append works correctly
4. Fix and re-run

---

## 📝 CRITICAL REMINDERS

1. **SCANNER HAS THE DATA** - Don't try to enrich/guess windows
2. **2010-2024 RANGE** - Excluding COVID 2020-2021
3. **CUMULATIVE OUTPUT** - Each scan appends to CLEAN.json
4. **35% TRAILING STOP** - Trading rule for exit-ability
5. **DRAWDOWN VELOCITY** - Must be able to fill stop losses
6. **NO VELOCITY = IDEAL** - Stable moves are best
7. **REALISTIC THRESHOLDS** - 200%+ gain, <35% gap
8. **FILE VERIFICATION** - Always check data structure after scans
9. **PAIRED UPDATES** - Update catch-up + system_state.json together

---

## 🔗 IMPORTANT LINKS

**Repository:** https://github.com/cbenson85/GEM_Trading_System

**API:**
- Polygon Developer tier (unlimited requests)
- Key: pvv6DNmKAoxojCc0B5HOaji6I_k1egv0

**Scanner Workflow:**
https://github.com/cbenson85/GEM_Trading_System/actions

---

## ⚠️ WHAT TO TELL NEW AI

"The enrichment approach failed because CLEAN.json lacked entry dates. We're re-running the scanner (which captures everything) for 2010-2024. User is testing 2022-2024 now. If successful, run 2010-2019 next. Both outputs are cumulative to CLEAN.json. After scans complete: add drawdown velocity → run filter V4.0 → get tradeable stocks → begin Phase 3."

---

**END OF CATCH-UP PROMPT**
Generated: 2025-11-02 21:00:00
System: v5.1.0-SCANNER-APPROACH
Next: Wait for 2022-2024 test results, then run 2010-2019
Key Insight: Scanner has the data - don't try to find windows retroactively
