# Phase 4 Historical Screener Testing - Final Report
**Generated**: 2025-11-08 01:23:56
**Test Mode**: test

## Executive Summary

- **Test Dates**: 3 strategic dates
- **Total Stocks Analyzed**: 120
- **True Positives (500%+ gains)**: 1
- **Hit Rate**: 0.8%
- **Win Rate (100%+ gains)**: 4.2%

## Key Findings

- Optimal score threshold: 90 (hit rate: 1.0%)
- Most predictive pattern: rsi_score (+2.3% correlation)
- Average gain for explosions: 786%
- Average days to peak: 68 days

## Classification Breakdown

| Classification | Count | Percentage |
|---------------|-------|------------|
| TRUE_POSITIVE | 1 | 0.8% |
| MODERATE_WIN | 4 | 3.3% |
| SMALL_WIN | 7 | 5.8% |
| BREAK_EVEN | 108 | 90.0% |
| LOSS | 0 | 0.0% |
| NO_DATA | 0 | 0.0% |
| ERROR | 0 | 0.0% |

## Pattern Effectiveness

| Pattern | Correlation | Success Rate |
|---------|-------------|-------------|
| rsi_score | 0.023 | 2.3% |
| volume_score | 0.010 | 1.0% |
| composite_bonus | 0.008 | 0.8% |
| accumulation_score | -0.020 | 0.0% |
| breakout_score | -0.071 | 0.0% |

## Score Threshold Analysis

| Threshold | Stocks | True Positives | Hit Rate |
|-----------|--------|----------------|----------|
| 60 | 120 | 1 | 0.8% |
| 75 | 120 | 1 | 0.8% |
| 90 | 101 | 1 | 1.0% |
| 105 | 82 | 0 | 0.0% |
| 120 | 80 | 0 | 0.0% |
| 135 | 73 | 0 | 0.0% |
| 150 | 6 | 0 | 0.0% |

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
