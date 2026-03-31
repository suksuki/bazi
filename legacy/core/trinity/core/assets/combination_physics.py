"""
Antigravity Combination Physics (Phase B-09)
============================================
Handles Heavenly Stem Combinations with Environmental Energy Phase Validation.
"""

import json
import os
from typing import Dict, Tuple, Optional

class CombinationPhysics:
    
    # 5-He Mappings
    COMBINATIONS = {
        frozenset(['甲', '己']): 'Earth',
        frozenset(['乙', '庚']): 'Metal',
        frozenset(['丙', '辛']): 'Water',
        frozenset(['丁', '壬']): 'Wood',
        frozenset(['戊', '癸']): 'Fire'
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'energy_phase_matrix.json')
            
        self.config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        self.threshold = self.config.get('combination_thresholds', {}).get('transform_base_energy', 4.5)

    def check_combination(self, stem1: str, stem2: str, env_energy: Dict[str, float]) -> Dict:
        """
        Check if two stems combine and if the environment supports transformation.
        
        Args:
            stem1, stem2: Heavenly Stems
            env_energy: Dict of current environmental energy (e.g., {'Wood': 5.0, ...})
            
        Returns:
            Dict: { 'is_comb': bool, 'target': str, 'success': bool, 'energy': float }
        """
        pair = frozenset([stem1, stem2])
        target_element = self.COMBINATIONS.get(pair)
        
        if not target_element:
            return {'is_comb': False, 'status': 'NONE'}
            
        # Check Environmental Support for Target Element
        # The target element needs sufficient environmental energy to "Solidify" (Hua Qi)
        # We look up the environmental energy of the target element (e.g., 'Wood')
        current_strength = env_energy.get(target_element, 0.0)
        
        success = current_strength >= self.threshold
        
        return {
            'is_comb': True,
            'target': target_element,
            'env_strength': current_strength,
            'threshold': self.threshold,
            'success': success,
            'status': 'TRANSFORMED' if success else 'BOUND_FAIL'
        }

# Singleton Asset
comb_engine = CombinationPhysics()
