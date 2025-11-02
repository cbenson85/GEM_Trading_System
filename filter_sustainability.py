#!/usr/bin/env python3
"""
GEM Trading System - Sustainability Filter (Proper Version)
Version: 2.0
Created: 2025-11-02

PURPOSE:
Test stocks from CLEAN.json for sustainability using Polygon API.
Only test stocks already in CLEAN.json - do NOT scan all stocks.

SUSTAINABILITY CRITERIA:
- Stock must hold ≥80% of peak gain 21 days after peak
- This filters out pump & dumps and untradeable flukes

PROCESS:
1. Read stock list from CLEAN.json (200 stocks)
2. For each stock:
   - Use Polygon API to scan that stock's year
   - Find the 180-day window with 500%+ gain (catalyst window)
   - Get catalyst start date (entry date)
   - Get peak price within window
   - Get test price 21 days after peak
   - Calculate retention: (test_price - entry_price) / (peak_price - entry_price)
3. If retention >= 80%: Keep in CLEAN.json
4. If retention < 80%: Move to UNSUSTAINABLE.json

INPUT: explosive_stocks_CLEAN.json (200 stocks from master list)
OUTPUT:
  - explosive_stocks_CLEAN.json (updated - sustainable stocks only)
  - explosive_stocks_UNSUSTAINABLE.json (pump & dumps)
  - sustainability_summary.json (statistics)
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
OUTPUT_UNSUSTAINABLE = f"{DATA_DIR}/explosive_stocks_UNSUSTAINABLE.json"
SUMMARY_FILE = f"{DATA_DIR}/sustainability_summary.json"

# Sustainability criteria
RETENTION_THRESHOLD = 0.80  # 80% of peak gain must be retained
TEST_DAYS_AFTER_PEAK = 21   # Test 21 days after peak


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
                # Convert timestamps to dates
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
    # Get all daily prices for the year (plus buffer for windows)
    start_date = f"{year - 1}-07-01"  # Start 6 months before to catch windows
    end_date = f"{year + 1}-06-30"     # End 6 months after
    
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
        if gain_pct >= target_gain_pct * 0.9:  # Allow 10% tolerance
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


def get_test_price(ticker, peak_date, test_days, api_key):
    """
    Get stock price X days after peak
    Returns: price or None
    """
    peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
    test_date = peak_dt + timedelta(days=test_days)
    
    # Fetch price data around test date (buffer for weekends/holidays)
    buffer_start = (test_date - timedelta(days=5)).strftime('%Y-%m-%d')
    buffer_end = (test_date + timedelta(days=5)).strftime('%Y-%m-%d')
    
    prices = get_daily_prices(ticker, buffer_start, buffer_end, api_key)
    
    if not prices:
        return None
    
    # Find closest date to test date
    test_date_str = test_date.strftime('%Y-%m-%d')
    
    for day in prices:
        if day['date'] >= test_date_str:
            return day['close']
    
    # If no exact match, use last available price
    return prices[-1]['close'] if prices else None


def test_sustainability(stock, api_key):
    """
    Test if stock meets sustainability criteria
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
        peak_date = stock.get('catalyst_date', entry_date)
        peak_price = stock['peak_price']
        
        # Still need to get test price
        test_price = get_test_price(ticker, peak_date, TEST_DAYS_AFTER_PEAK, api_key)
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
        
        # Get test price
        print(f"  📅 Getting price {TEST_DAYS_AFTER_PEAK} days after peak...")
        test_price = get_test_price(ticker, peak_date, TEST_DAYS_AFTER_PEAK, api_key)
    
    if not test_price:
        return {
            'sustainable': False,
            'reason': f'Could not fetch price {TEST_DAYS_AFTER_PEAK} days after peak',
            'test_data': {
                'entry_date': entry_date,
                'entry_price': entry_price,
                'peak_date': peak_date,
                'peak_price': peak_price,
                'test_date': None,
                'test_price': None
            }
        }
    
    # Calculate retention
    peak_gain = peak_price - entry_price
    test_gain = test_price - entry_price
    retention = test_gain / peak_gain if peak_gain > 0 else 0
    
    test_dt = datetime.strptime(peak_date, '%Y-%m-%d') + timedelta(days=TEST_DAYS_AFTER_PEAK)
    
    sustainable = retention >= RETENTION_THRESHOLD
    
    print(f"\n  📊 RESULTS:")
    print(f"     Entry: ${entry_price:.2f} on {entry_date}")
    print(f"     Peak:  ${peak_price:.2f} on {peak_date}")
    print(f"     Test:  ${test_price:.2f} on {test_dt.strftime('%Y-%m-%d')} ({TEST_DAYS_AFTER_PEAK} days later)")
    print(f"     Retention: {retention*100:.1f}%")
    print(f"     Result: {'✅ SUSTAINABLE' if sustainable else '❌ UNSUSTAINABLE'}")
    
    return {
        'sustainable': sustainable,
        'reason': 'Sustainable' if sustainable else f'Only retained {retention*100:.1f}% of gain (need {RETENTION_THRESHOLD*100}%)',
        'test_data': {
            'entry_date': entry_date,
            'entry_price': entry_price,
            'peak_date': peak_date,
            'peak_price': peak_price,
            'test_date': test_dt.strftime('%Y-%m-%d'),
            'test_price': test_price,
            'retention_percent': round(retention * 100, 2),
            'threshold_percent': RETENTION_THRESHOLD * 100
        }
    }


