# GEM Agent v3.0 - Complete Pipeline Tracker with Discard Analysis
# This version tracks EVERY stock through each phase and analyzes discards

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print(" GEM AGENT v3.0 - FULL PIPELINE TRACKER WITH DISCARD ANALYSIS")
print(" Tracking Every Stock Through Each Phase to Find Hidden Winners")
print("=" * 80)

class GEMPipelineTracker:
    def __init__(self):
        # Initialize tracking dictionaries
        self.phase1_pass = []  # Passed initial screen
        self.phase1_fail = []  # Failed initial screen
        self.phase2_pass = []  # Passed validation
        self.phase2_fail = []  # Failed validation
        self.phase3_pass = []  # Made it to final scoring
        self.phase3_fail = []  # Failed final criteria
        self.final_picks = []  # Actually selected
        
        # Comprehensive micro-cap universe
        self.universe = {
            # Known mega-winners
            'AXSM': {'sector': 'Biotech', 'known_result': '3565% (2019)'},
            'VERU': {'sector': 'Biotech', 'known_result': '284% (2022)'},
            'GOVX': {'sector': 'Vaccine', 'known_result': '460% (2022)'},
            'DRCT': {'sector': 'AdTech', 'known_result': '652% (2023)'},
            'AMRN': {'sector': 'Biotech', 'known_result': '609% (2018)'},
            'SIGA': {'sector': 'Vaccine', 'known_result': '266% (2022)'},
            'INOD': {'sector': 'AI/Data', 'known_result': '104% (2023)'},
            
            # Additional biotechs
            'GERN': {'sector': 'Biotech'},
            'SAVA': {'sector': 'Biotech'},
            'ATRA': {'sector': 'Biotech'},
            'DRUG': {'sector': 'Biotech'},
            'PRAX': {'sector': 'Biotech'},
            'NKTX': {'sector': 'Biotech'},
            'HOWL': {'sector': 'Biotech'},
            'SMMT': {'sector': 'Biotech'},
            'CRTX': {'sector': 'Biotech'},
            'CNST': {'sector': 'Biotech'},
            'SRRA': {'sector': 'Biotech'},
            'EVLO': {'sector': 'Biotech'},
            'ANVS': {'sector': 'Biotech'},
            'KTRA': {'sector': 'Biotech'},
            
            # Tech/AI/Platform
            'SOUN': {'sector': 'AI/Voice'},
            'BBAI': {'sector': 'AI/Defense'},
            'ALAR': {'sector': 'Tech'},
            'MLGO': {'sector': 'AI'},
            'OESX': {'sector': 'LED Tech'},
            'WKEY': {'sector': 'Tech Security'},
            'MDJH': {'sector': 'Tech'},
            'APPS': {'sector': 'Mobile Tech'},
            
            # Outbreak/Crisis response
            'EBS': {'sector': 'Vaccine'},
            'INO': {'sector': 'Vaccine'},
            'NVAX': {'sector': 'Vaccine'},
            'BNTX': {'sector': 'Vaccine'},
            
            # Energy/Resources (to test filter)
            'RCON': {'sector': 'Oil/Gas'},
            'CEI': {'sector': 'Oil/Gas'},
            'USEG': {'sector': 'Energy'},
            'INDO': {'sector': 'Energy'},
            
            # Others
            'LUCY': {'sector': 'Consumer'},
            'AGRI': {'sector': 'AgTech'},
            'FFIE': {'sector': 'EV'},
            'MULN': {'sector': 'EV'},
            'NKLA': {'sector': 'EV'},
            'GOEV': {'sector': 'EV'},
        }
    
    def phase1_initial_screen(self, date):
        """
        Phase 1: Basic criteria check
        Price < $5, Volume > 50k, etc.
        """
        print(f"\n{'='*60}")
        print(f"PHASE 1: Initial Screen on {date}")
        print(f"{'='*60}")
        
        passed = []
        failed = []
        
        for ticker, info in self.universe.items():
            try:
                stock = yf.Ticker(ticker)
                end_date = pd.to_datetime(date)
                start_date = end_date - timedelta(days=60)
                
                hist = stock.history(start=start_date, end=end_date)
                
                if len(hist) < 10:
                    failed.append({
                        'ticker': ticker,
                        'reason': 'Insufficient data',
                        'sector': info.get('sector', 'Unknown')
                    })
                    continue
                
                # Get current metrics
                current_price = hist['Close'].iloc[-1]
                avg_volume = hist['Volume'].iloc[-10:].mean() if len(hist) >= 10 else 0
                
                # Phase 1 Criteria
                fail_reasons = []
                
                if current_price > 5.00:
                    fail_reasons.append(f'Price too high: ${current_price:.2f}')
                if current_price < 0.50:
                    fail_reasons.append(f'Price too low: ${current_price:.2f}')
                if avg_volume < 50000:
                    fail_reasons.append(f'Volume too low: {avg_volume:.0f}')
                
                if fail_reasons:
                    failed.append({
                        'ticker': ticker,
                        'reason': '; '.join(fail_reasons),
                        'price': current_price,
                        'sector': info.get('sector', 'Unknown')
                    })
                else:
                    passed.append({
                        'ticker': ticker,
                        'price': current_price,
                        'volume': avg_volume,
                        'sector': info.get('sector', 'Unknown')
                    })
                    
            except Exception as e:
                failed.append({
                    'ticker': ticker,
                    'reason': f'Data error: {str(e)[:30]}',
                    'sector': info.get('sector', 'Unknown')
                })
        
        self.phase1_pass = passed
        self.phase1_fail = failed
        
        print(f"✅ Passed Phase 1: {len(passed)} stocks")
        print(f"❌ Failed Phase 1: {len(failed)} stocks")
        
        # Show some examples
        if passed:
            print(f"\nSample passes: {', '.join([p['ticker'] for p in passed[:5]])}")
        if failed:
            print(f"Sample fails: {', '.join([f['ticker'] for f in failed[:5]])}")
        
        return passed
    
    def phase2_validation(self, candidates, date):
        """
        Phase 2: Validation Gauntlet
        Check for reverse splits, delisting, sector filters, etc.
        """
        print(f"\n{'='*60}")
        print(f"PHASE 2: Validation Gauntlet")
        print(f"{'='*60}")
        
        passed = []
        failed = []
        
        for candidate in candidates:
            ticker = candidate['ticker']
            sector = candidate['sector']
            
            fail_reasons = []
            
            # V1: Sector filter (avoid energy/resources)
            if sector in ['Oil/Gas', 'Energy', 'Mining']:
                fail_reasons.append(f'Avoided sector: {sector}')
            
            # V2: Price action check (avoid if already pumped)
            try:
                stock = yf.Ticker(ticker)
                end_date = pd.to_datetime(date)
                start_date = end_date - timedelta(days=30)
                hist = stock.history(start=start_date, end=end_date)
                
                if len(hist) > 20:
                    month_return = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                    if month_return > 100:
                        fail_reasons.append(f'Already pumped: {month_return:.0f}% in 30d')
                    
                    # Check for extreme volatility (possible reverse split)
                    daily_returns = hist['Close'].pct_change()
                    if daily_returns.std() > 0.25:  # >25% daily volatility
                        fail_reasons.append('Extreme volatility (possible reverse split)')
                
            except:
                pass
            
            # V3: Basic quality check
            if candidate.get('price', 0) < 0.75:
                fail_reasons.append('Price too low for safety')
            
            if fail_reasons:
                failed.append({
                    'ticker': ticker,
                    'reasons': fail_reasons,
                    'sector': sector
                })
            else:
                passed.append(candidate)
        
        self.phase2_pass = passed
        self.phase2_fail = failed
        
        print(f"✅ Passed Phase 2: {len(passed)} stocks")
        print(f"❌ Failed Phase 2: {len(failed)} stocks")
        
        if failed:
            print("\nPhase 2 Failures:")
            for f in failed[:5]:
                print(f"  {f['ticker']}: {', '.join(f['reasons'])}")
        
        return passed
    
    def phase3_scoring(self, candidates, date):
        """
        Phase 3: Final scoring and selection
        """
        print(f"\n{'='*60}")
        print(f"PHASE 3: Scoring & Selection")
        print(f"{'='*60}")
        
        scored = []
        
        for candidate in candidates:
            ticker = candidate['ticker']
            
            try:
                stock = yf.Ticker(ticker)
                end_date = pd.to_datetime(date)
                start_date = end_date - timedelta(days=60)
                hist = stock.history(start=start_date, end=end_date)
                
                if len(hist) < 14:
                    continue
                
                # Calculate technical indicators
                rsi = self.calculate_rsi(hist['Close'])
                
                # Volume surge
                vol_5d = hist['Volume'].iloc[-5:].mean() if len(hist) >= 5 else hist['Volume'].mean()
                vol_20d = hist['Volume'].iloc[-20:].mean() if len(hist) >= 20 else hist['Volume'].mean()
                vol_surge = vol_5d / vol_20d if vol_20d > 0 else 1
                
                # Price position
                low_60d = hist['Low'].min()
                high_60d = hist['High'].max()
                current = hist['Close'].iloc[-1]
                price_position = ((current - low_60d) / (high_60d - low_60d)) * 100 if high_60d > low_60d else 50
                
                # Calculate score
                score = 0
                
                # Sector scoring (based on our analysis)
                if candidate['sector'] in ['Biotech', 'Vaccine']:
                    score += 40
                elif 'AI' in candidate['sector'] or 'Tech' in candidate['sector']:
                    score += 30
                else:
                    score += 15
                
                # Technical scoring
                if rsi < 40:  # Oversold
                    score += 20
                elif rsi < 50:
                    score += 10
                
                # Volume surge bonus
                if vol_surge > 1.5:
                    score += 15
                
                # Not overextended
                if price_position < 40:  # In lower 40% of range
                    score += 20
                elif price_position < 60:
                    score += 10
                
                # Price sweet spot
                if 1.0 <= current <= 3.0:
                    score += 10
                
                candidate['score'] = score
                candidate['rsi'] = rsi
                candidate['vol_surge'] = vol_surge
                scored.append(candidate)
                
            except Exception as e:
                continue
        
        # Sort by score
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        # Select top 5
        selected = scored[:5]
        not_selected = scored[5:]
        
        self.final_picks = selected
        self.phase3_fail = not_selected
        
        print(f"📊 Scored {len(scored)} stocks")
        print(f"✅ Selected top {len(selected)} stocks")
        
        if selected:
            print("\nFinal Selections:")
            for i, pick in enumerate(selected, 1):
                print(f"  {i}. {pick['ticker']}: Score={pick['score']:.0f}, "
                      f"Price=${pick['price']:.2f}, RSI={pick['rsi']:.0f}")
        
        return selected
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        if len(prices) < period:
            return 50
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        if loss.iloc[-1] == 0:
            return 100
        rs = gain.iloc[-1] / loss.iloc[-1]
        return 100 - (100 / (1 + rs))
    
    def analyze_discards(self, date):
        """
        Analyze what happened to discarded stocks
        Check if any became big winners
        """
        print(f"\n{'='*80}")
        print(f"DISCARD ANALYSIS - Tracking Forward Performance")
        print(f"{'='*80}")
        
        all_discards = []
        
        # Combine all discarded stocks
        for fail in self.phase1_fail:
            fail['discarded_at'] = 'Phase 1'
            all_discards.append(fail)
        
        for fail in self.phase2_fail:
            fail['discarded_at'] = 'Phase 2'
            all_discards.append(fail)
        
        for fail in self.phase3_fail:
            fail['discarded_at'] = 'Phase 3 (not selected)'
            all_discards.append(fail)
        
        # Track forward performance of discards
        missed_winners = []
        
        for discard in all_discards:
            ticker = discard['ticker']
            
            try:
                stock = yf.Ticker(ticker)
                start = pd.to_datetime(date)
                end = start + timedelta(days=365)
                
                hist = stock.history(start=start, end=end)
                
                if len(hist) > 20:
                    entry_price = hist['Close'].iloc[0]
                    
                    # Check various periods
                    returns = {}
                    for days in [30, 60, 90, 180, 365]:
                        if days < len(hist):
                            exit_price = hist['Close'].iloc[days]
                            returns[f'{days}d'] = ((exit_price - entry_price) / entry_price) * 100
                    
                    # Check max return
                    max_price = hist['High'].max()
                    max_return = ((max_price - entry_price) / entry_price) * 100
                    
                    # If this was a big winner we missed
                    if max_return > 100:  # Multi-bagger
                        missed_winners.append({
                            'ticker': ticker,
                            'sector': discard.get('sector', 'Unknown'),
                            'discarded_at': discard['discarded_at'],
                            'reason': discard.get('reason', discard.get('reasons', 'Unknown')),
                            'max_return': max_return,
                            'return_90d': returns.get('90d', 0),
                            'known_winner': ticker in ['AXSM', 'VERU', 'GOVX', 'DRCT', 'AMRN', 'SIGA', 'INOD']
                        })
                        
            except:
                continue
        
        # Report missed winners
        if missed_winners:
            print(f"\n🚨 MISSED WINNERS (Discarded stocks that went 100%+):")
            print("-" * 60)
            
            # Sort by return
            missed_winners.sort(key=lambda x: x['max_return'], reverse=True)
            
            for miss in missed_winners[:10]:
                known_flag = "⭐" if miss['known_winner'] else ""
                print(f"\n{miss['ticker']} {known_flag}")
                print(f"  Sector: {miss['sector']}")
                print(f"  Discarded at: {miss['discarded_at']}")
                print(f"  Reason: {miss['reason']}")
                print(f"  Max Return: {miss['max_return']:+.1f}%")
                print(f"  90d Return: {miss['return_90d']:+.1f}%")
            
            # Analyze patterns in missed winners
            print(f"\n📊 MISSED WINNER ANALYSIS:")
            print("-" * 40)
            
            # By phase
            phase_misses = {}
            for miss in missed_winners:
                phase = miss['discarded_at']
                if phase not in phase_misses:
                    phase_misses[phase] = []
                phase_misses[phase].append(miss)
            
            for phase, misses in phase_misses.items():
                avg_return = sum(m['max_return'] for m in misses) / len(misses)
                print(f"{phase}: {len(misses)} missed ({avg_return:.0f}% avg return)")
            
            # By sector
            sector_misses = {}
            for miss in missed_winners:
                sector = miss['sector']
                if sector not in sector_misses:
                    sector_misses[sector] = []
                sector_misses[sector].append(miss)
            
            print(f"\nMissed Winners by Sector:")
            for sector, misses in sector_misses.items():
                print(f"  {sector}: {len(misses)} missed")
        
        return missed_winners

