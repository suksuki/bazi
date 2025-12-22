
"""
Quantum Trinity V2.0: The Oracle
================================
Elegant Facade and Orchestrator for the Bazi Physics system.
"""

from typing import List, Dict, Optional, Any
import numpy as np

from .nexus.definitions import PhysicsConstants, BaziParticleNexus
from .physics.wave_laws import WaveState, WaveLaws, PhaseTransitionTheory
from .engines.energy_flux import EnergyFlux
from .engines.resonance_field import ResonanceField, ResonanceProfile
from .intelligence.logic_arbitrator import LogicArbitrator
from .intelligence.quantum_remedy import QuantumRemedy
from .intelligence.deconstructor import Deconstructor

class TrinityOracle:
    """The Single Point of Truth and Analysis Orchestrator."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    def analyze(self, 
                pillars: List[str], 
                day_master: str,
                luck_pillar: Optional[str] = None,
                annual_pillar: Optional[str] = None,
                t: float = 0.0,
                prev_sync: float = 1.0,
                injections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        [UNIFIED V2.0 PIPELINE]
        Logic -> Field Init -> Flux -> Resonance -> Verdict -> Remediation -> Deconstruction
        """
        all_pillars = pillars.copy()
        if luck_pillar: all_pillars.append(luck_pillar)
        if annual_pillar: all_pillars.append(annual_pillar)
        
        # 1. Logic Analysis
        interactions = LogicArbitrator.match_interactions(all_pillars)
        
        # 2. Field Initialization
        initial_waves = LogicArbitrator.initialize_field(all_pillars, day_master)
        
        # 3. Apply Manual Injections (if any)
        if injections:
            for char in injections:
                 for elem in initial_waves:
                      initial_waves[elem] = QuantumRemedy.apply_injection(initial_waves[elem], char)
        
        # 4. Flux Rheology (Energy Flow)
        # Month branch is index 1 of pillars
        month_b = pillars[1][1] if len(pillars) > 1 and len(pillars[1]) > 1 else '寅'
        final_waves = EnergyFlux.simulate_flow(initial_waves, month_b, steps=3)
        
        # 5. Resonance Analysis
        from core.bazi_profile import BaziProfile
        day_p = pillars[2] if len(pillars) > 2 else ""
        voids = BaziProfile.get_void_branches(day_p)
        is_void = month_b in voids
        
        dm_elem, _, _ = BaziParticleNexus.STEMS.get(day_master, ("Earth", "", 0))
        dm_wave = final_waves[dm_elem]
        field_list = [v for k, v in final_waves.items() if k != dm_elem]
        
        resonance = ResonanceField.evaluate_system(dm_wave, field_list, prev_sync=prev_sync, is_void=is_void)
        
        # 6. Verdict (Phase Transition)
        allies = [dm_elem]
        for m, c in PhysicsConstants.GENERATION.items():
            if c == dm_elem: allies.append(m)
            
        allies_energy = sum(final_waves[e].amplitude for e in allies if e in final_waves)
        total_energy = sum(final_waves[e].amplitude for e in final_waves)
        
        order_param = PhaseTransitionTheory.calculate_order_parameter(allies_energy, total_energy)
        
        if resonance.is_follow:
            order_param = -0.95
            label = "Extreme Weak (Follow)"
        else:
            label = PhaseTransitionTheory.map_to_label(order_param)
            
        if resonance.mode == "BEATING":
            label += " (Fake)"

        # 7. Intelligence Layer (Remedy & Deconstruction)
        remedy = None
        if resonance.sync_state < 0.7:
             remedy = QuantumRemedy.find_optimal_remedy(dm_wave, field_list, prev_sync=prev_sync)
             
        breakdown = Deconstructor.simulate_breakdown(dm_wave, field_list, resonance.sync_state)

        return {
            "verdict": {
                "label": label,
                "order_parameter": order_param,
                "score": (allies_energy / total_energy * 100) if total_energy > 0 else 0
            },
            "resonance": resonance,
            "waves": final_waves,
            "interactions": interactions,
            "remedy": remedy,
            "breakdown": breakdown,
            "metadata": {
                "engine": "Quantum Trinity V2.0 Refined",
                "brittleness": resonance.brittleness,
                "void_active": is_void
            }
        }
