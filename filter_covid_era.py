#!/usr/bin/env python3
"""
Data Filter - COVID-Era Exclusion (WITH SMART MERGE LOGIC)
Separates explosive stocks into clean dataset vs COVID-era anomalies
UPDATES existing incomplete records with new complete data

FIXED: 2025-11-02
CHANGE: Now UPDATES duplicate records instead of skipping them
REASON: New scanner data is more complete (has entry_date, entry_price, etc.)
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

def is_more_complete(new_stock, old_stock):
    """Check if new stock has more complete data than old stock"""
    # Check for critical fields that were missing in old data
    new_has_dates = bool(new_stock.get('entry_date') and new_stock.get('peak_date'))
    new_has_prices = bool(new_stock.get('entry_price') and new_stock.get('peak_price'))
    
    old_has_dates = bool(old_stock.get('entry_date') and old_stock.get('peak_date'))
    old_has_prices = bool(old_stock.get('entry_price') and old_stock.get('peak_price'))
    
    # New is more complete if it has dates/prices and old doesn't
    return (new_has_dates and not old_has_dates) or (new_has_prices and not old_has_prices)

def merge_stocks(existing_stocks, new_stocks):
    """
    Merge new stocks into existing stocks
    UPDATES duplicates if new data is more complete
    ADDS new stocks that don't exist
    """
    # Create dictionary of existing stocks by key
    existing_dict = {create_stock_key(s): s for s in existing_stocks}
    
    # Track what we're doing
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    # Process new stocks
    for new_stock in new_stocks:
        key = create_stock_key(new_stock)
        
        if key in existing_dict:
            # Stock exists - check if we should update it
            old_stock = existing_dict[key]
            
            if is_more_complete(new_stock, old_stock):
                # New data is better - REPLACE old with new
                existing_dict[key] = new_stock
                updated_count += 1
                print(f"   🔄 Updated {new_stock.get('ticker')} ({get_year(new_stock)}) - added missing dates/prices")
            else:
                # Old data is fine - keep it
                skipped_count += 1
        else:
            # Brand new stock - ADD it
            existing_dict[key] = new_stock
            added_count += 1
    
    # Convert back to list
    merged_stocks = list(existing_dict.values())
    
    return merged_stocks, added_count, updated_count, skipped_count

def filter_explosive_stocks(catalog_path='Verified_Backtest_Data/explosive_stocks_catalog.json'):
    """
    Filter explosive stocks catalog into clean vs COVID-era datasets
    UPDATES existing incomplete data with new complete data
    
    RULE: Exclude 2020-2021 from pattern analysis
    REASON: Unprecedented market conditions (stimulus, zero rates, pandemic anomalies)
    """
    
    print("="*60)
    print(" DATA FILTER - COVID-ERA EXCLUSION (SMART MERGE)")
    print("="*60)
    print("\nRULE: Exclude 2020-2021 from pattern discovery")
    print("REASON: Unprecedented market conditions not repeatable")
    print("MODE: Update incomplete records with new complete data\n")
    
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
    
    # Merge with existing data (SMART MERGE - updates incomplete records)
    print(f"\n🔄 Merging new stocks with existing data...")
    
    merged_clean, clean_added, clean_updated, clean_skipped = merge_stocks(existing_clean, new_clean_stocks)
    merged_covid, covid_added, covid_updated, covid_skipped = merge_stocks(existing_covid, new_covid_stocks)
    
    print(f"\n   CLEAN: Added {clean_added}, Updated {clean_updated}, Skipped {clean_skipped}")
    print(f"   COVID: Added {covid_added}, Updated {covid_updated}, Skipped {covid_skipped}")
    
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
    if clean_added > 0 or clean_updated > 0 or covid_added > 0 or covid_updated > 0:
        print(f"\n✨ CHANGES THIS SCAN:")
        if clean_added > 0:
            print(f"   ➕ {clean_added} new CLEAN stocks added")
        if clean_updated > 0:
            print(f"   🔄 {clean_updated} CLEAN stocks updated with complete data")
            # Show top 5 updated
            updated_stocks = [s for s in new_clean_stocks if create_stock_key(s) in {create_stock_key(e) for e in existing_clean}]
            updated_sorted = sorted(updated_stocks[:5], key=lambda x: x.get('gain_percent', 0), reverse=True)
            for i, stock in enumerate(updated_sorted, 1):
                ticker = stock.get('ticker', 'N/A')
                year = get_year(stock)
                gain = stock.get('gain_percent', 0)
                days = stock.get('days_to_peak', 0)
                print(f"      {i}. {ticker:6s} ({year}): {gain:>6.0f}% in {days} days")
        
        if covid_added > 0:
            print(f"   ➕ {covid_added} new COVID-era stocks archived")
        if covid_updated > 0:
            print(f"   🔄 {covid_updated} COVID stocks updated with complete data")
    else:
        print(f"\n📌 NO CHANGES - All data already current")
    
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
            'records_updated': clean_updated,
            'duplicates_skipped': clean_skipped,
            'merge_mode': 'smart_update'
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
            'records_updated': covid_updated,
            'duplicates_skipped': covid_skipped,
            'merge_mode': 'smart_update'
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
            'records_updated': clean_updated,
            'duplicates_skipped': clean_skipped,
            'pre_covid_2014_2019': len(pre_covid),
            'post_covid_2022_2024': len(post_covid)
        },
        'covid_dataset': {
            'total': len(merged_covid),
            'new_additions': covid_added,
            'records_updated': covid_updated,
            'duplicates_skipped': covid_skipped
        },
        'ready_for_analysis': len(merged_clean) > 0,
        'merge_mode': 'smart_update'
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
        print(f"   Updated CLEAN records: {summary['clean_dataset']['records_updated']}")
        print(f"   New COVID additions: {summary['covid_dataset']['new_additions']}")
        print(f"   Updated COVID records: {summary['covid_dataset']['records_updated']}")
        print(f"\n🎯 Ready for pattern analysis on {summary['clean_dataset']['total']} clean stocks!")
        print(f"\nNext step: Analyze pre-catalyst conditions on clean dataset")
    else:
        print(f"\n⚠️ Filter process incomplete - check errors above")
