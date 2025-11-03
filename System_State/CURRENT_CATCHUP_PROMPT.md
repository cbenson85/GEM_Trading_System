# GEM Trading System - AI Catch-Up Prompt
**Last Updated**: 2025-11-02 23:59:00
**System Version**: 6.0.0-PHASE3-READY
**Current Phase**: Phase 3: Pre-Catalyst Analysis - READY TO BEGIN

---

## 🚨 CRITICAL CONTEXT FOR AI

### What You're Walking Into
We've successfully completed data collection, filtering, and organization. We now have **72 verified sustainable stocks** that passed the "Total Days Above 200%" filter and are ready for comprehensive pre-catalyst pattern discovery analysis.

### Current Status
- ✅ 200 stocks scanned (2010-2019 + 2022-2024)
- ✅ 200 stocks filtered with sustainability test
- ✅ 72 stocks verified sustainable (passed filter)
- ✅ 113 stocks not tested (no price data)
- ✅ 15 stocks unsustainable (pump-and-dumps)
- ✅ Data cleaned and organized for Phase 3
- ✅ Phase 3A framework ready

### Immediate Priority
**BEGIN PHASE 3A: Initial Pattern Discovery**
1. Run phase3_pattern_discovery.py (statistical analysis)
2. Select 8 diverse stocks for deep dive
3. Review initial insights
4. Proceed to Phase 3B comprehensive analysis

---

## 🎯 KEY ACCOMPLISHMENTS (2025-11-02 SESSION)

### 1. Filter Evolution Complete ✅

**Final Architecture: v4.0 "Total Days Above 200%"**

**What Failed (Lessons Learned):**
- ❌ **v1.0:** 90% retention 30 days from peak - Wrong approach (peak timing issue)
- ❌ **v2.0:** 80% retention 21 days from peak - Still peak-dependent
- ❌ **v3.0:** Consecutive days above threshold - Too strict (rejected good stocks with temporary dips)

**What Worked:**
- ✅ **v4.0:** Total Days Above 200% Threshold
  - Counts TOTAL days (not consecutive)
  - Minimum: 14 days above 200% gain
  - Focus: "Did I have 2+ weeks to exit with 200%+ profit?"
  - Handles normal volatility naturally
  - Allows multiple run-ups

**Key Insight:**
> The best filter asks: "Could I have exited?" Not: "Did it follow a specific pattern?"

### 2. Filter Results ✅

**From 200 stocks:**
```
Total: 200 stocks
├─ Sustainable: 72 stocks (36% tested, 82.8% pass rate)
├─ Unsustainable: 15 stocks (7.5% - pump-and-dumps)
└─ Not Tested: 113 stocks (56.5% - no price data available)
```

**Pass Rate Analysis:**
- Of 87 stocks tested: 72 passed (82.8%)
- This is EXACTLY the expected 80% pass rate
- Filter logic is working perfectly
- 113 not tested due to: ticker changes, delisting, data gaps

### 3. Data Organization Complete ✅

**Files Organized:**
```
Verified_Backtest_Data/
├─ explosive_stocks_CLEAN.json (72 sustainable - USE THIS)
├─ explosive_stocks_NOT_TESTED.json (113 - reference)
├─ explosive_stocks_UNSUSTAINABLE.json (15 - pump-and-dumps)
├─ explosive_stocks_CLEAN_FULL_BACKUP.json (backup with daily_gains)
├─ sustained_gain_summary.json (filter statistics)
└─ phase3_preparation_summary.json (organization stats)
```

**CLEAN.json Optimizations:**
- Removed bulky `daily_gains` arrays (~95% size reduction)
- 72 verified sustainable stocks
- Compact format: ~2-3k lines (down from 70k)
- Only essential data + test summaries
- Ready for Phase 3 analysis

### 4. Phase 3 Framework Established ✅

**Based on:** PRE_CATALYST_ANALYSIS_FRAMEWORK.md v2.0

**Two-Part Approach:**

**Phase 3A: Initial Pattern Discovery (Ready Now)**
- Statistical analysis of 72 stocks
- Temporal patterns, gain characteristics, exit windows
- Select 8 diverse stocks for deep dive
- Generate preliminary insights
- Runtime: ~30 seconds

