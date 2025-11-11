#!/usr/bin/env python3
"""
GEM TRADING SYSTEM - LIVE PREDICTIVE SCREENER (v2)

This script tests our "Golden Fingerprint (Tier 2)" model.
It can be run in two modes:

1.  TEST MODE (Default):
    - Reads tickers from an input file (e.g., 'DISCARD_EXPLOSIONS.json').
    - Analyzes *only* those tickers against the model.
    - Saves a `screener_test_report.txt`.
    - python live_screener.py DISCARD_EXPLOSIONS.json

2.  LIVE MODE (No Arguments):
    - Fetches *all* ~8,000+ US tickers from Polygon.
    - Runs the scan on all of them.
    - Saves a `screener_live_report.txt`.
    - python live_screener.py
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
import numpy as np
import sys
from polygon import RESTClient
from typing import Dict, List, Optional, TextIO

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    print("❌ ERROR: POLYGON_API_KEY environment variable not set.")
    sys.exit(1)

# Initialize the Polygon client
try:
    polygon_client = RESTClient(POLYGON_API_KEY)
    print("Polygon client initialized successfully.")
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Polygon client: {e}")
    sys.exit(1)

def map_sic_to_sector(sic_description: str) -> str:
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

def get_all_tickers() -> List[str]:
    """Fetches all US-based stock tickers from Polygon."""
    print("Fetching all US stock tickers (this may take a moment)...")
    tickers = []
    try:
        for ticker in polygon_client.list_tickers(market='stocks', type='CS', active=True, limit=1000):
            if ticker.locale == 'us':
                tickers.append(ticker.ticker)
        print(f"Found {len(tickers)} active US tickers.")
        return tickers
    except Exception as e:
        print(f"❌ ERROR fetching ticker list: {e}")
        return []

def get_tickers_from_file(input_file: str) -> List[str]:
    """Extracts a list of tickers from a JSON file (like CLEAN_EXPLOSIONS.json)."""
    print(f"Loading tickers from input file: {input_file}...")
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Check for both 'discoveries' (our format) or just a list of tickers
        if 'discoveries' in data:
            tickers = [d['ticker'] for d in data['discoveries'] if 'ticker' in d]
        elif isinstance(data, list):
            tickers = [str(item) for item in data]
        else:
            print(f"❌ ERROR: Unrecognized JSON format in {input_file}.")
            return []
            
        print(f"Found {len(tickers)} tickers to test in {input_file}.")
        return list(set(tickers)) # Return unique list
    except Exception as e:
        print(f"❌ ERROR reading {input_file}: {e}")
        return []

def get_profile(ticker: str) -> Optional[Dict]:
    """Fetches the profile for a single ticker."""
    try:
        resp = polygon_client.get_ticker_details(ticker)
        data = resp.__dict__
        
        market_cap = data.get('market_cap', 0)
        shares = data.get('share_class_shares_outstanding', 0)
        
        if shares == 0:
            return None # Cannot determine float
            
        sic_desc = data.get('sic_description', '')
        sector = map_sic_to_sector(sic_desc)

        return {
            'ticker': ticker,
            'is_micro_cap': bool(0 < market_cap < 300_000_000),
            'is_ultra_low_float': bool(0 < shares < 20_000_000),
            'sector': sector,
            'is_hot_sector': sector in ["BIOTECH/HEALTH", "ENERGY/MINING", "TECH"]
        }
    except Exception as e:
        # This will fail often for weird tickers, it's normal.
        # print(f"  Profile error for {ticker}: {e}")
        return None

def get_technicals(ticker: str) -> Optional[Dict]:
    """Fetches the latest technical indicators for a single ticker."""
    try:
        # Get last 50 days of bar data
        today = datetime.now()
        start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

        bars = []
        for bar in polygon_client.list_aggs(
            ticker, 1, "day", start_date, end_date, limit=50
        ):
            bars.append(bar)
        
        if len(bars) < 50:
            return None # Not enough data

        closes = [b.close for b in bars]
        
        # Calculate MAs
        price_ma20 = np.mean(closes[-20:])
        price_ma50 = np.mean(closes[-50:])
        
        # Check Golden Cross
        is_golden_cross = price_ma20 > price_ma50
        
        # Check Relative Strength
        # We need SPY's data too
        spy_bars = []
        for bar in polygon_client.list_aggs(
            "SPY", 1, "day", start_date, end_date, limit=50
        ):
            spy_bars.append(bar)
            
        if len(spy_bars) < 50:
            return None # Can't compare

        ticker_return = (closes[-1] - closes[0]) / closes[0]
        spy_return = (spy_bars[-1].close - spy_bars[0].close) / spy_bars[0].close
        
        strongly_outperforming = (ticker_return > (spy_return + 0.1)) # 10% or more over SPY

        return {
            'is_golden_cross': is_golden_cross,
            'strongly_outperforming': strongly_outperforming
        }
    except Exception as e:
        # print(f"  Technicals error for {ticker}: {e}")
        return None

def run_screener(tickers: List[str], report_file: TextIO):
    """
    Runs the full Tier 2 "Golden Fingerprint" scan on a list of tickers.
    """
    print(f"\nScanning {len(tickers)} tickers against Tier 2 'Golden' model...")
    report_file.write(f"--- Screener Report (Tier 2 'Golden' Model) ---\n")
    report_file.write(f"Scan initiated at: {datetime.now().isoformat()} on {len(tickers)} tickers.\n")
    report_file.write("Model: (is_ultra_low_float == True) AND (is_hot_sector == True) AND (is_golden_cross == True OR strongly_outperforming == True)\n")
    report_file.write("="*60 + "\n")
    report_file.write("Stocks that MATCHED the filter:\n\n")

    pass_count = 0
    fail_count = 0
    
    for i, ticker in enumerate(tickers):
        if (i + 1) % 100 == 0:
            print(f"  ...scanned {i+1}/{len(tickers)}...")
        
        try:
            # --- Filter 1: The Setup (Profile) ---
            profile = get_profile(ticker)
            time.sleep(0.05) # Rate limit
            
            if not profile:
                fail_count += 1
                continue
                
            passes_profile = (
                profile['is_ultra_low_float'] and
                profile['is_hot_sector']
            )
            
            if not passes_profile:
                fail_count += 1
                continue
                
            # --- Filter 2: The Momentum (Technicals) ---
            tech = get_technicals(ticker)
            time.sleep(0.05) # Rate limit
            
            if not tech:
                fail_count += 1
                continue
            
            passes_momentum = (
                tech['is_golden_cross'] or
                tech['strongly_outperforming']
            )
            
            if not passes_momentum:
                fail_count += 1
                continue

            # --- If it passes ALL filters, it's a match! ---
            pass_count += 1
            print(f"✅ FOUND A MATCH: {ticker}")
            report_file.write(f"✅ {ticker}\n")
            report_file.write(f"  - Profile: ULF={profile['is_ultra_low_float']}, Sector={profile['sector']}\n")
            report_file.write(f"  - Momentum: GoldenCross={tech['is_golden_cross']}, StrongPerf={tech['strongly_outperforming']}\n")
            report_file.write(f"  - Polygon URL: https://polygon.io/stocks/{ticker}\n\n")

        except Exception as e:
            if "Too Many Requests" in str(e):
                print("Hit rate limit. Sleeping for 15 seconds...")
                time.sleep(15)
            # print(f"  Skipping {ticker} due to error: {e}")
            fail_count += 1

    print("\n" + "="*60)
    print("Screener Run Complete.")
    print(f"  Total Stocks Scanned: {len(tickers)}")
    print(f"  Stocks Passed Filters: {pass_count}")
    print(f"  Stocks Failed/Skipped: {fail_count}")
    print("="*60)
    
    report_file.write("\n" + "="*60 + "\n")
    report_file.write("Screener Run Complete.\n")
    report_file.write(f"  Total Stocks Scanned: {len(tickers)}\n")
    report_file.write(f"  Stocks Passed Filters: {pass_count}\n")
    report_file.write(f"  Stocks Failed/Skipped: {fail_count}\n")
    report_file.write("="*60 + "\n")

def main():
    is_test_mode = False
    tickers_to_scan = []
    report_filename = ""

    if len(sys.argv) > 1:
        # --- TEST MODE ---
        # An input file was provided, so we are in test mode.
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"❌ ERROR: Input file '{input_file}' not found.")
            sys.exit(1)
        
        is_test_mode = True
        report_filename = "screener_test_report.txt"
        tickers_to_scan = get_tickers_from_file(input_file)
        
    else:
        # --- LIVE MODE ---
        # No file provided, scan all tickers.
        is_test_mode = False
        report_filename = "screener_live_report.txt"
        tickers_to_scan = get_all_tickers()
        
    if not tickers_to_scan:
        print("No tickers to scan. Exiting.")
        return

    # Run the screener and write to the report file
    with open(report_filename, 'w') as report_file:
        mode_str = "TEST MODE" if is_test_mode else "LIVE MODE"
        print(f"Starting screener in {mode_str}...")
        report_file.write(f"--- RUNNING IN {mode_str} ---\n")
        
        run_screener(tickers_to_scan, report_file)
    
    print(f"✅ Screener complete. Full report saved to {report_filename}.")

if __name__ == "__main__":
    main()
