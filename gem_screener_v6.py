#!/usr/bin/env python3
"""
GEM Screener v6.0 - Built on Verified Data Only
Based on Phase 3 analysis of 694 verified explosive stocks
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class GEMScreenerV6:
    def __init__(self):
        """Initialize with verified pattern weights from Phase 3 analysis"""
        # Pattern weights based on correlation data
        self.weights = {
            'volume_3x': 25,      # 90% frequency, 0.9 correlation
            'volume_5x': 35,      # 70% frequency, 0.7 correlation  
            'volume_10x': 50,     # 37.6% frequency, high impact
            'rsi_oversold_35': 20,  # 84% frequency
            'rsi_oversold_30': 30,  # Less common, more powerful
            'accumulation': 40,    # 20% frequency, 22,155% avg gain!
            'market_outperform': 15,  # 100% frequency baseline
            
            # Composite bonuses
            'volume_rsi_combo': 25,    # 80% frequency, 9,882% avg
            'rsi_accumulation_combo': 40,  # 20% frequency, 22,155% avg
            'triple_signal': 50,       # 20% frequency, highest gains
            
            # Additional factors
            'first_spike_30days': 10,
            'breaking_resistance': 10,
            'clean_setup': 5
        }
        
        # Core filters
        self.filters = {
            'min_price': 0.50,
            'max_price': 7.00,
            'extended_max_price': 15.00,  # For strong signals
            'min_volume': 10000,
            'max_float': 100_000_000  # 100M shares
        }
        
        # Tracking for analysis
        self.screening_history = []
        self.rejected_stocks = []  # Track these for false negatives!
        
    def calculate_indicators(self, ticker):
        """Calculate technical indicators for a stock"""
        try:
            # Get 60 days of data for calculations
            stock = yf.Ticker(ticker)
            df = stock.history(period="3mo")
            
            if len(df) < 20:
                return None
                
            # Current metrics
            current_price = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            
            # Volume analysis (critical pattern from verified data)
            avg_volume_20 = df['Volume'].iloc[-20:].mean()
            avg_volume_5 = df['Volume'].iloc[-5:].mean()
            volume_spike_today = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0
            volume_spike_5day = avg_volume_5 / avg_volume_20 if avg_volume_20 > 0 else 0
            max_volume_5day = df['Volume'].iloc[-5:].max()
            max_volume_spike = max_volume_5day / avg_volume_20 if avg_volume_20 > 0 else 0
            
            # RSI calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            min_rsi_10day = rsi.iloc[-10:].min()
            
            # Accumulation (OBV)
            obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
            obv_slope = np.polyfit(range(20), obv.iloc[-20:].values, 1)[0]
            
            # Price trend (for accumulation pattern)
            lows_20day = df['Low'].iloc[-20:]
            higher_lows = all(lows_20day.iloc[i] <= lows_20day.iloc[i+1] 
                             for i in range(0, len(lows_20day)-5, 5))
            
            # Market outperformance (vs SPY)
            spy = yf.Ticker("SPY")
            spy_df = spy.history(period="1mo")
            stock_return_1m = (df['Close'].iloc[-1] / df['Close'].iloc[-20] - 1) * 100
            spy_return_1m = (spy_df['Close'].iloc[-1] / spy_df['Close'].iloc[-20] - 1) * 100
            outperformance = stock_return_1m - spy_return_1m
            
            # Days since last major spike
            major_spikes = df['Volume'] > (df['Volume'].rolling(20).mean() * 3)
            days_since_spike = (~major_spikes.iloc[-30:]).sum() if major_spikes.any() else 30
            
            # Resistance levels
            resistance = df['High'].iloc[-20:].max()
            breaking_resistance = current_price > resistance * 0.98
            
            # Get basic info
            info = stock.info
            
            return {
                'ticker': ticker,
                'price': current_price,
                'volume': current_volume,
                'avg_volume': avg_volume_20,
                'market_cap': info.get('marketCap', 0),
                'float': info.get('floatShares', info.get('sharesOutstanding', 0)),
                
                # Pattern indicators
                'volume_spike_today': volume_spike_today,
                'volume_spike_5day': volume_spike_5day,
                'max_volume_spike': max_volume_spike,
                'rsi': current_rsi,
                'min_rsi_10day': min_rsi_10day,
                'obv_slope': obv_slope,
                'higher_lows': higher_lows,
                'outperformance': outperformance,
                'days_since_spike': days_since_spike,
                'breaking_resistance': breaking_resistance,
                
                # Raw data for analysis
                'df': df
            }
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {str(e)}")
            return None
    
    def calculate_score(self, data):
        """Calculate score based on verified patterns from Phase 3"""
        score = 0
        patterns_found = []
        
        # Volume patterns (most important from verified data)
        if data['max_volume_spike'] >= 10:
            score += self.weights['volume_10x']
            patterns_found.append('volume_10x')
        elif data['max_volume_spike'] >= 5:
            score += self.weights['volume_5x']
            patterns_found.append('volume_5x')
        elif data['max_volume_spike'] >= 3:
            score += self.weights['volume_3x']
            patterns_found.append('volume_3x')
            
        # RSI patterns
        if data['min_rsi_10day'] < 30:
            score += self.weights['rsi_oversold_30']
            patterns_found.append('rsi_oversold_30')
        elif data['min_rsi_10day'] < 35:
            score += self.weights['rsi_oversold_35']
            patterns_found.append('rsi_oversold_35')
            
        # Accumulation pattern (rare but powerful)
        if data['obv_slope'] > 0 and data['higher_lows']:
            score += self.weights['accumulation']
            patterns_found.append('accumulation')
            
        # Market outperformance
        if data['outperformance'] > 0:
            score += self.weights['market_outperform']
            patterns_found.append('market_outperform')
            
        # Composite bonuses (critical from verified data)
        has_volume = any(p in patterns_found for p in ['volume_3x', 'volume_5x', 'volume_10x'])
        has_rsi = any(p in patterns_found for p in ['rsi_oversold_30', 'rsi_oversold_35'])
        has_accumulation = 'accumulation' in patterns_found
        
        if has_volume and has_rsi:
            score += self.weights['volume_rsi_combo']
            patterns_found.append('volume_rsi_combo')
            
        if has_rsi and has_accumulation:
            score += self.weights['rsi_accumulation_combo']
            patterns_found.append('rsi_accumulation_combo')
            
        if has_volume and has_rsi and has_accumulation:
            score += self.weights['triple_signal']
            patterns_found.append('triple_signal')
            
        # Additional scoring factors
        if data['days_since_spike'] >= 30:
            score += self.weights['first_spike_30days']
            patterns_found.append('first_spike_30days')
            
        if data['breaking_resistance']:
            score += self.weights['breaking_resistance']
            patterns_found.append('breaking_resistance')
            
        # Clean setup bonus
        if len(patterns_found) >= 3:
            score += self.weights['clean_setup']
            
        return score, patterns_found
    
    def screen_stock(self, ticker):
        """Screen a single stock through all phases"""
        # Phase 1: Get data and apply basic filters
        data = self.calculate_indicators(ticker)
        if not data:
            return None
            
        # Core filters
        if data['price'] < self.filters['min_price'] or data['price'] > self.filters['extended_max_price']:
            self.rejected_stocks.append({
                'ticker': ticker,
                'reason': 'price_out_of_range',
                'price': data['price'],
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            return None
            
        if data['avg_volume'] < self.filters['min_volume']:
            self.rejected_stocks.append({
                'ticker': ticker, 
                'reason': 'low_volume',
                'volume': data['avg_volume'],
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            return None
            
        if data['float'] > self.filters['max_float'] and data['float'] > 0:
            self.rejected_stocks.append({
                'ticker': ticker,
                'reason': 'high_float',
                'float': data['float'],
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            return None
            
        # Phase 2: Calculate pattern score
        score, patterns = self.calculate_score(data)
        
        # Store result
        result = {
            'ticker': ticker,
            'score': score,
            'patterns': patterns,
            'price': data['price'],
            'volume_spike': max(data['volume_spike_today'], data['max_volume_spike']),
            'rsi': data['rsi'],
            'outperformance': data['outperformance'],
            'market_cap': data['market_cap'],
            'recommendation': self.get_recommendation(score),
            'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
    
    def get_recommendation(self, score):
        """Get recommendation based on score thresholds"""
        if score >= 100:
            return "STRONG BUY"
        elif score >= 75:
            return "BUY"
        elif score >= 60:
            return "WATCH"
        else:
            return "PASS"
    
    def run_screen(self, tickers):
        """Run screening on a list of tickers"""
        results = []
        
        print(f"Screening {len(tickers)} stocks...")
        print("=" * 60)
        
        for ticker in tickers:
            print(f"Analyzing {ticker}...")
            result = self.screen_stock(ticker)
            if result:
                results.append(result)
                
        # Sort by score
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Store in history (including rejects for false negative analysis!)
        self.screening_history.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_screened': len(tickers),
            'passed_filters': len(results),
            'top_30': results[:30],  # Keep top 30 even if not buying!
            'rejected': self.rejected_stocks[-len(tickers):]  # Recent rejects
        })
        
        return results
    
    def display_results(self, results, top_n=30):
        """Display screening results"""
        print("\n" + "=" * 100)
        print(f"TOP {top_n} SCREENING RESULTS")
        print("=" * 100)
        
        # Create DataFrame for nice display
        if results:
            df = pd.DataFrame(results[:top_n])
            df = df[['ticker', 'score', 'recommendation', 'price', 
                    'volume_spike', 'rsi', 'patterns']]
            
            for idx, row in df.iterrows():
                print(f"\n{idx+1}. {row['ticker']} - Score: {row['score']} - {row['recommendation']}")
                print(f"   Price: ${row['price']:.2f} | Volume Spike: {row['volume_spike']:.1f}x | RSI: {row['rsi']:.1f}")
                print(f"   Patterns: {', '.join(row['patterns'][:5])}")
                
            # Summary statistics
            print("\n" + "=" * 100)
            print("SUMMARY STATISTICS")
            print("=" * 100)
            print(f"Strong Buy (100+): {len(df[df['score'] >= 100])} stocks")
            print(f"Buy (75-99): {len(df[(df['score'] >= 75) & (df['score'] < 100)])} stocks")
            print(f"Watch (60-74): {len(df[(df['score'] >= 60) & (df['score'] < 75)])} stocks")
            
            # Pattern frequency in top results
            all_patterns = []
            for patterns in df['patterns']:
                all_patterns.extend(patterns)
            
            from collections import Counter
            pattern_counts = Counter(all_patterns)
            
            print("\nMost Common Patterns in Top Picks:")
            for pattern, count in pattern_counts.most_common(5):
                pct = (count / len(df)) * 100
                print(f"  {pattern}: {count} stocks ({pct:.1f}%)")
                
        else:
            print("No stocks passed the screening filters.")
            
        return df if results else None
    
    def export_results(self, results, filename=None):
        """Export results to JSON for tracking and analysis"""
        if filename is None:
            filename = f"gem_screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        # Include full history for false negative analysis
        export_data = {
            'screen_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'parameters': {
                'weights': self.weights,
                'filters': self.filters
            },
            'results': {
                'all_results': results,
                'top_30': results[:30],
                'strong_buys': [r for r in results if r['score'] >= 100],
                'buys': [r for r in results if 75 <= r['score'] < 100],
                'watch_list': [r for r in results if 60 <= r['score'] < 75]
            },
            'rejected_stocks': self.rejected_stocks,
            'statistics': {
                'total_passed': len(results),
                'total_rejected': len(self.rejected_stocks),
                'avg_score': np.mean([r['score'] for r in results]) if results else 0,
                'max_score': max([r['score'] for r in results]) if results else 0
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
            
        print(f"\nResults exported to: {filename}")
        print("Remember to track all top 30 for false negative analysis!")
        
        return filename
    
    def backtest_stock(self, ticker, check_date, forward_days=120):
        """Check if a stock exploded within forward_days of check_date"""
        # This is for backtesting - checking if our rejects actually exploded
        try:
            stock = yf.Ticker(ticker)
            
            # Get data from check_date forward
            start = pd.to_datetime(check_date)
            end = start + timedelta(days=forward_days)
            
            df = stock.history(start=start, end=end)
            if len(df) == 0:
                return None
                
            start_price = df['Close'].iloc[0]
            max_price = df['Close'].max()
            max_gain = ((max_price - start_price) / start_price) * 100
            
            return {
                'ticker': ticker,
                'check_date': check_date,
                'start_price': start_price,
                'max_price': max_price,
                'max_gain_pct': max_gain,
                'exploded': max_gain >= 100,  # 100% gain threshold
                'days_to_peak': df['Close'].idxmax()
            }
            
        except Exception as e:
            print(f"Error backtesting {ticker}: {e}")
            return None


def main():
    """Main function to run the screener"""
    screener = GEMScreenerV6()
    
    # Example ticker list - replace with your universe
    # This is just for testing - you'd want to use your full stock universe
    test_tickers = [
        'AAPL', 'MSFT', 'NVDA', 'AMD', 'TSLA',  # Large caps for testing
        'PLTR', 'SOFI', 'RIVN', 'LCID', 'NIO',  # Mid/small caps
        'BBIG', 'PROG', 'ATER', 'VERU', 'IMPP'   # Penny stocks
    ]
    
    # Run the screen
    results = screener.run_screen(test_tickers)
    
    # Display results
    df_results = screener.display_results(results, top_n=30)
    
    # Export for tracking
    if results:
        screener.export_results(results)
    
    # Important reminder
    print("\n" + "="*60)
    print("CRITICAL REMINDERS:")
    print("="*60)
    print("1. Track ALL top 30 stocks for 120 days (even rejects)")
    print("2. Check rejected stocks for false negatives")
    print("3. Document why each stock was bought or passed")
    print("4. Review patterns monthly and adjust weights")
    print("5. This is based on VERIFIED DATA from 694 explosive stocks")
    
    return screener, results


if __name__ == "__main__":
    screener, results = main()
