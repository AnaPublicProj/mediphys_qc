import pandas as pd
import yaml
import argparse
import matplotlib.pyplot as plt
from scipy.stats import linregress
import os
import sys
import sqlite3
import logging

# Set up logging to write to both a file and the screen
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("qc_audit.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# stop matplotlib from cluttering the logs with debug info
logging.getLogger('matplotlib').setLevel(logging.WARNING)

class QualityControlEngine:
    def __init__(self, config_path, db_path="qc_history.db"):
        self.db_path = db_path
        
        # Open and load the settings from the yml file
        try:
            with open(config_path, "r") as f:
                self.rules = yaml.safe_load(f)
            logging.info(f"Configuration loaded successfully from {config_path}")
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
            
        self.drift_alerts = []
        
        # Make sure the database is ready when we start
        self.init_database()

    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create the table only if it doesn't exist yet
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qc_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP,
                    machine_id TEXT,
                    metric TEXT,
                    value REAL,
                    qc_status TEXT,
                    audit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logging.info(f"Database connection verified at {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Database initialization failed: {e}")

    def save_to_database(self, df):
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Select only the columns we need for the database to avoid errors
            data_to_save = df[['Date', 'Machine_ID', 'Metric', 'Value', 'QC_Status']].copy()
            
            # Rename columns to lowercase to match standard SQL style
            data_to_save.columns = ['date', 'machine_id', 'metric', 'value', 'qc_status']
            
            # Write data to the table, appending to existing records
            data_to_save.to_sql('qc_records', conn, if_exists='append', index=False)
            conn.close()
            
            logging.info(f"Successfully archived {len(df)} records to database.")
            return self.db_path
        except Exception as e:
            logging.error(f"Failed to save records to database: {e}")
            return None

    def check_compliance(self, machine, metric, value):
        # Check if we actually have a rule for this machine/metric in the config
        if machine not in self.rules or metric not in self.rules[machine]:
            logging.warning(f"Configuration missing for {machine} - {metric}")
            return "UNKNOWN_CONFIG"
            
        rule = self.rules[machine][metric]
        target = rule['target']
        tol = rule['tolerance_abs']
        
        # See how far off the value is from the target
        diff = abs(value - target)
        
        # If the difference is bigger than the allowed tolerance, mark as FAIL
        if diff > tol:
            return f"FAIL (Dev: {diff:.2f})"
        return "PASS"

    def analyze_drift(self, dates, values, machine, metric):
        # We need at least 5 points to make a reliable trend line
        if len(values) < 5: 
            return
        
        # Convert dates to number of days so we can do math on them
        days = (dates - dates.min()).dt.days
        slope, intercept, r, p, err = linregress(days, values)
        
        # If the slope (rate of change) is too steep, warn the user
        if abs(slope) > 0.1:
            alert_msg = f"[{machine}] {metric}: Significant Drift detected (Slope: {slope:.3f}/day)"
            self.drift_alerts.append(alert_msg)
            logging.warning(alert_msg)

    def generate_plot(self, df_subset, machine, metric):
        try:
            rule = self.rules[machine][metric]
            target = rule['target']
            tol = rule['tolerance_abs']
            
            # Start a new plot
            plt.figure(figsize=(10, 5))
            plt.plot(df_subset['Date'], df_subset['Value'], 'o-', label='Measured')
            
            # Add horizontal lines for Target and Limits
            plt.axhline(target, color='green', linestyle='--', label='Target')
            plt.axhline(target + tol, color='red', linestyle=':', label='Upper Limit')
            plt.axhline(target - tol, color='red', linestyle=':', label='Lower Limit')
            
            plt.title(f"QC Trend: {machine} - {metric}")
            plt.ylabel(rule['unit'])
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Create the folder if it's missing, then save the chart
            os.makedirs("qc_reports/plots", exist_ok=True)
            plot_path = f"qc_reports/plots/{machine}_{metric}.png"
            plt.savefig(plot_path)
            plt.close() # Close the plot to free up memory
        except Exception as e:
            logging.error(f"Failed to generate plot for {machine}-{metric}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Medical Physics QC Auditor (CLI)")
    parser.add_argument("--input", required=True, help="Path to Excel data file")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    logging.info("INITIALIZING MEDIPHYS QC AUDITOR...")
    
    # 1. Load Resources and Data
    try:
        engine = QualityControlEngine(args.config)
        df = pd.read_excel(args.input)
        df['Date'] = pd.to_datetime(df['Date'])
        logging.info(f"Data loaded: {len(df)} records across {df['Machine_ID'].nunique()} machines.")
    except Exception as e:
        logging.critical(f"Critical error loading input files: {e}")
        sys.exit(1)

    # 2. Run Checks
    # We loop through each row to check pass/fail status
    logging.info("Running compliance checks...")
    results = []
    for idx, row in df.iterrows():
        status = engine.check_compliance(row['Machine_ID'], row['Metric'], row['Value'])
        results.append(status)
    
    df['QC_Status'] = results

    # 3. Trends and Plots
    # Group data by machine and metric to analyze history
    logging.info("Analyzing trends and generating plots...")
    groups = df.groupby(['Machine_ID', 'Metric'])
    for (machine, metric), group_data in groups:
        # Only run analysis if we recognize the machine/metric
        if machine in engine.rules and metric in engine.rules[machine]:
            engine.analyze_drift(group_data['Date'], group_data['Value'], machine, metric)
            engine.generate_plot(group_data, machine, metric)

    # 4. Save Everything
    os.makedirs("qc_reports", exist_ok=True)
    
    # Save to database (append mode)
    db_file = engine.save_to_database(df)
    
    # Save to Excel (overwrite mode)
    out_path = "qc_reports/audit_results.xlsx"
    try:
        df.to_excel(out_path, index=False)
        logging.info(f"Excel report generated: {out_path}")
    except Exception as e:
        logging.error(f"Failed to save Excel report: {e}")

    # Print final summary to log
    logging.info("="*40)
    logging.info("       AUDIT COMPLETE       ")
    logging.info("="*40)
    logging.info(f"1. Data Log (Excel): {out_path}")
    logging.info(f"2. History (DB):     {db_file} (Appended)")
    logging.info(f"3. Plots:            qc_reports/plots/")
    
    if engine.drift_alerts:
        logging.warning("[!] PREDICTIVE MAINTENANCE ALERTS FOUND:")
        for alert in engine.drift_alerts:
            logging.warning(f"    {alert}")
    else:
        logging.info("[OK] No significant drift detected.")
    logging.info("="*40)

if __name__ == "__main__":
    main()