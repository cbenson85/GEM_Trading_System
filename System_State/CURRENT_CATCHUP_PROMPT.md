# GEM Trading System - AI Catch-Up Prompt
**Last Updated**: 2025-11-02 20:00:00
**System Version**: 5.0.3-SUSTAINED-GAIN-FILTER-FINAL
**Current Phase**: Phase 3: Stock Discovery & Pre-Catalyst Analysis - READY TO RUN V3.0

---

## 🚨 CRITICAL CONTEXT FOR AI

### What You're Walking Into
After multiple filter iterations, we've finalized the Sustained Gain Window Filter V3.0. Key learnings:
- V2.0 passed only 17/200 (8.5%) - tested from peak, captured market corrections not stock quality
- V3.0 uses realistic 120-day trading window with 30-day selling window
- CLEAN.json is the master stock list - filter reads it, uses Polygon API for all data, then updates it with sustainable stocks only
- User has Polygon Developer tier (unlimited API requests)

### Immediate Priority
Run V3.0 filter with correct 120-day trading window to get realistic sustainable stock dataset.

---

## 🔬 SUSTAINED GAIN WINDOW FILTER V3.0 (FINAL)

### Architecture (CRITICAL - User Corrected This Multiple Times!)

**CLEAN.json Role:**
- Master stock list (200 stocks: ticker, year, gain%, days_to_peak)
- Filter READS it to know what stocks to test
- Filter uses Polygon API to fetch ALL data (doesn't rely on enriched fields)
- Filter UPDATES it to keep only sustainable stocks
- After filtering: CLEAN.json = sustainable master list

**NOT:**
- ❌ Don't create separate SUSTAINABLE.json
- ❌ Don't preserve CLEAN.json unchanged
- ✅ DO update CLEAN.json with only sustainable stocks

### Trading Window Specifications

**Realistic 120-Day Trading Horizon:**
```
Day 0:     Entry (catalyst starts)
Day 0-120: Our trading window
Day 120:   Latest we hold a position
Peak:      Use actual peak OR day 120 (whichever comes first)
Test:      30 days after peak (selling window)
Max:       150 days total (120 + 30)
```

**Why 120 Days?**
- We don't hold stocks forever
- Realistic position management
- Clear exit windows (30 days to sell after peak)
- Forces discipline

**Peak Determination:**
- If stock peaks before day 120: Use actual peak
- If stock peaks after day 120: Cap at day 120 price
- Test 30 days after the peak we're using

### Speed-Adjusted Thresholds

**Minimum gain that must be maintained:**
- **FAST** (<30 days to peak): **250%+** minimum
  - Fast spikes are risky, need to prove they hold
  - Filters out pump & dumps (they collapse quickly)
  
- **MEDIUM** (30-90 days to peak): **200%+** minimum
  - Moderate speed, moderate requirements
  
- **SLOW** (90-120 days to peak): **150%+** minimum
  - Slow builds are safer, lower threshold acceptable

**Key Insight:** Fast movers need higher thresholds to prove they're not pumps.

### Example Scenarios

**Sustainable Stock (PASSES):**
```
Entry: $10 (Day 0)
Peak: $72 (Day 60, 620% gain) - MEDIUM speed
Test: $65 (Day 90, 550% gain)
Required: 200% minimum
Actual: 550% minimum
Result: ✅ PASSES (has 30-day selling window)
```

**Pump & Dump (FAILS):**
```
Entry: $10 (Day 0)
Peak: $60 (Day 10, 500% gain) - FAST speed
Test: $15 (Day 40, 50% gain)
Required: 250% minimum
Actual: 50% minimum
Result: ❌ FAILS (collapsed, no selling window)
```

**Late Peaker (Capped at 120):**
```
Entry: $10 (Day 0)
Real peak: $80 (Day 150)
Forced peak: $60 (Day 120, 500% gain) - SLOW
Test: $55 (Day 150, 450% gain)
Required: 150% minimum
Actual: 450% minimum
Result: ✅ PASSES (held through our trading window)
```

**Too Recent (Skipped):**
```
Entry: $10 (Oct 2024)
Peak: $60 (Nov 2024)
Test date: Dec 25, 2024 (future)
Result: ⏸️ SKIPPED (need 30 days post-peak data)
```

---

## 📊 SYSTEM STATUS

### Current State
- **Portfolio**: CLEARED
- **Cash**: $10,000
- **Explosive Stocks**: 200 (2010-2024, excluding COVID)
- **Filter Status**: V3.0 final version ready
- **API**: Polygon Developer (unlimited)
- **Next**: Run V3.0 filter

### Filter Evolution
1. **V1.0** - 90% retention, 30 days → All failed (wrong criteria)
2. **V2.0** - 80% retention, 21 days from peak → 17/200 (8.5%) passed, but tested from peak (captured market corrections)
3. **V3.0** - 120-day window, 30-day selling window, speed-adjusted thresholds → READY TO RUN

---

## 📝 CRITICAL DECISIONS MADE

### Key Architecture Decisions
1. ✅ CLEAN.json is master list - filter reads, uses API, updates it
2. ✅ Filter uses Polygon API for ALL data (doesn't need enriched fields)
3. ✅ 120-day trading window (realistic holding period)
4. ✅ 30-day post-peak test (selling window)
5. ✅ Speed-adjusted thresholds (fast = stricter)
6. ✅ Cap peak at day 120 if stock peaks later
7. ✅ Skip stocks too recent to test (need 30 days post-peak)

### What We Learned
- Testing from peak captures market corrections, not stock quality
- Need realistic trading windows (120 days, not forever)
- Fast movers need stricter tests (250%+ to prove sustainability)
- Must have selling windows (30 days to exit)
- CLEAN.json gets updated by filter (it's not a separate output)

---

## 🎯 WHAT NEEDS TO HAPPEN NEXT

### Immediate (NOW)
1. **Upload updated filter files:**
   - filter_sustainability.py (V3.0 with 120-day window)
   - sustainability_filter_workflow.yml (updated descriptions)

2. **Run V3.0 filter:**
   - Go to GitHub Actions
   - Select "Sustainability Filter Workflow"
   - Click "Run workflow"
   - Wait 10-20 minutes

3. **Analyze results:**
   - Check sustained_gain_summary.json
   - Expected: 40-80 sustainable (20-40% of 200)
   - Review by speed category
   - Compare to V2.0 results (17 stocks)

### After Filter Completes
1. Analyze position management insights
2. Begin Phase 3 pre-catalyst data collection
3. Build data collection scripts for sustainable stocks
4. Pattern discovery and correlation analysis

---

## 🔗 KEY FILES & LOCATIONS

**Repository:** https://github.com/cbenson85/GEM_Trading_System

**Core Files:**
- `/filter_sustainability.py` - V3.0 (120-day window)
- `/.github/workflows/sustainability_filter_workflow.yml` - V3.0
- `/Verified_Backtest_Data/explosive_stocks_CLEAN.json` - Master list (200 stocks)
- `/Verified_Backtest_Data/explosive_stocks_UNSUSTAINABLE.json` - Filtered out
- `/Verified_Backtest_Data/sustained_gain_summary.json` - Statistics

**API:**
- Polygon Developer tier (unlimited requests)
- Key: pvv6DNmKAoxojCc0B5HOaji6I_k1egv0

---

## ⚠️ CRITICAL REMINDERS

1. **NO FABRICATION** - Verify data or say you can't
2. **CLEAN.json IS MODIFIED** - It's the master list, filter updates it
3. **USE POLYGON API** - Don't rely on enriched fields in JSON
4. **120-DAY WINDOW** - Realistic trading horizon
5. **30-DAY SELLING WINDOW** - Must be able to exit
6. **FAST = STRICT** - 250%+ to prove it's not a pump
7. **FILE VERIFICATION** - Follow protocol for new files
8. **PAIRED FILES** - Update catch-up + system_state.json together

---

## 📊 EXPECTED V3.0 RESULTS

**V2.0 Results:** 17/200 (8.5%)  
**V3.0 Expected:** 40-80/200 (20-40%)

**Why More Will Pass:**
- Market corrections don't disqualify good stocks
- 120-day window is realistic (not testing forever)
- Speed-adjusted thresholds are appropriate
- Still filters pump & dumps (they collapse within 30 days)

---

## 🚀 HOW TO CONTINUE

1. Read this prompt thoroughly
2. Understand the V3.0 architecture (CLEAN.json role)
3. Run the V3.0 filter workflow
4. Analyze results
5. Proceed with Phase 3 pre-catalyst analysis
6. Update this prompt after V3.0 results

---

**END OF CATCH-UP PROMPT**
Generated: 2025-11-02 20:00:00
System: v5.0.3-SUSTAINED-GAIN-FILTER-FINAL
Next: Run V3.0 filter with 120-day trading window
