# Pre-Catalyst Analysis Framework v3.0
**Updated**: 2025-11-03
**Analysis Window**: 90 Days (Updated from 180 days)
**Purpose**: Identify actionable patterns in the practical buying window

---

## Framework Overview

### Key Update: 180 → 90 Day Window

**Rationale for Change:**
1. **More Practical** - Retail traders don't position 6 months early
2. **More Actionable** - Signals closer to explosion are tradeable
3. **Less Noise** - Focus on relevant pre-catalyst period
4. **Faster Analysis** - 50% data reduction per stock
5. **Stronger Correlations** - Proximity effect increases predictive power

**Timeline Impact:**
- Phase 3B: 2-3 weeks (down from 4-6 weeks)
- Per stock: 1-1.5 hours (down from 1.5-2.5 hours)

---

## Analysis Structure

### For Each Sample Stock

**Analysis Period**: 90 days before `entry_date`

**Input Required:**
- Ticker symbol
- Entry date (from explosive_stocks_CLEAN.json)
- Peak date (for validation)
- Gain percentage (for correlation)

**Output Generated:**
- Comprehensive JSON file with 100+ metrics
- Pattern flags and scores
- Correlation analysis
- Visual charts (optional)

---

## 12 Data Categories (90-Day Lookback)

### 1. Price & Volume Patterns

**Data Points:**
- Daily OHLC for 90 days
- Volume (actual and relative to average)
- Price volatility (daily % changes)
- Gap events (overnight moves)
- Consolidation periods
- Breakout events

**Patterns to Identify:**
- Volume spikes without price movement (accumulation)
- Consolidation followed by volume increase
- Base-building patterns
- Support/resistance levels
- Range tightening

**Data Source:** Polygon API
**API Calls:** ~1 per stock (aggregates endpoint)

---

### 2. Technical Indicators

**Indicators to Calculate:**
- RSI (14-day, 30-day)
- MACD (12, 26, 9)
- Moving Averages (20, 50, 90-day SMA)
- Bollinger Bands (20-day, 2 std dev)
- Volume vs 30-day average
- OBV (On-Balance Volume)

**Patterns to Identify:**
- RSI divergence (price down, RSI up)
- MACD crossovers in advance
- Price approaching/crossing moving averages
- Volatility contraction (Bollinger squeeze)
- Volume acceleration

**Data Source:** Calculated from price data
**API Calls:** None (derived)

---

### 3. Float & Ownership ⭐ CRITICAL

**Data Points:**
- Insider transactions (SEC Form 4)
- Institutional ownership changes (13F)
- Short interest and days-to-cover
- Share dilution events
- Buyback programs

**Patterns to Identify:**
- **Insider cluster buying** (3+ insiders within 30 days)
- Insider purchases increasing in size
- New institutional positions
- Short interest reduction
- Low float with increasing ownership

**Data Source:** SEC Edgar, Finviz
**API Calls:** Manual scraping required

---

### 4. Catalyst Intelligence

**Data Points:**
- Catalyst type (FDA, earnings, merger, product launch, etc.)
- Catalyst date (if known)
- Previous similar catalysts (track record)
- Pre-announcements or leaks
- SEC 8-K filing frequency

**Patterns to Identify:**
- Binary catalysts with dates (FDA decisions)
- Increasing 8-K filings (material events)
- Conference presentations scheduled
- Patent filings or approvals
- Partnership announcements building

**Data Source:** SEC Edgar, company IR, news
**API Calls:** Manual research required

---

### 5. News & Sentiment

**Data Points:**
- News article count (90-day trend)
- Article sentiment (positive/negative/neutral)
- Social media mentions (Reddit, Twitter, StockTwits)
- Message board activity
- Options unusual activity alerts

**Patterns to Identify:**
- News acceleration (3x article count in last 30 days)
- Sentiment shift (negative → positive)
- Social media breakout (10x mentions)
- Coordinated discussions (multiple platforms)
- Options unusual activity

**Data Source:** News APIs, social scrapers
**API Calls:** Varies by platform

---

### 6. Leadership & Management

**Data Points:**
- CEO/management changes
- Executive track record
- Previous company successes
- Board additions
- Management reputation

