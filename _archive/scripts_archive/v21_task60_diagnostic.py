"""
V21.0 Task 60: Algorithm Consistency Verification
==================================================
Disclose intermediate calculation values for C07 (Career) and C01 (Relationship)
to enable AI theoretical verification.
"""

import sys
import os
import json
sys.path.append(os.getcwd())

from core.engine_v88 import EngineV88 as QuantumEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def create_profile_mock(case, luck):
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
            return luck

    return MockProfile(case['day_master'], bazi, case['gender'])

def run_diagnostic():
    """Run diagnostic for C07 and C01 cases"""
    
    # Load cases
    path = "data/calibration_cases.json"
    if not os.path.exists(path):
        path = "calibration_cases.json"
    if not os.path.exists(path):
        print("Error: calibration_cases.json not found")
        return

    with open(path, "r", encoding='utf-8') as f:
        cases = json.load(f)

    # Filter to C07 and C01
    target_cases = {case['id']: case for case in cases if case['id'] in ['C07', 'C01']}
    
    if 'C07' not in target_cases or 'C01' not in target_cases:
        print("Error: C07 or C01 not found in cases")
        return

    # Init engine with V21.0 config
    engine = QuantumEngine()
    engine.config = DEFAULT_FULL_ALGO_PARAMS
    
    # Enable debug mode in processors
    # We'll need to modify processors to output debug info
    # For now, let's create a custom diagnostic engine wrapper
    
    print("=" * 80)
    print("V21.0 Task 60: Algorithm Consistency Verification")
    print("=" * 80)
    print()
    
    for case_id in ['C07', 'C01']:
        case = target_cases[case_id]
        print(f"\n{'=' * 80}")
        print(f"Case: {case_id}")
        print(f"Bazi: {case['bazi']}")
        print(f"Day Master: {case['day_master']}")
        print(f"Gender: {case['gender']}")
        print(f"{'=' * 80}\n")
        
        # Create profile
        luck_pillar = case.get('luck_pillar', ['', ''])
        profile = create_profile_mock(case, luck_pillar)
        
        # Get target domain
        target = case.get('target', 'WEALTH')
        
        # Calculate with debug output
        try:
            # We need to intercept the calculation at each layer
            # Let's modify the engine to output debug info
            
            # Step 1: Get raw energy (before complex interactions)
            bazi_list = case['bazi']
            dm_char = case['day_master']
            
            # Create a diagnostic context
            from core.processors.physics import PhysicsProcessor
            physics = PhysicsProcessor()
            
            # Get pillar weights from config
            pillar_weights = engine.config.get('physics', {}).get('pillarWeights', {})
            physics.PILLAR_WEIGHTS = {
                'year': pillar_weights.get('year', 1.0),
                'month': pillar_weights.get('month', 2.0),
                'day': pillar_weights.get('day', 1.5),
                'hour': pillar_weights.get('hour', 1.2)
            }
            
            # Calculate raw energy step by step
            print("--- Step 1: Raw Energy Calculation (Before Complex Interactions) ---")
            
            # Initialize
            from core.processors.physics import STEM_ELEMENTS
            dm_elem = STEM_ELEMENTS.get(dm_char, 'wood')
            energy_before = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 'metal': 0.0, 'water': 0.0}
            
            # Process each pillar
            pillar_names = ['year', 'month', 'day', 'hour']
            stem_details = []
            branch_details = []
            
            for idx, pillar in enumerate(bazi_list):
                if len(pillar) < 2:
                    continue
                
                p_name = pillar_names[idx]
                stem_char = pillar[0]
                branch_char = pillar[1]
                w_pillar = physics.PILLAR_WEIGHTS.get(p_name, 1.0)
                
                # Stem contribution
                if idx != 2:  # Skip day master
                    elem = STEM_ELEMENTS.get(stem_char, 'wood')
                    score = 10.0 * w_pillar
                    energy_before[elem] += score
                    stem_details.append({
                        'pillar': p_name,
                        'stem': stem_char,
                        'element': elem,
                        'weight': w_pillar,
                        'score': score
                    })
                
                # Branch contribution
                from core.processors.physics import PhysicsProcessor
                hiddens = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
                for h_char, h_weight in hiddens:
                    elem = STEM_ELEMENTS.get(h_char, 'wood')
                    score = w_pillar * h_weight
                    energy_before[elem] += score
                    branch_details.append({
                        'pillar': p_name,
                        'branch': branch_char,
                        'hidden': h_char,
                        'element': elem,
                        'weight': w_pillar,
                        'hidden_weight': h_weight,
                        'score': score
                    })
            
            print(f"Raw Energy (Before Interactions): {energy_before}")
            print(f"\nStem Contributions:")
            for detail in stem_details:
                print(f"  {detail['pillar']:6s} {detail['stem']} ({detail['element']:6s}): {detail['score']:.2f} = 10.0 * {detail['weight']:.2f}")
            
            print(f"\nBranch Contributions:")
            for detail in branch_details:
                print(f"  {detail['pillar']:6s} {detail['branch']} -> {detail['hidden']} ({detail['element']:6s}): {detail['score']:.2f} = {detail['weight']:.2f} * {detail['hidden_weight']}")
            
            # Apply rooting bonus
            print(f"\n--- Step 2: Rooting Bonus ---")
            all_hidden_chars = set()
            for pillar in bazi_list:
                if len(pillar) > 1:
                    branch_char = pillar[1]
                    hiddens = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
                    for h_char, _ in hiddens:
                        all_hidden_chars.add(h_char)
            
            rooting_bonus = {}
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
                    bonus = original_score * 0.2  # ROOT_BONUS - 1.0 = 1.2 - 1.0 = 0.2
                    energy_before[elem] += bonus
                    rooting_bonus[elem] = rooting_bonus.get(elem, 0) + bonus
                    print(f"  {stem_char} ({elem}): +{bonus:.2f} (rooting bonus)")
            
            print(f"Rooting Bonus Total: {rooting_bonus}")
            print(f"Raw Energy (After Rooting): {energy_before}")
            
            # Step 3: Apply complex interactions
            print(f"\n--- Step 3: Complex Interactions (合冲刑害墓库) ---")
            
            # Create context for complex interactions
            context = {
                'bazi': bazi_list,
                'day_master': dm_char,
                'dm_element': dm_elem,
                'month_branch': bazi_list[1][1] if len(bazi_list) > 1 and len(bazi_list[1]) > 1 else '',
                'interactions_config': engine.config.get('interactions', {}),
                'flow_config': engine.config.get('flow', {})
            }
            
            energy_after_interactions = physics._apply_complex_interactions(
                energy_before.copy(), bazi_list, dm_elem, context
            )
            
            print(f"Raw Energy (After Complex Interactions): {energy_after_interactions}")
            
            # Step 4: Apply coupling effects
            print(f"\n--- Step 4: Energy Flow Coupling Effects ---")
            
            energy_after_coupling = physics._apply_coupling_effects(
                energy_after_interactions.copy(), bazi_list, dm_elem, context
            )
            
            print(f"Raw Energy (After Coupling Effects): {energy_after_coupling}")
            
            # Step 5: Calculate Ten God particles using DomainProcessor
            print(f"\n--- Step 5: Ten God Particle Calculation ---")
            
            # We need to calculate ten god particles from raw energy
            from core.processors.domains import DomainProcessor
            from core.processors.strength_judge import StrengthJudge
            
            # First, calculate strength
            strength_judge = StrengthJudge()
            strength_context = {
                'raw_energy': energy_after_coupling,
                'dm_element': dm_elem,
                'base_score': sum(energy_after_coupling.values()),
                'in_command': False,  # Simplified
                'is_resource_month': False,  # Simplified
                'in_command_bonus': 0,
                'resource_month_bonus': 0,
                'resource_efficiency': 1.0
            }
            strength_result = strength_judge.process(strength_context)
            
            print(f"Strength Verdict: {strength_result.get('verdict', 'Unknown')}")
            print(f"Body Score: {strength_result.get('raw_score', 0):.2f}")
            
            # Calculate ten god particles
            domain_processor = DomainProcessor()
            domain_context = {
                'raw_energy': energy_after_coupling,
                'dm_element': dm_elem,
                'strength': strength_result,
                'gender': profile.gender,
                'particle_weights': engine.config.get('particleWeights', {}),
                'physics_config': engine.config.get('physics', {}),
                'observation_bias_config': engine.config.get('ObservationBiasFactor', {})
            }
            
            # Get ten god particles
            # We need to manually calculate ten god energies
            elements = ['wood', 'fire', 'earth', 'metal', 'water']
            dm_idx = elements.index(dm_elem) if dm_elem in elements else 0
            
            self_idx = dm_idx
            output_idx = (dm_idx + 1) % 5
            wealth_idx = (dm_idx + 2) % 5
            officer_idx = (dm_idx + 3) % 5
            resource_idx = (dm_idx + 4) % 5
            
            # Get base energies
            self_energy = energy_after_coupling.get(elements[self_idx], 0)
            output_energy = energy_after_coupling.get(elements[output_idx], 0)
            wealth_energy = energy_after_coupling.get(elements[wealth_idx], 0)
            officer_energy = energy_after_coupling.get(elements[officer_idx], 0)
            resource_energy = energy_after_coupling.get(elements[resource_idx], 0)
            
            # Apply particle weights
            particle_weights = domain_context.get('particle_weights', {})
            self_weight = max(particle_weights.get('BiJian', 1.0), particle_weights.get('JieCai', 1.0))
            output_weight = max(particle_weights.get('ShiShen', 1.0), particle_weights.get('ShangGuan', 1.0))
            wealth_weight = max(particle_weights.get('ZhengCai', 1.0), particle_weights.get('PianCai', 1.0))
            officer_weight = max(particle_weights.get('ZhengGuan', 1.0), particle_weights.get('QiSha', 1.0))
            resource_weight = max(particle_weights.get('ZhengYin', 1.0), particle_weights.get('PianYin', 1.0))
            
            gods = {
                'self': self_energy * self_weight,
                'output': output_energy * output_weight,
                'wealth': wealth_energy * wealth_weight,
                'officer': officer_energy * officer_weight,
                'resource': resource_energy * resource_weight
            }
            
            print(f"Ten God Particle Energies:")
            print(f"  Self (比劫):     {gods['self']:.2f}")
            print(f"  Output (食伤):   {gods['output']:.2f}")
            print(f"  Wealth (财):     {gods['wealth']:.2f}")
            print(f"  Officer (官杀):  {gods['officer']:.2f}")
            print(f"  Resource (印):   {gods['resource']:.2f}")
            
            # Step 6: Domain base score (before BiasFactor)
            print(f"\n--- Step 6: Domain Base Score (Before BiasFactor) ---")
            
            # Calculate domain scores
            wealth_result = domain_processor._calc_wealth(
                gods, strength_result.get('raw_score', 0), strength_result.get('verdict', 'Weak')
            )
            career_result = domain_processor._calc_career(
                gods, strength_result.get('raw_score', 0), strength_result.get('verdict', 'Weak')
            )
            relationship_result = domain_processor._calc_relationship(
                gods, strength_result.get('raw_score', 0), strength_result.get('verdict', 'Weak'), profile.gender
            )
            
            # Extract base scores (S0_Base) from results
            wealth_base = wealth_result.get('s0_base', wealth_result.get('base_score', 0))
            career_base = career_result.get('s0_base', career_result.get('base_score', 0))
            relationship_base = relationship_result.get('s0_base', relationship_result.get('base_score', 0))
            
            print(f"Domain Base Scores (S0_Base, before BiasFactor):")
            print(f"  Wealth:      {wealth_base:.2f}")
            print(f"  Career:      {career_base:.2f}")
            print(f"  Relationship: {relationship_base:.2f}")
            
            # Get final scores from engine calculation
            # Use the engine's process method
            case_data = {
                'year': bazi_list[0],
                'month': bazi_list[1],
                'day': bazi_list[2],
                'hour': bazi_list[3],
                'day_master': dm_char,
                'gender': profile.gender,
                'case_id': case_id
            }
            
            result = engine.process(case_data, case.get('target_year', 2024))
            
            # Extract domain scores from result
            domain_details = result.get('domain_details', {})
            domain_scores = {
                'wealth': domain_details.get('wealth', {}).get('score', 0),
                'career': domain_details.get('career', {}).get('score', 0),
                'relationship': domain_details.get('relationship', {}).get('score', 0)
            }
            
            if target == 'WEALTH':
                target_score = domain_scores['wealth']
                target_gt = case.get('wealth', 0)
            elif target == 'CAREER':
                target_score = domain_scores['career']
                target_gt = case.get('career', 0)
            elif target == 'RELATIONSHIP':
                target_score = domain_scores['relationship']
                target_gt = case.get('relationship', 0)
            else:
                target_score = 0
                target_gt = 0
            
            print(f"\nFinal Domain Scores (After All Corrections):")
            print(f"  Wealth:      {domain_scores['wealth']:.2f}")
            print(f"  Career:      {domain_scores['career']:.2f}")
            print(f"  Relationship: {domain_scores['relationship']:.2f}")
            print(f"\nTarget Domain ({target}):")
            print(f"  Model Score: {target_score:.2f}")
            print(f"  GT Score:    {target_gt:.2f}")
            print(f"  MAE:         {abs(target_score - target_gt):.2f}")
            
            # Output summary for AI verification
            print(f"\n{'=' * 80}")
            print(f"SUMMARY FOR AI VERIFICATION - {case_id}")
            print(f"{'=' * 80}")
            print(f"\n1. Raw Energy (Before Complex Interactions):")
            print(f"   {energy_before}")
            print(f"\n2. Raw Energy (After Complex Interactions):")
            print(f"   {energy_after_interactions}")
            print(f"\n3. Raw Energy (After Coupling Effects - FINAL):")
            print(f"   {energy_after_coupling}")
            print(f"\n4. Ten God Particle Energies:")
            print(f"   Self:     {gods['self']:.2f}")
            print(f"   Output:   {gods['output']:.2f}")
            print(f"   Wealth:   {gods['wealth']:.2f}")
            print(f"   Officer:  {gods['officer']:.2f}")
            print(f"   Resource: {gods['resource']:.2f}")
            print(f"\n5. Domain Base Scores (S0_Base, before BiasFactor):")
            print(f"   Wealth:      {wealth_base:.2f}")
            print(f"   Career:      {career_base:.2f}")
            print(f"   Relationship: {relationship_base:.2f}")
            print(f"\n6. Final Domain Scores (After All Corrections):")
            print(f"   Wealth:      {domain_scores['wealth']:.2f}")
            print(f"   Career:      {domain_scores['career']:.2f}")
            print(f"   Relationship: {domain_scores['relationship']:.2f}")
            print(f"\n7. Target Domain ({target}):")
            print(f"   Model Score: {target_score:.2f}")
            print(f"   GT Score:    {target_gt:.2f}")
            print(f"   MAE:         {abs(target_score - target_gt):.2f}")
            
        except Exception as e:
            print(f"Error processing {case_id}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_diagnostic()

