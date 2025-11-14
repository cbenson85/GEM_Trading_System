import os
import json
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    raise ValueError("POLYGON_API_KEY environment variable not set.")

POLYGON_BASE_URL = "https://api.polygon.io"
HEADERS = {"Authorization": f"Bearer {POLYGON_API_KEY}"}

# Backtest period
SCAN_START_DATE = '2022-01-01'
SCAN_END_DATE = '2023-12-31'

# Data window needs
PRE_ROLL_DAYS = 60  # Need ~50 days for MA50, 60 is safe
POST_ROLL_DAYS = 90 # Need 90 days *after* scan period to check performance

# Calculate total data window
DATA_START_DATE = (pd.to_datetime(SCAN_START_DATE) - pd.DateOffset(days=PRE_ROLL_DAYS)).strftime('%Y-%m-%d')
DATA_END_DATE = (pd.to_datetime(SCAN_END_DATE) + pd.DateOffset(days=POST_ROLL_DAYS)).strftime('%Y-%m-%d')

# Model Thresholds
SCORE_THRESHOLD = 80
SHARES_ULTRA_LOW_FLOAT = 20_000_000
MARKET_CAP_MICRO = 300_000_000
HOT_SECTORS = ["BIOTECH/HEALTH", "TECH", "ENERGY/MINING"]

# Copied from fingerprint_analyzer.py for consistency
SECTOR_SIC_MAP = {
    "BIOTECH/HEALTH": list(range(2830, 2840)) + [3841, 3842, 3845, 3851, 8000, 8060, 8062, 8071],
    "TECH": list(range(3570, 3580)) + list(range(3600, 3700)) + list(range(7370, 7380)) + [3812, 3825, 3826, 3827, 3829, 4812, 4813],
    "ENERGY/MINING": list(range(1000, 1100)) + list(range(1200, 1300)) + list(range(1300, 1400)) + [2911, 4911, 4924, 4925, 4931, 4932],
}

# --- API & DATA FUNCTIONS ---

def fetch_with_retry(url: str, params: dict, retries: int = 5, backoff_factor: float = 0.5) -> dict:
    """Fetches from Polygon API with retry logic."""
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            if response.status_code == 404:
                # Don't retry 404s
                print(f"    [404 Not Found]: {url}")
                return None
            print(f"    [WARN] API call failed (Attempt {i+1}/{retries}): {e}")
            time.sleep(backoff_factor * (2 ** i))
    print(f"    [ERROR] API call failed after {retries} retries: {url}")
    return None

def get_all_tickers(limit: int = 5000) -> list:
    """Gets all active, non-OTC US common stocks."""
    print("Fetching all tickers...")
    tickers = []
    url = f"{POLYGON_BASE_URL}/v3/reference/tickers"
    params = {
        "active": "true",
        "market": "stocks",
        "exchange": "XNAS,XNYS,XASE", # Major US exchanges
        "type": "CS", # Common Stock
        "limit": 1000
    }
    
    while True:
        data = fetch_with_retry(url, params)
        if not data or "results" not in data or not data["results"]:
            break
        
        tickers.extend(data["results"])
        
        if len(tickers) >= limit: # Safety break to prevent full 12k scan
             print(f"Reached ticker limit of {limit}. Stopping fetch.")
             return tickers[:limit]
        
        if "next_url" in data:
            url = data["next_url"]
            params = {} # next_url includes all params
        else:
            break
            
    print(f"Fetched {len(tickers)} total tickers.")
    return tickers

def get_ticker_details(ticker: str) -> dict:
    """Gets snapshot details for a single ticker."""
    url = f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"
    data = fetch_with_retry(url, {})
    return data.get("results", {}) if data else {}

