
import os
import sys
import json
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("💥 Starting Final Reversion Audit (518,400 Samples) for [MHGG] Transmutation Stability...")
    controller = SimulationController(workspace_root)
    
    def progress(curr, tot, stats):
        if curr % 100000 == 0 or curr == tot:
            print(f"  [Reversion Scan] {curr}/{tot} (Flash Events Detected: {stats.get('matched', 0)})")

    res = controller.run_v44_reversion_audit(progress_callback=progress)
    
    print("\n✅ Final Reversion Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  Property Flash / Synthetic Patterns Found: {res['hit_count']}")
    
    if res['top_samples']:
        print("\n⚡ Top Property Flash / Reversion Samples (High Stress):")
        for i, s in enumerate(res['top_samples'][:5]):
            print(f"  {i+1}. {s['label']} | God: {s['trans_god']} | Er: {s['reversion_stress_er']} | SAI Pulse: {s['sai']}")

if __name__ == "__main__":
    main()
