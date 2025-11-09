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
        """Collect pre-catalyst fingerprints for all explosions"""
        
        print("="*60)
        print("PRE-CATALYST FINGERPRINT COLLECTION")
        print("="*60)
        
        # Load clean explosions
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data['discoveries']
        print(f"Found {len(explosions)} explosions to analyze")
        
        fingerprints = []
        
        for i, explosion in enumerate(explosions):
            print(f"\n[{i+1}/{len(explosions)}] Processing {explosion['ticker']}...")
            
            try:
                fingerprint = self.build_fingerprint(explosion)
                fingerprints.append(fingerprint)
                
                # Save progress periodically
                if (i + 1) % 10 == 0:
                    self.save_progress(fingerprints, 'fingerprints_progress.json')
                    print(f"  Saved progress: {len(fingerprints)} complete")
                
                # Rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                print(f"  Error: {e}")
                fingerprints.append({
                    'ticker': explosion['ticker'],
                    'error': str(e),
                    'explosion_data': explosion
                })
        
        # Final save
        self.save_final_analysis(fingerprints, output_file)
        
    def build_fingerprint(self, explosion: Dict) -> Dict:
        """Build complete pre-catalyst fingerprint for one explosion"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Time windows
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_gain': explosion['gain_pct'],
            'volume_spike': explosion['volume_spike'],
            'exit_quality': explosion.get('exit_quality', 'unknown'),
            
            # Collect each category
            'profile': self.get_company_profile(ticker, t_minus_120),
            'technicals': self.get_technical_fingerprint(ticker, t_minus_120, catalyst_date),
            'fundamentals': self.get_fundamental_data(ticker, catalyst_dt),
            'smart_money': self.get_smart_money_indicators(ticker, t_minus_120, catalyst_date),
            'catalyst_type': self.classify_catalyst(ticker, t_minus_30, catalyst_date)
        }
        
        # Add composite scores
        fingerprint['scores'] = self.calculate_composite_scores(fingerprint)
        
        return fingerprint
    
    def get_company_profile(self, ticker: str, as_of_date: str) -> Dict:
        """Get company profile and float data"""
        
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code != 200:
                return {'error': 'Failed to fetch'}
            
            data = response.json().get('results', {})
            
            # Extract key metrics
            market_cap = data.get('market_cap', 0)
            shares = data.get('share_class_shares_outstanding', 0)
            
            return {
                'market_cap': market_cap,
                'shares_outstanding': shares,
                'industry': data.get('sic_description', 'Unknown'),
                'is_low_float': shares < 50_000_000 if shares else False,
                'is_micro_cap': market_cap < 300_000_000 if market_cap else False,
                'float_category': self.categorize_float(shares)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_technical_fingerprint(self, ticker: str, start: str, end: str) -> Dict:
        """Analyze technical patterns in pre-catalyst window"""
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true', 'limit': 50000}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code != 200:
                return {'error': 'Failed to fetch'}
            
            bars = response.json().get('results', [])
            
            if len(bars) < 60:
                return {'insufficient_data': True}
            
            # Calculate technical metrics
            return {
                'volatility_contraction': self.detect_volatility_squeeze(bars),
                'volume_trend': self.analyze_volume_trend(bars),
                'price_consolidation': self.detect_consolidation(bars),
                'relative_strength': self.calculate_relative_strength(ticker, bars, start, end),
                'technical_setup_score': 0  # Will calculate composite
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def detect_volatility_squeeze(self, bars: List[Dict]) -> Dict:
        """Detect Bollinger Band squeeze pattern"""
        
        closes = [b['c'] for b in bars[-60:]]  # Last 60 days
        
        # Calculate BB width trend
        bb_widths = []
        for i in range(20, len(closes)):
            window = closes[i-20:i]
            mean = np.mean(window)
            std = np.std(window)
            bb_width = (2 * std) / mean if mean > 0 else 0
            bb_widths.append(bb_width)
        
        # Check if narrowing
        if len(bb_widths) >= 20:
            recent_avg = np.mean(bb_widths[-10:])
            older_avg = np.mean(bb_widths[-30:-20])
            squeeze_ratio = recent_avg / older_avg if older_avg > 0 else 1
            
            return {
                'is_squeezing': squeeze_ratio < 0.7,
                'squeeze_ratio': squeeze_ratio,
                'current_bb_width': bb_widths[-1] if bb_widths else 0
            }
        
        return {'is_squeezing': False, 'squeeze_ratio': 1.0}
    
    def analyze_volume_trend(self, bars: List[Dict]) -> Dict:
        """Check if volume is drying up"""
        
        volumes = [b['v'] for b in bars[-60:]]  # Last 60 days
        
        if len(volumes) >= 40:
            recent_avg = np.mean(volumes[-20:])
            older_avg = np.mean(volumes[-60:-20])
            volume_ratio = recent_avg / older_avg if older_avg > 0 else 1
            
            return {
                'is_drying_up': volume_ratio < 0.7,
                'volume_ratio': volume_ratio,
                'avg_daily_volume': np.mean(volumes)
            }
        
        return {'is_drying_up': False, 'volume_ratio': 1.0}
    
    def detect_consolidation(self, bars: List[Dict]) -> Dict:
        """Detect price consolidation pattern"""
        
        recent_bars = bars[-30:]  # Last 30 days
        if len(recent_bars) < 20:
            return {'is_consolidating': False}
        
        highs = [b['h'] for b in recent_bars]
        lows = [b['l'] for b in recent_bars]
        
        # Calculate range
        price_range = (max(highs) - min(lows)) / np.mean(lows) if lows else 0
        
        return {
            'is_consolidating': price_range < 0.3,  # Less than 30% range
            'consolidation_range': price_range,
            'days_in_range': len(recent_bars)
        }
    
    def get_fundamental_data(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Get fundamental metrics - revenue growth, profitability"""
        
        # This would need financial statement data
        # Polygon's financials endpoint requires higher tier
        # For now, return placeholder
        
        return {
            'data_available': False,
            'note': 'Financials require upgraded Polygon subscription'
        }
    
    def get_smart_money_indicators(self, ticker: str, start: str, end: str) -> Dict:
        """Get short interest and insider activity"""
        
        # These also require upgraded Polygon tier
        # Return what we can calculate
        
        return {
            'short_interest_available': False,
            'insider_data_available': False,
            'note': 'Requires upgraded Polygon subscription'
        }
    
    def classify_catalyst(self, ticker: str, start: str, end: str) -> str:
        """Try to classify the catalyst type from news"""
        
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': start,
            'published_utc.lte': end,
            'limit': 10
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code != 200:
                return 'unknown'
            
            articles = response.json().get('results', [])
            
            # Simple keyword classification
            for article in articles:
                title = article.get('title', '').lower()
                
                if 'earnings' in title or 'revenue' in title:
                    return 'earnings'
                elif 'fda' in title or 'approval' in title:
                    return 'fda_approval'
                elif 'merger' in title or 'acquisition' in title:
                    return 'merger'
                elif 'contract' in title or 'partnership' in title:
                    return 'contract'
            
            return 'other'
            
        except:
            return 'unknown'
    
    def categorize_float(self, shares: float) -> str:
        """Categorize float size"""
        if not shares:
            return 'unknown'
        elif shares < 10_000_000:
            return 'ultra_low'
        elif shares < 50_000_000:
            return 'low'
        elif shares < 200_000_000:
            return 'medium'
        else:
            return 'high'
    
    def calculate_composite_scores(self, fingerprint: Dict) -> Dict:
        """Calculate composite scores for pattern matching"""
        
        scores = {
            'setup_score': 0,
            'coil_score': 0,
            'fuel_score': 0,
            'total_score': 0
        }
        
        # Setup Score (Company Profile)
        if fingerprint['profile'].get('is_low_float'):
            scores['setup_score'] += 40
        if fingerprint['profile'].get('is_micro_cap'):
            scores['setup_score'] += 30
        
        # Coil Score (Technicals)
        tech = fingerprint['technicals']
        if tech.get('volatility_contraction', {}).get('is_squeezing'):
            scores['coil_score'] += 30
        if tech.get('volume_trend', {}).get('is_drying_up'):
            scores['coil_score'] += 30
        if tech.get('price_consolidation', {}).get('is_consolidating'):
            scores['coil_score'] += 20
        
        scores['total_score'] = scores['setup_score'] + scores['coil_score']
        
        return scores
    
    def calculate_relative_strength(self, ticker: str, bars: List, start: str, end: str) -> float:
        """Calculate relative strength vs SPY"""
        
        # Get SPY data for comparison
        spy_url = f"{self.base_url}/v2/aggs/ticker/SPY/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(spy_url, params=params)
            if response.status_code != 200:
                return 0
            
            spy_bars = response.json().get('results', [])
            
            if len(bars) >= 20 and len(spy_bars) >= 20:
                stock_return = (bars[-1]['c'] - bars[-20]['c']) / bars[-20]['c']
                spy_return = (spy_bars[-1]['c'] - spy_bars[-20]['c']) / spy_bars[-20]['c']
                return stock_return - spy_return
            
        except:
            pass
        
        return 0
    
    def save_progress(self, data: List, filename: str):
        """Save intermediate progress"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_final_analysis(self, fingerprints: List, output_file: str):
        """Save final analysis with summary statistics"""
        
        # Calculate summary stats
        summary = {
            'total_analyzed': len(fingerprints),
            'low_float_count': sum(1 for f in fingerprints if f.get('profile', {}).get('is_low_float')),
            'volatility_squeeze_count': sum(1 for f in fingerprints if f.get('technicals', {}).get('volatility_contraction', {}).get('is_squeezing')),
            'volume_drying_count': sum(1 for f in fingerprints if f.get('technicals', {}).get('volume_trend', {}).get('is_drying_up')),
            'api_calls_made': self.api_calls
        }
        
        output = {
            'analysis_date': datetime.now().isoformat(),
            'summary': summary,
            'fingerprints': fingerprints
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total stocks analyzed: {summary['total_analyzed']}")
        print(f"Low float stocks: {summary['low_float_count']}")
        print(f"Volatility squeezes: {summary['volatility_squeeze_count']}")
        print(f"Volume drying up: {summary['volume_drying_count']}")
        print(f"Results saved to: {output_file}")

def main():
    analyzer = PreCatalystFingerprint(POLYGON_API_KEY)
    analyzer.collect_all_fingerprints('CLEAN_EXPLOSIONS.json', 'FINGERPRINTS.json')

if __name__ == "__main__":
    main()