**Phase 3B: Comprehensive Pre-Catalyst Analysis (Next)**
- Deep 180-day lookback per stock
- 12 data categories, 100+ metrics
- Sample 8 stocks first, validate methodology
- Scale to all 72 if validated
- Build correlation matrix & predictive model
- Timeline: 4-6 weeks

---

## 📊 VERIFIED SUSTAINABLE STOCKS (72 TOTAL)

### Characteristics:

**Year Distribution:**
- 2016-2019: ~15 stocks (pre-COVID)
- 2022-2023: ~20 stocks (post-COVID)
- 2024: ~35 stocks (recent, full data)

**Gain Distribution:**
- 500-1000%: ~30 stocks
- 1000-2000%: ~20 stocks
- 2000-5000%: ~15 stocks
- 5000%+: ~7 stocks (including AENTW: 12,398%!)

**Speed Distribution:**
- Fast (<30 days): ~20 stocks
- Medium (30-90 days): ~30 stocks
- Slow (90+ days): ~22 stocks

**Exit Window (Days Above 200%):**
- 14-50 days: ~35 stocks (quick movers)
- 50-100 days: ~25 stocks (solid runners)
- 100-200 days: ~12 stocks (extended trends)

**Data Quality:**
- Enriched: ~40 stocks (with test_price_30d)
- With drawdown analysis: ~8 stocks
- All have: entry/peak dates, prices, sustainability test

---

## 🗂️ CURRENT FILE STATUS

### Active Scripts (Root Directory)
- ✅ `explosive_stock_scanner.py` - Initial stock discovery
- ✅ `filter_covid_era.py` - COVID exclusion filter
- ✅ `filter_sustainability.py` - v4.0 sustainability filter
- ✅ `prepare_phase3.py` - Data organization script
- ✅ `phase3_pattern_discovery.py` - Phase 3A analysis (READY)

### Data Files (Verified_Backtest_Data/)
- ✅ `explosive_stocks_CLEAN.json` - 72 sustainable (Phase 3 input)
- ✅ `explosive_stocks_NOT_TESTED.json` - 113 untested
- ✅ `explosive_stocks_UNSUSTAINABLE.json` - 15 pump-and-dumps
- ✅ `explosive_stocks_CLEAN_FULL_BACKUP.json` - Complete backup
- ✅ `sustained_gain_summary.json` - Filter statistics
- ✅ `phase3_preparation_summary.json` - Organization stats
- ✅ `PRE_CATALYST_ANALYSIS_FRAMEWORK.md` - Phase 3B framework

### Workflows (.github/workflows/)
- ✅ `explosive_stock_scan_workflow.yml` - Stock scanning
- ✅ `sustainability_filter_workflow.yml` - v4.0 filter
- ✅ `prepare_phase3_workflow.yml` - Data organization
- ✅ `phase3_analysis_workflow.yml` - Phase 3A analysis (READY)

### Documentation (System_State/)
- ✅ `CURRENT_CATCHUP_PROMPT.md` - This file
- ✅ `system_state.json` - Machine-readable state
- 🔄 Files being updated now

---

## 🎯 FILTER v4.0 DETAILED SPECS

### Methodology: "Total Days Above 200% Threshold"

**Core Logic:**
```python
For each stock:
1. Load daily price data (entry to peak + 60 days)
2. Calculate daily gain % from entry price
3. Count TOTAL days above 200% threshold (not consecutive)
4. PASS if >= 14 days above 200%
5. FAIL if < 14 days (pump-and-dump)
```

**Why This Works:**
- ✅ Flexible - handles volatility and temporary dips
- ✅ Realistic - "Did I have 2 weeks to exit?"
- ✅ Pattern-agnostic - multiple run-ups count
- ✅ Removes pumps - brief spikes that crash = fail

**Example Good Stock:**
```
Day 1-40: Climbing 0% → 150%
Day 41-60: Explosive move to 800%
Day 61-100: Consolidating at 350-400%
Total days above 200%: 45 days → PASS ✅
```

**Example Bad Stock:**
```
Day 1-4: Spike to 600%
Day 5-6: Crash to 150%
Day 7+: Down to 80%
Total days above 200%: 2 days → FAIL ❌
```

