# GEM Trading System - AI Catch-Up Prompt
**Last Updated**: 2025-11-02 02:09:36
**System Version**: 5.0.1-REBUILD
**Current Phase**: Phase 2: System Requirements & Data Infrastructure

---

## 🎯 CRITICAL CONTEXT

### What You're Walking Into
System being rebuilt from ground up. Previous model fabricated backtest data. Starting fresh with verified data only.

### Immediate Priority
Build catch-up prompt system, then create data infrastructure for verified backtesting

---

## 📊 SYSTEM STATUS

### Current State
- **Portfolio**: CLEARED - Starting fresh
- **Cash Available**: $10,000 (reset)
- **System Stage**: Pre-Development - Planning & Infrastructure
- **Last Completed Phase**: Phase 1: Discovery & Documentation Audit - COMPLETE
- **Next Phase**: Phase 2: System Requirements & Data Infrastructure

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

- `/Verified_Backtest_Data/` - TO BE CREATED
- `/Verified_Backtest_Data/explosive_stocks_catalog.json` - TO BE CREATED
- `/Verified_Backtest_Data/pre_catalyst_analysis/` - TO BE CREATED
- `/Verified_Backtest_Data/backtest_runs/` - TO BE CREATED
                

### Unverified/Archived Content

- `/Backtest_Results/` - MARKED UNVERIFIED, kept as framework reference
- `/Strategy_Evolution/` - MARKED UNVERIFIED, contains unproven claims
- All Python backtest scripts - MARKED UNVERIFIED, frameworks only
                

### 📂 Complete GitHub File Catalog

**Key Files for AI to Read:**

**System State:**
- [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/System_State/CURRENT_CATCHUP_PROMPT.md) - Latest state
- [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/System_State/system_state.json) - Current data

**Core Protocols:**
- [GEM_v5_Master_Screening_Protocol.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Current_System/GEM_v5_Master_Screening_Protocol.md) - 7-phase screening
- [Trading_Rules_Complete.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Current_System/Trading_Rules_Complete.md) - Operations
- [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/COVID_ERA_EXCLUSION_RULE.md) - Critical filter
- [FILE_VERIFICATION_PROTOCOL.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/FILE_VERIFICATION_PROTOCOL.md) - File access method

**Live Data:**
- [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Verified_Backtest_Data/explosive_stocks_catalog.json) - Scan results
- [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Verified_Backtest_Data/refinement_history.json) - Changes log

**Active Scripts:**
- [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/explosive_stock_scanner.py) - Scanner
- [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/filter_covid_era.py) - Data filter
- [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/.github/workflows/explosive_stock_scan_workflow.yml) - Automation

**Full Catalog:**
- [GITHUB_FILE_CATALOG.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/GITHUB_FILE_CATALOG.md) - Complete file list with all links

---

## 🔬 BACKTESTING METHODOLOGY

### Approach

1. Find stocks with 500%+ gains in any 6-month window (last 10 years)
2. Deep dive into 180 days PRE-CATALYST for each stock
3. Analyze: price, volume, sentiment, leadership, news, patterns
4. Identify correlations between explosive stocks
5. Build screener based on correlations
6. Backtest on random historical dates
7. Apply FALSE MISS principle to discarded stocks
8. Track picks AND discards with full performance data
9. Refine until consistent 10-year performance
10. Store ALL data for future refinement
                

### Current Progress
NOT STARTED - Building infrastructure first

### Data Sources

- Price/Volume: Polygon API (Developer tier) + Yahoo Finance backup
- News/Sentiment: Web scraping (Google, Yahoo Finance)
- Insider Trading: Free sources (Finviz, OpenInsider, SEC Form 4)
- SEC Filings: SEC EDGAR (free)
- Float/Shares: Polygon API + manual verification
                

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


### Rules Established
1. NEVER fabricate data - verify or say you can't
2. FALSE MISS CHECK - Always check discarded stocks for explosive growth
3. STORE EVERYTHING - All decisions, data, refinements must be saved
4. COPY/PASTE ONLY - User should never manually enter data
5. 10-YEAR VALIDATION - System must prove consistency before live trading
6. FILE VERIFICATION: Every file must be verified using the established protocol


---

## 📝 WHAT NEEDS TO HAPPEN NEXT