**Patterns to Identify:**
- Experienced biotech CEO hired
- Successful track record in similar catalysts
- Notable board members added
- Management purchasing shares

**Data Source:** LinkedIn, company filings, news
**API Calls:** Manual research

---

### 7. Financial Metrics

**Data Points:**
- Cash and equivalents
- Quarterly burn rate
- Runway (months of cash)
- Revenue trends (if revenue)
- Debt levels
- Recent financing

**Patterns to Identify:**
- Sufficient cash for catalyst
- Improving cash position
- Revenue acceleration
- Debt reduction
- Strategic financing

**Data Source:** SEC 10-Q, 10-K filings
**API Calls:** Polygon financials API

---

### 8. Analyst Coverage

**Data Points:**
- Analyst initiations (90-day window)
- Upgrades/downgrades
- Price target changes
- Research report frequency
- Coverage expansion

**Patterns to Identify:**
- New analyst initiations
- Upgrade cascades
- Price target increases
- Increased coverage before catalyst
- Big firm initiations

**Data Source:** Finviz, news, research reports
**API Calls:** Manual tracking

---

### 9. Sector & Market Context

**Data Points:**
- Relative strength vs SPY (90 days)
- Relative strength vs QQQ (90 days)
- Sector performance
- Peer stock performance
- Macro environment

**Patterns to Identify:**
- Outperformance vs market
- Sector rotation into stock's industry
- Peers also moving (sector tailwind)
- Macro conditions favorable

**Data Source:** Polygon API for indices
**API Calls:** ~2 per stock

---

### 10. Red Flags & Risks

**Data Points:**
- Management turnover
- Failed previous catalysts
- Dilution history
- Lawsuits or investigations
- Warning letters (FDA)

**Patterns to Identify:**
- Absence of red flags
- Previous failures in similar catalysts
- Excessive dilution
- Regulatory issues
- Management credibility problems

**Data Source:** SEC filings, news, FDA
**API Calls:** Manual research

---

### 11. Polygon API Advanced

**Data Points:**
- Tick-level price action
- Dark pool vs lit market
- Bid-ask spread changes
- Market maker activity
- Order flow patterns

**Patterns to Identify:**
- Dark pool accumulation
- Spread tightening
- Large block trades
- Institutional footprints

**Data Source:** Polygon advanced endpoints
**API Calls:** ~5-10 per stock

---

### 12. Pattern Library

**Compare Against Known Patterns:**
- GEM v5 proven patterns
- Outbreak first-mover
- Biotech binary with date
- Platform technology shift
- Multi-catalyst stack
- Consolidation breakout
- Insider cluster buying
- Short squeeze setup

**New Patterns to Discover:**
- Social media breakout
- Institutional accumulation
- Options flow predictive
- News acceleration
- Leadership change positive
- Float reduction
- Analyst upgrade cascade
- Gamma squeeze setup
- Volatility contraction → expansion

**Data Source:** Pattern matching algorithm
**API Calls:** None (analysis)

---

## Data Collection Infrastructure

### Required Scripts

**1. polygon_data_collector.py**
```python
def collect_90_day_data(ticker, entry_date):
    """
    Fetch 90 days of OHLC + volume before entry_date
    Calculate technical indicators
    Return structured data
    """
    # Implementation here
```

**2. phase3b_analyzer.py**
```python
def analyze_stock(ticker, year, entry_date, peak_date):
    """
    Main orchestrator
    Runs all data collectors
    Aggregates results
    Generates comprehensive JSON
    """
    # Implementation here
```

**3. sec_filing_scraper.py**
```python
def get_insider_transactions(ticker, start_date, end_date):
    """
    Scrape Form 4 filings
    Parse insider buys/sells
    Identify clusters
    """
    # Implementation here
```

**4. social_sentiment_analyzer.py** (optional for pilot)
**5. options_data_collector.py** (optional for pilot)

---

## Output Format

### Per-Stock Comprehensive JSON

