# GEM Trading System - Complete GitHub File Catalog

**Repository**: https://github.com/cbenson85/GEM_Trading_System
**Last Updated**: 2025-11-01
**Purpose**: Complete reference of all system files and their locations

---

## 📂 FILE STRUCTURE

### Root Directory

```
https://github.com/cbenson85/GEM_Trading_System/blob/main/

├── README.md
├── explosive_stock_scanner.py
├── filter_covid_era.py
└── COVID_ERA_EXCLUSION_RULE.md
```

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/README.md) - Repository overview
- [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/explosive_stock_scanner.py) - Main scanner (GitHub Actions)
- [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_covid_era.py) - COVID-era data filter
- [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/COVID_ERA_EXCLUSION_RULE.md) - Rule documentation

---

### .github/workflows/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/.github/workflows

├── daily_gem_screening.yml (DISABLED - old workflow)
├── test_polygon_api_workflow.yml
└── explosive_stock_scan_workflow.yml (ACTIVE)
```

**Files:**
- [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/explosive_stock_scan_workflow.yml) - Automated scanning workflow (ACTIVE)
- [daily_gem_screening.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/daily_gem_screening.yml) - Old workflow (DISABLED)

---

### System_State/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/System_State

├── CURRENT_CATCHUP_PROMPT.md
├── catchup_prompt_generator.py
├── system_state.json
├── update_prompt.py
└── CATCHUP_SYSTEM_USAGE.md
```

**Files:**
- [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CURRENT_CATCHUP_PROMPT.md) - Copy/paste this to new AI
- [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/system_state.json) - Current system state
- [catchup_prompt_generator.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/catchup_prompt_generator.py) - Generator script
- [update_prompt.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/update_prompt.py) - Quick updater
- [CATCHUP_SYSTEM_USAGE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CATCHUP_SYSTEM_USAGE.md) - Usage guide

---

### Current_System/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Current_System

├── GEM_v5_Master_Screening_Protocol.md
├── Trading_Rules_Complete.md
├── Scoring_Methodology_Detailed.md
├── GEM_v5_Screener_Criteria.json
├── Daily_Pre_Screening_Verification.md
├── Portfolio_Tracker_Template.csv
└── README.md
```

**Files:**
- [GEM_v5_Master_Screening_Protocol.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Master_Screening_Protocol.md) - Core screening rules (7 phases)
- [Trading_Rules_Complete.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/Trading_Rules_Complete.md) - Trading operations guide
- [Scoring_Methodology_Detailed.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/Scoring_Methodology_Detailed.md) - Scoring details
- [GEM_v5_Screener_Criteria.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Screener_Criteria.json) - Criteria JSON
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/README.md) - Current system overview

---

### Verified_Backtest_Data/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Verified_Backtest_Data

├── README.md
├── explosive_stocks_catalog.json (ACTIVE - updated by scans)
├── explosive_stocks_CLEAN.json (Created after filtering)
├── explosive_stocks_COVID_ERA.json (Created after filtering)
├── filter_summary.json (Created after filtering)
├── correlations_discovered.json
├── refinement_history.json
├── pre_catalyst_analysis/
└── backtest_runs/
```

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/README.md) - Data quality standards
- [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json) - Raw scan results (LIVE DATA)
- [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/refinement_history.json) - All system refinements
- [correlations_discovered.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/correlations_discovered.json) - Patterns found

---

### Archive_Unverified/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Archive_Unverified

└── README.md
```

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Archive_Unverified/README.md) - Marks old data as unverified

---

### Daily_Operations/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Daily_Operations

└── CURRENT_UPDATE.md
```

**Files:**
- [CURRENT_UPDATE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Daily_Operations/CURRENT_UPDATE.md) - Daily update template

---

### Polygon_Integration/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Polygon_Integration

├── README.md
├── daily_screener.py
├── requirements.txt
└── test_polygon_api.py
```

**Files:**
- [README.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Polygon_Integration/README.md) - Integration docs
- [daily_screener.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Polygon_Integration/daily_screener.py) - Old screener (superseded)

---

### Daily_Logs/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Daily_Logs

├── Daily_Screening_Template.md
├── Live_Portfolio_Tracking.md
├── master_trading_data.json
└── README.md
```

**Files:**
- [master_trading_data.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Daily_Logs/master_trading_data.json) - Portfolio data (CLEARED)

---

