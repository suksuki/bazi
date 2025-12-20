
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
from core.trinity.core.physics_engine import ParticleDefinitions

class V14Calibrator:
    def __init__(self):
        self.data_path = Path(__file__).parent.parent / "data" / "v14_synthetic_cases.json"
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.cases = json.load(f)
            
        # Filter for the 4 Extreme Cases mentioned by Architect + Limit Cases
        self.target_cases = [c for c in self.cases if c['name'].startswith("Synthetic_Ex") or c['name'].startswith("V14_STRESS")]

    def run_grid_search(self):
        print("🧪 V14.2 Quantum Physics Grid Search")
        print("====================================")
        
        # Parameter Grid
        coherence_boosts = np.arange(1.0, 3.1, 0.5) # 1.0 to 3.0
        recoil_factors = np.arange(0.1, 2.1, 0.4)   # 0.1 to 2.1
        
        best_score = -1.0
        best_params = {}
        
        total_combinations = len(coherence_boosts) * len(recoil_factors)
        print(f"Scanning {total_combinations} parameter combinations...")
        
        for cb in coherence_boosts:
            for rf in recoil_factors:
                # 1. Configure Engine (Inject Parameters)
                # Note: We need to modify the engine to accept these overrides. 
                # For now, we will pass them via config or patch the class constants temporarily.
                config = {
                    'physics': {
                        'coherence_boost': float(cb), 
                        'recoil_factor': float(rf)
                    }
                }
                
                # Update Global Constants (Mocking injection for simulation)
                # In a real scenario, these should be instance variables.
                # We will support this in QuantumEngine/FluxEngine logic next.
                
                engine = QuantumEngine(config=config)
                
                score, passed = self.evaluate_batch(engine)
                
                print(f"Params(coh={cb:.1f}, recoil={rf:.1f}) -> Score: {score:.2f}% ({passed}/{len(self.target_cases)} Pass)")
                
                if score > best_score:
                    best_score = score
                    best_params = {'coherence_boost': cb, 'recoil_factor': rf}
                    
        print("\n" + "="*50)
        print(f"🏆 Best Found Parameters: {best_params}")
        print(f"   Max Precision: {best_score:.2f}%")
        print("="*50)

    def evaluate_batch(self, engine: QuantumEngine) -> tuple:
        passed_count = 0
        total_error = 0.0
        
        for case in self.target_cases:
            bazi = case.get('bazi', [])
            dm = case.get('day_master', '')
            month_branch = bazi[1][1] if len(bazi) > 1 else ''
            
            res = engine.analyze_bazi(bazi, dm, month_branch)
            verdict = res['verdict']['label']
            ground_truth = case.get('ground_truth', {}).get('strength')
            
            if verdict == ground_truth:
                passed_count += 1
            else:
                # Penalty
                pass
                
        # Simple Accuracy
        return (passed_count / len(self.target_cases)) * 100.0, passed_count

if __name__ == "__main__":
    calibrator = V14Calibrator()
    calibrator.run_grid_search()
