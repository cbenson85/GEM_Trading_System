#!/usr/bin/env python3
"""
Phase 4 Integrated Screener - Generates strategic dates and screens entire market
Runs entirely on GitHub Actions
"""

import json
import os
import sys
import random
from datetime import datetime, timedelta
import requests
import yfinance as yf
from typing import List, Dict, Tuple

class Phase4MarketScreener:
    def __init__(self):
        self.polygon_api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
        
    def generate_strategic_dates(self, mode='test') -> List[str]:
        """
        Generate 15 random dates with 120+ day spacing
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
        
        # Sort dates chronologically
        selected_dates.sort()
        
        print(f"\n✅ Generated {len(selected_dates)} strategic dates")
        print(f"  Earliest: {selected_dates[0]}")
        print(f"  Latest: {selected_dates[-1]}")
        
        return selected_dates
    
    def get_market_stocks(self, date: str) -> List[Dict]:
        """
        Get all US stocks from the market on a specific date
        Uses Polygon API for comprehensive coverage
        """
        print(f"\n📊 Fetching market stocks for {date}...")
        
        all_stocks = []
        
        try:
            # Get all tickers from Polygon
            url = f"{self.base_url}/v3/reference/tickers"
            params = {
                'apiKey': self.polygon_api_key,
                'market': 'stocks',
                'exchange': 'XNYS,XNAS',  # NYSE and NASDAQ
                'active': 'true',
                'limit': 1000
            }
            
            next_url = url
            page_count = 0
            
            while next_url and page_count < 10:  # Limit pages for testing
                response = requests.get(next_url, params=params if page_count == 0 else {'apiKey': self.polygon_api_key})
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data:
                        for ticker_info in data['results']:
                            stock = {
                                'ticker': ticker_info.get('ticker'),
                                'name': ticker_info.get('name', ''),
                                'market_cap': ticker_info.get('market_cap', 0),
                                'exchange': ticker_info.get('primary_exchange', '')
                            }
                            all_stocks.append(stock)
                    
                    # Check for next page
                    next_url = data.get('next_url')
                    page_count += 1
                else:
                    print(f"  ⚠️ API error: {response.status_code}")
                    break
            
            print(f"  Found {len(all_stocks)} total stocks")
            
        except Exception as e:
            print(f"  ❌ Error fetching stocks: {e}")
            # Fallback: use a predefined list of common stocks for testing
            print("  Using fallback stock list...")
            all_stocks = self.get_fallback_stocks()
        
        return all_stocks
    
    def get_fallback_stocks(self) -> List[Dict]:
        """
        Fallback list of stocks if API fails
        """
        # Common small-cap stocks for testing
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
                   'NVDA', 'META', 'AMD', 'INTC', 'NFLX',
                   'ROKU', 'SNAP', 'PINS', 'HOOD', 'PLTR',
                   'SOFI', 'RIVN', 'LCID', 'NIO', 'XPEV']
        
        return [{'ticker': t, 'name': t, 'market_cap': 0, 'exchange': 'UNKNOWN'} for t in tickers]
    
    def get_stock_data(self, ticker: str, date: str) -> Dict:
        """
        Get price and volume data for a stock on a specific date
        """
        try:
            # Calculate date range (90 days before to get averages)
            end_date = datetime.fromisoformat(date)
            start_date = end_date - timedelta(days=90)
            
            # Get historical data
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {'apiKey': self.polygon_api_key, 'adjusted': 'true'}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    results = data['results']
                    
                    # Get most recent data
                    recent_bar = results[-1] if results else None
                    
                    if recent_bar:
                        # Calculate averages
                        volumes = [bar['v'] for bar in results]
                        prices = [bar['c'] for bar in results]
                        
                        avg_volume = sum(volumes) / len(volumes) if volumes else 0
                        avg_price = sum(prices) / len(prices) if prices else 0
                        
                        return {
                            'price': recent_bar['c'],
                            'volume': recent_bar['v'],
                            'avg_volume_20d': avg_volume,
                            'avg_price_20d': avg_price,
                            'high': recent_bar['h'],
                            'low': recent_bar['l'],
                            'open': recent_bar['o']
                        }
            
            return None
            
        except Exception as e:
            return None
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculate RSI
        """
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def score_stock(self, ticker: str, data: Dict, date: str) -> Tuple[float, Dict]:
        """
        Score a stock based on Phase 3 insights
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
        
        # Volume scoring (most important pattern from Phase 3)
        volume_ratio = data['volume'] / data['avg_volume_20d'] if data['avg_volume_20d'] > 0 else 0
        
        if volume_ratio >= 10:
            breakdown['volume_score'] = 50
        elif volume_ratio >= 5:
            breakdown['volume_score'] = 35
        elif volume_ratio >= 3:
            breakdown['volume_score'] = 25
        
        # RSI scoring (look for oversold bounce)
        # Note: Simplified RSI calculation for screening
        if data['price'] < data['avg_price_20d'] * 0.85:  # Proxy for oversold
            breakdown['rsi_score'] = 30
        elif data['price'] < data['avg_price_20d'] * 0.90:
            breakdown['rsi_score'] = 20
        
        # Breakout scoring
        if data['price'] > data['high'] * 0.95:  # Near high
            breakdown['breakout_score'] = 20
        
        # Accumulation (higher lows)
        if data['low'] > data['avg_price_20d'] * 0.95 and volume_ratio > 1.5:
            breakdown['accumulation_score'] = 30
        
        # Composite bonuses
        signals = sum([
            breakdown['volume_score'] > 0,
            breakdown['rsi_score'] > 0,
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
        Screen the entire market on a specific date
        """
        print(f"\n🔍 SCREENING MARKET: {date}")
        print("="*50)
        
        # Get all stocks
        all_stocks = self.get_market_stocks(date)
        
        # Filter and score stocks
        scored_stocks = []
        
        print(f"  Analyzing {len(all_stocks)} stocks...")
        
        for i, stock_info in enumerate(all_stocks):
            if i % 100 == 0:
                print(f"    Progress: {i}/{len(all_stocks)}")
            
            ticker = stock_info['ticker']
            
            # Get stock data
            stock_data = self.get_stock_data(ticker, date)
            
            if stock_data:
                # Apply basic filters
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
                            'rank': 0  # Will be set after sorting
                        })
        
        # Sort by score and select top 30
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign ranks
        for i, stock in enumerate(scored_stocks):
            stock['rank'] = i + 1
        
        # Select top 30
        top_30 = scored_stocks[:30]
        runners_up = scored_stocks[30:60] if len(scored_stocks) > 30 else []
        
        print(f"\n  ✅ Screening complete:")
        print(f"    Total stocks analyzed: {len(all_stocks)}")
        print(f"    Passed filters: {len(scored_stocks)}")
        print(f"    Top 30 selected: {len(top_30)}")
        
        if top_30:
            print(f"\n  Top 5 picks:")
            for stock in top_30[:5]:
                print(f"    {stock['rank']}. {stock['ticker']}: Score {stock['score']}")
        
        return {
            'screening_date': date,
            'market_stats': {
                'total_stocks_scanned': len(all_stocks),
                'passed_filters': len(scored_stocks),
                'top_30_selected': len(top_30)
            },
            'selected_stocks': top_30,
            'runners_up': runners_up
        }
    
    def check_false_miss(self, stock: Dict) -> Dict:
        """
        Check if stock would have been caught earlier (60 days lookback)
        """
        ticker = stock['ticker']
        screening_date = datetime.fromisoformat(stock['screening_date'])
        lookback_date = screening_date - timedelta(days=60)
        
        # Get historical data
        hist_data = self.get_stock_data(ticker, lookback_date.strftime('%Y-%m-%d'))
        
        if hist_data and hist_data['price'] < 0.50:
            # Stock was below threshold 60 days ago
            return {
                'is_false_miss': False,
                'status': 'GENUINE_PICK',
                'price_60d_ago': hist_data['price']
            }
        elif hist_data and hist_data['price'] >= 0.50:
            # Stock was already above threshold
            return {
                'is_false_miss': True,
                'status': 'FALSE_MISS',
                'price_60d_ago': hist_data['price']
            }
        else:
            return {
                'is_false_miss': False,
                'status': 'NO_DATA',
                'price_60d_ago': None
            }

def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 4 Integrated Screener')
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
    
    for date in test_dates:
        result = screener.screen_market(date)
        all_results['screening_results'].append(result)
        
        # Add false miss check for selected stocks
        for stock in result['selected_stocks']:
            false_miss_check = screener.check_false_miss(stock)
            stock['false_miss_analysis'] = false_miss_check
            all_results['all_selected_stocks'].append(stock)
        
        # Also track runners-up
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
        print(f"  {date}: {stats['top_30_selected']} stocks from {stats['total_stocks_scanned']} scanned")

if __name__ == '__main__':
    main()
