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
        
    def get_universe(self, limit: int = None) -> List[str]:
        """Get ALL stocks - active AND delisted/inactive"""
        print("\n" + "="*50)
        print("FETCHING COMPLETE HISTORICAL UNIVERSE")
        print("="*50)
        
        url = f"{self.base_url}/v3/reference/tickers"
        all_tickers = set()
        
        # ACTIVE stocks
        print("\n1. Fetching ACTIVE stocks...")
        params = {
            'apiKey': self.api_key,
            'market': 'stocks',
            'active': 'true',
            'limit': 1000
        }
        
        next_url = None
        page = 0
        
        while True:
            page += 1
            try:
                if next_url:
                    response = requests.get(next_url)
                else:
                    response = requests.get(url, params=params)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                tickers = [t['ticker'] for t in data.get('results', [])]
                all_tickers.update(tickers)
                print(f"  Page {page}: {len(tickers)} tickers (Total: {len(all_tickers)})")
                
                next_url = data.get('next_url')
                if next_url:
                    next_url += f"&apiKey={self.api_key}"
                else:
                    break
                    
            except Exception as e:
                print(f"Error: {e}")
                break
        
        active_count = len(all_tickers)
        print(f"\nActive stocks: {active_count}")
        
        # INACTIVE/DELISTED stocks
        print("\n2. Fetching INACTIVE/DELISTED stocks...")
        params['active'] = 'false'
        
        next_url = None
        page = 0
        
        while True:
            page += 1
            try:
                if next_url:
                    response = requests.get(next_url)
                else:
                    response = requests.get(url, params=params)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                tickers = [t['ticker'] for t in data.get('results', [])]
                before = len(all_tickers)
                all_tickers.update(tickers)
                new_tickers = len(all_tickers) - before
                print(f"  Page {page}: {len(tickers)} tickers ({new_tickers} new, Total: {len(all_tickers)})")
                
                next_url = data.get('next_url')
                if next_url:
                    next_url += f"&apiKey={self.api_key}"
                else:
                    break
                    
            except Exception as e:
                print(f"Error: {e}")
                break
        
        print(f"\n{'='*50}")
        print(f"TOTAL UNIVERSE: {len(all_tickers)} stocks")
        print("="*50)
        
        return list(all_tickers)
    
    def scan_ticker(self, ticker: str, scan_start: str, scan_end: str) -> List[Dict]:
        """Scan one ticker for 500% moves with catalyst - 120 DAY WINDOWS"""
        
        # Skip bad tickers
        if len(ticker) > 6 or ticker.startswith('$') or '/' in ticker:
            return []
        
        # Need buffer for MA calculations (350 days for 120-day window + 50MA + 52W high)
        buffer_start = (datetime.strptime(scan_start, '%Y-%m-%d') - timedelta(days=400)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{buffer_start}/{scan_end}"
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            if 'results' not in data:
                return []
                
            bars = data.get('results', [])
            
            # Need enough history for 120-day window + technical indicators
            if len(bars) < 400:
                return []
            
            explosions = []
            
            # Find scan start index
            scan_start_dt = datetime.strptime(scan_start, '%Y-%m-%d')
            scan_idx = 0
            for i, bar in enumerate(bars):
                if datetime.fromtimestamp(bar['t']/1000) >= scan_start_dt:
                    scan_idx = i
                    break
            
            # Scan all 120-day windows
            for window_start in range(scan_idx, len(bars) - 120):
                window = bars[window_start:window_start + 120]
                
                # Find min/max in 120-day window
                lows = [b['l'] for b in window if 'l' in b]
                highs = [b['h'] for b in window if 'h' in b]
                
                if not lows or not highs:
                    continue
                
                base = min(lows)
                peak = max(highs)
                
                # Skip data errors
                if base > 10000 or peak > 100000:
                    continue
                if base < 0.01:
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
                        # Find TRUE initial catalyst
                        catalyst = self.find_true_catalyst(bars, base_idx, peak_idx)
                        
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
                                'days_to_peak': peak_idx - catalyst['idx']
                            })
            
            return explosions
            
        except Exception as e:
            return []
    
    def find_true_catalyst(self, bars: List[Dict], base_idx: int, peak_idx: int) -> Optional[Dict]:
        """Find TRUE initial catalyst by searching for first major move from quiet period"""
        
        # Need at least 100 days of history before to find quiet period
        if base_idx < 100:
            return None
        
        # Step 1: Find the TRUE start by working FORWARD from a quiet period
        # Look for the lowest volatility period in the 60 days before the base
        search_start = max(50, base_idx - 60)
        
        # Find the quietest 20-day period (lowest average daily range)
        quietest_start = search_start
        min_volatility = float('inf')
        
        for i in range(search_start, base_idx - 20):
            # Calculate average daily range for 20-day window
            daily_ranges = []
            for j in range(i, i + 20):
                if j < len(bars):
                    high = bars[j].get('h', 0)
                    low = bars[j].get('l', 0)
                    close = bars[j].get('c', 1)
                    if close > 0:
                        daily_range = (high - low) / close
                        daily_ranges.append(daily_range)
            
            avg_volatility = sum(daily_ranges) / len(daily_ranges) if daily_ranges else float('inf')
            
            if avg_volatility < min_volatility:
                min_volatility = avg_volatility
                quietest_start = i
        
        # Step 2: From the quiet period, find the FIRST significant breakout
        for i in range(quietest_start + 20, min(peak_idx, quietest_start + 100)):
            if i < 50:
                continue
            
            # Calculate metrics
            vol_50 = sum([bars[j].get('v', 0) for j in range(i-50, i)]) / 50
            current_vol = bars[i].get('v', 0)
            
            if vol_50 == 0:
                continue
            
            volume_spike = current_vol / vol_50
            
            # Need significant volume
            if volume_spike < 3.0:
                continue
            
            current_close = bars[i].get('c', 0)
            prev_close = bars[i-1].get('c', 0) if i > 0 else 0
            
            if prev_close == 0:
                continue
            
            daily_gain = (current_close - prev_close) / prev_close
            
            # Calculate 20-day average before this point
            avg_20 = sum([bars[j].get('c', 0) for j in range(i-20, i)]) / 20
            
            # Check if this is a significant move from recent average
            move_from_avg = (current_close - avg_20) / avg_20 if avg_20 > 0 else 0
            
            # VALIDATION: Make sure stock hasn't already exploded
            # Check 30-day return before this point
            price_30_ago = bars[i-30].get('c', 0) if i >= 30 else 0
            return_30d = (current_close - price_30_ago) / price_30_ago if price_30_ago > 0 else 0
            
            # If already up >100% in 30 days, this is NOT the initial catalyst
            if return_30d > 1.0:
                continue
            
            # Found a potential catalyst - check if it's valid
            if (daily_gain > 0.05 and volume_spike >= 3.0 and move_from_avg > 0.10):
                
                # Final validation: check that the explosion actually continues
                # Look ahead 10 days - should see continued upward movement
                future_gains = []
                for j in range(i+1, min(i+10, peak_idx)):
                    future_price = bars[j].get('c', 0)
                    future_gain = (future_price - current_close) / current_close if current_close > 0 else 0
                    future_gains.append(future_gain)
                
                # If stock continues up (at least some positive days)
                if future_gains and max(future_gains) > 0.20:
                    catalyst_dt = datetime.fromtimestamp(bars[i]['t']/1000)
                    
                    # Determine catalyst type
                    ma50 = sum([bars[j].get('c', 0) for j in range(i-50, i)]) / 50
                    
                    if prev_close <= ma50 * 1.05 and current_close > ma50:
                        catalyst_type = "50MA_BREAKOUT"
                    elif daily_gain > 0.15:
                        catalyst_type = "PRICE_SURGE"
                    elif volume_spike > 10:
                        catalyst_type = "VOLUME_EXPLOSION"
                    else:
                        catalyst_type = "BREAKOUT"
                    
                    return {
                        'date': catalyst_dt.strftime('%Y-%m-%d'),
                        'price': current_close,
                        'type': catalyst_type,
                        'volume_spike': f"{volume_spike:.1f}x",
                        'analysis_start': (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d'),
                        'idx': i
                    }
        
        # If no clean catalyst found in quiet period search, 
        # fall back to finding first major move but with strict validation
        for i in range(max(50, base_idx - 30), min(base_idx + 30, peak_idx)):
            vol_50 = sum([bars[j].get('v', 0) for j in range(i-50, i)]) / 50
            current_vol = bars[i].get('v', 0)
            
            if vol_50 == 0:
                continue
            
            volume_spike = current_vol / vol_50
            
            # Require higher volume for fallback
            if volume_spike < 5.0:
                continue
            
            current_close = bars[i].get('c', 0)
            
            # Check that stock is still near lows (within 50% of base)
            if current_close > base * 1.5:
                continue
            
            # Check 30-day return - must be low
            price_30_ago = bars[i-30].get('c', 0) if i >= 30 else 0
            return_30d = (current_close - price_30_ago) / price_30_ago if price_30_ago > 0 else 0
            
            if return_30d < 0.5:  # Less than 50% up in 30 days
                catalyst_dt = datetime.fromtimestamp(bars[i]['t']/1000)
                return {
                    'date': catalyst_dt.strftime('%Y-%m-%d'),
                    'price': current_close,
                    'type': 'VOLUME_SURGE',
                    'volume_spike': f"{volume_spike:.1f}x",
                    'analysis_start': (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d'),
                    'idx': i
                }
        
        return None

def main():
    print("="*70)
    print("TRUE CATALYST SCANNER - FINDING REAL EXPLOSION STARTS")
    print("="*70)
    
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    scanner = PureScanner(POLYGON_API_KEY)
    
    # Get batch parameters
    batch_size = int(os.environ.get('BATCH_SIZE', '500'))
    batch_number = int(os.environ.get('BATCH_NUMBER', '0'))
    scan_start = os.environ.get('SCAN_START', '2010-01-01')
    scan_end = os.environ.get('SCAN_END', '2024-12-31')
    
    print(f"\nBatch: {batch_number}")
    print(f"Size: {batch_size}")
    print(f"Period: {scan_start} to {scan_end}")
    print(f"Window: 120 days")
    print("Method: Finding TRUE initial catalysts from quiet periods")
    
    # Get universe
    universe = scanner.get_universe()
    
    # Process batch
    start_idx = batch_number * batch_size
    end_idx = min(start_idx + batch_size, len(universe))
    batch_tickers = universe[start_idx:end_idx] if start_idx < len(universe) else []
    
    print(f"\nProcessing batch {batch_number}: indices {start_idx}-{end_idx}")
    print(f"Tickers in batch: {len(batch_tickers)}")
    
    if not batch_tickers:
        print("BATCH EMPTY")
        return
    
    # Scan
    all_discoveries = []
    
    for idx, ticker in enumerate(batch_tickers):
        if idx % 50 == 0:
            print(f"Progress: {idx}/{len(batch_tickers)}")
        
        explosions = scanner.scan_ticker(ticker, scan_start, scan_end)
        
        if explosions:
            all_discoveries.extend(explosions)
            for exp in explosions:
                print(f"  💥 {ticker}: {exp['gain_pct']:.0f}% in {exp.get('days_to_peak', 'N/A')} days")
    
    # Save
    results = {
        'batch_info': {
            'batch_number': batch_number,
            'batch_size': batch_size,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'universe_size': len(universe),
            'window_days': 120,
            'catalyst_method': 'TRUE_INITIAL_FROM_QUIET'
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
    
    os.makedirs('scan_results/batches', exist_ok=True)
    output_file = f'scan_results/batches/batch_{batch_number}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Batch {batch_number}: {len(all_discoveries)} explosions found")
    print("="*70)

if __name__ == "__main__":
    main()
