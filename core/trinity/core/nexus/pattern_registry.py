
"""
Pattern Registry (ASE Phase 5)
=============================
Stores learned physical constants and failure thresholds 
extracted from population-scale simulations.
"""

class PatternRegistry:
    # --- SGJG (Shang Guan Jian Guan) Refined Constants ---
    # Learned from 20,988 high-purity samples
    SGJG_CONST = {
        "BREAKING_MODULUS": 1.25,        # Threshold for SAI singularity
        "DAMPING_SENSITIVITY": 0.88,      # Resistance to damping agents
        "ISOLATION_EFFICIENCY": 0.15,    # Protection efficiency of Cai buffer
        "PHASE_COHERENCE_LIMIT": 0.12    # Min coherence before structural collapse
    }
    
    # --- PGB (PGB Branded Tracks) ---
    PGB_SUPER_FLUID = {
        "FRICTION_THRESHOLD": 0.05,
        "ENERGY_GAIN_COEFF": 1.5
    }
    
    # [V14.0.9] Stress Buffer (Exceptions to 1.25 Rule)
    PGB_STRESS_BUFFER = {
        "REINFORCEMENT_GAIN": 0.35, # Decreases SAI by 35%
        "FINGERPRINTS": [
            "SHANG_GUAN_HE_SHA", # 伤官合杀: Stress diversion
            "YIN_XING_HUA_SHA"   # 印星化杀: Stress absorption
        ]
    }

    PGB_BRITTLE_TITAN = {
        "MODULUS_OF_RIGIDITY": 4.5,
        "BRITTLE_TRANSITION": 0.75
    }

    @classmethod
    def update_const(cls, pattern_id: str, key: str, value: float):
        if pattern_id == "SHANG_GUAN_JIAN_GUAN":
            cls.SGJG_CONST[key] = value
        elif pattern_id == "PGB_SUPER_FLUID":
            cls.PGB_SUPER_FLUID[key] = value
        elif pattern_id == "PGB_BRITTLE_TITAN":
            cls.PGB_BRITTLE_TITAN[key] = value
