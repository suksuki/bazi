
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from .wave_mechanics import WaveState, InterferenceSolver

@dataclass
class ResonanceResult:
    vibration_mode: str          # COHERENT, BEATING, DAMPED
    sync_state: float            # 0.0 to 1.0 (Effective Synchronization)
    snr: float                   # Signal-to-Noise Ratio (Field Purity)
    locking_ratio: float         # Injection Locking Ratio
    envelop_frequency: float     # For BEATING mode: Δf
    impedance_shift: float       # Change in impedance
    description: str

class ResonanceEngine:
    """
    Quantum Trinity V21.0: Resonance & Frequency Synchronization Engine.
    Models the "Follow" (从格) and "Resonance" phenomena in Bazi waves.
    """
    
    @staticmethod
    def analyze_vibration_mode(
        dm_wave: WaveState, 
        field_waves: List[WaveState],
        config: Optional[Dict] = None
    ) -> ResonanceResult:
        """
        Determines the vibration mode of the Day Master in the background field.
        """
        c = config or {}
        critical_locking = c.get('criticalLockingRatio', 1.0)
        beating_thresh = c.get('beatingThreshold', 0.4)
        coherent_sync = c.get('coherentSyncThreshold', 0.80)
        beating_sync = c.get('beatingSyncThreshold', 0.45)

        # 1. Calculate Signal vs Noise
        # Signal: Elements that match or generate DM
        # Noise: Elements that control or are controlled by DM
        # (Using a simplified heuristic: DM element is signal, all others are noise for now)
        # Better: Sum of 'Friend' elements vs 'Enemy' elements
        
        # Calculate Dominant Field Component
        z_total = sum(w.to_complex() for w in field_waves)
        field_amp = float(np.abs(z_total))
        field_phase = float(np.angle(z_total))
        
        # 2. Vector SNR (Coherence Purity)
        # Sum of individual amplitudes vs amplitude of vector sum
        total_potential = sum(w.amplitude for w in field_waves)
        # SNR = 1.0 means all waves are perfectly in-phase
        snr = field_amp / max(total_potential, 0.1)
        
        # 3. Injection Locking Ratio
        locking_ratio = field_amp / max(dm_wave.amplitude, 0.1)
        
        # 4. Phase Match (Coherence) adjusted by SNR
        # If SNR is low (chaotic field), sync is harder to maintain
        phase_diff = abs(dm_wave.phase - field_phase) % (2 * np.pi)
        if phase_diff > np.pi: phase_diff = 2 * np.pi - phase_diff
        
        # Raw sync
        raw_sync = np.cos(phase_diff / 2.0) ** 2
        
        # Effective Sync: SNR acts as a coherence multiplier
        sync_state = raw_sync * snr
        
        mode = "DAMPED"
        env_f = 0.0
        impedance_shift = 0.0
        desc = ""
        
        # Phase 23 Tuning: Lower capture barrier for Bazi
        if locking_ratio >= critical_locking:
            if sync_state > coherent_sync:
                mode = "COHERENT"
                desc = f"🌟 HIGH-Q RESONANCE (True Follow/Support). SNR={snr:.2f}"
                impedance_shift = -0.8 * sync_state
            elif sync_state > beating_sync:
                mode = "BEATING"
                # Δf is proportional to mismatch and inversely to logic
                env_f = (phase_diff + (1.0 - snr)) / (locking_ratio + 1e-6)
                desc = f"🌀 RESONANCE BEATING (Fake Follow). Env Freq: {env_f:.3f}"
                impedance_shift = -0.4 * sync_state
            else:
                mode = "DAMPED"
                desc = f"📉 FRAGMENTED STATE. Noise Dominance (SNR={snr:.2f})"
                impedance_shift = 0.2
        else:
            mode = "DAMPED"
            desc = "🛡️ INDEPENDENT MODE. Critical locking not achieved."
            impedance_shift = 0.5
            
        return ResonanceResult(
            vibration_mode=mode,
            sync_state=sync_state,
            snr=snr,
            locking_ratio=locking_ratio,
            envelop_frequency=env_f,
            impedance_shift=impedance_shift,
            description=desc
        )

    @staticmethod
    def interference_envelope(t: float, delta_f: float) -> float:
        """
        Quantifies the periodic crisis in BEATING mode.
        Returns a value from 0.0 (Total Collapse/Crisis) to 1.0 (Peak Performance).
        The envelope of two beating waves is given by |cos(Δf * t / 2)|.
        """
        # Periodic crises occur at t = (2n+1) * pi / delta_f
        return float(np.abs(np.cos(delta_f * t / 2.0)))

    @staticmethod
    def solve_resonance_interference(
        dm_wave: WaveState,
        result: ResonanceResult,
        t: float = 0.0,
        config: Optional[Dict] = None
    ) -> WaveState:
        """
        Modifies the DM wave based on the resonance result.
        In COHERENT mode, energy is boosted. In BEATING, it fluctuates.
        """
        c = config or {}
        boost = c.get('superconductiveBoost', 0.5)
        beating_base = c.get('beatingBaseMultiplier', 0.6)
        beating_swing = c.get('beatingAmplitudeSwing', 0.5)

        multiplier = 1.0
        if result.vibration_mode == "COHERENT":
            multiplier = 1.0 + (result.sync_state * boost)
        elif result.vibration_mode == "BEATING":
            # Envelope effect: A = A0 * interference_envelope(t, Δf)
            env = ResonanceEngine.interference_envelope(t, result.envelop_frequency)
            multiplier = beating_base + (beating_swing * env * result.sync_state)
        else:
            multiplier = 0.7 # Damped
            
        return WaveState(
            amplitude=dm_wave.amplitude * multiplier,
            phase=dm_wave.phase,
            frequency=dm_wave.frequency + result.envelop_frequency
        )
