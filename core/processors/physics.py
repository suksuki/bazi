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
    Layer 1: Base Physics Score Calculator (Genesis V9.1)
    
    Rebuilt strictly according to 'Algorithm Constitution'.
    Logic: Energy Quantization.
    """
    
    # === Genesis Blueprint Constants ===
    
    # 1. Hidden Stems Map (Hardcoded Source of Truth)
    # Format: Branch -> [(Stem, Weight)]
    GENESIS_HIDDEN_MAP = {
        '子': [('癸', 10)],                                      # Zi: Gui (Pure)
        '丑': [('己', 10), ('癸', 7), ('辛', 3)],                 # Chou: Ji, Gui, Xin
        '寅': [('甲', 10), ('丙', 7), ('戊', 3)],                 # Yin: Jia, Bing, Wu
        '卯': [('乙', 10)],                                      # Mao: Yi (Pure)
        '辰': [('戊', 10), ('乙', 7), ('癸', 3)],                 # Chen: Wu, Yi, Gui
        '巳': [('丙', 10), ('戊', 7), ('庚', 3)],                 # Si: Bing, Wu, Geng
        '午': [('丁', 10), ('己', 7)],                           # Wu: Ding, Ji
        '未': [('己', 10), ('丁', 7), ('乙', 3)],                 # Wei: Ji, Ding, Yi
        '申': [('庚', 10), ('壬', 7), ('戊', 3)],                 # Shen: Geng, Ren, Wu
        '酉': [('辛', 10)],                                      # You: Xin (Pure)
        '戌': [('戊', 10), ('辛', 7), ('丁', 3)],                 # Xu: Wu, Xin, Ding
        '亥': [('壬', 10), ('甲', 7)]                            # Hai: Ren, Jia
    }
    
    # 2. Weights
    PILLAR_WEIGHTS = {'year': 0.8, 'month': 2.0, 'day': 1.0, 'hour': 0.9}
    BASE_SCORE = 10.0
    ROOT_BONUS = 1.2
    
    @property
    def name(self) -> str:
        return "Physics Layer 1 (Genesis)"
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates raw five-element energy using Genesis Logic.
        """
        bazi = context.get('bazi', [])
        dm_char = context.get('day_master', '甲')
        dm_element = self._get_element_stem(dm_char)
        
        # Initialize Energy Accumulator
        energy = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 'metal': 0.0, 'water': 0.0}
        
        # Helper lists for analysis
        stem_chars = []
        branch_chars = []
        all_hidden_chars = set()
        
        # --- 1. Processing Loop ---
        pillar_names = ['year', 'month', 'day', 'hour']
        
        for idx, pillar in enumerate(bazi):
            if len(pillar) < 2: continue
            
            p_name = pillar_names[idx]
            stem_char = pillar[0]
            branch_char = pillar[1]
            w_pillar = self.PILLAR_WEIGHTS.get(p_name, 1.0)
            
            # A. Heavenly Stems ( 天干 )
            if idx != 2: # Skip DM for energy counting
                stem_chars.append(stem_char)
                elem = self._get_element_stem(stem_char)
                score = self.BASE_SCORE * w_pillar
                energy[elem] += score
                
            # B. Earthly Branches ( 地支 ) - Using Genesis Map
            branch_chars.append(branch_char)
            hiddens = self.GENESIS_HIDDEN_MAP.get(branch_char, [])
            
            for h_char, h_weight in hiddens:
                all_hidden_chars.add(h_char)
                elem = self._get_element_stem(h_char)
                # Formula: Pillar_Weight * Hidden_Weight
                # Note: Hidden_Weight is 10, 7, 3.
                score = w_pillar * h_weight 
                energy[elem] += score

        # --- 2. Rooting Logic ( 通根 ) ---
        # "If a Stem matches a Hidden Stem in ANY branch -> Multiply Stem's score"
        # Since we already added Stem scores, we apply a bonus calculation.
        
        rooted_stems = []
        
        # We need to re-iterate stems to apply the bonus to the specific stem contribution?
        # Simpler: Just add the bonus directly to the energy map.
        # But wait, which stem contributed?
        # Let's re-calculate Stem Energy with Root Bonus.
        
        # Reset energy to just branch contribution first? No.
        # Let's separate Stem and Branch calculations for clarity?
        # Or just apply bonus now.
        
        # Refined Logic:
        # For each stem (except DM):
        #   If rooted:
        #      Add extra (Score * 0.2) to match 1.2x total.
        
        for idx, pillar in enumerate(bazi):
             if idx == 2: continue # Skip DM
             if len(pillar) < 1: continue
             
             stem_char = pillar[0]
             p_name = pillar_names[idx]
             w_pillar = self.PILLAR_WEIGHTS.get(p_name, 1.0)
             
             if stem_char in all_hidden_chars:
                 elem = self._get_element_stem(stem_char)
                 # Original Score was BASE(10) * W_Pillar
                 original_score = self.BASE_SCORE * w_pillar
                 bonus = original_score * (self.ROOT_BONUS - 1.0) # 0.2x
                 energy[elem] += bonus
                 rooted_stems.append(stem_char)

        # --- 3. Era Multipliers (Preserve V9.1 Feature) ---
        # V9.5 Performance Optimization: era_multipliers now passed via context
        # to avoid file I/O operations (eliminated 20.33% performance overhead)
        era_mults = context.get('era_multipliers', {})
        if era_mults:
            for elem, mult in era_mults.items():
                if elem in energy and isinstance(mult, (int, float)):
                    energy[elem] *= mult

        return {
            'raw_energy': energy,
            'dm_element': dm_element,
            'rooted_elements': list(set(rooted_stems)),
            'stem_elements': [self._get_element_stem(c) for c in stem_chars],
            'branch_elements': list(all_hidden_chars)
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
