
"""
Quantum Trinity V2.0: Resonance & Structural Integrity
======================================================
Unified analyzer for system stability, resonance modes, and patterns.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from ..nexus.definitions import PhysicsConstants
from ..physics.wave_laws import WaveState, WaveLaws

@dataclass
class ResonanceProfile:
    mode: str             # COHERENT, BEATING, DAMPED
    sync_state: float     # Coherence (0.0 - 1.0)
    locking_ratio: float  # Field/DM intensity ratio
    brittleness: float    # Fracture risk
    velocity: float       # Phase transition speed
    is_follow: bool       # Pattern detection
    description: str
    dm_wave: WaveState
    field_waves: List[WaveState]
    envelop_frequency: float = 0.0

class ResonanceField:
    """Analyzes the Bazi as a High-Q Resonant Cavity."""

    @staticmethod
    def evaluate_system(dm_wave: WaveState, 
                        field_waves: List[WaveState], 
                        prev_sync: float = 1.0, 
                        is_void: bool = False) -> ResonanceProfile:
        """
        Comprehensive Stability Analysis.
        """
        # 1. Field Integration
        z_total = sum(w.to_complex() for w in field_waves)
        field_amp = float(np.abs(z_total))
        field_phase = float(np.angle(z_total))
        
        # 2. Resonance Metrics
        locking_ratio = field_amp / max(dm_wave.amplitude, 0.1)
        
        # Phase Matching (Coherence)
        phase_diff = abs(dm_wave.phase - field_phase) % (2 * np.pi)
        if phase_diff > np.pi: phase_diff = 2 * np.pi - phase_diff
        
        # Sync calculation with Void penalty
        sync_state = np.cos(phase_diff / 2.0) ** 2
        if is_void:
            sync_state *= 0.8 # Gravitational leakage
            locking_ratio *= 0.3 # Energy sink
            
        # 3. Mode Determination
        mode = "DAMPED"
        if locking_ratio >= PhysicsConstants.LOCKING_RATIO_CRITICAL:
            if sync_state > PhysicsConstants.SYNC_THRESHOLD_COHERENT:
                mode = "COHERENT"
            elif sync_state > PhysicsConstants.SNR_THRESHOLD_BEATING:
                mode = "BEATING"
        
        # 4. Phase 21-24 Features (Brittleness & Velocity)
        brittleness = 0.0
        if sync_state > PhysicsConstants.BRITTLENESS_COEFF:
            brittleness = (sync_state - PhysicsConstants.BRITTLENESS_COEFF) / (1.0 - PhysicsConstants.BRITTLENESS_COEFF)
            
        dt = 0.1
        velocity = abs(sync_state - prev_sync) / dt
        
        # 5. Pattern Detection
        is_follow = (mode == "COHERENT") and (locking_ratio > 2.0)
        
        desc = f"Resonance: {mode} Mode | Sync: {sync_state:.2f}"
        if is_follow:
            desc += " | 🔥 SUPERCONDUCTING (True Follow)"
        if is_void:
            desc += " | 🕳️ VOID PENALTY ACTIVE"

        # 6. Envelope Frequency (Simplified for V2.0)
        avg_field_phase = float(np.angle(z_total))
        envelop_frequency = abs(dm_wave.phase - avg_field_phase) / np.pi
        
        return ResonanceProfile(
            mode=mode,
            sync_state=sync_state,
            locking_ratio=locking_ratio,
            brittleness=brittleness,
            velocity=velocity,
            is_follow=is_follow,
            description=desc,
            dm_wave=dm_wave,
            field_waves=field_waves,
            envelop_frequency=envelop_frequency
        )
