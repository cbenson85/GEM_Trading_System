import json
import os
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
            'removed_corporate_action': 0,
            'total_passed': 0
        }
    
    def filter_bad_data(self, explosion: Dict) -> bool:
        """Filter 1: Remove obvious data errors"""
        
        # Price sanity checks
        if explosion['peak_price'] > 20000:
            self.stats['removed_bad_data'] += 1
            return False
        
        if explosion['base_price'] < 0.01:
            self.stats['removed_bad_data'] += 1
            return False
            
        # Gain sanity check
        if explosion['gain_pct'] > 20000:
            self.stats['removed_bad_data'] += 1
            return False
        
        # Days to peak sanity
        if explosion.get('days_to_peak', 0) < 3:  # Too fast to trade
            self.stats['removed_bad_data'] += 1
            return False
            
        return True
    
    def check_pre_catalyst_liquidity(self, ticker: str, catalyst_date: str) -> bool:
        """Filter 2: Check liquidity BEFORE the catalyst"""
        
        # Calculate date range for 50 days before catalyst
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
            
            if len(bars) < 30:  # Need decent data
                return False
            
            # Check average volume and price
            avg_volume = sum([b.get('v', 0) for b in bars]) / len(bars)
            avg_price = sum([b.get('c', 0) for b in bars]) / len(bars)
            
            # Must have 75,000+ volume and $0.50+ price
            if avg_volume < 75000 or avg_price < 0.50:
                self.stats['removed_low_liquidity'] += 1
                return False
                
            return True
            
        except:
            return False
    
    def check_gap_risk(self, ticker: str, peak_date: str) -> bool:
        """Filter 3: Check for catastrophic gaps after peak"""
        
        peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
        start_date = peak_date
        end_date = (peak_dt + timedelta(days=15)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return True  # Give benefit of doubt
                
            data = response.json()
            bars = data.get('results', [])
            
            # Check for overnight gaps
            for i in range(1, min(11, len(bars))):  # 10 days after peak
                if i >= len(bars):
                    break
                    
                yesterday_close = bars[i-1].get('c', 0)
                today_open = bars[i].get('o', 0)
                
                if yesterday_close > 0:
                    gap = abs((today_open - yesterday_close) / yesterday_close)
                    
                    # 25% gap = untradeable
                    if gap >= 0.25:
                        self.stats['removed_gap_risk'] += 1
                        return False
                        
            return True
            
        except:
            return True
    
    def check_crash_speed(self, explosion: Dict, ticker: str) -> bool:
        """Filter 4: Check if drop from 500% to <200% in 5 days"""
        
        if explosion['gain_pct'] < 500:
            return True  # Not applicable
            
        peak_dt = datetime.strptime(explosion['peak_date'], '%Y-%m-%d')
        base_price = explosion['base_price']
        
        # Get 5 days after peak
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
                
            # Check if it drops below 200% gain
            for bar in bars[1:6]:  # Days 1-5 after peak
                low = bar.get('l', 0)
                if low > 0:
                    gain = ((low - base_price) / base_price) * 100
                    if gain < 200:  # Dropped from 500%+ to <200%
                        self.stats['removed_crash_speed'] += 1
                        return False
                        
            return True
            
        except:
            return True
    
    def check_pump_dump(self, ticker: str, peak_date: str, peak_price: float) -> bool:
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
                
            # Find lowest in 5 days
            five_day_low = min([b.get('l', peak_price) for b in bars[1:6]])
            drop_pct = ((peak_price - five_day_low) / peak_price) * 100
            
            if drop_pct >= 20:
                self.stats['removed_pump_dump'] += 1
                return False
                
            return True
            
        except:
            return True
    
    def filter_explosion(self, explosion: Dict) -> bool:
        """Run all filters on a single explosion"""
        
        # Filter 1: Bad data
        if not self.filter_bad_data(explosion):
            return False
        
        ticker = explosion['ticker']
        
        # Filter 2: Pre-catalyst liquidity (expensive API call)
        if not self.check_pre_catalyst_liquidity(ticker, explosion['catalyst_date']):
            return False
        
        # Filter 3: Gap risk
        if not self.check_gap_risk(ticker, explosion['peak_date']):
            return False
        
        # Filter 4: Crash speed
        if not self.check_crash_speed(explosion, ticker):
            return False
        
        # Filter 5: Pump & dump
        if not self.check_pump_dump(ticker, explosion['peak_date'], explosion['peak_price']):
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
        
        # Filter explosions
        clean_explosions = []
        
        for i, explosion in enumerate(explosions):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(explosions)}")
            
            if self.filter_explosion(explosion):
                clean_explosions.append(explosion)
                self.stats['total_passed'] += 1
            
            # Add small delay to avoid API rate limits
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

def main():
    filter = ExplosionFilter(POLYGON_API_KEY)
    
    # Process the merged file
    input_file = 'FINAL_SCAN.json'  # Your merged results
    output_file = 'CLEAN_EXPLOSIONS.json'
    
    filter.process_file(input_file, output_file)

if __name__ == "__main__":
    main()
