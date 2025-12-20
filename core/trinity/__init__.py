"""
Quantum Trinity (V1.0)
=======================
Unified implementation of Math, Physics, Registry, and Tuning systems.
"""

from .core.math_engine import ProbValue, prob_compare, expit, softplus, saturate, decay
from .core.physics_engine import PhysicsEngine, ParticleDefinitions
from .registry.parameter_store import ParameterStore
from .registry.rule_registry import RuleRegistry
from .tuning.engine import TuningEngine
from .tuning.verifier import UnifiedVerifier
from .tuning.strategies import BayesianStrategy, SCDStrategy

__all__ = [
    'ProbValue', 'prob_compare', 'expit', 'softplus', 'saturate', 'decay',
    'PhysicsEngine', 'ParticleDefinitions',
    'ParameterStore', 'RuleRegistry',
    'TuningEngine', 'UnifiedVerifier', 'BayesianStrategy', 'SCDStrategy'
]
