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
            
            if next_url:
                response = requests.get(next_url)
            else:
                response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"ERROR: Status {response.status_code}")
                break
                
            data = response.json()
            page_tickers = [t['ticker'] for t in data.get('results', [])]
            universe.extend(page_tickers)
            
            print(f"  Page {page_count}: Got {len(page_tickers)} tickers")
            print(f"  First few: {page_tickers[:5]}")
            print(f"  Total so far: {len(universe)}")
            
            if limit and len(universe) >= limit:
                print(f"Hit limit of {limit}")
                return universe[:limit]
            
            next_url = data.get('next_url')
            if next_url:
                next_url += f"&apiKey={self.api_key}"
                print(f"  Next page available...")
            else:
                print("  No more pages")
                break
            
            # Stop after 10 pages for safety
            if page_count >= 10:
                print("WARNING: Stopping at 10 pages")
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
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return []
            
            data = response.json()
            bars = data.get('results', [])
            
            if len(bars) < 340:
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
            for window_start in range(scan_idx, len(bars) - 90):
                window = bars[window_start:window_start + 90]
                
                # Find min/max in window
                lows = [b['l'] for b in window if 'l' in b]
                highs = [b['h'] for b in window if 'h' in b]
                
                if not lows or not highs:
                    continue
                
                base = min(lows)
                peak = max(highs)
                
                # VALIDATION: Skip obvious data errors
                if base < 0.01 or base > 50000:
                    continue
                if peak > 100000:
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
                                'analysis_start': catalyst['analysis_start']
                            })
            
            return explosions
            
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            return []
    
    def find_catalyst(self, bars: List[Dict], base_idx: int, peak_idx: int) -> Optional[Dict]:
        """Find catalyst: MA break or 52W high with 2x+ volume"""
        
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
            
            # VALIDATION: Skip unrealistic volume spikes
            if volume_spike > 50:
                continue
            
            # Need 2x+ volume
            if volume_spike < 2.0:
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
    print("PURE MARKET SCANNER - BATCH MODE")
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
    
    print(f"\nBATCH PARAMETERS:")
    print(f"  Batch Number: {batch_number}")
    print(f"  Batch Size: {batch_size}")
    print(f"  Scan Period: {scan_start} to {scan_end}")
    
    # Get universe
    universe = scanner.get_universe()
    
    # DEBUG: Show universe details
    print("\n" + "="*50)
    print("UNIVERSE DEBUG")
    print("="*50)
    print(f"Total tickers: {len(universe)}")
    print(f"First 10: {universe[:10] if universe else 'EMPTY'}")
    print(f"Last 10: {universe[-10:] if universe else 'EMPTY'}")
    
    # Check for issues
    if len(universe) < 1000:
        print(f"WARNING: Only {len(universe)} tickers - expected thousands!")
    
    # Process batch
    start_idx = batch_number * batch_size
    end_idx = min(start_idx + batch_size, len(universe))
    batch_tickers = universe[start_idx:end_idx] if start_idx < len(universe) else []
    
    print("\n" + "="*50)
    print("BATCH DEBUG")
    print("="*50)
    print(f"Batch {batch_number}: indices {start_idx} to {end_idx}")
    print(f"Tickers in batch: {len(batch_tickers)}")
    if batch_tickers:
        print(f"First ticker: {batch_tickers[0]}")
        print(f"Last ticker: {batch_tickers[-1]}")
        print(f"Sample: {batch_tickers[:5]}")
    else:
        print("BATCH IS EMPTY!")
    
    # Scan
    all_discoveries = []
    
    for idx, ticker in enumerate(batch_tickers):
        if idx % 10 == 0:
            print(f"\nProgress: {idx}/{len(batch_tickers)}")
        
        explosions = scanner.scan_ticker(ticker, scan_start, scan_end)
        
        if explosions:
            all_discoveries.extend(explosions)
            for exp in explosions:
                print(f"  ✓ {ticker}: {exp['catalyst_date']} - {exp['gain_pct']:.0f}%")
    
    # Save
    results = {
        'batch_info': {
            'batch_number': batch_number,
            'batch_size': batch_size,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'actual_tickers_count': len(batch_tickers),
            'universe_size': len(universe)
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
        },
        'debug': {
            'sample_tickers': batch_tickers[:10] if batch_tickers else []
        }
    }
    
    os.makedirs('scan_results/batches', exist_ok=True)
    output_file = f'scan_results/batches/batch_{batch_number}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"BATCH {batch_number} COMPLETE")
    print(f"  Universe size: {len(universe)}")
    print(f"  Batch contained: {len(batch_tickers)} tickers")
    print(f"  Explosions found: {len(all_discoveries)}")
    print(f"  Saved: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
