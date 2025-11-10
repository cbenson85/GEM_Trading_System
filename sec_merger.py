#!/usr/bin/env python3
"""
SEC Data Merger for GEM Trading System
Enriches Polygon raw data with SEC filing information
"""

import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SECDataMerger:
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.headers = {
            'User-Agent': 'GEM Trading System (gemtrading@example.com)'
        }
        self.api_calls = 0
        
    def merge_sec_data(self, polygon_file: str, output_file: str):
        """Main merge function"""
        
        print("="*60)
        print("SEC DATA ENRICHMENT")
        print("="*60)
        
        # Load Polygon data
        with open(polygon_file, 'r') as f:
            polygon_data = json.load(f)
        
        fingerprints = polygon_data.get('fingerprints', [])
        print(f"Found {len(fingerprints)} stocks to enrich with SEC data")
        
        enriched_fingerprints = []
        
        for i, fingerprint in enumerate(fingerprints):
            ticker = fingerprint.get('ticker')
            
            # Skip if error
            if 'error' in fingerprint:
                enriched_fingerprints.append(fingerprint)
                continue
            
            print(f"\n[{i+1}/{len(fingerprints)}] Enriching {ticker}...")
            
            # Get CIK from ticker details
            cik = fingerprint.get('ticker_details', {}).get('cik', '')
            
            if not cik:
                print(f"  No CIK found, skipping SEC data")
                fingerprint['sec_data'] = {'error': 'No CIK available'}
                enriched_fingerprints.append(fingerprint)
                continue
            
            # Pad CIK to 10 digits
            cik_padded = cik.zfill(10)
            catalyst_date = fingerprint.get('catalyst_date')
            
            # Collect SEC data
            sec_data = {}
            
            # 1. Get recent 8-Ks
            print(f"  Getting 8-K filings...")
            sec_data['form_8k'] = self.get_8k_filings(cik_padded, catalyst_date)
            
            # 2. Get insider transactions (Form 4)
            print(f"  Getting insider transactions...")
            sec_data['insider_trades'] = self.get_insider_transactions(cik_padded, catalyst_date)
            
            # 3. Get institutional holdings (13F)
            print(f"  Getting institutional data...")
            sec_data['institutional'] = self.get_institutional_data(cik_padded)
            
            # Add to fingerprint
            fingerprint['sec_data'] = sec_data
            enriched_fingerprints.append(fingerprint)
            
            # Save progress every 10 stocks
            if (i + 1) % 10 == 0:
                self.save_progress(enriched_fingerprints, 'sec_merge_progress.json')
                print(f"  Progress saved: {i+1} complete")
            
            # Rate limit: 10 requests per second
            time.sleep(0.1)
        
        # Save final merged data
        self.save_final(polygon_data, enriched_fingerprints, output_file)
    
    def get_8k_filings(self, cik: str, catalyst_date: str, days_before: int = 30) -> Dict:
        """Get 8-K filings around catalyst"""
        
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        start_date = catalyst_dt - timedelta(days=days_before)
        end_date = catalyst_dt + timedelta(days=7)
        
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                recent_filings = data.get('filings', {}).get('recent', {})
                
                # Extract 8-K filings
                form_types = recent_filings.get('form', [])
                filing_dates = recent_filings.get('filingDate', [])
                accession_numbers = recent_filings.get('accessionNumber', [])
                primary_documents = recent_filings.get('primaryDocument', [])
                
                eight_k_filings = []
                
                for i in range(len(form_types)):
                    if '8-K' in form_types[i]:
                        filing_date = filing_dates[i] if i < len(filing_dates) else ''
                        
                        # Check if within date range
                        if filing_date:
                            filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
                            if start_date <= filing_dt <= end_date:
                                eight_k_filings.append({
                                    'filing_date': filing_date,
                                    'form_type': form_types[i],
                                    'accession_number': accession_numbers[i] if i < len(accession_numbers) else '',
                                    'document': primary_documents[i] if i < len(primary_documents) else '',
                                    'days_from_catalyst': (filing_dt - catalyst_dt).days
                                })
                
                return {
                    'count': len(eight_k_filings),
                    'filings': eight_k_filings[:5],  # Limit to 5 most relevant
                    'has_catalyst_8k': any(abs(f['days_from_catalyst']) <= 3 for f in eight_k_filings)
                }
                
        except Exception as e:
            print(f"    8-K error: {e}")
        
        return {'count': 0, 'filings': []}
    
    def get_insider_transactions(self, cik: str, catalyst_date: str, days_before: int = 90) -> Dict:
        """Get insider transactions (Form 4)"""
        
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        start_date = catalyst_dt - timedelta(days=days_before)
        
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                recent_filings = data.get('filings', {}).get('recent', {})
                
                form_types = recent_filings.get('form', [])
                filing_dates = recent_filings.get('filingDate', [])
                
                insider_filings = []
                
                for i in range(len(form_types)):
                    if form_types[i] in ['4', '3', '5']:
                        filing_date = filing_dates[i] if i < len(filing_dates) else ''
                        
                        if filing_date:
                            filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
                            if start_date <= filing_dt <= catalyst_dt:
                                insider_filings.append({
                                    'filing_date': filing_date,
                                    'form_type': form_types[i],
                                    'days_before_catalyst': (catalyst_dt - filing_dt).days
                                })
                
                # Analyze patterns
                buys_30d = sum(1 for f in insider_filings if f['days_before_catalyst'] <= 30)
                buys_90d = len(insider_filings)
                
                return {
                    'total_transactions': buys_90d,
                    'transactions_30d': buys_30d,
                    'recent_filings': insider_filings[:10],
                    'insider_buying_surge': buys_30d >= 3
                }
                
        except Exception as e:
            print(f"    Insider error: {e}")
        
        return {'total_transactions': 0}
    
    def get_institutional_data(self, cik: str) -> Dict:
        """Get institutional ownership indicators"""
        
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                recent_filings = data.get('filings', {}).get('recent', {})
                
                form_types = recent_filings.get('form', [])
                
                # Count institutional interest
                thirteen_f_count = sum(1 for f in form_types if '13' in f)
                schedule_13d_count = sum(1 for f in form_types if '13D' in f or '13G' in f)
                
                return {
                    'has_13f_activity': thirteen_f_count > 0,
                    'has_activist_interest': schedule_13d_count > 0,
                    'institutional_filings': thirteen_f_count,
                    'activist_filings': schedule_13d_count
                }
                
        except Exception as e:
            print(f"    Institutional error: {e}")
        
        return {'has_13f_activity': False}
    
    def save_progress(self, data: List, filename: str):
        """Save intermediate progress"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_final(self, original_data: Dict, enriched_fingerprints: List, output_file: str):
        """Save final merged dataset"""
        
        # Update summary
        summary = original_data.get('summary', {})
        summary['sec_enrichment_date'] = datetime.now().isoformat()
        summary['sec_api_calls'] = self.api_calls
        
        # Count SEC data success
        sec_success = sum(1 for f in enriched_fingerprints 
                         if 'sec_data' in f and 'error' not in f.get('sec_data', {}))
        summary['sec_data_added'] = sec_success
        
        output = {
            'metadata': {
                'type': 'master_fingerprints',
                'sources': ['polygon_advanced_tier', 'sec_edgar'],
                'ready_for_analysis': True
            },
            'summary': summary,
            'fingerprints': enriched_fingerprints
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print("\n" + "="*60)
        print("SEC ENRICHMENT COMPLETE")
        print("="*60)
        print(f"SEC data added: {sec_success} stocks")
        print(f"SEC API calls: {self.api_calls}")
        print(f"\nMaster file saved: {output_file}")
        print("\nReady for correlation analysis!")

def main():
    merger = SECDataMerger()
    
    polygon_file = 'POLYGON_FINGERPRINTS.json'
    output_file = 'MASTER_FINGERPRINTS.json'
    
    import os
    if not os.path.exists(polygon_file):
        print(f"ERROR: {polygon_file} not found!")
        print("Run fingerprint_collector_raw.py first")
        return
    
    print("Starting SEC data enrichment...")
    print("~3 SEC API calls per ticker")
    print("Estimated time: 10-15 minutes")
    
    merger.merge_sec_data(polygon_file, output_file)

if __name__ == "__main__":
    main()
