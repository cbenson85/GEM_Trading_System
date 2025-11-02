# Standard Data Format Template
**Version**: 1.0
**Created**: 2025-11-02
**Purpose**: Define uniform data structure for all 200 explosive stocks

---

## 🎯 OVERVIEW

This template defines the **exact JSON structure** that every stock analysis file must follow. By using identical structure across all 200 stocks, we enable:

- Easy cross-stock pattern scanning
- Automated correlation analysis
- Consistent data quality tracking
- Simple aggregation and comparison

**File Naming Convention**: `{TICKER}_{CATALYST_DATE}.json`
- Example: `TSLA_2020-01-03.json`
- Date format: YYYY-MM-DD

---

## 📋 COMPLETE JSON SCHEMA

```json
{
  "stock_info": {
    "ticker": "TSLA",
    "company_name": "Tesla Inc",
    "sector": "Consumer Cyclical",
    "industry": "Auto Manufacturers",
    "exchange": "NASDAQ"
  },
  
  "explosion_event": {
    "catalyst_date": "2020-01-03",
    "catalyst_type": "Earnings Beat + Product Launch Announcement",
    "catalyst_description": "Q4 2019 earnings beat estimates, Cybertruck pre-orders exceeded expectations",
    "entry_date": "2019-07-07",
    "entry_price": 45.90,
    "peak_date": "2021-01-03",
    "peak_price": 386.95,
    "gain_percent": 743.4,
    "days_to_peak": 365,
    "speed_category": "slow_burn",
    "year_discovered": 2020,
    "all_explosive_windows": 47
  },
  
  "pre_catalyst_window": {
    "start_date": "2019-07-07",
    "end_date": "2020-01-02",
    "total_days": 180,
    "trading_days": 126,
    "note": "Analysis window is 180 calendar days before catalyst"
  },
  
  "price_volume_data": {
    "daily": [
      {
        "date": "2019-07-07",
        "days_before_catalyst": 180,
        "open": 45.20,
        "high": 46.10,
        "low": 44.80,
        "close": 45.90,
        "volume": 8234567,
        "vwap": 45.50,
        "transactions": 12543,
        "volume_weighted_avg_price": 45.50
      }
    ],
    "summary_statistics": {
      "avg_daily_volume": 7500000,
      "avg_price": 52.30,
      "volatility": 3.2,
      "price_range_low": 42.10,
      "price_range_high": 68.50,
      "total_return_pct": 32.5
    }
  },
  
  "technical_indicators": {
    "daily": [
      {
        "date": "2019-07-07",
        "days_before_catalyst": 180,
        "rsi_14": 52.3,
        "macd": -0.15,
        "macd_signal": -0.10,
        "macd_histogram": -0.05,
        "bb_upper": 48.20,
        "bb_middle": 45.50,
        "bb_lower": 42.80,
        "bb_position": 0.62,
        "bb_width": 11.9,
        "atr_14": 2.15,
        "obv": 125000000,
        "mfi_14": 58.4,
        "adx_14": 25.3,
        "stoch_k": 68.2,
        "stoch_d": 65.1
      }
    ],
    "notable_events": [
      {
        "date": "2019-09-15",
        "days_before_catalyst": 110,
        "event_type": "RSI Breakout",
        "description": "RSI crossed above 60 after 3 weeks below 50"
      },
      {
        "date": "2019-11-01",
        "days_before_catalyst": 63,
        "event_type": "MACD Crossover",
        "description": "Bullish MACD crossover - signal line crossed above MACD"
      }
    ]
  },
  
  "relative_metrics": {
    "daily": [
      {
        "date": "2019-07-07",
        "days_before_catalyst": 180,
        "volume_vs_avg_20d": 1.2,
        "volume_vs_avg_50d": 1.1,
        "price_vs_sma_20": 1.03,
        "price_vs_sma_50": 0.98,
        "price_vs_sma_200": 0.92,
        "price_vs_ema_12": 1.01,
        "price_vs_ema_26": 0.99
      }
    ],
    "trends": {
      "d180_to_d120": {
        "price_trend": "consolidating",
        "volume_trend": "declining",
        "avg_volume_ratio": 0.95
      },
      "d120_to_d60": {
        "price_trend": "uptrending",
        "volume_trend": "increasing",
        "avg_volume_ratio": 1.15
      },
      "d60_to_d1": {
        "price_trend": "accelerating",
        "volume_trend": "surging",
        "avg_volume_ratio": 1.45
      }
    }
  },
  
  "sector_market_context": {
    "daily": [
      {
        "date": "2019-07-07",
        "days_before_catalyst": 180,
        "spy_close": 298.45,
        "spy_volume": 45000000,
        "sector_etf_ticker": "XLY",
        "sector_etf_close": 156.78,
        "sector_etf_volume": 8500000,
        "relative_strength_spy": 1.05,
        "relative_strength_sector": 1.02,
        "beta_20d": 1.35,
        "correlation_spy_20d": 0.72
      }
    ],
    "market_regime": {
      "overall": "bull_market",
      "volatility": "low",
      "vix_avg": 14.5,
      "note": "Low volatility bull market during pre-catalyst window"
    }
  },
  
  "catalyst_intelligence": {
    "known_catalysts": [
      {
        "announcement_date": "2019-12-15",
        "days_before_explosion": 19,
        "catalyst_type": "Product Launch",
        "catalyst_description": "Cybertruck unveiling event",
        "source": "Company Press Release",
        "market_reaction_1d_pct": 5.2,
        "market_reaction_5d_pct": 12.3,
        "volume_spike": 2.8
      }
    ],
    "sec_filings": [
      {
        "filing_date": "2019-11-20",
        "days_before_explosion": 44,
        "filing_type": "10-Q",
        "filing_url": "https://sec.gov/...",
        "key_metrics": {
          "revenue_usd": 6350000000,
          "revenue_growth_yoy_pct": 18.5,
          "eps": 0.15,
          "eps_surprise": 0.08,
          "guidance_raised": true
        },
        "notable_items": [
          "Beat revenue estimates by 3.2%",
          "Raised FY guidance"
        ]
      },
      {
        "filing_date": "2019-10-01",
        "days_before_explosion": 94,
        "filing_type": "8-K",
        "filing_url": "https://sec.gov/...",
        "key_items": [
          "Q3 delivery numbers announced",
          "Record production quarter"
        ]
      }
    ],
    "insider_activity": [
      {
        "transaction_date": "2019-10-15",
        "days_before_explosion": 80,
        "transaction_type": "Purchase",
        "insider_name": "Elon Musk",
        "insider_title": "CEO",
        "shares": 50000,
        "price_per_share": 45.00,
        "total_value_usd": 2250000,
        "ownership_change_pct": 0.03,
        "form_4_url": "https://sec.gov/..."
      },
      {
        "transaction_date": "2019-09-20",
        "days_before_explosion": 105,
        "transaction_type": "Purchase",
        "insider_name": "Robyn Denholm",
        "insider_title": "Chair",
        "shares": 10000,
        "price_per_share": 48.50,
        "total_value_usd": 485000,
        "ownership_change_pct": 0.01,
        "form_4_url": "https://sec.gov/..."
      }
    ],
    "catalyst_timeline": {
      "earliest_signal_date": "2019-09-20",
      "earliest_signal_type": "Insider buying",
      "days_before_explosion": 105,
      "buildup_phase_days": 105,
      "note": "Insider buying preceded public catalyst by 105 days"
    }
  },
  
  "news_sentiment": {
    "daily": [
      {
        "date": "2019-07-07",
        "days_before_catalyst": 180,
        "articles_count": 3,
        "sentiment_score": 0.35,
        "sentiment_category": "neutral_positive",
        "sentiment_distribution": {
          "positive": 2,
          "neutral": 1,
          "negative": 0
        },
        "key_topics": ["production", "sales", "earnings"],
        "major_headlines": [
          "Tesla Q2 Production Numbers Released"
        ],
        "media_sources": ["Reuters", "Bloomberg", "CNBC"]
      }
    ],
    "sentiment_trends": {
      "d180_to_d120": {
        "avg_sentiment": 0.25,
        "avg_articles_per_day": 2.3,
        "trend": "neutral",
        "momentum": "stable"
      },
      "d120_to_d60": {
        "avg_sentiment": 0.42,
        "avg_articles_per_day": 4.1,
        "trend": "improving",
        "momentum": "accelerating"
      },
      "d60_to_d1": {
        "avg_sentiment": 0.68,
        "avg_articles_per_day": 8.7,
        "trend": "very_positive",
        "momentum": "surging"
      }
    },
    "sentiment_shifts": [
      {
        "date": "2019-11-01",
        "days_before_catalyst": 63,
        "shift_type": "positive_inflection",
        "description": "Sentiment shifted from neutral to positive after profitability announcement",
        "before_avg": 0.32,
        "after_avg": 0.61,
        "significance": "high"
      }
    ],
    "media_attention": {
      "total_articles": 847,
      "articles_per_day_avg": 4.7,
      "peak_coverage_date": "2019-12-15",
      "peak_coverage_articles": 47,
      "coverage_trend": "exponential_increase"
    }
  },
  
  "social_sentiment": {
    "note": "Optional - if data available",
    "twitter_mentions": {
      "daily_avg": 1250,
      "peak_date": "2019-12-15",
      "peak_mentions": 8500,
      "sentiment_avg": 0.55
    },
    "reddit_activity": {
      "subreddits": ["wallstreetbets", "stocks", "investing"],
      "daily_mentions_avg": 35,
      "sentiment_avg": 0.48
    },
    "stocktwits_sentiment": {
      "bullish_pct_avg": 68,
      "bearish_pct_avg": 32,
      "message_volume_avg": 450
    }
  },
  
  "ownership_structure": {
    "snapshots": [
      {
        "as_of_date": "2019-09-30",
        "days_before_catalyst": 95,
        "float_shares": 150000000,
        "float_percent": 82.5,
        "shares_outstanding": 181800000,
        "institutional_ownership_pct": 45.2,
        "insider_ownership_pct": 15.3,
        "top_5_institutional_holders": [
          {
            "holder": "Vanguard Group",
            "shares": 12500000,
            "percent": 6.9
          },
          {
            "holder": "Blackrock",
            "shares": 11200000,
            "percent": 6.2
          }
        ]
      }
    ],
    "short_interest": [
      {
        "date": "2019-07-15",
        "days_before_catalyst": 172,
        "short_interest_shares": 12300000,
        "short_interest_pct": 8.2,
        "days_to_cover": 3.5,
        "change_vs_prev": -0.5
      },
      {
        "date": "2019-08-15",
        "days_before_catalyst": 141,
        "short_interest_shares": 11800000,
        "short_interest_pct": 7.9,
        "days_to_cover": 3.2,
        "change_vs_prev": -0.3
      }
    ],
    "ownership_changes": {
      "institutional_flow": {
        "d180_to_d90": {
          "net_shares_bought": 2500000,
          "net_change_pct": 1.4,
          "trend": "accumulating"
        },
        "d90_to_d1": {
          "net_shares_bought": 4200000,
          "net_change_pct": 2.3,
          "trend": "accelerating_accumulation"
        }
      },
      "insider_flow": {
        "total_insider_buys": 3,
        "total_insider_sells": 1,
        "net_shares": 65000,
        "net_value_usd": 3100000,
        "signal": "bullish"
      },
      "short_interest_trend": {
        "direction": "declining",
        "change_pct": -15.2,
        "squeeze_potential": "moderate"
      }
    }
  },
  
  "float_analysis": {
    "float_category": "medium",
    "float_shares": 150000000,
    "avg_daily_volume": 7500000,
    "days_to_trade_float": 20,
    "liquidity_score": 7.5,
    "note": "Adequate liquidity for institutional accumulation"
  },
  
  "financial_metrics": {
    "quarterly_snapshots": [
      {
        "quarter_end": "2019-09-30",
        "days_before_catalyst": 95,
        "revenue_usd": 6350000000,
        "revenue_growth_yoy_pct": 18.5,
        "revenue_growth_qoq_pct": 8.2,
        "gross_profit_usd": 1448200000,
        "gross_margin_pct": 22.8,
        "operating_income_usd": 76200000,
        "operating_margin_pct": 1.2,
        "net_income_usd": 31800000,
        "net_margin_pct": 0.5,
        "eps": 0.15,
        "eps_diluted": 0.15,
        "ebitda_usd": 950000000,
        "free_cash_flow_usd": 371000000
      }
    ],
    "balance_sheet": {
      "as_of_date": "2019-09-30",
      "days_before_catalyst": 95,
      "total_assets_usd": 34300000000,
      "total_liabilities_usd": 27200000000,
      "total_equity_usd": 7100000000,
      "cash_and_equivalents_usd": 5100000000,
      "debt_short_term_usd": 2300000000,
      "debt_long_term_usd": 11400000000,
      "total_debt_usd": 13700000000,
      "debt_to_equity": 1.93,
      "current_ratio": 1.05,
      "quick_ratio": 0.73
    },
    "key_ratios": {
      "as_of_date": "2019-09-30",
      "days_before_catalyst": 95,
      "pe_ratio": 45.2,
      "price_to_sales": 1.8,
      "price_to_book": 6.5,
      "peg_ratio": 2.1,
      "roe_pct": 2.3,
      "roa_pct": 0.9,
      "asset_turnover": 1.85
    },
    "growth_metrics": {
      "revenue_cagr_3y_pct": 48.5,
      "earnings_growth_yoy_pct": 285.0,
      "book_value_growth_yoy_pct": 12.3
    }
  },
  
  "analyst_coverage": {
    "coverage_summary": {
      "total_analysts": 23,
      "buy_ratings": 8,
      "hold_ratings": 11,
      "sell_ratings": 4,
      "avg_price_target": 58.50,
      "price_target_high": 95.00,
      "price_target_low": 32.00
    },
    "rating_changes": [
      {
        "date": "2019-11-05",
        "days_before_catalyst": 59,
        "analyst_firm": "Morgan Stanley",
        "old_rating": "Hold",
        "new_rating": "Buy",
        "old_price_target": 48.00,
        "new_price_target": 68.00,
        "reason": "Improving fundamentals and profitability"
      }
    ],
    "estimate_revisions": {
      "eps_estimates_q4": {
        "date_range": "d180_to_d1",
        "direction": "upward",
        "revision_count": 12,
        "avg_revision_pct": 8.5
      },
      "revenue_estimates_q4": {
        "date_range": "d180_to_d1",
        "direction": "upward",
        "revision_count": 9,
        "avg_revision_pct": 5.2
      }
    }
  },
  
  "options_activity": {
    "note": "Optional - if data available",
    "unusual_activity": [
      {
        "date": "2019-12-10",
        "days_before_catalyst": 24,
        "activity_type": "Unusual Call Buying",
        "strike": 55.00,
        "expiration": "2020-01-17",
        "volume": 8500,
        "open_interest": 2300,
        "volume_oi_ratio": 3.7,
        "premium_spent_usd": 425000
      }
    ],
    "put_call_ratio": {
      "d60_to_d30_avg": 0.68,
      "d30_to_d1_avg": 0.42,
      "trend": "bullish",
      "note": "Decreasing put/call ratio indicates bullish sentiment"
    }
  },
  
  "pattern_flags": {
    "volume_patterns": [
      {
        "pattern_name": "gradual_volume_increase",
        "detected": true,
        "confidence": 0.85,
        "description": "Volume increased 45% from D-180 to D-1",
        "start_date": "2019-07-07",
        "end_date": "2020-01-02"
      },
      {
        "pattern_name": "volume_spike_on_news",
        "detected": true,
        "confidence": 0.92,
        "description": "Volume spike on Cybertruck announcement",
        "date": "2019-12-15",
        "days_before_catalyst": 19
      }
    ],
    "price_patterns": [
      {
        "pattern_name": "higher_lows",
        "detected": true,
        "confidence": 0.78,
        "description": "Series of higher lows from D-120 to D-1",
        "start_date": "2019-09-05",
        "end_date": "2020-01-02"
      },
      {
        "pattern_name": "consolidation_then_breakout",
        "detected": true,
        "confidence": 0.83,
        "description": "3-month consolidation followed by breakout",
        "consolidation_start": "2019-07-07",
        "consolidation_end": "2019-10-15",
        "breakout_date": "2019-10-16"
      }
    ],
    "sentiment_patterns": [
      {
        "pattern_name": "sentiment_inflection",
        "detected": true,
        "confidence": 0.88,
        "description": "Sentiment shifted from neutral to positive",
        "inflection_date": "2019-11-01",
        "days_before_catalyst": 63
      },
      {
        "pattern_name": "media_attention_surge",
        "detected": true,
        "confidence": 0.91,
        "description": "Media coverage increased 280% in final 60 days",
        "surge_start": "2019-11-03",
        "days_before_catalyst": 61
      }
    ],
    "catalyst_patterns": [
      {
        "pattern_name": "insider_buying_precedes_catalyst",
        "detected": true,
        "confidence": 0.95,
        "description": "Insider buying 105 days before public catalyst",
        "first_buy_date": "2019-09-20",
        "days_before_catalyst": 105
      },
      {
        "pattern_name": "earnings_beat_streak",
        "detected": true,
        "confidence": 0.82,
        "description": "Beat earnings estimates 3 quarters in a row",
        "quarters": ["Q1 2019", "Q2 2019", "Q3 2019"]
      }
    ],
    "ownership_patterns": [
      {
        "pattern_name": "institutional_accumulation",
        "detected": true,
        "confidence": 0.87,
        "description": "Institutional ownership increased 3.7% during window",
        "start_ownership_pct": 41.5,
        "end_ownership_pct": 45.2
      },
      {
        "pattern_name": "short_interest_decline",
        "detected": true,
        "confidence": 0.79,
        "description": "Short interest declined 15.2% during window",
        "start_short_pct": 8.2,
        "end_short_pct": 6.9
      }
    ],
    "technical_patterns": [
      {
        "pattern_name": "rsi_breakout",
        "detected": true,
        "confidence": 0.81,
        "description": "RSI broke above 60 at D-110",
        "breakout_date": "2019-09-15",
        "days_before_catalyst": 110
      },
      {
        "pattern_name": "macd_crossover",
        "detected": true,
        "confidence": 0.84,
        "description": "Bullish MACD crossover at D-63",
        "crossover_date": "2019-11-01",
        "days_before_catalyst": 63
      }
    ],
    "financial_patterns": [
      {
        "pattern_name": "margin_expansion",
        "detected": true,
        "confidence": 0.76,
        "description": "Gross margin expanded from 19.8% to 22.8%",
        "timeframe": "6 months"
      },
      {
        "pattern_name": "cash_position_improving",
        "detected": true,
        "confidence": 0.89,
        "description": "Cash increased 42% during pre-catalyst window",
        "start_cash_usd": 3600000000,
        "end_cash_usd": 5100000000
      }
    ]
  },
  
  "red_flags": {
    "detected_red_flags": [],
    "note": "No significant red flags detected during pre-catalyst window"
  },
  
  "data_quality": {
    "completeness": {
      "price_volume_pct": 100,
      "technical_indicators_pct": 100,
      "sec_filings_pct": 100,
      "insider_trading_pct": 95,
      "news_sentiment_pct": 90,
      "ownership_data_pct": 85,
      "financial_metrics_pct": 100,
      "analyst_coverage_pct": 75,
      "options_activity_pct": 60,
      "social_sentiment_pct": 50,
      "overall_pct": 86
    },
    "data_sources": {
      "price_volume": "Polygon API",
      "sec_filings": "SEC EDGAR",
      "insider_trading": "SEC Form 4 + OpenInsider",
      "news": "Google News + Yahoo Finance",
      "ownership": "Polygon API + Finviz",
      "financials": "Polygon API + SEC",
      "analyst_data": "Yahoo Finance",
      "options": "Yahoo Finance"
    },
    "missing_data_notes": [
      "Social sentiment data incomplete (50% coverage)",
      "Options activity data limited to last 90 days",
      "Some analyst estimates unavailable for full 180-day window"
    ],
    "data_validation": {
      "price_gaps_checked": true,
      "volume_outliers_flagged": true,
      "date_alignment_verified": true,
      "calculations_spot_checked": true
    }
  },
  
  "analysis_metadata": {
    "analysis_date": "2025-11-02",
    "analysis_version": "1.0",
    "framework_version": "2.0",
    "analyst_notes": [
      "Strong insider buying preceded public catalyst by 105 days",
      "Institutional accumulation accelerated in final 90 days",
      "Sentiment inflection point at D-63 coincided with MACD crossover",
      "Multiple positive patterns converged in final 60 days"
    ],
    "confidence_score": 0.87,
    "data_quality_score": 86,
    "recommended_for_pattern_analysis": true
  }
}
```

