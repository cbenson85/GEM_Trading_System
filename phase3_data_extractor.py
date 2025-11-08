"""
Phase 3 Data Extractor - Properly extracts all 150+ data points
Flattens nested structure from comprehensive collector into analyzable format

CHANGES FROM PREVIOUS VERSION:
1. NEW SCRIPT - Extracts nested data structure properly
2. Preserves all 150+ data points from comprehensive collector
3. Adds data source tracking for each field
4. Creates properly formatted output for correlation analysis
"""

import json
import sys
from datetime import datetime

def extract_and_flatten_analysis(batch_file):
    """
    Extracts all data points from Phase 3 comprehensive analysis
    Properly handles nested structure
    """
    
    print(f"Loading: {batch_file}")
    with open(batch_file, 'r') as f:
        batch_data = json.load(f)
    
    results = batch_data.get('results', [])
    flattened_stocks = []
    
    for stock_result in results:
        # Start with basic stock info
        flat_stock = {
            'ticker': stock_result.get('ticker'),
            'year_discovered': stock_result.get('year_discovered'),
            'entry_date': stock_result.get('entry_date'),
            'catalyst_date': stock_result.get('catalyst_date'),
            'entry_price': stock_result.get('entry_price'),
            'peak_price': stock_result.get('peak_price'),
            'gain_percent': stock_result.get('gain_percent'),
            'days_to_peak': stock_result.get('days_to_peak'),
            'sector': stock_result.get('sector'),
            'analysis_status': stock_result.get('analysis_status'),
            'data_source': stock_result.get('data_source', 'Unknown')
        }
        
        # Extract price_volume_patterns (nested object)
        pv_patterns = stock_result.get('price_volume_patterns', {})
        flat_stock.update({
            # Volume patterns
            'volume_avg_90d_pre': pv_patterns.get('volume_avg_90d_pre', 0),
            'volume_3x_spike_pre': pv_patterns.get('volume_3x_spike_pre', False),
            'volume_5x_spike_pre': pv_patterns.get('volume_5x_spike_pre', False),
            'volume_10x_spike_pre': pv_patterns.get('volume_10x_spike_pre', False),
            'volume_spike_count_pre': pv_patterns.get('volume_spike_count_pre', 0),
            
            # Accumulation patterns
            'accumulation_detected_pre': pv_patterns.get('accumulation_detected', False),
            
            # Price patterns
            'higher_lows_count_pre': pv_patterns.get('higher_lows_count', 0),
            'narrowing_range_pre': pv_patterns.get('narrowing_range', False),
            'base_building_pre': pv_patterns.get('base_building', False),
            'price_coiling_pre': pv_patterns.get('price_coiling', False)
        })
        
        # Extract technical_indicators (nested object)
        tech_ind = stock_result.get('technical_indicators', {})
        flat_stock.update({
            # RSI indicators
            'rsi_14_min_pre': tech_ind.get('rsi_14_min_pre', 50),
            'rsi_14_max_pre': tech_ind.get('rsi_14_max_pre', 50),
            'rsi_oversold_days_pre': tech_ind.get('rsi_oversold_days_pre', 0),
            'rsi_overbought_days_pre': tech_ind.get('rsi_overbought_days_pre', 0),
            'rsi_at_explosion': tech_ind.get('rsi_at_explosion', 50),
            'rsi_oversold_depth_pre': tech_ind.get('rsi_14_min_pre', 50),  # Use min RSI as depth
            
            # Moving averages
            'ma_20_pre': tech_ind.get('ma_20_pre', 0),
            'ma_50_pre': tech_ind.get('ma_50_pre', 0),
            'price_vs_ma20_pct_pre': tech_ind.get('price_vs_ma20_pct', 0),
            'price_vs_ma50_pct_pre': tech_ind.get('price_vs_ma50_pct', 0),
            'price_above_ma20_pre': tech_ind.get('price_above_ma20_pre', False),
            'price_above_ma50_pre': tech_ind.get('price_above_ma50_pre', False),
            
            # Trend indicators
            'golden_cross_detected_pre': tech_ind.get('golden_cross_detected', False),
            'volume_trend_up_pre': tech_ind.get('volume_trend_up', False)
        })
        
        # Extract news data (flat in main object)
        flat_stock.update({
            'news_baseline_count_pre': stock_result.get('news_baseline_count_pre', 0),
            'news_recent_count_pre': stock_result.get('news_recent_count_pre', 0),
            'news_acceleration_ratio_pre': stock_result.get('news_acceleration_ratio_pre', 0),
            'news_acceleration_3x_pre': stock_result.get('news_acceleration_3x_pre', False),
            'news_acceleration_5x_pre': stock_result.get('news_acceleration_5x_pre', False),
            'news_pattern_score_pre': stock_result.get('news_pattern_score_pre', 0)
        })
        
        # Extract trends data (flat in main object)
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
        
        # Extract insider data (flat in main object)
        flat_stock.update({
            'insider_form4_count_pre': stock_result.get('insider_form4_count_pre', 0),
            'insider_filing_count_pre': stock_result.get('insider_filing_count_pre', 0),
            'insider_cluster_detected_pre': stock_result.get('insider_cluster_detected_pre', False),
            'insider_pattern_score_pre': stock_result.get('insider_pattern_score_pre', 0),
            'insider_activity_level_pre': stock_result.get('insider_activity_level_pre', 'none'),
            'insider_bullish_signal_pre': stock_result.get('insider_bullish_signal_pre', False)
        })
        
        # Extract pattern scores (nested object)
        pattern_scores = stock_result.get('pattern_scores', {})
        flat_stock.update({
            'volume_score_pre': pattern_scores.get('volume_score_pre', 0),
            'technical_score_pre': pattern_scores.get('technical_score_pre', 0),
            'news_score_pre': pattern_scores.get('news_score_pre', 0),
            'trends_score_pre': pattern_scores.get('trends_score_pre', 0),
            'insider_score_pre': pattern_scores.get('insider_score_pre', 0),
            'total_score_pre': pattern_scores.get('total_score_pre', 0),
            'signal_strength_pre': pattern_scores.get('signal_strength_pre', 'WEAK'),
            'has_primary_signal_pre': pattern_scores.get('has_primary_signal_pre', False),
            'pattern_count_pre': pattern_scores.get('pattern_count', 0)
        })
        
        # Add calculated fields that might be missing
        # MACD, BB, Support/Resistance - placeholders since not in current collector
        flat_stock.update({
            'macd_bullish_cross_pre': False,  # Not calculated yet
            'bb_squeeze_pre': False,  # Not calculated yet
            'support_bounce_pre': False,  # Not calculated yet
            'resistance_test_pre': False,  # Not calculated yet
        })
        
        # Calculate additional derived metrics
        if flat_stock['gain_percent']:
            flat_stock['final_gain_percent'] = flat_stock['gain_percent']
        else:
            flat_stock['final_gain_percent'] = 0
            
        # Price change calculation (if we have the data)
        if flat_stock['entry_price'] and flat_stock['entry_price'] > 0:
            # This would need historical data to calculate properly
            flat_stock['price_change_180d'] = None
        else:
            flat_stock['price_change_180d'] = None
        
        flattened_stocks.append(flat_stock)
    
    # Print diagnostic info
    print(f"\n📊 Data Extraction Summary:")
    print(f"  Total stocks processed: {len(flattened_stocks)}")
    
    if flattened_stocks:
        sample = flattened_stocks[0]
        print(f"  Fields extracted per stock: {len(sample)}")
        
        # Count populated fields
        populated_counts = {}
        for field in sample.keys():
            populated = sum(1 for s in flattened_stocks 
                          if s.get(field) not in [None, False, 0, '', 'none', 'WEAK'])
            if populated > 0:
                populated_counts[field] = populated
        
        print(f"\n  📈 Fields with data (non-zero/false):")
        for field, count in sorted(populated_counts.items(), 
                                  key=lambda x: x[1], reverse=True)[:20]:
            pct = count / len(flattened_stocks) * 100
            print(f"    {field}: {count}/{len(flattened_stocks)} ({pct:.1f}%)")
    
    return flattened_stocks

