
import numpy as np
import json
import random
from typing import List, Dict

def generate_tier_a_samples(count=500):
    """
    Simulates FDS-V1.4 Step 2: Data Stratification.
    Generates 500 Tier A samples for A-03 (YangRen JiaSha).
    """
    samples = []
    
    for i in range(count):
        # 1. Randomize Input Vector (Simulating Physics Engine output)
        # parallel, resource, power, wealth, output, clash, combination
        
        # We want A-03 Elite samples mainly
        is_elite = random.random() > 0.3
        
        if is_elite:
            parallel = random.uniform(1.5, 3.5)
            power = random.uniform(1.2, 2.5)
            resource = random.uniform(0.1, 1.5)
            wealth = random.uniform(0.1, 3.0) # Diverse wealth
            output = random.uniform(0.1, 1.0)
            clash = random.choice([0.0, 0.0, 0.5, 1.0])
            comb = random.choice([0.0, 0.0, 0.5])
        else:
            # "Broken" or "Weak" A-03 cases
            parallel = random.uniform(0.5, 1.5)
            power = random.uniform(0.5, 1.5)
            resource = random.uniform(0.5, 2.5)
            wealth = random.uniform(2.0, 6.0) # High wealth burden
            output = random.uniform(1.0, 3.0)
            clash = random.uniform(0.5, 1.5)
            comb = 0.0
            
        x = [parallel, resource, power, wealth, output, clash, comb]
        
        # 2. Simulate "Life Labels" (y_true)
        # In reality, this would be from LLM analysis of biographies.
        # Here we use a "Golden Formula" + noise.
        
        # Order (O): High when parallel and power are balanced and well-rooted.
        # Penalty for high wealth/output interference in A-03.
        o_base = min(parallel, power) * 0.4 - (wealth * 0.05) - (clash * 0.2)
        o_true = max(0.1, min(0.95, o_base + random.uniform(-0.1, 0.1)))
        
        # Energy (E): High when parallel is high.
        e_base = parallel * 0.3 + resource * 0.1
        e_true = max(0.2, min(0.98, e_base + random.uniform(-0.05, 0.05)))
        
        # Wealth (M): Higher with wealth/output, but too much parallel kills it.
        m_base = (wealth * 0.2 + output * 0.1) / (1.0 + parallel * 0.1)
        m_true = max(0.1, min(0.90, m_base + random.uniform(-0.1, 0.1)))
        
        # Stress (S): High with clash and unbalanced power vs parallel.
        s_base = clash * 0.4 + abs(power - parallel) * 0.1
        s_true = max(0.1, min(1.0, s_base + random.uniform(0, 0.2)))
        
        # Relation (R)
        r_true = max(0.1, min(0.8, 0.5 - parallel * 0.1 + comb * 0.2))
        
        y = [e_true, o_true, m_true, s_true, r_true]
        
        samples.append({
            "x": x,
            "y": y
        })
        
    return samples

if __name__ == "__main__":
    data = generate_tier_a_samples(500)
    with open("data/stratified_samples_a03.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Successfully stratified 500 Tier A samples to data/stratified_samples_a03.json")
