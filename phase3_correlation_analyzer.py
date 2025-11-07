#!/usr/bin/env python3
"""
Phase 3 Correlation Analyzer - Builds correlation matrix from merged analysis
"""

import json
import os
import sys
from typing import Dict, List
from datetime import datetime

def calculate_correlations(merged_file: str, output_dir: str = 'Verified_Backtest_Data'):
    """
    Calculate correlations and build final matrix
    """
    print(f"{'='*60}")
    print(f"PHASE 3 CORRELATION ANALYZER")
    print(f"{'='*60}")
    
    # Load merged data
    with open(merged_file, 'r') as f:
        data = json.load(f)
    
    total_stocks = data.get('total_stocks', 0)
    successful = data.get('successful_analyses', 0)
    all_stocks = data.get('all_stocks', [])
    
    print(f"Total stocks: {total_stocks}")
    print(f"Successful analyses: {successful}")
    
    if successful == 0:
        print("❌ No successful analyses to build correlations!")
        sys.exit(1)
    
    # Initialize correlation matrix
    correlation_matrix = {
        'generated_date': datetime.now().isoformat(),
        'total_stocks': total_stocks,
        'successful_analyses': successful,
        'pattern_frequencies': {},
        'pattern_correlations': {},
        'composite_patterns': {},
        'screening_criteria': {},
        'key_findings': []
    }
    
    # Calculate detailed pattern frequencies
    patterns_analysis = analyze_patterns(all_stocks, successful)
    correlation_matrix['pattern_frequencies'] = patterns_analysis
    
    # Calculate pattern correlations with outcomes
    correlations = calculate_pattern_correlations(all_stocks)
    correlation_matrix['pattern_correlations'] = correlations
    
    # Find composite patterns (multiple signals together)
    composites = find_composite_patterns(all_stocks)
    correlation_matrix['composite_patterns'] = composites
    
    # Generate screening criteria based on correlations
    criteria = generate_screening_criteria(correlations, composites)
    correlation_matrix['screening_criteria'] = criteria
    
    # Extract key findings
    findings = extract_key_findings(patterns_analysis, correlations, composites)
    correlation_matrix['key_findings'] = findings
    
    # Save correlation matrix
    output_file = os.path.join(output_dir, 'phase3_correlation_matrix.json')
    with open(output_file, 'w') as f:
        json.dump(correlation_matrix, f, indent=2)
    
    # Display results
    display_correlation_results(correlation_matrix)
    
    # Generate report
    report_file = os.path.join(output_dir, 'PHASE3_CORRELATION_REPORT.md')
    generate_correlation_report(correlation_matrix, report_file)
    
    print(f"\n💾 Correlation matrix saved to: {output_file}")
    print(f"📊 Report saved to: {report_file}")
    
    return correlation_matrix


def analyze_patterns(stocks: List[Dict], total_successful: int) -> Dict:
    """
    Analyze pattern frequencies and characteristics
    """
    patterns = {
        # Volume patterns
        'volume_3x_spike': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0},
        'volume_5x_spike': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0},
        'volume_10x_spike': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0},
        
        # Technical patterns
        'rsi_oversold': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0},
        'breakout_pattern': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0},
        'accumulation': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0},
        
        # Market context
        'market_outperform': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0},
        'sector_strength': {'count': 0, 'with_big_gains': 0, 'avg_gain': 0}
    }
    
    # Analyze each stock
    for stock in stocks:
        if stock.get('analysis_status') != 'complete':
            continue
        
        gain = stock.get('gain_percent', 0)
        big_gain = gain > 1000  # 1000%+ gains
        
        pv = stock.get('price_volume_patterns', {})
        ti = stock.get('technical_indicators', {})
        mc = stock.get('market_context', {})
        
        # Volume patterns
        if pv.get('volume_3x_spike'):
            patterns['volume_3x_spike']['count'] += 1
            patterns['volume_3x_spike']['avg_gain'] += gain
            if big_gain:
                patterns['volume_3x_spike']['with_big_gains'] += 1
        
        if pv.get('volume_5x_spike'):
            patterns['volume_5x_spike']['count'] += 1
            patterns['volume_5x_spike']['avg_gain'] += gain
            if big_gain:
                patterns['volume_5x_spike']['with_big_gains'] += 1
        
        if pv.get('volume_10x_spike'):
            patterns['volume_10x_spike']['count'] += 1
            patterns['volume_10x_spike']['avg_gain'] += gain
            if big_gain:
                patterns['volume_10x_spike']['with_big_gains'] += 1
        
        # Technical patterns
        if ti.get('rsi_oversold_days', 0) > 0:
            patterns['rsi_oversold']['count'] += 1
            patterns['rsi_oversold']['avg_gain'] += gain
            if big_gain:
                patterns['rsi_oversold']['with_big_gains'] += 1
        
        if pv.get('breakout_20d_high'):
            patterns['breakout_pattern']['count'] += 1
            patterns['breakout_pattern']['avg_gain'] += gain
            if big_gain:
                patterns['breakout_pattern']['with_big_gains'] += 1
        
        if pv.get('accumulation_detected'):
            patterns['accumulation']['count'] += 1
            patterns['accumulation']['avg_gain'] += gain
            if big_gain:
                patterns['accumulation']['with_big_gains'] += 1
        
        # Market context
        if mc.get('spy_outperformance', 0) > 20:
            patterns['market_outperform']['count'] += 1
            patterns['market_outperform']['avg_gain'] += gain
            if big_gain:
                patterns['market_outperform']['with_big_gains'] += 1
    
    # Calculate frequencies and averages
    result = {}
    for pattern_name, pattern_data in patterns.items():
        if pattern_data['count'] > 0:
            result[pattern_name] = {
                'count': pattern_data['count'],
                'frequency_percent': round(pattern_data['count'] / total_successful * 100, 1),
                'avg_gain_when_present': round(pattern_data['avg_gain'] / pattern_data['count'], 0),
                'big_gain_rate': round(pattern_data['with_big_gains'] / pattern_data['count'] * 100, 1)
            }
    
    return result


