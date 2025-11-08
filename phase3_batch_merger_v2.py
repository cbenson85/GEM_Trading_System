"""
Phase 3 Batch Merger - Version 2
Properly merges batch results with nested structure extraction

CHANGES FROM PREVIOUS VERSION:
1. Handles nested data structure from comprehensive collector
2. Properly extracts all 150+ data points
3. Adds diagnostic output for missing patterns
4. Compatible with correlation analyzer v2
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

def merge_batch_results(batch_dir):
    """Merge all Phase 3 batch results with proper data extraction"""
    
    print("=" * 60)
    print("PHASE 3 BATCH MERGER - ENHANCED VERSION")
    print("=" * 60)
    
    # Find all batch result files
    batch_files = []
    for filename in os.listdir(batch_dir):
        if filename.startswith('phase3_batch_') and filename.endswith('.json'):
            batch_files.append(os.path.join(batch_dir, filename))
    
    print(f"\nFound {len(batch_files)} batch files to merge")
    
    all_stocks = []
    total_successful = 0
    total_failed = 0
    pattern_tracker = defaultdict(int)
    
    for batch_file in sorted(batch_files):
        print(f"\nProcessing: {os.path.basename(batch_file)}")
        
        with open(batch_file, 'r') as f:
            batch_data = json.load(f)
        
        results = batch_data.get('results', [])
        batch_successful = batch_data.get('successful_analyses', 0)
        
        print(f"  Stocks in batch: {len(results)}")
        print(f"  Successful analyses: {batch_successful}")
        
        # Process each stock result
        for stock_result in results:
            # Extract and flatten the nested structure
            flat_stock = extract_stock_data(stock_result)
            all_stocks.append(flat_stock)
            
            # Track patterns found
            for key, value in flat_stock.items():
                if key.endswith('_pre') and value is True:
                    pattern_tracker[key] += 1
            
            if stock_result.get('analysis_status') == 'complete':
                total_successful += 1
            else:
                total_failed += 1
    
    print("\n" + "=" * 60)
    print("MERGE COMPLETE")
    print("=" * 60)
    print(f"Total stocks processed: {len(all_stocks)}")
    print(f"Successful analyses: {total_successful}")
    print(f"Failed analyses: {total_failed}")
    
    # Show pattern detection rates
    print("\n📊 Pattern Detection Summary:")
    for pattern, count in sorted(pattern_tracker.items(), 
                                key=lambda x: x[1], reverse=True)[:10]:
        pct = count / len(all_stocks) * 100 if all_stocks else 0
        print(f"  {pattern}: {count}/{len(all_stocks)} ({pct:.1f}%)")
    
    # Create merged output
    merged_data = {
        'merge_date': datetime.now().isoformat(),
        'total_batches': len(batch_files),
        'total_stocks': len(all_stocks),
        'successful_analyses': total_successful,
        'failed_analyses': total_failed,
        'all_stocks': all_stocks  # Using all_stocks to match correlation analyzer
    }
    
    # Save merged file
    output_file = 'Verified_Backtest_Data/phase3_merged_analysis.json'
    os.makedirs('Verified_Backtest_Data', exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(merged_data, f, indent=2)
    
    print(f"\n✅ Merged data saved to: {output_file}")
    
    # Run diagnostic
    run_diagnostic(all_stocks)
    
    return merged_data

def extract_stock_data(stock_result):
    """Extract and flatten nested stock data structure"""
    
    # Start with basic info
    flat_stock = {
        'ticker': stock_result.get('ticker'),
        'year_discovered': stock_result.get('year_discovered'),
        'entry_date': stock_result.get('entry_date'),
        'catalyst_date': stock_result.get('catalyst_date'),
        'entry_price': stock_result.get('entry_price'),
        'peak_price': stock_result.get('peak_price'),
        'gain_percent': stock_result.get('gain_percent'),
        'final_gain_percent': stock_result.get('gain_percent', 0),
        'days_to_peak': stock_result.get('days_to_peak'),
        'sector': stock_result.get('sector'),
        'analysis_status': stock_result.get('analysis_status'),
        'data_source': stock_result.get('data_source', 'Unknown'),
        'price_change_180d': None  # Would need historical calculation
    }
    
    # Extract price_volume_patterns
    pv = stock_result.get('price_volume_patterns', {})
    flat_stock.update({
        'volume_avg_90d_pre': pv.get('volume_avg_90d_pre', 0),
        'volume_spike_3x_pre': pv.get('volume_3x_spike_pre', False),
        'volume_spike_5x_pre': pv.get('volume_5x_spike_pre', False),
        'volume_spike_10x_pre': pv.get('volume_10x_spike_pre', False),
        'volume_spike_count_pre': pv.get('volume_spike_count_pre', 0),
        'accumulation_detected_pre': pv.get('accumulation_detected', False),
        'higher_lows_count_pre': pv.get('higher_lows_count', 0),
        'narrowing_range_pre': pv.get('narrowing_range', False),
        'base_building_pre': pv.get('base_building', False),
        'price_coiling_pre': pv.get('price_coiling', False)
    })
    
    # Extract technical_indicators
    ti = stock_result.get('technical_indicators', {})
    flat_stock.update({
        'rsi_14_min_pre': ti.get('rsi_14_min_pre', 50),
        'rsi_14_max_pre': ti.get('rsi_14_max_pre', 50),
        'rsi_oversold_days_pre': ti.get('rsi_oversold_days_pre', 0),
        'rsi_overbought_days_pre': ti.get('rsi_overbought_days_pre', 0),
        'rsi_at_explosion': ti.get('rsi_at_explosion', 50),
        'rsi_oversold_depth_pre': ti.get('rsi_14_min_pre', 50),
        'ma_20_pre': ti.get('ma_20_pre', 0),
        'ma_50_pre': ti.get('ma_50_pre', 0),
        'price_vs_ma20_pct_pre': ti.get('price_vs_ma20_pct', 0),
        'price_vs_ma50_pct_pre': ti.get('price_vs_ma50_pct', 0),
        'price_above_ma20_pre': ti.get('price_above_ma20_pre', False),
        'price_above_ma50_pre': ti.get('price_above_ma50_pre', False),
        'golden_cross_detected_pre': ti.get('golden_cross_detected', False),
        'volume_trend_up_pre': ti.get('volume_trend_up', False)
    })
    
    # Extract news data (flat fields)
    flat_stock.update({
        'news_baseline_count_pre': stock_result.get('news_baseline_count_pre', 0),
        'news_recent_count_pre': stock_result.get('news_recent_count_pre', 0),
        'news_acceleration_ratio_pre': stock_result.get('news_acceleration_ratio_pre', 0),
        'news_acceleration_3x_pre': stock_result.get('news_acceleration_3x_pre', False),
        'news_acceleration_5x_pre': stock_result.get('news_acceleration_5x_pre', False),
        'news_pattern_score_pre': stock_result.get('news_pattern_score_pre', 0)
    })
    
    # Extract trends data (flat fields)
    flat_stock.update({
        'trends_baseline_avg_pre': stock_result.get('trends_baseline_avg_pre', 0),
        'trends_recent_avg_pre': stock_result.get('trends_recent_avg_pre', 0),
        'trends_max_interest_pre': stock_result.get('trends_max_interest_pre', 0),
        'trends_acceleration_ratio_pre': stock_result.get('trends_acceleration_ratio_pre', 0),
        'trends_spike_2x_pre': stock_result.get('trends_spike_2x_pre', False),
        'trends_spike_5x_pre': stock_result.get('trends_spike_5x_pre', False),
        'trends_high_interest_pre': stock_result.get('trends_high_interest_pre', False),
        'trends_pattern_score_pre': stock_result.get('trends_pattern_score_pre', 0)
    })
    
    # Extract insider data (flat fields)
    flat_stock.update({
        'insider_form4_count_pre': stock_result.get('insider_form4_count_pre', 0),
        'insider_filing_count_pre': stock_result.get('insider_filing_count_pre', 0),
        'insider_cluster_detected_pre': stock_result.get('insider_cluster_detected_pre', False),
        'insider_pattern_score_pre': stock_result.get('insider_pattern_score_pre', 0),
        'insider_activity_level_pre': stock_result.get('insider_activity_level_pre', 'none'),
        'insider_bullish_signal_pre': stock_result.get('insider_bullish_signal_pre', False)
    })
    
    # Extract pattern_scores
    ps = stock_result.get('pattern_scores', {})
    flat_stock.update({
        'volume_score_pre': ps.get('volume_score_pre', 0),
        'technical_score_pre': ps.get('technical_score_pre', 0),
        'news_score_pre': ps.get('news_score_pre', 0),
        'trends_score_pre': ps.get('trends_score_pre', 0),
        'insider_score_pre': ps.get('insider_score_pre', 0),
        'total_score_pre': ps.get('total_score_pre', 0),
        'signal_strength_pre': ps.get('signal_strength_pre', 'WEAK'),
        'has_primary_signal_pre': ps.get('has_primary_signal_pre', False),
        'pattern_count_pre': ps.get('pattern_count', 0)
    })
    
    # Add placeholders for patterns not yet implemented
    flat_stock.update({
        'macd_bullish_cross_pre': False,
        'bb_squeeze_pre': False,
        'support_bounce_pre': False,
        'resistance_test_pre': False
    })
    
    return flat_stock

def run_diagnostic(stocks):
    """Run diagnostic on merged data"""
    
    print("\n" + "=" * 60)
    print("DATA DIAGNOSTIC")
    print("=" * 60)
    
    if not stocks:
        print("No stocks to analyze")
        return
    
    # Check field population
    sample = stocks[0]
    field_stats = {}
    
    for field in sample.keys():
        populated = 0
        for stock in stocks:
            value = stock.get(field)
            if value not in [None, False, 0, '', 'none', 'WEAK']:
                populated += 1
        
        field_stats[field] = {
            'populated': populated,
            'percentage': populated / len(stocks) * 100
        }
    
    # Show fields with good data
    print("\n✅ Fields with data (>10% populated):")
    good_fields = [(k, v) for k, v in field_stats.items() 
                   if v['percentage'] > 10]
    for field, stats in sorted(good_fields, 
                               key=lambda x: x[1]['percentage'], 
                               reverse=True)[:15]:
        print(f"  {field}: {stats['populated']}/{len(stocks)} "
              f"({stats['percentage']:.1f}%)")
    
    # Show fields with no data
    print("\n❌ Fields with NO data:")
    empty_fields = [k for k, v in field_stats.items() 
                   if v['percentage'] == 0]
    for field in empty_fields[:10]:
        print(f"  {field}")
    
    # Score distribution
    scores = [s.get('total_score_pre', 0) for s in stocks]
    if scores:
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        print(f"\n📊 Score Statistics:")
        print(f"  Average: {avg_score:.1f}")
        print(f"  Max: {max_score}")
        print(f"  Min: {min_score}")
        print(f"  Stocks scoring 50+: {sum(1 for s in scores if s >= 50)}")
        print(f"  Stocks scoring 70+: {sum(1 for s in scores if s >= 70)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python phase3_batch_merger.py <batch_results_directory>")
        sys.exit(1)
    
    batch_dir = sys.argv[1]
    merge_batch_results(batch_dir)
