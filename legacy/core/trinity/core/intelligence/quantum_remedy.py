
"""
Quantum Trinity V2.0: Quantum Remedy
====================================
Intelligence layer for prescribing corrective particles (Remediation).
"""

from typing import List, Dict, Optional, Any
import numpy as np
from ..nexus.definitions import PhysicsConstants, BaziParticleNexus
from ..physics.wave_laws import WaveState, WaveLaws
from ..engines.resonance_field import ResonanceField

class QuantumRemedy:
    """The Physician: Prescribes particles to stabilize resonance."""

    @staticmethod
    def find_optimal_remedy(dm_wave: WaveState, 
                           field_list: List[WaveState], 
                           prev_sync: float = 1.0,
                           unified_metrics: Optional[Dict] = None,
                           day_master: str = None) -> Dict[str, Any]:
        """
        Scan all five elements to find which one maximizes the system's sync_state.
        """
        elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
        best_elem = "None"
        max_sync = -1.0
        
        # Base sync
        base_res = ResonanceField.evaluate_system(dm_wave, field_list, prev_sync=prev_sync)
        max_sync = base_res.sync_state
        
        for elem in elements:
            # Create a test injection wave
            test_amp = PhysicsConstants.BASE_SCORE * 2.0 # Strong injection
            test_phase = PhysicsConstants.ELEMENT_PHASES[elem]
            test_wave = WaveState(test_amp, test_phase)
            
            # 1. Subjective Remediation: Inject into DM
            # Using 1:1 coupling for testing
            new_dm = WaveLaws.solve_interference(dm_wave, test_wave, coupling=1.0)
            
            # 2. Objective Remediation: Inject into Field
            new_field = [WaveLaws.solve_interference(w, test_wave, coupling=0.5) for w in field_list]
            
            # Evaluate
            test_res = ResonanceField.evaluate_system(new_dm, new_field, prev_sync=prev_sync)
            
            if test_res.sync_state > max_sync:
                max_sync = test_res.sync_state
                best_elem = elem
        
        if day_master:
             dm_elem, _, _ = BaziParticleNexus.STEMS.get(day_master, ("Earth", "", 0))
        
        # [PH30-SHIELD] Strategic Override for Spectral Cutting
        if unified_metrics and unified_metrics.get('cutting', {}).get('status') == 'CRITICAL':
             # If cutting is critical, Bi-Jie (Same Element) is the mandatory shield
             # forcing the optimizer to prefer DM's element if it provides *reasonable* sync
             if day_master:
                 shield_elem = dm_elem
                 # Check if shield was analyzed (we scanned all elements)
                 # We simply boost the 'best_elem' selection logic or override description
                 if best_elem == shield_elem:
                      pass # Natural convergence
                 else:
                      # If shield provides at least 80% of max_sync, prefer it for structural safety
                      # But here we don't have the sync dict. 
                      # Let's simplify: blindly prioritizing Shield might be safer for User Logic.
                      # Re-evaluate Shield Element explicitly
                      pass 

        # Map element to a specific Particle (Stem)
        particle_map = {
            "Wood": "甲", "Fire": "丙", "Earth": "戊", "Metal": "庚", "Water": "壬"
        }
        
        desc = f"Injection of {best_elem} optimized sync."
        
        # Override for Critical Cutting
        if unified_metrics and unified_metrics.get('cutting', {}).get('status') == 'CRITICAL' and day_master:
            shield_elem = dm_elem
            best_elem = shield_elem # Force Shield
            best_char = particle_map.get(best_elem, "None")
            desc = f"[CRITICAL SHIELD] Injecting {best_char} (Bi-Jie) to shunt Owl God cutting frequency."
        else:
             best_char = particle_map.get(best_elem, "None")
             desc = f"Injection of {best_char}({best_elem}) optimized sync to {max_sync:.2f}"
        return {
            "optimal_element": best_elem,
            "best_particle": best_char,
            "expected_sync": max_sync,
            "improvement": max_sync - base_res.sync_state,
            "description": desc
        }

    @staticmethod
    def apply_injection(wave: WaveState, particle_char: str, coupling: float = 0.5) -> WaveState:
        """Inject a specific Bazi character into a wave field."""
        if particle_char in BaziParticleNexus.STEMS:
            elem, _, _ = BaziParticleNexus.STEMS[particle_char]
            amp = PhysicsConstants.BASE_SCORE
            phase = PhysicsConstants.ELEMENT_PHASES[elem]
            injection = WaveState(amp, phase)
            return WaveLaws.solve_interference(wave, injection, coupling=coupling)
        return wave
