# GEM Trading System - GitHub File Catalog

**Repository**: https://github.com/cbenson85/GEM_Trading_System
**Last Updated**: 2025-11-02 17:30:00
**Status**: Accurate reflection of current repository state

---

## 📂 ACTUAL CURRENT FILE STRUCTURE

### **Root Directory**

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/README.md)
- [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/explosive_stock_scanner.py) ✅ Active
- [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_covid_era.py) ✅ Active (with merge logic)
- [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/COVID_ERA_EXCLUSION_RULE.md) ✅ Active
- [FILE_VERIFICATION_PROTOCOL.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/FILE_VERIFICATION_PROTOCOL.md) ✅ Active (mandatory workflow)

---

### **.github/workflows/**

**Files:**
- [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/explosive_stock_scan_workflow.yml) ✅ ACTIVE (includes filter step, full automation)
- [daily_gem_screening.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/daily_gem_screening.yml) ⚠️ DISABLED
- [test_polygon_api_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/test_polygon_api_workflow.yml)

---

### **System_State/**

**Files:**
- [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CURRENT_CATCHUP_PROMPT.md) ✅ VERIFIED (2025-11-02) - Updated with Phase 2 complete, 200 stocks
- [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/system_state.json) ✅ VERIFIED (2025-11-02) - Machine-readable state
- [catchup_prompt_generator.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/catchup_prompt_generator.py) ✅ Generator
- [update_prompt.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/update_prompt.py)
- [CATCHUP_SYSTEM_USAGE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CATCHUP_SYSTEM_USAGE.md)
- [CATCHUP_SYSTEM_COMPLETE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CATCHUP_SYSTEM_COMPLETE.md)

---

### **Current_System/**

**Files:**
- [GEM_v5_Master_Screening_Protocol.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Master_Screening_Protocol.md) ✅ Core protocol
- [Trading_Rules_Complete.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/Trading_Rules_Complete.md) ✅ Trading rules
- [Scoring_Methodology_Detailed.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/Scoring_Methodology_Detailed.md)
- [GEM_v5_Screener_Criteria.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Screener_Criteria.json)
- [Daily_Pre_Screening_Verification.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/Daily_Pre_Screening_Verification.md)
- [Portfolio_Tracker_Template.csv](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/Portfolio_Tracker_Template.csv)
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/README.md)

---

### **Verified_Backtest_Data/**

**Files (Currently Exist):**
- [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json) ✅ LIVE DATA (Latest: 2010-2012 scan, 11 stocks)
- [explosive_stocks_CLEAN.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_CLEAN.json) ✅ VERIFIED (200 stocks, 2010-2024 excluding COVID)
- [explosive_stocks_COVID_ERA.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_COVID_ERA.json) ✅ VERIFIED (81 stocks, 2020-2021 archived)
- [filter_summary.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/filter_summary.json) ✅ VERIFIED (Merge statistics)
- [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/refinement_history.json) ✅ Active
- [PRE_CATALYST_ANALYSIS_FRAMEWORK.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PRE_CATALYST_ANALYSIS_FRAMEWORK.md) ✅ VERIFIED (2025-11-02) - v2.0, 12 categories, 100+ data points
- [PHASE_3_IMPLEMENTATION_PLAN.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PHASE_3_IMPLEMENTATION_PLAN.md) ⏳ PENDING VERIFICATION - Detailed Phase 3 execution plan
- [STANDARD_DATA_FORMAT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/STANDARD_DATA_FORMAT.md) ✅ VERIFIED (2025-11-02) - v1.0, JSON schema for all 200 stocks

**Missing Files (To Be Created):**
- README.md ❌ (need to create)
- correlations_discovered.json ❌ (will be created in Phase 3)
- pre_catalyst_analysis/ folder ❌ (need to create for Phase 3 data)
- backtest_runs/ folder ❌ (need to create for Phase 4)

---

### **Daily_Operations/**

**Files:**
- [CURRENT_UPDATE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Daily_Operations/CURRENT_UPDATE.md)

---

### **Polygon_Integration/**

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Polygon_Integration/README.md)
- [daily_screener.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Polygon_Integration/daily_screener.py)
- [requirements.txt](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Polygon_Integration/requirements.txt)
- [test_polygon_api.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Polygon_Integration/test_polygon_api.py)

---

### **Daily_Logs/**

**Files:**
- [Daily_Screening_Template.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Daily_Logs/Daily_Screening_Template.md)
- [Live_Portfolio_Tracking.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Daily_Logs/Live_Portfolio_Tracking.md)
- [master_trading_data.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Daily_Logs/master_trading_data.json)
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Daily_Logs/README.md)

---

### **Backtest_Results/** ⚠️ UNVERIFIED - OLD DATA

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Backtest_Results/README.md)
- [Historical_Performance_Summary.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Backtest_Results/Historical_Performance_Summary.md) ❌ Unverified
- [Test_Data_Location_Guide.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Backtest_Results/Test_Data_Location_Guide.md)
- [deep_dive_300pct_winners.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Backtest_Results/deep_dive_300pct_winners.py) 
- [gem_pipeline_tracker.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Backtest_Results/gem_pipeline_tracker.py)
- [gem_v4_adjusted_analysis.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Backtest_Results/gem_v4_adjusted_analysis.py)
- [historical_entry_analysis.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Backtest_Results/historical_entry_analysis.py)

---

