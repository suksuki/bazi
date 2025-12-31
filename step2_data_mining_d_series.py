
import numpy as np
import json
import random
from typing import List, Dict

def generate_d_series_samples(pattern_id, count=250):
    """
    Simulates FDS-V1.4 Step 2: Data Stratification for D-Series.
    """
    samples = []
    
    for i in range(count):
        # parallel, resource, power, wealth, output, clash, combination
        
        if pattern_id == "D-01": # Zheng Cai (Stable)
            wealth = random.uniform(1.5, 4.0)
            parallel = random.uniform(1.0, 3.0) # Needs root
            output = random.uniform(0.5, 2.0)
            resource = random.uniform(0.5, 2.0)
            power = random.uniform(0.1, 1.5)
            clash = random.choice([0.0, 0.0, 0.3])
            comb = random.choice([0.0, 0.5])
            
            # y_true (Life Labels)
            m_true = max(0.4, min(0.95, wealth * 0.2 + output * 0.1))
            e_true = max(0.3, min(0.90, parallel * 0.3 - wealth * 0.1))
            o_true = max(0.2, min(0.85, power * 0.3 + wealth * 0.1))
            s_true = max(0.1, min(0.60, clash * 0.5 + wealth * 0.05))
            r_true = max(0.3, min(0.90, comb * 0.4 + 0.4))
            
        else: # D-02 (Pian Cai - Volatile)
            wealth = random.uniform(2.0, 6.0) # Higher wealth
            parallel = random.uniform(1.0, 4.0)
            output = random.uniform(1.0, 3.0)
            resource = random.uniform(0.1, 1.5)
            power = random.uniform(0.1, 1.0)
            clash = random.uniform(0.5, 2.5) # Clash is common for windfall
            comb = random.choice([0.0, 0.8])
            
            # y_true (Life Labels)
            m_true = max(0.5, min(1.0, wealth * 0.15 + clash * 0.1 + output * 0.1))
            e_true = max(0.2, min(0.8, parallel * 0.2 - wealth * 0.15))
            o_true = max(0.1, min(0.7, power * 0.2 + wealth * 0.05))
            s_true = max(0.3, min(1.0, clash * 0.3 + wealth * 0.1))
            r_true = max(0.1, min(0.8, comb * 0.3 + 0.2))
            
        x = [parallel, resource, power, wealth, output, clash, comb]
        y = [e_true, o_true, m_true, s_true, r_true]
        
        samples.append({
            "pattern_id": pattern_id,
            "x": x,
            "y": y
        })
        
    return samples

if __name__ == "__main__":
    d01_data = generate_d_series_samples("D-01", 250)
    d02_data = generate_d_series_samples("D-02", 250)
    
    with open("data/stratified_samples_d_series.json", "w") as f:
        json.dump(d01_data + d02_data, f, indent=2)
    print(f"✅ Successfully stratified 500 D-Series samples to data/stratified_samples_d_series.json")
