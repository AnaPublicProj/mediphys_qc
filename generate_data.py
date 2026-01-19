import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate():
    # We will store all our generated rows in this list before creating the DataFrame
    data = []
    start_date = datetime(2023, 1, 1)
    
    # 1. LINAC SIMULATION: 

    # This machine works perfectly until the very last day, where it breaks.
    # This is Useful for testing if our code catches single-point failures.
    for i in range(30):
        date = start_date + timedelta(days=i)
        
        # Generate normal daily readings with a tiny bit of random noise
        dose = np.random.normal(100.0, 0.5)  # Target is 100
        sym = np.random.normal(0.5, 0.2)     # Target is 0.5
        
        # On the last day (index 29), force a bad reading
        if i == 29:
            dose = 104.5 # This is >2% deviation, so it should trigger a fail
            
        data.append([date, "Linac_1", "Dose_Output", dose])
        data.append([date, "Linac_1", "Symmetry", sym])

    # 2. CT SCANNER SIMULATION: 

    # This machine slowly gets worse over time.
    # This is Useful for testing if our linear regression (slope check) works.
    
    # Create a smooth array of 30 values going from 0 up to 6
    drift_values = np.linspace(0, 6.0, 30) 
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        # Take the drift value and add some random noise so it looks like real data
        val = drift_values[i] + np.random.normal(0, 0.5) 
        data.append([date, "CT_Scanner_A", "Water_HU", val])

    # 3. GAMMA CAMERA SIMULATION: 

    # This machine never fails. It's our control group.
    for i in range(30):
        date = start_date + timedelta(days=i)
        val = np.random.normal(2.5, 0.1) # Fluctuate slightly around 2.5%
        data.append([date, "Gamma_Cam_SPECT", "Uniformity", val])

    # 4. MRI SCANNER SIMULATION:

    # This simulates a loose cable or bad connection.
    # It works most days, but fails randomly (spikes) on specific days.

    for i in range(30):
        date = start_date + timedelta(days=i)
        
        # Signal-to-Noise Ratio (SNR): Target is 50
        snr_val = np.random.normal(50.0, 1.0)
        
        # Force a failure on day 10 and day 20 (random drops in signal)
        if i == 10 or i == 20:
            snr_val = 42.0 # Significant drop, should fail
        
        # Geometric Distortion: Stays very stable
        dist_val = abs(np.random.normal(0.2, 0.05))

        data.append([date, "MRI_Scanner_3T", "SNR_Coil_1", snr_val])
        data.append([date, "MRI_Scanner_3T", "Geometric_Distortion", dist_val])

    # Convert our list of lists into a Pandas DataFrame and save it
    df = pd.DataFrame(data, columns=["Date", "Machine_ID", "Metric", "Value"])
    df.to_excel("daily_qc_log.xlsx", index=False)
    print(f" [GENERATOR] Created 'daily_qc_log.xlsx' with {len(df)} records.")

if __name__ == "__main__":
    generate()