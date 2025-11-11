import json
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List
import os

MASTER_FILE = 'MASTER_FINGERPRINTS.json'
CLEAN_FILE = 'CLEAN_FINGERPRINTS.json'
HEATMAP_FILE = 'correlation_heatmap.png'

def filter_noisy_data(fingerprints: List[Dict]) -> List[Dict]:
    """
    Filters out ETFs, Warrants, SPACs, and entries with 
    insufficient data to create a clean list of companies for analysis.
    """
    clean_fingerprints = []
    print(f"Loading {len(fingerprints)} raw fingerprints...")
    
    for fp in fingerprints:
        if 'error' in fp:
            continue
            
        profile = fp.get('1_profile', {})
        technicals = fp.get('2_technicals', {})
        
        if not profile.get('has_data') or technicals.get('insufficient_data'):
            print(f"  Filtering {fp['ticker']}: Insufficient technical or profile data.")
            continue
            
        name = profile.get('name', '').lower()
        sic = profile.get('sic_description', '').lower()
        sector = profile.get('sector', 'UNKNOWN') # Use new sector field
        
        if sector == 'ETF' or 'etf' in name or 'fund' in name:
            print(f"  Filtering {fp['ticker']}: Is an ETF/Fund.")
            continue
        if 'warrant' in name or '.ws' in fp['ticker'].lower() or 'corzw' in fp['ticker'].lower() or 'lacqw' in fp['ticker'].lower():
            print(f"  Filtering {fp['ticker']}: Is a warrant.")
            continue
        if sector == 'SPAC' or 'blank checks' in sic:
            print(f"  Filtering {fp['ticker']}: Is a SPAC.")
            continue
        
        clean_fingerprints.append(fp)
        
    print(f"Filtered down to {len(clean_fingerprints)} clean company fingerprints.")
    
    with open(CLEAN_FILE, 'w') as f:
        json.dump(clean_fingerprints, f, indent=2)
    print(f"Saved clean data to {CLEAN_FILE}")
    
    return clean_fingerprints

def flatten_fingerprint(fp: Dict) -> Dict:
    """
    Flattens the nested JSON structure into a single-level dictionary
    suitable for a Pandas DataFrame.
    --- UPDATED (v3) ---
    Adds all new v4 metrics.
    """
    profile = fp.get('1_profile', {})
    tech = fp.get('2_technicals', {})
    funda = fp.get('3_fundamentals', {})
    rel_str = fp.get('4_relative_strength', {})
    news = fp.get('5_news', {})
    patterns = fp.get('6_price_patterns', {})
    vol_profile = fp.get('7_volume_profile', {})
    short = fp.get('8_short_interest', {})
    sec = fp.get('sec_data', {})
    insider = sec.get('insider_trades', {}) if sec else {}
    k8 = sec.get('form_8k', {}) if sec else {}
    institutional = sec.get('institutional', {}) if sec else {}
    
    # --- Cash Runway Calculation ---
    cash = funda.get('cash', 0)
    expenses_quarterly = abs(funda.get('operating_expenses', 0))
    
    cash_runway_months = 0
    if expenses_quarterly > 0:
        burn_rate_monthly = expenses_quarterly / 3
        if burn_rate_monthly > 0:
            cash_runway_months = cash / burn_rate_monthly
            
    has_6mo_cash = cash_runway_months > 6
    # --- End Calculation ---

    return {
        # Target Variable
        'gain_pct': fp.get('explosion_metrics', {}).get('gain_pct'),
        
        # 1_profile
        'is_micro_cap': profile.get('is_micro_cap'),
        'is_ultra_low_float': profile.get('is_ultra_low_float'),
        'sector': profile.get('sector'), # <-- NEW (will be one-hot encoded)
        
        # 2_technicals
        'bb_squeeze': tech.get('bb_squeeze', {}).get('is_squeezing'),
        'volume_drying': tech.get('volume_trend', {}).get('is_drying'),
        'consolidation': tech.get('consolidation', {}).get('is_consolidating'),
        'rsi_14d': tech.get('rsi'),
        'volatility_rank': tech.get('volatility_rank'),
        'is_golden_cross': tech.get('is_golden_cross'), # <-- NEW
        
        # 3_fundamentals
        'revenue_accel': funda.get('is_accelerating'),
        'turning_profitable': funda.get('turning_profitable'),
        'revenue_yoy_growth': funda.get('revenue_yoy_growth'),
        'has_6mo_cash': has_6mo_cash,
        'debt_to_asset_ratio': funda.get('debt_to_asset_ratio'), # <-- NEW
        
        # 4_relative_strength
        'relative_strength': rel_str.get('relative_strength'),
        'strongly_outperforming': rel_str.get('strongly_outperforming'),
        
        # 5_news
        'is_news_catalyst': news.get('primary_catalyst') in ['earnings', 'fda_approval', 'merger', 'contract'],
        
        # 6_price_patterns (momentum)
        'return_7d': patterns.get('return_7d'),
        'return_30d': patterns.get('return_30d'),
        
        # 8_short_interest
        'is_squeeze_setup': short.get('is_squeeze_setup'),
        'is_heavily_shorted': short.get('is_heavily_shorted'),
        
        # SEC Data
        'insider_buying_surge': insider.get('insider_buying_surge'),
        'any_insider_buys_30d': insider.get('any_insider_buys_30d'), # <-- NEW
        'has_catalyst_8k': k8.get('has_catalyst_8k'),
        'new_activist_filing_90d': institutional.get('new_activist_filing_90d') # <-- NEW
    }

