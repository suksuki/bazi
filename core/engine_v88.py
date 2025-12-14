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
    
    # === Full Feature Methods (migrated from QuantumEngine) ===
    
    def get_year_pillar(self, year: int) -> str:
        """Get the GanZhi for a specific year."""
        try:
            from lunar_python import Solar
            # Use mid-year to avoid boundary issues
            solar = Solar.fromYmdHms(year, 6, 15, 12, 0, 0)
            lunar = solar.getLunar()
            return lunar.getYearInGanZhi()
        except Exception:
            return ""
    
    def _determine_favorable(self, dm: str, wang_shuai: str, bazi: list) -> list:
        """Determine Xi Yong Shen based on Strong/Weak."""
        from core.processors.physics import GENERATION, CONTROL
        dm_elem = self._get_element(dm)
        elements = ["wood", "fire", "earth", "metal", "water"]
        
        # Find resource element (what generates DM)
        resource = None
        for mother, child in GENERATION.items():
            if child == dm_elem:
                resource = mother
                break
        
        # Find output element (what DM generates)
        output = GENERATION.get(dm_elem)
        
        # Find wealth element (what DM controls)
        wealth = CONTROL.get(dm_elem)
        
        # Find officer element (what controls DM)
        officer = None
        for mother, child in CONTROL.items():
            if child == dm_elem:
                officer = mother
                break
        
        if "Strong" in wang_shuai:
            # Strong needs output, wealth, officer
            favorable = [output, wealth, officer]
        else:
            # Weak needs resource and self
            favorable = [resource, dm_elem]
        
        return [e.capitalize() for e in favorable if e]
    
    def calculate_year_score(self, year_pillar: str, favorable: list, unfavorable: list, birth_chart: dict = None) -> dict:
        """Calculate year luck score - simplified V8.8 version."""
        if not year_pillar or len(year_pillar) < 2:
            return {'score': 0, 'details': ['Invalid year pillar']}
        
        year_stem = year_pillar[0]
        year_branch = year_pillar[1]
        
        stem_elem = self._get_element(year_stem).capitalize()
        branch_elem = self._get_element(year_branch).capitalize()
        
        score = 0.0
        details = []
        
        # Stem scoring
        if stem_elem in favorable:
            score += 5.0
            details.append(f"年干 {year_stem}({stem_elem}) 喜用 +5")
        elif stem_elem in unfavorable:
            score -= 3.0
            details.append(f"年干 {year_stem}({stem_elem}) 忌神 -3")
        
        # Branch scoring
        if branch_elem in favorable:
            score += 5.0
            details.append(f"年支 {year_branch}({branch_elem}) 喜用 +5")
        elif branch_elem in unfavorable:
            score -= 3.0
            details.append(f"年支 {year_branch}({branch_elem}) 忌神 -3")
        
        return {'score': score, 'details': details}
    
    def calculate_year_context(self, profile, year: int):
        """
        V8.8 Year Context Calculation.
        Returns a DestinyContext-like object for UI compatibility.
        """
        from core.context import DestinyContext
        
        # Get year pillar
        year_pillar = self.get_year_pillar(year)
        
        # Extract bazi
        bazi_list = [
            profile.pillars.get('year', '甲子'),
            profile.pillars.get('month', '甲子'),
            profile.pillars.get('day', '甲子'),
            profile.pillars.get('hour', '甲子')
        ]
        
        # Calculate strength
        dm = profile.day_master
        strength, score = self._evaluate_wang_shuai(dm, bazi_list)
        
        # Determine favorable elements
        favorable = self._determine_favorable(dm, strength, bazi_list)
        unfavorable = [e.capitalize() for e in ['wood', 'fire', 'earth', 'metal', 'water']
                       if e.capitalize() not in favorable]
        
        # Calculate year score
        year_result = self.calculate_year_score(year_pillar, favorable, unfavorable)
        base_score = year_result.get('score', 0)
        details = year_result.get('details', [])
        
        # Determine icon
        if base_score >= 5:
            icon = "✨"
        elif base_score >= 0:
            icon = "☀️"
        elif base_score >= -3:
            icon = "⚡"
        else:
            icon = "💀"
        
        # Calculate dimension scores based on year score
        # Career benefits from Officer/Wealth elements
        # Wealth benefits from Wealth elements
        # Relationship benefits from Resource/Output elements
        career_score = base_score * 0.8 + 2.0
        wealth_score = base_score * 0.7 + 1.5
        rel_score = base_score * 0.6 + 1.0
        
        # Build context
        ctx = DestinyContext(
            year=year,
            pillar=year_pillar,
            score=base_score,
            icon=icon,
            details=details,
            tags=[],
            risk_level="low" if base_score >= 0 else "medium",
            day_master_strength=strength,
            # Dimension scores for hologram display
            career=career_score,
            wealth=wealth_score,
            relationship=rel_score
        )
        
        return ctx
    
    def calculate_energy(self, case_data: Dict, dynamic_context: Dict = None) -> Dict:
        """
        V8.8 Energy calculation - simplified version.
        Returns energy breakdown for UI display.
        """
        dm_char = case_data.get('day_master', '甲')
        dm_elem = self._get_element(dm_char)
        
        # Get bazi from case_data
        bazi_list = [
            case_data.get('year', '甲子'),
            case_data.get('month', '甲子'),
            case_data.get('day', '甲子'),
            case_data.get('hour', '甲子')
        ]
        
        # Calculate strength using modular processors
        strength, score = self._evaluate_wang_shuai(dm_char, bazi_list)
        
        # Get raw energy from physics processor
        context = {
            'bazi': bazi_list,
            'day_master': dm_char,
            'dm_element': dm_elem,
            'month_branch': bazi_list[1][1] if len(bazi_list) > 1 and len(bazi_list[1]) > 1 else ''
        }
        physics_result = self.physics.process(context)
        raw_energy = physics_result['raw_energy']
        
        # Determine favorable based on strength
        favorable = self._determine_favorable(dm_char, strength, bazi_list)
        
        # Build result
        result = {
            'wang_shuai': strength,
            'wang_shuai_score': score,
            'dm_element': dm_elem,
            'favorable': favorable,
            'energy_map': raw_energy,
            'e_self': raw_energy.get(dm_elem, 0),
            'e_resource': 0,
            'e_output': 0,
            'e_wealth': 0,
            'e_officer': 0,
            'narrative': [f'{strength} ({score:.1f})'],
            'desc': f'{dm_char}日主 {strength}',
            # UI compatibility - dimension scores
            'career': score / 10.0,
            'wealth': score / 10.0,
            'relationship': score / 10.0
        }
        
        # Map energies to ten gods
        from core.processors.physics import GENERATION, CONTROL
        
        for elem, value in raw_energy.items():
            rel = self._get_relation(dm_elem, elem)
            if rel == 'self':
                result['e_self'] = value
            elif rel == 'resource':
                result['e_resource'] = value
            elif rel == 'output':
                result['e_output'] = value
            elif rel == 'wealth':
                result['e_wealth'] = value
            elif rel == 'officer':
                result['e_officer'] = value
        
        return result
    
    def get_luck_timeline(self, profile_or_year, start_year_or_month=None, years_or_day=None,
                          hour=None, gender=None, num_steps=None) -> List[Dict]:
        """
        V8.8 Luck Timeline - simplified version.
        Generates timeline with year pillars and luck info.
        """
        from datetime import datetime
        
        # Detect calling mode
        if hasattr(profile_or_year, 'get_luck_pillar_at'):
            # New interface: BaziProfile object
            profile = profile_or_year
            start_year = start_year_or_month or datetime.now().year
            years = years_or_day if years_or_day else 12
            birth_year = profile.birth_date.year if hasattr(profile, 'birth_date') and profile.birth_date else None
        else:
            # Legacy interface: year, month, day, hour, gender
            birth_year = profile_or_year
            birth_month = start_year_or_month or 1
            birth_day = years_or_day or 1
            birth_hour = hour or 12
            gender_val = gender if gender is not None else 1
            years = num_steps or 8
            
            try:
                from core.bazi_profile import BaziProfile
                birth_date = datetime(birth_year, birth_month, birth_day, birth_hour, 0)
                profile = BaziProfile(birth_date, gender_val)
                start_year = datetime.now().year
            except Exception:
                return []
        
        # Generate timeline
        timeline = []
        prev_luck = None
        
        for i in range(years):
            y = start_year + i
            
            # Get luck pillar for this year
            try:
                current_luck = profile.get_luck_pillar_at(y) if hasattr(profile, 'get_luck_pillar_at') else "未知"
            except:
                current_luck = "未知"
            
            # Detect handover year
            is_handover = (prev_luck is not None and current_luck != prev_luck)
            
            # Calculate age
            age = (y - birth_year) if birth_year else None
            
            # Get year pillar
            year_ganzhi = self.get_year_pillar(y)
            
            timeline.append({
                'year': y,
                'age': age,
                'year_pillar': year_ganzhi,
                'stem': year_ganzhi[0] if year_ganzhi else None,
                'branch': year_ganzhi[1] if len(year_ganzhi) > 1 else None,
                'luck_pillar': current_luck,
                'is_handover': is_handover
            })
            
            prev_luck = current_luck
        
        return timeline
    
    def get_dynamic_luck_pillar(self, profile_or_year, year_or_month=None,
                                day=None, hour=None, gender=None, target_year=None) -> str:
        """
        V8.8 Dynamic Luck Pillar - get luck pillar for a specific year.
        Supports both new (BaziProfile) and legacy (year, month, day, hour, gender, target_year) interfaces.
        """
        from datetime import datetime
        
        # Detect calling mode
        if hasattr(profile_or_year, 'get_luck_pillar_at'):
            # New interface: BaziProfile object
            profile = profile_or_year
            year = year_or_month
            try:
                return profile.get_luck_pillar_at(year)
            except:
                return "未知"
        else:
            # Legacy interface: year, month, day, hour, gender, target_year
            birth_year = profile_or_year
            birth_month = year_or_month or 1
            birth_day = day or 1
            birth_hour = hour or 12
            
            try:
                from core.bazi_profile import BaziProfile
                birth_date = datetime(birth_year, birth_month, birth_day, birth_hour, 0)
                profile = BaziProfile(birth_date, gender or 1)
                return profile.get_luck_pillar_at(target_year)
            except Exception:
                return "计算异常"
