"""
Phase 3B Pilot Analysis
Runs automated analysis on 2 sample stocks: AENTW and ASNS
Fully automated - loads stock data, runs analysis, saves results
"""

import os
import json
from polygon_data_collector import PolygonDataCollector


def load_phase3a_samples():
    """Load the 8 sample stocks from Phase 3A"""
    
    # These are the 8 stocks selected in Phase 3A
    # Located in: Verified_Backtest_Data/phase3_sample_selection.json
    
    samples = [
        {
            'ticker': 'AENTW',
            'company_name': 'Alliance Entertainment Holding Corporation Warrant',
            'year': 2024,
            'gain_percent': 12398.33,
            'days_to_peak': 177,
            'entry_date': '2023-12-12',
            'peak_date': '2024-06-07',
            'role': 'Extreme outlier - test framework limits'
        },
        {
            'ticker': 'ASNS',
            'company_name': 'Actelis Networks Inc',
            'year': 2024,
            'gain_percent': 955.05,
            'days_to_peak': 3,
            'entry_date': '2024-05-31',
            'peak_date': '2024-06-03',
            'role': 'Ultra-fast explosion pattern'
        },
        {
            'ticker': 'ABVEW',
            'company_name': 'Above Food Ingredients Inc Warrant',
            'year': 2024,
            'gain_percent': 500.67,
            'days_to_peak': 153,
            'entry_date': '2024-01-29',
            'peak_date': '2024-07-01',
            'role': 'Baseline moderate gainer'
        },
        {
            'ticker': 'ACONW',
            'company_name': 'Aclarion Inc Warrant',
            'year': 2024,
            'gain_percent': 1428.75,
            'days_to_peak': 158,
            'entry_date': '2024-01-16',
            'peak_date': '2024-06-23',
            'role': 'Strong recent performer'
        },
        {
            'ticker': 'ARWR',
            'company_name': 'Arrowhead Pharmaceuticals Inc',
            'year': 2018,
            'gain_percent': 586.81,
            'days_to_peak': 179,
            'entry_date': '2018-01-29',
            'peak_date': '2018-07-27',
            'role': 'Slow accumulation pattern'
        },
        {
            'ticker': 'AG',
            'company_name': 'First Majestic Silver Corp',
            'year': 2016,
            'gain_percent': 662.95,
            'days_to_peak': 142,
            'entry_date': '2016-01-20',
            'peak_date': '2016-06-10',
            'role': 'Historical diversity'
        },
        {
            'ticker': 'AIMD',
            'company_name': 'Ainos Inc',
            'year': 2022,
            'gain_percent': 1071.88,
            'days_to_peak': 25,
            'entry_date': '2022-09-15',
            'peak_date': '2022-10-10',
            'role': 'Post-COVID era winner'
        },
        {
            'ticker': 'ACXP',
            'company_name': 'Acurx Pharmaceuticals Inc',
            'year': 2023,
            'gain_percent': 589.06,
            'days_to_peak': 7,
            'entry_date': '2023-08-14',
            'peak_date': '2023-08-21',
            'role': 'Fast mover pattern'
        }
    ]
    
    return samples


