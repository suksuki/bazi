"""
V25.0 Task 68: AI Precise Calculation Path Disclosure
=====================================================
Detailed step-by-step verification of C07 career calculation
to identify misalignment between theory and implementation.
"""

import sys
import os
sys.path.append(os.getcwd())

from core.engine_v88 import EngineV88 as QuantumEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.processors.physics import PhysicsProcessor, STEM_ELEMENTS
from core.processors.domains import DomainProcessor
from core.processors.strength_judge import StrengthJudge

def create_profile_mock(case):
    """Create a mock profile for testing"""
    bazi = case['bazi']
    
    class MockProfile:
        def __init__(self, dm, pillars, gender):
            self.day_master = dm
            self.pillars = {
                'year': pillars[0],
                'month': pillars[1],
                'day': pillars[2],
                'hour': pillars[3]
            }
            self.gender = 1 if gender == "男" else 0
            self.birth_date = None
        
        def get_luck_pillar_at(self, year):
            return ['', '']

    return MockProfile(case['day_master'], bazi, case['gender'])

def run_detailed_diagnostic():
    """Run detailed diagnostic for C07 case"""
    
    # Load C07 case
    path = "data/calibration_cases.json"
    if not os.path.exists(path):
        path = "calibration_cases.json"
    
    with open(path, "r", encoding='utf-8') as f:
        cases = json.load(f)
    
    c07 = next((c for c in cases if c['id'] == 'C07'), None)
    if not c07:
        print("Error: C07 not found")
        return
    
    print("=" * 80)
    print("V25.0 Task 68: AI Precise Calculation Path Disclosure - C07 Career")
    print("=" * 80)
    print(f"\nCase: C07")
    print(f"Bazi: {c07['bazi']}")
    print(f"Day Master: {c07['day_master']} (庚 Metal)")
    print(f"Target: CAREER, GT = 80.0")
    print(f"Current Model Score: 43.2, MAE = 36.8")
    print()
    
    # Init engine
    engine = QuantumEngine()
    engine.config = DEFAULT_FULL_ALGO_PARAMS
    
    bazi_list = c07['bazi']
    dm_char = c07['day_master']
    dm_elem = STEM_ELEMENTS.get(dm_char, 'metal')
    
    # Get config
    physics_config = engine.config.get('physics', {})
    interactions_config = engine.config.get('interactions', {})
    flow_config = engine.config.get('flow', {})
    pillar_weights = physics_config.get('pillarWeights', {})
    
    print("=" * 80)
    print("Step A: Raw Energy Calculation (基础能量提取)")
    print("=" * 80)
    
    # Initialize PhysicsProcessor
    physics = PhysicsProcessor()
    physics.PILLAR_WEIGHTS = {
        'year': pillar_weights.get('year', 1.0),
        'month': pillar_weights.get('month', 1.8),
        'day': pillar_weights.get('day', 1.5),
        'hour': pillar_weights.get('hour', 1.2)
    }
    
    # Calculate raw energy step by step
    energy_before = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 'metal': 0.0, 'water': 0.0}
    pillar_names = ['year', 'month', 'day', 'hour']
    
    print(f"\nPillar Weights: {physics.PILLAR_WEIGHTS}")
    print(f"\nStem Contributions:")
    
    for idx, pillar in enumerate(bazi_list):
        if len(pillar) < 2:
            continue
        
        p_name = pillar_names[idx]
        stem_char = pillar[0]
        branch_char = pillar[1]
        w_pillar = physics.PILLAR_WEIGHTS.get(p_name, 1.0)
        
        if idx != 2:  # Skip day master
            elem = STEM_ELEMENTS.get(stem_char, 'wood')
            score = 10.0 * w_pillar
            energy_before[elem] += score
            print(f"  {p_name:6s} {stem_char} ({elem:6s}): {score:.2f} = 10.0 * {w_pillar:.2f}")
    
    print(f"\nBranch Contributions:")
    all_hidden_chars = set()
    
    for idx, pillar in enumerate(bazi_list):
        if len(pillar) < 2:
            continue
        
        p_name = pillar_names[idx]
        branch_char = pillar[1]
        w_pillar = physics.PILLAR_WEIGHTS.get(p_name, 1.0)
        
        hiddens = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
        for h_char, h_weight in hiddens:
            all_hidden_chars.add(h_char)
            elem = STEM_ELEMENTS.get(h_char, 'wood')
            score = w_pillar * h_weight
            energy_before[elem] += score
            print(f"  {p_name:6s} {branch_char} -> {h_char} ({elem:6s}): {score:.2f} = {w_pillar:.2f} * {h_weight}")
    
    print(f"\nRaw Energy (Before Rooting): {energy_before}")
    
    # Apply rooting bonus
    print(f"\nRooting Bonus:")
    for idx, pillar in enumerate(bazi_list):
        if idx == 2:  # Skip day master
            continue
        if len(pillar) < 1:
            continue
        
        stem_char = pillar[0]
        if stem_char in all_hidden_chars:
            p_name = pillar_names[idx]
            w_pillar = physics.PILLAR_WEIGHTS.get(p_name, 1.0)
            elem = STEM_ELEMENTS.get(stem_char, 'wood')
            original_score = 10.0 * w_pillar
            
            # Check if same pillar rooting
            branch_char = pillar[1] if len(pillar) > 1 else ''
            is_same_pillar = False
            if branch_char:
                hiddens = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
                for h_char, _ in hiddens:
                    if h_char == stem_char:
                        is_same_pillar = True
                        break
            
            if is_same_pillar:
                bonus = original_score * (2.5 - 1.0)  # SAME_PILLAR_BONUS
                print(f"  {stem_char} ({elem}): +{bonus:.2f} (自坐强根, 2.5x)")
            else:
                bonus = original_score * (1.2 - 1.0)  # ROOT_BONUS
                print(f"  {stem_char} ({elem}): +{bonus:.2f} (通根, 1.2x)")
            
            energy_before[elem] += bonus
    
    print(f"\nRaw Energy (After Rooting): {energy_before}")
    
    # Step B: Complex Interactions
    print(f"\n{'=' * 80}")
    print("Step B: Complex Interactions (复杂交互修正)")
    print("=" * 80)
    
    context = {
        'bazi': bazi_list,
        'day_master': dm_char,
        'dm_element': dm_elem,
        'month_branch': bazi_list[1][1] if len(bazi_list) > 1 and len(bazi_list[1]) > 1 else '',
        'interactions_config': interactions_config,
        'flow_config': flow_config,
        'pillar_weights': pillar_weights
    }
    
    energy_after_interactions = physics._apply_complex_interactions(
        energy_before.copy(), bazi_list, dm_elem, context
    )
    
    print(f"\nRaw Energy (After Complex Interactions): {energy_after_interactions}")
    print(f"\nChanges:")
    for elem in energy_before:
        change = energy_after_interactions.get(elem, 0) - energy_before.get(elem, 0)
        if abs(change) > 0.01:
            print(f"  {elem:6s}: {energy_before.get(elem, 0):.2f} -> {energy_after_interactions.get(elem, 0):.2f} (change: {change:+.2f})")
    
    # Check if subtraction penalty is used
    clash_score = interactions_config.get('branchEvents', {}).get('clashScore', -3.0)
    print(f"\n⚠️  Alignment Check 1: Clash Penalty Method")
    print(f"  Config clashScore: {clash_score}")
    print(f"  Expected: Subtraction (energy[elem] = max(0, energy[elem] + clash_score))")
    print(f"  If Earth energy dropped significantly (e.g., 29.7 -> 1.85), multiplication is being used!")
    
    # Step C: Ten God Particles
    print(f"\n{'=' * 80}")
    print("Step C: Ten God Particle Calculation (十神波函数)")
    print("=" * 80)
    
    # Calculate strength
    strength_judge = StrengthJudge()
    strength_context = {
        'raw_energy': energy_after_interactions,
        'dm_element': dm_elem,
        'base_score': sum(energy_after_interactions.values()),
        'in_command': False,
        'is_resource_month': False,
        'in_command_bonus': 0,
        'resource_month_bonus': 0,
        'resource_efficiency': 1.0
    }
    strength_result = strength_judge.process(strength_context)
    
    print(f"Strength Verdict: {strength_result.get('verdict', 'Unknown')}")
    print(f"Body Score: {strength_result.get('raw_score', 0):.2f}")
    
    # Calculate ten god particles
    domain_processor = DomainProcessor()
    elements = ['wood', 'fire', 'earth', 'metal', 'water']
    dm_idx = elements.index(dm_elem) if dm_elem in elements else 0
    
    self_idx = dm_idx
    output_idx = (dm_idx + 1) % 5
    wealth_idx = (dm_idx + 2) % 5
    officer_idx = (dm_idx + 3) % 5
    resource_idx = (dm_idx + 4) % 5
    
    print(f"\nDay Master: {dm_elem} (index {dm_idx})")
    print(f"Ten God Mapping:")
    print(f"  Self (比劫):     {elements[self_idx]}")
    print(f"  Output (食伤):   {elements[output_idx]}")
    print(f"  Wealth (财):     {elements[wealth_idx]}")
    print(f"  Officer (官杀):  {elements[officer_idx]}")
    print(f"  Resource (印):   {elements[resource_idx]}")
    
    # Get base energies
    self_energy = energy_after_interactions.get(elements[self_idx], 0)
    output_energy = energy_after_interactions.get(elements[output_idx], 0)
    wealth_energy = energy_after_interactions.get(elements[wealth_idx], 0)
    officer_energy = energy_after_interactions.get(elements[officer_idx], 0)
    resource_energy = energy_after_interactions.get(elements[resource_idx], 0)
    
    print(f"\nBase Element Energies:")
    print(f"  {elements[self_idx]:6s} (Self):     {self_energy:.2f}")
    print(f"  {elements[output_idx]:6s} (Output):   {output_energy:.2f}")
    print(f"  {elements[wealth_idx]:6s} (Wealth):   {wealth_energy:.2f}")
    print(f"  {elements[officer_idx]:6s} (Officer):  {officer_energy:.2f}")
    print(f"  {elements[resource_idx]:6s} (Resource): {resource_energy:.2f}")
    
    # Apply particle weights
    particle_weights = engine.config.get('particleWeights', {})
    self_weight = max(particle_weights.get('BiJian', 1.0), particle_weights.get('JieCai', 1.0))
    output_weight = max(particle_weights.get('ShiShen', 1.0), particle_weights.get('ShangGuan', 1.0))
    wealth_weight = max(particle_weights.get('ZhengCai', 1.0), particle_weights.get('PianCai', 1.0))
    officer_weight = max(particle_weights.get('ZhengGuan', 1.0), particle_weights.get('QiSha', 1.0))
    resource_weight = max(particle_weights.get('ZhengYin', 1.0), particle_weights.get('PianYin', 1.0))
    
    print(f"\nParticle Weights:")
    print(f"  Self:     {self_weight:.2f}")
    print(f"  Output:   {output_weight:.2f}")
    print(f"  Wealth:   {wealth_weight:.2f}")
    print(f"  Officer:  {officer_weight:.2f}")
    print(f"  Resource: {resource_weight:.2f}")
    
    # Check if controlImpact and resourceImpedance are applied
    control_impact = flow_config.get('controlImpact', 0.7)
    resource_impedance = flow_config.get('resourceImpedance', {}).get('base', 0.20)
    
    print(f"\n⚠️  Alignment Check 2: Energy Flow Parameters")
    print(f"  controlImpact: {control_impact}")
    print(f"  resourceImpedance.base: {resource_impedance}")
    print(f"  ⚠️  WARNING: These parameters may not be applied in first layer!")
    print(f"  They are used in FlowEngine, which may not be in the calculation path.")
    
    gods = {
        'self': self_energy * self_weight,
        'output': output_energy * output_weight,
        'wealth': wealth_energy * wealth_weight,
        'officer': officer_energy * officer_weight,
        'resource': resource_energy * resource_weight
    }
    
    print(f"\nTen God Particle Energies (After Weights):")
    print(f"  Self (比劫):     {gods['self']:.2f}")
    print(f"  Output (食伤):   {gods['output']:.2f}")
    print(f"  Wealth (财):     {gods['wealth']:.2f}")
    print(f"  Officer (官杀):  {gods['officer']:.2f}")
    print(f"  Resource (印):   {gods['resource']:.2f}")
    
    # Step D: Domain Base Score
    print(f"\n{'=' * 80}")
    print("Step D: Domain Base Score (宏观相基础得分)")
    print("=" * 80)
    
    career_result = domain_processor._calc_career(
        gods, strength_result.get('raw_score', 0), strength_result.get('verdict', 'Weak')
    )
    
    s0_base = career_result.get('s0_base', career_result.get('base_score', 0))
    print(f"\nCareer Base Score (S0_Base): {s0_base:.2f}")
    
    print(f"\n⚠️  Alignment Check 3: Base Score Calculation")
    if s0_base <= 0:
        print(f"  ❌ ERROR: S0_Base is {s0_base:.2f} (should be > 0)")
    else:
        print(f"  ✅ S0_Base > 0: {s0_base:.2f}")
    
    # Show calculation details
    officer = gods['officer']
    output = gods['output']
    resource = gods['resource']
    
    score_officer = officer + (resource * 0.3)
    score_output = output * 1.2
    
    print(f"\nCareer Path Calculation:")
    print(f"  Path A (Bureaucracy): officer + resource*0.3 = {officer:.2f} + {resource:.2f}*0.3 = {score_officer:.2f}")
    print(f"  Path B (Talent): output * 1.2 = {output:.2f} * 1.2 = {score_output:.2f}")
    
    if score_officer > score_output:
        chosen_path = score_officer
        path_name = "Bureaucracy (官印相生)"
    else:
        chosen_path = score_output
        path_name = "Talent (食伤泄秀)"
    
    print(f"  Chosen Path: {path_name} = {chosen_path:.2f}")
    
    # Step E: Final Score
    print(f"\n{'=' * 80}")
    print("Step E: Final Score (最终得分)")
    print("=" * 80)
    
    # Get final score from engine
    profile = create_profile_mock(c07)
    case_data = {
        'year': bazi_list[0],
        'month': bazi_list[1],
        'day': bazi_list[2],
        'hour': bazi_list[3],
        'day_master': dm_char,
        'gender': profile.gender,
        'case_id': 'C07'
    }
    
    result = engine.calculate_energy(case_data)
    domain_details = result.get('domain_details', {})
    career_final = domain_details.get('career', {}).get('score', 0)
    
    print(f"\nFinal Career Score: {career_final:.2f}")
    print(f"GT Score: 80.0")
    print(f"MAE: {abs(career_final - 80.0):.2f}")
    
    # Show breakdown if available
    if 'score_breakdown' in domain_details.get('career', {}):
        breakdown = domain_details['career']['score_breakdown']
        print(f"\nScore Breakdown:")
        print(f"  S0_Base:                    {breakdown.get('S0_Base', 0):.2f}")
        print(f"  S1_After_Amplifier:         {breakdown.get('S1_After_Amplifier', 0):.2f}")
        print(f"  S2_After_BiasFactor:         {breakdown.get('S2_After_BiasFactor', 0):.2f}")
        print(f"  S3_After_Corrector:          {breakdown.get('S3_After_Corrector', 0):.2f}")
        print(f"  S4_Final_Score:              {breakdown.get('S4_Final_Score', 0):.2f}")
    
    print(f"\n{'=' * 80}")
    print("Summary for AI Verification")
    print("=" * 80)
    print(f"1. Raw Energy (After Rooting): {energy_before}")
    print(f"2. Raw Energy (After Interactions): {energy_after_interactions}")
    print(f"3. Ten God Particles: {gods}")
    print(f"4. Career Base Score (S0_Base): {s0_base:.2f}")
    print(f"5. Final Career Score: {career_final:.2f}")
    print(f"6. GT Score: 80.0")
    print(f"7. MAE: {abs(career_final - 80.0):.2f}")

if __name__ == "__main__":
    import json
    run_detailed_diagnostic()

