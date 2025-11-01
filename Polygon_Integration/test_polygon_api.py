#!/usr/bin/env python3
"""
GEM Trading System - Debug Version
Tests Polygon API connection and data retrieval
"""

import os
import requests
from datetime import datetime

# Configuration
API_KEY = os.environ.get('POLYGON_API_KEY')

def test_api_connection():
    """Test basic API connectivity."""
    print("\n" + "="*60)
    print("POLYGON API CONNECTION TEST")
    print("="*60)
    
    if not API_KEY:
        print("❌ ERROR: POLYGON_API_KEY not set")
        return False
    
    print(f"✅ API Key found (length: {len(API_KEY)})")
    
    # Test 1: Simple ticker request
    print("\n--- Test 1: Single Ticker Request ---")
    url = f"https://api.polygon.io/v3/reference/tickers/AAPL"
    params = {'apiKey': API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully retrieved AAPL data")
            print(f"Response keys: {list(data.keys())}")
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    # Test 2: Market snapshot
    print("\n--- Test 2: Market Snapshot ---")
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
    params = {'apiKey': API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            tickers = data.get('tickers', [])
            print(f"✅ Market snapshot retrieved")
            print(f"Total tickers: {len(tickers)}")
            print(f"Response keys: {list(data.keys())}")
            
            if len(tickers) > 0:
                print(f"\nSample ticker data:")
                sample = tickers[0]
                print(f"  Ticker: {sample.get('ticker', 'N/A')}")
                print(f"  Day data keys: {list(sample.get('day', {}).keys())}")
                print(f"  Sample day data: {sample.get('day', {})}")
            else:
                print("⚠️ No tickers returned (market might be closed)")
                
        elif response.status_code == 429:
            print(f"❌ Rate limit exceeded")
            return False
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    return True

def main():
    """Run API tests."""
    print(f"Current Time: {datetime.now()}")
    print(f"Current Day: {datetime.now().strftime('%A')}")
    
    # Check if market hours (roughly)
    hour = datetime.now().hour
    day = datetime.now().weekday()  # 0=Monday, 6=Sunday
    
    if day >= 5:
        print("⚠️ Weekend - Market is closed")
    elif hour < 9 or hour >= 16:
        print("⚠️ Outside market hours (9 AM - 4 PM ET)")
    else:
        print("✅ During market hours")
    
    success = test_api_connection()
    
    if not success:
        print("\n❌ API tests failed - check your API key and subscription level")
        exit(1)
    else:
        print("\n✅ API is working correctly")
        exit(0)

if __name__ == "__main__":
    main()
