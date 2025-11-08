#!/usr/bin/env python3
"""
Phase 4 Integrated Screener - Troubleshooting version with debug prints
"""

import json
import os
import sys
import random
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Tuple
import time

print("[DEBUG] Script started, imports complete", flush=True)

class Phase4MarketScreener:
    def __init__(self):
        print("[DEBUG] Initializing screener...", flush=True)
        self.polygon_api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
        print(f"[DEBUG] API Key length: {len(self.polygon_api_key) if self.polygon_api_key else 0}", flush=True)
        print(f"  API Key configured: {'✅' if self.polygon_api_key else '❌'}", flush=True)
        
    def generate_strategic_dates(self, mode='test') -> List[str]:
        """
        Generate WEEKDAY dates with 120+ day spacing
        """
        print("[DEBUG] Starting date generation...", flush=True)
        print("="*60)
        print("GENERATING STRATEGIC TEST DATES (WEEKDAYS ONLY)")
        print("="*60)
        
        if mode == 'test':
            print("[DEBUG] Using test mode fixed dates", flush=True)
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
            print("[DEBUG] Generating random dates for full mode", flush=True)
            # Generate 15 random weekday dates
            valid_ranges = [
                (datetime(2010, 1, 1), datetime(2019, 12, 31)),
                (datetime(2022, 1, 1), datetime(2024, 10, 31))
            ]
            
            selected_dates = []
            attempts = 0
            
            while len(selected_dates) < 15 and attempts < 1000:
                attempts += 1
                
                # Pick random range
                range_idx = random.randint(0, len(valid_ranges) - 1)
                start, end = valid_ranges[range_idx]
                
                # Generate random date
                days_between = (end - start).days
                random_days = random.randint(0, days_between)
                candidate_date = start + timedelta(days=random_days)
                
                # ENSURE IT'S A WEEKDAY
                while candidate_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    candidate_date = candidate_date + timedelta(days=1)
                
                # Check spacing from existing dates (120+ days)
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
        print("[DEBUG] Date generation complete", flush=True)
        
        return selected_dates
    
    def get_all_market_tickers(self, date: str) -> List[str]:
        """
        Get ALL tickers that traded on a specific date - NO FALLBACK
        """
        print(f"\n📊 Fetching ENTIRE MARKET for {date}...")
        print(f"[DEBUG] Starting API call for date {date}", flush=True)
        
        all_tickers = []
        
        # Use Polygon grouped daily endpoint to get ALL stocks that traded
        try:
            url = f"{self.base_url}/v2/aggs/grouped/locale/us/market/stocks/{date}"
            params = {
                'apiKey': self.polygon_api_key,
                'adjusted': 'true'
            }
            
            print(f"[DEBUG] URL: {url}", flush=True)
            print(f"[DEBUG] Making request with 30 second timeout...", flush=True)
            
            response = requests.get(url, params=params, timeout=30)  # EXPLICIT TIMEOUT
            
            print(f"[DEBUG] Response received, status: {response.status_code}", flush=True)
            
            if response.status_code == 200:
                print("[DEBUG] Parsing JSON response...", flush=True)
                data = response.json()
                
                print(f"[DEBUG] JSON parsed, status: {data.get('status')}", flush=True)
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    print(f"  ✅ Found {len(results)} stocks that traded on {date}")
                    
                    # Get ALL tickers, no limits
                    for item in results:
                        ticker = item.get('T')  # T is the ticker symbol
                        # Basic filters - skip warrants and special securities
                        if ticker and '.' not in ticker and not ticker.endswith('W'):
                            # Also get basic data for initial filtering
                            close_price = item.get('c', 0)
                            volume = item.get('v', 0)
                            
                            # Pre-filter for efficiency (price range and minimum volume)
                            if 0.10 <= close_price <= 50 and volume >= 5000:
                                all_tickers.append({
                                    'ticker': ticker,
                                    'close': close_price,
                                    'volume': volume
                                })
                    
                    print(f"  After basic filters: {len(all_tickers)} stocks")
                    return all_tickers
                    
                else:
                    print(f"  ❌ No trading data for {date} - might be weekend/holiday")
                    print(f"  Status: {data.get('status')}")
                    print(f"  Message: {data.get('message', 'No message')}")
                    
            elif response.status_code == 404:
                print(f"  ❌ No data for {date} - likely weekend/holiday")
            else:
                print(f"  ❌ API error: {response.status_code}")
                print(f"  Response: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            print(f"[DEBUG] ❌ REQUEST TIMED OUT AFTER 30 SECONDS", flush=True)
        except Exception as e:
            print(f"[DEBUG] ❌ Error: {type(e).__name__}: {e}", flush=True)
        
        # NO FALLBACK - if we can't get market data, the test fails
        if not all_tickers:
            print("  ❌ CRITICAL: Could not get market data. Test cannot continue.")
        
        print(f"[DEBUG] Market ticker fetch complete, got {len(all_tickers)} tickers", flush=True)
        return all_tickers
    
    def get_stock_data(self, ticker: str, date: str) -> Dict:
        """
        Get detailed price and volume data for scoring
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
            
            response = requests.get(url, params=params, timeout=5)  # SHORT TIMEOUT
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    
                    if len(results) >= 20:  # Need at least 20 days for averages
                        recent_bar = results[-1]
                        
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
            
        except requests.exceptions.Timeout:
            pass  # Timeout is expected sometimes
        except:
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
        
        # Volume scoring (most important)
        if data['avg_volume_20d'] > 0:
            volume_ratio = data['volume'] / data['avg_volume_20d']
            
            if volume_ratio >= 10:
                breakdown['volume_score'] = 50
            elif volume_ratio >= 5:
                breakdown['volume_score'] = 35
            elif volume_ratio >= 3:
                breakdown['volume_score'] = 25
        
        # RSI proxy (overbought is better based on results)
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
        Screen the ENTIRE market and select top 30 stocks
        """
        print(f"\n🔍 SCREENING ENTIRE MARKET: {date}")
        print("="*50)
        print(f"[DEBUG] Starting market screen for {date}", flush=True)
        
        # Get ALL market tickers
        market_snapshot = self.get_all_market_tickers(date)
        
        if not market_snapshot:
            print("  ❌ No market data available - cannot screen")
            return {
                'screening_date': date,
                'market_stats': {
                    'total_stocks_scanned': 0,
                    'stocks_analyzed': 0,
                    'api_failures': 0,
                    'passed_filters': 0,
                    'top_30_selected': 0,
                    'error': 'No market data available'
                },
                'selected_stocks': [],
                'runners_up': []
            }
        
        # Process and score ALL stocks
        scored_stocks = []
        api_failures = 0
        stocks_analyzed = 0
        
        print(f"  Analyzing {len(market_snapshot)} stocks from market...")
        print("[DEBUG] Starting stock analysis loop", flush=True)
        
        for i, stock_info in enumerate(market_snapshot):
            ticker = stock_info['ticker']
            
            # Progress update
            if (i + 1) % 100 == 0:
                print(f"    Progress: {i + 1}/{len(market_snapshot)} analyzed, {len(scored_stocks)} qualified so far")
            
            # Get detailed data for scoring
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
            
            # Rate limiting - be nice to the API
            if (i + 1) % 50 == 0:
                time.sleep(1)
        
        print("[DEBUG] Stock analysis complete, sorting results", flush=True)
        
        # Sort ALL qualified stocks by score
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign ranks
        for i, stock in enumerate(scored_stocks):
            stock['rank'] = i + 1
        
        # Select EXACTLY top 30 (or all if less than 30)
        top_30 = scored_stocks[:30]
        runners_up = scored_stocks[30:60] if len(scored_stocks) > 30 else []
        
        print(f"\n  ✅ Screening complete:")
        print(f"    Total market stocks: {len(market_snapshot)}")
        print(f"    Successfully analyzed: {stocks_analyzed}")
        print(f"    Met minimum score: {len(scored_stocks)}")
        print(f"    TOP 30 SELECTED: {len(top_30)}")
        print(f"    Runners-up (31-60): {len(runners_up)}")
        
        if top_30:
            print(f"\n  🏆 Top 5 picks from ENTIRE MARKET:")
            for stock in top_30[:5]:
                print(f"    {stock['rank']}. {stock['ticker']}: Score {stock['score']} @ ${stock['entry_price']:.2f}")
        
        print(f"[DEBUG] Market screen complete for {date}", flush=True)
        
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
    """
    Main entry point
    """
    print("[DEBUG] main() function started", flush=True)
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 4 Market Screener')
    parser.add_argument('--mode', choices=['test', 'full'], default='test',
                       help='Test mode (3 dates) or full mode (15 dates)')
    
    args = parser.parse_args()
    print(f"[DEBUG] Arguments parsed: mode={args.mode}", flush=True)
    
    print("="*60)
    print("PHASE 4 INTEGRATED SCREENER")
    print(f"Mode: {args.mode}")
    print("NO FALLBACK LISTS - SCREENING ENTIRE MARKET")
    print("="*60)
    
    try:
        # Initialize screener
        print("[DEBUG] Creating screener instance...", flush=True)
        screener = Phase4MarketScreener()
        
        # Generate strategic dates (weekdays only)
        print("[DEBUG] Generating dates...", flush=True)
        test_dates = screener.generate_strategic_dates(args.mode)
        
        # Screen market on each date
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
            result = screener.screen_market(date)
            all_results['screening_results'].append(result)
            
            # Add ALL selected stocks (should be 30 per date)
            for stock in result['selected_stocks']:
                stock['false_miss_analysis'] = {
                    'is_false_miss': False,
                    'status': 'NOT_CHECKED',
                    'price_60d_ago': None
                }
                all_results['all_selected_stocks'].append(stock)
            
            # Add runners-up
            for stock in result['runners_up']:
                all_results['all_runners_up'].append(stock)
            
            print(f"  Cumulative stocks selected: {len(all_results['all_selected_stocks'])}/{expected_stocks} expected")
        
        # Save results
        print("[DEBUG] Saving results to JSON...", flush=True)
        output_file = 'phase4_screening_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n{'='*60}")
        print("SCREENING COMPLETE")
        print(f"{'='*60}")
        print(f"Expected stocks (30 × {len(test_dates)} dates): {expected_stocks}")
        print(f"Actually selected: {len(all_results['all_selected_stocks'])}")
        
        if len(all_results['all_selected_stocks']) < expected_stocks:
            print(f"⚠️ WARNING: Selected fewer stocks than expected!")
            print(f"   This could mean some dates had fewer than 30 qualifying stocks")
        
        print(f"Total runners-up: {len(all_results['all_runners_up'])}")
        print(f"Results saved to: {output_file}")
        
        # Summary by date
        print(f"\n📊 Summary by Date:")
        for result in all_results['screening_results']:
            date = result['screening_date']
            stats = result['market_stats']
            selected = stats.get('top_30_selected', 0)
            total = stats.get('total_stocks_scanned', 0)
            print(f"  {date}: {selected} stocks selected from {total} market stocks")
            
    except Exception as e:
        print(f"[DEBUG] ❌ EXCEPTION: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        # Create minimal output file so workflow continues
        with open('phase4_screening_results.json', 'w') as f:
            json.dump({'error': str(e), 'all_selected_stocks': []}, f)

    print("[DEBUG] Script complete", flush=True)

if __name__ == '__main__':
    print("[DEBUG] Script entry point reached", flush=True)
    main()
