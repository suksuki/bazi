import sys
import os
import json
import copy
import time

# Add project root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.engine_v91 import EngineV91

ERA_PATH = os.path.join(os.path.dirname(__file__), "../data/era_constants.json")

def load_era():
    with open(ERA_PATH, 'r') as f:
        return json.load(f)

def save_era(data):
    with open(ERA_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def run_spacetime_test():
    print("🚀 V9.1 Spacetime Fusion Test")
    print("===========================")
    
    # Backup original era config
    original_era = load_era()
    
    try:
        engine = EngineV91()
        
        # Case: Weak Fire (Propyl Fire needed)
        # Using a chart with some fire to see multiplication effects
        bazi = ["丙午", "庚子", "丙午", "壬辰"]
        dm = "丙"
        
        results = {}
        
        # --- SCENARIO 1: Baseline (Period 8 / Neutral) ---
        print("\n[Scenario 1] Simulating Period 8 (Neutral Era)...")
        neutral_era = copy.deepcopy(original_era)
        neutral_era['physics_multipliers'] = {k: 1.0 for k in neutral_era['physics_multipliers']}
        save_era(neutral_era)
        
        # Force reload? PhysicsProcessor reloads on each call? 
        # Check physics.py: Yes, it reads file on processing if we implemented it there.
        # Wait, my previous edit to physics.py inserted the read/apply logic inside process().
        # So yes, it's hot-reload capable.
        
        res1 = engine.analyze(bazi, dm, city="Unknown")
        score1 = res1.energy_distribution['fire']
        results['S1_Base'] = score1
        print(f"   -> Fire Score: {score1:.2f} (Baseline)")
        
        # --- SCENARIO 2: V9.1 Period 9 + Harbin ---
        print("\n[Scenario 2] Period 9 (Fire x1.25) + Harbin (Fire x0.6)...")
        # Restore Period 9 constants
        save_era(original_era) 
        
        res2 = engine.analyze(bazi, dm, city="Harbin")
        score2 = res2.energy_distribution['fire']
        results['S2_Harbin'] = score2
        print(f"   -> Fire Score: {score2:.2f}")
        
        # --- SCENARIO 3: V9.1 Period 9 + Singapore ---
        print("\n[Scenario 3] Period 9 (Fire x1.25) + Singapore (Fire x1.3)...")
        res3 = engine.analyze(bazi, dm, city="Singapore")
        score3 = res3.energy_distribution['fire']
        results['S3_Singapore'] = score3
        print(f"   -> Fire Score: {score3:.2f}")

        # --- Analysis ---
        print("\n📊 Comparative Analysis:")
        base = results['S1_Base']
        
        diff2 = (results['S2_Harbin'] - base) / base * 100
        diff3 = (results['S3_Singapore'] - base) / base * 100
        
        print(f"1. Baseline:  {base:.2f}")
        print(f"2. Harbin:    {results['S2_Harbin']:.2f} (Diff: {diff2:+.1f}%)")
        print(f"3. Singapore: {results['S3_Singapore']:.2f} (Diff: {diff3:+.1f}%)")
        
        # Validation Logic
        # Era (1.25) * Harbin (0.6) = 0.75. Should be LOWER than Base (1.0).
        if results['S2_Harbin'] < base:
            print("✅ Harbin check passed: Geo Cold (>40%) overpowered Era Heat (25%).")
        else:
            print("⚠️ Harbin check unexpected.")

        # Era (1.25) * Singapore (1.3) = 1.625. Should be MUCH HIGHER.
        if results['S3_Singapore'] > base:
            print("✅ Singapore check passed: Geo Heat + Era Heat = Super Bonus.")
        else:
            print("⚠️ Singapore check unexpected.")
            
    finally:
        # RESTORE CONFIG
        save_era(original_era)
        print("\n🔄 Environment restored.")

if __name__ == "__main__":
    run_spacetime_test()
