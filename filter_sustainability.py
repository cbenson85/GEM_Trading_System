#!/usr/bin/env python3
"""
GEM Trading System - Sustained Gain Window Filter V3.0
Version: 3.0
Created: 2025-11-02

PURPOSE:
Test stocks for SUSTAINED gains over realistic trading windows.
This filters out pump & dumps while keeping stocks with clear selling windows.

KEY INSIGHT:
We don't hold stocks forever. Test within realistic 120-day trading window.
Fast movers must hold gains longer to prove they're not pumps.

TRADING WINDOW: 120 Days from Catalyst Entry
- Day 0: Entry (catalyst starts)
- Day 0-120: Our trading window
- Peak: Use actual peak OR day 120 (whichever comes first)
- Test: 30 days after peak (realistic selling window)

METHODOLOGY:
1. Find the explosive window (entry point identified in CLEAN.json)
2. Track stock for up to 150 days (120 trading + 30 observation)
3. Peak = actual peak within 120 days OR day 120 price (cap it)
4. Test 30 days after peak
5. Calculate MINIMUM gain maintained during entire test period
6. Speed-adjusted thresholds:
   - Fast gains (<30 days): Must hold 250%+ minimum (pumps fail here)
   - Medium gains (30-90 days): Must hold 200%+ minimum  
   - Slow gains (90-120 days): Must hold 150%+ minimum

This identifies stocks with:
✅ Fundamental strength (sustained elevation)
✅ Clear selling windows (30 days to exit)
✅ Realistic holding periods (120 days max)

INPUT: explosive_stocks_CLEAN.json (master stock list - NEVER modified by enrichment)
OUTPUT:
  - explosive_stocks_CLEAN.json (UPDATED - sustainable stocks only)
  - explosive_stocks_UNSUSTAINABLE.json (pump & dumps)
  - sustained_gain_summary.json (statistics + position management insights)
"""

import json
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

# Polygon API Configuration
POLYGON_API_KEY = "pvv6DNmKAoxojCc0B5HOaji6I_k1egv0"
POLYGON_BASE_URL = "https://api.polygon.io/v2"

# File paths
DATA_DIR = "Verified_Backtest_Data"
INPUT_FILE = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
OUTPUT_SUSTAINABLE = f"{DATA_DIR}/explosive_stocks_SUSTAINABLE.json"
OUTPUT_UNSUSTAINABLE = f"{DATA_DIR}/explosive_stocks_UNSUSTAINABLE.json"
SUMMARY_FILE = f"{DATA_DIR}/sustained_gain_summary.json"

# Sustained gain criteria (minimum % gain that must be maintained)
FAST_GAIN_THRESHOLD = 2.50    # <30 days: must hold 250%+ minimum
MEDIUM_GAIN_THRESHOLD = 2.00  # 30-90 days: must hold 200%+ minimum
SLOW_GAIN_THRESHOLD = 1.50    # 90+ days: must hold 150%+ minimum

# Test period: track for 30 days after peak (realistic selling window)
TEST_DAYS_AFTER_PEAK = 30


def get_daily_prices(ticker, start_date, end_date, api_key):
    """
    Get daily price data for a ticker within date range
    Returns: list of {date, open, high, low, close, volume}
    """
    url = f"{POLYGON_BASE_URL}/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {"apiKey": api_key, "adjusted": "true", "sort": "asc", "limit": 50000}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 429:
            print(f"  ⚠️  Rate limited, waiting 5 seconds...")
            time.sleep(5)
            return get_daily_prices(ticker, start_date, end_date, api_key)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('resultsCount', 0) > 0 and 'results' in data:
                prices = []
                for bar in data['results']:
                    prices.append({
                        'date': datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d'),
                        'open': bar['o'],
                        'high': bar['h'],
                        'low': bar['l'],
                        'close': bar['c'],
                        'volume': bar['v']
                    })
                return prices
        
        return []
        
    except Exception as e:
        print(f"  ❌ Error fetching prices for {ticker}: {e}")
        return []


