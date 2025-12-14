"""
Antigravity V8.8 Hybrid Engine
===============================
Inherits from legacy QuantumEngine for full feature support,
but overrides core strength calculation with modular processors.

This is the production engine for UI.
"""

from typing import Dict, Any, List, Optional
from core.quantum_engine import QuantumEngine
from core.processors import (
    PhysicsProcessor,
    SeasonalProcessor,
    PhaseChangeProcessor,
    StrengthJudge
)


class HybridEngineV88(QuantumEngine):
    """
    V8.8 Hybrid Engine
    
    - Inherits ALL methods from QuantumEngine (get_year_pillar, calculate_year_context, etc.)
    - Overrides _evaluate_wang_shuai with modular processors
    - Best of both worlds: full features + clean algorithm
    """
    
    VERSION = "V8.8-Hybrid"
    
    def __init__(self, params=None):
        """Initialize hybrid engine with both legacy and modular components."""
        # Initialize legacy engine first
        super().__init__(params)
        
        # Initialize modular processors
        self.physics_processor = PhysicsProcessor()
        self.seasonal_processor = SeasonalProcessor()
        self.phase_processor = PhaseChangeProcessor()
        self.strength_judge = StrengthJudge()
        
        print(f"⚡ Antigravity {self.VERSION} Hybrid Engine Initialized")
        print(f"   Modular Processors: 4")
        print(f"   Legacy Features: ✓")
    
    def _evaluate_wang_shuai(self, dm: str, bazi: list) -> tuple:
        """
        Override core strength calculation with modular processors.
        This is where V8.8's clean architecture takes over.
        """
        # Build context
        month_branch = bazi[1][1] if len(bazi) > 1 and len(bazi[1]) > 1 else ''
        dm_element = self.physics_processor._get_element_stem(dm)
        
        context = {
            'bazi': bazi,
            'day_master': dm,
            'dm_element': dm_element,
            'month_branch': month_branch
        }
        
        # === Layer 1: Physics ===
        physics_result = self.physics_processor.process(context)
        raw_energy = physics_result['raw_energy']
        
        # Calculate self + resource
        from core.processors.physics import GENERATION
        resource_element = None
        for mother, child in GENERATION.items():
            if child == dm_element:
                resource_element = mother
                break
        
        e_self = raw_energy.get(dm_element, 0)
        e_resource = raw_energy.get(resource_element, 0) if resource_element else 0
        base_score = e_self + e_resource
        
        # === Layer 2: Seasonal ===
        seasonal_result = self.seasonal_processor.process(context)
        base_score += seasonal_result['in_command_bonus']
        base_score += seasonal_result['resource_month_bonus']
        
        # === Layer 2.5: Phase Change ===
        phase_result = self.phase_processor.process(context)
        resource_efficiency = phase_result['resource_efficiency']
        
        if phase_result['is_active']:
            print(f"[V8.8 Hybrid] {phase_result['description']}")
        
        # === Layer 3: Judgment ===
        judge_context = {
            'base_score': base_score,
            'in_command_bonus': seasonal_result['in_command_bonus'],
            'resource_month_bonus': seasonal_result['resource_month_bonus'],
            'resource_efficiency': resource_efficiency,
            'is_in_command': seasonal_result['is_in_command'],
            'is_resource_month': seasonal_result['is_resource_month']
        }
        
        judgment = self.strength_judge.process(judge_context)
        
        return (judgment['verdict'], judgment['final_score'])