---

## 📊 FIELD DEFINITIONS

### Speed Categories
- **ultra_fast**: < 10 days to peak
- **fast**: 10-30 days
- **moderate**: 31-90 days
- **slow_burn**: 91-180 days

### Sentiment Scores
- Range: -1.0 (very negative) to +1.0 (very positive)
- Categories:
  - very_negative: -1.0 to -0.6
  - negative: -0.6 to -0.2
  - neutral: -0.2 to +0.2
  - neutral_positive: +0.2 to +0.4
  - positive: +0.4 to +0.7
  - very_positive: +0.7 to +1.0

### Float Categories
- **micro**: < 10M shares
- **small**: 10M - 50M shares
- **medium**: 50M - 150M shares
- **large**: 150M - 500M shares
- **mega**: > 500M shares

### Pattern Confidence Scores
- Range: 0.0 to 1.0
- Interpretation:
  - 0.0 - 0.3: Low confidence
  - 0.3 - 0.6: Moderate confidence
  - 0.6 - 0.8: High confidence
  - 0.8 - 1.0: Very high confidence

---

## 🎯 DATA COLLECTION PRIORITIES

### Critical (Must Have - 100%)
- ✅ Price/volume data (daily OHLCV)
- ✅ Basic stock info (ticker, dates, gains)
- ✅ Explosion event details

