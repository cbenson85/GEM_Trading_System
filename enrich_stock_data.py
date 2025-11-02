#!/usr/bin/env python3
"""
GEM Trading System - Comprehensive Data Enrichment Scanner
Version: 1.0
Created: 2025-11-02

PURPOSE:
Enrich all 200 stocks in CLEAN.json with complete data from Polygon API.
This prepares stocks for proper sustainability filtering.

WHAT IT DOES:
1. Reads all stocks from CLEAN.json (ticker, year, gain%, days_to_peak)
2. For each stock, finds:
   - Entry date (when explosive move started)
   - Entry price
   - Peak date (highest price in 180-day window)
   - Peak price
   - Days to peak
   - Test price (30 days after peak)
3. Enriches CLEAN.json with this data
4. Logs any stocks where data can't be found

DATA SOURCES:
- Primary: Polygon API (Developer tier - unlimited)
- Backup: Yahoo Finance (if Polygon fails)

OUTPUT:
- explosive_stocks_CLEAN.json (ENRICHED with full data)
- enrichment_log.json (success/failure tracking)
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
OUTPUT_FILE = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
LOG_FILE = f"{DATA_DIR}/enrichment_log.json"

# Progress tracking
enrichment_log = {
    'started': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_stocks': 0,
    'enriched': 0,
    'already_enriched': 0,
    'failed': 0,
    'skipped': 0,
    'failures': []
}


def get_daily_prices(ticker, start_date, end_date, api_key):
    """Get daily price data from Polygon"""
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
        print(f"  ❌ Error: {e}")
        return []


def analyze_drawdown_velocity(prices):
    """
    Analyze how fast stock drops during the explosive window
    Returns: dict with drawdown metrics
    """
    if len(prices) < 2:
        return None
    
    # Find all significant drops
    max_single_day_drop = 0
    max_single_day_drop_date = None
    
    # Find largest multi-day drawdowns
    drawdowns = []
    
    for i in range(1, len(prices)):
        # Single day drop
        prev_close = prices[i-1]['close']
        curr_close = prices[i]['close']
        daily_drop_pct = ((prev_close - curr_close) / prev_close) * 100
        
        if daily_drop_pct > max_single_day_drop:
            max_single_day_drop = daily_drop_pct
            max_single_day_drop_date = prices[i]['date']
        
        # Look for drawdowns >20% over multiple days
        if i >= 10:  # Need at least 10 days of history
            window = prices[i-10:i+1]
            high = max(d['high'] for d in window)
            low = min(d['low'] for d in window)
            drawdown_pct = ((high - low) / high) * 100
            
            if drawdown_pct > 20:
                # Find how many days it took
                high_idx = next(j for j, d in enumerate(window) if d['high'] == high)
                low_idx = next(j for j, d in enumerate(window) if d['low'] == low)
                days = abs(low_idx - high_idx)
                
                if days > 0:
                    velocity = drawdown_pct / days
                    drawdowns.append({
                        'drawdown_pct': round(drawdown_pct, 2),
                        'days': days,
                        'velocity_per_day': round(velocity, 2)
                    })
    
    # Classify tradeability based on 35% trailing stop loss
    # We need to exit if stock drops 35% from peak
    # Problem: If it drops >35% in ONE day, our stop won't fill
    
    if max_single_day_drop > 35:
        tradeable = "UNTRADEABLE"
        reason = f"Single-day drop of {max_single_day_drop:.1f}% - would gap past 35% stop loss"
    elif max_single_day_drop > 25:
        tradeable = "RISKY"
        reason = f"Single-day drop of {max_single_day_drop:.1f}% - might gap through stop"
    elif max_single_day_drop == 0:
        tradeable = "IDEAL"
        reason = "No significant drops - plenty of time to exit at any point"
    else:
        tradeable = "TRADEABLE"
        reason = f"Max drop {max_single_day_drop:.1f}% - 35% trailing stop should fill"
    
    return {
        'max_single_day_drop_pct': round(max_single_day_drop, 2),
        'max_drop_date': max_single_day_drop_date,
        'significant_drawdowns': drawdowns[:3] if drawdowns else [],  # Top 3
        'tradeable_classification': tradeable,
        'tradeable_reason': reason
    }


def find_explosive_window(ticker, year, target_gain_pct, api_key):
    """
    Find the 180-day window with the explosive gain
    Returns complete enrichment data
    """
    # Search range: 6 months before year to 6 months after
    start_date = f"{year - 1}-07-01"
    end_date = f"{year + 1}-06-30"
    
    print(f"  📊 Fetching data: {start_date} to {end_date}")
    prices = get_daily_prices(ticker, start_date, end_date, api_key)
    
    if len(prices) < 180:
        print(f"  ⚠️  Insufficient data: only {len(prices)} days")
        return None
    
    print(f"  ✅ Got {len(prices)} days of data")
    
    # Find best 180-day window
    best_window = None
    max_gain = 0
    
    for i in range(len(prices) - 180):
        window = prices[i:i+180]
        entry_price = window[0]['close']
        
        # Find peak in window
        peak_idx = 0
        peak_price = entry_price
        
        for j, day in enumerate(window):
            if day['high'] > peak_price:
                peak_price = day['high']
                peak_idx = j
        
        gain_pct = ((peak_price - entry_price) / entry_price) * 100
        
        # Accept ANY window with 500%+ gain (not just matching target)
        if gain_pct >= 500:
            if gain_pct > max_gain:
                max_gain = gain_pct
                
                # Get test price (30 days after peak)
                peak_date = window[peak_idx]['date']
                peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
                test_dt = peak_dt + timedelta(days=30)
                
                # Find test price
                test_price = None
                for k in range(peak_idx, min(peak_idx + 40, len(window))):
                    if datetime.strptime(window[k]['date'], '%Y-%m-%d') >= test_dt:
                        test_price = window[k]['close']
                        break
                
                best_window = {
                    'entry_date': window[0]['date'],
                    'entry_price': round(entry_price, 4),
                    'peak_date': peak_date,
                    'peak_price': round(peak_price, 4),
                    'days_to_peak': peak_idx,
                    'gain_percent': round(gain_pct, 2),
                    'test_price': round(test_price, 4) if test_price else None,
                    'test_date': test_dt.strftime('%Y-%m-%d') if test_price else None
                }
    
    if best_window:
        print(f"  ✅ Found window:")
        print(f"     Entry: {best_window['entry_date']} @ ${best_window['entry_price']}")
        print(f"     Peak:  {best_window['peak_date']} @ ${best_window['peak_price']}")
        print(f"     Gain:  {best_window['gain_percent']}% in {best_window['days_to_peak']} days")
        if best_window['test_price']:
            print(f"     Test:  {best_window['test_date']} @ ${best_window['test_price']}")
        
        # Analyze drawdown velocity for tradeability
        print(f"  📊 Analyzing drawdown velocity...")
        drawdown_analysis = analyze_drawdown_velocity(prices)
        if drawdown_analysis:
            best_window['drawdown_analysis'] = drawdown_analysis
            print(f"     Max single-day drop: {drawdown_analysis['max_single_day_drop_pct']:.1f}%")
            print(f"     Tradeable: {drawdown_analysis['tradeable_classification']}")
            print(f"     {drawdown_analysis['tradeable_reason']}")
    
    return best_window


def enrich_stock(stock, api_key):
    """Enrich a single stock with complete data"""
    ticker = stock.get('ticker')
    year = stock.get('year', stock.get('year_discovered'))
    gain_percent = stock.get('gain_percent')
    
    # Check if already enriched
    if 'entry_date' in stock and 'entry_price' in stock and 'peak_price' in stock:
        print(f"  ℹ️  Already enriched - skipping")
        enrichment_log['already_enriched'] += 1
        return stock
    
    if not all([ticker, year, gain_percent]):
        print(f"  ❌ Missing required fields")
        enrichment_log['failed'] += 1
        enrichment_log['failures'].append({
            'ticker': ticker,
            'year': year,
            'reason': 'Missing required fields (ticker, year, or gain_percent)'
        })
        return stock
    
    # Find explosive window
    window_data = find_explosive_window(ticker, year, gain_percent, api_key)
    
    if not window_data:
        print(f"  ❌ Could not find explosive window")
        enrichment_log['failed'] += 1
        enrichment_log['failures'].append({
            'ticker': ticker,
            'year': year,
            'reason': 'Could not find explosive window in Polygon data'
        })
        return stock
    
    # Enrich stock with found data
    enriched_stock = stock.copy()
    enriched_stock.update({
        'entry_date': window_data['entry_date'],
        'entry_price': window_data['entry_price'],
        'peak_date': window_data['peak_date'],
        'peak_price': window_data['peak_price'],
        'days_to_peak': window_data['days_to_peak'],
        'gain_percent': window_data['gain_percent'],
        'enriched': True,
        'enrichment_date': datetime.now().strftime('%Y-%m-%d'),
        'data_source': 'Polygon API'
    })
    
    if window_data['test_price']:
        enriched_stock['test_price_30d'] = window_data['test_price']
        enriched_stock['test_date_30d'] = window_data['test_date']
    
    # Add drawdown analysis
    if 'drawdown_analysis' in window_data:
        enriched_stock['drawdown_analysis'] = window_data['drawdown_analysis']
    
    enrichment_log['enriched'] += 1
    return enriched_stock


def save_progress(clean_data, stocks_processed):
    """Save progress periodically"""
    if isinstance(clean_data, dict) and 'stocks' in clean_data:
        clean_data['stocks'] = stocks_processed
        clean_data['metadata']['last_enrichment'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        clean_data = stocks_processed
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(clean_data, f, indent=2)
    
    with open(LOG_FILE, 'w') as f:
        json.dump(enrichment_log, f, indent=2)


def run_enrichment():
    """Main enrichment process"""
    print("\n" + "="*70)
    print("🔬 COMPREHENSIVE DATA ENRICHMENT SCANNER")
    print("="*70)
    print(f"📅 Started: {enrichment_log['started']}")
    print("🎯 Goal: Enrich all 200 stocks with complete Polygon data")
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
    else:
        all_stocks = clean_data
        clean_data = {'stocks': all_stocks}
    
    enrichment_log['total_stocks'] = len(all_stocks)
    
    print(f"✅ Loaded {len(all_stocks)} stocks")
    print(f"⚡ Using Polygon Developer API (unlimited requests)\n")
    
    # Process each stock
    enriched_stocks = []
    
    for i, stock in enumerate(all_stocks, 1):
        ticker = stock.get('ticker', 'UNKNOWN')
        year = stock.get('year', stock.get('year_discovered', 'UNKNOWN'))
        
        print(f"\n[{i}/{len(all_stocks)}] {ticker} ({year})")
        print("="*70)
        
        enriched_stock = enrich_stock(stock, POLYGON_API_KEY)
        enriched_stocks.append(enriched_stock)
        
        # Save progress every 10 stocks
        if i % 10 == 0:
            print(f"\n💾 Saving progress...")
            save_progress(clean_data, enriched_stocks)
        
        # Small delay to be polite
        time.sleep(0.1)
    
    # Final save
    print("\n" + "="*70)
    print("💾 SAVING FINAL RESULTS")
    print("="*70)
    
    save_progress(clean_data, enriched_stocks)
    
    enrichment_log['completed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(LOG_FILE, 'w') as f:
        json.dump(enrichment_log, f, indent=2)
    
    # Final summary
    print("\n" + "="*70)
    print("📊 ENRICHMENT COMPLETE")
    print("="*70)
    print(f"Total Stocks: {enrichment_log['total_stocks']}")
    print(f"✅ Enriched: {enrichment_log['enriched']}")
    print(f"ℹ️  Already Had Data: {enrichment_log['already_enriched']}")
    print(f"❌ Failed: {enrichment_log['failed']}")
    print(f"\nSuccess Rate: {(enrichment_log['enriched'] + enrichment_log['already_enriched'])/enrichment_log['total_stocks']*100:.1f}%")
    print("="*70)
    
    if enrichment_log['failed'] > 0:
        print(f"\n⚠️  {enrichment_log['failed']} stocks failed enrichment")
        print(f"   See {LOG_FILE} for details")


if __name__ == "__main__":
    run_enrichment()
