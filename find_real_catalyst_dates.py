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

def debug_stock_dates(stocks):
    """Debug function to see what's in the data"""
    print("\n" + "="*70)
    print("DEBUGGING FIRST 5 STOCKS:")
    print("="*70)
    
    for i, stock in enumerate(stocks[:5]):
        ticker = stock.get('ticker', 'NO_TICKER')
        catalyst = stock.get('catalyst_date', 'NO_DATE')
        year = stock.get('year_discovered', 'NO_YEAR')
        
        print(f"\nStock {i+1}: {ticker}")
        print(f"  Year Discovered: {year}")
        print(f"  Catalyst Date: {catalyst}")
        
        # Check if date is bad
        if catalyst != 'NO_DATE':
            try:
                catalyst_dt = datetime.fromisoformat(catalyst)
                now = datetime.now()
                
                if catalyst_dt > now:
                    print(f"  ⚠️ FUTURE DATE! ({catalyst_dt.date()} vs today {now.date()})")
                elif catalyst_dt.year < 2014:
                    print(f"  ⚠️ TOO OLD! (Year {catalyst_dt.year})")
                else:
                    days_ago = (now - catalyst_dt).days
                    print(f"  ✓ Valid date ({days_ago} days ago)")
            except Exception as e:
                print(f"  ⚠️ INVALID DATE FORMAT! Error: {e}")
        else:
            print(f"  ⚠️ MISSING DATE!")
    
    # Count total issues
    future_count = 0
    missing_count = 0
    invalid_count = 0
    old_count = 0
    
    for stock in stocks:
        catalyst = stock.get('catalyst_date', None)
        if not catalyst:
            missing_count += 1
        else:
            try:
                catalyst_dt = datetime.fromisoformat(catalyst)
                if catalyst_dt > datetime.now():
                    future_count += 1
                elif catalyst_dt.year < 2014:
                    old_count += 1
            except:
                invalid_count += 1
    
    print(f"\n{'='*70}")
    print(f"TOTAL ISSUES IN ALL {len(stocks)} STOCKS:")
    print(f"  Future dates: {future_count}")
    print(f"  Missing dates: {missing_count}")
    print(f"  Invalid format: {invalid_count}")
    print(f"  Too old (<2014): {old_count}")
    print(f"  TOTAL BAD: {future_count + missing_count + invalid_count + old_count}")
    print("="*70)

