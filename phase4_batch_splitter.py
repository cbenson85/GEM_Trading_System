#!/usr/bin/env python3
"""
Phase 4 Batch Splitter - Divides screening results into batches for parallel processing
"""

import json
import os
import sys

def split_into_batches(results_file: str, batch_size: int = 90):
    """
    Split screening results into batches
    """
    print(f"{'='*60}")
    print(f"PHASE 4 BATCH SPLITTER")
    print(f"{'='*60}")
    
    # Load screening results
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    all_stocks = data.get('all_selected_stocks', [])
    runners_up = data.get('all_runners_up', [])
    
    # Combine all stocks for analysis
    all_to_analyze = all_stocks + runners_up
    
    print(f"Total stocks to analyze: {len(all_to_analyze)}")
    print(f"  Selected stocks: {len(all_stocks)}")
    print(f"  Runners-up: {len(runners_up)}")
    
    # Create output directory
    os.makedirs('batch_inputs', exist_ok=True)
    
    # Split into batches
    batches = []
    batch_num = 1
    
    for i in range(0, len(all_to_analyze), batch_size):
        batch = all_to_analyze[i:i + batch_size]
        
        batch_data = {
            'batch_id': f'batch{batch_num}',
            'batch_number': batch_num,
            'stocks_count': len(batch),
            'stocks': batch,
            'metadata': {
                'source': 'phase4_screening',
                'total_batches': (len(all_to_analyze) + batch_size - 1) // batch_size
            }
        }
        
        # Save batch file
        batch_file = f'batch_inputs/batch{batch_num}_stocks.json'
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        batches.append({
            'batch_id': f'batch{batch_num}',
            'file': batch_file,
            'stocks_count': len(batch)
        })
        
        print(f"  Batch {batch_num}: {len(batch)} stocks → {batch_file}")
        batch_num += 1
    
    # Create manifest
    manifest = {
        'total_stocks': len(all_to_analyze),
        'num_batches': len(batches),
        'batch_size': batch_size,
        'batches': batches
    }
    
    manifest_file = 'batch_inputs/batch_manifest.json'
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ Batch splitting complete!")
    print(f"📁 Created {len(batches)} batches")
    print(f"📋 Manifest: {manifest_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python phase4_batch_splitter.py <screening_results.json>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    
    if not os.path.exists(results_file):
        print(f"Error: File not found: {results_file}")
        sys.exit(1)
    
    split_into_batches(results_file)

if __name__ == '__main__':
    main()
