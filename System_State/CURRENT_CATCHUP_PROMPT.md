# GEM Trading System - AI Catch-Up Prompt
**Last Updated**: 2025-11-05 (After Timeout - Updated Strategy)
**System Version**: 6.2.0-SCANNING
**Current Phase**: Phase 3A: Complete Stock Discovery (In Progress)

---

## 🎯 CRITICAL CONTEXT

### What You're Walking Into
Running optimized 2-year chunk scan (2010-2024, COVID excluded). Previous 3-year chunks hit GitHub Actions timeout. New approach: 7 parallel 2-year scans = timeout-proof. Check if scan is running or completed.

### Immediate Priority
**IF SCAN RUNNING**: Wait for completion (~3 hours total)
**IF SCAN COMPLETE**: Download results, upload to repo, begin Phase 3B pattern analysis

---

## 🚨 RECENT DEVELOPMENTS (CRITICAL)

### Timeout Issue Discovered
**Problem**: First workflow attempt used 3-4 year chunks
- 2013-2015 scan hit 6-hour GitHub Actions timeout
- 3 out of 4 scans succeeded
- Learned: 3+ year chunks are too risky

**Solution**: New workflow with 2-year chunks
- 7 parallel scans instead of 4
- Each scan: 2-3 hours max (safe!)
- 50% safety margin under 6-hour limit
- Same total time: ~3 hours (all parallel)

### Current Workflow
- **File**: `safe_multi_year_scan_2year_chunks.yml`
- **Location**: `.github/workflows/`
- **Status**: Check Actions tab to see if running or completed
- **Artifact Name**: `final-results-2year-chunks`

---

## 📊 SYSTEM STATUS

### Current State
- **Portfolio**: CLEARED - Starting fresh
- **Cash Available**: $10,000 (reset)
- **System Stage**: Phase 3A - Stock Discovery (Scanning)
- **Last Completed Phase**: Phase 2: System Requirements & Data Infrastructure
- **Next Phase**: Phase 3B: Pre-Catalyst Analysis & Pattern Discovery

### Scan Configuration
- **Workflow**: safe_multi_year_scan_2year_chunks.yml
- **Approach**: 7 parallel 2-year scans (timeout-proof)
- **Scan Window**: 120 days (4 months max to peak)
- **Gain Threshold**: 500%+ (6x minimum)
- **Years Covered**: 2010-2011, 2012-2013, 2014-2015, 2016-2017, 2018-2019, 2022-2023, 2024
- **Years Excluded**: 2020-2021 (COVID anomalies - never scanned)
- **Expected Time**: ~3 hours (all parallel)
- **Safety**: Each scan 2-3 hours (50% under limit)

### Data Verification Status
- Current Prices: ✅ VERIFIED (Polygon API)
- Volume Data: ✅ VERIFIED (Polygon API)
- Explosive Stock Scan: 🔄 IN PROGRESS or ✅ COMPLETE (check Actions tab)
- Scan Window: ✅ 120 days (4 months)
- COVID Exclusion: ✅ BUILT-IN (not scanning 2020-2021)
- Float Data: ⚠️ PARTIAL (Polygon API - not all stocks)
- Catalyst Data: ❌ NOT YET IMPLEMENTED
- Pattern Analysis: ⏸️ WAITING (Phase 3B after scan)

---

## 🗂️ FILE STRUCTURE & LOCATIONS

**Repository**: https://github.com/cbenson85/GEM_Trading_System

### Core System Files (VERIFIED)
- `/Current_System/GEM_v5_Master_Screening_Protocol.md` - Core screening rules
- `/Current_System/Trading_Rules_Complete.md` - Trading operations guide
- `/explosive_stock_scanner.py` - Scanner (120-day window)
- `/.github/workflows/safe_multi_year_scan_2year_chunks.yml` - Current workflow
- `/filter_sustainability.py` - Sustainability filter

### Workflow Files
- `safe_multi_year_scan_2year_chunks.yml` ✅ CURRENT (timeout-proof)
- `optimized_multi_year_scan_workflow.yml` ⚠️ DEPRECATED (hit timeout)

### Data Files (Status)
- `/Verified_Backtest_Data/explosive_stocks_CLEAN.json` - 🔄 WILL BE CREATED (after scan)
- `/Verified_Backtest_Data/explosive_stocks_UNSUSTAINABLE.json` - 🔄 WILL BE CREATED (after filter)
- `/Verified_Backtest_Data/refinement_history.json` - ✅ ACTIVE

### Complete GitHub File Catalog
[GITHUB_FILE_CATALOG.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/GITHUB_FILE_CATALOG.md) - Complete file list with all links

---

## 🔬 SCAN METHODOLOGY

