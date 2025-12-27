
import os
import sys
import json
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("⛓️ Starting Global Inertia Audit (518,400 Samples) for [LYKG] LC Circuit...")
    controller = SimulationController(workspace_root)
    
    def progress(curr, tot, stats):
        if curr % 100000 == 0 or curr == tot:
            print(f"  [Inertia Scan] {curr}/{tot} (Matched: {stats.get('matched', 0)})")

    res = controller.run_v435_inertia_audit(progress_callback=progress)
    
    print("\n✅ Inertia Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  Self-Locking Circuits Found: {res['hit_count']}")
    
    if res['top_samples']:
        print("\n⚡ Top Inertia/Saturation Samples:")
        for i, s in enumerate(res['top_samples'][:5]):
            print(f"  {i+1}. {s['label']} | Mi: {s['inertia_margin_mi']} | L: {s['inductance_L']} | {s['category']}")

if __name__ == "__main__":
    main()
