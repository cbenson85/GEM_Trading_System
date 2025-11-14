import os
import glob
import json
import pandas as pd

def collect_and_generate_master_report():
    """
    Scans for all 'buy_signals_*.json' files in the artifact directory,
    combines them, and generates a final master report.
    """
    print("--- Starting Master Report Collection ---")
    
    # Path where 'download-artifact' action places all files
    artifact_path = 'all_artifacts' 
    if not os.path.exists(artifact_path):
        print(f"Error: Artifact directory '{artifact_path}' not found.")
        print("This script should be run after the 'download-artifact' step.")
        # Create a dummy report
        with open("FINAL_backtest_report.txt", "w") as f:
            f.write("FINAL REPORT FAILED: Artifact directory not found.\n")
        return

    json_files = glob.glob(os.path.join(artifact_path, 'buy_signals_*.json'))
    
    if not json_files:
        print("No 'buy_signals_*.json' files found in artifacts.")
        with open("FINAL_backtest_report.txt", "w") as f:
            f.write("FINAL REPORT FAILED: No 'buy_signals_*.json' files found.\n")
        return

    print(f"Found {len(json_files)} batch JSON files to aggregate.")

    all_signals = []
    for f_path in json_files:
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
                if data:
                    all_signals.extend(data)
        except Exception as e:
            print(f"Warning: Could not read or parse {f_path}: {e}")

    if not all_signals:
        print("No valid signals collected from JSON files.")
        with open("FINAL_backtest_report.txt", "w") as f:
            f.write("FINAL REPORT: No 'BUY' signals found across all batches.\n")
        return

    # --- Generate Master DataFrame and Report ---
    master_df = pd.DataFrame(all_signals)
    master_df.dropna(subset=['fwd_return_90d', 'spy_fwd_return_90d'], inplace=True)
    
    total_signals = len(master_df)
    
    # Save the final combined JSON
    master_df.to_json("FINAL_buy_signals.json", orient='records', indent=2)
    
    report_content = "--- MASTER BACKTEST REPORT (2022-2023) ---\n\n"
    report_content += f"Total 'BUY' Signals Generated: {total_signals}\n"
    
    if total_signals > 0:
        # --- Overall Performance ---
        wins = master_df[master_df['fwd_return_90d'] > master_df['spy_fwd_return_90d']]
        win_rate = (len(wins) / total_signals) * 100
        
        supernova_hits = master_df[master_df['fwd_return_90d'] >= 5.0] # 500%+
        positive_gains = master_df[master_df['fwd_return_90d'] > 0]
        false_positives = master_df[master_df['fwd_return_90d'] <= 0]
        
        avg_gain_pct = master_df['fwd_return_90d'].mean() * 100
        median_gain_pct = master_df['fwd_return_90d'].median() * 100
        avg_spy_gain_pct = master_df['spy_fwd_return_90d'].mean() * 100
        
        report_content += "\n--- Overall Performance (90-Day Hold) ---\n"
        report_content += f"Win Rate (vs. SPY): {win_rate:.2f}%\n"
        report_content += f"Win Rate (vs. 0%): {(len(positive_gains) / total_signals) * 100:.2f}%\n"
        report_content += f"False Positive Rate (<= 0%): {(len(false_positives) / total_signals) * 100:.2f}%\n"
        report_content += "---------------------------------------\n"
        report_content += f"Average Gain: {avg_gain_pct:.2f}%\n"
        report_content += f"Median Gain: {median_gain_pct:.2f}%\n"
        report_content += f"Average SPY Gain: {avg_spy_gain_pct:.2f}%\n"
        report_content += "---------------------------------------\n"
        report_content += f"Supernova Hits (500%+): {len(supernova_hits)}\n"
        report_content += f"Total Tickers Found: {master_df['ticker'].nunique()}\n"

        # --- Top 10 Winners ---
        top_10 = master_df.sort_values(by='fwd_return_90d', ascending=False).head(10)
        report_content += "\n--- Top 10 Winners ---\n"
        for _, row in top_10.iterrows():
            gain = row['fwd_return_90d'] * 100
            report_content += f"  - {row['date']} | {row['ticker']:<8} | +{gain:.2f}%\n"

        # --- Top 10 Losers (False Positives) ---
        bottom_10 = master_df.sort_values(by='fwd_return_90d', ascending=True).head(10)
        report_content += "\n--- Top 10 Losers (False Positives) ---\n"
        for _, row in bottom_10.iterrows():
            gain = row['fwd_return_90d'] * 100
            report_content += f"  - {row['date']} | {row['ticker']:<8} | {gain:.2f}%\n"
            
        # --- Analysis by Sector ---
        report_content += "\n--- Performance by Sector ---\n"
        for sector in master_df['sector'].unique():
            sector_df = master_df[master_df['sector'] == sector]
            sector_wins = sector_df[sector_df['fwd_return_90d'] > sector_df['spy_fwd_return_90d']]
            sector_win_rate = (len(sector_wins) / len(sector_df)) * 100
            sector_avg_gain = sector_df['fwd_return_90d'].mean() * 100
            report_content += f"  Sector: {sector}\n"
            report_content += f"    Signals: {len(sector_df)}\n"
            report_content += f"    Win Rate: {sector_win_rate:.2f}%\n"
            report_content += f"    Avg Gain: {sector_avg_gain:.2f}%\n"
            
    else:
        report_content += "\nNo 'BUY' signals had complete 90-day forward data to analyze.\n"

    # Save the final report
    with open("FINAL_backtest_report.txt", 'w') as f:
        f.write(report_content)
        
    print("\n--- Master Report Generated ---")
    print(report_content)
    print("Saved FINAL_backtest_report.txt")
    print("Saved FINAL_buy_signals.json")


if __name__ == "__main__":
    collect_and_generate_master_report()
