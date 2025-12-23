
import sys
import os
sys.path.append(os.getcwd())

from core.trinity.core.unified_arbitrator_master import unified_arbitrator
from core.trinity.core.oracle import TrinityOracle

def test_from_pattern_logic():
    print("Test 1: From-Pattern (从格) Detection and Use-Shen")
    # 丁巳-乙巳-乙丑-乙酉 (From Killings - Metal)
    bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
    ctx = {
        'luck_pillar': '辛丑',
        'annual_pillar': '乙未',
        'data': {
            'city': '首尔 (Seoul)',
            'geo_factor': 1.15,
            'geo_element': 'Metal/Water'
        }
    }
    res = unified_arbitrator.arbitrate_bazi(bazi, {}, ctx)
    
    # Check physics flags
    phy = res.get('physics', {})
    is_follow = phy.get('resonance', {}).get('is_follow', False)
    locking_ratio = phy.get('resonance', {}).get('locking_ratio', 1.0)
    
    print(f"  Locking Ratio: {locking_ratio:.2f}")
    
    # We updated oracle to detect CONG in interactions
    # UnifiedArbitrator should reflect this in rules
    rules = res.get('rules', [])
    has_cong = any('从' in r.get('id', '') or 'CONG' in r.get('id', '') for r in rules)
    
    # Check if verdict contains From-Pattern info (manual check as UI does it)
    print(f"  Rules triggered: {[r['id'] for r in rules]}")
    
    # Check GEO info
    geo = phy.get('geo', {})
    print(f"  GEO Desc: {geo.get('desc')}")
    assert "首尔" in geo.get('desc')
    assert geo.get('temperature_factor') == 1.15

def test_dm_strength_logic():
    print("\nTest 2: DM Strength Logic (Strong vs Weak)")
    # Case A: Strong DM (甲木 born in Spring with roots)
    bazi_strong = ['甲寅', '丙寅', '甲子', '甲子']
    res_strong = unified_arbitrator.arbitrate_bazi(bazi_strong, {}, {})
    lr_strong = res_strong.get('physics', {}).get('resonance', {}).get('locking_ratio', 1.0)
    # Strong DM should have LOW locking_ratio (field weaker than DM)
    print(f"  Strong Case LR: {lr_strong:.2f} (Expected < 0.8 if very strong)")
    
    # Case B: Weak DM (甲木 born in Autumn surrounded by Metal)
    bazi_weak = ['庚申', '辛酉', '甲申', '庚午']
    res_weak = unified_arbitrator.arbitrate_bazi(bazi_weak, {}, {})
    lr_weak = res_weak.get('physics', {}).get('resonance', {}).get('locking_ratio', 1.0)
    # Weak DM should have HIGH locking_ratio (field stronger than DM)
    print(f"  Weak Case LR: {lr_weak:.2f} (Expected > 1.5)")

def test_international_geo():
    print("\nTest 3: International GEO City List Integration")
    from ui.pages.quantum_lab import GEO_CITY_MAP
    
    test_cities = ["东京 (Tokyo)", "纽约 (New York)", "悉尼 (Sydney)"]
    for city in test_cities:
        assert city in GEO_CITY_MAP
        gf, elem = GEO_CITY_MAP[city]
        print(f"  Verified {city}: Factor={gf}, Elem={elem}")

if __name__ == "__main__":
    try:
        test_from_pattern_logic()
        test_dm_strength_logic()
        test_international_geo()
        print("\n✅ Smoke tests completed successfully!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