### High Priority (Target 95%+)
- Technical indicators (RSI, MACD, BB, etc.)
- SEC filings (10-Q, 10-K, 8-K)
- Insider trading (Form 4)
- Relative metrics (vs moving averages)

### Medium Priority (Target 85%+)
- News sentiment (daily articles)
- Ownership structure (float, institutional)
- Short interest data
- Financial metrics (quarterly)
- Sector/market context

### Low Priority (Target 70%+)
- Analyst coverage and ratings
- Social sentiment (Twitter, Reddit, StockTwits)
- Options activity
- Detailed leadership info

---

## 🔄 HANDLING MISSING DATA

### Best Practices:

1. **Use `null` for missing values** - Never fabricate or estimate
2. **Document in data_quality section** - Note what's missing and why
3. **Flag incomplete stocks** - Mark if overall completeness < 80%
4. **Proceed anyway** - Don't exclude stocks due to missing data
5. **Pattern scanning accounts for nulls** - Correlation tools skip null values

### Example:
```json
{
  "insider_activity": null,
  "data_quality": {
    "missing_data_notes": [
      "No insider trading data available for this stock during window"
    ]
  }
}
```

---

## 📝 USAGE WORKFLOW

### For Each Stock in CLEAN.json:

1. **Create file**: `{TICKER}_{CATALYST_DATE}.json`
2. **Populate basic info**: From CLEAN.json (ticker, year, gains, etc.)
3. **Calculate window**: 180 days before catalyst_date
4. **Run collectors**: Each collector fills its section
5. **Validate**: Check data quality, flag issues
6. **Save**: To `/Verified_Backtest_Data/pre_catalyst_analysis/raw_data/`