def calculate_pattern_correlations(stocks: List[Dict]) -> Dict:
    """
    Calculate correlation between patterns and outcomes
    """
    correlations = {}
    
    # Group stocks by gain magnitude
    gain_groups = {
        'mega_winners': [],  # 2000%+
        'big_winners': [],   # 1000-2000%
        'moderate_winners': [],  # 500-1000%
    }
    
    for stock in stocks:
        if stock.get('analysis_status') != 'complete':
            continue
        
        gain = stock.get('gain_percent', 0)
        if gain >= 2000:
            gain_groups['mega_winners'].append(stock)
        elif gain >= 1000:
            gain_groups['big_winners'].append(stock)
        else:
            gain_groups['moderate_winners'].append(stock)
    
    # Analyze pattern presence in each group
    patterns_by_group = {}
    for group_name, group_stocks in gain_groups.items():
        if not group_stocks:
            continue
        
        patterns_by_group[group_name] = {
            'stock_count': len(group_stocks),
            'patterns': {}
        }
        
        # Count pattern occurrences
        for pattern in ['volume_3x_spike', 'volume_5x_spike', 'rsi_oversold', 'breakout_20d_high']:
            count = 0
            for stock in group_stocks:
                pv = stock.get('price_volume_patterns', {})
                ti = stock.get('technical_indicators', {})
                
                if pattern == 'volume_3x_spike' and pv.get('volume_3x_spike'):
                    count += 1
                elif pattern == 'volume_5x_spike' and pv.get('volume_5x_spike'):
                    count += 1
                elif pattern == 'rsi_oversold' and ti.get('rsi_oversold_days', 0) > 0:
                    count += 1
                elif pattern == 'breakout_20d_high' and pv.get('breakout_20d_high'):
                    count += 1
            
            if len(group_stocks) > 0:
                patterns_by_group[group_name]['patterns'][pattern] = round(count / len(group_stocks) * 100, 1)
    
    # Calculate correlation scores
    for pattern in ['volume_3x_spike', 'volume_5x_spike', 'rsi_oversold', 'breakout_20d_high']:
        mega_rate = patterns_by_group.get('mega_winners', {}).get('patterns', {}).get(pattern, 0)
        moderate_rate = patterns_by_group.get('moderate_winners', {}).get('patterns', {}).get(pattern, 0)
        
        # Simple correlation: higher presence in mega winners = higher correlation
        if mega_rate > 0 or moderate_rate > 0:
            correlation_score = (mega_rate - moderate_rate) / 100
            correlation_score = max(-1, min(1, correlation_score))  # Clamp to [-1, 1]
            
            correlations[pattern] = {
                'correlation_score': round(correlation_score, 3),
                'mega_winner_rate': mega_rate,
                'moderate_winner_rate': moderate_rate,
                'predictive_power': 'HIGH' if correlation_score > 0.3 else 'MEDIUM' if correlation_score > 0.1 else 'LOW'
            }
    
    correlations['gain_distribution'] = patterns_by_group
    
    return correlations


