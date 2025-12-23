
import json
import os
import sys

def find_index():
    base_dir = "/home/jin/bazi_predict/ui/pages" # Assuming script runs relative or absolute
    paths = [
        "../../tests/data/integrated_extreme_cases.json",
        "../../tests/data/oppose_matrix_v21.json",
        "../../tests/data/quantum_mantra_v93.json", 
        "../../tests/v14_tuning_matrix.json", 
        "../../data/calibration_cases.json"
    ]
    
    cases = []
    
    for p in paths:
        abs_p = os.path.normpath(os.path.join(base_dir, p))
        if os.path.exists(abs_p):
            try:
                with open(abs_p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for c in data:
                        if not any(ex.get('id') == c.get('id') for ex in cases): cases.append(c)
            except Exception as e:
                print(f"Error loading {abs_p}: {e}")

    # Sort logic from UI
    def sort_key(x):
        cid = str(x.get('id', ''))
        priority = 0 if cid.startswith('OPPOSE_') else 1
        return (priority, cid)
    
    cases.sort(key=sort_key)
    
    # Find
    for i, c in enumerate(cases):
        if c.get('id') == "INTEGRATED_EXTREME_001":
            print(f"✅ FOUND: Index={i}, Display Number={i+1:03d}")
            print(f"   Name: {c.get('description')}")
            return
            
    print("❌ NOT FOUND")

if __name__ == "__main__":
    find_index()
