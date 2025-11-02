# GEM Trading System - AI Catch-Up Prompt
**Last Updated**: 2025-11-01 23:55:47
**System Version**: 5.0.1-REBUILD
**Current Phase**: Phase 3: Stock Discovery & Catalog Building

---

## 🎯 CRITICAL CONTEXT

### What You're Walking Into
System being rebuilt from ground up. Previous model fabricated backtest data. Starting fresh with verified data only.

### Immediate Priority
Upload scan results to GitHub, begin Phase 3: Deep-dive pre-catalyst analysis on 170 clean stocks

---

## 📊 SYSTEM STATUS

### Current State
- **Portfolio**: CLEARED - Starting fresh
- **Cash Available**: $10,000 (reset)
- **System Stage**: Pre-Development - Planning & Infrastructure
- **Last Completed Phase**: Phase 2: System Requirements & Data Infrastructure - COMPLETE
- **Next Phase**: Phase 3: Stock Discovery (awaiting local scan results)

### Data Verification Status

- Current Prices: ✅ VERIFIED (Polygon API)
- Volume Data: ✅ VERIFIED (Polygon API)
- Float Data: ⚠️ PARTIAL (Polygon API - not all stocks)
- Backtest Results: ❌ UNVERIFIED (marked for removal)
- Catalyst Data: ❌ NOT YET IMPLEMENTED
- Historical Analysis: ❌ NOT YET STARTED
                

---

## 🗂️ FILE STRUCTURE & LOCATIONS

**Repository**: https://github.com/cbenson85/GEM_Trading_System

### Core System Files (VERIFIED)

- `/Current_System/GEM_v5_Master_Screening_Protocol.md` - Core screening rules
- `/Current_System/Trading_Rules_Complete.md` - Trading operations guide
- `/Polygon_Integration/daily_screener.py` - Working Polygon integration
- `/Daily_Operations/CURRENT_UPDATE.md` - Daily update template
                

### Data Files (Location & Status)

- `/Verified_Backtest_Data/` - ✅ CREATED
- `/Verified_Backtest_Data/explosive_stocks_catalog.json` - ✅ LIVE (updated by scans)
- `/Verified_Backtest_Data/explosive_stocks_CLEAN.json` - To be created after filtering
- `/Verified_Backtest_Data/explosive_stocks_COVID_ERA.json` - To be created after filtering
- `/Verified_Backtest_Data/refinement_history.json` - ✅ ACTIVE
- `/Verified_Backtest_Data/correlations_discovered.json` - ✅ TEMPLATE
- `/GITHUB_FILE_CATALOG.md` - ✅ Complete file reference with all links


### Unverified/Archived Content

- `/Backtest_Results/` - MARKED UNVERIFIED, kept as framework reference
- `/Strategy_Evolution/` - MARKED UNVERIFIED, contains unproven claims
- All Python backtest scripts - MARKED UNVERIFIED, frameworks only
                

### 📂 Complete GitHub File Catalog

**Key Files for AI to Read:**

**System State:**
- [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CURRENT_CATCHUP_PROMPT.md) - Latest state
- [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/system_state.json) - Current data

**Core Protocols:**
- [GEM_v5_Master_Screening_Protocol.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Master_Screening_Protocol.md) - 7-phase screening
- [Trading_Rules_Complete.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/Trading_Rules_Complete.md) - Operations
- [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/COVID_ERA_EXCLUSION_RULE.md) - Critical filter

**Live Data:**
- [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json) - Scan results
- [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/refinement_history.json) - Changes log

**Active Scripts:**
- [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/explosive_stock_scanner.py) - Scanner
- [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_covid_era.py) - Data filter
- [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/explosive_stock_scan_workflow.yml) - Automation

**Full Catalog:**
- [GITHUB_FILE_CATALOG.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/GITHUB_FILE_CATALOG.md) - Complete file list with all links

---

## 🔬 BACKTESTING METHODOLOGY

### Approach

1. Find stocks with 500%+ gains via AUTOMATED GitHub Actions scan
2. Deep dive into 180 days PRE-CATALYST for each stock
3. Analyze: price, volume, sentiment, leadership, news, patterns
4. Identify correlations between explosive stocks
5. Build screener based on correlations
6. Backtest on random historical dates
7. Apply FALSE MISS principle to discarded stocks
8. Track picks AND discards with full performance data
9. Refine until consistent 10-year performance
10. Store ALL data for future refinement
11. ALL VIA GITHUB ACTIONS - zero manual work except triggering


### Current Progress

PHASE 2 COMPLETE: ✅
- Full 10-year scan: 244 total explosive stocks found
- Clean dataset: 170 stocks (2014-2019, 2022-2024)
- COVID-era archived: 69 stocks (excluded from analysis)
- Data quality: Verified via Polygon API + Yahoo Finance
- Ready for Phase 3: Pre-catalyst analysis

NEXT: Analyze 180 days BEFORE each explosion to find patterns


### Data Sources