def find_composite_patterns(stocks: List[Dict]) -> Dict:
    """
    Find combinations of patterns that appear together
    """
    composites = {
        'volume_and_rsi': {'count': 0, 'avg_gain': 0},
        'volume_and_breakout': {'count': 0, 'avg_gain': 0},
        'rsi_and_accumulation': {'count': 0, 'avg_gain': 0},
        'triple_signal': {'count': 0, 'avg_gain': 0}  # 3+ signals
    }
    
    total = 0
    for stock in stocks:
        if stock.get('analysis_status') != 'complete':
            continue
        
        total += 1
        gain = stock.get('gain_percent', 0)
        
        pv = stock.get('price_volume_patterns', {})
        ti = stock.get('technical_indicators', {})
        ps = stock.get('pattern_scores', {})
        
        # Check composite patterns
        has_volume = pv.get('volume_3x_spike', False)
        has_rsi = ti.get('rsi_oversold_days', 0) > 0
        has_breakout = pv.get('breakout_20d_high', False)
        has_accumulation = pv.get('accumulation_detected', False)
        
        if has_volume and has_rsi:
            composites['volume_and_rsi']['count'] += 1
            composites['volume_and_rsi']['avg_gain'] += gain
        
        if has_volume and has_breakout:
            composites['volume_and_breakout']['count'] += 1
            composites['volume_and_breakout']['avg_gain'] += gain
        
        if has_rsi and has_accumulation:
            composites['rsi_and_accumulation']['count'] += 1
            composites['rsi_and_accumulation']['avg_gain'] += gain
        
        # Count total signals
        signal_count = sum([has_volume, has_rsi, has_breakout, has_accumulation])
        if signal_count >= 3:
            composites['triple_signal']['count'] += 1
            composites['triple_signal']['avg_gain'] += gain
    
    # Calculate frequencies and averages
    result = {}
    for comp_name, comp_data in composites.items():
        if comp_data['count'] > 0:
            result[comp_name] = {
                'count': comp_data['count'],
                'frequency_percent': round(comp_data['count'] / total * 100, 1) if total > 0 else 0,
                'avg_gain': round(comp_data['avg_gain'] / comp_data['count'], 0)
            }
    
    return result


def generate_screening_criteria(correlations: Dict, composites: Dict) -> Dict:
    """
    Generate actionable screening criteria
    """
    criteria = {
        'primary_signals': [],
        'secondary_signals': [],
        'composite_signals': [],
        'entry_rules': [],
        'filters': []
    }
    
    # Identify primary signals (high correlation)
    for pattern, data in correlations.items():
        if pattern == 'gain_distribution':
            continue
        
        if data.get('predictive_power') == 'HIGH':
            criteria['primary_signals'].append({
                'pattern': pattern,
                'correlation': data.get('correlation_score', 0),
                'mega_winner_rate': data.get('mega_winner_rate', 0)
            })
        elif data.get('predictive_power') == 'MEDIUM':
            criteria['secondary_signals'].append({
                'pattern': pattern,
                'correlation': data.get('correlation_score', 0)
            })
    
    # Add composite patterns
    for comp_name, comp_data in composites.items():
        if comp_data.get('avg_gain', 0) > 1500:  # High gain composites
            criteria['composite_signals'].append({
                'pattern': comp_name,
                'avg_gain': comp_data.get('avg_gain', 0),
                'frequency': comp_data.get('frequency_percent', 0)
            })
    
    # Entry rules
    criteria['entry_rules'] = [
        'PRIMARY: Any primary signal present',
        'SECONDARY: 2+ secondary signals present',
        'COMPOSITE: Any high-gain composite pattern',
        'TIMING: Enter on signal day or next day open'
    ]
    
    # Filters
    criteria['filters'] = [
        'Price range: $0.50 - $10.00',
        'Volume: >100,000 daily average',
        'Market cap: <$500M preferred'
    ]
    
    return criteria


