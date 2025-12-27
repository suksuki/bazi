
"""
[SSEP] Mission 002: Hidden Conductor Search
Automated Script to execute the 'Evolutionary Scan' to find Potential Singularities.
"""
import sys
import pandas as pd
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.controllers.singularity_controller import SingularityController

def run_mission():
    print("🛰️ [MISSION 002] Searching for Hidden Conductors...")
    print(f"   Timestamp: {datetime.now()}")
    
    controller = SingularityController()
    
    # 1. Evolutionary Scan
    print("\n[STEP 1] Executing Evolutionary Scan (Dynamic Luck Injection)...")
    hidden_gems_df = controller.execute_potential_scan()
    
    if hidden_gems_df.empty:
        print("   >> No Hidden Conductors found in current batch.")
    else:
        print("   >> Targets Locked. Latent Energy Detected.")
        print("\n   [POTENTIAL SINGULARITY LIST]")
        print(hidden_gems_df.to_string(index=False))
        
        # Analyze Findings
        for _, row in hidden_gems_df.iterrows():
            print(f"\n   >>> Analyst Report for {row['ID']} ({row['Name']})")
            print(f"       Current Purity: {row['Base Purity']} (High Resistance)")
            print(f"       Activation Key: {row['Triggers']}")
            print("       Physics: Chart is 'Pre-Superconducting'. Waiting for Trigger to complete Quantum Pair.")
            print("       Verdict: 🟡 HIDDEN SINGULARITY (Awakening Possible)")

    print("\n[MISSION COMPLETE] Evolutionary Scan Finished.")

if __name__ == "__main__":
    run_mission()
