# Historical Entry Point Analysis
# Check when "missed" stocks were actually catchable by GEM v4.0

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print(" HISTORICAL ENTRY POINT ANALYSIS")
print(" When Could We Have Actually Caught These 'Missed' Winners?")
print("=" * 80)

# Key "missed" winners from the backtest that were above price limits
missed_due_to_price = [
    # Stocks repeatedly missed for being > $7 or > $10
    {'ticker': 'AXSM', 'missed_dates': ['2022-02-22', '2022-03-01', '2022-05-26', '2022-06-11'], 'reason': 'Price > $10'},
    {'ticker': 'VERU', 'missed_dates': ['2022-02-22', '2022-03-01', '2022-05-26', '2022-06-11'], 'reason': 'Price > $10'},
    {'ticker': 'GOVX', 'missed_dates': ['2022-02-22', '2022-03-01', '2022-05-26', '2022-06-11'], 'reason': 'Price > $10'},
    {'ticker': 'INOD', 'missed_dates': ['2024-02-21', '2024-05-10', '2024-05-17', '2024-08-09'], 'reason': 'Price > $10'},
    {'ticker': 'MLGO', 'missed_dates': ['2023-04-01', '2023-06-06', '2023-07-21', '2024-05-10'], 'reason': 'Price > $7'},
    {'ticker': 'ALAR', 'missed_dates': ['2023-04-01', '2023-08-05', '2024-02-21', '2024-03-09'], 'reason': 'Volume < 15k or Price > $7'},
    {'ticker': 'SAVA', 'missed_dates': ['2023-04-01', '2023-06-06', '2024-08-09'], 'reason': 'Price > $10'},
    {'ticker': 'PRAX', 'missed_dates': ['2023-06-06', '2023-07-21', '2023-07-28'], 'reason': 'Price > $10'},
    {'ticker': 'DRCT', 'missed_dates': ['2024-02-21', '2024-03-09'], 'reason': 'Price > $10'},
    {'ticker': 'DRUG', 'missed_dates': ['2024-10-18'], 'reason': 'Price > $10'},
]

def find_catchable_periods(ticker, missed_date, price_limit=7.0, override_limit=10.0):
    """
    Find when this stock was within our price limits before the missed date
    """
    try:
        stock = yf.Ticker(ticker)
        end = pd.to_datetime(missed_date)
        start = end - timedelta(days=365)  # Look back 1 year
        
        hist = stock.history(start=start, end=end)
        
        if len(hist) == 0:
            return None
        
        # Find periods when stock was under limits
        under_7 = hist[hist['Close'] <= price_limit]
        under_10 = hist[hist['Close'] <= override_limit]
        
        result = {
            'ticker': ticker,
            'missed_date': missed_date,
            'price_on_missed_date': hist['Close'].iloc[-1] if len(hist) > 0 else None
        }
        
        # Find last date it was under $7
        if len(under_7) > 0:
            last_under_7 = under_7.index[-1]
            days_since_under_7 = (end - last_under_7).days
            result['last_under_7'] = last_under_7.strftime('%Y-%m-%d')
            result['days_since_under_7'] = days_since_under_7
            result['price_when_under_7'] = under_7['Close'].iloc[-1]
        else:
            result['last_under_7'] = None
            result['days_since_under_7'] = None
        
        # Find last date it was under $10 (for biotech/catalyst plays)
        if len(under_10) > 0:
            last_under_10 = under_10.index[-1]
            days_since_under_10 = (end - last_under_10).days
            result['last_under_10'] = last_under_10.strftime('%Y-%m-%d')
            result['days_since_under_10'] = days_since_under_10
            result['price_when_under_10'] = under_10['Close'].iloc[-1]
        else:
            result['last_under_10'] = None
            result['days_since_under_10'] = None
        
        # Check what happened after (to see if it was worth catching)
        future = stock.history(start=end, end=end + timedelta(days=180))
        if len(future) > 0:
            max_return = ((future['High'].max() - hist['Close'].iloc[-1]) / hist['Close'].iloc[-1]) * 100
            result['180d_return_from_missed'] = max_return
        
        return result
        
    except Exception as e:
        print(f"  Error analyzing {ticker}: {str(e)[:50]}")
        return None

