# GEM Trading System - AI Catch-Up Prompt
**Last Updated**: 2025-11-02 20:30:00
**System Version**: 5.0.4-REALISTIC-FILTER
**Current Phase**: Phase 3: Stock Discovery & Pre-Catalyst Analysis - ENRICHMENT & FILTERING

---

## 🚨 CRITICAL CONTEXT FOR AI

### What You're Walking Into
After extensive filter evolution, we've landed on the correct approach: **drawdown velocity testing** combined with **realistic gain thresholds**. The key insight: we need to ensure we can actually EXIT positions (35% trailing stop must fill).

### Current Status
- 109/200 stocks enriched (54.5%)
- 91 stocks failed enrichment (Polygon can't find exact target gain)
- Updated enrichment to accept ANY 500%+ window (not exact match)
- Created realistic filter V4.0 with 35% trailing stop logic
- Ready to re-run enrichment and filter

### Immediate Priority
1. Re-run enrichment with relaxed search (should get 70-80% success)
2. Run realistic filter V4.0 (should pass 90-100 stocks)
3. Proceed with Phase 3 analysis on filtered stocks

---

## 🎯 KEY LEARNINGS FROM FILTER EVOLUTION

### What Didn't Work
1. ❌ **V1.0**: 90% retention 30 days - all failed (wrong criteria)
2. ❌ **V2.0**: 80% retention 21 days from peak - only 17/200 (peak timing issue)
3. ❌ **V3.0**: 120-day window, speed-adjusted - all failed (no enriched data)

### What We Discovered
1. ✅ **Testing from peak doesn't work** - peak could be years later, captures market corrections
2. ✅ **Need drawdown velocity testing** - ensure we can exit (35% trailing stop must fill)
3. ✅ **No velocity = IDEAL** - plenty of time to exit
4. ✅ **Focus on tradeability** - can we actually exit the position?
5. ✅ **Realistic thresholds** - 200%+ gain, max 35% single-day drop

---

## 🔬 FINAL ARCHITECTURE (V4.0 REALISTIC FILTER)

### Drawdown Velocity Testing

**Purpose:** Ensure stop losses can fill (no massive gaps)

**Classifications:**
- **IDEAL**: No significant drops (0%) → "Plenty of time to exit at any point"
- **TRADEABLE**: Max drop <25% → "35% trailing stop should fill"
- **RISKY**: Max drop 25-35% → "Might gap through stop"
- **UNTRADEABLE**: Max drop >35% → "Would gap past 35% stop loss"

### Filter Criteria

**Stock Must Meet:**
1. **TRADEABLE**: Max single-day drop <35% during explosive window
2. **PROFITABLE**: Captured 200%+ gain
3. **REALISTIC**: Within 120 days OR sustained growth beyond

**What Gets Filtered:**
- ❌ Stocks with >35% single-day drops (can't exit)
- ❌ Stocks with <200% gains (not profitable enough)
- ✅ Everything else passes (including un-enriched for now)

---

## 📊 ENRICHMENT IMPROVEMENTS

### Original Issue
Searched for exact target gain (e.g., if stock gained 900%, but we're looking for 500%, it wouldn't find it)

### Fixed
Now accepts **ANY 180-day window with 500%+ gain**

**Expected Improvement:**
- Before: 109/200 (54.5%)
- After: 140-160/200 (70-80%)

---

## 🗂️ CURRENT FILE STATUS

### Active Scripts
- `/enrich_stock_data.py` - ✅ UPDATED (accepts any 500%+ window, adds drawdown analysis)
- `/filter_sustainability.py` - ✅ UPDATED (V4.0 realistic filter with 35% threshold)

### Data Files
- `/Verified_Backtest_Data/explosive_stocks_CLEAN.json` - 200 stocks (109 enriched)
- `/Verified_Backtest_Data/enrichment_log.json` - Enrichment tracking
- `/Verified_Backtest_Data/explosive_stocks_UNTRADEABLE.json` - To be created by filter

### Workflows
- `/.github/workflows/enrich_stock_data_workflow.yml` - Data enrichment
- `/.github/workflows/sustainability_filter_workflow.yml` - Realistic filtering

---

## 📝 WHAT NEEDS TO HAPPEN NEXT

### Immediate Steps (IN ORDER)

**Step 1: Re-run Enrichment**
- Upload updated `enrich_stock_data.py` (accepts any 500%+ window)
- Run enrichment workflow
- Expected: 140-160 stocks enriched (70-80%)
- Adds drawdown velocity data to all

**Step 2: Run Realistic Filter V4.0**
- Run sustainability filter workflow (uses V4.0 code)
- Expected: 90-100 stocks pass (90% of enriched)
- Filters only stocks with >35% single-day drops

**Step 3: Analyze Results**
- Review filter summary
- Verify stocks have exit-ability
- Confirm tradeable dataset ready

**Step 4: Begin Phase 3**
- Pre-catalyst data collection on filtered stocks
- Pattern discovery
- Correlation analysis
- Build screening criteria

---

## 🎯 KEY DECISIONS

### Trading Rules Established
1. ✅ **35% trailing stop loss** - Exit if stock drops 35% from peak
2. ✅ **Must be able to exit** - No >35% single-day gaps
3. ✅ **200%+ gain minimum** - Profitable threshold
4. ✅ **120-day trading window** - Realistic holding period
5. ✅ **No velocity = ideal** - Stable moves best

### Architecture Decisions
1. ✅ **CLEAN.json is master list** - Filter modifies it
2. ✅ **Enrichment separate from filtering** - Two-stage process
3. ✅ **Drawdown velocity critical** - Tests exit-ability
4. ✅ **Realistic criteria** - Based on actual trading constraints
5. ✅ **Accept imperfect data** - 70-80% enrichment acceptable

---

## 📊 EXPECTED FINAL RESULTS

**After Both Steps:**
```
Total: 200 stocks
Enriched: 140-160 (70-80%)
Tradeable: 90-100 (45-50% of total)
Untradeable: 40-50 (gaps/insufficient gains)
Un-enriched: 40-60 (old/delisted/warrants)
```

**This gives us 90-100 quality stocks for Phase 3!**

---

## 🔗 IMPORTANT LINKS

**Repository:** https://github.com/cbenson85/GEM_Trading_System

**API:**
- Polygon Developer tier (unlimited requests)
- Key: pvv6DNmKAoxojCc0B5HOaji6I_k1egv0

---

## ⚠️ CRITICAL REMINDERS

1. **TWO-STAGE PROCESS** - Enrich first, filter second
2. **35% THRESHOLD** - Based on trailing stop loss
3. **NO VELOCITY = GOOD** - Stable moves are ideal
4. **REALISTIC CRITERIA** - Can we actually exit?
5. **ACCEPT 70-80%** - Won't enrich every stock (some have no data)
6. **CLEAN.json MODIFIED** - Filter updates it with sustainable only
7. **FILE VERIFICATION** - Follow protocol for new files
8. **PAIRED FILES** - Update catch-up + system_state.json together

---

## 🚀 HOW TO CONTINUE

1. Read this prompt thoroughly
2. Re-run enrichment with updated script
3. Wait for enrichment completion (~15-20 min)
4. Run realistic filter V4.0
5. Analyze results
6. Proceed with Phase 3 if results good
7. Update this prompt after filtering complete

---

**END OF CATCH-UP PROMPT**
Generated: 2025-11-02 20:30:00
System: v5.0.4-REALISTIC-FILTER
Next: Re-run enrichment, then filter, then Phase 3
Key Insight: Drawdown velocity = exit-ability = tradeable