### Backtest_Results/ (UNVERIFIED)

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Backtest_Results

├── Historical_Performance_Summary.md (UNVERIFIED)
├── README.md
├── Test_Data_Location_Guide.md
└── [Python scripts - frameworks only]
```

**Status**: UNVERIFIED - Contains fabricated data from previous iteration

---

### Strategy_Evolution/ (UNVERIFIED)

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Strategy_Evolution

├── GEM_Strategy_Evolution_Complete.md (UNVERIFIED)
├── Failed_Patterns_Lessons_Learned.md
├── Winning_Patterns_Discovered.md
└── README.md
```

**Status**: UNVERIFIED - Contains unproven claims from previous iteration

---

### Scripts/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Scripts

├── gem_daily_updater.py
├── gem_v4_comprehensive_backtest.py
├── gem_v4_final_screener.py
├── investment_strategy_analysis.py
└── ten_year_backtest_2010_2019.py
```

**Status**: Framework scripts - not executed, contain no actual results

---

### Resources/

```
https://github.com/cbenson85/GEM_Trading_System/tree/main/Resources

├── Portfolio_Position_Management_UPDATED.md
├── Resources_README.md
└── Tools_and_Resources.md
```

---

## 🔑 KEY FILES FOR AI REFERENCE

### **Must Read First:**
1. [CURRENT_CATCHUP_PROMPT.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/CURRENT_CATCHUP_PROMPT.md) - Current system state
2. [GEM_v5_Master_Screening_Protocol.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Current_System/GEM_v5_Master_Screening_Protocol.md) - Screening rules
3. [COVID_ERA_EXCLUSION_RULE.md](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/COVID_ERA_EXCLUSION_RULE.md) - Critical data filter rule

### **Live Data Files:**
1. [explosive_stocks_catalog.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json) - Current scan results
2. [refinement_history.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/refinement_history.json) - System changes log
3. [system_state.json](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/System_State/system_state.json) - Current state

### **Active Automation:**
1. [explosive_stock_scanner.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/explosive_stock_scanner.py) - Main scanner
2. [explosive_stock_scan_workflow.yml](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/.github/workflows/explosive_stock_scan_workflow.yml) - GitHub Actions workflow
3. [filter_covid_era.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/filter_covid_era.py) - Data filter

---

## 📋 QUICK ACCESS TEMPLATE

When starting new AI session, access files like this:

```python
# In AI session, use web_fetch tool:
web_fetch("https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/[FILE_PATH]")

# Example:
web_fetch("https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/main/Verified_Backtest_Data/explosive_stocks_catalog.json")
```

---

## ⚠️ IMPORTANT NOTES

### Files to TRUST (Verified):
- ✅ Everything in `/Verified_Backtest_Data/`
- ✅ Everything in `/System_State/`
- ✅ Everything in `/Current_System/`
- ✅ Root scripts (`explosive_stock_scanner.py`, `filter_covid_era.py`)
- ✅ Active workflow (`explosive_stock_scan_workflow.yml`)

### Files to IGNORE (Unverified):
- ❌ Everything in `/Backtest_Results/` (except README)
- ❌ Everything in `/Strategy_Evolution/` (except README)
- ❌ Scripts in `/Scripts/` (frameworks only, no actual data)

### Files Updated by Automation:
- 🔄 `explosive_stocks_catalog.json` - Updated by GitHub Actions scans
- 🔄 `CURRENT_CATCHUP_PROMPT.md` - Updated after each phase
- 🔄 `system_state.json` - Updated after each phase

---

## 🔗 Repository Structure Summary

```
GEM_Trading_System/
├── 🟢 Active System (TRUST)
│   ├── Current_System/
│   ├── System_State/
│   ├── Verified_Backtest_Data/
│   ├── explosive_stock_scanner.py
│   ├── filter_covid_era.py
│   └── .github/workflows/explosive_stock_scan_workflow.yml
│
├── 🔵 Reference Only
│   ├── Daily_Operations/
│   ├── Daily_Logs/
│   ├── Polygon_Integration/ (old)
│   └── Resources/
│
└── 🔴 Unverified (DO NOT USE)
    ├── Backtest_Results/
    ├── Strategy_Evolution/
    └── Scripts/
```

---

**This catalog should be referenced at the start of every AI session to understand what exists and where to find it.**

**Repository**: https://github.com/cbenson85/GEM_Trading_System
**Catalog Last Updated**: 2025-11-01
