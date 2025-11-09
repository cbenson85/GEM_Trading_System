import json
import os
import time
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict, List

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')

def load_explosive_stocks():
    """Load the explosive stocks data"""
    with open('Verified_Backtest_Data/explosive_stocks_CLEAN.json', 'r') as f:
        data = json.load(f)
        if isinstance(data, dict) and 'stocks' in data:
            return data['stocks']
        return data

def find_catalyst_from_peak(ticker: str) -> Dict:
    """
    Fetch ALL data for stock, find peak, work backwards to find catalyst
    """
    print(f"\n{'='*60}")
    print(f"Processing {ticker}")
    
    # Fetch maximum date range (2010 to now)
    start_date = "2010-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Fetching ALL data: {start_date} to {end_date}")
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {
        'apiKey': POLYGON_API_KEY,
        'adjusted': 'true',
        'sort': 'asc',
        'limit': 50000
    }
    
    try:
        print("Making API call...")
        start_time = time.time()
        response = requests.get(url, params=params)
        api_time = time.time() - start_time
        print(f"API took {api_time:.2f}s")
        
        time.sleep(0.25)  # Rate limit
        
        if response.status_code == 404:
            print(f"ERROR: Ticker not found/delisted")
            return {'error': 'ticker_not_found'}
        
        if response.status_code != 200:
            print(f"ERROR: API status {response.status_code}")
            return {'error': f'api_{response.status_code}'}
        
        data = response.json()
        
        if 'results' not in data or not data['results']:
            print(f"ERROR: No data found")
            return {'error': 'no_data'}
        
        bars = data['results']
        print(f"Got {len(bars)} days of data")
        
        if len(bars) < 30:
            print(f"ERROR: Insufficient data ({len(bars)} days)")
            return {'error': 'insufficient_data'}
        
        # STEP 1: Find the absolute peak price
        peak_price = 0
        peak_idx = 0
        peak_date = None
        
        for idx, bar in enumerate(bars):
            if 'h' in bar and bar['h'] > peak_price:
                peak_price = bar['h']
                peak_idx = idx
                peak_date = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')
        
        print(f"\nPEAK: ${peak_price:.4f} on {peak_date} (bar {peak_idx}/{len(bars)})")
        
        if peak_idx < 10:
            print(f"ERROR: Peak too early in data (bar {peak_idx})")
            return {'error': 'peak_too_early'}
        
        # STEP 2: Find the lowest price BEFORE the peak (baseline)
        pre_peak_bars = bars[:peak_idx]
        baseline_price = min([b['l'] for b in pre_peak_bars if 'l' in b])
        baseline_idx = 0
        baseline_date = None
        
        for idx, bar in enumerate(pre_peak_bars):
            if bar.get('l') == baseline_price:
                baseline_idx = idx
                baseline_date = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')
                break
        
        print(f"BASELINE: ${baseline_price:.4f} on {baseline_date}")
        
        # Calculate max gain
        max_gain = ((peak_price - baseline_price) / baseline_price) * 100
        print(f"MAX GAIN: {max_gain:.1f}%")
        
        if max_gain < 500:
            print(f"ERROR: Max gain only {max_gain:.1f}% (need 500%+)")
            return {'error': f'insufficient_gain_{max_gain:.0f}pct'}
        
        # STEP 3: Find FIRST 100% jump after baseline (this is our catalyst)
        catalyst_date = None
        catalyst_price = None
        catalyst_idx = None
        
        for idx in range(baseline_idx + 1, peak_idx + 1):
            bar = bars[idx]
            if 'c' not in bar:
                continue
            
            close = bar['c']
            gain = ((close - baseline_price) / baseline_price) * 100
            
            if gain >= 100:
                # This is our catalyst!
                catalyst_idx = idx
                catalyst_date = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')
                catalyst_price = close
                print(f"\nCATALYST FOUND:")
                print(f"  Date: {catalyst_date}")
                print(f"  Price: ${catalyst_price:.4f}")
                print(f"  Gain from baseline: {gain:.1f}%")
                print(f"  Days from catalyst to peak: {peak_idx - catalyst_idx}")
                break
        
        if not catalyst_date:
            print(f"ERROR: No 100% jump found between baseline and peak")
            return {'error': 'no_catalyst_found'}
        
        # STEP 4: Calculate analysis start date (90 days before catalyst)
        catalyst_dt = datetime.fromisoformat(catalyst_date)
        analysis_start = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        
        print(f"\nFINAL RESULTS:")
        print(f"  Catalyst: {catalyst_date}")
        print(f"  Analysis Start (90 days prior): {analysis_start}")
        print(f"  Baseline → Catalyst: {((catalyst_price - baseline_price) / baseline_price * 100):.1f}%")
        print(f"  Baseline → Peak: {max_gain:.1f}%")
        
        return {
            'catalyst_date': catalyst_date,
            'catalyst_price': catalyst_price,
            'analysis_start_date': analysis_start,
            'baseline_price': baseline_price,
            'baseline_date': baseline_date,
            'peak_price': peak_price,
            'peak_date': peak_date,
            'max_gain_pct': max_gain,
            'days_to_peak': peak_idx - catalyst_idx,
            'verified': True
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

def main():
    print("="*70)
    print("CATALYST FINDER - PEAK BACKWARD SEARCH")
    print("="*70)
    
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    print(f"✓ API Key: {POLYGON_API_KEY[:10]}...")
    
    # Load stocks
    stocks = load_explosive_stocks()
    print(f"Loaded {len(stocks)} stocks")
    
    # Process ALL stocks (or first N for testing)
    process_limit = 20  # Start with 20, increase as needed
    process_count = min(process_limit, len(stocks))
    
    print(f"\nProcessing first {process_count} stocks...")
    print("This will take time - each stock needs a full data fetch")
    
    fixed = 0
    errors = 0
    error_details = {}
    
    for idx, stock in enumerate(stocks[:process_count]):
        ticker = stock.get('ticker', 'UNKNOWN')
        old_catalyst = stock.get('catalyst_date', 'None')
        
        print(f"\n[{idx+1}/{process_count}] {ticker}")
        print(f"  Old catalyst: {old_catalyst}")
        
        result = find_catalyst_from_peak(ticker)
        
        if 'catalyst_date' in result:
            # Update with correct data
            if old_catalyst != result['catalyst_date']:
                stock['old_catalyst_date'] = old_catalyst
            
            stock['catalyst_date'] = result['catalyst_date']
            stock['analysis_start_date'] = result['analysis_start_date']
            stock['catalyst_price'] = result['catalyst_price']
            stock['baseline_price'] = result['baseline_price']
            stock['baseline_date'] = result['baseline_date']
            stock['peak_price'] = result['peak_price']
            stock['peak_date'] = result['peak_date']
            stock['max_gain_pct'] = result['max_gain_pct']
            stock['days_to_peak'] = result['days_to_peak']
            stock['catalyst_verified'] = True
            stock['catalyst_updated'] = datetime.now().isoformat()
            
            fixed += 1
            if old_catalyst != result['catalyst_date']:
                print(f"  ✓ FIXED: {old_catalyst} → {result['catalyst_date']}")
            else:
                print(f"  ✓ CONFIRMED: {result['catalyst_date']}")
        else:
            error = result.get('error', 'unknown')
            stock['catalyst_error'] = error
            stock['catalyst_verified'] = False
            errors += 1
            
            # Track error types
            if error not in error_details:
                error_details[error] = []
            error_details[error].append(ticker)
            
            print(f"  ✗ ERROR: {error}")
    
    print(f"\n{'='*70}")
    print(f"PROCESSING COMPLETE")
    print(f"  Total: {process_count} stocks")
    print(f"  Fixed/Confirmed: {fixed} stocks")
    print(f"  Errors: {errors} stocks")
    
    if error_details:
        print(f"\nError breakdown:")
        for error_type, tickers in error_details.items():
            print(f"  {error_type}: {len(tickers)} stocks")
            if len(tickers) <= 5:
                print(f"    {', '.join(tickers)}")
    
    # Save results
    output_data = {
        'stocks': stocks,
        'metadata': {
            'updated': datetime.now().isoformat(),
            'total_stocks': len(stocks),
            'stocks_processed': process_count,
            'stocks_fixed': fixed,
            'stocks_errored': errors,
            'error_details': {k: len(v) for k, v in error_details.items()}
        }
    }
    
    output_file = 'Verified_Backtest_Data/explosive_stocks_CATALYST_FIXED.json'
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
