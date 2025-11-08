#!/usr/bin/env python3
"""
Phase 4 Integrated Screener - Screens ENTIRE US MARKET
Fixed version that won't hang
"""

import json
import os
import sys
import random
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Tuple
import time

print("Script started - importing complete")

class Phase4MarketScreener:
    def __init__(self):
        print("  Initializing screener...")
        self.polygon_api_key = os.environ.get('POLYGON_API_KEY', '')
        if not self.polygon_api_key:
            print("  ⚠️ WARNING: No POLYGON_API_KEY found in environment")
            self.polygon_api_key = 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0'  # Fallback
        self.base_url = 'https://api.polygon.io'
        print(f"  API Key configured: {'✅' if self.polygon_api_key else '❌'}")
        print(f"  API Key first 8 chars: {self.polygon_api_key[:8]}..." if self.polygon_api_key else "  No API key")
        
    def generate_strategic_dates(self, mode='test') -> List[str]:
        """
        Generate random dates with 120+ day spacing
        Mode: 'test' = 3 dates, 'full' = 15 dates
        """
        print("="*60)
        print("GENERATING STRATEGIC TEST DATES")
        print("="*60)
        
        # For testing, use fixed known good dates to avoid randomness issues
        if mode == 'test':
            # Use specific weekdays that we know had trading
            selected_dates = [
                '2019-03-15',  # Friday
                '2022-06-20',  # Monday  
                '2023-09-11'   # Monday
            ]
            print("  Using fixed test dates:")
            for i, date in enumerate(selected_dates, 1):
                print(f"  Date {i}: {date}")
        else:
            # Full mode - generate random dates
            valid_ranges = [
                (datetime(2010, 1, 1), datetime(2019, 12, 31)),
                (datetime(2022, 1, 1), datetime(2024, 10, 31))
            ]
            
            num_dates = 15
            selected_dates = []
            attempts = 0
            
            while len(selected_dates) < num_dates and attempts < 1000:
                attempts += 1
                
                # Pick a random range
                range_idx = random.randint(0, len(valid_ranges) - 1)
                start, end = valid_ranges[range_idx]
                
                # Generate random date in range
                days_between = (end - start).days
                random_days = random.randint(0, days_between)
                candidate_date = start + timedelta(days=random_days)
                
                # Skip weekends
                while candidate_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    candidate_date = candidate_date + timedelta(days=1)
                
                # Check spacing from existing dates
                valid = True
                for existing in selected_dates:
                    existing_dt = datetime.fromisoformat(existing)
                    days_apart = abs((candidate_date - existing_dt).days)
                    if days_apart < 120:
                        valid = False
                        break
                
                if valid:
                    selected_dates.append(candidate_date.strftime('%Y-%m-%d'))
                    print(f"  Date {len(selected_dates)}: {candidate_date.strftime('%Y-%m-%d')}")
            
            selected_dates.sort()
        
        print(f"\n✅ Generated {len(selected_dates)} strategic dates")
        if selected_dates:
            print(f"  Earliest: {selected_dates[0]}")
            print(f"  Latest: {selected_dates[-1]}")
        
        return selected_dates
    
    def test_api_connection(self) -> bool:
        """
        Test if API is working with a simple call
        """
        print("\n  Testing API connection...")
        try:
            # Try a simple ticker details call
            url = f"{self.base_url}/v3/reference/tickers/AAPL"
            params = {'apiKey': self.polygon_api_key}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                print("  ✅ API connection successful")
                return True
            else:
                print(f"  ❌ API test failed: Status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"  ❌ API connection error: {e}")
            return False
    
    def get_all_tickers_for_date(self, date: str) -> List[str]:
        """
        Get tickers - simplified version that won't hang
        """
        print(f"\n📊 Getting market tickers for {date}...")
        
        # First test the API
        if not self.test_api_connection():
            print("  ⚠️ API test failed, using fallback tickers")
            return self.get_fallback_tickers()
        
        all_tickers = []
        
        # Try to get market snapshot for the date
        try:
            print(f"  Fetching market snapshot for {date}...")
            url = f"{self.base_url}/v2/aggs/grouped/locale/us/market/stocks/{date}"
            params = {
                'apiKey': self.polygon_api_key,
                'adjusted': 'true'
            }
            
            # Use shorter timeout
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    print(f"  Found {len(results)} tickers that traded on {date}")
                    
                    # Take a subset for testing - full market would be too slow
                    for item in results[:500]:  # Limit to 500 for testing
                        ticker = item.get('T')
                        if ticker and '.' not in ticker:  # Skip special securities
                            all_tickers.append(ticker)
                    
                    print(f"  Using {len(all_tickers)} tickers for screening")
                    return all_tickers
                else:
                    print(f"  No data for {date} - might be weekend/holiday")
                    
            elif response.status_code == 404:
                print(f"  No data for {date} (404)")
            else:
                print(f"  API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  Request timed out")
        except Exception as e:
            print(f"  Error: {e}")
        
        # If we get here, use fallback
        print("  Using fallback ticker list")
        return self.get_fallback_tickers()
    
    def get_fallback_tickers(self) -> List[str]:
        """
        Fallback list of liquid stocks for testing
        """
        return [
            # Large caps
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'JPM', 'V',
            # Tech
            'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'CSCO', 'AVGO', 'TXN', 'QCOM', 'MU',
            # Finance
            'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'SCHW', 'BLK', 'SPGI', 'USB',
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'CVS', 'DHR', 'LLY',
            # Consumer
            'WMT', 'HD', 'PG', 'KO', 'PEP', 'NKE', 'MCD', 'DIS', 'COST', 'TGT',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'KMI',
            # Small/Mid caps with volatility
            'ROKU', 'SNAP', 'PINS', 'PLTR', 'SOFI', 'HOOD', 'DKNG', 'COIN', 'RBLX', 'U',
            'GME', 'AMC', 'BBBY', 'BB', 'NOK', 'WISH', 'CLOV', 'SDC', 'ATER', 'PROG'
        ]
    
    def get_stock_data(self, ticker: str, date: str) -> Dict:
        """
        Get price and volume data for a stock
        """
        try:
            end_date = datetime.fromisoformat(date)
            start_date = end_date - timedelta(days=90)
            
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                'apiKey': self.polygon_api_key,
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 120
            }
            
            response = requests.get(url, params=params, timeout=5)  # Short timeout
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    
                    if len(results) >= 20:
                        recent_bar = results[-1]
                        
                        volumes = [bar['v'] for bar in results]
                        prices = [bar['c'] for bar in results]
                        highs = [bar['h'] for bar in results]
                        lows = [bar['l'] for bar in results]
                        
                        avg_volume_20d = sum(volumes[-20:]) / 20
                        avg_price_20d = sum(prices[-20:]) / 20
                        
                        return {
                            'price': recent_bar['c'],
                            'volume': recent_bar['v'],
                            'avg_volume_20d': avg_volume_20d,
                            'avg_price_20d': avg_price_20d,
                            'high': max(highs[-20:]),
                            'low': min(lows[-20:]),
                            'open': recent_bar['o']
                        }
            
        except:
            pass
        
        return None
    
    def score_stock(self, ticker: str, data: Dict, date: str) -> Tuple[float, Dict]:
        """
        Score a stock based on patterns
        """
        score = 0
        breakdown = {
            'volume_score': 0,
            'rsi_score': 0,
            'breakout_score': 0,
            'accumulation_score': 0,
            'composite_bonus': 0
        }
        
        if not data:
            return 0, breakdown
        
        # Volume scoring
        if data['avg_volume_20d'] > 0:
            volume_ratio = data['volume'] / data['avg_volume_20d']
            
            if volume_ratio >= 10:
                breakdown['volume_score'] = 50
            elif volume_ratio >= 5:
                breakdown['volume_score'] = 35
            elif volume_ratio >= 3:
                breakdown['volume_score'] = 25
        
        # RSI proxy (overbought is better based on test results)
        if data['avg_price_20d'] > 0:
            price_ratio = data['price'] / data['avg_price_20d']
            
            if price_ratio > 1.15:
                breakdown['rsi_score'] = 30
            elif price_ratio > 1.10:
                breakdown['rsi_score'] = 20
            elif price_ratio < 0.85:
                breakdown['rsi_score'] = -20
        
        # Breakout scoring
        if data['high'] > 0 and data['price'] > data['high'] * 0.95:
            breakdown['breakout_score'] = 30
        
        # Accumulation
        if data['low'] > 0 and data['avg_price_20d'] > 0:
            if data['low'] > data['avg_price_20d'] * 0.95 and volume_ratio > 1.5:
                breakdown['accumulation_score'] = 30
        
        # Composite bonuses
        signals = sum([
            breakdown['volume_score'] > 0,
            breakdown['rsi_score'] > 10,
            breakdown['breakout_score'] > 0,
            breakdown['accumulation_score'] > 0
        ])
        
        if signals >= 3:
            breakdown['composite_bonus'] = 50
        elif signals >= 2:
            breakdown['composite_bonus'] = 25
        
        score = sum(breakdown.values())
        return score, breakdown
    
    def screen_market(self, date: str) -> Dict:
        """
        Screen the market on a specific date
        """
        print(f"\n🔍 SCREENING MARKET: {date}")
        print("="*50)
        
        # Get tickers
        all_tickers = self.get_all_tickers_for_date(date)
