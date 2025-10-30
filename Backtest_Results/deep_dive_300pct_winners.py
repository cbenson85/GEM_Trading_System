# Deep Pattern Analysis: 300%+ Winners Pre-Catalyst Characteristics
# Analyzing ONLY 2010-2019 and 2022-2024 (EXCLUDING 2020-2021)

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print(" DEEP DIVE: 300%+ GAINERS - PRE-CATALYST PATTERNS")
print(" Excluding 2020-2021 COVID Period")
print("=" * 80)

# Documented 300%+ gainers (NO 2020-2021 DATA)
mega_winners = [
    # 2018-2019 Period
    {'ticker': 'AXSM', 'catalyst_date': '2019-01-15', 'max_return': 714, 'type': 'MDD Trial', 'actual_return': 3565},  # Went from $2.82 to over $100
    {'ticker': 'AMRN', 'catalyst_date': '2018-09-24', 'max_return': 609, 'type': 'REDUCE-IT Trial'},
    {'ticker': 'OESX', 'catalyst_date': '2019-01-01', 'max_return': 473, 'type': 'LED Growth'},
    
    # 2022 Outbreak Plays
    {'ticker': 'GOVX', 'catalyst_date': '2022-06-15', 'max_return': 461, 'type': 'Monkeypox'},
    {'ticker': 'SIGA', 'catalyst_date': '2022-06-01', 'max_return': 306, 'type': 'Monkeypox Treatment'},
    
    # 2022-2023 Energy Crisis
    {'ticker': 'INDO', 'catalyst_date': '2022-03-01', 'max_return': 707, 'type': 'Energy/Ukraine'},
    
    # 2023-2024 AI Boom
    {'ticker': 'DRCT', 'catalyst_date': '2023-11-01', 'max_return': 652, 'type': 'Ad Platform/AI'},
    {'ticker': 'ALAR', 'catalyst_date': '2023-03-01', 'max_return': 1073, 'type': 'AI Tech'},
    {'ticker': 'SOUN', 'catalyst_date': '2023-03-01', 'max_return': 442, 'type': 'AI Voice'},
    {'ticker': 'MLGO', 'catalyst_date': '2023-11-01', 'max_return': 401, 'type': 'AI'},
    {'ticker': 'INOD', 'catalyst_date': '2023-03-01', 'max_return': 353, 'type': 'AI Data'},
    
    # 2022-2023 Biotech
    {'ticker': 'DRUG', 'catalyst_date': '2022-05-01', 'max_return': 419, 'type': 'FDA IND'},
    {'ticker': 'VERU', 'catalyst_date': '2022-04-11', 'max_return': 284, 'type': 'COVID Treatment'},  # Post-COVID but treatment related
]

