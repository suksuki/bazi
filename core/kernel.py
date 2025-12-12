from core.config_manager import ConfigManager

class Kernel:
    """
    Antigravity Physics Kernel (Axioms) - Constitution Compliant V2.0
    Defines the fundamental laws of the Bazi Universe.
    Adheres to Prime Axiom: NO HARD-CODED PARAMETERS (All constants are modifiable).
    """
    
    # --- 1. Particle Structure Axioms ---
    
    # Zodiac Angular Mapping (Degrees) - Spatial Geometry
    # 0 degrees = North (Zi/Rat)
    ZODIAC_ANGLES = {
        "子": 0, "丑": 30, "寅": 60, "卯": 90, 
        "辰": 120, "巳": 150, "午": 180, "未": 210, 
        "申": 240, "酉": 270, "戌": 300, "亥": 330
    }
    
    # Core Composition (Hidden Stems) - Mass/Substance
    # Ratios define the 'purity' of the Mass.
    # DEFAULT VALUES (Can be overridden by global_config.json)
    HIDDEN_STEMS = {
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
    
    # Stem Polarity & Element Map (Wave Properties)
    STEM_PROPERTIES = {
        "甲": {"element": "Wood", "polarity": "Yang"},
        "乙": {"element": "Wood", "polarity": "Yin"},
        "丙": {"element": "Fire", "polarity": "Yang"},
        "丁": {"element": "Fire", "polarity": "Yin"},
        "戊": {"element": "Earth", "polarity": "Yang"},
        "己": {"element": "Earth", "polarity": "Yin"},
        "庚": {"element": "Metal", "polarity": "Yang"},
        "辛": {"element": "Metal", "polarity": "Yin"},
        "壬": {"element": "Water", "polarity": "Yang"},
        "癸": {"element": "Water", "polarity": "Yin"}
    }

    # Element Generation Cycle (Sheng)
    ELEMENT_GENERATION = {
        "Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"
    }

    # --- 3. Dimensionality Axioms ---
    
    # Positional Weights (Mass Potential)
    # Month is thermodynamic baseline.
    POSITION_WEIGHTS = {
        "month": 0.45, "hour": 0.25, "year": 0.15, "day": 0.15 
    }

    @classmethod
    def load_overrides(cls):
        """
        AXIOM IMPLEMENTATION: Dynamic Parameter Loading.
        Allows the Optimizer to tune physical constants.
        """
        cm = ConfigManager()
        
        # 1. Override Position Weights
        pos_weights = cm.get("kernel_position_weights")
        if pos_weights:
            cls.POSITION_WEIGHTS.update(pos_weights)
            
        # 2. Override Hidden Stems (Advanced Tuning)
        hidden_ratios = cm.get("kernel_hidden_stems")
        if hidden_ratios:
            # Deep update
            for branch, ratios in hidden_ratios.items():
                if branch in cls.HIDDEN_STEMS:
                    cls.HIDDEN_STEMS[branch] = ratios
                    
    @staticmethod
    def get_angle(char):
        return Kernel.ZODIAC_ANGLES.get(char, None)

    @staticmethod
    def get_angular_diff(char1, char2):
        """
        Calculates shortest arc difference on the 360 circle.
        """
        a1 = Kernel.get_angle(char1)
        a2 = Kernel.get_angle(char2)
        if a1 is None or a2 is None: return None
        
        diff = abs(a1 - a2)
        if diff > 180:
            diff = 360 - diff
        return diff

    @staticmethod
    def get_interaction_type(char1, char2):
        """
        Determines Interaction Geometry based on Axiom 2.
        """
        diff = Kernel.get_angular_diff(char1, char2)
        if diff is None: return None
        
        # Exact integer degrees (Zodiac is discrete)
        # Using tolerances? For now, Constitution implies precise geometry,
        # but in simulation, we might accept +/- 5 degrees if floating point.
        # Since specific mapping is Integer, exact match is fine.
        
        if diff == 120: return "SanHe"      # Phase Locking (120°)
        if diff == 180: return "LiuChong"   # Head-on Collision (180°)
        if diff == 90:  return "XiangXing"  # Shear Stress (90°)
        # Note: 60° is LiuHe (Combination), 30° is minor. 
        # Focusing on the mandated axioms.
        return None
        
# Auto-load on module import to ensure latest config is active
try:
    Kernel.load_overrides()
except:
    pass # ConfigManager might not be ready during bootstrap