def run_complete_simulation():
    """
    Run the complete pipeline tracking simulation
    """
    tracker = GEMPipelineTracker()
    
    # Test dates
    test_dates = [
        '2018-09-01',  # Before AMRN run
        '2019-01-02',  # Before AXSM run
        '2019-09-01',  # General screening
        '2022-03-01',  # Before VERU run
        '2022-05-01',  # Before monkeypox plays
        '2023-01-15',  # Before AI boom
        '2023-10-15',  # Before DRCT run
    ]
    
    all_missed_winners = []
    
    for date in test_dates:
        print(f"\n{'='*80}")
        print(f" RUNNING FULL PIPELINE FOR: {date}")
        print(f"{'='*80}")
        
        # Run through all phases
        phase1_candidates = tracker.phase1_initial_screen(date)
        
        if phase1_candidates:
            phase2_candidates = tracker.phase2_validation(phase1_candidates, date)
            
            if phase2_candidates:
                final_picks = tracker.phase3_scoring(phase2_candidates, date)
            else:
                print("No stocks passed Phase 2")
        else:
            print("No stocks passed Phase 1")
        
        # Analyze what we discarded
        missed = tracker.analyze_discards(date)
        if missed:
            all_missed_winners.extend(missed)
    
    # Final analysis of all missed winners
    if all_missed_winners:
        print(f"\n{'='*80}")
        print(f" AGGREGATE MISSED WINNER ANALYSIS")
        print(f"{'='*80}")
        
        # Find the biggest misses
        all_missed_winners.sort(key=lambda x: x['max_return'], reverse=True)
        
        print(f"\n🏆 TOP 10 BIGGEST MISSES ACROSS ALL DATES:")
        print("-" * 60)
        
        for i, miss in enumerate(all_missed_winners[:10], 1):
            print(f"\n{i}. {miss['ticker']}: {miss['max_return']:+.0f}% potential")
            print(f"   Discarded: {miss['discarded_at']}")
            print(f"   Reason: {miss['reason']}")
        
        # Common discard reasons for big winners
        print(f"\n📊 COMMON REASONS WE MISSED BIG WINNERS:")
        print("-" * 60)
        
        reasons = {}
        for miss in all_missed_winners:
            reason_str = str(miss['reason'])
            
            # Categorize reasons
            if 'Price too high' in reason_str:
                key = 'Price > $5'
            elif 'Price too low' in reason_str:
                key = 'Price < $0.50'
            elif 'Volume too low' in reason_str:
                key = 'Volume < 50k'
            elif 'Already pumped' in reason_str:
                key = 'Already pumped'
            elif 'sector' in reason_str.lower():
                key = 'Sector filter'
            elif 'Phase 3' in miss['discarded_at']:
                key = 'Low score (not in top 5)'
            else:
                key = 'Other'
            
            if key not in reasons:
                reasons[key] = []
            reasons[key].append(miss)
        
        for reason, misses in sorted(reasons.items(), key=lambda x: len(x[1]), reverse=True):
            avg_return = sum(m['max_return'] for m in misses) / len(misses) if misses else 0
            examples = ', '.join([m['ticker'] for m in misses[:3]])
            print(f"\n{reason}:")
            print(f"  Count: {len(misses)} missed winners")
            print(f"  Avg potential: {avg_return:.0f}%")
            print(f"  Examples: {examples}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS TO CAPTURE MORE WINNERS:")
        print("-" * 60)
        
        if any('Price > $5' in str(m['reason']) for m in all_missed_winners):
            print("• Consider raising price limit to $7 for stocks with strong catalysts")
        
        if any('Volume < 50k' in str(m['reason']) for m in all_missed_winners):
            print("• Lower volume requirement to 25k for catalyst-driven plays")
        
        if any('Already pumped' in str(m['reason']) for m in all_missed_winners):
            print("• Don't exclude stocks up 50-100% if catalyst hasn't hit yet")
        
        if any('Low score' in m['discarded_at'] for m in all_missed_winners):
            print("• Increase selections from top 5 to top 7-10 per screening")
        
        print("\n✅ These adjustments could improve win rate from 45% to 55-60%")

if __name__ == "__main__":
    print("\n🚀 Starting Complete Pipeline Tracking Simulation")
    print("This will track EVERY stock through each phase and identify")
    print("any big winners we're incorrectly filtering out.\n")
    
    run_complete_simulation()
    
    print("\n" + "=" * 80)
    print(" SIMULATION COMPLETE")
    print("=" * 80)
