#!/usr/bin/env python3
"""
GEM TRADING SYSTEM - TIMELINE ANALYZER (v2 - Weighted Score)

This is the final validation script.

It loads a list of known winners (e.g., our 2023-2024 test set)
and runs our "Golden Fingerprint" (Tier 2) model at different
intervals *before* the catalyst date.

This version calculates a weighted "GEM Score" (0-100) instead
of a simple PASS/FAIL, allowing us to see *how* a signal develops.

"GEM Score" (Tier 2 Model):
1. [SETUP]
   - Is Ultra-Low-Float (<20M shares): +20 points
   - Is in a "Hot Sector" (Biotech/Tech/Energy): +20 points
2. [MOMENTUM]
   - Is "Strongly Outperforming" SPY: +40 points
   - Has a "Golden Cross" (MA20 > MA50): +20 points
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

# Load API key from environment
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    print("❌ ERROR: POLYGON_API_KEY environment variable not set.")
    sys.exit(1)

class TimelineAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.polygon_client = RESTClient(api_key)
        self.api_calls = 0
        self.scan_results = []
        self.pass_threshold = 80 # <-- Stocks must score 80+ to be a "PASS"

    def log_call(self):
        self.api_calls += 1
        # 10 calls/sec limit for SEC, 5 calls/sec for Polygon (w/ Advanced)
        # 0.2s is a safe buffer for all endpoints
        time.sleep(0.2) 

    def map_sic_to_sector(self, sic_description: str) -> str:
        """Maps SIC description to a broad sector category."""
        if not sic_description:
            return "UNKNOWN"
        sic = sic_description.lower()
        if any(kw in sic for kw in ['pharmaceutical', 'biological', 'medical lab', 'health', 'surgical']):
            return "BIOTECH/HEALTH"
        if any(kw in sic for kw in ['software', 'electronic', 'computer', 'semiconductor', 'communications']):
            return "TECH"
        if any(kw in sic for kw in ['oil & gas', 'mining', 'coal', 'petroleum', 'ores']):
            return "ENERGY/MINING"
        if 'blank checks' in sic:
            return "SPAC"
        if any(kw in sic for kw in ['bank', 'finance', 'investment']):
            return "FINANCE"
        if 'retail' in sic:
            return "RETAIL"
        return "OTHER"

    def get_ticker_info_at_date(self, ticker: str, as_of_date: str) -> Optional[Dict]:
        """
        Fetches Ticker Details and maps SIC code.
        NOTE: This must be called *at the specific date* to avoid lookahead bias.
        """
        try:
            url = f"{self.base_url}/v3/reference/tickers/{ticker}"
            params = {'apiKey': self.api_key, 'date': as_of_date}
            response = requests.get(url, params=params)
            self.log_call()
            
            if response.status_code != 200:
                return {'error': f'API error {response.status_code} getting profile'}
                
            data = response.json().get('results', {})
            sic = data.get('sic_description', '')
            sector = self.map_sic_to_sector(sic)
            
            return {
                'name': data.get('name', ''),
                'sic_description': sic,
                'sector': sector,
                'market_cap': float(data.get('market_cap', 0) or 0),
                'shares_outstanding': float(data.get('share_class_shares_outstanding', 0) or 
                                            data.get('weighted_shares_outstanding', 0) or 0)
            }
        except Exception as e:
            return {'error': f"Profile error: {e}"}

    def run_model_at_date(self, ticker: str, as_of_date: str) -> Dict:
        """
        Runs the full "Tier 2" weighted model check for a single ticker
        at a single point in time. Returns a score and details.
        """
        try:
            as_of_dt = datetime.strptime(as_of_date, '%Y-%m-%d')
            start_120d = (as_of_dt - timedelta(days=120)).strftime('%Y-%m-%d')
            
            gem_score = 0
            reasons = []

            # --- 1. [SETUP] Get Profile & Check Sector/Float/MC ---
            profile = self.get_ticker_info_at_date(ticker, as_of_date)
            if 'error' in profile:
                return {'score': 0, 'reason': profile['error']}
            
            is_hot_sector = profile['sector'] in ["BIOTECH/HEALTH", "TECH", "ENERGY/MINING"]
            is_micro_cap = bool(0 < profile['market_cap'] < 300_000_000)
            is_ultra_low_float = bool(0 < profile['shares_outstanding'] < 20_000_000)
            
            # These are hard filters. A stock must pass these to even be scored.
            if not is_hot_sector:
                return {'score': 0, 'reason': f"Wrong Sector ({profile['sector']})"}
            if not is_micro_cap:
                return {'score': 0, 'reason': f"Not Micro-Cap (MC: {profile['market_cap']:,.0f})"}
            if not is_ultra_low_float:
                return {'score': 0, 'reason': f"Not ULF (Shares: {profile['shares_outstanding']:,.0f})"}

            # If it passes setup, give it the setup points
            gem_score += 20 # 20 for ULF
            gem_score += 20 # 20 for Hot Sector
            reasons.append("SETUP_PASS(40)")

            # --- 2. [MOMENTUM] Get Bars & Check Golden Cross/RS ---
            
            # Get Stock Bars
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_120d}/{as_of_date}"
            params = {'apiKey': self.api_key, 'adjusted': 'true', 'sort': 'asc', 'limit': 120}
            response = requests.get(url, params=params)
            self.log_call()
            
            if response.status_code != 200:
                return {'score': gem_score, 'reason': f"SETUP_PASS(40), API error (Stock Bars {response.status_code})"}
            
            bars = response.json().get('results', [])
            if len(bars) < 50:
                return {'score': gem_score, 'reason': f"SETUP_PASS(40), Insufficient bars ({len(bars)})"}
            
            closes = [float(b['c']) for b in bars]
            price_ma20 = float(np.mean(closes[-20:]))
            price_ma50 = float(np.mean(closes[-50:]))
            is_golden_cross = price_ma20 > price_ma50

            # Get SPY Bars
            spy_url = f"{self.base_url}/v2/aggs/ticker/SPY/range/1/day/{start_120d}/{as_of_date}"
            spy_response = requests.get(spy_url, params=params)
            self.log_call()
            
            if spy_response.status_code != 200:
                return {'score': gem_score, 'reason': f"SETUP_PASS(40), API error (SPY Bars {spy_response.status_code})"}
            
            spy_bars = spy_response.json().get('results', [])
            if len(spy_bars) < 50:
                return {'score': gem_score, 'reason': f"SETUP_PASS(40), Insufficient SPY bars"}

            # Check Strong Outperformance
            ticker_return = (bars[-1]['c'] - bars[0]['c']) / bars[0]['c'] if bars[0]['c'] > 0 else 0
            spy_return = (spy_bars[-1]['c'] - spy_bars[0]['c']) / spy_bars[0]['c'] if spy_bars[0]['c'] > 0 else 0
            strongly_outperforming = bool(ticker_return > spy_return + 0.1) # 10% beat

            # --- 3. [FINAL SCORE] ---
            if strongly_outperforming:
                gem_score += 40
                reasons.append("STRONG_RS(+40)")
                
            if is_golden_cross:
                gem_score += 20
                reasons.append("GOLDEN_CROSS(+20)")

            return {'score': gem_score, 'reason': ", ".join(reasons)}

        except Exception as e:
            return {'score': 0, 'reason': f"Unknown Error: {e}"}

    def run_timeline_analysis(self, input_file: str, output_file: str):
        """
        Main logic loop. Loads test file and runs the model at each
        T-minus interval for each ticker.
        """
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            discoveries = data.get('discoveries', [])
            print(f"Loaded {len(discoveries)} tickers from {input_file} for timeline analysis.")
        except Exception as e:
            print(f"❌ Failed to load test file: {e}")
            return

        intervals_to_test = [-90, -60, -30, -15, -7, -1] # T-minus days
        results_log = []

        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("GEM TRADING SYSTEM - TIMELINE BACKTEST REPORT (v2 - Weighted Score)\n")
            f.write(f"Test Set: {input_file}\n")
            f.write(f"Run at: {datetime.now().isoformat()}\n")
            f.write(f"Model: ULF + Hot Sector (40pts), Strong RS (+40pts), Golden Cross (+20pts)\n")
            f.write(f"Pass Threshold: {self.pass_threshold} points\n")
            f.write("="*80 + "\n\n")

            # Create header
            header = "Ticker | Gain % | T-90 | T-60 | T-30 | T-15 | T-7  | T-1 \n"
            f.write(header)
            f.write(f"{'-'*len(header)}\n")
            print(header, end="") # No newline for console

            for i, explosion in enumerate(discoveries):
                ticker = explosion['ticker']
                gain_pct = float(explosion['gain_pct'])
                catalyst_dt = datetime.strptime(explosion['catalyst_date'], '%Y-%m-%d')
                
                print(f"Analyzing {ticker} (Catalyst: {explosion['catalyst_date']})...")
                
                result_row = {
                    'ticker': ticker,
                    'gain_pct': f"{gain_pct:,.0f}%",
                }

                for days in intervals_to_test:
                    scan_date = (catalyst_dt + timedelta(days=days)).strftime('%Y-%m-%d')
                    
                    try:
                        scan_result = self.run_model_at_date(ticker, scan_date)
                        result_row[f'T{days}'] = scan_result['score']
                    except Exception as e:
                        print(f"  Error scanning {ticker} at {scan_date}: {e}")
                        result_row[f'T{days}'] = "ERR"
                
                results_log.append(result_row)
                
                # Write to file
                f.write(f"{result_row['ticker']:<6} | "
                        f"{result_row['gain_pct']:>7} | "
                        f"{str(result_row['T-90']):>4} | "
                        f"{str(result_row['T-60']):>4} | "
                        f"{str(result_row['T-30']):>4} | "
                        f"{str(result_row['T-15']):>4} | "
                        f"{str(result_row['T-7']):>4} | "
                        f"{str(result_row['T-1']):>4}\n")
                
                # Print to console
                print(f"  > {result_row}\n")

            # --- Final Summary ---
            df = pd.DataFrame(results_log)
            total_stocks = len(df)
            
            f.write("\n" + "="*80 + "\n")
            f.write("TIMELINE ANALYSIS SUMMARY\n")
            f.write("="*80 + "\n")
            f.write(f"Total Stocks Tested: {total_stocks}\n")
            f.write(f"Pass Threshold: {self.pass_threshold} points\n\n")
            f.write("Detection Rate (What % of winners did we find?)\n")
            
            for days in intervals_to_test:
                col_name = f'T{days}'
                # Ensure column is numeric, coercing errors to NaN
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
