"""
Test Engine Adapter - Legacy Test Compatibility Layer
=====================================================
V9.5 MVC Architecture Migration Support

This adapter provides backward-compatible interfaces for legacy tests,
ensuring all Model access goes through BaziController.

Usage:
    # Old way (direct import):
    from core.calculator import BaziCalculator
    calc = BaziCalculator(2024, 2, 10, 12)
    chart = calc.get_chart()
    
    # New way (through adapter):
    from tests.adapters.test_engine_adapter import BaziCalculatorAdapter
    calc = BaziCalculatorAdapter(2024, 2, 10, 12)
    chart = calc.get_chart()
    
    # Old way (direct import):
    from core.engine_v91 import EngineV91
    engine = EngineV91()
    result = engine.analyze(bazi, day_master, city="Harbin")
    
    # New way (through adapter):
    from tests.adapters.test_engine_adapter import QuantumEngineAdapter
    engine = QuantumEngineAdapter()
    result = engine.analyze(bazi, day_master, city="Harbin")
"""

import datetime
from typing import Dict, List, Optional, Any
from controllers.bazi_controller import BaziController


class BaziCalculatorAdapter:
    """
    Adapter for BaziCalculator - provides backward-compatible interface
    while routing through BaziController.
    
    This class mimics the BaziCalculator API but uses BaziController internally.
    """
    
    def __init__(self, year: int, month: int, day: int, hour: int, 
                 minute: int = 0, longitude: Optional[float] = None, 
                 tz_offset: int = 8):
        """
        Initialize adapter with birth information.
        
        Args:
            year: Birth year
            month: Birth month
            day: Birth day
            hour: Birth hour (0-23)
            minute: Birth minute (default: 0)
            longitude: Longitude for solar time correction (optional)
            tz_offset: Timezone offset (default: 8)
        """
        self._controller = BaziController()
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._longitude = longitude
        self._tz_offset = tz_offset
        
        # Initialize controller with user input
        date_obj = datetime.date(year, month, day)
        longitude_val = longitude if longitude is not None else 116.46
        self._controller.set_user_input(
            name="TestUser",
            gender="男",  # Default to male for tests
            date_obj=date_obj,
            time_int=hour,
            city="Unknown",
            enable_solar=(longitude is not None),
            longitude=longitude_val
        )
    
    def get_chart(self) -> Dict:
        """
        Return the calculated Bazi chart.
        
        Returns:
            Dictionary with 'year', 'month', 'day', 'hour' pillars
        """
        return self._controller.get_chart()
    
    def get_details(self) -> Dict:
        """
        Return calculation details.
        
        Returns:
            Dictionary with calculation metadata
        """
        return self._controller.get_details()
    
    def get_luck_cycles(self, gender_idx: int) -> List[Dict]:
        """
        Return the Da Yun (Great Luck) cycles list.
        
        Args:
            gender_idx: 1 for male, 0 for female
            
        Returns:
            List of luck cycle dictionaries
        """
        # Update controller gender if needed
        if gender_idx != self._controller.get_gender_idx():
            # Re-initialize with correct gender
            date_obj = datetime.date(self._year, self._month, self._day)
            gender_str = "男" if gender_idx == 1 else "女"
            self._controller.set_user_input(
                name="TestUser",
                gender=gender_str,
                date_obj=date_obj,
                time_int=self._hour,
                city="Unknown",
                enable_solar=(self._longitude is not None),
                longitude=self._longitude if self._longitude is not None else 116.46
            )
        
        return self._controller.get_luck_cycles()
    
    def get_wuxing_counts(self) -> Dict:
        """
        Return Five Elements counts (placeholder for compatibility).
        
        Returns:
            Empty dictionary (legacy method)
        """
        return {}
    
    @property
    def controller(self) -> BaziController:
        """
        Access the underlying BaziController instance (for advanced usage).
        
        Returns:
            BaziController instance
        """
        return self._controller


