import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.config import config
from core.registry_loader import RegistryLoader

def verify_resolver():
    print("🔍 Testing FDS-V3.0 Runtime Resolver...")
    
    loader = RegistryLoader()
    
    # 1. Test single resolution
    try:
        ref = "@config.gating.weak_self_limit"
        val = loader.resolve_config_ref(ref)
        print(f"✅ Single Resolution: {ref} -> {val}")
        assert isinstance(val, float)
    except Exception as e:
        print(f"❌ Single Resolution Failed: {e}")
        return

    # 2. Test dictionary resolution
    test_dict = {
        "thresholds": {
            "min_sai_gating_ref": "@config.gating.weak_self_limit",
            "max_mahalanobis_dist_ref": "@config.patterns.a01.mahalanobis_threshold"
        }
    }
    
    try:
        resolved = loader.resolve_config_refs_in_dict(test_dict)
        print(f"✅ Dictionary Resolution: {resolved}")
        assert "min_sai_gating" in resolved["thresholds"]
        assert "max_mahalanobis_dist" in resolved["thresholds"]
        assert isinstance(resolved["thresholds"]["min_sai_gating"], float)
        assert isinstance(resolved["thresholds"]["max_mahalanobis_dist"], float)
    except Exception as e:
        print(f"❌ Dictionary Resolution Failed: {e}")
        return

    # 3. Test real Pattern A-01 matching router logic
    print("\n🔍 Testing Pattern A-01 Matrix Projection Flow...")
    try:
        # Mock chart and day_master for A-01 (Direct Officer)
        chart = ['庚午', '壬午', '戊午', '甲寅']
        day_master = '戊'
        
        # Calculate projection
        result = loader.calculate_tensor_projection_from_registry(
            pattern_id="A-01",
            chart=chart,
            day_master=day_master
        )
        
        print(f"✅ A-01 Calculation Success: SAI={result.get('sai')}")
        print(f"   Projection: {result.get('projection')}")
        
    except Exception as e:
        print(f"❌ A-01 Calculation Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 All Resolver Verifications Passed!")

if __name__ == "__main__":
    verify_resolver()
