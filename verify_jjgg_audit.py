
import os
import sys
import json
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("🌌 Starting Global Quantum Tunnel Audit (518,400 Samples) for [JJGG]...")
    controller = SimulationController(workspace_root)
    
    def progress(curr, tot, stats):
        if curr % 100000 == 0 or curr == tot:
            print(f"  [Tunnel Scan] {curr}/{tot} (Resonance Found: {stats.get('matched', 0)})")

    res = controller.run_v435_tunnel_audit(progress_callback=progress)
    
    print("\n✅ Quantum Tunnel Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  Tunneling Cavities Found: {res['hit_count']}")
    
    if res['top_samples']:
        print("\n🔭 Void Energy Injection Samples:")
        for i, s in enumerate(res['top_samples'][:5]):
            print(f"  {i+1}. {s['label']} | Pt: {s['tunneling_probability_pt']} | V_tunnel: {s['virtual_energy_v_tunnel']} | {s['category']}")

if __name__ == "__main__":
    main()