def run_pilot_analysis(output_dir: str = 'Verified_Backtest_Data'):
    """
    Run Phase 3B pilot analysis on first 2 stocks
    
    Args:
        output_dir: Directory to save analysis results
    """
    
    print("=" * 70)
    print("PHASE 3B PILOT ANALYSIS")
    print("Analyzing: AENTW + ASNS")
    print("Framework: 90-day pre-catalyst window")
    print("=" * 70)
    print()
    
    # Get API key
    api_key = os.environ.get('POLYGON_API_KEY')
    if not api_key:
        print("❌ Error: POLYGON_API_KEY environment variable not set")
        print("Set it in GitHub Actions secrets or export locally")
        return
    
    # Initialize collector
    collector = PolygonDataCollector(api_key)
    
    # Load all samples
    all_samples = load_phase3a_samples()
    
    # Select pilot stocks (first 2)
    pilot_stocks = all_samples[:2]
    
    print(f"📊 Loaded {len(pilot_stocks)} stocks for pilot analysis")
    print()
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze each stock
    results = []
    
    for i, stock in enumerate(pilot_stocks, 1):
        print(f"\n{'='*70}")
        print(f"STOCK {i}/2: {stock['ticker']}")
        print(f"{'='*70}")
        
        try:
            # Run comprehensive analysis
            analysis = collector.analyze_stock_comprehensive(
                ticker=stock['ticker'],
                company_name=stock['company_name'],
                entry_date=stock['entry_date'],
                peak_date=stock['peak_date'],
                gain_percent=stock['gain_percent'],
                days_to_peak=stock['days_to_peak']
            )
            
            # Add role to analysis
            analysis['stock_info']['role'] = stock['role']
            
            # Save individual analysis
            filename = f"phase3b_{stock['ticker']}_{stock['year']}_analysis.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            print(f"✅ Saved: {filepath}")
            
            results.append({
                'ticker': stock['ticker'],
                'status': 'success',
                'file': filename,
                'summary': analysis.get('summary', {})
            })
            
        except Exception as e:
            print(f"❌ Error analyzing {stock['ticker']}: {e}")
            results.append({
                'ticker': stock['ticker'],
                'status': 'error',
                'error': str(e)
            })
    
    # Create pilot summary
    pilot_summary = {
        'metadata': {
            'analysis_date': collector._generate_summary({}, {}, 0, 0),  # Just to get timestamp
            'phase': '3B_PILOT',
            'stocks_analyzed': len(pilot_stocks),
            'framework': '90-day pre-catalyst window'
        },
        'stocks': results,
        'success_count': sum(1 for r in results if r['status'] == 'success'),
        'error_count': sum(1 for r in results if r['status'] == 'error')
    }
    
    # Save pilot summary
    summary_file = os.path.join(output_dir, 'phase3b_pilot_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(pilot_summary, f, indent=2)
    
    print(f"\n{'='*70}")
    print("PILOT ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {pilot_summary['success_count']}/{len(pilot_stocks)}")
    print(f"❌ Errors: {pilot_summary['error_count']}/{len(pilot_stocks)}")
    print(f"📁 Summary: {summary_file}")
    print()
    
    # Print next steps
    print("NEXT STEPS:")
    print("1. Review analysis files in Verified_Backtest_Data/")
    print("2. Validate patterns detected")
    print("3. Run searches for catalyst discovery")
    print("4. If validated, proceed to remaining 6 stocks")
    print()


def run_full_analysis(output_dir: str = 'Verified_Backtest_Data'):
    """
    Run Phase 3B analysis on all 8 stocks
    
    Args:
        output_dir: Directory to save analysis results
    """
    
    print("=" * 70)
    print("PHASE 3B FULL ANALYSIS")
    print("Analyzing: All 8 sample stocks")
    print("Framework: 90-day pre-catalyst window")
    print("=" * 70)
    print()
    
    # Get API key
    api_key = os.environ.get('POLYGON_API_KEY')
    if not api_key:
        print("❌ Error: POLYGON_API_KEY environment variable not set")
        return
    
    # Initialize collector
    collector = PolygonDataCollector(api_key)
    
    # Load all samples
    all_samples = load_phase3a_samples()
    
    print(f"📊 Loaded {len(all_samples)} stocks for analysis")
    print()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze each stock
    results = []
    
    for i, stock in enumerate(all_samples, 1):
        print(f"\n{'='*70}")
        print(f"STOCK {i}/{len(all_samples)}: {stock['ticker']}")
        print(f"{'='*70}")
        
        try:
            # Run comprehensive analysis
            analysis = collector.analyze_stock_comprehensive(
                ticker=stock['ticker'],
                company_name=stock['company_name'],
                entry_date=stock['entry_date'],
                peak_date=stock['peak_date'],
                gain_percent=stock['gain_percent'],
                days_to_peak=stock['days_to_peak']
            )
            
            # Add role to analysis
            analysis['stock_info']['role'] = stock['role']
            
            # Save individual analysis
            filename = f"phase3b_{stock['ticker']}_{stock['year']}_analysis.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            print(f"✅ Saved: {filepath}")
            
            results.append({
                'ticker': stock['ticker'],
                'status': 'success',
                'file': filename,
                'summary': analysis.get('summary', {})
            })
            
        except Exception as e:
            print(f"❌ Error analyzing {stock['ticker']}: {e}")
            results.append({
                'ticker': stock['ticker'],
                'status': 'error',
                'error': str(e)
            })
    
    # Create full summary
    full_summary = {
        'metadata': {
            'phase': '3B_FULL',
            'stocks_analyzed': len(all_samples),
            'framework': '90-day pre-catalyst window'
        },
        'stocks': results,
        'success_count': sum(1 for r in results if r['status'] == 'success'),
        'error_count': sum(1 for r in results if r['status'] == 'error')
    }
    
    # Save summary
    summary_file = os.path.join(output_dir, 'phase3b_full_analysis_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(full_summary, f, indent=2)
    
    print(f"\n{'='*70}")
    print("FULL ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {full_summary['success_count']}/{len(all_samples)}")
    print(f"❌ Errors: {full_summary['error_count']}/{len(all_samples)}")
    print(f"📁 Summary: {summary_file}")
    print()
    
    # Print next steps
    print("NEXT STEPS:")
    print("1. Review all 8 analysis files")
    print("2. Run catalyst searches")
    print("3. Build correlation matrix")
    print("4. Identify top patterns")
    print("5. Proceed to Phase 4: Backtesting")
    print()


if __name__ == "__main__":
    import sys
    
    # Check command line argument
    mode = sys.argv[1] if len(sys.argv) > 1 else 'pilot'
    
    if mode == 'full':
        print("Running FULL analysis (all 8 stocks)...")
        run_full_analysis()
    else:
        print("Running PILOT analysis (2 stocks)...")
        run_pilot_analysis()
