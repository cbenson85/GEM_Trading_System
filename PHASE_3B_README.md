# Phase 3B: 90-Day Pre-Catalyst Analysis
**Created**: 2025-11-03
**Status**: Infrastructure Ready - Pilot Testing Phase

---

## 🎯 Overview

Phase 3B performs comprehensive 90-day pre-catalyst analysis on the 8 selected sample stocks to discover patterns that predict explosive moves.

**Framework**: 90-day lookback window (optimized from 180 days)
**Sample Size**: 8 stocks with maximum diversity
**Timeline**: 2-3 weeks
**Goal**: Discover 5-10 patterns with >0.60 correlation

---

## 📁 Files Created

### 1. polygon_data_collector.py
**Purpose**: Fetches 90-day OHLC data and calculates technical indicators

**Features**:
- Fetches daily OHLC + volume from Polygon API
- Calculates RSI, MACD, moving averages, Bollinger Bands
- Identifies volume/price patterns automatically
- Handles rate limiting (100 calls/min)
- Generates summary statistics

**Output**: Complete price/volume/technical data for 90 days

### 2. phase3b_analyzer.py
**Purpose**: Main orchestrator for comprehensive analysis

**Features**:
- Coordinates all data collection
- Integrates price, volume, technical data
- Matches against GEM v5 pattern library
- Generates comprehensive JSON per stock
- Calculates actionability scores
- Identifies manual review needs

**Output**: One comprehensive JSON file per stock analyzed

---

## 🚀 Setup Instructions

### Step 1: Upload Scripts to Repository

Upload these files to **root directory**:
- `polygon_data_collector.py`
- `phase3b_analyzer.py`

### Step 2: Set Up Polygon API Key

The API key is already stored in GitHub secrets as `POLYGON_API_KEY`.

**For local testing:**
```bash
export POLYGON_API_KEY='your_api_key_here'
```

### Step 3: Verify Dependencies

The scripts use only standard Python libraries:
- `requests` (for API calls)
- `json`, `os`, `datetime`, `pathlib` (built-in)

**In GitHub Actions**, add to workflow if needed:
```yaml
- name: Install dependencies
  run: pip install requests
```

---

## 💻 Usage

### Option A: Analyze Single Stock (Pilot Test)

```bash
python3 phase3b_analyzer.py
```

**Note**: You'll need to modify the script to include entry/peak dates for the stock you want to analyze. These dates are in `explosive_stocks_CLEAN.json`.

### Option B: Test Data Collector Only

```bash
python3 polygon_data_collector.py
```

This will test the collector with AAPL as a sample.

### Option C: Programmatic Usage

```python
from phase3b_analyzer import Phase3BAnalyzer
import os

# Initialize
api_key = os.environ['POLYGON_API_KEY']
analyzer = Phase3BAnalyzer(api_key)

# Analyze a stock
analysis = analyzer.analyze_stock(
    ticker='AENTW',
    year=2024,
    entry_date='2024-01-15',  # From CLEAN.json
    peak_date='2024-07-10',    # From CLEAN.json
    gain_percent=12398.33
)

# Results saved automatically to:
# Verified_Backtest_Data/phase3b_analysis/AENTW_2024_analysis.json
```

---

## 📊 Data Categories

### Currently Automated (40%)
✅ 1. **Price & Volume** - Polygon API
✅ 2. **Technical Indicators** - Calculated from price data
✅ 9. **Sector Context** - SPY/QQQ comparison

### Manual Collection Needed (60%)
📝 3. **Float & Ownership** - SEC Form 4, 13F filings
📝 4. **Catalyst Intelligence** - Research catalysts, dates
📝 5. **News & Sentiment** - News APIs, social media
📝 6. **Leadership** - Management changes, quality
📝 7. **Financials** - Deep financial analysis
📝 8. **Analyst Coverage** - Tracking coverage changes
📝 10. **Red Flags** - Risk identification
📝 11. **Polygon Advanced** - Dark pool, tick data (optional)

---

## 📈 Output Format

Each stock generates a comprehensive JSON file:

```json
{
  "metadata": {
    "ticker": "AENTW",
    "year": 2024,
    "entry_date": "2024-01-15",
    "peak_date": "2024-07-10",
    "gain_percent": 12398.33,
    "analysis_date": "2025-11-03...",
    "analysis_version": "3.0_90day"
  },
  
  "price_volume": {
    "metadata": { ... },
    "daily_data": [ ... ],  // 90 days of OHLC
    "patterns_detected": [ ... ],
    "summary": { ... }
  },
  
  "technical_indicators": {
    "rsi": 45.23,
    "macd": { ... },
    "moving_averages": { ... },
    "bollinger_bands": { ... },
    "volume_analysis": { ... },
    "volatility": { ... }
  },
  
  "sector_context": {
    "spy_performance": -2.5,
    "qqq_performance": 1.2,
    "data_collected": true
  },
  
  "pattern_library": {
    "total_patterns_detected": 4,
    "patterns": [ ... ],
    "gem_v5_matches": 1,
    "new_patterns": 3,
    "high_confidence_patterns": [ ... ]
  },
  
  "summary": {
    "gain_achieved": 12398.33,
    "days_analyzed": 87,
    "patterns_detected": 4,
    "actionability_score": 70,
    "actionability_rating": "GOOD",
    "data_completeness": {
      "overall_pct": 40
    },
    "manual_review_needed": [ ... ]
  }
}
```

