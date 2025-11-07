#!/usr/bin/env python3
"""
GEM Screener v6.0 - Backtesting Framework
Tests screener against verified explosive stocks to optimize weights and reduce false negatives
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from gem_screener_v6 import GEMScreenerV6
import warnings
warnings.filterwarnings('ignore')

class GEMBacktester:
    def __init__(self, verified_stocks_file=None):
        """Initialize backtester with verified explosive stocks data"""
        self.screener = GEMScreenerV6()
        self.verified_stocks = self.load_verified_stocks(verified_stocks_file)
        self.backtest_results = []
        self.false_negatives = []
        self.false_positives = []
        self.true_positives = []
        
    def load_verified_stocks(self, filename):
        """Load the 694 verified explosive stocks from Phase 3 analysis"""
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
                # Extract stock list from your phase3 data structure
                return data
        else:
            # Placeholder - replace with actual verified stock list
            return {
                'ACONW': {'gain': 8875, 'explosion_date': '2019-03-15'},
                'ASNS': {'gain': 5420, 'explosion_date': '2018-06-20'},
                'AIMD': {'gain': 12340, 'explosion_date': '2022-09-10'},
                # Add all 694 stocks here from your verified data
            }
    
    def test_screener_on_date(self, test_date, stock_universe):
        """Run screener on a specific date and check results"""
        print(f"\nTesting screener on {test_date}")
        print("-" * 40)
        
        # Run screener on all stocks
        results = []
        for ticker in stock_universe:
            result = self.simulate_screen_historical(ticker, test_date)
            if result:
                results.append(result)
        
        # Sort by score
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Get top 30
        top_30 = results[:30]
        
        # Track which exploded in next 120 days
        explosion_tracking = []
        for stock_result in top_30:
            ticker = stock_result['ticker']
            exploded = self.check_explosion(ticker, test_date, days_forward=120)
            
            explosion_tracking.append({
                'ticker': ticker,
                'score': stock_result['score'],
                'rank': top_30.index(stock_result) + 1,
                'patterns': stock_result['patterns'],
                'exploded': exploded['exploded'] if exploded else False,
                'gain': exploded['max_gain_pct'] if exploded else 0,
                'days_to_explosion': exploded['days_to_peak'] if exploded else None
            })
        
        return {
            'test_date': test_date,
            'total_screened': len(stock_universe),
            'passed_filters': len(results),
            'top_30': explosion_tracking,
            'hit_rate': sum(1 for x in explosion_tracking if x['exploded']) / len(explosion_tracking) if explosion_tracking else 0
        }
    
    def simulate_screen_historical(self, ticker, check_date):
        """Simulate screening a stock on a historical date"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get 90 days of data before check_date
            end_date = pd.to_datetime(check_date)
            start_date = end_date - timedelta(days=90)
            
            df = stock.history(start=start_date, end=end_date)
            
            if len(df) < 20:
                return None
            
            # Calculate all indicators as of check_date
            current_price = df['Close'].iloc[-1]
            current_volume = df['Volume'].iloc[-1]
            
            # Volume analysis
            avg_volume_20 = df['Volume'].iloc[-20:].mean()
            max_volume_5day = df['Volume'].iloc[-5:].max()
            max_volume_spike = max_volume_5day / avg_volume_20 if avg_volume_20 > 0 else 0
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            min_rsi_10day = rsi.iloc[-10:].min()
            
            # Quick accumulation check
            obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
            obv_slope = np.polyfit(range(min(20, len(obv))), obv.iloc[-20:].values, 1)[0]
            
            # Apply filters
            if current_price < 0.50 or current_price > 15:
                return None
            if avg_volume_20 < 10000:
                return None
            
            # Create data structure for scoring
            data = {
                'ticker': ticker,
                'price': current_price,
                'volume': current_volume,
                'avg_volume': avg_volume_20,
                'max_volume_spike': max_volume_spike,
                'volume_spike_today': current_volume / avg_volume_20 if avg_volume_20 > 0 else 0,
                'volume_spike_5day': max_volume_spike,
                'rsi': rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50,
                'min_rsi_10day': min_rsi_10day if not pd.isna(min_rsi_10day) else 50,
                'obv_slope': obv_slope,
                'higher_lows': False,  # Simplified for backtesting
                'outperformance': 0,  # Simplified for backtesting
                'days_since_spike': 30,
                'breaking_resistance': False
            }
            
            # Calculate score
            score, patterns = self.screener.calculate_score(data)
            
            return {
                'ticker': ticker,
                'score': score,
                'patterns': patterns,
                'check_date': check_date
            }
            
        except Exception as e:
            return None
    
    def check_explosion(self, ticker, start_date, days_forward=120):
        """Check if stock exploded (100%+ gain) within days_forward"""
        try:
            stock = yf.Ticker(ticker)
            
            start = pd.to_datetime(start_date)
            end = start + timedelta(days=days_forward)
            
            df = stock.history(start=start, end=end)
            if len(df) == 0:
                return None
            
            start_price = df['Close'].iloc[0]
            max_price = df['Close'].max()
            max_gain = ((max_price - start_price) / start_price) * 100
            
            # Find days to peak
            peak_date = df['Close'].idxmax()
            days_to_peak = (peak_date - start).days
            
            return {
                'ticker': ticker,
                'start_date': start_date,
                'start_price': start_price,
                'max_price': max_price,
                'max_gain_pct': max_gain,
                'exploded': max_gain >= 100,
                'days_to_peak': days_to_peak
            }
            
        except Exception as e:
            return None
    
    def analyze_false_negatives(self, test_date, known_explosions):
        """Find verified explosive stocks that screener missed"""
        print(f"\nAnalyzing false negatives for {test_date}")
        print("-" * 40)
        
        false_negs = []
        
        for ticker, explosion_info in known_explosions.items():
            explosion_date = pd.to_datetime(explosion_info['explosion_date'])
            
            # Check if we should have caught it
            check_window_start = explosion_date - timedelta(days=120)
            check_window_end = explosion_date - timedelta(days=1)
            
            test_dt = pd.to_datetime(test_date)
            
            if check_window_start <= test_dt <= check_window_end:
                # This stock exploded within 120 days, did we catch it?
                result = self.simulate_screen_historical(ticker, test_date)
                
                if not result or result['score'] < 60:
                    false_negs.append({
                        'ticker': ticker,
                        'explosion_date': explosion_info['explosion_date'],
                        'actual_gain': explosion_info['gain'],
                        'score_received': result['score'] if result else 0,
                        'patterns_found': result['patterns'] if result else [],
                        'days_until_explosion': (explosion_date - test_dt).days
                    })
        
        if false_negs:
            print(f"Found {len(false_negs)} false negatives:")
            for fn in false_negs[:5]:  # Show top 5
                print(f"  {fn['ticker']}: Score {fn['score_received']}, "
                      f"exploded in {fn['days_until_explosion']} days for {fn['actual_gain']:.0f}% gain")
        
        return false_negs
    
    def optimize_weights(self, test_dates, stock_universe):
        """Test different weight configurations to minimize false negatives"""
        print("\nOptimizing pattern weights...")
        print("=" * 60)
        
        best_weights = self.screener.weights.copy()
        best_hit_rate = 0
        
        # Test variations of weights
        weight_variations = [
            {'volume_3x': 30, 'volume_5x': 40, 'volume_10x': 60},  # Emphasize volume more
            {'rsi_oversold_30': 40, 'rsi_oversold_35': 30},  # Emphasize RSI more
            {'accumulation': 60},  # Boost rare but powerful pattern
            {'volume_rsi_combo': 40, 'triple_signal': 70},  # Boost composites
        ]
        
        for variation in weight_variations:
            # Apply variation
            test_weights = best_weights.copy()
            test_weights.update(variation)
            self.screener.weights = test_weights
            
            # Test on multiple dates
            total_hit_rate = 0
            for test_date in test_dates:
                result = self.test_screener_on_date(test_date, stock_universe)
                total_hit_rate += result['hit_rate']
            
            avg_hit_rate = total_hit_rate / len(test_dates)
            
            if avg_hit_rate > best_hit_rate:
                best_hit_rate = avg_hit_rate
                best_weights = test_weights.copy()
                print(f"New best weights found! Hit rate: {best_hit_rate:.2%}")
        
        return best_weights, best_hit_rate
    
    def generate_report(self, output_file='backtest_report.json'):
        """Generate comprehensive backtest report"""
        report = {
            'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'true_positives': len(self.true_positives),
                'false_negatives': len(self.false_negatives),
                'false_positives': len(self.false_positives),
                'overall_hit_rate': len(self.true_positives) / (len(self.true_positives) + len(self.false_positives)) if self.true_positives else 0
            },
            'pattern_analysis': self.analyze_pattern_performance(),
            'weight_recommendations': self.get_weight_recommendations(),
            'false_negative_patterns': self.analyze_false_negative_patterns(),
            'all_results': self.backtest_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nBacktest report saved to: {output_file}")
        return report
    
    def analyze_pattern_performance(self):
        """Analyze which patterns are most predictive"""
        pattern_stats = {}
        
        for result in self.backtest_results:
            if 'top_30' in result:
                for stock in result['top_30']:
                    for pattern in stock['patterns']:
                        if pattern not in pattern_stats:
                            pattern_stats[pattern] = {
                                'appearances': 0,
                                'explosions': 0,
                                'total_gain': 0,
                                'avg_score': 0
                            }
                        
                        pattern_stats[pattern]['appearances'] += 1
                        if stock['exploded']:
                            pattern_stats[pattern]['explosions'] += 1
                            pattern_stats[pattern]['total_gain'] += stock['gain']
                        pattern_stats[pattern]['avg_score'] += stock['score']
        
        # Calculate hit rates
        for pattern in pattern_stats:
            stats = pattern_stats[pattern]
            stats['hit_rate'] = stats['explosions'] / stats['appearances'] if stats['appearances'] > 0 else 0
            stats['avg_gain'] = stats['total_gain'] / stats['explosions'] if stats['explosions'] > 0 else 0
            stats['avg_score'] = stats['avg_score'] / stats['appearances'] if stats['appearances'] > 0 else 0
        
        return pattern_stats
    
    def analyze_false_negative_patterns(self):
        """Identify patterns in stocks we missed"""
        patterns = {}
        
        for fn in self.false_negatives:
            for pattern in fn.get('patterns_found', []):
                if pattern not in patterns:
                    patterns[pattern] = 0
                patterns[pattern] += 1
        
        return {
            'total_false_negatives': len(self.false_negatives),
            'pattern_frequency': patterns,
            'recommendations': self.get_false_negative_recommendations()
        }
    
    def get_false_negative_recommendations(self):
        """Get recommendations to reduce false negatives"""
        recommendations = []
        
        if len(self.false_negatives) > 0:
            avg_score = np.mean([fn.get('score_received', 0) for fn in self.false_negatives])
            
            if avg_score < 40:
                recommendations.append("Consider lowering minimum score threshold")
            if avg_score > 0 and avg_score < 60:
                recommendations.append("Many false negatives scored 40-60, consider tracking these")
            
            # Check days to explosion
            avg_days = np.mean([fn.get('days_until_explosion', 0) for fn in self.false_negatives])
            if avg_days > 60:
                recommendations.append(f"Average explosion happens {avg_days:.0f} days out - consider longer tracking")
        
        return recommendations
    
    def get_weight_recommendations(self):
        """Recommend weight adjustments based on backtest results"""
        pattern_perf = self.analyze_pattern_performance()
        recommendations = {}
        
        for pattern, stats in pattern_perf.items():
            current_weight = self.screener.weights.get(pattern, 0)
            
            if stats['hit_rate'] > 0.7 and current_weight < 40:
                recommendations[pattern] = {
                    'current': current_weight,
                    'recommended': min(current_weight + 10, 50),
                    'reason': f"High hit rate: {stats['hit_rate']:.2%}"
                }
            elif stats['hit_rate'] < 0.3 and current_weight > 20:
                recommendations[pattern] = {
                    'current': current_weight,
                    'recommended': max(current_weight - 10, 10),
                    'reason': f"Low hit rate: {stats['hit_rate']:.2%}"
                }
        
        return recommendations


