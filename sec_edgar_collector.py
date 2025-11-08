"""
SEC Edgar Data Collector - REAL DATA
Fetches actual SEC filings to identify catalysts and insider activity
"""

import requests
import json
from datetime import datetime, timedelta
import time
import re

class SECEdgarCollector:
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.headers = {
            'User-Agent': 'GEM Trading System (gemtrading@example.com)',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
    
    def get_company_cik(self, ticker):
        """Get CIK number from ticker symbol"""
        # SEC provides a ticker to CIK mapping
        url = "https://www.sec.gov/files/company_tickers.json"
        
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = response.json()
            
            # Search for ticker
            for item in data.values():
                if item['ticker'] == ticker.upper():
                    # CIK needs to be 10 digits with leading zeros
                    return str(item['cik_str']).zfill(10)
        except:
            pass
        return None
    
    def get_recent_8k_filings(self, ticker, days_back=30):
        """Get recent 8-K filings (material events)"""
        cik = self.get_company_cik(ticker)
        if not cik:
            return []
        
        # Get company submissions
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            time.sleep(0.1)  # SEC rate limiting
            
            if response.status_code == 200:
                data = response.json()
                filings = []
                
                # Look for recent 8-K filings
                recent_filings = data.get('filings', {}).get('recent', {})
                
                if recent_filings:
                    forms = recent_filings.get('form', [])
                    dates = recent_filings.get('filingDate', [])
                    primary_docs = recent_filings.get('primaryDocument', [])
                    
                    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                    
                    for i in range(len(forms)):
                        if forms[i] == '8-K' and dates[i] >= cutoff_date:
                            filings.append({
                                'form': '8-K',
                                'date': dates[i],
                                'document': primary_docs[i] if i < len(primary_docs) else None
                            })
                
                return filings
        except Exception as e:
            print(f"Error fetching SEC data for {ticker}: {e}")
        
        return []
    
    def get_insider_transactions(self, ticker, days_back=90):
        """Get Form 4 insider transactions"""
        cik = self.get_company_cik(ticker)
        if not cik:
            return []
        
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            time.sleep(0.1)
            
            if response.status_code == 200:
                data = response.json()
                transactions = []
                
                recent_filings = data.get('filings', {}).get('recent', {})
                
                if recent_filings:
                    forms = recent_filings.get('form', [])
                    dates = recent_filings.get('filingDate', [])
                    
                    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                    
                    form4_count = 0
                    for i in range(len(forms)):
                        if forms[i] in ['3', '4', '5'] and dates[i] >= cutoff_date:
                            form4_count += 1
                            transactions.append({
                                'form': forms[i],
                                'date': dates[i]
                            })
                
                return {
                    'total_transactions': form4_count,
                    'transactions': transactions[:10]  # Return first 10
                }
        except Exception as e:
            print(f"Error fetching insider data for {ticker}: {e}")
        
        return {'total_transactions': 0, 'transactions': []}
    
    def analyze_8k_for_catalyst(self, filing_text):
        """Analyze 8-K text for catalyst keywords"""
        catalyst_patterns = {
            'fda': ['fda', 'approval', 'clearance', 'crl', 'complete response'],
            'clinical': ['clinical', 'trial', 'phase', 'endpoint', 'results'],
            'merger': ['merger', 'acquisition', 'definitive agreement', 'buyout'],
            'offering': ['offering', 'registration', 'shelf', 's-3', 'atm'],
            'bankruptcy': ['bankruptcy', 'chapter 11', 'restructuring'],
            'legal': ['lawsuit', 'litigation', 'court', 'settlement', 'verdict']
        }
        
        text_lower = filing_text.lower() if filing_text else ""
        
        for catalyst_type, keywords in catalyst_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return catalyst_type
        
        return 'other'

def collect_sec_data(stock):
    """Main function to collect SEC data for a stock"""
    ticker = stock['ticker']
    explosion_date = stock.get('catalyst_date') or stock['entry_date']
    
    collector = SECEdgarCollector()
    
    print(f"  Collecting SEC data for {ticker}...")
    
    # Get 8-K filings around explosion date
    eight_k_filings = collector.get_recent_8k_filings(ticker, days_back=30)
    
    # Get insider transactions
    insider_data = collector.get_insider_transactions(ticker, days_back=90)
    
    # Determine if there was an 8-K catalyst
    catalyst_type = 'unknown'
    catalyst_date = None
    
    if eight_k_filings:
        # Check if 8-K was filed near explosion
        explosion_dt = datetime.fromisoformat(explosion_date)
        for filing in eight_k_filings:
            filing_dt = datetime.fromisoformat(filing['date'])
            days_diff = abs((explosion_dt - filing_dt).days)
            
            if days_diff <= 7:  # Within a week of explosion
                catalyst_type = '8k_filing'
                catalyst_date = filing['date']
                break
    
    return {
        'ticker': ticker,
        'eight_k_count': len(eight_k_filings),
        'eight_k_filings': eight_k_filings[:5],  # First 5
        'insider_transactions': insider_data['total_transactions'],
        'insider_activity': 'high' if insider_data['total_transactions'] >= 5 else 
                           'medium' if insider_data['total_transactions'] >= 2 else 
                           'low' if insider_data['total_transactions'] >= 1 else 'none',
        'catalyst_type': catalyst_type,
        'catalyst_date': catalyst_date,
        'data_source': 'SEC_Edgar'
    }

if __name__ == "__main__":
    # Test with a sample stock
    test_stock = {
        'ticker': 'AAPL',
        'entry_date': '2024-01-01',
        'catalyst_date': None
    }
    
    result = collect_sec_data(test_stock)
    print(json.dumps(result, indent=2))
