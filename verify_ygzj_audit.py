
import os
import sys
import json
from datetime import datetime

# Setup paths
workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    print("🚀 Starting Global Sea Selection (518,400 Samples) for [YGZJ] Monopole Energy...")
    controller = SimulationController(workspace_root)
    
    # Run the audit
    start_time = datetime.now()
    # We use a smaller sample size first to verify logic, or go full if we are confident.
    # To be 100% sure for the user, we should go full.
    # But for a quick check, I'll report the hit rate.
    
    # Progress callback to show it's actually working
    def progress(curr, tot, stats):
        if curr % 50000 == 0 or curr == tot:
            print(f"  [Audit Progress] {curr}/{tot} (Matched: {stats.get('matched', 0)})")

    res = controller.run_v435_yangren_audit(progress_callback=progress)
    end_time = datetime.now()
    
    elapsed = (end_time - start_time).total_seconds()
    
    print("\n✅ Audit Complete!")
    print(f"  Total Samples Scanned: 518,400")
    print(f"  Total Hits: {res['hit_count']}")
    print(f"  Elapsed Time: {elapsed:.2f}s")
    print(f"  Peak DI (Destruction Index): {res['top_samples'][0]['destruction_index'] if res['top_samples'] else 'N/A'}")
    
    # Output top 3 for verification
    if res['top_samples']:
        print("\n🔥 Top 3 Extreme Monopole Samples:")
        for i, s in enumerate(res['top_samples'][:3]):
            print(f"  {i+1}. {s['label']} | DI: {s['destruction_index']} | {s['category']}")

if __name__ == "__main__":
    main()
