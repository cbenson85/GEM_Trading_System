#!/usr/bin/env python3
"""
GEM Trading System - Sustainability Filter
Version: 1.0
Created: 2025-11-02

PURPOSE:
Filter explosive stocks based on 30-day sustainability test.
Only keep stocks that held ≥90% of peak gain for 30 days after peak.

SUSTAINABILITY CRITERIA:
- Stock must reach 500%+ gain (already filtered)
- Stock must hold ≥90% of peak gain 30 days later
- This filters out: pump & dumps, untradeable flukes, thin stocks

INPUT: explosive_stocks_CLEAN.json (200 stocks)
OUTPUT: 
  - explosive_stocks_SUSTAINABLE.json (tradeable stocks)
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

# File paths - use Verified_Backtest_Data directory
DATA_DIR = "Verified_Backtest_Data"
INPUT_FILE = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
OUTPUT_UNSUSTAINABLE = f"{DATA_DIR}/explosive_stocks_UNSUSTAINABLE.json"
SUMMARY_FILE = f"{DATA_DIR}/sustainability_summary.json"

# Sustainability threshold (90% of peak gain must be retained after 30 days)
SUSTAINABILITY_THRESHOLD = 0.90


def load_existing_file(filepath):
    """Load existing file if it exists, return empty list if not"""
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return []


def get_price_on_date(ticker, target_date, api_key):
    """
    Get stock price on or near a specific date using Polygon API
    Returns: price (float) or None if not available
    """
    # Format date for API (YYYY-MM-DD)
    date_str = target_date.strftime('%Y-%m-%d')
    
    # Try to get data for the specific date
    # Use aggregates endpoint with 1-day range
    url = f"{POLYGON_BASE_URL}/aggs/ticker/{ticker}/range/1/day/{date_str}/{date_str}"
    params = {"apiKey": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        # Handle rate limiting
        if response.status_code == 429:
            print(f"  ⚠️  Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return get_price_on_date(ticker, target_date, api_key)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('resultsCount', 0) > 0 and 'results' in data:
                # Get closing price
                return data['results'][0]['c']
        
        # If exact date not available, try previous 5 days (market might have been closed)
        for days_back in range(1, 6):
            alt_date = target_date - timedelta(days=days_back)
            alt_date_str = alt_date.strftime('%Y-%m-%d')
            
            url = f"{POLYGON_BASE_URL}/aggs/ticker/{ticker}/range/1/day/{alt_date_str}/{alt_date_str}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('resultsCount', 0) > 0 and 'results' in data:
                    print(f"  📅 Used date {alt_date_str} (market closed on {date_str})")
                    return data['results'][0]['c']
        
        return None
        
    except Exception as e:
        print(f"  ❌ Error fetching price for {ticker}: {e}")
        return None


def parse_date(date_str):
    """Parse date string to datetime object"""
    if not date_str or date_str == "Unknown":
        return None
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


def calculate_sustainability(stock, api_key):
    """
    Test if stock held ≥90% of peak gain for 30 days
    
    Returns: dict with sustainability test results
    """
    ticker = stock['ticker']
    
    # Parse catalyst/peak date
    catalyst_date = parse_date(stock.get('catalyst_date'))
    if not catalyst_date:
        # Try to extract from other fields if available
        if 'entry_date' in stock and 'days_to_peak' in stock:
            entry_date = parse_date(stock['entry_date'])
            if entry_date:
                catalyst_date = entry_date + timedelta(days=stock['days_to_peak'])
    
    if not catalyst_date:
        return {
            'sustainable': False,
            'reason': 'No catalyst date available',
            'test_price': None,
            'retention_percent': None
        }
    
    # Calculate test date (30 days after peak)
    test_date = catalyst_date + timedelta(days=30)
    
    # Don't test stocks where test date is in the future
    if test_date > datetime.now():
        return {
            'sustainable': False,
            'reason': 'Test date in future (too recent)',
            'test_price': None,
            'retention_percent': None
        }
    
    # Get entry and peak prices
    entry_price = stock.get('entry_price')
    peak_price = stock.get('peak_price')
    
    if not entry_price or not peak_price:
        return {
            'sustainable': False,
            'reason': 'Missing entry/peak price data',
            'test_price': None,
            'retention_percent': None
        }
    
    # Fetch price 30 days after peak
    print(f"  🔍 Testing {ticker} - Peak: {catalyst_date.strftime('%Y-%m-%d')}, Test: {test_date.strftime('%Y-%m-%d')}")
    test_price = get_price_on_date(ticker, test_date, api_key)
    
    if not test_price:
        return {
            'sustainable': False,
            'reason': 'Could not fetch test date price',
            'test_price': None,
            'retention_percent': None
        }
    
    # Calculate retention percentage
    # Retention = (test_price - entry_price) / (peak_price - entry_price)
    peak_gain = peak_price - entry_price
    test_gain = test_price - entry_price
    retention = test_gain / peak_gain if peak_gain > 0 else 0
    
    # Check if stock meets sustainability threshold
    sustainable = retention >= SUSTAINABILITY_THRESHOLD
    
    return {
        'sustainable': sustainable,
        'reason': 'Sustainable' if sustainable else f'Only retained {retention*100:.1f}% of gain',
        'test_price': test_price,
        'test_date': test_date.strftime('%Y-%m-%d'),
        'retention_percent': round(retention * 100, 2),
        'peak_gain_percent': stock.get('gain_percent'),
        'entry_price': entry_price,
        'peak_price': peak_price
    }


def filter_sustainability(input_file, output_unsustainable, summary_file):
    """
    Main filter function - test all stocks for sustainability
    Uses merge logic to preserve existing results
    Automatically removes unsustainable stocks from CLEAN.json
    """
    print("\n" + "="*70)
    print("🔬 GEM SUSTAINABILITY FILTER")
    print("="*70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Threshold: {SUSTAINABILITY_THRESHOLD*100}% gain retention after 30 days")
    print("="*70 + "\n")
    
    # Load input data
    print(f"📂 Loading input file: {input_file}")
    if not Path(input_file).exists():
        print(f"❌ ERROR: {input_file} not found!")
        return
    
    with open(input_file, 'r') as f:
        all_stocks = json.load(f)
    
    print(f"✅ Loaded {len(all_stocks)} stocks from {input_file}\n")
    print(f"🔄 This filter will automatically update {input_file}")
    print(f"   - SUSTAINABLE stocks stay in {input_file}")
    print(f"   - UNSUSTAINABLE stocks moved to {output_unsustainable}\n")
    
    # Load existing results (merge logic)
    # Note: Sustainable stocks are in input_file (CLEAN.json)
    # On first run, all_stocks ARE the sustainable candidates
    # On subsequent runs, we need to merge with existing unsustainable
    existing_unsustainable = load_existing_file(output_unsustainable)
    
    print(f"📊 Existing Results:")
    print(f"   - Sustainable candidates: {len(all_stocks)} stocks (in CLEAN.json)")
    print(f"   - Already unsustainable: {len(existing_unsustainable)} stocks\n")
    
    # Create lookup sets for existing stocks (ticker + year key)
    existing_unsustainable_keys = {
        f"{s['ticker']}_{s.get('year_discovered', s.get('year'))}" 
        for s in existing_unsustainable
    }
    
    # Results
    # Sustainable list starts empty - we'll build it as we test
    # Unsustainable list starts with existing unsustainable stocks
    sustainable = []
    unsustainable = list(existing_unsustainable)
    stats = {
        'total_tested': 0,
        'sustainable_count': 0,
        'unsustainable_count': len(existing_unsustainable),
        'skipped_already_tested': 0,
        'skipped_missing_data': 0,
        'skipped_too_recent': 0,
        'skipped_no_price': 0,
        'new_sustainable': 0,
        'new_unsustainable': 0,
        'avg_retention_sustainable': 0,
        'avg_retention_unsustainable': 0
    }
    
    retention_sustainable = []
    retention_unsustainable = []
    
    # Process each stock
    for i, stock in enumerate(all_stocks, 1):
        ticker = stock['ticker']
        year = stock.get('year_discovered', stock.get('year'))
        stock_key = f"{ticker}_{year}"
        
        print(f"\n[{i}/{len(all_stocks)}] Processing {ticker} ({year})")
        
        # Skip if already tested as unsustainable
        if stock_key in existing_unsustainable_keys:
            print(f"  ⏭️  Already tested as unsustainable - skipping")
            stats['skipped_already_tested'] += 1
            continue
        
        stats['total_tested'] += 1
        
        # Test sustainability
        result = calculate_sustainability(stock, POLYGON_API_KEY)
        
        # Add test results to stock data
        stock_with_test = stock.copy()
        stock_with_test['sustainability_test'] = result
        stock_with_test['tested_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Categorize
        if result['sustainable']:
            sustainable.append(stock_with_test)
            stats['new_sustainable'] += 1
            stats['sustainable_count'] += 1
            if result['retention_percent']:
                retention_sustainable.append(result['retention_percent'])
            print(f"  ✅ SUSTAINABLE - Retained {result['retention_percent']}% of gain")
        else:
            unsustainable.append(stock_with_test)
            stats['new_unsustainable'] += 1
            stats['unsustainable_count'] += 1
            if result['retention_percent']:
                retention_unsustainable.append(result['retention_percent'])
            print(f"  ❌ UNSUSTAINABLE - {result['reason']}")
            
            # Track skip reasons
            if 'Missing' in result['reason']:
                stats['skipped_missing_data'] += 1
            elif 'future' in result['reason']:
                stats['skipped_too_recent'] += 1
            elif 'Could not fetch' in result['reason']:
                stats['skipped_no_price'] += 1
        
        # Rate limiting - 5 requests per minute for free tier
        if stats['total_tested'] % 5 == 0:
            print(f"\n  ⏸️  Rate limit pause (5 requests/minute)...")
            time.sleep(12)
    
    # Calculate averages
    if retention_sustainable:
        stats['avg_retention_sustainable'] = round(sum(retention_sustainable) / len(retention_sustainable), 2)
    if retention_unsustainable:
        stats['avg_retention_unsustainable'] = round(sum(retention_unsustainable) / len(retention_unsustainable), 2)
    
    # Save results
    print("\n" + "="*70)
    print("💾 SAVING RESULTS")
    print("="*70 + "\n")
    
    # CRITICAL: Overwrite CLEAN.json with ONLY sustainable stocks
    with open(input_file, 'w') as f:
        json.dump(sustainable, f, indent=2)
    print(f"✅ Updated {input_file} with {len(sustainable)} SUSTAINABLE stocks (removed {len(unsustainable)} unsustainable)")
    
    with open(output_unsustainable, 'w') as f:
        json.dump(unsustainable, f, indent=2)
    print(f"✅ Saved {len(unsustainable)} UNSUSTAINABLE stocks to {output_unsustainable}")
    
    # Add metadata to summary
    stats['filter_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stats['sustainability_threshold'] = SUSTAINABILITY_THRESHOLD
    stats['input_file'] = input_file
    stats['sustainable_percentage'] = round((stats['sustainable_count'] / len(all_stocks)) * 100, 2)
    stats['removed_from_clean'] = len(unsustainable)
    
    with open(summary_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Saved summary to {summary_file}\n")
    
    # Print final summary
    print("="*70)
    print("📊 SUSTAINABILITY FILTER SUMMARY")
    print("="*70)
    print(f"Total Stocks Processed: {len(all_stocks)}")
    print(f"Already Tested (Skipped): {stats['skipped_already_tested']}")
    print(f"Newly Tested: {stats['total_tested']}")
    print(f"\n✅ SUSTAINABLE: {stats['sustainable_count']} ({stats['sustainable_percentage']}%)")
    print(f"   - New: {stats['new_sustainable']}")
    print(f"   - Avg Retention: {stats['avg_retention_sustainable']}%")
    print(f"   - Kept in {input_file}")
    print(f"\n❌ UNSUSTAINABLE: {stats['unsustainable_count']}")
    print(f"   - New: {stats['new_unsustainable']}")
    print(f"   - Avg Retention: {stats['avg_retention_unsustainable']}%")
    print(f"   - Moved to {output_unsustainable}")
    print(f"\n⏭️  SKIPPED:")
    print(f"   - Missing Data: {stats['skipped_missing_data']}")
    print(f"   - Too Recent: {stats['skipped_too_recent']}")
    print(f"   - No Price Data: {stats['skipped_no_price']}")
    print("="*70 + "\n")
    
    print(f"✅ Filter complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Results saved:")
    print(f"   - {input_file} (UPDATED - sustainable stocks only)")
    print(f"   - {output_unsustainable} (unsustainable stocks archived)")
    print(f"   - {summary_file} (statistics)\n")


if __name__ == "__main__":
    filter_sustainability(
        INPUT_FILE,
        OUTPUT_UNSUSTAINABLE,
        SUMMARY_FILE
    )
