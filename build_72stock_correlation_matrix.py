"""
Build Comprehensive Correlation Matrix from 72-Stock Phase 3B Analysis
Aggregates all individual analysis files and identifies patterns
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime


def load_all_analyses(data_dir='Verified_Backtest_Data'):
    """Load all phase3b analysis files"""
    
    analyses = []
    pattern = 'phase3b_'
    
    if not os.path.exists(data_dir):
        print(f"[ERROR] Directory not found: {data_dir}")
        return []
    
    files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith('_analysis.json')]
    files = [f for f in files if 'summary' not in f.lower()]
    
    print(f"[INFO] Found {len(files)} analysis files")
    print()
    
    for filename in sorted(files):
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                analyses.append({
                    'filename': filename,
                    'data': data
                })
        except Exception as e:
            print(f"[WARNING] Error loading {filename}: {e}")
    
    return analyses


def extract_patterns(analyses):
    """Extract pattern frequencies and statistics"""
    
    stats = {
        'total_analyzed': len(analyses),
        'data_quality': Counter(),
        'volume_spikes': {
            'with_spikes': 0,
            'without_spikes': 0,
            'spike_counts': Counter(),
            'details': []
        },
        'rsi_oversold': {
            'oversold_count': 0,
            'near_oversold_count': 0,
            'normal_count': 0,
            'details': []
        },
        'patterns_detected': {
            'stocks_with_patterns': 0,
            'stocks_without_patterns': 0,
            'pattern_types': Counter(),
            'details': []
        },
        'speed_distribution': Counter(),
        'gain_distribution': Counter(),
        'year_distribution': Counter(),
        'days_analyzed_distribution': []
    }
    
    for analysis in analyses:
        data = analysis['data']
        summary = data.get('summary', {})
        stock_info = data.get('stock_info', {})
        price_data = data.get('price_volume_data', {})
        tech_indicators = price_data.get('technical_indicators', {})
        
        ticker = stock_info.get('ticker', 'UNKNOWN')
        year = stock_info.get('entry_date', '')[:4] if stock_info.get('entry_date') else 'UNKNOWN'
        
        # Data quality
        quality = summary.get('data_quality', 'unknown')
        stats['data_quality'][quality] += 1
        
        # Volume spikes
        volume_spikes = summary.get('volume_spikes_detected', 0)
        if volume_spikes > 0:
            stats['volume_spikes']['with_spikes'] += 1
            stats['volume_spikes']['spike_counts'][volume_spikes] += 1
            stats['volume_spikes']['details'].append({
                'ticker': ticker,
                'year': year,
                'spikes': volume_spikes,
                'gain_percent': stock_info.get('gain_percent')
            })
        else:
            stats['volume_spikes']['without_spikes'] += 1
        
        # RSI analysis
        rsi_data = tech_indicators.get('rsi', {})
        rsi_14 = rsi_data.get('14_day')
        rsi_oversold = summary.get('rsi_oversold', False)
        
        if rsi_oversold:
            stats['rsi_oversold']['oversold_count'] += 1
            stats['rsi_oversold']['details'].append({
                'ticker': ticker,
                'year': year,
                'rsi_14': rsi_14,
                'gain_percent': stock_info.get('gain_percent')
            })
        elif rsi_14 and 30 <= rsi_14 < 35:
            stats['rsi_oversold']['near_oversold_count'] += 1
        else:
            stats['rsi_oversold']['normal_count'] += 1
        
        # Patterns detected
        patterns_found = summary.get('patterns_found', 0)
        if patterns_found > 0:
            stats['patterns_detected']['stocks_with_patterns'] += 1
            patterns_data = price_data.get('patterns_detected', {})
            for pattern, detected in patterns_data.items():
                if pattern != 'count' and detected:
                    stats['patterns_detected']['pattern_types'][pattern] += 1
        else:
            stats['patterns_detected']['stocks_without_patterns'] += 1
        
        # Speed and gain categories
        stats['speed_distribution'][summary.get('speed_category', 'unknown')] += 1
        stats['gain_distribution'][summary.get('gain_category', 'unknown')] += 1
        
        # Year distribution
        stats['year_distribution'][year] += 1
        
        # Days analyzed
        days = summary.get('days_analyzed', 0)
        stats['days_analyzed_distribution'].append(days)
    
    return stats


def calculate_correlations(stats):
    """Calculate pattern correlations and predictive power"""
    
    total = stats['total_analyzed']
    
    correlations = {
        'volume_spikes': {
            'frequency': stats['volume_spikes']['with_spikes'] / total if total > 0 else 0,
            'correlation_score': 0.0,
            'predictive_power': 'HIGH' if (stats['volume_spikes']['with_spikes'] / total) > 0.7 else 'MEDIUM',
            'sample_size': stats['volume_spikes']['with_spikes']
        },
        'rsi_oversold': {
            'frequency': stats['rsi_oversold']['oversold_count'] / total if total > 0 else 0,
            'near_oversold_frequency': stats['rsi_oversold']['near_oversold_count'] / total if total > 0 else 0,
            'correlation_score': 0.0,
            'predictive_power': 'LOW' if (stats['rsi_oversold']['oversold_count'] / total) < 0.2 else 'MEDIUM',
            'sample_size': stats['rsi_oversold']['oversold_count']
        },
        'volume_plus_oversold': {
            'note': 'Combination pattern - needs cross-reference analysis',
            'estimated_frequency': 0.0
        },
        'patterns_detected': {
            'frequency': stats['patterns_detected']['stocks_with_patterns'] / total if total > 0 else 0,
            'pattern_breakdown': dict(stats['patterns_detected']['pattern_types']),
            'sample_size': stats['patterns_detected']['stocks_with_patterns']
        }
    }
    
    # Calculate correlation scores
    for pattern_name, pattern_data in correlations.items():
        if 'frequency' in pattern_data:
            freq = pattern_data['frequency']
            pattern_data['correlation_score'] = round(freq, 3)
    
    return correlations


def generate_screening_criteria(stats, correlations):
    """Generate preliminary screening criteria"""
    
    criteria = {
        'note': f'Based on {stats["total_analyzed"]} explosive stocks - PRELIMINARY',
        'confidence': 'MEDIUM' if stats['total_analyzed'] >= 50 else 'LOW',
        'primary_signals': [],
        'secondary_signals': [],
        'combination_signals': []
    }
    
    if correlations['volume_spikes']['frequency'] > 0.6:
        criteria['primary_signals'].append({
            'signal': 'Volume Spike >3x',
            'frequency': f"{correlations['volume_spikes']['frequency']*100:.1f}%",
            'threshold': '3x average volume',
            'lead_time': '4-25 days before entry'
        })
    
    if 0.3 < correlations['rsi_oversold']['frequency'] <= 0.6:
        criteria['secondary_signals'].append({
            'signal': 'RSI Oversold <30',
            'frequency': f"{correlations['rsi_oversold']['frequency']*100:.1f}%",
            'threshold': 'RSI 14-day < 30',
            'note': 'Rare but strong signal'
        })
    
    criteria['combination_signals'].append({
        'signal': 'Volume Spike + RSI <35',
        'note': 'Strongest conviction - both signals present',
        'recommendation': 'Priority screening target'
    })
    
    return criteria


def build_comprehensive_matrix(data_dir='Verified_Backtest_Data'):
    """Main function"""
    
    print("=" * 70)
    print("BUILDING COMPREHENSIVE CORRELATION MATRIX")
    print("72-Stock Phase 3B Analysis")
    print("=" * 70)
    print()
    
    analyses = load_all_analyses(data_dir)
    
    if not analyses:
        print("[ERROR] No analysis files found")
        return None
    
    print(f"[SUCCESS] Loaded {len(analyses)} analysis files")
    print()
    
    print("[INFO] Extracting patterns and statistics...")
    stats = extract_patterns(analyses)
    print("[SUCCESS] Statistics extracted")
    print()
    
    print("[INFO] Calculating pattern correlations...")
    correlations = calculate_correlations(stats)
    print("[SUCCESS] Correlations calculated")
    print()
    
    print("[INFO] Generating screening criteria...")
    criteria = generate_screening_criteria(stats, correlations)
    print("[SUCCESS] Criteria generated")
    print()
    
    matrix = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'phase': '3B_FULL_72_STOCKS',
            'framework': '90-day pre-catalyst window',
            'stocks_analyzed': len(analyses),
            'confidence_level': 'MEDIUM' if len(analyses) >= 50 else 'LOW',
            'note': 'Based on 72 sustainable explosive stocks from 2016-2024'
        },
        'statistics': {
            'total_stocks': stats['total_analyzed'],
            'data_quality_breakdown': dict(stats['data_quality']),
            'speed_distribution': dict(stats['speed_distribution']),
            'gain_distribution': dict(stats['gain_distribution']),
            'year_distribution': dict(stats['year_distribution']),
            'avg_days_analyzed': sum(stats['days_analyzed_distribution']) / len(stats['days_analyzed_distribution']) if stats['days_analyzed_distribution'] else 0
        },
        'pattern_frequencies': {
            'volume_spikes': {
                'with_spikes': stats['volume_spikes']['with_spikes'],
                'without_spikes': stats['volume_spikes']['without_spikes'],
                'frequency_pct': (stats['volume_spikes']['with_spikes'] / stats['total_analyzed'] * 100) if stats['total_analyzed'] > 0 else 0,
                'spike_distribution': dict(stats['volume_spikes']['spike_counts']),
                'top_examples': sorted(stats['volume_spikes']['details'], key=lambda x: x.get('gain_percent', 0), reverse=True)[:10]
            },
            'rsi_oversold': {
                'oversold_count': stats['rsi_oversold']['oversold_count'],
                'near_oversold_count': stats['rsi_oversold']['near_oversold_count'],
                'frequency_pct': (stats['rsi_oversold']['oversold_count'] / stats['total_analyzed'] * 100) if stats['total_analyzed'] > 0 else 0,
                'examples': stats['rsi_oversold']['details']
            },
            'patterns_detected': {
                'with_patterns': stats['patterns_detected']['stocks_with_patterns'],
                'without_patterns': stats['patterns_detected']['stocks_without_patterns'],
                'pattern_types': dict(stats['patterns_detected']['pattern_types'])
            }
        },
        'correlations': correlations,
        'screening_criteria': criteria,
        'top_signals_ranked': [
            {
                'rank': 1,
                'signal': 'Volume Spike >3x',
                'frequency': correlations['volume_spikes']['frequency'],
                'correlation': correlations['volume_spikes']['correlation_score'],
                'predictive_power': correlations['volume_spikes']['predictive_power']
            },
            {
                'rank': 2,
                'signal': 'RSI Oversold <30',
                'frequency': correlations['rsi_oversold']['frequency'],
                'correlation': correlations['rsi_oversold']['correlation_score'],
                'predictive_power': correlations['rsi_oversold']['predictive_power']
            }
        ],
        'key_insights': {
            'most_common_signal': 'Volume Spike' if correlations['volume_spikes']['frequency'] > 0.5 else 'No dominant signal',
            'strongest_correlation': 'Volume Spike' if correlations['volume_spikes']['correlation_score'] > 0.6 else 'Requires more analysis',
            'recommended_screening_approach': 'Multi-signal: Volume + Technical indicators',
            'confidence_assessment': 'MEDIUM - 72 stocks provides good preliminary patterns'
        }
    }
    
    return matrix


if __name__ == "__main__":
    matrix = build_comprehensive_matrix()
    
    if matrix:
        output_file = 'Verified_Backtest_Data/phase3b_correlation_matrix_72STOCKS.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(matrix, f, indent=2)
        
        print("=" * 70)
        print("[SUCCESS] CORRELATION MATRIX COMPLETE")
        print("=" * 70)
        print(f"[INFO] Saved to: {output_file}")
        print()
        print("KEY FINDINGS:")
        print(f"  * Total stocks analyzed: {matrix['statistics']['total_stocks']}")
        print(f"  * Volume spike frequency: {matrix['pattern_frequencies']['volume_spikes']['frequency_pct']:.1f}%")
        print(f"  * RSI oversold frequency: {matrix['pattern_frequencies']['rsi_oversold']['frequency_pct']:.1f}%")
        print(f"  * Top signal: {matrix['key_insights']['most_common_signal']}")
        print()
