"""
Antigravity V8.8 Physics Processor
===================================
Layer 1: Pure Five-Element Physics

This processor calculates raw energy distribution based on:
- Heavenly Stem elements
- Earthly Branch main elements
- Rooting relationships
- Stem support

NO seasonal adjustments or phase changes here.
"""

from core.processors.base import BaseProcessor
from typing import Dict, Any, List, Optional


# Element mapping constants
STEM_ELEMENTS = {
    '甲': 'wood', '乙': 'wood',
    '丙': 'fire', '丁': 'fire',
    '戊': 'earth', '己': 'earth',
    '庚': 'metal', '辛': 'metal',
    '壬': 'water', '癸': 'water'
}

BRANCH_ELEMENTS = {
    '子': 'water', '丑': 'earth', '寅': 'wood', '卯': 'wood',
    '辰': 'earth', '巳': 'fire', '午': 'fire', '未': 'earth',
    '申': 'metal', '酉': 'metal', '戌': 'earth', '亥': 'water'
}

# Generation cycle
GENERATION = {
    'wood': 'fire', 
    'fire': 'earth', 
    'earth': 'metal', 
    'metal': 'water', 
    'water': 'wood'
}

# Control cycle
CONTROL = {
    'wood': 'earth', 
    'earth': 'water', 
    'water': 'fire', 
    'fire': 'metal', 
    'metal': 'wood'
}


class PhysicsProcessor(BaseProcessor):
    """
    Layer 1: Base Physics Score Calculator
    
    Calculates raw five-element energy distribution.
    Does NOT consider:
    - Seasonal adjustments (that's SeasonalProcessor)
    - Phase changes (that's PhaseProcessor)
    - Special patterns (that's PatternProcessor)
    """
    
    # === Configurable Weights (all tunable) ===
    BASE_UNIT = 50.0
    
    # Positional weights (from config_schema)
    PILLAR_WEIGHTS = {
        'year': 0.8,
        'month': 2.0,   # Month is king
        'day': 1.0,
        'hour': 0.9
    }
    
    # Spatial decay
    SPATIAL_DECAY = {
        'gap1': 0.6,    # Adjacent pillars
        'gap2': 0.3     # Far pillars
    }
    
    # Rooting bonus
    ROOTING_WEIGHT = 1.5
    EXPOSED_BOOST = 1.3
    
    @property
    def name(self) -> str:
        return "Physics Layer 1"
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate raw five-element energy distribution.
        
        Returns:
            {
                'raw_energy': {element: score},
                'dm_element': str,
                'rooted_elements': [str],
                'stem_elements': [str]
            }
        """
        # 🔥 Hot-Reload: Load latest config
        from core.config_manager import ConfigManager
        config = ConfigManager.load_config()
        p_params = config.get("physics", {})
        
        # Load params
        base_stem = p_params.get("stem_score", 10.0)
        base_branch = p_params.get("branch_main_qi", 10.0)
        
        # Hardcoded weights for now, can be moved to config later if needed
        pillar_weights = {
            'year': 0.8,
            'month': 2.0,
            'day': 1.0,
            'hour': 0.9
        }
        
        bazi = context.get('bazi', [])
        dm_char = context.get('day_master', '甲')
        dm_element = self._get_element_stem(dm_char)
        
        if len(bazi) < 4:
            return self._empty_result(dm_element)
        
        # Initialize energy map
        energy = {
            'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 
            'metal': 0.0, 'water': 0.0
        }
        
        # Track rooting and stems
        branch_elements = []
        stem_elements = []
        
        # Collect branch elements for rooting check
        for pillar in bazi:
            if len(pillar) >= 2:
                branch_elements.append(self._get_element_branch(pillar[1]))
        
        # Calculate energy from each pillar
        pillar_names = ['year', 'month', 'day', 'hour']
        
        for idx, pillar in enumerate(bazi):
            if not pillar or len(pillar) < 2:
                continue
            
            stem, branch = pillar[0], pillar[1]
            p_name = pillar_names[idx]
            p_weight = pillar_weights.get(p_name, 1.0)
            
            # Spatial decay from Day pillar (idx=2)
            dist = abs(idx - 2)
            k_dist = 1.0
            # Use fixed decay for now as it's not in default config
            if dist == 1:
                k_dist = 0.6
            elif dist >= 2:
                k_dist = 0.3
            
            # Stem energy (skip Day Master itself)
            if idx != 2:
                s_elem = self._get_element_stem(stem)
                stem_elements.append(s_elem)
                
                # Check if rooted
                is_rooted = s_elem in branch_elements
                k_root = self.ROOTING_WEIGHT if is_rooted else 0.5
                k_exposed = self.EXPOSED_BOOST if is_rooted else 1.0
                
                # Apply multipliers
                s_score = base_stem * p_weight * k_dist * k_exposed
                energy[s_elem] += s_score
            
            # Branch energy
            b_elem = self._get_element_branch(branch)
            b_score = base_branch * p_weight * k_dist
            energy[b_elem] += b_score
        
        return {
            'raw_energy': energy,
            'dm_element': dm_element,
            'rooted_elements': list(set(e for e in stem_elements if e in branch_elements)),
            'stem_elements': stem_elements,
            'branch_elements': branch_elements
        }
    
    def _get_element_stem(self, stem: str) -> str:
        """Get element for heavenly stem"""
        return STEM_ELEMENTS.get(stem, 'wood')
    
    def _get_element_branch(self, branch: str) -> str:
        """Get element for earthly branch"""
        return BRANCH_ELEMENTS.get(branch, 'earth')
    
    def _empty_result(self, dm_element: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'raw_energy': {'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0},
            'dm_element': dm_element,
            'rooted_elements': [],
            'stem_elements': [],
            'branch_elements': []
        }


def get_relation(dm_element: str, target_element: str) -> str:
    """
    Get the relation between Day Master element and target element.
    
    Returns one of: 'self', 'resource', 'output', 'wealth', 'officer'
    """
    if dm_element == target_element:
        return 'self'
    
    # Find what generates dm_element (resource)
    for mother, child in GENERATION.items():
        if child == dm_element and mother == target_element:
            return 'resource'
    
    # Find what dm_element generates (output)
    if GENERATION.get(dm_element) == target_element:
        return 'output'
    
    # Find what dm_element controls (wealth)
    if CONTROL.get(dm_element) == target_element:
        return 'wealth'
    
    # The remaining relation (officer/killer)
    return 'officer'
