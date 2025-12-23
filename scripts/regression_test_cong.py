
import sys
import os
import json
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle
from core.profile_manager import ProfileManager
from core.calculator import BaziCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_regression_test():
    """
    Regression Test for Pattern Detection (Follow/Cong).
    Ensures that known 'Follow' archetypes are identified as COHERENT with correct flags.
    """
    oracle = TrinityOracle()
    pm = ProfileManager()
    profiles = pm.get_all()
    
    # Archetypes for Follow pattern (Self-created for test if not in archive)
    test_cases = [
        {
            "name": "TEST_FOLLOW_FIRE",
            "bazi": ["丙午", "甲午", "丙午", "甲午"], # Extreme Fire
            "dm": "丙",
            "expected_mode": "COHERENT",
            "expected_follow": True
        },
        {
            "name": "TEST_FOLLOW_METAL",
            "bazi": ["庚申", "庚申", "庚申", "庚申"], # Extreme Metal
            "dm": "庚",
            "expected_mode": "COHERENT",
            "expected_follow": True
        }
    ]
    
    # Also add existing archive profiles that should be Follow (if any)
    # The current audit showed many as ANNIHILATION due to conflicting priorities.
    
    print("\n🚀 [REGRESSION_TEST] Starting Follow Pattern Validation...")
    print("="*60)
    
    pass_count = 0
    fail_count = 0
    
    for case in test_cases:
        res = oracle.analyze(case['bazi'], case['dm'])
        resonance = res['resonance']
        verdict = res['verdict']
        
        mode_match = resonance.mode == case['expected_mode']
        follow_match = resonance.is_follow == case['expected_follow']
        
        status = "✅ PASS" if mode_match and follow_match else "❌ FAIL"
        if status == "✅ PASS": pass_count += 1
        else: fail_count += 1
        
        print(f"CASE: {case['name']} | Result: {status}")
        print(f"  - Bazi: {' '.join(case['bazi'])}")
        print(f"  - Mode: {resonance.mode} (Expected: {case['expected_mode']})")
        print(f"  - Follow Flag: {resonance.is_follow} (Expected: {case['expected_follow']})")
        print(f"  - Sync (η): {resonance.sync_state:.4f}")
        print(f"  - Locking Ratio: {resonance.locking_ratio:.2f}")
        print(f"  - active_rules: {res['logic_stack']['active_rules']}")
        print("-" * 60)

    print(f"\n📈 [SUMMARY]: Passes: {pass_count} | Fails: {fail_count}")
    print("="*60)
    
    if fail_count > 0:
        print("⚠️ Regression test failed. Refinement of PH17-20 logic required.")
        return False
    else:
        print("🟢 All Follow archetypes confirmed. Resonance Engine alignment complete.")
        return True

if __name__ == "__main__":
    run_regression_test()
