
"""
Quantum Trinity V2.0: Energy Flux Engine
========================================
Simulates the 'River of Qi' (Energy Rheology) across the Five Elements.
"""

from typing import Dict, List, Optional, Any
import numpy as np
from ..nexus.definitions import PhysicsConstants
from ..physics.wave_laws import WaveState, WaveLaws

class EnergyFlux:
    """The Rheology Engine for Non-Linear Qi Flow."""

    @staticmethod
    def simulate_flow(initial_waves: Dict[str, WaveState], 
                      month_branch: str,
                      steps: int = 3) -> Dict[str, WaveState]:
        """
        Simulates the redistribution of energy across elements via generation/control cycles.
        """
        current = {k: v for k, v in initial_waves.items()}
        
        gen_cycle = PhysicsConstants.GENERATION
        con_cycle = PhysicsConstants.CONTROL
        
        for _ in range(steps):
            next_state = {k: v for k, v in current.items()}
            
            # --- 1. Generation Rheology (Conductive Flow) ---
            for mother, child in gen_cycle.items():
                m_wave = current[mother]
                c_wave = current[child]
                
                if m_wave.amplitude < 0.1: continue
                
                # Conductance depends on relative strength and phase
                # High energy = High pressure -> High flow
                conductance = 0.4 * (m_wave.amplitude / max(c_wave.amplitude, 0.5))
                conductance = np.clip(conductance, 0.1, 0.7)
                
                # Mother generates child (Construction)
                transfer_z = m_wave.to_complex() * conductance
                new_c_z = c_wave.to_complex() + transfer_z
                
                next_state[child] = WaveState.from_complex(new_c_z)
                
                # Energy conservation: Mother loses some energy
                # (Simplified: assume 20% loss for generation effort)
                next_state[mother] = WaveState(next_state[mother].amplitude * 0.9, next_state[mother].phase)

            # --- 2. Control Rheology (Interference Damping) ---
            for controller, subject in con_cycle.items():
                ctl_wave = current[controller]
                sub_wave = current[subject]
                
                if ctl_wave.amplitude < 0.1: continue
                
                # Impedance factor (Phase 13 Inverse Control check)
                impedance = 0.5 if ctl_wave.amplitude > sub_wave.amplitude else 0.2
                
                # Controller dampens subject (Destructive Interference ~180 phase)
                damping_z = ctl_wave.amplitude * impedance * np.exp(1j * (ctl_wave.phase + np.pi))
                new_sub_z = sub_wave.to_complex() + damping_z
                
                next_state[subject] = WaveState.from_complex(new_sub_z)
            
            # Global Saturation Guard
            current = {e: WaveLaws.apply_saturation(w) for e, w in next_state.items()}
            
        return current
