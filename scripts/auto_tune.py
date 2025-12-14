import sys
import os
import time
import copy
import json
import numpy as np
from tqdm import tqdm

# Add project root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.config_manager import ConfigManager
from core.engine_v88 import EngineV88

def load_calibration_cases():
    path = os.path.join(os.path.dirname(__file__), "../data/calibration_cases.json")
    with open(path, 'r') as f:
        return json.load(f)

def evaluate_accuracy(engine, cases):
    """Calculate Accuracy of Strength Verdict matching"""
    correct = 0
    total = 0
    
    for case in cases:
        ground_truth = case.get('ground_truth', {})
        expected_strength = ground_truth.get('strength')
        
        if not expected_strength:
            continue
            
        try:
            bazi = case.get('bazi', [])
            dm = case.get('day_master', '甲')
            
            res = engine.analyze(bazi, dm) # Correct method and args
            actual_strength = res.strength.verdict
            
            # Simple matching: Strong/Weak
            # Note: "Follower" cases handled? Engine might return Weak for Follower in some logics
            if actual_strength == expected_strength:
                correct += 1
            elif expected_strength == "Follower" and actual_strength == "Weak":
                # Partial credit? Or treat Follower as Weak in this engine version?
                # Let's be strict for now.
                pass
                
            total += 1
        except Exception:
            pass 
        
    return correct / total if total > 0 else 0.0

def main():
    print("🤖 Antigravity Auto-Tuner V1.0 (Strength Optimizer)")
    print("==================================================")
    
    # 1. Init
    engine = EngineV88()
    cases = load_calibration_cases()
    original_config = ConfigManager.load_config()
    
    print(f"📚 Loaded {len(cases)} calibration cases")
    print(f"⚙️  Current Stem Score: {original_config['physics']['stem_score']}")
    
    # 2. Search Space
    search_space = np.arange(8.0, 14.5, 0.5)
    best_acc = 0.0
    best_param = 0
    
    print("\n🚀 Starting Grid Search...")
    
    try:
        pbar = tqdm(search_space)
        for stem_score in pbar:
            # A. Update Config
            cfg = copy.deepcopy(original_config)
            cfg['physics']['stem_score'] = float(stem_score) 
            ConfigManager.save_config(cfg)
            
            # B. Evaluate
            acc = evaluate_accuracy(engine, cases)
            
            pbar.set_description(f"Stem={stem_score:.1f} | Acc={acc:.1%}")
            
            if acc > best_acc:
                best_acc = acc
                best_param = stem_score
        
        print(f"\n🏆 Optimization Complete!")
        print(f"   Best Stem Score: {best_param}")
        print(f"   Highest Accuracy:{best_acc:.1%}")
        
        # 3. Apply Best
        print(f"\n💾 Saving optimal configuration...")
        final_config = copy.deepcopy(original_config)
        final_config['physics']['stem_score'] = float(best_param)
        ConfigManager.save_config(final_config)
        print("✅ System optimized.")
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted! restoring original config...")
        ConfigManager.save_config(original_config)

if __name__ == "__main__":
    main()
