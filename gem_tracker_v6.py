#!/usr/bin/env python3
"""
GEM Screener v6.0 - Top 30 Tracking System
Tracks all top 30 picks (even rejects) to identify false negatives
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta
import os

class GEMTracker:
    def __init__(self, tracking_file='gem_tracking_master.json'):
        """Initialize tracking system"""
        self.tracking_file = tracking_file
        self.tracking_data = self.load_tracking_data()
        
    def load_tracking_data(self):
        """Load existing tracking data or create new"""
        if os.path.exists(self.tracking_file):
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        else:
            return {
                'screens': [],
                'positions': [],
                'watchlist': [],
                'performance': {
                    'true_positives': 0,
                    'false_positives': 0,
                    'false_negatives': 0,
                    'total_return': 0
                }
            }
    
    def save_tracking_data(self):
        """Save tracking data to file"""
        with open(self.tracking_file, 'w') as f:
            json.dump(self.tracking_data, f, indent=2, default=str)
        print(f"Tracking data saved to {self.tracking_file}")
    
    def add_screening_results(self, screen_date, results):
        """Add new screening results to tracking"""
        # Get top 30
        top_30 = results[:30] if len(results) >= 30 else results
        
        screen_entry = {
            'screen_date': screen_date,
            'top_30': [],
            'positions_taken': [],
            'positions_rejected': []
        }
        
        # Process each stock in top 30
        for rank, stock in enumerate(top_30, 1):
            entry = {
                'ticker': stock['ticker'],
                'rank': rank,
                'score': stock['score'],
                'patterns': stock['patterns'],
                'recommendation': stock['recommendation'],
                'start_price': stock['price'],
                'start_date': screen_date,
                'status': 'pending',  # pending, bought, rejected, expired
                'reason': None,
                'tracking_end_date': (datetime.strptime(screen_date, '%Y-%m-%d') + 
                                     timedelta(days=120)).strftime('%Y-%m-%d'),
                'outcome': None  # Will be filled after 120 days
            }
            screen_entry['top_30'].append(entry)
        
        self.tracking_data['screens'].append(screen_entry)
        self.save_tracking_data()
        
        print(f"Added screening results from {screen_date}")
        print(f"Tracking {len(top_30)} stocks for next 120 days")
        
        return screen_entry
    
    def update_position_decision(self, screen_date, ticker, action, reason=None):
        """Update whether a stock was bought or rejected"""
        for screen in self.tracking_data['screens']:
            if screen['screen_date'] == screen_date:
                for stock in screen['top_30']:
                    if stock['ticker'] == ticker:
                        stock['status'] = action  # 'bought' or 'rejected'
                        stock['reason'] = reason
                        
                        if action == 'bought':
                            screen['positions_taken'].append(ticker)
                            self.tracking_data['positions'].append({
                                'ticker': ticker,
                                'entry_date': screen_date,
                                'entry_price': stock['start_price'],
                                'score': stock['score'],
                                'patterns': stock['patterns'],
                                'status': 'open'
                            })
                        else:
                            screen['positions_rejected'].append({
                                'ticker': ticker,
                                'reason': reason
                            })
                        
                        self.save_tracking_data()
                        print(f"Updated {ticker}: {action} - {reason}")
                        return
        
        print(f"Could not find {ticker} in screen from {screen_date}")
    
    def check_outcomes(self, current_date=None):
        """Check 120-day outcomes for all tracked stocks"""
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        current_dt = datetime.strptime(current_date, '%Y-%m-%d')
        
        print(f"\nChecking outcomes as of {current_date}")
        print("="*60)
        
        false_negatives = []
        true_positives = []
        false_positives = []
        
        for screen in self.tracking_data['screens']:
            screen_dt = datetime.strptime(screen['screen_date'], '%Y-%m-%d')
            
            # Only check screens older than 120 days
            if (current_dt - screen_dt).days >= 120:
                print(f"\nScreen from {screen['screen_date']}:")
                
                for stock in screen['top_30']:
                    if stock['outcome'] is None:  # Not yet checked
                        outcome = self.check_stock_performance(
                            stock['ticker'], 
                            stock['start_date'],
                            stock['start_price']
                        )
                        stock['outcome'] = outcome
                        
                        # Classify result
                        if outcome['exploded']:
                            if stock['status'] == 'bought':
                                true_positives.append(stock)
                                print(f"  ✓ {stock['ticker']}: TRUE POSITIVE - {outcome['max_gain']:.0f}% gain")
                            elif stock['status'] == 'rejected':
                                false_negatives.append(stock)
                                print(f"  ✗ {stock['ticker']}: FALSE NEGATIVE - Rejected but gained {outcome['max_gain']:.0f}%!")
                                print(f"    Reason for rejection: {stock['reason']}")
                        else:
                            if stock['status'] == 'bought':
                                false_positives.append(stock)
                                print(f"  ⚠ {stock['ticker']}: FALSE POSITIVE - Bought but only gained {outcome['max_gain']:.0f}%")
        
        # Update performance metrics
        self.tracking_data['performance']['true_positives'] = len(true_positives)
        self.tracking_data['performance']['false_positives'] = len(false_positives)
        self.tracking_data['performance']['false_negatives'] = len(false_negatives)
        
        self.save_tracking_data()
        
        # Print summary
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        print(f"True Positives: {len(true_positives)} (Bought and exploded)")
        print(f"False Negatives: {len(false_negatives)} (Rejected but exploded) ⚠️")
        print(f"False Positives: {len(false_positives)} (Bought but didn't explode)")
        
        if false_negatives:
            print("\n⚠️ FALSE NEGATIVES ANALYSIS:")
            print("These stocks were rejected but would have been winners:")
            for fn in false_negatives[:10]:  # Show top 10
                print(f"  {fn['ticker']}: Score {fn['score']}, Rejected for: {fn['reason']}")
                print(f"    Patterns: {', '.join(fn['patterns'][:3])}")
        
        return {
            'true_positives': true_positives,
            'false_negatives': false_negatives,
            'false_positives': false_positives
        }
    
    def check_stock_performance(self, ticker, start_date, start_price):
        """Check if stock exploded within 120 days"""
        try:
            stock = yf.Ticker(ticker)
            
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = start_dt + timedelta(days=120)
            
            # Get historical data
            df = stock.history(start=start_dt, end=end_dt)
            
            if len(df) == 0:
                return {'exploded': False, 'max_gain': 0, 'days_to_peak': None}
            
            # Calculate maximum gain
            max_price = df['Close'].max()
            max_gain = ((max_price - start_price) / start_price * 100) if start_price > 0 else 0
            
            # Find days to peak
            if max_gain > 0:
                peak_date = df['Close'].idxmax()
                days_to_peak = (peak_date - start_dt).days
            else:
                days_to_peak = None
            
            return {
                'exploded': max_gain >= 100,  # 100% gain threshold
                'max_gain': max_gain,
                'max_price': max_price,
                'days_to_peak': days_to_peak
            }
            
        except Exception as e:
            print(f"Error checking {ticker}: {e}")
            return {'exploded': False, 'max_gain': 0, 'days_to_peak': None}
    
    def get_pending_checks(self, current_date=None):
        """Get list of stocks pending 120-day outcome check"""
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        current_dt = datetime.strptime(current_date, '%Y-%m-%d')
        pending = []
        
        for screen in self.tracking_data['screens']:
            for stock in screen['top_30']:
                end_dt = datetime.strptime(stock['tracking_end_date'], '%Y-%m-%d')
                
                if stock['outcome'] is None and end_dt <= current_dt:
                    days_elapsed = (current_dt - datetime.strptime(stock['start_date'], '%Y-%m-%d')).days
                    pending.append({
                        'ticker': stock['ticker'],
                        'start_date': stock['start_date'],
                        'days_elapsed': days_elapsed,
                        'status': stock['status'],
                        'score': stock['score']
                    })
        
        return pending
    
    def generate_report(self):
        """Generate comprehensive tracking report"""
        report = {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_screens': len(self.tracking_data['screens']),
            'total_stocks_tracked': sum(len(s['top_30']) for s in self.tracking_data['screens']),
            'performance': self.tracking_data['performance'],
            'pattern_analysis': self.analyze_pattern_performance(),
            'rejection_analysis': self.analyze_rejection_reasons(),
            'recommendations': self.get_recommendations()
        }
        
        # Save report
        report_file = f"tracking_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to {report_file}")
        return report
    
    def analyze_pattern_performance(self):
        """Analyze which patterns led to success/failure"""
        pattern_stats = {}
        
        for screen in self.tracking_data['screens']:
            for stock in screen['top_30']:
                if stock['outcome']:
                    for pattern in stock['patterns']:
                        if pattern not in pattern_stats:
                            pattern_stats[pattern] = {
                                'total': 0,
                                'exploded': 0,
                                'in_rejected': 0,
                                'in_false_negatives': 0
                            }
                        
                        pattern_stats[pattern]['total'] += 1
                        
                        if stock['outcome']['exploded']:
                            pattern_stats[pattern]['exploded'] += 1
                            
                            if stock['status'] == 'rejected':
                                pattern_stats[pattern]['in_false_negatives'] += 1
                        
                        if stock['status'] == 'rejected':
                            pattern_stats[pattern]['in_rejected'] += 1
        
        # Calculate hit rates
        for pattern in pattern_stats:
            stats = pattern_stats[pattern]
            stats['hit_rate'] = stats['exploded'] / stats['total'] if stats['total'] > 0 else 0
            stats['false_neg_rate'] = stats['in_false_negatives'] / stats['in_rejected'] if stats['in_rejected'] > 0 else 0
        
        return pattern_stats
    
    def analyze_rejection_reasons(self):
        """Analyze why stocks were rejected"""
        rejection_reasons = {}
        false_neg_by_reason = {}
        
        for screen in self.tracking_data['screens']:
            for stock in screen['top_30']:
                if stock['status'] == 'rejected' and stock['reason']:
                    reason = stock['reason']
                    
                    if reason not in rejection_reasons:
                        rejection_reasons[reason] = 0
                        false_neg_by_reason[reason] = 0
                    
                    rejection_reasons[reason] += 1
                    
                    if stock['outcome'] and stock['outcome']['exploded']:
                        false_neg_by_reason[reason] += 1
        
        return {
            'total_rejections': rejection_reasons,
            'false_negatives_by_reason': false_neg_by_reason
        }
    
    def get_recommendations(self):
        """Get recommendations based on tracking data"""
        recommendations = []
        
        perf = self.tracking_data['performance']
        
        # Hit rate analysis
        if perf['true_positives'] + perf['false_positives'] > 0:
            hit_rate = perf['true_positives'] / (perf['true_positives'] + perf['false_positives'])
            
            if hit_rate < 0.4:
                recommendations.append("Hit rate below 40% - Consider tightening entry criteria")
            elif hit_rate > 0.7:
                recommendations.append("Hit rate above 70% - Consider taking more positions")
        
        # False negative analysis
        if perf['false_negatives'] > perf['true_positives']:
            recommendations.append("More false negatives than true positives - Review rejection criteria")
        
        # Pattern analysis
        pattern_perf = self.analyze_pattern_performance()
        for pattern, stats in pattern_perf.items():
            if stats.get('false_neg_rate', 0) > 0.5:
                recommendations.append(f"Pattern '{pattern}' has high false negative rate - Consider increasing weight")
        
        # Rejection reason analysis
        rejection_analysis = self.analyze_rejection_reasons()
        for reason, false_negs in rejection_analysis['false_negatives_by_reason'].items():
            if false_negs > 2:
                recommendations.append(f"Rejection reason '{reason}' caused {false_negs} false negatives - Review this criterion")
        
        return recommendations


def main():
    """Example usage of the tracking system"""
    tracker = GEMTracker()
    
    # Example: Add today's screening results
    example_results = [
        {
            'ticker': 'XYZ',
            'score': 95,
            'patterns': ['volume_3x', 'rsi_oversold', 'accumulation'],
            'recommendation': 'BUY',
            'price': 3.45
        },
        {
            'ticker': 'ABC',
            'score': 82,
            'patterns': ['volume_5x', 'market_outperform'],
            'recommendation': 'BUY',
            'price': 1.23
        },
        # Add more results...
    ]
    
    # Add screening results
    today = datetime.now().strftime('%Y-%m-%d')
    # tracker.add_screening_results(today, example_results)
    
    # Update position decisions
    # tracker.update_position_decision(today, 'XYZ', 'bought', 'Strong signal alignment')
    # tracker.update_position_decision(today, 'ABC', 'rejected', 'Too many red flags')
    
    # Check outcomes (for screens 120+ days old)
    outcomes = tracker.check_outcomes()
    
    # Get pending checks
    pending = tracker.get_pending_checks()
    if pending:
        print(f"\n{len(pending)} stocks pending outcome check")
    
    # Generate report
    report = tracker.generate_report()
    
    print("\n" + "="*60)
    print("CRITICAL TRACKING REMINDERS:")
    print("="*60)
    print("1. Add ALL screening results immediately after running")
    print("2. Update buy/reject decisions for EACH stock in top 30")
    print("3. Run outcome checks after 120 days")
    print("4. Review false negatives monthly")
    print("5. Adjust weights based on pattern performance")
    
    return tracker


if __name__ == "__main__":
    tracker = main()
