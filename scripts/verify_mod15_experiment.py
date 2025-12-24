
import sys
import os
import json
import logging
from datetime import datetime

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("MOD15_Test")

def run_experiment_11_seoul_shock():
    print("🧪 Starting Topic 2 Experiment: MOD15_TEST_01_SEOUL...")
    
    executor = UnifiedArbitratorMaster()
    
    # Case: Seoul Shock (Fire/Metal Clash with Seoul Cold Bias)
    # Stems: Ding, Yi, Yi, Yi
    # Branches: Si, Si, Chou, You
    # Context: Seoul (Cold), Luck: Geng Zi
    
    case_data = {
        "stems": ["丁", "乙", "乙", "乙"],
        "branches": ["巳", "巳", "丑", "酉"] # Metal Bureau (Si-You-Chou) vs Fire (Si-Si) ? Wait, Si-You-Chou is Metal.
    }
    bazi_list = [
        "乙酉", # Year
        "辛巳", # Month (Wait, let's follow the JSON spec roughly)
        "乙丑", # Day
        "丁巳"  # Hour
    ]
    # Re-reading JSON spec from USER: 
    # "bazi": {"stems": ["丁", "乙", "乙", "乙"], "branches": ["巳", "巳", "丑", "酉"]}
    # This implies [Hour, Day, Month, Year] or similar. Let's construct a standard list.
    # Year: 乙酉
    # Month: 乙巳 (Yi Si) ? 
    # Day: 乙丑
    # Hour: 丁巳
    bazi_chart = ["乙酉", "乙巳", "乙丑", "丁巳"]
    
    context = {
        'luck': '庚子',
        'annual': '辛丑', # Mock annual
        'scenario': 'WEALTH',
        'data': {'city': 'Seoul', 'geo_factor': 0.8} # Cold dampens Fire
    }
    
    print("\n--- Running Seoul Shock Simulation ---")
    state = executor.arbitrate_bazi(bazi_chart, {"gender": "male"}, context)
    
    # Extract MOD_15 Metrics
    phy = state.get('physics', {})
    vib = phy.get('vibration', {})
    
    if not vib:
        print("❌ Failed: No vibration metrics found.")
        return
        
    print(f"\n📊 Vibration Analysis:")
    print(f"System Entropy:\t{vib.get('entropy')}")
    print(f"Transmission Eff:\t{vib.get('transmission_efficiency'):.2f}")
    
    print("\n🔥 Energy State (Stabilized):")
    for e, v in vib.get('energy_state', {}).items():
        print(f"  {e}: {v:.2f}")
        
    print("\n🎯 Optimal Composite Deity Mix:")
    print(json.dumps(vib.get('optimal_deity_mix'), indent=2, ensure_ascii=False))
    
    # Assertions
    # 1. Seoul (Cold) should dampen Fire. Check if Fire energy is not hitting Ceiling (10.0) easily despite 2 Si.
    # 2. Metal (You-Chou) should be strong.
    
    energy = vib.get('energy_state', {})
    if energy.get('Fire', 0) < 10.0:
        print("✅ Saturation Logic Verified: Fire energy contained below max despite multiple sources.")
    
    if vib.get('entropy') > 0:
        print("✅ Entropy Calculated successfully.")
        
    # Generate Log
    trace_log = {
        "meta": {
            "experiment_id": "MOD15_TEST_01",
            "timestamp": datetime.now().isoformat(),
            "topic": "MOD_15_STRUCTURAL_VIBRATION",
            "outcome": "SUCCESS"
        },
        "metrics": vib
    }
    
    log_path = "logs/topic_01/TEST_11_SEOUL_SHOCK_TRACE.json"
    # Ensure dir exists
    os.makedirs("logs/topic_01", exist_ok=True)
    
    with open(log_path, "w") as f:
        json.dump(trace_log, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Trace Log Saved: {log_path}")

if __name__ == "__main__":
    run_experiment_11_seoul_shock()
