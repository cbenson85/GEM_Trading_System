#!/usr/bin/env python3
"""
GEM TRADING SYSTEM - PRODUCTION BACKTESTER (WORKFLOW-COMPATIBLE)
Matches your workflow and collect_reports.py requirements exactly
"""

import os
import json
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# === CONFIGURATION ===
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    raise ValueError("POLYGON_API_KEY environment variable not set.")

POLYGON_BASE_URL = "https://api.polygon.io"

# Read batch parameters from workflow
BATCH_START = int(os.getenv('BATCH_START', 0))
BATCH_END = int(os.getenv('BATCH_END', 250))

# Backtest period
SCAN_START_DATE = '2022-01-01'
SCAN_END_DATE = '2023-12-31'

# Data window requirements
PRE_ROLL_DAYS = 60  # For MA50
POST_ROLL_DAYS = 90 # For performance tracking

# Calculate data window
DATA_START_DATE = (pd.to_datetime(SCAN_START_DATE) - pd.DateOffset(days=PRE_ROLL_DAYS)).strftime('%Y-%m-%d')
DATA_END_DATE = (pd.to_datetime(SCAN_END_DATE) + pd.DateOffset(days=POST_ROLL_DAYS)).strftime('%Y-%m-%d')

# Model thresholds
SCORE_THRESHOLD = 80
SHARES_ULTRA_LOW_FLOAT = 20_000_000
MARKET_CAP_MICRO = 300_000_000
HOT_SECTORS = ["BIOTECH/HEALTH", "TECH", "ENERGY/MINING"]

# CRITICAL: Exact mapping from fingerprint_analyzer.py
SECTOR_SIC_MAP = {
    "BIOTECH/HEALTH": list(range(2830, 2840)) + [3841, 3842, 3845, 3851, 8000, 8060, 8062, 8071],
    "TECH": list(range(3570, 3580)) + list(range(3600, 3700)) + list(range(7370, 7380)) + [3812, 3825, 3826, 3827, 3829, 4812, 4813],
    "ENERGY/MINING": list(range(1000, 1100)) + list(range(1200, 1300)) + list(range(1300, 1400)) + [2911, 4911, 4924, 4925, 4931, 4932],
}

# === API FUNCTIONS ===

def fetch_with_retry(url: str, params: dict = None, retries: int = 5, backoff_factor: float = 0.5) -> Optional[dict]:
    """Fetch with exponential backoff retry."""
    headers = {"Authorization": f"Bearer {POLYGON_API_KEY}"}
    
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if i == retries - 1:
                print(f"    [ERROR] Failed after {retries} retries: {e}")
                return None
            time.sleep(backoff_factor * (2 ** i))
    return None

def get_sector_from_sic(sic_code: Optional[int]) -> str:
    """Maps SIC code to sector - MUST match fingerprint_analyzer.py"""
    if not sic_code:
        return "OTHER"
    try:
        sic = int(sic_code)
        for sector, codes in SECTOR_SIC_MAP.items():
            if sic in codes:
                return sector
    except (ValueError, TypeError):
        pass
    return "OTHER"

def get_all_tickers(limit: int = 10000) -> list:
    """Get all active common stocks."""
    print("Fetching all tickers...")
    tickers = []
    url = f"{POLYGON_BASE_URL}/v3/reference/tickers"
    params = {
        "active": "true",
        "market": "stocks",
        "type": "CS",
        "limit": 1000,
        "apiKey": POLYGON_API_KEY
    }
    
    while True:
        data = fetch_with_retry(url, params)
        if not data or "results" not in data:
            break
        tickers.extend(data["results"])
        if len(tickers) >= limit:
            return tickers[:limit]
        if "next_url" in data:
            url = data["next_url"]
            params = {}
        else:
            break
    
    print(f"Fetched {len(tickers)} tickers.")
    return tickers

