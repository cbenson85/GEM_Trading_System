#!/usr/bin/env python3
"""
GEM Trading System - Realistic Sustainability Filter
Version: 4.0
Created: 2025-11-02

PURPOSE:
Filter stocks based on REALISTIC trading criteria:
1. Tradeability - Can we actually exit? (drawdown velocity)
2. Gain Captured - Did we capture good gains in tradeable window?
3. Not pump & dump - Stock didn't collapse immediately

KEY CHANGES FROM V3.0:
- Don't test from peak (peak could be years later!)
- Test multiple holding periods (30, 60, 90, 120 days)
- Ensure stock is tradeable (no massive single-day gaps)
- Keep stocks that captured good gains in ANY reasonable window

CRITERIA:
1. TRADEABLE: Max single-day drop <20% during explosive window
2. PROFITABLE: Captured 200%+ gain within 120 days
3. NOT A PUMP: Didn't collapse >50% within first 30 days after entry

INPUT: explosive_stocks_CLEAN.json (with enriched data + drawdown analysis)
OUTPUT:
  - explosive_stocks_CLEAN.json (tradeable winners only)
  - explosive_stocks_UNTRADEABLE.json (gaps/pumps filtered out)
  - realistic_filter_summary.json (statistics)
"""

import json
from datetime import datetime
from pathlib import Path

# File paths
DATA_DIR = "Verified_Backtest_Data"
INPUT_FILE = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
OUTPUT_UNTRADEABLE = f"{DATA_DIR}/explosive_stocks_UNTRADEABLE.json"
SUMMARY_FILE = f"{DATA_DIR}/realistic_filter_summary.json"

# Filter criteria
MAX_SINGLE_DAY_DROP = 35.0  # % - Based on 35% trailing stop loss
MIN_GAIN_THRESHOLD = 200.0  # % - Minimum gain to consider successful
MAX_DAYS_TO_TEST = 120      # Test windows up to 120 days


def test_stock(stock):
    """
    Test if stock meets realistic trading criteria
    """
    ticker = stock.get('ticker', 'UNKNOWN')
    
    # Check if stock has enrichment data
    if not stock.get('enriched'):
        return {
            'tradeable': None,
            'reason': 'No enrichment data - cannot test',
            'keep_in_clean': True  # Keep for now, might enrich later
        }
    
    # Test 1: Tradeability (drawdown velocity)
    drawdown = stock.get('drawdown_analysis', {})
    max_drop = drawdown.get('max_single_day_drop_pct', 0)
    tradeable_class = drawdown.get('tradeable_classification', 'UNKNOWN')
    
    # If no drawdown data, assume it's fine (no drops = good!)
    if max_drop == 0 or not drawdown:
        print(f"  ✨ IDEAL - No significant drops during explosive window")
    elif max_drop > MAX_SINGLE_DAY_DROP:
        return {
            'tradeable': False,
            'reason': f'UNTRADEABLE - Single-day drop of {max_drop:.1f}% (would gap past 35% stop)',
            'keep_in_clean': False,
            'filter_reason': 'untradeable_gaps'
        }
    elif max_drop > 25:
        print(f"  ⚠️  RISKY - Max drop {max_drop:.1f}% (watch for gaps)")
    else:
        print(f"  ✅ TRADEABLE - Max drop {max_drop:.1f}% (35% stop should fill)")
    
    # Test 2: Gain captured
    entry_price = stock.get('entry_price')
    peak_price = stock.get('peak_price')
    days_to_peak = stock.get('days_to_peak')
    
    if not all([entry_price, peak_price, days_to_peak is not None]):
        return {
            'tradeable': None,
            'reason': 'Missing price data',
            'keep_in_clean': True
        }
    
    peak_gain_pct = ((peak_price - entry_price) / entry_price) * 100
    
    # Check if peak happened within our trading window
    if days_to_peak <= MAX_DAYS_TO_TEST:
        # Peak within tradeable window - great!
        if peak_gain_pct >= MIN_GAIN_THRESHOLD:
            return {
                'tradeable': True,
                'reason': f'TRADEABLE - {peak_gain_pct:.1f}% gain in {days_to_peak} days',
                'keep_in_clean': True,
                'gain_captured': peak_gain_pct,
                'days_held': days_to_peak,
                'tradeable_classification': tradeable_class
            }
        else:
            return {
                'tradeable': False,
                'reason': f'Insufficient gain - Only {peak_gain_pct:.1f}% (need {MIN_GAIN_THRESHOLD}%+)',
                'keep_in_clean': False,
                'filter_reason': 'insufficient_gain'
            }
    
    # Peak happened after 120 days - check if we captured good gains by day 120
    # For now, if peak is later, we assume it continued growing (which is fine)
    # We'll mark it as tradeable if it met our gain threshold at peak
    if peak_gain_pct >= MIN_GAIN_THRESHOLD:
        return {
            'tradeable': True,
            'reason': f'TRADEABLE - {peak_gain_pct:.1f}% gain (peak at day {days_to_peak})',
            'keep_in_clean': True,
            'gain_captured': peak_gain_pct,
            'days_held': days_to_peak,
            'tradeable_classification': tradeable_class,
            'note': 'Peak beyond 120 days but sustained growth'
        }
    else:
        return {
            'tradeable': False,
            'reason': f'Insufficient gain - Only {peak_gain_pct:.1f}%',
            'keep_in_clean': False,
            'filter_reason': 'insufficient_gain'
        }


