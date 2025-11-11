import json
import pandas as pd
import numpy as np
import os
from typing import Dict, List, TextIO
from datetime import datetime # <-- FIX: Added the missing import

MASTER_FILE = 'MASTER_FINGERPRINTS.json'
CLEAN_FILE = 'CLEAN_FINGERPRINTS_FOR_BACKTEST.json'
REPORT_FILE = 'backtest_report.txt' # <-- NEW: Output file for our report

def filter_noisy_data(fingerprints: List[Dict], report_file: TextIO) -> List[Dict]:
    """
    Filters out ETFs, Warrants, SPACs, and entries with 
    insufficient data to create a clean list of companies for analysis.
    """
    clean_fingerprints = []
    report_file.write(f"Loading {len(fingerprints)} raw fingerprints for filtering...\n")
    
    filtered_out = {
        'error': 0,
        'insufficient_data': 0,
        'etf_fund': 0,
        'warrant': 0,
        'spac': 0
    }
    
    for fp in fingerprints:
        if 'error' in fp:
            filtered_out['error'] += 1
            continue
            
        profile = fp.get('1_profile', {})
        technicals = fp.get('2_technicals', {})
        
        if not profile.get('has_data') or technicals.get('insufficient_data'):
            filtered_out['insufficient_data'] += 1
            continue
            
        name = profile.get('name', '').lower()
        sic = profile.get('sic_description', '').lower()
        sector = profile.get('sector', 'UNKNOWN')
        
        if sector == 'ETF' or 'etf' in name or 'fund' in name:
            filtered_out['etf_fund'] += 1
            continue
        if 'warrant' in name or '.ws' in fp['ticker'].lower():
            filtered_out['warrant'] += 1
            continue
        if sector == 'SPAC' or 'blank checks' in sic:
            filtered_out['spac'] += 1
            continue
        
        clean_fingerprints.append(fp)
        
    report_file.write(f"Filtered down to {len(clean_fingerprints)} clean company fingerprints.\n")
    report_file.write("Filtered-out breakdown:\n")
    for reason, count in filtered_out.items():
        report_file.write(f"  - {reason}: {count}\n")
    
    # Save the clean list for inspection
    with open(CLEAN_FILE, 'w') as f:
        json.dump(clean_fingerprints, f, indent=2)
    report_file.write(f"Saved clean, filtered data to {CLEAN_FILE}\n")
    
    return clean_fingerprints

def flatten_fingerprint(fp: Dict) -> Dict:
    """
    Flattens the nested JSON structure into a single-level dictionary
    suitable for a Pandas DataFrame, including all our v4 metrics.
    """
    profile = fp.get('1_profile', {})
    tech = fp.get('2_technicals', {})
    funda = fp.get('3_fundamentals', {})
    rel_str = fp.get('4_relative_strength', {})
    short = fp.get('8_short_interest', {})
    sec = fp.get('sec_data', {})
    insider = sec.get('insider_trades', {}) if sec else {}
    institutional = sec.get('institutional', {}) if sec else {}
    
    # Calculate Cash Runway
    cash = funda.get('cash', 0)
    expenses_quarterly = abs(funda.get('operating_expenses', 0))
    cash_runway_months = 0
    if expenses_quarterly > 0:
        burn_rate_monthly = expenses_quarterly / 3
        if burn_rate_monthly > 0:
            cash_runway_months = cash / burn_rate_monthly
            
    has_6mo_cash = cash_runway_months > 6

    return {
        'ticker': fp.get('ticker'),
        'catalyst_date': fp.get('catalyst_date'),
        'gain_pct': fp.get('explosion_metrics', {}).get('gain_pct'),
        
        'is_micro_cap': profile.get('is_micro_cap'),
        'is_ultra_low_float': profile.get('is_ultra_low_float'),
        'sector': profile.get('sector'),
        
        'bb_squeeze': tech.get('bb_squeeze', {}).get('is_squeezing'),
        'volume_drying': tech.get('volume_trend', {}).get('is_drying'),
        'is_golden_cross': tech.get('is_golden_cross'),
        
        'has_6mo_cash': has_6mo_cash,
        'debt_to_asset_ratio': funda.get('debt_to_asset_ratio'),
        
        'strongly_outperforming': rel_str.get('strongly_outperforming'),
        
        'is_squeeze_setup': short.get('is_squeeze_setup'),
        'is_heavily_shorted': short.get('is_heavily_shorted'),
        
        'any_insider_buys_30d': insider.get('any_insider_buys_30d'),
        'insider_buying_surge': insider.get('insider_buying_surge'),
        'new_activist_filing_90d': institutional.get('new_activist_filing_90d')
    }

