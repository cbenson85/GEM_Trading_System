import json
import os
import time
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')

class PureScanner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.api_calls = 0
        self.errors = {
            'not_found': [],
            'api_error': [],
            'insufficient_data': [],
            'no_results': []
        }
        
    def get_universe(self, limit: int = None) -> List[str]:
        """Get ALL active US stocks"""
        print("\n" + "="*50)
        print("FETCHING UNIVERSE")
        print("="*50)
        
        url = f"{self.base_url}/v3/reference/tickers"
        params = {
            'apiKey': self.api_key,
            'market': 'stocks',
            'active': 'true',
            'limit': 1000,
            'type': 'CS'
        }
        
        universe = []
        next_url = None
        page_count = 0
        
        while True:
            page_count += 1
            print(f"Fetching page {page_count}...")
            
            try:
                if next_url:
                    response = requests.get(next_url)
                else:
                    response = requests.get(url, params=params)
                
                self.api_calls += 1
                
                if response.status_code != 200:
                    print(f"ERROR: Status {response.status_code}")
                    break
                    
                data = response.json()
                page_tickers = [t['ticker'] for t in data.get('results', [])]
                universe.extend(page_tickers)
                
                print(f"  Page {page_count}: Got {len(page_tickers)} tickers")
                print(f"  Total so far: {len(universe)}")
                
                if limit and len(universe) >= limit:
                    return universe[:limit]
                
                next_url = data.get('next_url')
                if next_url:
                    next_url += f"&apiKey={self.api_key}"
                else:
                    print("  No more pages")
                    break
                    
            except Exception as e:
                print(f"ERROR fetching page {page_count}: {e}")
                break
        
        print(f"\nUNIVERSE COMPLETE: {len(universe)} tickers")
        return universe
    
    def scan_ticker(self, ticker: str, scan_start: str, scan_end: str) -> List[Dict]:
        """Scan one ticker for 500% moves with catalyst"""
        
        # Skip obviously bad tickers
        if len(ticker) > 5 or ticker.startswith('$'):
            return []
        
        # Need buffer for MA calculations
        buffer_start = (datetime.strptime(scan_start, '%Y-%m-%d') - timedelta(days=300)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{buffer_start}/{scan_end}"
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        try:
            start_time = time.time()
            response = requests.get(url, params=params)
            api_time = time.time() - start_time
            self.api_calls += 1
            
            # Track API response times
            if api_time < 0.01:
                print(f"  WARNING: {ticker} returned in {api_time:.3f}s - too fast, likely cached or error")
            
            if response.status_code == 404:
                self.errors['not_found'].append(ticker)
                return []
            elif response.status_code != 200:
                self.errors['api_error'].append(f"{ticker}:{response.status_code}")
                return []
            
            data = response.json()
            
            if 'results' not in data:
                self.errors['no_results'].append(ticker)
                return []
                
            bars = data.get('results', [])
            
            if len(bars) < 340:
                self.errors['insufficient_data'].append(f"{ticker}:{len(bars)}")
                return []
            
            explosions = []
            
            # Find scan start index
            scan_start_dt = datetime.strptime(scan_start, '%Y-%m-%d')
            scan_idx = 0
            for i, bar in enumerate(bars):
                if datetime.fromtimestamp(bar['t']/1000) >= scan_start_dt:
                    scan_idx = i
                    break
            
            # Scan all 90-day windows
            windows_checked = 0
            for window_start in range(scan_idx, len(bars) - 90):
                windows_checked += 1
                window = bars[window_start:window_start + 90]
                
                # Find min/max in window
                lows = [b['l'] for b in window if 'l' in b]
                highs = [b['h'] for b in window if 'h' in b]
                
                if not lows or not highs:
                    continue
                
                base = min(lows)
                peak = max(highs)
                
                # Skip data errors
                if base > 10000 or peak > 100000:
                    continue
                if base < 0.10:
                    continue
                
                gain = ((peak - base) / base) * 100
                
                if gain >= 500:
                    # Find exact indices
                    base_idx = None
                    peak_idx = None
                    
                    for j, bar in enumerate(window):
                        if bar.get('l') == base and base_idx is None:
                            base_idx = window_start + j
                        if bar.get('h') == peak and peak_idx is None:
                            peak_idx = window_start + j
                    
                    if base_idx and peak_idx and base_idx < peak_idx:
                        # Find catalyst
                        catalyst = self.find_catalyst(bars, base_idx, peak_idx)
                        
                        if catalyst:
                            explosions.append({
                                'ticker': ticker,
                                'base_price': base,
                                'base_date': datetime.fromtimestamp(bars[base_idx]['t']/1000).strftime('%Y-%m-%d'),
                                'peak_price': peak,
                                'peak_date': datetime.fromtimestamp(bars[peak_idx]['t']/1000).strftime('%Y-%m-%d'),
                                'gain_pct': gain,
                                'catalyst_date': catalyst['date'],
                                'catalyst_price': catalyst['price'],
                                'catalyst_type': catalyst['type'],
                                'volume_spike': catalyst['volume_spike'],
                                'analysis_start': catalyst['analysis_start'],
                                'days_to_peak': peak_idx - base_idx
                            })
            
            if windows_checked > 0 and windows_checked < 100:
                print(f"  WARNING: {ticker} only checked {windows_checked} windows")
                
            return explosions
            
        except Exception as e:
            print(f"ERROR scanning {ticker}: {e}")
            self.errors['api_error'].append(f"{ticker}:exception")
            return []
    
    def find_catalyst(self, bars: List[Dict], base_idx: int, peak_idx: int) -> Optional[Dict]:
        """Find catalyst with realistic volume for 500% moves"""
        
        if base_idx < 50:
            return None
        
        for i in range(base_idx, peak_idx + 1):
            if i < 50:
                continue
            
            # Calculate 50-day average volume
            vol_50 = sum([bars[j].get('v', 0) for j in range(i-50, i)]) / 50
            current_vol = bars[i].get('v', 0)
            
            if vol_50 == 0:
                continue
            
            volume_spike = current_vol / vol_50
            
            # For 500% moves, catalyst should be 5x+ volume
            if volume_spike < 5.0:
                continue
            
            current_close = bars[i].get('c', 0)
            prev_close = bars[i-1].get('c', 0) if i > 0 else 0
            
            # Calculate 50-day MA
            ma50 = sum([bars[j].get('c', 0) for j in range(i-50, i)]) / 50
            prev_ma50 = sum([bars[j].get('c', 0) for j in range(i-51, i-1)]) / 50
            
            catalyst_type = None
            
            # Check MA breakout
            if prev_close <= prev_ma50 and current_close > ma50:
                catalyst_type = "50MA_BREAKOUT"
            # Check 52-week high
            elif i >= 252:
                year_high = max([bars[j].get('h', 0) for j in range(i-252, i)])
                if current_close > year_high:
                    catalyst_type = "52W_HIGH"
            
            if catalyst_type:
                catalyst_dt = datetime.fromtimestamp(bars[i]['t']/1000)
                analysis_start = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
                
                return {
                    'date': catalyst_dt.strftime('%Y-%m-%d'),
                    'price': current_close,
                    'type': catalyst_type,
                    'volume_spike': f"{volume_spike:.1f}x",
                    'analysis_start': analysis_start
                }
        
        return None

def main():
    print("="*70)
    print("PURE SCANNER v3.0 - FULL DEBUG MODE")
    print("MINIMUM VOLUME: 5X")
    print("="*70)
    
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    scanner = PureScanner(POLYGON_API_KEY)
    
    # Get batch parameters
    batch_size = int(os.environ.get('BATCH_SIZE', '100'))
    batch_number = int(os.environ.get('BATCH_NUMBER', '0'))
    scan_start = os.environ.get('SCAN_START', '2010-01-01')
    scan_end = os.environ.get('SCAN_END', '2024-12-31')
    
    print(f"\nBATCH: {batch_number}")
    print(f"SIZE: {batch_size}")
    print(f"PERIOD: {scan_start} to {scan_end}")
    
    # Track timing
    start_time = time.time()
    
    # Get universe
    universe = scanner.get_universe()
    
    fetch_time = time.time() - start_time
    print(f"\nUniverse fetched in {fetch_time:.1f}s")
    print(f"API calls so far: {scanner.api_calls}")
    
    # Process batch
    start_idx = batch_number * batch_size
    end_idx = min(start_idx + batch_size, len(universe))
    batch_tickers = universe[start_idx:end_idx] if start_idx < len(universe) else []
    
    print(f"\nBatch {batch_number}: indices {start_idx}-{end_idx}")
    print(f"Tickers in batch: {len(batch_tickers)}")
    
    if not batch_tickers:
        print("BATCH EMPTY - beyond universe size")
        results = {
            'batch_info': {
                'batch_number': batch_number,
                'empty': True,
                'reason': 'beyond_universe_size'
            }
        }
    else:
        print(f"First: {batch_tickers[0]}, Last: {batch_tickers[-1]}")
        
        # Scan
        all_discoveries = []
        scan_start_time = time.time()
        
        for idx, ticker in enumerate(batch_tickers):
            if idx % 10 == 0:
                elapsed = time.time() - scan_start_time
                rate = idx / elapsed if elapsed > 0 else 0
                print(f"\nProgress: {idx}/{len(batch_tickers)} ({rate:.1f} tickers/sec)")
                print(f"  API calls: {scanner.api_calls}")
            
            explosions = scanner.scan_ticker(ticker, scan_start, scan_end)
            
            if explosions:
                all_discoveries.extend(explosions)
                for exp in explosions:
                    print(f"  💥 {ticker}: {exp['catalyst_date']} ({exp['gain_pct']:.0f}% in {exp.get('days_to_peak', 'N/A')} days, {exp['volume_spike']} volume)")
        
        scan_time = time.time() - scan_start_time
        
        # Results
        results = {
            'batch_info': {
                'batch_number': batch_number,
                'batch_size': batch_size,
                'start_idx': start_idx,
                'end_idx': end_idx,
                'universe_size': len(universe),
                'tickers_scanned': len(batch_tickers)
            },
            'performance': {
                'total_time': time.time() - start_time,
                'fetch_time': fetch_time,
                'scan_time': scan_time,
                'api_calls': scanner.api_calls,
                'tickers_per_second': len(batch_tickers) / scan_time if scan_time > 0 else 0
            },
            'errors': scanner.errors,
            'error_counts': {
                'not_found': len(scanner.errors['not_found']),
                'api_error': len(scanner.errors['api_error']),
                'insufficient_data': len(scanner.errors['insufficient_data']),
                'no_results': len(scanner.errors['no_results'])
            },
            'scan_parameters': {
                'start': scan_start,
                'end': scan_end,
                'timestamp': datetime.now().isoformat()
            },
            'discoveries': all_discoveries,
            'summary': {
                'tickers_scanned': len(batch_tickers),
                'explosions_found': len(all_discoveries)
            }
        }
    
    # Save
    os.makedirs('scan_results/batches', exist_ok=True)
    output_file = f'scan_results/batches/batch_{batch_number}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"BATCH {batch_number} COMPLETE")
    print(f"  Time: {results.get('performance', {}).get('total_time', 0):.1f}s")
    print(f"  API calls: {scanner.api_calls}")
    print(f"  Errors: {sum(results.get('error_counts', {}).values())}")
    print(f"  Found: {len(all_discoveries)} explosions")
    print(f"  Saved: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
