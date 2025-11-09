import json
import os
import time
import requests
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')

class PreCatalystFingerprint:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"  # Still using polygon.io domain
        self.api_calls = 0
    
    def collect_all_fingerprints(self, input_file: str, output_file: str):
        """Main method to collect all fingerprints"""
        
        print("="*60)
        print("PRE-CATALYST FINGERPRINT COLLECTION - MASSIVE API VERSION")
        print("="*60)
        
        # Load clean explosions
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data['discoveries']
        print(f"Found {len(explosions)} explosions to analyze")
        print("Using Massive (Polygon) API endpoints...")
        
        fingerprints = []
        
        for i, explosion in enumerate(explosions):
            print(f"\n[{i+1}/{len(explosions)}] Processing {explosion['ticker']}...")
            
            try:
                fingerprint = self.build_complete_fingerprint(explosion)
                fingerprints.append(fingerprint)
                
                # Save progress periodically
                if (i + 1) % 10 == 0:
                    self.save_progress(fingerprints, 'fingerprints_progress.json')
                    print(f"  Saved progress: {len(fingerprints)} complete")
                
                # Rate limiting (5 calls per second for free tier)
                time.sleep(0.3)
                
            except Exception as e:
                print(f"  Error: {e}")
                fingerprints.append({
                    'ticker': explosion['ticker'],
                    'error': str(e),
                    'explosion_data': explosion
                })
        
        # Final save
        self.save_final_analysis(fingerprints, output_file)
    
    def build_complete_fingerprint(self, explosion: Dict) -> Dict:
        """Build complete fingerprint using Massive API"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Define time windows
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        t_plus_5 = (catalyst_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        
        print(f"  Collecting data for {ticker}...")
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_metrics': {
                'gain_pct': float(explosion['gain_pct']),
                'volume_spike': str(explosion['volume_spike']),
                'exit_quality': explosion.get('exit_quality', 'unknown')
            },
            
            # Core data collection
            'profile': self.get_ticker_details(ticker, t_minus_120),
            'technicals': self.get_technical_data(ticker, t_minus_120, catalyst_date),
            'fundamentals': self.get_stock_financials(ticker, catalyst_dt),
            'price_action': self.analyze_price_action(ticker, catalyst_dt),
            'volume_profile': self.analyze_volume_profile(ticker, t_minus_120, catalyst_date),
            'relative_strength': self.calculate_relative_strength(ticker, t_minus_120, catalyst_date),
            'news': self.get_news_data(ticker, t_minus_30, t_plus_5)
        }
        
        # Calculate scores
        fingerprint['scores'] = self.calculate_composite_scores(fingerprint)
        
        return fingerprint
    
    # ============= CORRECT MASSIVE/POLYGON ENDPOINTS =============
    
    def get_ticker_details(self, ticker: str, as_of_date: str) -> Dict:
        """Get ticker details using v3 endpoint"""
        
        # Correct endpoint: /v3/reference/tickers/{ticker}
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        params = {
            'apiKey': self.api_key,
            'date': as_of_date  # Get historical snapshot
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json().get('results', {})
                
                # Extract fields based on actual API response
                market_cap = float(data.get('market_cap', 0) or 0)
                shares = float(data.get('share_class_shares_outstanding', 0) or 
                             data.get('weighted_shares_outstanding', 0) or 0)
                
                # Get SIC/Industry info
                sic_code = data.get('sic_code', '')
                sic_description = data.get('sic_description', '')
                
                return {
                    'name': data.get('name', ''),
                    'market_cap': market_cap,
                    'shares_outstanding': shares,
                    'sic_code': sic_code,
                    'industry': sic_description,
                    'primary_exchange': data.get('primary_exchange', ''),
                    'type': data.get('type', ''),
                    'is_low_float': bool(0 < shares < 50_000_000),
                    'is_ultra_low_float': bool(0 < shares < 20_000_000),
                    'is_micro_cap': bool(0 < market_cap < 300_000_000),
                    'float_category': self.categorize_float(shares),
                    'has_data': True
                }
            
        except Exception as e:
            print(f"    Ticker details error: {e}")
        
        return {'has_data': False}
    
    def get_technical_data(self, ticker: str, start: str, end: str) -> Dict:
        """Get aggregated bars for technical analysis"""
        
        # Correct endpoint: /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc',
            'limit': 50000
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                bars = data.get('results', [])
                
                if len(bars) < 20:
                    return {'insufficient_data': True}
                
                # Calculate technical indicators
                closes = [b['c'] for b in bars]
                volumes = [b['v'] for b in bars]
                
                return {
                    'bar_count': len(bars),
                    'volatility_squeeze': self.detect_volatility_squeeze(bars),
                    'volume_trend': self.analyze_volume_trend(bars),
                    'consolidation': self.detect_consolidation(bars),
                    'bb_width': self.calculate_bb_width(closes),
                    'rsi': self.calculate_rsi(closes),
                    'volume_ma20': float(np.mean(volumes[-20:])) if len(volumes) >= 20 else 0,
                    'price_ma20': float(np.mean(closes[-20:])) if len(closes) >= 20 else 0,
                    'price_ma50': float(np.mean(closes[-50:])) if len(closes) >= 50 else 0
                }
            
        except Exception as e:
            print(f"    Technical data error: {e}")
        
        return {'insufficient_data': True}
    
    def get_stock_financials(self, ticker: str, as_of_date: datetime) -> Dict:
        """Get stock financials - Note: Requires Business tier"""
        
        # This endpoint requires Business tier ($299+/month)
        # /vX/reference/financials
        
        # For Starter tier, we can try to get basic data from snapshot
        snapshot_url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(snapshot_url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json().get('ticker', {})
                
                # Limited financial data available in snapshot
                return {
                    'has_data': True,
                    'day_change': data.get('day', {}).get('change', 0),
                    'day_change_pct': data.get('day', {}).get('change_percent', 0),
                    'prev_close': data.get('prevDay', {}).get('c', 0),
                    'prev_volume': data.get('prevDay', {}).get('v', 0),
                    'note': 'Full financials require Business tier API'
                }
            
        except Exception as e:
            print(f"    Financials error: {e}")
        
        return {
            'has_data': False,
            'note': 'Financials endpoint requires Business tier subscription'
        }
    
    def calculate_relative_strength(self, ticker: str, start: str, end: str) -> Dict:
        """Calculate relative strength vs SPY"""
        
        # Get aggregated bars for both ticker and SPY
        ticker_url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        spy_url = f"{self.base_url}/v2/aggs/ticker/SPY/range/1/day/{start}/{end}"
        
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc'
        }
        
        try:
            # Get ticker data
            ticker_response = requests.get(ticker_url, params=params)
            self.api_calls += 1
            
            # Get SPY data
            spy_response = requests.get(spy_url, params=params)
            self.api_calls += 1
            
            if ticker_response.status_code == 200 and spy_response.status_code == 200:
                ticker_bars = ticker_response.json().get('results', [])
                spy_bars = spy_response.json().get('results', [])
                
                if len(ticker_bars) >= 20 and len(spy_bars) >= 20:
                    # Calculate returns
                    ticker_return = (ticker_bars[-1]['c'] - ticker_bars[0]['c']) / ticker_bars[0]['c']
                    spy_return = (spy_bars[-1]['c'] - spy_bars[0]['c']) / spy_bars[0]['c']
                    
                    return {
                        'ticker_return': float(ticker_return),
                        'spy_return': float(spy_return),
                        'relative_strength': float(ticker_return - spy_return),
                        'outperforming': bool(ticker_return > spy_return),
                        'has_data': True
                    }
            
        except Exception as e:
            print(f"    RS calc error: {e}")
        
        return {'has_data': False}
    
    def get_news_data(self, ticker: str, start: str, end: str) -> Dict:
        """Get news data for catalyst analysis"""
        
        # Correct endpoint: /v2/reference/news
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': start,
            'published_utc.lte': end,
            'order': 'desc',
            'limit': 20,
            'sort': 'published_utc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('results', [])
                
                # Analyze news themes
                themes = self.classify_news_themes(articles)
                
                return {
                    'article_count': len(articles),
                    'themes': themes,
                    'primary_catalyst': max(themes, key=themes.get) if themes else 'unknown',
                    'has_data': True
                }
            
        except Exception as e:
            print(f"    News error: {e}")
        
        return {'has_data': False}
    
    def classify_news_themes(self, articles: List[Dict]) -> Dict:
        """Classify news articles by theme"""
        
        themes = {
            'earnings': 0,
            'fda_approval': 0,
            'merger': 0,
            'contract': 0,
            'upgrade': 0,
            'other': 0
        }
        
        for article in articles:
            title = str(article.get('title', '')).lower()
            description = str(article.get('description', '')).lower()
            full_text = title + ' ' + description
            
            if 'earning' in full_text or 'revenue' in full_text or 'eps' in full_text:
                themes['earnings'] += 1
            elif 'fda' in full_text or 'approval' in full_text or 'clinical' in full_text:
                themes['fda_approval'] += 1
            elif 'merger' in full_text or 'acquisition' in full_text:
                themes['merger'] += 1
            elif 'contract' in full_text or 'partnership' in full_text:
                themes['contract'] += 1
            elif 'upgrade' in full_text or 'price target' in full_text:
                themes['upgrade'] += 1
            else:
                themes['other'] += 1
        
        return themes
    
    def analyze_price_action(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Analyze price action at multiple timeframes"""
        
        periods = {'7d': 7, '30d': 30, '60d': 60, '90d': 90}
        price_action = {}
        
        for period_name, days in periods.items():
            start = (catalyst_dt - timedelta(days=days)).strftime('%Y-%m-%d')
            end = catalyst_dt.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
            params = {'apiKey': self.api_key, 'adjusted': 'true'}
            
            try:
                response = requests.get(url, params=params)
                self.api_calls += 1
                
                if response.status_code == 200:
                    bars = response.json().get('results', [])
                    
                    if bars and len(bars) >= 2:
                        return_val = (bars[-1]['c'] - bars[0]['c']) / bars[0]['c'] if bars[0]['c'] > 0 else 0
                        price_action[f'return_{period_name}'] = float(return_val)
            except:
                pass
        
        return price_action
    
    def analyze_volume_profile(self, ticker: str, start: str, end: str) -> Dict:
        """Analyze volume profile"""
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                bars = response.json().get('results', [])
                
                if len(bars) >= 20:
                    volumes = [float(b['v']) for b in bars]
                    mean_vol = float(np.mean(volumes))
                    
                    return {
                        'avg_volume': mean_vol,
                        'median_volume': float(np.median(volumes)),
                        'volume_volatility': float(np.std(volumes) / mean_vol) if mean_vol > 0 else 0,
                        'unusual_volume_days': int(sum(1 for v in volumes if v > mean_vol * 2)),
                        'dry_volume_days': int(sum(1 for v in volumes if v < mean_vol * 0.5))
                    }
        except:
            pass
        
        return {}
    
    # ============= TECHNICAL INDICATOR CALCULATIONS =============
    
    def detect_volatility_squeeze(self, bars: List[Dict]) -> Dict:
        """Detect Bollinger Band squeeze"""
        
        if len(bars) < 60:
            return {'is_squeezing': False}
        
        closes = [b['c'] for b in bars[-60:]]
        
        # Calculate BB widths
        bb_widths = []
        for i in range(20, len(closes)):
            window = closes[i-20:i]
            mean = float(np.mean(window))
            std = float(np.std(window))
            bb_width = (2 * std) / mean if mean > 0 else 0
            bb_widths.append(bb_width)
        
        if len(bb_widths) >= 30:
            recent = float(np.mean(bb_widths[-10:]))
            older = float(np.mean(bb_widths[-30:-20]))
            squeeze_ratio = recent / older if older > 0 else 1
            
            return {
                'is_squeezing': bool(squeeze_ratio < 0.7),
                'squeeze_ratio': float(squeeze_ratio)
            }
        
        return {'is_squeezing': False}
    
    def analyze_volume_trend(self, bars: List[Dict]) -> Dict:
        """Analyze volume trend"""
        
        if len(bars) < 40:
            return {'is_drying': False}
        
        volumes = [b['v'] for b in bars[-40:]]
        recent = float(np.mean(volumes[-20:]))
        older = float(np.mean(volumes[:20]))
        
        return {
            'is_drying': bool(recent < older * 0.7),
            'volume_ratio': float(recent / older) if older > 0 else 1
        }
    
    def detect_consolidation(self, bars: List[Dict]) -> Dict:
        """Detect consolidation pattern"""
        
        if len(bars) < 30:
            return {'is_consolidating': False}
        
        recent = bars[-30:]
        highs = [b['h'] for b in recent]
        lows = [b['l'] for b in recent]
        
        mean_price = float(np.mean([b['c'] for b in recent]))
        price_range = max(highs) - min(lows)
        range_pct = (price_range / mean_price) if mean_price > 0 else 0
        
        return {
            'is_consolidating': bool(range_pct < 0.3),
            'range_pct': float(range_pct)
        }
    
    def calculate_bb_width(self, closes: List[float]) -> float:
        """Calculate current Bollinger Band width"""
        
        if len(closes) < 20:
            return 0
        
        recent = closes[-20:]
        mean = float(np.mean(recent))
        std = float(np.std(recent))
        
        return float((2 * std) / mean) if mean > 0 else 0
    
    def calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        
        if len(closes) < period + 1:
            return 50.0
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = float(np.mean(gains))
        avg_loss = float(np.mean(losses))
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))
    
    def categorize_float(self, shares: float) -> str:
        """Categorize float size"""
        
        if not shares or shares == 0:
            return 'unknown'
        elif shares < 10_000_000:
            return 'ultra_low'
        elif shares < 20_000_000:
            return 'very_low'  
        elif shares < 50_000_000:
            return 'low'
        elif shares < 200_000_000:
            return 'medium'
        else:
            return 'high'
    
    def calculate_composite_scores(self, fingerprint: Dict) -> Dict:
        """Calculate composite scores"""
        
        scores = {
            'setup_score': 0,
            'technical_score': 0,
            'catalyst_score': 0,
            'total_score': 0
        }
        
        # Company setup score
        profile = fingerprint.get('profile', {})
        if profile.get('is_ultra_low_float'):
            scores['setup_score'] += 50
        elif profile.get('is_low_float'):
            scores['setup_score'] += 30
        if profile.get('is_micro_cap'):
            scores['setup_score'] += 30
        
        # Technical score
        tech = fingerprint.get('technicals', {})
        if tech.get('volatility_squeeze', {}).get('is_squeezing'):
            scores['technical_score'] += 40
        if tech.get('volume_trend', {}).get('is_drying'):
            scores['technical_score'] += 30
        if tech.get('consolidation', {}).get('is_consolidating'):
            scores['technical_score'] += 30
        
        # Catalyst score
        news = fingerprint.get('news', {})
        if news.get('primary_catalyst') in ['earnings', 'fda_approval', 'merger']:
            scores['catalyst_score'] += 50
        
        scores['total_score'] = sum(scores.values()) - scores.get('total_score', 0)
        
        return scores
    
    # ============= SAVE METHODS =============
    
    def clean_for_json(self, obj):
        """Clean numpy types for JSON"""
        if isinstance(obj, (np.bool_, np.bool)):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self.clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_for_json(item) for item in obj]
        else:
            return obj
    
    def save_progress(self, data: List, filename: str):
        """Save progress"""
        clean_data = self.clean_for_json(data)
        with open(filename, 'w') as f:
            json.dump(clean_data, f, indent=2)
    
    def save_final_analysis(self, fingerprints: List, output_file: str):
        """Save final analysis"""
        
        summary = {
            'total_analyzed': len(fingerprints),
            'ultra_low_float': sum(1 for f in fingerprints if f.get('profile', {}).get('is_ultra_low_float')),
            'volatility_squeezes': sum(1 for f in fingerprints if f.get('technicals', {}).get('volatility_squeeze', {}).get('is_squeezing')),
            'volume_drying': sum(1 for f in fingerprints if f.get('technicals', {}).get('volume_trend', {}).get('is_drying')),
            'api_calls': self.api_calls
        }
        
        output = {
            'analysis_date': datetime.now().isoformat(),
            'api_version': 'Massive/Polygon API',
            'summary': summary,
            'fingerprints': fingerprints
        }
        
        clean_output = self.clean_for_json(output)
        
        with open(output_file, 'w') as f:
            json.dump(clean_output, f, indent=2)
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total analyzed: {summary['total_analyzed']}")
        print(f"Ultra-low float: {summary['ultra_low_float']}")
        print(f"Volatility squeezes: {summary['volatility_squeezes']}")
        print(f"Volume drying: {summary['volume_drying']}")
        print(f"API calls made: {summary['api_calls']}")
        print(f"Results saved to: {output_file}")

def main():
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    analyzer = PreCatalystFingerprint(POLYGON_API_KEY)
    
    input_file = 'CLEAN_EXPLOSIONS.json'
    output_file = 'FINGERPRINTS_COMPLETE.json'
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file {input_file} not found!")
        return
    
    print(f"Starting analysis with Massive/Polygon API")
    analyzer.collect_all_fingerprints(input_file, output_file)

if __name__ == "__main__":
    main()
