#!/usr/bin/env python3
"""
Phase 4 Integrated Screener - Troubleshooting version with debug output
"""

print("[DEBUG] Starting imports...", flush=True)
import json
print("[DEBUG] json imported", flush=True)
import os
print("[DEBUG] os imported", flush=True)
import sys
print("[DEBUG] sys imported", flush=True)
import random
print("[DEBUG] random imported", flush=True)
from datetime import datetime, timedelta
print("[DEBUG] datetime imported", flush=True)
import requests
print("[DEBUG] requests imported", flush=True)
from typing import List, Dict, Tuple
print("[DEBUG] typing imported", flush=True)
import time
print("[DEBUG] time imported", flush=True)
from concurrent.futures import ThreadPoolExecutor, as_completed
print("[DEBUG] concurrent.futures imported", flush=True)
import threading
print("[DEBUG] threading imported", flush=True)
print("[DEBUG] ALL IMPORTS COMPLETE", flush=True)

class Phase4MarketScreener:
    def __init__(self):
        print("[DEBUG] __init__ called", flush=True)
        self.polygon_api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
        print(f"  API Key configured: {'✅' if self.polygon_api_key else '❌'}")
        print("  Using Polygon DEVELOPER API - UNLIMITED calls, no rate limits!")
        
        # Thread-safe counters for progress tracking
        self.progress_lock = threading.Lock()
        self.stocks_processed = 0
        self.stocks_qualified = 0
        print("[DEBUG] __init__ complete", flush=True)
        
    def generate_strategic_dates(self, mode='test') -> List[str]:
        """
        Generate WEEKDAY dates with 120+ day spacing
        """
        print("[DEBUG] generate_strategic_dates called", flush=True)
        print("="*60)
        print("GENERATING STRATEGIC TEST DATES (WEEKDAYS ONLY)")
        print("="*60)
        
        if mode == 'test':
            # Fixed weekday dates for consistent testing
            selected_dates = [
                '2019-03-15',  # Friday
                '2022-06-20',  # Monday
                '2023-09-11'   # Monday
            ]
            print("  Using fixed weekday test dates:")
            for i, date in enumerate(selected_dates, 1):
                dt = datetime.fromisoformat(date)
                day_name = dt.strftime('%A')
                print(f"  Date {i}: {date} ({day_name})")
        else:
            # Generate 15 random weekday dates
            valid_ranges = [
                (datetime(2010, 1, 1), datetime(2019, 12, 31)),
                (datetime(2022, 1, 1), datetime(2024, 10, 31))
            ]
            
            selected_dates = []
            attempts = 0
            
            while len(selected_dates) < 15 and attempts < 1000:
                attempts += 1
                
                range_idx = random.randint(0, len(valid_ranges) - 1)
                start, end = valid_ranges[range_idx]
                
                days_between = (end - start).days
                random_days = random.randint(0, days_between)
                candidate_date = start + timedelta(days=random_days)
                
                # Ensure weekday
                while candidate_date.weekday() >= 5:
                    candidate_date = candidate_date + timedelta(days=1)
                
                # Check spacing
                valid = True
                for existing in selected_dates:
                    existing_dt = datetime.fromisoformat(existing)
                    days_apart = abs((candidate_date - existing_dt).days)
                    if days_apart < 120:
                        valid = False
                        break
                
                if valid:
                    date_str = candidate_date.strftime('%Y-%m-%d')
                    selected_dates.append(date_str)
                    day_name = candidate_date.strftime('%A')
                    print(f"  Date {len(selected_dates)}: {date_str} ({day_name})")
            
            selected_dates.sort()
        
        print(f"\n✅ Generated {len(selected_dates)} strategic weekday dates")
        print(f"  Earliest: {selected_dates[0]}")
        print(f"  Latest: {selected_dates[-1]}")
        print("[DEBUG] generate_strategic_dates complete", flush=True)
        
        return selected_dates
    
    def get_all_market_tickers(self, date: str) -> List[Dict]:
        """
        Get ALL tickers that traded on a specific date
        """
        print(f"[DEBUG] get_all_market_tickers called for {date}", flush=True)
        print(f"\n📊 Fetching ENTIRE MARKET for {date}...")
        
        all_tickers = []
        
        try:
            url = f"{self.base_url}/v2/aggs/grouped/locale/us/market/stocks/{date}"
            params = {
                'apiKey': self.polygon_api_key,
                'adjusted': 'true'
            }
            
            print(f"  Calling Polygon API...")
            print(f"[DEBUG] URL: {url}", flush=True)
            print(f"[DEBUG] Making request...", flush=True)
            response = requests.get(url, params=params, timeout=60)
            print(f"[DEBUG] Response received: {response.status_code}", flush=True)
            
            if response.status_code == 200:
                print(f"[DEBUG] Parsing JSON...", flush=True)
                data = response.json()
                print(f"[DEBUG] JSON parsed", flush=True)
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    print(f"  ✅ Found {len(results)} stocks that traded on {date}")
                    
                    # Get ALL tickers with basic filtering
                    for item in results:
                        ticker = item.get('T')
                        if ticker and '.' not in ticker and not ticker.endswith('W'):
                            close_price = item.get('c', 0)
                            volume = item.get('v', 0)
                            
                            # Pre-filter
                            if 0.10 <= close_price <= 50 and volume >= 5000:
                                all_tickers.append({
                                    'ticker': ticker,
                                    'close': close_price,
                                    'volume': volume
                                })
                    
                    print(f"  After basic filters: {len(all_tickers)} stocks")
                    print(f"[DEBUG] get_all_market_tickers returning {len(all_tickers)} tickers", flush=True)
                    return all_tickers
                    
                else:
                    print(f"  ❌ No trading data for {date}")
                    
            else:
                print(f"  ❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error fetching market data: {e}")
            print(f"[DEBUG] Exception details: {type(e).__name__}", flush=True)
        
        print(f"[DEBUG] get_all_market_tickers returning {len(all_tickers)} tickers", flush=True)
        return all_tickers
    
    def get_stock_data_batch(self, ticker: str, date: str) -> Tuple[str, Dict]:
        """
        Get stock data - designed for parallel execution
        Returns (ticker, data_dict) tuple
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
            
            # FAST timeout - we have unlimited calls, skip slow responses
            response = requests.get(url, params=params, timeout=1)
            
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
                        
                        return ticker, {
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
        
        return ticker, None
    
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
        
        # RSI proxy
        if data['avg_price_20d'] > 0:
            price_ratio = data['price'] / data['avg_price_20d']
            
            if price_ratio > 1.15:
                breakdown['rsi_score'] = 30
            elif price_ratio > 1.10:
                breakdown['rsi_score'] = 20
            elif price_ratio < 0.85:
                breakdown['rsi_score'] = -20
        
        # Breakout
        if data['high'] > 0 and data['price'] > data['high'] * 0.95:
            breakdown['breakout_score'] = 30
        
        # Accumulation
        if data['low'] > 0 and data['avg_price_20d'] > 0:
            if data['low'] > data['avg_price_20d'] * 0.95 and volume_ratio > 1.5:
                breakdown['accumulation_score'] = 30
        
        # Composite
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
        Screen market using PARALLEL PROCESSING - ULTRA FAST
        """
        print(f"[DEBUG] screen_market called for {date}", flush=True)
        print(f"\n🔍 SCREENING ENTIRE MARKET: {date}")
        print("="*50)
        
        # Get market tickers
        market_snapshot = self.get_all_market_tickers(date)
        
        if not market_snapshot:
            print("  ❌ No market data available")
            return {
                'screening_date': date,
                'market_stats': {
                    'total_stocks_scanned': 0,
                    'stocks_analyzed': 0,
                    'api_failures': 0,
                    'passed_filters': 0,
                    'top_30_selected': 0
                },
                'selected_stocks': [],
                'runners_up': []
            }
        
        # Reset counters
        self.stocks_processed = 0
        self.stocks_qualified = 0
        
        scored_stocks = []
        api_failures = 0
        stocks_analyzed = 0
        
        print(f"  🚀 PARALLEL PROCESSING {len(market_snapshot)} stocks...")
        print(f"  Using 100 concurrent threads (Developer API - no limits)")
        
        start_time = time.time()
        
        print(f"[DEBUG] Starting ThreadPoolExecutor", flush=True)
        
        # Process in parallel with 100 threads (unlimited API)
        with ThreadPoolExecutor(max_workers=100) as executor:
            # Submit all tasks
            print(f"[DEBUG] Submitting {len(market_snapshot)} tasks", flush=True)
            futures = {}
            for stock_info in market_snapshot:
                ticker = stock_info['ticker']
                future = executor.submit(self.get_stock_data_batch, ticker, date)
                futures[future] = ticker
            
            print(f"[DEBUG] All tasks submitted, waiting for completion", flush=True)
            
            # Process completed futures
            for future in as_completed(futures):
                ticker = futures[future]
                
                try:
                    ticker, stock_data = future.result()
                    
                    # Update progress
                    with self.progress_lock:
                        self.stocks_processed += 1
                        if self.stocks_processed % 100 == 0:
                            elapsed = time.time() - start_time
                            rate = self.stocks_processed / elapsed
                            eta = (len(market_snapshot) - self.stocks_processed) / rate
                            print(f"    Progress: {self.stocks_processed}/{len(market_snapshot)} "
                                  f"({self.stocks_processed/len(market_snapshot)*100:.1f}%) - "
                                  f"Rate: {rate:.0f} stocks/sec - ETA: {eta:.0f}s")
                    
                    if stock_data:
                        stocks_analyzed += 1
                        
                        # Apply filters
                        if (stock_data['price'] >= 0.50 and 
                            stock_data['price'] <= 15.00 and
                            stock_data['avg_volume_20d'] >= 10000):
                            
                            # Calculate score
                            score, breakdown = self.score_stock(ticker, stock_data, date)
                            
                            if score >= 60:
                                scored_stocks.append({
                                    'ticker': ticker,
                                    'score': score,
                                    'score_breakdown': breakdown,
                                    'entry_price': stock_data['price'],
                                    'entry_volume': stock_data['volume'],
                                    'screening_date': date,
                                    'rank': 0
                                })
                                
                                with self.progress_lock:
                                    self.stocks_qualified += 1
                    else:
                        api_failures += 1
                        
                except Exception as e:
                    api_failures += 1
        
        print(f"[DEBUG] ThreadPoolExecutor complete", flush=True)
        
        elapsed = time.time() - start_time
        print(f"  ⚡ Processed {len(market_snapshot)} stocks in {elapsed:.1f} seconds!")
        print(f"  Speed: {len(market_snapshot)/elapsed:.0f} stocks/second")
        
        # Sort and rank
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        for i, stock in enumerate(scored_stocks):
            stock['rank'] = i + 1
        
        # Select top 30
        top_30 = scored_stocks[:30]
        runners_up = scored_stocks[30:60] if len(scored_stocks) > 30 else []
        
        print(f"\n  ✅ Screening complete:")
        print(f"    Total market stocks: {len(market_snapshot)}")
        print(f"    Successfully analyzed: {stocks_analyzed}")
        print(f"    Met minimum score: {len(scored_stocks)}")
        print(f"    TOP 30 SELECTED: {len(top_30)}")
        print(f"    Runners-up (31-60): {len(runners_up)}")
        
        if top_30:
            print(f"\n  🏆 Top 5 picks:")
            for stock in top_30[:5]:
                print(f"    {stock['rank']}. {stock['ticker']}: Score {stock['score']} @ ${stock['entry_price']:.2f}")
        
        print(f"[DEBUG] screen_market complete for {date}", flush=True)
        
        return {
            'screening_date': date,
            'market_stats': {
                'total_stocks_scanned': len(market_snapshot),
                'stocks_analyzed': stocks_analyzed,
                'api_failures': api_failures,
                'passed_filters': len(scored_stocks),
                'top_30_selected': len(top_30)
            },
            'selected_stocks': top_30,
            'runners_up': runners_up
        }

