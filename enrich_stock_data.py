#!/usr/bin/env python3
"""
GEM TRADING SYSTEM - POST-PROCESSOR & ENRICHER (v4)

Fixes bugs from v3 and implements smarter analysis.
1.  FIXED: `get_sec_filings` now uses correct `form_type` param.
2.  CHANGED: Now *measures* `bb_squeeze_value` instead of filtering.
3.  ADDED: Report now analyzes performance by squeeze *quantiles*.
"""

import os
import json
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import numpy as np

# === CONFIGURATION ===
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    raise ValueError("POLYGON_API_KEY environment variable not set.")

POLYGON_BASE_URL = "https://api.polygon.io"
INPUT_FILE = "FINAL_buy_signals.json"
OUTPUT_FILE = "FINAL_ENRICHED_signals.json"
OUTPUT_REPORT = "FINAL_ENRICHED_report.txt"

# Filter thresholds to test
VOLUME_SPIKE_RATIO = 10.0  # 10x average volume

# === API FUNCTIONS ===

def fetch_with_retry(url: str, params: dict = None, retries: int = 5, backoff_factor: float = 0.5) -> Optional[dict]:
    """Fetches from Polygon API with exponential backoff retry logic."""
    headers = {"Authorization": f"Bearer {POLYGON_API_KEY}"}
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 404: return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if i == retries - 1:
                print(f"    [ERROR] API call failed after {retries} retries: {e}")
                return None
            time.sleep(backoff_factor * (2 ** i))
    return None

def get_signal_context(ticker: str, signal_date_str: str) -> dict:
    """
    Gets rich context data *leading up to* the signal date.
    Calculates:
    1.  Bollinger Band Squeeze value (on day *before* signal)
    2.  Volume Spike ratio (on signal day vs. 20-day avg)
    """
    signal_date = pd.to_datetime(signal_date_str)
    # Need 20 days prior for BB/Vol, plus the signal day
    start_date = (signal_date - pd.DateOffset(days=45)).strftime('%Y-%m-%d') 
    end_date = signal_date.strftime('%Y-%m-%d') # Force YYYY-MM-DD format

    url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {"adjusted": "true", "sort": "asc", "limit": 500, "apiKey": POLYGON_API_KEY}
    
    data = fetch_with_retry(url, params)
    
    if not data or not data.get("results") or len(data.get("results", [])) < 21:
        return {"bb_squeeze_value": None, "volume_spike_ratio": None} # Not enough data

    df = pd.DataFrame(data["results"])
    df['date'] = pd.to_datetime(df['t'], unit='ms')
    df = df.set_index('date')
    
    # 1. Calculate Bollinger Bands (20-day)
    df['middle_band'] = df['c'].rolling(window=20).mean()
    df['std_dev'] = df['c'].rolling(window=20).std()
    df['upper_band'] = df['middle_band'] + (df['std_dev'] * 2)
    df['lower_band'] = df['middle_band'] - (df['std_dev'] * 2)
    
    # The "Squeeze" is the width of the bands as a % of price
    df['bb_squeeze_value'] = (df['upper_band'] - df['lower_band']) / df['middle_band']
    
    # 2. Calculate Volume Spike
    df['avg_20d_vol'] = df['v'].rolling(window=20).mean().shift(1) # Avg *before* today
    df['volume_spike_ratio'] = df['v'] / df['avg_20d_vol']
    
    # Get the data for the actual signal date
    try:
        signal_row = df.loc[signal_date_str]
    except KeyError:
        if not df.empty:
            signal_row = df.iloc[-1]
        else:
            return {"bb_squeeze_value": None, "volume_spike_ratio": None}

    # Get the squeeze value from the day *before* the signal
    bb_squeeze_value = None
    try:
        prev_day_index = df.index.get_loc(signal_date_str) - 1
        if prev_day_index >= 0:
            bb_squeeze_value = df.iloc[prev_day_index]['bb_squeeze_value']
    except Exception:
        pass # Will be None if not found

    return {
        "bb_squeeze_value": bb_squeeze_value,
        "volume_spike_ratio": signal_row['volume_spike_ratio']
    }

def get_sec_filings(ticker: str, signal_date_str: str) -> bool:
    """Checks for 8-K, 13D/G filings 3 days prior to signal."""
    signal_date = pd.to_datetime(signal_date_str)
    start_date = (signal_date - pd.DateOffset(days=5)).strftime('%Y-%m-%d')
    end_date = signal_date.strftime('%Y-%m-%d') # Force YYYY-MM-DD format
    
    url = f"{POLYGON_BASE_URL}/v2/reference/filings"
    
    # --- THIS IS THE BUG FIX ---
    # The parameter is 'form_type', NOT 'form_type.in'
    params = {
        "ticker": ticker,
        "filing_date.gte": start_date,
        "filing_date.lte": end_date,
        "form_type": "8-K,13D,13G", # Catalyst filings
        "limit": 10,
        "apiKey": POLYGON_API_KEY
    }
    data = fetch_with_retry(url, params)
    return bool(data and data.get("results"))

# === MAIN PROCESSING LOGIC ===