def main():
    """Run comprehensive backtesting"""
    print("="*60)
    print("GEM SCREENER V6.0 - BACKTESTING")
    print("="*60)
    
    # Initialize backtester
    backtester = GEMBacktester()
    
    # Test dates (spread across different market conditions)
    test_dates = [
        '2019-01-15',
        '2019-06-15', 
        '2022-03-15',
        '2022-09-15',
        '2023-01-15',
        '2023-06-15'
    ]
    
    # Small test universe (expand this with your full universe)
    test_universe = [
        'ACONW', 'ASNS', 'AIMD', 'AENTW', 'ARWR', 'ACXP', 'AG', 'ALYA',
        # Add more stocks from your verified list
    ]
    
    # Run backtests
    for date in test_dates:
        result = backtester.test_screener_on_date(date, test_universe)
        backtester.backtest_results.append(result)
        
        print(f"\nResults for {date}:")
        print(f"  Hit rate in top 30: {result['hit_rate']:.2%}")
        print(f"  Stocks that exploded: {sum(1 for x in result['top_30'] if x['exploded'])}")
        
        # Check false negatives
        false_negs = backtester.analyze_false_negatives(date, backtester.verified_stocks)
        if false_negs:
            backtester.false_negatives.extend(false_negs)
    
    # Optimize weights
    print("\n" + "="*60)
    best_weights, best_rate = backtester.optimize_weights(test_dates[:3], test_universe)
    print(f"Best hit rate achieved: {best_rate:.2%}")
    
    # Generate report
    report = backtester.generate_report()
    
    # Key findings
    print("\n" + "="*60)
    print("KEY FINDINGS")
    print("="*60)
    print(f"Overall hit rate: {report['summary']['overall_hit_rate']:.2%}")
    print(f"False negatives: {report['summary']['false_negatives']}")
    print(f"False positives: {report['summary']['false_positives']}")
    
    print("\nTop performing patterns:")
    pattern_perf = report['pattern_analysis']
    sorted_patterns = sorted(pattern_perf.items(), 
                           key=lambda x: x[1].get('hit_rate', 0), 
                           reverse=True)
    for pattern, stats in sorted_patterns[:5]:
        print(f"  {pattern}: {stats['hit_rate']:.2%} hit rate, {stats['avg_gain']:.0f}% avg gain")
    
    print("\nCritical reminder: Track ALL top 30 stocks for 120 days!")
    
    return backtester, report


if __name__ == "__main__":
    backtester, report = main()
