"""
Phase 3B Orchestrator - Runs all automation scripts on all 72 stocks
"""

import os
import sys
import json
from datetime import datetime
import subprocess

class Phase3BOrchestrator:
    def __init__(self, stocks_file, output_dir='Verified_Backtest_Data'):
        """Initialize orchestrator"""
        self.stocks_file = stocks_file
        self.output_dir = output_dir
        self.scripts = [
            {
                'name': 'Sector Context Analysis',
                'script': 'sector_context_analyzer.py',
                'description': 'Relative strength vs SPY/QQQ',
                'estimated_time_mins': 30
            },
            {
                'name': 'Insider Transactions',
                'script': 'insider_transactions_scraper.py',
                'description': 'Form 4 insider buying clusters',
                'estimated_time_mins': 90
            },
            {
                'name': 'News Volume',
                'script': 'news_volume_counter.py',
                'description': 'News article acceleration',
                'estimated_time_mins': 120
            }
        ]
        
    def run_all(self):
        """
        Run all automation scripts
        """
        print("=" * 80)
        print("PHASE 3B ORCHESTRATOR - Full Automation Run")
        print("=" * 80)
        print(f"Input: {self.stocks_file}")
        print(f"Output: {self.output_dir}/")
        print(f"Scripts: {len(self.scripts)}")
        
        # Load stocks to get count
        with open(self.stocks_file, 'r') as f:
            data = json.load(f)
            stocks = data.get('stocks', data)
            stock_count = len(stocks)
        
        print(f"Stocks: {stock_count}")
        
        # Calculate total estimated time
        total_time = sum(s['estimated_time_mins'] for s in self.scripts)
        print(f"Estimated Time: {total_time} minutes ({total_time/60:.1f} hours)")
        print("=" * 80)
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Run each script
        results = []
        
        for i, script_info in enumerate(self.scripts):
            print(f"\n{'='*80}")
            print(f"RUNNING SCRIPT {i+1}/{len(self.scripts)}: {script_info['name']}")
            print(f"{'='*80}")
            print(f"Script: {script_info['script']}")
            print(f"Description: {script_info['description']}")
            print(f"Estimated Time: {script_info['estimated_time_mins']} minutes")
            print(f"{'='*80}\n")
            
            start_time = datetime.now()
            
            try:
                # Run script
                result = subprocess.run(
                    ['python', script_info['script'], self.stocks_file],
                    capture_output=True,
                    text=True,
                    timeout=7200  # 2 hour timeout
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 60
                
                # Check result
                if result.returncode == 0:
                    status = 'SUCCESS'
                    print(f"\n✅ {script_info['name']} completed successfully")
                else:
                    status = 'ERROR'
                    print(f"\n❌ {script_info['name']} failed")
                    print(f"Error: {result.stderr}")
                
                print(f"Duration: {duration:.1f} minutes")
                
                results.append({
                    'script': script_info['name'],
                    'file': script_info['script'],
                    'status': status,
                    'duration_minutes': round(duration, 2),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'stdout': result.stdout[-1000:] if result.stdout else '',
                    'stderr': result.stderr[-1000:] if result.stderr else ''
                })
                
            except subprocess.TimeoutExpired:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 60
                
                print(f"\n⏱️ {script_info['name']} timed out after {duration:.1f} minutes")
                
                results.append({
                    'script': script_info['name'],
                    'file': script_info['script'],
                    'status': 'TIMEOUT',
                    'duration_minutes': round(duration, 2),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                })
                
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 60
                
                print(f"\n❌ {script_info['name']} error: {e}")
                
                results.append({
                    'script': script_info['name'],
                    'file': script_info['script'],
                    'status': 'ERROR',
                    'duration_minutes': round(duration, 2),
                    'error': str(e),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                })
        
        # Final summary
        print("\n" + "=" * 80)
        print("ORCHESTRATOR COMPLETE")
        print("=" * 80)
        
        successful = sum(1 for r in results if r['status'] == 'SUCCESS')
        failed = sum(1 for r in results if r['status'] in ['ERROR', 'TIMEOUT'])
        total_duration = sum(r['duration_minutes'] for r in results)
        
        print(f"Scripts Run: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total Duration: {total_duration:.1f} minutes ({total_duration/60:.1f} hours)")
        
        # Save results
        output_file = f'{self.output_dir}/phase3b_orchestrator_results.json'
        with open(output_file, 'w') as f:
            json.dump({
                'run_date': datetime.now().isoformat(),
                'stocks_file': self.stocks_file,
                'stock_count': stock_count,
                'scripts_run': len(results),
                'successful': successful,
                'failed': failed,
                'total_duration_minutes': round(total_duration, 2),
                'results': results
            }, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        
        # Generate next steps
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("1. Review individual JSON files in Verified_Backtest_Data/")
        print("2. Run correlation analysis to aggregate results")
        print("3. Update correlation matrix with new patterns")
        print("4. Generate updated screening criteria")
        print("=" * 80)
        
        return results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python phase3b_orchestrator.py explosive_stocks_CLEAN.json")
        sys.exit(1)
    
    stocks_file = sys.argv[1]
    
    if not os.path.exists(stocks_file):
        print(f"Error: File not found: {stocks_file}")
        sys.exit(1)
    
    orchestrator = Phase3BOrchestrator(stocks_file)
    orchestrator.run_all()
