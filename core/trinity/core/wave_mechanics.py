"""
Quantum Trinity V14.0: Wave Mechanics Engine
============================================
Fundamental physics layer for complex impedance, phase interference, 
and non-linear energy transmission.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from .math_engine import ProbValue

@dataclass
class WaveState:
    """Represents a five-element wave in the complex plane."""
    amplitude: float       # E (Energy level)
    phase: float           # θ (Phase angle in radians, 0 to 2π)
    frequency: float = 1.0 # ω (Base frequency, default 1.0)
    
    def to_complex(self) -> complex:
        """Convert to Phasor representation: A * exp(jθ)"""
        return self.amplitude * np.exp(1j * self.phase)
    
    @classmethod
    def from_complex(cls, z: complex) -> 'WaveState':
        """Convert from Phasor back to WaveState"""
        return cls(amplitude=float(np.abs(z)), phase=float(np.angle(z)))

class ImpedanceModel:
    """
    Complex Impedance Calculator: Z = R + jX
    R: Resistance (Static damping/entropy)
    X: Reactance (Phase-induced storage/rejection)
    """
    
    # Interaction Phase Shifts (Legacy mapping to wave space)
    PHASE_MAP = {
        'Generation': 0.0,             # In-phase (Constructive)
        'Control': np.pi,               # Counter-phase (Destructive)
        'Draining': -np.pi / 4,         # Backward lag
        'Clash': np.pi * 0.9,           # Near-destructive interference
        'Harmony': np.pi / 12,          # Slight phase shift toward resonance
    }

    @staticmethod
    def calculate_transmission(source: WaveState, target_impedance: complex) -> complex:
        """
        Generalized Ohm's Law for Five-Element Flux: 
        I = V / Z -> Flow = Energy / Impedance
        """
        v_phasor = source.to_complex()
        # Impedance acts as a complex filter
        i_phasor = v_phasor / target_impedance
        return i_phasor

class InterferenceSolver:
    """
    Solves for wave interference (Constructive/Destructive)
    Uses the law of cosines in the complex plane:
    |W|^2 = |A|^2 + |B|^2 + 2|A||B|cos(Δθ)
    """
    
    @staticmethod
    def solve_interference(w1: WaveState, w2: WaveState, coupling: float = 1.0, 
                           saturation: float = 100.0, threshold: float = 0.5) -> WaveState:
        """
        Combines two waves with a specific coupling factor, saturation, and threshold.
        """
        z1 = w1.to_complex()
        
        # Threshold Gating: Only excite if w2 is strong enough
        actual_coupling = coupling if w2.amplitude > threshold else 0.0
        z2 = w2.to_complex()
        
        # Superposition
        z_res = z1 + (z2 * actual_coupling)
        
        # Soft Saturation (Tanh-based)
        amp = float(np.abs(z_res))
        phase = float(np.angle(z_res))
        
        # Nonlinear gain: G(x) = saturation * tanh(x / saturation)
        saturated_amp = saturation * np.tanh(amp / saturation)
        
        return WaveState(amplitude=saturated_amp, phase=phase)

    @staticmethod
    def apply_phase_shift(w: WaveState, delta_theta: float) -> WaveState:
        """Apply a manual phase shift to a wave"""
        new_phase = (w.phase + delta_theta) % (2 * np.pi)
        return WaveState(w.amplitude, new_phase, w.frequency)

class PhaseTransitionEngine:
    """
    Landau Phase Transition Model for Bazi Strength Judgment.
    Determines if the 'Self' wave has collapsed into a 'Strong' or 'Weak' state.
    """
    
    @staticmethod
    def calculate_order_parameter(dm_energy: float, total_energy: float) -> float:
        """
        Calculates the order parameter (η) for the strength phase.
        η near 1.0 -> Fully collapsed (Extreme Strong/Weak)
        η near 0.0 -> Critical point (Balanced/Chaos)
        """
        if total_energy == 0: return 0.0
        ratio = dm_energy / total_energy
        # Landau transition centered at 0.5
        return float(np.tanh((ratio - 0.5) * 4.0))

    @staticmethod
    def collapse_to_label(order_param: float) -> str:
        """Map order parameter to categorical label"""
        if order_param > 0.9: return "Extreme Strong"
        if order_param > 0.4: return "Strong"
        if order_param < -0.9: return "Extreme Weak" # Or "Follow" depending on context
        if order_param < -0.4: return "Weak"
        return "Balanced"
class ModulationEngine:
    """
    Handles carrier-modulation relationships between Bazi components.
    Carrier: Month (A1) - Base energy environment.
    Modulation: Twelve Life Stages (A4) - Modulates the frequency/phase 
               of the stem wave based on the branch.
    """
    
    @staticmethod
    def modulate(carrier: WaveState, stage_factor: float) -> WaveState:
        """
        Applies frequency/amplitude modulation.
        Stage factor mapping: 
        Long Sheng (Birth) -> High Resonance Q
        Si/Jue (Dead/Extinction) -> High Damping
        """
        # A4 modulates the carrier's amplitude and phase
        new_amplitude = carrier.amplitude * stage_factor
        # Simplified phase shift: active stages advance phase, dormant stages lag
        phase_shift = (stage_factor - 1.0) * (np.pi / 6)
        return WaveState(new_amplitude, (carrier.phase + phase_shift) % (2*np.pi))
