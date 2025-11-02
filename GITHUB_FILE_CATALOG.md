# GEM Trading System - GitHub File Catalog

**Repository**: https://github.com/cbenson85/GEM_Trading_System
**Last Updated**: 2025-11-02 17:15:00
**Status**: Updated with sustainability filter automation

---

## 📂 ACTUAL CURRENT FILE STRUCTURE

### **Root Directory**

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/README.md)
- [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/explosive_stock_scanner.py) ✅ Active
- [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_covid_era.py) ✅ Active
- [filter_sustainability.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_sustainability.py) ✅ **VERIFIED** (30-day hold test, modifies CLEAN.json)
- [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/COVID_ERA_EXCLUSION_RULE.md) ✅ Active
- [FILE_VERIFICATION_PROTOCOL.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/FILE_VERIFICATION_PROTOCOL.md) ✅ Active
- [GITHUB_FILE_CATALOG.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/GITHUB_FILE_CATALOG.md) ✅ This file
- [SUSTAINABILITY_FILTER_README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/SUSTAINABILITY_FILTER_README.md) ✅ **VERIFIED** (Filter documentation)
- [SUSTAINABILITY_AUTOMATION_UPDATE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/SUSTAINABILITY_AUTOMATION_UPDATE.md) ✅ **VERIFIED** (Automation explanation)

---

### **.github/workflows/**

**Files:**
- [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/explosive_stock_scan_workflow.yml) ✅ ACTIVE (Full automation)
- [sustainability_filter_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/sustainability_filter_workflow.yml) ✅ **VERIFIED** (Sustainability filter automation)
- [daily_gem_screening.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/daily_gem_screening.yml) ⚠️ DISABLED
- [test_polygon_api_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/test_polygon_api_workflow.yml)

---

### **System_State/**

**Files:**
- [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CURRENT_CATCHUP_PROMPT.md) ✅ Main prompt
- [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/system_state.json) ✅ State data
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
- [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json) ✅ LIVE DATA (Latest scan: 2010-2012, 11 stocks)
- [explosive_stocks_CLEAN.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_CLEAN.json) ✅ VERIFIED (200 stocks - WILL BE MODIFIED by sustainability filter)
- [explosive_stocks_COVID_ERA.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_COVID_ERA.json) ✅ VERIFIED (81 stocks archived)
- [filter_summary.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/filter_summary.json) ✅ VERIFIED (Merge statistics)
- [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/refinement_history.json) ✅ Active
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/README.md) ✅ Data quality standards
- [PRE_CATALYST_ANALYSIS_FRAMEWORK.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PRE_CATALYST_ANALYSIS_FRAMEWORK.md) ✅ VERIFIED
- [PHASE_3_IMPLEMENTATION_PLAN.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PHASE_3_IMPLEMENTATION_PLAN.md) ✅ VERIFIED
- [STANDARD_DATA_FORMAT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/STANDARD_DATA_FORMAT.md) ✅ VERIFIED

**Will Be Created by Sustainability Filter:**
- explosive_stocks_UNSUSTAINABLE.json ❌ (Will be created - pump & dumps archived here)
- sustainability_summary.json ❌ (Will be created - filter statistics)

**Folders:**
- pre_catalyst_analysis/ ❌ (Phase 3 data collection - not started)
- backtest_runs/ ❌ (Phase 4+ - not started)

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

### **Archive_Unverified/** ✅ EXISTS

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Archive_Unverified/README.md) ✅ Archived data explanation

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

## 🔑 KEY FILES FOR AI TO READ

### **Start Here (Critical):**
1. [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CURRENT_CATCHUP_PROMPT.md) - Current state
2. [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/system_state.json) - State data (MUST update with prompt)
3. [FILE_VERIFICATION_PROTOCOL.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/FILE_VERIFICATION_PROTOCOL.md) - File workflow
4. [GEM_v5_Master_Screening_Protocol.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Master_Screening_Protocol.md) - Core rules
5. [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/COVID_ERA_EXCLUSION_RULE.md) - Filter rule

### **Live Data:**
1. [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json) - Latest scan (LIVE)
2. [explosive_stocks_CLEAN.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_CLEAN.json) - 200 clean stocks
3. [explosive_stocks_COVID_ERA.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_COVID_ERA.json) - 81 archived
4. [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/refinement_history.json) - System changes

### **Phase 3 Framework:**
1. [PRE_CATALYST_ANALYSIS_FRAMEWORK.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PRE_CATALYST_ANALYSIS_FRAMEWORK.md) - Analysis methodology
2. [PHASE_3_IMPLEMENTATION_PLAN.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/PHASE_3_IMPLEMENTATION_PLAN.md) - Execution plan
3. [STANDARD_DATA_FORMAT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/STANDARD_DATA_FORMAT.md) - Data schema

### **Sustainability Filter (NEW):**
1. [filter_sustainability.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_sustainability.py) - 30-day hold test filter
2. [SUSTAINABILITY_FILTER_README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/SUSTAINABILITY_FILTER_README.md) - Filter documentation
3. [SUSTAINABILITY_AUTOMATION_UPDATE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/SUSTAINABILITY_AUTOMATION_UPDATE.md) - Automation explanation
4. [sustainability_filter_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/sustainability_filter_workflow.yml) - GitHub Action

### **Active Scripts:**
1. [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/explosive_stock_scanner.py) - Multi-year scanner
2. [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_covid_era.py) - COVID filter (merge logic)
3. [filter_sustainability.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_sustainability.py) - Sustainability filter (30-day hold test)
4. [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/explosive_stock_scan_workflow.yml) - Scan automation
5. [sustainability_filter_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/sustainability_filter_workflow.yml) - Filter automation

---

## 📝 FILES VERIFIED IN THIS SESSION (2025-11-02)

### **Created & Verified:**
1. ✅ **filter_sustainability.py** - Sustainability filter script
2. ✅ **SUSTAINABILITY_FILTER_README.md** - Filter documentation  
3. ✅ **SUSTAINABILITY_AUTOMATION_UPDATE.md** - Automation explanation
4. ✅ **sustainability_filter_workflow.yml** - GitHub Actions workflow
5. ✅ **GITHUB_FILE_CATALOG.md** - This file (updated)

---

## ✅ VERIFICATION CHECKLIST

- ✅ Root files correct (including sustainability filter files)
- ✅ System_State files correct
- ✅ Current_System files correct
- ✅ Verified_Backtest_Data has all Phase 2 files verified
- ✅ Archive_Unverified exists with README
- ✅ All old folders exist (Backtest_Results, Strategy_Evolution, Scripts)
- ✅ Sustainability filter files verified and documented
- ✅ GitHub Actions workflows verified

---

## 🚨 CRITICAL REMINDERS

1. **ALWAYS UPDATE THIS CATALOG** when creating new files
2. **PAIRED FILES**: When updating CURRENT_CATCHUP_PROMPT.md, ALSO update system_state.json
3. **FILE VERIFICATION**: Follow protocol - create, post URL, user uploads, verify, update catalog
4. **STATUS MARKERS**:
   - ✅ VERIFIED - File uploaded and verified via web_fetch
   - ⏳ PENDING - File created, awaiting upload/verification
   - ❌ MISSING - File needed but not created yet
   - ⚠️ UNVERIFIED - Old data, reference only

---

**Last Updated**: 2025-11-02 17:15:00
**Repository**: https://github.com/cbenson85/GEM_Trading_System
**Status**: Sustainability filter automation complete and documented
