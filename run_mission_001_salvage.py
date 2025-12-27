
"""
[SSEP] Mission 001: Global Singularity Salvage
Automated Script to execute the 'Holographic Scan' and 'Horizon Penetration' protocols via the SingularityController.
"""
import sys
import pandas as pd
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.controllers.singularity_controller import SingularityController

def run_mission():
    print("🛰️ [MISSION 001] Global Singularity Salvage Initiated...")
    print(f"   Timestamp: {datetime.now()}")
    
    controller = SingularityController()
    
    # 1. Holographic Scan
    print("\n[STEP 1] Executing Holographic Scan on Quantum Matrix...")
    scan_df = controller.execute_global_scan()
    print("   >> Scan Complete. Signals Locked.")
    print("\n   [PREY MATRIX]")
    print(scan_df.to_string(index=False))
    
    # 2. Horizon Penetration (Simulating Action A & B)
    ids = scan_df['ID'].tolist()
    
    print("\n[STEP 2] Penetrating Event Horizons (Dynamic Injection)...")
    
    for target_id in ids:
        print(f"\n   >>> Targeting: {target_id}")
        timeline_df = controller.run_dynamic_injection(target_id)
        
        # Analyze outcome
        final_state = timeline_df.iloc[-1]['state']
        purity_trend = timeline_df['purity'].tolist()
        start_p = purity_trend[0]
        end_p = purity_trend[-1]
        
        print(f"       Trace: {len(timeline_df)} Years injected.")
        print(f"       Purity Delta: {start_p:.4f} -> {end_p:.4f}")
        print(f"       Final State: {final_state}")
        
        if final_state == "STABLE":
            print("       Verdict: 🔵 TRUE SINGULARITY (Superconducting)")
        elif final_state == "DECAY" or final_state == "COLLAPSE":
            print("       Verdict: 🔴 FALSE SINGULARITY (Turbulence/Collapse)")

    print("\n[MISSION COMPLETE] All Singularities Audited.")

if __name__ == "__main__":
    run_mission()