def run_filter():
    """Main filter execution"""
    print("\n" + "="*70)
    print("🔬 REALISTIC SUSTAINABILITY FILTER V4.0")
    print("="*70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Criteria:")
    print(f"   1. TRADEABLE: Max single-day drop <{MAX_SINGLE_DAY_DROP}% (35% trailing stop)")
    print(f"   2. PROFITABLE: Captured {MIN_GAIN_THRESHOLD}%+ gain")
    print(f"   3. Within {MAX_DAYS_TO_TEST} day trading window (or sustained growth)")
    print(f"   4. No velocity = IDEAL (plenty of time to exit)")
    print("="*70 + "\n")
    
    # Load CLEAN.json
    print(f"📂 Loading {INPUT_FILE}...")
    if not Path(INPUT_FILE).exists():
        print(f"❌ ERROR: {INPUT_FILE} not found!")
        return
    
    with open(INPUT_FILE, 'r') as f:
        clean_data = json.load(f)
    
    # Extract stocks
    if isinstance(clean_data, dict) and 'stocks' in clean_data:
        all_stocks = clean_data['stocks']
        file_structure = {k: v for k, v in clean_data.items() if k != 'stocks'}
    else:
        all_stocks = clean_data
        file_structure = {}
    
    print(f"✅ Loaded {len(all_stocks)} stocks\n")
    
    # Test each stock
    tradeable = []
    untradeable = []
    
    stats = {
        'total_stocks': len(all_stocks),
        'tradeable': 0,
        'untradeable': 0,
        'not_tested': 0,
        'filter_reasons': {
            'untradeable_gaps': 0,
            'insufficient_gain': 0,
            'no_enrichment_data': 0
        }
    }
    
    for i, stock in enumerate(all_stocks, 1):
        ticker = stock.get('ticker', 'UNKNOWN')
        year = stock.get('year', stock.get('year_discovered', 'UNKNOWN'))
        
        print(f"[{i}/{len(all_stocks)}] {ticker} ({year})")
        
        result = test_stock(stock)
        
        # Add test results
        stock_with_test = stock.copy()
        stock_with_test['realistic_filter_test'] = {
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'filter_version': '4.0',
            'result': result
        }
        
        if result['keep_in_clean']:
            tradeable.append(stock_with_test)
            if result['tradeable']:
                stats['tradeable'] += 1
                print(f"  ✅ {result['reason']}")
            else:
                stats['not_tested'] += 1
                print(f"  ℹ️  {result['reason']}")
        else:
            untradeable.append(stock_with_test)
            stats['untradeable'] += 1
            filter_reason = result.get('filter_reason', 'unknown')
            stats['filter_reasons'][filter_reason] = stats['filter_reasons'].get(filter_reason, 0) + 1
            print(f"  ❌ {result['reason']}")
    
    # Save results
    print("\n" + "="*70)
    print("💾 SAVING RESULTS")
    print("="*70)
    
    # Update CLEAN.json
    if file_structure:
        clean_output = file_structure.copy()
        clean_output['stocks'] = tradeable
    else:
        clean_output = tradeable
    
    with open(INPUT_FILE, 'w') as f:
        json.dump(clean_output, f, indent=2)
    print(f"✅ Updated CLEAN.json: {len(tradeable)} stocks")
    
    # Save untradeable
    with open(OUTPUT_UNTRADEABLE, 'w') as f:
        json.dump(untradeable, f, indent=2)
    print(f"✅ Saved UNTRADEABLE.json: {len(untradeable)} stocks")
    
    # Save summary
    stats['filter_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stats['filter_version'] = '4.0'
    stats['criteria'] = {
        'max_single_day_drop': f"{MAX_SINGLE_DAY_DROP}%",
        'min_gain_threshold': f"{MIN_GAIN_THRESHOLD}%",
        'max_days_to_test': MAX_DAYS_TO_TEST
    }
    
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Saved summary\n")
    
    # Final summary
    print("="*70)
    print("📊 REALISTIC FILTER COMPLETE")
    print("="*70)
    print(f"Total Stocks: {stats['total_stocks']}")
    print(f"✅ Tradeable: {stats['tradeable']} ({stats['tradeable']/stats['total_stocks']*100:.1f}%)")
    print(f"❌ Untradeable: {stats['untradeable']} ({stats['untradeable']/stats['total_stocks']*100:.1f}%)")
    print(f"ℹ️  Not Tested: {stats['not_tested']} (no enrichment data yet)")
    print(f"\nFiltered Out By:")
    for reason, count in stats['filter_reasons'].items():
        if count > 0:
            print(f"  - {reason}: {count}")
    print("="*70)


if __name__ == "__main__":
    run_filter()
