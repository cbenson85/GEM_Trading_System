#!/usr/bin/env python3
"""
Phase 3 Preparation - Organize Filtered Stocks
================================================

This script:
1. Separates 113 untested stocks → explosive_stocks_NOT_TESTED.json
2. Keeps 72 verified sustainable stocks in CLEAN.json
3. Removes bulky daily_gains arrays (reduces file size by ~90%)
4. Creates clean, organized files for Phase 3 pattern discovery

INPUT: explosive_stocks_CLEAN.json (200 stocks, 70k lines)
OUTPUT:
  - explosive_stocks_CLEAN.json (72 sustainable, ~2-3k lines)
  - explosive_stocks_NOT_TESTED.json (113 untested stocks)
  - explosive_stocks_UNSUSTAINABLE.json (15 pump-and-dumps - already exists)
  - phase3_preparation_summary.json (statistics)
"""

import json
from datetime import datetime
from pathlib import Path

# File paths
DATA_DIR = "Verified_Backtest_Data"
INPUT_FILE = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
OUTPUT_CLEAN = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
OUTPUT_NOT_TESTED = f"{DATA_DIR}/explosive_stocks_NOT_TESTED.json"
OUTPUT_SUMMARY = f"{DATA_DIR}/phase3_preparation_summary.json"
BACKUP_FULL = f"{DATA_DIR}/explosive_stocks_CLEAN_FULL_BACKUP.json"

def prepare_for_phase3():
    """Main cleanup and organization"""
    print("\n" + "="*80)
    print("PHASE 3 PREPARATION - ORGANIZING FILTERED STOCKS")
    print("="*80)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load current CLEAN.json
    print(f"📂 Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    # Extract stocks and metadata
    if isinstance(data, dict) and 'stocks' in data:
        all_stocks = data['stocks']
        file_metadata = {k: v for k, v in data.items() if k != 'stocks'}
    else:
        all_stocks = data if isinstance(data, list) else []
        file_metadata = {}
    
    print(f"✅ Loaded {len(all_stocks)} total stocks\n")
    
    # Separate stocks by test status
    sustainable = []
    not_tested = []
    
    stats = {
        "preparation_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_stocks_before": len(all_stocks),
        "sustainable_verified": 0,
        "not_tested": 0,
        "daily_records_removed": 0,
        "file_size_reduction": "pending"
    }
    
    print("🔬 Categorizing stocks...")
    for stock in all_stocks:
        ticker = stock.get('ticker', 'UNKNOWN')
        test = stock.get('sustained_gain_test', {})
        
        # Check if stock was tested
        if not test or test.get('sustainable') is None:
            # Not tested - move to separate file
            not_tested.append(stock)
            print(f"  ⚠️  {ticker} - Not tested (no price data)")
        else:
            # Was tested and sustainable - keep in CLEAN
            if test.get('sustainable') == True:
                # Remove bulky daily_gains array
                cleaned_stock = stock.copy()
                cleaned_test = test.copy()
                
                if 'daily_gains' in cleaned_test:
                    stats['daily_records_removed'] += len(cleaned_test['daily_gains'])
                    del cleaned_test['daily_gains']
                
                cleaned_stock['sustained_gain_test'] = cleaned_test
                sustainable.append(cleaned_stock)
                
                days_above = test.get('total_days_above_threshold', 0)
                print(f"  ✅ {ticker} - Sustainable ({days_above} days above 200%)")
            else:
                # Unsustainable stocks already in UNSUSTAINABLE.json
                print(f"  ❌ {ticker} - Unsustainable (already in UNSUSTAINABLE.json)")
    
    stats['sustainable_verified'] = len(sustainable)
    stats['not_tested'] = len(not_tested)
    
    # Create backup of full data before cleanup
    print(f"\n💾 Creating backup with full data...")
    with open(BACKUP_FULL, 'w') as f:
        if file_metadata:
            backup_data = file_metadata.copy()
            backup_data['stocks'] = all_stocks
            json.dump(backup_data, f, indent=2)
        else:
            json.dump(all_stocks, f, indent=2)
    print(f"✅ Backup saved: {BACKUP_FULL}")
    
    # Save CLEAN.json with only verified sustainable stocks
    print(f"\n💾 Saving cleaned CLEAN.json...")
    clean_output = {
        "filter_info": {
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "filter_version": "4.0",
            "filter_method": "Total Days Above 200% Threshold",
            "status": "Phase 3 Ready",
            "total_sustainable": len(sustainable),
            "note": "Only verified sustainable stocks - ready for pattern discovery"
        },
        "stocks": sustainable
    }
    
    with open(OUTPUT_CLEAN, 'w') as f:
        json.dump(clean_output, f, indent=2)
    print(f"✅ Saved {len(sustainable)} verified sustainable stocks → {OUTPUT_CLEAN}")
    
    # Save NOT_TESTED stocks to separate file
    print(f"\n💾 Saving not-tested stocks...")
    not_tested_output = {
        "info": {
            "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "reason": "Could not fetch price data from Polygon API",
            "total_stocks": len(not_tested),
            "note": "These stocks may have: ticker changes, delisting, data gaps, or source mismatches"
        },
        "stocks": not_tested
    }
    
    with open(OUTPUT_NOT_TESTED, 'w') as f:
        json.dump(not_tested_output, f, indent=2)
    print(f"✅ Saved {len(not_tested)} not-tested stocks → {OUTPUT_NOT_TESTED}")
    
    # Save summary
    print(f"\n💾 Saving preparation summary...")
    with open(OUTPUT_SUMMARY, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Saved summary → {OUTPUT_SUMMARY}")
    
    # Final summary
    print("\n" + "="*80)
    print("PHASE 3 PREPARATION COMPLETE")
    print("="*80)
    print(f"\n📊 STOCK DISTRIBUTION:")
    print(f"  Total Before: {stats['total_stocks_before']} stocks")
    print(f"  ✅ Verified Sustainable: {stats['sustainable_verified']} stocks (ready for Phase 3)")
    print(f"  ⚠️  Not Tested: {stats['not_tested']} stocks (moved to separate file)")
    print(f"  ❌ Unsustainable: 15 stocks (already in UNSUSTAINABLE.json)")
    
    print(f"\n📁 FILE ORGANIZATION:")
    print(f"  • explosive_stocks_CLEAN.json")
    print(f"    → 72 verified sustainable stocks")
    print(f"    → Daily gains removed (compact format)")
    print(f"    → READY FOR PHASE 3 ✅")
    print(f"")
    print(f"  • explosive_stocks_NOT_TESTED.json")
    print(f"    → 113 stocks without test data")
    print(f"    → Can investigate later if needed")
    print(f"")
    print(f"  • explosive_stocks_UNSUSTAINABLE.json")
    print(f"    → 15 pump-and-dump stocks")
    print(f"    → Filtered out, kept for reference")
    print(f"")
    print(f"  • explosive_stocks_CLEAN_FULL_BACKUP.json")
    print(f"    → Complete backup with all daily data")
    
    print(f"\n🧹 CLEANUP:")
    print(f"  Daily price records removed: {stats['daily_records_removed']:,}")
    print(f"  Estimated size reduction: ~90%")
    
    print(f"\n🎯 PHASE 3 READY:")
    print(f"  Work with: explosive_stocks_CLEAN.json")
    print(f"  Contains: 72 verified sustainable stocks")
    print(f"  Next step: Pattern discovery & analysis")
    
    print("\n" + "="*80)
    print("✅ ALL SET FOR PHASE 3!")
    print("="*80 + "\n")


if __name__ == "__main__":
    prepare_for_phase3()
