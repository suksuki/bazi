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
from core.interactions import (
    STEM_COMBINATIONS, BRANCH_SIX_COMBINES, BRANCH_CLASHES,
    BRANCH_PUNISHMENTS, BRANCH_HARMS
)


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
    
    # 2. Weights (V24.0: Default values, will be overridden by config)
    PILLAR_WEIGHTS = {'year': 1.0, 'month': 1.8, 'day': 1.5, 'hour': 1.2}
    BASE_SCORE = 10.0
    ROOT_BONUS = 1.2  # 通根加成（普通通根）
    SAME_PILLAR_BONUS = 2.5  # V24.0: 自坐强根加成（羊刃/建禄等）
    
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
        
        # V24.0: Get pillar weights from config if available, otherwise use defaults
        pillar_weights_config = context.get('pillar_weights', {})
        if pillar_weights_config:
            self.PILLAR_WEIGHTS = {
                'year': pillar_weights_config.get('year', 1.0),
                'month': pillar_weights_config.get('month', 1.8),  # V24.0: Updated to 1.8
                'day': pillar_weights_config.get('day', 1.5),
                'hour': pillar_weights_config.get('hour', 1.2)
            }
        
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
                 
                 # V24.0: Check if it's same pillar rooting (自坐强根)
                 # Same pillar means the stem is in its own branch's hidden stems
                 branch_char = pillar[1] if len(pillar) > 1 else ''
                 is_same_pillar = False
                 if branch_char:
                     hiddens = self.GENESIS_HIDDEN_MAP.get(branch_char, [])
                     for h_char, _ in hiddens:
                         if h_char == stem_char:
                             is_same_pillar = True
                             break
                 
                 # Apply appropriate bonus
                 if is_same_pillar:
                     # V24.0: Same pillar rooting (自坐强根) - stronger bonus
                     bonus = original_score * (self.SAME_PILLAR_BONUS - 1.0)  # 1.5x additional
                 else:
                     # Regular rooting (通根)
                     bonus = original_score * (self.ROOT_BONUS - 1.0)  # 0.2x additional
                 
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

        # --- 4. V21.0: Complex Interactions Integration (复杂交互集成) ---
        # 将合、冲、刑、害、墓库逻辑从流年计算提升到基础计算，直接修正 raw_energy
        energy = self._apply_complex_interactions(energy, bazi, dm_element, context)

        # --- 5. V22.0: Energy Flow Coupling Effects (能量流耦合效应) ---
        # V22.0: Disabled by default, only apply if explicitly enabled
        flow_config = context.get('flow_config', {})
        coupling = flow_config.get('couplingEffects', {})
        if coupling.get('Enabled', False):
            energy = self._apply_coupling_effects(energy, bazi, dm_element, context)

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
    
    def _apply_complex_interactions(self, energy: Dict[str, float], bazi: List[str], 
                                    dm_element: str, context: Dict[str, Any]) -> Dict[str, float]:
        """
        V21.0: Apply Complex Interactions (复杂交互集成)
        
        将合、冲、刑、害、墓库逻辑从流年计算提升到基础计算，直接修正 raw_energy。
        """
        if len(bazi) < 4:
            return energy
        
        # Get interaction parameters from config
        interactions_config = context.get('interactions_config', {})
        combo_physics = interactions_config.get('comboPhysics', {})
        branch_events = interactions_config.get('branchEvents', {})
        vault_physics = interactions_config.get('vault', {})
        stem_five = interactions_config.get('stemFiveCombination', {})
        
        # Extract stems and branches
        stems = [p[0] if len(p) > 0 else '' for p in bazi]
        branches = [p[1] if len(p) > 1 else '' for p in bazi]
        month_branch = branches[1] if len(branches) > 1 else ''
        
        # 1. 天干五合 (Stem Five Combination)
        month_elem = self._get_element_branch(month_branch) if month_branch else 'earth'
        pairs = [(0, 1), (1, 2), (2, 3)]  # Year-Month, Month-Day, Day-Hour
        
        for idx1, idx2 in pairs:
            if idx1 >= len(stems) or idx2 >= len(stems):
                continue
            s1, s2 = stems[idx1], stems[idx2]
            if not s1 or not s2:
                continue
            
            # Check if they combine
            if STEM_COMBINATIONS.get(s1) == s2:
                # Get transform element
                combo_set = frozenset([s1, s2])
                transform_map = {
                    frozenset(['甲', '己']): 'earth',
                    frozenset(['乙', '庚']): 'metal',
                    frozenset(['丙', '辛']): 'water',
                    frozenset(['丁', '壬']): 'wood',
                    frozenset(['戊', '癸']): 'fire'
                }
                transform_to = transform_map.get(combo_set)
                
                # Check if transformation succeeds (month element matches)
                if transform_to and transform_to == month_elem:
                    # Successful transformation: add energy to target, reduce from originals
                    bonus = stem_five.get('bonus', 2.0)
                    base_unit = 10.0
                    added_energy = base_unit * bonus
                    energy[transform_to] += added_energy
                    
                    # Deduct from originals
                    e1 = self._get_element_stem(s1)
                    e2 = self._get_element_stem(s2)
                    deduct = base_unit * 1.0
                    energy[e1] = max(0, energy.get(e1, 0) - deduct)
                    energy[e2] = max(0, energy.get(e2, 0) - deduct)
                else:
                    # Binding (合绊): reduce energy
                    penalty = stem_five.get('penalty', 0.4)
                    e1 = self._get_element_stem(s1)
                    e2 = self._get_element_stem(s2)
                    energy[e1] *= penalty
                    energy[e2] *= penalty
        
        # 2. 地支三合/三会 (Trine/Directional Harmony)
        # Three Harmonies
        three_harmonies = {
            'Water': {'申', '子', '辰'},
            'Wood': {'亥', '卯', '未'},
            'Fire': {'寅', '午', '戌'},
            'Metal': {'巳', '酉', '丑'}
        }
        
        # Directional Assembly (三会)
        directional_assembly = {
            'Wood': {'寅', '卯', '辰'},
            'Fire': {'巳', '午', '未'},
            'Metal': {'申', '酉', '戌'},
            'Water': {'亥', '子', '丑'}
        }
        
        branch_set = set(branches)
        
        # Check Three Harmonies
        for elem_name, members in three_harmonies.items():
            if members.issubset(branch_set):
                elem_lower = elem_name.lower()
                trine_bonus = combo_physics.get('trineBonus', 3.0)
                # Enhance element energy
                base_energy = energy.get(elem_lower, 0)
                energy[elem_lower] = base_energy * trine_bonus
        
        # Check Directional Assembly
        for elem_name, members in directional_assembly.items():
            if members.issubset(branch_set):
                elem_lower = elem_name.lower()
                dir_bonus = combo_physics.get('directionalBonus', 4.0)
                # Enhance element energy
                base_energy = energy.get(elem_lower, 0)
                energy[elem_lower] = base_energy * dir_bonus
        
        # 3. 地支六合 (Six Combinations) - V26.0: Apply BEFORE negative interactions
        # Note: Positive interactions (combinations) should be applied before negative ones
        # to avoid incorrect energy reduction
        # V26.0 FIX: 六合应该使用加法而不是乘法，避免与后续减法惩罚产生错误的复合效果
        for i, b1 in enumerate(branches):
            if not b1:
                continue
            for j, b2 in enumerate(branches):
                if i >= j or not b2:
                    continue
                if BRANCH_SIX_COMBINES.get(b1) == b2:
                    # Get transform element
                    combo_set = frozenset([b1, b2])
                    transform_map = {
                        frozenset(['子', '丑']): 'earth',
                        frozenset(['寅', '亥']): 'wood',
                        frozenset(['卯', '戌']): 'fire',
                        frozenset(['辰', '酉']): 'metal',
                        frozenset(['巳', '申']): 'water',
                        frozenset(['午', '未']): 'earth'
                    }
                    transform_to = transform_map.get(combo_set)
                    if transform_to:
                        # V26.0 FIX: Use addition instead of multiplication for positive effects
                        # This ensures consistent behavior with subtraction penalties
                        base_energy = energy.get(transform_to, 0)
                        liuhe_config = branch_events.get('sixHarmony', {})
                        if isinstance(liuhe_config, dict):
                            liuhe_bonus = liuhe_config.get('bonus', 5.0)
                        else:
                            liuhe_bonus = float(liuhe_config)
                        energy[transform_to] = energy.get(transform_to, 0) + liuhe_bonus  # 六合加成（加法）
        
        # 4. 地支六冲 (Six Clashes) - V22.0: Use subtraction penalty instead of multiplication
        # V26.0 FIX: Use correct default value from config (-3.0, not -15.0)
        clash_score = branch_events.get('clashScore', -3.0)
        for i, b1 in enumerate(branches):
            if not b1:
                continue
            for j, b2 in enumerate(branches):
                if i >= j or not b2:
                    continue
                if BRANCH_CLASHES.get(b1) == b2:
                    # V22.0: Apply subtraction penalty instead of multiplication
                    e1 = self._get_element_branch(b1)
                    e2 = self._get_element_branch(b2)
                    energy[e1] = max(0, energy.get(e1, 0) + clash_score)
                    energy[e2] = max(0, energy.get(e2, 0) + clash_score)
        
        # 5. 相刑 (Punishment) - V22.0: Use subtraction penalty
        # V26.0 FIX: Use correct default value from config (-3.0, not -8.0)
        punishment_penalty = branch_events.get('punishmentPenalty', -3.0)
        for i, b1 in enumerate(branches):
            if not b1:
                continue
            for j, b2 in enumerate(branches):
                if i >= j or not b2:
                    continue
                if b2 in BRANCH_PUNISHMENTS.get(b1, []):
                    # V22.0: Apply subtraction penalty
                    e1 = self._get_element_branch(b1)
                    e2 = self._get_element_branch(b2)
                    energy[e1] = max(0, energy.get(e1, 0) + punishment_penalty)
                    energy[e2] = max(0, energy.get(e2, 0) + punishment_penalty)
        
        # 6. 相害 (Harm) - V22.0: Use subtraction penalty
        # V26.0 FIX: Use correct default value from config (-2.0, not -5.0)
        harm_penalty = branch_events.get('harmPenalty', -2.0)
        for i, b1 in enumerate(branches):
            if not b1:
                continue
            for j, b2 in enumerate(branches):
                if i >= j or not b2:
                    continue
                if BRANCH_HARMS.get(b1) == b2:
                    # V22.0: Apply subtraction penalty
                    e1 = self._get_element_branch(b1)
                    e2 = self._get_element_branch(b2)
                    energy[e1] = max(0, energy.get(e1, 0) + harm_penalty)
                    energy[e2] = max(0, energy.get(e2, 0) + harm_penalty)
        
        # 7. 墓库物理 (Vault Physics) - V22.0: Use subtraction penalty for sealed state
        # Check if day branch is a vault
        day_branch = branches[2] if len(branches) > 2 else ''
        vault_mapping = {
            '辰': 'water',
            '戌': 'fire',
            '丑': 'metal',
            '未': 'wood'
        }
        
        if day_branch in vault_mapping:
            vault_element = vault_mapping[day_branch]
            vault_elem_energy = energy.get(vault_element, 0)
            threshold = vault_physics.get('threshold', 15.0)
            
            if vault_elem_energy >= threshold:
                # Vault (库): Open bonus (multiplication for positive effect)
                open_bonus = vault_physics.get('openBonus', 1.3)
                energy[vault_element] = vault_elem_energy * open_bonus
            else:
                # Tomb (墓): Sealed penalty (subtraction for negative effect)
                sealed_penalty = vault_physics.get('sealedPenalty', -10.0)
                energy[vault_element] = max(0, vault_elem_energy + sealed_penalty)
        
        return energy
    
    def _apply_coupling_effects(self, energy: Dict[str, float], bazi: List[str], 
                                dm_element: str, context: Dict[str, Any]) -> Dict[str, float]:
        """
        V21.0: Apply Energy Flow Coupling Effects (能量流耦合效应)
        
        实现顺生链放大、合力共振和多重力量抵消算法。
        """
        if len(bazi) < 4:
            return energy
        
        # Get coupling parameters from config
        flow_config = context.get('flow_config', {})
        coupling = flow_config.get('couplingEffects', {})
        seq_gain = coupling.get('Sequential_Gain_Factor', 1.20)
        coherence_boost = coupling.get('Coherence_Boost_Factor', 0.15)
        cancel_factor = coupling.get('Cancellation_Factor', 0.60)
        
        # Extract stem elements from each pillar
        stems = []
        stem_elements = []
        for idx, pillar in enumerate(bazi):
            if len(pillar) > 0:
                stem_char = pillar[0]
                stems.append(stem_char)
                stem_elements.append(self._get_element_stem(stem_char))
            else:
                stems.append(None)
                stem_elements.append(None)
        
        # Year (0), Month (1), Day (2), Hour (3)
        # Day Master is at index 2
        
        # 1. Sequential Amplification (顺生链放大)
        # Check for sequential generation chain: Year -> Month -> Day
        sequential_chain_length = 0
        if stems[0] and stems[1] and stems[2]:
            year_elem = stem_elements[0]
            month_elem = stem_elements[1]
            day_elem = stem_elements[2]  # Day Master
            
            # Check if Year generates Month
            if GENERATION.get(year_elem) == month_elem:
                # Check if Month generates Day
                if GENERATION.get(month_elem) == day_elem:
                    sequential_chain_length = 2
                # Check if Year directly generates Day (also counts as chain)
                elif GENERATION.get(year_elem) == day_elem:
                    sequential_chain_length = 1
        
        if sequential_chain_length > 0:
            dm_energy_before = energy.get(dm_element, 0)
            amplification = seq_gain ** sequential_chain_length
            energy[dm_element] = dm_energy_before * amplification
        
        # 2. Coherent Resonance (合力共振)
        # Count how many stems generate Day Master
        support_count = 0
        for idx in [0, 1, 3]:  # Year, Month, Hour (skip Day itself)
            if stems[idx] and stem_elements[idx]:
                source_elem = stem_elements[idx]
                if GENERATION.get(source_elem) == dm_element:
                    support_count += 1
        
        if support_count >= 2:
            dm_energy_before = energy.get(dm_element, 0)
            resonance_boost = 1 + (support_count - 1) * coherence_boost
            energy[dm_element] = dm_energy_before * resonance_boost
        
        # 3. Multi-Force Cancellation (多重力量抵消)
        # Count supports (generates DM) and controls (controls DM)
        support_count = 0
        control_count = 0
        
        for idx in [0, 1, 3]:  # Year, Month, Hour
            if stems[idx] and stem_elements[idx]:
                source_elem = stem_elements[idx]
                # Check generation (support)
                if GENERATION.get(source_elem) == dm_element:
                    support_count += 1
                # Check control (opposition)
                elif CONTROL.get(source_elem) == dm_element:
                    control_count += 1
        
        if support_count > 0 and control_count > 0:
            dm_energy_before = energy.get(dm_element, 0)
            total_forces = support_count + control_count
            net_energy_ratio = (support_count - control_count * cancel_factor) / total_forces
            
            if net_energy_ratio > 0:
                energy[dm_element] = dm_energy_before * net_energy_ratio
            else:
                # Minimum retention (10% of original)
                energy[dm_element] = dm_energy_before * 0.1
        
        return energy
    
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
