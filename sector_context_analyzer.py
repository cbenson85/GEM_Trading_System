"""
Sector Context Analyzer - Phase 3B Automation Script #1
Uses Polygon API to calculate relative strength vs SPY/QQQ

This is the EASIEST script - start here to test your setup!
"""

import os
import json
from datetime import datetime, timedelta
from polygon import RESTClient
import time

class SectorContextAnalyzer:
    def __init__(self, api_key):
        """Initialize with Polygon API key"""
        self.client = RESTClient(api_key)
    
    def get_price_data(self, ticker, start_date, end_date):
        """
        Get OHLC data from Polygon
        Returns: list of daily bars
        """
        try:
            # Polygon date format: YYYY-MM-DD
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan='day',
                from_=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d'),
                limit=50000
            )
            
            # Convert to list
            return list(aggs)
            
        except Exception as e:
            print(f"  ERROR fetching {ticker}: {e}")
            return None
    
    def calculate_return(self, price_data):
        """
        Calculate total return from price data
        """
        if not price_data or len(price_data) < 2:
            return None
        
        first_close = price_data[0].close
        last_close = price_data[-1].close
        
        return ((last_close - first_close) / first_close) * 100
    
    def analyze(self, ticker, entry_date):
        """
        Main analysis function
        
        Args:
            ticker: Stock ticker (e.g., 'AENTW')
            entry_date: datetime object or string 'YYYY-MM-DD'
        
        Returns:
            dict with sector context analysis
        """
        # Convert entry_date to datetime if string
        if isinstance(entry_date, str):
            entry_date = datetime.fromisoformat(entry_date)
        
        # Calculate 90-day window
        start_date = entry_date - timedelta(days=90)
        
        print(f"\n📊 Analyzing {ticker}")
        print(f"  Window: {start_date.date()} to {entry_date.date()}")
        
        # Get ticker data
        print(f"  Fetching {ticker} data...")
        ticker_data = self.get_price_data(ticker, start_date, entry_date)
        
        if not ticker_data:
            return {
                'error': f'No data available for {ticker}',
                'data_quality': 'no_data'
            }
        
        ticker_return = self.calculate_return(ticker_data)
        print(f"  {ticker} return: {ticker_return:.2f}%")
        
        # Get SPY data
        print(f"  Fetching SPY data...")
        time.sleep(0.6)  # Rate limit: 100/min = ~0.6s between calls
        spy_data = self.get_price_data('SPY', start_date, entry_date)
        spy_return = self.calculate_return(spy_data) if spy_data else None
        
        if spy_return:
            print(f"  SPY return: {spy_return:.2f}%")
        
        # Get QQQ data
        print(f"  Fetching QQQ data...")
        time.sleep(0.6)
        qqq_data = self.get_price_data('QQQ', start_date, entry_date)
        qqq_return = self.calculate_return(qqq_data) if qqq_data else None
        
        if qqq_return:
            print(f"  QQQ return: {qqq_return:.2f}%")
        
        # Calculate relative strength
        relative_spy = ticker_return - spy_return if spy_return else None
        relative_qqq = ticker_return - qqq_return if qqq_return else None
        
        # Detect patterns
        outperforming_spy = relative_spy > 0 if relative_spy else False
        outperforming_qqq = relative_qqq > 0 if relative_qqq else False
        outperforming_both = outperforming_spy and outperforming_qqq
        
        if outperforming_both:
            print(f"  ✅ PATTERN: Outperforming BOTH SPY and QQQ!")
        elif outperforming_spy or outperforming_qqq:
            print(f"  ⚠️  Outperforming {'SPY' if outperforming_spy else 'QQQ'} only")
        else:
            print(f"  ❌ Underperforming market")
        
        # Build result
        result = {
            'ticker': ticker,
            'analysis_window': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': entry_date.strftime('%Y-%m-%d'),
                'days': (entry_date - start_date).days,
                'data_points': len(ticker_data)
            },
            'returns': {
                'ticker_return_pct': round(ticker_return, 2),
                'spy_return_pct': round(spy_return, 2) if spy_return else None,
                'qqq_return_pct': round(qqq_return, 2) if qqq_return else None,
                'relative_strength_spy': round(relative_spy, 2) if relative_spy else None,
                'relative_strength_qqq': round(relative_qqq, 2) if relative_qqq else None
            },
            'patterns_detected': {
                'outperforming_spy': outperforming_spy,
                'outperforming_qqq': outperforming_qqq,
                'outperforming_both': outperforming_both,
                'pattern_score': 30 if outperforming_both else (15 if (outperforming_spy or outperforming_qqq) else 0)
            },
            'data_quality': 'good' if len(ticker_data) >= 60 else 'acceptable' if len(ticker_data) >= 30 else 'poor'
        }
        
        return result


