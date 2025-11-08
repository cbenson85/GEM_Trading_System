"""
Phase 3 Catalyst Identifier
Identifies what triggered each stock's explosion
"""

import json
import sys
import requests
from datetime import datetime, timedelta
import re

class CatalystIdentifier:
    def __init__(self):
        self.catalyst_keywords = {
            'fda': ['fda', 'approval', 'crl', 'pdufa', 'adcom', 'cleared', 'clearance'],
            'clinical': ['phase', 'trial', 'results', 'data', 'topline', 'endpoint', 'study'],
            'merger': ['merger', 'acquisition', 'buyout', 'acquired', 'bid', 'offer', 'takeover'],
            'partnership': ['partnership', 'collaboration', 'deal', 'license', 'agreement'],
            'earnings': ['earnings', 'revenue', 'eps', 'beat', 'guidance', 'results'],
            'squeeze': ['squeeze', 'short', 'cover', 'gamma', 'options'],
            'legal': ['court', 'ruling', 'lawsuit', 'settlement', 'patent', 'litigation'],
            'social': ['reddit', 'wsb', 'meme', 'viral', 'trending'],
            'offering': ['offering', 'direct', 'dilution', 'warrants', 'shelf'],
            'bankruptcy': ['bankruptcy', 'chapter', 'restructuring', 'emergence']
        }
    
    def search_sec_filings(self, ticker, date_range):
        """Search for 8-K filings around explosion date"""
        # This would use SEC Edgar API
        # Placeholder for actual implementation
        filings = {
            'catalyst_type': 'unknown',
            'catalyst_date': None,
            'catalyst_details': '',
            'was_scheduled': False
        }
        return filings
    
    def search_news(self, ticker, explosion_date):
        """Search news archives for catalyst"""
        # Would implement news API search
        # Looking for news ±7 days from explosion
        return {
            'headlines': [],
            'catalyst_found': False
        }
    
    def identify_catalyst(self, stock_data):
        """Main function to identify what caused the explosion"""
        ticker = stock_data['ticker']
        explosion_date = stock_data.get('catalyst_date') or stock_data['entry_date']
        
        # Search window: 7 days before to 2 days after explosion
        explosion_dt = datetime.fromisoformat(explosion_date)
        search_start = explosion_dt - timedelta(days=7)
        search_end = explosion_dt + timedelta(days=2)
        
        result = {
            'ticker': ticker,
            'explosion_date': explosion_date,
            'gain_percent': stock_data['gain_percent'],
            'catalyst_type': 'unknown',
            'catalyst_subtype': '',
            'catalyst_date': None,
            'was_scheduled': False,
            'days_notice': 0,
            'catalyst_details': '',
            'data_sources': []
        }
        
        # Try SEC filings first
        sec_data = self.search_sec_filings(ticker, (search_start, search_end))
        if sec_data['catalyst_type'] != 'unknown':
            result.update(sec_data)
            result['data_sources'].append('SEC')
        
        # Try news search
        news_data = self.search_news(ticker, explosion_date)
        if news_data['catalyst_found']:
            # Parse headlines for catalyst type
            for headline in news_data['headlines']:
                for cat_type, keywords in self.catalyst_keywords.items():
                    if any(kw in headline.lower() for kw in keywords):
                        result['catalyst_type'] = cat_type
                        result['catalyst_details'] = headline
                        result['data_sources'].append('news')
                        break
        
        # Determine if it was scheduled
        if result['catalyst_type'] in ['fda', 'clinical', 'earnings']:
            result['was_scheduled'] = True
        
        return result

def main():
    """Process all explosive stocks to identify catalysts"""
    
    # Load explosive stocks
    with open('Verified_Backtest_Data/explosive_stocks_CLEAN.json', 'r') as f:
        stocks = json.load(f)
    
    identifier = CatalystIdentifier()
    catalyst_catalog = []
    
    # Statistics
    catalyst_stats = {
        'fda': 0,
        'clinical': 0,
        'merger': 0,
        'partnership': 0,
        'earnings': 0,
        'squeeze': 0,
        'social': 0,
        'unknown': 0
    }
    
    print(f"Analyzing {len(stocks)} explosive stocks for catalysts...")
    
    for i, stock in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] Analyzing {stock['ticker']}...")
        
        catalyst_info = identifier.identify_catalyst(stock)
        catalyst_catalog.append(catalyst_info)
        
        # Update stats
        cat_type = catalyst_info['catalyst_type']
        if cat_type in catalyst_stats:
            catalyst_stats[cat_type] += 1
        else:
            catalyst_stats['unknown'] += 1
        
        if i % 10 == 0:
            print(f"Progress: {i}/{len(stocks)} stocks analyzed")
    
    # Save results
    output = {
        'analysis_date': datetime.now().isoformat(),
        'total_stocks': len(stocks),
        'catalyst_statistics': catalyst_stats,
        'catalyst_catalog': catalyst_catalog
    }
    
    with open('Verified_Backtest_Data/phase3_catalyst_catalog.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("CATALYST ANALYSIS COMPLETE")
    print("="*60)
    for cat_type, count in catalyst_stats.items():
        pct = count / len(stocks) * 100
        print(f"{cat_type:12} : {count:4} ({pct:5.1f}%)")
    
    scheduled = sum(1 for c in catalyst_catalog if c['was_scheduled'])
    print(f"\nScheduled events: {scheduled}/{len(stocks)} ({scheduled/len(stocks)*100:.1f}%)")

if __name__ == "__main__":
    main()