### Immediate Next Steps
1. Create catch-up prompt system (IN PROGRESS)
2. Build data infrastructure folders and files
3. Create explosive stock discovery script
4. Run 10-year scan for 500%+ stocks
5. Build pre-catalyst analysis framework
6. Begin deep-dive analyses


### Blockers/Questions
None currently

---

## 🔗 IMPORTANT LINKS

- **GitHub Repo**: https://github.com/cbenson85/GEM_Trading_System
- **Polygon API**: Developer tier (key: pvv6DNmKAoxojCc0B5HOaji6I_k1egv0)
- **Data Storage**: /Verified_Backtest_Data/ (to be created in GitHub)

---

## 🔐 FILE VERIFICATION PROTOCOL (MANDATORY)

### **The Problem We Solved:**
AI was creating files without verifying it could read them back from GitHub. This created broken links and lost context between sessions.

### **The Solution - REQUIRED WORKFLOW:**

**Step 1: AI constructs raw GitHub URL**
```
https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/[FILE_PATH]
```

**Step 2: AI posts URL and requests:** 
"Please paste this URL back to me"

**Step 3: User uploads file (if new) and pastes URL**

**Step 4: AI uses web_fetch to read the file**

**Step 5: AI confirms verification:**
"✅ VERIFIED: [filename] - [key contents summary]"

**Step 6: AI updates catalog and this prompt**

### **Critical Rules:**
- ❌ **AI CANNOT** fetch raw GitHub URLs directly without user providing them first
- ✅ **AI CAN** fetch URLs that user pastes back
- 🔄 **EVERY file** created must follow this verification workflow
- 📝 **EVERY verification** updates the catalog and this prompt
- 🚫 **NO EXCEPTIONS** - If file isn't verified, it doesn't exist to AI

### **Example Workflow:**
```
AI: "I've created backup_system.py. Upload it to /Verified_Backtest_Data/

    To verify, please paste this URL back:
    https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Verified_Backtest_Data/backup_system.py"
     
User: [uploads file to GitHub]
User: https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Verified_Backtest_Data/backup_system.py

AI: [uses web_fetch to read URL]
AI: "✅ VERIFIED: backup_system.py
     - 150 lines
     - Contains: BackupManager class, create_backup(), restore_backup()
     - Status: Accessible and ready to use"
     
AI: [updates GITHUB_FILE_CATALOG.md]
AI: [updates CURRENT_CATCHUP_PROMPT.md]
AI: "Catalog and prompt updated with verified file."
```

### **Why This Matters:**
- ✅ Zero broken links in catalog
- ✅ AI always knows what files exist
- ✅ No wasted conversation tokens searching
- ✅ Perfect continuity between AI sessions
- ✅ Complete audit trail of all files

**Full Documentation:** [FILE_VERIFICATION_PROTOCOL.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/FILE_VERIFICATION_PROTOCOL.md)

---

## 💾 PROGRESS LOG


**2025-11-02 02:09** - Phase 1
- Action: Completed audit of existing system
- Result: Identified fabricated backtest data, cleared portfolio, established new methodology

**2025-11-02 02:09** - Phase 2
- Action: Creating catch-up prompt system
- Result: IN PROGRESS


---

## ⚠️ CRITICAL REMINDERS

1. **NO FABRICATION**: All data must be verified. If unsure, say so immediately.
2. **FALSE MISS PRINCIPLE**: When backtesting, check discarded stocks for explosive growth
3. **USER DOES COPY/PASTE ONLY**: All automation, no manual data entry for user
4. **STORE EVERYTHING**: All backtest data, decisions, refinements must be saved
5. **10-YEAR VALIDATION**: System must work consistently across 10 years before live use
6. **FILE VERIFICATION**: Every file must be verified using the protocol above

---

## 🚀 HOW TO CONTINUE

1. Read this entire prompt
2. Ask clarifying questions if anything is unclear
3. Confirm you understand current state and next phase
4. Wait for user approval before proceeding
5. Update this prompt after each phase completion
6. **VERIFY FILES**: Follow verification protocol for any new files

---

**END OF CATCH-UP PROMPT**
Generated by: GEM Catch-Up Prompt System v2.0 (with File Verification Protocol)
