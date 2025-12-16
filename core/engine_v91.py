from typing import List, Dict, Any, Optional
from core.engine_v88 import EngineV88
from core.processors.geo import GeoProcessor
from core.schemas.ui_protocol import AnalysisResponse, UIElement, VisualTheme, StrengthResult, PhaseChangeInfo

class EngineV91(EngineV88):
    """
    Antigravity V9.1 Spacetime Fusion Engine
    
    Integrates:
    - Layer 1: Era-Aware Physics (via V9.1 refined PhysicsProcessor)
      * Automatically applies Period 9 constants loaded from JSON
    - Layer 0: Geo-Correction (via GeoProcessor)
      * Applies location-based modifiers (City or Latitude)
    """
    
    VERSION = "9.1.0-Spacetime"

    def __init__(self):
        super().__init__()
        # GeoProcessor for Layer 0
        self.geo = GeoProcessor()
        # Physics is already initialized in super().__init__(), and it now reads Era constants.

    # ... (inside EngineV91)

    def analyze(self, bazi: List[str], day_master: str, 
                city: str = "Unknown", latitude: Optional[float] = None,
                era_multipliers: Optional[Dict[str, float]] = None,
                **kwargs) -> AnalysisResponse:
        """
        V9.1 Analysis Entry Point.
        
        Args:
            bazi: List of 4 pillars
            day_master: Day master character
            city: City name for geo correction
            latitude: Optional latitude override
            era_multipliers: Optional cached era multipliers (for performance optimization)
            **kwargs: Additional arguments (e.g., year for UI display)
        """
        messages = [f"[{self.VERSION}] Starting Spacetime Analysis..."]
        
        # V9.5 Performance Optimization: Load era_multipliers if not provided
        # (backward compatibility - allows callers to pass cached multipliers)
        if era_multipliers is None:
            import json, os
            era_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/era_constants.json")
            try:
                with open(era_path, 'r') as f:
                    era_data = json.load(f)
                    era_multipliers = era_data.get('physics_multipliers', {})
            except:
                era_multipliers = {}
        
        # Store for UI display
        era_mods = era_multipliers.copy() if era_multipliers else {}
        
        # 1. Physics Context
        dm_element = self.physics._get_element_stem(day_master)
        context = {
            'bazi': bazi,
            'day_master': day_master,
            'dm_element': dm_element,
            'month_branch': bazi[1][1] if len(bazi) > 1 else '',
            'era_multipliers': era_multipliers or {}  # V9.5: Pass cached multipliers
        }
        
        # 2. Run Physics (Era-Aware)
        physics_result = self.physics.process(context)
        raw_energy = physics_result['raw_energy']
        messages.append("[Physics] Applied Era Constants (Period 9)")
        
        # 3. Apply Geo Modifiers (Layer 0)
        loc_input = latitude if latitude is not None else city
        geo_mods = self.geo.process(loc_input)
        
        if geo_mods:
            mod_desc = geo_mods.get('desc', 'GeoMod')
            messages.append(f"[Geo] Applying {mod_desc}")
            
            for elem, mult in geo_mods.items():
                if elem in raw_energy and isinstance(mult, (int, float)):
                    raw_energy[elem] *= mult
                    
        # 4. Continue Pipeline (Seasonal, Phase, Judge)
        seasonal_result = self.seasonal.process(context)
        
        resource_element = None
        from core.processors.physics import GENERATION
        for mother, child in GENERATION.items():
            if child == dm_element:
                resource_element = mother
                break
        
        e_self = raw_energy.get(dm_element, 0)
        e_resource = raw_energy.get(resource_element, 0) if resource_element else 0
        base_score = e_self + e_resource
        
        base_score += seasonal_result['in_command_bonus']
        base_score += seasonal_result['resource_month_bonus']
        
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
        
        messages.append(f"[Judge] Verdict provided based on Spacetime Energy.")
        
        # Prepare Delta Factors for UI
        modifiers = {
            "era_json": era_mods,
            "geo_json": geo_mods,
            "city": city,
            "latitude": latitude or "Auto",
            "year": kwargs.get('year', 2024)
        }
        
        return self._build_response(
            judgment=judgment,
            phase_result=phase_result,
            raw_energy=raw_energy,
            messages=messages,
            modifiers=modifiers  # Pass to new _build_response
        )

    def _build_response(
        self,
        judgment: Dict,
        phase_result: Dict,
        raw_energy: Dict,
        messages: List[str],
        modifiers: Dict = None
    ) -> AnalysisResponse:
        """Override to include debug.modifiers"""
        # Call super (or replicate logic, since super doesn't accept modifiers)
        # Replicating logic is safer to avoid argument mismatch
        
        verdict = judgment['verdict']
        score = judgment['final_score']
        reason = judgment['reason']
        
        # ... logic from EngineV88 ...
        # imports moved to top level
        
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
            
        # Prepare Dicts directly to guarantee type
        strength_dict = {
            "verdict": verdict,
            "raw_score": judgment.get('raw_score', score),
            "adjusted_score": score,
            "confidence": judgment.get('confidence', 0.8),
            "in_command_bonus": judgment.get('in_command_bonus', 0.0),
            "resource_month_bonus": judgment.get('resource_month_bonus', 0.0)
        }
        
        phase_dict = phase_result if phase_result else {"is_active": False, "description": "", "damping_factor": 1.0}
        
        ui_dict = ui.model_dump() # ui is already instantiated above, convert to dict
            
        repo_response = AnalysisResponse(
            strength=strength_dict,
            energy_distribution=raw_energy,
            phase_change=phase_dict,
            ui=ui_dict,
            messages=messages,
            debug={"modifiers": modifiers} if modifiers else None, # Inject here
            engine_version=self.VERSION
        )
        repo_response.chart_config.suggested_theme = theme
        return repo_response
    def calculate_energy(self, case_data: Dict, dynamic_context: Dict = None, 
                        era_multipliers: Optional[Dict[str, float]] = None) -> Dict:
        """
        V9.1 Spacetime Energy Calculation (Backwards Compatible / Dashboard Ready).
        
        Refines V8.8 logic by adding:
        1. Geo-Correction (City/Lat)
        2. Era-Correction (Already in Physics)
        3. Domain Logic (Recalculated with Spacetime Energy)
        
        Args:
            case_data: Case data dictionary
            dynamic_context: Dynamic context (year, dayun, etc.)
            era_multipliers: Optional era multipliers dict (for performance optimization)
        """
        dm_char = case_data.get('day_master', '甲')
        dm_elem = self.physics._get_element_stem(dm_char)
        
        # Get bazi
        bazi_list = case_data.get('bazi', [])
        
        # [V9.3 Logic] Dynamic Context Overlay
        # Replace Case Year with Dynamic Year for Time Series Simulation
        current_bazi = list(bazi_list) # Shallow copy to protect original source
        if dynamic_context and 'year' in dynamic_context:
             # V9.3: Time Series Simulation overrides the Year Pillar (Flow)
             if len(current_bazi) > 0:
                 current_bazi[0] = dynamic_context['year']
             else:
                 # DEBUG: Why is bazi empty?
                 # import streamlit as st
                 # st.error("CRITICAL: Engine received empty Bazi List!")
                 pass
        
        # 1. Physics (Era-Aware via PhysicsProcessor)
        # V9.5 Performance Optimization: Pass era_multipliers via context to avoid file I/O
        # V21.0: Pass flow_config and interactions_config for complex interactions and coupling effects
        flow_config = self.config.get('flow', {}) if hasattr(self, 'config') else {}
        interactions_config = self.config.get('interactions', {}) if hasattr(self, 'config') else {}
        physics_config = self.config.get('physics', {}) if hasattr(self, 'config') else {}
        pillar_weights = physics_config.get('pillarWeights', {}) if physics_config else {}
        context = {
            'bazi': current_bazi, # Use the dynamic-aware bazi list
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
            # Beijing is roughly neutral for basic phase mapping in V9.1 defaults
            geo_mods = {} # Empty dict means multiplier 1.0 (Safe)
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
        domain_ctx = {
            'raw_energy': raw_energy, # Now Geo-Corrected!
            'dm_element': dm_elem,
            'strength': {'verdict': strength, 'raw_score': score},
            'gender': case_data.get('gender', 1)
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
                    domain_res['wealth']['score'] *= 1.5 # Massive Bonus
                    # Append desc
                    current_desc = result.get('desc', '') if 'result' in locals() else '' # result not defined yet
                
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
        p_weights = [0.8, 1.2, 1.0, 0.9] # Year, Month, Day, Hour
        
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
        if not bazi or len(bazi) < 3: return {}
        
        # Parse Chart Branches using index 1
        try:
            month_branch = bazi[1][1]
            day_branch = bazi[2][1]
        except: return {}
        
        # 1. Determine Wealth Element & Its Tomb
        gan_map = {'甲':'wood', '乙':'wood', '丙':'fire', '丁':'fire', '戊':'earth', '己':'earth', '庚':'metal', '辛':'metal', '壬':'water', '癸':'water'}
        dm_elem = gan_map.get(dm, 'wood')
        
        # Wealth Map (I control)
        wealth_map = {'wood':'earth', 'fire':'metal', 'earth':'water', 'metal':'wood', 'water':'fire'}
        w_elem = wealth_map[dm_elem]
        
        # Tomb Map (Element -> Tomb Branch)
        tomb_map = {'water':'辰', 'earth':'戌', 'fire':'戌', 'metal':'丑', 'wood':'未'}
        w_tomb = tomb_map.get(w_elem)
        
        # Clash Map (Key to open Tomb)
        clash_map = {'辰':'戌', '戌':'辰', '丑':'未', '未':'丑'}
        key_branch = clash_map.get(w_tomb)
        
        events = {}
        
        # === KEY: Open Treasury (Wealth Tomb Clash) ===
        # Condition: Day Branch is Wealth Tomb AND Flow Branch is Key (Clash)
        if w_tomb and key_branch:
            if day_branch == w_tomb and flow_branch == key_branch:
                 events['is_treasury_open'] = True
                 events['icon'] = '🗝️' # Key
                 events['desc'] = f"Open Treasury: {flow_branch} clashes {day_branch} ({w_elem} Vault)"
                 events['risk_level'] = 'opportunity'

        # === SKULL: Three Penalties (San Xing) ===
        # Set of branches present in current timeframe (Flow + Month + Day)
        current_branches = {flow_branch, month_branch, day_branch}
        
        # Penalty Sets
        p_earth = {'丑', '未', '戌'}
        p_force = {'寅', '巳', '申'} # Ungrateful Penalty
        
        if p_earth.issubset(current_branches):
            events['risk_level'] = 'danger'
            events['icon'] = '💀'
            events['desc'] = "Earth Penalty (Triple San Xing) - Obstacles"
            # If simultaneous Open Treasury (e.g. Chou+Wei+Xu contains Wei+Chou clash?), 
            # it becomes High Risk Wealth.
            if events.get('is_treasury_open'):
                 events['icon'] = '🏴‍☠️' # Pirate (Danger + Wealth)

        if p_force.issubset(current_branches):
            events['risk_level'] = 'danger'
            events['icon'] = '💀'
            events['desc'] = "Ungrateful Penalty (Tiger-Snake-Monkey)"

        return events
