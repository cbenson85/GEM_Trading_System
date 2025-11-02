#!/usr/bin/env python3
"""
Data Filter - COVID-Era Exclusion (WITH MERGE LOGIC)
Separates explosive stocks into clean dataset vs COVID-era anomalies
PRESERVES existing data - no data loss on subsequent scans

UPDATED: 2025-11-02
CHANGE: Now MERGES new findings instead of overwriting
"""

import json
import os
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

def load_existing_data(filepath):
    """Load existing CLEAN or COVID file if it exists"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('stocks', [])
        except:
            print(f"⚠️ Could not load {filepath}, starting fresh")
            return []
    return []

def create_stock_key(stock):
    """Create unique key for stock (ticker + year)"""
    return f"{stock.get('ticker', '')}_{stock.get('year_discovered', stock.get('year', ''))}"

def merge_stocks(existing_stocks, new_stocks):
    """
    Merge new stocks into existing stocks
    Skip duplicates based on ticker + year
    """
    # Create set of existing keys
    existing_keys = {create_stock_key(s) for s in existing_stocks}
    
    # Track what we're adding
    added_count = 0
    duplicate_count = 0
    
    # Add only new stocks
    for stock in new_stocks:
        key = create_stock_key(stock)
        if key not in existing_keys:
            existing_stocks.append(stock)
            existing_keys.add(key)
            added_count += 1
        else:
            duplicate_count += 1
    
    return existing_stocks, added_count, duplicate_count

def filter_explosive_stocks(catalog_path='Verified_Backtest_Data/explosive_stocks_catalog.json'):
    """
    Filter explosive stocks catalog into clean vs COVID-era datasets
    MERGES with existing data to prevent loss
    
    RULE: Exclude 2020-2021 from pattern analysis
    REASON: Unprecedented market conditions (stimulus, zero rates, pandemic anomalies)
    """
    
    print("="*60)
    print(" DATA FILTER - COVID-ERA EXCLUSION (MERGE MODE)")
    print("="*60)
    print("\nRULE: Exclude 2020-2021 from pattern discovery")
    print("REASON: Unprecedented market conditions not repeatable")
    print("MODE: Merge new findings with existing data\n")
    
    # File paths
    clean_path = 'Verified_Backtest_Data/explosive_stocks_CLEAN.json'
    covid_path = 'Verified_Backtest_Data/explosive_stocks_COVID_ERA.json'
    
    # Load existing data
    print("📂 Loading existing data...")
    existing_clean = load_existing_data(clean_path)
    existing_covid = load_existing_data(covid_path)
    print(f"   Existing CLEAN stocks: {len(existing_clean)}")
    print(f"   Existing COVID stocks: {len(existing_covid)}")
    
    # Load new catalog
    print(f"\n📊 Reading new scan results from catalog...")
    try:
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
    except FileNotFoundError:
        print(f"❌ Catalog file not found: {catalog_path}")
        print(f"   Run explosive_stock_scanner.py first")
        return None
    
    stocks = catalog.get('stocks', [])
    print(f"   New stocks in catalog: {len(stocks)}")
    
    if not stocks:
        print(f"\n⚠️ No stocks in catalog - nothing to filter")
        return None
    
    # Separate NEW stocks
    new_clean_stocks = []
    new_covid_stocks = []
    
    for stock in stocks:
        # Normalize field names (handle both entry_date and year)
        entry_date = stock.get('entry_date', '')
        catalyst_date = stock.get('catalyst_date', '')
        year = stock.get('year_discovered', stock.get('year', ''))
        
        # Check if either date is in COVID era
        if is_covid_era(entry_date) or is_covid_era(catalyst_date):
            stock['covid_era'] = True
            new_covid_stocks.append(stock)
        else:
            stock['covid_era'] = False
            new_clean_stocks.append(stock)
    
    print(f"   New CLEAN stocks: {len(new_clean_stocks)}")
    print(f"   New COVID stocks: {len(new_covid_stocks)}")
    
    # Merge with existing data
    print(f"\n🔄 Merging new stocks with existing data...")
    
    merged_clean, clean_added, clean_dupes = merge_stocks(existing_clean, new_clean_stocks)
    merged_covid, covid_added, covid_dupes = merge_stocks(existing_covid, new_covid_stocks)
    
    print(f"   CLEAN: Added {clean_added}, Skipped {clean_dupes} duplicates")
    print(f"   COVID: Added {covid_added}, Skipped {covid_dupes} duplicates")
    
    # Categorize clean stocks by period
    pre_covid = [s for s in merged_clean if get_year(s) < 2020]
    post_covid = [s for s in merged_clean if get_year(s) > 2021]
    
    # Generate report
    print(f"\n{'='*60}")
    print(f"📊 FINAL MERGED RESULTS:")
    print(f"\n{'='*60}")
    print(f"CLEAN DATASET (For Pattern Analysis):")
    print(f"  Pre-COVID (2014-2019): {len(pre_covid)} stocks")
    print(f"  Post-COVID (2022-2024): {len(post_covid)} stocks")
    print(f"  Total clean stocks: {len(merged_clean)}")
    print(f"\n{'='*60}")
    print(f"COVID-ERA (Archived - Reference Only):")
    print(f"  2020-2021 stocks: {len(merged_covid)}")
    print(f"  Excluded from analysis")
    print(f"\n{'='*60}")
    
    # Show what changed
    if clean_added > 0 or covid_added > 0:
        print(f"\n✨ NEW ADDITIONS THIS SCAN:")
        if clean_added > 0:
            print(f"   📈 {clean_added} new CLEAN stocks added")
            # Show top 5 new additions
            new_sorted = sorted(new_clean_stocks, key=lambda x: x.get('gain_percent', 0), reverse=True)[:5]
            for i, stock in enumerate(new_sorted, 1):
                ticker = stock.get('ticker', 'N/A')
                year = get_year(stock)
                gain = stock.get('gain_percent', 0)
                days = stock.get('days_to_peak', 0)
                print(f"      {i}. {ticker:6s} ({year}): {gain:>6.0f}% in {days} days")
        
        if covid_added > 0:
            print(f"   📋 {covid_added} new COVID-era stocks archived")
    else:
        print(f"\n📌 NO NEW STOCKS - All catalog entries were already in database")
    
    # Show top gainers overall
    if merged_clean:
        print(f"\n🚀 TOP 5 CLEAN DATASET GAINERS (ALL-TIME):")
        top_clean = sorted(merged_clean, key=lambda x: x.get('gain_percent', 0), reverse=True)[:5]
        for i, stock in enumerate(top_clean, 1):
            ticker = stock.get('ticker', 'N/A')
            year = get_year(stock)
            gain = stock.get('gain_percent', 0)
            days = stock.get('days_to_peak', 0)
            print(f"  {i}. {ticker:6s} ({year}): {gain:>6.0f}% in {days} days")
    
    # Create filtered catalogs with scan info
    clean_catalog = {
        'scan_info': catalog.get('scan_info', {}).copy(),
        'filter_info': {
            'filter_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filter_applied': 'COVID-era exclusion (2020-2021)',
            'original_catalog_count': len(stocks),
            'total_clean_count': len(merged_clean),
            'new_additions': clean_added,
            'duplicates_skipped': clean_dupes,
            'merge_mode': True
        },
        'stocks': merged_clean,
        'metadata': {
            'note': 'Pattern analysis dataset - normal market conditions only',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cumulative': True
        }
    }
    
    covid_catalog = {
        'scan_info': catalog.get('scan_info', {}).copy(),
        'filter_info': {
            'period': '2020-2021',
            'reason': 'COVID-era market anomalies - unprecedented conditions',
            'total_covid_count': len(merged_covid),
            'new_additions': covid_added,
            'duplicates_skipped': covid_dupes,
            'merge_mode': True
        },
        'stocks': merged_covid,
        'metadata': {
            'note': 'Archive only - not used for pattern discovery',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cumulative': True
        }
    }
    
    # Save merged datasets
    with open(clean_path, 'w') as f:
        json.dump(clean_catalog, f, indent=2)
    
    with open(covid_path, 'w') as f:
        json.dump(covid_catalog, f, indent=2)
    
    print(f"\n✅ Updated datasets saved:")
    print(f"  - explosive_stocks_CLEAN.json ({len(merged_clean)} total stocks)")
    print(f"  - explosive_stocks_COVID_ERA.json ({len(merged_covid)} total stocks)")
    
    # Generate summary
    summary = {
        'filter_applied': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'catalog_stocks_processed': len(stocks),
        'clean_dataset': {
            'total': len(merged_clean),
            'new_additions': clean_added,
            'duplicates_skipped': clean_dupes,
            'pre_covid_2014_2019': len(pre_covid),
            'post_covid_2022_2024': len(post_covid)
        },
        'covid_dataset': {
            'total': len(merged_covid),
            'new_additions': covid_added,
            'duplicates_skipped': covid_dupes
        },
        'ready_for_analysis': len(merged_clean) > 0,
        'merge_mode': True
    }
    
    with open('Verified_Backtest_Data/filter_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"  - filter_summary.json (merge statistics)")
    
    return summary

def get_year(stock):
    """Extract year from stock data (handles different field names)"""
    year = stock.get('year_discovered', stock.get('year', 0))
    if not year:
        entry_date = stock.get('entry_date', '')
        if entry_date:
            try:
                return int(entry_date[:4])
            except:
                return 0
    return year

if __name__ == "__main__":
    summary = filter_explosive_stocks()
    
    if summary:
        print(f"\n{'='*60}")
        print(f"✅ FILTERING COMPLETE")
        print(f"{'='*60}")
        print(f"\n📊 Final Statistics:")
        print(f"   Total CLEAN stocks: {summary['clean_dataset']['total']}")
        print(f"   Total COVID stocks: {summary['covid_dataset']['total']}")
        print(f"   New CLEAN additions: {summary['clean_dataset']['new_additions']}")
        print(f"   New COVID additions: {summary['covid_dataset']['new_additions']}")
        print(f"\n🎯 Ready for pattern analysis on {summary['clean_dataset']['total']} clean stocks!")
        print(f"\nNext step: Analyze pre-catalyst conditions on clean dataset")
    else:
        print(f"\n⚠️ Filter process incomplete - check errors above")
