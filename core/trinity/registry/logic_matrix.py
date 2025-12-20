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
        san_hui = {
            frozenset({'寅', '卯', '辰'}): 'Wood',
            frozenset({'巳', '午', '未'}): 'Fire',
            frozenset({'申', '酉', '戌'}): 'Metal',
            frozenset({'亥', '子', '丑'}): 'Water',
        }
        for trio, element in san_hui.items():
            if trio.issubset(branch_set):
                raw_interactions.append({
                    'id': 'B7', 'type': 'SanHui', 'name': f'SanHui ({element})',
                    'target_element': element, 'branches': set(trio), 'priority': 100,
                    'resonance_q': 4.0, 'phase_shift': ImpedanceModel.PHASE_MAP['Harmony']
                })
        
        # B. Three Harmony (B6) - Priority 80
        three_harmony = {
            frozenset({'申', '子', '辰'}): 'Water',
            frozenset({'亥', '卯', '未'}): 'Wood',
            frozenset({'寅', '午', '戌'}): 'Fire',
            frozenset({'巳', '酉', '丑'}): 'Metal',
        }
        for trio, element in three_harmony.items():
            if trio.issubset(branch_set):
                raw_interactions.append({
                    'id': 'B6', 'type': 'SanHe', 'name': f'Three Harmony ({element})',
                    'target_element': element, 'branches': set(trio), 'priority': 80,
                    'resonance_q': 3.0, 'phase_shift': ImpedanceModel.PHASE_MAP['Harmony']
                })

        # C. LiuHe (B3) - Priority 60
        liu_he = {
            frozenset({'子', '丑'}): 'Earth', frozenset({'寅', '亥'}): 'Wood',
            frozenset({'卯', '戌'}): 'Fire', frozenset({'辰', '酉'}): 'Metal',
            frozenset({'巳', '申'}): 'Water', frozenset({'午', '未'}): 'Earth',
        }
        for pair, element in liu_he.items():
            if pair.issubset(branch_set):
                raw_interactions.append({
                    'id': 'B3', 'type': 'LiuHe', 'name': f'LiuHe ({element})',
                    'target_element': element, 'branches': set(pair), 'priority': 60,
                    'resonance_q': 1.8, 'phase_shift': ImpedanceModel.PHASE_MAP['Harmony']
                })

        # D. Branch Clashes (B2) - Priority 40
        clash_map = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅', 
                     '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
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
                    
                    e2 = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(b2, {}).get('element')
                    if e2:
                        raw_interactions.append({
                            'id': 'B2', 'type': 'Chong', 'name': f'Clash ({b2}-{b1})',
                            'target_element': e2, 'branches': {b1, b2}, 'priority': 40,
                            'resonance_q': 0.7, 'phase_shift': ImpedanceModel.PHASE_MAP['Clash']
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

        # --- 2. ARBITRATION PROTOCOL: Structural Locking ---
        
        # Sort by priority (Higher first)
        raw_interactions.sort(key=lambda x: x['priority'], reverse=True)
        
        locked_branches = set()
        for inter in raw_interactions:
            # Check if any branch in this interaction is already "Locked" by a higher priority structure
            overlap = inter['branches'].intersection(locked_branches)
            if not overlap:
                # No conflict, apply rule and lock branches
                matched_rules.append({
                    'id': inter['id'],
                    'name': inter['name'],
                    'category': 'B',
                    'target_element': inter['target_element'],
                    'phase_shift': inter['phase_shift'],
                    'resonance_q': inter['resonance_q'],
                    'active': True
                })
                # Hui and He structures lock their branches
                is_lock = inter['priority'] >= 60
                if is_lock:
                    locked_branches.update(inter['branches'])

                matched_rules.append({
                    'id': inter['id'],
                    'name': inter['name'],
                    'category': 'B',
                    'target_element': inter['target_element'],
                    'phase_shift': inter['phase_shift'],
                    'resonance_q': inter['resonance_q'],
                    'lock': is_lock, # Flag for FluxEngine
                    'active': True
                })

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
                    'resonance_q': 1.5, 'lock': False, 'active': True
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
                    'resonance_q': 2.0 if opened else 0.4, 'active': True
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
