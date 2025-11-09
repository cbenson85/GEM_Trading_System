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
            'tagged_volatile': 0,
            'tagged_sustained': 0,
            'total_passed': 0
        }
        self.removed = []
        
    def filter_data_errors(self, explosion: Dict) -> bool:
        """Only remove OBVIOUS data errors"""
        
        # Remove extreme price errors
        if explosion['peak_price'] > 20000:
            self.stats['removed_data_errors'] += 1
            self.removed.append({
                'ticker': explosion['ticker'],
                'reason': f"Peak price ${explosion['peak_price']} (data error)",
                'data': explosion
            })
            return False
            
        if explosion['base_price'] < 0.01 or explosion['base_price'] > 10000:
            self.stats['removed_data_errors'] += 1
            self.removed.append({
                'ticker': explosion['ticker'],
                'reason': f"Base price ${explosion['base_price']} (data error)",
                'data': explosion
            })
            return False
            
        # Remove impossible gains
        if explosion['gain_pct'] > 20000:
            self.stats['removed_data_errors'] += 1
            self.removed.append({
                'ticker': explosion['ticker'],
                'reason': f"Gain {explosion['gain_pct']:.0f}% (likely split/adjustment error)",
                'data': explosion
            })
            return False
            
        return True
    
    def check_minimum_liquidity(self, ticker: str, catalyst_date: str, explosion: Dict) -> bool:
        """Very minimal liquidity check - just avoid complete garbage"""
        
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
            
            if len(bars) < 20:  # Need some trading history
                return False
            
            avg_volume = sum([b.get('v', 0) for b in bars]) / len(bars)
            avg_price = sum([b.get('c', 0) for b in bars]) / len(bars)
            
            # VERY minimal requirements - just filter out true garbage
            if avg_volume < 1000:  # Less than 1k shares/day is untradeable
                self.stats['removed_no_liquidity'] += 1
                self.removed.append({
                    'ticker': ticker,
                    'reason': f"Volume {avg_volume:.0f} shares/day (untradeable)",
                    'data': explosion
                })
                return False
            
            if avg_price < 0.05:  # Sub-nickel stocks are too manipulated
                self.stats['removed_no_liquidity'] += 1
                self.removed.append({
                    'ticker': ticker,
                    'reason': f"Price ${avg_price:.3f} (sub-nickel)",
                    'data': explosion
                })
                return False
                
            return True
            
        except:
            return False
    
    def tag_exit_quality(self, ticker: str, peak_date: str, peak_price: float, explosion: Dict) -> str:
        """Tag as volatile vs sustained - don't filter, just categorize"""
        
        peak_dt = datetime.strptime(peak_date, '%Y-%m-%d')
        start_date = peak_date
        end_date = (peak_dt + timedelta(days=6)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return "unknown"
                
            data = response.json()
            bars = data.get('results', [])
            
            if len(bars) < 5:
                return "unknown"
                
            # Calculate 5-day drop
            five_day_low = min([b.get('l', peak_price) for b in bars[1:6]])
            drop_pct = ((peak_price - five_day_low) / peak_price) * 100
            
            # Tag based on exit behavior
            if drop_pct >= 30:
                self.stats['tagged_volatile'] += 1
                return "volatile_exit"
            else:
                self.stats['tagged_sustained'] += 1
                return "sustained_move"
                
        except:
            return "unknown"
    
    def process_explosion(self, explosion: Dict) -> Dict:
        """Process and tag a single explosion"""
        
        # Add exit quality tag
        explosion['exit_quality'] = self.tag_exit_quality(
            explosion['ticker'],
            explosion['peak_date'],
            explosion['peak_price'],
            explosion
        )
        
        # Add liquidity score for reference
        explosion['pre_catalyst_liquidity'] = "unknown"
        
        # Add data quality flag
        explosion['data_quality'] = "clean"
        
        return explosion
    
    def process_file(self, input_file: str, output_file: str):
        """Process the scan file with minimal filtering"""
        
        print(f"\nProcessing {input_file}...")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data.get('discoveries', [])
        self.stats['total_input'] = len(explosions)
        
        print(f"Found {len(explosions)} explosions to process")
        print("Applying minimal filters and tagging...")
        
        clean_explosions = []
        
        for i, explosion in enumerate(explosions):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(explosions)}")
            
            # Only filter out extreme garbage
            if not self.filter_data_errors(explosion):
                continue
                
            ticker = explosion['ticker']
            
            # Minimal liquidity check
            if not self.check_minimum_liquidity(ticker, explosion['catalyst_date'], explosion):
                continue
            
            # Process and tag the explosion
            tagged_explosion = self.process_explosion(explosion)
            clean_explosions.append(tagged_explosion)
            self.stats['total_passed'] += 1
            
            # Small delay to avoid API rate limits
            if i % 5 == 0:
                time.sleep(0.1)
        
        # Save results
        output_data = {
            'filter_date': datetime.now().isoformat(),
            'filter_stats': self.stats,
            'total_explosions': len(clean_explosions),
            'discoveries': clean_explosions
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Save removed stocks (minimal)
        if self.removed:
            with open('REMOVED_ERRORS.json', 'w') as f:
                json.dump({
                    'filter_date': datetime.now().isoformat(),
                    'removed_count': len(self.removed),
                    'removed': self.removed
                }, f, indent=2)
        
        # Print summary
        print("\n" + "="*50)
        print("PROCESSING COMPLETE")
        print("="*50)
        print(f"Input explosions: {self.stats['total_input']}")
        print(f"Removed data errors: {self.stats['removed_data_errors']}")
        print(f"Removed no liquidity: {self.stats['removed_no_liquidity']}")
        print(f"TOTAL KEPT: {self.stats['total_passed']}")
        print(f"\nTagged as volatile exit: {self.stats['tagged_volatile']}")
        print(f"Tagged as sustained move: {self.stats['tagged_sustained']}")
        print(f"\nPass rate: {(self.stats['total_passed']/self.stats['total_input']*100):.1f}%")

def main():
    filter = ExplosionFilter(POLYGON_API_KEY)
    
    input_file = 'FINAL_SCAN.json'
    output_file = 'CLEAN_EXPLOSIONS.json'
    
    filter.process_file(input_file, output_file)

if __name__ == "__main__":
    main()
