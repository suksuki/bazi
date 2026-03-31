
"""
Quantum Trinity V2.2: Unified Dynamics Engine
=============================================
Implementation of Capture, Cutting, and Contamination models
as part of the Grand Unified Framework.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from ..physics.wave_laws import WaveState, WaveLaws
from ..nexus.definitions import PhysicsConstants

class GravityCapture:
    """[PH29] Shishen vs Qisha: Momentum absorption and potential conversion."""
    
    @staticmethod
    def calculate_efficiency(output_wave: WaveState, kill_wave: WaveState) -> float:
        if kill_wave.amplitude <= 0: return 1.0
        # Capture efficiency depends on the ratio of output (Eating God) to target (Killings)
        # and phase alignment (should be ~pi apart for maximum neutralization)
        ratio = output_wave.amplitude / kill_wave.amplitude
        phase_diff = abs(output_wave.phase - kill_wave.phase) % (2 * np.pi)
        
        # Optimal neutralization occurs at phase_diff = pi
        neutralization = np.sin(phase_diff / 2.0) # Peaks at pi
        efficiency = np.tanh(ratio * neutralization)
        return float(efficiency)

class SpectralAnalyzer:
    """[PH30] Xiao Shen Duo Shi: Frequency notch filtering and supply interruption."""
    
    @staticmethod
    def calculate_cut_depth(resource_wave: WaveState, output_wave: WaveState, shield_wave: Optional[WaveState] = None) -> float:
        if resource_wave.amplitude <= 0: return 0.0
        # The 'Owl' (Indirect Resource) steals the 'Food' (Eating God)
        # Interaction is 'Control/Destruction', so use Sine of phase diff (Orthogonal/Opposite favored)
        # Phase diff for Fire vs Metal is ~144 deg, sin(72) ~ 0.95 -> High interaction
        overlap = np.sin(abs(resource_wave.phase - output_wave.phase) / 2.0) ** 2
        
        # [PH30-SHIELD] Bi-Jie (Friend/Rob Wealth) intervention
        # In physics, this acts as an impedance shunt or a buffer layer
        shield_efficiency = 0.0
        if shield_wave and shield_wave.amplitude > 1.0:
            # Shielding factor: Bi-Jie absorbs some of the Owl's energy
            # (Yin generates Bi-Jie, Bi-Jie generates Food)
            shield_efficiency = np.tanh(shield_wave.amplitude / max(resource_wave.amplitude, 0.1))
            
        # Increase base sensitivity (Owl is aggressive)
        raw_impact = (resource_wave.amplitude * 1.5) / max(output_wave.amplitude, 0.1)
        cut_depth = 1.0 - np.exp(- raw_impact * overlap)
        
        # Shielding works well if Shield(Earth) connects Fire and Metal
        # Fire->Earth->Metal. This is a "Generative Bridge", highly effective.
        cut_depth *= (1.0 - 0.85 * shield_efficiency)
        
        return float(cut_depth)

class ContaminationModel:
    """[PH31] Cai Xing Huai Yin: Dielectric breakdown and medium pollution."""
    
    @staticmethod
    def calculate_pollution_index(wealth_wave: WaveState, resource_wave: WaveState) -> float:
        if resource_wave.amplitude <= 0: return 0.0
        # Wealth (Cai) attacks Resource (Yin)
        # This reduces the dielectric constant of the resource field, leading to 'leakage'
        impact = wealth_wave.amplitude / max(resource_wave.amplitude, 1.0)
        # Pollution index saturates at 1.0
        pollution = np.tanh(impact * 1.5)
        return float(pollution)

class UnifiedDynamics:
    """Orchestrator for complex interaction clusters."""
    
    @staticmethod
    def run_analysis(waves: Dict[str, WaveState], interactions: List[Dict[str, Any]], day_master: str) -> Dict[str, Any]:
        results = {}
        
        from ..nexus.definitions import BaziParticleNexus, PhysicsConstants
        dm_elem, _, _ = BaziParticleNexus.STEMS.get(day_master, ("Earth", "Yang", 0))
        
        # Resolve Ten Gods (Simplified mapping for elements)
        output_elem = PhysicsConstants.GENERATION[dm_elem]
        resource_elem = None
        for k, v in PhysicsConstants.GENERATION.items():
            if v == dm_elem: resource_elem = k
        control_elem = None
        for k, v in PhysicsConstants.CONTROL.items():
            if v == dm_elem: control_elem = k
        wealth_elem = PhysicsConstants.CONTROL[dm_elem]
        
        # Identify elements based on DM
        # We assume the caller provides these mappings or we find them
        # For simulation, we'll look for specific interaction IDs
        
        for inter in interactions:
            i_id = inter.get("id")
            if i_id == "PH29_01": # CAPTURE
                eff = GravityCapture.calculate_efficiency(waves.get(output_elem), waves.get(control_elem))
                results["capture"] = {"efficiency": eff, "status": "STABLE" if eff > 0.6 else "WARNING"}
            
            elif i_id == "PH29_02": # CUTTING
                shield_wave = waves.get(dm_elem) # Friend/Rob Wealth is the DM's own element
                depth = SpectralAnalyzer.calculate_cut_depth(waves.get(resource_elem), waves.get(output_elem), shield_wave)
                results["cutting"] = {"depth": depth, "status": "CRITICAL" if depth > 0.8 else "STABLE"}
                
            elif i_id == "PH29_03": # CONTAMINATION
                poll = ContaminationModel.calculate_pollution_index(waves.get(wealth_elem), waves.get(resource_elem))
                results["contamination"] = {"index": poll, "status": "LEAKING" if poll > 0.5 else "CLEAR"}
                
        return results