### **Strategy_Evolution/** ⚠️ UNVERIFIED - OLD DATA

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Strategy_Evolution/README.md)
- [GEM_Strategy_Evolution_Complete.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Strategy_Evolution/GEM_Strategy_Evolution_Complete.md) ❌ Unverified
- [Failed_Patterns_Lessons_Learned.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Strategy_Evolution/Failed_Patterns_Lessons_Learned.md)
- [False_Miss_Discovery.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Strategy_Evolution/False_Miss_Discovery.md)
- [Winning_Patterns_Discovered.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Strategy_Evolution/Winning_Patterns_Discovered.md)

---

### **Scripts/** (Framework only - no actual results)

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Scripts/README.md)
- [gem_daily_updater.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Scripts/gem_daily_updater.py)
- [gem_v4_comprehensive_backtest.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Scripts/gem_v4_comprehensive_backtest.py)
- [gem_v4_final_screener.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Scripts/gem_v4_final_screener.py)
- [investment_strategy_analysis.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Scripts/investment_strategy_analysis.py)
- [ten_year_backtest_2010_2019.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Scripts/ten_year_backtest_2010_2019.py)

---

### **Resources/**

**Files:**
- [Portfolio_Position_Management_UPDATED.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Resources/Portfolio_Position_Management_UPDATED.md)
- [Resources_README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Resources/Resources_README.md)
- [Tools_and_Resources.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Resources/Tools_and_Resources.md)

---

## ❌ MISSING FOLDERS/FILES

### **Archive_Unverified/** - DOES NOT EXIST YET
- **Status**: Folder not created
- **Action**: Need to create this folder and add README.md

### **Verified_Backtest_Data/** - Missing Files:
- README.md (need to upload)
- correlations_discovered.json (will be created in Phase 3)
- pre_catalyst_analysis/ folder (need to create)
- backtest_runs/ folder (need to create)

---

## 🔑 KEY FILES FOR AI TO READ

### **Start Here (Critical):**
1. [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CURRENT_CATCHUP_PROMPT.md) - Current state (Phase 2 complete, 200 stocks)
2. [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/system_state.json) - Machine-readable state
3. [FILE_VERIFICATION_PROTOCOL.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/FILE_VERIFICATION_PROTOCOL.md) - **MANDATORY** file creation workflow
4. [GEM_v5_Master_Screening_Protocol.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Master_Screening_Protocol.md) - Core rules
5. [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/COVID_ERA_EXCLUSION_RULE.md) - Filter rule

### **Phase 3 Framework:**
1. [PRE_CATALYST_ANALYSIS_FRAMEWORK.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PRE_CATALYST_ANALYSIS_FRAMEWORK.md) - v2.0, 12 categories, 100+ data points
2. [PHASE_3_IMPLEMENTATION_PLAN.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PHASE_3_IMPLEMENTATION_PLAN.md) - Detailed execution plan
3. [STANDARD_DATA_FORMAT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/STANDARD_DATA_FORMAT.md) - JSON schema for all stocks

### **Live Data:**
1. [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json) - Latest scan (2010-2012, 11 stocks)
2. [explosive_stocks_CLEAN.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_CLEAN.json) - 200 stocks (2010-2024, excluding COVID)
3. [explosive_stocks_COVID_ERA.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_COVID_ERA.json) - 81 archived stocks (2020-2021)
4. [filter_summary.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/filter_summary.json) - Merge statistics
5. [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/refinement_history.json) - System changes

### **Active Automation:**
1. [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/explosive_stock_scanner.py) - Multi-year scanner
2. [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_covid_era.py) - Data filter (with merge logic)
3. [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/explosive_stock_scan_workflow.yml) - GitHub Actions (full automation)

---

## 📝 FILES TO CREATE/UPLOAD

### **Priority 1 (Need Now):**
1. **Verified_Backtest_Data/README.md** - Data quality standards
2. **Archive_Unverified/** folder with README.md

### **Priority 2 (Will be created in Phase 3):**
- Sustainability filter script (pre-filter for pump & dumps)
- Data collection scripts (8 collectors)
- Pattern scanning tools
- Correlation matrix

---

## ✅ VERIFICATION CHECKLIST

- ✅ Root files correct (includes FILE_VERIFICATION_PROTOCOL.md)
- ✅ System_State files correct (CATCHUP_PROMPT + system_state updated 2025-11-02)
- ✅ Current_System files correct
- ✅ Verified_Backtest_Data has 8 files (catalog, CLEAN, COVID, filter_summary, refinement, framework, implementation plan, standard format)
- ❌ Archive_Unverified does NOT exist (need to create)
- ✅ All old folders exist (Backtest_Results, Strategy_Evolution, Scripts)

---

## 📋 RECENT UPDATES (2025-11-02)

**System State Files:**
- ✅ CURRENT_CATCHUP_PROMPT.md - Updated with Phase 2 complete, 200 stocks, ready for Phase 3
- ✅ system_state.json - Machine-readable state snapshot

**Phase 3 Framework:**
- ✅ PRE_CATALYST_ANALYSIS_FRAMEWORK.md - Comprehensive framework (v2.0)
- ⏳ PHASE_3_IMPLEMENTATION_PLAN.md - Detailed execution plan (pending verification)
- ✅ STANDARD_DATA_FORMAT.md - JSON schema for uniform data structure (v1.0)

**Dataset:**
- ✅ explosive_stocks_CLEAN.json - Expanded from 189 to 200 stocks (2010-2012 added)
- ✅ filter_summary.json - Tracking merge statistics

---

**Last Updated**: 2025-11-02 17:30:00
**Repository**: https://github.com/cbenson85/GEM_Trading_System
**Status**: CURRENT - Reflects all verified files as of Phase 2 completion
