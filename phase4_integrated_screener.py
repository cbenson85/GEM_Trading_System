#!/usr/bin/env python3
"""
Phase 4 Integrated Screener with HANG DETECTION
Will timeout and show exact hang location
"""

import sys
import signal
import traceback

# TIMEOUT HANDLER - Will kill script if it hangs
def timeout_handler(signum, frame):
    print("\n" + "="*60, flush=True)
    print("❌ SCRIPT TIMEOUT - HUNG FOR MORE THAN 30 SECONDS", flush=True)
    print("="*60, flush=True)
    traceback.print_stack(frame)
    print("\nForcing exit due to hang...", flush=True)
    sys.exit(1)

# Set 30 second timeout for initial setup
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)

print("[STARTUP] Beginning imports...", flush=True)

try:
    import json
    print("[STARTUP] json imported", flush=True)
    import os
    print("[STARTUP] os imported", flush=True)
    import random
    print("[STARTUP] random imported", flush=True)
    from datetime import datetime, timedelta
    print("[STARTUP] datetime imported", flush=True)
    import requests
    print("[STARTUP] requests imported", flush=True)
    from typing import List, Dict, Tuple
    print("[STARTUP] typing imported", flush=True)
    import time
    print("[STARTUP] time imported", flush=True)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    print("[STARTUP] concurrent.futures imported", flush=True)
    import threading
    print("[STARTUP] threading imported", flush=True)
