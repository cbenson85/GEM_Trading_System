import json
import os
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')

# Import Polygon client for short interest
try:
    from polygon import RESTClient
    polygon_client = RESTClient(POLYGON_API_KEY) if POLYGON_API_KEY else None
except ImportError:
    polygon_client = None
    print("Warning: polygon-api-client not installed. Short interest data unavailable.")

class PreCatalystFingerprint:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.api_calls = 0
        
    def collect_all_fingerprints(self, input_file: str, output_file: str):
        """Main method to collect RAW DATA ONLY - no analysis"""
        
        print("="*60)
        print("RAW DATA COLLECTION - ADVANCED TIER")
        print("="*60)
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data['discoveries']
        print(f"Found {len(explosions)} explosions to collect")
        
        fingerprints = []
        
        for i, explosion in enumerate(explosions):
            print(f"\n[{i+1}/{len(explosions)}] Processing {explosion['ticker']}...")
            
            try:
                fingerprint = self.build_complete_fingerprint(explosion)
                fingerprints.append(fingerprint)
                
                if (i + 1) % 10 == 0:
                    self.save_progress(fingerprints, 'fingerprints_progress.json')
                    print(f"  Saved progress: {len(fingerprints)} complete")
                
                time.sleep(0.15)
                
            except Exception as e:
                print(f"  Error: {e}")
                fingerprints.append({
                    'ticker': explosion['ticker'],
                    'error': str(e),
                    'explosion_data': explosion
                })
        
        self.save_final_analysis(fingerprints, output_file)
    
    def build_complete_fingerprint(self, explosion: Dict) -> Dict:
        """Build fingerprint with ALL RAW DATA including short interest"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Time windows
        t_minus_365 = (catalyst_dt - timedelta(days=365)).strftime('%Y-%m-%d')
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        t_minus_3 = (catalyst_dt - timedelta(days=3)).strftime('%Y-%m-%d')
        t_plus_3 = (catalyst_dt + timedelta(days=3)).strftime('%Y-%m-%d')
        t_plus_5 = (catalyst_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        t_plus_30 = (catalyst_dt + timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"  Collecting raw data for {ticker}...")
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_metrics': explosion,
            
            # 1. TICKER PROFILE (T-120)
            'ticker_details': self.get_ticker_details_raw(ticker, t_minus_120),
            
            # 2. PRICE & VOLUME HISTORY (365 days)
            'price_bars': self.get_price_bars_raw(ticker, t_minus_365, t_plus_30),
            'spy_bars': self.get_price_bars_raw('SPY', t_minus_365, t_plus_30),
            
            # 3. INTRADAY DATA (T-3 to T+3)
            'intraday_bars': self.get_intraday_bars_raw(ticker, t_minus_3, t_plus_3),
            
            # 4. FINANCIALS (Quarterly)
            'financials': self.get_stock_financials_raw(ticker),
            
            # 5. SHORT INTEREST - THE SQUEEZE FUEL
            'short_interest': self.get_short_interest_raw(ticker),
            
            # 6. OPTIONS SNAPSHOT (30 days before catalyst)
            'options_snapshot': self.get_options_snapshot_raw(ticker, t_minus_30, catalyst_date),
            
            # 7. NEWS HEADLINES
            'news': self.get_news_raw(ticker, t_minus_30, t_plus_5),
            
            # 8. SNAPSHOT (current)
            'snapshot': self.get_snapshot_raw(ticker),
            
            # 9. PREVIOUS DAYS
            'previous_days': self.get_previous_days_raw(ticker, catalyst_dt)
        }
        
        return fingerprint
    
    def get_ticker_details_raw(self, ticker: str, as_of_date: str) -> Dict:
        """Get raw ticker details including CIK"""
        
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        params = {'apiKey': self.api_key, 'date': as_of_date}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                return response.json().get('results', {})
            
        except Exception as e:
            print(f"    Ticker details error: {e}")
        
        return {}
    
    def get_price_bars_raw(self, ticker: str, start: str, end: str) -> List:
        """Get raw OHLCV bars - NO CALCULATIONS"""
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true', 'sort': 'asc', 'limit': 50000}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                bars = data.get('results', [])
                # Add readable date for each bar
                for bar in bars:
                    bar['date'] = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d')
                return bars
            
        except Exception as e:
            print(f"    Price bars error: {e}")
        
        return []
    
    def get_stock_financials_raw(self, ticker: str) -> Dict:
        """Get raw stock financials"""
        
        url = f"{self.base_url}/vX/reference/financials"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'timeframe': 'quarterly',
            'limit': 8,
            'sort': 'filing_date',
            'order': 'desc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            print(f"    Financials error: {e}")
        
        return {}
    
    def get_news_raw(self, ticker: str, start: str, end: str) -> List:
        """Get raw news data"""
        
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': start,
            'published_utc.lte': end,
            'limit': 100,
            'sort': 'published_utc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                return response.json().get('results', [])
        except:
            pass
        
        return []
    
    def get_snapshot_raw(self, ticker: str) -> Dict:
        """Get raw snapshot data"""
        
        url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                return response.json().get('ticker', {})
        except:
            pass
        
        return {}
    
    def get_intraday_bars_raw(self, ticker: str, start: str, end: str) -> List:
        """Get raw intraday bars (5-minute)"""
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/5/minute/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true', 'sort': 'asc', 'limit': 50000}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                bars = data.get('results', [])
                # Add datetime for each bar
                for bar in bars:
                    bar['datetime'] = datetime.fromtimestamp(bar['t']/1000).strftime('%Y-%m-%d %H:%M')
                return bars
        except Exception as e:
            print(f"    Intraday error: {e}")
        
        return []
    
    def get_short_interest_raw(self, ticker: str) -> List:
        """Get historical short interest data - SQUEEZE FUEL"""
        
        if polygon_client:
            try:
                # Get 12 months of bi-monthly short interest reports
                short_interest = []
                for report in polygon_client.list_short_interest(ticker=ticker, limit=24):
                    short_interest.append({
                        'settlement_date': report.settlement_date,
                        'short_interest': report.short_interest,
                        'days_to_cover': report.days_to_cover,
                        'avg_daily_volume': report.avg_daily_volume
                    })
                self.api_calls += 1
                return short_interest
            except Exception as e:
                print(f"    Short interest error: {e}")
        
        return []
    
    def get_options_snapshot_raw(self, ticker: str, start: str, end: str) -> Dict:
        """Get raw options chain snapshot"""
        
        url = f"{self.base_url}/v3/snapshot/options/{ticker}"
        params = {
            'apiKey': self.api_key,
            'timestamp.gte': start,
            'timestamp.lte': end,
            'limit': 250
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"    Options error: {e}")
        
        return {}
    
    def get_previous_days_raw(self, ticker: str, catalyst_date: datetime) -> Dict:
        """Get previous day OHLCV data"""
        
        results = {}
        for days_back in [1, 2, 3, 7, 14, 30]:
            date = (catalyst_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
            url = f"{self.base_url}/v1/open-close/{ticker}/{date}"
            params = {'apiKey': self.api_key, 'adjusted': 'true'}
            
            try:
                response = requests.get(url, params=params)
                self.api_calls += 1
                
                if response.status_code == 200:
                    results[f'minus_{days_back}d'] = response.json()
            except:
                pass
        
        return results
    
    def save_progress(self, data: List, filename: str):
        """Save progress"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_final_analysis(self, fingerprints: List, output_file: str):
        """Save final raw data collection"""
        
        summary = {
            'total_analyzed': len(fingerprints),
            'successful': len([f for f in fingerprints if 'error' not in f]),
            'failed': len([f for f in fingerprints if 'error' in f]),
            'api_calls': self.api_calls
        }
        
        output = {
            'analysis_date': datetime.now().isoformat(),
            'api_tier': 'Advanced',
            'data_type': 'raw_collection',
            'summary': summary,
            'fingerprints': fingerprints
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print("\n" + "="*60)
        print("RAW DATA COLLECTION COMPLETE")
        print("="*60)
        print(f"Total analyzed: {summary['total_analyzed']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"API calls: {summary['api_calls']}")
        print(f"Saved to: {output_file}")

def main():
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    analyzer = PreCatalystFingerprint(POLYGON_API_KEY)
    
    input_file = 'CLEAN_EXPLOSIONS.json'
    output_file = 'FINGERPRINTS.json'
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file {input_file} not found!")
        return
    
    print(f"Starting raw data collection...")
    analyzer.collect_all_fingerprints(input_file, output_file)

if __name__ == "__main__":
    main()