class QuantumEngineAdapter:
    """
    Adapter for QuantumEngine (EngineV88/EngineV91) - provides backward-compatible
    interface while routing through BaziController.
    
    This class mimics the EngineV88/EngineV91 API but uses BaziController internally.
    For tests that require custom params/config, a direct engine instance is created
    while still maintaining Controller access for other operations.
    """
    
    def __init__(self, params: Optional[Dict] = None):
        """
        Initialize adapter.
        
        Args:
            params: Optional parameters dict (for backward compatibility)
                    If provided, creates a direct engine instance for compatibility
        """
        self._controller = BaziController()
        self._params = params or {}
        self._initialized = False
        self._direct_engine = None
        
        # If params are provided, create a direct engine instance for compatibility
        # This is needed for tests that require custom configuration
        if params:
            # Use EngineV88 which accepts 'config' parameter
            # EngineV91 inherits from EngineV88 but doesn't override __init__
            from core.engine_v88 import EngineV88
            # EngineV88 accepts 'config' parameter
            self._direct_engine = EngineV88(config=params)
    
    def analyze(self, bazi: List[str], day_master: str, 
                city: str = "Unknown", latitude: Optional[float] = None,
                year: int = 2024, **kwargs) -> Any:
        """
        Analyze Bazi chart with quantum engine.
        
        Args:
            bazi: List of 4 pillars, e.g., ['甲子', '丙午', '辛卯', '壬辰']
            day_master: Day Master character, e.g., '辛'
            city: City name for geo correction
            latitude: Optional latitude override
            year: Current year for era calculation
            **kwargs: Additional arguments
            
        Returns:
            AnalysisResponse or result dict
        """
        # If we have a direct engine (created with params), use it
        if self._direct_engine:
            return self._direct_engine.analyze(
                bazi=bazi,
                day_master=day_master,
                city=city,
                latitude=latitude,
                year=year,
                **kwargs
            )
        
        # Otherwise, use controller's engine
        quantum_engine = self._controller.get_quantum_engine()
        
        if quantum_engine is None:
            # Initialize controller with a dummy date if needed
            # We need to set user input to initialize the engine
            if not self._initialized:
                # Use a default date to initialize
                date_obj = datetime.date(2000, 1, 1)
                self._controller.set_user_input(
                    name="TestUser",
                    gender="男",
                    date_obj=date_obj,
                    time_int=12,
                    city=city if city != "Unknown" else "Beijing",
                    enable_solar=False,
                    longitude=116.46
                )
                self._initialized = True
                quantum_engine = self._controller.get_quantum_engine()
        
        if quantum_engine is None:
            raise RuntimeError("Failed to initialize QuantumEngine through Controller")
        
        # Call the engine's analyze method directly
        # This maintains backward compatibility while going through controller
        return quantum_engine.analyze(
            bazi=bazi,
            day_master=day_master,
            city=city,
            latitude=latitude,
            year=year,
            **kwargs
        )
    
    def calculate_energy(self, case_data: Dict, 
                        dynamic_context: Optional[Dict] = None) -> Dict:
        """
        Calculate energy for a case.
        
        Args:
            case_data: Case data dictionary
            dynamic_context: Optional dynamic context
            
        Returns:
            Energy calculation results
        """
        # If we have a direct engine (created with params), use it
        if self._direct_engine:
            return self._direct_engine.calculate_energy(case_data, dynamic_context or {})
        
        # Otherwise, use controller's engine
        quantum_engine = self._controller.get_quantum_engine()
        
        if quantum_engine is None:
            # Initialize if needed
            if not self._initialized:
                date_obj = datetime.date(2000, 1, 1)
                self._controller.set_user_input(
                    name="TestUser",
                    gender="男",
                    date_obj=date_obj,
                    time_int=12,
                    city=case_data.get('city', 'Unknown'),
                    enable_solar=False,
                    longitude=116.46
                )
                self._initialized = True
                quantum_engine = self._controller.get_quantum_engine()
        
        if quantum_engine is None:
            raise RuntimeError("Failed to initialize QuantumEngine through Controller")
        
        # Use controller's method if available, otherwise direct call
        if dynamic_context:
            return self._controller.run_single_year_simulation(case_data, dynamic_context)
        else:
            return quantum_engine.calculate_energy(case_data, dynamic_context or {})
    
    def get_luck_timeline(self, year: int, month: int, day: int, hour: int,
                         gender_idx: int, num_steps: int = 10) -> List[Dict]:
        """
        Get luck timeline.
        
        Args:
            year: Birth year
            month: Birth month
            day: Birth day
            hour: Birth hour
            gender_idx: Gender index (1=male, 0=female)
            num_steps: Number of steps
            
        Returns:
            List of luck cycle dictionaries
        """
        return self._controller.get_luck_timeline(num_steps)
    
    def get_dynamic_luck_pillar(self, year: int, month: int, day: int, hour: int,
                               gender_idx: int, target_year: int) -> str:
        """
        Get dynamic luck pillar for a specific year.
        
        Args:
            year: Birth year
            month: Birth month
            day: Birth day
            hour: Birth hour
            gender_idx: Gender index (1=male, 0=female)
            target_year: Target year
            
        Returns:
            Luck pillar GanZhi string
        """
        return self._controller.get_dynamic_luck_pillar(target_year)
    
    @property
    def controller(self) -> BaziController:
        """
        Access the underlying BaziController instance.
        
        Returns:
            BaziController instance
        """
        return self._controller
    
    @property
    def VERSION(self) -> str:
        """Return engine version."""
        quantum_engine = self._controller.get_quantum_engine()
        if quantum_engine:
            return getattr(quantum_engine, 'VERSION', 'Unknown')
        return 'Unknown'


