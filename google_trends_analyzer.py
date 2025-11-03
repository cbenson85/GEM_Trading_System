"""
Google Trends Analyzer - Phase 3B Automation Script #4
Uses Google Trends to detect search volume spikes
"""

import os
import json
from datetime import datetime, timedelta
import time

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("WARNING: pytrends not installed. Run: pip install pytrends")

class GoogleTrendsAnalyzer:
    def __init__(self):
        """Initialize Google Trends API"""
        if not PYTRENDS_AVAILABLE:
            raise ImportError("pytrends library required. Install with: pip install pytrends")
        
        self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=3)
    
    def get_search_interest(self, ticker, start_date, end_date):
        """
        Get Google search interest over time
        """
        try:
            # Build keyword list - try multiple variations
            keywords = [ticker]
            
            # Format dates for Google Trends
            timeframe = f'{start_date.strftime("%Y-%m-%d")} {end_date.strftime("%Y-%m-%d")}'
            
            # Build payload
            self.pytrends.build_payload(
                keywords,
                cat=0,
                timeframe=timeframe,
                geo='US',
                gprop=''
            )
            
            # Get interest over time
            interest_df = self.pytrends.interest_over_time()
            
            if interest_df.empty or ticker not in interest_df.columns:
                return None
            
            # Extract data
            data = []
            for date, row in interest_df.iterrows():
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'interest': int(row[ticker])
                })
            
            return data
            
        except Exception as e:
            print(f"  ERROR fetching trends: {e}")
            return None
    
    def analyze(self, ticker, entry_date):
        """
        Main analysis function
        """
        # Convert entry_date to datetime if string
        if isinstance(entry_date, str):
            entry_date = datetime.fromisoformat(entry_date)
        
        # Calculate windows
        start_date = entry_date - timedelta(days=90)
        baseline_end = entry_date - timedelta(days=30)
        
        print(f"\n📈 Analyzing Google Trends: {ticker}")
        print(f"  Window: {start_date.date()} to {entry_date.date()}")
        
        # Get search interest
        print(f"  Fetching Google Trends data...")
        interest_data = self.get_search_interest(ticker, start_date, entry_date)
        
        if not interest_data:
            return {
                'error': f'No Google Trends data for {ticker}',
                'data_quality': 'no_data'
            }
        
        # Split into baseline and recent periods
        baseline_data = [d for d in interest_data if datetime.fromisoformat(d['date']) <= baseline_end]
        recent_data = [d for d in interest_data if datetime.fromisoformat(d['date']) > baseline_end]
        
        # Calculate averages
        baseline_avg = sum(d['interest'] for d in baseline_data) / len(baseline_data) if baseline_data else 0
        recent_avg = sum(d['interest'] for d in recent_data) / len(recent_data) if recent_data else 0
        
        # Calculate max spike
        max_interest = max(d['interest'] for d in interest_data) if interest_data else 0
        
        # Calculate acceleration
        if baseline_avg > 0:
            acceleration = recent_avg / baseline_avg
        else:
            acceleration = recent_avg if recent_avg > 0 else 0
        
        # Detect patterns
        trends_spike_2x = acceleration >= 2.0
        trends_spike_5x = acceleration >= 5.0
        high_absolute_interest = max_interest >= 50  # Google Trends scale 0-100
        
        if trends_spike_5x:
            print(f"  ✅ PATTERN: 5x+ Google Trends spike!")
        elif trends_spike_2x:
            print(f"  ✅ PATTERN: 2x+ Google Trends spike!")
        elif high_absolute_interest:
            print(f"  ⚠️  High absolute interest (max: {max_interest})")
        else:
            print(f"  ❌ No significant trends spike ({acceleration:.1f}x)")
        
        # Build result
        result = {
            'ticker': ticker,
            'analysis_window': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': entry_date.strftime('%Y-%m-%d'),
                'days': 90
            },
            'trends_data': {
                'baseline_avg_interest': round(baseline_avg, 2),
                'recent_avg_interest': round(recent_avg, 2),
                'max_interest': max_interest,
                'acceleration_ratio': round(acceleration, 2),
                'data_points': len(interest_data)
            },
            'patterns_detected': {
                'trends_spike_2x': trends_spike_2x,
                'trends_spike_5x': trends_spike_5x,
                'high_absolute_interest': high_absolute_interest,
                'pattern_score': 40 if trends_spike_5x else (20 if trends_spike_2x else (10 if high_absolute_interest else 0))
            },
            'data_quality': 'good' if len(interest_data) >= 12 else 'acceptable' if len(interest_data) >= 6 else 'poor'
        }
        
        return result


def analyze_multiple_stocks(stocks_file, output_dir='Verified_Backtest_Data'):
    """
    Analyze multiple stocks from CLEAN.json
    """
    if not PYTRENDS_AVAILABLE:
        print("ERROR: pytrends not installed")
        return [], []
    
    # Load stocks
    print(f"Loading stocks from {stocks_file}...")
    with open(stocks_file, 'r') as f:
        data = json.load(f)
        stocks = data.get('stocks', data)
    
    print(f"Found {len(stocks)} stocks\n")
    
    # Initialize analyzer
    analyzer = GoogleTrendsAnalyzer()
    
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
            output_file = f'{output_dir}/phase3b_{ticker}_{year}_google_trends.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            results.append(result)
            
            # Rate limiting - Google is strict
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
    spike_2x = sum(1 for r in results if r.get('patterns_detected', {}).get('trends_spike_2x'))
    spike_5x = sum(1 for r in results if r.get('patterns_detected', {}).get('trends_spike_5x'))
    high_interest = sum(1 for r in results if r.get('patterns_detected', {}).get('high_absolute_interest'))
    
    print(f"\n📊 PATTERN FREQUENCY:")
    print(f"  Trends Spike 2x+: {spike_2x}/{len(results)} ({spike_2x/len(results)*100:.1f}%)")
    print(f"  Trends Spike 5x+: {spike_5x}/{len(results)} ({spike_5x/len(results)*100:.1f}%)")
    print(f"  High Absolute Interest: {high_interest}/{len(results)} ({high_interest/len(results)*100:.1f}%)")
    
    return results, errors


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 2:
        stocks_file = sys.argv[1]
        print(f"Analyzing all stocks from {stocks_file}...")
        analyze_multiple_stocks(stocks_file)
    else:
        print("Usage:")
        print("  python google_trends_analyzer.py explosive_stocks_CLEAN.json")
