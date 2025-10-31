#!/usr/bin/env python3
"""
GEM Trading System v5.0.1 - Daily Automated Screener
Uses Polygon.io (Massive) for real market data
"""

import os
import json
import requests
from datetime import datetime, timedelta
import sys

# Configuration
API_KEY = os.environ.get('POLYGON_API_KEY')
if not API_KEY:
    print("ERROR: POLYGON_API_KEY environment variable not set")
    sys.exit(1)

# GEM v5.0.1 Parameters
GEM_CRITERIA = {
    'price_min': 0.50,
    'price_max': 7.00,
    'price_max_imminent': 10.00,
    'volume_min': 10000,
    'float_max': 75000000,
    'min_score': 75
}

# Scoring multipliers from GEM v5.0.1
MULTIPLIERS = {
    'catalyst': 3.5,
    'timing': 2.0,
    'technical': 1.5,
    'short_interest': 1.0,
    'sector': 1.5,
    'float': 1.0
}

def get_market_snapshot():
    """Get current market snapshot for all US stocks."""
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
    params = {'apiKey': API_KEY}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('tickers', [])
        else:
            print(f"API Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching market snapshot: {e}")
        return []

def check_price_criteria(ticker_data):
    """Check if ticker meets GEM price criteria."""
    price = ticker_data.get('day', {}).get('c', 0)  # Closing price
    volume = ticker_data.get('day', {}).get('v', 0)  # Volume
    
    # Check basic criteria
    if price < GEM_CRITERIA['price_min'] or price > GEM_CRITERIA['price_max']:
        return False, "Price outside range"
    if volume < GEM_CRITERIA['volume_min']:
        return False, "Volume too low"
    
    return True, {"price": price, "volume": volume}

def get_ticker_details(symbol):
    """Get detailed info including float if available."""
    url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
    params = {'apiKey': API_KEY}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                return data['results']
    except Exception as e:
        print(f"Error getting details for {symbol}: {e}")
    
    return {}

def calculate_gem_score(ticker, price, volume, details):
    """Calculate GEM score based on available data."""
    score = 0
    components = {}
    
    # Note: Many components need external data (catalysts, short interest)
    # This is a simplified version showing the structure
    
    # Technical Score (simplified - based on price action)
    technical_score = 5  # Default middle score
    score += technical_score * MULTIPLIERS['technical']
    components['technical'] = technical_score * MULTIPLIERS['technical']
    
    # Float Score
    float_val = details.get('weighted_shares_outstanding', 0)
    if float_val > 0:
        if float_val < 10000000:
            float_score = 5
        elif float_val < 30000000:
            float_score = 4
        elif float_val < 50000000:
            float_score = 3
        elif float_val < 75000000:
            float_score = 2
        else:
            float_score = 0
    else:
        float_score = 0  # Unknown float
    
    score += float_score * MULTIPLIERS['float']
    components['float'] = float_score * MULTIPLIERS['float']
    
    # Placeholder for other scores (need additional data sources)
    components['catalyst'] = "NEED MANUAL CHECK"
    components['timing'] = "NEED MANUAL CHECK"
    components['short_interest'] = "DATA NOT AVAILABLE"
    components['sector'] = "NEED CLASSIFICATION"
    
    return score, components

