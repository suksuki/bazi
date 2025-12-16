"""
V26.0 Task 70: Step-by-Step Earth Energy Calculation Debug
==========================================================
Detailed step-by-step calculation to verify Earth energy alignment.
"""

import sys
import os
import json
sys.path.append(os.getcwd())

from core.processors.physics import PhysicsProcessor, STEM_ELEMENTS, BRANCH_ELEMENTS
from core.interactions import STEM_COMBINATIONS, BRANCH_CLASHES, BRANCH_HARMS, BRANCH_PUNISHMENTS, BRANCH_SIX_COMBINES

def step_by_step_c07():
    """Step-by-step calculation for C07 case"""
    
    print("=" * 80)
    print("V26.0 Task 70: C07 Earth Energy Step-by-Step Calculation")
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
    
    # Initialize PhysicsProcessor
    physics = PhysicsProcessor()
    
    # Step A: Calculate raw energy (before complex interactions)
    print("\n" + "=" * 80)
    print("Step A: Raw Energy Calculation (Before Complex Interactions)")
    print("=" * 80)
    
    # For Step A, we need to manually calculate without complex interactions
    # Since PhysicsProcessor always applies complex interactions, we'll calculate manually
    print("\nNote: PhysicsProcessor always applies complex interactions.")
    print("We'll calculate Step A manually, then show Step B separately.")
    
    # Manual Step A calculation (copy from step_a_debug logic)
    energy_a = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 'metal': 0.0, 'water': 0.0}
    pillar_weights = config.get('physics', {}).get('pillarWeights', {})
    BASE_SCORE = 10.0
    GENESIS_HIDDEN_MAP = physics.GENESIS_HIDDEN_MAP
    pillar_names = ['year', 'month', 'day', 'hour']
    all_hidden_chars = set()
    
    # Process stems and branches
    for idx, pillar in enumerate(bazi_list):
        if len(pillar) < 2:
            continue
        p_name = pillar_names[idx]
        stem_char = pillar[0]
        branch_char = pillar[1]
        w_pillar = pillar_weights.get(p_name, 1.0)
        
        if idx != 2:  # Skip DM
            elem = STEM_ELEMENTS.get(stem_char, 'wood')
            score = BASE_SCORE * w_pillar
            energy_a[elem] += score
        
        hiddens = GENESIS_HIDDEN_MAP.get(branch_char, [])
        for h_char, h_weight in hiddens:
            all_hidden_chars.add(h_char)
            elem = STEM_ELEMENTS.get(h_char, 'wood')
            score = w_pillar * h_weight
            energy_a[elem] += score
    
    # Rooting
    ROOT_BONUS = 1.2
    SAME_PILLAR_BONUS = 2.5
    for idx, pillar in enumerate(bazi_list):
        if idx == 2:
            continue
        if len(pillar) < 1:
            continue
        stem_char = pillar[0]
        p_name = pillar_names[idx]
        w_pillar = pillar_weights.get(p_name, 1.0)
        
        if stem_char in all_hidden_chars:
            elem = STEM_ELEMENTS.get(stem_char, 'wood')
            original_score = BASE_SCORE * w_pillar
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
            else:
                bonus = original_score * (ROOT_BONUS - 1.0)
            energy_a[elem] += bonus
    
    print(f"\nEnergy after Step A (Rooting, Era Multipliers, but NO interactions):")
    for elem in ['wood', 'fire', 'earth', 'metal', 'water']:
        print(f"  {elem.capitalize():6s}: {energy_a.get(elem, 0):.2f}")
    
    earth_a = energy_a.get('earth', 0)
    print(f"\nEarth Energy (Step A): {earth_a:.2f}")
    print(f"Expected (from V25 report): ~29.7")
    
    # Step B: Apply Complex Interactions
    print("\n" + "=" * 80)
    print("Step B: Complex Interactions")
    print("=" * 80)
    
    # Extract stems and branches
    stems = [p[0] if len(p) > 0 else '' for p in bazi_list]
    branches = [p[1] if len(p) > 1 else '' for p in bazi_list]
    month_branch = branches[1] if len(branches) > 1 else ''
    
    print(f"\nStems: {stems}")
    print(f"Branches: {branches}")
    print(f"Month Branch: {month_branch}")
    
    # Get interaction parameters
    interactions_config = config.get('interactions', {})
    branch_events = interactions_config.get('branchEvents', {})
    clash_score = branch_events.get('clashScore', -3.0)
    punishment_penalty = branch_events.get('punishmentPenalty', -3.0)
    harm_penalty = branch_events.get('harmPenalty', -2.0)
    six_harmony = branch_events.get('sixHarmony', 5.0)
    
    print(f"\nInteraction Parameters:")
    print(f"  clashScore: {clash_score}")
    print(f"  punishmentPenalty: {punishment_penalty}")
    print(f"  harmPenalty: {harm_penalty}")
    print(f"  sixHarmony: {six_harmony}")
    
    # Start with Step A energy
    energy_b = energy_a.copy()
    earth_before = energy_b.get('earth', 0)
    
    print(f"\nEarth Energy BEFORE interactions: {earth_before:.2f}")
    
    # Track each interaction
    interactions_applied = []
    
    # 1. Check 天干五合 (Stem Five Combination)
    print(f"\n--- 1. Stem Five Combination ---")
    month_elem = BRANCH_ELEMENTS.get(month_branch, 'earth')
    print(f"Month Element: {month_elem}")
    
    pairs = [(0, 1), (1, 2), (2, 3)]  # Year-Month, Month-Day, Day-Hour
    for idx1, idx2 in pairs:
        if idx1 >= len(stems) or idx2 >= len(stems):
            continue
        s1, s2 = stems[idx1], stems[idx2]
        if not s1 or not s2:
            continue
        
            if STEM_COMBINATIONS.get(s1) == s2:
                print(f"  Found Stem Five Combination: {s1} <-> {s2} (positions {idx1}-{idx2})")
            e1 = STEM_ELEMENTS.get(s1, 'wood')
            e2 = STEM_ELEMENTS.get(s2, 'wood')
            print(f"    Elements: {e1} ({s1}), {e2} ({s2})")
            
            # Check if transformation succeeds
            combo_set = frozenset([s1, s2])
            transform_map = {
                frozenset(['甲', '己']): 'earth',
                frozenset(['乙', '庚']): 'metal',
                frozenset(['丙', '辛']): 'water',
                frozenset(['丁', '壬']): 'wood',
                frozenset(['戊', '癸']): 'fire'
            }
            transform_to = transform_map.get(combo_set)
            
            if transform_to and transform_to == month_elem:
                print(f"    Transformation succeeds")
            else:
                print(f"    Transformation fails - applies 0.4x penalty to {e1} and {e2}")
                if e1 == 'earth' or e2 == 'earth':
                    print(f"    WARNING: This affects Earth energy!")
                    earth_before_stem = energy_b.get('earth', 0)
                    if e1 == 'earth':
                        energy_b['earth'] = energy_b.get('earth', 0) * 0.4
                    if e2 == 'earth':
                        energy_b['earth'] = energy_b.get('earth', 0) * 0.4
                    earth_after_stem = energy_b.get('earth', 0)
                    print(f"    Earth: {earth_before_stem:.2f} -> {earth_after_stem:.2f}")
                    interactions_applied.append(f"Stem Five Binding (Earth): {earth_before_stem:.2f} -> {earth_after_stem:.2f}")
    
    # 2. Check 地支三合/三会 (skip for C07, not applicable)
    print(f"\n--- 2. Trine/Directional Harmony ---")
    print(f"  Not applicable for C07")
    
    # 3. Check 地支六合 (Six Combinations)
    print(f"\n--- 3. Six Combinations ---")
    earth_before_liuhe = energy_b.get('earth', 0)
    print(f"Earth before Six Combinations: {earth_before_liuhe:.2f}")
    print(f"Branches: {branches}")
    print(f"BRANCH_SIX_COMBINES check:")
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
            print(f"  Checking {b1} <-> {b2}: BRANCH_SIX_COMBINES.get('{b1}') = {BRANCH_SIX_COMBINES.get(b1)}")
            if BRANCH_SIX_COMBINES.get(b1) == b2:
                    combo_set = frozenset([b1, b2])
                    transform_map = {
                        frozenset(['子', '丑']): 'earth',
                        frozenset(['寅', '亥']): 'wood',
                        frozenset(['卯', '戌']): 'fire',
                        frozenset(['辰', '酉']): 'metal',
                        frozenset(['巳', '申']): 'water',
                        frozenset(['午', '未']): 'earth'
                    }
                    transform_to = transform_map.get(combo_set)
                    if transform_to:
                        print(f"  Found Six Combine: {b1} <-> {b2} -> {transform_to}")
                    if transform_to == 'earth':
                        base_energy = energy_b.get('earth', 0)
                        energy_b['earth'] = base_energy + six_harmony
                        earth_after_liuhe = energy_b.get('earth', 0)
                        print(f"    Earth: {base_energy:.2f} + {six_harmony:.2f} = {earth_after_liuhe:.2f}")
                        interactions_applied.append(f"Six Combine (Wu-Wei): {base_energy:.2f} + {six_harmony:.2f} = {earth_after_liuhe:.2f}")
    
    # 4. Check 地支六冲 (Six Clashes)
    print(f"\n--- 4. Six Clashes ---")
    earth_before_clash = energy_b.get('earth', 0)
    
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
            if BRANCH_CLASHES.get(b1) == b2:
                e1 = BRANCH_ELEMENTS.get(b1, 'earth')
                e2 = BRANCH_ELEMENTS.get(b2, 'earth')
                print(f"  Found Six Clash: {b1} <-> {b2} ({e1} <-> {e2})")
                if e1 == 'earth' or e2 == 'earth':
                    earth_before_this = energy_b.get('earth', 0)
                    if e1 == 'earth':
                        energy_b['earth'] = max(0, energy_b.get('earth', 0) + clash_score)
                    if e2 == 'earth':
                        energy_b['earth'] = max(0, energy_b.get('earth', 0) + clash_score)
                    earth_after_this = energy_b.get('earth', 0)
                    print(f"    Earth: {earth_before_this:.2f} + ({clash_score:.2f}) = {earth_after_this:.2f}")
                    interactions_applied.append(f"Six Clash ({b1}-{b2}): {earth_before_this:.2f} + ({clash_score:.2f}) = {earth_after_this:.2f}")
    
    # 5. Check 相刑 (Punishment)
    print(f"\n--- 5. Punishment ---")
    earth_before_punishment = energy_b.get('earth', 0)
    
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
            if b2 in BRANCH_PUNISHMENTS.get(b1, []):
                e1 = BRANCH_ELEMENTS.get(b1, 'earth')
                e2 = BRANCH_ELEMENTS.get(b2, 'earth')
                print(f"  Found Punishment: {b1} <-> {b2} ({e1} <-> {e2})")
                if e1 == 'earth' or e2 == 'earth':
                    earth_before_this = energy_b.get('earth', 0)
                    if e1 == 'earth':
                        energy_b['earth'] = max(0, energy_b.get('earth', 0) + punishment_penalty)
                    if e2 == 'earth':
                        energy_b['earth'] = max(0, energy_b.get('earth', 0) + punishment_penalty)
                    earth_after_this = energy_b.get('earth', 0)
                    print(f"    Earth: {earth_before_this:.2f} + ({punishment_penalty:.2f}) = {earth_after_this:.2f}")
                    interactions_applied.append(f"Punishment ({b1}-{b2}): {earth_before_this:.2f} + ({punishment_penalty:.2f}) = {earth_after_this:.2f}")
    
    # 6. Check 相害 (Harm)
    print(f"\n--- 6. Harm ---")
    earth_before_harm = energy_b.get('earth', 0)
    
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
            if BRANCH_HARMS.get(b1) == b2:
                e1 = BRANCH_ELEMENTS.get(b1, 'earth')
                e2 = BRANCH_ELEMENTS.get(b2, 'earth')
                print(f"  Found Harm: {b1} <-> {b2} ({e1} <-> {e2})")
                if e1 == 'earth' or e2 == 'earth':
                    earth_before_this = energy_b.get('earth', 0)
                    if e1 == 'earth':
                        energy_b['earth'] = max(0, energy_b.get('earth', 0) + harm_penalty)
                    if e2 == 'earth':
                        energy_b['earth'] = max(0, energy_b.get('earth', 0) + harm_penalty)
                    earth_after_this = energy_b.get('earth', 0)
                    print(f"    Earth: {earth_before_this:.2f} + ({harm_penalty:.2f}) = {earth_after_this:.2f}")
                    interactions_applied.append(f"Harm ({b1}-{b2}): {earth_before_this:.2f} + ({harm_penalty:.2f}) = {earth_after_this:.2f}")
    
    # 7. Check 墓库物理 (Vault Physics)
    print(f"\n--- 7. Vault Physics ---")
    day_branch = branches[2] if len(branches) > 2 else ''
    vault_mapping = {
        '辰': 'water',
        '戌': 'fire',
        '丑': 'metal',
        '未': 'wood'
    }
    
    print(f"Day Branch: {day_branch}")
    if day_branch in vault_mapping:
        vault_element = vault_mapping[day_branch]
        print(f"  Vault Element: {vault_element}")
        if vault_element == 'earth':
            print(f"    WARNING: This affects Earth energy!")
    else:
        print(f"  Day branch {day_branch} is not a vault, no vault physics applied")
    
    # Final result
    earth_final = energy_b.get('earth', 0)
    
    print("\n" + "=" * 80)
    print("Step B: Final Earth Energy After All Interactions")
    print("=" * 80)
    print(f"\nEarth Energy (Step A): {earth_a:.2f}")
    print(f"Earth Energy (Step B Final): {earth_final:.2f}")
    print(f"Difference: {earth_final - earth_a:.2f}")
    
    print(f"\nInteractions Applied:")
    for interaction in interactions_applied:
        print(f"  - {interaction}")
    
    print(f"\nExpected (from V25 report):")
    print(f"  Step A: ~29.7")
    print(f"  Step B: 18.0 - 22.0 (after penalties: -3.0 -3.0 -2.0 = -8.0)")
    print(f"  Expected Step B: 29.7 - 8.0 = 21.7 (if no 六合)")
    print(f"  OR: 29.7 + 5.0 - 3.0 - 3.0 - 2.0 = 26.7 (if 六合 applied first)")
    
    print(f"\nActual Results:")
    print(f"  Step A: {earth_a:.2f}")
    print(f"  Step B: {earth_final:.2f}")
    
    # Validation
    if 18.0 <= earth_final <= 22.0:
        print(f"\nPASS: Earth energy in expected range [18.0, 22.0]")
        return True
    else:
        print(f"\nFAIL: Earth energy NOT in expected range [18.0, 22.0]")
        return False

if __name__ == "__main__":
    success = step_by_step_c07()
    sys.exit(0 if success else 1)
