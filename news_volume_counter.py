"""
News Volume Counter - Phase 3B Automation Script #3
Uses Google News to count article acceleration
"""

import os
import json
from datetime import datetime, timedelta
import time
from GoogleNews import GoogleNews

class NewsVolumeCounter:
    def __init__(self):
        """Initialize news counter"""
        self.googlenews = GoogleNews()
    
    def count_news_articles(self, ticker, start_date, end_date):
        """
        Count news articles in date range
        """
        try:
            # Set date range
            self.googlenews.set_time_range(
                start_date.strftime('%m/%d/%Y'),
                end_date.strftime('%m/%d/%Y')
            )
            
            # Search for ticker + company terms
            queries = [
                ticker,
                f"{ticker} stock",
                f"{ticker} shares"
            ]
            
            all_results = []
            
            for query in queries:
                self.googlenews.clear()
                self.googlenews.search(query)
                results = self.googlenews.results()
                
                if results:
                    all_results.extend(results)
                
                time.sleep(1)  # Rate limit
            
            # Remove duplicates by title
            unique_results = []
            seen_titles = set()
            
            for result in all_results:
                title = result.get('title', '')
                if title and title not in seen_titles:
                    unique_results.append(result)
                    seen_titles.add(title)
            
            return unique_results
            
        except Exception as e:
            print(f"  ERROR counting news: {e}")
            return []
    
    def analyze(self, ticker, entry_date):
        """
        Main analysis function
        """
        # Convert entry_date to datetime if string
        if isinstance(entry_date, str):
            entry_date = datetime.fromisoformat(entry_date)
        
        # Calculate windows
        full_window_start = entry_date - timedelta(days=90)
        baseline_start = entry_date - timedelta(days=90)
        baseline_end = entry_date - timedelta(days=30)
        recent_start = entry_date - timedelta(days=30)
        
        print(f"\n📰 Analyzing News Volume: {ticker}")
        print(f"  Full Window: {full_window_start.date()} to {entry_date.date()}")
        
        # Get baseline news count (days 90-30)
        print(f"  Counting baseline news (days 90-30)...")
        baseline_articles = self.count_news_articles(ticker, baseline_start, baseline_end)
        baseline_count = len(baseline_articles)
        print(f"  Baseline: {baseline_count} articles")
        
        # Get recent news count (days 30-0)
        print(f"  Counting recent news (days 30-0)...")
        recent_articles = self.count_news_articles(ticker, recent_start, entry_date)
        recent_count = len(recent_articles)
        print(f"  Recent: {recent_count} articles")
        
        # Calculate acceleration
        if baseline_count > 0:
            acceleration = recent_count / baseline_count
        else:
            acceleration = recent_count if recent_count > 0 else 0
        
        # Detect patterns
        news_acceleration_3x = acceleration >= 3.0
        news_acceleration_5x = acceleration >= 5.0
        
        if news_acceleration_5x:
            print(f"  ✅ PATTERN: 5x+ news acceleration!")
        elif news_acceleration_3x:
            print(f"  ✅ PATTERN: 3x+ news acceleration!")
        else:
            print(f"  ❌ No significant news acceleration ({acceleration:.1f}x)")
        
        # Build result
        result = {
            'ticker': ticker,
            'analysis_window': {
                'start_date': full_window_start.strftime('%Y-%m-%d'),
                'end_date': entry_date.strftime('%Y-%m-%d'),
                'days': 90
            },
            'news_volume': {
                'baseline_count': baseline_count,
                'recent_count': recent_count,
                'acceleration_ratio': round(acceleration, 2),
                'baseline_period': '90-30 days before',
                'recent_period': '30-0 days before'
            },
            'patterns_detected': {
                'news_acceleration_3x': news_acceleration_3x,
                'news_acceleration_5x': news_acceleration_5x,
                'pattern_score': 30 if news_acceleration_3x else 0
            },
            'data_quality': 'good' if (baseline_count + recent_count) >= 5 else 'low_coverage'
        }
        
        return result


def analyze_multiple_stocks(stocks_file, output_dir='Verified_Backtest_Data'):
    """
    Analyze multiple stocks from CLEAN.json
    """
    # Load stocks
    print(f"Loading stocks from {stocks_file}...")
    with open(stocks_file, 'r') as f:
        data = json.load(f)
        stocks = data.get('stocks', data)
    
    print(f"Found {len(stocks)} stocks\n")
    
    # Initialize counter
    counter = NewsVolumeCounter()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze each stock
    results = []
    errors = []
    
    for i, stock in enumerate(stocks):
        ticker = stock['ticker']
        year = stock['year']
        entry_date = stock['entry_date']
        
        print(f"[{i+1}/{len(stocks)}] {ticker} ({year})")
        
        try:
            result = counter.analyze(ticker, entry_date)
            result['year'] = year
            result['gain_percent'] = stock['gain_percent']
            
            # Save individual result
            output_file = f'{output_dir}/phase3b_{ticker}_{year}_news_volume.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            results.append(result)
            
            # Rate limiting
            time.sleep(3)
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            errors.append({'ticker': ticker, 'year': year, 'error': str(e)})
            continue
    
    # Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Successful: {len(results)}/{len(stocks)}")
    print(f"Errors: {len(errors)}/{len(stocks)}")
    
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err['ticker']} ({err['year']}): {err['error']}")
    
    # Calculate pattern frequency
    accel_3x = sum(1 for r in results if r.get('patterns_detected', {}).get('news_acceleration_3x'))
    accel_5x = sum(1 for r in results if r.get('patterns_detected', {}).get('news_acceleration_5x'))
    
    print(f"\n📊 PATTERN FREQUENCY:")
    print(f"  News Acceleration 3x+: {accel_3x}/{len(results)} ({accel_3x/len(results)*100:.1f}%)")
    print(f"  News Acceleration 5x+: {accel_5x}/{len(results)} ({accel_5x/len(results)*100:.1f}%)")
    
    return results, errors


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 2:
        stocks_file = sys.argv[1]
        print(f"Analyzing all stocks from {stocks_file}...")
        analyze_multiple_stocks(stocks_file)
    else:
        print("Usage:")
        print("  python news_volume_counter.py explosive_stocks_CLEAN.json")
