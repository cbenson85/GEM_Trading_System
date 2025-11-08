"""
Phase 3 Market Structure Collector
Gathers critical market structure data at explosion time
"""

import json
import requests
from datetime import datetime, timedelta
import os

class MarketStructureCollector:
    def __init__(self, polygon_api_key=None):
        self.api_key = polygon_api_key or os.environ.get('POLYGON_API_KEY')
        self.base_url = 'https://api.polygon.io'
    
    def get_ticker_details(self, ticker):
        """Get company details including share structure"""
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results']
                return {
                    'shares_outstanding': result.get('share_class_shares_outstanding', 0),
                    'market_cap': result.get('market_cap', 0),
                    'sic_description': result.get('sic_description', ''),
                    'total_employees': result.get('total_employees', 0),
                    'weighted_shares': result.get('weighted_shares_outstanding', 0)
                }
        except:
            pass
        return None
    
    def get_financials(self, ticker):
        """Get financial data to calculate key ratios"""
        url = f"{self.base_url}/vX/reference/financials"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'limit': 1
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                financials = result.get('financials', {})
                balance = financials.get('balance_sheet', {})
                
                return {
                    'current_assets': balance.get('current_assets', {}).get('value', 0),
                    'current_liabilities': balance.get('current_liabilities', {}).get('value', 0),
                    'cash': balance.get('cash_and_cash_equivalents', {}).get('value', 0),
                    'total_assets': balance.get('assets', {}).get('value', 0),
                    'total_debt': balance.get('total_debt', {}).get('value', 0),
                    'equity': balance.get('equity', {}).get('value', 0)
                }
        except:
            pass
        return None
    
    def calculate_float(self, ticker, shares_outstanding):
        """Estimate float from shares outstanding and insider holdings"""
        # This is a rough estimate - better data would come from other sources
        # Typically float = shares_outstanding - insider_holdings - institutional_holdings
        
        # For micro-caps, assume 70% of shares are float (rough estimate)
        estimated_float = shares_outstanding * 0.7
        
        return {
            'shares_outstanding': shares_outstanding,
            'estimated_float': estimated_float,
            'float_calculation_method': 'estimated_70_percent'
        }
    
    def get_trading_metrics(self, ticker, explosion_date):
        """Get trading metrics before explosion"""
        explosion_dt = datetime.fromisoformat(explosion_date)
        
        # Get 90 days of data before explosion
        end_date = (explosion_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (explosion_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                bars = data['results']
                
                # Calculate metrics
                volumes = [bar['v'] for bar in bars]
                closes = [bar['c'] for bar in bars]
                
                avg_volume_10d = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else 0
                avg_volume_30d = sum(volumes[-30:]) / 30 if len(volumes) >= 30 else 0
                avg_volume_90d = sum(volumes) / len(volumes) if volumes else 0
                
                # Price metrics
                last_close = closes[-1] if closes else 0
                high_52w = max(closes) if closes else 0
                low_52w = min(closes) if closes else 0
                
                pct_from_high = ((last_close - high_52w) / high_52w * 100) if high_52w > 0 else 0
                pct_from_low = ((last_close - low_52w) / low_52w * 100) if low_52w > 0 else 0
                
                # Dollar volume
                dollar_volume_avg = avg_volume_30d * last_close if avg_volume_30d > 0 else 0
                
                return {
                    'avg_volume_10d': avg_volume_10d,
                    'avg_volume_30d': avg_volume_30d,
                    'avg_volume_90d': avg_volume_90d,
                    'dollar_volume_avg': dollar_volume_avg,
                    'last_close_pre': last_close,
                    'high_52w_pre': high_52w,
                    'low_52w_pre': low_52w,
                    'pct_from_52w_high': pct_from_high,
                    'pct_from_52w_low': pct_from_low
                }
        except:
            pass
        return None
    
    def collect_market_structure(self, stock_data):
        """Collect all market structure data for a stock"""
        ticker = stock_data['ticker']
        explosion_date = stock_data.get('catalyst_date') or stock_data['entry_date']
        
        print(f"  Collecting market structure for {ticker}...")
        
        result = {
            'ticker': ticker,
            'explosion_date': explosion_date,
            'gain_percent': stock_data['gain_percent']
        }
        
        # Get ticker details
        details = self.get_ticker_details(ticker)
        if details:
            result.update(details)
            
            # Calculate float
            if details['shares_outstanding'] > 0:
                float_data = self.calculate_float(ticker, details['shares_outstanding'])
                result.update(float_data)
        
        # Get financials
        financials = self.get_financials(ticker)
        if financials:
            # Calculate key ratios
            if financials['current_liabilities'] > 0:
                result['current_ratio'] = financials['current_assets'] / financials['current_liabilities']
            
            if details and details['market_cap'] > 0:
                result['cash_to_market_cap'] = financials['cash'] / details['market_cap']
        
        # Get trading metrics
        trading = self.get_trading_metrics(ticker, explosion_date)
        if trading:
            result.update(trading)
            
            # Calculate volume/float ratio if we have float
            if 'estimated_float' in result and result['estimated_float'] > 0:
                result['volume_to_float_ratio'] = trading['avg_volume_30d'] / result['estimated_float']
        
        # SHORT INTEREST DATA (would need FINRA or other source)
        # Placeholder - this would need actual short interest API
        result['short_interest'] = None
        result['short_float_pct'] = None
        result['days_to_cover'] = None
        result['short_data_source'] = 'not_available'
        
        return result

def main():
    """Collect market structure for all explosive stocks"""
    
    # Load stocks
    with open('Verified_Backtest_Data/explosive_stocks_CLEAN.json', 'r') as f:
        stocks = json.load(f)
    
    collector = MarketStructureCollector()
    market_data = []
    
    # Statistics tracking
    stats = {
        'total_stocks': len(stocks),
        'micro_cap_count': 0,  # < $50M
        'small_cap_count': 0,  # $50M - $300M
        'low_float_count': 0,  # < 10M shares
        'high_volume_ratio': 0,  # volume/float > 1
    }
    
    print(f"Collecting market structure for {len(stocks)} stocks...")
    
    for i, stock in enumerate(stocks[:10], 1):  # Test with first 10
        print(f"\n[{i}/10] Processing {stock['ticker']}...")
        
        data = collector.collect_market_structure(stock)
        market_data.append(data)
        
        # Update statistics
        if data.get('market_cap'):
            if data['market_cap'] < 50_000_000:
                stats['micro_cap_count'] += 1
            elif data['market_cap'] < 300_000_000:
                stats['small_cap_count'] += 1
        
        if data.get('estimated_float'):
            if data['estimated_float'] < 10_000_000:
                stats['low_float_count'] += 1
        
        if data.get('volume_to_float_ratio'):
            if data['volume_to_float_ratio'] > 1:
                stats['high_volume_ratio'] += 1
    
    # Save results
    output = {
        'collection_date': datetime.now().isoformat(),
        'statistics': stats,
        'market_structure_data': market_data
    }
    
    with open('Verified_Backtest_Data/phase3_market_structure.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("MARKET STRUCTURE ANALYSIS COMPLETE")
    print("="*60)
    print(f"Micro-cap (<$50M): {stats['micro_cap_count']}")
    print(f"Small-cap ($50-300M): {stats['small_cap_count']}")
    print(f"Low float (<10M): {stats['low_float_count']}")
    print(f"High volume/float ratio: {stats['high_volume_ratio']}")

if __name__ == "__main__":
    main()
