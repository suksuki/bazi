
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

class V14CalibratorV2:
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
        print("🧪 V14.5 Quantum Physics 3D Grid Search")
        print("========================================")
        
        # Parameter Grid (Optimized Range)
        coherence_boosts = [1.0, 1.2, 1.5, 2.0]
        recoil_factors = [0.8, 1.0, 1.2, 1.5]
        shielding_factors = [5.0, 10.0, 15.0]
        
        best_score = -1.0
        best_params = {}
        
        total_combinations = len(coherence_boosts) * len(recoil_factors) * len(shielding_factors)
        print(f"Scanning {total_combinations} parameter combinations...")
        
        count = 0
        for cb in coherence_boosts:
            for rf in recoil_factors:
                for sf in shielding_factors:
                    count += 1
                    config = {
                        'physics': {
                            'coherence_boost': float(cb), 
                            'recoil_factor': float(rf),
                            'shielding_factor': float(sf)
                        }
                    }
                    
                    engine = QuantumEngine(config=config)
                    score, passed = self.evaluate_batch(engine)
                    
                    if score >= best_score: # Prefer later results if tied? No, just keep tracking
                        best_score = score
                        best_params = {'coherence_boost': cb, 'recoil_factor': rf, 'shielding_factor': sf}
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
    calibrator = V14CalibratorV2()
    calibrator.run_grid_search()