def analyze_correlations(fingerprints: List[Dict]):
    """
    Loads the clean data into Pandas, flattens it,
    and runs a correlation analysis.
    """
    print("\n" + "="*60)
    print("RUNNING CORRELATION ANALYSIS (v3)")
    print("="*60)
    
    flat_data = [flatten_fingerprint(fp) for fp in fingerprints]
    df = pd.DataFrame(flat_data)
    
    # --- NEW: One-Hot Encode Sector ---
    # Convert 'sector' column into multiple 0/1 columns
    try:
        sector_dummies = pd.get_dummies(df['sector'], prefix='sector')
        df = pd.concat([df, sector_dummies], axis=1)
        df.drop('sector', axis=1, inplace=True)
        print(f"One-hot encoded sectors. New columns: {list(sector_dummies.columns)}")
    except Exception as e:
        print(f"Could not one-hot encode sectors: {e}")
    
    # Convert booleans to 1s and 0s for correlation
    df = df.astype(float)
    
    # Handle potential infinite values if any
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Calculate the correlation matrix
    corr_matrix = df.corr()
    
    # --- The most important part ---
    print("\nCorrelation with Target Variable (gain_pct):\n")
    corr_with_target = corr_matrix['gain_pct'].sort_values(ascending=False)
    print(corr_with_target)
    
    # --- Generate a heatmap visualization ---
    try:
        print(f"\nGenerating heatmap at {HEATMAP_FILE}...")
        # Increase figure size to accommodate new features
        num_features = len(df.columns)
        fig_height = max(16, num_features * 0.8)
        fig_width = max(20, num_features * 0.8)
        
        plt.figure(figsize=(fig_width, fig_height))
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, annot_kws={"size": 8})
        plt.title('Feature Correlation Matrix (v3 - All Features)')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(HEATMAP_FILE)
        print(f"✅ Successfully saved heatmap to {HEATMAP_FILE}")
    except Exception as e:
        print(f"Could not generate heatmap: {e}")

def main():
    if not os.path.exists(MASTER_FILE):
        print(f"❌ ERROR: {MASTER_FILE} not found!")
        print("Please run the 'Full Data Pipeline' workflow first to generate this file.")
        return
        
    with open(MASTER_FILE, 'r') as f:
        master_data = json.load(f)
        
    clean_fingerprints = filter_noisy_data(master_data.get('fingerprints', []))
    
    analyze_correlations(clean_fingerprints)
    
    print("\nAnalysis complete. Check the GitHub Actions log for correlation numbers.")
    print(f"The '{HEATMAP_FILE}' and '{MASTER_FILE}' will be committed to your repo.")

if __name__ == "__main__":
    main()
