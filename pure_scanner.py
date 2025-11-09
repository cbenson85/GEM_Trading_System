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
        
        while True:
            if next_url:
                response = requests.get(next_url)
            else:
                response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Error getting tickers: {response.status_code}")
                break
                
            data = response.json()
            universe.extend([t['ticker'] for t in data.get('results', [])])
            
            if limit and len(universe) >= limit:
                return universe[:limit]
            
            next_url = data.get('next_url')
            if next_url:
                next_url += f"&apiKey={self.api_key}"
            else:
                break
        
        return universe
    
    def scan_ticker(self, ticker: str, scan_start: str, scan_end: str) -> List[Dict]:
        """Scan one ticker for 500% moves with catalyst"""
        
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
            
            if len(bars) < 340:  # Need sufficient data
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
    print("PURE MARKET SCANNER - GITHUB ACTIONS")
    print("="*70)
    
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    scanner = PureScanner(POLYGON_API_KEY)
    
    # Get batch parameters from environment or defaults
    batch_size = int(os.environ.get('BATCH_SIZE', '100'))
    batch_number = int(os.environ.get('BATCH_NUMBER', '0'))
    scan_start = os.environ.get('SCAN_START', '2024-01-01')
    scan_end = os.environ.get('SCAN_END', '2024-12-31')
    
    print(f"\nScan Parameters:")
    print(f"  Period: {scan_start} to {scan_end}")
    print(f"  Batch: {batch_number}")
    print(f"  Size: {batch_size}")
    
    # Get universe
    print("\nFetching universe...")
    universe = scanner.get_universe()
    print(f"Total universe: {len(universe)} stocks")
    
    # Process this batch
    start_idx = batch_number * batch_size
    end_idx = min(start_idx + batch_size, len(universe))
    batch_tickers = universe[start_idx:end_idx]
    
    print(f"\nProcessing batch {batch_number}: stocks {start_idx} to {end_idx}")
    print(f"Tickers in batch: {len(batch_tickers)}")
    
    # Scan batch
    all_discoveries = []
    
    for idx, ticker in enumerate(batch_tickers):
        print(f"\n[{idx+1}/{len(batch_tickers)}] Scanning {ticker}...")
        explosions = scanner.scan_ticker(ticker, scan_start, scan_end)
        
        if explosions:
            all_discoveries.extend(explosions)
            for exp in explosions:
                print(f"  ✓ FOUND: {exp['catalyst_date']} - {exp['gain_pct']:.0f}% gain")
    
    # Save results
    results = {
        'batch_info': {
            'batch_number': batch_number,
            'batch_size': batch_size,
            'tickers_in_batch': batch_tickers,
            'start_idx': start_idx,
            'end_idx': end_idx
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
    
    output_file = f'discoveries_batch_{batch_number}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"BATCH {batch_number} COMPLETE")
    print(f"  Scanned: {len(batch_tickers)} tickers")
    print(f"  Found: {len(all_discoveries)} explosions")
    print(f"  Saved: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
