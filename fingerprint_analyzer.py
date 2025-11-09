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
        self.tier = "advanced"  # Advanced tier capabilities
    
    def collect_all_fingerprints(self, input_file: str, output_file: str):
        """Main method to collect all fingerprints"""
        
        print("="*60)
        print("PRE-CATALYST FINGERPRINT COLLECTION - ADVANCED TIER")
        print("="*60)
        print("Using full Advanced tier capabilities...")
        
        # Load clean explosions
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
                
                # Save progress periodically
                if (i + 1) % 10 == 0:
                    self.save_progress(fingerprints, 'fingerprints_progress.json')
                    print(f"  Saved progress: {len(fingerprints)} complete")
                
                # Rate limiting for Advanced tier (higher limits)
                time.sleep(0.15)  # Can go faster with Advanced
                
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
                'exit_quality': explosion.get('exit_quality', 'unknown'),
                'days_to_peak': explosion.get('days_to_peak', 0)
            },
            
            # 1. COMPANY PROFILE DATA
            'profile': self.get_ticker_details_advanced(ticker, t_minus_120),
            
            # 2. TECHNICAL DATA (Full 120-day analysis)
            'technicals': self.get_technical_analysis(ticker, t_minus_120, catalyst_date),
            
            # 3. FUNDAMENTAL DATA (Stock Financials - Advanced tier)
            'fundamentals': self.get_stock_financials_advanced(ticker, catalyst_dt),
            
            # 4. RELATIVE STRENGTH VS SPY
            'relative_strength': self.calculate_relative_strength(ticker, t_minus_120, catalyst_date),
            
            # 5. NEWS & CATALYST DATA
            'news': self.get_news_analysis(ticker, t_minus_30, t_plus_5),
            
            # 6. SNAPSHOT DATA (Real-time-ish data)
            'snapshot': self.get_ticker_snapshot(ticker),
            
            # 7. PRICE ACTION PATTERNS
            'price_patterns': self.analyze_price_patterns(ticker, catalyst_dt),
            
            # 8. VOLUME PROFILE
            'volume_profile': self.analyze_volume_profile(ticker, t_minus_120, catalyst_date)
        }
        
        # Calculate comprehensive scores
        fingerprint['scores'] = self.calculate_all_scores(fingerprint)
        
        return fingerprint
    
    # ============= 1. TICKER DETAILS (ADVANCED) =============
    
    def get_ticker_details_advanced(self, ticker: str, as_of_date: str) -> Dict:
        """Get comprehensive ticker details with Advanced tier"""
        
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        params = {
            'apiKey': self.api_key,
            'date': as_of_date
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json().get('results', {})
                
                # Get all available fields
                market_cap = float(data.get('market_cap', 0) or 0)
                shares_outstanding = float(data.get('share_class_shares_outstanding', 0) or 
                                         data.get('weighted_shares_outstanding', 0) or 0)
                
                # If shares not available, calculate from market cap
                if shares_outstanding == 0 and market_cap > 0:
                    # Get price to estimate shares
                    price_data = self.get_price_at_date(ticker, as_of_date)
                    if price_data and price_data > 0:
                        shares_outstanding = market_cap / price_data
                
                return {
                    'ticker': ticker,
                    'name': data.get('name', ''),
                    'market_cap': market_cap,
                    'shares_outstanding': shares_outstanding,
                    'sic_code': data.get('sic_code', ''),
                    'sic_description': data.get('sic_description', ''),
                    'ticker_root': data.get('ticker_root', ''),
                    'primary_exchange': data.get('primary_exchange', ''),
                    'type': data.get('type', ''),
                    'currency': data.get('currency_name', 'USD'),
                    'locale': data.get('locale', ''),
                    'composite_figi': data.get('composite_figi', ''),
                    'share_class_figi': data.get('share_class_figi', ''),
                    
                    # Categorizations
                    'is_ultra_low_float': bool(0 < shares_outstanding < 20_000_000),
                    'is_low_float': bool(0 < shares_outstanding < 50_000_000),
                    'is_micro_cap': bool(0 < market_cap < 300_000_000),
                    'is_small_cap': bool(300_000_000 <= market_cap < 2_000_000_000),
                    'float_category': self.categorize_float(shares_outstanding),
                    
                    'has_data': True
                }
            
        except Exception as e:
            print(f"    Ticker details error: {e}")
        
        return {'has_data': False}
    
    def get_price_at_date(self, ticker: str, date: str) -> float:
        """Helper to get price at specific date"""
        
        url = f"{self.base_url}/v1/open-close/{ticker}/{date}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('close', 0))
        except:
            pass
        
        return 0
    
    # ============= 2. STOCK FINANCIALS (ADVANCED TIER) =============
    
    def get_stock_financials_advanced(self, ticker: str, as_of_date: datetime) -> Dict:
        """Get comprehensive stock financials - Available in Advanced tier"""
        
        # Stock Financials endpoint - Available in Advanced tier!
        url = f"{self.base_url}/vX/reference/financials"
        
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'timeframe': 'quarterly',
            'limit': 10,  # Get 10 quarters
            'sort': 'filing_date',
            'order': 'desc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if len(results) >= 4:
                    # Get recent quarters
                    q0 = results[0] if len(results) > 0 else {}
                    q1 = results[1] if len(results) > 1 else {}
                    q4 = results[4] if len(results) > 4 else {}  # Year ago quarter
                    
                    # Extract comprehensive financials
                    financials_q0 = q0.get('financials', {})
                    financials_q1 = q1.get('financials', {})
                    financials_q4 = q4.get('financials', {})
                    
                    # Income Statement
                    income_q0 = financials_q0.get('income_statement', {})
                    income_q1 = financials_q1.get('income_statement', {})
                    income_q4 = financials_q4.get('income_statement', {})
                    
                    revenues_q0 = float(income_q0.get('revenues', {}).get('value', 0) or 0)
                    revenues_q1 = float(income_q1.get('revenues', {}).get('value', 0) or 0)
                    revenues_q4 = float(income_q4.get('revenues', {}).get('value', 0) or 0)
                    
                    # Calculate growth metrics
                    qoq_growth = ((revenues_q0 - revenues_q1) / revenues_q1 * 100) if revenues_q1 > 0 else 0
                    yoy_growth = ((revenues_q0 - revenues_q4) / revenues_q4 * 100) if revenues_q4 > 0 else 0
                    
                    # Revenue acceleration
                    if len(results) > 5:
                        q5 = results[5]
                        revenues_q5 = float(q5.get('financials', {}).get('income_statement', {}).get('revenues', {}).get('value', 0) or 0)
                        old_yoy = ((revenues_q1 - revenues_q5) / revenues_q5 * 100) if revenues_q5 > 0 else 0
                        acceleration = yoy_growth - old_yoy
                    else:
                        acceleration = 0
                    
                    # Profitability metrics
                    net_income_q0 = float(income_q0.get('net_income_loss', {}).get('value', 0) or 0)
                    net_income_q1 = float(income_q1.get('net_income_loss', {}).get('value', 0) or 0)
                    gross_profit = float(income_q0.get('gross_profit', {}).get('value', 0) or 0)
                    operating_income = float(income_q0.get('operating_income_loss', {}).get('value', 0) or 0)
                    
                    # Balance Sheet
                    balance_q0 = financials_q0.get('balance_sheet', {})
                    cash = float(balance_q0.get('cash_and_cash_equivalents', {}).get('value', 0) or 0)
                    total_assets = float(balance_q0.get('assets', {}).get('value', 0) or 0)
                    total_debt = float(balance_q0.get('long_term_debt', {}).get('value', 0) or 0)
                    total_equity = float(balance_q0.get('equity', {}).get('value', 0) or 0)
                    
                    # Cash Flow
                    cash_flow = financials_q0.get('cash_flow_statement', {})
                    operating_cf = float(cash_flow.get('net_cash_flow_from_operating_activities', {}).get('value', 0) or 0)
                    free_cash_flow = float(cash_flow.get('net_cash_flow_from_operating_activities_continuing', {}).get('value', 0) or 0)
                    
                    return {
                        'has_data': True,
                        'latest_filing': q0.get('filing_date', ''),
                        'fiscal_period': q0.get('fiscal_period', ''),
                        
                        # Revenue metrics
                        'revenue': revenues_q0,
                        'revenue_qoq_growth': float(qoq_growth),
                        'revenue_yoy_growth': float(yoy_growth),
                        'revenue_acceleration': float(acceleration),
                        'is_accelerating': bool(acceleration > 10),
                        
                        # Profitability
                        'net_income': net_income_q0,
                        'turning_profitable': bool(net_income_q0 > 0 and net_income_q1 <= 0),
                        'gross_profit': gross_profit,
                        'gross_margin': float(gross_profit / revenues_q0 * 100) if revenues_q0 > 0 else 0,
                        'operating_income': operating_income,
                        'operating_margin': float(operating_income / revenues_q0 * 100) if revenues_q0 > 0 else 0,
                        
                        # Balance sheet strength
                        'cash': cash,
                        'total_assets': total_assets,
                        'total_debt': total_debt,
                        'total_equity': total_equity,
                        'debt_to_equity': float(total_debt / total_equity) if total_equity > 0 else 0,
                        'current_ratio': self.calculate_current_ratio(balance_q0),
                        
                        # Cash flow
                        'operating_cash_flow': operating_cf,
                        'free_cash_flow': free_cash_flow,
                        'cash_burn_rate': float(-operating_cf / 3) if operating_cf < 0 else 0,
                        'quarters_of_cash': float(cash / (-operating_cf)) if operating_cf < 0 else 999,
                        
                        # Quality scores
                        'fundamental_quality': self.score_fundamentals(yoy_growth, net_income_q0, operating_cf)
                    }
            
            elif response.status_code == 403:
                print(f"    Note: Stock financials may need Business tier (got 403)")
                return {'has_data': False, 'error': 'May need Business tier'}
            
        except Exception as e:
            print(f"    Financials error: {e}")
        
        return {'has_data': False}
    
    def calculate_current_ratio(self, balance_sheet: Dict) -> float:
        """Calculate current ratio from balance sheet"""
        
        current_assets = float(balance_sheet.get('current_assets', {}).get('value', 0) or 0)
        current_liabilities = float(balance_sheet.get('current_liabilities', {}).get('value', 0) or 0)
        
        if current_liabilities > 0:
            return float(current_assets / current_liabilities)
        return 0
    
    def score_fundamentals(self, revenue_growth: float, net_income: float, operating_cf: float) -> int:
        """Score fundamental quality 0-100"""
        
        score = 0
        
        # Revenue growth scoring
        if revenue_growth > 100:
            score += 40
        elif revenue_growth > 50:
            score += 30
        elif revenue_growth > 20:
            score += 20
        elif revenue_growth > 0:
            score += 10
        
        # Profitability scoring
        if net_income > 0:
            score += 30
        
        # Cash flow scoring
        if operating_cf > 0:
            score += 30
        
        return score
    
    # ============= 3. TECHNICAL ANALYSIS =============
    
    def get_technical_analysis(self, ticker: str, start: str, end: str) -> Dict:
        """Complete technical analysis"""
        
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
                
                # Extract price and volume arrays
                closes = [float(b['c']) for b in bars]
                highs = [float(b['h']) for b in bars]
                lows = [float(b['l']) for b in bars]
                volumes = [float(b['v']) for b in bars]
                
                return {
                    'bar_count': len(bars),
                    
                    # Volatility indicators
                    'bb_squeeze': self.detect_bb_squeeze(closes),
                    'atr_trend': self.calculate_atr_trend(highs, lows, closes),
                    'volatility_rank': self.calculate_volatility_rank(closes),
                    
                    # Volume analysis
                    'volume_trend': self.analyze_volume_trend_detailed(volumes),
                    'volume_ma20': float(np.mean(volumes[-20:])) if len(volumes) >= 20 else 0,
                    'volume_ma50': float(np.mean(volumes[-50:])) if len(volumes) >= 50 else 0,
                    
                    # Price patterns
                    'consolidation': self.detect_consolidation_pattern(bars),
                    'trend_strength': self.calculate_trend_strength(closes),
                    
                    # Moving averages
                    'ma20': float(np.mean(closes[-20:])) if len(closes) >= 20 else 0,
                    'ma50': float(np.mean(closes[-50:])) if len(closes) >= 50 else 0,
                    'ma200': float(np.mean(closes[-200:])) if len(closes) >= 200 else 0,
                    'price_vs_ma20': float((closes[-1] - np.mean(closes[-20:])) / np.mean(closes[-20:])) if len(closes) >= 20 else 0,
                    'price_vs_ma50': float((closes[-1] - np.mean(closes[-50:])) / np.mean(closes[-50:])) if len(closes) >= 50 else 0,
                    
                    # Momentum
                    'rsi': self.calculate_rsi(closes),
                    'macd': self.calculate_macd(closes),
                    'stochastic': self.calculate_stochastic(highs, lows, closes),
                    
                    # Technical setup quality
                    'technical_quality': self.score_technical_setup(bars)
                }
            
        except Exception as e:
            print(f"    Technical analysis error: {e}")
        
        return {'insufficient_data': True}
    
    def detect_bb_squeeze(self, closes: List[float]) -> Dict:
        """Detect Bollinger Band squeeze with details"""
        
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
            recent_width = float(np.mean(bb_widths[-10:]))
            historical_width = float(np.mean(bb_widths))
            squeeze_percentile = float(np.percentile(bb_widths, 20))
            
            return {
                'is_squeezing': bool(recent_width < squeeze_percentile),
                'current_width': recent_width,
                'historical_avg': historical_width,
                'squeeze_ratio': float(recent_width / historical_width) if historical_width > 0 else 1
            }
        
        return {'is_squeezing': False}
    
    def calculate_atr_trend(self, highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        """Calculate ATR and trend"""
        
        if len(highs) < 14:
            return {'atr': 0, 'is_contracting': False}
        
        atrs = []
        for i in range(14, len(highs)):
            tr_values = []
            for j in range(i-14, i):
                high_low = highs[j] - lows[j]
                high_close = abs(highs[j] - closes[j-1]) if j > 0 else 0
                low_close = abs(lows[j] - closes[j-1]) if j > 0 else 0
                tr = max(high_low, high_close, low_close)
                tr_values.append(tr)
            atr = float(np.mean(tr_values))
            atrs.append(atr)
        
        if len(atrs) >= 20:
            recent_atr = float(np.mean(atrs[-10:]))
            older_atr = float(np.mean(atrs[-30:-20]))
            
            return {
                'current_atr': recent_atr,
                'is_contracting': bool(recent_atr < older_atr * 0.8),
                'contraction_ratio': float(recent_atr / older_atr) if older_atr > 0 else 1
            }
        
        return {'current_atr': 0, 'is_contracting': False}
    
    def analyze_volume_trend_detailed(self, volumes: List[float]) -> Dict:
        """Detailed volume trend analysis"""
        
        if len(volumes) < 60:
            return {'is_drying': False}
        
        # Multiple timeframe analysis
        recent_10 = float(np.mean(volumes[-10:]))
        recent_20 = float(np.mean(volumes[-20:]))
        older_20_40 = float(np.mean(volumes[-40:-20]))
        older_40_60 = float(np.mean(volumes[-60:-40]))
        
        # Trend calculation
        volume_trend = (recent_20 - older_20_40) / older_20_40 if older_20_40 > 0 else 0
        
        return {
            'is_drying': bool(recent_20 < older_20_40 * 0.7),
            'volume_trend': float(volume_trend),
            'recent_vs_older': float(recent_20 / older_20_40) if older_20_40 > 0 else 1,
            'accelerating_dryup': bool(recent_10 < recent_20 * 0.8)
        }
    
    # ============= 4. RELATIVE STRENGTH =============
    
    def calculate_relative_strength(self, ticker: str, start: str, end: str) -> Dict:
        """Calculate relative strength vs SPY"""
        
        # Get both ticker and SPY data
        ticker_url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        spy_url = f"{self.base_url}/v2/aggs/ticker/SPY/range/1/day/{start}/{end}"
        
        params = {
            'apiKey': self.api_key,
            'adjusted': 'true',
            'sort': 'asc'
        }
        
        try:
            ticker_resp = requests.get(ticker_url, params=params)
            spy_resp = requests.get(spy_url, params=params)
            self.api_calls += 2
            
            if ticker_resp.status_code == 200 and spy_resp.status_code == 200:
                ticker_bars = ticker_resp.json().get('results', [])
                spy_bars = spy_resp.json().get('results', [])
                
                if len(ticker_bars) >= 60 and len(spy_bars) >= 60:
                    # Calculate at multiple timeframes
                    periods = [5, 10, 20, 60]
                    rs_data = {}
                    
                    for period in periods:
                        if len(ticker_bars) > period and len(spy_bars) > period:
                            ticker_return = (ticker_bars[-1]['c'] - ticker_bars[-period]['c']) / ticker_bars[-period]['c']
                            spy_return = (spy_bars[-1]['c'] - spy_bars[-period]['c']) / spy_bars[-period]['c']
                            
                            rs_data[f'rs_{period}d'] = float(ticker_return - spy_return)
                            rs_data[f'outperform_{period}d'] = bool(ticker_return > spy_return)
                    
                    # Overall RS score
                    rs_values = [v for k, v in rs_data.items() if 'rs_' in k]
                    avg_rs = float(np.mean(rs_values)) if rs_values else 0
                    
                    rs_data['avg_relative_strength'] = avg_rs
                    rs_data['consistently_strong'] = bool(avg_rs > 0)
                    rs_data['strongly_outperforming'] = bool(avg_rs > 0.1)  # 10%+ outperformance
                    
                    return rs_data
            
        except Exception as e:
            print(f"    RS error: {e}")
        
        return {'avg_relative_strength': 0}
    
    # ============= 5. OTHER ANALYSIS METHODS =============
    
    def get_ticker_snapshot(self, ticker: str) -> Dict:
        """Get current snapshot data"""
        
        url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json().get('ticker', {})
                
                return {
                    'has_data': True,
                    'updated': data.get('updated'),
                    'day_change': float(data.get('day', {}).get('c', 0) or 0),
                    'day_change_pct': float(data.get('day', {}).get('change_percent', 0) or 0),
                    'day_volume': float(data.get('day', {}).get('v', 0) or 0),
                    'prev_close': float(data.get('prevDay', {}).get('c', 0) or 0)
                }
        except:
            pass
        
        return {'has_data': False}
    
    def get_news_analysis(self, ticker: str, start: str, end: str) -> Dict:
        """Analyze news for catalyst identification"""
        
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': start,
            'published_utc.lte': end,
            'order': 'asc',
            'limit': 100,
            'sort': 'published_utc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                articles = response.json().get('results', [])
                
                # Categorize news
                themes = {
                    'earnings_beat': 0,
                    'fda_approval': 0,
                    'merger_acquisition': 0,
                    'new_contract': 0,
                    'analyst_upgrade': 0,
                    'short_squeeze': 0,
                    'insider_activity': 0,
                    'other': 0
                }
                
                for article in articles:
                    text = (str(article.get('title', '')) + ' ' + 
                           str(article.get('description', ''))).lower()
                    
                    if 'earnings' in text or 'revenue beat' in text or 'eps beat' in text:
                        themes['earnings_beat'] += 1
                    elif 'fda' in text or 'approval' in text or 'clinical trial' in text:
                        themes['fda_approval'] += 1
                    elif 'merger' in text or 'acquisition' in text or 'buyout' in text:
                        themes['merger_acquisition'] += 1
                    elif 'contract' in text or 'partnership' in text or 'agreement' in text:
                        themes['new_contract'] += 1
                    elif 'upgrade' in text or 'price target' in text or 'raised' in text:
                        themes['analyst_upgrade'] += 1
                    elif 'short' in text or 'squeeze' in text:
                        themes['short_squeeze'] += 1
                    elif 'insider' in text or 'director' in text or 'ceo' in text:
                        themes['insider_activity'] += 1
                    else:
                        themes['other'] += 1
                
                # Identify primary catalyst
                primary = max(themes, key=themes.get) if any(themes.values()) else 'unknown'
                
                return {
                    'article_count': len(articles),
                    'news_velocity': float(len(articles) / 30),  # Articles per day
                    'themes': themes,
                    'primary_catalyst': primary,
                    'has_multiple_catalysts': bool(sum(1 for v in themes.values() if v > 2) >= 2)
                }
        
        except Exception as e:
            print(f"    News error: {e}")
        
        return {'primary_catalyst': 'unknown'}
    
    # Additional helper methods continue...
    
    def analyze_price_patterns(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Analyze price patterns at multiple timeframes"""
        
        patterns = {}
        periods = [7, 14, 30, 60, 90]
        
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
                        period_return = (bars[-1]['c'] - bars[0]['c']) / bars[0]['c'] if bars[0]['c'] > 0 else 0
                        patterns[f'return_{days}d'] = float(period_return)
                        patterns[f'positive_{days}d'] = bool(period_return > 0)
            except:
                pass
        
        return patterns
    
    # Score calculation methods...
    
    def calculate_all_scores(self, fingerprint: Dict) -> Dict:
        """Calculate comprehensive scores"""
        
        scores = {
            'setup_score': 0,      # Max 100
            'technical_score': 0,  # Max 100
            'fundamental_score': 0, # Max 100
            'catalyst_score': 0,   # Max 100
            'total_score': 0       # Max 400
        }
        
        # Setup Score
        profile = fingerprint.get('profile', {})
        if profile.get('is_ultra_low_float'):
            scores['setup_score'] += 50
        elif profile.get('is_low_float'):
            scores['setup_score'] += 30
        
        if profile.get('is_micro_cap'):
            scores['setup_score'] += 30
        elif profile.get('is_small_cap'):
            scores['setup_score'] += 20
        
        # Technical Score
        tech = fingerprint.get('technicals', {})
        if tech.get('bb_squeeze', {}).get('is_squeezing'):
            scores['technical_score'] += 30
        if tech.get('volume_trend', {}).get('is_drying'):
            scores['technical_score'] += 30
        if tech.get('consolidation', {}).get('is_consolidating'):
            scores['technical_score'] += 20
        
        rs = fingerprint.get('relative_strength', {})
        if rs.get('strongly_outperforming'):
            scores['technical_score'] += 20
        
        # Fundamental Score
        fund = fingerprint.get('fundamentals', {})
        if fund.get('has_data'):
            scores['fundamental_score'] = fund.get('fundamental_quality', 0)
        
        # Catalyst Score
        news = fingerprint.get('news', {})
        high_impact = ['earnings_beat', 'fda_approval', 'merger_acquisition']
        if news.get('primary_catalyst') in high_impact:
            scores['catalyst_score'] += 50
        if news.get('has_multiple_catalysts'):
            scores['catalyst_score'] += 25
        
        scores['total_score'] = sum(v for k, v in scores.items() if k != 'total_score')
        
        return scores
    
    # Other helper methods remain the same...
    
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
    
    def detect_consolidation_pattern(self, bars: List[Dict]) -> Dict:
        """Detect consolidation pattern"""
        
        if len(bars) < 30:
            return {'is_consolidating': False}
        
        recent = bars[-30:]
        highs = [b['h'] for b in recent]
        lows = [b['l'] for b in recent]
        closes = [b['c'] for b in recent]
        
        mean_price = float(np.mean(closes))
        price_range = max(highs) - min(lows)
        range_pct = (price_range / mean_price) if mean_price > 0 else 0
        
        return {
            'is_consolidating': bool(range_pct < 0.3),
            'range_pct': float(range_pct),
            'consolidation_days': len(recent)
        }
    
    def calculate_volatility_rank(self, closes: List[float]) -> float:
        """Calculate volatility rank (0-100)"""
        
        if len(closes) < 60:
            return 50.0
        
        # Calculate daily returns
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        # Calculate rolling volatility
        vol_values = []
        for i in range(20, len(returns)):
            window_vol = float(np.std(returns[i-20:i]))
            vol_values.append(window_vol)
        
        if vol_values:
            current_vol = vol_values[-1]
            percentile = float(np.percentile(vol_values, 
                                           [i for i in range(101)]).tolist().index(
                                           min(vol_values, key=lambda x: abs(x - current_vol))))
            return percentile
        
        return 50.0
    
    def calculate_trend_strength(self, closes: List[float]) -> float:
        """Calculate trend strength using linear regression"""
        
        if len(closes) < 20:
            return 0
        
        recent = closes[-20:]
        x = np.arange(len(recent))
        slope, intercept = np.polyfit(x, recent, 1)
        
        # R-squared calculation
        y_pred = slope * x + intercept
        ss_res = np.sum((recent - y_pred) ** 2)
        ss_tot = np.sum((recent - np.mean(recent)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return float(r_squared)
    
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
    
    def calculate_macd(self, closes: List[float]) -> Dict:
        """Calculate MACD"""
        
        if len(closes) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        # Simple EMA approximation
        ema12 = self.calculate_ema(closes, 12)
        ema26 = self.calculate_ema(closes, 26)
        
        macd_line = ema12 - ema26
        signal_line = self.calculate_ema([macd_line], 9) if len([macd_line]) >= 9 else macd_line
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line),
            'signal': float(signal_line),
            'histogram': float(histogram)
        }
    
    def calculate_ema(self, values: List[float], period: int) -> float:
        """Calculate EMA"""
        
        if len(values) < period:
            return float(np.mean(values)) if values else 0
        
        multiplier = 2 / (period + 1)
        ema = float(np.mean(values[:period]))  # Initial SMA
        
        for value in values[period:]:
            ema = (value * multiplier) + (ema * (1 - multiplier))
        
        return float(ema)
    
    def calculate_stochastic(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """Calculate Stochastic oscillator"""
        
        if len(closes) < 14:
            return 50.0
        
        recent_high = max(highs[-14:])
        recent_low = min(lows[-14:])
        current_close = closes[-1]
        
        if recent_high - recent_low > 0:
            k_percent = ((current_close - recent_low) / (recent_high - recent_low)) * 100
            return float(k_percent)
        
        return 50.0
    
    def score_technical_setup(self, bars: List[Dict]) -> int:
        """Score technical setup quality 0-100"""
        
        if len(bars) < 60:
            return 0
        
        score = 0
        
        # Check for consolidation
        recent_30 = bars[-30:]
        highs = [b['h'] for b in recent_30]
        lows = [b['l'] for b in recent_30]
        range_pct = (max(highs) - min(lows)) / np.mean(lows) if lows else 1
        
        if range_pct < 0.3:
            score += 30  # Tight consolidation
        
        # Check for volume dry-up
        volumes = [b['v'] for b in bars]
        recent_vol = np.mean(volumes[-20:])
        older_vol = np.mean(volumes[-60:-20])
        
        if recent_vol < older_vol * 0.7:
            score += 30  # Volume drying up
        
        # Check for higher lows
        lows_60 = [b['l'] for b in bars[-60:]]
        higher_lows = sum(1 for i in range(1, len(lows_60)) if lows_60[i] > lows_60[i-1])
        
        if higher_lows > 30:
            score += 20  # Uptrend
        
        # Check for relative strength
        closes = [b['c'] for b in bars]
        if closes[-1] > np.mean(closes[-50:]):
            score += 20  # Above MA50
        
        return min(score, 100)
    
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
                    prices = [float(b['c']) for b in bars]
                    
                    mean_vol = float(np.mean(volumes))
                    dollar_volumes = [volumes[i] * prices[i] for i in range(len(volumes))]
                    
                    return {
                        'avg_volume': mean_vol,
                        'median_volume': float(np.median(volumes)),
                        'volume_volatility': float(np.std(volumes) / mean_vol) if mean_vol > 0 else 0,
                        'unusual_volume_days': int(sum(1 for v in volumes if v > mean_vol * 2)),
                        'dry_volume_days': int(sum(1 for v in volumes if v < mean_vol * 0.5)),
                        'avg_dollar_volume': float(np.mean(dollar_volumes)),
                        'volume_trend': self.calculate_volume_trend_slope(volumes)
                    }
        except:
            pass
        
        return {}
    
    def calculate_volume_trend_slope(self, volumes: List[float]) -> float:
        """Calculate volume trend slope"""
        
        if len(volumes) < 20:
            return 0
        
        x = np.arange(len(volumes[-20:]))
        y = volumes[-20:]
        
        try:
            slope, _ = np.polyfit(x, y, 1)
            return float(slope)
        except:
            return 0
    
    # ============= SAVE METHODS =============
    
    def clean_for_json(self, obj):
        """Clean numpy types for JSON serialization"""
        if isinstance(obj, (np.bool_, np.bool8)):
            return bool(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
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
        """Save progress to file"""
        clean_data = self.clean_for_json(data)
        with open(filename, 'w') as f:
            json.dump(clean_data, f, indent=2)
    
    def save_final_analysis(self, fingerprints: List, output_file: str):
        """Save final analysis with comprehensive summary"""
        
        # Calculate detailed statistics
        summary = {
            'total_analyzed': len(fingerprints),
            
            # Company profile stats
            'ultra_low_float': sum(1 for f in fingerprints if f.get('profile', {}).get('is_ultra_low_float')),
            'low_float': sum(1 for f in fingerprints if f.get('profile', {}).get('is_low_float')),
            'micro_cap': sum(1 for f in fingerprints if f.get('profile', {}).get('is_micro_cap')),
            
            # Technical stats
            'bb_squeeze': sum(1 for f in fingerprints if f.get('technicals', {}).get('bb_squeeze', {}).get('is_squeezing')),
            'volume_drying': sum(1 for f in fingerprints if f.get('technicals', {}).get('volume_trend', {}).get('is_drying')),
            'consolidating': sum(1 for f in fingerprints if f.get('technicals', {}).get('consolidation', {}).get('is_consolidating')),
            
            # Fundamental stats
            'has_financials': sum(1 for f in fingerprints if f.get('fundamentals', {}).get('has_data')),
            'accelerating_revenue': sum(1 for f in fingerprints if f.get('fundamentals', {}).get('is_accelerating')),
            'turning_profitable': sum(1 for f in fingerprints if f.get('fundamentals', {}).get('turning_profitable')),
            
            # Relative strength
            'outperforming_spy': sum(1 for f in fingerprints if f.get('relative_strength', {}).get('consistently_strong')),
            
            # API usage
            'api_calls': self.api_calls
        }
        
        # Calculate percentages
        if summary['total_analyzed'] > 0:
            total = summary['total_analyzed']
            summary['percentages'] = {
                'ultra_low_float_pct': float(summary['ultra_low_float'] / total * 100),
                'low_float_pct': float(summary['low_float'] / total * 100),
                'micro_cap_pct': float(summary['micro_cap'] / total * 100),
                'bb_squeeze_pct': float(summary['bb_squeeze'] / total * 100),
                'volume_drying_pct': float(summary['volume_drying'] / total * 100),
                'outperforming_spy_pct': float(summary['outperforming_spy'] / total * 100),
                'has_financials_pct': float(summary['has_financials'] / total * 100)
            }
        
        output = {
            'analysis_date': datetime.now().isoformat(),
            'api_tier': 'Advanced',
            'summary': summary,
            'fingerprints': fingerprints
        }
        
        # Clean numpy types
        clean_output = self.clean_for_json(output)
        
        with open(output_file, 'w') as f:
            json.dump(clean_output, f, indent=2)
        
        print("\n" + "="*60)
        print("ADVANCED TIER ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total analyzed: {summary['total_analyzed']}")
        print("\nKey Findings:")
        if 'percentages' in summary:
            pct = summary['percentages']
            print(f"  Ultra-low float (<20M): {pct.get('ultra_low_float_pct', 0):.1f}%")
            print(f"  Low float (<50M): {pct.get('low_float_pct', 0):.1f}%")
            print(f"  Micro cap (<$300M): {pct.get('micro_cap_pct', 0):.1f}%")
            print(f"  BB Squeeze detected: {pct.get('bb_squeeze_pct', 0):.1f}%")
            print(f"  Volume drying up: {pct.get('volume_drying_pct', 0):.1f}%")
            print(f"  Outperforming SPY: {pct.get('outperforming_spy_pct', 0):.1f}%")
            print(f"  Has financials data: {pct.get('has_financials_pct', 0):.1f}%")
        print(f"\nAPI calls made: {summary['api_calls']}")
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
    
    print("Starting Advanced Tier analysis...")
    print("This will collect comprehensive data including financials.")
    analyzer.collect_all_fingerprints(input_file, output_file)

if __name__ == "__main__":
    main()
