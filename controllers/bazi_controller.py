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
            
            # V9.5 Performance Optimization: Cache era multipliers to avoid file I/O
            self._era_multipliers: Dict[str, float] = {}
            self._load_era_multipliers()
            logger.debug(f"Era multipliers loaded: {len(self._era_multipliers)} elements")
            
            # V9.5 Performance Optimization: Smart result caching
            self._timeline_cache: Dict[str, Tuple[pd.DataFrame, List[Dict]]] = {}
            self._cache_stats: Dict[str, int] = {
                'hits': 0,
                'misses': 0,
                'invalidations': 0
            }

            # V9.8: Global configuration manager
            self.config_manager = get_config_manager()

            # V16.0: Load particle weights from config/parameters.json
            self._particle_weights_config: Dict[str, float] = {}
            self._load_particle_weights_config()

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
    
    def _load_particle_weights_config(self) -> None:
        """
        V16.0: Load particle weights from config/parameters.json.
        This is the single source of truth for particle weights.
        """
        import os
        import json
        
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, "config", "parameters.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self._particle_weights_config = config_data.get('particleWeights', {})
                logger.info(f"Particle weights loaded from {config_path}: {len(self._particle_weights_config)} weights")
            else:
                logger.warning(f"Config file not found: {config_path}, using defaults")
                self._particle_weights_config = {}
        except Exception as e:
            logger.error(f"Failed to load particle weights config: {e}", exc_info=True)
            self._particle_weights_config = {}
    
    def _load_golden_config(self) -> Optional[Dict]:
        """
        V50.0: Load full golden config from config/parameters.json.
        This is the single source of truth for all algorithm parameters.
        
        Returns:
            Full config dict with all parameters, or None if loading fails
        """
        import os
        import json
        
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, "config", "parameters.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    golden_config = json.load(f)
                
                # Merge with default structure to ensure completeness
                from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
                merged_config = DEFAULT_FULL_ALGO_PARAMS.copy()
                
                # Deep merge golden config into defaults
                def deep_merge(base, update):
                    """Recursively merge update into base"""
                    for key, value in update.items():
                        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                            deep_merge(base[key], value)
                        else:
                            base[key] = value
                
                deep_merge(merged_config, golden_config)
                logger.debug(f"Golden config loaded from {config_path}")
                return merged_config
            else:
                logger.warning(f"Config file not found: {config_path}, using defaults")
                return None
        except Exception as e:
            logger.error(f"Failed to load golden config: {e}", exc_info=True)
            return None
    
    def _save_particle_weights_config(self, weights: Dict[str, float]) -> bool:
        """
        V16.0: Save particle weights to config/parameters.json.
        Returns True if successful, False otherwise.
        """
        import os
        import json
        
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, "config", "parameters.json")
            
            # Load existing config
            config_data = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            
            # Update particle weights
            config_data['particleWeights'] = weights
            self._particle_weights_config = weights
            
            # Save back
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Particle weights saved to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save particle weights config: {e}", exc_info=True)
            return False
    
    # =========================================================================
    # Performance Optimization: Era Multipliers Cache
    # =========================================================================
    
    def _load_era_multipliers(self) -> None:
        """
        Load era multipliers from file and cache in memory.
        
        V9.5 Performance Optimization: This eliminates repeated file I/O operations
        that were causing 20.33% performance overhead.
        """
        import os
        import json
        
        try:
            # Calculate era_constants.json path
            # From controllers/ -> project root -> data/
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            era_path = os.path.join(project_root, "data", "era_constants.json")
            
            if os.path.exists(era_path):
                with open(era_path, 'r', encoding='utf-8') as f:
                    era_data = json.load(f)
                    self._era_multipliers = era_data.get('physics_multipliers', {})
                logger.debug(f"Era multipliers loaded from {era_path}")
            else:
                # Default multipliers if file doesn't exist
                self._era_multipliers = {}
                logger.warning(f"Era constants file not found: {era_path}, using defaults")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse era constants JSON: {e}")
            self._era_multipliers = {}
        except Exception as e:
            # Fallback to empty dict on any error
            logger.error(f"Error loading era multipliers: {e}", exc_info=True)
            self._era_multipliers = {}
    
    def get_era_multipliers(self) -> Dict[str, float]:
        """
        Get cached era multipliers.
        
        Returns:
            Dictionary of element multipliers, e.g., {'fire': 1.25, 'water': 0.85}
        """
        return self._era_multipliers.copy()
    
    # =========================================================================
    # Performance Optimization: Smart Result Caching
    # =========================================================================
    
    def _generate_cache_key(self, start_year: int, duration: int, 
                           params: Optional[Dict] = None) -> str:
        """
        Generate a unique cache key for timeline simulation.
        
        Args:
            start_year: Starting year for simulation
            duration: Number of years to simulate
            params: Optional golden parameters
            
        Returns:
            Cache key string
        """
        import hashlib
        import json
        
        # Build key components
        key_data = {
            'user_input': self._user_input,
            'start_year': start_year,
            'duration': duration,
            'params': params or {}
        }
        
        # Create hash from key data
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        
        return f"timeline_{key_hash}"
    
    def _invalidate_cache(self) -> None:
        """
        Invalidate all cached timeline simulation results.
        Called when user input changes.
        """
        if self._timeline_cache:
            cache_size = len(self._timeline_cache)
            self._cache_stats['invalidations'] += cache_size
            self._timeline_cache.clear()
            logger.info(f"Cache invalidated: {cache_size} entries cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dictionary with cache statistics (hits, misses, invalidations, size)
        """
        stats = self._cache_stats.copy()
        stats['size'] = len(self._timeline_cache)
        stats['hit_rate'] = (
            self._cache_stats['hits'] / 
            (self._cache_stats['hits'] + self._cache_stats['misses'])
            if (self._cache_stats['hits'] + self._cache_stats['misses']) > 0 
            else 0.0
        )
        return stats

    # =========================================================================
    # Case Normalization Helpers (shared across P1/P2/P3)
    # =========================================================================
    @staticmethod
    def normalize_case_fields(case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure required fields exist:
        - day_master: derive from bazi[2] (day pillar stem) if missing.
        - gender: default to '未知' if missing.
        - birth_date/time: if missing and bazi complete, reverse-lookup Gregorian datetime.
        - dynamic_checks: fill 'year' from birth_date or bazi year pillar if missing.
        """
        if not isinstance(case, dict):
            return case
        c = case
        if not c.get("day_master"):
            bazi = c.get("bazi") or []
            if len(bazi) >= 3 and isinstance(bazi[2], str) and bazi[2]:
                c["day_master"] = bazi[2][0]
        if not c.get("gender"):
            c["gender"] = "未知"

        # Reverse lookup birth date/time from full bazi if missing
        if (not c.get("birth_date") or not c.get("birth_time")) and isinstance(c.get("bazi"), list) and len(c["bazi"]) >= 4:
            try:
                dt = BaziController.reverse_lookup_bazi(c["bazi"])
                if dt:
                    c["birth_date"] = dt.strftime("%Y-%m-%d")
                    c["birth_time"] = f"{dt.hour:02d}:{dt.minute:02d}"
            except Exception:
                pass

        # Fill dynamic_checks.year:
        # - Prefer birth_date (YYYY-MM-DD) year component
        # - Else fall back to bazi year pillar (bazi[0]) to avoid KeyError
        if c.get("dynamic_checks"):
            normalized_checks = []
            for chk in c.get("dynamic_checks", []):
                if not isinstance(chk, dict):
                    continue
                if "year" not in chk or not chk.get("year"):
                    birth_date = c.get("birth_date")
                    year_val = None
                    if isinstance(birth_date, str) and len(birth_date) >= 4:
                        try:
                            year_val = birth_date.split("-")[0]
                        except Exception:
                            year_val = None
                    if not year_val:
                        bazi = c.get("bazi") or []
                        if len(bazi) >= 1 and isinstance(bazi[0], str) and bazi[0]:
                            year_val = bazi[0]  # fallback to year pillar
                    chk["year"] = year_val
                normalized_checks.append(chk)
            c["dynamic_checks"] = normalized_checks
        return c

    @classmethod
    def normalize_cases(cls, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a list of cases safely."""
        if not isinstance(cases, list):
            return cases
        return [cls.normalize_case_fields(c) for c in cases]

    # =========================================================================
    # Reverse lookup date/time from Bazi
    # =========================================================================
    @staticmethod
    def reverse_lookup_bazi(target_bazi: List[str], start_year: int = 1950, end_year: int = 2030):
        """
        Brute-force reverse lookup of Bazi (Y, M, D, H GanZhi) to Gregorian datetime.
        Returns datetime.datetime if found, else None.
        """
        if not target_bazi or len(target_bazi) < 4:
            return None
        tg_y, tg_m, tg_d, tg_h = target_bazi[:4]
        import datetime

        for y in range(start_year, end_year + 1):
            start_d = datetime.date(y, 1, 1)
            end_d = datetime.date(y, 12, 31)
            curr = start_d
            while curr <= end_d:
                try:
                    s = Solar.fromYmd(curr.year, curr.month, curr.day)
                    l = s.getLunar()
                    if l.getYearInGanZhiExact() != tg_y:
                        curr += datetime.timedelta(days=1)
                        continue
                    if l.getMonthInGanZhiExact() != tg_m:
                        curr += datetime.timedelta(days=1)
                        continue
                    if l.getDayInGanZhiExact() != tg_d:
                        curr += datetime.timedelta(days=1)
                        continue
                    # check hour
                    for h in range(0, 24):
                        sh = Solar.fromYmdHms(curr.year, curr.month, curr.day, h, 0, 0)
                        lh = sh.getLunar()
                        if lh.getTimeInGanZhi() == tg_h:
                            return datetime.datetime(curr.year, curr.month, curr.day, h, 0, 0)
                except Exception:
                    pass
                curr += datetime.timedelta(days=1)
        return None
    
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
                       time_int: int, city: str = "Unknown",
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
            city: Birth city for geo correction
            enable_solar: Enable solar time correction
            longitude: Longitude for solar time
            
        Raises:
            BaziInputError: If input validation fails
            BaziCalculationError: If base calculation fails
        """
        logger.info(f"Setting user input: name={name}, gender={gender}, date={date_obj}, time={time_int}, city={city}")
        
        try:
            # Input validation
            if not name or not name.strip():
                raise BaziInputError("用户姓名不能为空", "name parameter is empty")
            if gender not in ["男", "女"]:
                raise BaziInputError(f"性别参数无效: {gender}", f"gender must be '男' or '女', got '{gender}'")
            if not isinstance(date_obj, datetime.date):
                raise BaziInputError("日期格式无效", f"date_obj must be datetime.date, got {type(date_obj)}")
            if not (0 <= time_int <= 23):
                raise BaziInputError(f"时间参数无效: {time_int}", "time_int must be between 0 and 23")
            
            # V9.5: Check if input actually changed to avoid unnecessary cache invalidation
            input_changed = (
                not self._user_input or
                self._user_input.get('name') != name or
                self._user_input.get('gender') != gender or
                self._user_input.get('date') != date_obj or
                self._user_input.get('time') != time_int or
                self._user_input.get('city') != city or
                self._user_input.get('enable_solar') != enable_solar or
                self._user_input.get('longitude') != longitude or
                self._user_input.get('era_factor') != era_factor or
                self._user_input.get('particle_weights') != particle_weights
            )
            
            self._user_input = {
                'name': name,
                'gender': gender,
                'date': date_obj,
                'time': time_int,
                'city': city,
                'enable_solar': enable_solar,
                'longitude': longitude,
                'era_factor': era_factor,
                'particle_weights': particle_weights
            }
            
            self._gender_idx = 1 if "男" in gender else 0
            self._city = city if city and city.lower() not in ['unknown', 'none', ''] else "Beijing"
            
            # V9.5: Invalidate cache if input changed
            if input_changed:
                logger.info("User input changed, invalidating cache")
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
            lng = self._user_input.get('longitude', 120.0)
            
            # 1. BaziCalculator
            logger.debug(f"Initializing BaziCalculator: {d.year}-{d.month}-{d.day} {t}:00")
            self._calc = BaziCalculator(d.year, d.month, d.day, t, 0, longitude=lng)
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
                # V50.0: Load full golden config from config/parameters.json
                engine_config = self._load_golden_config()
                self._quantum_engine = QuantumEngine()
                # Update engine with full golden config
                if engine_config:
                    self._quantum_engine.update_full_config(engine_config)
                    logger.debug(f"Updated QuantumEngine with full golden config from config/parameters.json")
            
            # V50.0: Always update engine config with latest golden parameters
            # This ensures engine uses the latest optimized parameters from config/parameters.json
            engine_config = self._load_golden_config()
            if engine_config:
                self._quantum_engine.update_full_config(engine_config)
                logger.debug(f"Updated QuantumEngine with latest golden config")
                
            # 4. BaziProfile
            logger.debug("Creating BaziProfile...")
            birth_dt = datetime.datetime.combine(d, datetime.time(t, 0))
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
        logger.info(f"Starting timeline simulation: start_year={start_year}, duration={duration}, use_cache={use_cache}")
        start_time = time.time()
        
        try:
            if not self._quantum_engine or not self._profile:
                raise BaziDataError(
                    "缺少必要的引擎或配置文件",
                    "QuantumEngine or BaziProfile not initialized. Call set_user_input() first."
                )
            
            # V9.5 Performance Optimization: Check cache first
            cache_key = None
            if use_cache and case_data is None:
                cache_key = self._generate_cache_key(start_year, duration, params)
                if cache_key in self._timeline_cache:
                    self._cache_stats['hits'] += 1
                    logger.info(f"Cache HIT for key: {cache_key[:16]}...")
                    # Return deep copy to prevent cache pollution
                    df, handovers = self._timeline_cache[cache_key]
                    elapsed = time.time() - start_time
                    logger.info(f"Timeline simulation completed (cached) in {elapsed:.4f} seconds")
                    return df.copy(), copy.deepcopy(handovers)
                else:
                    self._cache_stats['misses'] += 1
                    logger.debug(f"Cache MISS for key: {cache_key[:16]}...")
            
            # Build case_data if not provided
            if case_data is None:
                logger.debug("Building case_data from user input...")
                case_data = self._build_case_data(params)
            
            # GanZhi calculation helpers
            gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
            zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
            base_year = 1924
            
            traj_data = []
            handover_years = []
            
            # Initialize prev_luck to detect handovers correctly
            prev_luck = self._profile.get_luck_pillar_at(start_year - 1)
            
            logger.debug(f"Processing {duration} years starting from {start_year}...")
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
                # V9.5 Performance Optimization: Pass cached era_multipliers
                try:
                    energy_res = self._quantum_engine.calculate_energy(
                        safe_case_data, 
                        dyn_ctx,
                        era_multipliers=self._era_multipliers
                    )
                except Exception as e:
                    logger.error(f"Error calculating energy for year {y}: {e}", exc_info=True)
                    raise BaziCalculationError(
                        f"计算年份 {y} 的能量时发生错误",
                        f"Error in calculate_energy for year {y}: {str(e)}"
                    )
                
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
            
            # Build result
            result_df = pd.DataFrame(traj_data)
            result_handovers = handover_years
            
            # V9.5 Performance Optimization: Cache result if using cache
            if use_cache and cache_key is not None:
                logger.debug(f"Caching result with key: {cache_key[:16]}...")
                try:
                    # Store deep copies to prevent cache pollution
                    self._timeline_cache[cache_key] = (
                        result_df.copy(),
                        copy.deepcopy(result_handovers)
                    )
                    logger.debug(f"Result cached successfully (cache size: {len(self._timeline_cache)})")
                except Exception as e:
                    logger.warning(f"Failed to cache result: {e}", exc_info=True)
                    # Continue without caching - not critical
            
            elapsed = time.time() - start_time
            logger.info(f"Timeline simulation completed in {elapsed:.4f} seconds "
                       f"(years: {duration}, rows: {len(result_df)})")
            
            return result_df, result_handovers
            
        except BaziDataError:
            raise
        except BaziCacheError:
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Timeline simulation failed after {elapsed:.4f} seconds: {e}", exc_info=True)
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

    def get_current_era_factor(self) -> Dict[str, float]:
        """
        Return current ERA factor stored in user input.
        """
        era = self._user_input.get('era_factor') if self._user_input else None
        if isinstance(era, dict):
            return era
        return {}

    def get_current_particle_weights(self) -> Dict[str, float]:
        """
        V16.0: Return current particle weights.
        Priority: user_input > config file > defaults (1.0)
        """
        # First check user input (from UI sliders)
        pw = self._user_input.get('particle_weights') if self._user_input else None
        if pw:
            return pw
        
        # Fall back to config file (single source of truth)
        if self._particle_weights_config:
            return self._particle_weights_config.copy()
        
        # Default: all 1.0
        from utils.constants_manager import get_constants
        consts = get_constants()
        return {god: 1.0 for god in consts.TEN_GODS}
    
    def get_particle_weight_from_config(self, god_name: str) -> float:
        """
        V16.0: Get a specific particle weight from config file.
        Returns 1.0 if not found.
        """
        return self._particle_weights_config.get(god_name, 1.0)
        if isinstance(pw, dict):
            return pw
        return {}

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