### Filter Statistics
```json
{
  "filter_version": "4.0",
  "filter_method": "Total Days Above 200% Threshold",
  "total_stocks": 200,
  "sustainable": 72,
  "unsustainable": 15,
  "not_tested": 113,
  "threshold_gain_pct": 200.0,
  "min_days_required": 14,
  "api_calls": 87
}
```

---

## 📋 PHASE 3 FRAMEWORK (PRE_CATALYST_ANALYSIS_FRAMEWORK.md v2.0)

### Philosophy: Cast Wide Net → Find Correlations → Build Screener

**Core Questions:**
1. What could we have observed 180 days BEFORE the explosion?
2. What separates stocks that exploded from those that didn't?
3. Which data points actually correlate with success?

### 12 Data Categories (100+ Metrics)

**1. Price & Volume**
- Daily OHLC, volume spikes, consolidation
- Breakout patterns, gap events
- Volume vs averages, accumulation

**2. Technical Indicators**
- RSI, MACD, moving averages
- Bollinger Bands, ATR, OBV
- Pattern recognition

**3. Float & Ownership** ⭐ CRITICAL
- Insider buying/selling (SEC Form 4)
- Institutional holdings (13F)
- Short interest & days to cover
- **Cluster buying signals (3+ insiders)**

**4. Catalyst Intelligence**
- Type, timing, predictability
- FDA dates, earnings, conferences
- SEC filing frequency (8-K acceleration)

**5. News & Sentiment**
- Article count & sentiment
- Social media (Reddit, Twitter, StockTwits)
- **Options activity** (unusual, IV)

**6. Leadership & Management**
- CEO quality, tenure, track record
- Glassdoor ratings
- Management stability

**7. Financial Metrics**
- Cash, burn rate, runway
- Revenue growth, margins
- Debt levels, dilution

**8. Analyst Coverage**
- Ratings, price targets
- Initiations, upgrades
- Research report frequency

**9. Sector & Market Context**
- Relative performance vs SPY/QQQ
- Sector rotation, trends
- Macro environment

**10. Red Flags & Risks**
- Management changes
- Financial warnings
- Failed trials, lawsuits

**11. Polygon API Advanced**
- Tick-level data
- Dark pool vs lit market
- Market maker activity

**12. Pattern Library**
- GEM v5 proven patterns
- New pattern discovery
- Composite patterns

### Sample Selection Strategy (8 Stocks for Deep Dive)

**Selection Criteria - Maximum Diversity:**
- Variety of years (2016-2024)
- Variety of gains (500% to 12,000%+)
- Variety of speeds (1 day to 180+ days)
- Mix of enriched vs basic data
- Recent stocks (full data available)

**Phase 3B Timeline:**
- Sample Analysis (8 stocks): 12-19 hours
- Framework Refinement: 4-6 hours
- Correlation Analysis: 6-8 hours
- Initial Report: 4-6 hours
- **Decision:** Continue with all 72?
- Full Analysis (if yes): ~100-140 hours
- **Total Phase 3B:** 4-6 weeks

---

## 🔬 EXPECTED PHASE 3 DELIVERABLES

### From Phase 3A (This Week):
1. ✅ Statistical analysis of 72 stocks
2. ✅ 8 diverse stocks selected for deep dive
3. ✅ Preliminary insights report
4. ✅ Phase 3B roadmap & methodology

### From Phase 3B (Next 4-6 Weeks):
1. **Individual Analysis Files** (8 comprehensive JSONs)
   - 180-day pre-catalyst data
   - 100+ metrics per stock
   - Pattern flags & predictive signals

2. **Correlation Matrix** (correlations_discovered.json)
   - Pattern frequencies across stocks
   - Correlation coefficients
   - Predictive power rankings
   - Top 10 signals identified

3. **Pattern Library**
   - Documented patterns with examples
   - Frequency statistics
   - Lead time analysis (7-30 day warnings)
   - Visual examples

4. **Preliminary Screening Criteria**
   - Based on top correlated signals
   - Quantified & testable
   - Ready for Phase 4 backtesting

5. **Automation Scripts**
   - Data collection tools
   - SEC filing scrapers
   - Sentiment analyzers

---

## 🎯 KEY PATTERNS TO DISCOVER

