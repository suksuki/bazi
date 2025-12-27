
import os
import sys
import json
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("🌌 Starting Virtual Gap Audit (518,400 Samples) for [GXYG] Arching Space...")
    controller = SimulationController(workspace_root)
    
    def progress(curr, tot, stats):
        if curr % 100000 == 0 or curr == tot:
            print(f"  [Gap Scan] {curr}/{tot} (Potential Wells Found: {stats.get('matched', 0)})")

    res = controller.run_v45_gxyg_audit(progress_callback=progress)
    
    print("\n✅ Virtual Gap Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  Virtual Potential Wells Detected: {res['hit_count']}")
    
    if res['top_samples']:
        print("\n🕳️ Top Virtual Potential Well Samples (Vacuum Energy Supply):")
        for i, s in enumerate(res['top_samples'][:5]):
            print(f"  {i+1}. {s['label']} | Vind: {s['virtual_induction_v_ind']} | dSAI: {s['dsai_correction']} | Gaps: {', '.join(s['gaps'])}")

if __name__ == "__main__":
    main()
