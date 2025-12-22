
"""
Quantum Trinity V2.0 (The Oracle)
=====================================
Modularized Bazi Physics Framework.
"""

from .core.oracle import TrinityOracle
from .core.nexus.definitions import PhysicsConstants, BaziParticleNexus
from .core.physics.wave_laws import WaveState, WaveLaws

__all__ = [
    'TrinityOracle',
    'PhysicsConstants',
    'BaziParticleNexus',
    'WaveState',
    'WaveLaws'
]