def find_explosive_window(ticker, year, target_gain_pct, api_key):
    """
    Find the 180-day window with the target gain percentage
    Returns: {
        'entry_date': date,
        'entry_price': price,
        'peak_date': date,
        'peak_price': price,
        'days_to_peak': int,
        'gain_percent': float
    }
    """
    # Get all daily prices for the year (plus buffer)
    start_date = f"{year - 1}-07-01"
    end_date = f"{year + 1}-06-30"
    
    print(f"  📊 Fetching price data for {ticker} ({start_date} to {end_date})...")
    prices = get_daily_prices(ticker, start_date, end_date, api_key)
    
    if len(prices) < 180:
        print(f"  ⚠️  Insufficient data: only {len(prices)} days")
        return None
    
    print(f"  ✅ Got {len(prices)} days of price data")
    
    # Find 180-day windows with target gain
    best_window = None
    max_gain = 0
    
    print(f"  🔍 Scanning for 180-day windows with {target_gain_pct}%+ gain...")
    
    for i in range(len(prices) - 180):
        window_prices = prices[i:i+180]
        entry_price = window_prices[0]['close']
        
        # Find peak within window
        peak_idx = 0
        peak_price = entry_price
        
        for j, day in enumerate(window_prices):
            if day['high'] > peak_price:
                peak_price = day['high']
                peak_idx = j
        
        gain_pct = ((peak_price - entry_price) / entry_price) * 100
        
        # Check if this window matches target gain
        if gain_pct >= target_gain_pct * 0.9:  # 10% tolerance
            if gain_pct > max_gain:
                max_gain = gain_pct
                best_window = {
                    'entry_date': window_prices[0]['date'],
                    'entry_price': entry_price,
                    'peak_date': window_prices[peak_idx]['date'],
                    'peak_price': peak_price,
                    'days_to_peak': peak_idx,
                    'gain_percent': gain_pct
                }
    
    if best_window:
        print(f"  ✅ Found window: {best_window['entry_date']} → {best_window['peak_date']}")
        print(f"     Entry: ${best_window['entry_price']:.2f}, Peak: ${best_window['peak_price']:.2f}")
        print(f"     Gain: {best_window['gain_percent']:.1f}%, Days: {best_window['days_to_peak']}")
    else:
        print(f"  ❌ No window found with {target_gain_pct}%+ gain")
    
    return best_window


