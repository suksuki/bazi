import sys
import os
import json
import math

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.engines.temporal_shunting import TemporalShuntingEngine

def run_experiment():
    print("🧪 Starting Topic 3 Experiment: Temporal Shunting Verification...")
    
    # 1. Load Test Case
    case_id = "MOD16_TEST_01_ESCAPE"
    print(f"📂 Loading Test Case: {case_id}")
    
    try:
        with open("tests/cases/mod_16_temporal_shunting.json", "r") as f:
            cases = json.load(f)
            test_case = next(c for c in cases if c['case_id'] == case_id)
    except Exception as e:
        print(f"❌ Failed to load test case: {e}")
        return

    # 2. Initialize Engine
    print("⚙️ Initializing TemporalShuntingEngine...")
    dm = test_case['bazi']['stems'][0]
    engine = TemporalShuntingEngine(dm)
    
    # 3. Scan Singularities
    print("📡 Scanning Future 120 Months for Singularities...")
    scan_res = engine.scan_singularities(start_year=2024)
    singularities = scan_res['singularities']
    
    if not singularities:
        print("⚠️ No singularities found. Adjusting mock parameters for test.")
        # Force a high SAI for testing if none found naturally in mock
        peak_sai = 2.5
    else:
        peak_sai = max([x['sai'] for x in singularities])
        print(f"⚠️ Found {len(singularities)} Singularity Points. Peak SAI: {peak_sai:.4f}")

    # 4. Simulate Intervention (Study)
    action = "STUDY"
    geo_k = 1.0 # Neutral Geo
    print(f"🛡️ Simulating Intervention: Action={action}, K_geo={geo_k}")
    
    sim_res = engine.simulate_intervention(peak_sai, action, geo_k)
    new_sai = sim_res['final_sai']
    
    print(f"📊 Results:")
    print(f"  - Original SAI: {peak_sai:.4f}")
    print(f"  - Shunted SAI:  {new_sai:.4f}")
    print(f"  - Reduction:    {sim_res['reduction_pct']}%")
    
    # 5. Verify Logic
    if new_sai < peak_sai:
        print("✅ Shunting Successful: SAI reduced.")
    else:
        print("❌ Shunting Failed: No reduction.")
        
    if new_sai < engine.SAI_THRESHOLD and peak_sai > engine.SAI_THRESHOLD:
        print("✅ ESCAPE SUCCESSFUL: Structure stabilized below threshold.")
    elif new_sai > engine.SAI_THRESHOLD:
        print(f"⚠️ PARTIAL SUCCESS: Still Critical (> {engine.SAI_THRESHOLD})")
        
    # 6. Oracle Search
    print("🔮 Running Sensitivity Search (Oracle)...")
    best_path = engine.sensitivity_search(peak_sai)[0]
    print(f"  - Best Strategy: {best_path['action']} + {best_path['geo']} (K={best_path['geo_k']})")
    print(f"  - Projected Final SAI: {best_path['metrics']['final_sai']}")

if __name__ == "__main__":
    run_experiment()
