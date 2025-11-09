import json
import os
import time
from datetime import datetime, timedelta
import requests
from typing import Dict, List

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')

class ExplosionFilter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.stats = {
            'total_input': 0,
            'removed_bad_data': 0,
            'removed_low_liquidity': 0,
            'removed_gap_risk': 0,
            'removed_crash_speed': 0,
            'removed_pump_dump': 0,
            'total_passed': 0
        }
        # Track rejected stocks
        self.rejected = {
            'bad_data': [],
            'low_liquidity': [],
            'gap_risk': [],
            'crash_speed': [],
            'pump_dump': []
        }
    
    def filter_bad_data(self, explosion: Dict) -> bool:
        """Filter 1: Remove obvious data errors"""
        
        reject_reason = None
        
        # Price sanity checks
        if explosion['peak_price'] > 20000:
            reject_reason = f"Peak price ${explosion['peak_price']}"
        elif explosion['base_price'] < 0.01:
            reject_reason = f"Base price ${explosion['base_price']}"
        elif explosion['gain_pct'] > 20000:
            reject_reason = f"Gain {explosion['gain_pct']:.0f}%"
        # REMOVED days_to_peak check - we're analyzing pre-catalyst patterns
        # Timing of peak vs catalyst doesn't matter for our analysis
            
        if reject_reason:
            self.stats['removed_bad_data'] += 1
            self.rejected['bad_data'].append({
                'ticker': explosion['ticker'],
                'reason': reject_reason,
                'data': explosion
            })
            return False
            
        return True
    
    def check_pre_catalyst_liquidity(self, ticker: str, catalyst_date: str, explosion: Dict) -> bool:
        """Filter 2: Flexible liquidity check - price and volume can compensate for each other"""
        
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        end_date = (catalyst_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (catalyst_dt - timedelta(days=51)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return False
                
            data = response.json()
            bars = data.get('results', [])
            
            if len(bars) < 30:
                return False
            
            avg_volume = sum([b.get('v', 0) for b in bars]) / len(bars)
            avg_price = sum([b.get('c', 0) for b in bars]) / len(bars)
            
            # FLEXIBLE LIQUIDITY SCORING
            # Absolute minimums (very relaxed)
            if avg_volume < 5000 or avg_price < 0.10:
                self.stats['removed_low_liquidity'] += 1
                self.rejected['low_liquidity'].append({
                    'ticker': ticker,
                    'reason': f"Vol: {avg_volume:.0f}, Price: ${avg_price:.2f} (below absolute minimum)",
                    'data': explosion
                })
                return False
            
            # Liquidity score: volume * price
            # $0.50 stock with 50k volume = 25,000 score
            # $5.00 stock with 5k volume = 25,000 score (same liquidity)
            liquidity_score = avg_volume * avg_price
            
            # Minimum score of 25,000 (much more flexible than fixed thresholds)
            if liquidity_score < 25000:
                self.stats['removed_low_liquidity'] += 1
                self.rejected['low_liquidity'].append({
                    'ticker': ticker,
                    'reason': f"Vol: {avg_volume:.0f}, Price: ${avg_price:.2f}, Score: {liquidity_score:.0f}",
                    'data': explosion
                })
                return False
                
            return True
            
        except:
            return False
    
    def check_gap_risk(self, ticker: str, peak_date: str, explosion: Dict) -> bool:
        """Filter 3: Check for catastrophic gaps after peak"""
        
        peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
        start_date = peak_date
        end_date = (peak_dt + timedelta(days=15)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return True
                
            data = response.json()
            bars = data.get('results', [])
            
            for i in range(1, min(11, len(bars))):
                if i >= len(bars):
                    break
                    
                yesterday_close = bars[i-1].get('c', 0)
                today_open = bars[i].get('o', 0)
                
                if yesterday_close > 0:
                    gap = abs((today_open - yesterday_close) / yesterday_close)
                    
                    if gap >= 0.25:
                        self.stats['removed_gap_risk'] += 1
                        self.rejected['gap_risk'].append({
                            'ticker': ticker,
                            'reason': f"{gap*100:.0f}% gap on day {i}",
                            'data': explosion
                        })
                        return False
                        
            return True
            
        except:
            return True
    
    def check_crash_speed(self, explosion: Dict, ticker: str) -> bool:
        """Filter 4: Check if drop from 500% to <200% in 5 days"""
        
        if explosion['gain_pct'] < 500:
            return True
            
        peak_dt = datetime.strptime(explosion['peak_date'], '%Y-%m-%d')
        base_price = explosion['base_price']
        
        start_date = explosion['peak_date']
        end_date = (peak_dt + timedelta(days=6)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return True
                
            data = response.json()
            bars = data.get('results', [])
            
            if len(bars) < 5:
                return True
                
            for day, bar in enumerate(bars[1:6], 1):
                low = bar.get('l', 0)
                if low > 0:
                    gain = ((low - base_price) / base_price) * 100
                    if gain < 200:
                        self.stats['removed_crash_speed'] += 1
                        self.rejected['crash_speed'].append({
                            'ticker': ticker,
                            'reason': f"Dropped to {gain:.0f}% gain on day {day}",
                            'data': explosion
                        })
                        return False
                        
            return True
            
        except:
            return True
    
    def check_pump_dump(self, ticker: str, peak_date: str, peak_price: float, explosion: Dict) -> bool:
        """Filter 5: Standard pump & dump check"""
        
        peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
        start_date = peak_date
        end_date = (peak_dt + timedelta(days=6)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return True
                
            data = response.json()
            bars = data.get('results', [])
            
            if len(bars) < 5:
                return True
                
            five_day_low = min([b.get('l', peak_price) for b in bars[1:6]])
            drop_pct = ((peak_price - five_day_low) / peak_price) * 100
            
            if drop_pct >= 20:
                self.stats['removed_pump_dump'] += 1
                self.rejected['pump_dump'].append({
                    'ticker': ticker,
                    'reason': f"{drop_pct:.0f}% drop in 5 days",
                    'data': explosion
                })
                return False
                
            return True
            
        except:
            return True
    
    def filter_explosion(self, explosion: Dict) -> bool:
        """Run all filters on a single explosion"""
        
        if not self.filter_bad_data(explosion):
            return False
        
        ticker = explosion['ticker']
        
        if not self.check_pre_catalyst_liquidity(ticker, explosion['catalyst_date'], explosion):
            return False
        
        if not self.check_gap_risk(ticker, explosion['peak_date'], explosion):
            return False
        
        if not self.check_crash_speed(explosion, ticker):
            return False
        
        if not self.check_pump_dump(ticker, explosion['peak_date'], explosion['peak_price'], explosion):
            return False
        
        return True
    
    def process_file(self, input_file: str, output_file: str):
        """Process a complete scan file"""
        
        print(f"\nProcessing {input_file}...")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data.get('discoveries', [])
        self.stats['total_input'] = len(explosions)
        
        print(f"Found {len(explosions)} explosions to filter")
        
        clean_explosions = []
        
        for i, explosion in enumerate(explosions):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(explosions)}")
            
            if self.filter_explosion(explosion):
                clean_explosions.append(explosion)
                self.stats['total_passed'] += 1
            
            if i % 5 == 0:
                time.sleep(0.1)
        
        # Save clean data
        output_data = {
            'filter_date': datetime.now().isoformat(),
            'filter_stats': self.stats,
            'total_explosions': len(clean_explosions),
            'discoveries': clean_explosions
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Save rejected stocks
        rejected_file = 'REJECTED_EXPLOSIONS.json'
        with open(rejected_file, 'w') as f:
            json.dump({
                'filter_date': datetime.now().isoformat(),
                'filter_stats': self.stats,
                'rejected_by_category': self.rejected
            }, f, indent=2)
        
        # Print summary
        print("\n" + "="*50)
        print("FILTERING COMPLETE")
        print("="*50)
        print(f"Input explosions: {self.stats['total_input']}")
        print(f"Removed - Bad data: {self.stats['removed_bad_data']}")
        print(f"Removed - Low liquidity: {self.stats['removed_low_liquidity']}")
        print(f"Removed - Gap risk: {self.stats['removed_gap_risk']}")
        print(f"Removed - Crash speed: {self.stats['removed_crash_speed']}")
        print(f"Removed - Pump & dump: {self.stats['removed_pump_dump']}")
        print(f"PASSED ALL FILTERS: {self.stats['total_passed']}")
        print(f"Pass rate: {(self.stats['total_passed']/self.stats['total_input']*100):.1f}%")
        print(f"\nRejected stocks saved to: {rejected_file}")

def main():
    filter = ExplosionFilter(POLYGON_API_KEY)
    
    input_file = 'FINAL_SCAN.json'
    output_file = 'CLEAN_EXPLOSIONS.json'
    
    filter.process_file(input_file, output_file)

if __name__ == "__main__":
    main()
