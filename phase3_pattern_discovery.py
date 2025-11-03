#!/usr/bin/env python3
"""
GEM Trading System - Phase 3: Pre-Catalyst Analysis & Pattern Discovery
Version: 2.0 - COMPREHENSIVE FRAMEWORK
Created: 2025-11-02

PURPOSE:
Comprehensive analysis of 72 verified sustainable stocks to discover what patterns,
signals, and characteristics were observable 180 days BEFORE explosive moves.

METHODOLOGY:
Based on PRE_CATALYST_ANALYSIS_FRAMEWORK.md v2.0
- Cast wide net: Gather ALL observable data
- Find correlations: Statistical analysis across stocks
- Identify patterns: What predicts explosions?
- Build criteria: GEM v6 screening rules

PHASE 3A: Initial Pattern Discovery (This Script)
- Basic temporal, gain, and characteristic analysis
- Identify top performers and common traits
- Statistical analysis of 72 stocks
- Generate preliminary insights

PHASE 3B: Deep Pre-Catalyst Analysis (Future)
- Comprehensive 180-day lookback per stock
- 12 data categories, 100+ metrics
- Sample 8 stocks first, then scale to all 72
- Build correlation matrix and predictive model

INPUT: explosive_stocks_CLEAN.json (72 verified sustainable stocks)
OUTPUT:
  - phase3_initial_analysis.json (statistical patterns)
  - phase3_sample_selection.json (8 stocks for deep dive)
  - phase3_insights_report.md (readable insights)
  - phase3_next_steps.md (roadmap for Phase 3B)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import statistics

# File paths
DATA_DIR = "Verified_Backtest_Data"
INPUT_FILE = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
OUTPUT_PATTERNS = f"{DATA_DIR}/phase3_pattern_discovery.json"
OUTPUT_CRITERIA = f"{DATA_DIR}/phase3_screening_criteria.json"
OUTPUT_REPORT = f"{DATA_DIR}/phase3_insights_report.md"


class Phase3Analyzer:
    """Phase 3: Pattern Discovery and Analysis"""
    
    def __init__(self):
        self.stocks = []
        self.patterns = {}
        self.insights = []
        
    def load_stocks(self):
        """Load verified sustainable stocks"""
        print("\n" + "="*80)
        print("PHASE 3: PATTERN DISCOVERY & ANALYSIS")
        print("="*80)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        self.stocks = data.get('stocks', [])
        print(f"✅ Loaded {len(self.stocks)} verified sustainable stocks\n")
    
    def analyze_temporal_patterns(self):
        """Analyze when explosive moves occur"""
        print("🔍 ANALYZING TEMPORAL PATTERNS...")
        print("-" * 80)
        
        patterns = {
            'by_year': defaultdict(int),
            'by_month': defaultdict(int),
            'days_to_peak': {
                'fast': [],  # <30 days
                'medium': [],  # 30-90 days
                'slow': []  # 90+ days
            },
            'peak_months': defaultdict(int)
        }
        
        for stock in self.stocks:
            # Year distribution
            year = stock.get('year', stock.get('year_discovered', 'unknown'))
            patterns['by_year'][str(year)] += 1
            
            # Days to peak
            days = stock.get('days_to_peak', 0)
            if days < 30:
                patterns['days_to_peak']['fast'].append(days)
            elif days < 90:
                patterns['days_to_peak']['medium'].append(days)
            else:
                patterns['days_to_peak']['slow'].append(days)
            
            # Peak month
            peak_date = stock.get('peak_date', '')
            if peak_date:
                try:
                    month = datetime.strptime(peak_date, '%Y-%m-%d').strftime('%B')
                    patterns['peak_months'][month] += 1
                except:
                    pass
        
        # Calculate stats
        all_days = []
        for category in patterns['days_to_peak'].values():
            all_days.extend(category)
        
        if all_days:
            patterns['days_to_peak_stats'] = {
                'min': min(all_days),
                'max': max(all_days),
                'mean': round(statistics.mean(all_days), 1),
                'median': round(statistics.median(all_days), 1)
            }
        
        print(f"  Years Covered: {len(patterns['by_year'])} years")
        print(f"  Fast Movers (<30d): {len(patterns['days_to_peak']['fast'])}")
        print(f"  Medium Movers (30-90d): {len(patterns['days_to_peak']['medium'])}")
        print(f"  Slow Movers (90+d): {len(patterns['days_to_peak']['slow'])}")
        if all_days:
            print(f"  Average Days to Peak: {patterns['days_to_peak_stats']['mean']}")
        print()
        
        self.patterns['temporal'] = patterns
        return patterns
    
    def analyze_gain_characteristics(self):
        """Analyze gain patterns and magnitudes"""
        print("🔍 ANALYZING GAIN CHARACTERISTICS...")
        print("-" * 80)
        
        patterns = {
            'gain_ranges': {
                '500-1000%': [],
                '1000-2000%': [],
                '2000-5000%': [],
                '5000%+': []
            },
            'max_gains': [],
            'sustained_test': {
                'days_above_200': [],
                'max_gain_observed': []
            }
        }
        
        for stock in self.stocks:
            # Peak gain
            gain = stock.get('gain_percent', 0)
            patterns['max_gains'].append(gain)
            
            if gain < 1000:
                patterns['gain_ranges']['500-1000%'].append(gain)
            elif gain < 2000:
                patterns['gain_ranges']['1000-2000%'].append(gain)
            elif gain < 5000:
                patterns['gain_ranges']['2000-5000%'].append(gain)
            else:
                patterns['gain_ranges']['5000%+'].append(gain)
            
            # Sustained gain test data
            test = stock.get('sustained_gain_test', {})
            if test:
                days_above = test.get('total_days_above_threshold', 0)
                max_gain = test.get('max_gain_observed', 0)
                
                if days_above:
                    patterns['sustained_test']['days_above_200'].append(days_above)
                if max_gain:
                    patterns['sustained_test']['max_gain_observed'].append(max_gain)
        
        # Calculate stats
        if patterns['max_gains']:
            patterns['gain_stats'] = {
                'min': round(min(patterns['max_gains']), 1),
                'max': round(max(patterns['max_gains']), 1),
                'mean': round(statistics.mean(patterns['max_gains']), 1),
                'median': round(statistics.median(patterns['max_gains']), 1)
            }
        
        if patterns['sustained_test']['days_above_200']:
            patterns['exit_window_stats'] = {
                'min': min(patterns['sustained_test']['days_above_200']),
                'max': max(patterns['sustained_test']['days_above_200']),
                'mean': round(statistics.mean(patterns['sustained_test']['days_above_200']), 1),
                'median': round(statistics.median(patterns['sustained_test']['days_above_200']), 1)
            }
        
        print(f"  Gain Ranges:")
        for range_name, stocks in patterns['gain_ranges'].items():
            print(f"    {range_name}: {len(stocks)} stocks")
        if 'gain_stats' in patterns:
            print(f"  Average Gain: {patterns['gain_stats']['mean']}%")
            print(f"  Median Gain: {patterns['gain_stats']['median']}%")
        if 'exit_window_stats' in patterns:
            print(f"  Average Exit Window: {patterns['exit_window_stats']['mean']} days")
        print()
        
        self.patterns['gains'] = patterns
        return patterns
    
    def analyze_exit_windows(self):
        """Analyze exit window characteristics"""
        print("🔍 ANALYZING EXIT WINDOWS...")
        print("-" * 80)
        
        patterns = {
            'exit_window_categories': {
                'quick': [],  # 14-30 days
                'standard': [],  # 31-60 days
                'extended': [],  # 61-100 days
                'very_extended': []  # 100+ days
            },
            'tradeable_classifications': defaultdict(int)
        }
        
        for stock in self.stocks:
            test = stock.get('sustained_gain_test', {})
            days_above = test.get('total_days_above_threshold', 0)
            
            if days_above:
                if days_above <= 30:
                    patterns['exit_window_categories']['quick'].append(days_above)
                elif days_above <= 60:
                    patterns['exit_window_categories']['standard'].append(days_above)
                elif days_above <= 100:
                    patterns['exit_window_categories']['extended'].append(days_above)
                else:
                    patterns['exit_window_categories']['very_extended'].append(days_above)
            
            # Drawdown classification (if available)
            drawdown = stock.get('drawdown_analysis', {})
            if drawdown:
                classification = drawdown.get('tradeable_classification', 'UNKNOWN')
                patterns['tradeable_classifications'][classification] += 1
        
        print(f"  Exit Window Distribution:")
        for category, days_list in patterns['exit_window_categories'].items():
            print(f"    {category.replace('_', ' ').title()}: {len(days_list)} stocks")
        
        if patterns['tradeable_classifications']:
            print(f"\n  Tradeable Classifications:")
            for classification, count in patterns['tradeable_classifications'].items():
                print(f"    {classification}: {count} stocks")
        print()
        
        self.patterns['exit_windows'] = patterns
        return patterns
    
    def analyze_enrichment_quality(self):
        """Analyze data quality and enrichment"""
        print("🔍 ANALYZING DATA QUALITY...")
        print("-" * 80)
        
        patterns = {
            'enriched_count': 0,
            'with_drawdown': 0,
            'with_test_price': 0,
            'data_sources': defaultdict(int)
        }
        
        for stock in self.stocks:
            if stock.get('enriched'):
                patterns['enriched_count'] += 1
            
            if stock.get('drawdown_analysis'):
                patterns['with_drawdown'] += 1
            
            if stock.get('test_price_30d'):
                patterns['with_test_price'] += 1
            
            source = stock.get('data_source', 'unknown')
            patterns['data_sources'][source] += 1
        
        print(f"  Enriched Stocks: {patterns['enriched_count']}/{len(self.stocks)} ({patterns['enriched_count']/len(self.stocks)*100:.1f}%)")
        print(f"  With Drawdown Analysis: {patterns['with_drawdown']}")
        print(f"  With 30-Day Test Price: {patterns['with_test_price']}")
        print(f"\n  Data Sources:")
        for source, count in patterns['data_sources'].items():
            print(f"    {source}: {count} stocks")
        print()
        
        self.patterns['data_quality'] = patterns
        return patterns
    
    def identify_top_performers(self):
        """Identify top performing stocks"""
        print("🔍 IDENTIFYING TOP PERFORMERS...")
        print("-" * 80)
        
        # Sort by various metrics
        by_gain = sorted(self.stocks, key=lambda x: x.get('gain_percent', 0), reverse=True)[:10]
        
        by_exit_window = sorted(
            [s for s in self.stocks if s.get('sustained_gain_test', {}).get('total_days_above_threshold')],
            key=lambda x: x['sustained_gain_test']['total_days_above_threshold'],
            reverse=True
        )[:10]
        
        by_speed = sorted(self.stocks, key=lambda x: x.get('days_to_peak', 999))[:10]
        
        patterns = {
            'top_by_gain': [
                {
                    'ticker': s.get('ticker'),
                    'year': s.get('year', s.get('year_discovered')),
                    'gain_percent': s.get('gain_percent'),
                    'days_to_peak': s.get('days_to_peak')
                }
                for s in by_gain
            ],
            'top_by_exit_window': [
                {
                    'ticker': s.get('ticker'),
                    'year': s.get('year', s.get('year_discovered')),
                    'days_above_200': s['sustained_gain_test']['total_days_above_threshold'],
                    'gain_percent': s.get('gain_percent')
                }
                for s in by_exit_window
            ],
            'top_by_speed': [
                {
                    'ticker': s.get('ticker'),
                    'year': s.get('year', s.get('year_discovered')),
                    'days_to_peak': s.get('days_to_peak'),
                    'gain_percent': s.get('gain_percent')
                }
                for s in by_speed
            ]
        }
        
        print(f"  Top Gainers:")
        for i, stock in enumerate(patterns['top_by_gain'][:5], 1):
            print(f"    {i}. {stock['ticker']} ({stock['year']}): {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days")
        
        print(f"\n  Longest Exit Windows:")
        for i, stock in enumerate(patterns['top_by_exit_window'][:5], 1):
            print(f"    {i}. {stock['ticker']} ({stock['year']}): {stock['days_above_200']} days above 200%")
        
        print(f"\n  Fastest Movers:")
        for i, stock in enumerate(patterns['top_by_speed'][:5], 1):
            print(f"    {i}. {stock['ticker']} ({stock['year']}): {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days")
        print()
        
        self.patterns['top_performers'] = patterns
        return patterns
    
    
    def select_deep_dive_sample(self):
        """Select 8 diverse stocks for comprehensive Phase 3B analysis"""
        print("🔍 SELECTING DEEP DIVE SAMPLE...")
        print("-" * 80)
        
        # Selection criteria for maximum diversity
        selection = {
            "methodology": "Maximum diversity across all dimensions",
            "criteria": [
                "Variety of years (2016-2024)",
                "Variety of gains (500% to 10,000%+)",
                "Variety of speeds (1 day to 180 days)",
                "Mix of enriched vs basic data",
                "Recent stocks (full data available)"
            ],
            "sample_stocks": []
        }
        
        # Sort stocks by different metrics
        by_gain = sorted(self.stocks, key=lambda x: x.get('gain_percent', 0), reverse=True)
        by_speed_fast = sorted(self.stocks, key=lambda x: x.get('days_to_peak', 999))
        by_speed_slow = sorted(self.stocks, key=lambda x: x.get('days_to_peak', 0), reverse=True)
        by_exit_window = sorted(
            [s for s in self.stocks if s.get('sustained_gain_test', {}).get('total_days_above_threshold')],
            key=lambda x: x['sustained_gain_test']['total_days_above_threshold'],
            reverse=True
        )
        
        # Get year distribution
        recent_2024 = [s for s in self.stocks if s.get('year', s.get('year_discovered')) == 2024]
        year_2022_2023 = [s for s in self.stocks if s.get('year', s.get('year_discovered')) in [2022, 2023]]
        year_2016_2019 = [s for s in self.stocks if s.get('year', s.get('year_discovered')) in [2016, 2018, 2019]]
        
        # Select diverse sample
        sample = []
        
        # 1. Extreme gainer (test framework limits)
        if by_gain[0]['gain_percent'] > 5000:
            sample.append({
                "ticker": by_gain[0]['ticker'],
                "year": by_gain[0].get('year', by_gain[0].get('year_discovered')),
                "reason": f"Extreme gainer - {by_gain[0]['gain_percent']:.0f}% in {by_gain[0]['days_to_peak']} days",
                "role": "Test framework limits",
                "entry_date": by_gain[0].get('entry_date'),
                "entry_price": by_gain[0].get('entry_price'),
                "peak_date": by_gain[0].get('peak_date'),
                "gain_percent": by_gain[0]['gain_percent'],
                "days_to_peak": by_gain[0]['days_to_peak']
            })
        
        # 2-3. Recent moderate gainers (full data available)
        for stock in recent_2024[:2]:
            if stock['ticker'] not in [s['ticker'] for s in sample]:
                sample.append({
                    "ticker": stock['ticker'],
                    "year": stock.get('year', stock.get('year_discovered')),
                    "reason": f"Recent stock - {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days",
                    "role": "Recent with full data",
                    "entry_date": stock.get('entry_date'),
                    "entry_price": stock.get('entry_price'),
                    "peak_date": stock.get('peak_date'),
                    "gain_percent": stock['gain_percent'],
                    "days_to_peak": stock['days_to_peak']
                })
        
        # 4. Ultra-fast mover (<10 days)
        for stock in by_speed_fast:
            if stock['days_to_peak'] < 10 and stock['ticker'] not in [s['ticker'] for s in sample]:
                sample.append({
                    "ticker": stock['ticker'],
                    "year": stock.get('year', stock.get('year_discovered')),
                    "reason": f"Ultra-fast - {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days",
                    "role": "Test rapid explosion patterns",
                    "entry_date": stock.get('entry_date'),
                    "entry_price": stock.get('entry_price'),
                    "peak_date": stock.get('peak_date'),
                    "gain_percent": stock['gain_percent'],
                    "days_to_peak": stock['days_to_peak']
                })
                break
        
        # 5. Slow builder (150+ days)
        for stock in by_speed_slow:
            if stock['days_to_peak'] > 150 and stock['ticker'] not in [s['ticker'] for s in sample]:
                sample.append({
                    "ticker": stock['ticker'],
                    "year": stock.get('year', stock.get('year_discovered')),
                    "reason": f"Slow builder - {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days",
                    "role": "Test slow accumulation patterns",
                    "entry_date": stock.get('entry_date'),
                    "entry_price": stock.get('entry_price'),
                    "peak_date": stock.get('peak_date'),
                    "gain_percent": stock['gain_percent'],
                    "days_to_peak": stock['days_to_peak']
                })
                break
        
        # 6. Longest exit window
        if by_exit_window:
            stock = by_exit_window[0]
            if stock['ticker'] not in [s['ticker'] for s in sample]:
                sample.append({
                    "ticker": stock['ticker'],
                    "year": stock.get('year', stock.get('year_discovered')),
                    "reason": f"Longest exit window - {stock['sustained_gain_test']['total_days_above_threshold']} days",
                    "role": "Test extended tradeable period",
                    "entry_date": stock.get('entry_date'),
                    "entry_price": stock.get('entry_price'),
                    "peak_date": stock.get('peak_date'),
                    "gain_percent": stock['gain_percent'],
                    "days_to_peak": stock['days_to_peak'],
                    "exit_window_days": stock['sustained_gain_test']['total_days_above_threshold']
                })
        
        # 7-8. Fill remaining with diverse years
        for year_group in [year_2022_2023, year_2016_2019]:
            for stock in year_group:
                if len(sample) >= 8:
                    break
                if stock['ticker'] not in [s['ticker'] for s in sample]:
                    sample.append({
                        "ticker": stock['ticker'],
                        "year": stock.get('year', stock.get('year_discovered')),
                        "reason": f"Historical diversity - {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days",
                        "role": f"Represent {stock.get('year', stock.get('year_discovered'))} winners",
                        "entry_date": stock.get('entry_date'),
                        "entry_price": stock.get('entry_price'),
                        "peak_date": stock.get('peak_date'),
                        "gain_percent": stock['gain_percent'],
                        "days_to_peak": stock['days_to_peak']
                    })
        
        selection['sample_stocks'] = sample[:8]
        selection['sample_count'] = len(sample[:8])
        
        print(f"  Selected {len(sample[:8])} stocks for deep dive:\n")
        for i, stock in enumerate(sample[:8], 1):
            print(f"  {i}. {stock['ticker']} ({stock['year']})")
            print(f"     {stock['reason']}")
            print(f"     Role: {stock['role']}\n")
        
        self.patterns['sample_selection'] = selection
        return selection
        """Generate GEM v6 screening criteria from patterns"""
        print("🎯 GENERATING SCREENING CRITERIA...")
        print("-" * 80)
        
        temporal = self.patterns.get('temporal', {})
        gains = self.patterns.get('gains', {})
        exit_windows = self.patterns.get('exit_windows', {})
        
        criteria = {
            "version": "6.0",
            "generated_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "based_on_stocks": len(self.stocks),
            "criteria": {}
        }
        
        # Temporal criteria
        if temporal.get('days_to_peak_stats'):
            criteria['criteria']['days_to_peak'] = {
                "typical_range": f"0-{temporal['days_to_peak_stats']['mean']*2:.0f} days",
                "fast_threshold": 30,
                "medium_threshold": 90,
                "note": f"Average winner peaks in {temporal['days_to_peak_stats']['mean']} days"
            }
        
        # Gain criteria
        if gains.get('gain_stats'):
            criteria['criteria']['minimum_gain'] = {
                "target": "500%+",
                "typical": f"{gains['gain_stats']['median']:.0f}%",
                "note": "Median gain among winners"
            }
        
        # Exit window criteria
        if gains.get('exit_window_stats'):
            criteria['criteria']['exit_window'] = {
                "minimum_days": 14,
                "typical": f"{gains['exit_window_stats']['median']:.0f} days",
                "ideal": "60+ days",
                "note": "Days above 200% gain threshold"
            }
        
        # Risk management
        criteria['criteria']['risk_management'] = {
            "trailing_stop": "35%",
            "max_single_day_drop": "35%",
            "preferred": "TRADEABLE or IDEAL classification",
            "avoid": "UNTRADEABLE (>35% gaps)"
        }
        
        # Year patterns
        if temporal.get('by_year'):
            years = sorted(temporal['by_year'].items(), key=lambda x: int(x[0]) if x[0] != 'unknown' else 0)
            recent_years = [year for year, count in years[-3:] if year != 'unknown']
            criteria['criteria']['temporal_focus'] = {
                "recent_hot_years": recent_years,
                "note": "Years with most winners in dataset"
            }
        
        print("  Generated screening criteria for GEM v6")
        print(f"  Based on {len(self.stocks)} verified sustainable stocks")
        print()
        
        return criteria
    
    def generate_insights(self):
        """Generate human-readable insights"""
        print("📝 GENERATING INSIGHTS REPORT...")
        print("-" * 80)
        
        temporal = self.patterns.get('temporal', {})
        gains = self.patterns.get('gains', {})
        exit_windows = self.patterns.get('exit_windows', {})
        top_performers = self.patterns.get('top_performers', {})
        
        insights = []
        
        # Key findings
        insights.append("# Phase 3: Pattern Discovery Insights\n")
        insights.append(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}")
        insights.append(f"**Stocks Analyzed:** {len(self.stocks)} verified sustainable winners\n")
        insights.append("---\n")
        
        insights.append("## 🎯 Key Findings\n")
        
        # Temporal insights
        if temporal.get('days_to_peak_stats'):
            stats = temporal['days_to_peak_stats']
            insights.append("### Timing Patterns")
            insights.append(f"- **Average Time to Peak:** {stats['mean']} days")
            insights.append(f"- **Median Time to Peak:** {stats['median']} days")
            insights.append(f"- **Range:** {stats['min']}-{stats['max']} days")
            
            fast = len(temporal['days_to_peak']['fast'])
            medium = len(temporal['days_to_peak']['medium'])
            slow = len(temporal['days_to_peak']['slow'])
            total = fast + medium + slow
            
            if total > 0:
                insights.append(f"- **Fast Movers (<30d):** {fast} ({fast/total*100:.0f}%)")
                insights.append(f"- **Medium Movers (30-90d):** {medium} ({medium/total*100:.0f}%)")
                insights.append(f"- **Slow Movers (90+d):** {slow} ({slow/total*100:.0f}%)\n")
        
        # Gain insights
        if gains.get('gain_stats'):
            stats = gains['gain_stats']
            insights.append("### Gain Characteristics")
            insights.append(f"- **Average Gain:** {stats['mean']}%")
            insights.append(f"- **Median Gain:** {stats['median']}%")
            insights.append(f"- **Range:** {stats['min']}%-{stats['max']}%")
            
            for range_name, stocks_list in gains['gain_ranges'].items():
                if stocks_list:
                    insights.append(f"- **{range_name}:** {len(stocks_list)} stocks")
            insights.append("")
        
        # Exit window insights
        if gains.get('exit_window_stats'):
            stats = gains['exit_window_stats']
            insights.append("### Exit Windows")
            insights.append(f"- **Average Days Above 200%:** {stats['mean']} days")
            insights.append(f"- **Median Days Above 200%:** {stats['median']} days")
            insights.append(f"- **Range:** {stats['min']}-{stats['max']} days\n")
        
        # Top performers
        if top_performers:
            insights.append("## 🏆 Top Performers\n")
            
            insights.append("### Highest Gains")
            for i, stock in enumerate(top_performers.get('top_by_gain', [])[:5], 1):
                insights.append(f"{i}. **{stock['ticker']}** ({stock['year']}): {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days")
            insights.append("")
            
            insights.append("### Longest Exit Windows")
            for i, stock in enumerate(top_performers.get('top_by_exit_window', [])[:5], 1):
                insights.append(f"{i}. **{stock['ticker']}** ({stock['year']}): {stock['days_above_200']} days above 200%")
            insights.append("")
            
            insights.append("### Fastest Movers")
            for i, stock in enumerate(top_performers.get('top_by_speed', [])[:5], 1):
                insights.append(f"{i}. **{stock['ticker']}** ({stock['year']}): {stock['gain_percent']:.0f}% in {stock['days_to_peak']} days")
            insights.append("")
        
        # Year distribution
        if temporal.get('by_year'):
            insights.append("## 📅 Year Distribution\n")
            years = sorted(temporal['by_year'].items(), key=lambda x: int(x[0]) if x[0] != 'unknown' else 0, reverse=True)
            for year, count in years:
                if year != 'unknown':
                    insights.append(f"- **{year}:** {count} stocks")
            insights.append("")
        
        # Actionable insights
        insights.append("## 💡 Actionable Insights for GEM v6\n")
        
        if gains.get('gain_stats'):
            insights.append(f"1. **Target gains of {gains['gain_stats']['median']:.0f}%+** based on median winner performance")
        
        if gains.get('exit_window_stats'):
            insights.append(f"2. **Plan for {gains['exit_window_stats']['median']:.0f}-day exit windows** on average")
        
        if temporal.get('days_to_peak_stats'):
            insights.append(f"3. **Expect peak within {temporal['days_to_peak_stats']['mean']:.0f} days** on average")
        
        insights.append("4. **Use 35% trailing stop loss** to protect gains")
        insights.append("5. **Avoid stocks with >35% single-day gaps** (untradeable)")
        
        insights_text = "\n".join(insights)
        
        print("  Generated comprehensive insights report")
        print()
        
        return insights_text
    
    def run_analysis(self):
        """Run complete Phase 3A analysis"""
        self.load_stocks()
        
        # Run Phase 3A analyses
        self.analyze_temporal_patterns()
        self.analyze_gain_characteristics()
        self.analyze_exit_windows()
        self.analyze_enrichment_quality()
        self.identify_top_performers()
        self.select_deep_dive_sample()
        
        # Generate outputs
        criteria = self.generate_screening_criteria()
        insights = self.generate_insights()
        next_steps = self.generate_phase3b_roadmap()
        
        # Save results
        self.save_results(criteria, insights, next_steps)
        self.print_summary()
    
    def save_results(self, criteria, insights):
        """Save analysis results"""
        print("💾 SAVING RESULTS...")
        print("-" * 80)
        
        # Save pattern discovery
        with open(OUTPUT_PATTERNS, 'w') as f:
            json.dump({
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stocks_analyzed': len(self.stocks),
                'patterns': self.patterns
            }, f, indent=2)
        print(f"  ✅ Saved pattern discovery → {OUTPUT_PATTERNS}")
        
        # Save screening criteria
        with open(OUTPUT_CRITERIA, 'w') as f:
            json.dump(criteria, f, indent=2)
        print(f"  ✅ Saved screening criteria → {OUTPUT_CRITERIA}")
        
        # Save insights report
        with open(OUTPUT_REPORT, 'w') as f:
            f.write(insights)
        print(f"  ✅ Saved insights report → {OUTPUT_REPORT}")
        print()
    
    def print_summary(self):
        """Print analysis summary"""
        print("="*80)
        print("PHASE 3 ANALYSIS COMPLETE")
        print("="*80)
        print(f"📊 Analyzed {len(self.stocks)} verified sustainable stocks")
        print(f"📝 Generated insights and screening criteria")
        print(f"🎯 Ready for GEM v6 screener development")
        print()
        print("Output Files:")
        print(f"  • {OUTPUT_PATTERNS} - Complete pattern analysis")
        print(f"  • {OUTPUT_CRITERIA} - GEM v6 screening criteria")
        print(f"  • {OUTPUT_REPORT} - Human-readable insights")
        print()
        print("="*80)


def main():
    """Run Phase 3 analysis"""
    analyzer = Phase3Analyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
