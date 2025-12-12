
from learning.db import LearningDB
import json
import os

try:
    db = LearningDB()
    cases = db.get_all_cases()
    
    total = len(cases)
    with_truth = 0
    with_wealth = 0
    with_career = 0
    
    for c in cases:
        if c.get('truth'):
            with_truth += 1
            if c['truth'].get('wealth'): with_wealth += 1
            if c['truth'].get('career'): with_career += 1
            
    print(f"Total Cases: {total}")
    print(f"With Ground Truth: {with_truth}")
    print(f"With Wealth Score: {with_wealth}")
    print(f"With Career Score: {with_career}")
    
    # Check model files
    import pickle
    model_dir = "data/models"
    for m in os.listdir(model_dir):
        if m.endswith(".pkl"):
            p = os.path.join(model_dir, m)
            size = os.path.getsize(p)
            print(f"Model {m}: {size/1024:.1f} KB")

except Exception as e:
    print(f"Error: {e}")
