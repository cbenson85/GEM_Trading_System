# COVID-Era Exclusion Rule

**Established**: 2025-11-01
**Status**: Active - Applied to all pattern discovery and screener development

---

## 📋 The Rule

**EXCLUDE from pattern analysis:**
- Any explosive stock where entry date is between **2020-01-01** and **2021-12-31**
- Any explosive stock where catalyst/peak date is between **2020-01-01** and **2021-12-31**

**USE for pattern analysis:**
- Pre-COVID: 2014-2019 (6 years of normal market conditions)
- Post-COVID: 2022-2024 (3 years of normalized market)

---

## 🎯 Why This Rule Exists

### Unprecedented Market Conditions (2020-2021)

The 2020-2021 period had unique, non-repeatable factors:

1. **Massive Stimulus**
   - $5+ trillion in government spending
   - Direct checks to citizens
   - PPP loans
   - Enhanced unemployment

2. **Zero Interest Rates**
   - Fed funds rate at 0%
   - Free money era
   - Asset inflation across all markets

3. **Meme Stock Mania**
   - GME, AMC, BB short squeezes
   - Retail coordination via WSB
   - Options-driven gamma squeezes
   - Not fundamental-driven

4. **COVID-Specific Plays**
   - Vaccine rush (MRNA, BNTX, NVAX)
   - Stay-at-home boom (ZM, DOCU, PTON)
   - Won't repeat without pandemic

5. **Retail Trading Explosion**
   - Robinhood era
   - Commission-free trading boom
   - Stimulus checks into stocks
   - YOLO culture

6. **Everything Bubble**
   - SPACs exploding
   - Crypto mania
   - NFT boom
   - Irrational exuberance

---

## ❌ What We're Avoiding

By excluding 2020-2021, we avoid building a screener that looks for:
- Patterns that only worked with stimulus
- Patterns that only worked at zero rates
- Meme stock characteristics
- Pandemic-specific plays
- Bubble-era momentum

**These won't repeat in normal markets.**

---

## ✅ What We're Building

By using 2014-2019 and 2022-2024, we build a screener that finds:
- Patterns that work in normal interest rate environments
- Fundamental catalyst-driven moves
- Repeatable setups
- Patterns that worked before AND after the anomaly
- Sustainable strategies

**These will work going forward.**

---

## 📊 Data Treatment

### Clean Dataset (For Analysis):
```
2014: ✅ Include
2015: ✅ Include
2016: ✅ Include
2017: ✅ Include
2018: ✅ Include
2019: ✅ Include
2020: ❌ EXCLUDE (COVID era)
2021: ❌ EXCLUDE (COVID era)
2022: ✅ Include
2023: ✅ Include
2024: ✅ Include

Total: ~9 years of NORMAL market data
```

### COVID-Era Dataset (Archived):
```
2020: 📋 Archive (reference only)
2021: 📋 Archive (reference only)

Kept for:
- Historical reference
- Understanding what NOT to rely on
- Curiosity about anomaly period

NOT used for:
- Pattern discovery
- Screener development
- Backtesting
```

---

## 🔬 Scientific Reasoning

This is similar to excluding:
- 2008 financial crisis from housing models
- Dot-com bubble from tech valuations
- 1929 crash from normal market behavior

**We want patterns that work in NORMAL conditions, not once-in-a-century events.**

---

## 🛠️ Implementation

### Automatic Filtering:
When scan results arrive, `filter_covid_era.py` automatically:
1. Loads `explosive_stocks_catalog.json`
2. Separates stocks by date
3. Creates two datasets:
   - `explosive_stocks_CLEAN.json` (for analysis)
   - `explosive_stocks_COVID_ERA.json` (archived)
4. Generates filtering report
5. Proceeds with clean dataset only

### Manual Override:
If you ever want to analyze COVID-era stocks:
- They're preserved in `explosive_stocks_COVID_ERA.json`
- Clearly marked with `covid_era: true` flag
- Can study separately from main system

---

## 📈 Expected Impact

### On Pattern Discovery:
- More reliable patterns (work in normal conditions)
- Higher confidence in correlations
- Repeatable findings

### On Backtesting:
- Test on 2014-2019 (pre-COVID)
- Test on 2022-2024 (post-COVID)
- Skip 2020-2021 (anomaly period)
- Validate screener works across normal cycles

### On Live Trading:
- System designed for normal markets
- Won't chase pandemic-era anomalies
- Sustainable long-term approach

---

## 🔄 Reviewing This Rule

This rule should be reviewed if:
- Market conditions fundamentally change again
- New unprecedented events occur
- We discover COVID-era patterns that ARE repeatable

**But for now: EXCLUDE 2020-2021, ALWAYS.**

---

## 📝 Summary

**Problem**: 2020-2021 had unprecedented, non-repeatable conditions

**Solution**: Exclude from pattern discovery, use only normal market periods

**Result**: Build screener based on sustainable, repeatable patterns

**Implementation**: Automatic filtering via `filter_covid_era.py`

---

**This rule protects us from building a system based on once-in-a-century anomalies.**

We want a screener that works in 2025, 2026, 2027... not one that only worked during a pandemic with free money.

---

**Rule Status**: ACTIVE and ENFORCED
**Review Date**: Only if market fundamentals change dramatically
**Override**: Manual only, with documented reasoning
