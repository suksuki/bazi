import json
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.engines.structural_vibration import StructuralVibrationEngine
from core.trinity.core.nexus.context import ContextInjector

def run_test():
    print("🧪 Verifying MOD_15 Phase Transition Logic...")
    
    # Load cases
    with open("tests/cases/mod_15_phase_transition.json", "r") as f:
        cases = json.load(f)
        
    engine = StructuralVibrationEngine("甲") # Init check
    
    for case in cases:
        print(f"\n📂 Running Case: {case['case_id']} ({case['name']})")
        
        # Parse Bazi
        s = case['bazi']['stems'] # List of 4
        b = case['bazi']['branches'] # List of 4
        dm = s[2] # Day Master
        
        # Override DM in engine
        engine.day_master = dm
        
        # Check if 4 pillars
        if len(s) != 4 or len(b) != 4:
            print("❌ Invalid Bazi length")
            continue
            
        # Run Engine
        metrics = engine.calculate_vibration_metrics(s, b, context={})
        
        # Check Phase
        is_phase = metrics.get('is_phase_transition')
        dom = metrics.get('dominant_element')
        
        print(f"   - Detected Phase Transition: {is_phase}")
        print(f"   - Dominant Element: {dom}")
        print(f"   - Transmission Efficiency: {metrics['transmission_efficiency']:.2f}")
        print(f"   - Optimal Deity Mix: {metrics['optimal_deity_mix']}")
        
        # Validation
        if case['case_id'] == "MOD15_PHASE_01_FOLLOW":
            if is_phase:
                print("✅ PASS: Correctly identified True Follow structure.")
                # Logic Inversion Check: Optimal Deity should be Dominant (Metal)
                if 'Metal' in metrics['optimal_deity_mix']:
                     print("✅ PASS: Logic Inverted (Enemy 'Metal' became Friend).")
                else:
                     print("❌ FAIL: Logic Inversion Failed. Optimal is not Metal.")
            else:
                print("❌ FAIL: Failed to identify True Follow.")
                
        elif case['case_id'] == "MOD15_PHASE_02_FALSE_FOLLOW":
            # For False Follow, currently engine is aggressive (purity 87.5%), so it likely outputs True
            # But let's see the metrics.
            print(f"   - Note: False Follow scenario. Engine output: {is_phase}")
            # If it outputs True, it means it decided "Maintains Follow". 
            # If False, "Collapsed".
            
    print("\n🏁 Verification Complete.")

if __name__ == "__main__":
    run_test()
