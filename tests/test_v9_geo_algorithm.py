import sys
import os

# Add project root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.engine_v88 import EngineV88 as EngineV91  # Alias for compatibility

def run_algo_test():
    print("🌍 V9.1 Geo Algorithm Regression Test")
    print("=====================================")
    
    engine = EngineV91()
    bazi = ["丙子", "庚子", "丙午", "壬辰"] # Dummy data
    dm = "丙"
    
    # Test Points
    test_points = [
        {"lat": 0.0, "desc": "Equator (0deg)"},
        {"lat": 30.0, "desc": "Mid-Lat (30deg)"},
        {"lat": 60.0, "desc": "High-Lat (60deg)"}
    ]
    
    print(f"{'Lat':<10} | {'Fire Multiplier':<15} | {'Water Multiplier':<15}")
    print("-" * 50)
    
    for pt in test_points:
        # We can test process directly or via analyze
        # Let's use geo processor direct access for simpler unit testing
        mods = engine.geo.process(pt['lat'])
        
        f_mult = mods.get('fire', 1.0)
        w_mult = mods.get('water', 1.0)
        
        print(f"{pt['lat']:<10} | {f_mult:<15} | {w_mult:<15}")
        
    print("=====================================")
    print("Expected Behavior:")
    print(" - Equator (0): Fire ~1.3, Water ~0.7")
    print(" - High (60):   Fire ~0.6, Water ~1.4")
    print(" - Mid (30):    Somewhere in between")

if __name__ == "__main__":
    run_algo_test()
