#!/usr/bin/env python3
"""
GEM Trading System - Realistic Sustainability Filter
Version: 4.0
Created: 2025-11-02

PURPOSE:
Filter stocks based on exit window tradeability using "Total Days Above 200%" method.

KEY CHANGES FROM V3.0:
- Don't test sustained consecutive days (too strict)
- Count TOTAL days (not consecutive) above 200% gain
- Focus: "Did stock give me at least 14 days to exit with 200%+ profit?"
- Handles normal volatility and multiple run-ups

CRITERIA:
1. TRADEABLE: Stock was above 200% gain for at least 14 total days
2. NOT PUMP-AND-DUMP: Brief spikes that crash immediately are filtered out
3. EXIT WINDOW: Had sufficient time to notice and exit with profit

METHOD:
- Load daily price data from entry to peak + 60 days
- Calculate gain % from entry each day
- Count total days above 200% threshold (not consecutive)
- PASS if >= 14 days above 200%
- FAIL if < 14 days (pump-and-dump)

INPUT: explosive_stocks_CLEAN.json (with enriched data)
OUTPUT:
  - explosive_stocks_CLEAN.json (sustainable winners only)
  - explosive_stocks_UNSUSTAINABLE.json (pump & dumps filtered out)
  - sustained_gain_summary.json (statistics)
"""

import json
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import time

# Configuration
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'pvv6DNmKAoxojCc0B5HOaji6I_k1egv0')
DATA_DIR = "Verified_Backtest_Data"
INPUT_FILE = f"{DATA_DIR}/explosive_stocks_CLEAN.json"
OUTPUT_UNSUSTAINABLE = f"{DATA_DIR}/explosive_stocks_UNSUSTAINABLE.json"
SUMMARY_FILE = f"{DATA_DIR}/sustained_gain_summary.json"

# Filter thresholds
GAIN_THRESHOLD_PCT = 200.0  # 200% gain = 3x from entry
MIN_DAYS_ABOVE_THRESHOLD = 14  # Need at least 14 days above 200%

