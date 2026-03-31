"""
V12.0 量子财富引力场引擎 (Quantum Wealth Field Engine)

核心模块：
- vectors.py: F, C, σ 三维向量计算
- tomb_physics.py: 墓库物理（冲开/坍塌临界判定）
- timeline_simulator.py: 0-100岁时间序列模拟器
"""

from .vectors import (
    calculate_flow_vector,
    calculate_capacity_vector,
    calculate_volatility_sigma
)

from .tomb_physics import (
    check_tomb_opening,
    calculate_tomb_clash_intensity
)

from .timeline_simulator import (
    simulate_life_wealth,
    calculate_wealth_potential
)

__all__ = [
    'calculate_flow_vector',
    'calculate_capacity_vector',
    'calculate_volatility_sigma',
    'check_tomb_opening',
    'calculate_tomb_clash_intensity',
    'simulate_life_wealth',
    'calculate_wealth_potential'
]

