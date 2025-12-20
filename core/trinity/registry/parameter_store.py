"""
Quantum Trinity: Parameter Store (V1.0)
========================================
Centralized management for all algorithmic and physical parameters.
Unifies config_schema.py and PhysicsParameters.
"""

import json
import os
from typing import Dict, Any, Optional

class ParameterStore:
    """
    Unified Parameter Store supporting hierarchical access and hot-reloading.
    """
    def __init__(self, config_path: Optional[str] = None):
        self._params = {}
        self._init_defaults()
        if config_path and os.path.exists(config_path):
            self.load(config_path)

    def _init_defaults(self):
        """Standardized default parameters from V13.1 logic."""
        self._params = {
            "physics": {
                "seasonWeights": {"wang": 1.20, "xiang": 1.00, "xiu": 0.90, "qiu": 0.60, "si": 0.45},
                "pillarWeights": {"year": 0.7, "month": 1.42, "day": 1.35, "hour": 0.77},
                "hiddenStemRatios": {"main": 0.60, "middle": 0.30, "remnant": 0.10},
                "lifeStageImpact": 0.2,
                "angle_tolerance": 5.0,
                "chong_power": 0.8,
                "sanhe_power": 1.5,
                "liuhe_power": 1.2,
                "xing_power": 0.3
            },
            "flow": {
                "generationEfficiency": 0.7,
                "generationDrain": 0.3,
                "controlImpact": 0.5,
                "dampingFactor": 0.1,
                "scorchedEarthDamping": 0.15,
                "frozenWaterDamping": 0.3
            },
            "grading": {
                "strong_threshold": 60.0,
                "weak_threshold": 40.0,
                "follower_threshold": 0.15
            }
        }

    def get(self, path: str, default: Any = None) -> Any:
        """Access parameters using dot notation (e.g., 'physics.pillarWeights.month')"""
        keys = path.split('.')
        val = self._params
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, path: str, value: Any):
        """Set parameters using dot notation."""
        keys = path.split('.')
        val = self._params
        for k in keys[:-1]:
            val = val.setdefault(k, {})
        val[keys[-1]] = value

    def load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._params.update(data)

    def save(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._params, f, indent=2, ensure_ascii=False)

    def flatten(self) -> Dict[str, Any]:
        """Convert to a flat dictionary for Optuna/Optimization."""
        flat = {}
        def _recurse(d, prefix):
            for k, v in d.items():
                new_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    _recurse(v, new_key)
                else:
                    flat[new_key] = v
        _recurse(self._params, "")
        return flat
