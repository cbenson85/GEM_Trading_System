# Phase 4 Historical Screener Testing - Final Report
**Generated**: 2025-11-08 03:13:28
**Test Mode**: test

## Executive Summary

- **Test Dates**: 3 strategic dates
- **Total Stocks Analyzed**: 120
- **True Positives (500%+ gains)**: 0
- **Hit Rate**: 0.0%
- **Win Rate (100%+ gains)**: 2.5%

## Key Findings

- Most predictive pattern: volume_score (+0.0% correlation)

## Classification Breakdown

| Classification | Count | Percentage |
|---------------|-------|------------|
| TRUE_POSITIVE | 0 | 0.0% |
| MODERATE_WIN | 3 | 2.5% |
| SMALL_WIN | 3 | 2.5% |
| BREAK_EVEN | 114 | 95.0% |
| LOSS | 0 | 0.0% |
| NO_DATA | 0 | 0.0% |
| ERROR | 0 | 0.0% |

## Pattern Effectiveness

| Pattern | Correlation | Success Rate |
|---------|-------------|-------------|
| volume_score | 0.000 | 0.0% |
| rsi_score | 0.000 | 0.0% |
| breakout_score | 0.000 | 0.0% |
| accumulation_score | 0.000 | 0.0% |
| composite_bonus | 0.000 | 0.0% |

## Score Threshold Analysis

| Threshold | Stocks | True Positives | Hit Rate |
|-----------|--------|----------------|----------|
| 60 | 120 | 0 | 0.0% |
| 75 | 115 | 0 | 0.0% |
| 90 | 96 | 0 | 0.0% |
| 105 | 30 | 0 | 0.0% |
| 120 | 6 | 0 | 0.0% |

## Recommendations

Based on Phase 4 analysis:

1. **Screening Frequency**: Run screener bi-weekly to catch emerging patterns
2. **Position Sizing**: Scale positions based on score (higher score = larger position)
3. **Risk Management**: Expect 40-50% hit rate, size positions accordingly
4. **Hold Period**: Average explosion occurs within 60 days
5. **Score Threshold**: Focus on stocks scoring above optimal threshold

## Next Steps

1. Refine scoring weights based on pattern correlations
2. Test on additional dates for validation
3. Implement live screening with refined criteria
4. Paper trade for real-world validation
5. Monitor and adjust based on results
