
import sys
import os
import json
import itertools
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine

class V14CalibratorV3:
    def __init__(self):
        self.matrix_path = Path(__file__).parent.parent / "tests" / "v14_tuning_matrix.json"
        
        if self.matrix_path.exists():
            with open(self.matrix_path, 'r', encoding='utf-8') as f:
                self.cases = json.load(f)
            print(f"Loaded Matrix 30 Dataset ({len(self.cases)} cases)")
        else:
            print("Matrix 30 Dataset not found!")
            sys.exit(1)

    def run_grid_search(self):
        print("🧪 V14.6 Quantum Physics 4D Grid Search")
        print("========================================")
        
        # Parameter Grid (Refined Range)
        recoil_factors = [1.5] # Fixed best from V2
        shielding_factors = [15.0] # Fixed best from V2
        
        # New Dimensions
        coherence_boosts = [2.0, 3.0, 4.0] # Need higher boost for Metal Blade?
        entropy_guards = [0.98, 0.99, 1.0] # Can we allow 1.0 (Superconductor)?
        
        best_score = -1.0
        best_params = {}
        
        total_combinations = len(coherence_boosts) * len(recoil_factors) * len(shielding_factors) * len(entropy_guards)
        print(f"Scanning {total_combinations} parameter combinations...")
        
        count = 0
        for cb in coherence_boosts:
            for rf in recoil_factors:
                for sf in shielding_factors:
                    for eg in entropy_guards:
                        count += 1
                        config = {
                            'physics': {
                                'coherence_boost': float(cb), 
                                'recoil_factor': float(rf),
                                'shielding_factor': float(sf),
                                'entropy_guard': float(eg)
                            }
                        }
                        
                        engine = QuantumEngine(config=config)
                        score, passed = self.evaluate_batch(engine)
                        
                        if score >= best_score:
                            best_score = score
                            best_params = {
                                'coherence_boost': cb, 
                                'recoil_factor': rf, 
                                'shielding_factor': sf,
                                'entropy_guard': eg
                            }
                            print(f"[{count}/{total_combinations}] New Best: Score={score:.1f}% Params={best_params}")
                    
        print("\n" + "="*50)
        print(f"🏆 Best Found Parameters: {best_params}")
        print(f"   Max Precision: {best_score:.2f}%")
        print("="*50)

    def evaluate_batch(self, engine: QuantumEngine) -> tuple:
        passed_count = 0
        
        for case in self.cases:
            bazi = case.get('bazi', [])
            dm = case.get('day_master', '')
            month_branch = case.get('month_branch', '')
            
            res = engine.analyze_bazi(bazi, dm, month_branch)
            verdict = res['verdict']['label']
            ground_truth = case.get('ground_truth', {}).get('strength')
            
            if verdict == ground_truth:
                passed_count += 1
                
        return (passed_count / len(self.cases)) * 100.0, passed_count

if __name__ == "__main__":
    calibrator = V14CalibratorV3()
    calibrator.run_grid_search()