class FluxEngineAdapter:
    """
    Adapter for FluxEngine - provides backward-compatible interface
    while routing through BaziController.
    """
    
    def __init__(self, chart: Dict):
        """
        Initialize adapter with chart.
        
        Args:
            chart: Bazi chart dictionary
        """
        self._controller = BaziController()
        self._chart = chart
        
        # Initialize controller with chart data
        # Extract date from chart if possible, otherwise use default
        date_obj = datetime.date(2000, 1, 1)
        self._controller.set_user_input(
            name="TestUser",
            gender="男",
            date_obj=date_obj,
            time_int=12,
            city="Unknown",
            enable_solar=False,
            longitude=116.46
        )
    
    def compute_energy_state(self) -> Dict:
        """
        Compute energy state.
        
        Returns:
            Energy state dictionary
        """
        return self._controller.get_flux_data()
    
    def set_environment(self, dayun: Optional[Dict] = None, 
                       liunian: Optional[Dict] = None) -> None:
        """
        Set environment for flux calculation.
        
        Args:
            dayun: Da Yun dictionary
            liunian: Liu Nian dictionary
        """
        # Convert to format expected by controller
        selected_yun = None
        if dayun:
            gan = dayun.get('stem', '')
            zhi = dayun.get('branch', '')
            if gan and zhi:
                selected_yun = {'gan_zhi': f"{gan}{zhi}"}
        
        current_gan_zhi = None
        if liunian:
            gan = liunian.get('stem', '')
            zhi = liunian.get('branch', '')
            if gan and zhi:
                current_gan_zhi = f"{gan}{zhi}"
        
        self._controller.get_flux_data(selected_yun, current_gan_zhi)
    
    def calculate_flux(self, dayun_gan: str, dayun_zhi: str,
                      liunian_gan: str, liunian_zhi: str) -> Dict:
        """
        Calculate flux with specific GanZhi.
        
        Args:
            dayun_gan: Da Yun stem
            dayun_zhi: Da Yun branch
            liunian_gan: Liu Nian stem
            liunian_zhi: Liu Nian branch
            
        Returns:
            Flux data dictionary
        """
        selected_yun = {'gan_zhi': f"{dayun_gan}{dayun_zhi}"}
        current_gan_zhi = f"{liunian_gan}{liunian_zhi}"
        return self._controller.get_flux_data(selected_yun, current_gan_zhi)
    
    @property
    def particles(self) -> List:
        """
        Get flux particles.
        
        Returns:
            List of particles
        """
        flux_engine = self._controller.get_flux_engine()
        if flux_engine:
            return getattr(flux_engine, 'particles', [])
        return []
    
    @property
    def controller(self) -> BaziController:
        """
        Access the underlying BaziController instance.
        
        Returns:
            BaziController instance
        """
        return self._controller


def get_controller_for_test(year: int, month: int, day: int, hour: int,
                           gender: str = "男", city: str = "Unknown") -> BaziController:
    """
    Helper function to get a BaziController instance for testing.
    
    Args:
        year: Birth year
        month: Birth month
        day: Birth day
        hour: Birth hour (0-23)
        gender: Gender string ("男" or "女")
        city: Birth city
        
    Returns:
        Initialized BaziController instance
    """
    controller = BaziController()
    date_obj = datetime.date(year, month, day)
    controller.set_user_input(
        name="TestUser",
        gender=gender,
        date_obj=date_obj,
        time_int=hour,
        city=city,
        enable_solar=False,
        longitude=116.46
    )
    return controller

