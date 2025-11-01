#!/usr/bin/env python3
"""
Data Filter - COVID-Era Exclusion
Separates explosive stocks into clean dataset vs COVID-era anomalies
"""

import json
from datetime import datetime

# COVID era dates
COVID_START = datetime(2020, 1, 1)
COVID_END = datetime(2021, 12, 31)

def is_covid_era(date_str):
    """Check if a date falls within COVID era (2020-2021)"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return COVID_START <= date <= COVID_END
    except:
        return False

def filter_explosive_stocks(catalog_path='Verified_Backtest_Data/explosive_stocks_catalog.json'):
    """
    Filter explosive stocks catalog into clean vs COVID-era datasets
    
    RULE: Exclude 2020-2021 from pattern analysis
    REASON: Unprecedented market conditions (stimulus, zero rates, pandemic anomalies)
    """
    
    print("="*60)
    print(" DATA FILTER - COVID-ERA EXCLUSION")
    print("="*60)
    print("\nRULE: Exclude 2020-2021 from pattern discovery")
    print("REASON: Unprecedented market conditions not repeatable\n")
    
    # Load catalog
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    
    stocks = catalog.get('stocks', [])
    
    # Separate stocks
    clean_stocks = []
    covid_stocks = []
    
    for stock in stocks:
        entry_date = stock.get('entry_date', '')
        catalyst_date = stock.get('catalyst_date', '')
        
        # Check if either date is in COVID era
        if is_covid_era(entry_date) or is_covid_era(catalyst_date):
            stock['covid_era'] = True
            stock['excluded_reason'] = 'COVID-era anomaly (2020-2021)'
            covid_stocks.append(stock)
        else:
            stock['covid_era'] = False
            clean_stocks.append(stock)
    
    # Categorize clean stocks by period
    pre_covid = [s for s in clean_stocks if datetime.strptime(s['entry_date'], '%Y-%m-%d').year < 2020]
    post_covid = [s for s in clean_stocks if datetime.strptime(s['entry_date'], '%Y-%m-%d').year > 2021]
    
    # Generate report
    print(f"📊 FILTERING RESULTS:")
    print(f"\nTotal explosive stocks found: {len(stocks)}")
    print(f"\n{'='*60}")
    print(f"CLEAN DATASET (For Pattern Analysis):")
    print(f"  Pre-COVID (2014-2019): {len(pre_covid)} stocks")
    print(f"  Post-COVID (2022-2024): {len(post_covid)} stocks")
    print(f"  Total clean stocks: {len(clean_stocks)}")
    print(f"\n{'='*60}")
    print(f"COVID-ERA (Archived - Reference Only):")
    print(f"  2020-2021 stocks: {len(covid_stocks)}")
    print(f"  Excluded from analysis")
    print(f"\n{'='*60}")
    
    # Show top gainers in each category
    if clean_stocks:
        print(f"\n🚀 TOP 5 CLEAN DATASET GAINERS:")
        top_clean = sorted(clean_stocks, key=lambda x: x['gain_percent'], reverse=True)[:5]
        for i, stock in enumerate(top_clean, 1):
            print(f"  {i}. {stock['ticker']:6s} ({stock['entry_date'][:4]}): {stock['gain_percent']:>6.0f}% in {stock['days_to_peak']} days")
    
    if covid_stocks:
        print(f"\n📋 COVID-ERA STOCKS (Archived):")
        top_covid = sorted(covid_stocks, key=lambda x: x['gain_percent'], reverse=True)[:5]
        for i, stock in enumerate(top_covid, 1):
            print(f"  {i}. {stock['ticker']:6s} ({stock['entry_date'][:4]}): {stock['gain_percent']:>6.0f}% in {stock['days_to_peak']} days")
    
    # Create filtered catalogs
    clean_catalog = {
        'scan_info': catalog['scan_info'].copy(),
        'filter_info': {
            'filter_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filter_applied': 'COVID-era exclusion (2020-2021)',
            'original_count': len(stocks),
            'clean_count': len(clean_stocks),
            'excluded_count': len(covid_stocks),
            'exclusion_reason': 'Unprecedented market conditions (stimulus, zero rates, pandemic)'
        },
        'stocks': clean_stocks,
        'metadata': catalog['metadata'].copy()
    }
    
    covid_catalog = {
        'scan_info': catalog['scan_info'].copy(),
        'filter_info': {
            'period': '2020-2021',
            'reason': 'COVID-era market anomalies',
            'usage': 'Reference only - not used for pattern discovery'
        },
        'stocks': covid_stocks,
        'metadata': {
            'note': 'Archive of COVID-era explosive stocks - unprecedented conditions'
        }
    }
    
    # Save filtered datasets
    with open('Verified_Backtest_Data/explosive_stocks_CLEAN.json', 'w') as f:
        json.dump(clean_catalog, f, indent=2)
    
    with open('Verified_Backtest_Data/explosive_stocks_COVID_ERA.json', 'w') as f:
        json.dump(covid_catalog, f, indent=2)
    
    print(f"\n✅ Filtered datasets saved:")
    print(f"  - explosive_stocks_CLEAN.json ({len(clean_stocks)} stocks)")
    print(f"  - explosive_stocks_COVID_ERA.json ({len(covid_stocks)} stocks)")
    
    # Generate summary for system
    summary = {
        'filter_applied': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_stocks': len(stocks),
        'clean_dataset': {
            'total': len(clean_stocks),
            'pre_covid_2014_2019': len(pre_covid),
            'post_covid_2022_2024': len(post_covid)
        },
        'covid_era_archived': len(covid_stocks),
        'ready_for_analysis': len(clean_stocks) > 0
    }
    
    with open('Verified_Backtest_Data/filter_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

if __name__ == "__main__":
    summary = filter_explosive_stocks()
    
    print(f"\n{'='*60}")
    print(f"✅ FILTERING COMPLETE")
    print(f"{'='*60}")
    print(f"\nReady to proceed with pattern analysis on {summary['clean_dataset']['total']} clean stocks!")
    print(f"\nNext step: Analyze pre-catalyst conditions on clean dataset")
