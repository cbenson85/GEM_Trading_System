#!/usr/bin/env python3
"""
Phase 3 Batch Splitter - Divides stocks into batches for parallel processing
"""

import json
import os
import sys
from typing import List, Dict

def split_stocks_into_batches(stocks_file: str, num_batches: int = 5, test_mode: bool = False):
    """
    Split stocks into batches for parallel processing
    
    Args:
        stocks_file: Path to explosive_stocks_CLEAN.json
        num_batches: Number of parallel batches to create
        test_mode: If True, only use first 10 stocks for testing
    """
    print(f"{'='*60}")
    print(f"PHASE 3 BATCH SPLITTER")
    print(f"{'='*60}")
    
    # Load stocks
    with open(stocks_file, 'r') as f:
        data = json.load(f)
    
    # Handle nested structure
    if isinstance(data, dict) and 'stocks' in data:
        all_stocks = data['stocks']
        metadata = {k: v for k, v in data.items() if k != 'stocks'}
    else:
        all_stocks = data if isinstance(data, list) else []
        metadata = {}
    
    print(f"Total stocks loaded: {len(all_stocks)}")
    
    # Test mode: only use first 10 stocks
    if test_mode:
        print(f"TEST MODE: Using only first 10 stocks")
        all_stocks = all_stocks[:10]
        num_batches = min(num_batches, 5)  # Max 5 batches for test
    
    # Calculate batch sizes
    stocks_per_batch = len(all_stocks) // num_batches
    remainder = len(all_stocks) % num_batches
    
    print(f"Creating {num_batches} batches")
    print(f"Stocks per batch: ~{stocks_per_batch}")
    
    # Create output directory
    output_dir = 'batch_inputs'
    os.makedirs(output_dir, exist_ok=True)
    
    # Split stocks into batches
    batches = []
    start_idx = 0
    
    for batch_num in range(num_batches):
        # Calculate batch size (distribute remainder)
        batch_size = stocks_per_batch + (1 if batch_num < remainder else 0)
        
        # Get stocks for this batch
        end_idx = start_idx + batch_size
        batch_stocks = all_stocks[start_idx:end_idx]
        
        # Create batch info
        batch_info = {
            'batch_id': f'batch{batch_num + 1}',
            'batch_number': batch_num + 1,
            'total_batches': num_batches,
            'stocks_count': len(batch_stocks),
            'stocks': batch_stocks,
            'metadata': metadata
        }
        
        # Save batch file
        batch_file = os.path.join(output_dir, f'batch{batch_num + 1}_stocks.json')
        with open(batch_file, 'w') as f:
            json.dump(batch_info, f, indent=2)
        
        batches.append({
            'batch_id': f'batch{batch_num + 1}',
            'file': batch_file,
            'stocks_count': len(batch_stocks),
            'tickers': [s.get('ticker') for s in batch_stocks]
        })
        
        print(f"  Batch {batch_num + 1}: {len(batch_stocks)} stocks → {batch_file}")
        
        # Update start index
        start_idx = end_idx
    
    # Create batch manifest
    manifest = {
        'total_stocks': len(all_stocks),
        'num_batches': num_batches,
        'test_mode': test_mode,
        'batches': batches
    }
    
    manifest_file = os.path.join(output_dir, 'batch_manifest.json')
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ Batch splitting complete!")
    print(f"📁 Batch files saved to: {output_dir}/")
    print(f"📋 Manifest saved to: {manifest_file}")
    
    # Show sample of batches for verification
    print(f"\n📊 Batch Distribution:")
    for batch in batches:
        print(f"  {batch['batch_id']}: {batch['stocks_count']} stocks")
        if test_mode:
            print(f"    Tickers: {', '.join(batch['tickers'][:5])}")
    
    return manifest


def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Split stocks into batches for parallel processing')
    parser.add_argument('stocks_file', help='Path to explosive_stocks_CLEAN.json')
    parser.add_argument('--batches', type=int, default=5, help='Number of batches (default: 5)')
    parser.add_argument('--test', action='store_true', help='Test mode - only use 10 stocks')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.stocks_file):
        print(f"Error: File not found: {args.stocks_file}")
        sys.exit(1)
    
    # Split stocks
    manifest = split_stocks_into_batches(
        args.stocks_file,
        num_batches=args.batches,
        test_mode=args.test
    )
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Upload batch files to GitHub")
    print(f"2. Run parallel workflow to analyze all batches")
    print(f"3. Merge results with phase3_batch_merger.py")


if __name__ == '__main__':
    main()
