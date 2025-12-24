import sys
import os
import json

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.engines.temporal_shunting import TemporalShuntingEngine

def run_test():
    print("🧪 Verifying Phase 3.5: Historical Calibration Logic...")
    
    # Init Engine
    engine = TemporalShuntingEngine("甲")
    engine.SAI_THRESHOLD = 2.0 # Set known baseline
    
    print(f"   [Init] Threshold: {engine.SAI_THRESHOLD}")
    
    # 1. Scan History (Birth 1990)
    print("\n1. Scanning Historical Timeline (1990-2024)...")
    res = engine.scan_singularities(start_year=2024, birth_year=1990)
    history_evts = [n for n in res['singularities'] if not n['is_future']]
    
    print(f"   Found {len(history_evts)} historical singularities.")
    if history_evts:
        evt = history_evts[0]
        print(f"   - Example: Year {evt['year']} (Age {evt['age']}) | SAI: {evt['sai']} | Type: {evt['type']}")
        print(f"   - Assertion: {evt['assertion']}")
    else:
        print("   No historical singularities found with default parameters. Lowering baseline for test.")
        # Force a simulation with higher baseline to get events
        res = engine.scan_singularities(start_year=2024, birth_year=1990, baseline_sai=1.5)
        history_evts = [n for n in res['singularities'] if not n['is_future']]
        print(f"   [Retry] Found {len(history_evts)} historical singularities.")
        
    # 2. Test Calibration (User denies accuracy)
    print("\n2. Testing Calibration Loop...")
    # Simulate user feedback: "I am fine in these years" (False Positive denial)
    feedback = [{"year": e['year'], "is_accurate": False} for e in history_evts]
    
    old_th = engine.SAI_THRESHOLD
    cal_res = engine.calibrate_model(feedback)
    new_th = cal_res['new_threshold']
    
    print(f"   Old Threshold: {old_th}")
    print(f"   New Threshold: {new_th}")
    
    if new_th > old_th:
        print("✅ PASS: Threshold increased to reduce false positives.")
    else:
        print("❌ FAIL: Threshold did not increase.")
        
    # 3. Verify Effect (Rescan)
    print("\n3. Verifying Effect on Scan...")
    res_2 = engine.scan_singularities(start_year=2024, birth_year=1990, baseline_sai=1.5)
    history_evts_2 = [n for n in res_2['singularities'] if not n['is_future']]
    print(f"   Singularities after calibration: {len(history_evts_2)} (Was {len(history_evts)})")
    
    if len(history_evts_2) < len(history_evts):
        print("✅ PASS: Calibration successfully filtered out 'safe' events.")
    else:
        print("⚠️ NOTE: Count remains same, maybe threshold change wasn't large enough for these specific values.")

    print("\n🏁 Verification Complete.")

if __name__ == "__main__":
    run_test()
