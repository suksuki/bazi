"""
Antigravity V8.8 Seasonal Processor
=====================================
Layer 2: Month Command & Seasonal Adjustments

This processor handles:
- 得令 (In-Command) detection and bonus
- 印绶月 (Resource Month) detection and bonus
- Basic seasonal element strength
"""

from core.processors.base import BaseProcessor
from core.processors.physics import GENERATION, STEM_ELEMENTS, BRANCH_ELEMENTS
from typing import Dict, Any


class SeasonalProcessor(BaseProcessor):
    """
    Layer 2: Seasonal & Month Command Calculator
    
    Determines if Day Master is supported by the month.
    """
    
    # === Configurable Weights ===
    IN_COMMAND_BONUS = 150.0     # 得令 - Month branch same element as DM
    RESOURCE_MONTH_BONUS = 75.0  # 印绶月 - Month branch generates DM
    
    # Month element prosperity levels
    MONTH_PROSPERITY = {
        # Spring (Wood prospers)
        '寅': {'wood': 1.2, 'fire': 0.8, 'earth': 0.6, 'metal': 0.7, 'water': 1.0},
        '卯': {'wood': 1.3, 'fire': 0.9, 'earth': 0.5, 'metal': 0.6, 'water': 0.9},
        '辰': {'wood': 1.0, 'fire': 0.8, 'earth': 1.0, 'metal': 0.7, 'water': 1.1},
        
        # Summer (Fire prospers)
        '巳': {'wood': 0.8, 'fire': 1.2, 'earth': 1.0, 'metal': 0.5, 'water': 0.6},
        '午': {'wood': 0.7, 'fire': 1.3, 'earth': 1.1, 'metal': 0.4, 'water': 0.5},
        '未': {'wood': 0.6, 'fire': 1.0, 'earth': 1.2, 'metal': 0.5, 'water': 0.5},
        
        # Autumn (Metal prospers)
        '申': {'wood': 0.6, 'fire': 0.7, 'earth': 1.0, 'metal': 1.2, 'water': 0.9},
        '酉': {'wood': 0.5, 'fire': 0.6, 'earth': 0.9, 'metal': 1.3, 'water': 1.0},
        '戌': {'wood': 0.6, 'fire': 0.8, 'earth': 1.1, 'metal': 1.0, 'water': 0.7},
        
        # Winter (Water prospers)
        '亥': {'wood': 0.9, 'fire': 0.5, 'earth': 0.6, 'metal': 0.9, 'water': 1.2},
        '子': {'wood': 0.8, 'fire': 0.4, 'earth': 0.5, 'metal': 1.0, 'water': 1.3},
        '丑': {'wood': 0.7, 'fire': 0.5, 'earth': 1.0, 'metal': 1.1, 'water': 1.0},
    }
    
    @property
    def name(self) -> str:
        return "Seasonal Layer 2"
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate seasonal adjustments (Genesis Reconstruction).
        
        Logic:
        1. Monthly Command (月令提纲): The King of the chart.
        2. Resource Support (印绶): Motherly support.
        
        Bonuses are returned as Absolute Points to be added to DM Strength.
        """
        month_branch = context.get('month_branch', '')
        dm_element = context.get('dm_element', 'wood')
        
        # 1. Resolve Month Element
        month_element = BRANCH_ELEMENTS.get(month_branch, 'earth')
        
        # 2. Determine Relationship (Command vs Resource)
        is_in_command = (month_element == dm_element)
        
        resource_element = None
        for mother, child in GENERATION.items():
            if child == dm_element:
                resource_element = mother
                break
        is_resource_month = (month_element == resource_element)
        
        # 3. Calculate Genesis Bonuses (Hardcoded)
        # "Huge Bonus" strategy:
        # 1 Stem = 10 pts.
        # In-Command = Worth 5 Stems (50 pts).
        # Resource Month = Worth 3 Stems (30 pts).
        
        bonus_command = 50.0 if is_in_command else 0.0
        bonus_resource = 30.0 if is_resource_month else 0.0
        
        # 4. Writer Lady Flag (Survival Pattern)
        # Weak Day Master (not in command) but born in Resource Month -> Special Protection
        is_writer_lady = False
        if is_resource_month and not is_in_command:
            is_writer_lady = True

        return {
            'is_in_command': is_in_command,
            'is_resource_month': is_resource_month,
            'in_command_bonus': bonus_command,
            'resource_month_bonus': bonus_resource,
            'month_element': month_element,
            'is_writer_lady': is_writer_lady,
            'flags': [k for k, v in locals().items() if k.startswith('is_') and v]
        }
