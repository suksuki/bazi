
import math
import numpy as np
from typing import Dict, List, Any, Optional
from core.trinity.core.nexus.definitions import PhysicsConstants, BaziParticleNexus

class StructuralVibrationEngine:
    """
    MOD_15: Structural Vibration Transmission Engine
    
    Implements non-linear energy transmission physics including:
    1. Tanh Saturation: Limiting energy blow-up in transmission chains.
    2. Vertical Coupling: Ground branch modulation of Heavenly Stem carriers.
    3. Entropy Optimization: Finding the lowest entropy 'Deity' configuration.
    """
    
    def __init__(self, day_master: str):
        self.day_master = day_master
        self.E_MAX = 10.0  # Physical energy ceiling
        self.K_COUPLING = 3.0 # Vertical coupling constant
        
    def calculate_vibration_metrics(self, stems: List[str], branches: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for calculating structural vibration transmission.
        Now supports 'annual_stem' pulse trigger for hidden stems.
        """
        context = context or {}
        geo_k = self._get_geo_factor(context)
        # Extract periodic pulse (Annual Stem)
        annual_pillar = context.get('annual_pillar', '甲子')
        annual_stem = annual_pillar[0] if annual_pillar else None
        
        # 1. Base Energy Mapping (Linear)
        energy_map = self._map_base_energy(stems, branches)
        
        # 2. Vertical Coupling (Branch -> Stem Modulation)
        # Phase 4.0: Includes Hidden-State Pulse (0.6/0.3/0.1)
        self._apply_vertical_coupling(energy_map, stems, branches, geo_k, annual_stem)
        
        # 3. Non-linear Transmission (Tanh Saturation)
        final_energy = {}
        for elem, e_val in energy_map.items():
            final_energy[elem] = self._tanh_saturation(e_val)
            
        # 4. Phase Transition Detection (MOD_15 Extension - Refined 80% Threshold)
        is_phase_transition, dominant_elem = self._detect_phase_transition(final_energy)
        
        # 5. Entropy Calculation
        entropy = self._calculate_system_entropy(final_energy)
        
        # 6. Composite Deity Optimization
        optimal_mix = self._optimize_composite_deity(final_energy, is_phase_transition, dominant_elem)
        
        efficiency = self._calculate_efficiency(energy_map, final_energy)
        impedance = 1.0 / efficiency if efficiency > 0 else 10.0
        
        return {
            "energy_state": final_energy,
            "entropy": round(entropy, 4),
            "optimal_deity_mix": optimal_mix,
            "transmission_efficiency": efficiency,
            "impedance_magnitude": round(impedance, 4),
            "is_phase_transition": is_phase_transition,
            "dominant_element": dominant_elem
        }
    
    def _detect_phase_transition(self, energy_map: Dict[str, float]) -> tuple[bool, str]:
        """
        Detects Phase Transition (Extreme Follow).
        Threshold increased to 80% for Phase 4.0.
        """
        total_energy = sum(energy_map.values())
        if total_energy == 0: return False, None
        
        sorted_elems = sorted(energy_map.items(), key=lambda x: x[1], reverse=True)
        dom_elem, dom_val = sorted_elems[0]
        
        purity = dom_val / total_energy
        if purity < 0.80: # Strict 80% Threshold
            return False, None
            
        return True, dom_elem

    def _tanh_saturation(self, energy_in: float) -> float:
        """
        Non-linear saturation: E_out = E_max * tanh(E_in / threshold)
        """
        threshold = self.E_MAX / 2.0
        return self.E_MAX * math.tanh(energy_in / threshold)
    
    def _apply_vertical_coupling(self, energy_map: Dict[str, float], stems: List[str], branches: List[str], geo_k: float, annual_stem: str = None):
        """
        Modulates Stem energy.
        Phase 4.0: Hidden-State Pulse Trigger.
        If current annual_stem matches a hidden stem, release it at full potential.
        Otherwise, use default weights.
        """
        for stem in stems:
            stem_elem = BaziParticleNexus.STEMS.get(stem)[0]
            root_strength = 0.0
            
            for br in branches:
                hidden = BaziParticleNexus.get_branch_weights(br)
                # Hidden structure: [(Stem, Weight), ...] 
                # Weight is usually a priority: Main(10), Secondary(3), Tertiary(1)
                for h_idx, (h_stem, h_weight) in enumerate(hidden):
                    h_elem = BaziParticleNexus.STEMS.get(h_stem)[0]
                    if h_elem == stem_elem:
                        # [PATCH] Pulsed Release Logic
                        # If annual_stem 'activates' this hidden stem, increase release efficiency
                        is_pulsed = (h_stem == annual_stem)
                        pulse_mult = 1.5 if is_pulsed else 1.0
                        
                        # Apply 0.6/0.3/0.1 Ratio for Main/Sub/Residual
                        ratios = [0.6, 0.3, 0.1]
                        ratio = ratios[h_idx] if h_idx < len(ratios) else 0.05
                        
                        root_strength += h_weight * ratio * pulse_mult
            
            v_boost = root_strength * self.K_COUPLING * geo_k
            energy_map[stem_elem] = energy_map.get(stem_elem, 0) + v_boost

    def _calculate_system_entropy(self, energy_map: Dict[str, float]) -> float:
        """Shannon Entropy S = -Sum(Pi * ln(Pi))"""
        total = sum(energy_map.values())
        if total == 0: return 0.0
        entropy = 0.0
        for e, v in energy_map.items():
            p = v / total
            if p > 0:
                entropy -= p * math.log(p)
        return entropy

    def _optimize_composite_deity(self, current_energy: Dict[str, float], is_phase_transition: bool = False, dominant_elem: str = None) -> Dict[str, float]:
        """
        Normal: Minimize Entropy.
        Phase Transition: Support Flow (Follow or Clear Output).
        """
        if is_phase_transition and dominant_elem:
            # We also suggest the 'Output' of the dominant element if it exists
            gen_map = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
            output_elem = gen_map.get(dominant_elem)
            return {dominant_elem: 0.8, output_elem: 0.2}
            
        results = {}
        for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water']:
            temp_map = current_energy.copy()
            temp_map[elem] = temp_map.get(elem, 0) + 2.0
            new_s = self._calculate_system_entropy(temp_map)
            results[elem] = new_s
            
        sorted_res = sorted(results.items(), key=lambda x: x[1])
        return {sorted_res[0][0]: 1.0}
    
    def _get_geo_factor(self, context: Dict[str, Any]) -> float:
        data = context.get('data', {})
        return data.get('geo_factor', 1.0)
        
    def _map_base_energy(self, stems: List[str], branches: List[str]) -> Dict[str, float]:
        emap = {}
        for s in stems:
             e = BaziParticleNexus.STEMS.get(s)[0]
             emap[e] = emap.get(e, 0) + 1.0
        for b in branches:
             e = BaziParticleNexus.BRANCHES.get(b)[0]
             emap[e] = emap.get(e, 0) + 0.5 # Minimal base from branch
        return emap
    
    def _calculate_efficiency(self, energy_in: Dict[str, float], energy_out: Dict[str, float]) -> float:
        total_in = sum(energy_in.values())
        total_out = sum(energy_out.values())
        if total_in == 0: return 0.0
        return total_out / total_in

