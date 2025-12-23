
import numpy as np
from typing import List
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants, ArbitrationNexus

class StructuralStressEngine:
    """
    Phase 32: Penalty & Harm Dynamics Engine
    Responsible for calculating:
    1. SAI (Stress Accumulation Index) - Kinetic/Bond Energy Model
    2. IC (Interference Coefficient) - Phase Jitter SNR Model
    """
    
    def __init__(self, resonance_context=None, day_master=None):
        self.resonance_context = resonance_context
        self.day_master = day_master
        
    def calculate_micro_lattice_defects(self, branches: list, month_branch: str = None) -> dict:
        """
        Main entry point for structural stress analysis.
        Args:
            branches: List of Earthly Branches in the chart.
            month_branch: The month branch (Season Command) for Bond Energy calculation.
        Returns:
            Dict containing SAI, IC, and detailed topology.
        """
        if not branches:
            return {'SAI': 0.0, 'IC': 0.0, 'defects': []}
            
        defects = []
        
        # --- 1. SAI (Stress Accumulation Index) ---
        # Formula: SAI = (Sigma E_kinetic) / E_bond
        # E_kinetic: Sum of seasonal strengths of participating penalty branches.
        # E_bond: Bonding energy of the lattice (Month Support).
        
        # Get Month Energy Matrix
        season_factors = PhysicsConstants.SEASONAL_MATRIX.get(month_branch, {})
        # Fallback if unknown
        if not season_factors:
            season_factors = {'Wood': 1.0, 'Fire': 1.0, 'Earth': 1.0, 'Metal': 1.0, 'Water': 1.0}
            
        def get_branch_energy(b):
            elem = BaziParticleNexus.BRANCHES.get(b, ("Earth", 0, []))[0]
            return season_factors.get(elem, 1.0)

        # Base Bond Energy (Lattice Strength)
        # If the month itself is involved in penalty, Bond Strength decreases.
        E_bond_base = 1.5 # Standard stability constant
        
        kinetic_sum = 0.0
        branch_counts = {b: branches.count(b) for b in branches}
        unique_branches = set(branches)
        
        # A. Ungrateful Penalty (寅-巳-申)
        # Key Feature: Wood feeds Fire, Fire melts Metal, Metal chops Wood. A loop of creation/destruction.
        if {'寅', '巳', '申'}.issubset(unique_branches):
            # Calculate Kinetic Energy of the trio
            k_yin = get_branch_energy('寅') * branch_counts['寅']
            k_si = get_branch_energy('巳') * branch_counts['巳']
            k_shen = get_branch_energy('申') * branch_counts['申']
            
            # The more active the season is for these elements, the higher the shear stress.
            # e.g. In Spring (Tiger), Wood is strong so Yin is active.
            
            # [PHASE 33] Remedy Logic: Hai (Pig) Injection
            # Hai combines with Yin (Wood+), Clashes Si (Fire Balancing), Harms Shen (Metal Distraction).
            # This creates a "Buffer Zone".
            damping = 1.0
            if '亥' in unique_branches:
                damping = 0.5
                defects.append({'type': 'REMEDY_ACTIVE', 'score': -0.5, 'nodes': ['亥'], 'desc': 'Hai Water Logic Damping'})
            
            base_coeff = 0.8 * damping
            kinetic_sum += (k_yin + k_si + k_shen) * base_coeff
            
            defects.append({'type': 'PENALTY_UNGRATEFUL', 'score': kinetic_sum, 'nodes': ['寅', '巳', '申']})
            
        elif len({'寅', '巳', '申'}.intersection(unique_branches)) == 2:
            # Partial penalty (Stress rise but not collapse)
            kinetic_sum += 0.3
            
        # B. Bullying Penalty (丑-戌-未)
        if {'丑', '戌', '未'}.issubset(unique_branches):
            k_chou = get_branch_energy('丑') * branch_counts['丑']
            k_xu = get_branch_energy('戌') * branch_counts['戌']
            k_wei = get_branch_energy('未') * branch_counts['未']
            
            kinetic_sum += (k_chou + k_xu + k_wei) * 0.8
            defects.append({'type': 'PENALTY_BULLYING', 'score': kinetic_sum, 'nodes': ['丑', '戌', '未']})

        # C. Uncivil Penalty (子-卯)
        if '子' in unique_branches and '卯' in unique_branches:
            k_zi = get_branch_energy('子') * branch_counts['子']
            k_mao = get_branch_energy('卯') * branch_counts['卯']
            kinetic_sum += (k_zi + k_mao) * 0.6
            defects.append({'type': 'PENALTY_UNCIVIL', 'score': (k_zi+k_mao)*0.6, 'nodes': ['子', '卯']})
            
        # D. Self Penalty (辰, 午, 酉, 亥)
        for b in ['辰', '午', '酉', '亥']:
            if branch_counts.get(b, 0) >= 2:
                k_self = get_branch_energy(b) * (branch_counts[b] - 1)
                kinetic_sum += k_self * 0.5
                defects.append({'type': 'PENALTY_SELF', 'score': k_self * 0.5, 'nodes': [b]})

        # E. Yang Ren Shear Burst (Sheep Blade Phase Transition)
        if self.day_master:
            shear_burst_score = self._calculate_shear_burst(branches)
            if shear_burst_score > 0:
                kinetic_sum += shear_burst_score
                defects.append({
                    'type': 'SHEAR_BURST', 
                    'score': shear_burst_score, 
                    'nodes': branches, 
                    'desc': '羊刃逢冲: 超临界能级爆发 (Shear Burst)'
                })

        # Calculate Final SAI
        # If month is part of penalty, E_bond drops.
        # Simple heuristic: If kinetic sum is high, it likely involves the month.
        SAI = kinetic_sum / E_bond_base
        
        
        # --- 2. IC (Interference Coefficient) ---
        # Formula: IC = 1 - (1 / (1 + alpha * N_Harm))
        # Logic: SNR attenuation.
        
        alpha = 0.8 # Increased sensitivity coefficient
        harm_energy_sum = 0.0
        
        checked_pairs = set()
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                b1 = branches[i]
                b2 = branches[j]
                if ArbitrationNexus.HARM_MAP.get(b1) == b2:
                    pair_key = tuple(sorted([b1, b2]))
                    if pair_key not in checked_pairs:
                        # Energy-weighted harm: Sum of participating branch energies
                        e1 = get_branch_energy(b1)
                        e2 = get_branch_energy(b2)
                        harm_energy_sum += (e1 + e2) * 0.5
                        defects.append({'type': 'HARM_JITTER', 'score': (e1 + e2) * 0.5, 'nodes': [b1, b2]})
                        checked_pairs.add(pair_key)
        
        if harm_energy_sum == 0:
            IC = 0.0
        else:
            # SNR Model with energy weighting
            IC = 1.0 - (1.0 / (1.0 + alpha * harm_energy_sum))
            
        return {
            'SAI': round(SAI, 4),
            'IC': round(IC, 4),
            'defects': defects
        }
    def _calculate_shear_burst(self, branches: List[str]) -> float:
        """
        Detects if a 'Sheep Blade' (Yang Ren) node is under extreme clash.
        Triggering this leads to a non-linear SAI jump.
        """
        from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine
        yang_ren = SymbolicStarsEngine.YANG_REN_MAP.get(self.day_master)
        
        if not yang_ren or yang_ren not in branches:
            return 0.0
            
        # Check if the yang_ren node is being clashed
        chong_target = ArbitrationNexus.CLASH_MAP.get(yang_ren)
        if chong_target in branches:
            # Phase Transition: The stress isn't just cumulative, it hits a burst threshold.
            return 2.5  # Critical shockwave score
            
        return 0.0
