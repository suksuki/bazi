
import sys
import os
import json
from dataclasses import dataclass
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.trinity.core.structural_dynamics import StructuralDynamics, CollisionResult

def run_extreme_stress_test():
    print("\n=== PHASE 19: EXTREME FUSION STRESS TEST (10 CASES) ===")
    
    # Load Cases
    result_log = []
    
    data_path = os.path.join(os.path.dirname(__file__), "data/phase19_extreme_cases.json")
    with open(data_path, 'r') as f:
        cases = json.load(f)
        
    for case in cases:
        cid = case['id']
        cname = case['test_focus']
        params = case['physics_params']
        ptype = params.get('type')
        
        print(f"\n🔬 Processing {cid}: {cname}")
        
        simulation_result = "N/A"
        narrative = "Analysis Pending"
        
        # --- Dispatch Logic ---
        
        if ptype == "multi_branch":
            # Case 003 (N=4) & 008 (Mirror)
            total_e = params.get('total_energy', 20.0)
            branches = params.get('branches', [])
            
            # If branches is list of ints (gaps)
            if branches and isinstance(branches[0], int):
                res = StructuralDynamics.simulate_multi_branch_interference(total_e, branches)
            elif branches and isinstance(branches[0], dict):
                 # Convert dicts to gaps for simple simulation or use new asymmetric?
                 # simulate_multi_branch takes list of gap ints.
                 # simulate_asymmetric takes list of dicts.
                 # Let's try asymmetric if dicts
                 res = StructuralDynamics.simulate_asymmetric_capture(total_e, branches)
            
            if hasattr(res, 'total_effective_energy'):
                eff = res.total_effective_energy
                ratio = eff / total_e
                if ratio < 0.2:
                    narrative = "⚠️ SYSTEM SINGULARITY (Internal Friction > 80%). Total Collapse."
                else:
                    narrative = f"📉 Damped State. Efficiency {ratio*100:.1f}%."
                simulation_result = f"Eff Energy: {eff:.2f}"
            elif hasattr(res, 'ratio'):
                 # Asymmetric Result
                 narrative = res.description
                 simulation_result = f"Ratio: {res.ratio:.2f}"

        elif ptype == "dual_fusion" or ptype == "multi_fusion_chaos":
            # Case 001 & 010 (Multiple concurrent fusions)
            # Simulate additive entropy
            # Heuristic: Each fusion adds stability but also complexity cost
            base_eta = 0.8
            entropy_tax = params.get('entropy_tax', 0.0)
            base_eta -= entropy_tax
            
            res = StructuralDynamics.generalized_collision(base_eta, 20.0, 5.0) # Minor clash
            narrative = f"Phase Shift Multiplier. Entropy: {res.entropy_increase:.2f}. " + res.description
            simulation_result = f"Rem Eta: {res.remaining_coherence:.2f}"

        elif ptype == "stem_branch_coupling":
             # Case 002 (Full Field)
             # Extremely high coherence
             target_eta = params.get('eta_target', 0.95)
             res = StructuralDynamics.generalized_collision(target_eta, 30.0, 0.0)
             narrative = "🛡️ SUPERFLUID STATE (Zero Resistance). " + res.description
             simulation_result = f"Eta: {res.remaining_coherence:.2f}"

        elif ptype == "month_resistance":
            # Case 004 (False Fusion)
            # Low Eta due to Month Denial
            # Generalized Collision with Clash > Fusion?
            # Or just low initial Eta
            res = StructuralDynamics.generalized_collision(0.2, 10.0, 0.0) # Eta 0.2
            narrative = "❌ PHASE TRANSITION FAILED (Month Resistance). " + res.description
            simulation_result = "Structure Collapsed"

        elif ptype == "spatial_decay":
            # Case 005 (Gap 2)
            gap = params.get('gap', 2)
            base = params.get('base_energy', 10.0)
            k = StructuralDynamics.calculate_spatial_decay(gap)
            final = base * k
            narrative = f"📡 Signal Decay (Gap {gap}). K={k}. Energy {base} -> {final:.2f}."
            simulation_result = f"E_final: {final:.2f}"

        elif ptype == "vault_break":
            # Case 006
            clash = params.get('clash_energy', 10.0)
            integ = params.get('vault_integrity', 10.0)
            # Use Defusion Event logic conceptualized as Vault Break
            res = StructuralDynamics.simulate_defusion_event(integ, 0.5, clash)
            if res.broken:
                narrative = "🔓 VAULT BREACHED. Hidden Stems Released."
            else:
                narrative = "🔒 Vault Holds. Impact Insufficient."
            simulation_result = f"Broken: {res.broken}"

        elif ptype == "stability_test":
            # Case 007 (Half vs Clash)
            bond = params.get('bond_energy', 8.0)
            clash = params.get('clash_energy', 14.0)
            # Half Combinations have medium Eta
            res = StructuralDynamics.simulate_defusion_event(bond, 0.6, clash) # Eta 0.6 for Half
            narrative = "⚠️ " + res.description
            simulation_result = f"Entropy: {res.entropy_released:.2f}"
            
        elif ptype == "field_overlap":
            # Case 009
            # Purely additive check
            e1 = params.get('directional_energy', 0)
            e2 = params.get('trine_energy', 0)
            total = e1 + e2 # Constructive interference
            narrative = f"🌊 CONSTRUCTIVE SUPERPOSITION. Total Field: {total}."
            simulation_result = f"Total: {total}"
            
        else:
            narrative = "Unknown Physics Type"
            
        print(f"   > Result: {simulation_result}")
        print(f"   > Narrative: {narrative}")
        
        result_log.append(f"| {cid} | {ptype} | {simulation_result} | {narrative} |")

    print("\n--- REPORT GENERATION ---")
    print("\n".join(result_log))

if __name__ == "__main__":
    run_extreme_stress_test()
