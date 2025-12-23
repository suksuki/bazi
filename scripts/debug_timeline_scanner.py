#!/usr/bin/env python3
"""
Phase 36-C: Lifetime Timeline Scanner Deep Debug Test
Diagnoses why 0 events are detected in the timeline scanner.
"""

import sys
sys.path.insert(0, '/home/jin/bazi_predict')

from core.trinity.core.engines.relationship_gravity import RelationshipGravityEngine
from core.trinity.core.nexus.definitions import ArbitrationNexus, BaziParticleNexus
from core.bazi_profile import VirtualBaziProfile

# Test case: 王金星 (from archives)
TEST_CASE = {
    "name": "王金星",
    "bazi": ["丁未", "壬子", "己卯", "甲戌"],
    "day_master": "己",
    "gender": "男",
    "birth_year": 1967
}

def main():
    print("=" * 70)
    print("🔬 Phase 36-C: Timeline Scanner Deep Debug")
    print("=" * 70)
    print(f"\n[TEST CASE] {TEST_CASE['name']}")
    print(f"  八字: {' | '.join(TEST_CASE['bazi'])}")
    print(f"  日主: {TEST_CASE['day_master']} ({TEST_CASE['gender']})")
    print(f"  出生年: {TEST_CASE['birth_year']}")
    
    # 1. Create VirtualBaziProfile
    print(f"\n[STEP 1] Creating VirtualBaziProfile...")
    pillars_dict = {
        'year': TEST_CASE['bazi'][0],
        'month': TEST_CASE['bazi'][1],
        'day': TEST_CASE['bazi'][2],
        'hour': TEST_CASE['bazi'][3]
    }
    gender_code = 1 if TEST_CASE['gender'] == '男' else 0
    v_profile = VirtualBaziProfile(pillars_dict, gender=gender_code)
    
    # 2. Get luck cycles
    print(f"\n[STEP 2] Getting Luck Cycles...")
    luck_cycles = v_profile.get_luck_cycles()
    print(f"  Found {len(luck_cycles)} luck cycles:")
    for lc in luck_cycles[:5]:  # Show first 5
        print(f"    {lc['start_year']}-{lc['end_year']}: {lc['gan_zhi']}")
    if len(luck_cycles) > 5:
        print(f"    ... and {len(luck_cycles) - 5} more")
    
    # 3. Extract Spouse Palace info
    day_pillar = TEST_CASE['bazi'][2]
    spouse_palace = day_pillar[1] if len(day_pillar) > 1 else "?"
    spouse_palace_element = BaziParticleNexus.BRANCHES.get(spouse_palace, ("Unknown",))[0]
    print(f"\n[STEP 3] Spouse Palace Analysis:")
    print(f"  日支 (Day Branch): {spouse_palace}")
    print(f"  配偶宫元素: {spouse_palace_element}")
    
    # 4. Check what clashes with Spouse Palace
    clash_target = ArbitrationNexus.CLASH_MAP.get(spouse_palace)
    print(f"\n[STEP 4] Clash Analysis:")
    print(f"  与 {spouse_palace} 相冲的地支: {clash_target}")
    
    # 5. Create engine
    print(f"\n[STEP 5] Creating RelationshipGravityEngine...")
    dm = TEST_CASE['day_master']
    gravity_engine = RelationshipGravityEngine(dm, TEST_CASE['gender'])
    print(f"  配偶星 (Spouse Star): {gravity_engine.spouse_star_element}")
    
    # 6. Create mock waves (minimal)
    mock_waves = {}
    for elem in ["Wood", "Fire", "Earth", "Metal", "Water"]:
        class MockWave:
            def __init__(self, amp, ph):
                self.amplitude = amp
                self.phase = ph
        mock_waves[elem] = MockWave(10.0, 0.5)
    
    # 7. Scan a sample of years and record states
    print(f"\n[STEP 6] Scanning Sample Years (age 0, 10, 20, 30, 40, 50, 60, 70, 80)...")
    print("-" * 70)
    
    birth_year = TEST_CASE['birth_year']
    sample_ages = [0, 10, 20, 30, 40, 50, 60, 70, 80]
    prev_state = None
    events = []
    
    for age in sample_ages:
        year = birth_year + age
        
        # Get annual pillar
        annual_pillar = v_profile.get_year_pillar(year)
        
        # Find luck pillar
        luck_pillar = "?"
        for lc in luck_cycles:
            if lc['start_year'] <= year <= lc['end_year']:
                luck_pillar = lc['gan_zhi']
                break
        
        # Calculate state
        result = gravity_engine.analyze_relationship(
            mock_waves,
            TEST_CASE['bazi'][:4],
            luck_pillar=luck_pillar,
            annual_pillar=annual_pillar,
            geo_factor=1.0
        )
        
        state = result.get('State', 'UNKNOWN')
        r = result.get('Metrics', {}).get('Orbital_Distance', 0)
        annual_imp = result.get('Metrics', {}).get('Annual_Impulse', 0)
        luck_mod = result.get('Metrics', {}).get('Luck_Modifier', 1.0)
        
        # Check for state change
        changed = "🔴 CHANGE!" if prev_state is not None and state != prev_state else ""
        if changed:
            events.append((age, year, prev_state, state))
        
        print(f"  Age {age:2d} | {year} | 大运:{luck_pillar} | 流年:{annual_pillar} | r={r:.2f} | λ={luck_mod:.2f} | Δr={annual_imp:.1f} | State={state} {changed}")
        
        prev_state = state
    
    print("-" * 70)
    print(f"\n[RESULT] Detected {len(events)} state changes in sample:")
    for age, year, old_state, new_state in events:
        print(f"  Age {age}: {old_state} → {new_state}")
    
    # 8. Diagnosis
    print("\n" + "=" * 70)
    print("🔎 DIAGNOSIS")
    print("=" * 70)
    
    if len(events) == 0:
        print("\n⚠️ 问题: 在样本中未检测到状态变化！")
        print("\n可能原因:")
        print("  1. 所有年份的 Orbital Distance (r) 变化不够大")
        print("  2. 相位相干性 (η) 在所有年份都相同")
        print("  3. 绑定能 (E) 和摄动能 (Perturbation) 的比例始终导致相同状态")
        
        # Check if any annual/luck pillars clash with spouse palace
        print(f"\n[检查冲合] 配偶宫 {spouse_palace} 与各年大运/流年的关系:")
        for age in sample_ages:
            year = birth_year + age
            annual = v_profile.get_year_pillar(year)
            annual_branch = annual[1] if len(annual) > 1 else "?"
            
            luck_p = "?"
            for lc in luck_cycles:
                if lc['start_year'] <= year <= lc['end_year']:
                    luck_p = lc['gan_zhi']
                    break
            luck_branch = luck_p[1] if len(luck_p) > 1 else "?"
            
            # Check clash
            annual_clashes = ArbitrationNexus.CLASH_MAP.get(annual_branch) == spouse_palace
            luck_clashes = ArbitrationNexus.CLASH_MAP.get(luck_branch) == spouse_palace
            
            markers = []
            if annual_clashes:
                markers.append("🚨流年冲")
            if luck_clashes:
                markers.append("⚠️大运冲")
            
            if markers:
                print(f"    Age {age}: 流年{annual_branch} 大运{luck_branch} - {' '.join(markers)}")
    else:
        print(f"✅ 检测到 {len(events)} 个状态变化，算法正常工作！")

if __name__ == "__main__":
    main()
