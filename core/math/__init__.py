"""
Antigravity Core Math Module
============================

统一的数学模型接口，包含分布层、内核层、物理层和工具层。
"""

from .distributions import ProbValue, prob_compare
from .kernels import (
    expit, softplus, gating_function, 
    sigmoid_threshold, softplus_threshold
)
from .physics import (
    calculate_control_damage, 
    calculate_generation,
    quantum_tunneling_probability,
    phase_transition_energy
)
from .utils import (
    saturation_curve, 
    exponential_decay, 
    smooth_step,
    gaussian_gating
)

__all__ = [
    'ProbValue', 'prob_compare',
    'expit', 'softplus', 'gating_function',
    'sigmoid_threshold', 'softplus_threshold',
    'calculate_control_damage', 'calculate_generation',
    'quantum_tunneling_probability', 'phase_transition_energy',
    'saturation_curve', 'exponential_decay', 'smooth_step',
    'gaussian_gating'
]
