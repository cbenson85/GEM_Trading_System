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
        self.base_url = "https://api.polygon.io"
        self.api_calls = 0
        
    def collect_all_fingerprints(self, input_file: str, output_file: str):
        """Main method to collect all fingerprints"""
        
        print("="*60)
        print("PRE-CATALYST FINGERPRINT COLLECTION - ADVANCED TIER")
        print("="*60)
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data['discoveries']
        print(f"Found {len(explosions)} explosions to analyze")
        
        fingerprints = []
        
        for i, explosion in enumerate(explosions):
            print(f"\n[{i+1}/{len(explosions)}] Processing {explosion['ticker']}...")
            
            try:
                fingerprint = self.build_complete_fingerprint(explosion)
                fingerprints.append(fingerprint)
                
                if (i + 1) % 10 == 0:
                    self.save_progress(fingerprints, 'fingerprints_progress.json')
                    print(f"  Saved progress: {len(fingerprints)} complete")
                
                time.sleep(0.15)
                
            except Exception as e:
                print(f"  Error: {e}")
                fingerprints.append({
                    'ticker': explosion['ticker'],
                    'error': str(e),
                    'explosion_data': explosion
                })
        
        self.save_final_analysis(fingerprints, output_file)
    
    def build_complete_fingerprint(self, explosion: Dict) -> Dict:
        """Build complete fingerprint with all Advanced tier data"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Time windows
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        t_plus_5 = (catalyst_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        
        print(f"  Collecting FULL Advanced tier data for {ticker}...")
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_metrics': {
                'gain_pct': float(explosion['gain_pct']),
                'volume_spike': str(explosion['volume_spike']),
                'exit_quality': explosion.get('exit_quality', 'unknown')
            },
            
            # Core data collection
            'profile': self.get_ticker_details_advanced(ticker, t_minus_120),
            'technicals': self.get_technical_analysis(ticker, t_minus_120, catalyst_date),
            'fundamentals': self.get_stock_financials_advanced(ticker, catalyst_dt),
            'relative_strength': self.calculate_relative_strength(ticker, t_minus_120, catalyst_date),
            'news': self.get_news_analysis(ticker, t_minus_30, t_plus_5),
            'price_patterns': self.analyze_price_patterns(ticker, catalyst_dt),
            'volume_profile': self.analyze_volume_profile(ticker, t_minus_120, catalyst_date)
        }
        
        fingerprint['scores'] = self.calculate_all_scores(fingerprint)
        
        return fingerprint
    
    def get_ticker_details_advanced(self, ticker: str, as_of_date: str) -> Dict:
        """Get comprehensive ticker details"""
        
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        params = {'apiKey': self.api_key, 'date': as_of_date}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json().get('results', {})
                
                market_cap = float(data.get('market_cap', 0) or 0)
                shares = float(data.get('share_class_shares_outstanding', 0) or 
                             data.get('weighted_shares_outstanding', 0) or 0)
                
                # Estimate shares if needed
                if shares == 0 and market_cap > 0:
                    price_data = self.get_price_at_date(ticker, as_of_date)
                    if price_data > 0:
                        shares = market_cap / price_data
                
                return {
                    'name': data.get('name', ''),
                    'market_cap': market_cap,
                    'shares_outstanding': shares,
                    'sic_description': data.get('sic_description', ''),
                    'primary_exchange': data.get('primary_exchange', ''),
                    'is_ultra_low_float': bool(0 < shares < 20_000_000),
                    'is_low_float': bool(0 < shares < 50_000_000),
                    'is_micro_cap': bool(0 < market_cap < 300_000_000),
                    'float_category': self.categorize_float(shares),
                    'has_data': True
                }
            
        except Exception as e:
            print(f"    Ticker details error: {e}")
        
        return {'has_data': False}
    
    def get_price_at_date(self, ticker: str, date: str) -> float:
        """Get closing price at specific date"""
        
        url = f"{self.base_url}/v1/open-close/{ticker}/{date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return float(response.json().get('close', 0))
        except:
            pass
        return 0
    
    def get_stock_financials_advanced(self, ticker: str, as_of_date: datetime) -> Dict:
        """Get stock financials - Advanced tier"""
        
        url = f"{self.base_url}/vX/reference/financials"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'timeframe': 'quarterly',
            'limit': 8,
            'sort': 'filing_date',
            'order': 'desc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                
                if len(results) >= 4:
                    q0 = results[0].get('financials', {})
                    q1 = results[1].get('financials', {}) if len(results) > 1 else {}
                    q4 = results[4].get('financials', {}) if len(results) > 4 else {}
                    
                    # Income Statement
                    income_q0 = q0.get('income_statement', {})
                    income_q1 = q1.get('income_statement', {})
                    income_q4 = q4.get('income_statement', {})
                    
                    revenues_q0 = float(income_q0.get('revenues', {}).get('value', 0) or 0)
                    revenues_q1 = float(income_q1.get('revenues', {}).get('value', 0) or 0)
                    revenues_q4 = float(income_q4.get('revenues', {}).get('value', 0) or 0)
                    
                    # Growth calculations
                    qoq_growth = ((revenues_q0 - revenues_q1) / revenues_q1 * 100) if revenues_q1 > 0 else 0
                    yoy_growth = ((revenues_q0 - revenues_q4) / revenues_q4 * 100) if revenues_q4 > 0 else 0
                    
                    # Profitability
                    net_income_q0 = float(income_q0.get('net_income_loss', {}).get('value', 0) or 0)
                    net_income_q1 = float(income_q1.get('net_income_loss', {}).get('value', 0) or 0)
                    
                    # Balance Sheet
                    balance = q0.get('balance_sheet', {})
                    cash = float(balance.get('cash_and_cash_equivalents', {}).get('value', 0) or 0)
                    total_debt = float(balance.get('long_term_debt', {}).get('value', 0) or 0)
                    
                    return {
                        'has_data': True,
                        'revenue': revenues_q0,
                        'revenue_qoq_growth': float(qoq_growth),
                        'revenue_yoy_growth': float(yoy_growth),
                        'is_accelerating': bool(yoy_growth > 50),
                        'net_income': net_income_q0,
                        'turning_profitable': bool(net_income_q0 > 0 and net_income_q1 <= 0),
                        'cash': cash,
                        'total_debt': total_debt
                    }
            
        except Exception as e:
            print(f"    Financials error: {e}")
        
        return {'has_data': False}
    
    def get_technical_analysis(self, ticker: str, start: str, end: str) -> Dict:
        """Complete technical analysis"""
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true', 'sort': 'asc', 'limit': 50000}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                bars = response.json().get('results', [])
                
                if len(bars) < 20:
                    return {'insufficient_data': True}
                
                closes = [float(b['c']) for b in bars]
                volumes = [float(b['v']) for b in bars]
                
                return {
                    'bar_count': len(bars),
                    'bb_squeeze': self.detect_bb_squeeze(closes),
                    'volume_trend': self.analyze_volume_trend_detailed(volumes),
                    'consolidation': self.detect_consolidation_pattern(bars),
                    'volatility_rank': self.calculate_volatility_rank(closes),
                    'rsi': self.calculate_rsi(closes),
                    'price_ma20': float(np.mean(closes[-20:])) if len(closes) >= 20 else 0,
                    'price_ma50': float(np.mean(closes[-50:])) if len(closes) >= 50 else 0,
                    'volume_ma20': float(np.mean(volumes[-20:])) if len(volumes) >= 20 else 0
                }
            
        except Exception as e:
            print(f"    Technical analysis error: {e}")
        
        return {'insufficient_data': True}
    
    def detect_bb_squeeze(self, closes: List[float]) -> Dict:
        """Detect Bollinger Band squeeze"""
        
        if len(closes) < 60:
            return {'is_squeezing': False}
        
        bb_widths = []
        for i in range(20, len(closes)):
            window = closes[i-20:i]
            mean = float(np.mean(window))
            std = float(np.std(window))
            bb_width = (2 * std / mean) if mean > 0 else 0
            bb_widths.append(bb_width)
        
        if len(bb_widths) >= 30:
            recent = float(np.mean(bb_widths[-10:]))
            historical = float(np.mean(bb_widths))
            
            return {
                'is_squeezing': bool(recent < historical * 0.7),
                'current_width': recent,
                'squeeze_ratio': float(recent / historical) if historical > 0 else 1
            }
        
        return {'is_squeezing': False}
    
    def analyze_volume_trend_detailed(self, volumes: List[float]) -> Dict:
        """Detailed volume trend analysis"""
        
        if len(volumes) < 40:
            return {'is_drying': False}
        
        recent = float(np.mean(volumes[-20:]))
        older = float(np.mean(volumes[-40:-20]))
        
        return {
            'is_drying': bool(recent < older * 0.7),
            'volume_ratio': float(recent / older) if older > 0 else 1
        }
    
    def detect_consolidation_pattern(self, bars: List[Dict]) -> Dict:
        """Detect consolidation"""
        
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
    
    def calculate_volatility_rank(self, closes: List[float]) -> float:
        """Calculate volatility rank"""
        
        if len(closes) < 60:
            return 50.0
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                returns.append((closes[i] - closes[i-1]) / closes[i-1])
        
        # Calculate rolling volatility
        vol_values = []
        for i in range(20, len(returns)):
            window_vol = float(np.std(returns[i-20:i]))
            vol_values.append(window_vol)
        
        if vol_values:
            current_vol = vol_values[-1]
            # Simple percentile calculation
            below = sum(1 for v in vol_values if v < current_vol)
            percentile = (below / len(vol_values)) * 100
            return float(percentile)
        
        return 50.0
    
    def calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        
        if len(closes) < period + 1:
            return 50.0
        
        deltas = []
        for i in range(1, len(closes)):
            deltas.append(closes[i] - closes[i-1])
        
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = float(np.mean(gains))
        avg_loss = float(np.mean(losses))
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))
    
    def calculate_relative_strength(self, ticker: str, start: str, end: str) -> Dict:
        """Calculate relative strength vs SPY"""
        
        ticker_url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        spy_url = f"{self.base_url}/v2/aggs/ticker/SPY/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            ticker_resp = requests.get(ticker_url, params=params)
            spy_resp = requests.get(spy_url, params=params)
            self.api_calls += 2
            
            if ticker_resp.status_code == 200 and spy_resp.status_code == 200:
                ticker_bars = ticker_resp.json().get('results', [])
                spy_bars = spy_resp.json().get('results', [])
                
                if len(ticker_bars) >= 20 and len(spy_bars) >= 20:
                    ticker_return = (ticker_bars[-1]['c'] - ticker_bars[0]['c']) / ticker_bars[0]['c']
                    spy_return = (spy_bars[-1]['c'] - spy_bars[0]['c']) / spy_bars[0]['c']
                    
                    return {
                        'relative_strength': float(ticker_return - spy_return),
                        'consistently_strong': bool(ticker_return > spy_return),
                        'strongly_outperforming': bool(ticker_return > spy_return + 0.1)
                    }
        except:
            pass
        
        return {'relative_strength': 0}
    
    def get_news_analysis(self, ticker: str, start: str, end: str) -> Dict:
        """Analyze news for catalyst"""
        
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': start,
            'published_utc.lte': end,
            'limit': 50
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                articles = response.json().get('results', [])
                
                themes = {
                    'earnings': 0,
                    'fda_approval': 0,
                    'merger': 0,
                    'contract': 0,
                    'upgrade': 0,
                    'other': 0
                }
                
                for article in articles:
                    text = (str(article.get('title', '')) + ' ' + 
                           str(article.get('description', ''))).lower()
                    
                    if 'earning' in text or 'revenue' in text:
                        themes['earnings'] += 1
                    elif 'fda' in text or 'approval' in text:
                        themes['fda_approval'] += 1
                    elif 'merger' in text or 'acquisition' in text:
                        themes['merger'] += 1
                    elif 'contract' in text or 'partner' in text:
                        themes['contract'] += 1
                    elif 'upgrade' in text:
                        themes['upgrade'] += 1
                    else:
                        themes['other'] += 1
                
                primary = max(themes, key=themes.get) if any(themes.values()) else 'unknown'
                
                return {
                    'article_count': len(articles),
                    'primary_catalyst': primary,
                    'themes': themes
                }
        except:
            pass
        
        return {'primary_catalyst': 'unknown'}
    
    def analyze_price_patterns(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Analyze price patterns"""
        
        patterns = {}
        periods = [7, 30, 60, 90]
        
        for days in periods:
            start = (catalyst_dt - timedelta(days=days)).strftime('%Y-%m-%d')
            end = catalyst_dt.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
            params = {'apiKey': self.api_key, 'adjusted': 'true'}
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    bars = response.json().get('results', [])
                    if len(bars) >= 2:
                        ret = (bars[-1]['c'] - bars[0]['c']) / bars[0]['c'] if bars[0]['c'] > 0 else 0
                        patterns[f'return_{days}d'] = float(ret)
            except:
                pass
        
        return patterns
    
    def analyze_volume_profile(self, ticker: str, start: str, end: str) -> Dict:
        """Volume profile analysis"""
        
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
                        'unusual_volume_days': int(sum(1 for v in volumes if v > mean_vol * 2)),
                        'dry_volume_days': int(sum(1 for v in volumes if v < mean_vol * 0.5))
                    }
        except:
            pass
        
        return {}
    
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
    
    def calculate_all_scores(self, fingerprint: Dict) -> Dict:
        """Calculate composite scores"""
        
        scores = {
            'setup_score': 0,
            'technical_score': 0,
            'fundamental_score': 0,
            'catalyst_score': 0,
            'total_score': 0
        }
        
        # Setup Score
        profile = fingerprint.get('profile', {})
        if profile.get('is_ultra_low_float'):
            scores['setup_score'] += 50
        elif profile.get('is_low_float'):
            scores['setup_score'] += 30
        if profile.get('is_micro_cap'):
            scores['setup_score'] += 30
        
        # Technical Score
        tech = fingerprint.get('technicals', {})
        if tech.get('bb_squeeze', {}).get('is_squeezing'):
            scores['technical_score'] += 40
        if tech.get('volume_trend', {}).get('is_drying'):
            scores['technical_score'] += 30
        if tech.get('consolidation', {}).get('is_consolidating'):
            scores['technical_score'] += 30
        
        # Fundamental Score
        fund = fingerprint.get('fundamentals', {})
        if fund.get('is_accelerating'):
            scores['fundamental_score'] += 50
        if fund.get('turning_profitable'):
            scores['fundamental_score'] += 50
        
        # Catalyst Score
        news = fingerprint.get('news', {})
        if news.get('primary_catalyst') in ['earnings', 'fda_approval', 'merger']:
            scores['catalyst_score'] += 50
        
        scores['total_score'] = sum(v for k, v in scores.items() if k != 'total_score')
        
        return scores
    
    def clean_for_json(self, obj):
        """Clean numpy types for JSON"""
        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
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
            'low_float': sum(1 for f in fingerprints if f.get('profile', {}).get('is_low_float')),
            'bb_squeeze': sum(1 for f in fingerprints if f.get('technicals', {}).get('bb_squeeze', {}).get('is_squeezing')),
            'volume_drying': sum(1 for f in fingerprints if f.get('technicals', {}).get('volume_trend', {}).get('is_drying')),
            'has_financials': sum(1 for f in fingerprints if f.get('fundamentals', {}).get('has_data')),
            'api_calls': self.api_calls
        }
        
        if summary['total_analyzed'] > 0:
            total = summary['total_analyzed']
            summary['percentages'] = {
                'ultra_low_float_pct': (summary['ultra_low_float'] / total * 100),
                'low_float_pct': (summary['low_float'] / total * 100),
                'bb_squeeze_pct': (summary['bb_squeeze'] / total * 100),
                'volume_drying_pct': (summary['volume_drying'] / total * 100)
            }
        
        output = {
            'analysis_date': datetime.now().isoformat(),
            'api_tier': 'Advanced',
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
        if 'percentages' in summary:
            print(f"Ultra-low float: {summary['percentages']['ultra_low_float_pct']:.1f}%")
            print(f"BB Squeeze: {summary['percentages']['bb_squeeze_pct']:.1f}%")
            print(f"Volume drying: {summary['percentages']['volume_drying_pct']:.1f}%")
        print(f"API calls: {summary['api_calls']}")
        print(f"Saved to: {output_file}")

def main():
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    analyzer = PreCatalystFingerprint(POLYGON_API_KEY)
    
    input_file = 'CLEAN_EXPLOSIONS.json'
    output_file = 'FINGERPRINTS.json'  # CONSISTENT FILENAME
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file {input_file} not found!")
        return
    
    print(f"Starting Advanced Tier analysis...")
    analyzer.collect_all_fingerprints(input_file, output_file)

if __name__ == "__main__":
    main()
