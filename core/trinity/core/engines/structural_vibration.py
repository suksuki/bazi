
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
        """
        context = context or {}
        geo_k = self._get_geo_factor(context)
        
        # 1. Base Energy Mapping (Linear)
        energy_map = self._map_base_energy(stems, branches)
        
        # 2. Vertical Coupling (Branch -> Stem Modulation)
        # Apply Geo Damping to Roots first
        self._apply_vertical_coupling(energy_map, stems, branches, geo_k)
        
        # 3. Non-linear Transmission (Tanh Saturation)
        # Simulate interaction network (Simplified graph dynamics)
        # Here we simulate the final energy state after stabilization
        final_energy = {}
        for elem, e_val in energy_map.items():
            final_energy[elem] = self._tanh_saturation(e_val)
            
        # 4. Entropy Calculation
        entropy = self._calculate_system_entropy(final_energy)
        
        # 5. Composite Deity Optimization
        # Find optimal 'Useful God' mix to minimize entropy
        optimal_mix = self._optimize_composite_deity(final_energy)
        
        return {
            "energy_state": final_energy,
            "entropy": round(entropy, 4),
            "optimal_deity_mix": optimal_mix,
            "transmission_efficiency": self._calculate_efficiency(energy_map, final_energy)
        }
    
    def _tanh_saturation(self, energy_in: float) -> float:
        """
        Non-linear saturation function: E_out = E_max * tanh(E_in / E_threshold)
        Assumes E_threshold approx E_MAX / 2 for smooth roll-off.
        """
        threshold = self.E_MAX / 2.0
        return self.E_MAX * math.tanh(energy_in / threshold)
    
    def _apply_vertical_coupling(self, energy_map: Dict[str, float], stems: List[str], branches: List[str], geo_k: float):
        """
        Modulates Stem energy based on Root strength and Geo factor.
        V_boost = Root * C_coupling * K_geo
        """
        # Simple mapping: Check if Stem has Root in ANY branch
        # If rooted, apply boost.
        
        for stem in stems:
            stem_elem = BaziParticleNexus.STEMS.get(stem)[0]
            # Check for roots
            root_strength = 0.0
            for br in branches:
                hidden = BaziParticleNexus.get_branch_weights(br)
                for h_stem, h_weight in hidden:
                    h_elem = BaziParticleNexus.STEMS.get(h_stem)[0]
                    if h_elem == stem_elem:
                        root_strength += h_weight * 0.1 # Scaling
            
            # Apply Vertical Boost
            v_boost = root_strength * self.K_COUPLING * geo_k
            
            # Add to map
            energy_map[stem_elem] = energy_map.get(stem_elem, 0) + v_boost

    def _calculate_system_entropy(self, energy_map: Dict[str, float]) -> float:
        """
        Shannon Entropy of the element distribution: S = -Sum(Pi * ln(Pi))
        """
        total = sum(energy_map.values())
        if total == 0: return 0.0
        
        entropy = 0.0
        for e, v in energy_map.items():
            p = v / total
            if p > 0:
                entropy -= p * math.log(p)
        return entropy

    def _optimize_composite_deity(self, current_energy: Dict[str, float]) -> Dict[str, float]:
        """
        Finds the element(s) that, if injected, would minimize system entropy (bring balance).
        Returns a dict of {Element: Injection_Percentage}.
        """
        # Naive Gradient Descent: Try injecting each element and see S delta
        best_elem = None
        min_s = float('inf')
        
        base_s = self._calculate_system_entropy(current_energy)
        
        results = {}
        for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water']:
            # Sim injection
            temp_map = current_energy.copy()
            temp_map[elem] = temp_map.get(elem, 0) + 2.0 # Injection Unit
            new_s = self._calculate_system_entropy(temp_map)
            results[elem] = new_s
            
        # Select best single or composite
        # For now, return top 1
        sorted_res = sorted(results.items(), key=lambda x: x[1])
        best_e = sorted_res[0][0]
        
        return {best_e: 1.0} # 100% suggestion

    def _get_geo_factor(self, context: Dict[str, Any]) -> float:
        # Extract K_geo from context.data or default 1.0
        # If 'geo_factor' is explicitly passed
        data = context.get('data', {})
        return data.get('geo_factor', 1.0)
        
    def _map_base_energy(self, stems: List[str], branches: List[str]) -> Dict[str, float]:
        emap = {}
        for s in stems:
             e = BaziParticleNexus.STEMS.get(s)[0]
             emap[e] = emap.get(e, 0) + 1.0
        # Branches handled via vertical coupling mostly, but add base
        for b in branches:
             e = BaziParticleNexus.BRANCHES.get(b)[0]
             emap[e] = emap.get(e, 0) + 1.0
        return emap
    
    def _calculate_efficiency(self, energy_in: Dict[str, float], energy_out: Dict[str, float]) -> float:
        total_in = sum(energy_in.values())
        total_out = sum(energy_out.values())
        if total_in == 0: return 0.0
        return total_out / total_in

