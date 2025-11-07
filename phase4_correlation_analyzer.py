#!/usr/bin/env python3
"""
Phase 4 Correlation Analyzer - Finds patterns in real-world screening results
"""

import json
import os
from datetime import datetime

def analyze_correlations():
    """Analyze correlations between screening scores and outcomes"""
    print(f"{'='*60}")
    print(f"PHASE 4 CORRELATION ANALYZER")
    print(f"{'='*60}")
    
    # Load merged data
    merged_file = 'Verified_Backtest_Data/phase4_merged_analysis.json'
    
    with open(merged_file, 'r') as f:
        data = json.load(f)
    
    all_stocks = data.get('all_stocks', [])
    
    print(f"Analyzing {len(all_stocks)} stocks")
    
    # Initialize correlation matrix
    correlation_matrix = {
        'generated_date': datetime.now().isoformat(),
        'total_stocks': len(all_stocks),
        'true_positives': data['classifications']['TRUE_POSITIVE'],
        'hit_rate': data.get('hit_rate', 0),
        'win_rate': data.get('win_rate', 0),
        'pattern_correlations': {},
        'score_correlations': {},
        'top_patterns': [],
        'key_findings': []
    }
    
    # Analyze score thresholds
    score_analysis = analyze_score_thresholds(all_stocks)
    correlation_matrix['score_correlations'] = score_analysis
    
    # Analyze pattern effectiveness
    pattern_analysis = analyze_pattern_effectiveness(all_stocks)
    correlation_matrix['pattern_correlations'] = pattern_analysis
    
    # Find top patterns
    top_patterns = find_top_patterns(pattern_analysis)
    correlation_matrix['top_patterns'] = top_patterns
    
    # Extract key findings
    findings = extract_key_findings(all_stocks, score_analysis, pattern_analysis)
    correlation_matrix['key_findings'] = findings
    
    # Save correlation matrix
    output_file = 'Verified_Backtest_Data/phase4_correlation_matrix.json'
    with open(output_file, 'w') as f:
        json.dump(correlation_matrix, f, indent=2)
    
    print(f"\n✅ Correlation analysis complete")
    print(f"Output: {output_file}")
    
    # Display summary
    print(f"\n📊 KEY FINDINGS:")
    for finding in findings[:5]:
        print(f"  • {finding}")
    
    return correlation_matrix

def analyze_score_thresholds(stocks):
    """Analyze effectiveness of different score thresholds"""
    thresholds = [60, 75, 90, 105, 120, 135, 150]
    analysis = {}
    
    for threshold in thresholds:
        above_threshold = [s for s in stocks if s.get('screening_score', 0) >= threshold]
        
        if above_threshold:
            true_positives = sum(1 for s in above_threshold 
                               if s.get('final_classification') == 'TRUE_POSITIVE')
            
            hit_rate = true_positives / len(above_threshold) if above_threshold else 0
            
            analysis[f'score_{threshold}'] = {
                'threshold': threshold,
                'stocks_above': len(above_threshold),
                'true_positives': true_positives,
                'hit_rate': round(hit_rate, 3)
            }
    
    return analysis

def analyze_pattern_effectiveness(stocks):
    """Analyze which patterns correlate with success"""
    patterns = {}
    
    # Analyze each scoring component
    components = ['volume_score', 'rsi_score', 'breakout_score', 'accumulation_score', 'composite_bonus']
    
    for component in components:
        with_pattern = []
        without_pattern = []
        
        for stock in stocks:
            breakdown = stock.get('score_breakdown', {})
            if breakdown.get(component, 0) > 0:
                with_pattern.append(stock)
            else:
                without_pattern.append(stock)
        
        # Calculate success rates
        if with_pattern:
            success_with = sum(1 for s in with_pattern 
                             if s.get('final_classification') == 'TRUE_POSITIVE') / len(with_pattern)
        else:
            success_with = 0
        
        if without_pattern:
            success_without = sum(1 for s in without_pattern 
                                if s.get('final_classification') == 'TRUE_POSITIVE') / len(without_pattern)
        else:
            success_without = 0
        
        patterns[component] = {
            'stocks_with_pattern': len(with_pattern),
            'stocks_without_pattern': len(without_pattern),
            'success_rate_with': round(success_with, 3),
            'success_rate_without': round(success_without, 3),
            'correlation': round(success_with - success_without, 3)
        }
    
    return patterns

def find_top_patterns(pattern_analysis):
    """Find patterns with highest correlation to success"""
    patterns = []
    
    for name, data in pattern_analysis.items():
        patterns.append({
            'name': name,
            'correlation': data['correlation'],
            'success_rate': data['success_rate_with']
        })
    
    # Sort by correlation
    patterns.sort(key=lambda x: x['correlation'], reverse=True)
    
    return patterns

def extract_key_findings(stocks, score_analysis, pattern_analysis):
    """Extract actionable insights"""
    findings = []
    
    # Find optimal score threshold
    best_threshold = None
    best_hit_rate = 0
    
    for threshold_data in score_analysis.values():
        if threshold_data['stocks_above'] >= 10:  # Minimum sample size
            if threshold_data['hit_rate'] > best_hit_rate:
                best_hit_rate = threshold_data['hit_rate']
                best_threshold = threshold_data['threshold']
    
    if best_threshold:
        findings.append(f"Optimal score threshold: {best_threshold} (hit rate: {best_hit_rate:.1%})")
    
    # Find most predictive pattern
    best_pattern = max(pattern_analysis.items(), key=lambda x: x[1]['correlation'])
    findings.append(f"Most predictive pattern: {best_pattern[0]} (+{best_pattern[1]['correlation']:.1%} correlation)")
    
    # Calculate average gain for true positives
    true_positives = [s for s in stocks if s.get('final_classification') == 'TRUE_POSITIVE']
    if true_positives:
        avg_gain = sum(s.get('forward_performance', {}).get('max_gain_percent', 0) 
                      for s in true_positives) / len(true_positives)
        findings.append(f"Average gain for explosions: {avg_gain:.0f}%")
    
    # Days to explosion
    days_to_peak = [s.get('forward_performance', {}).get('days_to_peak', 0) 
                    for s in true_positives if s.get('forward_performance', {}).get('days_to_peak')]
    if days_to_peak:
        avg_days = sum(days_to_peak) / len(days_to_peak)
        findings.append(f"Average days to peak: {avg_days:.0f} days")
    
    return findings

def main():
    if not os.path.exists('Verified_Backtest_Data/phase4_merged_analysis.json'):
        print("Error: Merged analysis file not found. Run merger first.")
        sys.exit(1)
    
    analyze_correlations()

if __name__ == '__main__':
    main()
