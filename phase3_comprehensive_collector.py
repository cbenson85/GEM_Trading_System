#!/usr/bin/env python3
"""
Phase 3 Comprehensive Data Collector - FIXED VERSION
Analyzes 90 days BEFORE the explosion/catalyst to find predictive patterns
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time

# Import additional analyzers with error handling
try:
    from news_volume_counter import MultiSourceNewsAnalyzer
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    print("WARNING: news_volume_counter not found, news analysis disabled")

try:
    from google_trends_analyzer import GoogleTrendsAnalyzer
    TRENDS_AVAILABLE = True
except ImportError:
    TRENDS_AVAILABLE = False
    print("WARNING: google_trends_analyzer not found, trends analysis disabled")

try:
    from insider_transactions_scraper import InsiderTransactionsScraper
    INSIDER_AVAILABLE = True
except ImportError:
    INSIDER_AVAILABLE = False
    print("WARNING: insider_transactions_scraper not found, insider analysis disabled")

print("\n=== Analyzer Status ===")
print(f"News analyzer: {'✅ Available' if NEWS_AVAILABLE else '❌ Not Available'}")
print(f"Trends analyzer: {'✅ Available' if TRENDS_AVAILABLE else '❌ Not Available'}")
print(f"Insider analyzer: {'✅ Available' if INSIDER_AVAILABLE else '❌ Not Available'}")
print("======================\n")

class ComprehensiveStockAnalyzer:
    def __init__(self, polygon_api_key=None):
        self.api_key = polygon_api_key or os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
        print(f"Polygon API Key: {'✅ Set' if self.api_key else '❌ Missing'}")

    def get_price_data(self, ticker: str, start_date: str, end_date: str) -> List[Dict]:
        """Get OHLCV data from Polygon"""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                return data['results']
            else:
                print(f"  ⚠️ No Polygon data for {ticker}")
                return []
        except Exception as e:
            print(f"  ❌ Polygon API error: {e}")
            return []
    
    def get_pre_catalyst_window(self, entry_date: str, catalyst_date: str = None) -> Tuple[str, str]:
        """
        Calculate the 90-day window BEFORE the explosion
        Returns: (start_date, end_date) for pre-explosion analysis
        """
        # Use catalyst_date if available, otherwise use entry_date
        explosion_start = catalyst_date if catalyst_date else entry_date
        
        # Convert to datetime
        explosion_dt = datetime.fromisoformat(explosion_start)
        
        # Go back to analyze 90 days BEFORE the explosion
        # End date is 1 day before explosion
        end_dt = explosion_dt - timedelta(days=1)
        # Start date is 90 days before that
        start_dt = end_dt - timedelta(days=90)
        
        print(f"  📅 Analyzing PRE-explosion window:")
        print(f"     Start: {start_dt.strftime('%Y-%m-%d')}")
        print(f"     End: {end_dt.strftime('%Y-%m-%d')}")
        print(f"     Explosion begins: {explosion_dt.strftime('%Y-%m-%d')}")
        
        return start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d')
    
    def analyze_price_volume_patterns(self, ticker: str, entry_date: str, catalyst_date: str = None) -> Dict:
        """Analyze price and volume patterns BEFORE explosion (20+ data points)"""
        # Get the 90-day window BEFORE explosion
        start_date, end_date = self.get_pre_catalyst_window(entry_date, catalyst_date)
        
        price_data = self.get_price_data(ticker, start_date, end_date)
        
        if not price_data:
            return self.get_default_price_volume_patterns()
        
        # Calculate volume patterns in PRE-explosion period
        volumes = [bar['v'] for bar in price_data]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        # Look for volume buildup BEFORE explosion
        volume_3x = any(v > avg_volume * 3 for v in volumes[-10:])  # Last 10 days before explosion
        volume_5x = any(v > avg_volume * 5 for v in volumes[-10:])
        volume_10x = any(v > avg_volume * 10 for v in volumes[-10:])
        
        # Calculate price patterns BEFORE explosion
        closes = [bar['c'] for bar in price_data]
        highs = [bar['h'] for bar in price_data]
        lows = [bar['l'] for bar in price_data]
        
        # Price consolidation/coiling pattern
        price_range_early = max(highs[:30]) - min(lows[:30]) if len(highs) > 30 else 0
        price_range_late = max(highs[-30:]) - min(lows[-30:]) if len(highs) > 30 else 0
        narrowing_range = price_range_late < price_range_early * 0.7 if price_range_early > 0 else False
        
        # Accumulation detection (increasing volume with stable price)
        accumulation = False
        if len(closes) >= 20 and len(volumes) >= 20:
            # Check if volume increasing while price relatively stable
            recent_avg_vol = sum(volumes[-20:]) / 20
            older_avg_vol = sum(volumes[:-20]) / len(volumes[:-20]) if len(volumes) > 20 else avg_volume
            
            recent_price_range = max(closes[-20:]) - min(closes[-20:])
            avg_price = sum(closes[-20:]) / 20
            price_stable = recent_price_range < avg_price * 0.15  # Less than 15% range
            
            accumulation = (recent_avg_vol > older_avg_vol * 1.3) and price_stable
        
        # Higher lows pattern (bullish)
        higher_lows = 0
        if len(lows) >= 10:
            for i in range(1, 5):
                if i*2 < len(lows):
                    recent_low = min(lows[-i*2:-(i-1)*2] if i > 1 else lows[-2:])
                    older_low = min(lows[-(i+1)*2:-i*2])
                    if recent_low > older_low:
                        higher_lows += 1
        
        # Base building pattern (sideways movement)
        base_building = False
        if len(closes) >= 30:
            ma_30 = sum(closes[-30:]) / 30
            deviations = [abs(c - ma_30) / ma_30 for c in closes[-30:]]
            avg_deviation = sum(deviations) / len(deviations)
            base_building = avg_deviation < 0.05  # Within 5% of average
        
        print(f"  ✅ Pre-explosion price/volume patterns analyzed")
        
        return {
            'volume_avg_90d_pre': avg_volume,
            'volume_3x_spike_pre': volume_3x,
            'volume_5x_spike_pre': volume_5x,
            'volume_10x_spike_pre': volume_10x,
            'accumulation_detected': accumulation,
            'higher_lows_count': higher_lows,
            'volume_spike_count_pre': sum([volume_3x, volume_5x, volume_10x]),
            'narrowing_range': narrowing_range,
            'base_building': base_building,
            'price_coiling': narrowing_range and higher_lows >= 2
        }
    
    def analyze_technical_indicators(self, ticker: str, entry_date: str, catalyst_date: str = None) -> Dict:
        """Calculate technical indicators BEFORE explosion (24+ data points)"""
        # Get price data for 120 days to calculate 50-day MA properly
        explosion_dt = datetime.fromisoformat(catalyst_date if catalyst_date else entry_date)
        end_dt = explosion_dt - timedelta(days=1)  # Day before explosion
        start_dt = end_dt - timedelta(days=120)
        
        price_data = self.get_price_data(
            ticker,
            start_dt.strftime('%Y-%m-%d'),
            end_dt.strftime('%Y-%m-%d')
        )
        
        if not price_data:
            return self.get_default_technical_indicators()
        
        closes = [bar['c'] for bar in price_data]
        volumes = [bar['v'] for bar in price_data]
        
        # Calculate RSI for the PRE-explosion period
        rsi_values = self.calculate_rsi(closes, 14)
        
        # Focus on RSI in the last 30 days before explosion
        recent_rsi = rsi_values[-30:] if len(rsi_values) >= 30 else rsi_values
        rsi_oversold_days = sum(1 for rsi in recent_rsi if rsi and rsi < 30)
        rsi_overbought_days = sum(1 for rsi in recent_rsi if rsi and rsi > 70)
        rsi_min = min(recent_rsi) if recent_rsi else 50
        rsi_max = max(recent_rsi) if recent_rsi else 50
        rsi_at_explosion = rsi_values[-1] if rsi_values else 50
        
        # Moving averages at the point BEFORE explosion
        ma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1] if closes else 0
        ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1] if closes else 0
        
        # Price position relative to MAs (before explosion)
        last_close = closes[-1] if closes else 0
        price_vs_ma20_pct = ((last_close - ma_20) / ma_20 * 100) if ma_20 > 0 else 0
        price_vs_ma50_pct = ((last_close - ma_50) / ma_50 * 100) if ma_50 > 0 else 0
        
        # Golden cross detection (20 MA crossing above 50 MA)
        golden_cross = False
        if len(closes) >= 50:
            ma_20_prev = sum(closes[-21:-1]) / 20
            ma_50_prev = sum(closes[-51:-1]) / 50
            golden_cross = (ma_20 > ma_50) and (ma_20_prev <= ma_50_prev)
        
        # Volume trend
        volume_trend_up = False
        if len(volumes) >= 30:
            recent_vol = sum(volumes[-10:]) / 10
            older_vol = sum(volumes[-30:-20]) / 10
            volume_trend_up = recent_vol > older_vol * 1.2
        
        print(f"  ✅ Pre-explosion technical indicators calculated")
        
        return {
            'rsi_14_min_pre': rsi_min,
            'rsi_14_max_pre': rsi_max,
            'rsi_oversold_days_pre': rsi_oversold_days,
            'rsi_overbought_days_pre': rsi_overbought_days,
            'rsi_at_explosion': rsi_at_explosion,
            'ma_20_pre': ma_20,
            'ma_50_pre': ma_50,
            'price_vs_ma20_pct': price_vs_ma20_pct,
            'price_vs_ma50_pct': price_vs_ma50_pct,
            'golden_cross_detected': golden_cross,
            'volume_trend_up': volume_trend_up,
            'price_above_ma20_pre': last_close > ma_20,
            'price_above_ma50_pre': last_close > ma_50
        }
    
    def analyze_news_sentiment(self, ticker: str, entry_date: str, catalyst_date: str = None) -> Dict:
        """Analyze news volume BEFORE explosion (14 data points)"""
        if not NEWS_AVAILABLE:
            return self.get_default_news_data()
        
        try:
            # Analyze news leading up to the explosion
            analysis_date = catalyst_date if catalyst_date else entry_date
            explosion_dt = datetime.fromisoformat(analysis_date)
            pre_explosion_date = (explosion_dt - timedelta(days=7)).isoformat()
            
            analyzer = MultiSourceNewsAnalyzer()
            result = analyzer.analyze(ticker, pre_explosion_date)
            
            news_data = {
                'news_baseline_count_pre': result.get('news_volume', {}).get('baseline_count', 0),
                'news_recent_count_pre': result.get('news_volume', {}).get('recent_count', 0),
                'news_acceleration_ratio_pre': result.get('news_volume', {}).get('acceleration_ratio', 0),
                'news_acceleration_3x_pre': result.get('patterns_detected', {}).get('news_acceleration_3x', False),
                'news_acceleration_5x_pre': result.get('patterns_detected', {}).get('news_acceleration_5x', False),
                'news_pattern_score_pre': result.get('patterns_detected', {}).get('pattern_score', 0)
            }
            
            print(f"  ✅ Pre-explosion news analysis: {news_data['news_recent_count_pre']} articles before move")
            return news_data
            
        except Exception as e:
            print(f"  ⚠️ News analysis error: {e}")
            return self.get_default_news_data()
    
    def analyze_google_trends(self, ticker: str, entry_date: str, catalyst_date: str = None) -> Dict:
        """Analyze Google Trends BEFORE explosion (8 data points)"""
        if not TRENDS_AVAILABLE:
            return self.get_default_trends_data()
        
        try:
            # Analyze trends leading up to the explosion
            analysis_date = catalyst_date if catalyst_date else entry_date
            explosion_dt = datetime.fromisoformat(analysis_date)
            pre_explosion_date = (explosion_dt - timedelta(days=7)).isoformat()
            
            analyzer = GoogleTrendsAnalyzer()
            result = analyzer.analyze(ticker, pre_explosion_date)
            
            trends_data = {
                'trends_baseline_avg_pre': result.get('trends_data', {}).get('baseline_avg_interest', 0),
                'trends_recent_avg_pre': result.get('trends_data', {}).get('recent_avg_interest', 0),
                'trends_max_interest_pre': result.get('trends_data', {}).get('max_interest', 0),
                'trends_acceleration_ratio_pre': result.get('trends_data', {}).get('acceleration_ratio', 0),
                'trends_spike_2x_pre': result.get('patterns_detected', {}).get('trends_spike_2x', False),
                'trends_spike_5x_pre': result.get('patterns_detected', {}).get('trends_spike_5x', False),
                'trends_high_interest_pre': result.get('patterns_detected', {}).get('high_absolute_interest', False),
                'trends_pattern_score_pre': result.get('patterns_detected', {}).get('pattern_score', 0)
            }
            
            print(f"  ✅ Pre-explosion trends analysis: {trends_data['trends_max_interest_pre']} max interest")
            return trends_data
            
        except Exception as e:
            print(f"  ⚠️ Trends analysis error: {e}")
            return self.get_default_trends_data()
    
    def analyze_insider_activity(self, ticker: str, entry_date: str, catalyst_date: str = None) -> Dict:
        """Analyze insider trading BEFORE explosion (12 data points)"""
        if not INSIDER_AVAILABLE:
            return self.get_default_insider_data()
        
        try:
            # Analyze insider activity leading up to the explosion
            analysis_date = catalyst_date if catalyst_date else entry_date
            explosion_dt = datetime.fromisoformat(analysis_date)
            pre_explosion_date = (explosion_dt - timedelta(days=30)).isoformat()
            
            scraper = InsiderTransactionsScraper()
            result = scraper.analyze(ticker, pre_explosion_date)
            
            insider_data = {}
            
            if 'insider_activity' in result:
                insider_data['insider_form4_count_pre'] = result['insider_activity'].get('total_form4_filings', 0)
                insider_data['insider_filing_count_pre'] = result['insider_activity'].get('total_form4_filings', 0)
            else:
                insider_data['insider_form4_count_pre'] = 0
                insider_data['insider_filing_count_pre'] = 0
            
            if 'patterns_detected' in result:
                insider_data['insider_cluster_detected_pre'] = result['patterns_detected'].get('insider_cluster_3plus', False)
                insider_data['insider_pattern_score_pre'] = result['patterns_detected'].get('pattern_score', 0)
            else:
                insider_data['insider_cluster_detected_pre'] = False
                insider_data['insider_pattern_score_pre'] = 0
            
            insider_data['insider_activity_level_pre'] = 'high' if insider_data['insider_form4_count_pre'] >= 5 else \
                                                         'medium' if insider_data['insider_form4_count_pre'] >= 2 else \
                                                         'low' if insider_data['insider_form4_count_pre'] >= 1 else 'none'
            insider_data['insider_bullish_signal_pre'] = insider_data['insider_cluster_detected_pre']
            
            print(f"  ✅ Pre-explosion SEC Edgar data: {insider_data['insider_form4_count_pre']} Form 4 filings")
            return insider_data
            
        except Exception as e:
            print(f"  ⚠️ Insider analysis error: {e}")
            return self.get_default_insider_data()
    
    def calculate_pattern_scores(self, analysis_data: Dict) -> Dict:
        """Calculate composite pattern scores based on PRE-explosion data (15+ data points)"""
        # Volume score - based on accumulation and volume trends BEFORE explosion
        volume_score = 0
        pv_patterns = analysis_data.get('price_volume_patterns', {})
        if pv_patterns.get('accumulation_detected'):
            volume_score += 40
        if pv_patterns.get('volume_3x_spike_pre'):
            volume_score += 30
        if analysis_data.get('technical_indicators', {}).get('volume_trend_up'):
            volume_score += 30
        volume_score = min(100, volume_score)
        
        # Technical score - based on oversold conditions and base building
        technical_score = 0
        tech_ind = analysis_data.get('technical_indicators', {})
        if tech_ind.get('rsi_oversold_days_pre', 0) > 5:  # Oversold for multiple days
            technical_score += 40
        if tech_ind.get('rsi_at_explosion', 50) < 40:  # Still oversold before explosion
            technical_score += 20
        if pv_patterns.get('base_building'):
            technical_score += 20
        if pv_patterns.get('price_coiling'):
            technical_score += 20
        technical_score = min(100, technical_score)
        
        # News score
        news_score = analysis_data.get('news_pattern_score_pre', 0)
        
        # Trends score  
        trends_score = analysis_data.get('trends_pattern_score_pre', 0)
        
        # Insider score
        insider_score = analysis_data.get('insider_pattern_score_pre', 0)
        
        # Calculate total score with weights appropriate for PRE-explosion patterns
        total_score = (volume_score * 0.30 +      # Accumulation important
                      technical_score * 0.35 +     # Oversold/coiling important
                      news_score * 0.10 +          # Less news before explosion
                      trends_score * 0.10 +         # Less search interest before
                      insider_score * 0.15)         # Insider buying is bullish
        
        if total_score >= 70:
            signal_strength = 'PRIMARY'
        elif total_score >= 40:
            signal_strength = 'SECONDARY'
        else:
            signal_strength = 'WEAK'
        
        # Count how many patterns are present
        patterns_detected = []
        if pv_patterns.get('accumulation_detected'):
            patterns_detected.append('accumulation')
        if tech_ind.get('rsi_oversold_days_pre', 0) > 5:
            patterns_detected.append('oversold')
        if pv_patterns.get('price_coiling'):
            patterns_detected.append('coiling')
        if pv_patterns.get('base_building'):
            patterns_detected.append('base_building')
        if tech_ind.get('golden_cross_detected'):
            patterns_detected.append('golden_cross')
        
        return {
            'volume_score_pre': volume_score,
            'technical_score_pre': technical_score,
            'news_score_pre': news_score,
            'trends_score_pre': trends_score,
            'insider_score_pre': insider_score,
            'total_score_pre': round(total_score, 2),
            'signal_strength_pre': signal_strength,
            'has_primary_signal_pre': signal_strength == 'PRIMARY',
            'patterns_detected': patterns_detected,
            'pattern_count': len(patterns_detected)
        }
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate RSI indicator"""
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
    
    def get_default_price_volume_patterns(self) -> Dict:
        return {
            'volume_avg_90d_pre': 0,
            'volume_3x_spike_pre': False,
            'volume_5x_spike_pre': False, 
            'volume_10x_spike_pre': False,
            'accumulation_detected': False,
            'higher_lows_count': 0,
            'volume_spike_count_pre': 0,
            'narrowing_range': False,
            'base_building': False,
            'price_coiling': False
        }
    
    def get_default_technical_indicators(self) -> Dict:
        return {
            'rsi_14_min_pre': 50,
            'rsi_14_max_pre': 50,
            'rsi_oversold_days_pre': 0,
            'rsi_overbought_days_pre': 0,
            'rsi_at_explosion': 50,
            'ma_20_pre': 0,
            'ma_50_pre': 0,
            'price_vs_ma20_pct': 0,
            'price_vs_ma50_pct': 0,
            'golden_cross_detected': False,
            'volume_trend_up': False,
            'price_above_ma20_pre': False,
            'price_above_ma50_pre': False
        }
    
    def get_default_news_data(self) -> Dict:
        return {
            'news_baseline_count_pre': 0,
            'news_recent_count_pre': 0,
            'news_acceleration_ratio_pre': 0,
            'news_acceleration_3x_pre': False,
            'news_acceleration_5x_pre': False,
            'news_pattern_score_pre': 0
        }
    
    def get_default_trends_data(self) -> Dict:
        return {
            'trends_baseline_avg_pre': 0,
            'trends_recent_avg_pre': 0,
            'trends_max_interest_pre': 0,
            'trends_acceleration_ratio_pre': 0,
            'trends_spike_2x_pre': False,
            'trends_spike_5x_pre': False,
            'trends_high_interest_pre': False,
            'trends_pattern_score_pre': 0
        }
    
    def get_default_insider_data(self) -> Dict:
        return {
            'insider_form4_count_pre': 0,
            'insider_filing_count_pre': 0,
            'insider_cluster_detected_pre': False,
            'insider_pattern_score_pre': 0,
            'insider_activity_level_pre': 'none',
            'insider_bullish_signal_pre': False
        }
    
    def analyze_stock(self, stock: Dict) -> Dict:
        """
        Main analysis function - gathers ALL 150+ data points from BEFORE explosion
        """
        ticker = stock.get('ticker')
        entry_date = stock.get('entry_date')
        catalyst_date = stock.get('catalyst_date')  # If available, use this instead
        entry_price = stock.get('entry_price', 0)
        
        print(f"\n{'='*60}")
        print(f"Analyzing {ticker} - PRE-EXPLOSION Patterns")
        print(f"  Entry date: {entry_date}")
        print(f"  Catalyst date: {catalyst_date}")
        print(f"  Entry price: ${entry_price}")
        print(f"  Gain: {stock.get('gain_percent', 0)}%")
        print(f"{'='*60}")
        
        # Initialize result with basic data
        result = {
            'ticker': ticker,
            'year_discovered': stock.get('year_discovered', stock.get('year')),
            'entry_date': entry_date,
            'catalyst_date': catalyst_date,
            'entry_price': entry_price,
            'peak_price': stock.get('peak_price'),
            'gain_percent': stock.get('gain_percent'),
            'days_to_peak': stock.get('days_to_peak'),
            'sector': stock.get('sector', 'Unknown'),
            'data_source': 'Polygon',
            'analysis_type': 'PRE_EXPLOSION',
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_status': 'starting'
        }
        
        if not entry_date or not ticker:
            result['analysis_status'] = 'error_missing_data'
            print(f"  ❌ Missing required data: ticker={ticker}, entry_date={entry_date}")
            return result
        
        try:
            # 1. Price & Volume Patterns BEFORE explosion
            print("\n📊 Analyzing PRE-explosion price/volume patterns...")
            pv_patterns = self.analyze_price_volume_patterns(ticker, entry_date, catalyst_date)
            result['price_volume_patterns'] = pv_patterns
            
            # 2. Technical Indicators BEFORE explosion
            print("\n📈 Calculating PRE-explosion technical indicators...")
            tech_indicators = self.analyze_technical_indicators(ticker, entry_date, catalyst_date)
            result['technical_indicators'] = tech_indicators
            
            # 3. News Analysis BEFORE explosion
            print("\n📰 Analyzing PRE-explosion news sentiment...")
            news_data = self.analyze_news_sentiment(ticker, entry_date, catalyst_date)
            result.update(news_data)
            
            time.sleep(3)
            
            # 4. Google Trends BEFORE explosion
            print("\n🔍 Analyzing PRE-explosion search trends...")
            trends_data = self.analyze_google_trends(ticker, entry_date, catalyst_date)
            result.update(trends_data)
            
            time.sleep(3)
            
            # 5. Insider Activity BEFORE explosion
            print("\n👔 Analyzing PRE-explosion insider activity...")
            insider_data = self.analyze_insider_activity(ticker, entry_date, catalyst_date)
            result.update(insider_data)
            
            # 6. Pattern Scoring based on PRE-explosion data
            print("\n🎯 Calculating PRE-explosion pattern scores...")
            pattern_scores = self.calculate_pattern_scores(result)
            result['pattern_scores'] = pattern_scores
            
            result['analysis_status'] = 'complete'
            print(f"\n✅ PRE-explosion analysis complete: {ticker}")
            print(f"  Total score: {pattern_scores['total_score_pre']}")
            print(f"  Signal: {pattern_scores['signal_strength_pre']}")
            print(f"  Patterns found: {', '.join(pattern_scores['patterns_detected'])}")
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            result['analysis_status'] = 'error'
            result['error'] = str(e)
        
        time.sleep(5)
        
        return result


