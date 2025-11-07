#!/usr/bin/env python3
"""
Phase 4 Comprehensive Data Collector - Adapted from Phase 3
Collects 150+ data points AND tracks forward performance
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta
import time

class Phase4StockAnalyzer:
    def __init__(self):
        self.api_key = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
        
    def get_price_data(self, ticker: str, start_date: str, end_date: str):
        """Get historical price data from Polygon"""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                return data['results']
            return []
        except Exception as e:
            print(f"  ❌ Polygon API error: {e}")
            return []
    
    def analyze_lookback_period(self, ticker: str, screening_date: str):
        """Analyze 60 days before screening date"""
        end_dt = datetime.fromisoformat(screening_date)
        start_dt = end_dt - timedelta(days=60)
        
        price_data = self.get_price_data(
            ticker,
            start_dt.strftime('%Y-%m-%d'),
            end_dt.strftime('%Y-%m-%d')
        )
        
        if not price_data:
            return {'data_available': False}
        
        # Find lowest price in lookback period
        lowest_price = min([bar['l'] for bar in price_data])
        highest_price = max([bar['h'] for bar in price_data])
        
        # Check if patterns were forming
        volumes = [bar['v'] for bar in price_data]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        # Count volume spikes
        volume_spikes = sum(1 for v in volumes if v > avg_volume * 3)
        
        return {
            'data_available': True,
            'lowest_price_60d': lowest_price,
            'highest_price_60d': highest_price,
            'avg_volume_60d': avg_volume,
            'volume_spike_days': volume_spikes,
            'price_range': highest_price - lowest_price
        }
    
    def analyze_forward_performance(self, ticker: str, screening_date: str, entry_price: float):
        """Track performance for 120 days after screening"""
        start_dt = datetime.fromisoformat(screening_date)
        end_dt = start_dt + timedelta(days=120)
        
        price_data = self.get_price_data(
            ticker,
            start_dt.strftime('%Y-%m-%d'),
            end_dt.strftime('%Y-%m-%d')
        )
        
        if not price_data:
            return {
                'data_available': False,
                'classification': 'NO_DATA'
            }
        
        # Find maximum gain
        max_price = max([bar['h'] for bar in price_data])
        min_price = min([bar['l'] for bar in price_data])
        
        max_gain_pct = ((max_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        max_loss_pct = ((min_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # Find days to peak
        days_to_peak = 0
        for i, bar in enumerate(price_data):
            if bar['h'] == max_price:
                days_to_peak = i + 1
                break
        
        # Classify the outcome
        if max_gain_pct >= 500:
            classification = 'TRUE_POSITIVE'
        elif max_gain_pct >= 100:
            classification = 'MODERATE_WIN'
        elif max_gain_pct >= 50:
            classification = 'SMALL_WIN'
        elif max_gain_pct >= 0:
            classification = 'BREAK_EVEN'
        else:
            classification = 'LOSS'
        
        return {
            'data_available': True,
            'max_gain_percent': round(max_gain_pct, 2),
            'max_loss_percent': round(max_loss_pct, 2),
            'max_price_reached': max_price,
            'min_price_reached': min_price,
            'days_to_peak': days_to_peak,
            'classification': classification,
            'is_explosive': max_gain_pct >= 500
        }
    
    def calculate_technical_indicators(self, ticker: str, screening_date: str):
        """Calculate RSI, moving averages, etc."""
        end_dt = datetime.fromisoformat(screening_date)
        start_dt = end_dt - timedelta(days=100)
        
        price_data = self.get_price_data(
            ticker,
            start_dt.strftime('%Y-%m-%d'),
            end_dt.strftime('%Y-%m-%d')
        )
        
        if not price_data:
            return self.get_default_technical_indicators()
        
        closes = [bar['c'] for bar in price_data]
        
        # Calculate RSI
        rsi_values = self.calculate_rsi(closes)
        rsi_current = rsi_values[-1] if rsi_values else 50
        
        # Moving averages
        ma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1] if closes else 0
        ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1] if closes else 0
        
        return {
            'rsi_14': rsi_current,
            'ma_20': ma_20,
            'ma_50': ma_50,
            'price_vs_ma20': ((closes[-1] - ma_20) / ma_20 * 100) if ma_20 > 0 else 0,
            'price_vs_ma50': ((closes[-1] - ma_50) / ma_50 * 100) if ma_50 > 0 else 0
        }
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return []
        
        rsi_values = []
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        for i in range(period, len(gains) + 1):
            avg_gain = sum(gains[i-period:i]) / period
            avg_loss = sum(losses[i-period:i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    def get_default_technical_indicators(self):
        return {
            'rsi_14': 50,
            'ma_20': 0,
            'ma_50': 0,
            'price_vs_ma20': 0,
            'price_vs_ma50': 0
        }
    
    def analyze_stock(self, stock: dict):
        """Main analysis function for Phase 4"""
        ticker = stock.get('ticker')
        screening_date = stock.get('screening_date')
        entry_price = stock.get('entry_price', 0)
        score = stock.get('score', 0)
        rank = stock.get('rank', 0)
        
        print(f"\n{'='*60}")
        print(f"Analyzing {ticker}")
        print(f"  Screening date: {screening_date}")
        print(f"  Entry price: ${entry_price:.2f}")
        print(f"  Score: {score} (Rank #{rank})")
        print(f"{'='*60}")
        
        result = {
            'ticker': ticker,
            'screening_date': screening_date,
            'entry_price': entry_price,
            'screening_score': score,
            'screening_rank': rank,
            'score_breakdown': stock.get('score_breakdown', {}),
            'false_miss_analysis': stock.get('false_miss_analysis', {}),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # 1. Lookback analysis (-60 days)
            print("  📊 Analyzing lookback period...")
            lookback = self.analyze_lookback_period(ticker, screening_date)
            result['lookback_analysis'] = lookback
            
            # 2. Technical indicators at screening date
            print("  📈 Calculating technical indicators...")
            technicals = self.calculate_technical_indicators(ticker, screening_date)
            result['technical_indicators'] = technicals
            
            # 3. Forward performance (+120 days)
            print("  🚀 Tracking forward performance...")
            forward = self.analyze_forward_performance(ticker, screening_date, entry_price)
            result['forward_performance'] = forward
            
            # 4. Overall classification
            result['final_classification'] = forward.get('classification', 'NO_DATA')
            result['is_success'] = forward.get('is_explosive', False)
            
            print(f"\n  ✅ Analysis complete:")
            print(f"    Max gain: {forward.get('max_gain_percent', 0):.1f}%")
            print(f"    Classification: {result['final_classification']}")
            
        except Exception as e:
            print(f"  ❌ Analysis error: {e}")
            result['error'] = str(e)
            result['final_classification'] = 'ERROR'
        
        time.sleep(2)  # Rate limiting
        
        return result

def main():
    """Process a batch of stocks"""
    if len(sys.argv) < 3:
        print("Usage: python phase4_comprehensive_collector.py <batch_name> <batch_file>")
        sys.exit(1)
    
    batch_name = sys.argv[1]
    batch_file = sys.argv[2]
    
    print(f"\n{'='*60}")
    print(f"PHASE 4 COMPREHENSIVE COLLECTOR")
    print(f"Batch: {batch_name}")
    print(f"File: {batch_file}")
    print(f"{'='*60}")
    
    # Load batch
    with open(batch_file, 'r') as f:
        batch_data = json.load(f)
    
    stocks = batch_data.get('stocks', [])
    print(f"\nProcessing {len(stocks)} stocks")
    
    # Initialize analyzer
    analyzer = Phase4StockAnalyzer()
    
    # Process each stock
    results = []
    for i, stock in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] Processing {stock.get('ticker', 'UNKNOWN')}")
        result = analyzer.analyze_stock(stock)
        results.append(result)
    
    # Save results
    output_dir = 'Verified_Backtest_Data'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/phase4_batch_{batch_name}_analysis.json'
    
    output_data = {
        'batch_name': batch_name,
        'analysis_date': datetime.now().isoformat(),
        'total_stocks': len(stocks),
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Summary
    true_positives = sum(1 for r in results if r.get('final_classification') == 'TRUE_POSITIVE')
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {batch_name}")
    print(f"True Positives: {true_positives}/{len(stocks)}")
    print(f"Output: {output_file}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
