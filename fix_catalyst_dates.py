"""
Fix Catalyst Dates in Explosive Stocks
Corrects future dates and calculates proper historical explosion dates
"""

import json
from datetime import datetime, timedelta
import os

def fix_catalyst_dates():
    """Fix incorrect catalyst dates in explosive_stocks_CLEAN.json"""
    
    print("=" * 60)
    print("FIXING CATALYST DATES")
    print("=" * 60)
    
    # Load the data
    input_file = 'Verified_Backtest_Data/explosive_stocks_CLEAN.json'
    
    with open(input_file, 'r') as f:
        stocks = json.load(f)
    
    print(f"\nLoaded {len(stocks)} stocks")
    
    fixed_count = 0
    future_dates = []
    
    for stock in stocks:
        ticker = stock['ticker']
        entry_date = stock.get('entry_date')
        catalyst_date = stock.get('catalyst_date')
        days_to_peak = stock.get('days_to_peak', 1)
        
        # Check if catalyst_date is in the future or missing
        needs_fix = False
        
        if catalyst_date:
            catalyst_dt = datetime.fromisoformat(catalyst_date)
            if catalyst_dt > datetime.now():
                print(f"\n❌ {ticker}: Future catalyst date detected: {catalyst_date}")
                future_dates.append(ticker)
                needs_fix = True
        else:
            print(f"\n❌ {ticker}: Missing catalyst date")
            needs_fix = True
        
        # Fix the date
        if needs_fix and entry_date:
            # Calculate proper catalyst date: entry_date + days_to_peak
            entry_dt = datetime.fromisoformat(entry_date)
            proper_catalyst_dt = entry_dt + timedelta(days=days_to_peak)
            proper_catalyst_date = proper_catalyst_dt.strftime('%Y-%m-%d')
            
            print(f"   Fixed: {proper_catalyst_date} (entry {entry_date} + {days_to_peak} days)")
            
            stock['catalyst_date'] = proper_catalyst_date
            stock['catalyst_date_source'] = 'calculated_from_entry_plus_days'
            fixed_count += 1
        
        # Verify the dates make sense
        if entry_date and stock.get('catalyst_date'):
            entry_dt = datetime.fromisoformat(entry_date)
            catalyst_dt = datetime.fromisoformat(stock['catalyst_date'])
            actual_days = (catalyst_dt - entry_dt).days
            
            if actual_days != days_to_peak:
                print(f"⚠️  {ticker}: Days mismatch - recorded: {days_to_peak}, actual: {actual_days}")
                # Fix it
                proper_catalyst_dt = entry_dt + timedelta(days=days_to_peak)
                stock['catalyst_date'] = proper_catalyst_dt.strftime('%Y-%m-%d')
                fixed_count += 1
    
    # Save the fixed data
    output_file = 'Verified_Backtest_Data/explosive_stocks_FIXED_DATES.json'
    
    with open(output_file, 'w') as f:
        json.dump(stocks, f, indent=2)
    
    # Also create a backup of the original
    backup_file = 'Verified_Backtest_Data/explosive_stocks_CLEAN_BACKUP.json'
    if not os.path.exists(backup_file):
        import shutil
        shutil.copy(input_file, backup_file)
        print(f"\n📁 Backup saved to: {backup_file}")
    
    print(f"\n" + "=" * 60)
    print(f"FIXES COMPLETE")
    print(f"=" * 60)
    print(f"Fixed {fixed_count} catalyst dates")
    print(f"Stocks with future dates: {len(future_dates)}")
    if future_dates:
        print(f"  {', '.join(future_dates[:10])}")
    print(f"\n✅ Fixed data saved to: {output_file}")
    print(f"⚠️  Original backed up to: {backup_file}")
    
    # Show sample of fixed data
    print(f"\n📊 SAMPLE FIXED DATA:")
    for stock in stocks[:5]:
        print(f"{stock['ticker']:6} | Entry: {stock['entry_date']} | Catalyst: {stock['catalyst_date']} | Days: {stock.get('days_to_peak', 0)}")
    
    return stocks

def validate_dates(stocks):
    """Validate all dates are historical and logical"""
    
    print("\n" + "=" * 60)
    print("VALIDATING DATES")
    print("=" * 60)
    
    issues = []
    today = datetime.now()
    
    for stock in stocks:
        ticker = stock['ticker']
        entry_date = stock.get('entry_date')
        catalyst_date = stock.get('catalyst_date')
        
        if not entry_date or not catalyst_date:
            issues.append(f"{ticker}: Missing dates")
            continue
        
        entry_dt = datetime.fromisoformat(entry_date)
        catalyst_dt = datetime.fromisoformat(catalyst_date)
        
        # Check for future dates
        if catalyst_dt > today:
            issues.append(f"{ticker}: Catalyst date {catalyst_date} is in the future!")
        
        if entry_dt > today:
            issues.append(f"{ticker}: Entry date {entry_date} is in the future!")
        
        # Check logical order
        if catalyst_dt < entry_dt:
            issues.append(f"{ticker}: Catalyst before entry!")
        
        # Check against year_discovered
        year_discovered = stock.get('year_discovered')
        if year_discovered:
            catalyst_year = catalyst_dt.year
            if catalyst_year != year_discovered:
                # Allow for year boundary (discovered in year after catalyst)
                if not (catalyst_year == year_discovered - 1 and catalyst_dt.month >= 10):
                    issues.append(f"{ticker}: Year mismatch - discovered {year_discovered}, catalyst {catalyst_year}")
    
    if issues:
        print(f"⚠️  Found {len(issues)} issues:")
        for issue in issues[:20]:  # Show first 20
            print(f"  - {issue}")
    else:
        print("✅ All dates validated successfully!")
    
    return len(issues) == 0

if __name__ == "__main__":
    # Fix the dates
    fixed_stocks = fix_catalyst_dates()
    
    # Validate the fixes
    is_valid = validate_dates(fixed_stocks)
    
    if is_valid:
        print("\n🎉 All catalyst dates fixed and validated!")
        print("\nNext steps:")
        print("1. Rename explosive_stocks_FIXED_DATES.json to explosive_stocks_CLEAN.json")
        print("2. Run your Phase 3 workflow again")
        print("3. You should now get real historical data!")
    else:
        print("\n⚠️  Some dates still have issues - review the output above")