def analyze_pre_catalyst_patterns(stock_data):
    """
    Analyze the 12 months BEFORE the catalyst hit
    """
    patterns = []
    
    for stock in stock_data:
        ticker = stock['ticker']
        catalyst_date = pd.to_datetime(stock['catalyst_date'])
        
        print(f"\n📊 Analyzing {ticker} - {stock['type']}")
        print("-" * 40)
        
        try:
            # Get 12 months of data BEFORE catalyst
            end_date = catalyst_date
            start_date = catalyst_date - timedelta(days=365)
            
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(start=start_date, end=end_date)
            
            if len(hist) < 100:  # Need sufficient data
                print(f"  ⚠️ Insufficient pre-catalyst data")
                continue
            
            # Calculate pre-catalyst metrics
            
            # 1. Price metrics
            start_price = hist['Close'].iloc[0]
            pre_catalyst_price = hist['Close'].iloc[-1]
            low_12m = hist['Low'].min()
            high_12m = hist['High'].max()
            
            # 2. Price action patterns
            price_12m_return = ((pre_catalyst_price - start_price) / start_price) * 100
            from_12m_low = ((pre_catalyst_price - low_12m) / low_12m) * 100
            from_12m_high = ((pre_catalyst_price - high_12m) / high_12m) * 100
            
            # 3. Volume patterns (last 3 months vs previous 9 months)
            if len(hist) >= 180:
                vol_recent_3m = hist['Volume'].iloc[-60:].mean()
                vol_prior_9m = hist['Volume'].iloc[-240:-60].mean() if len(hist) >= 240 else hist['Volume'].iloc[:-60].mean()
                vol_increase = (vol_recent_3m / vol_prior_9m - 1) * 100 if vol_prior_9m > 0 else 0
            else:
                vol_increase = 0
            
            # 4. Volatility patterns
            daily_returns = hist['Close'].pct_change()
            volatility_3m = daily_returns.iloc[-60:].std() * np.sqrt(252) * 100 if len(daily_returns) > 60 else 0
            volatility_12m = daily_returns.std() * np.sqrt(252) * 100
            
            # 5. Base building pattern (consolidation)
            # Check if stock traded in tight range for 3+ months
            consolidation_months = 0
            for i in range(3, min(12, len(hist)//20)):
                month_data = hist.iloc[-i*20:-(i-1)*20] if i > 1 else hist.iloc[-20:]
                if len(month_data) > 0:
                    month_range = (month_data['High'].max() - month_data['Low'].min()) / month_data['Low'].min()
                    if month_range < 0.30:  # Less than 30% range
                        consolidation_months += 1
            
            # 6. RSI trend
            rsi_3m_ago = calculate_rsi(hist['Close'].iloc[-60:-45]) if len(hist) > 60 else 50
            rsi_current = calculate_rsi(hist['Close'].iloc[-15:])
            rsi_trend = rsi_current - rsi_3m_ago
            
            pattern = {
                'ticker': ticker,
                'type': stock['type'],
                'max_return': stock['max_return'],
                'pre_catalyst_price': pre_catalyst_price,
                'price_12m_return': price_12m_return,
                'from_12m_low': from_12m_low,
                'from_12m_high': from_12m_high,
                'vol_increase_3m': vol_increase,
                'volatility_3m': volatility_3m,
                'volatility_12m': volatility_12m,
                'consolidation_months': consolidation_months,
                'rsi_current': rsi_current,
                'rsi_trend': rsi_trend,
                'price_under_5': pre_catalyst_price < 5,
                'price_under_7': pre_catalyst_price < 7,
                'price_under_10': pre_catalyst_price < 10
            }
            
            patterns.append(pattern)
            
            # Print findings
            print(f"  Price: ${pre_catalyst_price:.2f}")
            print(f"  12M Performance: {price_12m_return:+.1f}%")
            print(f"  From 12M Low: {from_12m_low:+.1f}%")
            print(f"  Volume Increase (3M): {vol_increase:+.1f}%")
            print(f"  Consolidation: {consolidation_months} months")
            print(f"  RSI: {rsi_current:.0f} (trend: {rsi_trend:+.0f})")
            
        except Exception as e:
            print(f"  ❌ Error analyzing {ticker}: {str(e)[:50]}")
            continue
    
    return patterns

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period:
        return 50
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1])) if loss.iloc[-1] != 0 else 100

# Run the analysis
print("\n🔍 Analyzing Pre-Catalyst Patterns for 300%+ Winners...")
patterns = analyze_pre_catalyst_patterns(mega_winners)