def analyze_performance(df: pd.DataFrame, label: str, report_file: TextIO):
    """Prints a standardized performance report for a given DataFrame."""
    
    report_file.write(f"\n{label}\n")
    report_file.write("-------------------------------------------------\n")

    if df.empty:
        report_file.write("  No stocks matched this filter.\n")
        print(f"No stocks matched filter: {label}")
        return {
            'total': 0, 'avg_gain': 0, 'median_gain': 0, 
            'hit_rate_100': 0, 'hit_rate_1000': 0
        }

    total_stocks = len(df)
    
    # Calculate performance metrics
    avg_gain = df['gain_pct'].mean()
    median_gain = df['gain_pct'].median()
    
    winners_100 = df[df['gain_pct'] > 100]
    winners_500 = df[df['gain_pct'] > 500]
    winners_1000 = df[df['gain_pct'] > 1000]
    
    hit_rate_100 = (len(winners_100) / total_stocks) * 100
    hit_rate_500 = (len(winners_500) / total_stocks) * 100
    hit_rate_1000 = (len(winners_1000) / total_stocks) * 100

    # --- Write Summary to Report File ---
    report_file.write(f"  Total Stocks:         {total_stocks}\n")
    report_file.write(f"  Average Gain:         {avg_gain:,.0f}%\n")
    report_file.write(f"  Median Gain:          {median_gain:,.0f}%\n")
    report_file.write(f"  Winners (> 100%):     {len(winners_100)} (Hit Rate: {hit_rate_100:.1f}%)\n")
    report_file.write(f"  Big Winners (> 500%): {len(winners_500)} (Hit Rate: {hit_rate_500:.1f}%)\n")
    report_file.write(f"  Mega Winners (> 1000%): {len(winners_1000)} (Hit Rate: {hit_rate_1000:.1f}%)\n")
    
    # --- NEW: Write individual stocks to file ---
    report_file.write("\n  Stocks that matched this filter:\n")
    report_file.write("  Ticker | Gain %   | Catalyst Date\n")
    report_file.write("  ----------------------------------\n")
    
    # Sort by gain to see our winners (and losers)
    sorted_df = df.sort_values(by='gain_pct', ascending=False)
    
    for index, row in sorted_df.iterrows():
        report_file.write(f"  {row['ticker']:<6} | {row['gain_pct']:>8,.0f}% | {row['catalyst_date']}\n")
        
    print(f"Analyzed {label}: Found {total_stocks} stocks. Avg Gain: {avg_gain:,.0f}%")
    
    return {
        'total': total_stocks,
        'avg_gain': avg_gain,
        'median_gain': median_gain,
        'hit_rate_100': hit_rate_100,
        'hit_rate_1000': hit_rate_1000
    }

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"❌ ERROR: {MASTER_FILE} not found!")
        print("Please run the 'Full Data Pipeline' workflow first to generate this file.")
        return
        
    with open(MASTER_FILE, 'r') as f:
        master_data = json.load(f)
        
    # Open the report file to write to
    with open(REPORT_FILE, 'w') as report_file:
        
        report_file.write("="*60 + "\n")
        report_file.write("GEM TRADING SYSTEM - BACKTEST REPORT\n")
        report_file.write(f"Generated at: {datetime.now().isoformat()}\n")
        report_file.write("="*60 + "\n")

        # 1. Clean the data
        clean_fingerprints = filter_noisy_data(master_data.get('fingerprints', []), report_file)
        
        # 2. Flatten for Pandas
        flat_data = [flatten_fingerprint(fp) for fp in clean_fingerprints]
        df_all_clean = pd.DataFrame(flat_data)
        
        # 3. One-hot encode the 'sector' column so we can filter on it
        sector_dummies = pd.get_dummies(df_all_clean['sector'], prefix='sector')
        df_all_clean = pd.concat([df_all_clean, sector_dummies], axis=1)
        
        # 4. Define our "Golden Fingerprint" Tiers for backtesting
        
        # --- Tier 3: The Setup (Our Base Filter) ---
        # --- FIX: Added backticks `` around names with special chars ---
        query_tier_3 = "is_ultra_low_float == True and (`sector_BIOTECH/HEALTH` == True or `sector_ENERGY/MINING` == True or sector_TECH == True)"
        df_tier_3 = df_all_clean.query(query_tier_3)

        # --- Tier 2: Setup + Momentum (The "Heating Up" Filter) ---
        query_tier_2 = "is_golden_cross == True or strongly_outperforming == True"
        df_tier_2 = df_tier_3.query(query_tier_2)

        # --- Tier 1: Setup + Momentum + "Squeeze Fuel" (The "Golden" Filter) ---
        query_tier_1 = "is_squeeze_setup == True or new_activist_filing_90d == True or any_insider_buys_30d == True"
        df_tier_1 = df_tier_2.query(query_tier_1)

        # 5. Run and print the final performance report
        report_file.write("\n" + "="*60 + "\n")
        report_file.write("BACKTEST PERFORMANCE REPORT\n")
        report_file.write("="*60 + "\n")

        stats_baseline = analyze_performance(df_all_clean, "--- BASELINE (All Clean Stocks) ---", report_file)
        stats_tier_3 = analyze_performance(df_tier_3, f"--- TIER 3 (Filter: ULF + Hot Sector) ---", report_file)
        stats_tier_2 = analyze_performance(df_tier_2, f"--- TIER 2 (Filter: TIER 3 + Momentum) ---", report_file)
        stats_tier_1 = analyze_performance(df_tier_1, f"--- TIER 1 'Golden' (Filter: TIER 2 + Squeeze/Activist/Insider) ---", report_file)

        # 6. Write final summary to the report
        report_file.write("\n\n" + "="*60 + "\n")
        report_file.write("BACKTEST SUMMARY\n")
        report_file.write("="*60 + "\n")
        report_file.write(f"Applying our 'Golden Fingerprint' filters had the following effect:\n")
        report_file.write(f"  - Stocks Found: {stats_tier_1['total']} (down from {stats_baseline['total']})\n")
        report_file.write(f"  - Average Gain: {stats_tier_1['avg_gain']:,.0f}% (vs. Baseline of {stats_baseline['avg_gain']:,.0f}%)\n")
        report_file.write(f"  - Median Gain:  {stats_tier_1['median_gain']:,.0f}% (vs. Baseline of {stats_baseline['median_gain']:,.0f}%)\n")
        report_file.write(f"  - Hit Rate (>100%): {stats_tier_1['hit_rate_100']:.1f}% (vs. Baseline of {stats_baseline['hit_rate_100']:.1f}%)\n")
        report_file.write(f"  - Mega-Winner Rate (>1000%): {stats_tier_1['hit_rate_1000']:.1f}% (vs. Baseline of {stats_baseline['hit_rate_1000']:.1f}%)\n")
    
    print(f"\n\n✅ Backtest complete. Full report saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()