def analyze_all_missed():
    """
    Analyze all missed winners to see when we could have caught them
    """
    all_results = []
    
    for stock_info in missed_due_to_price:
        ticker = stock_info['ticker']
        print(f"\n📊 Analyzing {ticker} - {stock_info['reason']}")
        print("-" * 40)
        
        for date in stock_info['missed_dates'][:3]:  # Check first 3 missed dates
            result = find_catchable_periods(ticker, date)
            
            if result:
                all_results.append(result)
                
                if result['last_under_7']:
                    print(f"  {date}: Price=${result['price_on_missed_date']:.2f}")
                    print(f"    → Was $7 or under {result['days_since_under_7']} days ago (${result['price_when_under_7']:.2f})")
                    
                    if result['days_since_under_7'] <= 30:
                        print(f"    ✅ Would have caught it recently!")
                    elif result['days_since_under_7'] <= 90:
                        print(f"    ⚠️ Might have caught it in past 3 months")
                    else:
                        print(f"    ❌ Been above $7 for too long")
                else:
                    print(f"  {date}: NEVER under $7 in past year")
    
    return all_results

# Run the analysis
print("\n🔍 Checking when 'missed' winners were actually catchable...")
results = analyze_all_missed()

# Summarize findings
if results:
    df = pd.DataFrame(results)
    
    print("\n" + "=" * 80)
    print(" SUMMARY: TRULY MISSED vs WOULD HAVE CAUGHT")
    print("=" * 80)
    
    # Group by ticker
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker]
        
        print(f"\n{ticker}:")
        
        # Check if we would have caught it
        recent_catches = ticker_df[ticker_df['days_since_under_7'] <= 30]
        medium_catches = ticker_df[(ticker_df['days_since_under_7'] > 30) & (ticker_df['days_since_under_7'] <= 90)]
        never_catchable = ticker_df[ticker_df['days_since_under_7'].isna()]
        
        if len(recent_catches) > 0:
            print(f"  ✅ WOULD HAVE CAUGHT - Was under $7 within 30 days on {len(recent_catches)} occasions")
        elif len(medium_catches) > 0:
            print(f"  ⚠️ POSSIBLY CAUGHT - Was under $7 within 90 days on {len(medium_catches)} occasions")
        elif len(never_catchable) > 0:
            print(f"  ❌ TRULY MISSED - Never under $7 in lookback period")
        else:
            print(f"  ❌ TRULY MISSED - Been above $7 for 90+ days")

print("\n" + "=" * 80)
print(" KEY INSIGHTS")
print("=" * 80)

print("""
Based on this analysis:

1. STOCKS WE WOULD HAVE CAUGHT EARLIER:
   - These shouldn't count as "misses" in our analysis
   - The screener would have picked them up when under $7
   - We just happened to test on dates after they ran

2. TRULY MISSED OPPORTUNITIES:
   - Stocks that were never under $7 in reasonable timeframe
   - These might need special catalyst overrides
   - Or they might be IPOs/SPACs that started high

3. RECOMMENDATION:
   - Don't adjust screener for stocks we would have caught
   - Only consider adjustments for truly missed opportunities
   - Run screener daily to catch stocks before they run
""")

# Now let's test specific dates when these stocks WERE catchable
print("\n" + "=" * 80)
print(" TESTING CATCHABLE DATES")
print("=" * 80)

# Test a few key stocks on dates when they were under $7
test_dates = [
    {'ticker': 'GOVX', 'test_date': '2022-01-15', 'note': 'Before monkeypox outbreak'},
    {'ticker': 'VERU', 'test_date': '2021-12-01', 'note': 'Before COVID treatment news'},
    {'ticker': 'DRCT', 'test_date': '2023-10-01', 'note': 'Before ad platform growth'},
    {'ticker': 'INOD', 'test_date': '2023-01-01', 'note': 'Before AI boom'},
]

print("\nTesting if screener would have caught these on better dates:")
print("-" * 60)

for test in test_dates:
    try:
        stock = yf.Ticker(test['ticker'])
        date = pd.to_datetime(test['test_date'])
        hist = stock.history(start=date - timedelta(days=30), end=date + timedelta(days=1))
        
        if len(hist) > 0:
            price = hist['Close'].iloc[-1]
            volume = hist['Volume'].iloc[-10:].mean()
            
            print(f"\n{test['ticker']} on {test['test_date']} ({test['note']}):")
            print(f"  Price: ${price:.2f}")
            print(f"  Volume: {volume:,.0f}")
            
            if price <= 7.0 and volume >= 15000:
                print(f"  ✅ WOULD HAVE BEEN SELECTED!")
            elif price <= 10.0 and volume >= 5000:
                print(f"  ✅ WOULD HAVE QUALIFIED WITH OVERRIDE!")
            else:
                print(f"  ❌ Still wouldn't qualify")
                
            # Check what happened next
            future = stock.history(start=date, end=date + timedelta(days=180))
            if len(future) > 0:
                max_gain = ((future['High'].max() - price) / price) * 100
                print(f"  → Next 180 days: +{max_gain:.0f}% potential")
                
    except Exception as e:
        print(f"\n{test['ticker']}: Error - {str(e)[:50]}")