def get_ticker_details(ticker: str) -> dict:
    """Get ticker details including SIC code."""
    url = f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"
    data = fetch_with_retry(url, {"apiKey": POLYGON_API_KEY})
    return data.get("results", {}) if data else {}

def get_price_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Get price history for ticker."""
    url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": POLYGON_API_KEY}
    data = fetch_with_retry(url, params)
    
    if not data or "results" not in data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data["results"])
    df['date'] = pd.to_datetime(df['t'], unit='ms').dt.strftime('%Y-%m-%d')
    df = df.rename(columns={'c': 'close', 'v': 'volume'})
    return df[['date', 'close', 'volume']]

# === MAIN BACKTEST ===

def run_backtest_batch(batch_start: int, batch_end: int):
    """Run backtest for ticker batch."""
    print(f"--- Starting Batch {batch_start}-{batch_end} ---")
    
    # 1. Fetch SPY data once
    print("Fetching SPY data...")
    spy_df = get_price_history('SPY', DATA_START_DATE, DATA_END_DATE)
    if spy_df.empty:
        raise Exception("Could not fetch SPY data.")
    
    spy_df.set_index('date', inplace=True)
    spy_df['spy_return_30d'] = spy_df['close'].pct_change(30)
    spy_df['spy_fwd_90d'] = spy_df['close'].shift(-90) / spy_df['close'] - 1
    
    # 2. Get tickers
    all_tickers = get_all_tickers(10000)
    batch_tickers = all_tickers[batch_start:batch_end]
    print(f"Processing {len(batch_tickers)} tickers.")
    
    all_signals = []
    summary = {
        "total_stocks_scanned": 0,
        "stocks_with_errors": 0,
        "stocks_passing_setup": 0,
        "total_buy_signals": 0
    }
    
    # 3. Process each ticker
    for i, ticker_info in enumerate(batch_tickers):
        ticker = ticker_info['ticker']
        
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(batch_tickers)}")
        
        try:
            # Get details
            details = get_ticker_details(ticker)
            if not details:
                summary['stocks_with_errors'] += 1
                continue
            
            # Get price history
            stock_df = get_price_history(ticker, DATA_START_DATE, DATA_END_DATE)
            if stock_df.empty or len(stock_df) < (PRE_ROLL_DAYS + POST_ROLL_DAYS):
                summary['stocks_with_errors'] += 1
                continue
            
            summary['total_stocks_scanned'] += 1
            
            # Check setup
            market_cap = details.get('market_cap', 0)
            shares = details.get('share_class_shares_outstanding', 0)
            sic_code = details.get('sic_code', None)
            sector = get_sector_from_sic(sic_code)
            
            is_ultra_low_float = (shares > 0 and shares < SHARES_ULTRA_LOW_FLOAT)
            is_micro_cap = (market_cap > 0 and market_cap < MARKET_CAP_MICRO)
            is_hot_sector = sector in HOT_SECTORS
            
            if not (is_ultra_low_float and is_micro_cap and is_hot_sector):
                continue
            
            summary['stocks_passing_setup'] += 1
            
            # Merge with SPY
            stock_df.set_index('date', inplace=True)
            combined = stock_df.join(spy_df[['spy_return_30d', 'spy_fwd_90d']], how='left')
            combined['spy_return_30d'].fillna(method='ffill', inplace=True)
            combined['spy_fwd_90d'].fillna(method='ffill', inplace=True)
            
            # Calculate signals
            combined['ma20'] = combined['close'].rolling(window=20).mean()
            combined['ma50'] = combined['close'].rolling(window=50).mean()
            combined['golden_cross_points'] = np.where(combined['ma20'] > combined['ma50'], 20, 0)
            
            combined['return_30d'] = combined['close'].pct_change(30)
            combined['outperforming_points'] = np.where(
                combined['return_30d'] > (combined['spy_return_30d'] + 0.10), 40, 0
            )
            
            combined['fwd_return_90d'] = combined['close'].shift(-90) / combined['close'] - 1
            
            combined['total_score'] = 40 + combined['golden_cross_points'] + combined['outperforming_points']
            combined['pass_filter'] = combined['total_score'] >= SCORE_THRESHOLD
            
            # Find triggers
            scan_period = combined.loc[SCAN_START_DATE:SCAN_END_DATE].copy()
            scan_period['prev_pass'] = scan_period['pass_filter'].shift(1).fillna(False)
            triggers = scan_period[(scan_period['pass_filter']) & (~scan_period['prev_pass'])]
            
            if not triggers.empty:
                summary['total_buy_signals'] += len(triggers)
                
                for date, row in triggers.iterrows():
                    all_signals.append({
                        "ticker": ticker,
                        "date": date,
                        "sector": sector,
                        "market_cap": market_cap,
                        "shares_outstanding": shares,
                        "score": row['total_score'],
                        "setup_points": 40,
                        "momentum_gc_pts": row['golden_cross_points'],
                        "momentum_spy_pts": row['outperforming_points'],
                        "price_at_buy": row['close'],
                        "fwd_return_90d": row.get('fwd_return_90d'),
                        "spy_fwd_return_90d": row.get('spy_fwd_90d'),
                        "beat_spy": row.get('fwd_return_90d', 0) > row.get('spy_fwd_90d', 0) if pd.notna(row.get('fwd_return_90d')) else None
                    })
                    
        except Exception as e:
            print(f"    Error processing {ticker}: {e}")
            summary['stocks_with_errors'] += 1
    
    # 4. Generate reports
    print(f"--- Batch {batch_start}-{batch_end} Complete ---")
    print(json.dumps(summary, indent=2))
    
    # Create report
    report_df = pd.DataFrame(all_signals)
    report_content = f"--- Backtest Report: Batch {batch_start}-{batch_end} ---\n\n"
    report_content += f"Scan Period: {SCAN_START_DATE} to {SCAN_END_DATE}\n"
    report_content += f"Tickers Processed: {summary['total_stocks_scanned']}\n"
    report_content += f"Stocks Passing Setup: {summary['stocks_passing_setup']}\n"
    report_content += f"Data Errors: {summary['stocks_with_errors']}\n"
    report_content += f"Total BUY Signals: {summary['total_buy_signals']}\n\n"
    
    if not report_df.empty:
        complete_df = report_df.dropna(subset=['fwd_return_90d', 'spy_fwd_return_90d'])
        
        if not complete_df.empty:
            wins = complete_df[complete_df['fwd_return_90d'] > complete_df['spy_fwd_return_90d']]
            win_rate = (len(wins) / len(complete_df)) * 100
            supernova_hits = complete_df[complete_df['fwd_return_90d'] >= 5.0]
            
            avg_gain_pct = complete_df['fwd_return_90d'].mean() * 100
            avg_spy_gain_pct = complete_df['spy_fwd_return_90d'].mean() * 100
            
            report_content += "--- Performance (90-Day Hold) ---\n"
            report_content += f"Win Rate (vs SPY): {win_rate:.2f}%\n"
            report_content += f"Average Gain: {avg_gain_pct:.2f}%\n"
            report_content += f"Average SPY Gain: {avg_spy_gain_pct:.2f}%\n"
            report_content += f"Supernova Hits (500%+): {len(supernova_hits)}\n"
    
    # Save files (CRITICAL: Match workflow expectations)
    report_filename = f"backtest_report_{batch_start}_{batch_end}.txt"
    json_filename = f"buy_signals_{batch_start}_{batch_end}.json"
    
    with open(report_filename, 'w') as f:
        f.write(report_content)
    
    # CRITICAL: Save as flat list for collect_reports.py
    report_df.to_json(json_filename, orient='records', indent=2)
    
    print(f"Saved {report_filename}")
    print(f"Saved {json_filename}")

# === MAIN ===
if __name__ == "__main__":
    run_backtest_batch(BATCH_START, BATCH_END)
