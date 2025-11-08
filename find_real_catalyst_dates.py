"""
Find Real Catalyst Dates by detecting first 100%+ price spike
"""

import json
import requests
import os
from datetime import datetime, timedelta
import time

class CatalystDateFinder:
    def __init__(self):
        self.polygon_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
    
    def find_catalyst_date(self, ticker, entry_date, year_discovered):
        """Find when stock first jumped 100%+ after entry date"""
        print(f"\n🔍 Finding catalyst for {ticker}")
        print(f"   Entry: {entry_date}, Year: {year_discovered}")
        
        # Start from entry date
        start_date = entry_date
        
        # Look for up to 180 days after entry
        entry_dt = datetime.fromisoformat(entry_date)
        end_dt = entry_dt + timedelta(days=180)
        end_date = end_dt.strftime('%Y-%m-%d')
        
        # Get daily price data
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {
            'apiKey': self.polygon_key,
            'adjusted': 'true',
            'sort': 'asc'
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"   ❌ API error: {response.status_code}")
                return None
            
            data = response.json()
            
            if data.get('status') != 'OK' or not data.get('results'):
                print(f"   ❌ No data found")
                return None
            
            bars = data['results']
            
            if len(bars) < 2:
                print(f"   ❌ Insufficient data")
                return None
            
            # Get baseline price (first bar or entry price)
            baseline_price = bars[0]['c']
            print(f"   Baseline price: ${baseline_price:.4f}")
            
            # Find first 100%+ spike
            catalyst_date = None
            catalyst_price = None
            max_gain = 0
            
            for i, bar in enumerate(bars[1:], 1):
                current_price = bar['c']
                gain_pct = ((current_price - baseline_price) / baseline_price) * 100
                
                # Update max gain
                if gain_pct > max_gain:
                    max_gain = gain_pct
                
                # First time hitting 100%+ gain?
                if gain_pct >= 100 and catalyst_date is None:
                    catalyst_date = datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d')
                    catalyst_price = current_price
                    print(f"   🎯 Found 100%+ spike on {catalyst_date}")
                    print(f"      Price: ${baseline_price:.4f} → ${current_price:.4f} ({gain_pct:.1f}%)")
                    
                    # Continue checking to verify it goes to 500%+
                    continue_checking = True
                    for future_bar in bars[i:min(i+30, len(bars))]:
                        future_gain = ((future_bar['c'] - baseline_price) / baseline_price) * 100
                        if future_gain >= 500:
                            print(f"   ✅ Confirmed! Reached {future_gain:.1f}% gain")
                            return catalyst_date
                    
                    # If it hit 100%+ but didn't reach 500%+, keep looking
                    if max_gain < 500:
                        print(f"   ⚠️ Only reached {max_gain:.1f}% - not a true catalyst")
                        catalyst_date = None
                        catalyst_price = None
            
            if catalyst_date:
                return catalyst_date
            else:
                print(f"   ❌ No catalyst found (max gain: {max_gain:.1f}%)")
                # If we found big gains but no clear catalyst, use entry + days_to_peak as estimate
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def process_stocks(self, stocks):
        """Process all stocks to find real catalyst dates"""
        fixed_count = 0
        failed_count = 0
        
        for stock in stocks:
            ticker = stock['ticker']
            entry_date = stock.get('entry_date')
            catalyst_date = stock.get('catalyst_date')
            year_discovered = stock.get('year_discovered')
            
            # Check if catalyst date needs fixing
            needs_fix = False
            
            if catalyst_date:
                try:
                    catalyst_dt = datetime.fromisoformat(catalyst_date)
                    if catalyst_dt > datetime.now():
                        print(f"\n❌ {ticker}: Future catalyst date {catalyst_date} - NEEDS FIX")
                        needs_fix = True
                except:
                    needs_fix = True
            
            if needs_fix and entry_date:
                # Find the real catalyst date
                real_catalyst = self.find_catalyst_date(ticker, entry_date, year_discovered)
                
                if real_catalyst:
                    stock['catalyst_date'] = real_catalyst
                    stock['catalyst_date_fixed'] = True
                    stock['original_catalyst_date'] = catalyst_date
                    fixed_count += 1
                    print(f"   ✅ Fixed: {catalyst_date} → {real_catalyst}")
                else:
                    # Fallback: estimate from entry_date + days_to_peak
                    days_to_peak = stock.get('days_to_peak', 1)
                    entry_dt = datetime.fromisoformat(entry_date)
                    estimated_catalyst = (entry_dt + timedelta(days=days_to_peak)).strftime('%Y-%m-%d')
                    stock['catalyst_date'] = estimated_catalyst
                    stock['catalyst_date_estimated'] = True
                    stock['original_catalyst_date'] = catalyst_date
                    failed_count += 1
                    print(f"   ⚠️ Estimated: {estimated_catalyst} (entry + {days_to_peak} days)")
                
                # Rate limit
                time.sleep(0.2)
        
        return fixed_count, failed_count

def main():
    print("="*60)
    print("FINDING REAL CATALYST DATES")
    print("="*60)
    
    # Load the data
    input_file = 'Verified_Backtest_Data/explosive_stocks_CLEAN.json'
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Get stocks list from structure
    if isinstance(data, dict) and 'stocks' in data:
        stocks = data['stocks']
        wrapper = data  # Keep the wrapper
    else:
        stocks = data
        wrapper = None
    
    print(f"Loaded {len(stocks)} stocks")
    
    # Find stocks with bad catalyst dates
    bad_dates = []
    for stock in stocks:
        catalyst_date = stock.get('catalyst_date')
        if catalyst_date:
            try:
                catalyst_dt = datetime.fromisoformat(catalyst_date)
                if catalyst_dt > datetime.now():
                    bad_dates.append(stock['ticker'])
            except:
                bad_dates.append(stock['ticker'])
    
    print(f"\nStocks with bad catalyst dates: {len(bad_dates)}")
    if bad_dates:
        print(f"  {', '.join(bad_dates[:10])}")
    
    # Process stocks to find real catalyst dates
    finder = CatalystDateFinder()
    fixed_count, failed_count = finder.process_stocks(stocks)
    
    # Save the corrected data
    output_file = 'Verified_Backtest_Data/explosive_stocks_CATALYST_FIXED.json'
    
    if wrapper:
        wrapper['stocks'] = stocks
        save_data = wrapper
    else:
        save_data = stocks
    
    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    print("\n" + "="*60)
    print(f"COMPLETE")
    print("="*60)
    print(f"Fixed: {fixed_count} stocks")
    print(f"Estimated: {failed_count} stocks")
    print(f"Saved to: {output_file}")
    
    # Show sample
    print("\nSAMPLE FIXED DATA:")
    for stock in stocks[:5]:
        if stock.get('catalyst_date_fixed') or stock.get('catalyst_date_estimated'):
            print(f"{stock['ticker']:6} | Original: {stock.get('original_catalyst_date')} → Fixed: {stock['catalyst_date']}")

if __name__ == "__main__":
    main()
