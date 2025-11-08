#!/usr/bin/env python3
"""
Phase 4 Integrated Screener - Screens ENTIRE US MARKET
Fixed version with proper debugging and timeout handling
"""

import json
import os
import sys
import random
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Tuple
import time

class Phase4MarketScreener:
    def __init__(self):
        self.polygon_api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
        print(f"  API Key configured: {'✅' if self.polygon_api_key else '❌'}")
        print(f"  API Key length: {len(self.polygon_api_key) if self.polygon_api_key else 0}")
        
    def generate_strategic_dates(self, mode='test') -> List[str]:
        """
        Generate random dates with 120+ day spacing
        Mode: 'test' = 3 dates, 'full' = 15 dates
        """
        print("="*60)
        print("GENERATING STRATEGIC TEST DATES")
        print("="*60)
        
        # Date range: 2010-2024, excluding 2020-2021
        valid_ranges = [
            (datetime(2010, 1, 1), datetime(2019, 12, 31)),
            (datetime(2022, 1, 1), datetime(2024, 10, 31))
        ]
        
        num_dates = 3 if mode == 'test' else 15
        selected_dates = []
        
        # Generate dates with 120+ day spacing
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
                print(f"  Date {len(selected_dates)}: {candidate_date.strftime('%Y-%m-%d')} ({candidate_date.strftime('%A')})")
        
        # Sort dates chronologically
        selected_dates.sort()
        
        print(f"\n✅ Generated {len(selected_dates)} strategic dates")
        print(f"  Earliest: {selected_dates[0]}")
        print(f"  Latest: {selected_dates[-1]}")
        
        return selected_dates
    
    def get_all_tickers_for_date(self, date: str) -> List[str]:
        """
        Get ALL active tickers that were trading on a specific date
        Uses Polygon snapshots API for historical ticker lists
        """
        print(f"\n📊 Fetching ALL market tickers for {date}...")
        
        all_tickers = []
        
        # Method 1: Try to get snapshot of all tickers for that date
        print(f"  Attempting grouped daily endpoint...")
        try:
            # Use grouped daily endpoint to get all tickers that traded on that date
            url = f"{self.base_url}/v2/aggs/grouped/locale/us/market/stocks/{date}"
            params = {
                'apiKey': self.polygon_api_key,
                'adjusted': 'true'
            }
            
            print(f"  API URL: {url}")
            print(f"  Making request with 30 second timeout...")
            
            response = requests.get(url, params=params, timeout=30)
            
            print(f"  Response status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  Parsing JSON response...")
                data = response.json()
                
                status = data.get('status')
                results_count = data.get('resultsCount', 0)
                
                print(f"  Response status: {status}")
                print(f"  Results count: {results_count}")
                
                if status == 'OK' and data.get('results'):
                    results = data['results']
                    print(f"  Found {len(results)} tickers that traded on {date}")
                    
                    for item in results:
                        ticker = item.get('T')  # T is the ticker symbol in grouped daily
                        if ticker:
                            all_tickers.append(ticker)
                    
                    print(f"  ✅ Successfully loaded {len(all_tickers)} tickers from market snapshot")
                    return all_tickers
                else:
                    print(f"  ⚠️ No trading data for {date}")
                    if status != 'OK':
                        print(f"  API Status: {status}")
                        print(f"  Message: {data.get('message', 'No message')}")
            elif response.status_code == 403:
                print(f"  ❌ API Key authentication failed (403)")
                print(f"  Response: {response.text[:200]}")
            elif response.status_code == 404:
                print(f"  ⚠️ No data for date {date} (404 - might be weekend/holiday)")
            else:
                print(f"  ❌ API error: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"  ❌ Request timed out after 30 seconds")
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ Connection error: {e}")
        except Exception as e:
            print(f"  ❌ Error fetching snapshot: {e}")
        
        # Method 2: If snapshot fails, get current ticker list (less accurate but works)
        if not all_tickers:
            print("\n  Falling back to reference tickers endpoint...")
            try:
                url = f"{self.base_url}/v3/reference/tickers"
                
                params = {
                    'apiKey': self.polygon_api_key,
                    'market': 'stocks',
                    'active': 'true',
                    'limit': 1000,
                    'sort': 'ticker',
                    'order': 'asc'
                }
                
                print(f"  API URL: {url}")
                print(f"  Making request...")
                
                response = requests.get(url, params=params, timeout=30)
                print(f"  Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    status = data.get('status')
                    count = data.get('count', 0)
                    
                    print(f"  Response status: {status}")
                    print(f"  Count: {count}")
                    
                    if 'results' in data and data['results']:
                        for ticker_info in data['results']:
                            ticker = ticker_info.get('ticker')
                            if ticker and '.' not in ticker:  # Skip warrants and special securities
                                all_tickers.append(ticker)
                        
                        print(f"  ✅ Loaded {len(all_tickers)} tickers from reference endpoint")
                        
                        # Check if there are more pages but limit for testing
                        if data.get('next_url'):
                            print(f"  Note: More tickers available via pagination, using first {len(all_tickers)} for testing")
                    else:
                        print(f"  ⚠️ No tickers in response")
                else:
                    print(f"  ❌ API error: {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                print(f"  ❌ Request timed out after 30 seconds")
            except Exception as e:
                print(f"  ❌ Error fetching ticker list: {e}")
        
        # If still no tickers, use a small fallback list for testing
        if not all_tickers:
            print("\n  ⚠️ API calls failed, using minimal fallback list for testing...")
            all_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMD', 'META', 'AMZN', 'NFLX', 'ROKU']
            print(f"  Using {len(all_tickers)} fallback tickers")
        
        return all_tickers
    
    def get_stock_data(self, ticker: str, date: str) -> Dict:
        """
        Get price and volume data for a stock on a specific date
        """
        try:
            # Calculate date range (90 days before to get averages)
            end_date = datetime.fromisoformat(date)
            start_date = end_date - timedelta(days=90)
            
            # Get historical data from Polygon
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                'apiKey': self.polygon_api_key,
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 120
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    
                    if len(results) >= 20:  # Need at least 20 days of data
                        # Get most recent data
                        recent_bar = results[-1]
                        
                        # Calculate averages
                        volumes = [bar['v'] for bar in results]
                        prices = [bar['c'] for bar in results]
                        highs = [bar['h'] for bar in results]
                        lows = [bar['l'] for bar in results]
                        
                        # Calculate 20-day averages
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
            
            elif response.status_code == 429:
                # Rate limit - wait and return None
                time.sleep(15)
                
        except Exception as e:
            pass
        
        return None
    
    def score_stock(self, ticker: str, data: Dict, date: str) -> Tuple[float, Dict]:
        """
        Score a stock based on Phase 3 patterns
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
        
        # Volume scoring (most important pattern)
        if data['avg_volume_20d'] > 0:
            volume_ratio = data['volume'] / data['avg_volume_20d']
        else:
            volume_ratio = 0
        
        if volume_ratio >= 10:
            breakdown['volume_score'] = 50
        elif volume_ratio >= 5:
            breakdown['volume_score'] = 35
        elif volume_ratio >= 3:
            breakdown['volume_score'] = 25
        
        # RSI proxy (based on Phase 4 test showing overbought > oversold)
        if data['avg_price_20d'] > 0:
            price_ratio = data['price'] / data['avg_price_20d']
            
            if price_ratio > 1.15:  # Overbought is GOOD
                breakdown['rsi_score'] = 30
            elif price_ratio > 1.10:
                breakdown['rsi_score'] = 20
            elif price_ratio < 0.85:  # Oversold is BAD
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
        
        # Calculate total score
        score = sum(breakdown.values())
        
        return score, breakdown
    
    def screen_market(self, date: str) -> Dict:
        """
        Screen the ENTIRE market on a specific date
        """
        print(f"\n🔍 SCREENING ENTIRE MARKET: {date}")
        print("="*50)
        
        # Get ALL tickers
        all_tickers = self.get_all_tickers_for_date(date)
        
        if not all_tickers:
            print("  ❌ Failed to get market tickers")
            return {
                'screening_date': date,
                'market_stats': {
                    'total_stocks_scanned': 0,
                    'api_failures': 0,
                    'passed_filters': 0,
                    'top_30_selected': 0
                },
                'selected_stocks': [],
                'runners_up': []
            }
        
        # Filter and score stocks
        scored_stocks = []
        api_failures = 0
        stocks_analyzed = 0
        
        print(f"  Analyzing {len(all_tickers)} tickers...")
        print("  This will take several minutes...")
        
        for i, ticker in enumerate(all_tickers):
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"    Progress: {i + 1}/{len(all_tickers)} - Found {len(scored_stocks)} qualifying stocks so far")
            
            # Get stock data
            stock_data = self.get_stock_data(ticker, date)
            
            if stock_data:
                stocks_analyzed += 1
                
                # Apply filters
                if (stock_data['price'] >= 0.50 and 
                    stock_data['price'] <= 15.00 and
                    stock_data['avg_volume_20d'] >= 10000):
                    
                    # Calculate score
                    score, breakdown = self.score_stock(ticker, stock_data, date)
                    
                    if score >= 60:  # Minimum score threshold
                        scored_stocks.append({
                            'ticker': ticker,
                            'score': score,
                            'score_breakdown': breakdown,
                            'entry_price': stock_data['price'],
                            'entry_volume': stock_data['volume'],
                            'screening_date': date,
                            'rank': 0
                        })
            else:
                api_failures += 1
            
            # Rate limit protection
            if (i + 1) % 50 == 0:
                time.sleep(1)  # 1 second pause every 50 stocks
        
        # Sort by score and rank
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        for i, stock in enumerate(scored_stocks):
            stock['rank'] = i + 1
        
        # Select top 30
        top_30 = scored_stocks[:30]
        runners_up = scored_stocks[30:60] if len(scored_stocks) > 30 else []
        
        print(f"\n  ✅ Screening complete:")
        print(f"    Total tickers checked: {len(all_tickers)}")
        print(f"    Successfully analyzed: {stocks_analyzed}")
        print(f"    API failures: {api_failures}")
        print(f"    Passed all filters: {len(scored_stocks)}")
        print(f"    Top 30 selected: {len(top_30)}")
        
        if top_30:
            print(f"\n  🏆 Top 5 picks:")
            for stock in top_30[:5]:
                print(f"    {stock['rank']}. {stock['ticker']}: Score {stock['score']}")
        
        return {
            'screening_date': date,
            'market_stats': {
                'total_stocks_scanned': len(all_tickers),
                'stocks_analyzed': stocks_analyzed,
                'api_failures': api_failures,
                'passed_filters': len(scored_stocks),
                'top_30_selected': len(top_30)
            },
            'selected_stocks': top_30,
            'runners_up': runners_up
        }
    
    def check_false_miss(self, stock: Dict) -> Dict:
        """
        Check if stock would have been caught earlier
        """
        return {
            'is_false_miss': False,
            'status': 'NOT_CHECKED',
            'price_60d_ago': None
        }

def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 4 Market Screener')
    parser.add_argument('--mode', choices=['test', 'full'], default='test',
                       help='Test mode (3 dates) or full mode (15 dates)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("PHASE 4 INTEGRATED SCREENER")
    print(f"Mode: {args.mode}")
    print("="*60)
    
    # Initialize screener
    screener = Phase4MarketScreener()
    
    # Generate strategic dates
    test_dates = screener.generate_strategic_dates(args.mode)
    
    # Screen market on each date
    all_results = {
        'mode': args.mode,
        'test_dates': test_dates,
        'screening_results': [],
        'all_selected_stocks': [],
        'all_runners_up': []
    }
    
    for date_idx, date in enumerate(test_dates):
        print(f"\n[Date {date_idx + 1}/{len(test_dates)}]")
        result = screener.screen_market(date)
        all_results['screening_results'].append(result)
        
        # Add stocks to combined lists
        for stock in result['selected_stocks']:
            false_miss_check = screener.check_false_miss(stock)
            stock['false_miss_analysis'] = false_miss_check
            all_results['all_selected_stocks'].append(stock)
        
        for stock in result['runners_up']:
            all_results['all_runners_up'].append(stock)
    
    # Save results
    output_file = 'phase4_screening_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("SCREENING COMPLETE")
    print(f"{'='*60}")
    print(f"Total stocks selected: {len(all_results['all_selected_stocks'])}")
    print(f"Total runners-up: {len(all_results['all_runners_up'])}")
    print(f"Results saved to: {output_file}")
    
    # Display summary
    print(f"\n📊 Summary by Date:")
    for result in all_results['screening_results']:
        date = result['screening_date']
        stats = result['market_stats']
        selected = stats.get('top_30_selected', 0)
        total = stats.get('total_stocks_scanned', 0)
        print(f"  {date}: {selected} stocks selected from {total} scanned")

if __name__ == '__main__':
    main()
