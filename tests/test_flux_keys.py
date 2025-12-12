
import pytest
from core.flux import FluxEngine

def test_ten_gods_keys_api_contract():
    """
    Verify that FluxEngine output contains the raw Ten Gods keys (BiJian, etc.)
    with float values, as expected by the Dashboard and QuantumEngine.
    """
    chart = {
        'year': {'stem': '甲', 'branch': '子'},
        'month': {'stem': '乙', 'branch': '丑'},
        'day': {'stem': '丙', 'branch': '寅'},
        'hour': {'stem': '丁', 'branch': '卯'}
    }
    
    engine = FluxEngine(chart)
    result = engine.compute_energy_state()
    
    # List of required keys
    required_keys = [
        "BiJian", "JieCai", "ShiShen", "ShangGuan", 
        "PianCai", "ZhengCai", "QiSha", "ZhengGuan", 
        "PianYin", "ZhengYin"
    ]
    
    print("Keys found:", list(result.keys()))
    
    for key in required_keys:
        assert key in result, f"Key {key} missing from FluxEngine output"
        val = result[key]
        assert isinstance(val, (int, float)), f"Value for {key} should be numeric, got {type(val)}"
        # Values can be 0.0 if not present in chart, but must exist as keys? 
        # Actually my fix only adds them if present in chart (simulated energy).
        # Wait, if a God is NOT present in the chart, stem_spec[stem] will be 0.0?
        # Yes, _get_stem_spectrum initializes all stems to 0.0.
        # But 'god_name' lookup depends on 'dm_stem'.
        # And my loop iterates 'stem_spec'. which has ALL 10 stems.
        # So ALL 10 God keys should be present.
        
