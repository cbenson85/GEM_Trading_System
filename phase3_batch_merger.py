#!/usr/bin/env python3
"""
Phase 3 Batch Merger - Combines results from all parallel batches
"""

import json
import os
import sys
from glob import glob
from datetime import datetime

def merge_batch_results(results_dir: str, output_dir: str = 'Verified_Backtest_Data'):
    """
    Merge all batch results into a single file
    """
    print(f"{'='*60}")
    print(f"PHASE 3 BATCH MERGER")
    print(f"{'='*60}")
    print(f"Results directory: {results_dir}")
    
    # Find all batch result files
    batch_files = glob(os.path.join(results_dir, 'phase3_batch_*.json'))
    
    if not batch_files:
        print("❌ No batch result files found!")
        sys.exit(1)
    
    print(f"Found {len(batch_files)} batch result files")
    
    # Initialize merged data
    merged = {
        'merge_date': datetime.now().isoformat(),
        'total_batches': len(batch_files),
        'total_stocks': 0,
        'successful_analyses': 0,
        'failed_analyses': 0,
        'all_stocks': []
    }
    
    # Process each batch
    for batch_file in sorted(batch_files):
        print(f"\n📁 Processing: {os.path.basename(batch_file)}")
        
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
            
            # Debug: Print what's in the batch
            print(f"  Batch keys: {list(batch_data.keys())}")
            
            # Extract stocks from results
            batch_results = batch_data.get('results', [])
            batch_total = len(batch_results)
            
            # Check analysis status of each stock
            batch_successful = 0
            batch_failed = 0
            batch_unknown = 0
            
            for stock in batch_results:
                status = stock.get('analysis_status', 'unknown')
                if status == 'complete':
                    batch_successful += 1
                elif status in ['error', 'error_missing_data']:
                    batch_failed += 1
                else:
                    batch_unknown += 1
                    print(f"    Stock {stock.get('ticker', 'UNKNOWN')} has status: {status}")
            
            print(f"  Batch contains {batch_total} stocks")
            print(f"  Success: {batch_successful}, Failed: {batch_failed}, Unknown: {batch_unknown}")
            
            # Add to merged data
            merged['total_stocks'] += batch_total
            merged['successful_analyses'] += batch_successful
            merged['failed_analyses'] += batch_failed
            merged['all_stocks'].extend(batch_results)
            
        except Exception as e:
            print(f"  ❌ Error processing batch: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"MERGE COMPLETE")
    print(f"{'='*60}")
    print(f"📊 Summary Statistics:")
    print(f"  Total stocks: {merged['total_stocks']}")
    print(f"  Successful analyses: {merged['successful_analyses']}")
    print(f"  Failed analyses: {merged['failed_analyses']}")
    
    # Calculate success rate safely
    if merged['total_stocks'] > 0:
        success_rate = merged['successful_analyses'] / merged['total_stocks'] * 100
        print(f"  Success rate: {success_rate:.1f}%")
    else:
        print(f"  Success rate: N/A (no stocks processed)")
        print("\n⚠️ WARNING: No stocks were processed!")
        print("Check that:")
        print("  1. The comprehensive collector is running properly")
        print("  2. The batch splitter created valid batch files")
        print("  3. All required analyzer scripts are present")
    
    # Save merged results even if empty
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'phase3_merged_analysis.json')
    
    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    print(f"\n💾 Merged data saved to: {output_file}")
    
    # Analyze patterns if we have successful analyses
    if merged['successful_analyses'] > 0:
        analyze_patterns(merged)
    else:
        print("\n⚠️ No successful analyses to analyze patterns")
    
    return merged

def analyze_patterns(merged_data: dict):
    """
    Quick analysis of patterns found
    """
    print(f"\n📊 PATTERN ANALYSIS")
    print(f"{'='*60}")
    
    successful_stocks = [s for s in merged_data['all_stocks'] 
                        if s.get('analysis_status') == 'complete']
    
    if not successful_stocks:
        print("No successful stocks to analyze")
        return
    
    # Count pattern occurrences
    patterns = {
        'volume_3x_spike': 0,
        'volume_5x_spike': 0,
        'volume_10x_spike': 0,
        'rsi_oversold': 0,
        'breakout_20d': 0,
        'news_acceleration_3x': 0,
        'trends_spike_2x': 0,
        'insider_cluster': 0
    }
    
    for stock in successful_stocks:
        pv = stock.get('price_volume_patterns', {})
        ti = stock.get('technical_indicators', {})
        
        if pv.get('volume_3x_spike'):
            patterns['volume_3x_spike'] += 1
        if pv.get('volume_5x_spike'):
            patterns['volume_5x_spike'] += 1
        if pv.get('volume_10x_spike'):
            patterns['volume_10x_spike'] += 1
        if pv.get('breakout_20d_high'):
            patterns['breakout_20d'] += 1
        if ti.get('rsi_oversold_days', 0) > 0:
            patterns['rsi_oversold'] += 1
        if stock.get('news_acceleration_3x'):
            patterns['news_acceleration_3x'] += 1
        if stock.get('trends_spike_2x'):
            patterns['trends_spike_2x'] += 1
        if stock.get('insider_cluster_detected'):
            patterns['insider_cluster'] += 1
    
    # Display pattern frequencies
    total = len(successful_stocks)
    print(f"Patterns found in {total} successful analyses:\n")
    
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            freq = count / total * 100
            print(f"  {pattern:25s}: {count:3d} stocks ({freq:5.1f}%)")
    
    print(f"{'='*60}")

def main():
    """
    Main entry point
    """
    if len(sys.argv) < 2:
        # Default to batch_results directory
        results_dir = 'batch_results'
        if not os.path.exists(results_dir):
            print(f"Error: Results directory not found: {results_dir}")
            print("Usage: python phase3_batch_merger.py <results_directory>")
            sys.exit(1)
    else:
        results_dir = sys.argv[1]
    
    if not os.path.exists(results_dir):
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)
    
    # Merge results
    merged = merge_batch_results(results_dir)
    
    print("\n✅ Batch merge complete!")

if __name__ == '__main__':
    main()
