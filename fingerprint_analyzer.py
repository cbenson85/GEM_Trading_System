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
        
    def build_complete_fingerprint(self, explosion: Dict) -> Dict:
        """Build fingerprint with ALL available Polygon data"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Time windows
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        t_plus_5 = (catalyst_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        
        print(f"  Collecting ALL available data for {ticker}...")
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_metrics': explosion,
            
            # ✅ AVAILABLE FROM POLYGON
            'profile': self.get_ticker_details(ticker, t_minus_120),
            'technicals': self.get_technical_analysis(ticker, t_minus_120, catalyst_date),
            'fundamentals': self.get_stock_financials(ticker, catalyst_dt),
            'short_interest': self.get_short_interest(ticker, catalyst_date),  # NEW!
            'options_activity': self.get_unusual_options_activity(ticker, catalyst_dt),  # NEW!
            'dividends': self.get_dividends(ticker, t_minus_120, catalyst_date),
            'splits': self.get_stock_splits(ticker, t_minus_120, catalyst_date),
            'news': self.get_news_analysis(ticker, t_minus_30, t_plus_5),
            'relative_strength': self.calculate_relative_strength(ticker, t_minus_120, catalyst_date),
            'snapshot': self.get_ticker_snapshot(ticker),
            
            # ❌ NOT AVAILABLE (would need sec-api.io or similar)
            'insider_transactions': {'available': False, 'note': 'Requires separate SEC API'},
            'institutional_ownership': {'available': False, 'note': 'Requires separate 13F API'}
        }
        
        fingerprint['scores'] = self.calculate_scores(fingerprint)
        return fingerprint
    
    # ============= SHORT INTEREST (NEW!) =============
    
    def get_short_interest(self, ticker: str, catalyst_date: str) -> Dict:
        """Get short interest data - CRITICAL for squeeze detection"""
        
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        end_date = catalyst_date
        start_date = (catalyst_dt - timedelta(days=180)).strftime('%Y-%m-%d')
        
        # Correct endpoint for short interest
        url = f"{self.base_url}/vX/reference/financials/stock_financials"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'type': 'short_interest',
            'filing_date.gte': start_date,
            'filing_date.lte': end_date,
            'limit': 12,  # Get 6 months of bi-monthly data
            'sort': 'filing_date',
            'order': 'desc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    latest = results[0]
                    
                    # Extract key metrics
                    short_interest = float(latest.get('short_interest', 0))
                    avg_daily_volume = float(latest.get('avg_daily_volume', 0))
                    days_to_cover = float(latest.get('days_to_cover', 0))
                    settlement_date = latest.get('settlement_date', '')
                    
                    # Calculate trends if we have historical data
                    short_increasing = False
                    if len(results) >= 3:
                        recent = results[0].get('short_interest', 0)
                        older = results[2].get('short_interest', 0)
                        short_increasing = recent > older * 1.1  # 10% increase
                    
                    # Get shares outstanding to calculate short % of float
                    profile = self.get_ticker_details(ticker, catalyst_date)
                    shares_outstanding = profile.get('shares_outstanding', 0)
                    
                    short_pct_float = (short_interest / shares_outstanding * 100) if shares_outstanding > 0 else 0
                    
                    return {
                        'has_data': True,
                        'settlement_date': settlement_date,
                        'short_interest': short_interest,
                        'avg_daily_volume': avg_daily_volume,
                        'days_to_cover': days_to_cover,
                        'short_pct_float': float(short_pct_float),
                        'high_short_interest': bool(short_pct_float > 15),
                        'extreme_short_interest': bool(short_pct_float > 25),
                        'short_increasing': bool(short_increasing),
                        'squeeze_setup': bool(short_pct_float > 15 and days_to_cover > 3),
                        'historical_data': results[:6] if len(results) > 1 else []
                    }
            
        except Exception as e:
            print(f"    Short interest error: {e}")
        
        return {'has_data': False}
    
    # ============= OPTIONS ACTIVITY (NEW!) =============
    
    def get_unusual_options_activity(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Detect unusual options activity"""
        
        catalyst_date = catalyst_dt.strftime('%Y-%m-%d')
        
        # Get options chain snapshot
        snapshot_url = f"{self.base_url}/v3/snapshot/options/{ticker}"
        params = {
            'apiKey': self.api_key,
            'strike_price.gte': 1,
            'limit': 250
        }
        
        try:
            response = requests.get(snapshot_url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                contracts = data.get('results', [])
                
                unusual_activity = []
                total_call_volume = 0
                total_put_volume = 0
                total_call_oi = 0
                total_put_oi = 0
                
                for contract in contracts:
                    details = contract.get('details', {})
                    day = contract.get('day', {})
                    
                    contract_type = details.get('contract_type', '')
                    volume = day.get('volume', 0)
                    open_interest = contract.get('open_interest', 0)
                    strike = details.get('strike_price', 0)
                    expiration = details.get('expiration_date', '')
                    
                    # Track totals
                    if contract_type == 'call':
                        total_call_volume += volume
                        total_call_oi += open_interest
                    else:
                        total_put_volume += volume
                        total_put_oi += open_interest
                    
                    # Flag unusual activity (volume > open interest)
                    if volume > 0 and open_interest > 0:
                        vol_oi_ratio = volume / open_interest
                        if vol_oi_ratio > 1.5:  # Volume 50% higher than OI
                            unusual_activity.append({
                                'strike': strike,
                                'type': contract_type,
                                'expiration': expiration,
                                'volume': volume,
                                'open_interest': open_interest,
                                'vol_oi_ratio': vol_oi_ratio
                            })
                
                # Calculate put/call ratios
                put_call_ratio = (total_put_volume / total_call_volume) if total_call_volume > 0 else 0
                
                # Sort unusual activity by vol/oi ratio
                unusual_activity.sort(key=lambda x: x['vol_oi_ratio'], reverse=True)
                
                return {
                    'has_data': True,
                    'total_call_volume': total_call_volume,
                    'total_put_volume': total_put_volume,
                    'put_call_ratio': float(put_call_ratio),
                    'bullish_sentiment': bool(put_call_ratio < 0.7),  # Low P/C = bullish
                    'unusual_activity_count': len(unusual_activity),
                    'has_unusual_activity': bool(len(unusual_activity) > 5),
                    'top_unusual': unusual_activity[:10]  # Top 10 unusual trades
                }
            
        except Exception as e:
            print(f"    Options error: {e}")
        
        return {'has_data': False}
    
    # ============= DIVIDENDS & SPLITS =============
    
    def get_dividends(self, ticker: str, start: str, end: str) -> Dict:
        """Get dividend history"""
        
        url = f"{self.base_url}/v3/reference/dividends"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'ex_dividend_date.gte': start,
            'ex_dividend_date.lte': end,
            'limit': 10
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                dividends = data.get('results', [])
                
                if dividends:
                    total_dividends = sum(d.get('cash_amount', 0) for d in dividends)
                    return {
                        'has_dividends': True,
                        'dividend_count': len(dividends),
                        'total_paid': total_dividends,
                        'recent_dividend': dividends[0] if dividends else None
                    }
        except:
            pass
        
        return {'has_dividends': False}
    
    def get_stock_splits(self, ticker: str, start: str, end: str) -> Dict:
        """Get stock split history"""
        
        url = f"{self.base_url}/v3/reference/splits"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'execution_date.gte': start,
            'execution_date.lte': end
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                splits = data.get('results', [])
                
                if splits:
                    return {
                        'has_splits': True,
                        'split_count': len(splits),
                        'splits': splits
                    }
        except:
            pass
        
        return {'has_splits': False}
    
    # ============= ENHANCED FINANCIALS =============
    
    def get_stock_financials(self, ticker: str, as_of_date: datetime) -> Dict:
        """Get comprehensive financials with ALL available metrics"""
        
        url = f"{self.base_url}/vX/reference/financials"
        params = {
            'ticker': ticker,
            'apiKey': self.api_key,
            'timeframe': 'quarterly',
            'limit': 10,
            'sort': 'filing_date',
            'order': 'desc'
        }
        
        try:
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                
                if len(results) >= 4:
                    # Get all available quarters
                    q0 = results[0].get('financials', {})
                    q1 = results[1].get('financials', {}) if len(results) > 1 else {}
                    q4 = results[4].get('financials', {}) if len(results) > 4 else {}
                    
                    # Extract EVERYTHING available
                    income = q0.get('income_statement', {})
                    balance = q0.get('balance_sheet', {})
                    cash_flow = q0.get('cash_flow_statement', {})
                    
                    # Income Statement - Get ALL fields
                    revenues = float(income.get('revenues', {}).get('value', 0) or 0)
                    gross_profit = float(income.get('gross_profit', {}).get('value', 0) or 0)
                    operating_income = float(income.get('operating_income_loss', {}).get('value', 0) or 0)
                    net_income = float(income.get('net_income_loss', {}).get('value', 0) or 0)
                    eps_basic = float(income.get('basic_earnings_per_share', {}).get('value', 0) or 0)
                    eps_diluted = float(income.get('diluted_earnings_per_share', {}).get('value', 0) or 0)
                    
                    # Balance Sheet - Get ALL fields
                    total_assets = float(balance.get('assets', {}).get('value', 0) or 0)
                    current_assets = float(balance.get('current_assets', {}).get('value', 0) or 0)
                    cash = float(balance.get('cash_and_cash_equivalents', {}).get('value', 0) or 0)
                    total_liabilities = float(balance.get('liabilities', {}).get('value', 0) or 0)
                    current_liabilities = float(balance.get('current_liabilities', {}).get('value', 0) or 0)
                    long_term_debt = float(balance.get('long_term_debt', {}).get('value', 0) or 0)
                    total_equity = float(balance.get('equity', {}).get('value', 0) or 0)
                    
                    # Cash Flow - Get ALL fields  
                    operating_cf = float(cash_flow.get('net_cash_flow_from_operating_activities', {}).get('value', 0) or 0)
                    investing_cf = float(cash_flow.get('net_cash_flow_from_investing_activities', {}).get('value', 0) or 0)
                    financing_cf = float(cash_flow.get('net_cash_flow_from_financing_activities', {}).get('value', 0) or 0)
                    free_cash_flow = operating_cf + investing_cf  # Approximation
                    
                    # Calculate ALL key ratios
                    current_ratio = (current_assets / current_liabilities) if current_liabilities > 0 else 0
                    debt_to_equity = (long_term_debt / total_equity) if total_equity > 0 else 0
                    gross_margin = (gross_profit / revenues * 100) if revenues > 0 else 0
                    operating_margin = (operating_income / revenues * 100) if revenues > 0 else 0
                    net_margin = (net_income / revenues * 100) if revenues > 0 else 0
                    roe = (net_income / total_equity * 100) if total_equity > 0 else 0
                    roa = (net_income / total_assets * 100) if total_assets > 0 else 0
                    
                    # Growth calculations (comparing quarters)
                    prior_revenues = float(q1.get('income_statement', {}).get('revenues', {}).get('value', 0) or 0)
                    yago_revenues = float(q4.get('income_statement', {}).get('revenues', {}).get('value', 0) or 0)
                    
                    qoq_growth = ((revenues - prior_revenues) / prior_revenues * 100) if prior_revenues > 0 else 0
                    yoy_growth = ((revenues - yago_revenues) / yago_revenues * 100) if yago_revenues > 0 else 0
                    
                    return {
                        'has_data': True,
                        'filing_date': results[0].get('filing_date'),
                        
                        # Income Statement
                        'revenue': revenues,
                        'gross_profit': gross_profit,
                        'operating_income': operating_income,
                        'net_income': net_income,
                        'eps_basic': eps_basic,
                        'eps_diluted': eps_diluted,
                        
                        # Balance Sheet
                        'total_assets': total_assets,
                        'current_assets': current_assets,
                        'cash': cash,
                        'total_liabilities': total_liabilities,
                        'current_liabilities': current_liabilities,
                        'long_term_debt': long_term_debt,
                        'total_equity': total_equity,
                        
                        # Cash Flow
                        'operating_cash_flow': operating_cf,
                        'investing_cash_flow': investing_cf,
                        'financing_cash_flow': financing_cf,
                        'free_cash_flow': free_cash_flow,
                        
                        # Ratios
                        'current_ratio': float(current_ratio),
                        'debt_to_equity': float(debt_to_equity),
                        'gross_margin': float(gross_margin),
                        'operating_margin': float(operating_margin),
                        'net_margin': float(net_margin),
                        'roe': float(roe),
                        'roa': float(roa),
                        
                        # Growth
                        'revenue_qoq_growth': float(qoq_growth),
                        'revenue_yoy_growth': float(yoy_growth),
                        'is_accelerating': bool(yoy_growth > 50),
                        'is_profitable': bool(net_income > 0),
                        'turning_profitable': bool(net_income > 0 and q1.get('income_statement', {}).get('net_income_loss', {}).get('value', 0) <= 0),
                        
                        # Quality metrics
                        'quality_of_earnings': float(operating_cf / net_income) if net_income > 0 else 0,
                        'cash_burn_rate': float(-operating_cf / 3) if operating_cf < 0 else 0,
                        'quarters_of_cash': float(cash / (-operating_cf)) if operating_cf < 0 else 999
                    }
            
        except Exception as e:
            print(f"    Financials error: {e}")
        
        return {'has_data': False}
    
    # [Include all other methods from before - technicals, news, etc.]
    
    def calculate_scores(self, fingerprint: Dict) -> Dict:
        """Calculate comprehensive scores including new data"""
        
        scores = {
            'setup_score': 0,      # Company profile
            'technical_score': 0,  # Technical patterns
            'fundamental_score': 0, # Financials
            'squeeze_score': 0,    # Short interest
            'options_score': 0,    # Options activity
            'catalyst_score': 0,   # News
            'total_score': 0
        }
        
        # Setup Score (Profile)
        profile = fingerprint.get('profile', {})
        if profile.get('is_ultra_low_float'):
            scores['setup_score'] += 50
        elif profile.get('is_low_float'):
            scores['setup_score'] += 30
        if profile.get('is_micro_cap'):
            scores['setup_score'] += 30
        
        # Squeeze Score (Short Interest) - NEW!
        short = fingerprint.get('short_interest', {})
        if short.get('extreme_short_interest'):
            scores['squeeze_score'] += 50
        elif short.get('high_short_interest'):
            scores['squeeze_score'] += 30
        if short.get('days_to_cover', 0) > 5:
            scores['squeeze_score'] += 30
        elif short.get('days_to_cover', 0) > 3:
            scores['squeeze_score'] += 20
        if short.get('short_increasing'):
            scores['squeeze_score'] += 20
        
        # Options Score - NEW!
        options = fingerprint.get('options_activity', {})
        if options.get('has_unusual_activity'):
            scores['options_score'] += 50
        if options.get('bullish_sentiment'):
            scores['options_score'] += 30
        if options.get('unusual_activity_count', 0) > 10:
            scores['options_score'] += 20
        
        # [Add other scoring logic]
        
        scores['total_score'] = sum(v for k, v in scores.items() if k != 'total_score')
        
        return scores
