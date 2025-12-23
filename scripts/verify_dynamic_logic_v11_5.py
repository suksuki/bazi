
import sys
import os
import json
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster

def test_dynamic_shang_guan_zheng_guan():
    print("=== Testing Dynamic Rule Arbitration (V11.5) ===")
    master = UnifiedArbitratorMaster()
    
    # User-inspired case: 戊 (Earth) Day Master
    # Natal: (Year/Month/Day/Hour) - Placeholder for first 3
    # 庚申 is Hour Pillar (Shi Shen)
    natal = ["丙寅", "庚子", "戊辰", "庚申"]
    current_dm = "戊"
    
    # Context: 辛酉大运 (Shang Guan), 乙巳流年 (Zheng Guan)
    context = {
        "luck_pillar": "辛酉",
        "annual_pillar": "乙巳",
        "months_since_switch": 6.0,
        "data": {"city": "Shanghai"}
    }
    
    print(f"Natal: {natal}")
    print(f"Luck: {context['luck_pillar']}")
    print(f"Annual: {context['annual_pillar']}")
    
    # Run Arbitration
    # We pass None for birth_info as it's optional
    res = master.arbitrate_bazi(natal, current_context=context)
    
    if "error" in res:
        print(f"Error: {res['error']}")
        return

    print("\n[Arbitration Results]")
    print(f"DM: {res['meta']['dm']}")
    
    # Check Rules
    rules = res.get("rules", [])
    print(f"\nTriggered Rules ({len(rules)}):")
    found_oppose = False
    for r in rules:
        print(f" - {r.get('id')}: {r.get('name')} (Intensity: {r.get('intensity', 'N/A')})")
        if r.get('id') == "PH28_01":
            found_oppose = True
    
    if found_oppose:
        print("\n✅ SUCCESS: 'Shang Guan vs Zheng Guan' (PH28_01) triggered across layers!")
    else:
        print("\n❌ FAILURE: 'Shang Guan vs Zheng Guan' (PH28_01) NOT triggered.")
        # Debug Intensities if possible (they are local in match_interactions, maybe print them in LogicArbitrator)
        
    # Check if Zheng Cai (癸 in 辰) is considered
    # Traditionally, 戊 in 辰 has 癸 (Zheng Cai) hidden.
    # We should see evidence of its intensity in rule triggers or the state
    print("\n[Physics Readings]")
    print(f"System Entropy: {res['physics']['entropy']}")
    print(f"SAI (Stress): {res['physics']['stress']['SAI']}")
    
    # Verdict synthesis
    print("\nVerdict Summary:")
    print(json.dumps(res.get("verdict", {}), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_dynamic_shang_guan_zheng_guan()
