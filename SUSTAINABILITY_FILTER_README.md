# Sustainability Filter - Documentation

## Purpose

The Sustainability Filter separates **tradeable explosive stocks** from **pump & dumps** and **untradeable flukes**.

## Problem Being Solved

Not all 500%+ explosive moves are tradeable:
- **Pump & dumps**: Collapse immediately after peak (no exit opportunity)
- **Flash squeezes**: Extreme intraday spikes that retrace instantly
- **Thin stocks**: Illiquid stocks with unsustainable gaps

These patterns can't be traded profitably in real-world conditions, so analyzing them wastes time.

## The 30-Day Hold Test

### Criteria
A stock is **SUSTAINABLE** if it meets BOTH conditions:
1. ✅ Achieved 500%+ gain from entry to peak (already filtered)
2. ✅ **Held ≥90% of peak gain for 30 days after peak**

### Why 30 Days?
- Gives enough time to identify and enter position
- Filters out short-lived pumps and flash events
- Ensures stock had real, sustained interest
- Proves the move was tradeable (not just a spike)

### Why 90% Retention?
- Allows for normal pullback (10%) after peak
- Strict enough to eliminate pumps
- Realistic for actual trading conditions

## Example

### ✅ SUSTAINABLE Stock
```
TICKER: XYZ
Entry Price: $2.00
Peak Price: $15.00 (650% gain on Day 45)
Price 30 Days Later: $14.00

Calculation:
- Peak Gain: $15 - $2 = $13
- Gain After 30 Days: $14 - $2 = $12
- Retention: $12 / $13 = 92.3%

Result: SUSTAINABLE ✅ (retained 92.3% > 90%)
```

### ❌ UNSUSTAINABLE Stock (Pump & Dump)
```
TICKER: ABC
Entry Price: $1.00
Peak Price: $8.00 (700% gain on Day 10)
Price 30 Days Later: $2.50

Calculation:
- Peak Gain: $8 - $1 = $7
- Gain After 30 Days: $2.50 - $1 = $1.50
- Retention: $1.50 / $7 = 21.4%

Result: UNSUSTAINABLE ❌ (retained only 21.4% < 90%)
```

## Script Operation

### Input
- `explosive_stocks_CLEAN.json` (200 stocks, 2010-2024)

### Process
1. Load all 200 explosive stocks
2. For each stock:
   - Parse catalyst/peak date
   - Calculate test date (peak + 30 days)
   - Fetch price on test date (Polygon API)
   - Calculate retention percentage
   - Classify as sustainable or unsustainable
3. Use merge logic (preserve existing test results)
4. Generate statistics and summaries

### Output Files
1. **explosive_stocks_SUSTAINABLE.json**
   - Stocks that passed 30-day hold test
   - These will be used for pre-catalyst analysis
   - Expected: ~120-150 stocks

2. **explosive_stocks_UNSUSTAINABLE.json**
   - Stocks that failed (pump & dumps, flukes)
   - Archived for reference
   - Expected: ~50-80 stocks

3. **sustainability_summary.json**
   - Test statistics
   - Average retention rates
   - Reasons for failures

### Merge Logic
Like the COVID filter, this script uses merge logic:
- Existing test results are preserved
- New stocks are tested and added
- No re-testing of already-tested stocks
- No data loss on subsequent runs

## Data Requirements

### Required Fields Per Stock
- `ticker`: Stock symbol
- `entry_price`: Entry price for the move
- `peak_price`: Peak price reached
- `catalyst_date` OR `entry_date` + `days_to_peak`: When peak occurred
- `gain_percent`: Total gain percentage

### API Usage
- **Data Source**: Polygon API (Developer tier)
- **Rate Limit**: 5 requests/minute (free tier)
- **Endpoint**: Daily aggregates (OHLCV data)
- **Fallback**: Checks previous 5 days if market closed

## Success Criteria

### Expected Results
- **Input**: 200 explosive stocks
- **Sustainable**: 120-150 stocks (60-75%)
- **Unsustainable**: 50-80 stocks (25-40%)

### Quality Indicators
- Sustainable stocks should have avg retention >95%
- Unsustainable stocks should have avg retention <60%
- Most failures should be from 2023-2024 (too recent to test)

## Next Steps After Filter

Once sustainability filter completes:
1. ✅ Have clean dataset of tradeable explosive stocks
2. ✅ Begin pre-catalyst data collection on SUSTAINABLE.json only
3. ✅ Save weeks of analysis time (no pump & dump research)
4. ✅ Build screener from reliable, tradeable patterns

## Usage

### Run Filter
```bash
python filter_sustainability.py
```

### View Results
```bash
# Count sustainable stocks
cat explosive_stocks_SUSTAINABLE.json | grep "ticker" | wc -l

# View summary
cat sustainability_summary.json
```

### Verify Filter
```bash
# Check for duplicates
python -c "
import json
with open('explosive_stocks_SUSTAINABLE.json') as f:
    stocks = json.load(f)
    keys = [f\"{s['ticker']}_{s.get('year_discovered', s.get('year'))}\" for s in stocks]
    print(f'Total: {len(keys)}, Unique: {len(set(keys))}')
"
```

## Notes

- Filter respects Polygon API rate limits (5 req/min)
- Full run on 200 stocks takes ~40 minutes
- Stocks from 2024 may be skipped (test date in future)
- Missing price data results in "unsustainable" classification
- All test results are preserved with stock data for audit trail

---

**Version**: 1.0  
**Created**: 2025-11-02  
**Purpose**: Filter tradeable explosive stocks before pre-catalyst analysis  
**Criteria**: 30-day hold test with 90% gain retention threshold
