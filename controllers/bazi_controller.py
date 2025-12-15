"""
BaziController - MVC Controller Layer
=====================================
V9.5 MVC Architecture - Zero Modification Refactor

This controller encapsulates all Model interactions:
- BaziCalculator (Chart Generation)
- FluxEngine (Energy State Calculation)
- QuantumEngine V9.1 (Quantum Physics + Geo Correction)

View components (P1, P2, P3) should ONLY interact with this controller.
"""

import datetime
import copy
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

# Model Imports
from core.calculator import BaziCalculator
from core.flux import FluxEngine
from core.engine_v91 import EngineV91 as QuantumEngine
from core.bazi_profile import BaziProfile


class BaziController:
    """
    Central Controller for Bazi Prediction System.
    
    Responsibilities:
    - Accept user input from View
    - Coordinate Model calculations
    - Return structured data for View rendering
    """
    
    VERSION = "9.5.0-MVC"
    
    def __init__(self):
        """Initialize controller with lazy-loaded models."""
        # Models (Lazy Initialization)
        self._calc: Optional[BaziCalculator] = None
        self._flux_engine: Optional[FluxEngine] = None
        self._quantum_engine: Optional[QuantumEngine] = None
        self._profile: Optional[BaziProfile] = None
        
        # State Cache
        self._user_input: Dict[str, Any] = {}
        self._chart: Optional[Dict] = None
        self._luck_cycles: Optional[List] = None
        self._flux_data: Optional[Dict] = None
        self._details: Optional[Dict] = None
        
        # Computed State
        self._gender_idx: int = 1
        self._city: str = "Unknown"
        
    # =========================================================================
    # Input Management
    # =========================================================================
    
    def set_user_input(self, name: str, gender: str, date_obj: datetime.date, 
                       time_int: int, city: str = "Unknown",
                       enable_solar: bool = True, longitude: float = 116.46) -> None:
        """
        Set user input and trigger base calculations.
        
        Args:
            name: User's name
            gender: "男" or "女"
            date_obj: Birth date
            time_int: Birth hour (0-23)
            city: Birth city for geo correction
            enable_solar: Enable solar time correction
            longitude: Longitude for solar time
        """
        self._user_input = {
            'name': name,
            'gender': gender,
            'date': date_obj,
            'time': time_int,
            'city': city,
            'enable_solar': enable_solar,
            'longitude': longitude
        }
        
        self._gender_idx = 1 if "男" in gender else 0
        self._city = city if city and city.lower() not in ['unknown', 'none', ''] else "Beijing"
        
        # Trigger base calculations
        self._calculate_base()
        
    def _calculate_base(self) -> None:
        """Internal: Calculate base chart and initialize engines."""
        if not self._user_input:
            return
            
        d = self._user_input['date']
        t = self._user_input['time']
        lng = self._user_input.get('longitude', 120.0)
        
        # 1. BaziCalculator
        self._calc = BaziCalculator(d.year, d.month, d.day, t, 0, longitude=lng)
        self._chart = self._calc.get_chart()
        self._details = self._calc.get_details()
        self._luck_cycles = self._calc.get_luck_cycles(self._gender_idx)
        
        # 2. FluxEngine
        self._flux_engine = FluxEngine(self._chart)
        
        # 3. QuantumEngine (Singleton-like)
        if self._quantum_engine is None:
            self._quantum_engine = QuantumEngine()
            
        # 4. BaziProfile
        birth_dt = datetime.datetime.combine(d, datetime.time(t, 0))
        self._profile = BaziProfile(birth_dt, self._gender_idx)
        
    # =========================================================================
    # Chart & Basic Data Accessors
    # =========================================================================
    
    def get_chart(self) -> Dict:
        """Return the calculated Bazi chart."""
        return self._chart or {}
        
    def get_details(self) -> Dict:
        """Return calculation details."""
        return self._details or {}
        
    def get_luck_cycles(self) -> List[Dict]:
        """Return the Da Yun (Great Luck) cycles list."""
        return self._luck_cycles or []
        
    def get_calculator(self) -> Optional[BaziCalculator]:
        """Return the BaziCalculator instance (for advanced usage)."""
        return self._calc
        
    # =========================================================================
    # FluxEngine Interface
    # =========================================================================
    
    def get_flux_engine(self) -> Optional[FluxEngine]:
        """Return the FluxEngine instance."""
        return self._flux_engine
        
    def get_flux_data(self, selected_yun: Optional[Dict] = None, 
                      current_gan_zhi: Optional[str] = None) -> Dict:
        """
        Compute and return flux energy state.
        
        Args:
            selected_yun: Selected Da Yun dict with 'gan_zhi' key
            current_gan_zhi: Current Liu Nian GanZhi string
            
        Returns:
            Flux energy state dictionary
        """
        if not self._flux_engine:
            return {}
            
        # Prepare environment
        dy_dict = None
        if selected_yun:
            gz = selected_yun.get('gan_zhi', '')
            if len(gz) >= 2:
                dy_dict = {'stem': gz[0], 'branch': gz[1]}
                
        ln_dict = None
        if current_gan_zhi and len(current_gan_zhi) >= 2:
            ln_dict = {'stem': current_gan_zhi[0], 'branch': current_gan_zhi[1]}
            
        self._flux_engine.set_environment(dy_dict, ln_dict)
        self._flux_data = self._flux_engine.compute_energy_state()
        
        return self._flux_data or {}
        
    # =========================================================================
    # QuantumEngine Interface
    # =========================================================================
    
    def get_quantum_engine(self) -> Optional[QuantumEngine]:
        """Return the QuantumEngine instance."""
        return self._quantum_engine
        
    def run_single_year_simulation(self, case_data: Dict, 
                                   dynamic_context: Dict) -> Dict:
        """
        Run quantum calculation for a single year.
        
        Args:
            case_data: Prepared case data dict
            dynamic_context: {'year': GanZhi, 'dayun': GanZhi}
            
        Returns:
            Quantum engine calculation results
        """
        if not self._quantum_engine:
            return {}
            
        return self._quantum_engine.calculate_energy(case_data, dynamic_context)
        
    def run_timeline_simulation(self, start_year: int, duration: int = 12,
                                case_data: Optional[Dict] = None,
                                params: Optional[Dict] = None) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Run multi-year timeline simulation.
        
        Args:
            start_year: Starting year for simulation
            duration: Number of years to simulate
            case_data: Pre-built case data (optional, will build if None)
            params: Golden parameters (optional)
            
        Returns:
            Tuple of (trajectory DataFrame, handover_years list)
        """
        if not self._quantum_engine or not self._profile:
            return pd.DataFrame(), []
            
        # Build case_data if not provided
        if case_data is None:
            case_data = self._build_case_data(params)
            
        # GanZhi calculation helpers
        gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        base_year = 1924
        
        traj_data = []
        handover_years = []
        
        # Initialize prev_luck to detect handovers correctly
        prev_luck = self._profile.get_luck_pillar_at(start_year - 1)
        
        for y in range(start_year, start_year + duration):
            offset = y - base_year
            l_gan = gan_chars[offset % 10]
            l_zhi = zhi_chars[offset % 12]
            l_gz = f"{l_gan}{l_zhi}"
            
            # Get dynamic luck pillar
            active_luck = self._profile.get_luck_pillar_at(y)
            
            # Detect handover
            if prev_luck and prev_luck != active_luck:
                handover_years.append({
                    'year': y,
                    'from': prev_luck,
                    'to': active_luck
                })
            prev_luck = active_luck
            
            # Deep copy to prevent reference pollution
            safe_case_data = copy.deepcopy(case_data)
            dyn_ctx = {'year': l_gz, 'dayun': active_luck, 'luck': active_luck}
            
            # Calculate
            energy_res = self._quantum_engine.calculate_energy(safe_case_data, dyn_ctx)
            
            # Extract with safety fallbacks
            final_career = float(energy_res.get('career') or 0.0)
            final_wealth = float(energy_res.get('wealth') or 0.0)
            final_rel = float(energy_res.get('relationship') or 0.0)
            
            # Domain details
            dom_det = energy_res.get('domain_details', {})
            
            traj_data.append({
                "year": int(y),
                "label": f"{y}\n{l_gz}",
                "career": round(final_career, 2),
                "wealth": round(final_wealth, 2),
                "relationship": round(final_rel, 2),
                "base_career": round(final_career * 0.9, 2),
                "base_wealth": round(final_wealth * 0.9, 2),
                "base_relationship": round(final_rel * 0.9, 2),
                "desc": energy_res.get('desc', ''),
                "is_treasury_open": dom_det.get('is_treasury_open', False),
                "treasury_icon": dom_det.get('icon', '❓'),
                "treasury_risk": dom_det.get('risk_level', 'Normal'),
                "result": energy_res  # Full result for advanced usage
            })
            
        return pd.DataFrame(traj_data), handover_years
        
    def _build_case_data(self, params: Optional[Dict] = None) -> Dict:
        """Build case_data dict for quantum engine."""
        if not self._chart or not self._user_input:
            return {}
            
        d = self._user_input['date']
        t = self._user_input['time']
        gender = self._user_input['gender']
        
        # Get flux data for physics sources
        flux_data = self._flux_data or {}
        scale = 0.08
        
        s_self = flux_data.get('BiJian', 0) + flux_data.get('JieCai', 0)
        s_output = flux_data.get('ShiShen', 0) + flux_data.get('ShangGuan', 0)
        s_wealth = flux_data.get('ZhengCai', 0) + flux_data.get('PianCai', 0)
        s_officer = flux_data.get('ZhengGuan', 0) + flux_data.get('QiSha', 0)
        s_resource = flux_data.get('ZhengYin', 0) + flux_data.get('PianYin', 0)
        
        est_self = s_self * scale
        wang_shuai_str = "身中和"
        final_self = est_self
        
        if est_self < 1.0:
            wang_shuai_str = "假从/极弱"
            final_self = est_self - 8.0
        elif est_self < 3.5:
            wang_shuai_str = "身弱"
            final_self = est_self - 6.0
        else:
            wang_shuai_str = "身旺"
            
        # Pillar energies
        pe_list = []
        p_order = ["year_stem", "year_branch", "month_stem", "month_branch", 
                   "day_stem", "day_branch", "hour_stem", "hour_branch"]
        
        for pid in p_order:
            val = 0.0
            if self._flux_engine:
                for p in self._flux_engine.particles:
                    if p.id == pid:
                        val = p.wave.amplitude * scale
                        break
            if val < 0.1:
                base_u = (params or {}).get('physics', {}).get('base_unit', 8.0)
                is_stem = 'stem' in pid
                val = base_u if is_stem else base_u * 1.5
                pw = (params or {}).get('pillarWeights', {})
                if 'year' in pid: val *= pw.get('year', 0.8)
                elif 'month' in pid: val *= pw.get('month', 1.2)
                elif 'hour' in pid: val *= pw.get('hour', 0.9)
                elif 'day' in pid: val *= pw.get('day', 1.0)
            pe_list.append(round(val, 1))
            
        physics_sources = {
            'self': {'stem_support': final_self},
            'output': {'base': s_output * scale},
            'wealth': {'base': s_wealth * scale},
            'officer': {'base': s_officer * scale},
            'resource': {'base': s_resource * scale},
            'pillar_energies': pe_list
        }
        
        bazi_list = [
            f"{self._chart.get('year',{}).get('stem','')}{self._chart.get('year',{}).get('branch','')}",
            f"{self._chart.get('month',{}).get('stem','')}{self._chart.get('month',{}).get('branch','')}",
            f"{self._chart.get('day',{}).get('stem','')}{self._chart.get('day',{}).get('branch','')}",
            f"{self._chart.get('hour',{}).get('stem','')}{self._chart.get('hour',{}).get('branch','')}"
        ]
        
        return {
            'id': 8888,
            'gender': gender,
            'day_master': self._chart.get('day', {}).get('stem', '?'),
            'wang_shuai': wang_shuai_str,
            'physics_sources': physics_sources,
            'bazi': bazi_list,
            'birth_info': {
                'year': d.year,
                'month': d.month,
                'day': d.day,
                'hour': t,
                'gender': self._gender_idx
            },
            'city': self._city
        }
        
    # =========================================================================
    # Geo & Luck Interfaces
    # =========================================================================
    
    def get_geo_modifiers(self, city: Optional[str] = None) -> Dict:
        """
        Get geographic correction modifiers.
        
        Args:
            city: City name (uses controller's city if None)
            
        Returns:
            Geo modifier dictionary
        """
        if not self._quantum_engine:
            return {}
            
        target_city = city or self._city
        if hasattr(self._quantum_engine, 'geo'):
            return self._quantum_engine.geo.process(target_city)
        return {}
        
    def get_luck_timeline(self, num_steps: int = 10) -> List[Dict]:
        """
        Get luck pillar timeline.
        
        Args:
            num_steps: Number of luck cycles to return
            
        Returns:
            List of luck cycle dictionaries
        """
        if not self._quantum_engine or not self._user_input:
            return []
            
        d = self._user_input['date']
        t = self._user_input['time']
        
        return self._quantum_engine.get_luck_timeline(
            d.year, d.month, d.day, t, self._gender_idx, num_steps=num_steps
        )
        
    def get_dynamic_luck_pillar(self, year: int) -> str:
        """
        Get the active luck pillar for a specific year.
        
        Args:
            year: Target year
            
        Returns:
            Luck pillar GanZhi string
        """
        if not self._quantum_engine or not self._user_input:
            return ""
            
        d = self._user_input['date']
        t = self._user_input['time']
        
        return self._quantum_engine.get_dynamic_luck_pillar(
            d.year, d.month, d.day, t, self._gender_idx, year
        )
        
    # =========================================================================
    # Convenience Methods for View
    # =========================================================================
    
    def get_user_data(self) -> Dict:
        """Return current user input data."""
        return self._user_input.copy()
        
    def get_gender_idx(self) -> int:
        """Return gender index (1=male, 0=female)."""
        return self._gender_idx
        
    def get_profile(self) -> Optional[BaziProfile]:
        """Return BaziProfile instance."""
        return self._profile
        
    def get_wang_shuai_str(self, flux_data: Dict, scale: float = 0.08) -> str:
        """
        Calculate Wang/Shuai strength string.
        
        Args:
            flux_data: Flux engine data
            scale: Scaling factor
            
        Returns:
            Strength description string
        """
        s_self = flux_data.get('BiJian', 0) + flux_data.get('JieCai', 0)
        est_self = s_self * scale
        
        if est_self < 1.0:
            return "假从/极弱"
        elif est_self < 3.5:
            return "身弱"
        else:
            return "身旺"
    
    # =========================================================================
    # P2 Quantum Verification: GEO Comparison Interface
    # =========================================================================
    
    def get_baseline_trajectory(self, start_year: int, duration: int = 12,
                                params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Get energy trajectory WITHOUT GEO correction (baseline).
        
        Args:
            start_year: Starting year for simulation
            duration: Number of years to simulate
            params: Optional golden parameters
            
        Returns:
            DataFrame with baseline energy values
        """
        # Save original city
        original_city = self._city
        
        # Force neutral location (no GEO modifiers)
        self._city = "Unknown"
        
        # Build case data with neutral city
        case_data = self._build_case_data(params)
        case_data['city'] = "Unknown"  # Ensure no GEO correction
        
        # Run simulation
        df, _ = self.run_timeline_simulation(start_year, duration, case_data, params)
        
        # Restore city
        self._city = original_city
        
        # Rename columns for clarity
        if not df.empty:
            df = df.rename(columns={
                'career': 'baseline_career',
                'wealth': 'baseline_wealth',
                'relationship': 'baseline_relationship'
            })
        
        return df
    
    def get_geo_trajectory(self, city: str, start_year: int, duration: int = 12,
                           params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Get energy trajectory WITH GEO correction for specified city.
        
        Args:
            city: Target city for GEO correction
            start_year: Starting year for simulation
            duration: Number of years to simulate
            params: Optional golden parameters
            
        Returns:
            DataFrame with GEO-corrected energy values
        """
        # Set target city
        self._city = city if city and city.lower() not in ['unknown', 'none', ''] else "Beijing"
        
        # Build case data with target city
        case_data = self._build_case_data(params)
        case_data['city'] = self._city
        
        # Run simulation
        df, handover_years = self.run_timeline_simulation(start_year, duration, case_data, params)
        
        # Rename columns for clarity
        if not df.empty:
            df = df.rename(columns={
                'career': 'geo_career',
                'wealth': 'geo_wealth',
                'relationship': 'geo_relationship'
            })
            
        return df
    
    def get_geo_comparison(self, city: str, start_year: int, duration: int = 12,
                           params: Optional[Dict] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Get combined baseline and GEO-corrected trajectories for comparison.
        
        Args:
            city: Target city for GEO correction
            start_year: Starting year for simulation  
            duration: Number of years to simulate
            params: Optional golden parameters
            
        Returns:
            Tuple of (combined DataFrame, geo_modifiers dict)
        """
        # Get baseline
        baseline_df = self.get_baseline_trajectory(start_year, duration, params)
        
        # Get GEO-corrected
        geo_df = self.get_geo_trajectory(city, start_year, duration, params)
        
        # Merge on year
        if not baseline_df.empty and not geo_df.empty:
            combined = baseline_df[['year', 'label', 'baseline_career', 
                                    'baseline_wealth', 'baseline_relationship']].merge(
                geo_df[['year', 'geo_career', 'geo_wealth', 'geo_relationship']],
                on='year',
                how='left'
            )
        else:
            combined = pd.DataFrame()
        
        # Get GEO modifiers for display
        geo_mods = self.get_geo_modifiers(city)
        
        return combined, geo_mods