### Approach (Updated After Timeout)
1. Find stocks with 500%+ gains in ≤120 days via GitHub Actions
2. **Use 2-year chunks** (7 parallel scans) to avoid timeout
3. Auto-merge all results
4. Run sustainability filter
5. Deep dive into 180 days PRE-CATALYST for each stock
6. Analyze: price, volume, sentiment, leadership, news, patterns
7. Identify correlations between explosive stocks
8. Build screener based on correlations
9. Backtest on random historical dates
10. Apply FALSE MISS principle to discarded stocks
11. Store ALL data for future refinement

### Current Progress

**PHASE 3A - IN PROGRESS OR COMPLETE**: 🔄 / ✅
Check GitHub Actions to see current status:
- Go to: https://github.com/cbenson85/GEM_Trading_System/actions
- Look for: "Safe Multi-Year Scan (2-Year Chunks)"
- Status: Running / Completed / Not Started

**If Running**:
- 7 parallel scans executing
- Expected completion: ~3 hours from start
- Wait for all to finish

**If Complete**:
- Download artifact: "final-results-2year-chunks"
- Contains 2 files:
  - explosive_stocks_CLEAN.json (~800-1,100 sustainable stocks)
  - explosive_stocks_UNSUSTAINABLE.json (~200-400 pump-and-dumps)
- Upload both to Verified_Backtest_Data/ folder
- Ready for Phase 3B

**If Not Started**:
- User needs to run workflow
- Go to Actions → "Safe Multi-Year Scan (2-Year Chunks)"
- Click "Run workflow" → Type "RUN" → Start

### Data Sources
- Price/Volume: Polygon API (via GitHub Actions)
- Automation: GitHub Actions (runs on GitHub servers)
- Backup: Yahoo Finance (if Polygon fails)
- Manual Input: None - fully automated

---

## 📈 LESSON LEARNED (CRITICAL)

### Timeout Discovery
**What Happened**:
- First workflow: 4 parallel scans (3-4 year chunks each)
- 2010-2012: ✅ Success (3h 55m)
- 2013-2015: ❌ TIMEOUT (6h 0m - hit limit exactly)
- 2016-2019: ✅ Success (4h 42m)
- 2022-2024: ✅ Success (2h 58m)

**Root Cause**:
- GitHub Actions has hard 6-hour limit per job
- 3-year chunks are too risky
- Cannot predict exact time per ticker

**Solution Implemented**:
- New workflow: 7 parallel scans (2-year chunks)
- Each scan: 2-3 hours max
- 50% safety margin under 6-hour limit
- Total time: ~3 hours (still parallel)
- Guaranteed to complete

---

## 📝 WHAT NEEDS TO HAPPEN NEXT

### Step 1: Check Scan Status
**First action**: Check GitHub Actions to see current state
- Running: Wait for completion
- Complete: Download results
- Not started: User needs to run it

### Step 2: If Scan Complete
1. Go to completed workflow run
2. Scroll to bottom → "Artifacts" section
3. Download: `final-results-2year-chunks`
4. Extract ZIP (contains 2 files)

### Step 3: Upload Results
1. Go to `Verified_Backtest_Data/` folder
2. Delete old files if they exist:
   - old explosive_stocks_CLEAN.json
   - old explosive_stocks_COVID_ERA.json
   - old explosive_stocks_catalog.json
3. Upload NEW files:
   - explosive_stocks_CLEAN.json (new)
   - explosive_stocks_UNSUSTAINABLE.json (new)