def test_sustained_gain(stock, api_key):
    """
    Test if stock maintained significant gains over extended period
    Returns: dict with test results
    """
    ticker = stock.get('ticker')
    year = stock.get('year', stock.get('year_discovered'))
    gain_percent = stock.get('gain_percent')
    
    if not all([ticker, year, gain_percent]):
        return {
            'sustainable': False,
            'reason': 'Missing required data (ticker, year, or gain_percent)',
            'test_data': None
        }
    
    print(f"\n{'='*70}")
    print(f"Testing {ticker} ({year}) - Target: {gain_percent}% gain")
    print(f"{'='*70}")
    
    # Check if stock already has enriched data
    if 'entry_date' in stock and 'entry_price' in stock and 'peak_price' in stock:
        print(f"  ℹ️  Using existing enriched data")
        entry_date = stock['entry_date']
        entry_price = stock['entry_price']
        peak_date = stock.get('catalyst_date') or stock.get('peak_date') or entry_date
        peak_price = stock['peak_price']
        days_to_peak = stock.get('days_to_peak', 0)
    else:
        # Find explosive window using Polygon
        window = find_explosive_window(ticker, year, gain_percent, api_key)
        
        if not window:
            return {
                'sustainable': False,
                'reason': 'Could not find explosive window in Polygon data',
                'test_data': None
            }
        
        entry_date = window['entry_date']
        entry_price = window['entry_price']
        peak_date = window['peak_date']
        peak_price = window['peak_price']
        days_to_peak = window['days_to_peak']
    
    # Calculate test period
    # Our trading window: Entry → 120 days max
    # Peak: Use actual peak OR day 120 (whichever comes first)
    # Test: 30 days after peak
    
    entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
    peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
    
    # Cap peak at 120 days from entry
    max_peak_dt = entry_dt + timedelta(days=120)
    if peak_dt > max_peak_dt:
        print(f"  ⚠️  Peak at day {(peak_dt - entry_dt).days} exceeds 120-day window")
        print(f"     Using day 120 as effective peak for testing")
        peak_dt = max_peak_dt
        peak_date = peak_dt.strftime('%Y-%m-%d')
        
        # Get price at day 120
        prices_at_120 = get_daily_prices(ticker, peak_date, peak_date, api_key)
        if prices_at_120:
            peak_price = prices_at_120[0]['close']
            print(f"     Day 120 price: ${peak_price:.2f}")
        else:
            return {
                'sustainable': False,
                'reason': 'Could not fetch day 120 price data',
                'test_data': None
            }
    
    # Test date: 30 days after peak
    test_end_dt = peak_dt + timedelta(days=TEST_DAYS_AFTER_PEAK)
    
    # Check if test date is in the future (too recent to test)
    if test_end_dt > datetime.now():
        days_until_testable = (test_end_dt - datetime.now()).days
        return {
            'sustainable': None,
            'reason': f'Stock too recent - need {days_until_testable} more days of data',
            'test_data': {
                'entry_date': entry_date,
                'entry_price': entry_price,
                'peak_date': peak_date,
                'peak_price': peak_price,
                'days_to_peak': days_to_peak,
                'test_date': test_end_dt.strftime('%Y-%m-%d'),
                'note': 'Cannot test yet - waiting for 30 days post-peak data'
            }
        }
    
    print(f"  📅 Test period: {entry_date} → {test_end_dt.strftime('%Y-%m-%d')}")
    print(f"     (Entry → Peak+{TEST_DAYS_AFTER_PEAK} days, max 150 days total)")
    
    # Get all prices during test period
    prices = get_daily_prices(
        ticker,
        entry_date,
        test_end_dt.strftime('%Y-%m-%d'),
        api_key
    )
    
    if not prices or len(prices) < 10:
        return {
            'sustainable': False,
            'reason': f'Insufficient price data during test period (only {len(prices)} days)',
            'test_data': {
                'entry_date': entry_date,
                'entry_price': entry_price,
                'peak_date': peak_date,
                'peak_price': peak_price,
                'days_to_peak': days_to_peak
            }
        }
    
    print(f"  ✅ Got {len(prices)} days of price data for test period")
    
    # Calculate gain for each day
    gains = []
    min_gain = float('inf')
    min_gain_date = None
    max_gain = 0
    max_gain_date = None
    
    for price_bar in prices:
        daily_gain = (price_bar['close'] - entry_price) / entry_price
        gains.append({
            'date': price_bar['date'],
            'price': price_bar['close'],
            'gain': daily_gain,
            'gain_pct': daily_gain * 100
        })
        
        if daily_gain < min_gain:
            min_gain = daily_gain
            min_gain_date = price_bar['date']
            min_gain_price = price_bar['close']
        
        if daily_gain > max_gain:
            max_gain = daily_gain
            max_gain_date = price_bar['date']
    
    min_gain_pct = min_gain * 100
    max_gain_pct = max_gain * 100
    
    # Determine speed category and threshold
    if days_to_peak < 30:
        speed_category = 'FAST'
        threshold = FAST_GAIN_THRESHOLD
        threshold_pct = threshold * 100
    elif days_to_peak < 90:
        speed_category = 'MEDIUM'
        threshold = MEDIUM_GAIN_THRESHOLD
        threshold_pct = threshold * 100
    else:
        speed_category = 'SLOW'
        threshold = SLOW_GAIN_THRESHOLD
        threshold_pct = threshold * 100
    
    # Test sustainability
    sustainable = min_gain >= threshold
    
    print(f"\n  📊 SUSTAINED GAIN ANALYSIS:")
    print(f"     Speed Category: {speed_category} ({days_to_peak} days to peak)")
    print(f"     Required Minimum: {threshold_pct:.0f}% sustained gain")
    print(f"     ")
    print(f"     Peak Gain: {max_gain_pct:.1f}% on {max_gain_date}")
    print(f"     Minimum Gain: {min_gain_pct:.1f}% on {min_gain_date}")
    print(f"     Price at minimum: ${min_gain_price:.2f}")
    print(f"     ")
    print(f"     Result: {'✅ SUSTAINABLE' if sustainable else '❌ UNSUSTAINABLE'}")
    
    if not sustainable:
        print(f"     Reason: Only held {min_gain_pct:.1f}% minimum (need {threshold_pct:.0f}%+)")
    else:
        print(f"     Stock maintained >{threshold_pct:.0f}% gain throughout period!")
    
    # Position management insights
    drawdown_from_peak = ((min_gain_price - peak_price) / peak_price) * 100
    
    return {
        'sustainable': sustainable,
        'reason': 'Sustainable' if sustainable else f'Only held {min_gain_pct:.1f}% minimum (need {threshold_pct:.0f}%+)',
        'test_data': {
            'entry_date': entry_date,
            'entry_price': entry_price,
            'peak_date': peak_date,
            'peak_price': peak_price,
            'days_to_peak': days_to_peak,
            'speed_category': speed_category,
            'threshold_required_pct': threshold_pct,
            'max_gain_pct': round(max_gain_pct, 2),
            'max_gain_date': max_gain_date,
            'min_gain_pct': round(min_gain_pct, 2),
            'min_gain_date': min_gain_date,
            'min_gain_price': round(min_gain_price, 2),
            'drawdown_from_peak_pct': round(drawdown_from_peak, 2),
            'test_period_days': len(prices),
            'position_management': {
                'stop_loss_reference': f"{min_gain_pct:.1f}% from entry",
                'max_drawdown_observed': f"{abs(drawdown_from_peak):.1f}% from peak",
                'holding_period_tested': f"{len(prices)} days"
            }
        }
    }


