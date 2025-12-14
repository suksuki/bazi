import sys
import os
import pytest

# Add project root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.engine_v88 import EngineV88
from core.config_manager import ConfigManager

def test_v91_era_physics_boost():
    print("🔥 V9.1 Era-Aware Physics Validation")
    print("===================================")
    
    # 1. Setup Standard Config
    cfg = ConfigManager.load_config()
    # Reset stem/branch score to known value for easy math
    cfg['physics']['stem_score'] = 10.0
    cfg['physics']['branch_main_qi'] = 10.0
    ConfigManager.save_config(cfg)
    
    engine = EngineV88() # Physics is in base V8.8 too now
    
    # 2. Test Case 1: Pure Fire (丙午年 only)
    # Note: Physics processor handles list of pillars.
    # Year weight = 0.8
    # Stem '丙' -> Fire. Base = 10 * 0.8 = 8.
    # Branch '午' -> Fire. Base = 10 * 0.8 = 8.
    # Total Raw = 16.0
    # Era Mult (Fire) = 1.25
    # Expected = 16.0 * 1.25 = 20.0
    
    # Using a dummy bazi that results in pure fire for Year pillar
    # We pass 4 pillars to satisfy len checks, but focus on the Year score
    bazi_fire = ["丙午", "xx", "xx", "xx"] 
    # Actually Physics processor iterates all.
    # Let's use a minimal bazi: 4 pillars of empty/neutral?
    # Or just calc manually what we expect.
    
    # Let's use a clean single-element dominance case
    bazi = ["丙午", "丙午", "丙午", "丙午"]
    dm = "丙"
    
    # Weights: Year 0.8 + Month 2.0 + Day 1.0 (Branch only) + Hour 0.9
    # Stem: 10 * (0.8 + 2.0 + 0.9) = 37.0 => With Spatial/Rooting? 
    # This is getting complex to calc manually due to multipliers.
    
    # Alternative: Compare Fire vs Water with same layout
    bazi_fire = ["丙午", "丙午", "丙午", "丙午"]
    bazi_water = ["壬子", "壬子", "壬子", "壬子"]
    
    res_fire = engine.analyze(bazi_fire, "丙")
    res_water = engine.analyze(bazi_water, "壬")
    
    fire_score = res_fire.energy_distribution['fire']
    water_score = res_water.energy_distribution['water']
    
    print(f"🔥 Total Fire Score (Era 9): {fire_score:.2f}")
    print(f"💧 Total Water Score (Era 9): {water_score:.2f}")
    
    # Ratio check
    # If no Era physics, ratio should be ~1.0 (assuming identical weights for Fire/Water in code)
    # With Era 9: Fire x1.25, Water x0.9
    # Expected Ratio = 1.25 / 0.9 = 1.388
    
    ratio = fire_score / water_score if water_score > 0 else 0
    print(f"📊 Fire/Water Ratio: {ratio:.3f} (Expected ~1.39)")
    
    # Check bounds
    assert ratio > 1.3, "Fire should be significantly boosted over Water in Era 9"
    assert fire_score > water_score, "Fire score must exceed Water score for identical charts"

    print("✅ V9.1 Physics Physics Layer is Era-Aware!")

if __name__ == "__main__":
    test_v91_era_physics_boost()
