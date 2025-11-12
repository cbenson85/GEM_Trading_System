import json
import os
import pandas as pd
from datetime import datetime

REPORT_DIR = "backtest_results"
FINAL_REPORT_FILE = "HYBRID_BACKTEST_FINAL_REPORT.txt"

# Read from environment variables set by the workflow
SCAN_START_DATE = os.environ.get('SCAN_START_DATE', 'N/A')
SCAN_END_DATE = os.environ.get('SCAN_END_DATE', 'N/A')

def collect_and_summarize():
    """
    Finds all 'batch_*.json' files in REPORT_DIR, combines them,
    and generates a final, human-readable summary report.
    """
    all_signals = []
    total_api_calls = 0
    
    if not os.path.exists(REPORT_DIR):
        print(f"Error: Report directory '{REPORT_DIR}' not found.")
        return

    print(f"Scanning for batch reports in {REPORT_DIR}...")
    batch_files = [f for f in os.listdir(REPORT_DIR) if f.startswith('batch_') and f.endswith('.json')]
    
    if not batch_files:
        print("No batch reports found.")
        # Create an empty report so the workflow doesn't fail
        with open(FINAL_REPORT_FILE, 'w') as f:
            f.write("="*80 + "\n")
            f.write("GEM TRADING SYSTEM - HYBRID BACKTEST FINAL REPORT\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n")
            f.write(f"Data Range: {SCAN_START_DATE} to {SCAN_END_DATE}\n")
            f.write("="*80 + "\n\n")
            f.write("--- SUMMARY --- \n")
            f.write("No batch report files were found. No signals were generated.\n")
        return
        
    print(f"Found {len(batch_files)} batch reports. Parsing...")

    # --- 1. Collect all data from batch files ---
    for filename in batch_files:
        filepath = os.path.join(REPORT_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                all_signals.extend(data.get('signals', []))
                total_api_calls += data.get('total_api_calls', 0)
        except Exception as e:
            print(f"Warning: Could not parse {filename}. Error: {e}")

    print(f"Parsing complete. Found {len(all_signals)} total signals.")
    
    if not all_signals:
        print("No signals found in any batch. Report will be minimal.")
        with open(FINAL_REPORT_FILE, 'w') as f:
            f.write("="*80 + "\n")
            f.write("GEM TRADING SYSTEM - HYBRID BACKTEST FINAL REPORT\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n")
            f.write(f"Data Range: {SCAN_START_DATE} to {SCAN_END_DATE}\n")
            f.write("="*80 + "\n\n")
            f.write("--- SUMMARY --- \n")
            f.write("No signals were found matching the criteria in the specified date range.\n")
            f.write(f"Total API Calls: {total_api_calls:,}\n")
        return

    # --- 2. Create DataFrame for analysis ---
    df = pd.DataFrame(all_signals)
    df['gain_pct_90d'] = pd.to_numeric(df['gain_pct_90d'], errors='coerce').fillna(0)

    # --- 3. Calculate Key Metrics ---
    avg_gain = df['gain_pct_90d'].mean()
    median_gain = df['gain_pct_90d'].median()
    
    winners = df[df['gain_pct_90d'] > 25] # > 25% gain
    losers = df[df['gain_pct_90d'] <= 25]
    
    win_rate = (len(winners) / len(df)) * 100
    
    avg_win_gain = winners['gain_pct_90d'].mean() if not winners.empty else 0
    avg_loss_pct = losers['gain_pct_90d'].mean() if not losers.empty else 0
    
    big_winners = df[df['gain_pct_90d'] > 500]
    mega_winners = df[df['gain_pct_90d'] > 1000]

    # --- 4. Write the Final Report ---
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
        f.write(f"  Total API Calls:       {total_api_calls:,}\n")
        f.write("\n" + "="*80 + "\n")

        f.write("\n--- ALL SIGNALS LOG (Sorted by Gain) --- \n")
        f.write("Scan Date  | Ticker | Score | 90-Day Gain | Reason\n")
        f.write("--------------------------------------------------------------------------\n")
        
        df_sorted = df.sort_values(by='gain_pct_90d', ascending=False)
        for _, row in df_sorted.iterrows():
            f.write(f"{row['scan_date']} | {row['ticker']:<6} | {row['gem_score']:<5} | {row['gain_pct_90d']:>11.2f}% | {row['reason']}\n")

    print(f"Successfully generated final report: {FINAL_REPORT_FILE}")

if __name__ == "__main__":
    collect_and_summarize()
