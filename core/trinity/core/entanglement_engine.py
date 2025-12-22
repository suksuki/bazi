
import numpy as np
from typing import Dict, List, Optional, Any
from .wave_mechanics import WaveState, InterferenceSolver
from .physics_engine import ParticleDefinitions

class EntanglementEngine:
    """
    Phase 23: Quantum Entanglement Remediation.
    Models the injection of external particles (Colors, Actions, Objects) 
    as persistent interference signals.
    """

    PARTICLE_MAP = {
        "Black/Blue": "Water",
        "Green/Cyan": "Wood",
        "Red/Purple": "Fire",
        "Yellow/Brown": "Earth",
        "White/Gold": "Metal"
    }

    @staticmethod
    def inject_particle(
        dm_wave: WaveState,
        particle_type: str,
        coupling: float = 0.2
    ) -> WaveState:
        """
        Injects an external particle wave into the Day Master's state.
        coupling: 0.0 to 1.0 (Strength of intervention)
        """
        # Phase 27: Enhanced mapping to support Branch damping
        element = EntanglementEngine.PARTICLE_MAP.get(particle_type)
        if not element:
            # Try Branch map (for Phase 27 Reorg)
            element = EntanglementEngine.BRANCH_MAP.get(particle_type, "Earth")
            
        target_phase = ParticleDefinitions.ELEMENT_PHASES.get(element, 0.0)
        
        # Create the intervention wave
        # Amplitude is proportional to coupling
        intervention_wave = WaveState(amplitude=coupling * 5.0, phase=target_phase)
        
        # Entangle: Use high-coherence interference to force phase alignment
        # This represents the 'Mantra' or 'Remediation' effect
        return InterferenceSolver.solve_interference(dm_wave, intervention_wave, coupling=1.0)

    @staticmethod
    def find_optimal_injection(
        dm_wave_original: WaveState,
        field_waves: List[WaveState],
        t: float = 0.0,
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Phase 24: Auto-Remediation Search.
        Scans across all particle types to find the one that maximizes stability.
        """
        from .resonance_engine import ResonanceEngine
        
        best_particle = None
        max_envelope = -1.0
        best_result = None
        
        # Test each particle type
        for p_name in EntanglementEngine.PARTICLE_MAP.keys():
            # Simulated Injection
            injected_dm = EntanglementEngine.inject_particle(dm_wave_original, p_name, coupling=0.5)
            
            # Evaluate result
            res = ResonanceEngine.analyze_vibration_mode(injected_dm, field_waves, config=config)
            
            # Metric: If Beating, maximize envelope at time t. If Coherent, maximize sync_state.
            current_metric = 0.0
            if res.vibration_mode == "BEATING":
                current_metric = ResonanceEngine.interference_envelope(t, res.envelop_frequency)
            elif res.vibration_mode == "COHERENT":
                current_metric = 1.0 + res.sync_state # Coherent is always preferred
            else:
                # DAMPED: Use sync_state as primary metric to move towards order
                current_metric = res.sync_state
            
            if current_metric > max_envelope:
                max_envelope = current_metric
                best_particle = p_name
                best_result = res
                
        return {
            "best_particle": best_particle,
            "metric": max_envelope,
            "resonance": best_result
        }

    @staticmethod
    def calculate_snr_remedy(
        dm_wave: WaveState,
        field_waves: List[WaveState],
        target_mode: str = "COHERENT"
    ) -> Dict[str, Any]:
        """
        Phase 24: Active SNR Filtering.
        Identifies noise components in the field and calculates the optimal
        counter-wave (Filtering Charge) to suppress interference.
        """
        from .resonance_engine import ResonanceEngine
        
        # 1. Identify Target Phase (The dominant trend we want to follow)
        z_field = sum(w.to_complex() for w in field_waves)
        target_phase = float(np.angle(z_field))
        
        # 2. Identify Noise Elements
        noise_map = {}
        for i, w in enumerate(field_waves):
            # If wave phase is more than π/2 away from target, it's destructive noise
            phase_diff = abs(w.phase - target_phase) % (2 * np.pi)
            if phase_diff > np.pi: phase_diff = 2 * np.pi - phase_diff
            
            if phase_diff > np.pi / 3: # Greater than 60 degrees is noise
                noise_map[i] = w.amplitude
                
        # 3. Calculate Filtering Charge
        # Optimal intervention is usually the 'Control' element of the Noise
        # or simply boosting the Target phase to overwhelm noise
        candidates = list(EntanglementEngine.PARTICLE_MAP.keys())
        best_snr_particle = None
        max_snr = 0.0
        
        for p_name in candidates:
            temp_dm = EntanglementEngine.inject_particle(dm_wave, p_name, coupling=0.6)
            res = ResonanceEngine.analyze_vibration_mode(temp_dm, field_waves)
            
            # Using SNR as the primary optimization metric
            # ResonanceEngine needs to return SNR in its result for this to be perfect
            # For now we use sync_state as a proxy for SNR-adjusted coherence
            if res.sync_state > max_snr:
                max_snr = res.sync_state
                best_snr_particle = p_name
                
        return {
            "remedy_particle": best_snr_particle,
            "predicted_snr": max_snr,
            "target_phase": target_phase,
            "noise_count": len(noise_map)
        }

    @staticmethod
    def apply_active_filtering(
        field_waves: List[WaveState],
        particle_type: str,
        coupling: float = 0.3
    ) -> List[WaveState]:
        """
        Phase 24: Active Field Filtering.
        Modifies the environment (field_waves) by injecting an interference signal 
        that suppresses noise.
        """
        element = EntanglementEngine.PARTICLE_MAP.get(particle_type, "Earth")
        target_phase = ParticleDefinitions.ELEMENT_PHASES.get(element, 0.0)
        
        # In a real scenario, the filtering particle would interact with 
        # all waves in the field.
        new_field = []
        for w in field_waves:
            # If the injected element 'Controls' the field element, it acts as a filter
            # (Simplified: just add the wave and let superposition handle it)
            # Actually, to 'Filter', we want to purposefully interfere with noise
            
            # Create a filtering wave for THIS specific element in the field
            # (This is more like environmental remediation)
            f_wave = WaveState(amplitude=coupling * 2.0, phase=target_phase)
            new_w = InterferenceSolver.solve_interference(w, f_wave, coupling=1.0)
            new_field.append(new_w)
            
        return new_field

    @staticmethod
    def scan_stability_cycle(
        engine: Any,
        bazi: List[str],
        dm: str,
        month: str,
        steps: int = 50,
        t_max: float = 100.0,
        injections: Optional[List[str]] = None
    ) -> List[Dict[str, float]]:
        """
        Phase 25: Spacetime Cycle Scanning.
        Generates a timeline of stability metrics (Sync, Envelope) across a range of t.
        """
        from .resonance_engine import ResonanceEngine
        
        timeline = []
        t_vals = np.linspace(0, t_max, steps)
        
        for t in t_vals:
            res = engine.analyze_bazi(bazi, dm, month, t=float(t), injections=injections)
            resonance = res.get('resonance_state')
            report = resonance.resonance_report
            
            env = 1.0
            if report.vibration_mode == "BEATING":
                env = ResonanceEngine.interference_envelope(float(t), report.envelop_frequency)
            
            timeline.append({
                "t": float(t),
                "sync": float(report.sync_state),
                "env": float(env),
                "stability": float(report.sync_state * env)
            })
            
        return timeline