def generate_daily_update(results):
    """Generate the CURRENT_UPDATE.md file."""
    now = datetime.now()
    
    content = f"""# GEM Daily Screening Update
## Date: {now.strftime('%Y-%m-%d %H:%M')} ET
## System: v5.0.1 with Polygon Integration

---

## 🔍 PHASE 1: Initial Screen Results

**Data Source:** Polygon.io (Massive) - VERIFIED REAL DATA
**Total Stocks Scanned:** {results['total_scanned']}
**Meeting Price Criteria ($0.50-$7.00):** {results['price_qualified']}
**Meeting Volume Criteria (>10K):** {results['volume_qualified']}

### Stocks Passing Phase 1:
"""
    
    for ticker in results['phase1_passed'][:20]:  # Limit to top 20
        content += f"- **{ticker['symbol']}**: ${ticker['price']:.2f} | Vol: {ticker['volume']:,}\n"
    
    if len(results['phase1_passed']) > 20:
        content += f"- ... and {len(results['phase1_passed']) - 20} more\n"
    
    content += f"""

---

## 📊 PHASE 2-3: Catalyst Check & Scoring

⚠️ **MANUAL CATALYST VERIFICATION REQUIRED**

The following stocks passed Phase 1 and need catalyst verification:

| Ticker | Price | Volume | Float | Partial Score | Action Required |
|--------|-------|--------|-------|---------------|-----------------|
"""
    
    for ticker in results['needs_catalyst_check'][:10]:
        content += f"| {ticker['symbol']} | ${ticker['price']:.2f} | {ticker['volume']:,} | "
        content += f"{ticker.get('float', 'N/A')} | {ticker['partial_score']:.1f} | CHECK CATALYST |\n"
    
    content += f"""

---

## ⚠️ DATA DISCLOSURE

### Available Data (Verified):
- ✅ Current prices
- ✅ Trading volume
- ✅ Basic ticker info
- ✅ Market cap (where available)
- ✅ Shares outstanding (partial)

### Data Requiring Manual Verification:
- ❌ Catalyst identification
- ❌ Catalyst timing
- ❌ Short interest
- ❌ Sector classification
- ❌ Technical patterns

### Next Steps:
1. Check BiopharmCatalyst for FDA catalysts
2. Review SEC filings for the Phase 1 passed stocks
3. Verify conference presentations
4. Calculate complete GEM scores with catalyst data

---

## 📈 Current Portfolio Status
*Update manually with current positions*

---

*Generated by GEM Automated Screening v5.0.1*
*Powered by Polygon.io (Massive) API*
"""
    
    return content

def main():
    """Main screening function."""
    print("Starting GEM Daily Screening...")
    print(f"Time: {datetime.now()}")
    
    results = {
        'total_scanned': 0,
        'price_qualified': 0,
        'volume_qualified': 0,
        'phase1_passed': [],
        'needs_catalyst_check': []
    }
    
    # Get market snapshot
    print("Fetching market data...")
    tickers = get_market_snapshot()
    results['total_scanned'] = len(tickers)
    print(f"Found {len(tickers)} stocks to screen")
    
    # Screen each ticker
    for ticker_data in tickers:
        symbol = ticker_data.get('ticker', '')
        
        # Check Phase 1 criteria
        passed, data = check_price_criteria(ticker_data)
        
        if passed and isinstance(data, dict):
            results['price_qualified'] += 1
            
            # Get additional details
            details = get_ticker_details(symbol)
            
            # Calculate partial score
            partial_score, components = calculate_gem_score(
                symbol, 
                data['price'], 
                data['volume'],
                details
            )
            
            ticker_info = {
                'symbol': symbol,
                'price': data['price'],
                'volume': data['volume'],
                'float': details.get('weighted_shares_outstanding', 'N/A'),
                'market_cap': details.get('market_cap', 'N/A'),
                'partial_score': partial_score,
                'components': components
            }
            
            results['phase1_passed'].append(ticker_info)
            
            # Flag for catalyst check
            if data['price'] <= GEM_CRITERIA['price_max']:
                results['needs_catalyst_check'].append(ticker_info)
    
    # Sort by partial score
    results['phase1_passed'].sort(key=lambda x: x['partial_score'], reverse=True)
    results['needs_catalyst_check'].sort(key=lambda x: x['partial_score'], reverse=True)
    
    print(f"Phase 1 complete: {len(results['phase1_passed'])} stocks qualified")
    
    # Generate update file
    print("Generating CURRENT_UPDATE.md...")
    update_content = generate_daily_update(results)
    
    # Save to file
    output_path = '../Daily_Operations/CURRENT_UPDATE.md'
    with open(output_path, 'w') as f:
        f.write(update_content)
    
    print(f"Update saved to {output_path}")
    print("Screening complete!")

if __name__ == "__main__":
    main()
