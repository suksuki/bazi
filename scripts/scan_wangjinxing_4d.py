#!/usr/bin/env python3
"""
🚀 SCAN_WANGJINXING_4D: Four-Dimensional Relationship Spacetime Analysis
=========================================================================

Executes full 4D scan on 王金星's relationship dynamics:
1. Luck Cycle Field (大运背景场) - Chronic gravitational modifiers
2. Annual Impulse (流年冲量) - Instantaneous orbital perturbations  
3. Geo Factor (地域常数) - Spatial medium influence on G
4. Timeline State Transitions - Lifetime relationship triggers

Focus Years: 2024 (甲辰), 2025 (乙巳)
"""

import sys
sys.path.insert(0, '/home/jin/bazi_predict')

from core.trinity.core.engines.relationship_gravity import RelationshipGravityEngine
from core.trinity.core.nexus.definitions import ArbitrationNexus, BaziParticleNexus
from core.bazi_profile import VirtualBaziProfile
import json

# ═══════════════════════════════════════════════════════════════════════════
# 📋 TARGET PROFILE: 王金星
# ═══════════════════════════════════════════════════════════════════════════
TARGET = {
    "name": "王金星",
    "bazi": ["丁未", "壬子", "己卯", "甲戌"],
    "day_master": "己",
    "gender": "男",
    "birth_year": 1967,
    "current_age": 57  # 2024
}

# GEO FACTOR CITY MAP
GEO_CITIES = {
    "北京": 1.15,
    "上海": 1.10,
    "广州": 0.90,
    "深圳": 0.92,
    "首尔": 1.10,
    "新加坡": 0.85,
    "东京": 1.08,
}

def print_header(title):
    print("\n" + "═" * 70)
    print(f"  {title}")
    print("═" * 70)

def print_section(title):
    print(f"\n{'─' * 70}")
    print(f"  📊 {title}")
    print("─" * 70)

