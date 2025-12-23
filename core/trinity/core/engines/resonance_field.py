
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
    flow_efficiency: float = 1.0     # Energy conduction efficiency
    fragmentation_index: float = 0.0 # Ratio of destructive vs constructive nodes

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
            
        # 3. Mode Determination & Phase 28 Annihilation
        mode = "DAMPED"
        if locking_ratio >= PhysicsConstants.LOCKING_RATIO_CRITICAL:
            if sync_state > PhysicsConstants.SYNC_THRESHOLD_COHERENT:
                mode = "COHERENT"
            elif sync_state > PhysicsConstants.SNR_THRESHOLD_BEATING:
                mode = "BEATING"
        
        # New: Annihilation Check (Frequency Incompatibility)
        if sync_state < PhysicsConstants.ANNIHILATION_THRESHOLD:
            # Phase 28: Shang Guan Shang Jin (Vacuum Free State)
            # If the Official is effectively 'stripped' or absent, transition to Superfluid
            is_shang_jin = False
            # We need to know which elements are which relative to DM.
            # For now, if sync is extremely low but fragmentation is very low, it might be a vacuum state.
            # But let's use a simpler heuristic: if mode remains ANNIHILATION but user wants Superfluid,
            # we check if control element is below a certain ratio.
            mode = "ANNIHILATION"
        
        # 4. Phase 21-24 Features (Brittleness & Velocity)
        brittleness = 0.0
        if sync_state > PhysicsConstants.BRITTLENESS_COEFF:
            brittleness = (sync_state - PhysicsConstants.BRITTLENESS_COEFF) / (1.0 - PhysicsConstants.BRITTLENESS_COEFF)
            
        dt = 0.1
        velocity = abs(sync_state - prev_sync) / dt
        
        # Fragmentation Index (H2: Phase dispersion)
        all_waves = [dm_wave] + field_waves
        # Increase threshold to filter out tiny noise elements
        active_waves = [w for w in all_waves if w.amplitude > 1.0]
        phases = [w.phase for w in active_waves]
        if len(phases) > 1:
            # Normalized phase standard deviation
            fragmentation_index = np.std(phases) / np.pi
        else:
            fragmentation_index = 0.0

        # 5. Pattern Detection
        # A 'True Follow' must be Coherent, strong enough, AND have low fragmentation (unified field)
        is_follow = (mode == "COHERENT") and (locking_ratio > 2.0) and (fragmentation_index < 0.25)
        
        # Mode descriptions in bilingual format
        mode_names = {
            "COHERENT": "相干锁定 (Coherent)",
            "BEATING": "拍频摆动 (Beating)", 
            "DAMPED": "阻尼衰减 (Damped)",
            "ANNIHILATION": "湮灭失相 (Annihilation)"
        }
        
        sync_desc = "高" if sync_state > 0.7 else "中" if sync_state > 0.4 else "低"
        desc = f"共振模式: {mode_names.get(mode, mode)} | 同步度 (Sync): {sync_state:.2f} ({sync_desc})"
        
        if is_follow:
            desc += " | 🔥 超导锁定 (True Follow)"
        if is_void:
            desc += " | 🕳️ 空亡减益 (Void Penalty)"

        # 6. Envelope & Phase 28 Flow Metrics
        avg_field_phase = float(np.angle(z_total))
        envelop_frequency = abs(dm_wave.phase - avg_field_phase) / np.pi
        
        # Flow Efficiency (H1: Based on Sync and Mode)
        flow_efficiency = sync_state * (2.0 if is_follow else 1.0)
        if mode == "ANNIHILATION": flow_efficiency *= 0.1
        
        # [MOVED UP] Fragmentation Index (H2: Phase dispersion)
            
        # 7. Pattern Transitions (Phase 28)
        if mode == "ANNIHILATION" and fragmentation_index < 0.15:
            # This is a unified anti-phase field (e.g. Shang Guan Shang Jin)
            # Actually, if it's unified output without Guan, it's a Follow state
            mode = "COHERENT"
            desc = "共振模式: 相干锁定 (Coherent) - 超流态/真空自由 (Superfluid/Vacuum Free)"
            flow_efficiency = 2.5 # Peak efficiency
        
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
            envelop_frequency=envelop_frequency,
            flow_efficiency=flow_efficiency,
            fragmentation_index=fragmentation_index
        )
