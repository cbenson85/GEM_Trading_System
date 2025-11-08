"""
FORCE check and fix ALL catalyst dates by finding first 100% spike
"""

import json
import requests
import os
from datetime import datetime, timedelta
import time

def main():
    print("=" * 60)
    print("FORCE FIXING ALL CATALYST DATES")
    print("=" * 60)
    
    # Load data
    with open('Verified_Backtest_Data/explosive_stocks_CLEAN.json', 'r') as f:
        data = json.load(f)
    
    # Handle structure
    if isinstance(data, dict) and 'stocks' in data:
        stocks = data['stocks']
        print(f"Found {len(stocks)} stocks in 'stocks' key")
    else:
        stocks = data
        print(f"Found {len(stocks)} stocks as list")
    
    # FORCE CHECK FIRST 10 STOCKS
    print("\n" + "=" * 60)
    print("CHECKING FIRST 10 STOCKS (FORCED)")
    print("=" * 60)
    
    api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
    
    for i, stock in enumerate(stocks[:10]):
        ticker = stock.get('ticker')
        entry_date = stock.get('entry_date')
        current_catalyst = stock.get('catalyst_date')
        
        print(f"\n[{i+1}/10] {ticker}")
        print(f"  Current catalyst: {current_catalyst}")
        print(f"  Entry date: {entry_date}")
        
        if not entry_date:
            print("  ❌ No entry date - skipping")
            continue
        
        # FORCE API CALL regardless of current catalyst date
        print(f"  🔍 Fetching price data from Polygon...")
        
        # Get 180 days of data after entry
        entry_dt = datetime.fromisoformat(entry_date)
        start_date = entry_date
        end_date = (entry_dt + timedelta(days=180)).strftime('%Y-%m-%d')
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': api_key, 'adjusted': 'true', 'sort': 'asc'}
        
        try:
            response = requests.get(url, params=params)
            print(f"  API Response: {response.status_code}")
            
            if response.status_code == 200:
                data_response = response.json()
                
                if data_response.get('status') == 'OK' and data_response.get('results'):
                    bars = data_response['results']
                    print(f"  ✅ Got {len(bars)} price bars")
                    
                    if len(bars) > 1:
                        # Find first 100% spike
                        baseline = bars[0]['c']
                        print(f"  Baseline price: ${baseline:.4f}")
                        
                        catalyst_found = None
                        for j, bar in enumerate(bars[1:], 1):
                            gain_pct = ((bar['c'] - baseline) / baseline) * 100
                            
                            if gain_pct >= 100:
                                date = datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d')
                                print(f"  🎯 Found 100%+ on {date}: ${bar['c']:.4f} ({gain_pct:.1f}%)")
                                catalyst_found = date
                                
                                # Update the stock
                                stock['catalyst_date_FIXED'] = date
                                stock['original_catalyst'] = current_catalyst
                                break
                        
                        if not catalyst_found:
                            print(f"  ⚠️ No 100%+ spike found in data")
                    else:
                        print(f"  ❌ Not enough data")
                else:
                    print(f"  ❌ No results in response")
            else:
                print(f"  ❌ API error: {response.text[:200]}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Rate limit
        time.sleep(0.5)
    
    # Save results
    output_file = 'Verified_Backtest_Data/explosive_stocks_FORCED_FIX.json'
    
    if isinstance(data, dict) and 'stocks' in data:
        data['stocks'] = stocks
        save_data = data
    else:
        save_data = stocks
    
    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"Saved to: {output_file}")
    print("Check the output to see if catalyst dates were found")

if __name__ == "__main__":
    main()
