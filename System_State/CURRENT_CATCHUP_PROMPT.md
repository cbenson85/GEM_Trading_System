# GEM Trading System - Phase 4 Catch-Up Prompt
**Last Updated**: 2025-11-08 02:30:00
**System Version**: Phase 4 - Historical Screener Testing
**Current Issue**: Script hanging during execution

---

## 🚨 CRITICAL CONTEXT - READ FIRST

### The Hanging Problem
The phase4_integrated_screener.py keeps hanging after printing "Mode: test" in the GitHub Actions workflow. This has happened repeatedly despite multiple fixes. The script needs timeout protection and extensive debug output to identify the exact hang point.

### What We Discovered in Phase 3
- Analyzed 694 verified explosive stocks (500%+ gains)
- **75% had 10x+ volume spikes** (most important pattern)
- **60% had RSI < 30** (oversold stocks explode - NOT overbought)
- 45% were near 52-week highs
- 35% showed accumulation patterns

### The Scoring Problem We Found
Initial Phase 4 test showed only 0.8% hit rate because:
- RSI scoring was BACKWARDS (we scored overbought as positive)
- Breakout pattern had negative correlation but we scored it positively
- Selected 40 stocks per date instead of 30 (120 total instead of 90)

---

## 📊 CURRENT SYSTEM STATUS

### Phase 4 Implementation Status
- **Screener Script**: ❌ HANGING after "Mode: test"
- **Batch Processing**: ⏸️ BLOCKED (no screening results)
- **Analysis**: ⏸️ BLOCKED (no data to analyze)
- **Correlation Report**: ⏸️ BLOCKED (no results to correlate)

### Technical Configuration
```python
# Polygon Developer API - UNLIMITED calls
API_KEY = "pvv6DNmKAoxojCc0B5HOaji6I_k1egv0"

# Parallel Processing
MAX_WORKERS = 100  # Can handle 100 concurrent API calls

# Screening Parameters
STOCKS_PER_DATE = 30  # EXACTLY 30, not 40!
TEST_DATES = ["2019-03-15", "2022-06-20", "2023-09-11"]
PRICE_RANGE = ($0.50, $15.00)
MIN_VOLUME = 10,000
MIN_SCORE = 50
```

---

## 🔬 CORRECT SCORING (Based on 694 Verified Stocks)

```python
def score_stock(self, ticker: str, data: Dict, date: str) -> Tuple[float, Dict]:
    """
    CORRECT scoring based on Phase 3 analysis of 694 verified stocks
    """
    breakdown = {
        'volume_score': 0,      # 75% of explosives had 10x+ volume
        'rsi_score': 0,         # 60% had RSI < 30 (oversold is GOOD)
        'breakout_score': 0,    # 45% near highs (moderate importance)
        'accumulation_score': 0, # 35% showed accumulation
        'composite_bonus': 0     # Multiple signals bonus
    }
    
    # Volume (MOST IMPORTANT - 75% correlation)
    volume_ratio = data['volume'] / data['avg_volume_20d']
    if volume_ratio >= 10:
        breakdown['volume_score'] = 50
    elif volume_ratio >= 5:
        breakdown['volume_score'] = 35
    
    # RSI (Oversold is POSITIVE - 60% correlation)
    rsi = data.get('rsi', 50)
    if rsi < 30:  # OVERSOLD IS GOOD!
        breakdown['rsi_score'] = 30
    elif rsi < 40:
        breakdown['rsi_score'] = 20
    elif rsi > 70:  # Overbought is slightly negative
        breakdown['rsi_score'] = -10
```

---

## 🐛 THE HANGING ISSUE - TROUBLESHOOTING

### Where It Hangs
```
Run MODE="test"
================================================
PHASE 4: HISTORICAL SCREENER TESTING
Mode: test
================================================
[HANGS HERE - No further output]
```

