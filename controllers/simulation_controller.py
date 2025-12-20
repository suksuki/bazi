import logging
import time
import copy
import hashlib
import json
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from core.engine_v88 import EngineV88 as QuantumEngine
from core.exceptions import BaziDataError

logger = logging.getLogger(__name__)

class SimulationController:
    """
    Controller responsible for executing Bazi simulations (timeline, single year).
    Manages its own result cache.
    """
    
    def __init__(self):
        self._timeline_cache: Dict[str, Tuple[pd.DataFrame, List[Dict]]] = {}
        self._cache_stats: Dict[str, int] = {
            'hits': 0, 
            'misses': 0, 
            'invalidations': 0
        }

    def _generate_cache_key(self, user_input: Dict, start_year: int, duration: int, 
                           params: Optional[Dict] = None) -> str:
        """Generate a unique cache key for timeline simulation."""
        key_data = {
            'user_input': user_input,
            'start_year': start_year,
            'duration': duration,
            'params': params or {}
        }
        # Create hash from key data
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        return f"timeline_{key_hash}"

    def invalidate_cache(self) -> None:
        """Invalidate all cached simulation results."""
        if self._timeline_cache:
            count = len(self._timeline_cache)
            self._cache_stats['invalidations'] += count
            self._timeline_cache.clear()
            logger.info(f"Simulation cache invalidated: {count} entries cleared")

    def run_single_year(self, engine: QuantumEngine, case_data: Dict, 
                        dynamic_context: Dict, era_multipliers: Dict[str, float]) -> Dict:
        """Run simulation for a single year."""
        if not engine:
            return {}
        return engine.calculate_energy(
            case_data, 
            dynamic_context,
            era_multipliers=era_multipliers
        )

    def run_timeline(self, engine: QuantumEngine, profile,
                     user_input: Dict, case_data: Dict,
                     start_year: int, duration: int, 
                     era_multipliers: Dict[str, float],
                     params: Optional[Dict] = None,
                     use_cache: bool = True) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Run multi-year timeline simulation.
        """
        logger.info(f"Starting timeline simulation: start_year={start_year}, duration={duration}, use_cache={use_cache}")
        start_time = time.time()
        
        if not engine or not profile:
             raise BaziDataError(
                "缺少必要的引擎或配置文件",
                "QuantumEngine or BaziProfile not provided."
            )

        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(user_input, start_year, duration, params)
            if cache_key in self._timeline_cache:
                self._cache_stats['hits'] += 1
                logger.debug(f"Cache HIT for key: {cache_key[:16]}...")
                df, handovers = self._timeline_cache[cache_key]
                return df.copy(), copy.deepcopy(handovers)
            else:
                self._cache_stats['misses'] += 1

        gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        base_year = 1924
        
        traj_data = []
        handover_years = []
        
        prev_luck = profile.get_luck_pillar_at(start_year - 1)
        
        for y in range(start_year, start_year + duration):
            offset = y - base_year
            l_gan = gan_chars[offset % 10]
            l_zhi = zhi_chars[offset % 12]
            l_gz = f"{l_gan}{l_zhi}"
            
            active_luck = profile.get_luck_pillar_at(y)
            
            if prev_luck and prev_luck != active_luck:
                handover_years.append({
                    'year': y,
                    'from': prev_luck,
                    'to': active_luck
                })
            prev_luck = active_luck
            
            safe_case_data = copy.deepcopy(case_data)
            dyn_ctx = {'year': l_gz, 'dayun': active_luck, 'luck': active_luck}
            
            try:
                energy_result = engine.calculate_energy(
                    safe_case_data, 
                    dyn_ctx,
                    era_multipliers=era_multipliers
                )
            except Exception as e:
                logger.error(f"Error simulating year {y}: {e}")
                continue
                
            # Flatten result for DataFrame
            row = {
                'year': y,
                'gan_zhi': l_gz,
                'luck': active_luck,
                'score': energy_result.get('total_strength', 0),
                'structure_score': energy_result.get('structure_score', 0), # Assuming this exists
                'flow_score': energy_result.get('flow_score', 0),
                'health_score': energy_result.get('health_score', 80), # Default
                'wealth_score': energy_result.get('wealth_score', 0),
            }
            # Flatten 5 elements
            for elem, val in energy_result.get('final_energy', {}).items():
                row[f"elem_{elem}"] = val
                
            traj_data.append(row)
            
        df = pd.DataFrame(traj_data)
        
        # Cache result
        if use_cache:
            self._timeline_cache[cache_key] = (df, copy.deepcopy(handover_years))
            
        elapsed = time.time() - start_time
        logger.info(f"Timeline simulation completed in {elapsed:.4f} seconds")
        
        return df, handover_years

    def get_cache_stats(self) -> Dict[str, int]:
        stats = self._cache_stats.copy()
        stats['size'] = len(self._timeline_cache)
        return stats
