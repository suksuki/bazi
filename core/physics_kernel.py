"""
Antigravity Physics Kernel V32.0 - First Principles Model
==========================================================

CRITICAL: All parameters are VARIABLES, not constants.
They MUST be tunable via configuration and data regression.

Based on 12 Core Definitions:
1. Physics Base (Yin/Yang as Spin, 5 Elements as Vector Fields)
2. Particle Phases (Stems as Waveforms, Branches as Field Environments)
3. Structure Algorithm (Shell-Core Model with tunable ratios)
4. Geometric Interaction (Phase Angles and Resonance)
5. Dynamics & Work (Rooting, Projection, Energy Flow)
6. Spacetime System (Da Yun as Background, Liu Nian as Trigger)
7. Spatial Correction (Geo-modifiers)
8. Probability Calculation (Wave Function)
9. Evolution Mechanism (Parameter Tuning Interface)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import os


class PhysicsParameters:
    """
    Centralized parameter store for ALL physics constants.
    All values are tunable and can be loaded from config or optimized via regression.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize physics parameters.
        
        Args:
            config_path: Path to JSON config file. If None, use defaults.
        """
        # Load from config or use defaults
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                params = json.load(f)
            self._load_from_dict(params)
        else:
            self._init_defaults()
    
    def _init_defaults(self):
        """Initialize default parameters (subject to tuning)"""
        
        # ========== 3. Structure Algorithm ==========
        # Hidden Stems ratios (Shell-Core Model)
        # NOTE: These are INITIAL values, must be optimized
        self.hidden_stems_ratios = {
            "子": {"癸": 1.0},
            "丑": {"己": 0.60, "癸": 0.30, "辛": 0.10},
            "寅": {"甲": 0.60, "丙": 0.30, "戊": 0.10},
            "卯": {"乙": 1.0},
            "辰": {"戊": 0.60, "乙": 0.30, "癸": 0.10},
            "巳": {"丙": 0.60, "戊": 0.30, "庚": 0.10},
            "午": {"丁": 0.70, "己": 0.30},
            "未": {"己": 0.60, "丁": 0.30, "乙": 0.10},
            "申": {"庚": 0.60, "壬": 0.30, "戊": 0.10},
            "酉": {"辛": 1.0},
            "戌": {"戊": 0.60, "辛": 0.30, "丁": 0.10},
            "亥": {"壬": 0.70, "甲": 0.30}
        }
        
        # ========== 4. Geometric Interaction ==========
        # Phase angle thresholds (degrees)
        self.angle_chong = 180.0      # Collision/Annihilation
        self.angle_sanhe = 120.0      # Phase Locking/Resonance
        self.angle_liuhe = 60.0       # Combination
        self.angle_xing = 90.0        # Shear Stress
        self.angle_tolerance = 5.0    # Tolerance for angle matching
        
        # Interaction strength coefficients
        self.chong_energy_release = 0.8    # Energy released in collision
        self.sanhe_resonance_boost = 1.5   # Resonance amplification
        self.liuhe_binding_strength = 1.2  # Combination binding
        self.xing_friction_loss = 0.3      # Shear stress loss
        
        # ========== 5. Dynamics & Work ==========
        # Rooting and Projection coefficients
        self.rooting_base_strength = 1.0
        self.rooting_distance_decay = 2.0  # 1/D^N power law
        self.projection_efficiency = 0.8
        
        # Energy flow parameters
        self.sheng_transfer_efficiency = 0.7  # Generation cycle efficiency
        self.ke_resistance_factor = 0.5       # Controlling cycle resistance
        self.distance_decay_exponent = 2.0    # 1/D^N
        
        # Work formula coefficients
        self.work_energy_coefficient = 1.0
        self.work_efficiency_base = 1.0
        
        # ========== 6. Spacetime System ==========
        # Da Yun (Static Background) modifiers
        self.dayun_field_strength = 1.0
        self.dayun_constant_rewrite_factor = 0.5
        
        # Liu Nian (Dynamic Trigger) modifiers
        self.liunian_impact_strength = 1.2
        self.liunian_trigger_threshold = 0.3
        
        # ========== 7. Spatial Correction ==========
        # Geographic modifiers (K_geo)
        self.latitude_temperature_coefficient = 0.01   # Per degree
        self.longitude_phase_shift = 0.0               # Time zone effect
        self.terrain_humidity_modifier = {
            "coastal": 1.2,
            "inland": 1.0,
            "desert": 0.7,
            "mountain": 0.9
        }
        
        # ========== 8. Probability Calculation ==========
        # Wave function parameters
        self.wavefunction_uncertainty_base = 10.0
        self.probability_threshold_high = 0.7
        self.probability_threshold_low = 0.3
        
        # ========== Position Weights ==========
        # Pillar importance (must sum to 1.0)
        self.position_weights = {
            "year": 0.15,
            "month": 0.45,  # Thermodynamic baseline
            "day": 0.15,
            "hour": 0.25
        }
        
        # ========== Spin (Yin/Yang) Modifiers ==========
        # Yang = Divergent (+), Yin = Convergent (-)
        self.yang_divergence_factor = 1.2
        self.yin_convergence_factor = 0.8
    
    def _load_from_dict(self, params: dict):
        """Load parameters from dictionary (handles nested JSON structure)"""
        # First initialize defaults
        self._init_defaults()
        
        # Then override with loaded values
        # Handle nested structure from JSON config
        if 'structure_algorithm' in params:
            struct = params['structure_algorithm']
            if 'hidden_stems_ratios' in struct:
                self.hidden_stems_ratios = struct['hidden_stems_ratios']
        
        if 'geometric_interaction' in params:
            geo = params['geometric_interaction']
            for key in ['angle_chong', 'angle_sanhe', 'angle_liuhe', 'angle_xing', 'angle_tolerance']:
                if key in geo:
                    setattr(self, key, geo[key])
            if 'interaction_strengths' in geo:
                strengths = geo['interaction_strengths']
                for key, value in strengths.items():
                    setattr(self, key, value)
        
        if 'dynamics_and_work' in params:
            dyn = params['dynamics_and_work']
            if 'rooting' in dyn:
                for key, value in dyn['rooting'].items():
                    setattr(self, f'rooting_{key}', value)
            if 'projection' in dyn:
                for key, value in dyn['projection'].items():
                    setattr(self, f'projection_{key}', value)
            if 'energy_flow' in dyn:
                for key, value in dyn['energy_flow'].items():
                    setattr(self, key, value)
            if 'work_formula' in dyn:
                for key, value in dyn['work_formula'].items():
                    setattr(self, f'work_{key}', value)
        
        if 'spacetime_system' in params:
            st = params['spacetime_system']
            if 'dayun' in st:
                for key, value in st['dayun'].items():
                    setattr(self, f'dayun_{key}', value)
            if 'liunian' in st:
                for key, value in st['liunian'].items():
                    setattr(self, f'liunian_{key}', value)
        
        if 'spatial_correction' in params:
            spatial = params['spatial_correction']
            for key in ['latitude_temperature_coefficient', 'longitude_phase_shift', 'terrain_humidity_modifier']:
                if key in spatial:
                    setattr(self, key, spatial[key])
        
        if 'probability_calculation' in params:
            prob = params['probability_calculation']
            for key, value in prob.items():
                setattr(self, key, value)
        
        if 'position_weights' in params:
            self.position_weights = params['position_weights']
        
        if 'spin_modifiers' in params:
            spin = params['spin_modifiers']
            for key, value in spin.items():
                setattr(self, key, value)

    
    def save_to_file(self, path: str):
        """Save current parameters to JSON file"""
        params = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
    
    def update_parameter(self, param_name: str, value):
        """Update a single parameter (for optimization)"""
        if hasattr(self, param_name):
            setattr(self, param_name, value)
        else:
            raise ValueError(f"Unknown parameter: {param_name}")


class ParticleDefinitions:
    """
    Definition 1 & 2: Physics Base and Particle Phases
    
    - Yin/Yang as Spin (divergent/convergent)
    - 5 Elements as Vector Fields
    - Stems as Waveforms (10 types)
    - Branches as Field Environments (12 types)
    """
    
    # ========== 1. Physics Base ==========
    SPIN = {
        "Yang": +1,  # Divergent
        "Yin": -1    # Convergent
    }
    
    VECTOR_FIELDS = {
        "Wood": np.array([1, 0, 0, 0, 0]),   # Basis vector
        "Fire": np.array([0, 1, 0, 0, 0]),
        "Earth": np.array([0, 0, 1, 0, 0]),
        "Metal": np.array([0, 0, 0, 1, 0]),
        "Water": np.array([0, 0, 0, 0, 1])
    }
    
    # Generation cycle (Sheng) - Energy transfer direction
    GENERATION_CYCLE = {
        "Wood": "Fire",
        "Fire": "Earth",
        "Earth": "Metal",
        "Metal": "Water",
        "Water": "Wood"
    }
    
    # Control cycle (Ke) - Vector opposition
    CONTROL_CYCLE = {
        "Wood": "Earth",
        "Earth": "Water",
        "Water": "Fire",
        "Fire": "Metal",
        "Metal": "Wood"
    }
    
    # ========== 2. Particle Phases ==========
    
    # Stems - Waveforms (天干波形态)
    STEM_WAVEFORMS = {
        "甲": {
            "element": "Wood",
            "polarity": "Yang",
            "waveform": "Vertical Pulse",
            "description": "Tension/Tree",
            "spin": +1,
            "hetu_number": 1
        },
        "乙": {
            "element": "Wood",
            "polarity": "Yin",
            "waveform": "Horizontal Network",
            "description": "Network/Grass",
            "spin": -1,
            "hetu_number": 2
        },
        "丙": {
            "element": "Fire",
            "polarity": "Yang",
            "waveform": "Omnidirectional Radiation",
            "description": "Radiation/Sun",
            "spin": +1,
            "hetu_number": 3
        },
        "丁": {
            "element": "Fire",
            "polarity": "Yin",
            "waveform": "Focused Laser",
            "description": "Laser/Candle",
            "spin": -1,
            "hetu_number": 4
        },
        "戊": {
            "element": "Earth",
            "polarity": "Yang",
            "waveform": "High Density Mass",
            "description": "Mass/Mountain",
            "spin": +1,
            "hetu_number": 5
        },
        "己": {
            "element": "Earth",
            "polarity": "Yin",
            "waveform": "Porous Matrix",
            "description": "Matrix/Soil",
            "spin": -1,
            "hetu_number": 6
        },
        "庚": {
            "element": "Metal",
            "polarity": "Yang",
            "waveform": "Rough Impact",
            "description": "Impact/Ore",
            "spin": +1,
            "hetu_number": 7
        },
        "辛": {
            "element": "Metal",
            "polarity": "Yin",
            "waveform": "Precision Crystal",
            "description": "Crystal/Jewelry",
            "spin": -1,
            "hetu_number": 8
        },
        "壬": {
            "element": "Water",
            "polarity": "Yang",
            "waveform": "Momentum Fluid",
            "description": "Momentum/Tsunami",
            "spin": +1,
            "hetu_number": 9
        },
        "癸": {
            "element": "Water",
            "polarity": "Yin",
            "waveform": "Permeability Field",
            "description": "Permeability/Mist",
            "spin": -1,
            "hetu_number": 10
        }
    }
    
    # Branches - Field Environments (地支场域环境)
    BRANCH_ENVIRONMENTS = {
        "子": {
            "element": "Water",
            "environment": "Polar Abyss",
            "description": "Extreme Cold Depth",
            "phase_angle": 0,
            "season": "Winter Peak"
        },
        "丑": {
            "element": "Earth",
            "environment": "Frozen Soil",
            "description": "Frozen Soil/Metal Vault",
            "phase_angle": 30,
            "season": "Winter End"
        },
        "寅": {
            "element": "Wood",
            "environment": "Accelerator Reactor",
            "description": "Rapid Reaction Chamber",
            "phase_angle": 60,
            "season": "Spring Begin"
        },
        "卯": {
            "element": "Wood",
            "environment": "Life Density Field",
            "description": "Dense Jungle",
            "phase_angle": 90,
            "season": "Spring Peak"
        },
        "辰": {
            "element": "Earth",
            "environment": "Reservoir",
            "description": "Water Reservoir/Wet Earth",
            "phase_angle": 120,
            "season": "Spring End"
        },
        "巳": {
            "element": "Fire",
            "environment": "Magnetic Bottle",
            "description": "Magnetic Confinement",
            "phase_angle": 150,
            "season": "Summer Begin"
        },
        "午": {
            "element": "Fire",
            "environment": "Thermal Furnace",
            "description": "Peak Radiation",
            "phase_angle": 180,
            "season": "Summer Peak"
        },
        "未": {
            "element": "Earth",
            "environment": "Desert",
            "description": "Dry Earth/Wood Vault",
            "phase_angle": 210,
            "season": "Summer End"
        },
        "申": {
            "element": "Metal",
            "environment": "Mineral Vein",
            "description": "Metal Ore Deposit",
            "phase_angle": 240,
            "season": "Autumn Begin"
        },
        "酉": {
            "element": "Metal",
            "environment": "Pure Crystal Field",
            "description": "Perfect Blade",
            "phase_angle": 270,
            "season": "Autumn Peak"
        },
        "戌": {
            "element": "Earth",
            "environment": "Volcano",
            "description": "Fire Vault/High Pressure",
            "phase_angle": 300,
            "season": "Autumn End"
        },
        "亥": {
            "element": "Water",
            "environment": "Primordial Ocean",
            "description": "Original Soup",
            "phase_angle": 330,
            "season": "Winter Begin"
        }
    }
    
    @staticmethod
    def get_stem_properties(char: str) -> dict:
        """Get stem waveform properties"""
        return ParticleDefinitions.STEM_WAVEFORMS.get(char, {})
    
    @staticmethod
    def get_branch_properties(char: str) -> dict:
        """Get branch environment properties"""
        return ParticleDefinitions.BRANCH_ENVIRONMENTS.get(char, {})
    
    @staticmethod
    def get_element_vector(element: str) -> np.ndarray:
        """Get element as vector field"""
        return ParticleDefinitions.VECTOR_FIELDS.get(element, np.zeros(5))


class GeometricInteraction:
    """
    Definition 4: Geometric Interaction Algorithm
    
    Based on phase angles (12 Zodiac positions) and Hetu resonance.
    """
    
    def __init__(self, params: PhysicsParameters):
        self.params = params
    
    def get_phase_angle(self, char: str) -> float:
        """Get phase angle for a branch character"""
        props = ParticleDefinitions.get_branch_properties(char)
        return props.get('phase_angle', 0.0)
    
    def calculate_angular_difference(self, char1: str, char2: str) -> float:
        """
        Calculate shortest arc difference on 360° circle.
        
        Returns:
            Angular difference in degrees (0-180)
        """
        angle1 = self.get_phase_angle(char1)
        angle2 = self.get_phase_angle(char2)
        
        diff = abs(angle1 - angle2)
        if diff > 180:
            diff = 360 - diff
        
        return diff
    
    def identify_interaction(self, char1: str, char2: str) -> Optional[Dict]:
        """
        Identify geometric interaction type based on phase angles.
        
        Returns:
            dict with 'type', 'angle', 'strength', or None if no interaction
        """
        angle_diff = self.calculate_angular_difference(char1, char2)
        tolerance = self.params.angle_tolerance
        
        # Check each interaction type
        if abs(angle_diff - self.params.angle_chong) < tolerance:
            return {
                'type': 'Chong',
                'angle': 180,
                'strength': self.params.chong_energy_release,
                'description': 'Collision/Annihilation'
            }
        
        elif abs(angle_diff - self.params.angle_sanhe) < tolerance:
            return {
                'type': 'SanHe',
                'angle': 120,
                'strength': self.params.sanhe_resonance_boost,
                'description': 'Phase Locking/Resonance'
            }
        
        elif abs(angle_diff - self.params.angle_liuhe) < tolerance:
            return {
                'type': 'LiuHe',
                'angle': 60,
                'strength': self.params.liuhe_binding_strength,
                'description': 'Combination/Binding'
            }
        
        elif abs(angle_diff - self.params.angle_xing) < tolerance:
            return {
                'type': 'Xing',
                'angle': 90,
                'strength': self.params.xing_friction_loss,
                'description': 'Shear Stress/Friction'
            }
        
        return None
    
    def check_hetu_resonance(self, stem1: str, stem2: str) -> Optional[Dict]:
        """
        Check Hetu resonance (河图数理).
        Stems with number difference of 5 resonate.
        
        Returns:
            dict with resonance info or None
        """
        props1 = ParticleDefinitions.get_stem_properties(stem1)
        props2 = ParticleDefinitions.get_stem_properties(stem2)
        
        num1 = props1.get('hetu_number', 0)
        num2 = props2.get('hetu_number', 0)
        
        if abs(num1 - num2) == 5:
            # Hetu resonance detected
            return {
                'type': 'HetuResonance',
                'stems': [stem1, stem2],
                'numbers': [num1, num2],
                'description': f'{stem1}({num1}) ↔ {stem2}({num2}) Resonance'
            }
        
        return None


# Export main classes
__all__ = [
    'PhysicsParameters',
    'ParticleDefinitions',
    'GeometricInteraction'
]