```json
{
  "metadata": {
    "ticker": "AENTW",
    "year": 2024,
    "entry_date": "2024-XX-XX",
    "peak_date": "2024-XX-XX",
    "gain_percent": 12398.33,
    "analysis_window": {
      "start_date": "90 days before entry",
      "end_date": "entry_date",
      "days_analyzed": 90
    }
  },
  
  "price_volume": {
    "daily_data": [ ... ],
    "volume_spikes": [ ... ],
    "consolidation_periods": [ ... ],
    "patterns_detected": [ ... ]
  },
  
  "technical_indicators": {
    "rsi": { ... },
    "macd": { ... },
    "moving_averages": { ... },
    "bollinger_bands": { ... },
    "patterns_detected": [ ... ]
  },
  
  "float_ownership": {
    "insider_transactions": [ ... ],
    "insider_cluster_detected": true/false,
    "institutional_changes": [ ... ],
    "short_interest": { ... },
    "patterns_detected": [ ... ]
  },
  
  "catalyst_intelligence": {
    "catalyst_type": "FDA approval",
    "catalyst_date": "2024-XX-XX",
    "predictability": "high/medium/low",
    "lead_time_days": XX,
    "patterns_detected": [ ... ]
  },
  
  "news_sentiment": {
    "article_counts": { ... },
    "sentiment_scores": { ... },
    "social_mentions": { ... },
    "patterns_detected": [ ... ]
  },
  
  "leadership": {
    "changes_in_window": [ ... ],
    "executive_quality": "high/medium/low",
    "patterns_detected": [ ... ]
  },
  
  "financials": {
    "cash_position": XX,
    "burn_rate": XX,
    "runway_months": XX,
    "patterns_detected": [ ... ]
  },
  
  "analyst_coverage": {
    "initiations": [ ... ],
    "upgrades": [ ... ],
    "price_targets": [ ... ],
    "patterns_detected": [ ... ]
  },
  
  "sector_context": {
    "relative_strength_spy": XX,
    "relative_strength_qqq": XX,
    "sector_performance": XX,
    "patterns_detected": [ ... ]
  },
  
  "red_flags": {
    "flags_identified": [ ... ],
    "risk_level": "low/medium/high"
  },
  
  "polygon_advanced": {
    "dark_pool_activity": { ... },
    "order_flow": { ... },
    "patterns_detected": [ ... ]
  },
  
  "pattern_library": {
    "gem_v5_matches": [ ... ],
    "new_patterns_detected": [ ... ],
    "pattern_strength": { ... }
  },
  
  "summary": {
    "total_patterns_detected": XX,
    "high_confidence_patterns": [ ... ],
    "lead_time_estimate": "XX days",
    "correlation_score": 0.XX,
    "actionability": "high/medium/low"
  }
}
```

---

## Success Criteria

### Pattern Requirements

**Must Have:**
- Correlation >0.60 with successful explosions
- Observable 7-30 days before entry
- Accessible via API or scraper
- Low false positive rate (<30%)
- Consistent across multiple stocks (3+)

**Examples of Good Patterns:**
- 3+ insider buys within 30 days before entry
- Volume spike (3x avg) with <5% price move
- Social mentions 10x in last 2 weeks
- RSI <40 with MACD bullish crossover
- 2+ analyst initiations in 60-day window

**Examples of Bad Patterns:**
- Only visible after explosion (hindsight)
- One-off (doesn't repeat)
- Requires insider knowledge
- Too late (<7 day lead time)
- High false positives (>50%)

---

## Phase 3B Timeline

### Pilot Analysis (2-3 days)
- Stocks: AENTW + ASNS
- Build infrastructure
- Validate framework
- Refine methodology

### Complete Sample (1.5-2 weeks)
- Remaining 6 stocks
- Standardize data collection
- Document patterns
- Build correlation matrix

### Deliverables (2-3 days)
- 8 comprehensive JSON files
- Pattern library documentation
- Correlation matrix
- Preliminary screening criteria

**Total**: 2-3 weeks

---

## Next Steps

1. Build polygon_data_collector.py
2. Build phase3b_analyzer.py
3. Test on AENTW (extreme outlier)
4. Validate 90-day window works
5. Scale to all 8 stocks
6. Generate correlation matrix
7. Document discovered patterns

---

**Framework Version**: 3.0  
**Last Updated**: 2025-11-03  
**Status**: Ready for Implementation  
**Key Change**: 90-day window for actionable patterns