def run_filter():
    """Main filter execution"""
    print("\n" + "="*70)
    print("🔬 GEM SUSTAINED GAIN WINDOW FILTER V3.0")
    print("="*70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Criteria: Sustained minimum gain over extended period")
    print(f"   - FAST gains (<30d): {FAST_GAIN_THRESHOLD*100:.0f}%+ sustained")
    print(f"   - MEDIUM gains (30-90d): {MEDIUM_GAIN_THRESHOLD*100:.0f}%+ sustained")
    print(f"   - SLOW gains (90+d): {SLOW_GAIN_THRESHOLD*100:.0f}%+ sustained")
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
    
    print(f"✅ Loaded {len(all_stocks)} stocks from CLEAN.json")
    print(f"ℹ️  CLEAN.json will NOT be modified (master stock list)")
    print(f"ℹ️  Results will be saved to separate SUSTAINABLE.json file\n")
    
    # Load existing unsustainable (for merge logic)
    existing_unsustainable = []
    if Path(OUTPUT_UNSUSTAINABLE).exists():
        with open(OUTPUT_UNSUSTAINABLE, 'r') as f:
            unsust_data = json.load(f)
            existing_unsustainable = unsust_data if isinstance(unsust_data, list) else unsust_data.get('stocks', [])
        print(f"📊 Found {len(existing_unsustainable)} existing unsustainable stocks\n")
    
    # Test each stock
    sustainable = []
    unsustainable = list(existing_unsustainable)
    
    stats = {
        'total_stocks': len(all_stocks),
        'tested': 0,
        'sustainable': 0,
        'unsustainable': 0,
        'by_speed': {
            'FAST': {'total': 0, 'sustainable': 0},
            'MEDIUM': {'total': 0, 'sustainable': 0},
            'SLOW': {'total': 0, 'sustainable': 0}
        },
        'errors': 0
    }
    
    for i, stock in enumerate(all_stocks, 1):
        ticker = stock.get('ticker')
        year = stock.get('year', stock.get('year_discovered'))
        
        print(f"\n[{i}/{len(all_stocks)}] {ticker} ({year})")
        
        result = test_sustained_gain(stock, POLYGON_API_KEY)
        
        # Add test results to stock
        stock_with_test = stock.copy()
        stock_with_test['sustained_gain_test'] = {
            'sustainable': result['sustainable'],
            'reason': result['reason'],
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'filter_version': '3.0',
            'test_method': 'Sustained Gain Window (entry to peak+60 days)'
        }
        
        if result['test_data']:
            stock_with_test['sustained_gain_test'].update(result['test_data'])
            
            # Update speed category stats
            speed = result['test_data'].get('speed_category', 'UNKNOWN')
            if speed in stats['by_speed']:
                stats['by_speed'][speed]['total'] += 1
        
        if result['sustainable']:
            sustainable.append(stock_with_test)
            stats['sustainable'] += 1
            
            if result['test_data'] and result['test_data'].get('speed_category') in stats['by_speed']:
                stats['by_speed'][result['test_data']['speed_category']]['sustainable'] += 1
        else:
            unsustainable.append(stock_with_test)
            stats['unsustainable'] += 1
        
        stats['tested'] += 1
        
        # Small delay to be polite to API
        time.sleep(0.1)
    
    # Save results
    print("\n" + "="*70)
    print("💾 SAVING RESULTS")
    print("="*70)
    
    # Save sustainable stocks to SEPARATE file (DO NOT modify CLEAN.json)
    with open(OUTPUT_SUSTAINABLE, 'w') as f:
        json.dump(sustainable, f, indent=2)
    print(f"✅ Saved SUSTAINABLE.json: {len(sustainable)} stocks")
    print(f"ℹ️  CLEAN.json unchanged (master list preserved)")
    
    # Save unsustainable
    with open(OUTPUT_UNSUSTAINABLE, 'w') as f:
        json.dump(unsustainable, f, indent=2)
    print(f"✅ Saved UNSUSTAINABLE.json: {len(unsustainable)} stocks")
    
    # Calculate additional stats
    for speed in ['FAST', 'MEDIUM', 'SLOW']:
        total = stats['by_speed'][speed]['total']
        sust = stats['by_speed'][speed]['sustainable']
        stats['by_speed'][speed]['sustainability_rate'] = f"{(sust/total*100):.1f}%" if total > 0 else "0%"
    
    # Save summary
    stats['filter_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stats['filter_version'] = '3.0'
    stats['test_method'] = 'Sustained Gain Window'
    stats['criteria'] = {
        'FAST': f"{FAST_GAIN_THRESHOLD*100:.0f}%+ sustained (<30 days to peak)",
        'MEDIUM': f"{MEDIUM_GAIN_THRESHOLD*100:.0f}%+ sustained (30-90 days to peak)",
        'SLOW': f"{SLOW_GAIN_THRESHOLD*100:.0f}%+ sustained (90+ days to peak)"
    }
    
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Saved summary\n")
    
    # Final summary
    print("="*70)
    print("📊 SUSTAINED GAIN FILTER COMPLETE")
    print("="*70)
    print(f"Total Stocks: {stats['total_stocks']}")
    print(f"Tested: {stats['tested']}")
    print(f"✅ Sustainable: {stats['sustainable']} ({stats['sustainable']/stats['total_stocks']*100:.1f}%)")
    print(f"❌ Unsustainable: {stats['unsustainable']} ({stats['unsustainable']/stats['total_stocks']*100:.1f}%)")
    print(f"\nBy Speed Category:")
    for speed in ['FAST', 'MEDIUM', 'SLOW']:
        total = stats['by_speed'][speed]['total']
        sust = stats['by_speed'][speed]['sustainable']
        rate = stats['by_speed'][speed]['sustainability_rate']
        print(f"  {speed:8} : {sust}/{total} sustainable ({rate})")
    print("="*70)


if __name__ == "__main__":
    run_filter()
