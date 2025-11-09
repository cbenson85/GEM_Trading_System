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
                        # Find catalyst with FIXED method
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
            
            return explosions
            
        except Exception as e:
            return []
    
    def find_catalyst(self, bars: List[Dict], base_idx: int, peak_idx: int) -> Optional[Dict]:
        """Find INITIAL catalyst that started the move - search BEFORE/AT base, not within explosion"""
        
        if base_idx < 50:
            return None
        
        # CRITICAL FIX: Search from 30 days BEFORE base to 10 days AFTER
        # This finds the initial breakout, not continuation patterns
        search_start = max(50, base_idx - 30)
        search_end = min(base_idx + 10, peak_idx)
        
        # Track best catalyst found
        best_catalyst = None
        best_volume_spike = 0
        
        for i in range(search_start, search_end):
            if i < 50:
                continue
            
            # Check if stock is already exploding (skip continuation patterns)
            if i > search_start + 5:
                recent_gain = (bars[i]['c'] - bars[i-5]['c']) / bars[i-5]['c'] if bars[i-5]['c'] > 0 else 0
                if recent_gain > 0.5:  # Already up >50% in 5 days
                    continue
            
            # Calculate 50-day average volume
            vol_50 = sum([bars[j].get('v', 0) for j in range(i-50, i)]) / 50
            current_vol = bars[i].get('v', 0)
            
            if vol_50 == 0:
                continue
            
            volume_spike = current_vol / vol_50
            
            # Need 5x+ volume for real catalyst
            if volume_spike < 5.0:
                continue
            
            current_close = bars[i].get('c', 0)
            prev_close = bars[i-1].get('c', 0) if i > 0 else 0
            
            # Calculate 50-day MA
            ma50 = sum([bars[j].get('c', 0) for j in range(i-50, i)]) / 50
            prev_ma50 = sum([bars[j].get('c', 0) for j in range(i-51, i-1)]) / 50
            
            # Check for valid breakout patterns
            catalyst_type = None
            
            # MA breakout check
            if prev_close <= prev_ma50 * 1.05 and current_close > ma50:  # Allow 5% above MA
                catalyst_type = "50MA_BREAKOUT"
            
            # 52-week high check
            elif i >= 252:
                year_high = max([bars[j].get('h', 0) for j in range(i-252, i)])
                if current_close > year_high * 0.98:  # Within 2% of 52W high
                    catalyst_type = "52W_HIGH"
            
            # Volume-only catalyst (massive volume without specific pattern)
            elif volume_spike > 10.0:
                catalyst_type = "VOLUME_SURGE"
            
            # If we found a catalyst, check if it's better than previous
            if catalyst_type and volume_spike > best_volume_spike:
                # Additional validation: check RSI isn't already extreme
                rsi = self.calculate_simple_rsi(bars, i)
                if rsi < 80:  # Not already overbought
                    catalyst_dt = datetime.fromtimestamp(bars[i]['t']/1000)
                    best_catalyst = {
                        'date': catalyst_dt.strftime('%Y-%m-%d'),
                        'price': current_close,
                        'type': catalyst_type,
                        'volume_spike': f"{volume_spike:.1f}x",
                        'analysis_start': (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
                    }
                    best_volume_spike = volume_spike
        
        # If no catalyst found in the early window, look for the first significant move
        if not best_catalyst and search_end < peak_idx:
            # Extend search slightly but with stricter criteria
            for i in range(search_end, min(search_end + 20, peak_idx)):
                if i < 50:
                    continue
                
                vol_50 = sum([bars[j].get('v', 0) for j in range(i-50, i)]) / 50
                current_vol = bars[i].get('v', 0)
                
                if vol_50 == 0:
                    continue
                
                volume_spike = current_vol / vol_50
                
                # Require even higher volume for later catalysts
                if volume_spike >= 8.0:
                    # Check it's the start of a move
                    price_change = (bars[i]['c'] - bars[i-1]['c']) / bars[i-1]['c'] if bars[i-1]['c'] > 0 else 0
                    if price_change > 0.1:  # >10% price move
                        catalyst_dt = datetime.fromtimestamp(bars[i]['t']/1000)
                        best_catalyst = {
                            'date': catalyst_dt.strftime('%Y-%m-%d'),
                            'price': bars[i]['c'],
                            'type': 'BREAKOUT',
                            'volume_spike': f"{volume_spike:.1f}x",
                            'analysis_start': (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
                        }
                        break
        
        return best_catalyst
    
    def calculate_simple_rsi(self, bars: List[Dict], idx: int, period: int = 14) -> float:
        """Calculate simple RSI for validation"""
        if idx < period:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(idx - period, idx):
            change = bars[i]['c'] - bars[i-1]['c']
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

def main():
    print("="*70)
    print("120-DAY WINDOW SCANNER - FIXED CATALYST DETECTION")
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
    print("Catalyst: FIXED - searching BEFORE base, not within explosion")
    
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
            'catalyst_method': 'FIXED_BEFORE_BASE'
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