def main():
    print("[DEBUG] main() called", flush=True)
    import argparse
    print("[DEBUG] argparse imported", flush=True)
    
    parser = argparse.ArgumentParser(description='Phase 4 Ultra-Fast Screener')
    parser.add_argument('--mode', choices=['test', 'full'], default='test')
    
    print("[DEBUG] Parsing arguments", flush=True)
    args = parser.parse_args()
    print(f"[DEBUG] Arguments parsed: mode={args.mode}", flush=True)
    
    print("="*60)
    print("PHASE 4 INTEGRATED SCREENER - ULTRA FAST")
    print(f"Mode: {args.mode}")
    print("Using Polygon Developer API - UNLIMITED calls")
    print("="*60)
    
    print("[DEBUG] About to create screener instance", flush=True)
    
    try:
        # Initialize
        screener = Phase4MarketScreener()
        print("[DEBUG] Screener instance created", flush=True)
        
        # Generate dates
        print("[DEBUG] About to generate dates", flush=True)
        test_dates = screener.generate_strategic_dates(args.mode)
        print(f"[DEBUG] Dates generated: {test_dates}", flush=True)
        
        # Screen each date
        all_results = {
            'mode': args.mode,
            'test_dates': test_dates,
            'screening_results': [],
            'all_selected_stocks': [],
            'all_runners_up': []
        }
        
        expected_stocks = len(test_dates) * 30
        
        for date_idx, date in enumerate(test_dates):
            print(f"\n[Date {date_idx + 1}/{len(test_dates)}]")
            print(f"[DEBUG] Screening date {date}", flush=True)
            result = screener.screen_market(date)
            print(f"[DEBUG] Screening complete for {date}", flush=True)
            all_results['screening_results'].append(result)
            
            for stock in result['selected_stocks']:
                stock['false_miss_analysis'] = {
                    'is_false_miss': False,
                    'status': 'NOT_CHECKED',
                    'price_60d_ago': None
                }
                all_results['all_selected_stocks'].append(stock)
            
            for stock in result['runners_up']:
                all_results['all_runners_up'].append(stock)
            
            print(f"  Cumulative: {len(all_results['all_selected_stocks'])}/{expected_stocks} stocks")
        
        # Save results
        print("[DEBUG] Saving results", flush=True)
        output_file = 'phase4_screening_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print("[DEBUG] Results saved", flush=True)
        
        print(f"\n{'='*60}")
        print("COMPLETE")
        print(f"Total selected: {len(all_results['all_selected_stocks'])}/{expected_stocks} expected")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"[DEBUG] EXCEPTION IN MAIN: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        # Create minimal file so workflow continues
        with open('phase4_screening_results.json', 'w') as f:
            json.dump({'error': str(e), 'all_selected_stocks': []}, f)

    print("[DEBUG] main() complete", flush=True)

if __name__ == '__main__':
    print("[DEBUG] Script started - __main__ block", flush=True)
    try:
        main()
    except Exception as e:
        print(f"[DEBUG] EXCEPTION IN __MAIN__: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