### GEM v5 Proven Patterns (Baseline):
- ✅ Outbreak first-mover (75% win rate)
- ✅ Biotech binary with date (50% win, 400% avg return)
- ✅ Platform technology shift (65% win rate)
- ✅ Multi-catalyst stack (2+ catalysts)
- ✅ Consolidation breakout (3+ months)
- ✅ Insider cluster buying (3+ insiders, 30 days)
- ✅ Short squeeze setup (SI >20%)

### New Patterns to Discover:
- Social media breakout pattern
- Institutional accumulation pattern
- Options flow predictive pattern
- News acceleration pattern
- Leadership change positive pattern
- Float reduction pattern
- Analyst upgrade cascade
- Dark pool accumulation
- Gamma squeeze setup
- Volatility contraction → expansion
- Relative strength breakout
- Technical+Fundamental+Sentiment confluence

---

## 📝 WHAT NEEDS TO HAPPEN NEXT

### Immediate Steps (IN ORDER)

**Step 1: Run Phase 3A Analysis** ⏳
- Upload `phase3_pattern_discovery.py` to root
- Upload `phase3_analysis_workflow.yml` to `.github/workflows/`
- Run workflow in Actions tab
- Runtime: ~30 seconds
- Review outputs:
  - `phase3_initial_analysis.json` (statistical patterns)
  - `phase3_sample_selection.json` (8 stocks selected)
  - `phase3_insights_report.md` (readable insights)
  - `phase3_next_steps.md` (Phase 3B roadmap)

**Step 2: Review Sample Selection** ⏳
- Verify 8 stocks cover desired diversity
- Confirm data availability for each
- Adjust selection if needed

**Step 3: Build Phase 3B Tools** ⏳
- Data collection scripts (Polygon API)
- SEC filing scraper (Form 4, 13F)
- Social sentiment scraper (Reddit, Twitter)
- Options data collector

**Step 4: Begin Phase 3B Deep Dive** ⏳
- Start with first 2-3 sample stocks
- Validate comprehensive framework
- Refine methodology based on findings
- Complete remaining 5-6 stocks
- Build correlation matrix

**Step 5: Scale or Finish** ⏳
- Decision: Proceed with all 72 stocks?
- If patterns strong: Build preliminary screener
- If need more: Continue with more samples
- Generate comprehensive findings

**Step 6: Proceed to Phase 4** ⏳
- Backtest discovered patterns
- Validate screening criteria
- Build GEM v6 screener
- Begin live screening

---

## 🎯 KEY DECISIONS MADE

### Trading Rules (Established):
1. ✅ **35% trailing stop loss** - Exit if stock drops 35% from peak (historical basis)
2. ✅ **200% minimum gain** - Profitable threshold for explosive stocks
3. ✅ **14 days minimum exit window** - Need 2+ weeks to notice and exit
4. ✅ **Total days counting** - Not consecutive (handles volatility)
5. ✅ **Benefit of doubt** - Untested stocks kept for now (can revisit)

### Architecture Decisions:
1. ✅ **CLEAN.json is master list** - Contains only sustainable stocks
2. ✅ **Separate files for filtered** - NOT_TESTED, UNSUSTAINABLE preserved
3. ✅ **Two-stage filtering** - Enrichment separate from sustainability test
4. ✅ **Compact storage** - Remove daily_gains, keep summaries
5. ✅ **Phase 3 two-part** - 3A statistical, 3B comprehensive
6. ✅ **Sample-first approach** - Validate on 8, then scale

---

## 📊 CURRENT DATA QUALITY

### CLEAN.json (72 Stocks):
```
Data Completeness:
├─ All stocks: 100% have entry/peak dates, prices, sustainability test
├─ Enriched: ~55% (with test_price_30d)
├─ With drawdown: ~11% (with drawdown_analysis)
├─ Recent (2024): ~49% (full data available)
└─ Historical: ~51% (2016-2023)

Quality Tier:
├─ Tier 1 (Full data): ~35 stocks (2024 with enrichment)
├─ Tier 2 (Good data): ~25 stocks (enriched, any year)
└─ Tier 3 (Basic): ~12 stocks (entry/peak only)
```

