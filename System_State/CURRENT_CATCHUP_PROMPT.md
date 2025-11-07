📋 GEM Trading System - System Update & Catchup Prompt
Current Date: November 7, 2024
System Status: Phase 4 - Historical Screener Testing

🎯 Project Overview
Building a screener to identify stocks BEFORE they explode (500%+ gains) using patterns discovered from 694 verified explosive stocks.

📊 Completed Phases
Phase 1-2: Infrastructure & Data Collection ✅

10-year scan identified 244 explosive stocks
Filtered to 170 clean stocks (excluding COVID 2020-2021)
All data verified via Polygon API

Phase 3: Pattern Analysis ✅

Analyzed all 694 stocks (sustainable only)
Critical Discovery: Patterns are common but not predictive of magnitude

Volume 3x spike: 91% frequency (0.029 correlation)
RSI oversold: 84% frequency (-0.046 correlation)
Patterns identify "will explode" but NOT "how much"


Gain Distribution:

80.5% gain 500-1000% (moderate winners)
15.3% gain 1000-2000% (big winners)
4.2% gain 2000%+ (mega winners)




🚀 Current Phase 4: Historical Screener Testing
Objective
Test if screener can identify explosive stocks BEFORE catalyst, achieving hit rates that exceed market returns.
Testing Framework

72 test dates across 3 years (2019, 2022, 2023)
Every 2 weeks: Jan 1, Jan 15, Feb 1, Feb 15, etc.
For each screening run:

Get top 30 stocks
Look back 60 days (false miss check)
Look forward 120 days (explosion check)



Classification System

True Positive: In top 30, exploded within 120 days
False Positive: In top 30, didn't explode
False Negative: Not in top 30 but exploded
False Miss: Discarded but would've been caught earlier (NOTE ONLY, don't count)

False Miss Principle
If stock is above threshold today but was below threshold in past 60 days, it's a false miss - note it but don't adjust screener metrics either way.
Success Criteria

Initial target: 40-50% hit rate
Must exceed historical market returns when combined with investment strategy
Will iterate until achieving acceptable performance


📈 Screener Design Principles
Scoring System
Score indicates explosion probability (NOT magnitude):

90-100: Very high confidence
75-89: High confidence
60-74: Medium confidence
<60: Pass

Pattern Weights (from Phase 3 data)

Volume 10x spike: 50 points
Volume 5x spike: 35 points
Volume 3x spike: 25 points
RSI < 30: 30 points
RSI < 35: 20 points
Accumulation: 40 points
Composite bonuses: 25-50 points

Filters

Price: $0.50 - $7.00 (extend to $15 for strong signals)
Volume: >10,000 daily average
Float: <100M shares


🎯 Next Steps (Phase 4)
Step 1: Build Historical Testing Program
Create program that:

Loads 694 verified stocks
Runs screener on 72 historical dates
Checks 60 days back (false miss)
Checks 120 days forward (explosion)
Outputs classification results

Step 2: Run Initial 72-Date Test

Execute on 2019, 2022, 2023 data
Compile results
Calculate hit rates

Step 3: Develop Investment Strategy (After initial results)
Based on hit rates and patterns:

Position sizing by score
Entry/exit rules
Portfolio management
Risk controls

Step 4: Iterate

Refine based on false positives/negatives
Adjust weights if needed
Re-test until hit rate acceptable

Step 5: Forward Test

Test on 2024 data (unknown)
Validate patterns hold
Paper trade before live


💾 Key Data Files
Verified Data

phase3_correlation_matrix.json - Pattern frequencies
phase3_merged_analysis.json - All 694 stocks analyzed
explosive_stocks_CLEAN.json - 170 clean stocks for testing

Lessons Learned

Failed_Patterns_Lessons_Learned.md - What doesn't work
False_Miss_Discovery.md - Importance of timing


⚠️ Critical Reminders

We're NOT predicting magnitude - Just identifying explosions (500%+)
False misses don't count against screener - But note them for context
Need regular screening - Stocks can catalyst anytime in 120-day window
Investment strategy comes AFTER data - Let results guide position sizing
Goal is beating market returns - Not perfect prediction


📊 Expected Outcomes
Based on Phase 3 analysis:

Should catch 40-50% of explosions if run bi-weekly
Most will be 500-1000% gainers (80%)
Small chance of mega winners (4%)
Combined with proper investment strategy, should significantly exceed market returns


❓ Decisions Pending

Minimum acceptable hit rate - To be determined after initial 72-date test
Position sizing strategy - Based on score tiers from test results
Screening frequency - Bi-weekly suggested, confirm with data
Risk management - Stop losses, position limits, etc.


🚀 Ready to Build
With this framework agreed upon, ready to build the historical testing program that will:

Test screener on 72 dates
Apply false miss principle
Calculate true hit rates
Output data for investment strategy development

Next Action: Build the historical screener testing program

Use this prompt to quickly catch up any new Claude instance or continue work after conversation limits.
