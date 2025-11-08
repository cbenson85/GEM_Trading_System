"""
Phase 3 Correlation Analyzer - Version 2
Fixed to work with all_stocks structure and includes diagnostics
Changes from previous version:
1. Changed data structure from 'all_results' to 'all_stocks'
2. Added detailed diagnostic output for missing data
3. Added data completeness report
4. Added source tracking for all data points
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime

def analyze_correlations(merged_file):
    """Analyze correlations from merged Phase 3 results with diagnostics"""
    
    print("=" * 60)
    print("PHASE 3 CORRELATION ANALYSIS - PRE-EXPLOSION PATTERNS")
    print("=" * 60)
    
    # Load merged data - CHANGED from all_results to all_stocks
    try:
        with open(merged_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR loading file: {e}")
        return
    
    # CHANGE: Now looking for 'all_stocks' instead of 'all_results'
    stocks = data.get('all_stocks', [])
    
    if not stocks:
        print(f"WARNING: No stocks found in data!")
        print(f"Available keys in data: {list(data.keys())}")
        return
    
    print(f"\nTotal stocks loaded: {len(stocks)}")
    print(f"Successful analyses: {data.get('successful_analyses', 0)}")
    print(f"Failed analyses: {data.get('failed_analyses', 0)}")
    
    # Diagnostic: Check data completeness
    print("\n" + "=" * 60)
    print("DATA COMPLETENESS DIAGNOSTIC")
    print("=" * 60)
    
    missing_data = defaultdict(list)
    data_sources = defaultdict(set)
    
    for stock in stocks:
        ticker = stock.get('ticker', 'UNKNOWN')
        
        # Check for essential fields
        essential_fields = [
            'entry_date', 'catalyst_date', 'total_score_pre',
            'price_change_180d', 'final_gain_percent'
        ]
        
        for field in essential_fields:
            if field not in stock or stock.get(field) is None:
                missing_data[field].append(ticker)
        
        # Track data sources for each pattern
        pattern_fields = [
            'volume_spike_3x_pre', 'volume_spike_5x_pre', 'volume_spike_10x_pre',
            'rsi_oversold_days_pre', 'rsi_oversold_depth_pre',
            'accumulation_detected_pre', 'base_building_pre',
            'price_coiling_pre', 'volume_trend_up_pre',
            'macd_bullish_cross_pre', 'bb_squeeze_pre',
            'support_bounce_pre', 'resistance_test_pre'
        ]
        
        for field in pattern_fields:
            if field in stock and stock[field] not in [None, False, 0]:
                data_sources[field].add(ticker)
    
    # Print missing data report
    if missing_data:
        print("\n⚠️  MISSING ESSENTIAL DATA:")
        for field, tickers in missing_data.items():
            print(f"  {field}: Missing in {len(tickers)} stocks")
            if len(tickers) <= 5:
                print(f"    Tickers: {', '.join(tickers)}")
    else:
        print("\n✅ All essential fields present")
    
    # Print data source coverage
    print("\n📊 PATTERN DATA COVERAGE:")
    for pattern, tickers in sorted(data_sources.items()):
        coverage = len(tickers) / len(stocks) * 100 if stocks else 0
        print(f"  {pattern}: {len(tickers)}/{len(stocks)} stocks ({coverage:.1f}%)")
    
    # Analyze patterns
    print("\n" + "=" * 60)
    print("PATTERN FREQUENCY ANALYSIS")
    print("=" * 60)
    
    pattern_counts = Counter()
    pattern_values = defaultdict(list)
    score_distribution = Counter()
    
    for stock in stocks:
        ticker = stock.get('ticker', 'UNKNOWN')
        score = stock.get('total_score_pre', 0) or 0
        
        # Track score distribution
        score_bucket = (score // 10) * 10
        score_distribution[f"{score_bucket}-{score_bucket+9}"] += 1
        
        # Count boolean patterns
        boolean_patterns = [
            'volume_spike_3x_pre', 'volume_spike_5x_pre', 'volume_spike_10x_pre',
            'accumulation_detected_pre', 'base_building_pre',
            'price_coiling_pre', 'volume_trend_up_pre',
            'macd_bullish_cross_pre', 'bb_squeeze_pre',
            'support_bounce_pre', 'resistance_test_pre'
        ]
        
        for pattern in boolean_patterns:
            if stock.get(pattern):
                pattern_counts[pattern] += 1
        
        # Track numeric patterns
        numeric_patterns = [
            ('rsi_oversold_days_pre', stock.get('rsi_oversold_days_pre', 0)),
            ('rsi_oversold_depth_pre', stock.get('rsi_oversold_depth_pre', 0))
        ]
        
        for pattern_name, value in numeric_patterns:
            if value and value > 0:
                pattern_values[pattern_name].append(value)
                pattern_counts[pattern_name] += 1
    
    # Print pattern frequencies
    print("\n📈 PATTERN FREQUENCIES (stocks showing pattern):")
    for pattern, count in pattern_counts.most_common():
        percentage = (count / len(stocks) * 100) if stocks else 0
        print(f"  {pattern}: {count}/{len(stocks)} ({percentage:.1f}%)")
    
    # Print numeric pattern statistics
    if pattern_values:
        print("\n📊 NUMERIC PATTERN STATISTICS:")
        for pattern, values in pattern_values.items():
            if values:
                avg = sum(values) / len(values)
                print(f"  {pattern}:")
                print(f"    Average: {avg:.2f}")
                print(f"    Min: {min(values)}, Max: {max(values)}")
    
    # Score distribution
    print("\n📊 TOTAL SCORE DISTRIBUTION:")
    for score_range in sorted(score_distribution.keys(), 
                             key=lambda x: int(float(x.split('-')[0]))):
        count = score_distribution[score_range]
        percentage = (count / len(stocks) * 100) if stocks else 0
        bar = '█' * int(percentage / 2)
        print(f"  {score_range:>7}: {count:3} ({percentage:5.1f}%) {bar}")
    
    # Find high scorers
    high_scorers = [s for s in stocks if s.get('total_score_pre', 0) >= 50]
    print(f"\n🎯 HIGH SCORERS (50+): {len(high_scorers)}")
    if high_scorers:
        for stock in sorted(high_scorers, 
                          key=lambda x: x.get('total_score_pre', 0), 
                          reverse=True)[:5]:
            print(f"  {stock['ticker']}: Score {stock.get('total_score_pre', 0)}, "
                  f"Gain {stock.get('final_gain_percent', 0):.0f}%")
    
    # Correlation between score and gains
    print("\n" + "=" * 60)
    print("SCORE vs GAIN CORRELATION")
    print("=" * 60)
    
    score_ranges = {
        '0-19': [],
        '20-39': [],
        '40-59': [],
        '60-79': [],
        '80-100': []
    }
    
    for stock in stocks:
        score = stock.get('total_score_pre', 0) or 0
        gain = stock.get('final_gain_percent', 0) or 0
        
        if score < 20:
            score_ranges['0-19'].append(gain)
        elif score < 40:
            score_ranges['20-39'].append(gain)
        elif score < 60:
            score_ranges['40-59'].append(gain)
        elif score < 80:
            score_ranges['60-79'].append(gain)
        else:
            score_ranges['80-100'].append(gain)
    
    for range_name, gains in score_ranges.items():
        if gains:
            avg_gain = sum(gains) / len(gains)
            print(f"  Score {range_name}: {len(gains)} stocks, "
                  f"Avg gain {avg_gain:.0f}%")
    
    # Create output report
    output = {
        "analysis_type": "PRE_EXPLOSION_PATTERNS",
        "total_stocks": len(stocks),
        "successful_analyses": data.get('successful_analyses', 0),
        "data_completeness": {
            "missing_fields": {k: len(v) for k, v in missing_data.items()},
            "pattern_coverage": {k: len(v) for k, v in data_sources.items()}
        },
        "pattern_frequencies": dict(pattern_counts),
        "score_distribution": dict(score_distribution),
        "high_scorers": [
            {
                "ticker": s['ticker'],
                "score": s.get('total_score_pre', 0),
                "gain": s.get('final_gain_percent', 0)
            }
            for s in high_scorers
        ],
        "top_patterns": [
            {
                "pattern": pattern,
                "frequency": count,
                "percentage": (count / len(stocks) * 100) if stocks else 0
            }
            for pattern, count in pattern_counts.most_common(10)
        ],
        "key_findings": []
    }
    
    # Generate key findings
    if len(stocks) > 0:
        if pattern_counts:
            top_pattern = pattern_counts.most_common(1)[0]
            output["key_findings"].append(
                f"Most common pattern: {top_pattern[0]} "
                f"({top_pattern[1]}/{len(stocks)} stocks)"
            )
        
        avg_score = sum(s.get('total_score_pre', 0) for s in stocks) / len(stocks)
        output["key_findings"].append(f"Average pre-explosion score: {avg_score:.1f}")
        
        if high_scorers:
            output["key_findings"].append(
                f"Only {len(high_scorers)}/{len(stocks)} stocks scored 50+"
            )
    
    # Save analysis results
    output_file = merged_file.replace('.json', '_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Analysis saved to: {output_file}")
    
    return output

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python phase3_correlation_analyzer_v2.py <merged_file.json>")
        sys.exit(1)
    
    analyze_correlations(sys.argv[1])
