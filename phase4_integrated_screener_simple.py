#!/usr/bin/env python3
"""
Phase 4 Integrated Screener - SIMPLIFIED VERSION
Uses minimal API calls and includes test data for debugging
"""

import json
import os
import sys
import random
from datetime import datetime, timedelta

class Phase4MarketScreenerSimple:
    def __init__(self):
        self.polygon_api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        
    def generate_strategic_dates(self, mode='test'):
        """Generate test dates with 120+ day spacing"""
        print("="*60)
        print("GENERATING STRATEGIC TEST DATES")
        print("="*60)
        
        if mode == 'test':
            # Use fixed dates for testing
            dates = [
                '2019-03-15',
                '2022-06-20',
                '2023-09-10'
            ]
        else:
            # Generate 15 random dates
            dates = []
            current = datetime(2010, 3, 1)
            
            for i in range(15):
                # Add 120-200 random days
                days_to_add = random.randint(120, 200)
                current = current + timedelta(days=days_to_add)
                
                # Skip 2020-2021
                if 2020 <= current.year <= 2021:
                    current = datetime(2022, 1, 15)
                
                if current.year <= 2024:
                    dates.append(current.strftime('%Y-%m-%d'))
        
        print(f"Generated {len(dates)} dates:")
        for date in dates:
            print(f"  - {date}")
        
        return dates
    
    def get_test_stocks(self):
        """Return a fixed list of stocks for testing"""
        # Mix of stock types for testing
        return [
            # Tech stocks
            {'ticker': 'AAPL', 'name': 'Apple Inc', 'exchange': 'NASDAQ'},
            {'ticker': 'MSFT', 'name': 'Microsoft', 'exchange': 'NASDAQ'},
            {'ticker': 'GOOGL', 'name': 'Alphabet', 'exchange': 'NASDAQ'},
            {'ticker': 'NVDA', 'name': 'NVIDIA', 'exchange': 'NASDAQ'},
            {'ticker': 'AMD', 'name': 'AMD', 'exchange': 'NASDAQ'},
            
            # Small caps (more likely to explode)
            {'ticker': 'PINS', 'name': 'Pinterest', 'exchange': 'NYSE'},
            {'ticker': 'SNAP', 'name': 'Snapchat', 'exchange': 'NYSE'},
            {'ticker': 'ROKU', 'name': 'Roku', 'exchange': 'NASDAQ'},
            {'ticker': 'SQ', 'name': 'Square', 'exchange': 'NYSE'},
            {'ticker': 'PLTR', 'name': 'Palantir', 'exchange': 'NYSE'},
            
            # Penny stocks (for testing filters)
            {'ticker': 'SNDL', 'name': 'Sundial', 'exchange': 'NASDAQ'},
            {'ticker': 'TLRY', 'name': 'Tilray', 'exchange': 'NASDAQ'},
            {'ticker': 'ACB', 'name': 'Aurora Cannabis', 'exchange': 'NYSE'},
            {'ticker': 'HEXO', 'name': 'Hexo Corp', 'exchange': 'NYSE'},
            {'ticker': 'OGI', 'name': 'OrganiGram', 'exchange': 'NASDAQ'},
            
            # More test stocks
            {'ticker': 'BBBY', 'name': 'Bed Bath Beyond', 'exchange': 'NASDAQ'},
            {'ticker': 'GME', 'name': 'GameStop', 'exchange': 'NYSE'},
            {'ticker': 'AMC', 'name': 'AMC Entertainment', 'exchange': 'NYSE'},
            {'ticker': 'BB', 'name': 'BlackBerry', 'exchange': 'NYSE'},
            {'ticker': 'NOK', 'name': 'Nokia', 'exchange': 'NYSE'},
        ]
    
    def generate_mock_data(self, ticker, date):
        """Generate realistic mock data for testing"""
        random.seed(hash(ticker + date))  # Consistent random data
        
        base_price = random.uniform(0.5, 50.0)
        base_volume = random.randint(50000, 5000000)
        
        # Random multipliers for patterns
        volume_spike = random.choice([1.0, 1.5, 3.0, 5.0, 10.0])
        
        return {
            'price': base_price,
            'volume': base_volume * volume_spike,
            'avg_volume_20d': base_volume,
            'avg_price_20d': base_price * random.uniform(0.9, 1.1),
            'high': base_price * 1.05,
            'low': base_price * 0.95,
            'open': base_price * random.uniform(0.98, 1.02)
        }
    
    def score_stock(self, ticker, data):
        """Score based on Phase 3 patterns"""
        score = 0
        breakdown = {
            'volume_score': 0,
            'rsi_score': 0,
            'breakout_score': 0,
            'accumulation_score': 0,
            'composite_bonus': 0
        }
        
        # Volume scoring
        volume_ratio = data['volume'] / data['avg_volume_20d'] if data['avg_volume_20d'] > 0 else 0
        
        if volume_ratio >= 10:
            breakdown['volume_score'] = 50
        elif volume_ratio >= 5:
            breakdown['volume_score'] = 35
        elif volume_ratio >= 3:
            breakdown['volume_score'] = 25
        
        # RSI proxy (oversold if price below average)
        if data['price'] < data['avg_price_20d'] * 0.85:
            breakdown['rsi_score'] = 30
        elif data['price'] < data['avg_price_20d'] * 0.90:
            breakdown['rsi_score'] = 20
        
        # Breakout scoring
        if data['price'] > data['high'] * 0.95:
            breakdown['breakout_score'] = 20
        
        # Accumulation
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
        
        score = sum(breakdown.values())
        return score, breakdown
    
    def screen_market(self, date):
        """Screen stocks on a specific date"""
        print(f"\n🔍 SCREENING MARKET: {date}")
        print("="*50)
        
        # Get test stocks
        all_stocks = self.get_test_stocks()
        print(f"  Using {len(all_stocks)} test stocks")
        
        scored_stocks = []
        
        for stock_info in all_stocks:
            ticker = stock_info['ticker']
            
            # Generate mock data
            stock_data = self.generate_mock_data(ticker, date)
            
            # Apply filters
            if (stock_data['price'] >= 0.50 and 
                stock_data['price'] <= 15.00 and
                stock_data['avg_volume_20d'] >= 10000):
                
                # Calculate score
                score, breakdown = self.score_stock(ticker, stock_data)
                
                if score >= 60:
                    scored_stocks.append({
                        'ticker': ticker,
                        'score': score,
                        'score_breakdown': breakdown,
                        'entry_price': stock_data['price'],
                        'entry_volume': stock_data['volume'],
                        'screening_date': date,
                        'rank': 0,
                        'false_miss_analysis': {
                            'is_false_miss': False,
                            'status': 'MOCK_DATA',
                            'price_60d_ago': stock_data['price'] * 0.8
                        }
                    })
        
        # Sort and rank
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        for i, stock in enumerate(scored_stocks):
            stock['rank'] = i + 1
        
        # Take top 30 (or all if less)
        top_30 = scored_stocks[:30]
        runners_up = scored_stocks[30:60] if len(scored_stocks) > 30 else []
        
        print(f"  ✅ Screening complete:")
        print(f"    Qualified stocks: {len(scored_stocks)}")
        print(f"    Top 30 selected: {len(top_30)}")
        
        if top_30:
            print(f"\n  Top 5:")
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

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 4 Simplified Screener')
    parser.add_argument('--mode', choices=['test', 'full'], default='test')
    
    args = parser.parse_args()
    
    print("="*60)
    print("PHASE 4 INTEGRATED SCREENER (SIMPLIFIED)")
    print(f"Mode: {args.mode}")
    print("="*60)
    
    screener = Phase4MarketScreenerSimple()
    
    # Generate dates
    test_dates = screener.generate_strategic_dates(args.mode)
    
    # Screen each date
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
        
        for stock in result['selected_stocks']:
            all_results['all_selected_stocks'].append(stock)
        
        for stock in result['runners_up']:
            all_results['all_runners_up'].append(stock)
    
    # Save results
    output_file = 'phase4_screening_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("SCREENING COMPLETE")
    print(f"Total stocks selected: {len(all_results['all_selected_stocks'])}")
    print(f"Output: {output_file}")

if __name__ == '__main__':
    main()