def extract_key_findings(patterns: Dict, correlations: Dict, composites: Dict) -> List[Dict]:
    """
    Extract key findings from analysis
    """
    findings = []
    
    # Find most common pattern
    if patterns:
        most_common = max(patterns.items(), key=lambda x: x[1].get('frequency_percent', 0))
        findings.append({
            'finding': 'Most Common Pattern',
            'pattern': most_common[0],
            'frequency': f"{most_common[1].get('frequency_percent', 0)}%",
            'significance': 'HIGH'
        })
    
    # Find highest correlation pattern
    high_corr = None
    for pattern, data in correlations.items():
        if pattern == 'gain_distribution':
            continue
        if high_corr is None or data.get('correlation_score', 0) > high_corr[1].get('correlation_score', 0):
            high_corr = (pattern, data)
    
    if high_corr:
        findings.append({
            'finding': 'Highest Correlation Pattern',
            'pattern': high_corr[0],
            'correlation': high_corr[1].get('correlation_score', 0),
            'significance': 'VERY HIGH'
        })
    
    # Find best composite
    if composites:
        best_comp = max(composites.items(), key=lambda x: x[1].get('avg_gain', 0))
        findings.append({
            'finding': 'Best Composite Pattern',
            'pattern': best_comp[0],
            'avg_gain': f"{best_comp[1].get('avg_gain', 0):.0f}%",
            'significance': 'HIGH'
        })
    
    return findings


def display_correlation_results(matrix: Dict):
    """
    Display correlation results
    """
    print(f"\n{'='*60}")
    print(f"CORRELATION ANALYSIS RESULTS")
    print(f"{'='*60}")
    
    print(f"\n📊 Pattern Frequencies:")
    for pattern, data in matrix['pattern_frequencies'].items():
        print(f"  {pattern:20s}: {data.get('frequency_percent', 0):5.1f}% ({data.get('count', 0)} stocks)")
    
    print(f"\n📈 Pattern Correlations:")
    for pattern, data in matrix['pattern_correlations'].items():
        if pattern == 'gain_distribution':
            continue
        print(f"  {pattern:20s}: {data.get('correlation_score', 0):+.3f} correlation")
        print(f"    Mega winners: {data.get('mega_winner_rate', 0):.1f}%")
        print(f"    Moderate winners: {data.get('moderate_winner_rate', 0):.1f}%")
    
    print(f"\n🔄 Composite Patterns:")
    for pattern, data in matrix['composite_patterns'].items():
        print(f"  {pattern:20s}: {data.get('frequency_percent', 0):.1f}% frequency, {data.get('avg_gain', 0):.0f}% avg gain")
    
    print(f"\n🎯 Key Findings:")
    for finding in matrix['key_findings']:
        print(f"  • {finding['finding']}: {finding.get('pattern', 'N/A')}")


def generate_correlation_report(matrix: Dict, report_file: str):
    """
    Generate detailed correlation report
    """
    with open(report_file, 'w') as f:
        f.write("# Phase 3 Correlation Analysis Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Stocks Analyzed**: {matrix['total_stocks']}\n")
        f.write(f"**Successful Analyses**: {matrix['successful_analyses']}\n\n")
        
        f.write("## Executive Summary\n\n")
        for finding in matrix['key_findings']:
            f.write(f"- **{finding['finding']}**: {finding.get('pattern', 'N/A')}\n")
        f.write("\n")
        
        f.write("## Pattern Frequencies\n\n")
        f.write("| Pattern | Frequency | Count | Avg Gain |\n")
        f.write("|---------|-----------|-------|----------|\n")
        for pattern, data in matrix['pattern_frequencies'].items():
            f.write(f"| {pattern} | {data.get('frequency_percent', 0)}% | {data.get('count', 0)} | {data.get('avg_gain_when_present', 0):.0f}% |\n")
        
        f.write("\n## Screening Criteria\n\n")
        f.write("### Primary Signals\n")
        for signal in matrix['screening_criteria']['primary_signals']:
            f.write(f"- {signal['pattern']} (correlation: {signal['correlation']:.3f})\n")
        
        f.write("\n### Entry Rules\n")
        for rule in matrix['screening_criteria']['entry_rules']:
            f.write(f"- {rule}\n")
        
        f.write("\n## Next Steps\n\n")
        f.write("1. Implement screening criteria in live scanner\n")
        f.write("2. Backtest on out-of-sample data\n")
        f.write("3. Paper trade for validation\n")
        f.write("4. Refine thresholds based on results\n")


def main():
    """
    Main entry point
    """
    if len(sys.argv) < 2:
        print("Usage: python phase3_correlation_analyzer.py <merged_analysis_file>")
        print("Example: python phase3_correlation_analyzer.py Verified_Backtest_Data/phase3_merged_analysis.json")
        sys.exit(1)
    
    merged_file = sys.argv[1]
    
    if not os.path.exists(merged_file):
        print(f"Error: File not found: {merged_file}")
        sys.exit(1)
    
    # Calculate correlations
    matrix = calculate_correlations(merged_file)
    
    print(f"\n✅ Correlation analysis complete!")


if __name__ == '__main__':
    main()
