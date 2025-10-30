# GEM Agent v4.0 - Comprehensive Random Date Backtest
# January 1, 2022 to November 1, 2024
# Tracks picks, discards, and missed opportunities

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print(" GEM AGENT v4.0 - COMPREHENSIVE RANDOM DATE BACKTEST")
print(" Testing Period: Jan 1, 2022 - Nov 1, 2024")
print(" Full Tracking of Picks, Discards, and Missed Winners")
print("=" * 80)

class GEMBacktestV4:
    def __init__(self):
        # Optimized v4.0 criteria
        self.criteria = {
            'price_max': 7.00,
            'price_min': 0.50,
            'price_override_max': 10.00,
            'volume_min': 15000,
            'volume_override': 5000,
            'float_max': 75_000_000,
            'selections': 10
        }
        
        # Comprehensive test universe
        self.universe = {
            # Proven Winners
            'AXSM': {'sector': 'Biotech', 'known_catalyst': '2019 MDD trial'},
            'VERU': {'sector': 'Biotech', 'known_catalyst': '2022 COVID trial'},
            'GOVX': {'sector': 'Vaccine', 'known_catalyst': '2022 Monkeypox'},
            'DRCT': {'sector': 'AdTech', 'known_catalyst': '2023 Platform growth'},
            'SIGA': {'sector': 'Vaccine', 'known_catalyst': '2022 Monkeypox'},
            'INOD': {'sector': 'AI/Data', 'known_catalyst': '2023 AI boom'},
            'SOUN': {'sector': 'AI/Voice', 'known_catalyst': '2023 Voice AI'},
            'ALAR': {'sector': 'Tech', 'known_catalyst': '2023 Data collection'},
            'DRUG': {'sector': 'Biotech', 'known_catalyst': '2023 FDA IND'},
            'MLGO': {'sector': 'AI', 'known_catalyst': '2023 AI services'},
            
            # Biotech universe
            'GERN': {'sector': 'Biotech'},
            'SAVA': {'sector': 'Biotech'},
            'ATRA': {'sector': 'Biotech'},
            'PRAX': {'sector': 'Biotech'},
            'NKTX': {'sector': 'Biotech'},
            'HOWL': {'sector': 'Biotech'},
            'SMMT': {'sector': 'Biotech'},
            'ANVS': {'sector': 'Biotech'},
            'EVLO': {'sector': 'Biotech'},
            'SRRA': {'sector': 'Biotech'},
            'KTRA': {'sector': 'Biotech'},
            'CRTX': {'sector': 'Biotech'},
            'CNST': {'sector': 'Biotech'},
            
            # Tech/AI
            'BBAI': {'sector': 'AI/Defense'},
            'OESX': {'sector': 'LED Tech'},
            'APPS': {'sector': 'Mobile Tech'},
            'WKEY': {'sector': 'Security'},
            'MDJH': {'sector': 'Tech'},
            
            # Vaccine/Crisis
            'EBS': {'sector': 'Vaccine'},
            'INO': {'sector': 'Vaccine'},
            'NVAX': {'sector': 'Vaccine'},
            'BNTX': {'sector': 'Vaccine'},
            
            # Energy (typically avoided)
            'INDO': {'sector': 'Energy'},
            'RCON': {'sector': 'Oil/Gas'},
            'USEG': {'sector': 'Energy'},
            'CEI': {'sector': 'Oil/Gas'},
            
            # Others
            'LUCY': {'sector': 'Consumer'},
            'AGRI': {'sector': 'AgTech'},
            'MULN': {'sector': 'EV'},
            'FFIE': {'sector': 'EV'},
            'GOEV': {'sector': 'EV'},
            'NKLA': {'sector': 'EV'},
        }
        
        # Track everything
        self.all_picks = []
        self.all_discards = []
        self.missed_winners = []
    
    def screen_on_date(self, screen_date):
        """
        Run GEM v4.0 screener on specific date
        Track both picks and discards
        """
        print(f"\n{'='*60}")
        print(f"📅 Screening Date: {screen_date}")
        print(f"{'='*60}")
        
        qualified = []
        disqualified = []
        
        for ticker, info in self.universe.items():
            try:
                stock = yf.Ticker(ticker)
                end = pd.to_datetime(screen_date)
                start = end - timedelta(days=90)
                
                hist = stock.history(start=start, end=end)
                
                if len(hist) < 20:
                    disqualified.append({
                        'ticker': ticker,
                        'reason': 'Insufficient data',
                        'sector': info['sector']
                    })
                    continue
                
                current_price = hist['Close'].iloc[-1]
                avg_volume = hist['Volume'].iloc[-20:].mean()
                
                # Check criteria
                disqualify_reasons = []
                
                # Catalyst override for certain sectors
                has_override = info['sector'] in ['Biotech', 'Vaccine', 'AI/Data', 'AI/Voice', 'AdTech']
                
                # Price check
                if has_override:
                    if current_price > self.criteria['price_override_max']:
                        disqualify_reasons.append(f'Price ${current_price:.2f} > $10 (override max)')
                else:
                    if current_price > self.criteria['price_max']:
                        disqualify_reasons.append(f'Price ${current_price:.2f} > $7')
                
                if current_price < self.criteria['price_min']:
                    disqualify_reasons.append(f'Price ${current_price:.2f} < $0.50')
                
                # Volume check
                if has_override:
                    if avg_volume < self.criteria['volume_override']:
                        disqualify_reasons.append(f'Volume {avg_volume:.0f} < 5k (override min)')
                else:
                    if avg_volume < self.criteria['volume_min']:
                        disqualify_reasons.append(f'Volume {avg_volume:.0f} < 15k')
                
                # Sector filter (soft - can be overridden)
                if info['sector'] in ['Energy', 'Oil/Gas'] and not has_override:
                    disqualify_reasons.append(f'Avoided sector: {info["sector"]}')
                
                if disqualify_reasons:
                    disqualified.append({
                        'ticker': ticker,
                        'reasons': disqualify_reasons,
                        'sector': info['sector'],
                        'price': current_price,
                        'volume': avg_volume
                    })
                else:
                    # Calculate comprehensive score
                    score = self.calculate_score(ticker, info, hist, current_price, avg_volume)
                    
                    qualified.append({
                        'ticker': ticker,
                        'sector': info['sector'],
                        'price': current_price,
                        'volume': avg_volume,
                        'score': score,
                        'has_override': has_override
                    })
                    
            except Exception as e:
                disqualified.append({
                    'ticker': ticker,
                    'reason': f'Error: {str(e)[:30]}',
                    'sector': info['sector']
                })
        
        # Sort qualified by score and select top 10
        qualified.sort(key=lambda x: x['score'], reverse=True)
        picks = qualified[:self.criteria['selections']]
        not_selected = qualified[self.criteria['selections']:]
        
        # Add not selected to discards
        for stock in not_selected:
            disqualified.append({
                'ticker': stock['ticker'],
                'reasons': ['Score too low (not in top 10)'],
                'sector': stock['sector'],
                'price': stock['price'],
                'volume': stock['volume'],
                'score': stock['score']
            })
        
        # Display results
        print(f"\n✅ SELECTED ({len(picks)} stocks):")
        for i, pick in enumerate(picks, 1):
            print(f"  {i}. {pick['ticker']}: ${pick['price']:.2f} | {pick['sector']} | Score: {pick['score']:.0f}")
        
        print(f"\n❌ DISQUALIFIED ({len(disqualified)} stocks):")
        # Show sample of discards
        for discard in disqualified[:5]:
            reason = discard.get('reasons', [discard.get('reason', 'Unknown')])[0] if isinstance(discard.get('reasons'), list) else discard.get('reason', 'Unknown')
            print(f"  {discard['ticker']}: {reason}")
        
        if len(disqualified) > 5:
            print(f"  ... and {len(disqualified)-5} more")
        
        return picks, disqualified
    
    def calculate_score(self, ticker, info, hist, price, volume):
        """Calculate comprehensive score based on v4.0 criteria"""
        score = 0
        
        # Sector scoring
        sector_scores = {
            'Biotech': 40,
            'Vaccine': 35,
            'AI/Data': 30,
            'AI/Voice': 30,
            'AdTech': 30,
            'AI/Defense': 25,
            'Tech': 25,
            'AI': 25,
            'LED Tech': 20,
            'Mobile Tech': 20,
            'Security': 20,
            'Consumer': 15,
            'AgTech': 10,
            'EV': 10,
            'Energy': 5,
            'Oil/Gas': 5,
        }
        score += sector_scores.get(info['sector'], 10)
        
        # Technical analysis
        try:
            # RSI
            rsi = self.calculate_rsi(hist['Close'])
            if 30 <= rsi <= 60:
                score += 15
            elif rsi < 30:
                score += 10
            
            # Volume trend
            if len(hist) >= 40:
                vol_recent = hist['Volume'].iloc[-10:].mean()
                vol_prior = hist['Volume'].iloc[-40:-10].mean()
                if vol_prior > 0 and vol_recent / vol_prior > 1.5:
                    score += 15
            
            # Price position
            low_90d = hist['Low'].min()
            high_90d = hist['High'].max()
            price_position = ((price - low_90d) / (high_90d - low_90d) * 100) if high_90d > low_90d else 50
            
            if price_position < 40:  # Near lows
                score += 20
            elif price_position < 60:
                score += 10
            
            # Consolidation check
            if len(hist) >= 60:
                range_60d = (hist['High'].iloc[-60:].max() - hist['Low'].iloc[-60:].min()) / hist['Low'].iloc[-60:].min()
                if range_60d < 0.40:  # Tight range
                    score += 15
            
            # Price sweet spot
            if 1.0 <= price <= 3.0:
                score += 15
            elif 3.0 < price <= 5.0:
                score += 10
            elif 5.0 < price <= 7.0:
                score += 5
                
        except:
            pass
        
        return score
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period:
            return 50
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        if loss.iloc[-1] == 0:
            return 100
        rs = gain.iloc[-1] / loss.iloc[-1]
        return 100 - (100 / (1 + rs))
    
    def track_12month_performance(self, stocks, screen_date):
        """
        Track performance of stocks for 12 months after screening
        """
        results = []
        
        for stock in stocks:
            ticker = stock['ticker']
            
            try:
                yf_ticker = yf.Ticker(ticker)
                start = pd.to_datetime(screen_date)
                end = start + timedelta(days=365)
                
                hist = yf_ticker.history(start=start, end=end)
                
                if len(hist) < 20:
                    continue
                
                entry_price = hist['Close'].iloc[0]
                
                performance = {
                    'ticker': ticker,
                    'sector': stock['sector'],
                    'entry_price': entry_price,
                    'screen_date': screen_date,
                    'score': stock.get('score', 0)
                }
                
                # Calculate returns at intervals
                for days in [30, 60, 90, 180, 365]:
                    if days < len(hist):
                        exit_price = hist['Close'].iloc[min(days, len(hist)-1)]
                        performance[f'return_{days}d'] = ((exit_price - entry_price) / entry_price) * 100
                
                # Max return within 12 months
                max_price = hist['High'].max()
                performance['max_return'] = ((max_price - entry_price) / entry_price) * 100
                
                # Min (drawdown)
                min_price = hist['Low'].min()
                performance['max_drawdown'] = ((min_price - entry_price) / entry_price) * 100
                
                # Check for catalyst (>50% move in 5 days)
                performance['catalyst_detected'] = False
                for i in range(len(hist)-5):
                    five_day_return = ((hist['Close'].iloc[i+5] - hist['Close'].iloc[i]) / hist['Close'].iloc[i]) * 100
                    if abs(five_day_return) > 50:
                        performance['catalyst_detected'] = True
                        performance['catalyst_day'] = i
                        break
                
                results.append(performance)
                
            except:
                continue
        
        return results
    
    def analyze_missed_winners(self, discards, screen_date):
        """
        Check if any discarded stocks became big winners
        """
        missed = []
        
        for discard in discards:
            ticker = discard['ticker']
            
            try:
                stock = yf.Ticker(ticker)
                start = pd.to_datetime(screen_date)
                end = start + timedelta(days=365)
                
                hist = stock.history(start=start, end=end)
                
                if len(hist) < 20:
                    continue
                
                entry_price = hist['Close'].iloc[0]
                
                # Check performance
                max_price = hist['High'].max()
                max_return = ((max_price - entry_price) / entry_price) * 100
                
                if max_return > 100:  # Multi-bagger that we missed
                    
                    # Get 90d return
                    return_90d = 0
                    if len(hist) > 90:
                        price_90d = hist['Close'].iloc[90]
                        return_90d = ((price_90d - entry_price) / entry_price) * 100
                    
                    missed.append({
                        'ticker': ticker,
                        'sector': discard['sector'],
                        'reasons': discard.get('reasons', discard.get('reason', 'Unknown')),
                        'max_return': max_return,
                        'return_90d': return_90d,
                        'entry_price': entry_price
                    })
                    
            except:
                continue
        
        return missed
    
    def run_comprehensive_backtest(self, num_dates=20):
        """
        Run complete backtest with random dates
        """
        # Generate random dates between Jan 1, 2022 and Nov 1, 2024
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2024, 11, 1)
        days_between = (end_date - start_date).days
        
        random_dates = []
        for _ in range(num_dates):
            random_days = random.randint(0, days_between)
            random_date = start_date + timedelta(days=random_days)
            random_dates.append(random_date.strftime('%Y-%m-%d'))
        
        random_dates.sort()
        
        print(f"\n🎲 Testing {num_dates} random dates between Jan 2022 and Nov 2024")
        print("=" * 80)
        
        all_picks_performance = []
        all_missed_winners = []
        
        for date in random_dates:
            # Screen stocks
            picks, discards = self.screen_on_date(date)
            
            # Track performance of picks
            if picks:
                print(f"\n📈 Tracking 12-month performance for {len(picks)} picks...")
                pick_performance = self.track_12month_performance(picks, date)
                all_picks_performance.extend(pick_performance)
                
                # Show quick results
                for perf in pick_performance[:3]:  # Show top 3
                    if 'return_90d' in perf:
                        icon = "🚀" if perf['return_90d'] > 100 else "✅" if perf['return_90d'] > 20 else "❌"
                        catalyst = "⚡" if perf.get('catalyst_detected', False) else ""
                        print(f"  {perf['ticker']}: 90d={perf['return_90d']:+.1f}% | Max={perf['max_return']:+.1f}% {icon}{catalyst}")
            
            # Check for missed winners in discards
            if discards:
                print(f"\n🔍 Checking {len(discards)} discards for missed winners...")
                missed = self.analyze_missed_winners(discards, date)
                if missed:
                    all_missed_winners.extend(missed)
                    print(f"  ⚠️ Found {len(missed)} missed multi-baggers!")
                    for m in missed[:2]:  # Show top 2
                        print(f"    {m['ticker']}: {m['max_return']:+.0f}% (Reason: {m['reasons'][0] if isinstance(m['reasons'], list) else m['reasons']})")
        
        # Comprehensive analysis
        self.generate_final_report(all_picks_performance, all_missed_winners)
    
    def generate_final_report(self, picks_performance, missed_winners):
        """
        Generate comprehensive backtest report
        """
        print("\n" + "=" * 80)
        print(" COMPREHENSIVE BACKTEST RESULTS - GEM v4.0")
        print(" Period: Jan 2022 - Nov 2024")
        print("=" * 80)
        
        if picks_performance:
            df_picks = pd.DataFrame(picks_performance)
            
            total_picks = len(df_picks)
            
            # Win rate analysis
            print("\n📊 PICK PERFORMANCE:")
            print("-" * 60)
            
            for period in [30, 60, 90, 180]:
                col = f'return_{period}d'
                if col in df_picks.columns:
                    winners = len(df_picks[df_picks[col] > 0])
                    big_winners = len(df_picks[df_picks[col] > 100])
                    avg_return = df_picks[col].mean()
                    median_return = df_picks[col].median()
                    
                    print(f"\n{period}-Day Performance:")
                    print(f"  Win Rate: {winners}/{total_picks} ({winners/total_picks*100:.1f}%)")
                    print(f"  Average Return: {avg_return:+.1f}%")
                    print(f"  Median Return: {median_return:+.1f}%")
                    print(f"  100%+ Winners: {big_winners} ({big_winners/total_picks*100:.1f}%)")
            
            # Multi-bagger analysis
            print("\n🚀 MULTI-BAGGER ANALYSIS:")
            print("-" * 60)
            if 'max_return' in df_picks.columns:
                multi_2x = len(df_picks[df_picks['max_return'] > 100])
                multi_3x = len(df_picks[df_picks['max_return'] > 200])
                multi_5x = len(df_picks[df_picks['max_return'] > 400])
                
                print(f"2x+ (100%+): {multi_2x}/{total_picks} ({multi_2x/total_picks*100:.1f}%)")
                print(f"3x+ (200%+): {multi_3x}/{total_picks} ({multi_3x/total_picks*100:.1f}%)")
                print(f"5x+ (400%+): {multi_5x}/{total_picks} ({multi_5x/total_picks*100:.1f}%)")
                print(f"Average Max Return: {df_picks['max_return'].mean():+.1f}%")
            
            # Catalyst detection
            if 'catalyst_detected' in df_picks.columns:
                catalysts = df_picks['catalyst_detected'].sum()
                print(f"\n⚡ Catalysts Detected: {catalysts}/{total_picks} ({catalysts/total_picks*100:.1f}%)")
            
            # Sector performance
            print("\n📈 PERFORMANCE BY SECTOR:")
            print("-" * 60)
            if 'return_90d' in df_picks.columns:
                sector_perf = df_picks.groupby('sector')['return_90d'].agg(['count', 'mean'])
                sector_perf = sector_perf.sort_values('mean', ascending=False)
                for sector, stats in sector_perf.iterrows():
                    if stats['count'] > 0:
                        print(f"{sector:15s}: {stats['count']:2.0f} picks | {stats['mean']:+6.1f}% avg")
            
            # Best performers
            if 'return_90d' in df_picks.columns:
                print("\n🏆 TOP 5 PICKS (by 90-day return):")
                print("-" * 60)
                top_5 = df_picks.nlargest(5, 'return_90d')[['ticker', 'sector', 'return_90d', 'max_return']]
                for _, row in top_5.iterrows():
                    print(f"{row['ticker']:6s} ({row['sector']:12s}): 90d={row['return_90d']:+6.1f}% | Max={row['max_return']:+6.1f}%")
        
        if missed_winners:
            df_missed = pd.DataFrame(missed_winners)
            
            print("\n" + "=" * 80)
            print(" MISSED WINNERS ANALYSIS")
            print("=" * 80)
            
            print(f"\nTotal Missed Multi-baggers: {len(df_missed)}")
            print(f"Average Missed Return: {df_missed['max_return'].mean():+.1f}%")
            
            # Group by discard reason
            print("\n📊 REASONS FOR MISSING WINNERS:")
            print("-" * 60)
            
            reason_counts = {}
            for _, row in df_missed.iterrows():
                reasons = row['reasons']
                if isinstance(reasons, list):
                    reason = reasons[0] if reasons else 'Unknown'
                else:
                    reason = str(reasons)
                
                # Categorize reasons
                if 'Price' in reason and '> $7' in reason:
                    key = 'Price > $7'
                elif 'Price' in reason and '> $10' in reason:
                    key = 'Price > $10'
                elif 'Volume' in reason and '< 15k' in reason:
                    key = 'Volume < 15k'
                elif 'Volume' in reason and '< 5k' in reason:
                    key = 'Volume < 5k'
                elif 'Score too low' in reason:
                    key = 'Not in top 10'
                elif 'sector' in reason.lower():
                    key = 'Sector filter'
                else:
                    key = 'Other'
                
                if key not in reason_counts:
                    reason_counts[key] = []
                reason_counts[key].append(row)
            
            for reason, stocks in sorted(reason_counts.items(), key=lambda x: len(x[1]), reverse=True):
                avg_missed = sum(s['max_return'] for s in stocks) / len(stocks)
                examples = ', '.join([s['ticker'] for s in stocks[:3]])
                print(f"\n{reason}:")
                print(f"  Count: {len(stocks)} stocks")
                print(f"  Avg Missed Return: {avg_missed:+.1f}%")
                print(f"  Examples: {examples}")
            
            # Biggest misses
            print("\n💔 TOP 5 BIGGEST MISSES:")
            print("-" * 60)
            top_missed = df_missed.nlargest(5, 'max_return')[['ticker', 'sector', 'max_return', 'reasons']]
            for _, row in top_missed.iterrows():
                reason = row['reasons'][0] if isinstance(row['reasons'], list) else row['reasons']
                print(f"{row['ticker']:6s}: {row['max_return']:+6.0f}% | Reason: {reason[:40]}")
        
        # Final verdict
        print("\n" + "=" * 80)
        print(" FINAL VERDICT")
        print("=" * 80)
        
        if picks_performance:
            df_picks = pd.DataFrame(picks_performance)
            if 'return_90d' in df_picks.columns:
                win_rate_90d = len(df_picks[df_picks['return_90d'] > 0]) / len(df_picks) * 100
                avg_return_90d = df_picks['return_90d'].mean()
                
                print(f"\n📊 Overall 90-Day Performance:")
                print(f"  Win Rate: {win_rate_90d:.1f}%")
                print(f"  Average Return: {avg_return_90d:+.1f}%")
                
                if win_rate_90d >= 60:
                    print("\n✅ SUCCESS! Win rate exceeds 60% target!")
                elif win_rate_90d >= 55:
                    print("\n⚠️ CLOSE! Win rate 55-60% - nearly at target")
                elif win_rate_90d >= 50:
                    print("\n🔶 MODERATE: Win rate 50-55% - further refinement needed")
                else:
                    print("\n❌ BELOW TARGET: Win rate under 50%")
                
                print(f"\n💡 Missed Opportunities: {len(missed_winners) if missed_winners else 0} multi-baggers filtered out")
                if missed_winners and len(missed_winners) > 5:
                    print("   Consider further loosening criteria to capture more winners")

# Run the backtest
if __name__ == "__main__":
    print("\n🚀 Starting Comprehensive GEM v4.0 Backtest")
    print("Settings:")
    print("• Price: $0.50-$7.00 (override to $10)")
    print("• Volume: 15,000+ (override to 5,000)")
    print("• Selections: Top 10 stocks")
    print("• Period: Jan 1, 2022 - Nov 1, 2024")
    print("• Random dates: 20")
    
    backtester = GEMBacktestV4()
    backtester.run_comprehensive_backtest(num_dates=20)
    
    print("\n✅ Backtest Complete!")
