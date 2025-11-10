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
            'removed_data_errors': 0,
            'removed_no_liquidity': 0,
            'removed_pump_dump': 0,
            'total_passed': 0
        }
        self.removed = []
        
    def filter_data_errors(self, explosion: Dict) -> bool:
        """Remove obvious data errors and corporate actions"""
        
        # Price/gain outliers
        if explosion['peak_price'] > 25000:
            self.stats['removed_data_errors'] += 1
            self.removed.append({
                'ticker': explosion['ticker'],
                'reason': f"Peak price ${explosion['peak_price']} > $25,000",
                'data': explosion
            })
            return False
            
        if explosion['gain_pct'] > 40000:
            self.stats['removed_data_errors'] += 1
            self.removed.append({
                'ticker': explosion['ticker'],
                'reason': f"Gain {explosion['gain_pct']:.0f}% > 40,000%",
                'data': explosion
            })
            return False
            
        return True
    
    def check_minimum_liquidity(self, ticker: str, catalyst_date: str, explosion: Dict) -> bool:
        """Check pre-catalyst liquidity requirements"""
        
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
            
            if len(bars) < 20:
                self.stats['removed_no_liquidity'] += 1
                self.removed.append({
                    'ticker': ticker,
                    'reason': f"Less than 20 trading days pre-catalyst",
                    'data': explosion
                })
                return False
            
            avg_volume = sum([b.get('v', 0) for b in bars]) / len(bars)
            avg_price = sum([b.get('c', 0) for b in bars]) / len(bars)
            avg_dollar_volume = avg_volume * avg_price
            
            if avg_volume < 25000:
                self.stats['removed_no_liquidity'] += 1
                self.removed.append({
                    'ticker': ticker,
                    'reason': f"Volume {avg_volume:.0f} shares/day < 25,000",
                    'data': explosion
                })
                return False
                
            if avg_price < 0.25:
                self.stats['removed_no_liquidity'] += 1
                self.removed.append({
                    'ticker': ticker,
                    'reason': f"Price ${avg_price:.3f} < $0.25",
                    'data': explosion
                })
                return False
            
            # Add liquidity metrics to explosion
            explosion['pre_catalyst_volume'] = int(avg_volume)
            explosion['pre_catalyst_price'] = round(avg_price, 3)
            explosion['pre_catalyst_dollar_volume'] = int(avg_dollar_volume)
                
            return True
            
        except:
            return False
    
    def check_pump_and_dump(self, ticker: str, peak_date: str, explosion: Dict) -> bool:
        """Check for 80%+ overnight gap in 4 days after peak"""
        
        peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
        start_date = peak_date
        end_date = (peak_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return True  # Keep if can't verify
                
            data = response.json()
            bars = data.get('results', [])
            
            if len(bars) < 2:
                return True
            
            for i in range(1, min(5, len(bars))):
                prev_close = bars[i-1].get('c', 0)
                curr_open = bars[i].get('o', 0)
                
                if prev_close > 0:
                    gap_pct = abs((curr_open - prev_close) / prev_close) * 100
                    if gap_pct >= 80:
                        self.stats['removed_pump_dump'] += 1
                        self.removed.append({
                            'ticker': ticker,
                            'reason': f"Pump & dump - {gap_pct:.0f}% gap on day {i} after peak",
                            'data': explosion
                        })
                        return False
            return True
            
        except:
            return True
    
    def tag_explosion_type(self, explosion: Dict) -> Dict:
        """Tag explosion characteristics"""
        
        ticker = explosion['ticker']
        
        # Security type
        if ticker.endswith('W'):
            explosion['security_type'] = 'warrant'
        elif ticker.endswith('R'):
            explosion['security_type'] = 'rights'
        elif ticker.endswith('U'):
            explosion['security_type'] = 'unit'
        else:
            explosion['security_type'] = 'common'
        
        # Gain tier
        gain = explosion['gain_pct']
        if gain < 1000:
            explosion['gain_tier'] = 'standard'
        elif gain < 2000:
            explosion['gain_tier'] = 'high'
        elif gain < 5000:
            explosion['gain_tier'] = 'extreme'
        elif gain < 10000:
            explosion['gain_tier'] = 'super'
        else:
            explosion['gain_tier'] = 'lottery'
        
        # Price tier (using pre-catalyst price if available)
        price = explosion.get('pre_catalyst_price', explosion['base_price'])
        if price < 1.0:
            explosion['price_tier'] = 'penny'
        elif price < 10.0:
            explosion['price_tier'] = 'small_cap'
        else:
            explosion['price_tier'] = 'mid_cap'
            
        return explosion
    
    def process_file(self, input_file: str, output_file: str):
        """Process the scan file with comprehensive filtering"""
        
        print(f"\nProcessing {input_file}...")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data.get('discoveries', [])
        self.stats['total_input'] = len(explosions)
        
        print(f"Found {len(explosions)} explosions to process")
        print("Applying filters...")
        
        clean_explosions = []
        
        for i, explosion in enumerate(explosions):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(explosions)}")
            
            # Step 1: Filter data errors
            if not self.filter_data_errors(explosion):
                continue
            
            ticker = explosion['ticker']
            
            # Step 2: Check liquidity (also adds metrics)
            if not self.check_minimum_liquidity(ticker, explosion['catalyst_date'], explosion):
                continue
            
            # Step 3: Check pump and dump
            if not self.check_pump_and_dump(ticker, explosion['peak_date'], explosion):
                continue
            
            # Step 4: Tag characteristics
            tagged_explosion = self.tag_explosion_type(explosion)
            clean_explosions.append(tagged_explosion)
            self.stats['total_passed'] += 1
            
            # Small delay to avoid API rate limits
            if i % 5 == 0:
                time.sleep(0.1)
        
        # Sort by gain
        clean_explosions.sort(key=lambda x: x['gain_pct'], reverse=True)
        
        # Save results
        output_data = {
            'filter_date': datetime.now().isoformat(),
            'filter_stats': self.stats,
            'total_explosions': len(clean_explosions),
            'discoveries': clean_explosions
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Save removed stocks
        if self.removed:
            with open('REMOVED_EXPLOSIONS.json', 'w') as f:
                json.dump({
                    'filter_date': datetime.now().isoformat(),
                    'removed_count': len(self.removed),
                    'removed': self.removed
                }, f, indent=2)
        
        # Print summary
        print("\n" + "="*50)
        print("FILTER COMPLETE")
        print("="*50)
        print(f"Input: {self.stats['total_input']}")
        print(f"Removed data errors: {self.stats['removed_data_errors']}")
        print(f"Removed low liquidity: {self.stats['removed_no_liquidity']}")
        print(f"Removed pump & dump: {self.stats['removed_pump_dump']}")
        print(f"PASSED: {self.stats['total_passed']}")
        print(f"Pass rate: {(self.stats['total_passed']/self.stats['total_input']*100):.1f}%")

def main():
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
        
    filter = ExplosionFilter(POLYGON_API_KEY)
    
    input_file = os.environ.get('INPUT_FILE', 'FINAL_SCAN.json')
    output_file = 'CLEAN_EXPLOSIONS.json'
    
    filter.process_file(input_file, output_file)

if __name__ == "__main__":
    main()
