
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.trinity.sandbox.v17_transition.phase_transition import PhaseTransitionManager

def run_sandbox_tests():
    print("=== V17 Quantum Transition Sandbox ===")
    
    manager = PhaseTransitionManager()
    
    # Load Matrix-C
    matrix_path = Path("tests/v17_matrix_c.json")
    if not matrix_path.exists():
        print("Matrix-C not found!")
        return

    with open(matrix_path, 'r') as f:
        cases = json.load(f)
        
    for case in cases:
        print(f"\n>>> Testing: {case['desc']}")
        cid = case['id']
        
        # Mock inputs based on Case ID Description
        # In a real integration, this would come from the parser.
        
        if cid == "C_01_妒合":
            # Jealousy: 2 Stems vs 1 Branch? 
            # Actually C_01 is Stem Combine rivalry.
            # Let's mock a scenario: 2 Xin (Metal) vs 1 Bing (Fire)
            # This is a bit outside the branch logic, but let's test the "Conflict" param.
            # Conflict Ratio high.
            eta = manager.calculate_coherence(
                combination_type='LiuHe', # Stem combine treated like LiuHe for mock
                branches=[{'pos': 0}, {'pos': 1}], 
                catalyst_stem=None,
                external_conflict=0.8 # High rivalry
            )
            print(f"    Eta (Coherence): {eta:.2f}")
            
        elif cid == "C_02_冗余干涉":
            # Si Si You Chou + Bing
            # SanHe Metal. 
            # Branches: 1, 2, 3, 4 (Compact?) No, Si(0), Si(1), You(2), Chou(3).
            # Structure: Si+You+Chou. Redundant Si.
            branches = [{'name': '巳', 'pos': 1}, {'name': '酉', 'pos': 2}, {'name': '丑', 'pos': 3}]
            # Redundant Si acts as Fire conflict? Or just structural redundancy?
            # Prompt says "Fire Conflict".
            eta = manager.calculate_coherence(
                combination_type='SanHe',
                branches=branches,
                catalyst_stem='Fire', # Bing induces
                external_conflict=0.5 # Redundant Si Fire
            )
            print(f"    Eta (Coherence): {eta:.2f}")
            e_trans, e_resid = manager.calculate_residual_essence(eta, 100.0)
            print(f"    Energy: Transformed={e_trans:.1f}, Residual={e_resid:.1f}")
            
        elif cid == "C_03_隔位衰减":
            # Shen(0) ... Zi(2) ... Chen(3)
            # Gap between Shen and Zi is 1. (0 to 2)
            branches = [{'name': '申', 'pos': 0}, {'name': '子', 'pos': 2}, {'name': '辰', 'pos': 3}]
            eta = manager.calculate_coherence(
                combination_type='SanHe',
                branches=branches,
                catalyst_stem=None,
                external_conflict=0.0
            )
            print(f"    Eta (Coherence): {eta:.2f}")

        # Assertions (Soft)
        expected = case.get('ground_truth', {})
        if expected:
            tgt_eta = expected.get('coherence_target')
            if tgt_eta is not None:
                # print(f"    Target Eta: {tgt_eta}")
                pass

if __name__ == "__main__":
    run_sandbox_tests()
