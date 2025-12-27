
import os
import sys
import json
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("🌡️ Starting Global Thermal Audit (518,400 Samples) for [YHGS] Thermodynamic Entropy...")
    controller = SimulationController(workspace_root)
    
    def progress(curr, tot, stats):
        if curr % 100000 == 0 or curr == tot:
            print(f"  [Thermal Scan] {curr}/{tot} (Anomalies Found: {stats.get('matched', 0)})")

    res = controller.run_v435_thermo_audit(progress_callback=progress)
    
    print("\n✅ Thermal Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  Thermal Anomalies Recorded: {len(res['top_samples'])}")
    
    if res['top_samples']:
        print("\n🧊/🔥 Representative Thermal Singularities:")
        for i, s in enumerate(res['top_samples'][:5]):
            print(f"  {i+1}. {s['label']} | Temp: {s['system_temperature']} | Eta: {s['efficiency_eta']} | {s['category']}")

if __name__ == "__main__":
    main()
