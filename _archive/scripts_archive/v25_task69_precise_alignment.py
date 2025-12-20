"""
V25.0 Task 69: Precise Alignment with AI Calculation Path
=========================================================
Based on AI-disclosed precise calculation path for C07 case.
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
from core.processors.domains import DomainProcessor
from core.interactions import BRANCH_CLASHES, BRANCH_HARMS, BRANCH_PUNISHMENTS

def precise_alignment_c07():
    """Precise alignment check for C07 case following AI calculation path"""
    
    print("=" * 80)
    print("V25.0 Task 69: C07 Precise Alignment Check")
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
    
    # Verify V24.0 final parameters
    print("\n" + "=" * 80)
    print("Step 0: V24.0 Final Parameters Verification")
    print("=" * 80)
    
    pillar_weights = config.get('physics', {}).get('pillarWeights', {})
    pg_month = pillar_weights.get('month', 1.0)
    same_pill = 2.5  # This is hardcoded in PhysicsProcessor
    
    interactions_config = config.get('interactions', {})
    branch_events = interactions_config.get('branchEvents', {})
    clash_score = branch_events.get('clashScore', -3.0)
    punishment_penalty = branch_events.get('punishmentPenalty', -3.0)
    harm_penalty = branch_events.get('harmPenalty', -2.0)
    
    flow_config = config.get('flow', {})
    resource_impedance = flow_config.get('resourceImpedance', {})
    imp_base = resource_impedance.get('base', 0.20)
    ctl_imp = flow_config.get('controlImpact', 0.70)
    
    print(f"\nV24.0 最终参数:")
    print(f"  pg_month (月令权重): {pg_month} (预期: 1.8)")
    print(f"  same_pill (自坐强根): {same_pill} (预期: 2.5)")
    print(f"  clash_score: {clash_score} (Expected: -3.0)")
    print(f"  punishmentPenalty: {punishment_penalty} (Expected: -3.0)")
    print(f"  harmPenalty: {harm_penalty} (Expected: -2.0)")
    print(f"  imp_base: {imp_base} (Expected: 0.20)")
    print(f"  ctl_imp: {ctl_imp} (Expected: 0.70)")
    
    # Verify all parameters
    params_ok = (
        abs(pg_month - 1.8) < 0.01 and
        abs(same_pill - 2.5) < 0.01 and
        abs(clash_score - (-3.0)) < 0.01 and
        abs(punishment_penalty - (-3.0)) < 0.01 and
        abs(harm_penalty - (-2.0)) < 0.01 and
        abs(imp_base - 0.20) < 0.01 and
        abs(ctl_imp - 0.70) < 0.01
    )
    
    if params_ok:
        print("\nPASS: All V24.0 parameters are correct")
    else:
        print("\nFAIL: Some parameters are incorrect!")
        return False
    
    # Step A: Raw Structural Energy
    print("\n" + "=" * 80)
    print("Step A: Raw Structural Energy (E_Struct)")
    print("=" * 80)
    
    physics = PhysicsProcessor()
    context_a = {
        'bazi': bazi_list,
        'day_master': dm_char,
        'dm_element': dm_elem,
        'pillar_weights': pillar_weights,
        'interactions_config': {},  # No interactions for Step A
        'flow_config': {}
    }
    
    # Calculate manually to get Step A without interactions
    energy_a = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 'metal': 0.0, 'water': 0.0}
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
    
    earth_a = energy_a.get('earth', 0)
    fire_a = energy_a.get('fire', 0)
    
    print(f"\nStep A Results:")
    print(f"  E_Earth: {earth_a:.2f} (AI Expected: 48.0)")
    print(f"  E_Fire: {fire_a:.2f} (AI Expected: 30.0)")
    
    # Step B: Complex Interactions
    print("\n" + "=" * 80)
    print("Step B: Complex Interactions (E_Final)")
    print("=" * 80)
    
    print(f"\nAI Expected Calculation:")
    print(f"  E_Earth,Final = 48.0 - (3.0 + 2.0 + 5.0) = 38.0")
    print(f"  E_Fire,Final = 30.0 - 2.0 = 28.0")
    print(f"\n  惩罚项:")
    print(f"    - 丑未冲: -3.0")
    print(f"    - 午丑害: -2.0")
    print(f"    - 墓库: -5.0")
    
    # Apply interactions manually
    energy_b = energy_a.copy()
    
    # Extract branches
    branches = [p[1] if len(p) > 1 else '' for p in bazi_list]
    day_branch = branches[2] if len(branches) > 2 else ''
    
    print(f"\nBranches: {branches}")
    print(f"Day Branch: {day_branch}")
    
    # Check interactions
    interactions_found = []
    
    # 1. 丑未冲 (Chou-Wei Clash)
    if BRANCH_CLASHES.get('丑') == '未' or BRANCH_CLASHES.get('未') == '丑':
        if '丑' in branches and '未' in branches:
            print(f"\n1. 发现 丑未冲: -3.0")
            earth_before = energy_b.get('earth', 0)
            energy_b['earth'] = max(0, energy_b.get('earth', 0) + clash_score)
            earth_after = energy_b.get('earth', 0)
            print(f"   Earth: {earth_before:.2f} + ({clash_score:.2f}) = {earth_after:.2f}")
            interactions_found.append(('丑未冲', clash_score))
    
    # 2. 午丑害 (Wu-Chou Harm)
    if BRANCH_HARMS.get('午') == '丑' or BRANCH_HARMS.get('丑') == '午':
        if '午' in branches and '丑' in branches:
            print(f"\n2. 发现 午丑害: -2.0")
            earth_before = energy_b.get('earth', 0)
            fire_before = energy_b.get('fire', 0)
            energy_b['earth'] = max(0, energy_b.get('earth', 0) + harm_penalty)
            energy_b['fire'] = max(0, energy_b.get('fire', 0) + harm_penalty)
            earth_after = energy_b.get('earth', 0)
            fire_after = energy_b.get('fire', 0)
            print(f"   Earth: {earth_before:.2f} + ({harm_penalty:.2f}) = {earth_after:.2f}")
            print(f"   Fire: {fire_before:.2f} + ({harm_penalty:.2f}) = {fire_after:.2f}")
            interactions_found.append(('午丑害', harm_penalty))
    
    # 3. 墓库物理 (Vault Physics)
    vault_mapping = {
        '辰': 'water',
        '戌': 'fire',
        '丑': 'metal',
        '未': 'wood'
    }
    
    if day_branch in vault_mapping:
        vault_element = vault_mapping[day_branch]
        vault_elem_energy = energy_b.get(vault_element, 0)
        threshold = 15.0
        sealed_penalty = -5.0
        
        if vault_elem_energy < threshold:
            print(f"\n3. 发现 墓库物理: 日支 {day_branch} 是 {vault_element} 的墓库")
            print(f"   {vault_element} energy ({vault_elem_energy:.2f}) < threshold ({threshold:.2f})")
            print(f"   Applying sealed penalty: {sealed_penalty:.2f}")
            if vault_element == 'earth':
                earth_before = energy_b.get('earth', 0)
                energy_b['earth'] = max(0, energy_b.get('earth', 0) + sealed_penalty)
                earth_after = energy_b.get('earth', 0)
                print(f"   Earth: {earth_before:.2f} + ({sealed_penalty:.2f}) = {earth_after:.2f}")
                interactions_found.append(('墓库', sealed_penalty))
    else:
        print(f"\n3. 墓库物理: 日支 {day_branch} 不是墓库")
    
    earth_final = energy_b.get('earth', 0)
    fire_final = energy_b.get('fire', 0)
    
    print(f"\nStep B Results:")
    print(f"  E_Earth,Final: {earth_final:.2f} (AI Expected: 38.0)")
    print(f"  E_Fire,Final: {fire_final:.2f} (AI Expected: 28.0)")
    
    # Step C: Ten Gods Particle Wave Function
    print("\n" + "=" * 80)
    print("Step C: Ten Gods Particle Wave Function (E_Particle)")
    print("=" * 80)
    
    print(f"\nAI Expected Calculation:")
    print(f"  E_Resource = E_Earth,Final * (1 - imp_base)")
    print(f"             = 38.0 * (1 - 0.20) = 30.4")
    print(f"  E_Officer = E_Fire,Final * (1 + ctl_imp)")
    print(f"            = 28.0 * (1 + 0.70) = 47.6")
    
    e_resource = earth_final * (1 - imp_base)
    e_officer = fire_final * (1 + ctl_imp)
    
    print(f"\nStep C Results:")
    print(f"  E_Resource: {e_resource:.2f} (AI Expected: 30.4)")
    print(f"  E_Officer: {e_officer:.2f} (AI Expected: 47.6)")
    
    # Step D: Career Base Score
    print("\n" + "=" * 80)
    print("Step D: Career Base Score (S_Base)")
    print("=" * 80)
    
    print(f"\nAI Expected Calculation:")
    print(f"  S_Base = E_Resource * 0.5 + E_Officer * 0.5")
    print(f"        = 30.4 * 0.5 + 47.6 * 0.5")
    print(f"        = 15.2 + 23.8 = 39.0")
    
    # Use DomainProcessor to calculate actual score
    domain = DomainProcessor()
    context_d = {
        'raw_energy': energy_b,
        'dm_element': dm_elem,
        'strength': {'verdict': 'Strong', 'raw_score': 50.0},
        'gender': 1,
        'particle_weights': config.get('particleWeights', {}),
        'physics_config': config.get('physics', {}),
        'observation_bias_config': config.get('ObservationBiasFactor', {}),
        'flow_config': flow_config
    }
    
    domain._context = context_d
    gods = domain._calculate_ten_gods(energy_b, dm_elem, config.get('particleWeights', {}))
    
    # Calculate career score manually
    resource_god = gods.get('resource', 0)
    officer_god = gods.get('officer', 0)
    
    # Note: DomainProcessor applies particle weights, so we need to account for that
    # For manual calculation, we use the raw particle energies
    s_base_manual = e_resource * 0.5 + e_officer * 0.5
    
    print(f"\nStep D Results (Manual):")
    print(f"  S_Base: {s_base_manual:.2f} (AI Expected: 39.0)")
    
    # Step E: Final Score
    print("\n" + "=" * 80)
    print("Step E: Final Score (S_Final)")
    print("=" * 80)
    
    print(f"\nAI Expected Calculation:")
    print(f"  S_Final = S_Base * C_Corrector")
    print(f"         = 39.0 * 1.85 ≈ 72.15")
    print(f"  AI Expected Range: 70 ~ 75")
    
    # Summary
    print("\n" + "=" * 80)
    print("Alignment Summary")
    print("=" * 80)
    
    print(f"\nStep A:")
    print(f"  E_Earth: {earth_a:.2f} vs AI Expected: 48.0 (Diff: {earth_a - 48.0:.2f})")
    print(f"  E_Fire: {fire_a:.2f} vs AI Expected: 30.0 (Diff: {fire_a - 30.0:.2f})")
    
    print(f"\nStep B:")
    print(f"  E_Earth,Final: {earth_final:.2f} vs AI Expected: 38.0 (Diff: {earth_final - 38.0:.2f})")
    print(f"  E_Fire,Final: {fire_final:.2f} vs AI Expected: 28.0 (Diff: {fire_final - 28.0:.2f})")
    
    print(f"\nStep C:")
    print(f"  E_Resource: {e_resource:.2f} vs AI Expected: 30.4 (Diff: {e_resource - 30.4:.2f})")
    print(f"  E_Officer: {e_officer:.2f} vs AI Expected: 47.6 (Diff: {e_officer - 47.6:.2f})")
    
    print(f"\nStep D:")
    print(f"  S_Base: {s_base_manual:.2f} vs AI Expected: 39.0 (Diff: {s_base_manual - 39.0:.2f})")
    
    # Critical check: Step B Earth energy
    if abs(earth_final - 38.0) < 1.0:
        print(f"\nPASS: Step B Earth energy is close to AI expected value (38.0)")
        return True
    else:
        print(f"\nFAIL: Step B Earth energy ({earth_final:.2f}) is far from AI expected (38.0)")
        print(f"  This indicates a hidden multiplication decay bug or incorrect penalty stacking logic!")
        return False

if __name__ == "__main__":
    success = precise_alignment_c07()
    sys.exit(0 if success else 1)
