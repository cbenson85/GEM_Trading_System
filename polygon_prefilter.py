#!/usr/bin/env python3
"""
Polygon Pre-Filter - GEM Trading System
Quick scan of ALL tickers to find 500%+ gain candidates

This is Phase 0: Lightweight filtering using only high/low prices
Outputs: explosive_candidates.txt (for Phase 1 detailed analysis)

Performance: ~1 hour to scan 5,908 tickers
API Usage: ~60 calls (100 tickers per call)
"""

import os
import sys
import json
import time
from datetime import datetime
import requests

# Configuration
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
MIN_GAIN_PERCENT = 500  # 500% = 6x return
OUTPUT_FILE = 'explosive_candidates.txt'
STATS_FILE = 'prefilter_stats.json'

class PolygonPreFilter:
    def __init__(self, start_year=2016, end_year=2024):
        self.start_year = start_year
        self.end_year = end_year
        self.polygon_api_key = POLYGON_API_KEY
        self.candidates = []
        self.stats = {
            'total_tickers_scanned': 0,
            'candidates_found': 0,
            'api_calls_made': 0,
            'errors': 0,
            'scan_start': datetime.now().isoformat(),
            'years_scanned': []
        }
    
    def get_all_tickers(self):
        """
        Get complete list of US stock tickers from Polygon
        Uses pagination to get ALL tickers (not just first 1000)
        """
        print(f"\n📊 Fetching complete ticker universe from Polygon...")
        
        url = "https://api.polygon.io/v3/reference/tickers"
        params = {
            'market': 'stocks',
            'active': 'true',
            'limit': 1000,  # Max per page
            'apiKey': self.polygon_api_key
        }
        
        all_tickers = []
        page = 1
        
        try:
            next_url = url
            
            while next_url:
                print(f"   Fetching page {page}...", end='\r')
                
                if next_url == url:
                    response = requests.get(url, params=params, timeout=30)
                else:
                    response = requests.get(next_url, timeout=30)
                
                self.stats['api_calls_made'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    for ticker_data in results:
                        symbol = ticker_data.get('ticker', '')
                        # Filter for US stocks only (reasonable tickers)
                        if symbol and len(symbol) <= 6 and symbol[0].isalpha():
                            all_tickers.append(symbol)
                    
                    next_url = data.get('next_url')
                    if next_url:
                        # Add API key to next URL
                        next_url = f"{next_url}&apiKey={self.polygon_api_key}"
                        page += 1
                        time.sleep(0.2)  # Rate limit friendly
                    else:
                        break
                else:
                    print(f"\n⚠️ API error: {response.status_code}")
                    break
            
            print(f"\n✅ Found {len(all_tickers):,} tickers")
            return all_tickers
            
        except Exception as e:
            print(f"\n❌ Error fetching tickers: {e}")
            return []
    
    def check_ticker_for_explosive_gain(self, ticker, year):
        """
        Quick check: Did this ticker have 500%+ gain in this year?
        Uses only high/low prices for speed (no volume, no OHLC)
        
        Returns: (has_explosive_gain, max_gain_pct) or None if error
        """
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {
            'apiKey': self.polygon_api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000  # Get all data for the year
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            self.stats['api_calls_made'] += 1
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            results = data.get('results', [])
            
            if not results or len(results) < 60:  # Need ~3 months minimum
                return None
            
            # Quick algorithm: Find lowest low and highest high
            lowest_price = min(bar['l'] for bar in results)
            highest_price = max(bar['h'] for bar in results)
            
            max_gain_pct = ((highest_price - lowest_price) / lowest_price) * 100
            
            return (max_gain_pct >= MIN_GAIN_PERCENT, round(max_gain_pct, 1))
            
        except Exception as e:
            return None
    
    def scan_year(self, year, tickers):
        """
        Scan all tickers for a specific year
        """
        print(f"\n{'='*60}")
        print(f"🔍 PRE-FILTER SCAN: {year}")
        print(f"{'='*60}")
        print(f"Tickers to scan: {len(tickers):,}")
        print(f"Strategy: Quick high/low price check only")
        
        candidates_found = 0
        
        for idx, ticker in enumerate(tickers, 1):
            # Progress indicator every 100 tickers
            if idx % 100 == 0:
                print(f"Progress: {idx:,}/{len(tickers):,} | Candidates: {candidates_found} | API calls: {self.stats['api_calls_made']:,}", end='\r')
            
            self.stats['total_tickers_scanned'] += 1
            
            # Quick check
            result = self.check_ticker_for_explosive_gain(ticker, year)
            
            if result is None:
                self.stats['errors'] += 1
                continue
            
            has_explosive, max_gain = result
            
            if has_explosive:
                candidates_found += 1
                self.stats['candidates_found'] += 1
                
                candidate_entry = f"{ticker},{year},{max_gain}"
                self.candidates.append(candidate_entry)
                
                # Show significant finds immediately
                if max_gain > 1000:
                    print(f"\n🚀 {ticker} ({year}): {max_gain:.0f}% potential gain")
            
            # Rate limiting: ~6-7 requests per second
            time.sleep(0.15)
        
        print(f"\n✅ Year {year} complete: {candidates_found} candidates found")
        self.stats['years_scanned'].append({
            'year': year,
            'candidates': candidates_found
        })
    
    def save_results(self):
        """
        Save candidate list and statistics
        """
        # Save candidates to text file (one per line: ticker,year,gain_pct)
        print(f"\n💾 Saving results...")
        
        with open(OUTPUT_FILE, 'w') as f:
            f.write("# Explosive Stock Candidates (500%+ annual gains)\n")
            f.write("# Format: TICKER,YEAR,MAX_GAIN_PCT\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total candidates: {len(self.candidates)}\n")
            f.write("#\n")
            for candidate in self.candidates:
                f.write(f"{candidate}\n")
        
        print(f"✅ Candidates saved: {OUTPUT_FILE}")
        
        # Save statistics to JSON
        self.stats['scan_end'] = datetime.now().isoformat()
        self.stats['total_candidates'] = len(self.candidates)
        
        with open(STATS_FILE, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        print(f"✅ Statistics saved: {STATS_FILE}")
    
    def generate_report(self):
        """
        Generate summary report
        """
        print(f"\n{'='*60}")
        print(f"📊 PRE-FILTER COMPLETE - SUMMARY")
        print(f"{'='*60}")
        print(f"\nTotal tickers scanned: {self.stats['total_tickers_scanned']:,}")
        print(f"Explosive candidates found: {self.stats['candidates_found']:,}")
        print(f"Hit rate: {(self.stats['candidates_found'] / max(self.stats['total_tickers_scanned'], 1)) * 100:.2f}%")
        print(f"API calls made: {self.stats['api_calls_made']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        
        print(f"\n📅 Candidates by year:")
        for year_data in self.stats['years_scanned']:
            print(f"   {year_data['year']}: {year_data['candidates']:>4} candidates")
        
        print(f"\n📄 Output file: {OUTPUT_FILE}")
        print(f"   Format: TICKER,YEAR,MAX_GAIN_PCT")
        print(f"   Total lines: {len(self.candidates):,}")
        
        print(f"\n✅ Ready for Phase 1 (detailed analysis)")

def main():
    """
    Main execution
    """
    print("="*60)
    print(" POLYGON PRE-FILTER - Phase 0")
    print(" GEM Trading System")
    print("="*60)
    print(f"\nQuick scan strategy: High/Low price analysis only")
    print(f"Threshold: {MIN_GAIN_PERCENT}%+ annual gain")
    print(f"Coverage: ALL tickers (no 1,000 limit)")
    
    # Get parameters from environment (GitHub Actions)
    start_year = int(os.environ.get('START_YEAR', '2016'))
    end_year = int(os.environ.get('END_YEAR', '2024'))
    
    print(f"\nScan period: {start_year}-{end_year}")
    print(f"Estimated time: ~1 hour for all tickers")
    print(f"API tier: Developer (100 calls/min)")
    
    # Initialize scanner
    prefilter = PolygonPreFilter(start_year=start_year, end_year=end_year)
    
    # Get complete ticker universe (ALL tickers, not just 1000)
    all_tickers = prefilter.get_all_tickers()
    
    if not all_tickers:
        print("❌ Failed to fetch ticker universe")
        sys.exit(1)
    
    # Scan each year
    for year in range(start_year, end_year + 1):
        prefilter.scan_year(year, all_tickers)
    
    # Save and report
    prefilter.save_results()
    prefilter.generate_report()
    
    print(f"\n✅ Pre-filter complete!")
    print(f"📄 Next step: Run explosive_stock_scanner.py --use-prefilter")

if __name__ == "__main__":
    main()