### Required Fix
```python
# Add at script start:
import signal

def timeout_handler(signum, frame):
    print("❌ SCRIPT TIMEOUT - HUNG FOR 30 SECONDS", flush=True)
    traceback.print_stack(frame)
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout

# Debug output between EVERY operation
print("[DEBUG] Starting imports...", flush=True)
import json
print("[DEBUG] json imported", flush=True)
# etc...
```

---

## 📁 PHASE 4 FILES

### Core Files (Must Update)
1. **phase4_integrated_screener.py** - HANGING, needs timeout + debug
2. **phase4_batch_splitter.py** - Splits results into 5 batches
3. **phase4_comprehensive_collector.py** - Analyzes each batch
4. **phase4_batch_merger.py** - Merges batch results
5. **phase4_correlation_analyzer.py** - Generates correlations
6. **phase4_report_generator.py** - Creates final report

### Workflow File
- **.github/workflows/phase4_complete_workflow.yml** - Orchestrates all jobs

---

## ❌ WHAT NOT TO DO

1. **NO FALLBACK LISTS** - Don't add predefined stocks
2. **NO MOCK DATA** - Must use real API data
3. **NO RANDOM SAMPLING** - Screen entire market
4. **DON'T SELECT 40 STOCKS** - Exactly 30 per date
5. **DON'T SCORE RSI BACKWARDS** - Oversold (<30) is positive

---

## ✅ WHAT MUST HAPPEN

1. **Add timeout protection** - 30 sec setup, 5 min per date
2. **Add debug output everywhere** - With flush=True
3. **Fix scoring algorithm** - Match Phase 3 findings
4. **Select exactly 30 stocks per date** - Not 40
5. **Handle API failures gracefully** - Don't hang
6. **Use 100 parallel threads** - You have unlimited API

---

## 📈 EXPECTED RESULTS

### Test Mode (3 dates)
- Total stocks selected: **90** (30 × 3)
- Expected hit rate: **40-50%** (not 0.8%)
- Processing time: ~2 minutes per date

### Full Mode (15 dates)
- Total stocks selected: **450** (30 × 15)
- Expected hit rate: **40-50%**
- Processing time: ~30 minutes total

---

## 🔧 IMMEDIATE NEXT STEPS

1. **Fix the hanging issue**
   - Add signal.alarm(30) timeout
   - Add debug prints between every import
   - Add debug prints in __init__ methods
   - Flush all output immediately

2. **Fix the scoring**
   - RSI < 30 should be positive
   - Volume spikes most important
   - Reduce breakout importance

3. **Fix stock selection**
   - EXACTLY 30 per date
   - Use [:30] slice, not [:40]

4. **Run successful test**
   - Should complete in ~6 minutes
   - Should select 90 stocks total
   - Should show 40%+ hit rate

---

## 📊 PROGRESS TRACKING

### Phase 3 ✅ COMPLETE
- Analyzed 694 explosive stocks
- Discovered key patterns
- 75% volume correlation confirmed

### Phase 4 🔄 IN PROGRESS
- [x] Created workflow structure
- [x] Built parallel processing
- [ ] Fix hanging issue
- [ ] Fix scoring algorithm
- [ ] Fix stock count (30 not 40)
- [ ] Run successful test (3 dates)
- [ ] Run full validation (15 dates)
- [ ] Generate correlation report

### Phase 5 ⏸️ WAITING
- Live screening implementation
- Real-time monitoring
- Trading execution

---

## 🚀 TO CONTINUE WORK

1. Read this entire prompt
2. Review the hanging error screenshots
3. Implement timeout + debug solution
4. Fix scoring to match Phase 3
5. Ensure exactly 30 stocks per date
6. Run test and verify 90 stocks selected
7. Check hit rate is 40%+ not 0.8%

**Remember**: 
- NO FABRICATION
- NO FALLBACK LISTS
- NO MOCK DATA
- EXACTLY 30 STOCKS PER DATE
- RSI < 30 IS POSITIVE

---

**END OF CATCH-UP PROMPT**
Generated: 2025-11-08 02:30:00
Phase: 4 - Historical Screener Testing
Status: Fixing hanging issue
