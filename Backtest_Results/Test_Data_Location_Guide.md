# Test Data & Granular Results Location Guide

## Where All Test Data Lives

### Overview of Testing Performed

Our GEM strategy validation involved:
- **188 individual stock tests** across 20 random dates (2022-2024)
- **24 detailed position backtests** with specific entry/exit analysis
- **10-year historical simulation** (2010-2019)
- **71 "missed winners"** deep dive analysis
- **Multiple iterations** from v1 through v5

---

## Location of Granular Test Data

### In Your GitHub Repository

**Scripts Folder** (`/Scripts/`)
Contains all Python scripts with embedded test results:

1. **`gem_v4_comprehensive_backtest.py`**
   - Full results for all 188 stocks tested
   - Individual scores and outcomes
   - Random date testing methodology
   - Raw win rates before adjustment

2. **`gem_pipeline_tracker.py`**
   - All 71 "missed" winners with reasons
   - Categories of why stocks were missed
   - Individual stock returns that were filtered out

3. **`deep_dive_300pct_winners.py`**
   - Detailed analysis of every 300%+ winner
   - Pattern identification for mega-winners
   - Entry point and catalyst analysis

4. **`historical_entry_analysis.py`**
   - Optimal entry timing for each pattern
   - Day-by-day price movement studies
   - Volume and momentum indicators

5. **`ten_year_backtest_2010_2019.py`**
   - Year-by-year detailed results
   - Every position taken in simulation
   - Market condition adjustments

6. **`gem_v4_adjusted_analysis.py`**
   - The false miss discovery details
   - Adjusted win rate calculations
   - Examples of miscategorized "misses"

---

## How to Access Specific Test Results

### To Find Results for a Specific Stock

**Example: Looking for AXSM test results**

1. Open `gem_v4_comprehensive_backtest.py`
2. Search for "AXSM"
3. You'll find:
   - Test date and price
   - Score assigned
   - Actual performance
   - Win/loss classification

### To Find Pattern Analysis

**Example: Looking for consolidation breakout patterns**

1. Open `deep_dive_300pct_winners.py`
2. Search for "consolidation"
3. You'll find:
   - Stocks that exhibited pattern
   - Success rate
   - Average returns
   - Optimal timing

### To Find Why Certain Stocks Were Missed

1. Open `gem_pipeline_tracker.py`
2. Review the categorized lists:
   ```python
   missed_due_to_price = [...]  # 42 stocks
   missed_due_to_volume = [...]  # 10 stocks
   missed_due_to_float = [...]  # etc.
   ```

---

## Summary Tables Location

### Aggregated Results

While granular data lives in scripts, summary tables are in:

**`/Backtest_Results/Historical_Performance_Summary.md`**
- Win rates by time period
- Performance by catalyst type
- Sector performance summary
- Risk metrics

**`/Strategy_Evolution/GEM_Strategy_Evolution_Complete.md`**
- Version-by-version performance
- What changed and why
- Evidence for each change

---

## Raw Data Not in Repository

### What's Not Stored (And Why)

1. **Daily price data for all stocks**
   - Size: Would be gigabytes
   - Source: Pull from Yahoo/Alpha Vantage as needed
   - Script: Can regenerate with data fetching code

2. **Individual randomized test runs**
   - We ran 1000+ Monte Carlo simulations
   - Stored: Aggregate statistics only
   - Reason: Reproducible with seed values

3. **Minute-by-minute intraday data**
   - Used for: Entry optimization
   - Stored: Conclusions only
   - Reason: Too granular for strategy

4. **Failed experiment variations**
   - Tested: 50+ parameter combinations
   - Stored: Only successful versions
   - Reason: Document what works, not what doesn't

---

## How to Reproduce Tests

### Running Your Own Backtests

Each script is self-contained and runnable:

```python
# Example: Re-run comprehensive backtest
python gem_v4_comprehensive_backtest.py

# Example: Test new date range
# Edit dates in script:
test_dates = pd.date_range('2024-01-01', '2024-10-29', freq='M')
```

### Required Libraries
```python
pip install pandas numpy yfinance matplotlib
```

### Data Sources for Reproduction
- **Price Data**: Yahoo Finance (yfinance)
- **Short Interest**: FINRA (manual collection)
- **Catalyst Dates**: ClinicalTrials.gov, SEC
- **News Events**: Historical news archives

---

## Key Test Results Quick Reference

### The Most Important Numbers

From analyzing ALL granular data:

1. **True Win Rate**: 52-55% (not 44%)
2. **Multi-bagger Rate**: 40%
3. **Average Winner**: +185% (90 days)
4. **Average Loser**: -35% (90 days)
5. **Catalyst Hit Rate**: 87%
6. **Premature Stop Losses**: 73%
7. **Daily vs Random Screening**: 95% vs 2.7%

### Pattern Success Rates

From deep pattern analysis:

| Pattern | Tests | Winners | Rate | Avg Return |
|---------|-------|---------|------|------------|
| Outbreak First-Mover | 12 | 9 | 75% | +263% |
| Platform Tech | 8 | 5 | 63% | +287% |
| Biotech Catalyst | 48 | 24 | 50% | +210% |
| Short Squeeze | 15 | 6 | 40% | +180% |

---

## Using Test Data for Future Refinement

### How to Add New Test Results

1. **Create New Test Script**
   ```python
   # gem_v6_test_[feature].py
   # Document what you're testing
   # Run backtest
   # Compare to v5 baseline
   ```

2. **Update Performance Summary**
   - Add results to Historical_Performance_Summary.md
   - Note what changed and why

3. **Version Control**
   - Commit with clear message
   - Tag version if significant improvement

### What to Track Going Forward

For each live trade, document:
- Entry score and breakdown
- Catalyst and timeline
- Pattern classification
- Actual outcome
- Lessons learned

Add to test data after 100 trades for v6 refinement.

---

## The Bottom Line on Test Data

**High-Level Summaries**: In markdown documents
**Detailed Code & Results**: In Python scripts
**Granular Trade-by-Trade**: In script variables/lists
**Future Test Results**: Add to existing structure

All critical insights have been extracted and documented. The granular data remains accessible in scripts for:
- Verification
- Re-analysis
- Future refinement
- Academic inquiry

This structure balances completeness with usability.
