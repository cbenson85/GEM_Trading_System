#!/usr/bin/env python3
"""
Sustainability Filter V4.0 - Total Days Above 200%
Tests if stocks provided sufficient exit window (14+ days above 200% gain)
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Configuration
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
MIN_DAYS_ABOVE_200 = 14  # Minimum days above 200% to be sustainable
THRESHOLD_GAIN_PERCENT = 200  # 200% gain = 3x entry price
DATA_DIR = 'Verified_Backtest_Data'

def fetch_price_data(ticker: str, start_date: str, end_date: str = None) -> List[Dict]:
    """Fetch daily price data from Polygon API"""
    
    # Calculate end date (180 days after start if not specified)
    if not end_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = start_dt + timedelta(days=180)
        end_date = end_dt.strftime('%Y-%m-%d')
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {
        'apiKey': POLYGON_API_KEY,
        'adjusted': 'true',
        'sort': 'asc',
        'limit': 5000
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK' and data.get('results'):
                return data['results']
    except Exception as e:
        print(f"  ⚠️ API error for {ticker}: {str(e)}")
    
    return []

def test_sustainability(stock: Dict) -> Tuple[bool, Dict]:
    """
    Test if stock stayed above 200% gain for minimum days
    Returns: (is_sustainable, stats_dict)
    """
    
    ticker = stock['ticker']
    entry_date = stock.get('entry_date')
    entry_price = stock.get('entry_price')
    
    if not entry_date or not entry_price:
        return False, {"error": "Missing entry data"}
    
    # Fetch price data for 180 days after entry
    price_data = fetch_price_data(ticker, entry_date)
    
    if not price_data:
        return False, {"error": "No price data available"}
    
    # Calculate threshold price (200% gain = 3x entry)
    threshold_price = entry_price * 3.0
    
    # Count days above threshold
    days_above_threshold = 0
    max_gain_seen = 0
    first_threshold_day = None
    last_threshold_day = None
    
    for i, bar in enumerate(price_data):
        # Use high price of the day for checking if it went above threshold
        high_price = bar.get('h', 0)
        close_price = bar.get('c', 0)
        
        # Track maximum gain
        if high_price > 0:
            gain_pct = ((high_price - entry_price) / entry_price) * 100
            max_gain_seen = max(max_gain_seen, gain_pct)
        
        # Check if price stayed above threshold
        if close_price >= threshold_price:
            days_above_threshold += 1
            if first_threshold_day is None:
                first_threshold_day = i + 1
            last_threshold_day = i + 1
    
    # Determine if sustainable
    is_sustainable = days_above_threshold >= MIN_DAYS_ABOVE_200
    
    # Build stats
    stats = {
        "days_above_200pct": days_above_threshold,
        "max_gain_percent": round(max_gain_seen, 1),
        "first_day_above": first_threshold_day,
        "last_day_above": last_threshold_day,
        "threshold_price": round(threshold_price, 2),
        "is_sustainable": is_sustainable,
        "total_days_checked": len(price_data)
    }
    
    return is_sustainable, stats

def main():
    print("\n" + "="*60)
    print("🔬 SUSTAINABILITY FILTER V4.0")
    print("Testing: Total Days Above 200% Gain")
    print("="*60 + "\n")
    
    # Load current CLEAN data
    clean_file = os.path.join(DATA_DIR, 'explosive_stocks_CLEAN.json')
    
    if not os.path.exists(clean_file):
        print(f"❌ Error: {clean_file} not found!")
        sys.exit(1)
    
    with open(clean_file, 'r') as f:
        data = json.load(f)
    
    # Handle both nested and flat JSON structures
    if isinstance(data, dict) and 'stocks' in data:
        stocks = data['stocks']
        metadata = {k: v for k, v in data.items() if k != 'stocks'}
    else:
        stocks = data if isinstance(data, list) else []
        metadata = {}
    
    print(f"📊 Loaded {len(stocks)} stocks from CLEAN.json\n")
    print(f"Criteria: Stocks must stay above 200% gain for {MIN_DAYS_ABOVE_200}+ days")
    print(f"Testing each stock for realistic exit window...\n")
    print("-" * 60)
    
    # Process each stock
    sustainable_stocks = []
    unsustainable_stocks = []
    untestable_stocks = []
    api_calls = 0
    
    for i, stock in enumerate(stocks, 1):
        ticker = stock['ticker']
        year = stock.get('year_discovered', 'Unknown')
        gain = stock.get('gain_percent', 0)
        
        print(f"\n[{i}/{len(stocks)}] Testing {ticker} ({year}) - {gain:.0f}% gain")
        
        is_sustainable, stats = test_sustainability(stock)
        api_calls += 1
        
        # Add stats to stock data
        stock['sustainability_stats'] = stats
        
        if 'error' in stats:
            print(f"  ⚠️ Cannot test: {stats['error']}")
            untestable_stocks.append(stock)
        elif is_sustainable:
            print(f"  ✅ SUSTAINABLE: {stats['days_above_200pct']} days above 200% (max: {stats['max_gain_percent']:.0f}%)")
            sustainable_stocks.append(stock)
        else:
            print(f"  ❌ PUMP & DUMP: Only {stats['days_above_200pct']} days above 200%")
            unsustainable_stocks.append(stock)
    
    print("\n" + "="*60)
    print("📊 FILTER RESULTS")
    print("="*60 + "\n")
    
    total_tested = len(sustainable_stocks) + len(unsustainable_stocks)
    
    print(f"Total Stocks: {len(stocks)}")
    print(f"Sustainable: {len(sustainable_stocks)} ({len(sustainable_stocks)/len(stocks)*100:.1f}%)")
    print(f"Pump & Dumps: {len(unsustainable_stocks)} ({len(unsustainable_stocks)/len(stocks)*100:.1f}%)")
    print(f"Untestable: {len(untestable_stocks)} ({len(untestable_stocks)/len(stocks)*100:.1f}%)")
    
    if total_tested > 0:
        print(f"\nOf testable stocks:")
        print(f"  Pass Rate: {len(sustainable_stocks)/total_tested*100:.1f}%")
        print(f"  Fail Rate: {len(unsustainable_stocks)/total_tested*100:.1f}%")
    
    print(f"\nAPI Calls Made: {api_calls}")
    
    # Save sustainable stocks (update CLEAN.json)
    clean_output = {
        **metadata,
        'stocks': sustainable_stocks,
        'filter_info': {
            'last_filtered': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filter_version': 'V4.0',
            'method': 'Total Days Above 200%',
            'min_days_required': MIN_DAYS_ABOVE_200,
            'threshold_gain_percent': THRESHOLD_GAIN_PERCENT,
            'total_stocks': len(stocks),
            'sustainable': len(sustainable_stocks),
            'unsustainable': len(unsustainable_stocks),
            'untestable': len(untestable_stocks)
        }
    }
    
    with open(clean_file, 'w') as f:
        json.dump(clean_output, f, indent=2)
    print(f"\n✅ Updated {clean_file}")
    
    # Save unsustainable stocks
    unsustainable_file = os.path.join(DATA_DIR, 'explosive_stocks_UNSUSTAINABLE.json')
    unsustainable_output = {
        **metadata,
        'stocks': unsustainable_stocks,
        'filter_info': {
            'last_filtered': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filter_version': 'V4.0',
            'description': 'Pump & dump stocks that failed sustainability test',
            'criteria': f'Less than {MIN_DAYS_ABOVE_200} days above 200% gain'
        }
    }
    
    with open(unsustainable_file, 'w') as f:
        json.dump(unsustainable_output, f, indent=2)
    print(f"✅ Created {unsustainable_file}")
    
    # Save summary statistics
    summary_file = os.path.join(DATA_DIR, 'sustainability_summary.json')
    summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'filter_version': 'V4.0',
        'filter_method': 'Total Days Above 200% Threshold',
        'min_days_required': MIN_DAYS_ABOVE_200,
        'threshold_gain_pct': THRESHOLD_GAIN_PERCENT,
        'total_stocks': len(stocks),
        'sustainable': len(sustainable_stocks),
        'unsustainable': len(unsustainable_stocks),
        'not_tested': len(untestable_stocks),
        'api_calls': api_calls,
        'pass_rate': round(len(sustainable_stocks)/total_tested*100, 1) if total_tested > 0 else 0,
        'key_findings': {
            'sustainable_stocks_have': '14+ days above 200% gain to exit',
            'pump_dumps_have': 'Less than 14 days above 200% before crashing',
            'exit_window': 'Minimum 2 weeks to notice and exit position'
        }
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Created {summary_file}")
    
    print("\n" + "="*60)
    print("✅ SUSTAINABILITY FILTER COMPLETE")
    print("="*60)
    print(f"\n🎯 Ready for Phase 3 pattern analysis with {len(sustainable_stocks)} sustainable stocks!\n")

if __name__ == "__main__":
    main()
