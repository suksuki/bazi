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
        Calculate seasonal adjustments.
        
        Input context should include:
        - month_branch: e.g., '午'
        - dm_element: e.g., 'metal'
        
        Returns:
            {
                'is_in_command': bool,
                'is_resource_month': bool,
                'in_command_bonus': float,
                'resource_month_bonus': float,
                'seasonal_multipliers': {element: multiplier}
            }
        """
        month_branch = context.get('month_branch', '')
        dm_element = context.get('dm_element', 'wood')
        
        # Get month element
        month_element = BRANCH_ELEMENTS.get(month_branch, 'earth')
        
        # Check 得令 (In-Command)
        is_in_command = (month_element == dm_element)
        
        # Check 印绶月 (Resource Month)
        # Resource is what generates DM
        resource_element = None
        for mother, child in GENERATION.items():
            if child == dm_element:
                resource_element = mother
                break
        
        is_resource_month = (month_element == resource_element)
        
        # Calculate bonuses
        in_command_bonus = self.IN_COMMAND_BONUS if is_in_command else 0.0
        resource_month_bonus = self.RESOURCE_MONTH_BONUS if is_resource_month else 0.0
        
        # Get prosperity multipliers for this month
        seasonal_mults = self.MONTH_PROSPERITY.get(month_branch, {
            'wood': 1.0, 'fire': 1.0, 'earth': 1.0, 'metal': 1.0, 'water': 1.0
        })
        
        return {
            'is_in_command': is_in_command,
            'is_resource_month': is_resource_month,
            'in_command_bonus': in_command_bonus,
            'resource_month_bonus': resource_month_bonus,
            'month_element': month_element,
            'resource_element': resource_element,
            'seasonal_multipliers': seasonal_mults,
            'dm_prosperity': seasonal_mults.get(dm_element, 1.0)
        }