- Price/Volume: Polygon API (via GitHub Actions - no network restrictions)
- Automation: GitHub Actions (runs on GitHub servers)
- Backup: Yahoo Finance (if Polygon fails)
- Manual Input: None - fully automated


---

## 📈 DISCOVERED PATTERNS

### Verified Correlations
NONE YET - Will be discovered during analysis phase

### Current Scoring Criteria
CURRENT v5.0.1 CRITERIA - Will be updated based on pattern discovery

### Refinement History
No refinements yet - starting fresh

---

## 🎯 DECISIONS MADE

### Key Decisions
1. Mark all previous backtest results as UNVERIFIED
2. Clear all current portfolio positions - starting fresh
3. Build from verified data only - no fabrication
4. Use 500%+ in 6 months as explosive stock criteria
5. Analyze 180 days pre-catalyst for pattern discovery
6. Store all backtest data (picks AND discards) for refinement
7. Apply false miss principle in all backtests
8. User only does copy/paste - full automation required
9. Free data sources only (no paid APIs except Polygon)
10. Use GitHub Actions for full automation (no local execution)
11. Exclude 2020-2021 from pattern discovery (COVID-era market anomalies)


### Rules Established
1. NEVER fabricate data - verify or say you can't
2. FALSE MISS CHECK - Always check discarded stocks for explosive growth
3. STORE EVERYTHING - All decisions, data, refinements must be saved
4. COPY/PASTE ONLY - User should never manually enter data
5. 10-YEAR VALIDATION - System must prove consistency before live trading
6. COVID-ERA EXCLUSION: Ignore 2020-2021 data (stimulus, zero rates, pandemic anomalies) - not repeatable conditions


---

## 📝 WHAT NEEDS TO HAPPEN NEXT

### Immediate Next Steps
1. USER ACTION: Upload 3 catalog files to GitHub
   - explosive_stocks_catalog.json (raw)
   - explosive_stocks_CLEAN.json (for analysis)
   - explosive_stocks_COVID_ERA.json (archived)
2. AI ACTION: Begin pre-catalyst deep dives on clean stocks
3. AI ACTION: Extract patterns from 180 days before explosions
4. AI ACTION: Build correlation matrix
5. AI ACTION: Create screener criteria from patterns


### Blockers/Questions
None - data ready for analysis

---

## 🔗 IMPORTANT LINKS

- **GitHub Repo**: https://github.com/cbenson85/GEM_Trading_System
- **Polygon API**: Developer tier (key: pvv6DNmKAoxojCc0B5HOaji6I_k1egv0)
- **Data Storage**: /Verified_Backtest_Data/ (to be created in GitHub)

---

## 💾 PROGRESS LOG


**2025-11-01 20:41** - Phase 1
- Action: Completed audit of existing system
- Result: Identified fabricated backtest data, cleared portfolio, established new methodology

**2025-11-01 20:41** - Phase 2
- Action: Creating catch-up prompt system
- Result: IN PROGRESS

**2025-11-01 20:50** - Phase 2
- Action: Created catch-up prompt system
- Result: COMPLETE - System tracks all progress, auto-generates prompts, uploaded to GitHub

**2025-11-01 21:00** - Phase 2
- Action: Built complete data infrastructure and explosive stock scanner
- Result: COMPLETE - Folders created, scanner tested, ready for local execution

**2025-11-01 21:13** - Phase 2
- Action: Switched to GitHub Actions for full automation (no local execution needed)
- Result: Complete automation - user just clicks 'Run workflow', results auto-commit to repo

**2025-11-01 22:26** - Phase 2
- Action: Created COVID-era exclusion filter and documentation
- Result: Filter script ready - will exclude 2020-2021 anomalies from pattern analysis

**2025-11-01 22:39** - System Maintenance
- Action: Created complete GitHub file catalog with links
- Result: Full file structure documented. All files accessible via direct links in catch-up prompt.

**2025-11-01 23:55** - Phase 2 - COMPLETE
- Action: Full 10-year scan completed and filtered
- Result: 170 explosive stocks in clean dataset (2014-2019, 2022-2024). 69 COVID-era stocks archived. Ready for pattern analysis.


---

## ⚠️ CRITICAL REMINDERS

1. **NO FABRICATION**: All data must be verified. If unsure, say so immediately.
2. **FALSE MISS PRINCIPLE**: When backtesting, check discarded stocks for explosive growth
3. **USER DOES COPY/PASTE ONLY**: All automation, no manual data entry for user
4. **STORE EVERYTHING**: All backtest data, decisions, refinements must be saved
5. **10-YEAR VALIDATION**: System must work consistently across 10 years before live use

---

## 🚀 HOW TO CONTINUE

1. Read this entire prompt
2. Ask clarifying questions if anything is unclear
3. Confirm you understand current state and next phase
4. Wait for user approval before proceeding
5. Update this prompt after each phase completion

---

**END OF CATCH-UP PROMPT**
Generated by: GEM Catch-Up Prompt System v1.0
