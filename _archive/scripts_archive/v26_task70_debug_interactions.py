"""
V26.0 Task 70: Debug Complex Interactions for C07
=================================================
Detailed debugging to track Earth energy changes through each interaction step.
"""

import sys
import os
sys.path.append(os.getcwd())

from core.processors.physics import PhysicsProcessor, STEM_ELEMENTS, BRANCH_ELEMENTS
from core.interactions import STEM_COMBINATIONS, BRANCH_CLASHES, BRANCH_HARMS, BRANCH_PUNISHMENTS, BRANCH_SIX_COMBINES

def debug_c07_interactions():
    """Debug C07 interactions step by step"""
    
    bazi_list = ['辛丑', '乙未', '庚午', '甲申']
    dm_elem = 'metal'
    
    # Initialize energy (after rooting, before interactions)
    energy = {'wood': 42.6, 'fire': 18.4, 'earth': 29.7, 'metal': 31.4, 'water': 11.9}
    
    print("=" * 80)
    print("V26.0 Task 70: Debug C07 Complex Interactions")
    print("=" * 80)
    print(f"\nInitial Energy (After Rooting, Before Interactions):")
    print(f"  Earth: {energy['earth']:.2f}")
    print(f"  Fire: {energy['fire']:.2f}")
    print(f"  Wood: {energy['wood']:.2f}")
    print(f"  Metal: {energy['metal']:.2f}")
    print(f"  Water: {energy['water']:.2f}")
    
    # Extract stems and branches
    stems = [p[0] if len(p) > 0 else '' for p in bazi_list]
    branches = [p[1] if len(p) > 1 else '' for p in bazi_list]
    month_branch = branches[1] if len(branches) > 1 else ''
    
    print(f"\nStems: {stems}")
    print(f"Branches: {branches}")
    print(f"Month Branch: {month_branch}")
    
    # Step 1: Check 天干五合 (Stem Five Combination)
    print(f"\n{'=' * 80}")
    print("Step 1: 天干五合 (Stem Five Combination)")
    print("=" * 80)
    
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
            print(f"\n  Found 天干五合: {s1} <-> {s2} (positions {idx1}-{idx2})")
            
            combo_set = frozenset([s1, s2])
            transform_map = {
                frozenset(['甲', '己']): 'earth',
                frozenset(['乙', '庚']): 'metal',
                frozenset(['丙', '辛']): 'water',
                frozenset(['丁', '壬']): 'wood',
                frozenset(['戊', '癸']): 'fire'
            }
            transform_to = transform_map.get(combo_set)
            
            e1 = STEM_ELEMENTS.get(s1, 'wood')
            e2 = STEM_ELEMENTS.get(s2, 'wood')
            print(f"    Elements: {e1} ({s1}), {e2} ({s2})")
            print(f"    Transform To: {transform_to}")
            print(f"    Month Element: {month_elem}")
            
            if transform_to and transform_to == month_elem:
                print(f"    ✅ Transformation succeeds (合化)")
                print(f"    Before: Earth={energy['earth']:.2f}, {e1}={energy.get(e1, 0):.2f}, {e2}={energy.get(e2, 0):.2f}")
                # This would add energy to transform_to and deduct from e1, e2
                # But it doesn't affect Earth directly
            else:
                print(f"    ❌ Transformation fails (合绊)")
                print(f"    Before: Earth={energy['earth']:.2f}, {e1}={energy.get(e1, 0):.2f}, {e2}={energy.get(e2, 0):.2f}")
                # This would multiply e1 and e2 by 0.4
                # But it doesn't affect Earth directly
                if e1 == 'earth' or e2 == 'earth':
                    print(f"    ⚠️  WARNING: This affects Earth energy!")
                else:
                    print(f"    ✅ This does NOT affect Earth energy")
    
    # Step 2: Check 地支三合/三会
    print(f"\n{'=' * 80}")
    print("Step 2: 地支三合/三会 (Trine/Directional Harmony)")
    print("=" * 80)
    
    three_harmonies = {
        'Water': {'申', '子', '辰'},
        'Wood': {'亥', '卯', '未'},
        'Fire': {'寅', '午', '戌'},
        'Metal': {'巳', '酉', '丑'}
    }
    
    directional_assembly = {
        'Wood': {'寅', '卯', '辰'},
        'Fire': {'巳', '午', '未'},
        'Metal': {'申', '酉', '戌'},
        'Water': {'亥', '子', '丑'}
    }
    
    branch_set = set(branches)
    print(f"Branch Set: {branch_set}")
    
    # Check Three Harmonies
    for elem_name, members in three_harmonies.items():
        if members.issubset(branch_set):
            elem_lower = elem_name.lower()
            print(f"  Found 三合: {elem_name} ({members})")
            print(f"    Would multiply {elem_lower} energy")
            if elem_lower == 'earth':
                print(f"    ⚠️  WARNING: This affects Earth energy!")
            else:
                print(f"    ✅ This does NOT affect Earth energy")
    
    # Check Directional Assembly
    for elem_name, members in directional_assembly.items():
        if members.issubset(branch_set):
            elem_lower = elem_name.lower()
            print(f"  Found 三会: {elem_name} ({members})")
            print(f"    Would multiply {elem_lower} energy")
            if elem_lower == 'earth':
                print(f"    ⚠️  WARNING: This affects Earth energy!")
            else:
                print(f"    ✅ This does NOT affect Earth energy")
    
    # Step 3: Check 地支六合
    print(f"\n{'=' * 80}")
    print("Step 3: 地支六合 (Six Combinations)")
    print("=" * 80)
    
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
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
                print(f"  Found 六合: {b1} <-> {b2}")
                print(f"    Transform To: {transform_to}")
                if transform_to == 'earth':
                    print(f"    ⚠️  WARNING: This affects Earth energy (multiplication by 1.2)")
                else:
                    print(f"    ✅ This does NOT affect Earth energy")
    
    # Step 4: Check 地支六冲
    print(f"\n{'=' * 80}")
    print("Step 4: 地支六冲 (Six Clashes)")
    print("=" * 80)
    
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
            if BRANCH_CLASHES.get(b1) == b2:
                e1 = BRANCH_ELEMENTS.get(b1, 'earth')
                e2 = BRANCH_ELEMENTS.get(b2, 'earth')
                print(f"  Found 六冲: {b1} <-> {b2} ({e1} <-> {e2})")
                if e1 == 'earth' or e2 == 'earth':
                    print(f"    ⚠️  WARNING: This affects Earth energy (subtraction -3.0)")
                else:
                    print(f"    ✅ This does NOT affect Earth energy")
    
    # Step 5: Check 相刑
    print(f"\n{'=' * 80}")
    print("Step 5: 相刑 (Punishment)")
    print("=" * 80)
    
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
            if b2 in BRANCH_PUNISHMENTS.get(b1, []):
                e1 = BRANCH_ELEMENTS.get(b1, 'earth')
                e2 = BRANCH_ELEMENTS.get(b2, 'earth')
                print(f"  Found 相刑: {b1} <-> {b2} ({e1} <-> {e2})")
                if e1 == 'earth' or e2 == 'earth':
                    print(f"    ⚠️  WARNING: This affects Earth energy (subtraction -3.0)")
                else:
                    print(f"    ✅ This does NOT affect Earth energy")
    
    # Step 6: Check 相害
    print(f"\n{'=' * 80}")
    print("Step 6: 相害 (Harm)")
    print("=" * 80)
    
    for i, b1 in enumerate(branches):
        if not b1:
            continue
        for j, b2 in enumerate(branches):
            if i >= j or not b2:
                continue
            if BRANCH_HARMS.get(b1) == b2:
                e1 = BRANCH_ELEMENTS.get(b1, 'earth')
                e2 = BRANCH_ELEMENTS.get(b2, 'earth')
                print(f"  Found 相害: {b1} <-> {b2} ({e1} <-> {e2})")
                if e1 == 'earth' or e2 == 'earth':
                    print(f"    ⚠️  WARNING: This affects Earth energy (subtraction -2.0)")
                else:
                    print(f"    ✅ This does NOT affect Earth energy")
    
    # Step 7: Check 墓库物理
    print(f"\n{'=' * 80}")
    print("Step 7: 墓库物理 (Vault Physics)")
    print("=" * 80)
    
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
            print(f"    ⚠️  WARNING: This affects Earth energy!")
        else:
            print(f"    ✅ This does NOT affect Earth energy")
    else:
        print(f"  ✅ Day branch {day_branch} is not a vault, no vault physics applied")
    
    print(f"\n{'=' * 80}")
    print("Summary")
    print("=" * 80)
    print(f"Expected Earth penalties (subtraction only):")
    print(f"  - 六冲 (丑-未): -3.0")
    print(f"  - 相刑 (丑-未): -3.0")
    print(f"  - 相害 (丑-午): -2.0")
    print(f"  Total: -8.0")
    print(f"  Expected Earth energy: 29.7 - 8.0 = 21.7")
    print(f"  Actual Earth energy (from diagnostic): 4.64")
    print(f"  Difference: 4.64 - 21.7 = -17.06")
    print(f"\n⚠️  If Earth energy is 4.64, there must be a multiplication bug!")

if __name__ == "__main__":
    debug_c07_interactions()