### Data Collection Order:
1. Price/volume (foundation - everything depends on this)
2. Technical indicators (calculated from price/volume)
3. SEC filings (concrete, dated events)
4. Insider trading (concrete, dated events)
5. News/sentiment (time-consuming but valuable)
6. Ownership/float (quarterly, less frequent)
7. Financials (quarterly, structured)
8. Analyst data (optional, if time permits)
9. Options/social (nice-to-have, lowest priority)

---

## 🔍 PATTERN FLAG STRUCTURE

### How to Use Pattern Flags:

**During Initial Analysis:**
- Collectors populate data fields
- Pattern flags remain empty: `"pattern_flags": {}`

**After Manual Review:**
- Analyst reviews the data
- Identifies patterns manually
- Adds pattern flags with descriptions

**During Automated Scanning:**
- Pattern scanning scripts check for specific patterns
- Auto-populate pattern flags based on thresholds
- Calculate confidence scores

### Pattern Flag Template:
```json
{
  "pattern_name": "descriptive_name",
  "detected": true/false,
  "confidence": 0.0-1.0,
  "description": "What was observed",
  "key_dates": ["2019-10-15"],
  "key_metrics": {"metric": value}
}
```

---

## ✅ VALIDATION CHECKLIST

Before considering a stock file "complete":

- [ ] All critical fields populated (100%)
- [ ] High priority fields ≥ 95% complete
- [ ] Medium priority fields ≥ 85% complete
- [ ] Dates are accurate (no future dates)
- [ ] Price data has no unexplained gaps
- [ ] Calculations are verified (spot check)
- [ ] Missing data is documented
- [ ] Data sources are noted
- [ ] File follows exact JSON schema
- [ ] File saved with correct naming convention

---

## 🚀 NEXT STEPS

1. **Review & Approve Template** - User reviews this structure
2. **Build Data Enrichment Script** - Populate existing CLEAN.json data into this format
3. **Build Collectors** - Create scripts to fill each section
4. **Test on 2-3 Stocks** - Validate approach works
5. **Scale to All 200 Stocks** - Full dataset collection
6. **Build Pattern Scanner** - Automated pattern detection across all stocks

---

**END OF STANDARD DATA FORMAT TEMPLATE**

Version: 1.0
Created: 2025-11-02
Purpose: Uniform structure for all 200 explosive stock analyses
Framework: PRE_CATALYST_ANALYSIS_FRAMEWORK.md v2.0
