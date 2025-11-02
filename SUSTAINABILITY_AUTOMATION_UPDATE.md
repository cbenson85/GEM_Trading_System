# Sustainability Filter - Automation Update

## 🎯 What Changed

### Original Approach (filter_sustainability.py)
- Created 3 separate files:
  - `explosive_stocks_SUSTAINABLE.json` (tradeable stocks)
  - `explosive_stocks_UNSUSTAINABLE.json` (pump & dumps)
  - Original `CLEAN.json` stayed unchanged

### **NEW Automated Approach (filter_sustainability_v2.py)** ✅

Works exactly like the COVID filter:
- **MODIFIES `CLEAN.json` directly** - removes unsustainable stocks
- Creates `explosive_stocks_UNSUSTAINABLE.json` (archived pump & dumps)
- Creates `sustainability_summary.json` (statistics)
- Result: `CLEAN.json` contains ONLY sustainable, tradeable stocks

---

## 🔄 How It Works (Exactly Like COVID Filter)

### Before Filter:
```
explosive_stocks_CLEAN.json = 200 stocks (all explosive moves)
```

### After Filter:
```
explosive_stocks_CLEAN.json = 120-150 stocks (SUSTAINABLE ONLY)
explosive_stocks_UNSUSTAINABLE.json = 50-80 stocks (pump & dumps, archived)
sustainability_summary.json = statistics
```

---

## 📂 File Structure

```
Verified_Backtest_Data/
├── explosive_stocks_catalog.json      (latest scan snapshot)
├── explosive_stocks_CLEAN.json        (SUSTAINABLE stocks only - MODIFIED by filter)
├── explosive_stocks_COVID_ERA.json    (2020-2021 archived)
├── explosive_stocks_UNSUSTAINABLE.json (pump & dumps - CREATED by filter)
├── filter_summary.json                (COVID filter stats)
└── sustainability_summary.json        (sustainability filter stats - CREATED)
```

---

## 🤖 GitHub Actions Workflow

### Location: `.github/workflows/sustainability_filter_workflow.yml`

### What It Does:
1. ✅ Checks out repository
2. ✅ Sets up Python and installs dependencies
3. ✅ Runs `filter_sustainability.py`
4. ✅ Verifies results (shows counts)
5. ✅ Commits and pushes 3 files:
   - Updated `CLEAN.json` (sustainable only)
   - New `UNSUSTAINABLE.json` (archived)
   - New `sustainability_summary.json` (stats)

### How to Run:
1. Go to GitHub Actions tab
2. Select "Sustainability Filter Workflow"
3. Click "Run workflow"
4. Optionally enter reason
5. Wait ~40 minutes (API rate limits)
6. Files automatically committed and pushed

---

## 🔑 Key Features

### Merge Logic (Like COVID Filter)
- ✅ Preserves existing test results
- ✅ Only tests new/untested stocks
- ✅ No re-testing on subsequent runs
- ✅ No data loss

### Automatic Cleanup
- ✅ CLEAN.json automatically cleaned (sustainable only)
- ✅ Unsustainable stocks safely archived
- ✅ Available for future reference if needed
- ✅ Just like COVID_ERA.json approach

### Statistics Tracking
- ✅ Tracks how many removed
- ✅ Shows retention percentages
- ✅ Logs all skip reasons
- ✅ Full audit trail

---

## 📋 Files to Upload

### 1. **Replace existing filter** (CRITICAL UPDATE)
**File**: `filter_sustainability_v2.py`  
**Upload to**: `/filter_sustainability.py` (REPLACE existing)  
**Why**: Updated to modify CLEAN.json directly instead of creating separate file

### 2. **Add GitHub Actions workflow**
**File**: `sustainability_filter_workflow.yml`  
**Upload to**: `/.github/workflows/sustainability_filter_workflow.yml`  
**Why**: Enables one-click automated filtering

---

## 🎯 Expected Results

### Input:
- `explosive_stocks_CLEAN.json`: 200 stocks (2010-2024, no COVID)

### Output:
- `explosive_stocks_CLEAN.json`: ~120-150 sustainable stocks (MODIFIED)
- `explosive_stocks_UNSUSTAINABLE.json`: ~50-80 pump & dumps (NEW)
- `sustainability_summary.json`: Full statistics (NEW)

### Success Metrics:
- ✅ Sustainable stocks: avg retention >95%
- ✅ Unsustainable stocks: avg retention <60%
- ✅ CLEAN.json ready for pre-catalyst analysis
- ✅ All data preserved (nothing lost)

---

## 🚀 What Happens Next

After filter runs successfully:

1. ✅ `CLEAN.json` contains ONLY tradeable explosive stocks
2. ✅ Pump & dumps safely archived in `UNSUSTAINABLE.json`
3. ✅ Ready to begin Phase 3 pre-catalyst data collection
4. ✅ Save weeks of time by not analyzing untradeable stocks

---

## 📝 Summary

**This approach is IDENTICAL to the COVID filter methodology:**
- Automatically modifies CLEAN.json (removes bad stocks)
- Archives removed stocks for reference
- Uses merge logic (no data loss)
- Full GitHub Actions automation
- One-click operation

**Result**: Clean, tradeable dataset ready for pattern analysis! 🎯

---

**Version**: 2.0 (Automated)  
**Created**: 2025-11-02  
**Purpose**: Automate sustainability filtering with CLEAN.json modification
