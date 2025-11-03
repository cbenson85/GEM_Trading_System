"""
Phase 3B Analysis - Pilot or Full
Runs automated 90-day pre-catalyst analysis on sample or all sustainable stocks
"""

import os
import sys
import json
from polygon_data_collector import PolygonDataCollector


def load_sustainable_stocks():
    """
    Load all 72 sustainable stocks from explosive_stocks_CLEAN.json
    
    Returns:
        List of stock dictionaries with required fields
    """
    clean_file = 'Verified_Backtest_Data/explosive_stocks_CLEAN.json'
    
    if not os.path.exists(clean_file):
        print(f"❌ Error: {clean_file} not found")
        return []
    
    with open(clean_file, 'r') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    print(f"📊 Loaded {len(stocks)} sustainable stocks from CLEAN.json")
    
    # Convert to analysis format
    analysis_stocks = []
    for stock in stocks:
        # Get fields from CLEAN.json structure
        ticker = stock.get('ticker')
        entry_date = stock.get('entry_date', '')
        peak_date = stock.get('peak_date', '')
        year = stock.get('year')
        gain_percent = stock.get('gain_percent')
        days_to_peak = stock.get('days_to_peak')
        
        # Skip if missing critical fields
        if not all([ticker, entry_date, peak_date, year, gain_percent, days_to_peak]):
            print(f"⚠️  Skipping {ticker}: Missing required fields")
            continue
        
        analysis_stocks.append({
            'ticker': ticker,
            'company_name': ticker,  # Use ticker as company name
            'year': year,
            'gain_percent': gain_percent,
            'days_to_peak': days_to_peak,
            'entry_date': entry_date,
            'peak_date': peak_date,
            'role': 'Sustainable explosive stock'
        })
    
    return analysis_stocks


def load_phase3a_sample():
    """Load the 8 sample stocks from Phase 3A (pilot mode)"""
    
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


def run_analysis(stocks, output_dir='Verified_Backtest_Data', mode='pilot'):
    """
    Run Phase 3B analysis on provided stocks
    
    Args:
        stocks: List of stock dictionaries
        output_dir: Directory to save results
        mode: 'pilot' or 'full'
    """
    
    print("=" * 70)
    print(f"PHASE 3B ANALYSIS - {mode.upper()} MODE")
    print(f"Analyzing: {len(stocks)} stocks")
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
    
    print(f"📊 Processing {len(stocks)} stocks...")
    print()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze each stock
    results = []
    
    for i, stock in enumerate(stocks, 1):
        print(f"\n{'='*70}")
        print(f"STOCK {i}/{len(stocks)}: {stock['ticker']}")
        print(f"{'='*70}")
        
        try:
            # Run comprehensive analysis
            analysis = collector.analyze_stock_comprehensive(
                ticker=stock['ticker'],
                company_name=stock.get('company_name', stock['ticker']),
                entry_date=stock['entry_date'],
                peak_date=stock['peak_date'],
                gain_percent=stock['gain_percent'],
                days_to_peak=stock['days_to_peak']
            )
            
            # Add role to analysis
            analysis['stock_info']['role'] = stock.get('role', 'Sustainable stock')
            
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
    
    # Create summary
    summary = {
        'metadata': {
            'phase': f'3B_{mode.upper()}',
            'stocks_analyzed': len(stocks),
            'framework': '90-day pre-catalyst window'
        },
        'stocks': results,
        'success_count': sum(1 for r in results if r['status'] == 'success'),
        'error_count': sum(1 for r in results if r['status'] == 'error')
    }
    
    # Save summary
    summary_filename = f'phase3b_{mode}_analysis_summary.json'
    summary_file = os.path.join(output_dir, summary_filename)
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"{mode.upper()} ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {summary['success_count']}/{len(stocks)}")
    print(f"❌ Errors: {summary['error_count']}/{len(stocks)}")
    print(f"📁 Summary: {summary_file}")
    print()
    
    # Print next steps
    if mode == 'pilot':
        print("NEXT STEPS:")
        print("1. Review analysis files in Verified_Backtest_Data/")
        print("2. Validate patterns detected")
        print("3. If validated, run full analysis on all 72 stocks")
        print()
    else:
        print("NEXT STEPS:")
        print("1. Review all analysis files")
        print("2. Build correlation matrix with statistical significance")
        print("3. Document top patterns")
        print("4. Proceed to Phase 4: Backtesting")
        print()


if __name__ == "__main__":
    # Check command line argument
    mode = sys.argv[1] if len(sys.argv) > 1 else 'pilot'
    
    if mode == 'full':
        print("Loading all 72 sustainable stocks from CLEAN.json...")
        stocks = load_sustainable_stocks()
        if not stocks:
            print("❌ Failed to load stocks. Exiting.")
            sys.exit(1)
        run_analysis(stocks, mode='full')
    else:
        print("Running PILOT analysis (8 sample stocks)...")
        stocks = load_phase3a_sample()
        run_analysis(stocks, mode='pilot')
