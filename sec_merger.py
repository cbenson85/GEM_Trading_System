#!/usr/bin/env python3
"""
SEC Data Merger for GEM Trading System (v4 - New Signals)
Enriches Polygon raw data with actual SEC filing content.
- Parses Form 4 XML for Insider BUYS ('P' code)
- Parses 8-K HTML/Text for Catalyst Keywords
- ADDS: any_insider_buys_30d
- ADDS: new_activist_filing_90d
"""

import json
import time
import requests
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

class SECDataMerger:
    def __init__(self):
        self.submissions_url = "https://data.sec.gov/submissions/CIK{cik}.json"
        self.archive_url = "https://data.sec.gov/Archives/edgar/data"
        self.headers = {
            'User-Agent': 'GEM Trading System (gemtrading@example.com)',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.api_calls = 0

    def rate_limit_sleep(self):
        """Respects SEC 10 calls/sec limit"""
        self.api_calls += 1
        time.sleep(0.12) # 120ms is a safe buffer

    def merge_sec_data(self, polygon_file: str, output_file: str):
        print("="*60)
        print("SEC DATA ENRICHMENT (v4 - New Signals)")
        print("Parsing 8-K, Form 4, 13D/G...")
        print("="*60)

        if not os.path.exists(polygon_file):
            print(f"❌ ERROR: {polygon_file} not found! Run the Polygon collector first.")
            return

        with open(polygon_file, 'r') as f:
            polygon_data = json.load(f)
        
        fingerprints = polygon_data.get('fingerprints', [])
        print(f"Found {len(fingerprints)} stocks to enrich with SEC data")
        
        enriched_fingerprints = []

        for i, fingerprint in enumerate(fingerprints):
            ticker = fingerprint.get('ticker')
            if 'error' in fingerprint:
                enriched_fingerprints.append(fingerprint)
                continue
            
            print(f"\n[{i+1}/{len(fingerprints)}] Enriching {ticker}...")
            
            cik = fingerprint.get('1_profile', {}).get('cik', '')
            
            if not cik:
                print("  No CIK found in Polygon data, skipping SEC.")
                fingerprint['sec_data'] = {'error': 'No CIK available'}
                enriched_fingerprints.append(fingerprint)
                continue
            
            cik_padded = cik.zfill(10)
            catalyst_date = fingerprint.get('catalyst_date')
            catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
            
            submissions = self.get_submissions_json(cik_padded)
            if not submissions:
                print("  Could not fetch submissions JSON, skipping SEC.")
                fingerprint['sec_data'] = {'error': 'Could not fetch submissions from SEC'}
                enriched_fingerprints.append(fingerprint)
                continue

            sec_data = {}
            
            print("  Getting 8-K filings and text...")
            sec_data['form_8k'] = self.get_8k_filings(cik_padded, submissions, catalyst_dt)
            
            print("  Getting Insider BUYS (Form 4)...")
            sec_data['insider_trades'] = self.get_insider_transactions(cik_padded, submissions, catalyst_dt)
            
            print("  Getting Institutional indicators (13D/G)...")
            sec_data['institutional'] = self.get_institutional_data(submissions, catalyst_dt)
            
            fingerprint['sec_data'] = sec_data
            enriched_fingerprints.append(fingerprint)
            
            if (i + 1) % 10 == 0:
                self.save_progress(enriched_fingerprints, 'sec_merge_progress.json')
                print(f"  Progress saved: {i+1} complete")
        
        self.save_final(polygon_data, enriched_fingerprints, output_file)

    def get_submissions_json(self, cik: str) -> Optional[Dict]:
        """Fetches the complete submissions JSON for a single CIK."""
        url = self.submissions_url.format(cik=cik)
        try:
            response = requests.get(url, headers=self.headers)
            self.rate_limit_sleep()
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"    Submissions JSON error: {e}")
        return None

    def get_8k_filings(self, cik: str, submissions: Dict, catalyst_dt: datetime, days_before: int = 30) -> Dict:
        start_date = catalyst_dt - timedelta(days=days_before)
        end_date = catalyst_dt + timedelta(days=7)
        
        filings = []
        catalyst_keywords_found = []
        
        try:
            recent = submissions.get('filings', {}).get('recent', {})
            form_types = recent.get('form', [])
            filing_dates = recent.get('filingDate', [])
            accession_numbers = recent.get('accessionNumber', [])
            primary_documents = recent.get('primaryDocument', [])
            
            for i in range(len(form_types)):
                if '8-K' in form_types[i]:
                    filing_date = filing_dates[i]
                    filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
                    
                    if start_date <= filing_dt <= end_date:
                        accession_num = accession_numbers[i].replace('-', '')
                        doc_name = primary_documents[i]
                        filing_url = f"{self.archive_url}/{cik}/{accession_num}/{doc_name}"
                        
                        filing_text = self.get_filing_text(filing_url)
                        catalyst_type, keywords = self.analyze_8k_text(filing_text)
                        
                        filings.append({
                            'filing_date': filing_date,
                            'days_from_catalyst': (filing_dt - catalyst_dt).days,
                            'detected_catalyst_type': catalyst_type,
                            'keywords_found': keywords,
                        })
                        if catalyst_type != 'other':
                            catalyst_keywords_found.extend(keywords)
                            
        except Exception as e:
            print(f"    8-K error: {e}")

        return {
            'count_in_window': len(filings),
            'has_catalyst_8k': any(abs(f['days_from_catalyst']) <= 3 for f in filings),
            'all_keywords_found': list(set(catalyst_keywords_found)),
            'filings': filings, # Store full filing list
        }

    def get_filing_text(self, url: str) -> str:
        """Downloads the raw text of a filing."""
        try:
            response = requests.get(url, headers=self.headers)
            self.rate_limit_sleep()
            if response.status_code == 200:
                text = response.text
                text = re.sub(r'<[^>]+>', ' ', text) # Remove HTML
                text = re.sub(r'\s+', ' ', text) # Normalize whitespace
                return text.lower()
        except Exception as e:
            print(f"      Filing text download error: {e}")
        return ""

    def analyze_8k_text(self, text: str) -> (str, List[str]):
        """Analyze 8-K text for catalyst keywords"""
        catalyst_patterns = {
            'fda': ['fda', 'food and drug administration', 'pdufa', 'approval', 'phase 3', 'clinical trial', 'breakthrough therapy'],
            'merger': ['merger', 'acquisition', 'acquire', 'definitive agreement', 'buyout'],
            'earnings': ['earnings', 'quarterly results', 'financial results', 'exceeded expectations'],
            'contract': ['contract', 'agreement', 'partnership', 'collaboration', 'licensing'],
            'offering': ['offering', 'public offering', 'registered direct offering', 's-3', 'atm'],
            'legal': ['lawsuit', 'litigation', 'settlement', 'verdict'],
            'bankruptcy': ['bankruptcy', 'chapter 11', 'restructuring'],
        }
        
        found_keywords = []
        for catalyst_type, keywords in catalyst_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    found_keywords.append(keyword)
            if found_keywords:
                return catalyst_type, list(set(found_keywords))
                
        return 'other', []

    def get_insider_transactions(self, cik: str, submissions: Dict, catalyst_dt: datetime, days_before: int = 120) -> Dict:
        start_date = catalyst_dt - timedelta(days=days_before)
        
        insider_buys = []
        insider_sells = []
        
        try:
            recent = submissions.get('filings', {}).get('recent', {})
            form_types = recent.get('form', [])
            filing_dates = recent.get('filingDate', [])
            accession_numbers = recent.get('accessionNumber', [])
            primary_documents = recent.get('primaryDocument', [])
            
            for i in range(len(form_types)):
                if form_types[i] == '4':
                    filing_date = filing_dates[i]
                    filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
                    
                    if start_date <= filing_dt <= catalyst_dt:
                        accession_num = accession_numbers[i].replace('-', '')
                        doc_name = primary_documents[i]
                        xml_url = f"{self.archive_url}/{cik}/{accession_num}/{doc_name}"
                        
                        buys, sells = self.parse_form_4_xml(xml_url)
                        
                        if buys > 0:
                            insider_buys.append({'date': filing_date, 'shares': buys})
                        if sells > 0:
                            insider_sells.append({'date': filing_date, 'shares': sells})
                            
        except Exception as e:
            print(f"    Insider transaction error: {e}")

        recent_buys_30d_count = sum(1 for f in insider_buys if (catalyst_dt - datetime.strptime(f['date'], '%Y-%m-%d')).days <= 30)

        return {
            'total_buy_transactions': len(insider_buys),
            'total_sell_transactions': len(insider_sells),
            'buy_share_total': sum(b['shares'] for b in insider_buys),
            'sell_share_total': sum(s['shares'] for s in insider_sells),
            'net_insider_activity': 'BUY' if len(insider_buys) > len(insider_sells) else 'SELL' if len(insider_sells) > len(insider_buys) else 'NEUTRAL',
            'recent_buys_30d_count': recent_buys_30d_count, # <-- RENAMED for clarity
            'any_insider_buys_30d': bool(recent_buys_30d_count > 0), # <-- NEW
            'insider_buying_surge': bool(recent_buys_30d_count >= 3 and len(insider_sells) == 0) # Made more specific
        }

    def parse_form_4_xml(self, xml_url: str) -> (int, int):
        """Downloads and parses a Form 4 XML file to count *only* real buys and sells."""
        text = self.get_filing_text(xml_url) 
        if not text:
            return 0, 0
            
        total_buys = 0
        total_sells = 0
        
        try:
            transactions = re.findall(r'<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>', text, re.IGNORECASE | re.DOTALL)
            
            for tx in transactions:
                shares_match = re.search(r'<transactionShares>.*?<value>([\d\.]+)</value>.*?</transactionShares>', tx, re.IGNORECASE | re.DOTALL)
                code_match = re.search(r'<transactionAcquiredDisposedCode>.*?<value>([AD])</value>.*?</transactionAcquiredDisposedCode>', tx, re.IGNORECASE | re.DOTALL)
                tx_code_match = re.search(r'<transactionCode>([PS])</transactionCode>', tx, re.IGNORECASE)

                if shares_match and code_match and tx_code_match:
                    shares = float(shares_match.group(1))
                    acq_disp_code = code_match.group(1).upper()
                    tx_code = tx_code_match.group(1).upper()
                    
                    if tx_code == 'P' and acq_disp_code == 'A':
                        total_buys += shares
                    elif tx_code == 'S' and acq_disp_code == 'D':
                        total_sells += shares
            
            return int(total_buys), int(total_sells)
            
        except Exception as e:
            print(f"      XML Parse Error: {e}")
            return 0, 0

    def get_institutional_data(self, submissions: Dict, catalyst_dt: datetime) -> Dict:
        """
        Gets 13F/G/D filing counts and checks for NEW activist filings.
        --- UPDATED (v4) ---
        """
        thirteen_f_count = 0
        thirteen_d_g_count = 0
        new_activist_filing_90d = False
        
        try:
            filings = submissions.get('filings', {}).get('recent', {})
            form_types = filings.get('form', [])
            filing_dates = filings.get('filingDate', [])
            
            start_date_90d = catalyst_dt - timedelta(days=90)
            
            for i in range(len(form_types)):
                form_type = form_types[i]
                
                if '13F' in form_type:
                    thirteen_f_count += 1
                
                if '13D' in form_type or '13G' in form_type:
                    thirteen_d_g_count += 1
                    filing_dt = datetime.strptime(filing_dates[i], '%Y-%m-%d')
                    
                    if start_date_90d <= filing_dt <= catalyst_dt:
                        new_activist_filing_90d = True # <-- NEW SIGNAL
            
            return {
                'has_institutional_filings_13f': thirteen_f_count > 0,
                'has_activist_filings_13dg': thirteen_d_g_count > 0,
                'institutional_filing_count': thirteen_f_count,
                'activist_filing_count': thirteen_d_g_count,
                'new_activist_filing_90d': new_activist_filing_90d # <-- NEW
            }
        except Exception as e:
            print(f"    Institutional error: {e}")
            
        return {
            'has_institutional_filings_13f': False,
            'has_activist_filings_13dg': False,
            'institutional_filing_count': 0,
            'activist_filing_count': 0,
            'new_activist_filing_90d': False
        }

    def save_progress(self, data: List, filename: str):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_final(self, original_data: Dict, enriched_fingerprints: List, output_file: str):
        summary = original_data.get('polygon_summary', original_data.get('summary', {}))
        summary['sec_enrichment_date'] = datetime.now().isoformat()
        summary['sec_api_calls'] = self.api_calls
        
        sec_success = sum(1 for f in enriched_fingerprints if 'sec_data' in f and 'error' not in f.get('sec_data', {}))
        summary['sec_data_added'] = sec_success
        
        output = {
            'metadata': {
                'type': 'master_fingerprints',
                'sources': ['polygon_advanced_tier', 'sec_edgar_v2_parsed'],
                'ready_for_analysis': True
            },
            'polygon_summary': summary,
            'fingerprints': enriched_fingerprints
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
            
        print("\n" + "="*60)
        print("SEC ENRICHMENT COMPLETE (v4)")
        print("="*60)
        print(f"SEC data added to: {sec_success} stocks")
        print(f"SEC API calls: {self.api_calls}")
        print(f"\n✅ Master file saved: {output_file}")
        print("\nReady for correlation analysis!")

def main():
    merger = SECDataMerger()
    polygon_file = 'FINGERPRINTS.json' 
    output_file = 'MASTER_FINGERPRINTS.json' 
    
    if not os.path.exists(polygon_file):
        print(f"❌ ERROR: {polygon_file} not found!")
        print("Run fingerprint_analyzer.py first to generate it.")
        return
    
    print("Starting SEC data enrichment (v4)...")
    print(f"Input: {polygon_file}")
    print(f"Output: {output_file}")
    
    merger.merge_sec_data(polygon_file, output_file)

if __name__ == "__main__":
    main()