def main():
    print_header("🚀 SCAN_WANGJINXING_4D: 四维时空情感扫描")
    print(f"  目标: {TARGET['name']}")
    print(f"  八字: {' | '.join(TARGET['bazi'])}")
    print(f"  日主: {TARGET['day_master']} ({TARGET['gender']})")
    print(f"  出生年: {TARGET['birth_year']} | 当前年龄: {TARGET['current_age']}")
    
    # Initialize Profile
    pillars_dict = {
        'year': TARGET['bazi'][0],
        'month': TARGET['bazi'][1],
        'day': TARGET['bazi'][2],
        'hour': TARGET['bazi'][3]
    }
    gender_code = 1 if TARGET['gender'] == '男' else 0
    v_profile = VirtualBaziProfile(pillars_dict, gender=gender_code)
    
    # Initialize Engine
    gravity_engine = RelationshipGravityEngine(TARGET['day_master'], TARGET['gender'])
    
    # Extract key elements
    spouse_palace = TARGET['bazi'][2][1]  # 卯
    spouse_star = gravity_engine.spouse_star_element
    spouse_palace_elem = BaziParticleNexus.BRANCHES.get(spouse_palace, ["Unknown"])[0]
    clash_with_palace = ArbitrationNexus.CLASH_MAP.get(spouse_palace)
    
    print_section("1️⃣ 原局情感基础参数 (Natal Chart Baseline)")
    print(f"  配偶宫 (Spouse Palace): {spouse_palace} ({spouse_palace_elem})")
    print(f"  配偶星 (Spouse Star): {spouse_star}")
    print(f"  配偶宫冲: {spouse_palace} ↔ {clash_with_palace}")
    
    # Mock waves for analysis
    mock_waves = {}
    for elem in ["Wood", "Fire", "Earth", "Metal", "Water"]:
        class MockWave:
            def __init__(self, amp, ph):
                self.amplitude = amp
                self.phase = ph
        mock_waves[elem] = MockWave(10.0, 0.5)
    
    # Get luck cycles
    luck_cycles = v_profile.get_luck_cycles()
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCAN 1: 大运背景场分析 (Luck Cycle Field)
    # ═══════════════════════════════════════════════════════════════════════
    print_section("2️⃣ 大运背景场 (Luck Cycle Field)")
    
    # Find current and next luck cycles
    current_year = 2024
    current_luck = None
    for lc in luck_cycles:
        if lc['start_year'] <= current_year <= lc['end_year']:
            current_luck = lc
            break
    
    print(f"  当前大运: {current_luck['gan_zhi'] if current_luck else '未知'}")
    print(f"  大运范围: {current_luck['start_year']}-{current_luck['end_year']}" if current_luck else "")
    
    # Analyze luck pillar interaction with Spouse Palace
    if current_luck:
        luck_branch = current_luck['gan_zhi'][1]
        luck_stem = current_luck['gan_zhi'][0]
        
        if ArbitrationNexus.CLASH_MAP.get(luck_branch) == spouse_palace:
            print(f"  ⚠️ 大运地支 {luck_branch} 冲 配偶宫 {spouse_palace} → 慢性失稳期!")
        elif ArbitrationNexus.CLASH_MAP.get(spouse_palace) == luck_branch:
            print(f"  ⚠️ 配偶宫 {spouse_palace} 冲 大运 {luck_branch} → 慢性失稳期!")
        else:
            # Check for Liu He
            for pair, elem in ArbitrationNexus.LIU_HE.items():
                if luck_branch in pair and spouse_palace in pair:
                    print(f"  ✨ 大运 {luck_branch} 合 配偶宫 {spouse_palace} → 引力增益期!")
                    break
            else:
                print(f"  ◐ 大运 {luck_branch} 与配偶宫 {spouse_palace} 无直接冲合 → 中性背景")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCAN 2: 流年冲量分析 - 2024 & 2025
    # ═══════════════════════════════════════════════════════════════════════
    print_section("3️⃣ 流年冲量分析 (Annual Impulse Δr)")
    
    focus_years = [2024, 2025, 2026]
    for year in focus_years:
        annual_pillar = v_profile.get_year_pillar(year)
        annual_branch = annual_pillar[1] if len(annual_pillar) > 1 else "?"
        annual_stem = annual_pillar[0] if annual_pillar else "?"
        age = year - TARGET['birth_year']
        
        # Find luck pillar for this year
        luck_p = "?"
        for lc in luck_cycles:
            if lc['start_year'] <= year <= lc['end_year']:
                luck_p = lc['gan_zhi']
                break
        
        # Calculate with dynamic factors
        result = gravity_engine.analyze_relationship(
            mock_waves,
            TARGET['bazi'][:4],
            luck_pillar=luck_p,
            annual_pillar=annual_pillar,
            geo_factor=1.0
        )
        
        state = result.get('State', 'UNKNOWN')
        r = result.get('Metrics', {}).get('Orbital_Distance', 0)
        annual_imp = result.get('Metrics', {}).get('Annual_Impulse', 0)
        luck_mod = result.get('Metrics', {}).get('Luck_Modifier', 1.0)
        E = result.get('Binding_Energy', 0)
        
        # State icon
        state_icon = {"ENTANGLED": "🟢", "BOUND": "🔵", "PERTURBED": "🟠", "UNBOUND": "🔴"}.get(state, "⚪")
        
        # Clash detection
        clash_warning = ""
        if ArbitrationNexus.CLASH_MAP.get(annual_branch) == spouse_palace:
            clash_warning = f"🚨 流年{annual_branch}冲配偶宫{spouse_palace}!"
        elif annual_branch == spouse_palace:
            clash_warning = f"⚠️ 流年{annual_branch}临配偶宫!"
        
        print(f"\n  📅 {year}年 ({age}岁) | 流年: {annual_pillar} | 大运: {luck_p}")
        print(f"     State: {state_icon} {state} | E={E:.1f} | r={r:.2f} | λ={luck_mod:.2f} | Δr={annual_imp:.1f}")
        if clash_warning:
            print(f"     {clash_warning}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCAN 3: 地域常数分析 (Geo Factor ε)
    # ═══════════════════════════════════════════════════════════════════════
    print_section("4️⃣ 地域常数分析 (Geo Factor ε)")
    
    print("  测试不同城市对 2025 年感情状态的影响:")
    print()
    
    year_2025 = 2025
    annual_2025 = v_profile.get_year_pillar(year_2025)
    luck_2025 = None
    for lc in luck_cycles:
        if lc['start_year'] <= year_2025 <= lc['end_year']:
            luck_2025 = lc['gan_zhi']
            break
    
    for city, geo_factor in GEO_CITIES.items():
        result = gravity_engine.analyze_relationship(
            mock_waves,
            TARGET['bazi'][:4],
            luck_pillar=luck_2025,
            annual_pillar=annual_2025,
            geo_factor=geo_factor
        )
        
        state = result.get('State', 'UNKNOWN')
        E = result.get('Binding_Energy', 0)
        r = result.get('Metrics', {}).get('Orbital_Distance', 0)
        
        state_icon = {"ENTANGLED": "🟢", "BOUND": "🔵", "PERTURBED": "🟠", "UNBOUND": "🔴"}.get(state, "⚪")
        
        print(f"    {city:8s} (ε={geo_factor:.2f}) → {state_icon} {state:10s} | E={E:.1f} | r={r:.2f}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCAN 4: 终身时间线 (0-100 岁完整扫描)
    # ═══════════════════════════════════════════════════════════════════════
    print_section("5️⃣ 终身情感时间线 (Lifetime State Transitions)")
    
    timeline_events = []
    prev_state = None
    birth_year = TARGET['birth_year']
    
    for age in range(0, 101):
        year = birth_year + age
        annual_pillar = v_profile.get_year_pillar(year)
        
        luck_pillar = "?"
        for lc in luck_cycles:
            if lc['start_year'] <= year <= lc['end_year']:
                luck_pillar = lc['gan_zhi']
                break
        
        result = gravity_engine.analyze_relationship(
            mock_waves,
            TARGET['bazi'][:4],
            luck_pillar=luck_pillar,
            annual_pillar=annual_pillar,
            geo_factor=1.0
        )
        
        current_state = result.get('State', 'UNKNOWN')
        
        if prev_state is not None and current_state != prev_state:
            timeline_events.append({
                "age": age,
                "year": year,
                "luck": luck_pillar,
                "annual": annual_pillar,
                "transition": f"{prev_state} → {current_state}",
                "r": result.get('Metrics', {}).get('Orbital_Distance', 0),
                "E": result.get('Binding_Energy', 0)
            })
        
        prev_state = current_state
    
    print(f"  检测到 {len(timeline_events)} 个状态转换点:")
    print()
    
    for event in timeline_events:
        # Determine icon based on transition
        if "UNBOUND" in event['transition']:
            icon = "🚨"
        elif "PERTURBED" in event['transition'] and "→ PERTURBED" in event['transition']:
            icon = "⚠️"
        elif "ENTANGLED" in event['transition'] and "→ ENTANGLED" in event['transition']:
            icon = "🌟"
        else:
            icon = "◐"
        
        print(f"    {icon} {event['year']}年 ({event['age']}岁) | 大运:{event['luck']} | 流年:{event['annual']}")
        print(f"       {event['transition']} | r={event['r']:.2f} | E={event['E']:.1f}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # FINAL DIAGNOSIS
    # ═══════════════════════════════════════════════════════════════════════
    print_header("🔮 四维诊断结论 (4D Diagnosis)")
    
    # 2025 analysis
    annual_2025 = v_profile.get_year_pillar(2025)
    annual_branch_2025 = annual_2025[1] if len(annual_2025) > 1 else "?"
    
    print(f"\n  📌 2025年 (乙巳) 关键分析:")
    print(f"     流年地支: 巳 (Fire)")
    print(f"     配偶宫: {spouse_palace} ({spouse_palace_elem})")
    
    # Check 巳 vs 卯 relationship
    if ArbitrationNexus.CLASH_MAP.get('巳') == spouse_palace:
        print(f"     ⚠️ 巳 冲 {spouse_palace} → 剧烈摄动风险!")
    else:
        # Check Punishment
        penalty_巳 = BaziParticleNexus.PENALTY_GROUPS.get('巳', {})
        if spouse_palace in penalty_巳.get('components', []):
            print(f"     ⚠️ 巳 刑 {spouse_palace} → 中度摄动")
        else:
            print(f"     ◐ 巳 与 {spouse_palace} 无直接冲刑 → 相对平稳")
    
    print(f"\n  🌍 地域建议:")
    print(f"     最佳城市: 北京/首尔 (ε≥1.10, Water/Metal 增益)")
    print(f"     规避城市: 新加坡/广州 (ε≤0.90, Fire 加剧)")
    
    print("\n" + "═" * 70)
    print("  ✅ SCAN_WANGJINXING_4D 完成")
    print("═" * 70)

if __name__ == "__main__":
    main()
