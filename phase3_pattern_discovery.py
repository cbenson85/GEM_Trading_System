#!/usr/bin/env python3
"""
Phase 3A: Initial Pattern Discovery & Analysis
Analyzes 72 verified sustainable stocks to identify patterns and select deep dive sample
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class Phase3Analyzer:
    def __init__(self, clean_data_path: str):
        self.clean_data_path = clean_data_path
        self.stocks = []
        self.analysis_results = {}
        self.sample_selection = []
        
    def load_data(self):
        """Load verified sustainable stocks"""
        with open(self.clean_data_path, 'r') as f:
            data = json.load(f)
            self.stocks = data.get('stocks', [])
        print(f"✅ Loaded {len(self.stocks)} verified sustainable stocks")
        
    def analyze_temporal_patterns(self):
        """Analyze when explosions occurred and their speed"""
        print("\n🔍 ANALYZING TEMPORAL PATTERNS...")
        print("-" * 80)
        
        years = {}
        speed_categories = {'fast': 0, 'medium': 0, 'slow': 0}
        total_days = 0
        
        for stock in self.stocks:
            year = stock.get('year', 'unknown')
            years[year] = years.get(year, 0) + 1
            
            days_to_peak = stock.get('days_to_peak', 0)
            total_days += days_to_peak
            
            if days_to_peak < 30:
                speed_categories['fast'] += 1
            elif days_to_peak < 90:
                speed_categories['medium'] += 1
            else:
                speed_categories['slow'] += 1
        
        avg_days = total_days / len(self.stocks) if self.stocks else 0
        
        print(f"  Years Covered: {len(years)} years")
        print(f"  Fast Movers (<30d): {speed_categories['fast']}")
        print(f"  Medium Movers (30-90d): {speed_categories['medium']}")
        print(f"  Slow Movers (90+d): {speed_categories['slow']}")
        print(f"  Average Days to Peak: {avg_days:.1f}")
        
        self.analysis_results['temporal'] = {
            'year_distribution': years,
            'speed_distribution': speed_categories,
            'average_days_to_peak': round(avg_days, 1)
        }
        
    def analyze_gain_characteristics(self):
        """Analyze gain magnitudes and sustainability"""
        print("\n🔍 ANALYZING GAIN CHARACTERISTICS...")
        print("-" * 80)
        
        gain_ranges = {
            '500-1000%': 0,
            '1000-2000%': 0,
            '2000-5000%': 0,
            '5000%+': 0
        }
        
        gains = []
        exit_windows = []
        
        for stock in self.stocks:
            gain = stock.get('gain_percent', 0)
            gains.append(gain)
            
            if gain < 1000:
                gain_ranges['500-1000%'] += 1
            elif gain < 2000:
                gain_ranges['1000-2000%'] += 1
            elif gain < 5000:
                gain_ranges['2000-5000%'] += 1
            else:
                gain_ranges['5000%+'] += 1
            
            if 'sustainability_test' in stock:
                days_above = stock['sustainability_test'].get('days_above_threshold', 0)
                exit_windows.append(days_above)
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        median_gain = sorted(gains)[len(gains)//2] if gains else 0
        avg_exit = sum(exit_windows) / len(exit_windows) if exit_windows else 0
        
        print(f"  Gain Ranges:")
        for range_name, count in gain_ranges.items():
            print(f"    {range_name}: {count} stocks")
        print(f"  Average Gain: {avg_gain:.1f}%")
        print(f"  Median Gain: {median_gain:.1f}%")
        print(f"  Average Exit Window: {avg_exit:.1f} days")
        
        self.analysis_results['gains'] = {
            'distribution': gain_ranges,
            'average_gain_percent': round(avg_gain, 1),
            'median_gain_percent': round(median_gain, 1),
            'average_exit_window_days': round(avg_exit, 1)
        }
        
    def analyze_exit_windows(self):
        """Analyze tradeability based on exit window duration"""
        print("\n🔍 ANALYZING EXIT WINDOWS...")
        print("-" * 80)
        
        window_categories = {
            'quick': 0,      # 14-50 days
            'standard': 0,   # 50-100 days
            'extended': 0,   # 100-150 days
            'very_extended': 0  # 150+ days
        }
        
        tradeable_classifications = {
            'RISKY': 0,        # <21 days
            'TRADEABLE': 0,    # 21-49 days
            'COMFORTABLE': 0,  # 50-99 days
            'EXTENDED': 0,     # 100+ days
            'UNTRADEABLE': 0   # Data missing
        }
        
        for stock in self.stocks:
            if 'sustainability_test' in stock:
                days_above = stock['sustainability_test'].get('days_above_threshold', 0)
                
                if days_above < 50:
                    window_categories['quick'] += 1
                elif days_above < 100:
                    window_categories['standard'] += 1
                elif days_above < 150:
                    window_categories['extended'] += 1
                else:
                    window_categories['very_extended'] += 1
                
                if days_above < 21:
                    tradeable_classifications['RISKY'] += 1
                elif days_above < 50:
                    tradeable_classifications['TRADEABLE'] += 1
                elif days_above < 100:
                    tradeable_classifications['COMFORTABLE'] += 1
                else:
                    tradeable_classifications['EXTENDED'] += 1
            else:
                tradeable_classifications['UNTRADEABLE'] += 1
        
        print(f"  Exit Window Distribution:")
        for cat, count in window_categories.items():
            print(f"    {cat.capitalize()}: {count} stocks")
        
        print(f"  Tradeable Classifications:")
        for classification, count in tradeable_classifications.items():
            print(f"    {classification}: {count} stocks")
        
        self.analysis_results['exit_windows'] = {
            'distribution': window_categories,
            'tradeable_classifications': tradeable_classifications
        }
        
    def analyze_data_quality(self):
        """Assess data completeness and quality"""
        print("\n🔍 ANALYZING DATA QUALITY...")
        print("-" * 80)
        
        enriched_count = 0
        drawdown_count = 0
        test_price_count = 0
        data_sources = {}
        
        for stock in self.stocks:
            if stock.get('enriched'):
                enriched_count += 1
            
            if 'drawdown_analysis' in stock:
                drawdown_count += 1
            
            if 'test_price_30d' in stock:
                test_price_count += 1
            
            source = stock.get('data_source', 'unknown')
            data_sources[source] = data_sources.get(source, 0) + 1
        
        enriched_pct = (enriched_count / len(self.stocks) * 100) if self.stocks else 0
        
        print(f"  Enriched Stocks: {enriched_count}/{len(self.stocks)} ({enriched_pct:.1f}%)")
        print(f"  With Drawdown Analysis: {drawdown_count}")
        print(f"  With 30-Day Test Price: {test_price_count}")
        print(f"  Data Sources:")
        for source, count in data_sources.items():
            print(f"    {source}: {count} stocks")
        
        self.analysis_results['data_quality'] = {
            'total_stocks': len(self.stocks),
            'enriched_count': enriched_count,
            'enriched_percentage': round(enriched_pct, 1),
            'drawdown_count': drawdown_count,
            'test_price_count': test_price_count,
            'data_sources': data_sources
        }
        
    def identify_top_performers(self):
        """Identify standout stocks for analysis"""
        print("\n🔍 IDENTIFYING TOP PERFORMERS...")
        print("-" * 80)
        
        # Top gainers
        by_gain = sorted(self.stocks, key=lambda x: x.get('gain_percent', 0), reverse=True)[:5]
        print(f"  Top Gainers:")
        for i, stock in enumerate(by_gain, 1):
            ticker = stock.get('ticker', 'N/A')
            year = stock.get('year', 'N/A')
            gain = stock.get('gain_percent', 0)
            days = stock.get('days_to_peak', 0)
            print(f"    {i}. {ticker} ({year}): {gain:.0f}% in {days} days")
        
        # Longest exit windows
        stocks_with_windows = [s for s in self.stocks if 'sustainability_test' in s]
        by_window = sorted(stocks_with_windows, 
                          key=lambda x: x['sustainability_test'].get('days_above_threshold', 0), 
                          reverse=True)[:5]
        print(f"  Longest Exit Windows:")
        for i, stock in enumerate(by_window, 1):
            ticker = stock.get('ticker', 'N/A')
            year = stock.get('year', 'N/A')
            days = stock['sustainability_test'].get('days_above_threshold', 0)
            print(f"    {i}. {ticker} ({year}): {days} days above 200%")
        
        # Fastest movers
        by_speed = sorted(self.stocks, key=lambda x: x.get('days_to_peak', 999))[:5]
        print(f"  Fastest Movers:")
        for i, stock in enumerate(by_speed, 1):
            ticker = stock.get('ticker', 'N/A')
            year = stock.get('year', 'N/A')
            gain = stock.get('gain_percent', 0)
            days = stock.get('days_to_peak', 0)
            print(f"    {i}. {ticker} ({year}): {gain:.0f}% in {days} days")
        
        self.analysis_results['top_performers'] = {
            'top_gainers': [{'ticker': s.get('ticker'), 'year': s.get('year'), 
                           'gain_percent': s.get('gain_percent'), 'days': s.get('days_to_peak')} 
                          for s in by_gain],
            'longest_windows': [{'ticker': s.get('ticker'), 'year': s.get('year'),
                               'days_above_200': s['sustainability_test'].get('days_above_threshold')}
                              for s in by_window],
            'fastest_movers': [{'ticker': s.get('ticker'), 'year': s.get('year'),
                              'gain_percent': s.get('gain_percent'), 'days': s.get('days_to_peak')}
                             for s in by_speed]
        }
        
    def select_deep_dive_sample(self):
        """Select 8 diverse stocks for comprehensive Phase 3B analysis"""
        print("\n🔍 SELECTING DEEP DIVE SAMPLE...")
        print("-" * 80)
        
        selected = []
        
        # 1. Extreme gainer (test framework limits)
        extreme = max(self.stocks, key=lambda x: x.get('gain_percent', 0))
        selected.append({
            'ticker': extreme.get('ticker'),
            'year': extreme.get('year'),
            'reason': f"Extreme gainer - {extreme.get('gain_percent', 0):.0f}% in {extreme.get('days_to_peak', 0)} days",
            'role': 'Test framework limits',
            'stock_data': extreme
        })
        
        # 2-3. Recent stocks (2024) with full data
        recent_2024 = [s for s in self.stocks if s.get('year') == 2024 and s.get('enriched')]
        if len(recent_2024) >= 2:
            for stock in recent_2024[:2]:
                selected.append({
                    'ticker': stock.get('ticker'),
                    'year': stock.get('year'),
                    'reason': f"Recent stock - {stock.get('gain_percent', 0):.0f}% in {stock.get('days_to_peak', 0)} days",
                    'role': 'Recent with full data',
                    'stock_data': stock
                })
        
        # 4. Ultra-fast mover (test rapid explosion patterns)
        fast = min(self.stocks, key=lambda x: x.get('days_to_peak', 999))
        if fast not in [s['stock_data'] for s in selected]:
            selected.append({
                'ticker': fast.get('ticker'),
                'year': fast.get('year'),
                'reason': f"Ultra-fast - {fast.get('gain_percent', 0):.0f}% in {fast.get('days_to_peak', 0)} days",
                'role': 'Test rapid explosion patterns',
                'stock_data': fast
            })
        
        # 5. Slow builder (test slow accumulation patterns)
        slow = max([s for s in self.stocks if s.get('days_to_peak', 0) > 90], 
                   key=lambda x: x.get('days_to_peak', 0))
        if slow not in [s['stock_data'] for s in selected]:
            selected.append({
                'ticker': slow.get('ticker'),
                'year': slow.get('year'),
                'reason': f"Slow builder - {slow.get('gain_percent', 0):.0f}% in {slow.get('days_to_peak', 0)} days",
                'role': 'Test slow accumulation patterns',
                'stock_data': slow
            })
        
        # 6. Longest exit window (test extended tradeable period)
        stocks_with_windows = [s for s in self.stocks if 'sustainability_test' in s]
        longest = max(stocks_with_windows, 
                     key=lambda x: x['sustainability_test'].get('days_above_threshold', 0))
        if longest not in [s['stock_data'] for s in selected]:
            selected.append({
                'ticker': longest.get('ticker'),
                'year': longest.get('year'),
                'reason': f"Longest exit window - {longest['sustainability_test'].get('days_above_threshold', 0)} days",
                'role': 'Test extended tradeable period',
                'stock_data': longest
            })
        
        # 7-8. Historical diversity (different years)
        historical = [s for s in self.stocks if s.get('year') in [2022, 2023] 
                     and s not in [sel['stock_data'] for sel in selected]]
        for stock in historical[:2]:
            selected.append({
                'ticker': stock.get('ticker'),
                'year': stock.get('year'),
                'reason': f"Historical diversity - {stock.get('gain_percent', 0):.0f}% in {stock.get('days_to_peak', 0)} days",
                'role': f"Represent {stock.get('year')} winners",
                'stock_data': stock
            })
        
        print(f"  Selected {len(selected)} stocks for deep dive:")
        for i, selection in enumerate(selected, 1):
            print(f"  {i}. {selection['ticker']} ({selection['year']})")
            print(f"     {selection['reason']}")
            print(f"     Role: {selection['role']}")
        
        self.sample_selection = selected
        return selected
        
    def save_results(self):
        """Save all analysis results"""
        output_dir = Path('Verified_Backtest_Data')
        
        # Save full analysis
        analysis_path = output_dir / 'phase3_initial_analysis.json'
        with open(analysis_path, 'w') as f:
            json.dump({
                'generated': datetime.now().isoformat(),
                'total_stocks_analyzed': len(self.stocks),
                'analysis': self.analysis_results
            }, f, indent=2)
        print(f"\n✅ Saved analysis: {analysis_path}")
        
        # Save sample selection
        sample_path = output_dir / 'phase3_sample_selection.json'
        sample_data = {
            'generated': datetime.now().isoformat(),
            'sample_size': len(self.sample_selection),
            'selection_criteria': 'Maximum diversity across years, gains, speeds, and data quality',
            'stocks': [{
                'ticker': s['ticker'],
                'year': s['year'],
                'reason': s['reason'],
                'role': s['role'],
                'gain_percent': s['stock_data'].get('gain_percent'),
                'days_to_peak': s['stock_data'].get('days_to_peak'),
                'days_above_200': s['stock_data'].get('sustainability_test', {}).get('days_above_threshold'),
                'enriched': s['stock_data'].get('enriched', False)
            } for s in self.sample_selection]
        }
        with open(sample_path, 'w') as f:
            json.dump(sample_data, f, indent=2)
        print(f"✅ Saved sample selection: {sample_path}")
        
        # Generate insights report
        insights_path = output_dir / 'phase3_insights_report.md'
        self.generate_insights_report(insights_path)
        print(f"✅ Saved insights report: {insights_path}")
        
        # Generate next steps
        next_steps_path = output_dir / 'phase3_next_steps.md'
        self.generate_next_steps(next_steps_path)
        print(f"✅ Saved next steps: {next_steps_path}")
        
    def generate_insights_report(self, path):
        """Generate human-readable insights report"""
        with open(path, 'w') as f:
            f.write("# Phase 3A: Initial Pattern Discovery - Insights Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Stocks Analyzed**: {len(self.stocks)}\n\n")
            
            f.write("## Key Findings\n\n")
            
            # Temporal insights
            temp = self.analysis_results.get('temporal', {})
            f.write("### Temporal Patterns\n\n")
            f.write(f"- **Average time to peak**: {temp.get('average_days_to_peak', 0):.1f} days\n")
            speed = temp.get('speed_distribution', {})
            f.write(f"- **Speed distribution**:\n")
            f.write(f"  - Fast (<30 days): {speed.get('fast', 0)} stocks\n")
            f.write(f"  - Medium (30-90 days): {speed.get('medium', 0)} stocks\n")
            f.write(f"  - Slow (90+ days): {speed.get('slow', 0)} stocks\n\n")
            
            # Gain insights
            gains = self.analysis_results.get('gains', {})
            f.write("### Gain Characteristics\n\n")
            f.write(f"- **Average gain**: {gains.get('average_gain_percent', 0):.1f}%\n")
            f.write(f"- **Median gain**: {gains.get('median_gain_percent', 0):.1f}%\n")
            f.write(f"- **Average exit window**: {gains.get('average_exit_window_days', 0):.1f} days\n\n")
            
            # Exit window insights
            exits = self.analysis_results.get('exit_windows', {})
            f.write("### Exit Window Analysis\n\n")
            trade = exits.get('tradeable_classifications', {})
            f.write(f"- **Risky** (<21 days): {trade.get('RISKY', 0)} stocks\n")
            f.write(f"- **Tradeable** (21-49 days): {trade.get('TRADEABLE', 0)} stocks\n")
            f.write(f"- **Comfortable** (50-99 days): {trade.get('COMFORTABLE', 0)} stocks\n")
            f.write(f"- **Extended** (100+ days): {trade.get('EXTENDED', 0)} stocks\n\n")
            
            # Top performers
            f.write("### Top Performers\n\n")
            tops = self.analysis_results.get('top_performers', {})
            f.write("**Top 5 Gainers**:\n")
            for stock in tops.get('top_gainers', [])[:5]:
                f.write(f"- {stock['ticker']} ({stock['year']}): {stock['gain_percent']:.0f}% in {stock['days']} days\n")
            
            f.write("\n**Longest Exit Windows**:\n")
            for stock in tops.get('longest_windows', [])[:5]:
                f.write(f"- {stock['ticker']} ({stock['year']}): {stock['days_above_200']} days above 200%\n")
            
            f.write("\n## Sample Selection for Phase 3B\n\n")
            f.write(f"Selected {len(self.sample_selection)} diverse stocks for comprehensive analysis:\n\n")
            for i, stock in enumerate(self.sample_selection, 1):
                f.write(f"{i}. **{stock['ticker']}** ({stock['year']})\n")
                f.write(f"   - {stock['reason']}\n")
                f.write(f"   - Role: {stock['role']}\n\n")
                
    def generate_next_steps(self, path):
        """Generate next steps roadmap"""
        with open(path, 'w') as f:
            f.write("# Phase 3: Next Steps Roadmap\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Phase 3A Complete ✅\n\n")
            f.write(f"- Statistical analysis: {len(self.stocks)} stocks\n")
            f.write(f"- Sample selection: {len(self.sample_selection)} stocks\n")
            f.write("- Preliminary insights generated\n\n")
            
            f.write("## Phase 3B: Comprehensive Pre-Catalyst Analysis\n\n")
            f.write("### Immediate Actions\n\n")
            f.write("1. **Review Sample Selection**\n")
            f.write("   - Verify 8 stocks cover desired diversity\n")
            f.write("   - Confirm data availability for each\n")
            f.write("   - Adjust selection if needed\n\n")
            
            f.write("2. **Build Data Collection Tools**\n")
            f.write("   - Polygon API integration (OHLC, volume, technicals)\n")
            f.write("   - SEC filing scraper (Form 4, 13F)\n")
            f.write("   - Social sentiment collector (Reddit, Twitter)\n")
            f.write("   - Options data aggregator\n\n")
            
            f.write("3. **Begin Deep Dive Analysis**\n")
            f.write("   - Start with 2-3 sample stocks\n")
            f.write("   - Validate comprehensive framework\n")
            f.write("   - Collect 180-day pre-catalyst data\n")
            f.write("   - Generate individual analysis files\n\n")
            
            f.write("4. **Iterate and Refine**\n")
            f.write("   - Refine methodology based on findings\n")
            f.write("   - Complete remaining 5-6 stocks\n")
            f.write("   - Build correlation matrix\n\n")
            
            f.write("5. **Generate Deliverables**\n")
            f.write("   - 8 comprehensive JSON files\n")
            f.write("   - Pattern library documentation\n")
            f.write("   - Preliminary screening criteria\n")
            f.write("   - Correlation analysis report\n\n")
            
            f.write("### Timeline Estimate\n\n")
            f.write("- Sample analysis (8 stocks): 12-19 hours\n")
            f.write("- Framework refinement: 4-6 hours\n")
            f.write("- Correlation analysis: 6-8 hours\n")
            f.write("- Documentation: 4-6 hours\n")
            f.write("- **Total**: 4-6 weeks\n\n")
            
            f.write("### Key Framework Reference\n\n")
            f.write("See `PRE_CATALYST_ANALYSIS_FRAMEWORK.md` for:\n")
            f.write("- 12 data categories\n")
            f.write("- 100+ metrics per stock\n")
            f.write("- Analysis methodology\n")
            f.write("- Expected outcomes\n")
            
    def run_analysis(self):
        """Execute complete Phase 3A analysis"""
        print("=" * 80)
        print("PHASE 3: PATTERN DISCOVERY & ANALYSIS")
        print("=" * 80)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.load_data()
        self.analyze_temporal_patterns()
        self.analyze_gain_characteristics()
        self.analyze_exit_windows()
        self.analyze_data_quality()
        self.identify_top_performers()
        self.select_deep_dive_sample()
        
        # Note: Screening criteria generation is postponed to Phase 3B
        # After deep dive analysis, we'll have correlation data to build criteria
        
        self.save_results()
        
        print("\n" + "=" * 80)
        print("✅ PHASE 3A COMPLETE")
        print("=" * 80)
        print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📋 Next: Review sample selection and begin Phase 3B deep dive")

def main():
    analyzer = Phase3Analyzer('Verified_Backtest_Data/explosive_stocks_CLEAN.json')
    analyzer.run_analysis()

if __name__ == '__main__':
    main()
