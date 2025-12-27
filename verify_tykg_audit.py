
import os
import sys
import json
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("✨ Starting Global Resonance Audit (518,400 Samples) for [TYKG] Specialized Dominance...")
    controller = SimulationController(workspace_root)
    
    def progress(curr, tot, stats):
        if curr % 100000 == 0 or curr == tot:
            print(f"  [Resonance Scan] {curr}/{tot} (High Coherence Found: {stats.get('matched', 0)})")

    res = controller.run_v44_resonance_audit(progress_callback=progress)
    
    print("\n✅ Resonance Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  Strong Coherence Patterns Found: {res['hit_count']}")
    
    if res['top_samples']:
        print("\n🌊 Top Phase Coherence Samples:")
        for i, s in enumerate(res['top_samples'][:5]):
            print(f"  {i+1}. {s['label']} | C: {s['coherence_coefficient_c']} | G: {s['resonance_gain_g']} | {s['category']}")

if __name__ == "__main__":
    main()
