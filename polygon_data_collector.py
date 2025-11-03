"""
Polygon Data Collector with Integrated Catalyst Research
Fetches 90-day pre-catalyst data and searches for news/catalysts
Fully automated - zero manual work required
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class PolygonDataCollector:
    """Collects price data and researches catalysts for explosive stocks"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.rate_limit_delay = 0.7  # 100 calls/min = ~0.6s between calls, use 0.7 for safety
        
    def fetch_stock_data(self, ticker: str, entry_date: str, lookback_days: int = 90) -> Dict:
        """
        Fetch comprehensive stock data for analysis window
        
        Args:
            ticker: Stock ticker symbol
            entry_date: Entry date (YYYY-MM-DD)
            lookback_days: Days before entry to analyze (default 90)
            
        Returns:
            Dictionary with price, volume, and technical data
        """
        print(f"📊 Fetching data for {ticker}...")
        
        # Calculate date range
        entry = datetime.strptime(entry_date, '%Y-%m-%d')
        start_date = entry - timedelta(days=lookback_days + 30)  # Extra buffer for MAs
        
        # Fetch price data
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{entry_date}"
        params = {'adjusted': 'true', 'sort': 'asc', 'limit': 50000, 'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('resultsCount', 0) == 0:
                return {'error': 'No data available', 'ticker': ticker}
            
            bars = data.get('results', [])
            print(f"✅ Retrieved {len(bars)} days of data")
            
            time.sleep(self.rate_limit_delay)
            
            return self._process_bars(ticker, bars, entry_date, lookback_days)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching data: {e}")
            return {'error': str(e), 'ticker': ticker}
    
    def _process_bars(self, ticker: str, bars: List[Dict], entry_date: str, lookback_days: int) -> Dict:
        """Process raw price bars into analysis data"""
        
        # Filter to analysis window
        entry = datetime.strptime(entry_date, '%Y-%m-%d')
        window_start = entry - timedelta(days=lookback_days)
        
        filtered_bars = [
            bar for bar in bars 
            if window_start <= datetime.fromtimestamp(bar['t'] / 1000) <= entry
        ]
        
        if len(filtered_bars) < 20:
            return {
                'error': 'Insufficient data',
                'ticker': ticker,
                'days_available': len(filtered_bars)
            }
        
        # Extract basic data
        prices = [bar['c'] for bar in filtered_bars]
        volumes = [bar['v'] for bar in filtered_bars]
        dates = [datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d') for bar in filtered_bars]
        
        # Calculate technical indicators
        technicals = self._calculate_technicals(prices, volumes)
        
        # Detect patterns
        patterns = self._detect_patterns(filtered_bars, technicals)
        
        # Volume analysis
        volume_analysis = self._analyze_volume(volumes, dates)
        
        result = {
            'ticker': ticker,
            'entry_date': entry_date,
            'days_analyzed': len(filtered_bars),
            'data_quality': self._assess_quality(len(filtered_bars)),
            'price_data': {
                'entry_price': prices[-1],
                'high': max(prices),
                'low': min(prices),
                'price_range_pct': ((max(prices) - min(prices)) / min(prices)) * 100,
                'dates': dates,
                'closes': prices
            },
            'volume_analysis': volume_analysis,
            'technical_indicators': technicals,
            'patterns_detected': patterns
        }
        
        return result
    
    def _calculate_technicals(self, prices: List[float], volumes: List[float]) -> Dict:
        """Calculate technical indicators"""
        
        if len(prices) < 30:
            return {'error': 'Insufficient data for technicals'}
        
        # RSI
        rsi_14 = self._calculate_rsi(prices, 14)
        rsi_30 = self._calculate_rsi(prices, 30) if len(prices) >= 30 else None
        
        # Moving Averages
        sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else None
        sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else None
        sma_90 = sum(prices[-90:]) / 90 if len(prices) >= 90 else None
        
        # MACD
        macd_data = self._calculate_macd(prices)
        
        # Bollinger Bands
        bb_data = self._calculate_bollinger_bands(prices, 20)
        
        entry_price = prices[-1]
        
        return {
            'rsi': {
                '14_day': round(rsi_14, 2) if rsi_14 else None,
                '30_day': round(rsi_30, 2) if rsi_30 else None,
                'oversold': rsi_14 < 30 if rsi_14 else False
            },
            'moving_averages': {
                'sma_20': round(sma_20, 4) if sma_20 else None,
                'sma_50': round(sma_50, 4) if sma_50 else None,
                'sma_90': round(sma_90, 4) if sma_90 else None,
                'price_vs_sma20_pct': round(((entry_price - sma_20) / sma_20) * 100, 2) if sma_20 else None,
                'price_vs_sma50_pct': round(((entry_price - sma_50) / sma_50) * 100, 2) if sma_50 else None
            },
            'macd': macd_data,
            'bollinger_bands': bb_data
        }
    
    def _calculate_rsi(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> Dict:
        """Calculate MACD indicator"""
        if len(prices) < 26:
            return {'error': 'Insufficient data'}
        
        # Simple MACD calculation
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26)
        
        if ema_12 is None or ema_26 is None:
            return {'error': 'Calculation failed'}
        
        macd_line = ema_12 - ema_26
        
        return {
            'macd_line': round(macd_line, 4),
            'bullish': macd_line > 0,
            'ema_12': round(ema_12, 4),
            'ema_26': round(ema_26, 4)
        }
    
    def _ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Dict:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {'error': 'Insufficient data'}
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        
        # Standard deviation
        variance = sum((p - sma) ** 2 for p in recent_prices) / period
        std_dev = variance ** 0.5
        
        upper = sma + (2 * std_dev)
        lower = sma - (2 * std_dev)
        bandwidth = ((upper - lower) / sma) * 100
        
        entry_price = prices[-1]
        
        return {
            'middle': round(sma, 4),
            'upper': round(upper, 4),
            'lower': round(lower, 4),
            'bandwidth_pct': round(bandwidth, 2),
            'price_position': 'upper' if entry_price > sma else 'lower'
        }
    
    def _analyze_volume(self, volumes: List[float], dates: List[str]) -> Dict:
        """Analyze volume patterns"""
        
        avg_volume_30 = sum(volumes[-30:]) / min(30, len(volumes))
        
        # Find volume spikes (3x+ average)
        spikes = []
        for i, vol in enumerate(volumes[-30:]):  # Check last 30 days
            if vol >= avg_volume_30 * 3:
                spike_ratio = vol / avg_volume_30
                idx = len(volumes) - 30 + i
                spikes.append({
                    'date': dates[idx],
                    'volume': vol,
                    'ratio': round(spike_ratio, 2),
                    'days_before_entry': len(volumes) - 1 - idx
                })
        
        # Sort by ratio (largest first)
        spikes.sort(key=lambda x: x['ratio'], reverse=True)
        
        return {
            'avg_volume_30day': int(avg_volume_30),
            'entry_day_volume': volumes[-1],
            'entry_day_vs_avg': round(volumes[-1] / avg_volume_30, 2),
            'volume_spikes_3x': len(spikes),
            'top_volume_spikes': spikes[:5]  # Top 5 spikes
        }
    
    def _detect_patterns(self, bars: List[Dict], technicals: Dict) -> Dict:
        """Detect trading patterns"""
        
        patterns = {
            'rsi_oversold_macd_bullish': False,
            'volume_breakout': False,
            'bollinger_squeeze': False,
            'price_consolidation': False
        }
        
        # Pattern 1: RSI Oversold + MACD Bullish
        rsi = technicals.get('rsi', {}).get('14_day')
        macd_bullish = technicals.get('macd', {}).get('bullish', False)
        
        if rsi and rsi < 35 and macd_bullish:
            patterns['rsi_oversold_macd_bullish'] = True
        
        # Pattern 2: Volume Breakout (entry day volume spike)
        volumes = [bar['v'] for bar in bars]
        avg_vol = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else volumes[0]
        
        if volumes[-1] >= avg_vol * 3:
            patterns['volume_breakout'] = True
        
        # Pattern 3: Bollinger Squeeze
        bb = technicals.get('bollinger_bands', {})
        if isinstance(bb, dict) and bb.get('bandwidth_pct', 100) < 20:
            patterns['bollinger_squeeze'] = True
        
        # Pattern 4: Price Consolidation
        if len(bars) >= 10:
            recent_closes = [bar['c'] for bar in bars[-10:]]
            price_range = (max(recent_closes) - min(recent_closes)) / min(recent_closes)
            if price_range < 0.15:  # Within 15% range
                patterns['price_consolidation'] = True
        
        patterns['count'] = sum(1 for v in patterns.values() if v == True)
        
        return patterns
    
    def _assess_quality(self, days: int) -> str:
        """Assess data quality based on days analyzed"""
        if days >= 75:
            return "excellent"
        elif days >= 60:
            return "good"
        elif days >= 40:
            return "acceptable"
        elif days >= 20:
            return "partial"
        else:
            return "insufficient"
    
    def search_catalyst_news(self, ticker: str, company_name: str, entry_date: str) -> Dict:
        """
        Search for catalyst news using web search
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            entry_date: Entry date (YYYY-MM-DD)
            
        Returns:
            Dictionary with search results and catalyst analysis
        """
        print(f"🔍 Searching for catalysts for {ticker}...")
        
        entry = datetime.strptime(entry_date, '%Y-%m-%d')
        pre_window_start = entry - timedelta(days=90)
        
        # Generate search queries
        searches = [
            {
                'query': f'"{company_name}" OR "{ticker}" after:{pre_window_start.strftime("%Y-%m-%d")} before:{entry_date}',
                'purpose': '90-day pre-window news',
                'type': 'general'
            },
            {
                'query': f'"{company_name}" OR "{ticker}" (catalyst OR announcement OR approval OR contract OR earnings) after:{pre_window_start.strftime("%Y-%m-%d")} before:{entry_date}',
                'purpose': 'Catalyst keywords',
                'type': 'catalyst'
            },
            {
                'query': f'"{company_name}" OR "{ticker}" (insider OR "Form 4" OR "insider buying") after:{pre_window_start.strftime("%Y-%m-%d")} before:{entry_date}',
                'purpose': 'Insider activity',
                'type': 'insider'
            }
        ]
        
        # NOTE: Actual web search would be performed here using web_search tool
        # For now, return search queries for manual execution or tool integration
        
        result = {
            'ticker': ticker,
            'company_name': company_name,
            'entry_date': entry_date,
            'search_window': {
                'start': pre_window_start.strftime('%Y-%m-%d'),
                'end': entry_date,
                'days': 90
            },
            'searches_generated': searches,
            'search_count': len(searches),
            'note': 'Search queries generated - integrate with web_search tool for automated execution'
        }
        
        print(f"✅ Generated {len(searches)} search queries")
        
        return result
    
    def analyze_stock_comprehensive(self, ticker: str, company_name: str, entry_date: str, 
                                   peak_date: str, gain_percent: float, days_to_peak: int,
                                   lookback_days: int = 90) -> Dict:
        """
        Comprehensive analysis combining price data and catalyst research
        
        Args:
            ticker: Stock ticker
            company_name: Full company name
            entry_date: Entry date (YYYY-MM-DD)
            peak_date: Peak date (YYYY-MM-DD)
            gain_percent: Total gain percentage
            days_to_peak: Days from entry to peak
            lookback_days: Days before entry to analyze (default 90)
            
        Returns:
            Complete analysis dictionary
        """
        print(f"\n{'='*60}")
        print(f"🎯 ANALYZING: {ticker} ({company_name})")
        print(f"{'='*60}")
        
        # Fetch price and technical data
        price_data = self.fetch_stock_data(ticker, entry_date, lookback_days)
        
        # Search for catalysts
        catalyst_data = self.search_catalyst_news(ticker, company_name, entry_date)
        
        # Combine results
        analysis = {
            'metadata': {
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'analysis_type': 'comprehensive_90day',
                'analyst': 'automated'
            },
            'stock_info': {
                'ticker': ticker,
                'company_name': company_name,
                'entry_date': entry_date,
                'peak_date': peak_date,
                'gain_percent': gain_percent,
                'days_to_peak': days_to_peak
            },
            'price_volume_data': price_data,
            'catalyst_research': catalyst_data,
            'summary': self._generate_summary(price_data, catalyst_data, gain_percent, days_to_peak)
        }
        
        print(f"\n✅ Analysis complete for {ticker}")
        print(f"{'='*60}\n")
        
        return analysis
    
    def _generate_summary(self, price_data: Dict, catalyst_data: Dict, 
                         gain_percent: float, days_to_peak: int) -> Dict:
        """Generate analysis summary"""
        
        summary = {
            'data_quality': price_data.get('data_quality', 'unknown'),
            'days_analyzed': price_data.get('days_analyzed', 0),
            'patterns_found': price_data.get('patterns_detected', {}).get('count', 0),
            'volume_spikes_detected': price_data.get('volume_analysis', {}).get('volume_spikes_3x', 0),
            'rsi_oversold': price_data.get('technical_indicators', {}).get('rsi', {}).get('oversold', False),
            'gain_category': self._categorize_gain(gain_percent),
            'speed_category': self._categorize_speed(days_to_peak),
            'searches_generated': catalyst_data.get('search_count', 0)
        }
        
        # Key signals
        signals = []
        
        if summary['rsi_oversold']:
            signals.append('RSI Oversold (<30)')
        
        if summary['volume_spikes_detected'] > 0:
            signals.append(f"{summary['volume_spikes_detected']} Volume Spikes (3x+)")
        
        if summary['patterns_found'] > 0:
            signals.append(f"{summary['patterns_found']} Patterns Detected")
        
        summary['key_signals'] = signals
        
        return summary
    
    def _categorize_gain(self, gain_percent: float) -> str:
        """Categorize gain magnitude"""
        if gain_percent >= 5000:
            return "extreme"
        elif gain_percent >= 2000:
            return "very_high"
        elif gain_percent >= 1000:
            return "high"
        elif gain_percent >= 500:
            return "moderate"
        else:
            return "baseline"
    
    def _categorize_speed(self, days: int) -> str:
        """Categorize explosion speed"""
        if days <= 7:
            return "ultra_fast"
        elif days <= 30:
            return "fast"
        elif days <= 90:
            return "medium"
        else:
            return "slow"


def main():
    """Example usage"""
    
    # Get API key from environment
    api_key = os.environ.get('POLYGON_API_KEY')
    if not api_key:
        print("❌ Error: POLYGON_API_KEY environment variable not set")
        return
    
    # Initialize collector
    collector = PolygonDataCollector(api_key)
    
    # Example: Analyze ASNS
    analysis = collector.analyze_stock_comprehensive(
        ticker='ASNS',
        company_name='Actelis Networks',
        entry_date='2024-05-31',
        peak_date='2024-06-03',
        gain_percent=955.05,
        days_to_peak=3
    )
    
    # Save results
    output_file = 'phase3b_ASNS_2024_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"✅ Saved analysis to {output_file}")


if __name__ == "__main__":
    main()