def run_filter():
    """Main filter execution"""
    print("\n" + "="*70)
    print("🔬 GEM SUSTAINABILITY FILTER V2.0")
    print("="*70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Criteria: {RETENTION_THRESHOLD*100}% retention {TEST_DAYS_AFTER_PEAK} days after peak")
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
    print(f"ℹ️  These are the ONLY stocks we'll test\n")
    
    # Load existing unsustainable (for merge logic)
    existing_unsustainable = []
    if Path(OUTPUT_UNSUSTAINABLE).exists():
        with open(OUTPUT_UNSUSTAINABLE, 'r') as f:
            existing_unsustainable = json.load(f)
        print(f"📊 Found {len(existing_unsustainable)} existing unsustainable stocks\n")
    
    # Test each stock
    sustainable = []
    unsustainable = list(existing_unsustainable)
    stats = {
        'total_stocks': len(all_stocks),
        'tested': 0,
        'sustainable': 0,
        'unsustainable': 0,
        'skipped': 0,
        'errors': 0
    }
    
    for i, stock in enumerate(all_stocks, 1):
        ticker = stock.get('ticker')
        year = stock.get('year', stock.get('year_discovered'))
        
        print(f"\n[{i}/{len(all_stocks)}] {ticker} ({year})")
        
        result = test_sustainability(stock, POLYGON_API_KEY)
        
        # Add test results to stock
        stock_with_test = stock.copy()
        stock_with_test['sustainability_test'] = {
            'sustainable': result['sustainable'],
            'reason': result['reason'],
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'criteria': f"{RETENTION_THRESHOLD*100}% retention {TEST_DAYS_AFTER_PEAK} days after peak"
        }
        
        if result['test_data']:
            stock_with_test['sustainability_test'].update(result['test_data'])
        
        if result['sustainable']:
            sustainable.append(stock_with_test)
            stats['sustainable'] += 1
        else:
            unsustainable.append(stock_with_test)
            stats['unsustainable'] += 1
        
        stats['tested'] += 1
        
        # No rate limiting needed - Developer tier has unlimited requests
        # Just a small delay to avoid overwhelming the API
        time.sleep(0.1)  # 100ms between stocks
    
    # Save results
    print("\n" + "="*70)
    print("💾 SAVING RESULTS")
    print("="*70)
    
    # Update CLEAN.json with only sustainable stocks
    if file_structure:
        clean_output = file_structure.copy()
        clean_output['stocks'] = sustainable
    else:
        clean_output = sustainable
    
    with open(INPUT_FILE, 'w') as f:
        json.dump(clean_output, f, indent=2)
    print(f"✅ Updated CLEAN.json: {len(sustainable)} sustainable stocks")
    
    # Save unsustainable
    with open(OUTPUT_UNSUSTAINABLE, 'w') as f:
        json.dump(unsustainable, f, indent=2)
    print(f"✅ Saved UNSUSTAINABLE.json: {len(unsustainable)} stocks")
    
    # Save summary
    stats['filter_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stats['criteria'] = f"{RETENTION_THRESHOLD*100}% retention {TEST_DAYS_AFTER_PEAK} days after peak"
    
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Saved summary\n")
    
    # Final summary
    print("="*70)
    print("📊 SUSTAINABILITY FILTER COMPLETE")
    print("="*70)
    print(f"Total Stocks: {stats['total_stocks']}")
    print(f"Tested: {stats['tested']}")
    print(f"✅ Sustainable: {stats['sustainable']} ({stats['sustainable']/stats['total_stocks']*100:.1f}%)")
    print(f"❌ Unsustainable: {stats['unsustainable']} ({stats['unsustainable']/stats['total_stocks']*100:.1f}%)")
    print("="*70)


if __name__ == "__main__":
    run_filter()
