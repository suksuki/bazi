
"""
Quantum Trinity V2.0: Wave Mechanics & Field Laws
=================================================
The mathematical foundation for wave-particle duality in Bazi.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from ..nexus.definitions import PhysicsConstants

@dataclass(frozen=True)
class WaveState:
    """The Fundamental Bazi Particle Waveform."""
    amplitude: float       # Energy Magnitude (E)
    phase: float           # Quantum Phase (θ)
    frequency: float = 1.0 # Oscillation Frequency (ω)

    def to_complex(self) -> complex:
        """Phasor representation: A * exp(jθ)"""
        return self.amplitude * np.exp(1j * self.phase)

    @classmethod
    def from_complex(cls, z: complex) -> 'WaveState':
        """Reconstruct wave from complex vector."""
        return cls(amplitude=float(np.abs(z)), phase=float(np.angle(z)))

    def modulate(self, gain: float, shift: float = 0.0) -> 'WaveState':
        """Active modulation of the waveform."""
        return WaveState(
            amplitude=self.amplitude * gain,
            phase=(self.phase + shift) % (2 * np.pi),
            frequency=self.frequency
        )

class WaveLaws:
    """Universal algorithmic laws for Bazi interference."""

    @staticmethod
    def solve_interference(w1: WaveState, w2: WaveState, coupling: float = 1.0) -> WaveState:
        """Generalized Linear Superposition of Field Waves."""
        z1 = w1.to_complex()
        z2 = w2.to_complex()
        z_res = z1 + (z2 * coupling)
        return WaveState.from_complex(z_res)

    @staticmethod
    def apply_saturation(wave: WaveState, limit: float = 100.0) -> WaveState:
        """Non-linear energy saturation (Sigmoidal Damping)."""
        if wave.amplitude == 0: return wave
        new_amp = limit * np.tanh(wave.amplitude / limit)
        return WaveState(new_amp, wave.phase, wave.frequency)

class CollisionPhysics:
    """High-energy Particle Collision & Annihilation Dynamics."""

    @staticmethod
    def simulate_impact(structure_wave: WaveState, 
                        impact_wave: WaveState, 
                        coherence: float) -> Dict[str, Any]:
        """
        Simulate a collision event between a structure and an external impact (e.g. Clash).
        """
        # Binding Energy: Strengthened by coherence
        # E_bind = structure_amp * coherence^2
        e_bind = structure_wave.amplitude * (coherence ** 2)
        
        # Effective Impact Energy (reduced if phases are semi-aligned, maximized if ~pi apart)
        z1 = structure_wave.to_complex()
        z2 = impact_wave.to_complex()
        
        # Resultant intensity
        z_res = z1 + z2
        res_amp = float(np.abs(z_res))
        
        # If resultant intensity is LOWER than original, it means destruction (Anti-phase)
        is_annihilation = res_amp < structure_wave.amplitude
        destruction_ratio = max(0, 1.0 - (res_amp / structure_wave.amplitude))
        
        survived = True
        if impact_wave.amplitude > e_bind:
             survived = False
             
        # Entropy generation
        entropy = impact_wave.amplitude * (1.0 - coherence) * 2.0
        
        return {
            "survived": survived,
            "annihilation_ratio": destruction_ratio if is_annihilation else 0.0,
            "result_wave": WaveState.from_complex(z_res),
            "entropy": entropy,
            "description": "Structure Collapsed" if not survived else "Structure Vibrating"
        }

    @staticmethod
    def check_total_reflection(internal_e: float, external_e: float) -> bool:
        """Impedance mismatch leading to energy reflection/disruption."""
        if internal_e < 0.1 or external_e < 0.1: return False
        ratio = max(internal_e, external_e) / min(internal_e, external_e)
        return ratio > PhysicsConstants.CRITICAL_IMPEDANCE_RATIO

class PhaseTransitionTheory:
    """Landau-Ginzburg Symmetry Breaking for Bazi Strength."""

    @staticmethod
    def calculate_order_parameter(allies_energy: float, total_energy: float) -> float:
        if total_energy <= 0: return 0.0
        ratio = allies_energy / total_energy
        return (ratio - 0.5) * 2.0

    @staticmethod
    def map_to_label(order_param: float) -> str:
        if order_param > 0.6: return "Extreme Strong"
        if order_param > 0.2: return "Strong"
        if order_param > -0.2: return "Balanced"
        if order_param > -0.6: return "Weak"
        return "Extreme Weak"