---

## 🎯 Pilot Testing Plan

### Phase 1: Test Infrastructure (1 stock)

**Stock**: AENTW (2024) - 12,398% gain
**Purpose**: Validate scripts work correctly
**Timeline**: 1 day

**Steps**:
1. Get entry/peak dates from CLEAN.json
2. Run analyzer on AENTW
3. Review output JSON
4. Verify patterns detected
5. Check data quality

### Phase 2: Pilot Analysis (2 stocks)

**Stocks**: AENTW + ASNS
**Purpose**: Validate 90-day framework
**Timeline**: 2-3 days

**Steps**:
1. Analyze AENTW (slow builder, extreme gain)
2. Analyze ASNS (ultra-fast, 3 days)
3. Compare patterns between them
4. Identify common signals
5. Refine methodology

### Phase 3: Complete Sample (8 stocks)

**Timeline**: 1.5-2 weeks

**Steps**:
1. Analyze remaining 6 stocks
2. Standardize data collection
3. Complete manual research for all
4. Build pattern frequency matrix
5. Calculate correlations

---

## 🔧 Manual Data Collection Guide

### For Each Stock, Research:

**Float & Ownership (SEC Edgar)**:
- Form 4 filings (insider transactions)
- 13F filings (institutional holdings)
- Look for 3+ insider buys in 90-day window
- Track short interest changes

**Catalyst Intelligence**:
- What was the catalyst? (FDA, earnings, merger, etc.)
- Was there a known date?
- Any pre-announcements?
- Check 8-K filing frequency

**News & Sentiment**:
- Google News search for ticker + date range
- Check Reddit (r/wallstreetbets, r/stocks)
- Twitter/X mentions
- StockTwits sentiment

**Leadership**:
- Any CEO/management changes in 90 days?
- Check LinkedIn for executive backgrounds
- Review press releases

**Analyst Coverage**:
- Finviz "Analyst" tab
- Any initiations or upgrades in 90 days?
- Price target changes?

**Red Flags**:
- Any lawsuits, investigations?
- FDA warning letters?
- Failed previous trials?
- Excessive dilution?

---

## 📋 Next Steps

### Immediate (This Week):
1. ✅ Scripts created and ready
2. ⏳ Upload scripts to repository
3. ⏳ Get entry/peak dates for AENTW from CLEAN.json
4. ⏳ Run pilot test on AENTW
5. ⏳ Review output, validate framework

### Short Term (Next Week):
1. Run pilot on ASNS (compare fast vs slow)
2. Complete manual research for both stocks
3. Refine data collection process
4. Document lessons learned

### Medium Term (Weeks 2-3):
1. Analyze remaining 6 stocks
2. Complete manual research for all 8
3. Build correlation matrix
4. Identify top patterns
5. Generate Phase 3B deliverables

---

## 🎉 Success Metrics

**Pattern Discovery**:
- Find 5-10 patterns with >0.60 correlation
- 7-30 day lead time before entry
- Observable in real-time
- Low false positive rate

**Deliverables**:
- 8 comprehensive JSON files ✅ (framework ready)
- Pattern library documentation
- Correlation matrix
- Preliminary screening criteria

---

## ⚠️ Important Notes

### Rate Limiting
- Polygon API: 100 calls/minute
- Each stock uses ~5 API calls
- Scripts include 0.6s delay between calls

### Data Availability
- Some old tickers may not have data
- Warrant tickers (ending in W) may have limited data
- Check data quality in output JSON

### Manual Work Required
- 60% of data categories need manual research
- Budget ~1 hour per stock for manual collection
- This is normal for comprehensive analysis

---

## 📞 Support

**Issues?**
1. Check POLYGON_API_KEY is set
2. Verify input dates are correct
3. Review error messages in output
4. Check GitHub Actions logs if using workflows

**Questions?**
- Review PRE_CATALYST_ANALYSIS_FRAMEWORK.md
- Check phase3_sample_selection.json for stock details
- Refer to CURRENT_CATCHUP_PROMPT.md for full context

---

**README Version**: 1.0  
**Last Updated**: 2025-11-03  
**Status**: Ready for Pilot Testing  
**Next**: Run AENTW pilot analysis