def get_price_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Gets full price history for a ticker and returns a DataFrame."""
    url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000}
    data = fetch_with_retry(url, params)
    
    if not data or "results" not in data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data["results"])
    df['date'] = pd.to_datetime(df['t'], unit='ms').dt.strftime('%Y-%m-%d')
    df = df.rename(columns={'c': 'close', 'o': 'open', 'h': 'high', 'l': 'low', 'v': 'volume'})
    return df[['date', 'close', 'volume']]

def get_sector_from_sic(sic_code: int) -> str:
    """Maps SIC code to one of our hot sectors."""
    if not sic_code:
        return "OTHER"
    try:
        sic = int(sic_code)
        for sector, codes in SECTOR_SIC_MAP.items():
            if sic in codes:
                return sector
    except ValueError:
        pass
    return "OTHER"

# --- CORE BACKTEST LOGIC ---

def run_backtest_batch(batch_start: int, batch_end: int):
    """
    Runs the backtest for a specific slice of tickers using
    vectorized pandas operations to minimize API calls.
    """
    print(f"--- Starting Batch {batch_start}-{batch_end} ---")
    
    # 1. Fetch SPY data ONCE for the entire data window
    print("Fetching SPY data...")
    spy_df = get_price_history('SPY', DATA_START_DATE, DATA_END_DATE)
    if spy_df.empty:
        raise Exception("Could not fetch SPY data. Aborting.")
    
    # Pre-calculate SPY signals
    spy_df.rename(columns={'close': 'spy_close'}, inplace=True)
    spy_df['spy_return_30d'] = spy_df['spy_close'].pct_change(30)
    spy_df['spy_fwd_return_90d'] = spy_df['spy_close'].shift(-90) / spy_df['spy_close'] - 1
    spy_df = spy_df[['date', 'spy_close', 'spy_return_30d', 'spy_fwd_return_90d']]

    # 2. Get ticker list ONCE and slice
    # Note: In a real scenario, we might pass the 12k list in,
    # but for this script, fetching and slicing is fine.
    all_tickers = get_all_tickers(limit=10000) # Get all 10k tickers
    batch_tickers = all_tickers[batch_start:batch_end]
    print(f"Processing {len(batch_tickers)} tickers for this batch.")

    all_buy_signals = []
    summary = {
        "total_stocks_scanned": 0,
        "stocks_with_data_errors": 0,
        "stocks_passing_setup": 0,
        "total_buy_signals_found": 0
    }

    # 3. Loop by TICKER (not by day)
    for i, ticker_info in enumerate(batch_tickers):
        ticker = ticker_info['ticker']
        print(f"  ({i+1}/{len(batch_tickers)}) Processing: {ticker}")
        
        try:
            # 4. Make API calls PER TICKER
            # API Call 1: Get Fundamentals/Details
            details = get_ticker_details(ticker)
            if not details:
                summary['stocks_with_data_errors'] += 1
                continue

            # API Call 2: Get Price History
            stock_df = get_price_history(ticker, DATA_START_DATE, DATA_END_DATE)
            if stock_df.empty or len(stock_df) < (PRE_ROLL_DAYS + POST_ROLL_DAYS):
                print(f"    Skipping {ticker}: Insufficient price data.")
                summary['stocks_with_data_errors'] += 1
                continue
            
            summary['total_stocks_scanned'] += 1

            # 5. Calculate SETUP Score (Static points)
            market_cap = details.get('market_cap', 0)
            shares = details.get('share_class_shares_outstanding', 0) # Use this field
            sic_code = details.get('sic_code', None)
            sector = get_sector_from_sic(sic_code)

            is_ultra_low_float = (shares > 0 and shares < SHARES_ULTRA_LOW_FLOAT)
            is_micro_cap = (market_cap > 0 and market_cap < MARKET_CAP_MICRO)
            is_hot_sector = sector in HOT_SECTORS

            setup_points = 0
            if is_ultra_low_float and is_micro_cap and is_hot_sector:
                setup_points = 40
                summary['stocks_passing_setup'] += 1
            else:
                # If setup fails, no need to process momentum
                continue 

            # 6. Calculate MOMENTUM Scores (Vectorized)
            # Merge with SPY data to align dates
            stock_df = pd.merge(stock_df, spy_df, on='date', how='left')
            stock_df.set_index('date', inplace=True) # Set date index for rolling ops
            stock_df.sort_index(inplace=True)
            
            # Fill any missing SPY data on non-trading days (holidays)
            stock_df['spy_close'].fillna(method='ffill', inplace=True)
            stock_df['spy_return_30d'].fillna(method='ffill', inplace=True)
            stock_df['spy_fwd_return_90d'].fillna(method='ffill', inplace=True)

            # Golden Cross (20 pts)
            stock_df['ma20'] = stock_df['close'].rolling(window=20).mean()
            stock_df['ma50'] = stock_df['close'].rolling(window=50).mean()
            stock_df['golden_cross_points'] = np.where(stock_df['ma20'] > stock_df['ma50'], 20, 0)
            
            # Strongly Outperforming (40 pts)
            stock_df['return_30d'] = stock_df['close'].pct_change(30)
            stock_df['performance_vs_spy'] = stock_df['return_30d'] - stock_df['spy_return_30d']
            stock_df['outperforming_points'] = np.where(stock_df['performance_vs_spy'] > 0.10, 40, 0)
            
            # Calculate 90-day forward return for the stock
            stock_df['fwd_return_90d'] = stock_df['close'].shift(-90) / stock_df['close'] - 1

            # 7. Apply FINAL MODEL
            stock_df['setup_points'] = setup_points # Add static setup points
            stock_df['total_score'] = stock_df['setup_points'] + stock_df['golden_cross_points'] + stock_df['outperforming_points']
            stock_df['pass_filter'] = stock_df['total_score'] >= SCORE_THRESHOLD
            
            # 8. Filter for actual scan period
            scan_period_df = stock_df.loc[SCAN_START_DATE:SCAN_END_DATE].copy()
            
            # 9. Get all "Buy" signals
            # We must handle "re-buys". A simple way is to find where pass_filter
            # becomes True after being False.
            scan_period_df['prev_pass'] = scan_period_df['pass_filter'].shift(1).fillna(False)
            buy_signals = scan_period_df[
                (scan_period_df['pass_filter'] == True) & 
                (scan_period_df['prev_pass'] == False)
            ]

            if not buy_signals.empty:
                summary['total_buy_signals_found'] += len(buy_signals)
                
                for date, row in buy_signals.iterrows():
                    all_buy_signals.append({
                        "ticker": ticker,
                        "date": date.strftime('%Y-%m-%d'), # <-- FIX: Save in YYYY-MM-DD format
                        "score": row['total_score'],
                        "setup_points": row['setup_points'],
                        "momentum_gc_pts": row['golden_cross_points'],
                        "momentum_spy_pts": row['outperforming_points'],
                        "price_at_buy": row['close'],
                        "fwd_return_90d": row['fwd_return_90d'],
                        "spy_fwd_return_90d": row['spy_fwd_return_90d'],
                        "market_cap": market_cap,
                        "shares_outstanding": shares,
                        "sector": sector
                    })

        except Exception as e:
            print(f"    [ERROR] Failed processing {ticker}: {e}")
            summary['stocks_with_data_errors'] += 1

    # 10. Generate Batch Report
    print(f"--- Batch {batch_start}-{batch_end} Complete ---")
    print(json.dumps(summary, indent=2))

    report_df = pd.DataFrame(all_buy_signals)
    report_content = f"--- Backtest Report: Batch {batch_start}-{batch_end} ---\n\n"
    report_content += f"Scan Period: {SCAN_START_DATE} to {SCAN_END_DATE}\n"
    report_content += f"Tickers Processed: {summary['total_stocks_scanned']}\n"
    report_content += f"Stocks Passing Setup: {summary['stocks_passing_setup']}\n"
    report_content += f"Data Errors/Skips: {summary['stocks_with_data_errors']}\n"
    report_content += f"Total 'BUY' Signals Generated: {summary['total_buy_signals_found']}\n\n"

    if not report_df.empty:
        report_df.dropna(subset=['fwd_return_90d', 'spy_fwd_return_90d'], inplace=True)
        
        if not report_df.empty:
            wins = report_df[report_df['fwd_return_90d'] > report_df['spy_fwd_return_90d']]
            win_rate = (len(wins) / len(report_df)) * 100
            
            supernova_hits = report_df[report_df['fwd_return_90d'] >= 5.0] # 500%+
            
            avg_gain_pct = report_df['fwd_return_90d'].mean() * 100
            avg_spy_gain_pct = report_df['spy_fwd_return_90d'].mean() * 100
            
            report_content += "--- Performance (90-Day Hold) ---\n"
            report_content += f"Win Rate (vs. SPY): {win_rate:.2f}%\n"
            report_content += f"Average Gain: {avg_gain_pct:.2f}%\n"
            report_content += f"Average SPY Gain: {avg_spy_gain_pct:.2f}%\n"
            report_content += f"Supernova Hits (500%+): {len(supernova_hits)}\n"
            report_content += f"Total False Positives (Gain < 0%): {len(report_df[report_df['fwd_return_90d'] < 0])}\n"
        else:
            report_content += "--- Performance (90-Day Hold) ---\n"
            report_content += "No signals had complete 90-day forward data to analyze.\n"
    else:
        report_content += "--- Performance (90-Day Hold) ---\n"
        report_content += "No 'BUY' signals were generated in this batch.\n"

    # 11. Save files for artifact upload
    report_filename = f"backtest_report_{batch_start}_{batch_end}.txt"
    json_filename = f"buy_signals_{batch_start}_{batch_end}.json"
    
    with open(report_filename, 'w') as f:
        f.write(report_content)
        
    report_df.to_json(json_filename, orient='records', indent=2)

    print(f"Saved {report_filename}")
    print(f"Saved {json_filename}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    BATCH_START = int(os.getenv('BATCH_START', 0))
    BATCH_END = int(os.getenv('BATCH_END', 250))
    
    run_backtest_batch(BATCH_START, BATCH_END)