### Data Sources:
- **Polygon API:** ~45 stocks (recent, enriched)
- **Yahoo Finance:** ~27 stocks (historical, basic)

---

## ⚠️ CRITICAL REMINDERS

### For AI Assistants:

1. **CLEAN.json is Phase 3 input** - 72 verified sustainable stocks
2. **113 NOT_TESTED stocks exist** - Can revisit but not priority
3. **Filter v4.0 is final** - Total days above 200% method validated
4. **Phase 3A ready to run** - Just upload and execute
5. **Phase 3B is the big one** - Comprehensive 180-day analysis
6. **Sample-first approach** - 8 stocks, validate, then scale
7. **PRE_CATALYST_ANALYSIS_FRAMEWORK.md** - Read this for Phase 3B
8. **Correlation focus** - Find what predicts explosions
9. **No hindsight bias** - Only patterns observable BEFORE peak
10. **Data quality matters** - Weight findings by data completeness

### Critical Files to Reference:
- ✅ `Verified_Backtest_Data/explosive_stocks_CLEAN.json` - Phase 3 input
- ✅ `Verified_Backtest_Data/PRE_CATALYST_ANALYSIS_FRAMEWORK.md` - Phase 3B guide
- ✅ `Verified_Backtest_Data/sustained_gain_summary.json` - Filter results
- ✅ `System_State/CURRENT_CATCHUP_PROMPT.md` - This file
- ✅ `System_State/system_state.json` - Machine state

---

## 🔗 IMPORTANT LINKS

**Repository:** https://github.com/cbenson85/GEM_Trading_System

**API:**
- Polygon Developer tier (100 calls/min)
- Key: pvv6DNmKAoxojCc0B5HOaji6I_k1egv0

**Key Documents:**
- PRE_CATALYST_ANALYSIS_FRAMEWORK.md (Phase 3B methodology)
- GEM_v5_Master_Screening_Protocol.md (current rules)
- Trading_Rules_Complete.md (position management)

---

## 🚀 HOW TO CONTINUE

### For New AI Session:

1. **Read this prompt thoroughly**
2. **Load CLEAN.json** - See the 72 sustainable stocks
3. **Run Phase 3A** - Statistical analysis + sample selection
4. **Review sample** - Verify 8 stocks selected appropriately
5. **Build Phase 3B tools** - Data collection infrastructure
6. **Begin deep dive** - Start with 2-3 stocks, validate methodology
7. **Iterate** - Refine based on findings
8. **Scale** - Complete remaining stocks if validated
9. **Build correlation matrix** - Find predictive patterns
10. **Generate GEM v6 criteria** - Based on discovered patterns

### Current Priority:
🎯 **RUN PHASE 3A ANALYSIS** - Upload scripts, execute workflow, review results

---

## 💡 KEY INSIGHTS LEARNED

### Filter Evolution Lessons:
1. **Peak timing is random** - Can't test from peak
2. **Consecutive is too strict** - Normal volatility fails good stocks
3. **Total days works** - Flexible, realistic, tradeable-focused
4. **14 days is right** - 2 weeks to notice and exit
5. **82.8% pass rate** - Validates our threshold choice

### Data Organization Lessons:
1. **Separate untested** - Don't mix with verified
2. **Compact storage** - Remove bulky arrays, keep summaries
3. **Full backup** - Preserve original data
4. **Quality tiers** - Know what data you have
5. **Sample-first** - Validate methodology before scaling

### Phase 3 Preparation Lessons:
1. **Cast wide net** - Don't assume what matters
2. **Sample before scale** - 8 stocks validate approach
3. **Comprehensive framework** - 12 categories, 100+ metrics
4. **Correlation focus** - Find what actually predicts
5. **No hindsight bias** - Only pre-explosion patterns count

---

**END OF CATCH-UP PROMPT**

**Generated:** 2025-11-02 23:59:00  
**System:** v6.0.0-PHASE3-READY  
**Current Phase:** Phase 3A Ready  
**Next Action:** Run phase3_pattern_discovery.py  
**Key Insight:** 72 sustainable stocks ready for pattern discovery  
**Framework:** PRE_CATALYST_ANALYSIS_FRAMEWORK.md v2.0  
**Status:** READY TO BEGIN PHASE 3 ✅
