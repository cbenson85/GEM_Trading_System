#!/usr/bin/env python3
"""
GEM TRADING SYSTEM - TIMELINE ANALYZER (v3 - A/B Test)

This script validates our models against a holdout test set (e.g., 2023-2024 winners).
It runs two 'Golden Fingerprint' models in parallel at different intervals
before the catalyst date to see which model (and when) would have
detected the stock.

--- MODEL A: "Momentum" (Tier 2) ---
1. [SETUP] (40pts)
   - Is Ultra-Low-Float (<20M shares): +20 points
   - Is in a "Hot Sector" (Biotech/Tech/Energy): +20 points
2. [MOMENTUM] (60pts)
   - Is "Strongly Outperforming" SPY: +40 points
   - Has a "Golden Cross" (MA20 > MA50): +20 points
   
--- MODEL B: "Coiled Spring" (Fuel) ---
1. [SETUP] (40pts)
   - Is Ultra-Low-Float (<20M shares): +20 points
   - Is in a "Hot Sector" (Biotech/Tech/Energy): +20 points
2. [FUEL] (80pts)
   - Has "Squeeze Setup" (Shorts > 3 Days to Cover): +40 points
   - Has "New Activist" (13D/G filing in last 90d): +20 points
   - Has "Insider Buys" (Any Form 4 buy in last 30d): +20 points
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional, TextIO
from polygon import RESTClient
import sys
import pandas as pd
import re

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    print("❌ ERROR: POLYGON_API_KEY environment variable not set.")
    sys.exit(1)

class TimelineAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.polygon_client = RESTClient(api_key)
        self.sec_headers = {
            'User-Agent': 'GEM Trading System (gemtrading@example.com)',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.api_calls = 0
        self.pass_threshold = 80 # Stocks must score 80+ to be a "PASS"

    def log_call(self, service="polygon"):
        self.api_calls += 1
        # Polygon: 5 calls/sec. SEC: 10 calls/sec. Be safe.
        time.sleep(0.2) 

    # --- Data Collection Functions ---

    def map_sic_to_sector(self, sic_description: str) -> str:
        if not sic_description: return "UNKNOWN"
        sic = sic_description.lower()
        if any(kw in sic for kw in ['pharmaceutical', 'biological', 'medical lab', 'health', 'surgical']): return "BIOTECH/HEALTH"
        if any(kw in sic for kw in ['software', 'electronic', 'computer', 'semiconductor', 'communications']): return "TECH"
        if any(kw in sic for kw in ['oil & gas', 'mining', 'coal', 'petroleum', 'ores']): return "ENERGY/MINING"
        if 'blank checks' in sic: return "SPAC"
        if any(kw in sic for kw in ['bank', 'finance', 'investment']): return "FINANCE"
        if 'retail' in sic: return "RETAIL"
        return "OTHER"

    def get_profile_at_date(self, ticker: str, as_of_date: str) -> Dict:
        """Fetches Ticker Details, SIC code, and maps Sector."""
        try:
            url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?date={as_of_date}&apiKey={self.api_key}"
            response = requests.get(url)
            self.log_call()
            
            if response.status_code != 200:
                return {'error': f'API error {response.status_code} getting profile'}
                
            data = response.json().get('results', {})
            sic = data.get('sic_description', '')
            sector = self.map_sic_to_sector(sic)
            shares = float(data.get('share_class_shares_outstanding', 0) or data.get('weighted_shares_outstanding', 0) or 0)
            
            return {
                'cik': data.get('cik', None),
                'sector': sector,
                'market_cap': float(data.get('market_cap', 0) or 0),
                'shares_outstanding': shares
            }
        except Exception as e:
            return {'error': f"Profile error: {e}"}

    def get_momentum_at_date(self, ticker: str, as_of_date: str) -> Dict:
        """Fetches price bars and calculates all momentum metrics."""
        try:
            as_of_dt = datetime.strptime(as_of_date, '%Y-%m-%d')
            start_120d = (as_of_dt - timedelta(days=120)).strftime('%Y-%m-%d')
            
            # Get Stock Bars
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_120d}/{as_of_date}?apiKey={self.api_key}&adjusted=true&sort=asc&limit=120"
            response = requests.get(url)
            self.log_call()
            
            if response.status_code != 200:
                return {'error': 'API error (Stock Bars)'}
            
            bars = response.json().get('results', [])
            if len(bars) < 50:
                return {'error': f"Insufficient bars ({len(bars)})"}
            
            closes = [float(b['c']) for b in bars]
            is_golden_cross = float(np.mean(closes[-20:])) > float(np.mean(closes[-50:]))

            # Get SPY Bars
            spy_url = f"https://api.polygon.io/v2/aggs/ticker/SPY/range/1/day/{start_120d}/{as_of_date}?apiKey={self.api_key}&adjusted=true&sort=asc&limit=120"
            spy_response = requests.get(spy_url)
            self.log_call()
            
            if spy_response.status_code != 200:
                return {'error': 'API error (SPY Bars)'}
            
            spy_bars = spy_response.json().get('results', [])
            if len(spy_bars) < 50:
                return {'error': 'Insufficient SPY bars'}

            ticker_return = (bars[-1]['c'] - bars[0]['c']) / bars[0]['c'] if bars[0]['c'] > 0 else 0
            spy_return = (spy_bars[-1]['c'] - spy_bars[0]['c']) / spy_bars[0]['c'] if spy_bars[0]['c'] > 0 else 0
            strongly_outperforming = bool(ticker_return > spy_return + 0.1) # 10% beat

            return {
                'is_golden_cross': is_golden_cross,
                'strongly_outperforming': strongly_outperforming
            }
        except Exception as e:
            return {'error': f"Momentum error: {e}"}

    def get_fuel_at_date(self, ticker: str, cik: str, as_of_date: str) -> Dict:
        """Fetches Short Interest and SEC Filings to check for "Fuel"."""
        as_of_dt = datetime.strptime(as_of_date, '%Y-%m-%d')
        
        # 1. Short Interest (Squeeze Setup)
        is_squeeze_setup = False
        try:
            for report in self.polygon_client.list_short_interest(ticker=ticker, limit=1):
                self.log_call()
                dtc = float(report.days_to_cover) if report.days_to_cover else 0
                si = float(report.short_interest) if report.short_interest else 0
                if dtc > 3 and si > 100000:
                    is_squeeze_setup = True
                break # Only need the most recent report
        except Exception as e:
            print(f"  > Warn (Shorts): {e}")

        # 2. SEC Filings (Insiders & Activists)
        any_insider_buys_30d = False
        new_activist_filing_90d = False
        if not cik:
            return {'is_squeeze_setup': is_squeeze_setup, 'any_insider_buys_30d': False, 'new_activist_filing_90d': False, 'error': 'No CIK'}

        try:
            url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
            response = requests.get(url, headers=self.sec_headers)
            self.log_call("sec")
            
            if response.status_code == 200:
                submissions = response.json()
                filings = submissions.get('filings', {}).get('recent', {})
                form_types = filings.get('form', [])
                filing_dates = filings.get('filingDate', [])
                
                start_30d = (as_of_dt - timedelta(days=30))
                start_90d = (as_of_dt - timedelta(days=90))

                for i in range(len(form_types)):
                    filing_dt = datetime.strptime(filing_dates[i], '%Y-%m-%d')
                    if filing_dt > as_of_dt:
                        continue # Ignore filings from the future

                    # Check for insider buys
                    if form_types[i] == '4' and filing_dt >= start_30d:
                        any_insider_buys_30d = True # Simple check, parsing XML is too slow for a live scan
                    
                    # Check for new activists
                    if (form_types[i] == '13D' or form_types[i] == '13G') and filing_dt >= start_90d:
                        new_activist_filing_90d = True
            
        except Exception as e:
            print(f"  > Warn (SEC): {e}")

        return {
            'is_squeeze_setup': is_squeeze_setup,
            'any_insider_buys_30d': any_insider_buys_30d,
            'new_activist_filing_90d': new_activist_filing_90d
        }

    # --- Main Execution ---

    def run_models_at_date(self, ticker: str, as_of_date: str) -> Dict:
        """
        Runs the full model checks for a single ticker at a single point in time.
        Returns a dict with both scores and reasons.
        """
        score_m, score_f = 0, 0 # Momentum Score, Fuel Score
        reason_m, reason_f = [], []

        # --- 1. [SETUP] Get Profile & Check Sector/Float/MC ---
        profile = self.get_profile_at_date(ticker, as_of_date)
        if 'error' in profile:
            return {'score_m': 0, 'score_f': 0, 'reason': profile['error']}
        
        is_hot_sector = profile['sector'] in ["BIOTECH/HEALTH", "TECH", "ENERGY/MINING"]
        is_micro_cap = bool(0 < profile['market_cap'] < 300_000_000)
        is_ultra_low_float = bool(0 < profile['shares_outstanding'] < 20_000_000)
        
        # Hard filters. If these fail, both models fail.
        if not is_micro_cap or not is_ultra_low_float:
            return {'score_m': 0, 'score_f': 0, 'reason': f"Failed Setup (ULF: {is_ultra_low_float}, MC: {is_micro_cap})"}
        
        if not is_hot_sector:
             return {'score_m': 0, 'score_f': 0, 'reason': f"Wrong Sector ({profile['sector']})"}

        # Passed Setup: Add base points to *both* scores
        score_m += 40; reason_m.append("Setup(40)")
        score_f += 40; reason_f.append("Setup(40)")

        # --- 2. [MOMENTUM] Get Momentum Data ---
        mom_data = self.get_momentum_at_date(ticker, as_of_date)
        if 'error' not in mom_data:
            if mom_data['strongly_outperforming']:
                score_m += 40
                reason_m.append("RS(+40)")
            if mom_data['is_golden_cross']:
                score_m += 20
                reason_m.append("GC(+20)")
        else:
            reason_m.append(mom_data['error'])

        # --- 3. [FUEL] Get Fuel Data ---
        fuel_data = self.get_fuel_at_date(ticker, profile.get('cik'), as_of_date)
        if 'error' not in fuel_data:
            if fuel_data['is_squeeze_setup']:
                score_f += 40
                reason_f.append("Squeeze(+40)")
            if fuel_data['new_activist_filing_90d']:
                score_f += 20
                reason_f.append("Activist(+20)")
            if fuel_data['any_insider_buys_30d']:
                score_f += 20
                reason_f.append("Insider(+20)")
        else:
            reason_f.append(fuel_data['error'])

        return {
            'score_m': score_m,
            'score_f': score_f,
            'reason': f"M: [{', '.join(reason_m)}] | F: [{', '.join(reason_f)}]"
        }

    def run_timeline_analysis(self, input_file: str, output_file: str):
        """
        Main logic loop. Loads test file and runs the models at each
        T-minus interval for each ticker.
        """
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            discoveries = data.get('discoveries', [])
            print(f"Loaded {len(discoveries)} tickers from {input_file} for A/B timeline analysis.")
        except Exception as e:
            print(f"❌ Failed to load test file: {e}")
            return

        intervals_to_test = [-90, -60, -30, -15, -7, -1] # T-minus days
        results_log = []

        with open(output_file, 'w') as f:
            f.write("="*90 + "\n")
            f.write("GEM TRADING SYSTEM - TIMELINE A/B TEST REPORT (v3 - Momentum vs. Fuel)\n")
            f.write(f"Test Set: {input_file}\n")
            f.write(f"Run at: {datetime.now().isoformat()}\n")
            f.write(f"Model M (Momentum): ULF+Sector (40) + StrongRS (40) + GoldenCross (20)\n")
            f.write(f"Model F (Fuel):     ULF+Sector (40) + Squeeze (40) + Activist (20) + Insider (20)\n")
            f.write(f"Pass Threshold: {self.pass_threshold} points\n")
            f.write("="*90 + "\n\n")

            header = "Ticker | Gain % | T-90 (M/F) | T-60 (M/F) | T-30 (M/F) | T-15 (M/F) | T-7 (M/F) | T-1 (M/F)\n"
            f.write(header)
            f.write(f"{'-'*len(header)}\n")
            print(header, end="")

            for i, explosion in enumerate(discoveries):
                ticker = explosion['ticker']
                gain_pct = float(explosion['gain_pct'])
                catalyst_dt = datetime.strptime(explosion['catalyst_date'], '%Y-%m-%d')
                
                print(f"Analyzing {ticker} (Catalyst: {explosion['catalyst_date']})...")
                
                result_row = {
                    'ticker': ticker,
                    'gain_pct': f"{gain_pct:,.0f}%",
                }
                
                console_row = [f"{ticker:<6} | {gain_pct:>7,.0f}% |"]

                for days in intervals_to_test:
                    scan_date = (catalyst_dt + timedelta(days=days)).strftime('%Y-%m-%d')
                    
                    try:
                        scan_result = self.run_models_at_date(ticker, scan_date)
                        result_row[f'T{days}_M'] = scan_result['score_m']
                        result_row[f'T{days}_F'] = scan_result['score_f']
                        console_row.append(f"{scan_result['score_m']:>3}/{scan_result['score_f']:<3} |")
                    except Exception as e:
                        print(f"  Error scanning {ticker} at {scan_date}: {e}")
                        result_row[f'T{days}_M'] = "ERR"
                        result_row[f'T{days}_F'] = "ERR"
                        console_row.append(" ERR/ERR  |")
                
                results_log.append(result_row)
                
                # Write to file
                f.write(f"{result_row['ticker']:<6} | "
                        f"{result_row['gain_pct']:>7} | "
                        f" {str(result_row['T-90_M']):>3}/{str(result_row['T-90_F']):<3} | "
                        f" {str(result_row['T-60_M']):>3}/{str(result_row['T-60_F']):<3} | "
                        f" {str(result_row['T-30_M']):>3}/{str(result_row['T-30_F']):<3} | "
                        f" {str(result_row['T-15_M']):>3}/{str(result_row['T-15_F']):<3} | "
                        f" {str(result_row['T-7_M']):>3}/{str(result_row['T-7_F']):<3} | "
                        f" {str(result_row['T-1_M']):>3}/{str(result_row['T-1_F']):<3}\n")
                
                print(" ".join(console_row))

            # --- Final Summary ---
            df = pd.DataFrame(results_log)
            total_stocks = len(df)
            
            f.write("\n" + "="*90 + "\n")
            f.write("TIMELINE ANALYSIS SUMMARY\n")
            f.write("="*90 + "\n")
            f.write(f"Total Stocks Tested: {total_stocks}\n")
            f.write(f"Pass Threshold: {self.pass_threshold} points\n\n")
            
            f.write("--- Detection Rate (Model M: Momentum) ---\n")
            for days in intervals_to_test:
                col_name = f'T{days}_M'
                numeric_col = pd.to_numeric(df[col_name], errors='coerce')
                pass_count = (numeric_col >= self.pass_threshold).sum()
                rate = (pass_count / total_stocks) * 100 if total_stocks > 0 else 0
                f.write(f"  - At T{days} days: {pass_count}/{total_stocks} ({rate:.1f}%)\n")
                
            f.write("\n--- Detection Rate (Model F: Fuel) ---\n")
            for days in intervals_to_test:
                col_name = f'T{days}_F'
                numeric_col = pd.to_numeric(df[col_name], errors='coerce')
                pass_count = (numeric_col >= self.pass_threshold).sum()
                rate = (pass_count / total_stocks) * 100 if total_stocks > 0 else 0
                f.write(f"  - At T{days} days: {pass_count}/{total_stocks} ({rate:.1f}%)\n")

            print("\n" + "="*80)
            print("Timeline Analysis Complete.")
            print(f"Total API Calls: {self.api_calls}")
            print(f"Report saved to {output_file}")
            print("="*80)

def main():
    if len(sys.argv) < 3:
        print("Usage: python timeline_analyzer.py <input_file.json> <output_file.txt>")
        print("Example: python timeline_analyzer.py DISCARD_EXPLOSIONS.json timeline_report.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    analyzer = TimelineAnalyzer(POLYGON_API_KEY)
    analyzer.run_timeline_analysis(input_file, output_file)

if __name__ == "__main__":
    main()
