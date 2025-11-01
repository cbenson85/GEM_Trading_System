# Verified Backtest Data

**Purpose**: Store all VERIFIED backtesting data with full audit trail

**Status**: Active - All data here is verified from real sources

---

## Folder Structure

### `/explosive_stocks_catalog.json`
Complete catalog of all stocks that achieved 500%+ returns in any 6-month window from 2014-2024.

**Format:**
```json
{
  "scan_date": "2025-11-01",
  "scan_period": "2014-2024",
  "total_stocks_found": 0,
  "stocks": [
    {
      "ticker": "EXAMPLE",
      "catalyst_date": "2020-06-15",
      "pre_catalyst_price": 2.50,
      "peak_price": 15.00,
      "gain_percent": 500,
      "days_to_peak": 45,
      "sector": "Biotech",
      "verified": true,
      "data_source": "Polygon/Yahoo"
    }
  ]
}
```

### `/pre_catalyst_analysis/`
Detailed 180-day pre-catalyst analysis for each explosive stock.

**File naming**: `{TICKER}_{CATALYST_DATE}_analysis.json`

**Contains**: Price, volume, technical indicators, news sentiment, insider activity, float changes

### `/backtest_runs/`
Individual backtest run results with complete pick/discard tracking.

**File naming**: `backtest_{DATE}_{RUN_ID}.json`

**Contains**: 
- Date of backtest
- Screener criteria used
- All picks with scores
- All discards with reasons
- Performance tracking (30/60/90/180 days)
- False miss analysis

### `/correlations_discovered.json`
Patterns and correlations found across explosive stocks.

**Updated as we discover patterns**

### `/refinement_history.json`
Complete log of all screener refinements with reasoning.

**Tracks**: What changed, why it changed, impact of change

---

## Data Quality Standards

✅ **All data must be:**
- Verified from real sources (Polygon, Yahoo, SEC)
- Complete (no gaps or missing days)
- Accurate (spot-checked for errors)
- Documented (source and date noted)

❌ **Never include:**
- Fabricated or estimated data
- Unverified claims
- Data with quality issues
- Assumptions without evidence

---

## Usage

This folder is the **source of truth** for all backtesting work.

When starting new AI session, reference these files to understand:
- What stocks were explosive
- What patterns were found
- What refinements were made
- Current system performance

---

**Created**: 2025-11-01
**Last Updated**: 2025-11-01
