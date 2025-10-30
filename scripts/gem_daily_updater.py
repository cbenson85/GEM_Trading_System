#!/usr/bin/env python3
"""
GEM Trading System Daily Updater
Automatically updates GitHub repository with trading data
"""

import json
import datetime
import subprocess
import os
from typing import Dict, List

class GEMUpdater:
    def __init__(self):
        self.repo_path = "/path/to/GEM_Trading_System"  # Update this path
        self.today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Single source of truth - all data in one JSON
        self.data_file = f"{self.repo_path}/Daily_Logs/master_trading_data.json"
        
    def load_data(self) -> Dict:
        """Load existing data or create new structure"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        else:
            return self.create_empty_structure()
    
    def create_empty_structure(self) -> Dict:
        """Create initial data structure"""
        return {
            "last_updated": self.today,
            "portfolio": {
                "account_value": 10000,
                "cash_available": 2000,
                "positions": {}
            },
            "trades": {
                "open": {},
                "closed": {}
            },
            "watchlist": {},
            "daily_screens": {},
            "system_notes": []
        }
    
    def add_position(self, ticker: str, entry_date: str, entry_price: float, 
                    shares: int, score: int, catalyst: str):
        """Add or update a position"""
        data = self.load_data()
        data["portfolio"]["positions"][ticker] = {
            "entry_date": entry_date,
            "entry_price": entry_price,
            "shares": shares,
            "score": score,
            "catalyst": catalyst,
            "current_price": None,  # Will be updated by price fetcher
            "days_held": (datetime.date.today() - datetime.datetime.strptime(entry_date, "%Y-%m-%d").date()).days,
            "status": "NO_STOP" if data["portfolio"]["positions"][ticker]["days_held"] < 30 else "ACTIVE"
        }
        self.save_data(data)
    
    def close_position(self, ticker: str, exit_price: float, exit_date: str):
        """Move position from open to closed"""
        data = self.load_data()
        if ticker in data["portfolio"]["positions"]:
            position = data["portfolio"]["positions"].pop(ticker)
            position["exit_price"] = exit_price
            position["exit_date"] = exit_date
            position["pnl_percent"] = ((exit_price - position["entry_price"]) / position["entry_price"]) * 100
            position["pnl_dollars"] = (exit_price - position["entry_price"]) * position["shares"]
            
            # Move to closed trades
            data["trades"]["closed"][f"{ticker}_{exit_date}"] = position
            
            # Update cash
            data["portfolio"]["cash_available"] += exit_price * position["shares"]
        
        self.save_data(data)
    
    def add_to_watchlist(self, ticker: str, score: int, catalyst: str, catalyst_date: str):
        """Add ticker to watchlist"""
        data = self.load_data()
        data["watchlist"][ticker] = {
            "date_added": self.today,
            "score": score,
            "catalyst": catalyst,
            "catalyst_date": catalyst_date
        }
        self.save_data(data)
    
    def save_data(self, data: Dict):
        """Save data and generate markdown reports"""
        # Update timestamp
        data["last_updated"] = self.today
        
        # Save JSON
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Generate markdown files
        self.generate_portfolio_markdown(data)
        self.generate_trade_journal(data)
        
    def generate_portfolio_markdown(self, data: Dict):
        """Generate Live_Portfolio_Tracking.md from JSON data"""
        md_content = f"""# GEM Live Portfolio Tracking - Roth IRA
**Last Updated**: {self.today}
**Account Value**: ${data['portfolio']['account_value']:,.2f}
**Cash Available**: ${data['portfolio']['cash_available']:,.2f}

## Active Positions

| Ticker | Entry Date | Entry Price | Days Held | Score | Status | P&L |
|--------|------------|-------------|-----------|--------|---------|-----|
"""
        for ticker, pos in data["portfolio"]["positions"].items():
            status = "🔴 NO STOP" if pos["days_held"] < 30 else "🟢 ACTIVE"
            md_content += f"| {ticker} | {pos['entry_date']} | ${pos['entry_price']} | {pos['days_held']} | {pos['score']} | {status} | TBD |\n"
        
        # Add closed trades section
        md_content += "\n## Recent Closed Trades\n\n"
        md_content += "| Ticker | Entry | Exit | Days | P&L % | Result |\n"
        md_content += "|--------|-------|------|------|-------|--------|\n"
        
        for trade_id, trade in list(data["trades"]["closed"].items())[-10:]:  # Last 10 trades
            ticker = trade_id.split('_')[0]
            md_content += f"| {ticker} | {trade['entry_date']} | {trade['exit_date']} | {trade['days_held']} | {trade['pnl_percent']:.1f}% | ${trade['pnl_dollars']:.0f} |\n"
        
        # Save markdown
        with open(f"{self.repo_path}/Daily_Logs/Live_Portfolio_Tracking.md", 'w') as f:
            f.write(md_content)
    
    def generate_trade_journal(self, data: Dict):
        """Generate trade journal from closed trades"""
        md_content = "# GEM v5 Trade Journal\n\n"
        
        for trade_id, trade in data["trades"]["closed"].items():
            ticker = trade_id.split('_')[0]
            md_content += f"""
## {ticker} - {trade['exit_date']}
- Entry: {trade['entry_date']} @ ${trade['entry_price']}
- Exit: {trade['exit_date']} @ ${trade['exit_price']}
- Result: {trade['pnl_percent']:.1f}% (${trade['pnl_dollars']:.0f})
- Days Held: {trade['days_held']}
- Original Score: {trade['score']}
- Catalyst: {trade['catalyst']}

---
"""
        
        with open(f"{self.repo_path}/Daily_Logs/Trade_Journal.md", 'w') as f:
            f.write(md_content)
    
    def commit_and_push(self):
        """Commit and push changes to GitHub"""
        os.chdir(self.repo_path)
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", f"Daily update: {self.today}"])
        subprocess.run(["git", "push"])
        print(f"✅ GitHub updated: {self.today}")

# Command line interface
if __name__ == "__main__":
    import sys
    
    updater = GEMUpdater()
    
    if len(sys.argv) < 2:
        print("""
Usage:
  python gem_daily_updater.py add_position TICKER DATE PRICE SHARES SCORE "CATALYST"
  python gem_daily_updater.py close_position TICKER PRICE DATE
  python gem_daily_updater.py add_watchlist TICKER SCORE "CATALYST" DATE
  python gem_daily_updater.py update  # Just regenerate files from JSON
  python gem_daily_updater.py push    # Commit and push to GitHub
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add_position":
        updater.add_position(sys.argv[2], sys.argv[3], float(sys.argv[4]), 
                           int(sys.argv[5]), int(sys.argv[6]), sys.argv[7])
        print(f"✅ Added position: {sys.argv[2]}")
    
    elif command == "close_position":
        updater.close_position(sys.argv[2], float(sys.argv[3]), sys.argv[4])
        print(f"✅ Closed position: {sys.argv[2]}")
    
    elif command == "add_watchlist":
        updater.add_to_watchlist(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5])
        print(f"✅ Added to watchlist: {sys.argv[2]}")
    
    elif command == "update":
        data = updater.load_data()
        updater.save_data(data)
        print("✅ Files regenerated from master data")
    
    elif command == "push":
        updater.commit_and_push()
    
    else:
        print(f"Unknown command: {command}")