def test_single_stock():
    """
    Test function - analyze one stock
    """
    # Get API key from environment or replace with your key
    api_key = os.environ.get('POLYGON_API_KEY', 'YOUR_API_KEY_HERE')
    
    if api_key == 'YOUR_API_KEY_HERE':
        print("❌ ERROR: Set POLYGON_API_KEY environment variable or edit this file")
        return
    
    # Initialize analyzer
    analyzer = SectorContextAnalyzer(api_key)
    
    # Test on AAPL (easy test case)
    ticker = 'AAPL'
    entry_date = '2024-04-01'
    
    print("=" * 60)
    print("TESTING SECTOR CONTEXT ANALYZER")
    print("=" * 60)
    
    result = analyzer.analyze(ticker, entry_date)
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    
    print("\n✅ Test complete!")


def analyze_multiple_stocks(stocks_file, output_dir='Verified_Backtest_Data'):
    """
    Analyze multiple stocks from CLEAN.json
    
    Args:
        stocks_file: Path to explosive_stocks_CLEAN.json
        output_dir: Where to save results
    """
    # Get API key
    api_key = os.environ.get('POLYGON_API_KEY', 'YOUR_API_KEY_HERE')
    
    if api_key == 'YOUR_API_KEY_HERE':
        print("❌ ERROR: Set POLYGON_API_KEY environment variable")
        return
    
    # Load stocks
    print(f"Loading stocks from {stocks_file}...")
    with open(stocks_file, 'r') as f:
        data = json.load(f)
        stocks = data.get('stocks', data)
    
    print(f"Found {len(stocks)} stocks\n")
    
    # Initialize analyzer
    analyzer = SectorContextAnalyzer(api_key)
    
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
            output_file = f'{output_dir}/phase3b_{ticker}_{year}_sector_context.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            results.append(result)
            
            # Rate limiting
            time.sleep(2)  # Be nice to Polygon API
            
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
    outperforming_both = sum(1 for r in results if r.get('patterns_detected', {}).get('outperforming_both'))
    outperforming_any = sum(1 for r in results if r.get('patterns_detected', {}).get('outperforming_spy') or r.get('patterns_detected', {}).get('outperforming_qqq'))
    
    print(f"\n📊 PATTERN FREQUENCY:")
    print(f"  Outperforming BOTH: {outperforming_both}/{len(results)} ({outperforming_both/len(results)*100:.1f}%)")
    print(f"  Outperforming ANY: {outperforming_any}/{len(results)} ({outperforming_any/len(results)*100:.1f}%)")
    
    return results, errors


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # Test mode
        print("Running test mode...")
        test_single_stock()
        
    elif len(sys.argv) == 2:
        # Analyze all stocks
        stocks_file = sys.argv[1]
        print(f"Analyzing all stocks from {stocks_file}...")
        analyze_multiple_stocks(stocks_file)
        
    else:
        print("Usage:")
        print("  python sector_context_analyzer.py                    # Test mode")
        print("  python sector_context_analyzer.py CLEAN.json         # Analyze all stocks")
