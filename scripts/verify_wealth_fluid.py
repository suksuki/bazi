
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle

def run_simulation():
    print("--- 🌊 Phase 35: Wealth Fluid Dynamics Simulation (Navier-Stokes) ---")
    
    # Load Test Data
    data_path = os.path.join(os.path.dirname(__file__), '../tests/data/phase35_wealth_fluid.json')
    with open(data_path, 'r') as f:
        cases = json.load(f)
        
    oracle = TrinityOracle()
    
    for case in cases:
        print(f"\n[SIMULATION] Target: {case['id']} - {case['name']}")
        print(f"  > Description: {case['description']}")
        
        # Run Analysis
        res = oracle.analyze(case['bazi'], case['day_master'])
        w_data = res.get('wealth_fluid', {})
        
        # Extract Metrics
        Re = w_data.get('Reynolds', 0)
        nu = w_data.get('Viscosity', 1.0)
        Q = w_data.get('Flux', 0)
        state = w_data.get('State', 'UNKNOWN')
        metrics = w_data.get('Metrics', {})
        
        print(f"  > 🌊 Reynolds Number (Re): {Re}")
        print(f"  > 🧪 Viscosity (ν): {nu} (Friction: {metrics.get('Rival_Friction', 0)})")
        print(f"  > 🚪 Flux Gate (Q): {Q} (Velocity: {metrics.get('Output_Velocity', 0)})")
        print(f"  > 📊 Flow State: {state}")
        
        # Verification Logic
        if "Reynolds" in case["expected_result"]:
            expected_re = case["expected_result"]["Reynolds"]
            pass_check = False
            if ">" in expected_re:
                val = float(expected_re.replace(">",""))
                pass_check = Re > val
            elif "<" in expected_re:
                val = float(expected_re.replace("<",""))
                pass_check = Re < val
            
            status = "[PASS]" if pass_check else "[FAIL]"
            print(f"  > Verification (Re {expected_re}): {status}")

if __name__ == "__main__":
    run_simulation()