class SustainabilityFilter:
    """Filter stocks based on exit window - Total Days Above 200% method"""
    
    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.api_calls = 0
        self.stats = {
            "filter_version": "4.0",
            "filter_method": "Total Days Above 200% Threshold",
            "test_method": "Exit Window Analysis (Total Days)",
            "filter_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "threshold_gain_pct": GAIN_THRESHOLD_PCT,
            "min_days_required": MIN_DAYS_ABOVE_THRESHOLD,
            "total_stocks": 0,
            "sustainable": 0,
            "unsustainable": 0,
            "not_tested": 0,
            "api_calls": 0,
            "errors": []
        }
    
    def load_catalog(self) -> tuple:
        """Load stocks from CLEAN.json"""
        try:
            with open(INPUT_FILE, 'r') as f:
                data = json.load(f)
                
            # Handle both structures
            if isinstance(data, dict) and 'stocks' in data:
                stocks = data['stocks']
                file_structure = {k: v for k, v in data.items() if k != 'stocks'}
            else:
                stocks = data
                file_structure = {}
            
            self.stats['total_stocks'] = len(stocks)
            return stocks, file_structure
            
        except FileNotFoundError:
            print(f"❌ Error: {INPUT_FILE} not found")
            return [], {}
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {INPUT_FILE}: {e}")
            return [], {}
    
    def get_price_data(self, ticker: str, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """Fetch daily price data from Polygon API"""
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results']
                else:
                    return None
            elif response.status_code == 429:
                print(f"⚠️  Rate limit hit for {ticker}, waiting 60s...")
                time.sleep(60)
                return self.get_price_data(ticker, start_date, end_date)
            else:
                return None
                
        except Exception as e:
            error_msg = f"API error for {ticker}: {str(e)}"
            print(f"⚠️  {error_msg}")
            self.stats['errors'].append(error_msg)
            return None
    
    def calculate_exit_window(self, stock: Dict) -> Optional[Dict]:
        """
        Calculate exit window analysis for a stock
        
        Returns dict with:
        - total_days_above_threshold: Total days above 200% gain
        - max_gain_observed: Highest gain achieved
        - first_cross_date: When it first crossed 200%
        - last_above_date: Last date above 200%
        - tradeable: True if >= 14 days above 200%
        - reason: Human-readable explanation
        """
        ticker = stock.get('ticker')
        entry_date = stock.get('entry_date')
        entry_price = stock.get('entry_price')
        peak_date = stock.get('peak_date')
        
        # Validate required fields
        if not all([ticker, entry_date, entry_price, peak_date]):
            return None
        
        # Parse dates
        try:
            entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
            peak_dt = datetime.strptime(peak_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None
        
        # Define analysis window: entry to peak + 60 days
        end_dt = peak_dt + timedelta(days=60)
        
        # Fetch price data
        start_str = entry_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")
        
        price_data = self.get_price_data(ticker, start_str, end_str)
        
        if not price_data:
            return None
        
        # Analyze daily gains
        days_above_threshold = 0
        max_gain_pct = 0.0
        first_cross_date = None
        last_above_date = None
        daily_gains = []
        
        for bar in price_data:
            close_price = bar['c']
            bar_date = datetime.fromtimestamp(bar['t'] / 1000).strftime("%Y-%m-%d")
            
            # Calculate gain from entry
            gain_pct = ((close_price - entry_price) / entry_price) * 100
            
            # Track days above threshold
            above_threshold = gain_pct >= GAIN_THRESHOLD_PCT
            if above_threshold:
                days_above_threshold += 1
                last_above_date = bar_date
                if first_cross_date is None:
                    first_cross_date = bar_date
            
            # Track max gain
            if gain_pct > max_gain_pct:
                max_gain_pct = gain_pct
            
            daily_gains.append({
                "date": bar_date,
                "price": round(close_price, 2),
                "gain_pct": round(gain_pct, 2),
                "above_threshold": above_threshold
            })
        
        # Determine if sustainable
        sustainable = days_above_threshold >= MIN_DAYS_ABOVE_THRESHOLD
        
        return {
            "total_days_above_threshold": days_above_threshold,
            "min_days_required": MIN_DAYS_ABOVE_THRESHOLD,
            "max_gain_observed": round(max_gain_pct, 2),
            "first_cross_date": first_cross_date,
            "last_above_date": last_above_date,
            "sustainable": sustainable,
            "reason": self._get_reason(days_above_threshold, sustainable),
            "daily_gains": daily_gains,
            "test_date": datetime.now().strftime("%Y-%m-%d"),
            "filter_version": "4.0",
            "threshold_tested": f"{GAIN_THRESHOLD_PCT}% gain"
        }
    
    def _get_reason(self, days_above: int, sustainable: bool) -> str:
        """Generate human-readable reason"""
        if sustainable:
            return f"SUSTAINABLE: Stock was above 200% for {days_above} days - sufficient exit window"
        else:
            return f"PUMP-AND-DUMP: Only above 200% for {days_above} days (need {MIN_DAYS_ABOVE_THRESHOLD}+)"
    
    def filter_stocks(self):
        """Main filtering process"""
        print("=" * 80)
        print("GEM TRADING SYSTEM - SUSTAINABILITY FILTER v4.0")
        print("=" * 80)
        print(f"Method: Total Days Above {GAIN_THRESHOLD_PCT}% Threshold")
        print(f"Minimum Required: {MIN_DAYS_ABOVE_THRESHOLD} days")
        print()
        
        # Load stocks
        stocks, file_structure = self.load_catalog()
        if not stocks:
            print("❌ No stocks to process")
            return
        
        print(f"📊 Loaded {len(stocks)} stocks from CLEAN.json")
        print()
        
        sustainable_stocks = []
        unsustainable_stocks = []
        
        for idx, stock in enumerate(stocks, 1):
            ticker = stock.get('ticker', 'UNKNOWN')
            year = stock.get('year_discovered', stock.get('year', 'N/A'))
            
            print(f"[{idx}/{len(stocks)}] Processing {ticker} ({year})...", end=" ")
            
            # Skip if already tested with v4.0
            existing_test = stock.get('sustained_gain_test', {})
            if existing_test.get('filter_version') == '4.0':
                print("✓ Already tested (v4.0)")
                self.stats['not_tested'] += 1
                
                if existing_test.get('sustainable'):
                    sustainable_stocks.append(stock)
                    self.stats['sustainable'] += 1
                else:
                    unsustainable_stocks.append(stock)
                    self.stats['unsustainable'] += 1
                
                continue
            
            # Calculate exit window
            exit_window = self.calculate_exit_window(stock)
            
            if exit_window is None:
                print("⚠️  No data / incomplete")
                self.stats['not_tested'] += 1
                # Keep in sustainable by default (benefit of doubt)
                sustainable_stocks.append(stock)
                continue
            
            # Add to stock data with "sustained_gain_test" key to match existing structure
            stock['sustained_gain_test'] = exit_window
            
            # Classify
            if exit_window['sustainable']:
                print(f"✅ SUSTAINABLE ({exit_window['total_days_above_threshold']} days)")
                sustainable_stocks.append(stock)
                self.stats['sustainable'] += 1
            else:
                print(f"❌ PUMP-AND-DUMP ({exit_window['total_days_above_threshold']} days)")
                unsustainable_stocks.append(stock)
                self.stats['unsustainable'] += 1
            
            # Rate limiting
            if self.api_calls % 5 == 0 and self.api_calls > 0:
                time.sleep(0.2)
        
        # Update stats
        self.stats['api_calls'] = self.api_calls
        
        # Save results
        self.save_results(sustainable_stocks, unsustainable_stocks, file_structure)
        self.print_summary()
    
    def save_results(self, sustainable: List[Dict], unsustainable: List[Dict], file_structure: Dict):
        """Save filtered results to match existing structure"""
        # Update CLEAN.json with sustainable stocks only
        if file_structure:
            clean_output = file_structure.copy()
            clean_output['stocks'] = sustainable
        else:
            clean_output = {"stocks": sustainable}
        
        with open(INPUT_FILE, 'w') as f:
            json.dump(clean_output, f, indent=2)
        
        print(f"\n✅ Updated {INPUT_FILE}: {len(sustainable)} sustainable stocks")
        
        # Save unsustainable stocks
        with open(OUTPUT_UNSUSTAINABLE, 'w') as f:
            json.dump(unsustainable, f, indent=2)
        
        print(f"✅ Saved {OUTPUT_UNSUSTAINABLE}: {len(unsustainable)} pump-and-dumps")
        
        # Save summary
        with open(SUMMARY_FILE, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        print(f"✅ Saved {SUMMARY_FILE}")
    
    def print_summary(self):
        """Print filtering summary"""
        print("\n" + "=" * 80)
        print("FILTER SUMMARY")
        print("=" * 80)
        print(f"Total Stocks: {self.stats['total_stocks']}")
        print(f"Not Tested: {self.stats['not_tested']} (no data or already v4.0)")
        print()
        print(f"✅ SUSTAINABLE: {self.stats['sustainable']} stocks")
        print(f"   - Had {MIN_DAYS_ABOVE_THRESHOLD}+ days above {GAIN_THRESHOLD_PCT}% gain")
        print(f"   - Sufficient exit window")
        print()
        print(f"❌ UNSUSTAINABLE: {self.stats['unsustainable']} stocks")
        print(f"   - Less than {MIN_DAYS_ABOVE_THRESHOLD} days above {GAIN_THRESHOLD_PCT}% gain")
        print(f"   - Pump-and-dump pattern")
        print()
        
        total_tested = self.stats['sustainable'] + self.stats['unsustainable']
        if total_tested > 0:
            sustainability_rate = (self.stats['sustainable'] / total_tested) * 100
            print(f"📊 Sustainability Rate: {sustainability_rate:.1f}%")
        
        print(f"🔌 API Calls: {self.stats['api_calls']}")
        
        if self.stats['errors']:
            print(f"\n⚠️  Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                print(f"   - {error}")
        
        print("=" * 80)


def main():
    """Run the sustainability filter"""
    filter_tool = SustainabilityFilter()
    filter_tool.filter_stocks()


if __name__ == "__main__":
    main()
