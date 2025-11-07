#!/usr/bin/env python3
"""
Phase 4 Batch Merger - Combines results from parallel batches
"""

import json
import os
import sys
from glob import glob
from datetime import datetime

def merge_batch_results(results_dir: str):
    """Merge all batch results"""
    print(f"{'='*60}")
    print(f"PHASE 4 BATCH MERGER")
    print(f"{'='*60}")
    
    # Find batch files
    batch_files = glob(os.path.join(results_dir, 'phase4_batch_*.json'))
    
    if not batch_files:
        print("❌ No batch files found!")
        sys.exit(1)
    
    print(f"Found {len(batch_files)} batch files")
    
    # Initialize merged data
    merged = {
        'merge_date': datetime.now().isoformat(),
        'total_batches': len(batch_files),
        'total_stocks': 0,
        'classifications': {
            'TRUE_POSITIVE': 0,
            'MODERATE_WIN': 0,
            'SMALL_WIN': 0,
            'BREAK_EVEN': 0,
            'LOSS': 0,
            'NO_DATA': 0,
            'ERROR': 0
        },
        'all_stocks': []
    }
    
    # Process each batch
    for batch_file in sorted(batch_files):
        print(f"\n📁 Processing: {os.path.basename(batch_file)}")
        
        with open(batch_file, 'r') as f:
            batch_data = json.load(f)
        
        results = batch_data.get('results', [])
        
        for stock in results:
            classification = stock.get('final_classification', 'ERROR')
            merged['classifications'][classification] = merged['classifications'].get(classification, 0) + 1
            merged['all_stocks'].append(stock)
        
        merged['total_stocks'] += len(results)
        print(f"  Added {len(results)} stocks")
    
    # Calculate metrics
    if merged['total_stocks'] > 0:
        merged['hit_rate'] = merged['classifications']['TRUE_POSITIVE'] / merged['total_stocks']
        merged['win_rate'] = (merged['classifications']['TRUE_POSITIVE'] + 
                              merged['classifications']['MODERATE_WIN']) / merged['total_stocks']
    else:
        merged['hit_rate'] = 0
        merged['win_rate'] = 0
    
    # Save merged results
    output_dir = 'Verified_Backtest_Data'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'phase4_merged_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"MERGE COMPLETE")
    print(f"Total stocks: {merged['total_stocks']}")
    print(f"True Positives: {merged['classifications']['TRUE_POSITIVE']}")
    print(f"Hit Rate: {merged['hit_rate']:.1%}")
    print(f"Output: {output_file}")
    print(f"{'='*60}")
    
    return merged

def main():
    if len(sys.argv) < 2:
        results_dir = 'batch_results'
    else:
        results_dir = sys.argv[1]
    
    if not os.path.exists(results_dir):
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)
    
    merge_batch_results(results_dir)

if __name__ == '__main__':
    main()
