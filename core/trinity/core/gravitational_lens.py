
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from .wave_mechanics import WaveState
from .physics_engine import ParticleDefinitions
from .geophysics import GeoPhysics, GeoFactor

class GravitationalLensEngine:
    """
    Phase 22: Gravitational Lensing & Spatial Remediation.
    Models the "Focusing" of energy by pillars and the "Remediation" by spatial shift.
    """

    @staticmethod
    def calculate_lensing_coefficient(pillar_idx: int) -> float:
        """
        Returns the lensing coefficient (weight) for a given pillar index (0-3).
        Year=0, Month=1, Day=2, Hour=3.
        """
        pillar_names = ['year', 'month', 'day', 'hour']
        if pillar_idx < 0 or pillar_idx >= 4:
            return 1.0
        return ParticleDefinitions.PILLAR_WEIGHTS.get(pillar_names[pillar_idx], 1.0)

    @staticmethod
    def simulate_spatial_repair(
        dm_wave: WaveState,
        field_waves: List[WaveState],
        base_t: float,
        target_frequency: float,
        target_element: str
    ) -> Dict[str, Any]:
        """
        Simulates moving to different geographical locations to fix a phase crisis.
        Searches for a location where K_geo stabilizes the Beating Mode.
        """
        cities = [
            GeoFactor("Hainan (South)", 19.0, 109.0, "Fire Peak"),
            GeoFactor("Singapore (Equator)", 1.0, 103.0, "Absolute Heat"),
            GeoFactor("Harbin (North)", 45.0, 126.0, "Water Core"),
            GeoFactor("Shanghai (East)", 31.0, 121.0, "Wood/Metal Hub"),
            GeoFactor("Chengdu (West)", 30.0, 104.0, "Earth/Metal Support")
        ]

        # We want to boost 'target_element' to increase the synchronization or energy.
        # If we boost the field energy, the locking_ratio increases, potentially stabilizing the system.
        
        remediation_results = []
        
        for city in cities:
            k = GeoPhysics.calculate_k_geo(target_element, city.latitude)
            # Apply boost to the relevant element in the field waves
            # (Simplified: boost the aggregate field amplitude)
            
            # Recalculate Envelope at the crisis point
            # Crisis point is when env is minimum.
            # env = |cos(delta_f * t / 2)|
            # Crisis t = pi / delta_f (for first wave trough)
            
            # The boost increases field strength.
            # locking_ratio = Field_Amp / DM_Amp
            # delta_f = phase_diff / locking_ratio
            
            # We'll calculate the new Env at base_t
            # Let's assume the boost 'k' affects the field amplitude.
            
            field_amp = sum(w.amplitude for w in field_waves)
            new_field_amp = field_amp * k
            
            locking_ratio = new_field_amp / max(dm_wave.amplitude, 0.1)
            # Simplified phase_diff
            phase_diff = 1.0 # Constant for simulation
            new_delta_f = phase_diff / (locking_ratio + 1e-6)
            
            new_env = float(np.abs(np.cos(new_delta_f * base_t / 2.0)))
            
            remediation_results.append({
                "location": city.name,
                "k_geo": k,
                "env_at_t": new_env,
                "locking_ratio": locking_ratio,
                "description": city.description,
                "safety": "🍀 SAFE" if new_env > 0.6 else ("⚠️ WARNING" if new_env > 0.2 else "🔥 CRISIS")
            })

        return {
            "target": target_element,
            "simulated_time": base_t,
            "results": sorted(remediation_results, key=lambda x: x['env_at_t'], reverse=True)
        }

    @staticmethod
    def detect_virtual_centers(bazi: List[str]) -> List[Dict[str, Any]]:
        """
        Detects "Arch Combos" (拱合) or "Ghost Centers" (夹角) that act as virtual引力 centers.
        Example: Shen(申) and You(酉) arch Xu(戌).
        """
        # Mapping branches to angles
        branches = [b[1] for b in bazi if len(b) > 1]
        angles = [ParticleDefinitions.BRANCH_ENVIRONMENTS.get(b, {}).get('angle', 0) for b in branches]
        
        virtual_centers = []
        
        # Check for adjacent branches (30 degrees apart) that might arch a third
        for i in range(len(angles)):
            for j in range(i + 1, len(angles)):
                diff = abs(angles[i] - angles[j])
                if abs(diff - 60) < 5: # Gap of 60 might arch the 30 degree middle
                    mid_angle = (angles[i] + angles[j]) / 2.0
                    if mid_angle > 180 and abs(angles[i] - angles[j]) > 180: # handle wrapping
                        mid_angle = (mid_angle + 180) % 360
                    
                    # Find which branch corresponds to mid_angle
                    for b_name, b_data in ParticleDefinitions.BRANCH_ENVIRONMENTS.items():
                        if abs(b_data['angle'] - mid_angle) < 5:
                            # If this branch is NOT in the bazi, it's a "Virtual center"
                            if b_name not in branches:
                                virtual_centers.append({
                                    "type": "Arch",
                                    "virtual_branch": b_name,
                                    "source": [branches[i], branches[j]],
                                    "strength": 0.5 # Ghost particles have half strength
                                })
                                
        return virtual_centers
