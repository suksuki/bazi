"""
V26.0 Task 70: Step A Detailed Debug
====================================
Debug Step A calculation to find why Earth energy is 33.10 instead of 29.7
"""

import sys
import os
import json
sys.path.append(os.getcwd())

from core.processors.physics import PhysicsProcessor, STEM_ELEMENTS, BRANCH_ELEMENTS

def debug_step_a():
    """Debug Step A calculation in detail"""
    
    print("=" * 80)
    print("V26.0 Task 70: Step A Detailed Debug")
    print("=" * 80)
    
    # C07: 辛丑、乙未、庚午、甲申
    bazi_list = ['辛丑', '乙未', '庚午', '甲申']
    dm_char = '庚'
    dm_elem = STEM_ELEMENTS.get(dm_char, 'metal')
    
    print(f"\nC07 Bazi: {bazi_list}")
    print(f"Day Master: {dm_char} ({dm_elem})")
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    pillar_weights = config.get('physics', {}).get('pillarWeights', {})
    print(f"\nPillar Weights: {pillar_weights}")
    
    # Manual calculation
    print("\n" + "=" * 80)
    print("Manual Step A Calculation")
    print("=" * 80)
    
    # Initialize energy
    energy = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 'metal': 0.0, 'water': 0.0}
    
    pillar_names = ['year', 'month', 'day', 'hour']
    BASE_SCORE = 10.0
    
    # Hidden stems map
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
    
    print("\n1. Process Stems and Branches:")
    for idx, pillar in enumerate(bazi_list):
        if len(pillar) < 2:
            continue
        
        p_name = pillar_names[idx]
        stem_char = pillar[0]
        branch_char = pillar[1]
        w_pillar = pillar_weights.get(p_name, 1.0)
        
        print(f"\n  Pillar {idx} ({p_name}): {pillar}, weight={w_pillar}")
        
        # A. Heavenly Stems (skip DM for energy counting)
        if idx != 2:  # Skip day master
            elem = STEM_ELEMENTS.get(stem_char, 'wood')
            score = BASE_SCORE * w_pillar
            energy[elem] += score
            print(f"    Stem {stem_char} ({elem}): +{score:.2f} = {energy[elem]:.2f}")
        
        # B. Earthly Branches
        hiddens = GENESIS_HIDDEN_MAP.get(branch_char, [])
        print(f"    Branch {branch_char} hidden stems: {hiddens}")
        
        for h_char, h_weight in hiddens:
            elem = STEM_ELEMENTS.get(h_char, 'wood')
            score = w_pillar * h_weight
            energy[elem] += score
            print(f"      {h_char} ({elem}): +{score:.2f} = {energy[elem]:.2f}")
    
    print(f"\n2. Energy after stems and branches:")
    for elem in ['wood', 'fire', 'earth', 'metal', 'water']:
        print(f"  {elem.capitalize():6s}: {energy.get(elem, 0):.2f}")
    
    # 3. Rooting Logic
    print(f"\n3. Rooting Logic:")
    ROOT_BONUS = 1.2
    SAME_PILLAR_BONUS = 2.5
    
    all_hidden_chars = set()
    for pillar in bazi_list:
        if len(pillar) > 1:
            branch_char = pillar[1]
            hiddens = GENESIS_HIDDEN_MAP.get(branch_char, [])
            for h_char, _ in hiddens:
                all_hidden_chars.add(h_char)
    
    print(f"  All hidden stems: {all_hidden_chars}")
    
    for idx, pillar in enumerate(bazi_list):
        if idx == 2:  # Skip DM
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
            
            if is_same_pillar:
                bonus = original_score * (SAME_PILLAR_BONUS - 1.0)
                print(f"    {stem_char} ({elem}) same pillar rooting: +{bonus:.2f}")
            else:
                bonus = original_score * (ROOT_BONUS - 1.0)
                print(f"    {stem_char} ({elem}) regular rooting: +{bonus:.2f}")
            
            energy[elem] += bonus
            print(f"      {elem}: {energy[elem] - bonus:.2f} + {bonus:.2f} = {energy[elem]:.2f}")
    
    print(f"\n4. Energy after rooting:")
    for elem in ['wood', 'fire', 'earth', 'metal', 'water']:
        print(f"  {elem.capitalize():6s}: {energy.get(elem, 0):.2f}")
    
    # 5. Era Multipliers (if any)
    print(f"\n5. Era Multipliers:")
    print(f"  (None applied in this test)")
    
    print(f"\n" + "=" * 80)
    print(f"Final Step A Energy:")
    for elem in ['wood', 'fire', 'earth', 'metal', 'water']:
        print(f"  {elem.capitalize():6s}: {energy.get(elem, 0):.2f}")
    
    earth_final = energy.get('earth', 0)
    print(f"\nEarth Energy (Step A): {earth_final:.2f}")
    print(f"Expected (from V25 report): ~29.7")
    print(f"Difference: {earth_final - 29.7:.2f}")

if __name__ == "__main__":
    debug_step_a()