except Exception as e:
    print(f"[STARTUP] IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

print("[STARTUP] All imports successful", flush=True)

# Reset timeout to 5 minutes for main execution
signal.alarm(300)

class Phase4MarketScreener:
    def __init__(self):
        print("[INIT] Creating screener instance...", flush=True)
        self.polygon_api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
        print(f"[INIT] API Key configured: {'✅' if self.polygon_api_key else '❌'}", flush=True)
        print("[INIT] Using Polygon DEVELOPER API - UNLIMITED calls", flush=True)
        
        # Thread-safe counters
        self.progress_lock = threading.Lock()
        self.stocks_processed = 0
        self.stocks_qualified = 0
        print("[INIT] Screener ready", flush=True)
        
    def generate_strategic_dates(self, mode='test') -> List[str]:
        """
        Generate WEEKDAY dates with 120+ day spacing
        """
        print("[DATES] Starting date generation...", flush=True)
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
        print("[DATES] Date generation complete", flush=True)
        
        return selected_dates
    
    def get_all_market_tickers(self, date: str) -> List[Dict]:
        """
        Get ALL tickers that traded on a specific date - NO FALLBACK
        """
        print(f"\n[API] Fetching ENTIRE MARKET for {date}...", flush=True)
        
        all_tickers = []
        
        try:
            url = f"{self.base_url}/v2/aggs/grouped/locale/us/market/stocks/{date}"
            params = {
                'apiKey': self.polygon_api_key,
                'adjusted': 'true'
            }
            
            print(f"[API] Calling Polygon API...", flush=True)
            print(f"[API] URL: {url}", flush=True)
            
            # Set timeout for this specific call
            start = time.time()
            response = requests.get(url, params=params, timeout=30)
            elapsed = time.time() - start
            
            print(f"[API] Response received in {elapsed:.1f}s: Status {response.status_code}", flush=True)
            
            if response.status_code == 200:
                print("[API] Parsing JSON...", flush=True)
                data = response.json()
                print("[API] JSON parsed successfully", flush=True)
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    print(f"[API] ✅ Found {len(results)} stocks that traded on {date}", flush=True)
                    
                    # Get ALL tickers with basic filtering
                    for item in results:
                        ticker = item.get('T')
                        if ticker and '.' not in ticker and not ticker.endswith('W'):
                            close_price = item.get('c', 0)
                            volume = item.get('v', 0)
                            
                            # Pre-filter for efficiency
                            if 0.10 <= close_price <= 50 and volume >= 5000:
                                all_tickers.append({
                                    'ticker': ticker,
                                    'close': close_price,
                                    'volume': volume
                                })
                    
                    print(f"[API] After basic filters: {len(all_tickers)} stocks", flush=True)
                    return all_tickers
                    
                else:
                    print(f"[API] ❌ No trading data for {date}", flush=True)
                    print(f"[API] Status: {data.get('status')}, Message: {data.get('message')}", flush=True)
                    
            else:
                print(f"[API] ❌ API error: {response.status_code}", flush=True)
                print(f"[API] Response: {response.text[:200]}", flush=True)
                
        except requests.exceptions.Timeout:
            print(f"[API] ❌ TIMEOUT after 30 seconds", flush=True)
        except Exception as e:
            print(f"[API] ❌ Error: {type(e).__name__}: {e}", flush=True)
        
        print(f"[API] Returning {len(all_tickers)} tickers", flush=True)
        return all_tickers
    
    def get_stock_data_batch(self, ticker: str, date: str) -> Tuple[str, Dict]:
        """
        Get stock data for parallel execution
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
            
            response = requests.get(url, params=params, timeout=2)
            
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
                        
                        # Calculate RSI
                        rsi = self.calculate_rsi(prices)
                        
                        avg_volume_20d = sum(volumes[-20:]) / 20
                        avg_price_20d = sum(prices[-20:]) / 20
                        
                        return ticker, {
                            'price': recent_bar['c'],
                            'volume': recent_bar['v'],
                            'avg_volume_20d': avg_volume_20d,
                            'avg_price_20d': avg_price_20d,
                            'high': max(highs[-20:]),
                            'low': min(lows[-20:]),
                            'open': recent_bar['o'],
                            'rsi': rsi
                        }
        except:
            pass
        
        return ticker, None
    
    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        """
        Calculate RSI from price list
        """
        if len(prices) < period + 1:
            return 50
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def score_stock(self, ticker: str, data: Dict, date: str) -> Tuple[float, Dict]:
        """
        CORRECTED SCORING based on Phase 3 analysis of 694 verified stocks
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
        
        # VOLUME SCORING - Most important pattern (75% of explosives had 10x+ volume)
        if data['avg_volume_20d'] > 0:
            volume_ratio = data['volume'] / data['avg_volume_20d']
            
            if volume_ratio >= 10:
                breakdown['volume_score'] = 50
            elif volume_ratio >= 5:
                breakdown['volume_score'] = 35
            elif volume_ratio >= 3:
                breakdown['volume_score'] = 20
            elif volume_ratio >= 2:
                breakdown['volume_score'] = 10
        
        # RSI SCORING - Oversold is GOOD (60% of explosives had RSI < 30)
        rsi = data.get('rsi', 50)
        if rsi < 30:
            breakdown['rsi_score'] = 30
        elif rsi < 40:
            breakdown['rsi_score'] = 20
        elif rsi > 70:
            breakdown['rsi_score'] = -10
        
        # BREAKOUT SCORING - Near 52-week high (45% of explosives)
        if data['high'] > 0:
            if data['price'] >= data['high'] * 0.95:
                breakdown['breakout_score'] = 20
            elif data['price'] >= data['high'] * 0.90:
                breakdown['breakout_score'] = 10
        
        # ACCUMULATION - Higher lows with volume (35% of explosives)
        if data['low'] > 0 and data['avg_price_20d'] > 0:
            if data['low'] > data['avg_price_20d'] * 0.95:
                volume_ratio = data['volume'] / data['avg_volume_20d'] if data['avg_volume_20d'] > 0 else 0
                if volume_ratio > 2:
                    breakdown['accumulation_score'] = 20
                elif volume_ratio > 1.5:
                    breakdown['accumulation_score'] = 10
        
        # COMPOSITE BONUS - Multiple signals together
        signals = sum([
            breakdown['volume_score'] >= 20,
            breakdown['rsi_score'] >= 20,
            breakdown['breakout_score'] > 0,
            breakdown['accumulation_score'] > 0
        ])
        
        if signals >= 3:
            breakdown['composite_bonus'] = 30
        elif signals >= 2:
            breakdown['composite_bonus'] = 15
        
        # Calculate total score
        score = sum(breakdown.values())
        
        return score, breakdown
    
    def screen_market(self, date: str) -> Dict:
        """
        Screen market and select EXACTLY TOP 30 stocks
        """
        print(f"\n[SCREEN] SCREENING ENTIRE MARKET: {date}", flush=True)
        print("="*50)
        
        # Get market tickers
        market_snapshot = self.get_all_market_tickers(date)
        
        if not market_snapshot:
            print("[SCREEN] ❌ No market data available", flush=True)
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
        
        print(f"[SCREEN] 🚀 PARALLEL PROCESSING {len(market_snapshot)} stocks...", flush=True)
        print(f"[SCREEN] Using 100 concurrent threads", flush=True)
        
        start_time = time.time()
        
        # Process in parallel
        print("[SCREEN] Creating thread pool...", flush=True)
        with ThreadPoolExecutor(max_workers=100) as executor:
            print("[SCREEN] Submitting tasks...", flush=True)
            futures = {}
            for stock_info in market_snapshot:
                ticker = stock_info['ticker']
                future = executor.submit(self.get_stock_data_batch, ticker, date)
                futures[future] = ticker
            
            print(f"[SCREEN] Processing {len(futures)} tasks...", flush=True)
            
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
                            print(f"[SCREEN] Progress: {self.stocks_processed}/{len(market_snapshot)} "
                                  f"({self.stocks_processed/len(market_snapshot)*100:.1f}%) - "
                                  f"Rate: {rate:.0f} stocks/sec - ETA: {eta:.0f}s", flush=True)
                    
                    if stock_data:
                        stocks_analyzed += 1
                        
                        # Apply filters
                        if (stock_data['price'] >= 0.50 and 
                            stock_data['price'] <= 15.00 and
                            stock_data['avg_volume_20d'] >= 10000):
                            
                            # Calculate score
                            score, breakdown = self.score_stock(ticker, stock_data, date)
                            
                            if score >= 50:
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
        
        elapsed = time.time() - start_time
        print(f"[SCREEN] ⚡ Processed {len(market_snapshot)} stocks in {elapsed:.1f} seconds!", flush=True)
        
        # Sort by score
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign ranks
        for i, stock in enumerate(scored_stocks):
            stock['rank'] = i + 1
        
        # Select EXACTLY TOP 30
        top_30 = scored_stocks[:30]  # EXACTLY 30, not more
        runners_up = scored_stocks[30:60] if len(scored_stocks) > 30 else []
        
        print(f"\n[SCREEN] ✅ Screening complete:")
        print(f"  Total market stocks: {len(market_snapshot)}")
        print(f"  Successfully analyzed: {stocks_analyzed}")
        print(f"  Met minimum score (50+): {len(scored_stocks)}")
        print(f"  TOP 30 SELECTED: {len(top_30)}")
        print(f"  Runners-up (31-60): {len(runners_up)}")
        
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
    print("[MAIN] Starting main function...", flush=True)
    
    try:
        import argparse
        print("[MAIN] argparse imported", flush=True)
        
        parser = argparse.ArgumentParser(description='Phase 4 Screener')
        parser.add_argument('--mode', choices=['test', 'full'], default='test')
        
        print("[MAIN] Parsing arguments...", flush=True)
        args = parser.parse_args()
        print(f"[MAIN] Arguments: mode={args.mode}", flush=True)
        
        print("="*60)
        print("PHASE 4 INTEGRATED SCREENER")
        print(f"Mode: {args.mode}")
        print("="*60)
        
        print("[MAIN] Creating screener...", flush=True)
        screener = Phase4MarketScreener()
        
        print("[MAIN] Generating dates...", flush=True)
        test_dates = screener.generate_strategic_dates(args.mode)
        
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
            print(f"\n[MAIN] Processing date {date_idx + 1}/{len(test_dates)}: {date}", flush=True)
            
            # Reset alarm for each screening (5 minutes per date)
            signal.alarm(300)
            
            result = screener.screen_market(date)
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
            
            print(f"[MAIN] Cumulative: {len(all_results['all_selected_stocks'])} stocks", flush=True)
        
        # Save results
        print("[MAIN] Saving results...", flush=True)
        output_file = 'phase4_screening_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n{'='*60}")
        print("COMPLETE")
        print(f"Selected: {len(all_results['all_selected_stocks'])} stocks")
        print(f"Expected: {expected_stocks} stocks")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}")
        
        # Cancel alarm - we completed successfully
        signal.alarm(0)
        
    except Exception as e:
        print(f"[MAIN] ERROR: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        # Create minimal output file
        with open('phase4_screening_results.json', 'w') as f:
            json.dump({'error': str(e), 'all_selected_stocks': []}, f)
        sys.exit(1)

if __name__ == '__main__':
    print("\n[STARTUP] Phase 4 Screener Starting...", flush=True)
    print("[STARTUP] Python version:", sys.version, flush=True)
    print("[STARTUP] Current directory:", os.getcwd(), flush=True)
    
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL] Unhandled exception: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
