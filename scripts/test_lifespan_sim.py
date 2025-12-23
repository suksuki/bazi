
import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.bazi_profile import BaziProfile
from core.trinity.core.engines.life_path_simulation import LifePathEngine

def run_lifespan_verification():
    # 戊辰 丙辰 戊辰 丙辰 (Self-Penalty Cluster Case)
    birth_dt = datetime(1988, 4, 16, 8, 0)
    profile = BaziProfile(birth_dt, gender=1)
    
    engine = LifePathEngine()
    
    print(f"--- [LIFE_PATH_VERIFICATION] DM: {profile.day_master} ---")
    
    # Simulate 20 years (1988 - 2008)
    start_y = 1988
    end_y = 2008
    
    print(f"Simulating lifespan from {start_y} to {end_y}...")
    start_t = datetime.now()
    results = engine.simulate_lifespan(profile, start_year=start_y, end_year=end_y)
    end_t = datetime.now()
    
    timeline = results['timeline']
    risk_nodes = results['risk_nodes']
    
    print(f"\n[RESULTS]")
    print(f"Total Samples: {len(timeline)}")
    print(f"Total Risks Detected: {len(risk_nodes)}")
    print(f"Processing Time: {end_t - start_t}")
    
    if timeline:
        print(f"First Sample: {timeline[0]['year']} {timeline[0]['term']} | SAI={timeline[0]['sai']}")
        print(f"Last Sample: {timeline[-1]['year']} {timeline[-1]['term']} | SAI={timeline[-1]['sai']}")
    
    # Check for trend (e.g., does SAI vary?)
    sai_values = [t['sai'] for t in timeline]
    min_sai = min(sai_values)
    max_sai = max(sai_values)
    print(f"SAI Range: {min_sai} -> {max_sai}")
    
    if max_sai > min_sai:
        print("\n✅ VERIFICATION SUCCESS: Temporal variance detected.")
    else:
        print("\n❌ VERIFICATION FAILURE: No temporal variance (flat-line).")

    if risk_nodes:
        print(f"Sample Risk: {risk_nodes[0]['reason']} at {risk_nodes[0]['timestamp']}")

if __name__ == "__main__":
    run_lifespan_verification()
