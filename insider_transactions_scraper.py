"""
Multi-Source News Analyzer - Phase 3B Automation Script #3 (Enhanced)
Uses Yahoo Finance RSS + Google News for better coverage
"""

import os
import json
from datetime import datetime, timedelta
import time
import requests
from bs4 import BeautifulSoup

try:
    from GoogleNews import GoogleNews
    GOOGLE_NEWS_AVAILABLE = True
except ImportError:
    GOOGLE_NEWS_AVAILABLE = False
    print("WARNING: GoogleNews not installed")

class MultiSourceNewsAnalyzer:
    def __init__(self):
        """Initialize news sources"""
        if GOOGLE_NEWS_AVAILABLE:
            self.googlenews = GoogleNews()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_yahoo_finance_news(self, ticker, start_date, end_date):
        """
        Scrape Yahoo Finance news RSS feed
        """
        articles = []
        
        try:
            # Yahoo Finance RSS URL
            url = f'https://finance.yahoo.com/rss/headline?s={ticker}'
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')
                
                for item in items:
                    try:
                        pub_date_str = item.find('pubDate').text if item.find('pubDate') else None
                        title = item.find('title').text if item.find('title') else None
                        
                        if pub_date_str and title:
                            # Parse date
                            pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                            pub_date = pub_date.replace(tzinfo=None)
                            
                            # Filter by date range
                            if start_date <= pub_date <= end_date:
                                articles.append({
                                    'title': title,
                                    'date': pub_date.strftime('%Y-%m-%d'),
                                    'source': 'yahoo_finance'
                                })
                    except:
                        continue
            
            return articles
            
        except Exception as e:
            print(f"  Yahoo Finance error: {e}")
            return []
    
    def get_google_news_articles(self, ticker, start_date, end_date):
        """
        Get articles from Google News (with rate limiting)
        """
        if not GOOGLE_NEWS_AVAILABLE:
            return []
        
        articles = []
        
        try:
            self.googlenews.set_time_range(
                start_date.strftime('%m/%d/%Y'),
                end_date.strftime('%m/%d/%Y')
            )
            
            # Try ticker only (simpler query)
            self.googlenews.clear()
            self.googlenews.search(ticker)
            results = self.googlenews.results()
            
            if results:
                for result in results:
                    articles.append({
                        'title': result.get('title', ''),
                        'date': result.get('date', ''),
                        'source': 'google_news'
                    })
            
            time.sleep(10)  # Rate limit
            
            return articles
            
        except Exception as e:
            if "429" in str(e):
                print(f"  Google News rate limit - skipping")
            else:
                print(f"  Google News error: {e}")
            return []
    
    def count_news_articles(self, ticker, start_date, end_date):
        """
        Count news articles from multiple sources
        """
        all_articles = []
        
        # Try Yahoo Finance first (more reliable)
        print(f"  Fetching Yahoo Finance news...")
        yahoo_articles = self.get_yahoo_finance_news(ticker, start_date, end_date)
        all_articles.extend(yahoo_articles)
        print(f"  Yahoo: {len(yahoo_articles)} articles")
        
        time.sleep(2)
        
        # Try Google News as supplement (if available and not rate limited)
        if GOOGLE_NEWS_AVAILABLE:
            print(f"  Fetching Google News...")
            google_articles = self.get_google_news_articles(ticker, start_date, end_date)
            all_articles.extend(google_articles)
            print(f"  Google: {len(google_articles)} articles")
        
        # Remove duplicates by title
        unique_articles = []
        seen_titles = set()
        
        for article in all_articles:
            title = article.get('title', '').lower()
            if title and title not in seen_titles:
                unique_articles.append(article)
                seen_titles.add(title)
        
        return unique_articles
    
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
        print(f"  Baseline total: {baseline_count} articles")
        
        time.sleep(3)
        
        # Get recent news count (days 30-0)
        print(f"  Counting recent news (days 30-0)...")
        recent_articles = self.count_news_articles(ticker, recent_start, entry_date)
        recent_count = len(recent_articles)
        print(f"  Recent total: {recent_count} articles")
        
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
                'recent_period': '30-0 days before',
                'sources_used': ['yahoo_finance'] + (['google_news'] if GOOGLE_NEWS_AVAILABLE else [])
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
    
    # Initialize analyzer
    analyzer = MultiSourceNewsAnalyzer()
    
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
            result = analyzer.analyze(ticker, entry_date)
            result['year'] = year
            result['gain_percent'] = stock['gain_percent']
            
            # Save individual result
            output_file = f'{output_dir}/phase3b_{ticker}_{year}_news_volume.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            results.append(result)
            
            # Rate limiting between stocks
            time.sleep(15)  # 15 seconds between stocks
            
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
