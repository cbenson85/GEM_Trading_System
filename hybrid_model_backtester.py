#!/usr/bin/env python3
"""
GEM TRADING SYSTEM - FULL MARKET BACKTESTER (v3 - Unlimited API)

This script is built for speed, assuming no API rate limits.
It scans the *entire* market over a specified date range in a single run,
simulating a daily screener.

MODEL (Tier 2 "Golden Fingerprint"):
- PASS Threshold: 80 points
- [SETUP] (40pts)
  - Is Ultra-Low-Float AND Micro-Cap AND in a "Hot Sector"
- [MOMENTUM] (Max 60pts)
  - Is "Strongly Outperforming" SPY (+40pts)
  - Has a "Golden Cross" (MA20 > MA50) (+20pts)
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

# --- Environment Variable Setup ---
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    print("❌ ERROR: POLYGON_API_KEY environment variable not set.")
    sys.exit(1)

# Read from workflow environment
SCAN_START_DATE = os.environ.get('SCAN_START_DATE', '2022-01-01')
SCAN_END_DATE = os.environ.get('SCAN_END_DATE', '2023-12-31')
PASS_THRESHOLD = 80
FINAL_REPORT_FILE = "HYBRID_BACKTEST_FINAL_REPORT.txt"

class FullMarketBacktester:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.polygon_client = RESTClient(api_key)
        self.api_calls = 0
        self.scan_start_dt = datetime.strptime(SCAN_START_DATE, '%Y-%m-%d')
        self.scan_end_dt = datetime.strptime(SCAN_END_DATE, '%Y-%m-%d')

    def log_call(self, service="polygon"):
        # We still count calls for reference, but we do not sleep.
        self.api_calls += 1
        # time.sleep(0.2) # REMOVED for unlimited API tier

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

    def get_all_tickers(self) -> List[Dict]:
        """Fetches all active tickers from Polygon."""
        print("Fetching all active tickers from Polygon...")
        all_tickers = []
        try:
            for t in self.polygon_client.list_tickers(market="stocks", active=True, limit=1000):
                all_tickers.append({
                    'ticker': t.ticker,
                    'name': t.name
                })
        except Exception as e:
            print(f"  > Error fetching full ticker list: {e}")
            return []
        
        print(f"Processing {len(all_tickers)} total tickers.")
        return all_tickers

    def get_daily_watchlist(self, tickers: List[Dict], as_of_date: str) -> List[Dict]:
        """
        Runs the 'Setup' filter (Phase 1) on a list of tickers.
        Returns a smaller 'Watchlist' of stocks that pass.
        """
        watchlist = []
        for ticker_info in tickers:
            ticker = ticker_info['ticker']

            try:
                url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?date={as_of_date}&apiKey={self.api_key}"
                response = requests.get(url)
                self.log_call()
                
                if response.status_code != 200:
                    continue 
                    
                data = response.json().get('results', {})
                
                sic_desc = data.get('sic_description', '')
                sector = self.map_sic_to_sector(sic_desc)
                is_hot_sector = sector in ["BIOTECH/HEALTH", "TECH", "ENERGY/MINING"]
                
                if not is_hot_sector:
                    continue 
                
                market_cap = float(data.get('market_cap', 0) or 0)
                shares = float(data.get('share_class_shares_outstanding', 0) or 
                             data.get('weighted_shares_outstanding', 0) or 0)

                is_micro_cap = bool(0 < market_cap < 300_000_000)
                is_ultra_low_float = bool(0 < shares < 20_000_000)

                if is_micro_cap and is_ultra_low_float:
                    ticker_info['sector'] = sector
                    ticker_info['market_cap'] = market_cap
                    ticker_info['shares_outstanding'] = shares
                    watchlist.append(ticker_info)
            
            except Exception as e:
                print(f"  > Error (Watchlist) {ticker}: {e}")
                continue
                
        return watchlist

    def get_momentum_score(self, ticker: str, as_of_date: str) -> (int, str):
        """
        Calculates the 'Momentum' score for a single ticker.
        """
        try:
            as_of_dt = datetime.strptime(as_of_date, '%Y-%m-%d')
            start_170d = (as_of_dt - timedelta(days=170)).strftime('%Y-%m-%d')
            
            # Get Stock Bars
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_170d}/{as_of_date}?apiKey={self.api_key}&adjusted=true&sort=asc&limit=120"
            response = requests.get(url)
            self.log_call()
            
            if response.status_code != 200: return 0, "NoStockBars"
            bars = response.json().get('results', [])
            if len(bars) < 50: return 0, f"Bars<50({len(bars)})"
            
            closes = [float(b['c']) for b in bars]
            price_ma20 = float(np.mean(closes[-20:]))
            price_ma50 = float(np.mean(closes[-50:]))
            is_golden_cross = price_ma20 > price_ma50

            # Get SPY Bars
            spy_url = f"https://api.polygon.io/v2/aggs/ticker/SPY/range/1/day/{start_170d}/{as_of_date}?apiKey={self.api_key}&adjusted=true&sort=asc&limit=120"
            spy_response = requests.get(spy_url)
            self.log_call()
            
            if spy_response.status_code != 200: return 0, "NoSPYBars"
            spy_bars = spy_response.json().get('results', [])
            if len(spy_bars) < 50: return 0, "SPYBars<50"

            # Compare returns
            common_start_timestamp = max(bars[0]['t'], spy_bars[0]['t'])
            stock_start_bar = next((b for b in bars if b['t'] >= common_start_timestamp), None)
            spy_start_bar = next((b for b in spy_bars if b['t'] >= common_start_timestamp), None)

            if not stock_start_bar or not spy_start_bar:
                return 0, "NoCommonDate"

            ticker_return = (bars[-1]['c'] - stock_start_bar['c']) / stock_start_bar['c'] if stock_start_bar['c'] > 0 else 0
            spy_return = (spy_bars[-1]['c'] - spy_start_bar['c']) / spy_start_bar['c'] if spy_start_bar['c'] > 0 else 0
            strongly_outperforming = bool(ticker_return > spy_return + 0.1) 

            # Calculate score
            score = 0
            reasons = []
            if strongly_outperforming:
                score += 40
                reasons.append("RS(+40)")
            if is_golden_cross:
                score += 20
                reasons.append("GC(+20)")
            
            return score, ",".join(reasons) if reasons else "NoMomentum"

        except Exception as e:
            return 0, f"MomentumErr({e})"

    def get_90_day_performance(self, ticker: str, as_of_date: str) -> float:
        """Gets the % gain for a ticker 90 days *after* a scan date."""
        try:
            start_dt = datetime.strptime(as_of_date, '%Y-%m-%d')
            end_dt = (start_dt + timedelta(days=90))
            
            start_date_str = start_dt.strftime('%Y-%m-%d')
            end_date_str = end_dt.strftime('%Y-%m-%d')

            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date_str}/{end_date_str}?apiKey={self.api_key}&adjusted=true&sort=asc&limit=90"
            response = requests.get(url)
            self.log_call()

            if response.status_code != 200: return 0.0
            bars = response.json().get('results', [])
            if len(bars) < 2: return 0.0

            start_price = bars[0]['c']
            end_price = bars[-1]['c']
            
            if start_price > 0:
                return ((end_price - start_price) / start_price) * 100
            
        except Exception as e:
            print(f"  > Error (Perf Check) {ticker}: {e}")
        
        return 0.0

    def run_daily_scan(self, all_tickers: List[Dict]) -> List[Dict]:
        """
        Iterates through each day in the date range, scans all tickers,
        and logs performance for any stock that passes.
        """
        results = []
        
        date_range = pd.bdate_range(self.scan_start_dt, self.scan_end_dt)
        print(f"Scanning {len(all_tickers)} tickers over {len(date_range)} trading days...")
        
        last_watchlist = {} # Cache scores to find "new" triggers
        
        for i, day in enumerate(date_range):
            day_str = day.strftime('%Y-%m-%d')
            print(f"\n--- Scanning Date: {day_str} ({i+1}/{len(date_range)}) ---")
            
            # Phase 1: Filter 8000+ tickers down to a small watchlist
            watchlist = self.get_daily_watchlist(all_tickers, day_str)
            print(f"  > [Setup] Filtered {len(all_tickers)} tickers down to {len(watchlist)} on watchlist.")
            
            current_watchlist = {}

            # Phase 2: Score the watchlist
            for ticker_info in watchlist:
                ticker = ticker_info['ticker']
                setup_score = 40 # Already passed setup
                
                mom_score, mom_reason = self.get_momentum_score(ticker, day_str)
                
                gem_score = setup_score + mom_score
                current_watchlist[ticker] = gem_score
                
                if gem_score >= PASS_THRESHOLD:
                    if last_watchlist.get(ticker, 0) < PASS_THRESHOLD:
                        
                        print(f"  ✅✅✅ NEW 'BUY' SIGNAL: {ticker} (Score: {gem_score}) ✅✅✅")
                        print(f"  > Reason: Setup(40), {mom_reason}")
                        
                        gain_pct = self.get_90_day_performance(ticker, day_str)
                        print(f"  > Result: {ticker} had a 90-day gain of {gain_pct:.2f}%")
                        
                        results.append({
                            'scan_date': day_str,
                            'ticker': ticker,
                            'gem_score': gem_score,
                            'reason': f"Setup(40), {mom_reason}",
                            'gain_pct_90d': gain_pct
                        })

            last_watchlist = current_watchlist
            print(f"  > Day {day_str} complete. Total API calls: {self.api_calls}")

        return results

def main():
    start_time = time.time()
    
    # --- 1. Get All Tickers ---
    backtester = FullMarketBacktester(POLYGON_API_KEY)
    all_tickers = backtester.get_all_tickers()
    
    if not all_tickers:
        print("No tickers found. Exiting.")
        return

    # --- 2. Run Scan ---
    scan_results = backtester.run_daily_scan(all_tickers)

    # --- 3. Create Final Report ---
    if not scan_results:
        print("No signals found in any batch. Report will be minimal.")
        with open(FINAL_REPORT_FILE, 'w') as f:
            f.write("="*80 + "\n")
            f.write("GEM TRADING SYSTEM - HYBRID BACKTEST FINAL REPORT\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n")
            f.write(f"Data Range: {SCAN_START_DATE} to {SCAN_END_DATE}\n")
            f.write("="*80 + "\n\n")
            f.write("--- SUMMARY --- \n")
            f.write("No signals were found matching the criteria in the specified date range.\n")
            f.write(f"Total API Calls: {backtester.api_calls}\n")
        return

    # --- 4. Create DataFrame for analysis ---
    df = pd.DataFrame(scan_results)
    df['gain_pct_90d'] = pd.to_numeric(df['gain_pct_90d'], errors='coerce').fillna(0)

    # --- 5. Calculate Key Metrics ---
    avg_gain = df['gain_pct_90d'].mean()
    median_gain = df['gain_pct_90d'].median()
    
    winners = df[df['gain_pct_90d'] > 25] # > 25% gain
    losers = df[df['gain_pct_90d'] <= 25]
    
    win_rate = (len(winners) / len(df)) * 100
    
    avg_win_gain = winners['gain_pct_90d'].mean() if not winners.empty else 0
    avg_loss_pct = losers['gain_pct_90d'].mean() if not losers.empty else 0
    
    big_winners = df[df['gain_pct_90d'] > 500]
    mega_winners = df[df['gain_pct_90d'] > 1000]

    # --- 6. Write the Final Report ---
    with open(FINAL_REPORT_FILE, 'w') as f:
        f.write("="*80 + "\n")
        f.write("GEM TRADING SYSTEM - HYBRID BACKTEST FINAL REPORT\n")
        f.write(f"Generated at: {datetime.now().isoformat()}\n")
        f.write(f"Data Range: {SCAN_START_DATE} to {SCAN_END_DATE}\n")
        f.write("Model: Tier 2 (Setup + Momentum) | Pass Threshold: 80 points\n")
        f.write("="*80 + "\n\n")
        
        f.write("--- EXECUTIVE SUMMARY --- \n")
        f.write(f"  Total Signals Found:   {len(df)}\n")
        f.write(f"  Win Rate (> 25% Gain): {win_rate:.2f}%\n")
        f.write(f"  Average Gain (All):    {avg_gain:.2f}%\n")
        f.write(f"  Median Gain (All):     {median_gain:.2f}%\n")
        f.write(f"  Average Winner Gain:   {avg_win_gain:.2f}%\n")
        f.write(f"  Average Loser Pct:     {avg_loss_pct:.2f}%\n")
        f.write(f"  Big Winners (>500%):   {len(big_winners)}\n")
        f.write(f"  Mega Winners (>1000%): {len(mega_winners)}\n")
        f.write(f"  Total API Calls:       {backtester.api_calls:,}\n")
        f.write("\n" + "="*80 + "\n")

        f.write("\n--- ALL SIGNALS LOG (Sorted by Gain) --- \n")
        f.write("Scan Date  | Ticker | Score | 90-Day Gain | Reason\n")
        f.write("--------------------------------------------------------------------------\n")
        
        df_sorted = df.sort_values(by='gain_pct_90d', ascending=False)
        for _, row in df_sorted.iterrows():
            f.write(f"{row['scan_date']} | {row['ticker']:<6} | {row['gem_score']:<5} | {row['gain_pct_90d']:>11.2f}% | {row['reason']}\n")

    end_time = time.time()
    print("\n" + "="*60)
    print(f"FULL MARKET BACKTEST COMPLETE")
    print(f"  Total time: {((end_time - start_time) / 60):.2f} minutes")
    print(f"  Total API Calls: {backtester.api_calls}")
    print(f"  Signals Found: {len(scan_results)}")
    print(f"  Report saved to: {FINAL_REPORT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()
