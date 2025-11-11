#!/usr/bin/env python3
"""
GEM TRADING SYSTEM - BACKTESTER (v3)

This script runs a historical backtest on a MASTER_FINGERPRINTS.json file.
It applies a tiered filtering system based on the "Golden Fingerprint"
model derived from our correlation analysis.

It is parameterized to accept an input file and an output file.

Usage:
1. Test on main data:
   python backtester.py MASTER_FINGERPRINTS.json backtest_report.txt

2. Test on 2023-2024 "holdout" data:
   python backtester.py MASTER_FINGERPRINTS_TEST.json backtest_report_TEST.txt
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

def flatten_fingerprint(fp: Dict) -> Optional[Dict]:
    """Flattens the complex JSON structure into a single-level dict for pandas."""
    try:
        profile = fp.get('1_profile', {})
        tech = fp.get('2_technicals', {})
        funda = fp.get('3_fundamentals', {})
        rel_str = fp.get('4_relative_strength', {})
        short = fp.get('8_short_interest', {})
        sec = fp.get('sec_data', {})
        insider = sec.get('insider_trades', {})
        insti = sec.get('institutional', {})

        # --- Your Cash Runway Hypothesis ---
        cash = funda.get('cash', 0)
        op_ex = funda.get('operating_expenses', 0)
        
        # Calculate quarterly burn rate. Use abs() because op_ex is negative.
        quarterly_burn = abs(op_ex) if op_ex != 0 else 0
        
        cash_runway_months = 0
        if quarterly_burn > 0:
            cash_runway_months = (cash / quarterly_burn) * 3  # Convert quarterly burn to monthly
        
        has_6mo_cash = cash_runway_months > 6
        # ---
        
        # --- Your Debt Hypothesis ---
        debt = funda.get('total_debt', 0)
        assets = funda.get('total_assets', 0)
        debt_to_asset_ratio = (debt / assets) if assets > 0 else 0
        # ---

        flat = {
            'ticker': fp.get('ticker'),
            'catalyst_date': fp.get('catalyst_date'),
            'gain_pct': fp.get('explosion_metrics', {}).get('gain_pct', 0),
            
            # --- TIER 3 FILTERS (SETUP) ---
            'is_ultra_low_float': profile.get('is_ultra_low_float', False),
            'sector': profile.get('sector', 'UNKNOWN'),
            
            # --- TIER 2 FILTERS (MOMENTUM) ---
            'is_golden_cross': tech.get('is_golden_cross', False),
            'strongly_outperforming': rel_str.get('strongly_outperforming', False),
            
            # --- TIER 1 FILTERS (CATALYST/FUEL) ---
            'is_squeeze_setup': short.get('is_squeeze_setup', False),
            'is_heavily_shorted': short.get('is_heavily_shorted', False),
            'any_insider_buys_30d': insider.get('any_insider_buys_30d', False),
            'insider_buying_surge': insider.get('insider_buying_surge', False),
            'new_activist_filing_90d': insti.get('new_activist_filing_90d', False),
            
            # --- Other Data for Correlation ---
            'gain_pct_group': '>1000%' if fp.get('explosion_metrics', {}).get('gain_pct', 0) > 1000 else '>500%' if fp.get('explosion_metrics', {}).get('gain_pct', 0) > 500 else '<500%',
            'is_micro_cap': profile.get('is_micro_cap', False),
            'is_low_float': profile.get('is_low_float', False),
            'bb_squeeze': tech.get('bb_squeeze', {}).get('is_squeezing', False),
            'volume_drying': tech.get('volume_trend', {}).get('is_drying', False),
            'consolidation': tech.get('consolidation', {}).get('is_consolidating', False),
            'rsi': tech.get('rsi', 50),
            'volatility_rank': tech.get('volatility_rank', 50),
            'revenue_accel': funda.get('is_accelerating', False),
            'turning_profitable': funda.get('turning_profitable', False),
            'has_6mo_cash': has_6mo_cash,
            'cash_runway_months': cash_runway_months,
            'debt_to_asset_ratio': debt_to_asset_ratio,
            'relative_strength': rel_str.get('relative_strength', 0),
            'return_7d': fp.get('6_price_patterns', {}).get('return_7d', 0),
            'return_30d': fp.get('6_price_patterns', {}).get('return_30d', 0),
            'return_60d': fp.get('6_price_patterns', {}).get('return_60d', 0),
            'return_90d': fp.get('6_price_patterns', {}).get('return_90d', 0),
        }
        return flat
    except Exception as e:
        print(f"[Flatten Error] Ticker {fp.get('ticker')}: {e}")
        return None

def load_and_clean_data(master_file: str) -> pd.DataFrame:
    """Loads the master JSON, filters out noise, and flattens for analysis."""
    print(f"Loading raw fingerprints from {master_file} for filtering...")
    with open(master_file, 'r') as f:
        data = json.load(f)
    
    fingerprints = data.get('fingerprints', [])
    print(f"Loaded {len(fingerprints)} raw fingerprints.")
    
    clean_fingerprints = []
    filter_counts = {
        'error': 0,
        'insufficient_data': 0,
        'etf_fund': 0,
        'warrant': 0,
        'spac': 0
    }

    for fp in fingerprints:
        if 'error' in fp:
            filter_counts['error'] += 1
            continue
        if fp.get('2_technicals', {}).get('insufficient_data', False):
            filter_counts['insufficient_data'] += 1
            continue
        
        sic = fp.get('1_profile', {}).get('sic_description', '').lower()
        name = fp.get('1_profile', {}).get('name', '').lower()
        
        if 'etf' in sic or 'fund' in sic:
            filter_counts['etf_fund'] += 1
            continue
        if 'warrant' in name:
            filter_counts['warrant'] += 1
            continue
        if 'blank checks' in sic:
            filter_counts['spac'] += 1
            continue
            
        flat_fp = flatten_fingerprint(fp)
        if flat_fp:
            clean_fingerprints.append(flat_fp)

    print(f"Filtered down to {len(clean_fingerprints)} clean company fingerprints.")
    print("Filtered-out breakdown:")
    for key, count in filter_counts.items():
        print(f"  - {key}: {count}")
    
    # Save the clean data for review
    clean_filename = "CLEAN_FINGERPRINTS_FOR_BACKTEST.json"
    with open(clean_filename, 'w') as f:
        json.dump(clean_fingerprints, f, indent=2)
    print(f"Saved clean, filtered data to {clean_filename}\n")
    
    return pd.DataFrame(clean_fingerprints)

def analyze_performance(df: pd.DataFrame, title: str, report_file: TextIO):
    """Calculates and prints performance metrics for a given DataFrame."""
    if df.empty:
        report_file.write(f"--- {title} ---\n")
        report_file.write("  No stocks matched this filter.\n\n")
        return
        
    total_stocks = len(df)
    avg_gain = df['gain_pct'].mean()
    median_gain = df['gain_pct'].median()
    winners = (df['gain_pct'] > 100).sum()
    big_winners = (df['gain_pct'] > 500).sum()
    mega_winners = (df['gain_pct'] > 1000).sum()
    
    report_file.write(f"--- {title} ---\n")
    report_file.write(f"  Total Stocks:        {total_stocks}\n")
    report_file.write(f"  Average Gain:        {avg_gain:,.0f}%\n")
    report_file.write(f"  Median Gain:         {median_gain:,.0f}%\n")
    report_file.write(f"  Winners (> 100%):    {winners} (Hit Rate: {winners/total_stocks:.1%})\n")
    report_file.write(f"  Big Winners (> 500%): {big_winners} (Hit Rate: {big_winners/total_stocks:.1%})\n")
    report_file.write(f"  Mega Winners (> 1000%): {mega_winners} (Hit Rate: {mega_winners/total_stocks:.1%})\n\n")
    
    report_file.write("  Stocks that matched this filter:\n")
    report_file.write("  Ticker | Gain %   | Catalyst Date\n")
    report_file.write("  ----------------------------------\n")
    
    # Sort by gain for the report
    df_sorted = df.sort_values(by='gain_pct', ascending=False)
    for _, row in df_sorted.iterrows():
        report_file.write(f"  {row['ticker']:<5} | {row['gain_pct']:>8,.0f}% | {row['catalyst_date']}\n")
    report_file.write("\n")

def main():
    if len(sys.argv) < 3:
        print("Usage: python backtester.py <input_master_file> <output_report_file>")
        print("Example: python backtester.py MASTER_FINGERPRINTS.json backtest_report.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"❌ ERROR: Input file '{input_file}' not found.")
        sys.exit(1)

    # Load and clean the data
    df_all_clean = load_and_clean_data(input_file)
    
    if df_all_clean.empty:
        print("No clean data to analyze. Exiting.")
        return

    # --- Define Our "Golden Fingerprint" Filters ---

    # Tier 3: The Setup (ULF + Hot Sector)
    query_tier_3 = (
        "is_ultra_low_float == True & "
        "(`sector` == 'BIOTECH/HEALTH' | `sector` == 'TECH' | `sector` == 'ENERGY/MINING')"
    )

    # Tier 2: The Momentum (Tier 3 + Momentum)
    query_tier_2 = (
        f"({query_tier_3}) & "
        "(is_golden_cross == True | strongly_outperforming == True)"
    )

    # Tier 1: The "Golden" (Tier 2 + Catalyst/Fuel)
    query_tier_1 = (
        f"({query_tier_2}) & "
        "(is_squeeze_setup == True | new_activist_filing_90d == True | any_insider_buys_30d == True)"
    )
    
    # --- Run the Backtest ---
    
    # Create DataFrames for each tier
    df_tier_3 = df_all_clean.query(query_tier_3)
    df_tier_2 = df_all_clean.query(query_tier_2)
    df_tier_1 = df_all_clean.query(query_tier_1)
    
    # Open the report file and write the analysis
    with open(output_file, 'w') as report_file:
        report_file.write("="*60 + "\n")
        report_file.write("GEM TRADING SYSTEM - BACKTEST REPORT\n")
        report_file.write(f"Generated at: {datetime.now().isoformat()}\n")
        report_file.write(f"Based on data from: {input_file}\n")
        report_file.write("="*60 + "\n\n")

        # Analyze Baseline (all clean stocks)
        analyze_performance(df_all_clean, "BASELINE (All Clean Stocks)", report_file)
        
        # Analyze Tier 3
        analyze_performance(df_tier_3, "TIER 3 (Filter: ULF + Hot Sector)", report_file)
        
        # Analyze Tier 2
        analyze_performance(df_tier_2, "TIER 2 (Filter: TIER 3 + Momentum)", report_file)
        
        # Analyze Tier 1
        analyze_performance(df_tier_1, "TIER 1 'Golden' (Filter: TIER 2 + Squeeze/Activist/Insider)", report_file)

        # --- Final Summary ---
        baseline_median = df_all_clean['gain_pct'].median()
        tier_1_median = df_tier_1['gain_pct'].median() if not df_tier_1.empty else 0
        
        baseline_avg = df_all_clean['gain_pct'].mean()
        tier_1_avg = df_tier_1['gain_pct'].mean() if not df_tier_1.empty else 0

        baseline_mega_rate = (df_all_clean['gain_pct'] > 1000).sum() / len(df_all_clean)
        tier_1_mega_rate = (df_tier_1['gain_pct'] > 1000).sum() / len(df_tier_1) if not df_tier_1.empty else 0

        report_file.write("="*60 + "\n")
        report_file.write("BACKTEST SUMMARY\n")
        report_file.write("="*60 + "\n")
        report_file.write("Applying our 'Golden Fingerprint' (Tier 1) filters had the following effect:\n")
        report_file.write(f"  - Stocks Found: {len(df_tier_1)} (down from {len(df_all_clean)})\n")
        report_file.write(f"  - Average Gain: {tier_1_avg:,.0f}% (vs. Baseline of {baseline_avg:,.0f}%)\n")
        report_file.write(f"  - Median Gain:  {tier_1_median:,.0f}% (vs. Baseline of {baseline_median:,.0f}%)\n")
        report_file.write(f"  - Mega-Winner Rate (>1000%): {tier_1_mega_rate:.1%} (vs. Baseline of {baseline_mega_rate:.1%})\n")
        report_file.write("="*60 + "\n")

    print(f"Backtest complete. Report saved to {output_file}")

if __name__ == "__main__":
    main()
