"""
Antigravity V8.8 Engine
========================
New modular engine architecture.

This is a PARALLEL implementation alongside the legacy QuantumEngine.
Use this for testing the new architecture while keeping backward compatibility.
"""

from typing import Dict, Any, List, Optional
from core.processors import (
    PhysicsProcessor,
    SeasonalProcessor,
    PhaseChangeProcessor,
    StrengthJudge
)
from core.schemas import (
    AnalysisResponse,
    StrengthResult,
    PhaseChangeInfo,
    UIElement,
    ChartConfig,
    VisualTheme
)


class EngineV88:
    """
    V8.8 Modular Analysis Engine
    
    This engine delegates all calculations to specialized processors.
    It only handles orchestration and response assembly.
    
    Usage:
        engine = EngineV88()
        result = engine.analyze(['甲子', '丙午', '辛卯', '壬辰'], '辛')
    """
    
    VERSION = "V8.8"
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the modular engine with all processors."""
        self.config = config or {}
        
        # Initialize processors
        self.physics = PhysicsProcessor()
        self.seasonal = SeasonalProcessor()
        self.phase_change = PhaseChangeProcessor()
        self.judge = StrengthJudge()
        
        print(f"⚡ Antigravity {self.VERSION} Engine Initialized")
        print(f"   Processors: {len(self._get_processors())}")
    
    def _get_processors(self) -> List:
        """Get list of active processors"""
        return [self.physics, self.seasonal, self.phase_change, self.judge]
    
    def analyze(self, bazi: List[str], day_master: str) -> AnalysisResponse:
        """
        Main analysis entry point.
        
        Args:
            bazi: List of 4 pillars, e.g., ['甲子', '丙午', '辛卯', '壬辰']
            day_master: Day Master character, e.g., '辛'
        
        Returns:
            AnalysisResponse with full analysis results
        """
        messages = [f"[{self.VERSION}] Starting analysis..."]
        
        # Build initial context
        month_branch = bazi[1][1] if len(bazi) > 1 and len(bazi[1]) > 1 else ''
        dm_element = self.physics._get_element_stem(day_master)
        
        context = {
            'bazi': bazi,
            'day_master': day_master,
            'dm_element': dm_element,
            'month_branch': month_branch
        }
        
        # === Stage 1: Physics (Layer 1) ===
        physics_result = self.physics.process(context)
        raw_energy = physics_result['raw_energy']
        messages.append(f"[Physics] Raw energy: {raw_energy}")
        
        # Calculate self+resource vs others
        resource_element = None
        from core.processors.physics import GENERATION
        for mother, child in GENERATION.items():
            if child == dm_element:
                resource_element = mother
                break
        
        e_self = raw_energy.get(dm_element, 0)
        e_resource = raw_energy.get(resource_element, 0) if resource_element else 0
        base_score = e_self + e_resource
        
        # === Stage 2: Seasonal (Layer 2) ===
        seasonal_result = self.seasonal.process(context)
        is_in_command = seasonal_result['is_in_command']
        is_resource_month = seasonal_result['is_resource_month']
        
        # Apply bonuses
        base_score += seasonal_result['in_command_bonus']
        base_score += seasonal_result['resource_month_bonus']
        
        if is_in_command:
            messages.append(f"[Seasonal] 得令! +{seasonal_result['in_command_bonus']}")
        if is_resource_month:
            messages.append(f"[Seasonal] 印绶月! +{seasonal_result['resource_month_bonus']}")
        
        # === Stage 3: Phase Change (Layer 2.5) ===
        phase_result = self.phase_change.process(context)
        resource_efficiency = phase_result['resource_efficiency']
        
        if phase_result['is_active']:
            messages.append(f"[Phase] {phase_result['description']} (效率: {resource_efficiency})")
        
        # === Stage 4: Final Judgment (Layer 3) ===
        judge_context = {
            'base_score': base_score,
            'in_command_bonus': seasonal_result['in_command_bonus'],
            'resource_month_bonus': seasonal_result['resource_month_bonus'],
            'resource_efficiency': resource_efficiency,
            'is_in_command': is_in_command,
            'is_resource_month': is_resource_month
        }
        
        judgment = self.judge.process(judge_context)
        messages.append(f"[Judge] Verdict: {judgment['verdict']} ({judgment['reason']})")
        
        # === Build Response ===
        return self._build_response(
            judgment=judgment,
            phase_result=phase_result,
            raw_energy=raw_energy,
            messages=messages
        )
    
    def _build_response(
        self,
        judgment: Dict,
        phase_result: Dict,
        raw_energy: Dict,
        messages: List[str]
    ) -> AnalysisResponse:
        """Assemble the final response object"""
        
        verdict = judgment['verdict']
        score = judgment['final_score']
        reason = judgment['reason']
        
        # Determine UI styling based on verdict and phase
        if verdict == 'Strong':
            ui = UIElement(
                display_text=f"身强 ({reason})",
                color_hex="#27AE60",
                icon_name="shield-check",
                tooltip=f"最终分数: {score:.1f}"
            )
            theme = VisualTheme.PROSPERITY
        elif verdict == 'Weak' and phase_result['is_active']:
            ui = UIElement(
                display_text=f"身弱 ({phase_result['description']})",
                color_hex="#E67E22",
                icon_name="fire-alert",
                tooltip=f"相变效应触发"
            )
            theme = VisualTheme.WARNING
        else:
            ui = UIElement(
                display_text=f"身弱 ({reason})",
                color_hex="#E74C3C",
                icon_name="alert-triangle",
                tooltip=f"最终分数: {score:.1f}"
            )
            theme = VisualTheme.NORMAL
        
        return AnalysisResponse(
            strength=StrengthResult(
                verdict=verdict,
                raw_score=judgment.get('raw_score', score),
                adjusted_score=score,
                confidence=judgment.get('confidence', 0.8)
            ),
            energy_distribution=raw_energy,
            phase_change=PhaseChangeInfo(
                is_active=phase_result['is_active'],
                phase_type=phase_result.get('phase_type'),
                damping_factor=phase_result['resource_efficiency'],
                description=phase_result['description']
            ),
            ui=ui,
            chart_config=ChartConfig(
                suggested_theme=theme
            ),
            messages=messages,
            engine_version=self.VERSION
        )
    
    def evaluate_strength(self, day_master: str, bazi: List[str]) -> tuple:
        """
        Legacy-compatible interface.
        Returns (verdict, score) tuple like _evaluate_wang_shuai.
        """
        result = self.analyze(bazi, day_master)
        return (result.strength.verdict, result.strength.adjusted_score)
    
    # === Legacy Compatibility Methods ===
    # These methods mirror QuantumEngine's interface for easy migration
    
    def _get_element(self, char: str) -> str:
        """Get element for stem or branch character (legacy compat)"""
        from core.processors.physics import STEM_ELEMENTS, BRANCH_ELEMENTS
        if char in STEM_ELEMENTS:
            return STEM_ELEMENTS[char]
        if char in BRANCH_ELEMENTS:
            return BRANCH_ELEMENTS[char]
        return 'earth'  # default
    
    def _get_relation(self, dm_elem: str, target_elem: str) -> str:
        """Get relation between DM element and target (legacy compat)"""
        from core.processors.physics import get_relation
        return get_relation(dm_elem, target_elem)
    
    def _evaluate_wang_shuai(self, dm: str, bazi: List[str]) -> tuple:
        """Legacy method name compatibility"""
        return self.evaluate_strength(dm, bazi)
    
    def update_full_config(self, config: Dict) -> None:
        """Update configuration (legacy compat - currently no-op)"""
        self.config = config
        # V8.8 doesn't use config yet, but we accept it for compatibility
        pass