def run_enrichment():
    print("--- Starting Post-Processor Enrichment (v4) ---")
    print(f"Loading '{INPUT_FILE}'...")
    try:
        df = pd.read_json(INPUT_FILE)
    except Exception as e:
        print(f"ERROR: Could not read '{INPUT_FILE}'. Error: {e}")
        with open(OUTPUT_REPORT, 'w') as f: f.write(f"Post-processing failed: Could not read {INPUT_FILE}.\n")
        with open(OUTPUT_FILE, 'w') as f: json.dump([], f)
        return

    if df.empty:
        print("No signals to enrich. Exiting.")
        with open(OUTPUT_REPORT, 'w') as f: f.write("Post-processing: No signals found to enrich.\n")
        with open(OUTPUT_FILE, 'w') as f: json.dump([], f)
        return
        
    print(f"Found {len(df)} signals to enrich...")
    enriched_data = []
    
    for i, signal in df.iterrows():
        ticker = signal["ticker"]
        date = signal["date"]
        
        if (i + 1) % 50 == 0:
            print(f"  Processing signal {i+1}/{len(df)} ({ticker} on {date})...")
            
        context = get_signal_context(ticker, date)
        has_catalyst_filing = get_sec_filings(ticker, date)
        
        signal_dict = signal.to_dict()
        signal_dict.update(context)
        signal_dict["has_catalyst_filing"] = has_catalyst_filing
        
        enriched_data.append(signal_dict)

    print("Enrichment complete. Analyzing filtered results...")

    if not enriched_data:
        print("No signals were enriched.")
        return

    enriched_df = pd.DataFrame(enriched_data)
    # Clean data for analysis
    for col in ['fwd_return_90d', 'bb_squeeze_value', 'volume_spike_ratio']:
        enriched_df[col] = pd.to_numeric(enriched_df[col], errors='coerce')

    # --- Generate Report ---
    report_content = "--- POST-PROCESSOR ENRICHMENT REPORT (v4) ---\n\n"
    report_content += "Testing filters and analyzing squeeze quantiles.\n"
    report_content += f"Timestamp: {datetime.now().isoformat()}\n"

    # Baseline (all signals with valid 90-day data)
    baseline_df = enriched_df.dropna(subset=['fwd_return_90d'])
    report_content += get_performance_stats(baseline_df, "Baseline (All Signals w/ 90d Data)")

    # --- Test Filters ---
    
    # 1. Volume Spike Filter (from v3)
    vol_filter_df = baseline_df[baseline_df["volume_spike_ratio"] >= VOLUME_SPIKE_RATIO]
    report_content += get_performance_stats(vol_filter_df, f"FILTER: Volume Spike (>= {VOLUME_SPIKE_RATIO}x)")

    # 2. Catalyst Filter (FIXED)
    catalyst_df = baseline_df[baseline_df["has_catalyst_filing"] == True]
    report_content += get_performance_stats(catalyst_df, "FILTER: Catalyst (8-K or 13D Filing)")
    
    # --- Analyze BB Squeeze Quantiles ---
    
    # First, get all signals that *have* a squeeze value
    squeeze_df = baseline_df.dropna(subset=['bb_squeeze_value'])
    if not squeeze_df.empty:
        # Calculate quantiles (q=0 is min, q=0.25 is 1st quartile, etc.)
        # A *lower* value means a *tighter* squeeze
        q_tightest = squeeze_df['bb_squeeze_value'].quantile(0.25)
        q_loosest = squeeze_df['bb_squeeze_value'].quantile(0.75)
        
        tight_squeeze_df = squeeze_df[squeeze_df['bb_squeeze_value'] <= q_tightest]
        loose_squeeze_df = squeeze_df[squeeze_df['bb_squeeze_value'] >= q_loosest]
        
        report_content += get_performance_stats(squeeze_df, "All Signals with BB Squeeze Data")
        report_content += get_performance_stats(tight_squeeze_df, f"SQUEEZE (Top 25% Tightest, <= {q_tightest:.4f})")
        report_content += get_performance_stats(loose_squeeze_df, f"SQUEEZE (Bottom 25% Loosest, >= {q_loosest:.4f})")
        
    else:
        report_content += "\n--- BB Squeeze Analysis ---"
        report_content += "  No signals had valid BB Squeeze data to analyze.\n"

    # --- Test "Tier 3" Combo ---
    combo_df = baseline_df[
        (baseline_df["has_catalyst_filing"] == True) &
        (baseline_df["bb_squeeze_value"].notna()) &
        (baseline_df["bb_squeeze_value"] <= baseline_df["bb_squeeze_value"].quantile(0.50)) # Tighter half
    ]
    report_content += get_performance_stats(combo_df, "TIER 3 COMBO: Catalyst + Top 50% Squeeze")

    print(report_content)

    # Save files
    with open(OUTPUT_REPORT, 'w') as f:
        f.write(report_content)
        
    enriched_df.to_json(OUTPUT_FILE, orient='records', indent=2)
    print(f"Saved enriched report to '{OUTPUT_REPORT}'")
    print(f"Saved enriched data to '{OUTPUT_FILE}'")

def get_performance_stats(df: pd.DataFrame, title: str) -> str:
    """Helper function to generate performance stats for a DataFrame slice."""
    content = f"\n--- {title} ---\n"
    
    total_signals = len(df)
    
    if total_signals == 0:
        content += "  Total Signals: 0\n"
        content += "  No signals matched this filter.\n"
        return content

    avg_gain = df['fwd_return_90d'].mean() * 100
    median_gain = df['fwd_return_90d'].median() * 100
    win_rate_vs_0 = (len(df[df['fwd_return_90d'] > 0]) / total_signals) * 100
    supernovas = len(df[df['fwd_return_90d'] >= 5.0]) # 500%+

    content_template = (
        f"  Total Signals: {total_signals}\n"
        f"  Win Rate (vs 0%): {win_rate_vs_0:.2f}%\n"
        f"  Average Gain: {avg_gain:.2f}%\n"
        f"  Median Gain: {median_gain:.2f}%\n"
        f"  Supernovas (500%+): {supernovas}\n"
    )
    content += content_template
    
    return content

if __name__ == "__main__":
    run_enrichment()
