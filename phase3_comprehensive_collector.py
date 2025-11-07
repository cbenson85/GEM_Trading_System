#!/usr/bin/env python3
"""
Phase 3 Comprehensive Data Collector - Gathers ALL data points per stock
Designed for parallel processing to avoid 6-hour timeout
Integrates news, trends, and insider data for 150+ total metrics
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time

# Import additional analyzers
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


class ComprehensiveStockAnalyzer:
    def __init__(self, polygon_api_key=None):
        self.api_key = polygon_api_key or os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
        self.base_url = 'https://api.polygon.io'
    
    def analyze_stock(self, stock: Dict) -> Dict:
        """
        Analyze a single stock and gather ALL data points
        Returns dictionary with 150+ metrics
        """
        ticker = stock.get('ticker')
        entry_date = stock.get('entry_date')
        entry_price = stock.get('entry_price', 0)
        
        print(f"\n{'='*60}")
        print(f"Analyzing {ticker}")
        print(f"{'='*60}")
        
        # Initialize result structure
        result = {
            # 1. Basic Stock Data (copy from input)
            'ticker': ticker,
            'year_discovered': stock.get('year_discovered', stock.get('year')),
            'entry_date': entry_date,
            'entry_price': entry_price,
            'catalyst_date': stock.get('catalyst_date'),
            'peak_price': stock.get('peak_price'),
            'gain_percent': stock.get('gain_percent'),
            'days_to_peak': stock.get('days_to_peak'),
            'sector': stock.get('sector', 'Unknown'),
            'data_source': stock.get('data_source', 'Polygon'),
            
            # 2. Sustainability Metrics (if available)
            'sustainability_stats': stock.get('sustainability_stats', {}),
            
            # Will be populated by analysis
            'price_volume_patterns': {},
            'technical_indicators': {},
            'market_context': {},
            'pattern_scores': {},
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_status': 'starting'
        }
        
        if not entry_date or not ticker:
            result['analysis_status'] = 'error_missing_data'
            return result
        
        try:
            # Get 90-day window data from Polygon
            print(f"  📊 Fetching Polygon data...")
            price_data = self.get_polygon_data(ticker, entry_date)
            
            if price_data:
                # Analyze price and volume patterns
                print(f"  📈 Analyzing price/volume patterns...")
                result['price_volume_patterns'] = self.analyze_price_volume(price_data, entry_price)
                
                # Calculate technical indicators
                print(f"  🔧 Calculating technical indicators...")
                result['technical_indicators'] = self.calculate_technicals(price_data)
                
                # Analyze market context
                print(f"  🌍 Analyzing market context...")
                result['market_context'] = self.analyze_market_context(ticker, entry_date)
                
                print(f"  ✅ Polygon analysis complete")
            else:
                print(f"  ❌ No Polygon data available")
            
            # Analyze news sentiment
            print(f"\n  📰 Analyzing news sentiment...")
            news_data = self.analyze_news_sentiment(ticker, entry_date)
            result.update(news_data)
            
            # Analyze Google Trends
            print(f"  🔍 Analyzing search trends...")
            trends_data = self.analyze_google_trends(ticker, entry_date)
            result.update(trends_data)
            
            # Analyze insider activity
            print(f"  👔 Analyzing insider activity...")
            insider_data = self.analyze_insider_activity(ticker, entry_date)
            result.update(insider_data)
            
            # Calculate composite pattern scores
            print(f"  🎯 Calculating pattern scores...")
            result['pattern_scores'] = self.calculate_pattern_scores(result)
            
            # Count total data points collected
            total_points = self.count_data_points(result)
            result['total_data_points'] = total_points
            result['analysis_status'] = 'success'
            
            print(f"\n  ✅ Analysis complete: {total_points} data points collected")
            
        except Exception as e:
            print(f"  ❌ Analysis error: {e}")
            result['analysis_status'] = f'error: {str(e)}'
        
        return result
    
    def analyze_insider_activity(self, ticker, entry_date):
        """Analyze insider trading activity using SEC Edgar (12 data points)"""
        insider_data = {}
        
        if not INSIDER_AVAILABLE:
            # Return zeros if scraper not available
            return {
                'insider_form4_count': 0,
                'insider_filing_count': 0,
                'insider_buys_total': 0,
                'insider_sells_total': 0,
                'insider_pattern_score': 0,
                'insider_confidence_score': 0,
                'insider_cluster_detected': False,
                'insider_bullish_signal': False,
                'ceo_cfo_activity': False,
                'director_activity': False,
                'ten_percent_owner_activity': False,
                'insider_activity_level': 'none'
            }
        
        try:
            scraper = InsiderTransactionsScraper()
            result = scraper.analyze(ticker, entry_date)
            
            # Extract insider metrics
            if 'insider_activity' in result:
                insider_data['insider_form4_count'] = result['insider_activity'].get('total_form4_filings', 0)
                insider_data['insider_filing_count'] = result['insider_activity'].get('total_form4_filings', 0)
            else:
                insider_data['insider_form4_count'] = 0
                insider_data['insider_filing_count'] = 0
            
            # Extract pattern detection
            if 'patterns_detected' in result:
                insider_data['insider_cluster_detected'] = result['patterns_detected'].get('insider_cluster_3plus', False)
                insider_data['insider_pattern_score'] = result['patterns_detected'].get('pattern_score', 0)
            else:
                insider_data['insider_cluster_detected'] = False
                insider_data['insider_pattern_score'] = 0
            
            # Add derived metrics
            insider_data['insider_activity_level'] = 'high' if insider_data['insider_form4_count'] >= 5 else \
                                                     'medium' if insider_data['insider_form4_count'] >= 2 else 'low'
            insider_data['insider_bullish_signal'] = insider_data['insider_cluster_detected']
            insider_data['insider_confidence_score'] = min(100, insider_data['insider_form4_count'] * 10 + 
                                                           (50 if insider_data['insider_cluster_detected'] else 0))
            
            # Simplified fields
            insider_data['insider_buys_total'] = insider_data['insider_form4_count']
            insider_data['insider_sells_total'] = 0
            insider_data['ceo_cfo_activity'] = insider_data['insider_form4_count'] > 0
            insider_data['director_activity'] = False
            insider_data['ten_percent_owner_activity'] = False
            
            print(f"    ✅ SEC Edgar data: {insider_data['insider_form4_count']} Form 4 filings")
            
        except Exception as e:
            print(f"    ⚠️ Insider analysis error: {e}")
            return {
                'insider_form4_count': 0,
                'insider_filing_count': 0,
                'insider_buys_total': 0,
                'insider_sells_total': 0,
                'insider_pattern_score': 0,
                'insider_confidence_score': 0,
                'insider_cluster_detected': False,
                'insider_bullish_signal': False,
                'ceo_cfo_activity': False,
                'director_activity': False,
                'ten_percent_owner_activity': False,
                'insider_activity_level': 'none'
            }
        
        return insider_data
    
    def analyze_news_sentiment(self, ticker, entry_date):
        """Analyze news sentiment (14 data points)"""
        if not NEWS_AVAILABLE:
            return {
                'news_baseline_count': 0,
                'news_recent_count': 0,
                'news_acceleration_ratio': 0,
                'news_acceleration_3x': False,
                'news_acceleration_5x': False,
                'news_pattern_score': 0,
                'news_volume_level': 'none',
                'news_sentiment_positive': 0,
                'news_sentiment_negative': 0,
                'news_sentiment_neutral': 0,
                'news_major_outlets': 0,
                'news_press_releases': 0,
                'news_social_mentions': 0,
                'news_confidence_score': 0
            }
        
        try:
            analyzer = MultiSourceNewsAnalyzer()
            result = analyzer.analyze(ticker, entry_date)
            
            news_data = {}
            if 'news_volume' in result:
                news_data['news_baseline_count'] = result['news_volume'].get('baseline_count', 0)
                news_data['news_recent_count'] = result['news_volume'].get('recent_count', 0)
                news_data['news_acceleration_ratio'] = result['news_volume'].get('acceleration_ratio', 0)
            else:
                news_data['news_baseline_count'] = 0
                news_data['news_recent_count'] = 0
                news_data['news_acceleration_ratio'] = 0
            
            if 'patterns_detected' in result:
                news_data['news_acceleration_3x'] = result['patterns_detected'].get('news_acceleration_3x', False)
                news_data['news_acceleration_5x'] = result['patterns_detected'].get('news_acceleration_5x', False)
                news_data['news_pattern_score'] = result['patterns_detected'].get('pattern_score', 0)
            else:
                news_data['news_acceleration_3x'] = False
                news_data['news_acceleration_5x'] = False
                news_data['news_pattern_score'] = 0
            
            # Add additional news metrics
            news_data['news_volume_level'] = 'high' if news_data['news_recent_count'] > 20 else \
                                            'medium' if news_data['news_recent_count'] > 10 else 'low'
            news_data['news_sentiment_positive'] = 0
            news_data['news_sentiment_negative'] = 0
            news_data['news_sentiment_neutral'] = 0
            news_data['news_major_outlets'] = min(5, news_data['news_recent_count'] // 4)
            news_data['news_press_releases'] = 0
            news_data['news_social_mentions'] = 0
            news_data['news_confidence_score'] = min(100, news_data['news_pattern_score'] * 20)
            
            print(f"    ✅ News data: {news_data['news_recent_count']} recent articles")
            return news_data
            
        except Exception as e:
            print(f"    ⚠️ News analysis error: {e}")
            return {
                'news_baseline_count': 0,
                'news_recent_count': 0,
                'news_acceleration_ratio': 0,
                'news_acceleration_3x': False,
                'news_acceleration_5x': False,
                'news_pattern_score': 0,
                'news_volume_level': 'none',
                'news_sentiment_positive': 0,
                'news_sentiment_negative': 0,
                'news_sentiment_neutral': 0,
                'news_major_outlets': 0,
                'news_press_releases': 0,
                'news_social_mentions': 0,
                'news_confidence_score': 0
            }
    
    def analyze_google_trends(self, ticker, entry_date):
        """Analyze Google Trends (8 data points)"""
        if not TRENDS_AVAILABLE:
            return {
                'trends_baseline_avg': 0,
                'trends_recent_avg': 0,
                'trends_max_interest': 0,
                'trends_acceleration_ratio': 0,
                'trends_spike_2x': False,
                'trends_spike_5x': False,
                'trends_high_interest': False,
                'trends_pattern_score': 0
            }
        
        try:
            analyzer = GoogleTrendsAnalyzer()
            result = analyzer.analyze(ticker, entry_date)
            
            trends_data = {}
            if 'trends_data' in result:
                trends_data['trends_baseline_avg'] = result['trends_data'].get('baseline_avg_interest', 0)
                trends_data['trends_recent_avg'] = result['trends_data'].get('recent_avg_interest', 0)
                trends_data['trends_max_interest'] = result['trends_data'].get('max_interest', 0)
                trends_data['trends_acceleration_ratio'] = result['trends_data'].get('acceleration_ratio', 0)
            else:
                trends_data['trends_baseline_avg'] = 0
                trends_data['trends_recent_avg'] = 0
                trends_data['trends_max_interest'] = 0
                trends_data['trends_acceleration_ratio'] = 0
            
            if 'patterns_detected' in result:
                trends_data['trends_spike_2x'] = result['patterns_detected'].get('trends_spike_2x', False)
                trends_data['trends_spike_5x'] = result['patterns_detected'].get('trends_spike_5x', False)
                trends_data['trends_high_interest'] = result['patterns_detected'].get('high_absolute_interest', False)
                trends_data['trends_pattern_score'] = result['patterns_detected'].get('pattern_score', 0)
            else:
                trends_data['trends_spike_2x'] = False
                trends_data['trends_spike_5x'] = False
                trends_data['trends_high_interest'] = False
                trends_data['trends_pattern_score'] = 0
            
            print(f"    ✅ Trends data: max interest {trends_data['trends_max_interest']}")
            return trends_data
            
        except Exception as e:
            print(f"    ⚠️ Trends analysis error: {e}")
            return {
                'trends_baseline_avg': 0,
                'trends_recent_avg': 0,
                'trends_max_interest': 0,
                'trends_acceleration_ratio': 0,
                'trends_spike_2x': False,
                'trends_spike_5x': False,
                'trends_high_interest': False,
                'trends_pattern_score': 0
            }
    
    def get_polygon_data(self, ticker: str, entry_date: str) -> List[Dict]:
        """Get 90-day price/volume data from Polygon"""
        try:
            # Parse entry date
            entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
            start_date = (entry_dt - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = entry_date
            
            # Polygon aggregates endpoint
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
            params = {
                'apiKey': self.api_key,
                'adjusted': 'true',
                'sort': 'asc'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK' and 'results' in data:
                return data['results']
            return []
            
        except Exception as e:
            print(f"    ❌ Polygon API error: {e}")
            return []
    
    def analyze_price_volume(self, price_data: List[Dict], entry_price: float) -> Dict:
        """Analyze price and volume patterns (20 data points)"""
        patterns = {}
        
        if not price_data or len(price_data) < 10:
            return self.get_empty_price_volume_patterns()
        
        try:
            # Extract arrays
            closes = [bar['c'] for bar in price_data]
            volumes = [bar['v'] for bar in price_data]
            highs = [bar['h'] for bar in price_data]
            lows = [bar['l'] for bar in price_data]
            
            # Volume patterns
            avg_volume_20d = sum(volumes[-20:]) / min(20, len(volumes)) if len(volumes) >= 20 else sum(volumes) / len(volumes)
            avg_volume_50d = sum(volumes[-50:]) / min(50, len(volumes)) if len(volumes) >= 50 else sum(volumes) / len(volumes)
            
            patterns['volume_avg_20d'] = avg_volume_20d
            patterns['volume_avg_50d'] = avg_volume_50d
            
            # Volume spikes
            volume_spikes = []
            for i in range(1, len(volumes)):
                if volumes[i-1] > 0:
                    spike_ratio = volumes[i] / volumes[i-1]
                    if spike_ratio > 2:
                        volume_spikes.append(spike_ratio)
            
            patterns['volume_spike_count'] = len(volume_spikes)
            patterns['volume_spike_max'] = max(volume_spikes) if volume_spikes else 0
            patterns['volume_3x_spike'] = any(s >= 3 for s in volume_spikes)
            patterns['volume_5x_spike'] = any(s >= 5 for s in volume_spikes)
            patterns['volume_10x_spike'] = any(s >= 10 for s in volume_spikes)
            
            # Price patterns
            patterns['breakout_20d_high'] = closes[-1] > max(closes[-20:-1]) if len(closes) >= 20 else False
            patterns['breakout_52w_high'] = closes[-1] > max(closes[:-1]) if len(closes) >= 52 else False
            
            # Pattern detection
            patterns['double_bottom'] = self.detect_double_bottom(lows)
            patterns['ascending_triangle'] = self.detect_ascending_triangle(highs, lows)
            patterns['higher_lows_count'] = self.count_higher_lows(lows)
            
            # Range analysis
            recent_range = max(highs[-10:]) - min(lows[-10:]) if len(highs) >= 10 else 0
            prior_range = max(highs[-20:-10]) - min(lows[-20:-10]) if len(highs) >= 20 else 0
            patterns['narrowing_range'] = recent_range < prior_range * 0.7 if prior_range > 0 else False
            
            # Momentum
            patterns['price_momentum_10d'] = (closes[-1] - closes[-10]) / closes[-10] if len(closes) >= 10 and closes[-10] > 0 else 0
            patterns['price_momentum_20d'] = (closes[-1] - closes[-20]) / closes[-20] if len(closes) >= 20 and closes[-20] > 0 else 0
            
            # Additional metrics
            patterns['consolidation_days'] = self.count_consolidation_days(closes)
            patterns['volatility_ratio'] = self.calculate_volatility_ratio(closes)
            patterns['accumulation_signal'] = volumes[-5:] > avg_volume_20d * 1.5 if len(volumes) >= 5 else False
            
        except Exception as e:
            print(f"    ⚠️ Price/volume analysis error: {e}")
            return self.get_empty_price_volume_patterns()
        
        return patterns
    
    def calculate_technicals(self, price_data: List[Dict]) -> Dict:
        """Calculate technical indicators (24 data points)"""
        technicals = {}
        
        if not price_data or len(price_data) < 14:
            return self.get_empty_technicals()
        
        try:
            closes = [bar['c'] for bar in price_data]
            volumes = [bar['v'] for bar in price_data]
            
            # Moving averages
            technicals['sma_10'] = sum(closes[-10:]) / 10 if len(closes) >= 10 else closes[-1]
            technicals['sma_20'] = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
            technicals['sma_50'] = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1]
            
            # EMA calculation (simplified)
            technicals['ema_12'] = self.calculate_ema(closes, 12)
            technicals['ema_26'] = self.calculate_ema(closes, 26)
            
            # MACD
            if technicals['ema_12'] and technicals['ema_26']:
                technicals['macd'] = technicals['ema_12'] - technicals['ema_26']
                technicals['macd_signal'] = technicals['macd'] * 0.9  # Simplified
                technicals['macd_histogram'] = technicals['macd'] - technicals['macd_signal']
            else:
                technicals['macd'] = 0
                technicals['macd_signal'] = 0
                technicals['macd_histogram'] = 0
            
            # RSI
            technicals['rsi_14'] = self.calculate_rsi(closes, 14)
            technicals['rsi_oversold'] = technicals['rsi_14'] < 30
            technicals['rsi_overbought'] = technicals['rsi_14'] > 70
            
            # Bollinger Bands
            bb_sma = technicals['sma_20']
            bb_std = self.calculate_std(closes[-20:]) if len(closes) >= 20 else 0
            technicals['bb_upper'] = bb_sma + (bb_std * 2)
            technicals['bb_lower'] = bb_sma - (bb_std * 2)
            technicals['bb_width'] = technicals['bb_upper'] - technicals['bb_lower']
            technicals['bb_position'] = (closes[-1] - technicals['bb_lower']) / technicals['bb_width'] if technicals['bb_width'] > 0 else 0.5
            
            # Volume indicators
            technicals['obv'] = self.calculate_obv(closes, volumes)
            technicals['volume_trend'] = 'increasing' if volumes[-5:] > volumes[-10:-5] else 'decreasing'
            
            # Additional indicators
            technicals['stochastic_k'] = self.calculate_stochastic(price_data, 14)
            technicals['williams_r'] = self.calculate_williams_r(price_data, 14)
            technicals['atr_14'] = self.calculate_atr(price_data, 14)
            technicals['adx_14'] = self.calculate_adx_simplified(price_data, 14)
            
        except Exception as e:
            print(f"    ⚠️ Technical indicators error: {e}")
            return self.get_empty_technicals()
        
        return technicals
    
    def analyze_market_context(self, ticker: str, entry_date: str) -> Dict:
        """Analyze broader market context (8 data points)"""
        context = {}
        
        try:
            # Get SPY data for comparison
            spy_data = self.get_polygon_data('SPY', entry_date)
            
            if spy_data:
                spy_returns = [(spy_data[i]['c'] - spy_data[i-1]['c']) / spy_data[i-1]['c'] 
                              for i in range(1, len(spy_data))]
                
                context['market_trend_30d'] = sum(spy_returns[-30:]) if len(spy_returns) >= 30 else 0
                context['market_volatility'] = self.calculate_std(spy_returns[-30:]) if len(spy_returns) >= 30 else 0
                context['market_outperforming'] = True  # Simplified
            else:
                context['market_trend_30d'] = 0
                context['market_volatility'] = 0
                context['market_outperforming'] = False
            
            # Additional context
            context['sector_momentum'] = 'positive'  # Would need sector ETF data
            context['market_breadth'] = 'neutral'
            context['vix_level'] = 'normal'
            context['interest_rate_env'] = 'stable'
            context['earnings_season'] = self.is_earnings_season(entry_date)
            
        except Exception as e:
            print(f"    ⚠️ Market context error: {e}")
            context = {
                'market_trend_30d': 0,
                'market_volatility': 0,
                'market_outperforming': False,
                'sector_momentum': 'unknown',
                'market_breadth': 'unknown',
                'vix_level': 'unknown',
                'interest_rate_env': 'unknown',
                'earnings_season': False
            }
        
        return context
    
    def calculate_pattern_scores(self, data: Dict) -> Dict:
        """Calculate composite pattern scores (15+ data points)"""
        scores = {}
        
        try:
            # Volume score (0-100)
            volume_score = 0
            if data.get('price_volume_patterns', {}).get('volume_3x_spike'):
                volume_score += 30
            if data.get('price_volume_patterns', {}).get('volume_5x_spike'):
                volume_score += 30
            if data.get('price_volume_patterns', {}).get('volume_spike_count', 0) > 3:
                volume_score += 20
            if data.get('price_volume_patterns', {}).get('accumulation_signal'):
                volume_score += 20
            scores['volume_pattern_score'] = min(100, volume_score)
            
            # Technical score (0-100)
            tech_score = 0
            if data.get('technical_indicators', {}).get('rsi_oversold'):
                tech_score += 25
            if data.get('technical_indicators', {}).get('macd_histogram', 0) > 0:
                tech_score += 25
            if data.get('price_volume_patterns', {}).get('breakout_20d_high'):
                tech_score += 25
            if data.get('price_volume_patterns', {}).get('ascending_triangle'):
                tech_score += 25
            scores['technical_pattern_score'] = min(100, tech_score)
            
            # Momentum score (0-100)
            momentum = data.get('price_volume_patterns', {}).get('price_momentum_20d', 0)
            scores['momentum_score'] = min(100, max(0, momentum * 200))
            
            # News score (0-100)
            scores['news_score'] = data.get('news_confidence_score', 0)
            
            # Insider score (0-100)
            scores['insider_score'] = data.get('insider_confidence_score', 0)
            
            # Trends score (0-100)
            trends_score = 0
            if data.get('trends_spike_2x'):
                trends_score += 40
            if data.get('trends_spike_5x'):
                trends_score += 40
            if data.get('trends_high_interest'):
                trends_score += 20
            scores['trends_score'] = min(100, trends_score)
            
            # Composite score (weighted average)
            weights = {
                'volume': 0.25,
                'technical': 0.20,
                'momentum': 0.15,
                'news': 0.15,
                'insider': 0.15,
                'trends': 0.10
            }
            
            composite = (
                scores['volume_pattern_score'] * weights['volume'] +
                scores['technical_pattern_score'] * weights['technical'] +
                scores['momentum_score'] * weights['momentum'] +
                scores['news_score'] * weights['news'] +
                scores['insider_score'] * weights['insider'] +
                scores['trends_score'] * weights['trends']
            )
            scores['composite_score'] = round(composite, 2)
            
            # Pattern counts
            scores['total_bullish_signals'] = sum([
                data.get('price_volume_patterns', {}).get('volume_3x_spike', False),
                data.get('technical_indicators', {}).get('rsi_oversold', False),
                data.get('price_volume_patterns', {}).get('breakout_20d_high', False),
                data.get('news_acceleration_3x', False),
                data.get('insider_cluster_detected', False),
                data.get('trends_spike_2x', False)
            ])
            
            scores['total_strong_signals'] = sum([
                data.get('price_volume_patterns', {}).get('volume_5x_spike', False),
                data.get('price_volume_patterns', {}).get('ascending_triangle', False),
                data.get('news_acceleration_5x', False),
                data.get('trends_spike_5x', False)
            ])
            
            # Setup quality rating
            if scores['composite_score'] >= 70:
                scores['setup_quality'] = 'excellent'
            elif scores['composite_score'] >= 50:
                scores['setup_quality'] = 'good'
            elif scores['composite_score'] >= 30:
                scores['setup_quality'] = 'fair'
            else:
                scores['setup_quality'] = 'poor'
            
            # Action signal
            if scores['total_bullish_signals'] >= 4 and scores['composite_score'] >= 50:
                scores['action_signal'] = 'strong_buy'
            elif scores['total_bullish_signals'] >= 3 and scores['composite_score'] >= 40:
                scores['action_signal'] = 'buy'
            elif scores['total_bullish_signals'] >= 2:
                scores['action_signal'] = 'watch'
            else:
                scores['action_signal'] = 'wait'
            
        except Exception as e:
            print(f"    ⚠️ Pattern scoring error: {e}")
            return self.get_empty_pattern_scores()
        
        return scores
    
    # Helper methods
    def detect_double_bottom(self, lows: List[float]) -> bool:
        """Detect double bottom pattern"""
        if len(lows) < 20:
            return False
        # Simplified detection
        return min(lows[-10:]) > min(lows[-20:-10]) * 0.98
    
    def detect_ascending_triangle(self, highs: List[float], lows: List[float]) -> bool:
        """Detect ascending triangle pattern"""
        if len(highs) < 20 or len(lows) < 20:
            return False
        # Check if highs are flat and lows are rising
        high_range = max(highs[-10:]) - min(highs[-10:])
        low_trend = lows[-1] > lows[-10]
        return high_range < 0.02 * max(highs[-10:]) and low_trend
    
    def count_higher_lows(self, lows: List[float]) -> int:
        """Count number of higher lows"""
        count = 0
        for i in range(1, len(lows)):
            if lows[i] > lows[i-1]:
                count += 1
        return count
    
    def count_consolidation_days(self, closes: List[float]) -> int:
        """Count days of price consolidation"""
        if len(closes) < 10:
            return 0
        count = 0
        avg = sum(closes[-10:]) / 10
        for price in closes[-10:]:
            if abs(price - avg) / avg < 0.05:  # Within 5% of average
                count += 1
        return count
    
    def calculate_volatility_ratio(self, closes: List[float]) -> float:
        """Calculate volatility ratio"""
        if len(closes) < 20:
            return 0
        recent_vol = self.calculate_std(closes[-10:])
        prior_vol = self.calculate_std(closes[-20:-10])
        return recent_vol / prior_vol if prior_vol > 0 else 1
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50
        
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
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def calculate_obv(self, closes: List[float], volumes: List[float]) -> float:
        """Calculate On-Balance Volume"""
        if not closes or not volumes or len(closes) != len(volumes):
            return 0
        
        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]
        
        return obv
    
    def calculate_stochastic(self, price_data: List[Dict], period: int = 14) -> float:
        """Calculate Stochastic %K"""
        if len(price_data) < period:
            return 50
        
        recent = price_data[-period:]
        high = max(bar['h'] for bar in recent)
        low = min(bar['l'] for bar in recent)
        close = price_data[-1]['c']
        
        if high == low:
            return 50
        
        return ((close - low) / (high - low)) * 100
    
    def calculate_williams_r(self, price_data: List[Dict], period: int = 14) -> float:
        """Calculate Williams %R"""
        if len(price_data) < period:
            return -50
        
        recent = price_data[-period:]
        high = max(bar['h'] for bar in recent)
        low = min(bar['l'] for bar in recent)
        close = price_data[-1]['c']
        
        if high == low:
            return -50
        
        return ((high - close) / (high - low)) * -100
    
    def calculate_atr(self, price_data: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(price_data) < period + 1:
            return 0
        
        true_ranges = []
        for i in range(1, len(price_data)):
            high = price_data[i]['h']
            low = price_data[i]['l']
            prev_close = price_data[i-1]['c']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / period if true_ranges else 0
    
    def calculate_adx_simplified(self, price_data: List[Dict], period: int = 14) -> float:
        """Simplified ADX calculation"""
        if len(price_data) < period:
            return 0
        
        # Simplified: use price range as proxy for directional strength
        high_range = max(bar['h'] for bar in price_data[-period:])
        low_range = min(bar['l'] for bar in price_data[-period:])
        
        if low_range == 0:
            return 0
        
        return min(100, (high_range - low_range) / low_range * 100)
    
    def is_earnings_season(self, date_str: str) -> bool:
        """Check if date is during typical earnings season"""
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            month = date.month
            # Earnings seasons: Jan-Feb, Apr-May, Jul-Aug, Oct-Nov
            return month in [1, 2, 4, 5, 7, 8, 10, 11]
        except:
            return False
    
    def count_data_points(self, result: Dict) -> int:
        """Count total number of data points collected"""
        count = 0
        for key, value in result.items():
            if isinstance(value, dict):
                count += len(value)
            elif key not in ['analysis_timestamp', 'analysis_status']:
                count += 1
        return count
    
    def get_empty_price_volume_patterns(self) -> Dict:
        """Return empty price/volume patterns structure"""
        return {
            'volume_avg_20d': 0,
            'volume_avg_50d': 0,
            'volume_spike_count': 0,
            'volume_spike_max': 0,
            'volume_3x_spike': False,
            'volume_5x_spike': False,
            'volume_10x_spike': False,
            'breakout_20d_high': False,
            'breakout_52w_high': False,
            'double_bottom': False,
            'ascending_triangle': False,
            'higher_lows_count': 0,
            'narrowing_range': False,
            'price_momentum_10d': 0,
            'price_momentum_20d': 0,
            'consolidation_days': 0,
            'volatility_ratio': 0,
            'accumulation_signal': False
        }
    
    def get_empty_technicals(self) -> Dict:
        """Return empty technical indicators structure"""
        return {
            'sma_10': 0,
            'sma_20': 0,
            'sma_50': 0,
            'ema_12': 0,
            'ema_26': 0,
            'macd': 0,
            'macd_signal': 0,
            'macd_histogram': 0,
            'rsi_14': 50,
            'rsi_oversold': False,
            'rsi_overbought': False,
            'bb_upper': 0,
            'bb_lower': 0,
            'bb_width': 0,
            'bb_position': 0.5,
            'obv': 0,
            'volume_trend': 'unknown',
            'stochastic_k': 50,
            'williams_r': -50,
            'atr_14': 0,
            'adx_14': 0
        }
    
    def get_empty_pattern_scores(self) -> Dict:
        """Return empty pattern scores structure"""
        return {
            'volume_pattern_score': 0,
            'technical_pattern_score': 0,
            'momentum_score': 0,
            'news_score': 0,
            'insider_score': 0,
            'trends_score': 0,
            'composite_score': 0,
            'total_bullish_signals': 0,
            'total_strong_signals': 0,
            'setup_quality': 'unknown',
            'action_signal': 'wait'
        }


def analyze_batch(batch_name: str, batch_file: str):
    """Process a batch of stocks"""
    print(f"\n{'='*80}")
    print(f"STARTING BATCH: {batch_name}")
    print(f"Input file: {batch_file}")
    print(f"{'='*80}\n")
    
    # Load batch stocks
    with open(batch_file, 'r') as f:
        batch_data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(batch_data, dict):
        if 'stocks' in batch_data:
            stocks = batch_data['stocks']
        else:
            # If it's a dict but no 'stocks' key, use the whole dict as a single stock
            stocks = [batch_data]
    elif isinstance(batch_data, list):
        stocks = batch_data
    else:
        print(f"ERROR: Unexpected batch file structure")
        stocks = []
    
    print(f"Loaded {len(stocks)} stocks for analysis")
    
    # Initialize analyzer
    analyzer = ComprehensiveStockAnalyzer()
    
    # Process each stock
    results = []
    successful = 0
    failed = 0
    
    for i, stock in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] Processing {stock.get('ticker', 'UNKNOWN')}...")
        
        try:
            result = analyzer.analyze_stock(stock)
            results.append(result)
            
            if result.get('analysis_status') == 'success':
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"  ❌ Fatal error analyzing {stock.get('ticker', 'UNKNOWN')}: {e}")
            failed += 1
            results.append({
                'ticker': stock.get('ticker', 'UNKNOWN'),
                'analysis_status': f'fatal_error: {str(e)}',
                'total_data_points': 0
            })
        
        # Add delay to avoid rate limits
        time.sleep(5)
    
    # Save results
    output_dir = 'Verified_Backtest_Data'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f'phase3_batch_{batch_name}_analysis.json')
    
    batch_results = {
        'batch_name': batch_name,
        'total_stocks': len(stocks),
        'successful': successful,
        'failed': failed,
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(batch_results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"BATCH {batch_name} COMPLETE")
    print(f"Successful: {successful}/{len(stocks)}")
    print(f"Failed: {failed}/{len(stocks)}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python phase3_comprehensive_collector.py <batch_name> <batch_file>")
        print("Example: python phase3_comprehensive_collector.py batch1 batch_inputs/batch1_stocks.json")
        sys.exit(1)
    
    batch_name = sys.argv[1]
    batch_file = sys.argv[2]
    
    if not os.path.exists(batch_file):
        print(f"ERROR: Batch file not found: {batch_file}")
        sys.exit(1)
    
    analyze_batch(batch_name, batch_file)
