
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.trinity.core.engines.simulation_controller import SimulationController
from core.bazi_profile import BaziProfile

def test_huang_xiang_lifespan():
    controller = SimulationController(os.getcwd())
    
    # Huang Xiang: 1978-06-14 08:00 (Male)
    dt = datetime(1978, 6, 14, 8, 0)
    profile = BaziProfile(dt, 1)
    
    print(f"Testing Lifespan Scan for Huang Xiang (SGSJ)...")
    print(f"Natal Pillars: {profile.pillars}")
    
    # 100 Year Scan for SGSJ
    res = controller.run_lifespan_topic_scan(profile, ["SHANG_GUAN_SHANG_JIN"], max_age=100)
    
    summary = res["summary"]
    print(f"\nSummary:")
    print(f"Total Years Scanned: {summary['total_years_scanned']}")
    print(f"Total Topic Hits: {summary['total_triggered_years']}")
    print(f"Total Danger Years: {summary['total_danger_years']}")
    
    # Check if we have hits (should be 100% or close)
    if summary['total_triggered_years'] > 0:
        print("✅ SUCCESS: SGSJ detected in the scan.")
    else:
        print("❌ FAILURE: SGSJ NOT detected in the scan.")
        
    # Check for danger years (e.g. Ren Xu year 1982, Gui Hai 1983 - look for specific years)
    # Ren Xu (1982) is age 4
    for yd in res["timeline"]:
        if yd["year"] in [1982, 1983, 1992, 1993, 2002, 2012, 2022]:
            print(f"Year {yd['year']} (Age {yd['age']}): SAI={yd['max_sai']:.2f}, Danger={yd['is_danger_zone']}, Topics={[t['topic_name'] for t in yd['triggered_topics']]}")
            if yd["year"] == 1982: # Ren Xu (Guan/Sha in Annual)
                 if yd["is_danger_zone"]:
                     print(f"  ✅ Correctly flagged 1982 (Ren Xu) as dangerous.")
                 else:
                     print(f"  ❌ Failed to flag 1982 as dangerous.")

if __name__ == "__main__":
    test_huang_xiang_lifespan()
