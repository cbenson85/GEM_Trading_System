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

def find_real_catalyst(ticker: str, year_discovered: int) -> Dict:
    """
    Find the REAL catalyst date by scanning the appropriate year
    """
    print(f"\n{'='*60}")
    print(f"Processing {ticker} (discovered in {year_discovered})")
    
    # Create search window based on year discovered
    # Scan from January of that year to December (or current date if same year)
    start_date = f"{year_discovered}-01-01"
    end_date = f"{year_discovered}-12-31"
    
    # Make sure end date isn't in the future
    today = datetime.now()
    if datetime.fromisoformat(end_date) > today:
        end_date = today.strftime('%Y-%m-%d')
    
    print(f"Scanning {start_date} to {end_date} for catalyst")
    print(f"Making Polygon API call...")
    
    # Get daily bars from Polygon
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
        print(f"API call took {api_time:.2f} seconds")
        
        # Rate limiting
        time.sleep(0.25)
        
        if response.status_code == 404:
            print(f"TICKER NOT FOUND: {ticker} may be delisted or invalid")
            return {'error': 'ticker_not_found'}
            
        if response.status_code != 200:
            print(f"API ERROR: Status {response.status_code}")
            return {'error': f'api_error_{response.status_code}'}
            
        data = response.json()
        
        if 'results' not in data or not data['results']:
            print(f"NO DATA: No price data found for {ticker} in {year_discovered}")
            # Try previous year
            prev_year = year_discovered - 1
            print(f"Trying {prev_year}...")
            return find_real_catalyst_previous_year(ticker, prev_year)
        
        bars = data['results']
        print(f"Received {len(bars)} daily bars")
        
        if len(bars) < 20:
            print(f"INSUFFICIENT DATA: Only {len(bars)} bars")
            return {'error': 'insufficient_data'}
        
        # Find the lowest point in first 30 days (or all bars if less than 30)
        baseline_days = min(30, len(bars) // 3)
        baseline_bars = bars[:baseline_days]
        baseline = min([b['l'] for b in baseline_bars if 'l' in b])
        baseline_idx = 0
        baseline_date = None
        
        for idx, b in enumerate(baseline_bars):
            if b.get('l') == baseline:
                baseline_idx = idx
                baseline_date = datetime.fromtimestamp(b['t']/1000).strftime('%Y-%m-%d')
                break
        
        print(f"Baseline: ${baseline:.4f} on {baseline_date}")
        
        # Track all significant jumps
        jumps_found = []
        
        # Scan for 100%+ jumps starting after baseline
        for i in range(baseline_idx + 1, len(bars)):
            bar = bars[i]
            if 'c' not in bar:
                continue
            
            date = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')
            close = bar['c']
            
            # Check for 100%+ gain from baseline
            gain_pct = ((close - baseline) / baseline) * 100
            
            if gain_pct >= 100:
                # Found a 100%+ jump, verify it leads to 500%+
                print(f"\nTesting potential catalyst on {date}")
                print(f"  Price: ${close:.4f} ({gain_pct:.1f}% from baseline)")
                
                # Check maximum gain in remaining bars
                remaining_bars = bars[i:]
                if len(remaining_bars) < 5:  # Need at least 5 days to verify
                    print(f"  Not enough data to verify (only {len(remaining_bars)} days left)")
                    continue
                
                max_price = max([b['h'] for b in remaining_bars if 'h' in b])
                max_gain = ((max_price - baseline) / baseline) * 100
                
                print(f"  Maximum reached: ${max_price:.4f} ({max_gain:.1f}% gain)")
                
                if max_gain >= 500:
                    # This is our catalyst!
                    catalyst_dt = datetime.fromisoformat(date)
                    analysis_start = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
                    
                    print(f"  ✓ CONFIRMED CATALYST!")
                    print(f"  Analysis window: {analysis_start} to {date}")
                    
                    return {
                        'catalyst_date': date,
                        'catalyst_price': close,
                        'analysis_start_date': analysis_start,
                        'baseline_price': baseline,
                        'baseline_date': baseline_date,
                        'max_gain_pct': max_gain,
                        'verified': True
                    }
                else:
                    print(f"  ✗ Only reached {max_gain:.1f}% (need 500%+)")
                    jumps_found.append({
                        'date': date,
                        'gain': gain_pct,
                        'max_gain': max_gain
                    })
        
        print(f"\nNO VALID CATALYST FOUND")
        if jumps_found:
            print(f"Found {len(jumps_found)} jumps but none led to 500%+")
        
        return {'error': 'no_catalyst_found', 'jumps_tested': len(jumps_found)}
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {'error': str(e)}

def find_real_catalyst_previous_year(ticker: str, year: int) -> Dict:
    """Try to find catalyst in previous year if not found in discovered year"""
    print(f"\nChecking {year} for earlier catalyst...")
    
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {'apiKey': POLYGON_API_KEY, 'adjusted': 'true', 'sort': 'asc', 'limit': 50000}
    
    try:
        response = requests.get(url, params=params)
        time.sleep(0.25)
        
        if response.status_code != 200 or 'results' not in response.json():
            return {'error': 'no_data_previous_year'}
            
        # Use same logic as main function
        # ... (similar processing logic)
        return {'error': 'catalyst_in_previous_year_not_implemented'}
        
    except Exception as e:
        return {'error': f'previous_year_error: {str(e)}'}

def main():
    print("="*70)
    print("CATALYST DATE FINDER - FULL PROCESSING")
    print("="*70)
    
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    print(f"✓ API Key: {POLYGON_API_KEY[:10]}...")
    
    # Load stocks
    stocks = load_explosive_stocks()
    print(f"Loaded {len(stocks)} stocks")
    
    # Identify stocks needing fixes
    stocks_to_fix = []
    for stock in stocks:
        needs_fix = False
        
        # Check if catalyst date is missing or invalid
        if 'catalyst_date' not in stock:
            needs_fix = True
        else:
            try:
                catalyst_dt = datetime.fromisoformat(stock['catalyst_date'])
                # If date is in future, needs fix
                if catalyst_dt > datetime.now():
                    needs_fix = True
                # If date is before 2014, probably wrong
                if catalyst_dt.year < 2014:
                    needs_fix = True
            except:
                needs_fix = True
        
        if needs_fix:
            stocks_to_fix.append(stock)
    
    print(f"Found {len(stocks_to_fix)} stocks needing catalyst fixes")
    
    # Process in batches to avoid timeout
    batch_size = 10
    process_count = min(batch_size, len(stocks_to_fix))
    
    print(f"\nProcessing first {process_count} stocks...")
    
    fixed_count = 0
    error_count = 0
    
    for idx, stock in enumerate(stocks_to_fix[:process_count]):
        ticker = stock['ticker']
        year = stock.get('year_discovered', 2024)
        
        print(f"\n[{idx+1}/{process_count}] Processing {ticker}")
        
        result = find_real_catalyst(ticker, year)
        
        if result and 'catalyst_date' in result:
            # Update stock with new data
            stock['catalyst_date'] = result['catalyst_date']
            stock['analysis_start_date'] = result['analysis_start_date']
            stock['catalyst_price'] = result['catalyst_price']
            stock['baseline_price'] = result['baseline_price']
            stock['baseline_date'] = result['baseline_date']
            stock['max_gain_verified_pct'] = result['max_gain_pct']
            stock['catalyst_verified'] = True
            stock['catalyst_fixed_date'] = datetime.now().isoformat()
            fixed_count += 1
            print(f"✓ Fixed {ticker}: catalyst on {result['catalyst_date']}")
        else:
            # Mark as error
            stock['catalyst_error'] = result.get('error', 'unknown_error')
            stock['catalyst_verified'] = False
            error_count += 1
            print(f"✗ Could not fix {ticker}: {result.get('error', 'unknown')}")
    
    print(f"\n{'='*70}")
    print(f"PROCESSING COMPLETE")
    print(f"  Fixed: {fixed_count}/{process_count} stocks")
    print(f"  Errors: {error_count}/{process_count} stocks")
    print(f"  Remaining: {len(stocks_to_fix) - process_count} stocks need processing")
    
    # Save results
    output_data = {
        'stocks': stocks,
        'metadata': {
            'last_updated': datetime.now().isoformat(),
            'total_stocks': len(stocks),
            'stocks_needing_fix': len(stocks_to_fix),
            'stocks_processed': process_count,
            'stocks_fixed': fixed_count,
            'stocks_errored': error_count,
            'batch_size': batch_size
        }
    }
    
    output_file = 'Verified_Backtest_Data/explosive_stocks_CATALYST_FIXED.json'
    os.makedirs('Verified_Backtest_Data', exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nSaved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
