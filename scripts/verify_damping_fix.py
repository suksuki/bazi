import sys
import os
import math

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.engines.temporal_shunting import TemporalShuntingEngine

def verify_neutral_damping():
    print("🧪 Verifying Neutral Damping (Phase 4.0 Bugfix)...")
    
    t_engine = TemporalShuntingEngine("甲")
    
    # Range of Wave values (1.0 baseline + 1.2 wave + 0.2 noise = 2.4 max)
    # With original d=1.0 (formula raw/(1+d)), it was 2.4/2 = 1.2 (Sub-threshold)
    # With new d=1.0 (formula raw/d), it should be 2.4/1 = 2.4 (Supra-threshold)
    
    scan_neutral = t_engine.scan_singularities(social_damping=1.0)
    singularities = scan_neutral['singularities']
    
    print(f"   - Number of singularities found (D=1.0): {len(singularities)}")
    
    if len(singularities) > 0:
        print("   ✅ PASS: Singularities are visible at Neutral Damping (1.0).")
    else:
        print("   ❌ FAIL: Singularities still missing at Neutral Damping.")

    # Test Damping Impact
    scan_high = t_engine.scan_singularities(social_damping=2.0)
    s_high = scan_high['singularities']
    print(f"   - Number of singularities found (D=2.0): {len(s_high)}")
    
    if len(s_high) < len(singularities):
        print("   ✅ PASS: High damping correctly suppresses peaks.")
    else:
        print("   ❌ FAIL: High damping logic inconsistent.")

if __name__ == "__main__":
    verify_neutral_damping()
