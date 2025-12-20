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
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from lunar_python import Solar

# Model Imports
from core.calculator import BaziCalculator
from core.flux import FluxEngine
from core.engine_v88 import EngineV88 as QuantumEngine
from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import BaziProfile
from core.exceptions import (
    BaziCalculationError,
    BaziInputError,
    BaziDataError,
    BaziEngineError,
    BaziCacheError
)
# Notification Manager
from utils.notification_manager import get_notification_manager
# Config Manager
from utils.configuration_manager import get_config_manager
# Calibration
from services.calibration_service import CalibrationService

# Configure logger for BaziController
logger = logging.getLogger("BaziController")


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
        logger.info(f"Initializing {self.VERSION} Controller...")
        
        try:
            # Models (Lazy Initialization)
            self._calc: Optional[BaziCalculator] = None
            self._flux_engine: Optional[FluxEngine] = None
            self._quantum_engine: Optional[QuantumEngine] = None
            self._graph_engine: Optional[GraphNetworkEngine] = None
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
            

            
            # V9.5 Performance Optimization: Smart result caching delegated to SimulationController
            from controllers.simulation_controller import SimulationController
            self._simulation_controller = SimulationController()
            self._cache_stats: Dict[str, int] = {
                'hits': 0,
                'misses': 0,
                'invalidations': 0
            }

            # V9.8: Global configuration manager
            self.config_manager = get_config_manager()

            # V16.0: Config Controller
            from controllers.config_controller import ConfigController
            self._config_controller = ConfigController()
            
            # Load initial cache
            self._config_controller.get_full_config()

            # LLM service placeholder
            self._llm_service = None
            self._init_llm_service()

            # V10.0: Notification Manager
            self.notification_manager = get_notification_manager()

            # V12.0: Calibration Service
            self._calibration_service = CalibrationService(flux_engine=self._flux_engine)
            self._health_report: Dict[str, Any] = {}
            self._auto_recommendations: Dict[str, Any] = {}
            
            logger.info(f"{self.VERSION} Controller initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize controller: {e}", exc_info=True)
            raise BaziEngineError(
                "控制器初始化失败",
                f"Initialization error: {str(e)}"
            )
    
    # =========================================================================
    # V16.0: Particle Weights Configuration (Single Source of Truth)
    # =========================================================================
    

    

    

    
    # =========================================================================
    # Performance Optimization: Era Multipliers Cache
    # =========================================================================
    
    # =========================================================================
    # Configuration Management (Delegated to ConfigController)
    # =========================================================================
    
    def get_current_particle_weights(self) -> Dict[str, float]:
        """
        V16.0: Return current particle weights.
        Priority: user_input > config file > defaults (1.0)
        """
        # First check user input (from UI sliders)
        pw = self._user_input.get('particle_weights') if self._user_input else None
        if pw:
            return pw
        
        # Fall back to ConfigController
        pw_config = self._config_controller.get_particle_weights()
        if pw_config:
            return pw_config.copy()
        
        # Default: all 1.0
        from utils.constants_manager import get_constants
        consts = get_constants()
        return {god: 1.0 for god in consts.TEN_GODS}
        
    def get_era_multipliers(self) -> Dict[str, float]:
        """
        Get cached era multipliers from ConfigController.
        Returns:
            Dictionary of element multipliers, e.g., {'fire': 1.25, 'water': 0.85}
        """
        return self._config_controller.get_era_multipliers()
    

    
    # =========================================================================
    # Performance Optimization: Smart Result Caching
    # =========================================================================
    
    def _invalidate_cache(self) -> None:
        """
        Invalidate all cached timeline simulation results via SimulationController.
        Called when user input changes.
        """
        if hasattr(self, '_simulation_controller'):
             self._simulation_controller.invalidate_cache()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics for monitoring via SimulationController.
        """
        return self._simulation_controller.get_cache_stats() if hasattr(self, '_simulation_controller') else {}

    # =========================================================================
    # Case Normalization Helpers (Delegate to InputController)
    # =========================================================================
    @staticmethod
    def normalize_case_fields(case: Dict[str, Any]) -> Dict[str, Any]:
        from controllers.input_controller import InputController
        return InputController.normalize_case_fields(case)

    @classmethod
    def normalize_cases(cls, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        from controllers.input_controller import InputController
        return InputController.normalize_cases(cases)

    @staticmethod
    def reverse_lookup_bazi(target_bazi: List[str], start_year: int = 1950, end_year: int = 2030):
        from controllers.input_controller import InputController
        return InputController.reverse_lookup_bazi(target_bazi, start_year, end_year)

    
    def clear_cache(self) -> None:
        """
        Manually clear all cached results.
        Useful for memory management or forced recalculation.
        """
        self._invalidate_cache()
    
    # =========================================================================
    # Input Management
    # =========================================================================
    
    def set_user_input(self, name: str, gender: str, date_obj: datetime.date, 
                       time_int: int, minute_int: int = 0, city: str = "Unknown",
                       enable_solar: bool = True, longitude: float = 116.46,
                       era_factor: Optional[Dict] = None,
                       particle_weights: Optional[Dict] = None) -> None:
        """
        Set user input and trigger base calculations.
        
        Args:
            name: User's name
            gender: "男" or "女"
            date_obj: Birth date
            time_int: Birth hour (0-23)
            minute_int: Birth minute (0-59)
            city: Birth city for geo correction
            enable_solar: Enable solar time correction
            longitude: Longitude for solar time
            
        Raises:
            BaziInputError: If input validation fails
            BaziCalculationError: If base calculation fails
        """
        logger.info(f"Setting user input: name={name}, gender={gender}, date={date_obj}, time={time_int}:{minute_int:02d}, city={city}")
        
        try:
            # Input validation via Delegate
            from controllers.input_controller import InputController
            InputController.validate_user_input(name, gender, date_obj, time_int)
            
            # V9.5: Check if input actually changed to avoid unnecessary cache invalidation
            input_changed = (
                not self._user_input or
                self._user_input.get('name') != name or
                self._user_input.get('gender') != gender or
                self._user_input.get('date') != date_obj or
                self._user_input.get('time') != time_int or
                self._user_input.get('minute') != minute_int or
                self._user_input.get('city') != city or
                self._user_input.get('enable_solar') != enable_solar or
                self._user_input.get('longitude') != longitude or
                (self._user_input.get('era_factor') != era_factor and era_factor is not None) or
                (self._user_input.get('particle_weights') != particle_weights and particle_weights is not None)
            )
            
            if not input_changed:
                logger.debug("Input unchanged, skipping base calculation.")
                return

            self._user_input = {
                'name': name,
                'gender': gender,
                'date': date_obj,
                'time': time_int,
                'minute': minute_int,
                'city': city,
                'enable_solar': enable_solar,
                'longitude': longitude,
                'era_factor': era_factor,
                'particle_weights': particle_weights
            }
            
            self._gender_idx = 1 if "男" in gender else 0
            self._city = city if city and city.lower() not in ['unknown', 'none', ''] else "Beijing"
            
            # V9.5: Invalidate cache if input changed
            logger.info("User input changed, triggering recalculation")
            self._invalidate_cache()
            
            # Trigger base calculations
            self._calculate_base()

            # V12.0: Auto health check & recommendations
            try:
                if self._calibration_service:
                    # Ensure calibration service uses latest flux engine
                    self._calibration_service.flux_engine = self._flux_engine
                    self._health_report = self._calibration_service.run_health_check(self._user_input)
                    self._auto_recommendations = self._calibration_service.get_auto_recommendations(
                        self._health_report
                    )
                    for warning in self._health_report.get('warnings', []):
                        self.notification_manager.add_warning(f"档案健康警告: {warning}")
            except Exception as e:
                logger.warning(f"Calibration health check failed: {e}", exc_info=True)

            # Apply ERA factor if provided and supported by flux engine
            if self._flux_engine and hasattr(self._flux_engine, "set_input_parameters"):
                try:
                    self._flux_engine.set_input_parameters(
                        era_factor=era_factor,
                        particle_weights=particle_weights
                    )
                    if era_factor:
                        logger.info("Applied ERA factor to FluxEngine inputs.")
                    if particle_weights:
                        logger.info("Applied particle weights to FluxEngine inputs.")
                except Exception as e:
                    logger.warning(f"Failed to apply input parameters: {e}", exc_info=True)

            logger.info("User input set and base calculations completed")
            
        except BaziInputError:
            raise
        except Exception as e:
            logger.error(f"Error setting user input: {e}", exc_info=True)
            raise BaziCalculationError(
                "设置用户输入时发生错误",
                f"Error in set_user_input: {str(e)}"
            )
        
    def _calculate_base(self) -> None:
        """Internal: Calculate base chart and initialize engines."""
        if not self._user_input:
            logger.warning("_calculate_base called without user input")
            return
        
        try:
            logger.debug("Starting base calculations...")
            start_time = time.time()
            
            d = self._user_input['date']
            t = self._user_input['time']
            m = self._user_input.get('minute', 0)  # Get minute for precise calculation
            lng = self._user_input.get('longitude', 120.0)
            
            # 1. BaziCalculator (with minute for precise hour boundary)
            logger.debug(f"Initializing BaziCalculator: {d.year}-{d.month}-{d.day} {t}:{m:02d}")
            self._calc = BaziCalculator(d.year, d.month, d.day, t, m, longitude=lng)
            self._chart = self._calc.get_chart()
            self._details = self._calc.get_details()
            self._luck_cycles = self._calc.get_luck_cycles(self._gender_idx)
            
            if not self._chart:
                raise BaziDataError("排盘结果为空", "BaziCalculator returned empty chart")
            
            logger.debug(f"Chart calculated: {len(self._chart)} pillars")
            
            # 2. FluxEngine
            logger.debug("Initializing FluxEngine...")
            self._flux_engine = FluxEngine(self._chart)
            
            # 3. QuantumEngine (Singleton-like)
            if self._quantum_engine is None:
                logger.debug("Initializing QuantumEngine...")
                # V50.0: Load full golden config from ConfigController
                engine_config = self._config_controller.get_full_config()
                self._quantum_engine = QuantumEngine()
                # Update engine with full golden config
                if engine_config:
                    self._quantum_engine.update_full_config(engine_config)
                    logger.debug(f"Updated QuantumEngine with full golden config from config/parameters.json")
            
            # V50.0: Always update engine config with latest golden parameters
            # This ensures engine uses the latest optimized parameters from config/parameters.json
            engine_config = self._config_controller.get_full_config()
            if engine_config:
                self._quantum_engine.update_full_config(engine_config)
                logger.debug(f"Updated QuantumEngine with latest golden config")
                
            # 4. BaziProfile
            logger.debug("Creating BaziProfile...")
            birth_dt = datetime.datetime.combine(d, datetime.time(t, m))  # Include minute
            self._profile = BaziProfile(birth_dt, self._gender_idx)
            
            elapsed = time.time() - start_time
            logger.info(f"Base calculations completed in {elapsed:.4f} seconds")
            
        except BaziDataError:
            raise
        except Exception as e:
            logger.error(f"Error in base calculations: {e}", exc_info=True)
            raise BaziCalculationError(
                "基础计算失败",
                f"Error in _calculate_base: {str(e)}"
            )
        
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

    def run_advanced_simulation(self, dynamic_context: Dict) -> Dict:
        """
        Phase 12: Advanced Simulation using GraphNetworkEngine (Physics-Initialized GNN).
        Returns detailed energy, ten gods, and cybernetics status.
        """
        try:
            # 1. Initialize Graph Engine if needed
            if not self._graph_engine:
                params = self._config_controller.get_full_config()
                self._graph_engine = GraphNetworkEngine(config=params)

            # 2. Update config dynamically
            current_params = self._config_controller.get_full_config()
            self._graph_engine.config = current_params # Update config

            # 3. Prepare Inputs
            bazi_list = [
                f"{self._chart.get('year',{}).get('stem','')}{self._chart.get('year',{}).get('branch','')}",
                f"{self._chart.get('month',{}).get('stem','')}{self._chart.get('month',{}).get('branch','')}",
                f"{self._chart.get('day',{}).get('stem','')}{self._chart.get('day',{}).get('branch','')}",
                f"{self._chart.get('hour',{}).get('stem','')}{self._chart.get('hour',{}).get('branch','')}"
            ]
            dm = self._chart.get('day', {}).get('stem', '?')
            
            # 4. Run Pipeline
            # Phase 1: Init
            self._graph_engine.initialize_nodes(
                bazi=bazi_list, 
                day_master=dm,
                luck_pillar=dynamic_context.get('luck_pillar'),
                year_pillar=dynamic_context.get('year')
            )
            
            # Phase 2: Adjacency
            self._graph_engine.build_adjacency_matrix()
            
            # Phase 2.5: Quantum Entanglement (三合/六合/刑冲)
            # Must apply before propagation to modify initial energies
            self._graph_engine._apply_quantum_entanglement_once()
            
            # Phase 3: Propagate
            H_final = self._graph_engine.propagate(max_iterations=5)
            
            # 5. Extract Results
            feedback_stats = self._graph_engine.energy_propagator.feedback_stats
            
            from core.math import ProbValue
            
            # Proper Ten Gods Mapping (with Yin/Yang distinction)
            gods_map = {
                "甲": {"甲":"BiJian", "乙":"JieCai", "丙":"ShiShen", "丁":"ShangGuan", "戊":"PianCai", "己":"ZhengCai", "庚":"QiSha", "辛":"ZhengGuan", "壬":"PianYin", "癸":"ZhengYin"},
                "乙": {"乙":"BiJian", "甲":"JieCai", "丁":"ShiShen", "丙":"ShangGuan", "己":"PianCai", "戊":"ZhengCai", "辛":"QiSha", "庚":"ZhengGuan", "癸":"PianYin", "壬":"ZhengYin"},
                "丙": {"丙":"BiJian", "丁":"JieCai", "戊":"ShiShen", "己":"ShangGuan", "庚":"PianCai", "辛":"ZhengCai", "壬":"QiSha", "癸":"ZhengGuan", "甲":"PianYin", "乙":"ZhengYin"},
                "丁": {"丁":"BiJian", "丙":"JieCai", "己":"ShiShen", "戊":"ShangGuan", "辛":"PianCai", "庚":"ZhengCai", "癸":"QiSha", "壬":"ZhengGuan", "乙":"PianYin", "甲":"ZhengYin"},
                "戊": {"戊":"BiJian", "己":"JieCai", "庚":"ShiShen", "辛":"ShangGuan", "壬":"PianCai", "癸":"ZhengCai", "甲":"QiSha", "乙":"ZhengGuan", "丙":"PianYin", "丁":"ZhengYin"},
                "己": {"己":"BiJian", "戊":"JieCai", "辛":"ShiShen", "庚":"ShangGuan", "癸":"PianCai", "壬":"ZhengCai", "乙":"QiSha", "甲":"ZhengGuan", "丁":"PianYin", "丙":"ZhengYin"},
                "庚": {"庚":"BiJian", "辛":"JieCai", "壬":"ShiShen", "癸":"ShangGuan", "甲":"PianCai", "乙":"ZhengCai", "丙":"QiSha", "丁":"ZhengGuan", "戊":"PianYin", "己":"ZhengYin"},
                "辛": {"辛":"BiJian", "庚":"JieCai", "癸":"ShiShen", "壬":"ShangGuan", "乙":"PianCai", "甲":"ZhengCai", "丁":"QiSha", "丙":"ZhengGuan", "己":"PianYin", "戊":"ZhengYin"},
                "壬": {"壬":"BiJian", "癸":"JieCai", "甲":"ShiShen", "乙":"ShangGuan", "丙":"PianCai", "丁":"ZhengCai", "戊":"QiSha", "己":"ZhengGuan", "庚":"PianYin", "辛":"ZhengYin"},
                "癸": {"癸":"BiJian", "壬":"JieCai", "乙":"ShiShen", "甲":"ShangGuan", "丁":"PianCai", "丙":"ZhengCai", "己":"QiSha", "戊":"ZhengGuan", "辛":"PianYin", "庚":"ZhengYin"}
            }
            
            current_map = gods_map.get(dm, {})
            
            # Calculate Ten Gods energies (aggregate by Stem chars)
            # [V13.2] Fix: Include hidden stems from branches
            ten_gods_detail = {
                "BiJian": {"mean": 0, "std": 0}, "JieCai": {"mean": 0, "std": 0},
                "ShiShen": {"mean": 0, "std": 0}, "ShangGuan": {"mean": 0, "std": 0},
                "PianCai": {"mean": 0, "std": 0}, "ZhengCai": {"mean": 0, "std": 0},
                "QiSha": {"mean": 0, "std": 0}, "ZhengGuan": {"mean": 0, "std": 0},
                "PianYin": {"mean": 0, "std": 0}, "ZhengYin": {"mean": 0, "std": 0}
            }
            
            # [V13.2] Use original element for five element distribution (before transformation)
            element_dist = {"wood": {"mean": 0, "std": 0}, "fire": {"mean": 0, "std": 0}, 
                           "earth": {"mean": 0, "std": 0}, "metal": {"mean": 0, "std": 0}, 
                           "water": {"mean": 0, "std": 0}}
            
            # Hidden stems mapping for branches
            from core.kernel import Kernel
            HIDDEN_STEMS = Kernel.HIDDEN_STEMS  # {'巳': {'丙': 0.6, '庚': 0.3, '戊': 0.1}, ...}
            
            for node in self._graph_engine.nodes:
                if isinstance(node.current_energy, ProbValue):
                    mean_val = node.current_energy.mean
                    std_val = node.current_energy.std
                else:
                    mean_val = float(node.current_energy)
                    std_val = 0.1
                
                # [V13.2] Use original element if available (before three harmony transformation)
                elem = getattr(node, 'original_element', None) or node.element
                element_dist[elem]["mean"] += mean_val
                element_dist[elem]["std"] = (element_dist[elem]["std"]**2 + std_val**2)**0.5
                
                # Map STEM nodes to Ten Gods (use char, not element)
                if node.node_type == 'stem' and node.char in current_map:
                    god_name = current_map[node.char]
                    ten_gods_detail[god_name]["mean"] += mean_val
                    ten_gods_detail[god_name]["std"] = (ten_gods_detail[god_name]["std"]**2 + std_val**2)**0.5
                
                # [V13.2] Include hidden stems from branches
                elif node.node_type == 'branch' and node.char in HIDDEN_STEMS:
                    hidden = HIDDEN_STEMS[node.char]
                    for h_stem, ratio in hidden.items():
                        if h_stem in current_map:
                            god_name = current_map[h_stem]
                            h_mean = mean_val * ratio  # Weighted by hidden stem ratio
                            h_std = std_val * ratio
                            ten_gods_detail[god_name]["mean"] += h_mean
                            ten_gods_detail[god_name]["std"] = (ten_gods_detail[god_name]["std"]**2 + h_std**2)**0.5
            
            # Aggregate Ten Gods into 5 categories
            ten_gods_summary = {
                "比劫 (Self)": {"mean": ten_gods_detail["BiJian"]["mean"] + ten_gods_detail["JieCai"]["mean"],
                              "std": (ten_gods_detail["BiJian"]["std"]**2 + ten_gods_detail["JieCai"]["std"]**2)**0.5},
                "食伤 (Output)": {"mean": ten_gods_detail["ShiShen"]["mean"] + ten_gods_detail["ShangGuan"]["mean"],
                                "std": (ten_gods_detail["ShiShen"]["std"]**2 + ten_gods_detail["ShangGuan"]["std"]**2)**0.5},
                "财星 (Wealth)": {"mean": ten_gods_detail["PianCai"]["mean"] + ten_gods_detail["ZhengCai"]["mean"],
                                "std": (ten_gods_detail["PianCai"]["std"]**2 + ten_gods_detail["ZhengCai"]["std"]**2)**0.5},
                "官杀 (Power)": {"mean": ten_gods_detail["QiSha"]["mean"] + ten_gods_detail["ZhengGuan"]["mean"],
                               "std": (ten_gods_detail["QiSha"]["std"]**2 + ten_gods_detail["ZhengGuan"]["std"]**2)**0.5},
                "印枭 (Resource)": {"mean": ten_gods_detail["PianYin"]["mean"] + ten_gods_detail["ZhengYin"]["mean"],
                                  "std": (ten_gods_detail["PianYin"]["std"]**2 + ten_gods_detail["ZhengYin"]["std"]**2)**0.5}
            }
                
            return {
                "bazi": bazi_list,
                "day_master": dm,
                "element_distribution": element_dist,
                "ten_gods": ten_gods_summary,
                "ten_gods_detail": ten_gods_detail,
                "feedback_stats": feedback_stats,
                "nodes": [
                    {
                        "char": n.char, 
                        "element": n.element, 
                        "energy_mean": n.current_energy.mean if isinstance(n.current_energy, ProbValue) else float(n.current_energy),
                        "energy_std": n.current_energy.std if isinstance(n.current_energy, ProbValue) else 0.1,
                        "type": n.node_type,
                        "ten_god": current_map.get(n.char, "N/A") if n.node_type == 'stem' else "Branch"
                    } 
                    for n in self._graph_engine.nodes
                ]
            }
            
        except Exception as e:
            logger.error(f"Advanced simulation failed: {e}", exc_info=True)
            return {}
        
    def run_timeline_simulation(self, start_year: int, duration: int = 12,
                                case_data: Optional[Dict] = None,
                                params: Optional[Dict] = None,
                                use_cache: bool = True) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Run multi-year timeline simulation.
        
        Args:
            start_year: Starting year for simulation
            duration: Number of years to simulate
            case_data: Pre-built case data (optional, will build if None)
            params: Golden parameters (optional)
            use_cache: Whether to use cached results (default: True)
            
        Returns:
            Tuple of (trajectory DataFrame, handover_years list)
            
        Raises:
            BaziDataError: If required data is missing
            BaziCalculationError: If simulation fails
        """
        """
        Run timeline simulation (delegated to SimulationController).
        """
        try:
            # Build case_data if not provided
            if case_data is None:
                case_data = self._build_case_data(params)

            # Delegate to SimulationController
            df, handovers = self._simulation_controller.run_timeline(
                engine=self._quantum_engine,
                profile=self._profile,
                user_input=self._user_input,
                case_data=case_data,
                start_year=start_year,
                duration=duration,
                era_multipliers=self.get_era_multipliers(),
                params=params,
                use_cache=use_cache
            )
            
            # Update cache stats from controller (optional, mainly for monitoring)
            # self._cache_stats = self._simulation_controller.get_cache_stats()
            
            return df, handovers

        except Exception as e:
            logger.error(f"Timeline simulation failed: {e}", exc_info=True)
            raise BaziCalculationError(
                f"时间序列模拟失败 (start_year={start_year}, duration={duration})",
                f"Error in run_timeline_simulation: {str(e)}"
            )
        
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
        
    def get_case_data(self, params: Optional[Dict] = None) -> Dict:
        """
        Public API: Build and return case data for simulation.
        Wrapper around _build_case_data.
        """
        return self._build_case_data(params)
        
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

    def get_current_era_info(self) -> Dict[str, Any]:
        """
        [V9.3 MCP] 获取当前时代的详细信息
        
        Returns:
            Dict containing era information including:
            - era_element: 时代元素
            - period: 周期编号
            - desc: 描述（如"九紫离火运"）
            - modifiers: 修正系数
            - era_bonus: 时代红利系数
            - era_penalty: 时代折损系数
            - impact_description: 影响描述
        """
        from core.processors.era import EraProcessor
        from datetime import datetime
        
        current_year = datetime.now().year
        era_processor = EraProcessor()
        era_info = era_processor.process(current_year)
        
        return era_info if era_info else {}
    
    def get_current_era_factor(self) -> Dict[str, float]:
        """
        Return current ERA factor stored in user input.
        """
        era = self._user_input.get('era_factor') if self._user_input else None
        if isinstance(era, dict):
            return era
        return {}


    
    def get_particle_weight_from_config(self, god_name: str) -> float:
        """
        V16.0: Get a specific particle weight from config file.
        Returns 1.0 if not found.
        """
        weights = self._config_controller.get_particle_weights()
        return weights.get(god_name, 1.0)

    # V12.0: Calibration state accessors
    def get_health_report(self) -> Dict[str, Any]:
        """Return the latest health report generated during set_user_input."""
        return self._health_report or {}

    def get_auto_recommendations(self) -> Dict[str, Any]:
        """Return the latest auto calibration recommendations."""
        return self._auto_recommendations or {}

    def apply_temporary_corrections(
        self,
        era_factor: Optional[Dict[str, float]] = None,
        particle_weights: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Apply recommended corrections to current user input and refresh calculations.
        This reuses set_user_input to keep cache invalidation and engine sync consistent.
        """
        if not self._user_input:
            self.notification_manager.add_warning("尚未加载档案，无法应用校准。")
            return

        current = self._user_input
        try:
            self.set_user_input(
                name=current.get('name'),
                gender=current.get('gender'),
                date_obj=current.get('date'),
                time_int=current.get('time'),
                minute_int=current.get('minute', 0),
                city=current.get('city'),
                enable_solar=current.get('enable_solar', True),
                longitude=current.get('longitude', 116.46),
                era_factor=era_factor if era_factor is not None else current.get('era_factor'),
                particle_weights=particle_weights if particle_weights is not None else current.get('particle_weights')
            )
            self.notification_manager.add_success("已应用自动校准并刷新模型。")
        except Exception as e:
            logger.error(f"Failed to apply temporary corrections: {e}", exc_info=True)
            self.notification_manager.add_error(f"应用校准失败: {e}")

    def _assemble_llm_prompt_data(self, scenario_data: Dict) -> Dict:
        """
        Assemble prompt payload for LLM planning service.

        This keeps View clean and centralizes data shaping in Controller.
        """
        base_chart = scenario_data.get('base_chart_data') or {}
        sim_timeline = scenario_data.get('simulated_timeline') or {}
        target_adj = scenario_data.get('target_adjustment') or {}

        return {
            "chart": base_chart,
            "timeline": sim_timeline,
            "target_adjustment": target_adj,
            "meta": {
                "version": self.VERSION,
                "city": self._city,
            }
        }

    def get_llm_scenario_analysis(self, scenario_data: Dict) -> Dict:
        """
        Call LLM planning service to generate natural language analysis.

        Input:
            scenario_data includes:
              - base_chart_data
              - simulated_timeline (e.g., run_geo_predictive_timeline result)
              - target_adjustment (user desired element adjustments)

        Output:
            Dict with keys like 'text_summary', 'risk_assessment', 'actionable_steps'.
        """
        is_enabled = self.config_manager.get_setting('LLM_SERVICE_ENABLED', False)
        llm_service = getattr(self, "_llm_service", None)
        if (not is_enabled) or (llm_service is None):
            if hasattr(self, "notification_manager"):
                self.notification_manager.add_warning(
                    "LLM 服务未启用",
                    "请在配置中心启用 LLM_SERVICE_ENABLED，并提供有效 LLM_API_KEY。"
                )
            return {
                "text_summary": "LLM 服务未启用。请检查配置中心状态。",
                "risk_assessment": "高",
                "actionable_steps": "请在配置中心启用 LLM_SERVICE_ENABLED，并提供有效 LLM_API_KEY。"
            }

        prompt_payload = self._assemble_llm_prompt_data(scenario_data)

        try:
            return llm_service.generate_analysis(prompt_payload)
        except Exception as e:
            logger.warning(f"LLM scenario analysis failed: {e}", exc_info=True)
            if hasattr(self, "notification_manager"):
                self.notification_manager.add_error(
                    "LLM 服务调用失败",
                    str(e)
                )
            return {"text_summary": f"LLM 服务调用失败: {e}", "risk_assessment": "", "actionable_steps": ""}

    # =========================================================================
    # V9.8 Optimal Path Finder
    # =========================================================================
    def find_optimal_adjustment_path(self, target_metric: str, target_increase_percent: float,
                                     flux_data: Optional[Dict] = None, max_iter: int = 50) -> Dict[str, float]:
        """
        Heuristic optimal adjustment finder.

        Args:
            target_metric: Target field, e.g., 'Wealth', 'Career', 'Relationship', 'Health'
            target_increase_percent: desired increase percentage (e.g., 15 for +15%)
            flux_data: optional flux data; falls back to cached or recomputed
            max_iter: iteration budget for refinement (placeholder)

        Returns:
            Dict of five-element adjustments, e.g., {'Wood': 0.05, 'Fire': -0.02, ...}
        """
        # Ensure flux data
        if flux_data is None:
            flux_data = self._flux_data or self.get_flux_data()

        if not flux_data:
            logger.warning("No flux data available for optimal path computation.")
            return {}

        # Map target_metric to a baseline value
        metric_map = {
            'Wealth': lambda d: float(d.get('ZhengCai', 0) + d.get('PianCai', 0)),
            'Career': lambda d: float(d.get('ZhengGuan', 0) + d.get('QiSha', 0)),
            'Relationship': lambda d: float(d.get('ShiShen', 0) + d.get('ShangGuan', 0)),
            'Health': lambda d: float(d.get('ZhengYin', 0) + d.get('PianYin', 0)),
        }

        get_val = metric_map.get(target_metric, lambda d: 0.0)
        baseline = get_val(flux_data)

        if baseline <= 0:
            logger.warning(f"Baseline for {target_metric} is non-positive; cannot optimize meaningfully.")
            return {}

        gap = baseline * (target_increase_percent / 100.0)
        target_value = baseline + gap

        # Simple heuristic: distribute adjustment proportional to gap across elements
        # Positive gap -> boost nourishing elements; negative gap -> reduce controlling elements
        # This is a placeholder; can be replaced by a real optimizer later.
        element_adjustments = {e: 0.0 for e in ['Wood', 'Fire', 'Earth', 'Metal', 'Water']}

        # Determine primary element influence per metric (simplified mapping)
        primary_element = {
            'Wealth': 'Metal',       # 偏财/正财
            'Career': 'Water',       # 官杀
            'Relationship': 'Fire',  # 食伤在火 (示例)
            'Health': 'Earth',       # 印星偏土 (示例)
        }.get(target_metric, 'Earth')

        # Apply a bounded proportional adjustment
        delta = min(max(gap / max(baseline, 1e-3) * 0.3, -0.3), 0.3)  # cap at ±30%

        element_adjustments[primary_element] = round(delta, 3)

        # Spread a small counterbalance to the generating element to stabilize
        generate_map = {
            'Wood': 'Water',
            'Fire': 'Wood',
            'Earth': 'Fire',
            'Metal': 'Earth',
            'Water': 'Metal'
        }
        gen_elem = generate_map.get(primary_element)
        if gen_elem:
            element_adjustments[gen_elem] = round(delta * 0.3, 3)

        logger.info(f"Optimal path heuristic result for {target_metric}: {element_adjustments}, target={target_value:.2f}")
        return element_adjustments
    def get_current_city(self) -> str:
        """
        Get current city stored in controller (fallback to 'Unknown').
        """
        return self._city or "Unknown"
        
    def get_wang_shuai_str(self, flux_data: Dict, scale: float = 0.08) -> str:
        """
        Calculate Wang/Shuai strength string.
        
        [V12.1] 升级：优先使用GraphNetworkEngine的最新算法（包含SVM模型）
        
        Args:
            flux_data: Flux engine data
            scale: Scaling factor (legacy parameter, not used in new algorithm)
            
        Returns:
            Strength description string
        """
        # [V12.1] 优先使用GraphNetworkEngine的最新算法
        try:
            from core.engine_graph import GraphNetworkEngine
            from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
            from core.models.config_model import ConfigModel
            
            # 加载最新配置
            config_model = ConfigModel()
            config = config_model.load_config()
            
            # 获取八字信息
            chart = self.get_chart()
            if not chart:
                # Fallback to legacy method
                return self._get_wang_shuai_str_legacy(flux_data, scale)
            
            bazi_list = [
                f"{chart.get('year', {}).get('stem', '')}{chart.get('year', {}).get('branch', '')}",
                f"{chart.get('month', {}).get('stem', '')}{chart.get('month', {}).get('branch', '')}",
                f"{chart.get('day', {}).get('stem', '')}{chart.get('day', {}).get('branch', '')}",
                f"{chart.get('hour', {}).get('stem', '')}{chart.get('hour', {}).get('branch', '')}"
            ]
            day_master = chart.get('day', {}).get('stem', '')
            
            if not day_master or not all(bazi_list):
                # Fallback to legacy method
                return self._get_wang_shuai_str_legacy(flux_data, scale)
            
            # 使用GraphNetworkEngine计算旺衰
            engine = GraphNetworkEngine(config=config)
            engine.initialize_nodes(bazi_list, day_master)
            engine.build_adjacency_matrix()
            engine.propagate(max_iterations=10)
            
            # 使用最新的calculate_strength_score（包含SVM模型）
            result = engine.calculate_strength_score(day_master)
            strength_label = result.get('strength_label', 'Balanced')
            
            # 映射到中文标签
            label_map = {
                'Special_Strong': '身旺（专旺）',
                'Strong': '身旺',
                'Balanced': '身中和',
                'Weak': '身弱',
                'Follower': '从格/极弱'
            }
            
            return label_map.get(strength_label, '身中和')
            
        except Exception as e:
            logger.warning(f"使用GraphNetworkEngine计算旺衰失败，回退到旧方法: {e}")
            # Fallback to legacy method
            return self._get_wang_shuai_str_legacy(flux_data, scale)
    
    def _get_wang_shuai_str_legacy(self, flux_data: Dict, scale: float = 0.08) -> str:
        """
        Legacy method for calculating Wang/Shuai strength string.
        Used as fallback when GraphNetworkEngine is not available.
        """
        s_self = flux_data.get('BiJian', 0) + flux_data.get('JieCai', 0)
        est_self = s_self * scale
        
        if est_self < 1.0:
            return "假从/极弱"
        elif est_self < 3.5:
            return "身弱"
        else:
            return "身旺"
    
    def get_five_element_energies(self, flux_data: Optional[Dict] = None, 
                                   scale: float = 0.08) -> Dict[str, float]:
        """
        Calculate and return five-element energies (Wood, Fire, Earth, Metal, Water).
        
        This method encapsulates the calculation logic and ensures data accuracy.
        View layer should only call this API without knowing implementation details.
        
        Args:
            flux_data: Optional flux data dict. If None, uses internal _flux_data.
            scale: Scaling factor for energy values (default: 0.08, matching get_wang_shuai_str)
            
        Returns:
            Dictionary with keys: 'Wood', 'Fire', 'Earth', 'Metal', 'Water'
            Values are scaled energy amounts.
        """
        # Use provided flux_data or fall back to internal state
        if flux_data is None:
            flux_data = self._flux_data or {}
        
        element_energies = {'Wood': 0.0, 'Fire': 0.0, 'Earth': 0.0, 'Metal': 0.0, 'Water': 0.0}
        
        # Method 1: Extract from spectrum if available (most accurate)
        if 'spectrum' in flux_data:
            spectrum = flux_data['spectrum']
            if isinstance(spectrum, dict):
                # Spectrum is a dict with keys: Wood, Fire, Earth, Metal, Water
                for element in element_energies.keys():
                    element_energies[element] = spectrum.get(element, 0.0) * scale
                logger.debug(f"Five-element energies extracted from spectrum: {element_energies}")
                return element_energies
        
        # Method 2: Calculate from flux engine particles (if spectrum not available)
        if self._flux_engine and hasattr(self._flux_engine, 'particles'):
            element_totals = {'Wood': 0.0, 'Fire': 0.0, 'Earth': 0.0, 'Metal': 0.0, 'Water': 0.0}
            
            try:
                for particle in self._flux_engine.particles:
                    if hasattr(particle, 'wave') and hasattr(particle.wave, 'get_energy'):
                        for element in element_totals.keys():
                            energy = particle.wave.get_energy(element)
                            element_totals[element] += energy
                
                # Apply scale factor
                element_energies = {k: v * scale for k, v in element_totals.items()}
                logger.debug(f"Five-element energies calculated from particles: {element_energies}")
                return element_energies
            except Exception as e:
                logger.warning(f"Error calculating five-element energies from particles: {e}", exc_info=True)
        
        # Method 3: Fallback - return zeros with warning
        logger.warning("Unable to extract five-element energies from flux_data. Returning zeros.")
        return element_energies

    def _init_llm_service(self) -> None:
        """
        Initialize or disable LLM service based on configuration.
        """
        llm_enabled = self.config_manager.get_setting('LLM_SERVICE_ENABLED', False)
        api_key = self.config_manager.get_setting('LLM_API_KEY', '')

        # Try import lazily to avoid hard dependency if disabled
        try:
            from services.llm_planning_service import LLMPlanningService  # type: ignore
        except Exception:
            LLMPlanningService = None

        if llm_enabled and api_key and api_key != 'default_key' and LLMPlanningService:
            try:
                self._llm_service = LLMPlanningService(api_key=api_key)
                logger.info("LLM Planning Service initialized.")
            except Exception as e:
                self._llm_service = None
                logger.error(f"LLM Planning Service initialization failed: {e}", exc_info=True)
        else:
            self._llm_service = None
            logger.info("LLM Service disabled or missing API key; fallback to degraded mode.")

    def run_geo_predictive_timeline(self, start_year: int, duration: int = 10,
                                    geo_correction_city: Optional[str] = None,
                                    params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Run timeline simulation with optional GEO correction (cached).

        Args:
            start_year: starting year for simulation
            duration: number of years to simulate
            geo_correction_city: target city for GEO correction; if None, use current city
            params: optional golden parameters

        Returns:
            DataFrame containing timeline trajectory
        """
        original_city = self._city

        # Determine target city
        target_city = geo_correction_city if geo_correction_city else original_city
        if not target_city or target_city.lower() in ['none', 'unknown', '']:
            target_city = "Unknown"
        self._city = target_city

        try:
            # Build case data with target city
            case_data = self._build_case_data(params)
            case_data['city'] = target_city

            df, _ = self.run_timeline_simulation(start_year, duration, case_data, params, use_cache=True)
            return df
        finally:
            # Restore original city
            self._city = original_city
    
    def get_pillar_energies(self, flux_data: Optional[Dict] = None,
                            params: Optional[Dict] = None,
                            scale: float = 0.08) -> List[float]:
        """
        Get pillar energies for all 8 positions (year_stem, year_branch, ..., hour_branch).
        
        This method encapsulates pillar energy calculation logic.
        View layer should only call this API without accessing flux_engine directly.
        
        Args:
            flux_data: Optional flux data dict. If None, uses internal _flux_data.
            params: Optional golden parameters for fallback calculations.
            scale: Scaling factor for energy values (default: 0.08)
            
        Returns:
            List of 8 float values representing pillar energies in order:
            [year_stem, year_branch, month_stem, month_branch, 
             day_stem, day_branch, hour_stem, hour_branch]
        """
        # Use provided flux_data or fall back to internal state
        if flux_data is None:
            flux_data = self._flux_data or {}
        
        p_order = ["year_stem", "year_branch", "month_stem", "month_branch",
                   "day_stem", "day_branch", "hour_stem", "hour_branch"]
        pe_list = []
        
        # Method 1: Extract from particle_states if available
        if 'particle_states' in flux_data:
            particle_states = flux_data['particle_states']
            particle_map = {p.get('id'): p for p in particle_states if isinstance(p, dict)}
            
            for pid in p_order:
                val = 0.0
                if pid in particle_map:
                    p_data = particle_map[pid]
                    val = p_data.get('amp', 0.0) * scale
                
                # Fallback if value is too low
                if val < 0.1:
                    base_u = (params or {}).get('physics', {}).get('base_unit', 8.0) if params else 8.0
                    is_stem = 'stem' in pid
                    val = base_u if is_stem else base_u * 1.5
                    pw = (params or {}).get('pillarWeights', {}) if params else {}
                    if 'year' in pid:
                        val *= pw.get('year', 0.8)
                    elif 'month' in pid:
                        val *= pw.get('month', 1.2)
                    elif 'hour' in pid:
                        val *= pw.get('hour', 0.9)
                    elif 'day' in pid:
                        val *= pw.get('day', 1.0)
                
                pe_list.append(round(val, 1))
            
            logger.debug(f"Pillar energies extracted from particle_states: {pe_list}")
            return pe_list
        
        # Method 2: Calculate from flux engine particles (if particle_states not available)
        if self._flux_engine and hasattr(self._flux_engine, 'particles'):
            try:
                for pid in p_order:
                    val = 0.0
                    for p in self._flux_engine.particles:
                        if p.id == pid:
                            val = p.wave.amplitude * scale
                            break
                    
                    # Fallback if value is too low
                    if val < 0.1:
                        base_u = (params or {}).get('physics', {}).get('base_unit', 8.0) if params else 8.0
                        is_stem = 'stem' in pid
                        val = base_u if is_stem else base_u * 1.5
                        pw = (params or {}).get('pillarWeights', {}) if params else {}
                        if 'year' in pid:
                            val *= pw.get('year', 0.8)
                        elif 'month' in pid:
                            val *= pw.get('month', 1.2)
                        elif 'hour' in pid:
                            val *= pw.get('hour', 0.9)
                        elif 'day' in pid:
                            val *= pw.get('day', 1.0)
                    
                    pe_list.append(round(val, 1))
                
                logger.debug(f"Pillar energies calculated from particles: {pe_list}")
                return pe_list
            except Exception as e:
                logger.warning(f"Error calculating pillar energies from particles: {e}", exc_info=True)
        
        # Method 3: Fallback - return default values
        logger.warning("Unable to extract pillar energies. Returning default values.")
        base_u = (params or {}).get('physics', {}).get('base_unit', 8.0) if params else 8.0
        pw = (params or {}).get('pillarWeights', {}) if params else {}
        
        for pid in p_order:
            is_stem = 'stem' in pid
            val = base_u if is_stem else base_u * 1.5
            if 'year' in pid:
                val *= pw.get('year', 0.8)
            elif 'month' in pid:
                val *= pw.get('month', 1.2)
            elif 'hour' in pid:
                val *= pw.get('hour', 0.9)
            elif 'day' in pid:
                val *= pw.get('day', 1.0)
            pe_list.append(round(val, 1))
        
        return pe_list
    
    def get_particle_audit_data(self, flux_data: Optional[Dict] = None,
                                 scale: float = 0.08) -> List[Dict]:
        """
        Get particle audit data for calculation transparency.
        
        This method returns particle information for audit/debugging purposes.
        View layer should use this instead of directly accessing flux_engine.particles.
        
        Args:
            flux_data: Optional flux data dict. If None, uses internal _flux_data.
            scale: Scaling factor for energy values (default: 0.08)
            
        Returns:
            List of dictionaries with keys: 'Particle', 'Raw Flux (E_f)', 'Scale Factor', 'Quantum Input (E_q)'
        """
        # Use provided flux_data or fall back to internal state
        if flux_data is None:
            flux_data = self._flux_data or {}
        
        audit_data = []
        
        # Method 1: Extract from particle_states if available
        if 'particle_states' in flux_data:
            particle_states = flux_data['particle_states']
            for p_data in particle_states:
                if not isinstance(p_data, dict):
                    continue
                pid = p_data.get('id', '')
                # Skip dynamic particles (da yun, liu nian)
                if "dy_" in pid or "ln_" in pid:
                    continue
                
                raw = p_data.get('amp', 0.0)
                scaled = raw * scale
                audit_data.append({
                    "Particle": f"{p_data.get('char', '?')} ({pid})",
                    "Raw Flux (E_f)": f"{raw:.1f}",
                    "Scale Factor": f"{scale}",
                    "Quantum Input (E_q)": f"{scaled:.1f}"
                })
            
            logger.debug(f"Particle audit data extracted from particle_states: {len(audit_data)} particles")
            return audit_data
        
        # Method 2: Calculate from flux engine particles (if particle_states not available)
        if self._flux_engine and hasattr(self._flux_engine, 'particles'):
            try:
                for p in self._flux_engine.particles:
                    # Skip dynamic particles (da yun, liu nian)
                    if "dy_" in p.id or "ln_" in p.id:
                        continue
                    
                    raw = p.wave.amplitude
                    scaled = raw * scale
                    audit_data.append({
                        "Particle": f"{p.char} ({p.id})",
                        "Raw Flux (E_f)": f"{raw:.1f}",
                        "Scale Factor": f"{scale}",
                        "Quantum Input (E_q)": f"{scaled:.1f}"
                    })
                
                logger.debug(f"Particle audit data calculated from particles: {len(audit_data)} particles")
                return audit_data
            except Exception as e:
                logger.warning(f"Error calculating particle audit data from particles: {e}", exc_info=True)
        
        # Method 3: Fallback - return empty list
        logger.warning("Unable to extract particle audit data. Returning empty list.")
        return audit_data

    def get_balance_suggestion(self, element_energies: Optional[Dict[str, float]] = None) -> Dict[str, str]:
        """
        Provide a simple five-element balance suggestion.

        Args:
            element_energies: Dict with keys Wood/Fire/Earth/Metal/Water (scaled values).

        Returns:
            Dict with:
                - element_to_balance: element with the highest energy (needs restraint)
                - element_to_support: element with the lowest energy (needs nourishment)
                - text_summary: brief recommendation text.
        """
        elements = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']
        energies = element_energies or {}
        # Ensure all elements exist
        energies = {e: float(energies.get(e, 0.0) or 0.0) for e in elements}

        if not energies:
            return {
                "element_to_balance": "Unknown",
                "element_to_support": "Unknown",
                "text_summary": "数据不足，无法生成建议。"
            }

        # Find max/min
        max_elem = max(energies, key=energies.get)
        min_elem = min(energies, key=energies.get)

        # Simple five-element restraining cycle for suggestion
        restrain_map = {
            'Wood': 'Metal',
            'Fire': 'Water',
            'Earth': 'Wood',
            'Metal': 'Fire',
            'Water': 'Earth'
        }
        nourish_map = {
            'Wood': 'Water',
            'Fire': 'Wood',
            'Earth': 'Fire',
            'Metal': 'Earth',
            'Water': 'Metal'
        }

        restraint = restrain_map.get(max_elem, "Neutral")
        support = nourish_map.get(min_elem, "Neutral")

        summary = (
            f"{max_elem} 偏旺，宜用 {restraint} 适度制衡；"
            f"{min_elem} 偏弱，可用 {support} 予以滋养。"
        )

        return {
            "element_to_balance": max_elem,
            "element_to_support": min_elem,
            "text_summary": summary
        }

    def get_top_ten_gods_summary(self, flux_data: Optional[Dict] = None, top_n: int = 2,
                                 scale: float = 0.08) -> Dict[str, Any]:
        """
        Return a brief summary of the strongest Ten Gods.

        Args:
            flux_data: Flux data dict (expects raw Ten Gods scores).
            top_n: Number of top gods to include.
            scale: Scaling factor (kept for consistency).

        Returns:
            Dict with:
                - top_gods: list of (name, value) tuples (scaled)
                - top_two_gods: string summary of top two gods
        """
        tg_keys = [
            ('BiJian', '比肩'),
            ('JieCai', '劫财'),
            ('ShiShen', '食神'),
            ('ShangGuan', '伤官'),
            ('PianCai', '偏财'),
            ('ZhengCai', '正财'),
            ('QiSha', '七杀'),
            ('ZhengGuan', '正官'),
            ('PianYin', '偏印'),
            ('ZhengYin', '正印'),
        ]

        data = flux_data or self._flux_data or {}

        tg_list = []
        for key, label in tg_keys:
            val = float(data.get(key, 0.0) or 0.0) * scale
            tg_list.append((label, val))

        # Sort by value descending
        tg_list.sort(key=lambda x: x[1], reverse=True)
        top_gods = tg_list[:top_n]

        top_two_str = "、".join([f"{name}({val:.2f})" for name, val in top_gods]) if top_gods else "无数据"

        return {
            "top_gods": top_gods,
            "top_two_gods": top_two_str
        }
    
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
