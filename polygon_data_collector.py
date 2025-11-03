#!/usr/bin/env python3
"""
Polygon API Data Collector for Phase 3B
Fetches 90-day OHLC data and calculates technical indicators
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import time

class PolygonDataCollector:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Polygon API key"""
        self.api_key = api_key or os.environ.get('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("Polygon API key required - set POLYGON_API_KEY environment variable")
        
        self.base_url = "https://api.polygon.io"
        self.rate_limit_delay = 0.6  # 100 calls/min = 0.6s between calls
        
    def get_90_day_data(self, ticker: str, entry_date: str) -> Dict:
        """
        Fetch 90 days of OHLC data before entry_date
        
        Args:
            ticker: Stock symbol
            entry_date: Entry date in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary with price/volume data and technical indicators
        """
        print(f"\n📊 Collecting 90-day data for {ticker}")
        print(f"   Entry date: {entry_date}")
        
        # Calculate date range
        entry = datetime.strptime(entry_date, '%Y-%m-%d')
        start = entry - timedelta(days=120)  # Extra days for market holidays
        
        # Fetch aggregates (daily bars)
        aggs_data = self._fetch_aggregates(ticker, start, entry)
        
        if not aggs_data:
            return {"error": "No data available"}
        
        # Trim to exactly 90 days before entry
        aggs_data = aggs_data[-90:] if len(aggs_data) > 90 else aggs_data
        
        # Calculate technical indicators
        technicals = self._calculate_technicals(aggs_data)
        
        # Analyze volume patterns
        volume_analysis = self._analyze_volume(aggs_data)
        
        # Identify consolidation periods
        consolidations = self._find_consolidations(aggs_data)
        
        return {
            "ticker": ticker,
            "analysis_window": {
                "start_date": aggs_data[0]['date'] if aggs_data else start.strftime('%Y-%m-%d'),
                "end_date": entry_date,
                "days_analyzed": len(aggs_data)
            },
            "price_volume": {
                "daily_data": aggs_data,
                "consolidation_periods": consolidations
            },
            "technical_indicators": technicals,
            "volume_analysis": volume_analysis,
            "patterns_detected": self._detect_patterns(aggs_data, technicals)
        }
    
    def _fetch_aggregates(self, ticker: str, start: datetime, end: datetime) -> List[Dict]:
        """Fetch daily OHLCV data from Polygon"""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
        
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            if response.status_code != 200:
                print(f"   ⚠️  API Error: {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get('status') != 'OK' or 'results' not in data:
                print(f"   ⚠️  No results found")
                return []
            
            # Format results
            results = []
            for bar in data['results']:
                results.append({
                    'date': datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d'),
                    'open': bar['o'],
                    'high': bar['h'],
                    'low': bar['l'],
                    'close': bar['c'],
                    'volume': bar['v'],
                    'vwap': bar.get('vw', bar['c'])
                })
            
            print(f"   ✅ Fetched {len(results)} days of data")
            return results
            
        except Exception as e:
            print(f"   ❌ Error fetching data: {str(e)}")
            return []
    
    def _calculate_technicals(self, data: List[Dict]) -> Dict:
        """Calculate technical indicators"""
        if len(data) < 14:
            return {"error": "Insufficient data"}
        
        closes = [bar['close'] for bar in data]
        volumes = [bar['volume'] for bar in data]
        
        return {
            "rsi_14": self._calculate_rsi(closes, 14),
            "rsi_30": self._calculate_rsi(closes, 30) if len(closes) >= 30 else None,
            "macd": self._calculate_macd(closes),
            "moving_averages": {
                "sma_20": self._calculate_sma(closes, 20) if len(closes) >= 20 else None,
                "sma_50": self._calculate_sma(closes, 50) if len(closes) >= 50 else None,
                "sma_90": self._calculate_sma(closes, 90) if len(closes) >= 90 else None
            },
            "bollinger_bands": self._calculate_bollinger(closes, 20) if len(closes) >= 20 else None,
            "volume_sma_30": self._calculate_sma(volumes, 30) if len(volumes) >= 30 else None
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def _calculate_macd(self, prices: List[float]) -> Optional[Dict]:
        """Calculate MACD indicator"""
        if len(prices) < 26:
            return None
        
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        if ema_12 is None or ema_26 is None:
            return None
        
        macd_line = ema_12 - ema_26
        signal_line = macd_line  # Simplified
        
        return {
            "macd_line": round(macd_line, 4),
            "signal_line": round(signal_line, 4),
            "histogram": 0.0
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_sma(self, values: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(values) < period:
            return None
        return round(sum(values[-period:]) / period, 2)
    
    def _calculate_bollinger(self, prices: List[float], period: int = 20) -> Optional[Dict]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        variance = sum((p - sma) ** 2 for p in recent_prices) / period
        std_dev = variance ** 0.5
        
        return {
            "middle": round(sma, 2),
            "upper": round(sma + (2 * std_dev), 2),
            "lower": round(sma - (2 * std_dev), 2),
            "bandwidth": round((4 * std_dev) / sma * 100, 2)
        }
    
    def _analyze_volume(self, data: List[Dict]) -> Dict:
        """Analyze volume patterns"""
        volumes = [bar['volume'] for bar in data]
        
        if len(volumes) < 30:
            return {"error": "Insufficient data"}
        
        avg_volume_30 = sum(volumes[-30:]) / 30
        avg_volume_90 = sum(volumes) / len(volumes)
        
        # Find volume spikes (3x average)
        spikes = []
        for bar in data:
            if bar['volume'] > (avg_volume_30 * 3):
                price_change = ((bar['close'] - bar['open']) / bar['open']) * 100
                spikes.append({
                    'date': bar['date'],
                    'volume': bar['volume'],
                    'vs_avg': round(bar['volume'] / avg_volume_30, 2),
                    'price_change_pct': round(price_change, 2)
                })
        
        return {
            "avg_volume_30d": int(avg_volume_30),
            "avg_volume_90d": int(avg_volume_90),
            "current_vs_30d_avg": round(volumes[-1] / avg_volume_30, 2),
            "volume_spikes_3x": len(spikes),
            "spikes_detail": spikes[-5:] if spikes else []
        }
    
    def _find_consolidations(self, data: List[Dict]) -> List[Dict]:
        """Identify consolidation periods"""
        if len(data) < 20:
            return []
        
        consolidations = []
        window = 10
        
        for i in range(len(data) - window):
            period = data[i:i+window]
            highs = [bar['high'] for bar in period]
            lows = [bar['low'] for bar in period]
            closes = [bar['close'] for bar in period]
            
            price_range = max(highs) - min(lows)
            avg_close = sum(closes) / len(closes)
            range_pct = (price_range / avg_close) * 100
            
            if range_pct < 10:
                consolidations.append({
                    'start_date': period[0]['date'],
                    'end_date': period[-1]['date'],
                    'days': window,
                    'range_pct': round(range_pct, 2)
                })
        
        return consolidations
    
    def _detect_patterns(self, data: List[Dict], technicals: Dict) -> List[Dict]:
        """Detect pre-explosion patterns"""
        patterns = []
        
        if len(data) < 30:
            return patterns
        
        # Volume accumulation
        recent_volumes = [bar['volume'] for bar in data[-10:]]
        recent_closes = [bar['close'] for bar in data[-10:]]
        
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        price_change = ((recent_closes[-1] - recent_closes[0]) / recent_closes[0]) * 100
        
        if avg_volume > technicals.get('volume_sma_30', avg_volume) * 2 and abs(price_change) < 5:
            patterns.append({
                'pattern': 'Volume Accumulation',
                'confidence': 'high',
                'description': 'High volume with minimal price movement',
                'detected_date': data[-1]['date']
            })
        
        # RSI oversold + MACD bullish
        rsi = technicals.get('rsi_14')
        macd = technicals.get('macd', {})
        
        if rsi and rsi < 40 and macd.get('histogram', 0) >= 0:
            patterns.append({
                'pattern': 'RSI Oversold + MACD Bullish',
                'confidence': 'medium',
                'description': 'Oversold with momentum turning positive',
                'detected_date': data[-1]['date']
            })
        
        # Bollinger squeeze
        bb = technicals.get('bollinger_bands', {})
        if bb and bb.get('bandwidth', 100) < 10:
            patterns.append({
                'pattern': 'Bollinger Squeeze',
                'confidence': 'medium',
                'description': 'Volatility compression',
                'detected_date': data[-1]['date']
            })
        
        return patterns

if __name__ == '__main__':
    # Test
    print("Polygon Data Collector - Ready for use")
    print("Usage: collector = PolygonDataCollector()")
    print("       data = collector.get_90_day_data('TICKER', '2024-01-01')")
