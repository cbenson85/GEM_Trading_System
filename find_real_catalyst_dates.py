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

def find_real_catalyst(ticker: str, entry_date: str) -> Dict:
    """
    Find the REAL catalyst date by scanning a wide window of price data
    Returns dict with catalyst_date and analysis_start_date (90 days prior)
    """
    print(f"\n{'='*60}")
    print(f"Processing {ticker}")
    print(f"Entry date: {entry_date}")
    
    # Parse entry date and create WIDE search window
    try:
        entry_dt = datetime.fromisoformat(entry_date)
    except:
        print(f"ERROR: Invalid entry date format: {entry_date}")
        return {}
    
    # WIDE WINDOW: Check 6 months before to 12 months after entry
    # This handles stocks that may have been identified late
    start_date = (entry_dt - timedelta(days=180)).strftime('%Y-%m-%d')
    end_date = (entry_dt + timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Make sure end date isn't in the future
    today = datetime.now()
    if datetime.fromisoformat(end_date) > today:
        end_date = today.strftime('%Y-%m-%d')
    
    print(f"Scanning from {start_date} to {end_date}")
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
        time.sleep(0.2)
        
        if response.status_code != 200:
            print(f"API ERROR: Status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return {}
            
        data = response.json()
        
        if 'results' not in data or not data['results']:
            print(f"NO DATA: No price data found for {ticker}")
            return {}
        
        bars = data['results']
        print(f"Received {len(bars)} daily bars")
        
        if len(bars) < 30:
            print(f"INSUFFICIENT DATA: Only {len(bars)} bars")
            return {}
        
        # Find the absolute lowest point in first 60 days as baseline
        baseline_bars = bars[:60]
        baseline = min([b['l'] for b in baseline_bars if 'l' in b])
        baseline_date = None
        for b in baseline_bars:
            if b.get('l') == baseline:
                baseline_date = datetime.fromtimestamp(b['t']/1000).strftime('%Y-%m-%d')
                break
        
        print(f"Baseline: ${baseline:.3f} on {baseline_date}")
        
        # Now scan for first 100%+ jump from baseline
        catalyst_found = False
        catalyst_date = None
        catalyst_price = None
        
        for i in range(60, len(bars)):  # Start after baseline period
            bar = bars[i]
            if 'h' not in bar or 'c' not in bar:
                continue
            
            date = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')
            high = bar['h']
            close = bar['c']
            
            # Check if we hit 100%+ gain (using close price for stability)
            gain_pct = ((close - baseline) / baseline) * 100
            
            if gain_pct >= 100 and not catalyst_found:
                print(f"\nPotential catalyst on {date}:")
                print(f"  Close: ${close:.3f} ({gain_pct:.1f}% gain from baseline)")
                
                # CRITICAL: Verify this 100% jump leads to 500%+
                # Check all remaining bars after this point
                remaining_bars = bars[i:]
                max_price = baseline  # Start with baseline
                max_date = date
                
                for future_bar in remaining_bars:
                    if 'h' in future_bar:
                        if future_bar['h'] > max_price:
                            max_price = future_bar['h']
                            max_date = datetime.fromtimestamp(future_bar['t']/1000).strftime('%Y-%m-%d')
                
                max_gain = ((max_price - baseline) / baseline) * 100
                
                print(f"  Max price after catalyst: ${max_price:.3f} on {max_date}")
                print(f"  Max gain: {max_gain:.1f}%")
                
                if max_gain >= 500:
                    print(f"  ✓ VERIFIED: This catalyst leads to {max_gain:.1f}% gain!")
                    catalyst_found = True
                    catalyst_date = date
                    catalyst_price = close
                    
                    # Calculate analysis start date (90 days before catalyst)
                    catalyst_dt = datetime.fromisoformat(catalyst_date)
                    analysis_start = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
                    
                    print(f"\nFINAL RESULTS:")
                    print(f"  Catalyst Date: {catalyst_date}")
                    print(f"  Analysis Start Date (90 days prior): {analysis_start}")
                    
                    return {
                        'catalyst_date': catalyst_date,
                        'catalyst_price': catalyst_price,
                        'analysis_start_date': analysis_start,
                        'baseline_price': baseline,
                        'baseline_date': baseline_date,
                        'max_gain_pct': max_gain,
                        'verified': True
                    }
                else:
                    print(f"  ✗ FALSE POSITIVE: Only reached {max_gain:.1f}% max")
                    # Continue searching for the real catalyst
        
        if not catalyst_found:
            print(f"\nNO CATALYST FOUND: No 100%+ jump that leads to 500%+")
            return {}
        
    except Exception as e:
        print(f"ERROR processing {ticker}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    print("="*70)
    print("REAL CATALYST DATE FINDER - WITH VERIFICATION")
    print("="*70)
    
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY environment variable not set!")
        return
    else:
        print(f"✓ API Key found: {POLYGON_API_KEY[:10]}...")
    
    # Load stocks
    stocks = load_explosive_stocks()
    print(f"\nLoaded {len(stocks)} stocks from explosive_stocks_CLEAN.json")
    
    # Check for stocks with bad dates
    bad_date_stocks = []
    for stock in stocks:
        if 'catalyst_date' in stock:
            try:
                catalyst_dt = datetime.fromisoformat(stock['catalyst_date'])
                if catalyst_dt > datetime.now():
                    bad_date_stocks.append(stock)
            except:
                bad_date_stocks.append(stock)
    
    print(f"Found {len(bad_date_stocks)} stocks with future/invalid catalyst dates")
    
    # Process first 5 stocks as a test (whether they have bad dates or not)
    test_stocks = stocks[:5]
    print(f"\nTesting with first 5 stocks...")
    
    fixed_count = 0
    error_count = 0
    
    for stock in test_stocks:
        ticker = stock['ticker']
        entry_date = stock.get('entry_date', '2024-01-01')
        
        # Find real catalyst
        result = find_real_catalyst(ticker, entry_date)
        
        if result and 'catalyst_date' in result:
            # Update stock with all new data
            stock['catalyst_date'] = result['catalyst_date']
            stock['analysis_start_date'] = result['analysis_start_date']
            stock['catalyst_price'] = result['catalyst_price']
            stock['baseline_price'] = result['baseline_price']
            stock['baseline_date'] = result['baseline_date']
            stock['max_gain_verified'] = result['max_gain_pct']
            stock['catalyst_verified'] = True
            fixed_count += 1
        else:
            error_count += 1
            stock['catalyst_verified'] = False
            print(f"→ Could not find valid catalyst for {ticker}")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY:")
    print(f"  Fixed: {fixed_count} stocks")
    print(f"  Errors: {error_count} stocks")
    print(f"  Total API calls made: {fixed_count + error_count}")
    
    # Save results
    output_file = 'Verified_Backtest_Data/explosive_stocks_CATALYST_FIXED.json'
    
    # Create full output with all stocks (not just test ones)
    output_data = {
        'stocks': stocks,
        'metadata': {
            'last_updated': datetime.now().isoformat(),
            'fixed_count': fixed_count,
            'error_count': error_count,
            'total_stocks': len(stocks)
        }
    }
    
    os.makedirs('Verified_Backtest_Data', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