def find_real_catalyst(ticker: str, year_discovered: int) -> Dict:
    """Find the REAL catalyst date by scanning the appropriate year"""
    print(f"\n{'='*60}")
    print(f"Processing {ticker} (discovered in {year_discovered})")
    
    # Create search window based on year discovered
    start_date = f"{year_discovered}-01-01"
    end_date = f"{year_discovered}-12-31"
    
    # Make sure end date isn't in the future
    today = datetime.now()
    if datetime.fromisoformat(end_date) > today:
        end_date = today.strftime('%Y-%m-%d')
    
    print(f"Scanning {start_date} to {end_date}")
    print(f"Making API call...")
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {
        'apiKey': POLYGON_API_KEY,
        'adjusted': 'true',
        'sort': 'asc',
        'limit': 50000
    }
    
    try:
        start_time = time.time()
        response = requests.get(url, params=params)
        api_time = time.time() - start_time
        print(f"API took {api_time:.2f}s")
        
        time.sleep(0.25)  # Rate limit
        
        if response.status_code != 200:
            print(f"API ERROR: {response.status_code}")
            return {'error': f'api_{response.status_code}'}
        
        data = response.json()
        
        if 'results' not in data or not data['results']:
            print(f"NO DATA for {year_discovered}")
            return {'error': 'no_data'}
        
        bars = data['results']
        print(f"Got {len(bars)} bars")
        
        if len(bars) < 20:
            return {'error': 'insufficient_data'}
        
        # Find baseline (lowest in first 30 days)
        baseline_days = min(30, len(bars) // 3)
        baseline = min([b['l'] for b in bars[:baseline_days] if 'l' in b])
        baseline_date = None
        baseline_idx = 0
        
        for idx, b in enumerate(bars[:baseline_days]):
            if b.get('l') == baseline:
                baseline_idx = idx
                baseline_date = datetime.fromtimestamp(b['t']/1000).strftime('%Y-%m-%d')
                break
        
        print(f"Baseline: ${baseline:.4f} on {baseline_date}")
        
        # Find first 100% jump that leads to 500%
        for i in range(baseline_idx + 1, len(bars)):
            bar = bars[i]
            if 'c' not in bar:
                continue
            
            close = bar['c']
            gain_pct = ((close - baseline) / baseline) * 100
            
            if gain_pct >= 100:
                date = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')
                print(f"Testing {date}: ${close:.4f} ({gain_pct:.1f}%)")
                
                # Verify it reaches 500%
                remaining = bars[i:]
                if len(remaining) < 5:
                    continue
                
                max_price = max([b['h'] for b in remaining if 'h' in b])
                max_gain = ((max_price - baseline) / baseline) * 100
                
                if max_gain >= 500:
                    catalyst_dt = datetime.fromisoformat(date)
                    analysis_start = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
                    
                    print(f"✓ CATALYST FOUND! Max: {max_gain:.1f}%")
                    
                    return {
                        'catalyst_date': date,
                        'catalyst_price': close,
                        'analysis_start_date': analysis_start,
                        'baseline_price': baseline,
                        'baseline_date': baseline_date,
                        'max_gain_pct': max_gain,
                        'verified': True
                    }
        
        print("No valid catalyst found")
        return {'error': 'no_catalyst'}
        
    except Exception as e:
        print(f"ERROR: {e}")
        return {'error': str(e)}

def main():
    print("="*70)
    print("CATALYST DATE FINDER - DEBUG VERSION")
    print("="*70)
    
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    print(f"✓ API Key: {POLYGON_API_KEY[:10]}...")
    
    # Load stocks
    stocks = load_explosive_stocks()
    print(f"Loaded {len(stocks)} stocks")
    
    # DEBUG: Show what's in the data
    debug_stock_dates(stocks)
    
    # Find stocks needing fixes
    stocks_to_fix = []
    for stock in stocks:
        catalyst = stock.get('catalyst_date', None)
        needs_fix = False
        
        if not catalyst:
            needs_fix = True
        else:
            try:
                catalyst_dt = datetime.fromisoformat(catalyst)
                if catalyst_dt > datetime.now():
                    needs_fix = True
                elif catalyst_dt.year < 2014:
                    needs_fix = True
            except:
                needs_fix = True
        
        if needs_fix:
            stocks_to_fix.append(stock)
    
    print(f"\nFound {len(stocks_to_fix)} stocks needing fixes")
    
    if len(stocks_to_fix) == 0:
        print("\n⚠️ No stocks detected as needing fixes!")
        print("But let's force-process the first 3 anyway to test:")
        stocks_to_fix = stocks[:3]
    
    # Process first few
    process_count = min(3, len(stocks_to_fix))
    print(f"\nProcessing {process_count} stocks...")
    
    fixed = 0
    errors = 0
    
    for idx, stock in enumerate(stocks_to_fix[:process_count]):
        ticker = stock.get('ticker', 'UNKNOWN')
        year = stock.get('year_discovered', 2024)
        
        print(f"\n[{idx+1}/{process_count}] {ticker}")
        
        result = find_real_catalyst(ticker, year)
        
        if 'catalyst_date' in result:
            stock['catalyst_date'] = result['catalyst_date']
            stock['analysis_start_date'] = result['analysis_start_date']
            stock['catalyst_price'] = result['catalyst_price']
            stock['baseline_price'] = result['baseline_price']
            stock['baseline_date'] = result['baseline_date']
            stock['max_gain_verified_pct'] = result['max_gain_pct']
            stock['catalyst_verified'] = True
            stock['catalyst_fixed_date'] = datetime.now().isoformat()
            fixed += 1
            print(f"✓ Fixed: {result['catalyst_date']}")
        else:
            stock['catalyst_error'] = result.get('error', 'unknown')
            stock['catalyst_verified'] = False
            errors += 1
            print(f"✗ Error: {result.get('error')}")
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: Fixed {fixed}, Errors {errors}")
    
    # Save
    output_data = {
        'stocks': stocks,
        'metadata': {
            'updated': datetime.now().isoformat(),
            'total': len(stocks),
            'fixed': fixed,
            'errors': errors
        }
    }
    
    with open('Verified_Backtest_Data/explosive_stocks_CATALYST_FIXED.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved to explosive_stocks_CATALYST_FIXED.json")
    print("="*70)

if __name__ == "__main__":
    main()
