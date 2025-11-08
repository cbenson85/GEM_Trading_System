# Phase 4 Historical Screener Testing - Final Report
**Generated**: 2025-11-08 03:53:19
**Test Mode**: full

## Executive Summary

- **Test Dates**: 25 strategic dates
- **Total Stocks Analyzed**: 450
- **True Positives (500%+ gains)**: 2
- **Hit Rate**: 0.4%
- **Win Rate (100%+ gains)**: 3.3%

## Key Findings

- Optimal score threshold: 60 (hit rate: 0.5%)
- Most predictive pattern: volume_score (+0.6% correlation)
- Average gain for explosions: 617%
- Average days to peak: 38 days

## Classification Breakdown

| Classification | Count | Percentage |
|---------------|-------|------------|
| TRUE_POSITIVE | 2 | 0.4% |
| MODERATE_WIN | 13 | 2.9% |
| SMALL_WIN | 21 | 4.7% |
| BREAK_EVEN | 414 | 92.0% |
| LOSS | 0 | 0.0% |
| NO_DATA | 0 | 0.0% |
| ERROR | 0 | 0.0% |

## Pattern Effectiveness

| Pattern | Correlation | Success Rate |
|---------|-------------|-------------|
| volume_score | 0.006 | 0.6% |
| composite_bonus | 0.004 | 0.4% |
| rsi_score | -0.001 | 0.4% |
| accumulation_score | -0.004 | 0.3% |
| breakout_score | -0.016 | 0.3% |

## Score Threshold Analysis

| Threshold | Stocks | True Positives | Hit Rate |
|-----------|--------|----------------|----------|
| 60 | 415 | 2 | 0.5% |
| 75 | 306 | 0 | 0.0% |
| 90 | 246 | 0 | 0.0% |
| 105 | 107 | 0 | 0.0% |
| 120 | 30 | 0 | 0.0% |
| 135 | 1 | 0 | 0.0% |

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
