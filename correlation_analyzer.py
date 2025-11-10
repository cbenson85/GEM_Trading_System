import json
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List
import os # Import os to check for the file

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
        # 1. Skip entries that had an error
        if 'error' in fp:
            continue
            
        # 2. Skip entries missing profile or technical data
        profile = fp.get('1_profile', {})
        technicals = fp.get('2_technicals', {})
        
        if not profile.get('has_data') or technicals.get('insufficient_data'):
            print(f"  Filtering {fp['ticker']}: Insufficient technical or profile data.")
            continue
            
        # 3. Filter out non-company entities
        name = profile.get('name', '').lower()
        sic = profile.get('sic_description', '').lower()
        
        if 'etf' in name or 'fund' in name:
            print(f"  Filtering {fp['ticker']}: Is an ETF.")
            continue
        if 'warrant' in name or '.ws' in fp['ticker'].lower() or 'corzw' in fp['ticker'].lower() or 'lacqw' in fp['ticker'].lower():
            print(f"  Filtering {fp['ticker']}: Is a warrant.")
            continue
        if 'blank checks' in sic:
            print(f"  Filtering {fp['ticker']}: Is a SPAC.")
            continue
        
        clean_fingerprints.append(fp)
        
    print(f"Filtered down to {len(clean_fingerprints)} clean company fingerprints.")
    
    # Save the clean data for future use
    with open(CLEAN_FILE, 'w') as f:
        json.dump(clean_fingerprints, f, indent=2)
    print(f"Saved clean data to {CLEAN_FILE}")
    
    return clean_fingerprints

def flatten_fingerprint(fp: Dict) -> Dict:
    """
    Flattens the nested JSON structure into a single-level dictionary
    suitable for a Pandas DataFrame.
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
    # Add safe checks in case sec_data or insider_trades is missing
    insider = sec.get('insider_trades', {}) if sec else {}
    k8 = sec.get('form_8k', {}) if sec else {}
    
    return {
        # Target Variable
        'gain_pct': fp.get('explosion_metrics', {}).get('gain_pct'),
        
        # 1_profile
        'is_micro_cap': profile.get('is_micro_cap'),
        'is_ultra_low_float': profile.get('is_ultra_low_float'),
        'is_low_float': profile.get('is_low_float'),
        'shares_outstanding': profile.get('shares_outstanding'),
        
        # 2_technicals
        'bb_squeeze': tech.get('bb_squeeze', {}).get('is_squeezing'),
        'volume_drying': tech.get('volume_trend', {}).get('is_drying'),
        'consolidation': tech.get('consolidation', {}).get('is_consolidating'),
        'rsi_14d': tech.get('rsi'),
        'volatility_rank': tech.get('volatility_rank'),
        
        # 3_fundamentals
        'revenue_accel': funda.get('is_accelerating'),
        'turning_profitable': funda.get('turning_profitable'),
        'revenue_yoy_growth': funda.get('revenue_yoy_growth'),
        
        # 4_relative_strength
        'relative_strength': rel_str.get('relative_strength'),
        'strongly_outperforming': rel_str.get('strongly_outperforming'),
        
        # 5_news
        'news_article_count': news.get('article_count'),
        'is_news_catalyst': news.get('primary_catalyst') in ['earnings', 'fda_approval', 'merger', 'contract'],
        
        # 6_price_patterns (momentum)
        'return_7d': patterns.get('return_7d'),
        'return_30d': patterns.get('return_30d'),
        'return_90d': patterns.get('return_90d'),
        
        # 8_short_interest
        'is_squeeze_setup': short.get('is_squeeze_setup'),
        'is_heavily_shorted': short.get('is_heavily_shorted'),
        'short_interest_change_pct': short.get('short_interest_change_pct_1y'),
        
        # SEC Data
        'insider_buying_surge': insider.get('insider_buying_surge'),
        'net_insider_buys': insider.get('buy_share_total', 0) - insider.get('sell_share_total', 0),
        'has_catalyst_8k': k8.get('has_catalyst_8k')
    }

def analyze_correlations(fingerprints: List[Dict]):
    """
    Loads the clean data into Pandas, flattens it,
    and runs a correlation analysis.
    """
    print("\n" + "="*60)
    print("RUNNING CORRELATION ANALYSIS")
    print("="*60)
    
    # Flatten the data and load into a DataFrame
    flat_data = [flatten_fingerprint(fp) for fp in fingerprints]
    df = pd.DataFrame(flat_data)
    
    # Convert booleans to 1s and 0s for correlation
    df = df.astype(float)
    
    # Handle potential infinite values if any
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Calculate the correlation matrix
    corr_matrix = df.corr()
    
    # --- The most important part ---
    print("Correlation with Target Variable (gain_pct):\n")
    corr_with_target = corr_matrix['gain_pct'].sort_values(ascending=False)
    print(corr_with_target)
    
    # --- Generate a heatmap visualization ---
    try:
        print(f"\nGenerating heatmap at {HEATMAP_FILE}...")
        plt.figure(figsize=(20, 16)) # Make heatmap larger
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, annot_kws={"size": 8})
        plt.title('Feature Correlation Matrix')
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
        print("Please run the GitHub Actions workflow first to generate this file.")
        return
        
    with open(MASTER_FILE, 'r') as f:
        master_data = json.load(f)
        
    # 1. Filter the noisy data
    clean_fingerprints = filter_noisy_data(master_data.get('fingerprints', []))
    
    # 2. Run the analysis
    analyze_correlations(clean_fingerprints)
    
    print("\nAnalysis complete. Check the GitHub Actions log for correlation numbers.")
    print(f"The '{HEATMAP_FILE}' and '{MASTER_FILE}' will be committed to your repo.")

if __name__ == "__main__":
    # Ensure you have pandas, seaborn, and matplotlib installed
    # (This is handled in the .yml file)
    main()
