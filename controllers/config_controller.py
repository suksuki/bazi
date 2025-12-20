import logging
import time
from typing import Dict, Optional, Any
from core.models.config_model import ConfigModel

logger = logging.getLogger(__name__)

class ConfigController:
    """
    Controller responsible for managing application configuration.
    Delegates persistence to ConfigModel.
    Handles caching and hot-reloading logic if needed.
    """
    
    def __init__(self):
        self._model = ConfigModel()
        self._cached_config: Optional[Dict[str, Any]] = None
        self._last_load_time = 0
        self._cache_ttl = 5.0 # Seconds (short TTL for development)

    def get_full_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Get the full configuration dictionary.
        Uses short-term caching to avoid excessive disk reads.
        """
        current_time = time.time()
        if force_reload or self._cached_config is None or (current_time - self._last_load_time > self._cache_ttl):
            try:
                self._cached_config = self._model.load_config()
                self._last_load_time = current_time
                logger.debug("Configuration loaded from disk")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                if self._cached_config is None:
                     return self._model.get_default_config()
        
        return self._cached_config

    def get_particle_weights(self) -> Dict[str, float]:
        """
        Get particle weights configuration.
        """
        config = self.get_full_config()
        return config.get('particleWeights', {})

    def get_physics_config(self) -> Dict[str, Any]:
        """
        Get physics configuration.
        """
        config = self.get_full_config()
        return config.get('physics', {})

    def update_config(self, new_config: Dict[str, Any], merge: bool = True) -> bool:
        """
        Update configuration and save to disk.
        """
        success = self._model.save_config(new_config, merge=merge)
        if success:
            self._cached_config = None # Invalidate cache
            self.get_full_config(force_reload=True) # Reload immediately
        return success

    def get_era_multipliers(self) -> Dict[str, float]:
        """
        Get era multipliers (currently hardcoded or loaded from separate file).
        TODO: Migrate era constants to main config or keep separate?
        For now, we can keep the logic from BaziController or move it here.
        BaziController loads it from data/era_constants.json.
        """
        # We can implement era loading here too to centralize input/output
        import os
        import json
        
        try:
            # Assuming standard path relative to this file
            # core is parent of controllers, data is sibling of core
            project_root = self._model.config_path.parent.parent
            era_path = project_root / "data" / "era_constants.json"
            
            if era_path.exists():
                with open(era_path, 'r', encoding='utf-8') as f:
                    era_data = json.load(f)
                    return era_data.get('physics_multipliers', {})
        except Exception as e:
            logger.warning(f"Failed to load era constants: {e}")
        
        return {}
