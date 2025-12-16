"""
V26.0 Task 70: Step A 原子级计算细节披露
==========================================
详细分解 C07 案例 Earth 能量的完整计算过程
"""

import sys
import os
import json
import io

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.getcwd())

from core.processors.physics import PhysicsProcessor, STEM_ELEMENTS, BRANCH_ELEMENTS

def atomic_step_a_debug():
    """原子级 Step A 计算细节披露"""
    
    print("=" * 80)
    print("V26.0 Task 70: Step A 原子级计算细节披露 (C07 案例)")
    print("=" * 80)
    
    # C07: 辛丑、乙未、庚午、甲申
    bazi_list = ['辛丑', '乙未', '庚午', '甲申']
    dm_char = '庚'
    dm_elem = STEM_ELEMENTS.get(dm_char, 'metal')
    
    print(f"\nC07 八字: {bazi_list}")
    print(f"日主: {dm_char} ({dm_elem})")
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    pillar_weights = config.get('physics', {}).get('pillarWeights', {})
    pg_year = pillar_weights.get('year', 1.0)
    pg_month = pillar_weights.get('month', 1.8)
    pg_day = pillar_weights.get('day', 1.5)
    pg_hour = pillar_weights.get('hour', 1.2)
    
    print(f"\n柱位权重:")
    print(f"  pg_year: {pg_year}")
    print(f"  pg_month: {pg_month}")
    print(f"  pg_day: {pg_day}")
    print(f"  pg_hour: {pg_hour}")
    
    BASE_SCORE = 10.0
    ROOT_BONUS = 1.2
    SAME_PILLAR_BONUS = 2.5
    
    print(f"\n基础参数:")
    print(f"  BASE_SCORE: {BASE_SCORE}")
    print(f"  ROOT_BONUS: {ROOT_BONUS}")
    print(f"  SAME_PILLAR_BONUS: {SAME_PILLAR_BONUS}")
    
    # Genesis Hidden Map
    GENESIS_HIDDEN_MAP = {
        '子': [('癸', 10)],
        '丑': [('己', 10), ('癸', 7), ('辛', 3)],
        '寅': [('甲', 10), ('丙', 7), ('戊', 3)],
        '卯': [('乙', 10)],
        '辰': [('戊', 10), ('乙', 7), ('癸', 3)],
        '巳': [('丙', 10), ('戊', 7), ('庚', 3)],
        '午': [('丁', 10), ('己', 7)],
        '未': [('己', 10), ('丁', 7), ('乙', 3)],
        '申': [('庚', 10), ('壬', 7), ('戊', 3)],
        '酉': [('辛', 10)],
        '戌': [('戊', 10), ('辛', 7), ('丁', 3)],
        '亥': [('壬', 10), ('甲', 7)]
    }
    
    pillar_names = ['year', 'month', 'day', 'hour']
    
    # Initialize energy
    energy = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 'metal': 0.0, 'water': 0.0}
    all_hidden_chars = set()
    
    # Detailed breakdown for Earth energy
    earth_breakdown = {
        'stems': [],  # 天干贡献
        'branch_main': [],  # 地支主气贡献
        'branch_hidden': [],  # 地支藏干贡献
        'rooting': []  # 通根加成
    }
    
    print("\n" + "=" * 80)
    print("分解 1: 天干能量贡献（Earth 相关）")
    print("=" * 80)
    
    # Process stems (天干)
    for idx, pillar in enumerate(bazi_list):
        if len(pillar) < 1:
            continue
        
        p_name = pillar_names[idx]
        stem_char = pillar[0]
        w_pillar = pillar_weights.get(p_name, 1.0)
        
        if idx != 2:  # Skip day master
            elem = STEM_ELEMENTS.get(stem_char, 'wood')
            score = BASE_SCORE * w_pillar
            energy[elem] += score
            
            if elem == 'earth':
                earth_breakdown['stems'].append({
                    'pillar': p_name,
                    'stem': stem_char,
                    'weight': w_pillar,
                    'score': score,
                    'formula': f'{BASE_SCORE} × {w_pillar} = {score}'
                })
                print(f"  {p_name}柱 天干 {stem_char} ({elem}): {BASE_SCORE} × {w_pillar} = {score:.2f}")
    
    print(f"\n天干 Earth 能量小计: {sum([x['score'] for x in earth_breakdown['stems']]):.2f}")
    
    print("\n" + "=" * 80)
    print("分解 2: 地支主气和藏干能量贡献（Earth 相关）")
    print("=" * 80)
    
    # Process branches (地支)
    for idx, pillar in enumerate(bazi_list):
        if len(pillar) < 2:
            continue
        
        p_name = pillar_names[idx]
        branch_char = pillar[1]
        w_pillar = pillar_weights.get(p_name, 1.0)
        
        hiddens = GENESIS_HIDDEN_MAP.get(branch_char, [])
        print(f"\n  {p_name}柱 地支 {branch_char} (权重={w_pillar}):")
        
        for h_idx, (h_char, h_weight) in enumerate(hiddens):
            all_hidden_chars.add(h_char)
            elem = STEM_ELEMENTS.get(h_char, 'wood')
            score = w_pillar * h_weight
            energy[elem] += score
            
            if elem == 'earth':
                is_main_qi = (h_idx == 0)  # 第一个是主气
                entry = {
                    'pillar': p_name,
                    'branch': branch_char,
                    'hidden_stem': h_char,
                    'hidden_weight': h_weight,
                    'pillar_weight': w_pillar,
                    'score': score,
                    'is_main_qi': is_main_qi,
                    'formula': f'{w_pillar} × {h_weight} = {score}'
                }
                
                if is_main_qi:
                    earth_breakdown['branch_main'].append(entry)
                    print(f"    主气 {h_char} ({elem}): {w_pillar} × {h_weight} = {score:.2f} [主气]")
                else:
                    earth_breakdown['branch_hidden'].append(entry)
                    print(f"    藏干 {h_char} ({elem}): {w_pillar} × {h_weight} = {score:.2f}")
    
    branch_main_total = sum([x['score'] for x in earth_breakdown['branch_main']])
    branch_hidden_total = sum([x['score'] for x in earth_breakdown['branch_hidden']])
    
    print(f"\n地支主气 Earth 能量小计: {branch_main_total:.2f}")
    print(f"地支藏干 Earth 能量小计: {branch_hidden_total:.2f}")
    print(f"地支 Earth 能量总计: {branch_main_total + branch_hidden_total:.2f}")
    
    print("\n" + "=" * 80)
    print("分解 3: 通根加成（Earth 相关）")
    print("=" * 80)
    
    # Rooting logic
    for idx, pillar in enumerate(bazi_list):
        if idx == 2:  # Skip day master
            continue
        if len(pillar) < 1:
            continue
        
        stem_char = pillar[0]
        p_name = pillar_names[idx]
        w_pillar = pillar_weights.get(p_name, 1.0)
        
        if stem_char in all_hidden_chars:
            elem = STEM_ELEMENTS.get(stem_char, 'wood')
            original_score = BASE_SCORE * w_pillar
            
            # Check if same pillar rooting
            branch_char = pillar[1] if len(pillar) > 1 else ''
            is_same_pillar = False
            if branch_char:
                hiddens = GENESIS_HIDDEN_MAP.get(branch_char, [])
                for h_char, _ in hiddens:
                    if h_char == stem_char:
                        is_same_pillar = True
                        break
            
            if elem == 'earth':
                if is_same_pillar:
                    bonus = original_score * (SAME_PILLAR_BONUS - 1.0)
                    bonus_type = '自坐强根'
                    print(f"  {p_name}柱 天干 {stem_char} ({elem}): {original_score:.2f} × ({SAME_PILLAR_BONUS} - 1.0) = {bonus:.2f} [自坐强根]")
                else:
                    bonus = original_score * (ROOT_BONUS - 1.0)
                    bonus_type = '通根'
                    print(f"  {p_name}柱 天干 {stem_char} ({elem}): {original_score:.2f} × ({ROOT_BONUS} - 1.0) = {bonus:.2f} [通根]")
                
                earth_breakdown['rooting'].append({
                    'pillar': p_name,
                    'stem': stem_char,
                    'original_score': original_score,
                    'bonus': bonus,
                    'type': bonus_type,
                    'formula': f'{original_score:.2f} × ({SAME_PILLAR_BONUS if is_same_pillar else ROOT_BONUS} - 1.0) = {bonus:.2f}'
                })
                
                energy[elem] += bonus
    
    rooting_total = sum([x['bonus'] for x in earth_breakdown['rooting']])
    print(f"\n通根加成 Earth 能量小计: {rooting_total:.2f}")
    
    # Final summary
    earth_final = energy.get('earth', 0)
    
    print("\n" + "=" * 80)
    print("C07 Earth 能量完整分解表")
    print("=" * 80)
    
    print(f"\n1. 天干贡献:")
    for entry in earth_breakdown['stems']:
        print(f"   {entry['pillar']}柱 {entry['stem']}: {entry['formula']}")
    stems_total = sum([x['score'] for x in earth_breakdown['stems']])
    print(f"   小计: {stems_total:.2f}")
    
    print(f"\n2. 地支主气贡献:")
    for entry in earth_breakdown['branch_main']:
        print(f"   {entry['pillar']}柱 {entry['branch']} 主气 {entry['hidden_stem']}: {entry['formula']}")
    print(f"   小计: {branch_main_total:.2f}")
    
    print(f"\n3. 地支藏干贡献:")
    for entry in earth_breakdown['branch_hidden']:
        print(f"   {entry['pillar']}柱 {entry['branch']} 藏干 {entry['hidden_stem']}: {entry['formula']}")
    print(f"   小计: {branch_hidden_total:.2f}")
    
    print(f"\n4. 通根加成:")
    for entry in earth_breakdown['rooting']:
        print(f"   {entry['pillar']}柱 {entry['stem']} ({entry['type']}): {entry['formula']}")
    print(f"   小计: {rooting_total:.2f}")
    
    print(f"\n" + "=" * 80)
    print(f"Earth 能量总计: {earth_final:.2f}")
    print(f"AI 预期值: 48.0")
    print(f"差异: {earth_final - 48.0:.2f}")
    print("=" * 80)
    
    # Vault physics check
    print("\n" + "=" * 80)
    print("墓库物理逻辑确认")
    print("=" * 80)
    
    day_branch = bazi_list[2][1] if len(bazi_list) > 2 and len(bazi_list[2]) > 1 else ''
    vault_mapping = {
        '辰': 'water',
        '戌': 'fire',
        '丑': 'metal',
        '未': 'wood'
    }
    
    print(f"\n日支: {day_branch}")
    print(f"墓库映射表: {vault_mapping}")
    
    if day_branch in vault_mapping:
        vault_element = vault_mapping[day_branch]
        print(f"  ✅ 日支 {day_branch} 是 {vault_element} 的墓库")
    else:
        print(f"  ❌ 日支 {day_branch} 不是墓库")
        print(f"  说明: 根据 vault_mapping，只有 辰、戌、丑、未 是墓库")
        print(f"  午火不是墓库，因此 AI 预期的 -5.0 墓库惩罚可能基于错误判断")
    
    # Generate detailed breakdown table
    print("\n" + "=" * 80)
    print("完整数值分解表（JSON格式）")
    print("=" * 80)
    
    breakdown_json = {
        'case': 'C07',
        'bazi': bazi_list,
        'day_master': dm_char,
        'parameters': {
            'BASE_SCORE': BASE_SCORE,
            'ROOT_BONUS': ROOT_BONUS,
            'SAME_PILLAR_BONUS': SAME_PILLAR_BONUS,
            'pillar_weights': {
                'year': pg_year,
                'month': pg_month,
                'day': pg_day,
                'hour': pg_hour
            }
        },
        'earth_energy_breakdown': {
            'stems': earth_breakdown['stems'],
            'branch_main': earth_breakdown['branch_main'],
            'branch_hidden': earth_breakdown['branch_hidden'],
            'rooting': earth_breakdown['rooting'],
            'totals': {
                'stems': stems_total,
                'branch_main': branch_main_total,
                'branch_hidden': branch_hidden_total,
                'rooting': rooting_total,
                'final': earth_final
            }
        },
        'vault_physics': {
            'day_branch': day_branch,
            'is_vault': day_branch in vault_mapping,
            'vault_element': vault_mapping.get(day_branch, None)
        },
        'comparison': {
            'actual': earth_final,
            'ai_expected': 48.0,
            'difference': earth_final - 48.0
        }
    }
    
    print(json.dumps(breakdown_json, indent=2, ensure_ascii=False))
    
    return breakdown_json

if __name__ == "__main__":
    breakdown = atomic_step_a_debug()