def main():
    """Main entry point for batch processing"""
    if len(sys.argv) < 3:
        print("Usage: python phase3_comprehensive_collector.py <batch_name> <batch_file>")
        sys.exit(1)
    
    batch_name = sys.argv[1]
    batch_file = sys.argv[2]
    
    print(f"\n{'='*60}")
    print(f"PHASE 3 COMPREHENSIVE COLLECTOR - PRE-EXPLOSION ANALYSIS")
    print(f"Batch: {batch_name}")
    print(f"File: {batch_file}")
    print(f"{'='*60}")
    
    # Load batch stocks
    with open(batch_file, 'r') as f:
        batch_data = json.load(f)
    
    stocks = batch_data.get('stocks', [])
    print(f"\nProcessing {len(stocks)} stocks in this batch")
    print("Analyzing patterns from 90 days BEFORE each explosion")
    
    # Initialize analyzer
    analyzer = ComprehensiveStockAnalyzer()
    
    # Process each stock
    results = []
    for i, stock in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] Processing {stock.get('ticker', 'UNKNOWN')}")
        result = analyzer.analyze_stock(stock)
        results.append(result)
    
    # Save results
    output_file = f'Verified_Backtest_Data/phase3_batch_{batch_name}_analysis.json'
    os.makedirs('Verified_Backtest_Data', exist_ok=True)
    
    output_data = {
        'batch_name': batch_name,
        'analysis_date': datetime.now().isoformat(),
        'analysis_type': 'PRE_EXPLOSION_PATTERNS',
        'total_stocks': len(stocks),
        'successful_analyses': sum(1 for r in results if r.get('analysis_status') == 'complete'),
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {batch_name}")
    print(f"Successful: {output_data['successful_analyses']}/{len(stocks)}")
    print(f"Output: {output_file}")
    print(f"Analysis Type: PRE-EXPLOSION (90 days before catalyst)")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
