import json
import os
import time
import requests
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional
from polygon import RESTClient

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')

class PreCatalystFingerprint:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.polygon_client = RESTClient(api_key)
        self.api_calls = 0
        
    def collect_all_fingerprints(self, input_file: str, output_file: str):
        """Main method to collect ALL 9 fingerprint categories"""
        
        print("="*60)
        print("COMPLETE PRE-CATALYST FINGERPRINT COLLECTION")
        print("ALL 9 DATA CATEGORIES - ADVANCED TIER")
        print("="*60)
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        explosions = data['discoveries']
        print(f"Found {len(explosions)} explosions to analyze")
        print(f"Collecting: Profile, Technicals, Fundamentals, Relative Strength,")
        print(f"            News, Price Patterns, Volume Profile, SHORT INTEREST,")
        print(f"            OPTIONS ACTIVITY, INTRADAY DATA")
        print("="*60)
        
        fingerprints = []
        
        for i, explosion in enumerate(explosions):
            print(f"\n[{i+1}/{len(explosions)}] Processing {explosion['ticker']}...")
            
            try:
                fingerprint = self.build_complete_fingerprint(explosion)
                fingerprints.append(fingerprint)
                
                if (i + 1) % 10 == 0:
                    self.save_progress(fingerprints, 'fingerprints_progress.json')
                    print(f"  Saved progress: {len(fingerprints)} complete")
                
                time.sleep(0.15)  # Rate limiting
                
            except Exception as e:
                print(f"  Error: {e}")
                fingerprints.append({
                    'ticker': explosion['ticker'],
                    'error': str(e),
                    'explosion_data': explosion
                })
        
        self.save_final_analysis(fingerprints, output_file)
    
    def build_complete_fingerprint(self, explosion: Dict) -> Dict:
        """Build complete fingerprint with ALL 9 Advanced tier data categories"""
        
        ticker = explosion['ticker']
        catalyst_date = explosion['catalyst_date']
        catalyst_dt = datetime.strptime(catalyst_date, '%Y-%m-%d')
        
        # Time windows
        t_minus_120 = (catalyst_dt - timedelta(days=120)).strftime('%Y-%m-%d')
        t_minus_90 = (catalyst_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        t_minus_30 = (catalyst_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        t_minus_3 = (catalyst_dt - timedelta(days=3)).strftime('%Y-%m-%d')
        t_plus_3 = (catalyst_dt + timedelta(days=3)).strftime('%Y-%m-%d')
        t_plus_5 = (catalyst_dt + timedelta(days=5)).strftime('%Y-%m-%d')
        
        print(f"  Collecting ALL 9 data categories for {ticker}...")
        
        fingerprint = {
            'ticker': ticker,
            'catalyst_date': catalyst_date,
            'explosion_metrics': {
                'gain_pct': float(explosion['gain_pct']),
                'volume_spike': str(explosion['volume_spike']),
                'exit_quality': explosion.get('exit_quality', 'unknown')
            },
            
            # ALL 9 DATA CATEGORIES
            '1_profile': self.get_ticker_details_advanced(ticker, t_minus_120),
            '2_technicals': self.get_technical_analysis(ticker, t_minus_120, catalyst_date),
            '3_fundamentals': self.get_stock_financials_advanced(ticker, catalyst_dt),
            '4_relative_strength': self.calculate_relative_strength(ticker, t_minus_120, catalyst_date),
            '5_news': self.get_news_analysis(ticker, t_minus_30, t_plus_5),
            '6_price_patterns': self.analyze_price_patterns(ticker, catalyst_dt),
            '7_volume_profile': self.analyze_volume_profile(ticker, t_minus_120, catalyst_date),
            
            # MISSING CATEGORIES NOW ADDED:
            '8_short_interest': self.get_short_interest(ticker, catalyst_dt),
            '9_options_activity': self.get_options_activity(ticker, catalyst_dt),
            '10_intraday_data': self.get_intraday_data(ticker, t_minus_3, t_plus_3)
        }
        
        fingerprint['scores'] = self.calculate_all_scores(fingerprint)
        
        return fingerprint
    
    def get_short_interest(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Get short interest data using Polygon client"""
        
        print(f"    Getting short interest...")
        
        try:
            # Get 24 bi-monthly reports (1 year of data)
            short_reports = []
            
            for report in self.polygon_client.list_short_interest(
                ticker=ticker,
                limit=24
            ):
                self.api_calls += 1
                
                report_date = datetime.strptime(report.date_key, '%Y-%m-%d')
                days_from_catalyst = (catalyst_dt - report_date).days
                
                short_reports.append({
                    'date': report.date_key,
                    'short_interest': float(report.short_interest) if report.short_interest else 0,
                    'days_to_cover': float(report.days_to_cover) if report.days_to_cover else 0,
                    'days_from_catalyst': days_from_catalyst
                })
                
                # Only get reports up to catalyst date
                if days_from_catalyst < -90:
                    break
            
            if len(short_reports) >= 2:
                # Find reports closest to catalyst
                pre_catalyst = [r for r in short_reports if r['days_from_catalyst'] >= 0]
                
                if pre_catalyst:
                    recent = pre_catalyst[0]
                    older = pre_catalyst[-1] if len(pre_catalyst) > 1 else pre_catalyst[0]
                    
                    # Calculate changes
                    si_change = 0
                    if older['short_interest'] > 0:
                        si_change = ((recent['short_interest'] - older['short_interest']) / 
                                   older['short_interest'] * 100)
                    
                    # Check for squeeze setup
                    is_squeeze_setup = (
                        recent['days_to_cover'] > 3 and 
                        recent['short_interest'] > 0
                    )
                    
                    return {
                        'has_data': True,
                        'recent_short_interest': recent['short_interest'],
                        'recent_days_to_cover': recent['days_to_cover'],
                        'short_interest_change_pct': float(si_change),
                        'is_heavily_shorted': recent['days_to_cover'] > 5,
                        'is_squeeze_setup': is_squeeze_setup,
                        'reports_analyzed': len(pre_catalyst)
                    }
            
        except Exception as e:
            print(f"      Short interest error: {e}")
        
        return {'has_data': False}
    
    def get_options_activity(self, ticker: str, catalyst_dt: datetime) -> Dict:
        """Get options activity data"""
        
        print(f"    Getting options activity...")
        
        try:
            # Get options snapshot for catalyst date
            catalyst_str = catalyst_dt.strftime('%Y-%m-%d')
            
            # Try to get options chain
            url = f"{self.base_url}/v3/snapshot/options/{ticker}"
            params = {
                'apiKey': self.api_key,
                'limit': 250
            }
            
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Analyze options data
                    total_volume = sum(r.get('day', {}).get('volume', 0) for r in results)
                    total_oi = sum(r.get('open_interest', 0) for r in results)
                    
                    calls = [r for r in results if r.get('details', {}).get('contract_type') == 'call']
                    puts = [r for r in results if r.get('details', {}).get('contract_type') == 'put']
                    
                    call_volume = sum(c.get('day', {}).get('volume', 0) for c in calls)
                    put_volume = sum(p.get('day', {}).get('volume', 0) for p in puts)
                    
                    call_oi = sum(c.get('open_interest', 0) for c in calls)
                    put_oi = sum(p.get('open_interest', 0) for p in puts)
                    
                    # Calculate ratios
                    put_call_ratio = 0
                    if call_volume > 0:
                        put_call_ratio = put_volume / call_volume
                    
                    # Look for unusual activity
                    high_volume_strikes = [
                        r for r in results 
                        if r.get('day', {}).get('volume', 0) > total_volume / len(results) * 3
                    ]
                    
                    return {
                        'has_data': True,
                        'total_volume': int(total_volume),
                        'total_open_interest': int(total_oi),
                        'call_volume': int(call_volume),
                        'put_volume': int(put_volume),
                        'put_call_ratio': float(put_call_ratio),
                        'call_oi': int(call_oi),
                        'put_oi': int(put_oi),
                        'unusual_strikes': len(high_volume_strikes),
                        'bullish_flow': call_volume > put_volume * 2,
                        'contracts_analyzed': len(results)
                    }
                    
        except Exception as e:
            print(f"      Options error: {e}")
        
        return {'has_data': False}
    
    def get_intraday_data(self, ticker: str, start: str, end: str) -> Dict:
        """Get intraday 5-minute data around catalyst"""
        
        print(f"    Getting intraday data...")
        
        try:
            # Get 5-minute bars
            url = f"{self.base_url}/v2/aggs/ticker/{ticker}/range/5/minute/{start}/{end}"
            params = {
                'apiKey': self.api_key,
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 50000
            }
            
            response = requests.get(url, params=params)
            self.api_calls += 1
            
            if response.status_code == 200:
                bars = response.json().get('results', [])
                
                if len(bars) > 100:
                    # Analyze intraday patterns
                    volumes = [b['v'] for b in bars]
                    highs = [b['h'] for b in bars]
                    lows = [b['l'] for b in bars]
                    closes = [b['c'] for b in bars]
                    
                    # Calculate intraday volatility
                    avg_range = np.mean([(h - l) / l for h, l in zip(highs, lows) if l > 0])
                    
                    # Find volume spikes
                    mean_vol = np.mean(volumes)
                    volume_spikes = sum(1 for v in volumes if v > mean_vol * 3)
                    
                    # Detect gaps
                    gaps = []
                    for i in range(1, len(bars)):
                        prev_close = bars[i-1]['c']
                        curr_open = bars[i]['o']
                        gap_pct = (curr_open - prev_close) / prev_close if prev_close > 0 else 0
                        if abs(gap_pct) > 0.02:  # 2% gap
                            gaps.append(gap_pct)
                    
                    # Early morning activity (first 2 hours)
                    morning_bars = bars[:24]  # 24 * 5min = 2 hours
                    morning_vol = sum(b['v'] for b in morning_bars)
                    
                    return {
                        'has_data': True,
                        'total_bars': len(bars),
                        'avg_intraday_range_pct': float(avg_range * 100),
                        'volume_spikes_count': int(volume_spikes),
                        'gap_count': len(gaps),
                        'largest_gap_pct': float(max(gaps) * 100) if gaps else 0,
                        'morning_volume_ratio': float(morning_vol / sum(volumes)) if sum(volumes) > 0 else 0,
                        'high_volatility': avg_range > 0.03,
                        'unusual_early_activity': morning_vol > sum(volumes) * 0.4
                    }
                    
        except Exception as e:
            print(f"      Intraday error: {e}")
        
        return {'has_data': False}
    
    # [Previous methods remain the same - get_ticker_details_advanced, get_price_at_date, 
    # get_stock_financials_advanced, get_technical_analysis, detect_bb_squeeze, 
    # analyze_volume_trend_detailed, detect_consolidation_pattern, calculate_volatility_rank,
    # calculate_rsi, calculate_relative_strength, get_news_analysis, analyze_price_patterns,
    # analyze_volume_profile, categorize_float]
    
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
        """Calculate composite scores including new data"""
        
        scores = {
            'setup_score': 0,
            'technical_score': 0,
            'fundamental_score': 0,
            'catalyst_score': 0,
            'squeeze_score': 0,  # NEW
            'options_score': 0,  # NEW
            'total_score': 0
        }
        
        # Setup Score
        profile = fingerprint.get('1_profile', {})
        if profile.get('is_ultra_low_float'):
            scores['setup_score'] += 50
        elif profile.get('is_low_float'):
            scores['setup_score'] += 30
        if profile.get('is_micro_cap'):
            scores['setup_score'] += 30
        
        # Technical Score
        tech = fingerprint.get('2_technicals', {})
        if tech.get('bb_squeeze', {}).get('is_squeezing'):
            scores['technical_score'] += 40
        if tech.get('volume_trend', {}).get('is_drying'):
            scores['technical_score'] += 30
        if tech.get('consolidation', {}).get('is_consolidating'):
            scores['technical_score'] += 30
        
        # Fundamental Score
        fund = fingerprint.get('3_fundamentals', {})
        if fund.get('is_accelerating'):
            scores['fundamental_score'] += 50
        if fund.get('turning_profitable'):
            scores['fundamental_score'] += 50
        
        # Catalyst Score
        news = fingerprint.get('5_news', {})
        if news.get('primary_catalyst') in ['earnings', 'fda_approval', 'merger']:
            scores['catalyst_score'] += 50
        
        # NEW: Squeeze Score (short interest)
        short = fingerprint.get('8_short_interest', {})
        if short.get('is_squeeze_setup'):
            scores['squeeze_score'] += 50
        if short.get('is_heavily_shorted'):
            scores['squeeze_score'] += 30
        
        # NEW: Options Score
        options = fingerprint.get('9_options_activity', {})
        if options.get('bullish_flow'):
            scores['options_score'] += 40
        if options.get('unusual_strikes', 0) > 3:
            scores['options_score'] += 30
        
        # Intraday bonus
        intraday = fingerprint.get('10_intraday_data', {})
        if intraday.get('unusual_early_activity'):
            scores['technical_score'] += 20
        
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
        """Save final analysis with all data categories"""
        
        summary = {
            'total_analyzed': len(fingerprints),
            'data_categories_collected': 10,  # All 9 + intraday
            
            # Profile stats
            'ultra_low_float': sum(1 for f in fingerprints if f.get('1_profile', {}).get('is_ultra_low_float')),
            'low_float': sum(1 for f in fingerprints if f.get('1_profile', {}).get('is_low_float')),
            
            # Technical stats
            'bb_squeeze': sum(1 for f in fingerprints if f.get('2_technicals', {}).get('bb_squeeze', {}).get('is_squeezing')),
            'volume_drying': sum(1 for f in fingerprints if f.get('2_technicals', {}).get('volume_trend', {}).get('is_drying')),
            
            # Fundamental stats
            'has_financials': sum(1 for f in fingerprints if f.get('3_fundamentals', {}).get('has_data')),
            
            # NEW: Short interest stats
            'has_short_data': sum(1 for f in fingerprints if f.get('8_short_interest', {}).get('has_data')),
            'squeeze_setups': sum(1 for f in fingerprints if f.get('8_short_interest', {}).get('is_squeeze_setup')),
            
            # NEW: Options stats
            'has_options_data': sum(1 for f in fingerprints if f.get('9_options_activity', {}).get('has_data')),
            'bullish_options_flow': sum(1 for f in fingerprints if f.get('9_options_activity', {}).get('bullish_flow')),
            
            # NEW: Intraday stats
            'has_intraday_data': sum(1 for f in fingerprints if f.get('10_intraday_data', {}).get('has_data')),
            'unusual_intraday': sum(1 for f in fingerprints if f.get('10_intraday_data', {}).get('unusual_early_activity')),
            
            'api_calls': self.api_calls
        }
        
        if summary['total_analyzed'] > 0:
            total = summary['total_analyzed']
            summary['percentages'] = {
                'ultra_low_float_pct': (summary['ultra_low_float'] / total * 100),
                'low_float_pct': (summary['low_float'] / total * 100),
                'bb_squeeze_pct': (summary['bb_squeeze'] / total * 100),
                'volume_drying_pct': (summary['volume_drying'] / total * 100),
                'short_data_coverage': (summary['has_short_data'] / total * 100),
                'options_data_coverage': (summary['has_options_data'] / total * 100),
                'intraday_data_coverage': (summary['has_intraday_data'] / total * 100),
                'squeeze_setup_pct': (summary['squeeze_setups'] / total * 100)
            }
        
        output = {
            'analysis_date': datetime.now().isoformat(),
            'api_tier': 'Advanced - Complete',
            'data_categories': [
                'Company Profile',
                'Technical History', 
                'Fundamentals',
                'Relative Strength',
                'News Analysis',
                'Price Patterns',
                'Volume Profile',
                'SHORT INTEREST',
                'OPTIONS ACTIVITY',
                'INTRADAY DATA'
            ],
            'summary': summary,
            'fingerprints': fingerprints
        }
        
        clean_output = self.clean_for_json(output)
        
        with open(output_file, 'w') as f:
            json.dump(clean_output, f, indent=2)
        
        print("\n" + "="*60)
        print("COMPLETE ANALYSIS FINISHED")
        print("="*60)
        print(f"Total analyzed: {summary['total_analyzed']}")
        print(f"\nData Coverage:")
        if 'percentages' in summary:
            print(f"  Short Interest: {summary['percentages']['short_data_coverage']:.1f}%")
            print(f"  Options Data: {summary['percentages']['options_data_coverage']:.1f}%")
            print(f"  Intraday Data: {summary['percentages']['intraday_data_coverage']:.1f}%")
            print(f"\nKey Patterns:")
            print(f"  Ultra-low float: {summary['percentages']['ultra_low_float_pct']:.1f}%")
            print(f"  BB Squeeze: {summary['percentages']['bb_squeeze_pct']:.1f}%")
            print(f"  Short squeeze setups: {summary['percentages']['squeeze_setup_pct']:.1f}%")
        print(f"\nAPI calls: {summary['api_calls']}")
        print(f"Saved to: {output_file}")

def main():
    if not POLYGON_API_KEY:
        print("ERROR: POLYGON_API_KEY not set!")
        return
    
    analyzer = PreCatalystFingerprint(POLYGON_API_KEY)
    
    input_file = 'CLEAN_EXPLOSIONS.json'
    output_file = 'FINGERPRINTS.json'
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file {input_file} not found!")
        return
    
    print(f"Starting COMPLETE Advanced Tier analysis...")
    print(f"Collecting ALL 10 data categories...")
    analyzer.collect_all_fingerprints(input_file, output_file)

if __name__ == "__main__":
    main()
