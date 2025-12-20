from typing import List, Dict, Optional, Any
import numpy as np
from .rule_registry import RuleRegistry
from ..core.math_engine import ProbValue, prob_compare
from ..core.physics_engine import ParticleDefinitions, PhysicsEngine
from ..core.wave_mechanics import ImpedanceModel, WaveState

class LogicMatrix:
    """
    Quantum Trinity: Logic Matrix (V14.0)
    =====================================
    Advanced rule matching using Wave Interference and Resonant Harmonics.
    """
    
    def __init__(self):
        self.registry = RuleRegistry()
        
    def match_logic(self, bazi: List[str], day_master: str, waves: Dict[str, WaveState]) -> List[Dict[str, Any]]:
        """
        Identify active physical interactions and return their interference parameters.
        Implements the V14.0 Arbitration Protocol (Hui > He > Chong > Xing > Hai).
        """
        # 0. Context extraction
        stems = [p[0] for p in bazi if p]
        branches = [p[1] for p in bazi if len(p) > 1]
        month_branch = branches[1] if len(branches) > 1 else None
        stem_set = set(stems)
        branch_set = set(branches)
        
        matched_rules = []
        raw_interactions = []
        
        # --- 1. PROXIMITY & GEOMETRIC DATA (Interference) ---
        
        # A. SanHui (三会) - Priority 100
        for trio, element in self.registry.SAN_HUI.items():
            if trio.issubset(branch_set):
                raw_interactions.append({
                    'id': 'B7', 'type': 'SanHui', 'name': f'SanHui ({element})',
                    'target_element': element, 'branches': set(trio), 'priority': 100,
                    'resonance_q': 4.0, 'phase_shift': ImpedanceModel.PHASE_MAP['Harmony']
                })
        
        # B. Three Harmony (B6) - Priority 80
        for trio, element in self.registry.SAN_HE.items():
            if trio.issubset(branch_set):
                raw_interactions.append({
                    'id': 'B6', 'type': 'SanHe', 'name': f'Three Harmony ({element})',
                    'target_element': element, 'branches': set(trio), 'priority': 80,
                    'resonance_q': 3.0, 'phase_shift': ImpedanceModel.PHASE_MAP['Harmony']
                })

        # C. LiuHe (B3) - Priority 60
        for pair, element in self.registry.LIU_HE.items():
            if pair.issubset(branch_set):
                raw_interactions.append({
                    'id': 'B3', 'type': 'LiuHe', 'name': f'LiuHe ({element})',
                    'target_element': element, 'branches': set(pair), 'priority': 60,
                    'resonance_q': 1.8, 'phase_shift': ImpedanceModel.PHASE_MAP['Harmony']
                })

        # D. Branch Clashes (B2) - Priority 40
        clash_map = self.registry.CLASH_MAP
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                b1, b2 = branches[i], branches[j]
                if clash_map.get(b1) == b2:
                    # Apply Clash to BOTH branches (Symmetric Mutual Destruction)
                    e1 = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(b1, {}).get('element')
                    if e1:
                        raw_interactions.append({
                            'id': 'B2', 'type': 'Chong', 'name': f'Clash ({b1}-{b2})',
                            'target_element': e1, 'branches': {b1, b2}, 'priority': 40,
                            'resonance_q': 0.7, 'phase_shift': ImpedanceModel.PHASE_MAP['Clash']
                        })
                    
                    if e2:
                        raw_interactions.append({
                            'id': 'B2', 'type': 'Chong', 'name': f'Clash ({b2}-{b1})',
                            'target_element': e2, 'branches': {b1, b2}, 'priority': 40,
                            'resonance_q': 0.7, 'phase_shift': ImpedanceModel.PHASE_MAP['Clash']
                        })

                # B2.1 Branch Resonance (Identical Branches) - Priority 30
                # Represents wave amplification due to frequency matching
                elif b1 == b2:
                     e1 = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(b1, {}).get('element')
                     raw_interactions.append({
                        'id': 'B2_Res', 'type': 'Resonance', 'name': f'Resonance ({b1})',
                        'target_element': e1, 'branches': {b1}, # Logic engine usually merges set, but for visualization we need distinct connectivity?
                        # ACTUALLY, if branches is a set {b1}, it collapses to 1 item.
                        # We need to distinguish WHICH pillars are involved for the Visualizer.
                        # But LogicMatrix returns 'branches' as a SET of CHARS.
                        # If the set is {'Zi'}, it doesn't distinguish between Year-Zi and Month-Zi.
                        # Wait. The Visualizer maps rule['branches'] char to Chart Branches.
                        # If rule['branches'] = {'Zi'}, Visualizer finds ALL Zi's in chart and connects them?
                        # YES. The code in quantum_lab.py says:
                        # involved_nodes = [node_id for b_char in rule['branches'] ...]
                        # If rule branches = {'Zi'}, and chart has 4 Zis, involved_nodes will be ALL 4 Zis.
                        # And it will draw lines between them all (fully connected graph).
                        # This is PERFECT for resonance.
                        'branches': {b1}, 
                        'priority': 30,
                        'resonance_q': 1.2, # Constructive Interference
                        'phase_shift': ImpedanceModel.PHASE_MAP['Harmony']
                     })

        # E. Branch Harm (B9) - Priority 10
        liu_hai = {
            frozenset({'子', '未'}), frozenset({'丑', '午'}), frozenset({'寅', '巳'}),
            frozenset({'卯', '辰'}), frozenset({'申', '亥'}), frozenset({'酉', '戌'})
        }
        for pair in liu_hai:
            if pair.issubset(branch_set):
                # Target element for Harm is usually the one being damaged
                raw_interactions.append({
                    'id': 'B9', 'type': 'Hai', 'name': f'Harm ({list(pair)})',
                    'target_element': None, 'branches': set(pair), 'priority': 10,
                    'resonance_q': 0.5, 'phase_shift': ImpedanceModel.PHASE_MAP['Clash']
                })

        # --- 2. ARBITRATION PROTOCOL: Structural Locking & Jealousy ---
        from ..core.structural_dynamics import StructuralDynamics

        # Sort by priority (Higher first)
        raw_interactions.sort(key=lambda x: x['priority'], reverse=True)
        
        locked_branches = set()
        
        # Group by priority to handle same-tier conflicts (Jealousy)
        from collections import defaultdict
        by_priority = defaultdict(list)
        for r in raw_interactions: 
            by_priority[r['priority']].append(r)
            
        sorted_priorities = sorted(by_priority.keys(), reverse=True)
        
        for prio in sorted_priorities:
            tier_rules = by_priority[prio]
            
            # 2.1 Check for Contention within this tier
            # Map branch -> list of rules claiming it
            claims = defaultdict(list)
            for rule in tier_rules:
                # Only check branches not yet locked by HIGHER tiers
                available_branches = rule['branches'] - locked_branches
                if not available_branches: continue # Completely blocked by higher tier
                
                # If partially blocked, does the rule survive? 
                # Strict arbitration: Structure needs ALL branches? 
                # Usually yes. If SanHe loses one branch to SanHui, SanHe breaks.
                if len(available_branches) < len(rule['branches']):
                    continue # Broken structure
                
                for b in rule['branches']:
                    claims[b].append(rule)

            # 2.2 Resolve Contention
            processed_rules = set() # Track rules handled in this tier
            
            for b, rules_claiming in claims.items():
                if len(rules_claiming) > 1:
                    # JEALOUSY DETECTED (e.g. 2 rules fighting for branch 'b')
                    # Apply StructuralDynamics.simulate_multi_branch_interference logic
                    # Calculate Jealousy Damping Factor
                    N = len(rules_claiming)
                    damp_res = StructuralDynamics.simulate_multi_branch_interference(10.0, [1]*N) # Mock energy
                    
                    # Apply damping to ALL competitors
                    # Effective Q = Original Q * (Eff / Total) * N? 
                    # Simpler: Multiply Q by (1 - Damping) -> 0.7 approx
                    # From physics: 30% loss
                    damping = 0.7 if N == 2 else 0.5 # Heuristic based on physics
                    state_desc = "Jealousy Damping"
                    
                    for r in rules_claiming:
                        if id(r) in processed_rules: continue
                        r['resonance_q'] *= damping
                        r['fusion_state'] = f"{state_desc} (N={N})"
                        processed_rules.add(id(r))
                else:
                    # Single claim, clean pass (unless processed already)
                    pass

            # 2.3 Finalize & Lock
            for rule in tier_rules:
                # Re-verify availability (in case of logic drift)
                overlap = rule['branches'].intersection(locked_branches)
                if overlap: continue
                
                matched_rules.append({
                    'id': rule['id'],
                    'name': rule['name'],
                    'category': 'B',
                    'target_element': rule['target_element'],
                    'phase_shift': rule['phase_shift'],
                    'resonance_q': rule['resonance_q'],
                    'fusion_state': rule.get('fusion_state', 'Stable'),
                    'lock': rule['priority'] >= 60,
                    'active': True,
                    'branches': rule['branches']
                })

                if rule['priority'] >= 60:
                    locked_branches.update(rule['branches'])

        # --- 3. OTHER LOGIC (Non-Structural) ---

        # Stem Combinations (B1) - Context-based interference
        for pair, element in {
            frozenset({'甲', '己'}): 'Earth', frozenset({'乙', '庚'}): 'Metal',
            frozenset({'丙', '辛'}): 'Water', frozenset({'丁', '壬'}): 'Wood',
            frozenset({'戊', '癸'}): 'Fire',
        }.items():
            if pair.issubset(stem_set):
                matched_rules.append({
                    'id': 'B1', 'name': f'Stem Combine ({element})', 'category': 'B',
                    'target_element': element, 'phase_shift': ImpedanceModel.PHASE_MAP['Harmony'],
                    'resonance_q': 1.5, 'lock': False, 'active': True,
                    'branches': set() # Stems don't map to branches directly in this logic yet
                })

        # Vault Impedance (D-Category)
        for b in branch_set:
            if b in self.registry.TOMB_ELEMENTS:
                target_elem = self.registry.TOMB_ELEMENTS[b]
                # Vault is opened if ANY of the branches clashing it are NOT locked out
                # Simplified: check if it's in any applied clash rule
                opened = any(r['id'] == 'B2' and b in branches for r in matched_rules)
                matched_rules.append({
                    'id': 'D1' if not opened else 'D2',
                    'name': f'Vault ({target_elem})', 'category': 'D',
                    'resonance_q': 2.0 if opened else 0.4, 'active': True,
                    'branches': {b}
                })

        # Seasonal Command (A1)
        if month_branch:
            dm_elem = ParticleDefinitions.STEM_WAVEFORMS.get(day_master, {}).get('element')
            potential = PhysicsEngine.get_state_potential(dm_elem, month_branch)
            matched_rules.append({
                'id': 'A1', 'name': f'Seasonal Potential ({PhysicsEngine.get_seasonal_state(dm_elem, month_branch)})',
                'category': 'A', 'target_element': dm_elem, 'resonance_q': potential, 'active': True
            })

        return matched_rules