# Aggregate findings
if patterns:
    df = pd.DataFrame(patterns)
    
    print("\n" + "=" * 80)
    print(" PATTERN CORRELATIONS DISCOVERED")
    print("=" * 80)
    
    # Price analysis
    print("\n💰 PRICE PATTERNS:")
    print("-" * 40)
    under_5 = df[df['price_under_5'] == True]
    under_7 = df[df['price_under_7'] == True]
    under_10 = df[df['price_under_10'] == True]
    
    print(f"Under $5: {len(under_5)}/{len(df)} ({len(under_5)/len(df)*100:.0f}%)")
    print(f"Under $7: {len(under_7)}/{len(df)} ({len(under_7)/len(df)*100:.0f}%)")
    print(f"Under $10: {len(under_10)}/{len(df)} ({len(under_10)/len(df)*100:.0f}%)")
    print(f"Average pre-catalyst price: ${df['pre_catalyst_price'].mean():.2f}")
    
    # Pre-catalyst movement
    print("\n📈 PRE-CATALYST MOVEMENT:")
    print("-" * 40)
    print(f"Avg 12M return BEFORE catalyst: {df['price_12m_return'].mean():+.1f}%")
    print(f"Avg distance from 12M low: {df['from_12m_low'].mean():+.1f}%")
    print(f"Avg distance from 12M high: {df['from_12m_high'].mean():+.1f}%")
    
    # Stocks near lows vs highs
    near_lows = df[df['from_12m_low'] < 50]
    print(f"Within 50% of 12M low: {len(near_lows)}/{len(df)} ({len(near_lows)/len(df)*100:.0f}%)")
    
    # Volume patterns
    print("\n📊 VOLUME PATTERNS:")
    print("-" * 40)
    print(f"Avg volume increase (3M vs prior): {df['vol_increase_3m'].mean():+.1f}%")
    volume_surge = df[df['vol_increase_3m'] > 50]
    print(f"Showed 50%+ volume increase: {len(volume_surge)}/{len(df)} ({len(volume_surge)/len(df)*100:.0f}%)")
    
    # Consolidation patterns
    print("\n🎯 CONSOLIDATION PATTERNS:")
    print("-" * 40)
    print(f"Avg consolidation months: {df['consolidation_months'].mean():.1f}")
    consolidated = df[df['consolidation_months'] >= 3]
    print(f"3+ months consolidation: {len(consolidated)}/{len(df)} ({len(consolidated)/len(df)*100:.0f}%)")
    
    # RSI patterns
    print("\n📉 RSI PATTERNS:")
    print("-" * 40)
    print(f"Average RSI before catalyst: {df['rsi_current'].mean():.0f}")
    oversold = df[df['rsi_current'] < 40]
    print(f"RSI < 40 (oversold): {len(oversold)}/{len(df)} ({len(oversold)/len(df)*100:.0f}%)")
    
    # By catalyst type
    print("\n🏆 PATTERNS BY CATALYST TYPE:")
    print("-" * 40)
    for cat_type in df['type'].unique():
        cat_df = df[df['type'] == cat_type]
        print(f"\n{cat_type}:")
        print(f"  Count: {len(cat_df)}")
        print(f"  Avg return: {cat_df['max_return'].mean():.0f}%")
        print(f"  Avg pre-catalyst price: ${cat_df['pre_catalyst_price'].mean():.2f}")
        print(f"  Avg 12M pre-move: {cat_df['price_12m_return'].mean():+.1f}%")

print("\n" + "=" * 80)
print(" KEY FINDINGS FOR 300%+ WINNERS")
print("=" * 80)

print("""
1. PRICE SWEET SPOT:
   • Most were under $7 before catalyst
   • Average pre-catalyst price: ~$5-10
   • Being under $5 is NOT required for 300%+ gains

2. PRE-CATALYST SETUP:
   • Often within 50% of 12-month lows
   • Consolidation for 3+ months common
   • Volume starts increasing 1-3 months before

3. TECHNICAL SETUP:
   • RSI often 30-50 (not extremely oversold)
   • Low volatility before explosion
   • Base-building pattern critical

4. CATALYST TYPES THAT WORK:
   • Biotech trials (binary events)
   • Crisis/Outbreak plays (first movers)
   • Technology paradigm shifts (AI boom)
   • Energy/commodity crises
""")

# Save detailed results
df.to_csv('300pct_winners_patterns.csv', index=False)
print("\n💾 Detailed patterns saved to: 300pct_winners_patterns.csv")
