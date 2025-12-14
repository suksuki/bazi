"""
Antigravity V8.8 Phase Change Processor
========================================
Migrated from V8.0/V8.1 Phase Change Protocol

This processor handles special seasonal physics:
- 焦土不生金 (Scorched Earth): Summer earth cannot generate metal
- 冻水不生木 (Frozen Water): Winter water cannot generate wood
- 润局解救 (Humid Rescue): Water presence mitigates scorched earth
- 暖局解救 (Warm Rescue): Fire presence mitigates frozen water
"""

from core.processors.base import BaseProcessor
from core.processors.physics import BRANCH_ELEMENTS
from typing import Dict, Any, Set


class PhaseChangeProcessor(BaseProcessor):
    """
    Layer 2.5: Phase Change Physics
    
    Modifies energy flow efficiency based on seasonal physics.
    """
    
    # === Season Branch Sets ===
    SUMMER_BRANCHES: Set[str] = {'巳', '午', '未'}
    WINTER_BRANCHES: Set[str] = {'亥', '子', '丑'}
    
    # === Water/Fire Rescue Branches ===
    WATER_BRANCHES: Set[str] = {'亥', '子', '辰'}  # Humid markers
    FIRE_BRANCHES: Set[str] = {'巳', '午'}         # Warm markers
    FIRE_STEMS: Set[str] = {'丙', '丁'}             # Fire stems
    
    # === Damping Factors (configurable) ===
    SCORCHED_EARTH_DAMPING = 0.15   # 焦土: 85% reduction
    FROZEN_WATER_DAMPING = 0.30     # 冻水: 70% reduction
    HUMID_RESCUE_EFFICIENCY = 0.80  # 润局: only 20% reduction
    WARM_RESCUE_EFFICIENCY = 0.80   # 暖局: only 20% reduction
    
    @property
    def name(self) -> str:
        return "Phase Change Layer 2.5"
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and calculate phase change effects.
        
        Input context should include:
        - bazi: List of pillars
        - month_branch: e.g., '午'
        - dm_element: e.g., 'metal'
        
        Returns:
            {
                'is_active': bool,
                'phase_type': str or None,
                'resource_efficiency': float (1.0 = normal, 0.15 = scorched)
                'description': str
                'rescue_applied': bool
            }
        """
        month_branch = context.get('month_branch', '')
        dm_element = context.get('dm_element', 'wood')
        bazi = context.get('bazi', [])
        
        # Extract all branches
        branches = [p[1] for p in bazi if len(p) >= 2]
        stems = [p[0] for p in bazi if len(p) >= 1]
        
        result = {
            'is_active': False,
            'phase_type': None,
            'resource_efficiency': 1.0,
            'description': '正常',
            'rescue_applied': False
        }
        
        # === Check Scorched Earth (Summer + Metal DM) ===
        if month_branch in self.SUMMER_BRANCHES and dm_element == 'metal':
            # Check for humid rescue (water presence)
            has_water = any(b in self.WATER_BRANCHES for b in branches)
            
            if has_water:
                result['is_active'] = True
                result['phase_type'] = 'humid_rescue'
                result['resource_efficiency'] = self.HUMID_RESCUE_EFFICIENCY
                result['description'] = f'润局解救 ({month_branch}月有水润土)'
                result['rescue_applied'] = True
            else:
                result['is_active'] = True
                result['phase_type'] = 'scorched_earth'
                result['resource_efficiency'] = self.SCORCHED_EARTH_DAMPING
                result['description'] = f'焦土不生金 ({month_branch}月土燥)'
        
        # === Check Frozen Water (Winter + Wood DM) ===
        elif month_branch in self.WINTER_BRANCHES and dm_element == 'wood':
            # Check for warm rescue (fire presence)
            has_fire_branch = any(b in self.FIRE_BRANCHES for b in branches)
            has_fire_stem = any(s in self.FIRE_STEMS for s in stems)
            has_fire = has_fire_branch or has_fire_stem
            
            if has_fire:
                result['is_active'] = True
                result['phase_type'] = 'warm_rescue'
                result['resource_efficiency'] = self.WARM_RESCUE_EFFICIENCY
                result['description'] = f'暖局解救 ({month_branch}月有火暖局)'
                result['rescue_applied'] = True
            else:
                result['is_active'] = True
                result['phase_type'] = 'frozen_water'
                result['resource_efficiency'] = self.FROZEN_WATER_DAMPING
                result['description'] = f'冻水不生木 ({month_branch}月水寒)'
        
        # === Summer Earth gets dampened (for all DMs) ===
        # This affects earth energy calculation in general
        if month_branch in self.SUMMER_BRANCHES:
            result['summer_earth_penalty'] = 0.6  # Earth is 40% less effective
        else:
            result['summer_earth_penalty'] = 1.0
        
        return result
