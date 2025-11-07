#!/usr/bin/env python3
"""
Phase 3 Batch Merger - Combines results from parallel batch analyses
"""

import json
import os
import sys
from typing import Dict, List
from datetime import datetime

def merge_batch_results(results_dir: str, output_dir: str = 'Verified_Backtest_Data'):
    """
    Merge all batch analysis results into a single file
    """
    print(f"{'='*60}")
    print(f"PHASE 3 BATCH MERGER")
    print(f"{'='*60}")
    print(f"Results directory: {results_dir}")
    
    # Find all batch result files
    batch_files = []
    for file in os.listdir(results_dir):
        if file.startswith('phase3_batch_') and file.endswith('.json'):
            batch_files.append(os.path.join(results_dir, file))
    
    batch_files.sort()
    print(f"Found {len(batch_files)} batch result files")
    
    if not batch_files:
        print("❌ No batch results found!")
        sys.exit(1)
    
    # Initialize merged results
    merged = {
        'analysis_date': datetime.now().isoformat(),
        'merge_date': datetime.now().isoformat(),
        'total_batches': len(batch_files),
        'total_stocks': 0,
        'successful_analyses': 0,
        'failed_analyses': 0,
        'all_stocks': [],
        'pattern_summary': {},
        'batch_summaries': []
    }
    
    # Pattern counters
    pattern_counts = {
        'volume_3x_spike': 0,
        'volume_5x_spike': 0,
        'volume_10x_spike': 0,
        'rsi_oversold': 0,
        'rsi_overbought': 0,
        'breakout_20d_high': 0,
        'breakout_52w_high': 0,
        'accumulation_detected': 0,
        'ma_20_cross': 0,
        'price_above_all_ma': 0,
        'spy_outperformance_20': 0,
        'spy_outperformance_10': 0,
        'has_primary_signal': 0,
        'has_secondary_signals': 0
    }
    
    # Process each batch file
    for batch_file in batch_files:
        print(f"\n📁 Processing: {os.path.basename(batch_file)}")
        
        with open(batch_file, 'r') as f:
            batch_data = json.load(f)
        
        # Extract batch info
        batch_id = batch_data.get('batch_id', 'unknown')
        batch_summary = {
            'batch_id': batch_id,
            'stocks_count': batch_data.get('total_stocks', 0),
            'successful': 0,
            'failed': 0
        }
        
        # Process each stock in batch
        for stock in batch_data.get('stocks_analyzed', []):
            merged['all_stocks'].append(stock)
            merged['total_stocks'] += 1
            
            if stock.get('analysis_status') == 'complete':
                merged['successful_analyses'] += 1
                batch_summary['successful'] += 1
                
                # Count patterns
                pv = stock.get('price_volume_patterns', {})
                ti = stock.get('technical_indicators', {})
                mc = stock.get('market_context', {})
                ps = stock.get('pattern_scores', {})
                
                # Volume patterns
                if pv.get('volume_3x_spike'):
                    pattern_counts['volume_3x_spike'] += 1
                if pv.get('volume_5x_spike'):
                    pattern_counts['volume_5x_spike'] += 1
                if pv.get('volume_10x_spike'):
                    pattern_counts['volume_10x_spike'] += 1
                
                # Price patterns
                if pv.get('breakout_20d_high'):
                    pattern_counts['breakout_20d_high'] += 1
                if pv.get('breakout_52w_high'):
                    pattern_counts['breakout_52w_high'] += 1
                if pv.get('accumulation_detected'):
                    pattern_counts['accumulation_detected'] += 1
                
                # Technical indicators
                if ti.get('rsi_oversold_days', 0) > 0:
                    pattern_counts['rsi_oversold'] += 1
                if ti.get('rsi_overbought_days', 0) > 0:
                    pattern_counts['rsi_overbought'] += 1
                if ti.get('ma_20_cross'):
                    pattern_counts['ma_20_cross'] += 1
                if ti.get('price_above_all_ma'):
                    pattern_counts['price_above_all_ma'] += 1
                
                # Market context
                if mc.get('spy_outperformance', 0) > 20:
                    pattern_counts['spy_outperformance_20'] += 1
                elif mc.get('spy_outperformance', 0) > 10:
                    pattern_counts['spy_outperformance_10'] += 1
                
                # Signal counts
                if ps.get('has_primary_signal'):
                    pattern_counts['has_primary_signal'] += 1
                if ps.get('secondary_signal_count', 0) >= 2:
                    pattern_counts['has_secondary_signals'] += 1
            else:
                merged['failed_analyses'] += 1
                batch_summary['failed'] += 1
        
        merged['batch_summaries'].append(batch_summary)
        print(f"  ✅ Processed {batch_summary['stocks_count']} stocks")
        print(f"  Success: {batch_summary['successful']}, Failed: {batch_summary['failed']}")
    
    # Calculate pattern frequencies
    if merged['successful_analyses'] > 0:
        merged['pattern_summary'] = {}
        for pattern, count in pattern_counts.items():
            merged['pattern_summary'][pattern] = {
                'count': count,
                'frequency_percent': round(count / merged['successful_analyses'] * 100, 1)
            }
    
    # Sort patterns by frequency
    sorted_patterns = sorted(
        merged['pattern_summary'].items(),
        key=lambda x: x[1]['frequency_percent'],
        reverse=True
    )
    
    # Save merged results
    output_file = os.path.join(output_dir, 'phase3_merged_analysis.json')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    # Display summary
    print(f"\n{'='*60}")
    print(f"MERGE COMPLETE")
    print(f"{'='*60}")
    print(f"📊 Summary Statistics:")
    print(f"  Total stocks: {merged['total_stocks']}")
    print(f"  Successful analyses: {merged['successful_analyses']}")
    print(f"  Failed analyses: {merged['failed_analyses']}")
    print(f"  Success rate: {merged['successful_analyses']/merged['total_stocks']*100:.1f}%")
    
    print(f"\n📈 Top Patterns Found:")
    for i, (pattern, info) in enumerate(sorted_patterns[:10], 1):
        print(f"  {i:2d}. {pattern:25s}: {info['frequency_percent']:5.1f}% ({info['count']} stocks)")
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return merged


def main():
    """
    Main entry point
    """
    if len(sys.argv) < 2:
        print("Usage: python phase3_batch_merger.py <results_directory>")
        print("Example: python phase3_batch_merger.py batch_results/")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    
    if not os.path.exists(results_dir):
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)
    
    # Merge results
    merged = merge_batch_results(results_dir)
    
    print(f"\n✅ Merge complete!")
    print(f"Next step: Run phase3_correlation_analyzer.py to build correlation matrix")


if __name__ == '__main__':
    main()
