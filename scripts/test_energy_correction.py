
import sys
import os
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster

def test_probability_wave_correction():
    print("📊 Testing Antigravity V11.1 Probability Wave Correction (Energy Adjustment)...")
    
    executor = UnifiedArbitratorMaster()
    # 庚午 丙子 戊辰 庚申 -> Strong Zi-Wu Clash should generate SAI
    bazi_data = ["庚午", "丙子", "戊辰", "庚申"]
    birth_info = {"gender": "male"}
    
    # Test 1: Neutral GEO (Unknown)
    print("\n--- Test 1: Neutral GEO (Unknown) ---")
    ctx_neutral = {'data': {'city': 'Unknown'}}
    state_neutral = executor.arbitrate_bazi(bazi_data, birth_info, ctx_neutral)
    sai_neutral = state_neutral['physics']['stress']['SAI']
    ic_neutral = state_neutral['physics']['stress']['IC']
    print(f"Initial Stress: SAI={sai_neutral}, IC={ic_neutral}")
    
    # Test 2: Beijing (Earth Bias = 1.05)
    print("\n--- Test 2: Beijing (Earth Bias = 1.05) ---")
    ctx_beijing = {'data': {'city': 'Beijing'}}
    state_beijing = executor.arbitrate_bazi(bazi_data, birth_info, ctx_beijing)
    sai_beijing = state_beijing['physics']['stress']['SAI']
    ic_beijing = state_beijing['physics']['stress']['IC']
    print(f"Beijing Stress: SAI={sai_beijing}, IC={ic_beijing}")
    
    # Verification
    if sai_neutral > 0:
        if sai_beijing < sai_neutral and ic_beijing > ic_neutral:
            print("\n✅ Success: Probability Wave Correction confirmed")
            print(f"Dynamic Damping Ratio: {sai_beijing/sai_neutral:.2f}")
        else:
            print("\n❌ Error: Energy correction values did not move in expected direction")
    else:
        print("\n⚠️ Warning: Baseline SAI is still 0. System might be too stable for this test case.")

if __name__ == "__main__":
    test_probability_wave_correction()
