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
        print("PRE-CATALYST FINGERPRINT COLLECTION - COMPLETE VERSION")
        print("="*60)
        
        # Load clean explosions
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data['discoveries']
        print(f"Found {len(explosions)} explosions to analyze")
        print("Collecting ALL data: Profile, Technicals, Fundamentals, Smart Money, Narrative")
        
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
                
                # Rate limiting
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
        """Build COMPLETE fingerprint with ALL data points"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Define time windows
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_60 = (catalyst_dt - timedelta(days=60)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        t_plus_5 = (catalyst_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        
        print(f"  Collecting COMPLETE data for {ticker}...")
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_metrics': {
                'gain_pct': float(explosion['gain_pct']),
                'volume_spike': str(explosion['volume_spike']),
                'exit_quality': explosion.get('exit_quality', 'unknown'),
                'days_to_peak': explosion.get('days_to_peak', 0)
            },
            
            # 1. COMPANY PROFILE (The Setup)
            'profile': self.get_complete_company_profile(ticker, t_minus_120),
            
            # 2. TECHNICAL DATA (The Coil)
            'technicals': self.get_complete_technicals(ticker, t_minus_120, catalyst_date),
            
            # 3. FUNDAMENTAL DATA (The Fuel)
            'fundamentals': self.get_complete_fundamentals(ticker, catalyst_dt),
            
            # 4. SMART MONEY & SQUEEZE DATA
            'short_interest': self.get_short_interest_data(ticker, catalyst_date),
            'insider_transactions': self.get_insider_transactions(ticker, t_minus_120, catalyst_date),
            'institutional': self.get_institutional_ownership(ticker, catalyst_date),
            
            # 5. NARRATIVE DATA (The Catalyst)
            'narrative': self.get_complete_narrative(ticker, t_minus_30, t_plus_5),
            
            # ADDITIONAL ANALYSIS
            'price_action': self.analyze_price_action(ticker, catalyst_dt),
            'volume_profile': self.analyze_volume_profile(ticker, t_minus_120, catalyst_date),
            'relative_strength': self.get_relative_strength_vs_spy(ticker, t_minus_120, catalyst_date)
        }
        
        # Calculate comprehensive scores
        fingerprint['scores'] = self.calculate_all_scores(fingerprint)
        
        return fingerprint
    
    # ============= 1. COMPANY PROFILE DATA =============
    
    def get_complete_company_profile(self, ticker: str, as_of_date: str) -> Dict:
        """Get COMPLETE company profile with working shares outstanding"""
        
        # Try v3 ticker details endpoint
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json().get('results', {})
                
                # Get shares - try multiple field names
                shares = float(data.get('share_class_shares_outstanding', 0) or 
                             data.get('shares_outstanding', 0) or
                             data.get('weighted_shares_outstanding', 0) or 0)
                
                market_cap = float(data.get('market_cap', 0) or 0)
                
                # If no shares but we have market cap, estimate from price
                if shares == 0 and market_cap > 0:
                    # Get price around the as_of_date
                    price_url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{as_of_date}/{as_of_date}"
                    price_params = {'apiKey': self.api_key, 'adjusted': 'true'}
                    price_response = requests.get(price_url, params=price_params)
                    
                    if price_response.status_code == 200:
                        price_data = price_response.json().get('results', [])
                        if price_data:
                            price = float(price_data[0].get('c', 0))
                            if price > 0:
                                shares = market_cap / price
                
                return {
                    'market_cap': market_cap,
                    'shares_outstanding': shares,
                    'industry': str(data.get('sic_description', '') or data.get('industry', 'Unknown')),
                    'sector': str(data.get('sector', 'Unknown')),
                    'is_low_float': bool(0 < shares < 50_000_000),
                    'is_ultra_low_float': bool(0 < shares < 20_000_000),
                    'is_micro_cap': bool(0 < market_cap < 300_000_000),
                    'is_small_cap': bool(300_000_000 <= market_cap < 2_000_000_000),
                    'float_category': self.categorize_float(shares),
                    'has_data': True
                }
                
        except Exception as e:
            print(f"    Profile error: {e}")
            
        return {'has_data': False, 'error': 'Failed to fetch profile'}
    
    # ============= 2. TECHNICAL DATA (The Coil) =============
    
    def get_complete_technicals(self, ticker: str, start: str, end: str) -> Dict:
        """Get COMPLETE technical analysis with SPY comparison"""
        
        # Get stock data
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
            
            # Calculate ALL technical indicators
            technicals = {
                # Volatility indicators
                'bb_squeeze': self.calculate_bb_squeeze([b['c'] for b in bars]),
                'volatility_contraction': self.detect_volatility_squeeze(bars),
                'atr_trend': self.calculate_atr_trend(bars),
                
                # Volume analysis
                'volume_trend': self.analyze_volume_trend(bars),
                'volume_ma20': float(np.mean([b['v'] for b in bars[-20:]])),
                'volume_ma50': float(np.mean([b['v'] for b in bars[-50:]])) if len(bars) >= 50 else 0,
                'volume_drying_up': self.is_volume_drying_up(bars),
                
                # Price patterns
                'price_consolidation': self.detect_consolidation(bars),
                'higher_lows': self.count_higher_lows(bars),
                'tightening_range': self.detect_tightening_range(bars),
                
                # Moving averages
                'ma20': float(np.mean([b['c'] for b in bars[-20:]])),
                'ma50': float(np.mean([b['c'] for b in bars[-50:]])) if len(bars) >= 50 else 0,
                'price_above_ma50': bool(bars[-1]['c'] > np.mean([b['c'] for b in bars[-50:]])) if len(bars) >= 50 else False,
                
                # Momentum
                'rsi': self.calculate_rsi([b['c'] for b in bars]),
                'macd': self.calculate_macd([b['c'] for b in bars])
            }
            
            return technicals
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_relative_strength_vs_spy(self, ticker: str, start: str, end: str) -> Dict:
        """Calculate relative strength vs SPY market benchmark"""
        
        # Get both ticker and SPY data
        ticker_url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        spy_url = f"{self.base_url}/v2/aggs/ticker/SPY/range/1/day/{start}/{end}"
        params = {'apiKey': self.api_key, 'adjusted': 'true'}
        
        try:
            ticker_response = requests.get(ticker_url, params=params)
            spy_response = requests.get(spy_url, params=params)
            self.api_calls += 2
            
            if ticker_response.status_code == 200 and spy_response.status_code == 200:
                ticker_bars = ticker_response.json().get('results', [])
                spy_bars = spy_response.json().get('results', [])
                
                if len(ticker_bars) >= 20 and len(spy_bars) >= 20:
                    # Calculate returns at different intervals
                    periods = [5, 10, 20, 60]
                    relative_strength = {}
                    
                    for period in periods:
                        if len(ticker_bars) > period and len(spy_bars) > period:
                            ticker_return = (ticker_bars[-1]['c'] - ticker_bars[-period]['c']) / ticker_bars[-period]['c']
                            spy_return = (spy_bars[-1]['c'] - spy_bars[-period]['c']) / spy_bars[-period]['c']
                            
                            relative_strength[f'rs_{period}d'] = float(ticker_return - spy_return)
                            relative_strength[f'outperforming_{period}d'] = bool(ticker_return > spy_return)
                    
                    # Overall relative strength score
                    rs_values = [v for k, v in relative_strength.items() if 'rs_' in k]
                    if rs_values:
                        avg_rs = np.mean(rs_values)
                        relative_strength['avg_relative_strength'] = float(avg_rs)
                        relative_strength['consistently_strong'] = bool(avg_rs > 0)
                        relative_strength['stock_holding_better'] = bool(avg_rs > 0.05)  # 5% outperformance
                    
                    return relative_strength
                    
        except Exception as e:
            print(f"    RS error: {e}")
        
        return {'avg_relative_strength': 0.0}
    
    # ============= 3. FUNDAMENTAL DATA (The Fuel) =============
    
    def get_complete_fundamentals(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Get COMPLETE quarterly financials with all metrics"""
        
        url = f"{self.base_url}/vX/reference/financials"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'limit': 8,
            'timeframe': 'quarterly',
            'sort': 'filing_date',
            'order': 'desc',
            'filing_date.lte': catalyst_dt.strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                financials = data.get('results', [])
                
                if len(financials) >= 4:
                    # Get quarters
                    latest = financials[0].get('financials', {})
                    prior_q = financials[1].get('financials', {}) if len(financials) > 1 else {}
                    year_ago = financials[3].get('financials', {}) if len(financials) > 3 else {}
                    
                    # Income Statement
                    income = latest.get('income_statement', {})
                    prior_income = prior_q.get('income_statement', {})
                    yago_income = year_ago.get('income_statement', {})
                    
                    current_rev = float(income.get('revenues', {}).get('value', 0) or 0)
                    prior_rev = float(prior_income.get('revenues', {}).get('value', 0) or 0)
                    yago_rev = float(yago_income.get('revenues', {}).get('value', 0) or 0)
                    
                    # Growth calculations
                    qoq_growth = ((current_rev - prior_rev) / prior_rev * 100) if prior_rev > 0 else 0
                    yoy_growth = ((current_rev - yago_rev) / yago_rev * 100) if yago_rev > 0 else 0
                    
                    # Revenue acceleration
                    acceleration = 0
                    if len(financials) > 4:
                        two_q_ago = financials[2].get('financials', {}).get('income_statement', {})
                        two_q_rev = float(two_q_ago.get('revenues', {}).get('value', 0) or 0)
                        old_growth = ((prior_rev - two_q_rev) / two_q_rev * 100) if two_q_rev > 0 else 0
                        acceleration = yoy_growth - old_growth
                    
                    # Profitability
                    net_income = float(income.get('net_income_loss', {}).get('value', 0) or 0)
                    prior_net = float(prior_income.get('net_income_loss', {}).get('value', 0) or 0)
                    gross_profit = float(income.get('gross_profit', {}).get('value', 0) or 0)
                    operating_income = float(income.get('operating_income_loss', {}).get('value', 0) or 0)
                    
                    # Balance Sheet
                    balance = latest.get('balance_sheet', {})
                    cash = float(balance.get('cash_and_cash_equivalents', {}).get('value', 0) or 0)
                    total_debt = float(balance.get('long_term_debt', {}).get('value', 0) or 0)
                    total_assets = float(balance.get('assets', {}).get('value', 0) or 0)
                    
                    # Cash Flow
                    cash_flow = latest.get('cash_flow_statement', {})
                    operating_cf = float(cash_flow.get('net_cash_flow_from_operating_activities', {}).get('value', 0) or 0)
                    
                    return {
                        'has_data': True,
                        'latest_quarter': financials[0].get('filing_date'),
                        
                        # Revenue metrics
                        'revenue': current_rev,
                        'revenue_qoq_growth': float(qoq_growth),
                        'revenue_yoy_growth': float(yoy_growth),
                        'revenue_acceleration': float(acceleration),
                        'is_accelerating': bool(acceleration > 10),
                        
                        # Profitability
                        'net_income': net_income,
                        'turning_profitable': bool(net_income > 0 and prior_net <= 0),
                        'gross_margin': float(gross_profit / current_rev * 100) if current_rev > 0 else 0,
                        'operating_income': operating_income,
                        'ebitda_positive': bool(operating_income > 0),
                        
                        # Balance sheet
                        'cash': cash,
                        'total_debt': total_debt,
                        'debt_to_assets': float(total_debt / total_assets) if total_assets > 0 else 0,
                        
                        # Cash flow
                        'operating_cash_flow': operating_cf,
                        'cash_burn_rate': float(-operating_cf / 3) if operating_cf < 0 else 0,
                        'quarters_of_cash': float(cash / (-operating_cf)) if operating_cf < 0 else 999
                    }
            
        except Exception as e:
            print(f"    Fundamentals error: {e}")
        
        return {'has_data': False}
    
    # ============= 4. SMART MONEY & SQUEEZE DATA =============
    
    def get_short_interest_data(self, ticker: str, catalyst_date: str) -> Dict:
        """Get short interest data - key for squeeze detection"""
        
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        end_date = catalyst_date
        start_date = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Try different endpoints for short interest
        url = f"{self.base_url}/v2/reference/financials/stock_financial"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'period_of_report_date.gte': start_date,
            'period_of_report_date.lte': end_date,
            'limit': 10
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            # Parse short interest if available
            # Note: Actual field names may vary based on your API tier
            if response.status_code == 200:
                data = response.json().get('results', [])
                if data:
                    latest = data[0]
                    # These field names are examples - check actual API response
                    short_interest = float(latest.get('short_interest', 0) or 0)
                    shares_outstanding = float(latest.get('shares_outstanding', 0) or 0)
                    
                    short_pct = (short_interest / shares_outstanding * 100) if shares_outstanding > 0 else 0
                    
                    return {
                        'has_data': True,
                        'short_interest': short_interest,
                        'short_pct_float': short_pct,
                        'high_short_interest': bool(short_pct > 15),
                        'extreme_short_interest': bool(short_pct > 25),
                        'squeeze_potential': bool(short_pct > 15 and shares_outstanding < 50_000_000)
                    }
        
        except Exception as e:
            print(f"    Short interest error: {e}")
        
        return {'has_data': False}
    
    def get_insider_transactions(self, ticker: str, start_date: str, end_date: str) -> Dict:
        """Get insider trading activity"""
        
        # Note: Exact endpoint may vary based on API tier
        url = f"{self.base_url}/v1/reference/tickers/{ticker}/insider-transactions"
        params = {
            'apiKey': self.api_key,
            'start_date': start_date,
            'end_date': end_date,
            'limit': 100
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('results', [])
                
                buys = []
                sells = []
                
                for trans in transactions:
                    # Check transaction codes (P = Purchase, S = Sale)
                    if trans.get('transaction_code') in ['P', 'Buy', 'Purchase']:
                        buys.append({
                            'date': trans.get('filing_date'),
                            'insider': trans.get('reporting_name'),
                            'title': trans.get('officer_title', ''),
                            'shares': float(trans.get('shares', 0)),
                            'value': float(trans.get('total_value', 0))
                        })
                    elif trans.get('transaction_code') in ['S', 'Sell', 'Sale']:
                        sells.append(trans)
                
                # Analysis
                cluster_buying = len(set(b['insider'] for b in buys)) >= 3
                c_level_buying = any('CEO' in b.get('title', '') or 'CFO' in b.get('title', '') for b in buys)
                
                return {
                    'has_data': True,
                    'insider_buys': len(buys),
                    'insider_sells': len(sells),
                    'net_insider_buying': bool(len(buys) > len(sells)),
                    'cluster_buying': bool(cluster_buying),
                    'c_level_buying': bool(c_level_buying),
                    'buy_transactions': buys[:5]  # Keep top 5
                }
        
        except Exception as e:
            print(f"    Insider error: {e}")
        
        return {'has_data': False}
    
    def get_institutional_ownership(self, ticker: str, catalyst_date: str) -> Dict:
        """Get institutional ownership data"""
        
        # Note: This endpoint requires specific API tier
        # Placeholder implementation
        return {
            'has_data': False,
            'note': 'Requires specific API configuration'
        }
    
    # ============= 5. NARRATIVE DATA (The Catalyst) =============
    
    def get_complete_narrative(self, ticker: str, start: str, end: str) -> Dict:
        """Analyze news to categorize catalyst type"""
        
        url = f"{self.base_url}/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': ticker,
            'published_utc.gte': start,
            'published_utc.lte': end,
            'limit': 50,
            'sort': 'published_utc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                articles = response.json().get('results', [])
                
                # Categorize news themes
                themes = {
                    'earnings_beat': 0,
                    'fda_approval': 0,
                    'new_contract': 0,
                    'analyst_upgrade': 0,
                    'short_squeeze': 0,
                    'merger_acquisition': 0,
                    'other': 0
                }
                
                for article in articles:
                    title = (str(article.get('title', '')) + ' ' + str(article.get('description', ''))).lower()
                    
                    if 'earnings' in title or 'revenue beat' in title or 'eps beat' in title:
                        themes['earnings_beat'] += 1
                    elif 'fda' in title or 'approval' in title or 'clinical' in title:
                        themes['fda_approval'] += 1
                    elif 'contract' in title or 'partnership' in title or 'deal' in title:
                        themes['new_contract'] += 1
                    elif 'upgrade' in title or 'price target' in title or 'raised' in title:
                        themes['analyst_upgrade'] += 1
                    elif 'short' in title or 'squeeze' in title:
                        themes['short_squeeze'] += 1
                    elif 'merger' in title or 'acquisition' in title or 'buyout' in title:
                        themes['merger_acquisition'] += 1
                    else:
                        themes['other'] += 1
                
                # Determine primary catalyst
                primary_catalyst = max(themes, key=themes.get) if any(themes.values()) else 'unknown'
                
                return {
                    'news_count': len(articles),
                    'news_themes': themes,
                    'primary_catalyst': primary_catalyst,
                    'has_multiple_catalysts': bool(sum(1 for v in themes.values() if v > 0) > 1)
                }
                
        except Exception as e:
            print(f"    Narrative error: {e}")
        
        return {'primary_catalyst': 'unknown'}
    
    # ============= HELPER METHODS =============
    
    def detect_volatility_squeeze(self, bars: List[Dict]) -> Dict:
        """Detect Bollinger Band squeeze pattern"""
        
        closes = [b['c'] for b in bars[-60:]]
        
        bb_widths = []
        for i in range(20, len(closes)):
            window = closes[i-20:i]
            mean = float(np.mean(window))
            std = float(np.std(window))
            bb_width = (2 * std) / mean if mean > 0 else 0
            bb_widths.append(bb_width)
        
        if len(bb_widths) >= 20:
            recent_avg = float(np.mean(bb_widths[-10:]))
            older_avg = float(np.mean(bb_widths[-30:-20]))
            squeeze_ratio = recent_avg / older_avg if older_avg > 0 else 1.0
            
            return {
                'is_squeezing': bool(squeeze_ratio < 0.7),
                'squeeze_ratio': float(squeeze_ratio),
                'current_bb_width': float(bb_widths[-1]) if bb_widths else 0.0
            }
        
        return {'is_squeezing': False, 'squeeze_ratio': 1.0}
    
    def calculate_bb_squeeze(self, closes: List[float]) -> Dict:
        """Calculate Bollinger Band squeeze metrics"""
        
        if len(closes) < 20:
            return {'is_squeezing': False, 'bb_width': 0.0}
        
        ma20 = float(np.mean(closes[-20:]))
        std20 = float(np.std(closes[-20:]))
        bb_width = (2 * std20) / ma20 if ma20 > 0 else 0.0
        
        return {
            'is_squeezing': bool(bb_width < 0.05),
            'bb_width': float(bb_width)
        }
    
    def calculate_atr_trend(self, bars: List[Dict]) -> Dict:
        """Calculate ATR trend for volatility analysis"""
        
        if len(bars) < 14:
            return {'atr': 0.0, 'contracting': False}
        
        atrs = []
        for i in range(14, len(bars)):
            high_low = [bars[j]['h'] - bars[j]['l'] for j in range(i-14, i)]
            atr = float(np.mean(high_low))
            atrs.append(atr)
        
        if len(atrs) >= 20:
            recent = float(np.mean(atrs[-10:]))
            older = float(np.mean(atrs[-30:-20]))
            
            return {
                'atr': recent,
                'contracting': bool(recent < older * 0.8)
            }
        
        return {'atr': 0.0, 'contracting': False}
    
    def analyze_volume_trend(self, bars: List[Dict]) -> Dict:
        """Analyze volume trends"""
        
        volumes = [b['v'] for b in bars[-60:]]
        
        if len(volumes) >= 40:
            recent_avg = float(np.mean(volumes[-20:]))
            older_avg = float(np.mean(volumes[-60:-20]))
            volume_ratio = recent_avg / older_avg if older_avg > 0 else 1.0
            
            return {
                'is_drying': bool(volume_ratio < 0.7),
                'volume_ratio': float(volume_ratio),
                'avg_daily_volume': float(np.mean(volumes))
            }
        
        return {'is_drying': False, 'volume_ratio': 1.0}
    
    def is_volume_drying_up(self, bars: List[Dict]) -> bool:
        """Check if volume is decreasing over time"""
        
        if len(bars) < 40:
            return False
        
        volumes = [b['v'] for b in bars[-40:]]
        first_half = float(np.mean(volumes[:20]))
        second_half = float(np.mean(volumes[20:]))
        
        return bool(second_half < first_half * 0.7)
    
    def detect_consolidation(self, bars: List[Dict]) -> Dict:
        """Detect price consolidation pattern"""
        
        recent_bars = bars[-30:]
        if len(recent_bars) < 20:
            return {'is_consolidating': False, 'consolidation_range': 0.0, 'consolidation_score': 0.0}
        
        highs = [b['h'] for b in recent_bars]
        lows = [b['l'] for b in recent_bars]
        
        mean_low = float(np.mean(lows))
        if mean_low > 0:
            price_range = (max(highs) - min(lows)) / mean_low
        else:
            price_range = 0.0
        
        return {
            'is_consolidating': bool(price_range < 0.3),
            'consolidation_range': float(price_range),
            'consolidation_score': float(1 - price_range) if price_range < 1 else 0.0
        }
    
    def count_higher_lows(self, bars: List[Dict]) -> int:
        """Count number of higher lows"""
        
        if len(bars) < 20:
            return 0
        
        recent = bars[-20:]
        higher_lows = 0
        
        for i in range(1, len(recent)):
            if recent[i]['l'] > recent[i-1]['l']:
                higher_lows += 1
        
        return higher_lows
    
    def detect_tightening_range(self, bars: List[Dict]) -> bool:
        """Detect if price range is tightening"""
        
        if len(bars) < 40:
            return False
        
        # Compare range of first 20 days vs last 20 days
        first_range = max(b['h'] for b in bars[-40:-20]) - min(b['l'] for b in bars[-40:-20])
        last_range = max(b['h'] for b in bars[-20:]) - min(b['l'] for b in bars[-20:])
        
        return bool(last_range < first_range * 0.7)
    
    def calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        
        if len(closes) < period + 1:
            return 50.0
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = float(np.mean(gains[-period:]))
        avg_loss = float(np.mean(losses[-period:]))
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def calculate_macd(self, closes: List[float]) -> Dict:
        """Calculate MACD"""
        
        if len(closes) < 26:
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
        
        # Simple EMA calculation
        ema12 = float(np.mean(closes[-12:]))
        ema26 = float(np.mean(closes[-26:]))
        
        macd = ema12 - ema26
        signal = float(np.mean([macd]))  # Simplified
        histogram = macd - signal
        
        return {
            'macd': float(macd),
            'signal': float(signal),
            'histogram': float(histogram)
        }
    
    def analyze_price_action(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Analyze price action at multiple timeframes"""
        
        periods = {'7d': 7, '14d': 14, '30d': 30, '60d': 60, '90d': 90}
        price_action = {}
        
        for period_name, days in periods.items():
            start = (catalyst_dt - timedelta(days=days)).strftime('%Y-%m-%d')
            end = catalyst_dt.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
            params = {'apiKey': self.api_key, 'adjusted': 'true'}
            
            try:
                response = requests.get(url, params=params)
                self.api_calls += 1
                bars = response.json().get('results', [])
                
                if bars and len(bars) >= 2:
                    return_val = (bars[-1]['c'] - bars[0]['c']) / bars[0]['c'] if bars[0]['c'] > 0 else 0
                    price_action[f'return_{period_name}'] = float(return_val)
                    price_action[f'max_drawdown_{period_name}'] = float(self.calculate_max_drawdown(bars))
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
            bars = response.json().get('results', [])
            
            if len(bars) < 20:
                return {}
            
            volumes = [float(b['v']) for b in bars]
            mean_vol = float(np.mean(volumes))
            dollar_vols = [float(bars[i]['v'] * bars[i]['c']) for i in range(len(bars))]
            
            return {
                'avg_volume': float(np.mean(volumes)),
                'median_volume': float(np.median(volumes)),
                'volume_volatility': float(np.std(volumes) / mean_vol) if mean_vol > 0 else 0.0,
                'unusual_volume_days': int(sum(1 for v in volumes if v > mean_vol * 2)),
                'dry_volume_days': int(sum(1 for v in volumes if v < mean_vol * 0.5)),
                'dollar_volume_avg': float(np.mean(dollar_vols))
            }
        except:
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
    
    def calculate_max_drawdown(self, bars: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        if not bars:
            return 0.0
        
        peak = float(bars[0]['h'])
        max_dd = 0.0
        
        for bar in bars:
            peak = max(peak, float(bar['h']))
            drawdown = (peak - float(bar['l'])) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, drawdown)
        
        return float(max_dd)
    
    def calculate_all_scores(self, fingerprint: Dict) -> Dict:
        """Calculate comprehensive scores"""
        
        scores = {
            'setup_score': 0,      # Company profile (max 100)
            'coil_score': 0,       # Technical setup (max 100)
            'fuel_score': 0,       # Fundamentals (max 100)
            'squeeze_score': 0,    # Short interest (max 100)
            'catalyst_score': 0,   # News/catalyst (max 100)
            'total_score': 0
        }
        
        # Setup Score (Company Profile)
        profile = fingerprint.get('profile', {})
        if profile.get('is_ultra_low_float'):
            scores['setup_score'] += 50
        elif profile.get('is_low_float'):
            scores['setup_score'] += 30
        
        if profile.get('is_micro_cap'):
            scores['setup_score'] += 30
        elif profile.get('is_small_cap'):
            scores['setup_score'] += 20
        
        # Coil Score (Technicals)
        tech = fingerprint.get('technicals', {})
        if tech.get('volatility_contraction', {}).get('is_squeezing'):
            scores['coil_score'] += 30
        if tech.get('volume_trend', {}).get('is_drying'):
            scores['coil_score'] += 30
        if tech.get('price_consolidation', {}).get('is_consolidating'):
            scores['coil_score'] += 20
        if tech.get('price_above_ma50'):
            scores['coil_score'] += 10
        
        rs = fingerprint.get('relative_strength', {})
        if rs.get('consistently_strong'):
            scores['coil_score'] += 10
        
        # Fuel Score (Fundamentals)
        fund = fingerprint.get('fundamentals', {})
        if fund.get('is_accelerating'):
            scores['fuel_score'] += 40
        if fund.get('turning_profitable'):
            scores['fuel_score'] += 30
        if fund.get('revenue_yoy_growth', 0) > 50:
            scores['fuel_score'] += 30
        
        # Squeeze Score (Smart Money)
        short = fingerprint.get('short_interest', {})
        if short.get('extreme_short_interest'):
            scores['squeeze_score'] += 50
        elif short.get('high_short_interest'):
            scores['squeeze_score'] += 30
        
        insider = fingerprint.get('insider_transactions', {})
        if insider.get('cluster_buying'):
            scores['squeeze_score'] += 30
        elif insider.get('net_insider_buying'):
            scores['squeeze_score'] += 20
        
        # Catalyst Score
        narrative = fingerprint.get('narrative', {})
        catalyst = narrative.get('primary_catalyst', 'unknown')
        
        high_quality_catalysts = ['earnings_beat', 'fda_approval', 'merger_acquisition']
        if catalyst in high_quality_catalysts:
            scores['catalyst_score'] += 50
        elif catalyst == 'short_squeeze' and short.get('high_short_interest'):
            scores['catalyst_score'] += 70
        elif catalyst != 'unknown':
            scores['catalyst_score'] += 30
        
        scores['total_score'] = sum(v for k, v in scores.items() if k != 'total_score')
        
        return scores
    
    def clean_for_json(self, obj):
        """Convert numpy types to Python types for JSON serialization"""
        if isinstance(obj, np.bool_):
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
        """Save intermediate progress"""
        clean_data = self.clean_for_json(data)
        with open(filename, 'w') as f:
            json.dump(clean_data, f, indent=2)
    
    def save_final_analysis(self, fingerprints: List, output_file: str):
        """Save final analysis with comprehensive summary"""
        
        # Calculate detailed summary stats
        summary = {
            'total_analyzed': len(fingerprints),
            
            # Company Profile Stats
            'ultra_low_float': sum(1 for f in fingerprints if f.get('profile', {}).get('is_ultra_low_float')),
            'low_float': sum(1 for f in fingerprints if f.get('profile', {}).get('is_low_float')),
            'micro_cap': sum(1 for f in fingerprints if f.get('profile', {}).get('is_micro_cap')),
            
            # Technical Stats
            'volatility_squeeze': sum(1 for f in fingerprints if f.get('technicals', {}).get('volatility_contraction', {}).get('is_squeezing')),
            'volume_drying': sum(1 for f in fingerprints if f.get('technicals', {}).get('volume_trend', {}).get('is_drying')),
            'consolidating': sum(1 for f in fingerprints if f.get('technicals', {}).get('price_consolidation', {}).get('is_consolidating')),
            
            # Fundamental Stats
            'revenue_accelerating': sum(1 for f in fingerprints if f.get('fundamentals', {}).get('is_accelerating')),
            'turning_profitable': sum(1 for f in fingerprints if f.get('fundamentals', {}).get('turning_profitable')),
            
            # Smart Money Stats
            'high_short_interest': sum(1 for f in fingerprints if f.get('short_interest', {}).get('high_short_interest')),
            'insider_buying': sum(1 for f in fingerprints if f.get('insider_transactions', {}).get('net_insider_buying')),
            
            # Relative Strength
            'beating_spy': sum(1 for f in fingerprints if f.get('relative_strength', {}).get('consistently_strong')),
            
            # API Stats
            'api_calls_made': self.api_calls
        }
        
        # Calculate percentages
        if summary['total_analyzed'] > 0:
            total = summary['total_analyzed']
            summary['percentages'] = {
                'ultra_low_float_pct': float(summary['ultra_low_float'] / total * 100),
                'low_float_pct': float(summary['low_float'] / total * 100),
                'micro_cap_pct': float(summary['micro_cap'] / total * 100),
                'volatility_squeeze_pct': float(summary['volatility_squeeze'] / total * 100),
                'volume_drying_pct': float(summary['volume_drying'] / total * 100),
                'consolidating_pct': float(summary['consolidating'] / total * 100),
                'revenue_accelerating_pct': float(summary['revenue_accelerating'] / total * 100),
                'turning_profitable_pct': float(summary['turning_profitable'] / total * 100),
                'high_short_interest_pct': float(summary['high_short_interest'] / total * 100),
                'insider_buying_pct': float(summary['insider_buying'] / total * 100),
                'beating_spy_pct': float(summary['beating_spy'] / total * 100)
            }
        
        output = {
            'analysis_date': datetime.now().isoformat(),
            'summary': summary,
            'fingerprints': fingerprints
        }
        
        # Clean any numpy types before saving
        clean_output = self.clean_for_json(output)
        
        with open(output_file, 'w') as f:
            json.dump(clean_output, f, indent=2)
        
        print("\n" + "="*60)
        print("COMPLETE ANALYSIS FINISHED")
        print("="*60)
        print(f"Total stocks analyzed: {summary['total_analyzed']}")
        print("\nKey Findings:")
        print(f"  Ultra-low float (<20M): {summary.get('percentages', {}).get('ultra_low_float_pct', 0):.1f}%")
        print(f"  Low float (<50M): {summary.get('percentages', {}).get('low_float_pct', 0):.1f}%")
        print(f"  Volatility squeezes: {summary.get('percentages', {}).get('volatility_squeeze_pct', 0):.1f}%")
        print(f"  Volume drying up: {summary.get('percentages', {}).get('volume_drying_pct', 0):.1f}%")
        print(f"  Revenue accelerating: {summary.get('percentages', {}).get('revenue_accelerating_pct', 0):.1f}%")
        print(f"  High short interest: {summary.get('percentages', {}).get('high_short_interest_pct', 0):.1f}%")
        print(f"  Beating SPY: {summary.get('percentages', {}).get('beating_spy_pct', 0):.1f}%")
        print(f"\nResults saved to: {output_file}")

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
    
    print(f"Starting COMPLETE analysis of {input_file}")
    analyzer.collect_all_fingerprints(input_file, output_file)

if __name__ == "__main__":
    main()
