
import os
import sys
import json
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("🚀 Starting Quantum Transition Audit (518,400 Samples) for [CWJS] Follow Pattern...")
    controller = SimulationController(workspace_root)
    
    def progress(curr, tot, stats):
        if curr % 100000 == 0 or curr == tot:
            print(f"  [Transition Scan] {curr}/{tot} (Following Patterns Found: {stats.get('matched', 0)})")

    res = controller.run_v44_transition_audit(progress_callback=progress)
    
    print("\n✅ Transition Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  True Following (Subordinate) Patterns Found: {res['hit_count']}")
    
    if res['top_samples']:
        print("\n🚇 Top Following Phase Samples (Zero-Impedance):")
        for i, s in enumerate(res['top_samples'][:5]):
            print(f"  {i+1}. {s['label']} | Tt: {s['transition_threshold_tt']} | Pext: {s['external_pressure']} | SAI Reset: {s['sai']}")

if __name__ == "__main__":
    main()
