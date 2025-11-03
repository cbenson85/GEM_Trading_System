"""
Insider Transactions Scraper - Phase 3B Automation Script #2
Uses SEC Edgar API to detect insider buying clusters
"""

import os
import json
import requests
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup

class InsiderTransactionsScraper:
    def __init__(self):
        """Initialize scraper"""
        self.base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        self.headers = {
            'User-Agent': 'GEM Trading System chris@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
    
    def get_cik_from_ticker(self, ticker):
        """
        Convert ticker to CIK number using SEC API
        """
        try:
            url = f"https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'company': ticker,
                'type': '',
                'dateb': '',
                'owner': 'exclude',
                'count': 1,
                'output': 'atom'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                return None
            
            # Parse CIK from response
            soup = BeautifulSoup(response.text, 'xml')
            company_info = soup.find('company-info')
            
            if company_info:
                cik = company_info.get_text().strip().split('\n')[0]
                return cik.strip()
            
            return None
            
        except Exception as e:
            print(f"  ERROR getting CIK: {e}")
            return None
    
    def scrape_form4_filings(self, ticker, entry_date):
        """
        Scrape Form 4 insider transaction filings
        """
        try:
            # Get CIK
            cik = self.get_cik_from_ticker(ticker)
            if not cik:
                return None
            
            # Calculate date range
            start_date = entry_date - timedelta(days=90)
            
            # Query SEC Edgar
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': '4',
                'dateb': entry_date.strftime('%Y%m%d'),
                'datea': start_date.strftime('%Y%m%d'),
                'owner': 'include',
                'output': 'atom',
                'count': 100
            }
            
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                return None
            
            # Parse filings
            soup = BeautifulSoup(response.text, 'xml')
            entries = soup.find_all('entry')
            
            transactions = []
            
            for entry in entries:
                try:
                    filing_date = entry.find('filing-date').get_text() if entry.find('filing-date') else None
                    filing_href = entry.find('filing-href').get_text() if entry.find('filing-href') else None
                    
                    if filing_date:
                        transactions.append({
                            'filing_date': filing_date,
                            'filing_url': filing_href
                        })
                except:
                    continue
            
            return transactions
            
        except Exception as e:
            print(f"  ERROR scraping Form 4: {e}")
            return None
    
    def analyze(self, ticker, entry_date):
        """
        Main analysis function
        """
        # Convert entry_date to datetime if string
        if isinstance(entry_date, str):
            entry_date = datetime.fromisoformat(entry_date)
        
        start_date = entry_date - timedelta(days=90)
        
        print(f"\n📋 Analyzing Insider Transactions: {ticker}")
        print(f"  Window: {start_date.date()} to {entry_date.date()}")
        
        # Scrape Form 4 filings
        print(f"  Fetching Form 4 filings...")
        filings = self.scrape_form4_filings(ticker, entry_date)
        
        if filings is None:
            return {
                'error': f'Could not fetch insider data for {ticker}',
                'data_quality': 'no_data'
            }
        
        # Count transactions
        num_filings = len(filings)
        print(f"  Found {num_filings} Form 4 filings")
        
        # Detect cluster (3+ filings in 30-day window)
        cluster_detected = False
        if num_filings >= 3:
            # Sort by date
            sorted_filings = sorted(filings, key=lambda x: x['filing_date'])
            
            # Check for cluster
            for i in range(len(sorted_filings) - 2):
                window_start = datetime.fromisoformat(sorted_filings[i]['filing_date'])
                window_end = window_start + timedelta(days=30)
                
                count_in_window = sum(
                    1 for f in sorted_filings[i:]
                    if window_start <= datetime.fromisoformat(f['filing_date']) <= window_end
                )
                
                if count_in_window >= 3:
                    cluster_detected = True
                    break
        
        if cluster_detected:
            print(f"  ✅ PATTERN: Insider buying cluster detected!")
        else:
            print(f"  ❌ No insider buying cluster")
        
        # Build result
        result = {
            'ticker': ticker,
            'analysis_window': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': entry_date.strftime('%Y-%m-%d'),
                'days': (entry_date - start_date).days
            },
            'insider_activity': {
                'total_form4_filings': num_filings,
                'filings': filings[:10]  # First 10 filings
            },
            'patterns_detected': {
                'insider_cluster_3plus': cluster_detected,
                'pattern_score': 50 if cluster_detected else 0
            },
            'data_quality': 'good' if num_filings > 0 else 'no_activity'
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
    
    # Initialize scraper
    scraper = InsiderTransactionsScraper()
    
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
            result = scraper.analyze(ticker, entry_date)
            result['year'] = year
            result['gain_percent'] = stock['gain_percent']
            
            # Save individual result
            output_file = f'{output_dir}/phase3b_{ticker}_{year}_insider_transactions.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            results.append(result)
            
            # Rate limiting - SEC requires 10 requests per second max
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
    clusters_detected = sum(1 for r in results if r.get('patterns_detected', {}).get('insider_cluster_3plus'))
    has_activity = sum(1 for r in results if r.get('insider_activity', {}).get('total_form4_filings', 0) > 0)
    
    print(f"\n📊 PATTERN FREQUENCY:")
    print(f"  Insider Clusters (3+): {clusters_detected}/{len(results)} ({clusters_detected/len(results)*100:.1f}%)")
    print(f"  Any Insider Activity: {has_activity}/{len(results)} ({has_activity/len(results)*100:.1f}%)")
    
    return results, errors


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 2:
        stocks_file = sys.argv[1]
        print(f"Analyzing all stocks from {stocks_file}...")
        analyze_multiple_stocks(stocks_file)
    else:
        print("Usage:")
        print("  python insider_transactions_scraper.py explosive_stocks_CLEAN.json")
