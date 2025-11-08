"""
Yahoo Finance Data Collector - REAL DATA
Gets market structure, fundamentals, and short interest data
"""

import yfinance as yf
import requests
from datetime import datetime, timedelta
import json

class YahooFinanceCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_market_structure(self, ticker):
        """Get real market structure data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract key market structure data
            shares_outstanding = info.get('sharesOutstanding', 0)
            float_shares = info.get('floatShares', shares_outstanding * 0.7)  # Estimate if not available
            market_cap = info.get('marketCap', 0)
            
            # Short interest data
            short_ratio = info.get('shortRatio', 0)
            short_percent_float = info.get('shortPercentOfFloat', 0)
            shares_short = info.get('sharesShort', 0)
            shares_short_prior = info.get('sharesShortPriorMonth', 0)
            
            # Trading data
            avg_volume_10d = info.get('averageVolume10days', 0)
            avg_volume = info.get('averageVolume', 0)
            
            # Price data
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            year_high = info.get('fiftyTwoWeekHigh', 0)
            year_low = info.get('fiftyTwoWeekLow', 0)
            
            # Calculate metrics
            pct_from_high = ((current_price - year_high) / year_high * 100) if year_high > 0 else 0
            pct_from_low = ((current_price - year_low) / year_low * 100) if year_low > 0 else 0
            
            # Volume to float ratio
            volume_float_ratio = (avg_volume_10d / float_shares) if float_shares > 0 else 0
            
            # Days to cover
            days_to_cover = (shares_short / avg_volume_10d) if avg_volume_10d > 0 else 0
            
            return {
                'shares_outstanding': shares_outstanding,
                'float_shares': float_shares,
                'market_cap': market_cap,
                'short_percent_float': short_percent_float * 100 if short_percent_float else 0,
                'short_ratio': short_ratio,
                'shares_short': shares_short,
                'shares_short_change': shares_short - shares_short_prior if shares_short_prior else 0,
                'days_to_cover': days_to_cover,
                'avg_volume_10d': avg_volume_10d,
                'avg_volume': avg_volume,
                'volume_float_ratio': volume_float_ratio,
                'current_price': current_price,
                'year_high': year_high,
                'year_low': year_low,
                'pct_from_52w_high': pct_from_high,
                'pct_from_52w_low': pct_from_low,
                'data_source': 'Yahoo_Finance',
                'data_retrieved': True
            }
            
        except Exception as e:
            print(f"  Error fetching Yahoo data for {ticker}: {e}")
            return {
                'data_retrieved': False,
                'error': str(e)
            }
    
    def get_fundamentals(self, ticker):
        """Get fundamental data"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get quarterly financials
            try:
                balance_sheet = stock.quarterly_balance_sheet
                if not balance_sheet.empty:
                    latest_quarter = balance_sheet.iloc[:, 0]
                    cash = latest_quarter.get('Cash', 0)
                    total_assets = latest_quarter.get('Total Assets', 0)
                    total_debt = latest_quarter.get('Total Debt', 0)
                else:
                    cash = total_assets = total_debt = 0
            except:
                cash = info.get('totalCash', 0)
                total_assets = info.get('totalAssets', 0)
                total_debt = info.get('totalDebt', 0)
            
            # Company info
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            employees = info.get('fullTimeEmployees', 0)
            
            # Valuation metrics
            pe_ratio = info.get('trailingPE', 0)
            book_value = info.get('bookValue', 0)
            price_to_book = info.get('priceToBook', 0)
            
            # Calculate important ratios
            market_cap = info.get('marketCap', 0)
            cash_to_market_cap = (cash / market_cap) if market_cap > 0 else 0
            
            return {
                'sector': sector,
                'industry': industry,
                'employees': employees,
                'cash': cash,
                'total_assets': total_assets,
                'total_debt': total_debt,
                'cash_to_market_cap': cash_to_market_cap,
                'pe_ratio': pe_ratio,
                'book_value': book_value,
                'price_to_book': price_to_book,
                'data_source': 'Yahoo_Finance'
            }
            
        except Exception as e:
            print(f"  Error fetching fundamentals for {ticker}: {e}")
            return {'data_source': 'Yahoo_Finance', 'error': str(e)}
    
    def get_historical_data(self, ticker, start_date, end_date):
        """Get historical price and volume data"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if not hist.empty:
                return {
                    'data_points': len(hist),
                    'avg_volume': hist['Volume'].mean(),
                    'max_volume': hist['Volume'].max(),
                    'min_volume': hist['Volume'].min(),
                    'avg_close': hist['Close'].mean(),
                    'max_close': hist['Close'].max(),
                    'min_close': hist['Close'].min(),
                    'volatility': hist['Close'].std() / hist['Close'].mean() if hist['Close'].mean() > 0 else 0
                }
            
        except Exception as e:
            print(f"  Error fetching historical data: {e}")
        
        return None

def collect_yahoo_data(stock):
    """Main function to collect Yahoo Finance data"""
    ticker = stock['ticker']
    explosion_date = stock.get('catalyst_date') or stock['entry_date']
    
    collector = YahooFinanceCollector()
    
    print(f"  Collecting Yahoo Finance data for {ticker}...")
    
    # Get market structure
    market_data = collector.get_market_structure(ticker)
    
    # Get fundamentals
    fundamental_data = collector.get_fundamentals(ticker)
    
    # Get historical data for 90 days before explosion
    explosion_dt = datetime.fromisoformat(explosion_date)
    end_dt = explosion_dt - timedelta(days=1)
    start_dt = end_dt - timedelta(days=90)
    
    historical = collector.get_historical_data(
        ticker,
        start_dt.strftime('%Y-%m-%d'),
        end_dt.strftime('%Y-%m-%d')
    )
    
    # Combine all data
    result = {
        'ticker': ticker,
        'market_structure': market_data,
        'fundamentals': fundamental_data,
        'historical_stats': historical
    }
    
    return result

if __name__ == "__main__":
    # Test with a sample stock
    test_stock = {
        'ticker': 'AMC',
        'entry_date': '2024-01-01',
        'catalyst_date': None
    }
    
    result = collect_yahoo_data(test_stock)
    print(json.dumps(result, indent=2, default=str))
