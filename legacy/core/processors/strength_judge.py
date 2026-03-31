"""
Antigravity V8.8 Strength Judge
================================
Layer 3: Final Strength Determination

This processor makes the final Strong/Weak/Follower judgment
based on aggregated scores from other processors.
"""

import os
from core.processors.base import BaseProcessor
from typing import Dict, Any, Tuple


def _env_float(name: str, default: float) -> float:
    """Safely parse float from env, fallback to default."""
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class StrengthJudge(BaseProcessor):
    """
    Layer 3: Final Judgment
    
    Takes aggregated scores and makes the verdict.
    Implements fixed thresholds + special overrides.
    """
    
    # === Thresholds (configurable via env offsets) ===
    _BASE_VERY_STRONG = 150.0
    _BASE_STRONG = 80.0
    _BASE_MODERATE = 50.0
    _BASE_WEAK = 20.0
    _BASE_FOLLOWER = -10.0

    # Offsets allow global shifting without code edits
    _SHIFT_VERY_STRONG = _env_float("WANG_SHUAI_SHIFT_VERY_STRONG", 0.0)
    _SHIFT_STRONG = _env_float("WANG_SHUAI_SHIFT_STRONG", 0.0)
    _SHIFT_MODERATE = _env_float("WANG_SHUAI_SHIFT_MODERATE", 0.0)
    _SHIFT_WEAK = _env_float("WANG_SHUAI_SHIFT_WEAK", 0.0)
    _SHIFT_FOLLOWER = _env_float("WANG_SHUAI_SHIFT_FOLLOWER", 0.0)

    THRESHOLD_VERY_STRONG = _BASE_VERY_STRONG + _SHIFT_VERY_STRONG
    THRESHOLD_STRONG = _BASE_STRONG + _SHIFT_STRONG
    THRESHOLD_MODERATE = _BASE_MODERATE + _SHIFT_MODERATE
    THRESHOLD_WEAK = _BASE_WEAK + _SHIFT_WEAK
    THRESHOLD_FOLLOWER = _BASE_FOLLOWER + _SHIFT_FOLLOWER
    
    @property
    def name(self) -> str:
        return "Strength Judge Layer 3"
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make final strength judgment.
        
        Input context should include:
        - base_score: Raw physics score
        - in_command_bonus: 得令加分
        - resource_month_bonus: 印绶月加分
        - resource_efficiency: Phase change modifier
        - is_in_command: bool
        - is_resource_month: bool
        
        Returns:
            {
                'verdict': str,
                'final_score': float,
                'confidence': float,
                'reason': str
            }
        """
        # Extract inputs
        base_score = context.get('base_score', 0.0)
        in_command_bonus = context.get('in_command_bonus', 0.0)
        resource_month_bonus = context.get('resource_month_bonus', 0.0)
        resource_efficiency = context.get('resource_efficiency', 1.0)
        is_in_command = context.get('is_in_command', False)
        is_resource_month = context.get('is_resource_month', False)
        
        # Calculate adjusted score
        raw_total = base_score + in_command_bonus + resource_month_bonus
        adjusted_score = raw_total * resource_efficiency
        
        # === Special Override Rules ===
        
        # Rule 1: 得令必强 (In-Command Override)
        if is_in_command:
            return {
                'verdict': 'Strong',
                'final_score': max(adjusted_score, self.THRESHOLD_STRONG),
                'raw_score': raw_total,
                'confidence': 0.90,
                'reason': '得令覆盖 (Month Command)'
            }

        # Rule 2: Writer Lady Protection (Indulgence Protocol)
        # If output is favorable but DM is weak, and Month is Resource, we allow Survival.
        # This is a special "Protected Weak" or "Functional Strong".
        # V8.1 logic: Treat as Strong for flow purposes (Resource > Output chain).
        flags = context.get('flags', [])
        is_writer_lady = context.get('is_writer_lady', False) or 'writer_lady_protection' in flags
        
        if is_writer_lady:
             return {
                'verdict': 'Strong',
                'final_score': max(adjusted_score, self.THRESHOLD_MODERATE + 5),
                'raw_score': raw_total,
                'confidence': 0.88,
                'reason': '印绶护身 (Writer Lady)'
            }
        
        # Rule 3: 印绶月+高分 = 强
        if is_resource_month and raw_total > self.THRESHOLD_MODERATE:
            return {
                'verdict': 'Strong',
                'final_score': adjusted_score,
                'raw_score': raw_total,
                'confidence': 0.85,
                'reason': '印绶得月 (Resource Month)'
            }
        
        # === Standard Threshold Judgment ===
        verdict, reason = self._threshold_judge(adjusted_score)
        
        return {
            'verdict': verdict,
            'final_score': adjusted_score,
            'raw_score': raw_total,
            'confidence': 0.80,
            'reason': reason
        }
    
    def _threshold_judge(self, score: float) -> Tuple[str, str]:
        """Apply threshold-based judgment"""
        if score >= self.THRESHOLD_VERY_STRONG:
            return ('Strong', '分数极高')
        elif score >= self.THRESHOLD_STRONG:
            return ('Strong', '分数达标')
        elif score >= self.THRESHOLD_MODERATE:
            return ('Moderate', '中和')
        elif score >= self.THRESHOLD_WEAK:
            return ('Weak', '偏弱')
        elif score >= self.THRESHOLD_FOLLOWER:
            return ('Weak', '身弱')
        else:
            return ('Follower', '极弱/从格候选')
    
    def judge_with_overrides(
        self, 
        score: float, 
        is_in_command: bool = False,
        is_resource_month: bool = False,
        resource_efficiency: float = 1.0
    ) -> Dict[str, Any]:
        """
        Convenience method for direct judgment.
        """
        return self.process({
            'base_score': score,
            'in_command_bonus': 0.0,
            'resource_month_bonus': 0.0,
            'resource_efficiency': resource_efficiency,
            'is_in_command': is_in_command,
            'is_resource_month': is_resource_month
        })
