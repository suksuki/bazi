
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from .wave_mechanics import WaveState, InterferenceSolver
from .physics_engine import ParticleDefinitions

class PatternDeconstructor:
    """
    Phase 25/26: Multi-Resonance Deconstruction Engine.
    Handles 'Violent Disassembly' of complex Bazi structures.
    Analyzes the systemic binding energy and 'Chain Reactions' of clashes.
    """

    @staticmethod
    def identify_energy_nodes(bazi: List[str]) -> List[Dict[str, Any]]:
        """
        Identifies pillars with high interaction potential.
        """
        nodes = []
        for i, pillar in enumerate(bazi):
            if len(pillar) < 2: continue
            stem, branch = pillar[0], pillar[1]
            pillar_names = ['year', 'month', 'day', 'hour', 'luck', 'annual']
            p_name = pillar_names[i] if i < len(pillar_names) else 'unknown'
            nodes.append({
                "index": i,
                "pillar": pillar,
                "potential": ParticleDefinitions.PILLAR_WEIGHTS.get(p_name, 1.0)
            })
        return nodes

    @staticmethod
    def calculate_binding_energy(nodes: List[Dict[str, Any]], waves: Dict[str, WaveState]) -> float:
        """
        Estimates the 'Structural Integrity' energy (E_bind).
        Higher SNR and tighter phase alignment increase binding.
        """
        # Sum of amplitudes weighted by coherence
        z_sum = sum(w.to_complex() for w in waves.values())
        base_energy = float(np.abs(z_sum))
        
        # Factor in pillar stability
        # (Simplified for now: use base_energy)
        return base_energy * 0.8 # Empirical coefficient

    @staticmethod
    def simulate_violent_disassembly(
        dm_wave: WaveState,
        field_waves: List[WaveState],
        energy_nodes: List[Dict[str, Any]],
        trigger_nodes: Optional[List[Dict[str, Any]]] = None,
        threshold: float = 20.0
    ) -> Dict[str, Any]:
        """
        Phase 25/26: Branch-level Conflict Detection with Trigger Logic.
        """
        conflicts = []
        trigger_nodes = trigger_nodes or []
        
        # 1. Combined Search Space: Natal Nodes + Trigger Nodes
        all_nodes = energy_nodes + trigger_nodes
        
        for i, n1 in enumerate(all_nodes):
            for j, n2 in enumerate(all_nodes):
                if i >= j: continue
                
                # Theory Check: Is this an internal clash or an external trigger?
                is_external = n1.get('is_trigger') or n2.get('is_trigger')
                
                b1 = n1['pillar'][1] if len(n1['pillar']) > 1 else ''
                b2 = n2['pillar'][1] if len(n2['pillar']) > 1 else ''
                
                env1 = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(b1)
                env2 = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(b2)
                
                if env1 and env2:
                    diff = abs(env1['angle'] - env2['angle'])
                    if diff > 180: diff = 360 - diff
                    
                    if abs(diff - 180) < 5.0: # Identifies Chong (冲)
                        # Theoretical Weight: 
                        # Internal Clash = Base
                        # External Trigger (Annual) = 1.5x induction multiplier
                        multiplier = 1.5 if is_external else 1.0
                        impact = 10.0 * (n1['potential'] + n2['potential']) * multiplier
                        
                        conflicts.append({
                            "nodes": (n1.get('index', i), n2.get('index', j)), 
                            "branches": (b1, b2),
                            "impact": impact,
                            "type": "Induction" if is_external else "Structural"
                        })
        
        # 2. Results
        total_thermal_release = sum(c['impact'] for c in conflicts)
        survived = total_thermal_release < threshold
        
        status = "CRITICAL" if not survived else "STABLE"
        
        return {
            "status": status,
            "thermal_release": total_thermal_release,
            "chain_count": len(conflicts),
            "survived": survived,
            "conflicts": conflicts, # Pass list up
            "fragmentation_index": total_thermal_release / (threshold + 1e-6)
        }
