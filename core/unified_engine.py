"""
Antigravity V9.1 Engine (Unified)
==================================
Unified modular engine architecture combining V8.8 and V9.1 features.

This is the main production engine, replacing legacy engines.
Features:
- Modular processor architecture (V8.8)
- Geo-correction support (V9.1)
- Era-aware physics (V9.1)
- Spacetime event detection (V9.1)
"""

from typing import Dict, Any, List, Optional
import logging
import json
import os
from core.processors import (
    PhysicsProcessor,
    SeasonalProcessor,
    PhaseChangeProcessor,
    StrengthJudge
)
from core.processors.geo import GeoProcessor
from core.schemas import (
    AnalysisResponse,
    StrengthResult,
    PhaseChangeInfo,
    UIElement,
    ChartConfig,
    VisualTheme
)

logger = logging.getLogger(__name__)


class UnifiedEngine:
    """
    V9.1 Unified Modular Analysis Engine
    
    This engine delegates all calculations to specialized processors.
    It handles orchestration, response assembly, and spacetime corrections.
    
    Features:
    - Layer 1: Era-Aware Physics (via PhysicsProcessor with Era constants)
    - Layer 0: Geo-Correction (via GeoProcessor)
    - Spacetime Event Detection (Treasury & Skull protocols)
    
    Usage:
        engine = UnifiedEngine()
        result = engine.analyze(['甲子', '丙午', '辛卯', '壬辰'], '辛', city='Beijing')
    """
    
    VERSION = "9.1.0-Spacetime"
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the unified modular engine with all processors."""
        self.config = config or {}
        
        # Initialize core processors (V8.8 modular)
        self.physics = PhysicsProcessor()
        self.seasonal = SeasonalProcessor()
        self.phase_change = PhaseChangeProcessor()
        self.judge = StrengthJudge()
        
        # V9.1: GeoProcessor for Layer 0 (Geo-Correction)
        self.geo = GeoProcessor()
        
        # Initialize sub-engines (from legacy QuantumEngine for full features)
        from core.engines.luck_engine import LuckEngine
        from core.engines.treasury_engine import TreasuryEngine
        from core.engines.skull_engine import SkullEngine
        from core.engines.harmony_engine import HarmonyEngine
        from core.processors.domains import DomainProcessor
        
        self.luck_engine = LuckEngine()
        self.treasury_engine = TreasuryEngine()
        self.skull_engine = SkullEngine()
        self.harmony_engine = HarmonyEngine()
        
        # V9.3 Domain Processor (Restored Logic)
        self.domains = DomainProcessor()
        
        # Suppress Unicode output for Windows compatibility
        try:
            logger.info(f"⚡ Antigravity {self.VERSION} Engine Initialized")
            logger.info(f"   Processors: {len(self._get_processors())}")
            logger.info(f"   Sub-Engines: 4 (Luck, Treasury, Skull, Harmony)")
            logger.info(f"   Features: Geo-Correction, Era-Aware Physics")
        except UnicodeEncodeError:
            logger.info(f"Antigravity {self.VERSION} Engine Initialized")
            logger.info(f"   Processors: {len(self._get_processors())}")
            logger.info(f"   Sub-Engines: 4 (Luck, Treasury, Skull, Harmony)")
            logger.info(f"   Features: Geo-Correction, Era-Aware Physics")
    
    def _get_processors(self) -> List:
        """Get list of active processors"""
        return [self.physics, self.seasonal, self.phase_change, self.judge]
    
    def analyze(self, bazi: List[str], day_master: str, 
                city: str = "Unknown", latitude: Optional[float] = None,
                era_multipliers: Optional[Dict[str, float]] = None,
                **kwargs) -> AnalysisResponse:
        """
        V9.1 Unified Analysis Entry Point.
        
        Args:
            bazi: List of 4 pillars, e.g., ['甲子', '丙午', '辛卯', '壬辰']
            day_master: Day Master character, e.g., '辛'
            city: City name for geo correction
            latitude: Optional latitude override
            era_multipliers: Optional cached era multipliers (for performance optimization)
            **kwargs: Additional arguments (e.g., year for UI display)
        
        Returns:
            AnalysisResponse with full analysis results
        """
        messages = [f"[{self.VERSION}] Starting Spacetime Analysis..."]
        
        # V9.5 Performance Optimization: Load era_multipliers if not provided
        if era_multipliers is None:
            era_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/era_constants.json")
            try:
                with open(era_path, 'r') as f:
                    era_data = json.load(f)
                    era_multipliers = era_data.get('physics_multipliers', {})
            except:
                era_multipliers = {}
        
        # Store for UI display
        era_mods = era_multipliers.copy() if era_multipliers else {}
        
        # Build initial context with era multipliers
        month_branch = bazi[1][1] if len(bazi) > 1 and len(bazi[1]) > 1 else ''
        dm_element = self.physics._get_element_stem(day_master)
        
        context = {
            'bazi': bazi,
            'day_master': day_master,
            'dm_element': dm_element,
            'month_branch': month_branch,
            'era_multipliers': era_multipliers or {}  # V9.5: Pass cached multipliers
        }
        
        # === Stage 1: Physics (Layer 1) - Era-Aware ===
        physics_result = self.physics.process(context)
        raw_energy = physics_result['raw_energy']
        messages.append("[Physics] Applied Era Constants (Period 9)")
        
        # === V9.1 Layer 0: Apply Geo Modifiers ===
        loc_input = latitude if latitude is not None else city
        geo_mods = self.geo.process(loc_input)
        
        if geo_mods:
            mod_desc = geo_mods.get('desc', 'GeoMod')
            messages.append(f"[Geo] Applying {mod_desc}")
            
            for elem, mult in geo_mods.items():
                if elem in raw_energy and isinstance(mult, (int, float)):
                    raw_energy[elem] *= mult
        
        # === Stage 2: Seasonal (Layer 2) ===
        seasonal_result = self.seasonal.process(context)
        is_in_command = seasonal_result['is_in_command']
        is_resource_month = seasonal_result['is_resource_month']
        
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
        
        # Apply bonuses
        base_score += seasonal_result['in_command_bonus']
        base_score += seasonal_result['resource_month_bonus']
        
        if is_in_command:
            messages.append(f"[Seasonal] 得令! +{seasonal_result['in_command_bonus']}")
        if is_resource_month:
            messages.append(f"[Seasonal] 印绶月! +{seasonal_result['resource_month_bonus']}")
        
        # === Stage 3: Phase Change (Layer 2.5) ===
        context['raw_energy_snapshot'] = raw_energy
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
            'is_resource_month': is_resource_month,
            'is_writer_lady': seasonal_result.get('is_writer_lady', False),
            'flags': seasonal_result.get('flags', [])
        }
        
        judgment = self.judge.process(judge_context)
        messages.append(f"[Judge] Verdict provided based on Spacetime Energy.")
        
        # Prepare Delta Factors for UI
        modifiers = {
            "era_json": era_mods,
            "geo_json": geo_mods,
            "city": city,
            "latitude": latitude or "Auto",
            "year": kwargs.get('year', 2024)
        }
        
        # === Build Response ===
        return self._build_response(
            judgment=judgment,
            phase_result=phase_result,
            raw_energy=raw_energy,
            messages=messages,
            modifiers=modifiers
        )
    
    def _build_response(
        self,
        judgment: Dict,
        phase_result: Dict,
        raw_energy: Dict,
        messages: List[str],
        modifiers: Dict = None
    ) -> AnalysisResponse:
        """Assemble the final response object with optional modifiers"""
        
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
        
        # Prepare Dicts directly to guarantee type (V9.1 compatibility)
        strength_dict = {
            "verdict": verdict,
            "raw_score": judgment.get('raw_score', score),
            "adjusted_score": score,
            "confidence": judgment.get('confidence', 0.8),
            "in_command_bonus": judgment.get('in_command_bonus', 0.0),
            "resource_month_bonus": judgment.get('resource_month_bonus', 0.0)
        }
        
        phase_dict = phase_result if phase_result else {"is_active": False, "description": "", "damping_factor": 1.0}
        
        ui_dict = ui.model_dump() if hasattr(ui, 'model_dump') else {
            "display_text": ui.display_text,
            "color_hex": ui.color_hex,
            "icon_name": ui.icon_name,
            "tooltip": ui.tooltip
        }
        
        repo_response = AnalysisResponse(
            strength=strength_dict,
            energy_distribution=raw_energy,
            phase_change=phase_dict,
            ui=ui_dict,
            messages=messages,
            debug={"modifiers": modifiers} if modifiers else None,  # V9.1: Inject modifiers
            engine_version=self.VERSION
        )
        repo_response.chart_config.suggested_theme = theme
        return repo_response
    
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
        """
        V50.0: Update full configuration and propagate to sub-engines.
        This ensures all sub-engines use the latest golden parameters from config/parameters.json.
        """
        self.config = config or {}
        
        # Update sub-engines with new config
        if hasattr(self, 'skull_engine') and self.skull_engine:
            # Extract skull-specific config from interactions.skull.crashScore
            skull_config = self.skull_engine.config.copy()
            if 'interactions' in config and 'skull' in config['interactions']:
                crash_score = config['interactions']['skull'].get('crashScore', -50.0)
                skull_config['score_skull_crash'] = crash_score
                self.skull_engine.skull_crash_score = crash_score
            self.skull_engine.config = skull_config
        
        if hasattr(self, 'treasury_engine') and self.treasury_engine:
            # Treasury engine uses full config structure (reads from interactions.treasury and interactions.vaultPhysics)
            if hasattr(self.treasury_engine, 'update_config'):
                self.treasury_engine.update_config(config)
        
        if hasattr(self, 'harmony_engine') and self.harmony_engine:
            # Harmony engine uses full config structure (reads from interactions.comboPhysics and interactions.branchEvents)
            if hasattr(self.harmony_engine, 'update_config'):
                self.harmony_engine.update_config(config)
        
        # Update processors if they support config
        if hasattr(self, 'physics') and hasattr(self.physics, 'config'):
            if 'physics' in config:
                if isinstance(self.physics.config, dict):
                    self.physics.config.update(config['physics'])
                else:
                    self.physics.config = config['physics']
        
        logger.debug(f"EngineV88 config updated and propagated to sub-engines")
    
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
        V8.8 Year Context Calculation (Full Version).
        Uses all sub-engines for comprehensive analysis.
        """
        from core.context import DestinyContext
        
        # Get year pillar
        year_pillar = self.get_year_pillar(year)
        year_branch = year_pillar[1] if len(year_pillar) > 1 else ''
        
        # Extract bazi
        bazi_list = [
            profile.pillars.get('year', '甲子'),
            profile.pillars.get('month', '甲子'),
            profile.pillars.get('day', '甲子'),
            profile.pillars.get('hour', '甲子')
        ]
        chart_branches = [p[1] for p in bazi_list if len(p) > 1]
        
        # Calculate strength
        dm = profile.day_master
        dm_elem = self._get_element(dm)
        dm_elem_cap = dm_elem.capitalize() if dm_elem else 'Wood'
        strength, strength_score = self._evaluate_wang_shuai(dm, bazi_list)
        
        # Determine favorable elements
        favorable = self._determine_favorable(dm, strength, bazi_list)
        unfavorable = [e.capitalize() for e in ['wood', 'fire', 'earth', 'metal', 'water']
                       if e.capitalize() not in favorable]
        
        # === Layer 1: Base Year Score ===
        year_result = self.calculate_year_score(year_pillar, favorable, unfavorable)
        base_score = year_result.get('score', 0)
        details = year_result.get('details', [])
        tags = []
        icon = None
        risk_level = "low"
        is_treasury_open = False
        treasury_type = None
        treasury_element = None
        
        # === Layer 2: Treasury Engine ===
        try:
            adapter_chart = {
                'day_master': dm,
                'year': bazi_list[0],
                'month': bazi_list[1],
                'day': bazi_list[2],
                'hour': bazi_list[3],
                'dm_strength': strength
            }
            t_score, t_details, t_icon, t_risk = self.treasury_engine.process_treasury_scoring(
                adapter_chart, year_branch, base_score, strength, dm_elem_cap
            )
            base_score = t_score
            if t_details:
                details.extend(t_details)
                # Check if treasury was opened
                for detail in t_details:
                    if '财库' in detail or '墓库' in detail:
                        is_treasury_open = True
                        treasury_element = year_branch
                        if '财库' in detail:
                            treasury_type = "Wealth"
                        elif '官库' in detail:
                            treasury_type = "Power"
                        else:
                            treasury_type = "Resource"
            if t_icon:
                icon = t_icon
            if t_risk and t_risk != 'none':
                risk_level = t_risk
        except Exception as e:
            pass  # Treasury processing optional
        
        # === Layer 3: Harmony Engine (三合六合) ===
        try:
            h_interactions = self.harmony_engine.detect_interactions(chart_branches, year_branch)
            h_score, h_details, h_tags = self.harmony_engine.calculate_harmony_score(h_interactions, favorable)
            base_score += h_score
            details.extend(h_details)
            tags.extend(h_tags)
            if h_score >= 15.0:
                icon = "✨"
        except Exception:
            pass
        
        # === Layer 4: Skull Engine (三刑) ===
        try:
            skull_result = self.skull_engine.detect_three_punishments(chart_branches, year_branch)
            if skull_result.get('triggered'):
                base_score -= 20
                icon = "💀"
                risk_level = "danger"
                details.append(skull_result.get('detail', '三刑触发'))
                tags.append("三刑")
        except Exception:
            pass
        
        # Default icon if not set
        if not icon:
            if base_score >= 5:
                icon = "✨"
            elif base_score >= 0:
                icon = "☀️"
            elif base_score >= -3:
                icon = "⚡"
            else:
                icon = "💀"
        
        # Calculate dimension scores via DomainProcessor
        # Map Year Luck Score back to Domains
        # This is a dynamic estimation. True domain simulation requires re-running physics with year pillar.
        # For efficiency, we approximate: 
        # 1. Identify what the Year Pillar element represents (Ten Gods).
        # 2. If Year is Wealth, boost Wealth Score.
        
        # Determine Year Element Ten God
        # We need stem and branch elements
        y_stem_char = year_pillar[0] if year_pillar else ''
        y_branch_char = year_pillar[1] if len(year_pillar) > 1 else ''
        
        y_stem_elem = self._get_element(y_stem_char)
        y_branch_elem = self._get_element(y_branch_char)
        
        rel_stem = self._get_relation(dm_elem, y_stem_elem) if y_stem_elem else 'unknown'
        rel_branch = self._get_relation(dm_elem, y_branch_elem) if y_branch_elem else 'unknown'
        
        # Base Luck Impact (normalized around 0)
        luck_boost = base_score * 1.0
        
        # Domain Specific Boosts
        # Wealth: Impacted by Wealth element or Output (Source of Wealth)
        wealth_boost = luck_boost
        if rel_stem == 'wealth' or rel_branch == 'wealth':
            wealth_boost += 2.0
        elif rel_stem == 'output' or rel_branch == 'output':
            wealth_boost += 1.0
            
        # Career: Impacted by Officer or Resource (or Output for art)
        career_boost = luck_boost
        if rel_stem == 'officer' or rel_branch == 'officer':
            career_boost += 2.0
        elif rel_stem == 'resource' or rel_branch == 'resource':
            career_boost += 1.5
            
        # Relationship: Spouse Star
        rel_boost = luck_boost
        spouse_rel = 'wealth' if profile.gender == 1 else 'officer'
        if rel_stem == spouse_rel or rel_branch == spouse_rel:
            rel_boost += 2.0
            
        career_score = max(0, 5.0 + career_boost) # Center at 5.0
        wealth_score = max(0, 5.0 + wealth_boost)
        rel_score = max(0, 5.0 + rel_boost)
        
        # Get luck pillar
        try:
            luck_pillar = profile.get_luck_pillar_at(year) if hasattr(profile, 'get_luck_pillar_at') else None
        except:
            luck_pillar = None
        
        # Build context
        ctx = DestinyContext(
            year=year,
            pillar=year_pillar,
            luck_pillar=luck_pillar,
            score=base_score,
            icon=icon,
            details=details,
            tags=tags,
            risk_level=risk_level,
            day_master_strength=strength,
            # Treasury info
            is_treasury_open=is_treasury_open,
            treasury_type=treasury_type,
            treasury_element=treasury_element,
            # Dimension scores
            career=career_score,
            wealth=wealth_score,
            relationship=rel_score
        )
        
        return ctx
    
    def calculate_energy(self, case_data: Dict, dynamic_context: Dict = None,
                        era_multipliers: Optional[Dict[str, float]] = None) -> Dict:
        """
        V9.1 Spacetime Energy Calculation (Unified Version).
        
        Refines V8.8 logic by adding:
        1. Geo-Correction (City/Lat)
        2. Era-Correction (Already in Physics)
        3. Domain Logic (Recalculated with Spacetime Energy)
        4. Spacetime Event Detection (Treasury & Skull)
        
        Args:
            case_data: Case data dictionary
            dynamic_context: Dynamic context (year, dayun, etc.)
            era_multipliers: Optional era multipliers dict (for performance optimization)
        """
        dm_char = case_data.get('day_master', '甲')
        dm_elem = self.physics._get_element_stem(dm_char)
        
        # Get bazi from case_data (support both list and dict formats)
        bazi_list = case_data.get('bazi', [])
        if not bazi_list:
            # Fallback to individual fields
            bazi_list = [
                case_data.get('year', '甲子'),
                case_data.get('month', '甲子'),
                case_data.get('day', '甲子'),
                case_data.get('hour', '甲子')
            ]
        
        # [V9.3 Logic] Dynamic Context Overlay
        # Replace Case Year with Dynamic Year for Time Series Simulation
        current_bazi = list(bazi_list)  # Shallow copy to protect original source
        if dynamic_context and 'year' in dynamic_context:
            # V9.3: Time Series Simulation overrides the Year Pillar (Flow)
            if len(current_bazi) > 0:
                current_bazi[0] = dynamic_context['year']
        
        # 1. Physics (Era-Aware via PhysicsProcessor)
        # V9.5 Performance Optimization: Pass era_multipliers via context to avoid file I/O
        # V21.0: Pass flow_config and interactions_config for complex interactions and coupling effects
        flow_config = self.config.get('flow', {}) if hasattr(self, 'config') else {}
        interactions_config = self.config.get('interactions', {}) if hasattr(self, 'config') else {}
        physics_config = self.config.get('physics', {}) if hasattr(self, 'config') else {}
        pillar_weights = physics_config.get('pillarWeights', {}) if physics_config else {}
        context = {
            'bazi': current_bazi,  # Use the dynamic-aware bazi list
            'day_master': dm_char,
            'dm_element': dm_elem,
            'month_branch': current_bazi[1][1] if len(current_bazi) > 1 and len(current_bazi[1]) > 1 else '',
            'era_multipliers': era_multipliers or {},  # Pass cached multipliers
            'flow_config': flow_config,  # V21.0: Pass flow config for coupling effects
            'interactions_config': interactions_config,  # V21.0: Pass interactions config for complex interactions
            'pillar_weights': pillar_weights  # V22.0: Pass pillar weights to PhysicsProcessor
        }
        physics_result = self.physics.process(context)
        raw_energy = physics_result['raw_energy']
        
        # 2. Geo-Correction (Layer 0)
        # Check case_data for location
        city = case_data.get('city', 'Unknown')
        latitude = case_data.get('latitude', None)
        loc_input = latitude if latitude is not None else city
        
        geo_mods = self.geo.process(loc_input)
        
        # [V9.2 Fix] Neutral Region Fallback
        # Prevent "Unknown" from causing calculation collapse (e.g. NoneType math)
        if not geo_mods and loc_input in ['Unknown', '', None]:
            # Force Beijing-like neutral dict if logic failed
            geo_mods = {}  # Empty dict means multiplier 1.0 (Safe)
        geo_desc = ""
        if geo_mods:
            geo_desc = geo_mods.get('desc', '')
            for elem, mult in geo_mods.items():
                if elem in raw_energy and isinstance(mult, (int, float)):
                    raw_energy[elem] *= mult
        
        # 3. Strength Judge (Recalculate with Geo Energy)
        seasonal_result = self.seasonal.process(context)
        
        # Self/Resource
        resource_element = None
        from core.processors.physics import GENERATION
        for mother, child in GENERATION.items():
            if child == dm_elem:
                resource_element = mother
                break
        
        e_self = raw_energy.get(dm_elem, 0)
        e_resource = raw_energy.get(resource_element, 0) if resource_element else 0
        base_score = e_self + e_resource
        
        base_score += seasonal_result['in_command_bonus']
        base_score += seasonal_result['resource_month_bonus']
        
        # Phase Change
        context['raw_energy_snapshot'] = raw_energy
        phase_result = self.phase_change.process(context)
        resource_efficiency = phase_result['resource_efficiency']
        
        judge_context = {
            'base_score': base_score,
            'in_command_bonus': seasonal_result['in_command_bonus'],
            'resource_month_bonus': seasonal_result['resource_month_bonus'],
            'resource_efficiency': resource_efficiency,
            'is_in_command': seasonal_result['is_in_command'],
            'is_resource_month': seasonal_result['is_resource_month'],
            'is_writer_lady': seasonal_result.get('is_writer_lady', False),
            'flags': seasonal_result.get('flags', [])
        }
        judgment = self.judge.process(judge_context)
        strength = judgment['verdict']
        score = judgment['final_score']
        
        # 4. Domain Logic (V9.3)
        # V16.0: Pass particle weights and physics config from config
        particle_weights = self.config.get('particleWeights', {}) if hasattr(self, 'config') else {}
        observation_bias_config = self.config.get('ObservationBiasFactor', {}) if hasattr(self, 'config') else {}
        
        # V25.0: Ensure particle_weights is not empty (use defaults if missing)
        if not particle_weights:
            particle_weights = {
                'PianCai': 1.3, 'ZhengCai': 1.3, 'ShiShen': 1.4, 'ShangGuan': 1.2,
                'QiSha': 1.15, 'BiJian': 1.5, 'JieCai': 1.1, 'ZhengYin': 0.9,
                'PianYin': 1.1, 'ZhengGuan': 0.85
            }
        # V18.0: Extract dynamic context (luck pillar, annual pillar) for SpacetimeCorrector
        luck_pillar = None
        annual_pillar = None
        if dynamic_context:
            luck_pillar = dynamic_context.get('luck_pillar')
            annual_pillar = dynamic_context.get('pillar') or dynamic_context.get('annual_pillar')
        
        domain_ctx = {
            'raw_energy': raw_energy,  # Now Geo-Corrected!
            'dm_element': dm_elem,
            'strength': {'verdict': strength, 'raw_score': score},
            'gender': case_data.get('gender', 1),
            'particle_weights': particle_weights,  # V16.0: Pass particle weights
            'physics_config': physics_config,  # V16.0: Pass physics config (amplifiers, exponents)
            'observation_bias_config': observation_bias_config,  # V17.0: Pass observation bias factor
            'case_id': case_data.get('case_id', 'Unknown'),  # V16.0: Pass case_id for debug logging
            'luck_pillar': luck_pillar,  # V18.0: Pass luck pillar for SpacetimeCorrector
            'annual_pillar': annual_pillar  # V18.0: Pass annual pillar for SpacetimeCorrector
        }
        domain_res = self.domains.process(domain_ctx)
        
        # [V9.3 Logic] Spacetime Event Detection (Treasury & Skull)
        # Check interactions between Flow Year (Dynamic) and Chart
        flow_year_str = dynamic_context.get('year', '') if dynamic_context else ''
        if flow_year_str and len(flow_year_str) > 1:
            flow_branch = flow_year_str[1]
            st_events = self._check_spacetime_events(dm_char, bazi_list, flow_branch)
            
            # Merge events into domain_details
            if st_events:
                domain_res.update(st_events)
                # Modulate Wealth Score on Open Treasury
                if st_events.get('is_treasury_open'):
                    domain_res['wealth']['score'] *= 1.5  # Massive Bonus
                
                # Modulate Risk on Skull
                if st_events.get('risk_level') == 'danger':
                    # Penalize all scores
                    domain_res['career']['score'] *= 0.6
                    domain_res['wealth']['score'] *= 0.6
                    domain_res['relationship']['score'] *= 0.6

        # Support logic (Favorable)
        favorable = self._determine_favorable(dm_char, strength, bazi_list)
        
        # Assemble Result
        result = {
            'wang_shuai': strength,
            'wang_shuai_score': score,
            'dm_element': dm_elem,
            'favorable': favorable,
            'energy_map': raw_energy,
            'desc': f'{dm_char}日主 {strength} ({judgment["reason"]}) {geo_desc}',
            'career': domain_res['career']['score'] / 10.0,
            'wealth': domain_res['wealth']['score'] / 10.0,
            'relationship': domain_res['relationship']['score'] / 10.0,
            'domain_details': domain_res,
            'phase_info': phase_result
        }
        
        # Map Ten Gods (Simplified)
        # Calculate gods_strength if not in domain_res
        if 'gods_strength' not in domain_res:
            # Calculate ten gods from raw energy
            from core.processors.physics import GENERATION, CONTROL
            elements = ['wood', 'fire', 'earth', 'metal', 'water']
            dm_idx = elements.index(dm_elem) if dm_elem in elements else 0
            
            self_idx = dm_idx
            output_idx = (dm_idx + 1) % 5
            wealth_idx = (dm_idx + 2) % 5
            officer_idx = (dm_idx + 3) % 5
            resource_idx = (dm_idx + 4) % 5
            
            domain_res['gods_strength'] = {
                'self': raw_energy.get(elements[self_idx], 0.0),
                'output': raw_energy.get(elements[output_idx], 0.0),
                'wealth': raw_energy.get(elements[wealth_idx], 0.0),
                'officer': raw_energy.get(elements[officer_idx], 0.0),
                'resource': raw_energy.get(elements[resource_idx], 0.0)
            }
        
        from core.processors.physics import CONTROL
        result['e_self'] = domain_res['gods_strength']['self']
        result['e_output'] = domain_res['gods_strength']['output']
        result['e_wealth'] = domain_res['gods_strength']['wealth']
        result['e_officer'] = domain_res['gods_strength']['officer']
        result['e_resource'] = domain_res['gods_strength']['resource']
        
        # 5. Pillar Energies (API Patch for UI compatibility)
        # Creates a synthetic list of [YearStem, YearBranch, ..., HourBranch] scores
        # based on V9.1 Physics Constants.
        pe_list = []
        base_unit = 8.0
        p_weights = [0.8, 1.2, 1.0, 0.9]  # Year, Month, Day, Hour
        
        # Loop through 4 pillars
        for i in range(4):
            w = p_weights[i]
            # Stem Score
            pe_list.append(base_unit * w)
            # Branch Score (Approx 1.5x for Root+Hidden)
            pe_list.append(base_unit * w * 1.5)
            
        result['pillar_energies'] = pe_list
        
        return result
    
    def _check_spacetime_events(self, dm: str, bazi: List[str], flow_branch: str) -> Dict:
        """
        V9.3 Core Algorithm: Detect Key (Treasury) and Skull (Penalty).
        """
        if not bazi or len(bazi) < 3:
            return {}
        
        # Parse Chart Branches using index 1
        try:
            month_branch = bazi[1][1]
            day_branch = bazi[2][1]
        except:
            return {}
        
        # 1. Determine Wealth Element & Its Tomb
        gan_map = {'甲': 'wood', '乙': 'wood', '丙': 'fire', '丁': 'fire', '戊': 'earth', '己': 'earth',
                   '庚': 'metal', '辛': 'metal', '壬': 'water', '癸': 'water'}
        dm_elem = gan_map.get(dm, 'wood')
        
        # Wealth Map (I control)
        wealth_map = {'wood': 'earth', 'fire': 'metal', 'earth': 'water', 'metal': 'wood', 'water': 'fire'}
        w_elem = wealth_map[dm_elem]
        
        # Tomb Map (Element -> Tomb Branch)
        tomb_map = {'water': '辰', 'earth': '戌', 'fire': '戌', 'metal': '丑', 'wood': '未'}
        w_tomb = tomb_map.get(w_elem)
        
        # Clash Map (Key to open Tomb)
        clash_map = {'辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
        key_branch = clash_map.get(w_tomb)
        
        events = {}
        
        # === KEY: Open Treasury (Wealth Tomb Clash) ===
        # Condition: Day Branch is Wealth Tomb AND Flow Branch is Key (Clash)
        if w_tomb and key_branch:
            if day_branch == w_tomb and flow_branch == key_branch:
                events['is_treasury_open'] = True
                events['icon'] = '🗝️'  # Key
                events['desc'] = f"Open Treasury: {flow_branch} clashes {day_branch} ({w_elem} Vault)"
                events['risk_level'] = 'opportunity'

        # === SKULL: Three Penalties (San Xing) ===
        # Set of branches present in current timeframe (Flow + Month + Day)
        current_branches = {flow_branch, month_branch, day_branch}
        
        # Penalty Sets
        p_earth = {'丑', '未', '戌'}
        p_force = {'寅', '巳', '申'}  # Ungrateful Penalty
        
        if p_earth.issubset(current_branches):
            events['risk_level'] = 'danger'
            events['icon'] = '💀'
            events['desc'] = "Earth Penalty (Triple San Xing) - Obstacles"
            # If simultaneous Open Treasury (e.g. Chou+Wei+Xu contains Wei+Chou clash?),
            # it becomes High Risk Wealth.
            if events.get('is_treasury_open'):
                events['icon'] = '🏴‍☠️'  # Pirate (Danger + Wealth)

        if p_force.issubset(current_branches):
            events['risk_level'] = 'danger'
            events['icon'] = '💀'
            events['desc'] = "Ungrateful Penalty (Tiger-Snake-Monkey)"

        return events
    
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
