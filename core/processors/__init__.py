"""
Antigravity V8.8 Processors Package
=====================================
Modular processing pipeline for Bazi analysis.

Each processor handles one specific aspect:
- PhysicsProcessor: Raw five-element energy calculation
- SeasonalProcessor: Month command and seasonal adjustments
- PhaseChangeProcessor: Special seasonal physics (scorched/frozen)
- StrengthJudge: Final strength determination
"""

from core.processors.base import BaseProcessor
from core.processors.physics import PhysicsProcessor, get_relation, GENERATION, CONTROL
from core.processors.seasonal import SeasonalProcessor
from core.processors.phase_change import PhaseChangeProcessor
from core.processors.strength_judge import StrengthJudge

__all__ = [
    'BaseProcessor',
    'PhysicsProcessor',
    'SeasonalProcessor', 
    'PhaseChangeProcessor',
    'StrengthJudge',
    'get_relation',
    'GENERATION',
    'CONTROL'
]
