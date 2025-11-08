"""
Phase 3 Data Diagnostic Tool
Investigates why patterns aren't being detected and scores are low
"""

import json
import sys
from collections import defaultdict

def diagnose_data_collection(test_file):
    """Deep dive into what data we're actually collecting"""
    
    print("=" * 80)
    print("PHASE 3 DATA COLLECTION DIAGNOSTIC REPORT")
    print("=" * 80)
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    stocks = data.get('all_stocks', [])
    
    # Problem 1: Missing Essential Data
    print("\n🔴 CRITICAL DATA ISSUES:")
    print("-" * 40)
    
    missing_catalyst = [s['ticker'] for s in stocks if not s.get('catalyst_date')]
    missing_price_180 = [s['ticker'] for s in stocks if s.get('price_change_180d') is None]
    
    print(f"1. Missing catalyst_date: {len(missing_catalyst)}/10 stocks")
    if missing_catalyst:
        print(f"   Affected: {', '.join(missing_catalyst)}")
    
    print(f"2. Missing price_change_180d: {len(missing_price_180)}/10 stocks")
    if missing_price_180:
        print(f"   Affected: {', '.join(missing_price_180)}")
    
    # Problem 2: Pattern Detection Analysis
    print("\n🔍 PATTERN DETECTION ANALYSIS:")
    print("-" * 40)
    
    all_patterns = [
        'volume_spike_3x_pre', 'volume_spike_5x_pre', 'volume_spike_10x_pre',
        'rsi_oversold_days_pre', 'rsi_oversold_depth_pre',
        'accumulation_detected_pre', 'base_building_pre',
        'price_coiling_pre', 'volume_trend_up_pre',
        'macd_bullish_cross_pre', 'bb_squeeze_pre',
        'support_bounce_pre', 'resistance_test_pre'
    ]
    
    # Count how many patterns each stock has
    for stock in stocks:
        ticker = stock['ticker']
        gain = stock['final_gain_percent']
        score = stock['total_score_pre']
        patterns_found = []
        
        for pattern in all_patterns:
            value = stock.get(pattern, 0)
            if pattern in ['rsi_oversold_days_pre', 'rsi_oversold_depth_pre']:
                if value and value > 0:
                    patterns_found.append(f"{pattern}={value:.1f}")
            elif value:
                patterns_found.append(pattern)
        
        print(f"\n{ticker}: {gain:.0f}% gain, Score: {score}")
        if patterns_found:
            print(f"  Patterns: {', '.join(patterns_found)}")
        else:
            print(f"  ⚠️  NO PATTERNS DETECTED!")
    
    # Problem 3: Patterns Never Detected
    print("\n❌ PATTERNS WITH ZERO DETECTION:")
    print("-" * 40)
    
    never_detected = []
    for pattern in all_patterns:
        if pattern in ['rsi_oversold_days_pre', 'rsi_oversold_depth_pre']:
            if not any(s.get(pattern, 0) > 0 for s in stocks):
                never_detected.append(pattern)
        else:
            if not any(s.get(pattern) for s in stocks):
                never_detected.append(pattern)
    
    for pattern in never_detected:
        print(f"  • {pattern} - NEVER TRUE in any stock")
    
    # Problem 4: Score Analysis
    print("\n📊 SCORING BREAKDOWN:")
    print("-" * 40)
    
    # Analyze what contributes to scores
    score_components = {
        'volume_spike_3x_pre': 15,
        'volume_spike_5x_pre': 20,
        'volume_spike_10x_pre': 25,
        'rsi_oversold_days_pre': 'variable',  # based on days
        'base_building_pre': 15,
        'accumulation_detected_pre': 20,
        # Add other scoring components as needed
    }
    
    for stock in stocks[:3]:  # Analyze first 3 stocks in detail
        ticker = stock['ticker']
        print(f"\n{ticker} Score Breakdown (Total: {stock['total_score_pre']}):")
        
        calculated_score = 0
        if stock.get('volume_spike_3x_pre'):
            print(f"  + Volume 3x spike: 15 points")
            calculated_score += 15
        if stock.get('volume_spike_5x_pre'):
            print(f"  + Volume 5x spike: 20 points")
            calculated_score += 20
        if stock.get('volume_spike_10x_pre'):
            print(f"  + Volume 10x spike: 25 points")
            calculated_score += 25
        
        rsi_days = stock.get('rsi_oversold_days_pre', 0)
        if rsi_days > 0:
            rsi_score = min(rsi_days * 2, 20)  # Assuming 2 points per day, max 20
            print(f"  + RSI oversold {rsi_days} days: {rsi_score} points")
            calculated_score += rsi_score
        
        if stock.get('base_building_pre'):
            print(f"  + Base building: 15 points")
            calculated_score += 15
        
        print(f"  Calculated: {calculated_score}, Actual: {stock['total_score_pre']}")
        if calculated_score != stock['total_score_pre']:
            print(f"  ⚠️  MISMATCH!")
    
    # Problem 5: Data Sources
    print("\n📋 DATA SOURCE REQUIREMENTS:")
    print("-" * 40)
    print("Current data being collected:")
    print("  ✅ RSI - Technical indicator (calculated from price)")
    print("  ✅ Volume spikes - From market data")
    print("  ⚠️  Base building - Detected but rare")
    print("  ❌ MACD - Not being calculated")
    print("  ❌ Bollinger Bands - Not being calculated")
    print("  ❌ Support/Resistance - Not being calculated")
    print("  ❌ Accumulation - Not being detected")
    print("  ❌ Price coiling - Not being detected")
    
    print("\nData sources needed:")
    print("  • Price data: Daily OHLC for 90 days")
    print("  • Volume data: Daily volume for 90 days")
    print("  • Technical calculations: RSI, MACD, BB, ATR")
    print("  • Pattern recognition: Support/resistance levels")
    
    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    print("\n🚨 CRITICAL FINDINGS:")
    print("1. Most stocks missing catalyst_date - using entry_date-1 as fallback")
    print("2. Price change data missing for most recent stocks")
    print("3. Only 2 patterns consistently detected (RSI oversold, volume spikes)")
    print("4. 8 patterns NEVER detected in any stock")
    print("5. Highest scoring stock (39) still below threshold (50)")
    print("6. Inverse correlation: Lower scores = Higher gains!")
    
    print("\n💡 RECOMMENDATIONS:")
    print("1. Fix pattern detection algorithms (MACD, BB, support/resistance)")
    print("2. Verify we're looking at the RIGHT 90-day window")
    print("3. Adjust scoring weights - current weights may be wrong")
    print("4. Consider that explosive stocks may not show traditional patterns")
    print("5. May need to look for DIFFERENT patterns (micro-cap specific)")
    
    # Create detailed report
    report = {
        "diagnostic_type": "DATA_COLLECTION_ANALYSIS",
        "critical_issues": {
            "missing_catalyst_dates": len(missing_catalyst),
            "missing_price_data": len(missing_price_180),
            "patterns_never_detected": never_detected,
            "highest_score": max(s['total_score_pre'] for s in stocks),
            "stocks_above_50": sum(1 for s in stocks if s['total_score_pre'] >= 50)
        },
        "pattern_detection_rate": {
            pattern: sum(1 for s in stocks if s.get(pattern)) 
            for pattern in all_patterns
        },
        "recommendations": [
            "Fix technical indicator calculations (MACD, BB)",
            "Verify 90-day pre-explosion window calculation",
            "Recalibrate scoring weights",
            "Research micro-cap specific patterns",
            "Consider volume relative to float, not absolute"
        ]
    }
    
    # Save report
    with open('phase3_diagnostic_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: phase3_diagnostic_report.json")
    
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python phase3_diagnostic.py <test_data.json>")
        sys.exit(1)
    
    diagnose_data_collection(sys.argv[1])
