#!/usr/bin/env python3
"""
Phase 3 Correlation Analyzer - FIXED VERSION
Analyzes PRE-explosion patterns to find predictive indicators
"""

import json
import sys
from typing import Dict, List
from collections import defaultdict

def analyze_correlations(merged_file: str):
    """Analyze correlations between PRE-explosion patterns and explosive outcomes"""
    
    print("="*60)
    print("PHASE 3 CORRELATION ANALYSIS - PRE-EXPLOSION PATTERNS")
    print("="*60)
    
    # Load merged data
    with open(merged_file, 'r') as f:
        data = json.load(f)
    
    results = data.get('all_results', [])
    successful = [r for r in results if r.get('analysis_status') == 'complete']
    
    print(f"\nTotal stocks analyzed: {len(results)}")
    print(f"Successful analyses: {len(successful)}")
    
    # Pattern frequencies for PRE-explosion indicators
    pattern_frequencies = defaultdict(lambda: {'count': 0, 'total': 0, 'gains': []})
    
    # Technical patterns
    tech_patterns = {
        'oversold_pre': lambda r: r.get('technical_indicators', {}).get('rsi_oversold_days_pre', 0) > 5,
        'extreme_oversold_pre': lambda r: r.get('technical_indicators', {}).get('rsi_at_explosion', 50) < 30,
        'moderate_oversold_pre': lambda r: 30 <= r.get('technical_indicators', {}).get('rsi_at_explosion', 50) < 40,
        'below_ma20_pre': lambda r: r.get('technical_indicators', {}).get('price_vs_ma20_pct', 0) < -5,
        'below_ma50_pre': lambda r: r.get('technical_indicators', {}).get('price_vs_ma50_pct', 0) < -10,
        'golden_cross_pre': lambda r: r.get('technical_indicators', {}).get('golden_cross_detected', False),
    }
    
    # Volume patterns
    volume_patterns = {
        'accumulation_pre': lambda r: r.get('price_volume_patterns', {}).get('accumulation_detected', False),
        'volume_3x_spike_pre': lambda r: r.get('price_volume_patterns', {}).get('volume_3x_spike_pre', False),
        'volume_5x_spike_pre': lambda r: r.get('price_volume_patterns', {}).get('volume_5x_spike_pre', False),
        'volume_trend_up_pre': lambda r: r.get('technical_indicators', {}).get('volume_trend_up', False),
    }
    
    # Price patterns
    price_patterns = {
        'base_building_pre': lambda r: r.get('price_volume_patterns', {}).get('base_building', False),
        'price_coiling_pre': lambda r: r.get('price_volume_patterns', {}).get('price_coiling', False),
        'narrowing_range_pre': lambda r: r.get('price_volume_patterns', {}).get('narrowing_range', False),
        'higher_lows_pre': lambda r: r.get('price_volume_patterns', {}).get('higher_lows_count', 0) >= 3,
    }
    
    # News/Social patterns (usually quiet before explosion)
    news_patterns = {
        'low_news_volume_pre': lambda r: r.get('news_recent_count_pre', 0) < 5,
        'no_news_acceleration_pre': lambda r: not r.get('news_acceleration_3x_pre', False),
        'low_search_interest_pre': lambda r: r.get('trends_recent_avg_pre', 0) < 25,
    }
    
    # Insider patterns
    insider_patterns = {
        'insider_buying_pre': lambda r: r.get('insider_form4_count_pre', 0) > 0,
        'insider_cluster_pre': lambda r: r.get('insider_cluster_detected_pre', False),
        'high_insider_activity_pre': lambda r: r.get('insider_activity_level_pre', 'none') in ['medium', 'high'],
    }
    
    all_patterns = {**tech_patterns, **volume_patterns, **price_patterns, **news_patterns, **insider_patterns}
    
    # Analyze each stock
    for result in successful:
        gain = result.get('gain_percent', 0)
        
        for pattern_name, pattern_func in all_patterns.items():
            pattern_frequencies[pattern_name]['total'] += 1
            
            try:
                if pattern_func(result):
                    pattern_frequencies[pattern_name]['count'] += 1
                    pattern_frequencies[pattern_name]['gains'].append(gain)
            except Exception as e:
                print(f"  Warning: Error checking pattern {pattern_name}: {e}")
    
    # Calculate correlations
    print("\n" + "="*60)
    print("PRE-EXPLOSION PATTERN FREQUENCIES (What explosive stocks looked like BEFORE)")
    print("="*60)
    
    pattern_stats = []
    
    for pattern, data in pattern_frequencies.items():
        if data['total'] > 0:
            frequency = (data['count'] / data['total']) * 100
            avg_gain = sum(data['gains']) / len(data['gains']) if data['gains'] else 0
            
            pattern_stats.append({
                'pattern': pattern,
                'frequency_percent': frequency,
                'count': data['count'],
                'total': data['total'],
                'avg_gain_when_present': avg_gain
            })
    
    # Sort by frequency
    pattern_stats.sort(key=lambda x: x['frequency_percent'], reverse=True)
    
    print("\n📊 TOP PRE-EXPLOSION PATTERNS (by frequency):")
    print("-" * 60)
    
    for i, stat in enumerate(pattern_stats[:20], 1):
        print(f"{i:2}. {stat['pattern']:30} {stat['frequency_percent']:5.1f}% ({stat['count']}/{stat['total']}) "
              f"Avg gain: {stat['avg_gain_when_present']:.0f}%")
    
    # Identify pattern combinations
    print("\n" + "="*60)
    print("PATTERN COMBINATIONS (What patterns appear together)")
    print("="*60)
    
    combination_stats = defaultdict(lambda: {'count': 0, 'gains': []})
    
    # Check common combinations
    for result in successful:
        gain = result.get('gain_percent', 0)
        
        # Oversold + Accumulation
        if (tech_patterns['oversold_pre'](result) and 
            volume_patterns['accumulation_pre'](result)):
            combination_stats['oversold_accumulation']['count'] += 1
            combination_stats['oversold_accumulation']['gains'].append(gain)
        
        # Base building + Volume trend up
        if (price_patterns['base_building_pre'](result) and
            volume_patterns['volume_trend_up_pre'](result)):
            combination_stats['base_volume_trend']['count'] += 1
            combination_stats['base_volume_trend']['gains'].append(gain)
        
        # Coiling + Low news
        if (price_patterns['price_coiling_pre'](result) and
            news_patterns['low_news_volume_pre'](result)):
            combination_stats['coiling_quiet']['count'] += 1
            combination_stats['coiling_quiet']['gains'].append(gain)
        
        # Oversold + Insider buying
        if (tech_patterns['extreme_oversold_pre'](result) and
            insider_patterns['insider_buying_pre'](result)):
            combination_stats['oversold_insider']['count'] += 1
            combination_stats['oversold_insider']['gains'].append(gain)
    
    print("\n📊 POWERFUL COMBINATIONS:")
    print("-" * 60)
    
    for combo_name, data in combination_stats.items():
        if data['count'] > 0:
            frequency = (data['count'] / len(successful)) * 100
            avg_gain = sum(data['gains']) / len(data['gains'])
            
            combo_display = {
                'oversold_accumulation': 'Oversold + Accumulation',
                'base_volume_trend': 'Base Building + Volume Trend',
                'coiling_quiet': 'Price Coiling + Low News',
                'oversold_insider': 'Extreme Oversold + Insider Buying'
            }
            
            print(f"{combo_display.get(combo_name, combo_name):35} "
                  f"{frequency:5.1f}% ({data['count']}/{len(successful)}) "
                  f"Avg gain: {avg_gain:.0f}%")
    
    # Score distribution
    print("\n" + "="*60)
    print("SCORE DISTRIBUTION (Based on PRE-explosion patterns)")
    print("="*60)
    
    score_ranges = {
        '0-20': [],
        '20-40': [],
        '40-60': [],
        '60-80': [],
        '80-100': []
    }
    
    for result in successful:
        score = result.get('pattern_scores', {}).get('total_score_pre', 0)
        gain = result.get('gain_percent', 0)
        
        if score < 20:
            score_ranges['0-20'].append(gain)
        elif score < 40:
            score_ranges['20-40'].append(gain)
        elif score < 60:
            score_ranges['40-60'].append(gain)
        elif score < 80:
            score_ranges['60-80'].append(gain)
        else:
            score_ranges['80-100'].append(gain)
    
    print("\n📊 GAIN BY PRE-EXPLOSION SCORE:")
    print("-" * 60)
    
    for range_name, gains in score_ranges.items():
        if gains:
            avg_gain = sum(gains) / len(gains)
            print(f"Score {range_name:8} {len(gains):4} stocks, Avg gain: {avg_gain:6.0f}%")
        else:
            print(f"Score {range_name:8}    0 stocks")
    
    # Generate correlation matrix
    output_data = {
        'analysis_type': 'PRE_EXPLOSION_PATTERNS',
        'total_stocks': len(results),
        'successful_analyses': len(successful),
        'pattern_frequencies': {
            name: {
                'frequency_percent': stat['frequency_percent'],
                'count': stat['count'],
                'avg_gain_when_present': stat['avg_gain_when_present']
            }
            for name, stat in [(s['pattern'], s) for s in pattern_stats]
        },
        'top_patterns': [
            {
                'pattern': stat['pattern'],
                'frequency': stat['frequency_percent'],
                'effectiveness': stat['avg_gain_when_present']
            }
            for stat in pattern_stats[:10]
        ],
        'key_findings': []
    }
    
    # Identify key findings
    key_findings = []
    
    # Find most common PRE-explosion patterns
    for stat in pattern_stats[:5]:
        if stat['frequency_percent'] > 50:
            key_findings.append(
                f"{stat['pattern']}: {stat['frequency_percent']:.1f}% of explosive stocks "
                f"showed this BEFORE exploding"
            )
    
    # Find patterns with highest average gains
    gain_sorted = sorted(pattern_stats, key=lambda x: x['avg_gain_when_present'], reverse=True)
    for stat in gain_sorted[:3]:
        if stat['count'] >= 10:  # Only if pattern appears in at least 10 stocks
            key_findings.append(
                f"{stat['pattern']}: Stocks with this PRE-explosion pattern gained "
                f"{stat['avg_gain_when_present']:.0f}% on average"
            )
    
    output_data['key_findings'] = key_findings
    
    # Save correlation matrix
    output_file = 'Verified_Backtest_Data/phase3_correlation_matrix.json'
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS COMPLETE")
    print("="*60)
    print(f"Output saved to: {output_file}")
    print("\nKEY INSIGHTS FOR SCREENING:")
    
    # Print screening recommendations
    print("\n🎯 PATTERNS TO LOOK FOR (Based on PRE-explosion analysis):")
    print("-" * 60)
    
    essential_patterns = []
    valuable_patterns = []
    
    for stat in pattern_stats:
        if stat['frequency_percent'] > 60:
            essential_patterns.append(stat['pattern'])
        elif stat['frequency_percent'] > 40:
            valuable_patterns.append(stat['pattern'])
    
    if essential_patterns:
        print("ESSENTIAL (>60% frequency):")
        for pattern in essential_patterns[:5]:
            print(f"  ✓ {pattern}")
    
    if valuable_patterns:
        print("\nVALUABLE (>40% frequency):")
        for pattern in valuable_patterns[:5]:
            print(f"  ✓ {pattern}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python phase3_correlation_analyzer.py <merged_analysis_file>")
        sys.exit(1)
    
    analyze_correlations(sys.argv[1])
