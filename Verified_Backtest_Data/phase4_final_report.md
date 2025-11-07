# Phase 4 Historical Screener Testing - Final Report
**Generated**: 2025-11-07 22:33:56
**Test Mode**: test

## Executive Summary

- **Test Dates**: 3 strategic dates
- **Total Stocks Analyzed**: 13
- **True Positives (500%+ gains)**: 8
- **Hit Rate**: 61.5%
- **Win Rate (100%+ gains)**: 69.2%

## Key Findings

- Optimal score threshold: 90 (hit rate: 70.0%)
- Most predictive pattern: volume_score (+61.5% correlation)
- Average gain for explosions: 2478%
- Average days to peak: 61 days

## Classification Breakdown

| Classification | Count | Percentage |
|---------------|-------|------------|
| TRUE_POSITIVE | 8 | 61.5% |
| MODERATE_WIN | 1 | 7.7% |
| SMALL_WIN | 0 | 0.0% |
| BREAK_EVEN | 0 | 0.0% |
| LOSS | 3 | 23.1% |
| NO_DATA | 1 | 7.7% |
| ERROR | 0 | 0.0% |

## Pattern Effectiveness

| Pattern | Correlation | Success Rate |
|---------|-------------|-------------|
| volume_score | 0.615 | 61.5% |
| breakout_score | 0.615 | 61.5% |
| composite_bonus | 0.615 | 61.5% |
| accumulation_score | 0.528 | 77.8% |
| rsi_score | -0.615 | 0.0% |

## Score Threshold Analysis

| Threshold | Stocks | True Positives | Hit Rate |
|-----------|--------|----------------|----------|
| 60 | 13 | 8 | 61.5% |
| 75 | 12 | 8 | 66.7% |
| 90 | 10 | 7 | 70.0% |
| 105 | 9 | 7 | 77.8% |
| 120 | 9 | 7 | 77.8% |
| 135 | 6 | 4 | 66.7% |
| 150 | 3 | 2 | 66.7% |

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