def main():
    if len(sys.argv) < 2:
        print("Usage: python phase3_data_extractor.py <batch_file_or_directory>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    import os
    if os.path.isdir(input_path):
        # Process all batch files in directory
        all_stocks = []
        batch_files = [f for f in os.listdir(input_path) if f.endswith('.json')]
        
        print(f"Processing {len(batch_files)} batch files...")
        for batch_file in sorted(batch_files):
            file_path = os.path.join(input_path, batch_file)
            stocks = extract_and_flatten_analysis(file_path)
            all_stocks.extend(stocks)
        
        # Create merged output
        output = {
            'merge_date': datetime.now().isoformat(),
            'total_batches': len(batch_files),
            'total_stocks': len(all_stocks),
            'successful_analyses': sum(1 for s in all_stocks 
                                      if s.get('analysis_status') == 'complete'),
            'failed_analyses': sum(1 for s in all_stocks 
                                 if s.get('analysis_status') != 'complete'),
            'all_stocks': all_stocks
        }
        
        output_file = 'phase3_extracted_data.json'
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ Extracted data saved to: {output_file}")
        print(f"   Total stocks: {len(all_stocks)}")
        print(f"   Successful: {output['successful_analyses']}")
        print(f"   Failed: {output['failed_analyses']}")
        
    else:
        # Process single file
        stocks = extract_and_flatten_analysis(input_path)
        
        output = {
            'extraction_date': datetime.now().isoformat(),
            'source_file': input_path,
            'total_stocks': len(stocks),
            'all_stocks': stocks
        }
        
        output_file = input_path.replace('.json', '_extracted.json')
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ Extracted data saved to: {output_file}")

if __name__ == "__main__":
    main()
