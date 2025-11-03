#!/usr/bin/env python3
"""
Phase 3B Pilot Analysis
Test the 90-day framework on 1-2 sample stocks
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Import our collector
from polygon_data_collector import PolygonDataCollector

class Phase3BPilot:
    def __init__(self):
        self.collector = PolygonDataCollector()
        self.sample_stocks = self._load_sample_stocks()
        
    def _load_sample_stocks(self):
        """Load the 8 selected stocks"""
        sample_file = Path('Verified_Backtest_Data/phase3_sample_selection.json')
        
        if not sample_file.exists():
            print("❌ Sample selection file not found")
            return []
        
        with open(sample_file, 'r') as f:
            data = json.load(f)
            return data.get('stocks', [])
    
    def analyze_stock(self, ticker: str, year: int) -> dict:
        """Run complete 90-day analysis on a stock"""
        print(f"\n{'='*80}")
        print(f"ANALYZING: {ticker} ({year})")
        print(f"{'='*80}")
        
        # Find stock in sample
        stock_info = next((s for s in self.sample_stocks 
                          if s['ticker'] == ticker and s['year'] == year), None)
        
        if not stock_info:
            print(f"❌ Stock {ticker} ({year}) not in sample selection")
            return {}
        
        # Get entry date from CLEAN.json
        entry_date = self._get_entry_date(ticker, year)
        
        if not entry_date:
            print(f"❌ Could not find entry date for {ticker}")
            return {}
        
        print(f"📅 Entry Date: {entry_date}")
        print(f"🎯 Gain: {stock_info['gain_percent']:.0f}%")
        print(f"⏱️  Days to Peak: {stock_info['days_to_peak']}")
        print(f"📋 Role: {stock_info['role']}")
        
        # Collect 90-day data
        polygon_data = self.collector.get_90_day_data(ticker, entry_date)
        
        # Build comprehensive analysis
        analysis = {
            "metadata": {
                "ticker": ticker,
                "year": year,
                "entry_date": entry_date,
                "gain_percent": stock_info['gain_percent'],
                "days_to_peak": stock_info['days_to_peak'],
                "role": stock_info['role'],
                "analysis_date": datetime.now().isoformat()
            },
            "price_volume": polygon_data.get('price_volume', {}),
            "technical_indicators": polygon_data.get('technical_indicators', {}),
            "volume_analysis": polygon_data.get('volume_analysis', {}),
            "patterns_detected": polygon_data.get('patterns_detected', []),
            
            # Placeholders for manual data collection
            "float_ownership": {
                "note": "Manual collection required - SEC Form 4, 13F",
                "insider_transactions": [],
                "institutional_changes": [],
                "short_interest": {}
            },
            "catalyst_intelligence": {
                "note": "Manual research required",
                "catalyst_type": "TBD",
                "catalyst_date": "TBD",
                "predictability": "TBD"
            },
            "news_sentiment": {
                "note": "Manual collection required",
                "article_counts": {},
                "sentiment_scores": {},
                "social_mentions": {}
            },
            
            "summary": {
                "days_analyzed": polygon_data.get('analysis_window', {}).get('days_analyzed', 0),
                "patterns_found": len(polygon_data.get('patterns_detected', [])),
                "data_quality": "good" if polygon_data.get('analysis_window', {}).get('days_analyzed', 0) >= 60 else "partial",
                "actionability": "TBD - pending manual data"
            }
        }
        
        return analysis
    
    def _get_entry_date(self, ticker: str, year: int) -> str:
        """Get entry date from CLEAN.json"""
        clean_file = Path('Verified_Backtest_Data/explosive_stocks_CLEAN.json')
        
        if not clean_file.exists():
            return None
        
        with open(clean_file, 'r') as f:
            data = json.load(f)
            stocks = data.get('stocks', [])
            
            stock = next((s for s in stocks 
                         if s.get('ticker') == ticker and s.get('year') == year), None)
            
            if stock:
                return stock.get('entry_date')
        
        return None
    
    def run_pilot(self, pilot_stocks: list = None):
        """Run pilot analysis on specified stocks"""
        if pilot_stocks is None:
            # Default: AENTW (extreme outlier) + ASNS (ultra-fast)
            pilot_stocks = [
                ('AENTW', 2024),
                ('ASNS', 2024)
            ]
        
        print("\n" + "="*80)
        print("PHASE 3B PILOT ANALYSIS")
        print("="*80)
        print(f"Stocks to analyze: {len(pilot_stocks)}")
        print(f"Analysis window: 90 days before entry")
        print("="*80)
        
        results = []
        
        for ticker, year in pilot_stocks:
            try:
                analysis = self.analyze_stock(ticker, year)
                
                if analysis:
                    # Save individual analysis
                    output_file = f"Verified_Backtest_Data/phase3b_{ticker}_{year}_analysis.json"
                    with open(output_file, 'w') as f:
                        json.dump(analysis, f, indent=2)
                    
                    print(f"\n✅ Saved: {output_file}")
                    
                    # Print summary
                    summary = analysis.get('summary', {})
                    patterns = analysis.get('patterns_detected', [])
                    
                    print(f"\n📊 Summary:")
                    print(f"   Days analyzed: {summary.get('days_analyzed', 0)}")
                    print(f"   Patterns found: {summary.get('patterns_found', 0)}")
                    
                    if patterns:
                        print(f"   Patterns detected:")
                        for p in patterns:
                            print(f"      - {p['pattern']} ({p['confidence']} confidence)")
                    
                    results.append({
                        'ticker': ticker,
                        'year': year,
                        'status': 'success',
                        'file': output_file
                    })
                else:
                    results.append({
                        'ticker': ticker,
                        'year': year,
                        'status': 'failed',
                        'error': 'Analysis incomplete'
                    })
                    
            except Exception as e:
                print(f"\n❌ Error analyzing {ticker}: {str(e)}")
                results.append({
                    'ticker': ticker,
                    'year': year,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Save pilot summary
        pilot_summary = {
            "pilot_date": datetime.now().isoformat(),
            "stocks_analyzed": len(pilot_stocks),
            "successful": sum(1 for r in results if r['status'] == 'success'),
            "failed": sum(1 for r in results if r['status'] != 'success'),
            "results": results
        }
        
        summary_file = "Verified_Backtest_Data/phase3b_pilot_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(pilot_summary, f, indent=2)
        
        print(f"\n{'='*80}")
        print("PILOT ANALYSIS COMPLETE")
        print(f"{'='*80}")
        print(f"✅ Successful: {pilot_summary['successful']}")
        print(f"❌ Failed: {pilot_summary['failed']}")
        print(f"📄 Summary: {summary_file}")
        
        return pilot_summary

def main():
    """Run the pilot"""
    pilot = Phase3BPilot()
    
    # Run on default stocks (AENTW + ASNS)
    pilot.run_pilot()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Review the generated analysis files")
    print("2. Manually collect insider/catalyst/sentiment data")
    print("3. Refine pattern detection based on findings")
    print("4. If validated, scale to remaining 6 stocks")
    print("5. Build correlation matrix from all 8 analyses")

if __name__ == '__main__':
    main()
