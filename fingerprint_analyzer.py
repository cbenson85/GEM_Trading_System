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
        
    def build_fingerprint(self, explosion: Dict) -> Dict:
        """Build COMPREHENSIVE pre-catalyst fingerprint"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Define all time windows
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_60 = (catalyst_dt - timedelta(days=60)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        t_plus_5 = (catalyst_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        
        print(f"  Collecting comprehensive data for {ticker}...")
        
        # 1. COMPANY PROFILE & FLOAT DATA
        profile = self.get_complete_profile(ticker, t_minus_120)
        
        # 2. FULL TECHNICAL ANALYSIS (120 days)
        technicals = self.get_complete_technicals(ticker, t_minus_120, catalyst_date)
        
        # 3. FUNDAMENTAL DATA (Quarterly financials)
        fundamentals = self.get_fundamentals(ticker, catalyst_dt)
        
        # 4. SMART MONEY INDICATORS
        smart_money = self.get_smart_money_data(ticker, t_minus_120, catalyst_date)
        
        # 5. NEWS & CATALYST CLASSIFICATION
        narrative = self.get_narrative_analysis(ticker, t_minus_30, t_plus_5)
        
        # 6. PRICE ACTION DETAILS (Multiple timeframes)
        price_action = self.analyze_price_action(ticker, catalyst_dt)
        
        # 7. VOLUME PROFILE ANALYSIS
        volume_profile = self.analyze_volume_profile(ticker, t_minus_120, catalyst_date)
        
        # 8. SECTOR & MARKET CONTEXT
        market_context = self.get_market_context(ticker, t_minus_120, catalyst_date)
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_metrics': {
                'gain_pct': explosion['gain_pct'],
                'days_to_peak': explosion.get('days_to_peak'),
                'volume_spike': explosion['volume_spike'],
                'exit_quality': explosion.get('exit_quality', 'unknown')
            },
            
            # ALL DATA CATEGORIES
            'profile': profile,
            'technicals': technicals,
            'fundamentals': fundamentals,
            'smart_money': smart_money,
            'narrative': narrative,
            'price_action': price_action,
            'volume_profile': volume_profile,
            'market_context': market_context,
            
            # COMPOSITE SCORING
            'composite_scores': self.calculate_all_scores(
                profile, technicals, fundamentals, smart_money, volume_profile
            )
        }
        
        return fingerprint
    
    def get_complete_technicals(self, ticker: str, start: str, end: str) -> Dict:
        """Get ALL technical indicators"""
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true', 'limit': 50000}
        
        response = requests.get(url, params=params)
        bars = response.json().get('results', [])
        
        if len(bars) < 60:
            return {'insufficient_data': True}
        
        # Calculate everything
        closes = [b['c'] for b in bars]
        volumes = [b['v'] for b in bars]
        highs = [b['h'] for b in bars]
        lows = [b['l'] for b in bars]
        
        return {
            # VOLATILITY METRICS
            'bb_squeeze': self.calculate_bb_squeeze(closes),
            'atr_contraction': self.calculate_atr_trend(highs, lows, closes),
            'volatility_percentile': self.calculate_volatility_percentile(closes),
            
            # VOLUME ANALYSIS
            'volume_trend': self.calculate_volume_trend(volumes),
            'volume_ma_ratio': volumes[-1] / np.mean(volumes[-20:]) if len(volumes) >= 20 else 0,
            'accumulation_days': self.count_accumulation_days(bars),
            
            # PRICE PATTERNS
            'consolidation_score': self.score_consolidation(bars),
            'higher_lows_count': self.count_higher_lows(lows),
            'tightening_range': self.detect_tightening_range(bars),
            
            # MOMENTUM
            'rsi': self.calculate_rsi(closes),
            'macd_signal': self.calculate_macd_signal(closes),
            
            # MOVING AVERAGES
            'ma20': np.mean(closes[-20:]) if len(closes) >= 20 else 0,
            'ma50': np.mean(closes[-50:]) if len(closes) >= 50 else 0,
            'price_vs_ma50': (closes[-1] - np.mean(closes[-50:])) / np.mean(closes[-50:]) if len(closes) >= 50 else 0,
            
            # RELATIVE STRENGTH
            'relative_strength_spy': self.get_relative_strength(ticker, start, end),
            'relative_strength_sector': self.get_sector_relative_strength(ticker, start, end)
        }
    
    def get_fundamentals(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Get quarterly financials and growth metrics"""
        
        # Get last 6 quarters before catalyst
        url = f"{self.base_url}/vX/reference/financials"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'limit': 6,
            'timeframe': 'quarterly',
            'filing_date.lte': catalyst_dt.strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                financials = response.json().get('results', [])
                
                if len(financials) >= 2:
                    # Calculate growth metrics
                    latest = financials[0]
                    prior = financials[1]
                    year_ago = financials[3] if len(financials) > 3 else None
                    
                    return {
                        'revenue_growth_qoq': self.calculate_growth(
                            latest.get('revenues'), 
                            prior.get('revenues')
                        ),
                        'revenue_growth_yoy': self.calculate_growth(
                            latest.get('revenues'),
                            year_ago.get('revenues') if year_ago else None
                        ),
                        'revenue_acceleration': self.detect_acceleration(financials),
                        'turning_profitable': self.detect_profitability_turn(financials),
                        'ebitda_positive': latest.get('ebitda', 0) > 0 if latest else False,
                        'cash_burn_rate': self.calculate_burn_rate(financials),
                        'debt_to_equity': latest.get('debt_to_equity_ratio', 0),
                        'latest_quarter_date': latest.get('end_date')
                    }
            
        except:
            pass
        
        return {'data_available': False}
    
    def get_smart_money_data(self, ticker: str, start: str, end: str) -> Dict:
        """Get short interest, insider transactions, institutional ownership"""
        
        data = {}
        
        # SHORT INTEREST (if available)
        si_url = f"{self.base_url}/v2/reference/short_interest/{ticker}"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(si_url, params=params)
            if response.status_code == 200:
                si_data = response.json().get('results', [])
                if si_data:
                    latest = si_data[0]
                    data['short_interest'] = latest.get('short_interest')
                    data['days_to_cover'] = latest.get('days_to_cover', 0)
                    data['short_pct_float'] = latest.get('short_percent_of_float', 0)
                    data['high_short_interest'] = data['short_pct_float'] > 15
        except:
            pass
        
        # INSIDER TRANSACTIONS
        insider_url = f"{self.base_url}/v2/reference/insider_transactions"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'start_date': start,
            'end_date': end
        }
        
        try:
            response = requests.get(insider_url, params=params)
            if response.status_code == 200:
                transactions = response.json().get('results', [])
                
                # Count buys vs sells
                buys = [t for t in transactions if t.get('transaction_type') == 'buy']
                sells = [t for t in transactions if t.get('transaction_type') == 'sell']
                
                data['insider_buys'] = len(buys)
                data['insider_sells'] = len(sells)
                data['insider_net_buying'] = len(buys) > len(sells)
                data['insider_buy_value'] = sum(t.get('total_value', 0) for t in buys)
        except:
            pass
        
        return data
    
    def get_narrative_analysis(self, ticker: str, start: str, end: str) -> Dict:
        """Analyze news and classify catalyst"""
        
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': start,
            'published_utc.lte': end,
            'limit': 50,
            'sort': 'published_utc'
        }
        
        response = requests.get(url, params=params)
        articles = response.json().get('results', [])
        
        # Classify news themes
        themes = {
            'earnings': 0,
            'fda_clinical': 0,
            'merger_acquisition': 0,
            'contract_partnership': 0,
            'analyst_upgrade': 0,
            'short_squeeze': 0,
            'sector_momentum': 0,
            'other': 0
        }
        
        for article in articles:
            title = (article.get('title', '') + ' ' + article.get('description', '')).lower()
            
            if 'earning' in title or 'revenue' in title or 'eps' in title:
                themes['earnings'] += 1
            elif 'fda' in title or 'clinical' in title or 'trial' in title or 'approval' in title:
                themes['fda_clinical'] += 1
            elif 'merger' in title or 'acquisition' in title or 'buyout' in title:
                themes['merger_acquisition'] += 1
            elif 'contract' in title or 'partnership' in title or 'deal' in title:
                themes['contract_partnership'] += 1
            elif 'upgrade' in title or 'price target' in title:
                themes['analyst_upgrade'] += 1
            elif 'short' in title or 'squeeze' in title:
                themes['short_squeeze'] += 1
            else:
                themes['other'] += 1
        
        # Determine primary catalyst
        primary_catalyst = max(themes, key=themes.get) if themes else 'unknown'
        
        return {
            'news_count': len(articles),
            'news_themes': themes,
            'primary_catalyst': primary_catalyst,
            'news_velocity': len(articles) / 30,  # News per day
            'has_multiple_catalysts': sum(v > 0 for v in themes.values()) > 1
        }
    
    def analyze_price_action(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Detailed price action analysis at multiple timeframes"""
        
        # Get data for different periods
        periods = {
            '7d': 7,
            '14d': 14,
            '30d': 30,
            '60d': 60,
            '90d': 90
        }
        
        price_action = {}
        
        for period_name, days in periods.items():
            start = (catalyst_dt - timedelta(days=days)).strftime('%Y-%m-%d')
            end = catalyst_dt.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
            params = {'apiKey': self.api_key, 'adjusted': 'true'}
            
            response = requests.get(url, params=params)
            bars = response.json().get('results', [])
            
            if bars:
                price_action[f'return_{period_name}'] = (bars[-1]['c'] - bars[0]['c']) / bars[0]['c']
                price_action[f'max_drawdown_{period_name}'] = self.calculate_max_drawdown(bars)
        
        return price_action
    
    def analyze_volume_profile(self, ticker: str, start: str, end: str) -> Dict:
        """Detailed volume analysis"""
        
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        response = requests.get(url, params=params)
        bars = response.json().get('results', [])
        
        if len(bars) < 20:
            return {}
        
        volumes = [b['v'] for b in bars]
        
        return {
            'avg_volume': np.mean(volumes),
            'median_volume': np.median(volumes),
            'volume_volatility': np.std(volumes) / np.mean(volumes),
            'unusual_volume_days': sum(1 for v in volumes if v > np.mean(volumes) * 2),
            'dry_volume_days': sum(1 for v in volumes if v < np.mean(volumes) * 0.5),
            'volume_trend_slope': self.calculate_trend_slope(volumes),
            'dollar_volume_avg': np.mean([bars[i]['v'] * bars[i]['c'] for i in range(len(bars))])
        }
    
    def calculate_all_scores(self, profile, technicals, fundamentals, smart_money, volume) -> Dict:
        """Calculate comprehensive scoring"""
        
        scores = {
            'setup_score': 0,  # Company profile
            'coil_score': 0,   # Technical setup
            'fuel_score': 0,   # Fundamentals
            'squeeze_score': 0, # Short interest
            'momentum_score': 0, # Price/volume momentum
            'total_score': 0
        }
        
        # Setup Score (max 100)
        if profile.get('is_low_float'):
            scores['setup_score'] += 40
        if profile.get('is_micro_cap'):
            scores['setup_score'] += 30
        if profile.get('shares_outstanding', float('inf')) < 20_000_000:
            scores['setup_score'] += 30
        
        # Coil Score (max 100)
        if technicals.get('bb_squeeze', {}).get('is_squeezing'):
            scores['coil_score'] += 35
        if technicals.get('volume_trend', {}).get('is_drying'):
            scores['coil_score'] += 35
        if technicals.get('consolidation_score', 0) > 0.7:
            scores['coil_score'] += 30
        
        # Fuel Score (max 100)
        if fundamentals.get('revenue_acceleration'):
            scores['fuel_score'] += 40
        if fundamentals.get('turning_profitable'):
            scores['fuel_score'] += 40
        if fundamentals.get('revenue_growth_yoy', 0) > 0.5:
            scores['fuel_score'] += 20
        
        # Squeeze Score (max 100)
        if smart_money.get('high_short_interest'):
            scores['squeeze_score'] += 50
        if smart_money.get('insider_net_buying'):
            scores['squeeze_score'] += 30
        if smart_money.get('days_to_cover', 0) > 3:
            scores['squeeze_score'] += 20
        
        # Total
        scores['total_score'] = sum(scores.values()) - scores['total_score']
        
        return scores