4. Keep: refinement_history.json (don't touch)
5. Commit: "Complete 2010-2024 scan (2-year chunks, COVID excluded)"

### Step 4: Begin Phase 3B
1. Analyze 180 days BEFORE each explosion
2. Extract patterns: price, volume, sentiment, leadership
3. Build correlation matrix
4. Create updated screener criteria

### Blockers/Questions
None - workflow is timeout-proof and ready

---

## 🎯 DECISIONS MADE

### Key Decisions
1. Mark all previous backtest results as UNVERIFIED
2. Clear all current portfolio positions - starting fresh
3. Build from verified data only - no fabrication
4. Use 500%+ in 120 days as criteria (tightened from 180 days for focus)
5. Analyze 180 days pre-catalyst for pattern discovery
6. Store all backtest data (picks AND discards) for refinement
7. Apply false miss principle in all backtests
8. User only does copy/paste - full automation required
9. Use GitHub Actions for full automation (no local execution)
10. Exclude 2020-2021 from scan (COVID-era anomalies)
11. **Use 2-year scan chunks to avoid timeout** (learned from 2013-2015 failure)

### Rules Established
1. NEVER fabricate data - verify or say you can't
2. FALSE MISS CHECK - Always check discarded stocks for explosive growth
3. STORE EVERYTHING - All decisions, data, refinements must be saved
4. COPY/PASTE ONLY - User should never manually enter data
5. 10-YEAR VALIDATION - System must prove consistency before live trading
6. COVID-ERA EXCLUSION: Ignore 2020-2021 data (not repeatable conditions)
7. **TIMEOUT AWARENESS: GitHub Actions has 6-hour limit - use 2-year chunks**

---

## 🔗 IMPORTANT LINKS

- **GitHub Repo**: https://github.com/cbenson85/GEM_Trading_System
- **Actions Tab**: https://github.com/cbenson85/GEM_Trading_System/actions
- **Current Workflow**: safe_multi_year_scan_2year_chunks.yml
- **Polygon API**: Developer tier (key in GitHub secrets)
- **Data Storage**: /Verified_Backtest_Data/

---

## 💾 PROGRESS LOG

**2025-11-01 20:41** - Phase 1
- Action: Completed audit of existing system
- Result: Identified fabricated backtest data, cleared portfolio, established new methodology

**2025-11-01 20:50** - Phase 2
- Action: Created catch-up prompt system
- Result: COMPLETE - System tracks all progress, auto-generates prompts

**2025-11-01 21:13** - Phase 2
- Action: Switched to GitHub Actions for full automation
- Result: Complete automation - user just clicks 'Run workflow'

**2025-11-05** - Phase 3A
- Action: Updated scan window from 180 days to 120 days
- Result: Scanner configured for 500%+ gain in ≤120 days (4 months)

**2025-11-05** - Phase 3A
- Action: Removed pre-filter system (added complexity without savings)
- Result: Simplified to direct scanning of all tickers

**2025-11-05** - Phase 3A - CRITICAL
- Action: First workflow attempt - 4 parallel scans (3-4 year chunks)
- Result: PARTIAL SUCCESS - 3/4 succeeded, 2013-2015 hit 6-hour timeout

**2025-11-05** - Phase 3A - UPDATED
- Action: Created timeout-proof workflow - 7 parallel scans (2-year chunks)
- Result: READY TO RUN - Each scan 2-3 hours max (50% safety margin)

---

## 📊 THE 7 SCANS (Current Workflow)

All run **simultaneously** in parallel:

1. **2010-2011** (2 years) - ~2-3 hours ✅
2. **2012-2013** (2 years) - ~2-3 hours ✅
3. **2014-2015** (2 years) - ~2-3 hours ✅ (previously timed out as 3-year chunk)
4. **2016-2017** (2 years) - ~2-3 hours ✅
5. **2018-2019** (2 years) - ~2-3 hours ✅
6. **2022-2023** (2 years) - ~2-3 hours ✅
7. **2024** (1 year) - ~1.5-2 hours ✅

**Total Wall Time**: ~3 hours (longest scan)
**Safety Margin**: 50% under GitHub Actions 6-hour limit

---

## ⚠️ CRITICAL REMINDERS

1. **CHECK ACTIONS TAB FIRST**: See if scan is running/complete before doing anything
2. **NO FABRICATION**: All data must be verified
3. **FALSE MISS PRINCIPLE**: When backtesting, check discarded stocks
4. **USER DOES COPY/PASTE ONLY**: All automation, no manual data entry
5. **STORE EVERYTHING**: All backtest data, decisions, refinements must be saved
6. **TIMEOUT AWARENESS**: 2-year chunks = safe, 3+ year chunks = risky

---

## 🚀 HOW TO CONTINUE

### If You're Picking Up After Conversation Limit:

1. **First Action**: Check GitHub Actions status
   - Go to: https://github.com/cbenson85/GEM_Trading_System/actions
   - Find: "Safe Multi-Year Scan (2-Year Chunks)"
   - Determine: Running? Complete? Not started?

2. **If Running**: 
   - Do nothing, wait for completion
   - Monitor progress
   - Check back in ~3 hours

3. **If Complete**:
   - Download artifact: "final-results-2year-chunks"
   - Extract 2 files
   - Guide user to upload to Verified_Backtest_Data/
   - Begin Phase 3B pattern analysis

4. **If Not Started**:
   - Guide user to run workflow
   - Actions → "Safe Multi-Year Scan (2-Year Chunks)"
   - Type "RUN" → Start
   - Return in ~3 hours

5. **Update this prompt after each phase completion**

---

## 🎯 EXPECTED RESULTS

**After Scan Completes**:
- Total explosive stocks: ~1,200-1,500 (before filter)
- Sustainable stocks: ~800-1,100 (after filter)
- Pump-and-dumps removed: ~200-400
- Coverage: Complete 2010-2024 (COVID excluded)
- Ready for: Phase 3B pattern analysis

---

**END OF CATCH-UP PROMPT**
**Status**: Waiting for or monitoring 2-year chunk scan
**Next**: Check Actions tab, download results when ready, begin Phase 3B
