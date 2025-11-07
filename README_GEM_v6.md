# GEM Screener v6.0 - GitHub Actions Setup

## Quick Start

1. **Run Setup** (one time only):
   - Go to Actions tab
   - Select "GEM Screener v6.0 - Setup"
   - Click "Run workflow"

2. **Daily Screening**:
   - Go to Actions tab
   - Select "GEM Screener v6.0 - Daily Screen"
   - Choose universe size and run
   - Or wait for automatic 4:30 PM ET run

3. **Track Positions**:
   - After buying/rejecting stocks
   - Go to "GEM Screener v6.0 - Track & Validate"
   - Select "update_positions"
   - Enter ticker, decision, and reason

4. **Check Outcomes** (automatic weekly):
   - Runs every Sunday
   - Checks all stocks 120+ days old
   - Creates issue if false negatives found

5. **Backtest** (as needed):
   - Go to "GEM Screener v6.0 - Backtest"
   - Enter test dates
   - Optionally optimize weights

## Directory Structure

```
GEM_Trading_System/
├── Daily_Screens/          # Daily screening results
├── Backtest_Results/       # Backtest reports
├── Tracking_Data/          # Master tracking file
├── Tracking_Reports/       # Performance reports
├── Screening_Universe/     # Stock lists
├── gem_screener_v6.py      # Main screener
├── gem_backtest_v6.py      # Backtester
└── gem_tracker_v6.py       # Tracker
```

## Workflows

- **Daily Screen**: Runs screener on stock universe
- **Track & Validate**: Updates positions and checks outcomes
- **Backtest**: Tests screener on historical data
- **Setup**: Initializes repository (run once)

## Alerts

The system will create GitHub issues when:
- Strong buy signals detected (score 100+)
- False negatives discovered (rejected stocks that exploded)

## Based on Verified Data

All patterns and weights derived from:
- 694 verified explosive stocks
- 2014-2024 data (excluding COVID)
- Minimum 500% gain in 6 months
- Verified via Polygon API
