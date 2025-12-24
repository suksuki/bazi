
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import math
import numpy as np

class NonlinearType(Enum):
    NONE = "none"
    SIGMOID = "sigmoid"
    GAUSSIAN_DAMPING = "gaussian_damping"
    EXPONENTIAL_DECAY = "exponential_decay"
    IMPULSE = "impulse"
    LINEAR_SHIFT = "linear_shift"
    # [V13.7] 新增高阶物理类型
    COMPLEX_IMPEDANCE = "complex_impedance"  # 复阻抗
    ORBITAL_PERTURBATION = "orbital_perturbation"  # 轨道摄动
    QUANTUM_PROBABILITY = "quantum_probability"  # 量子概率

@dataclass
class PhysicsTensor:
    """
    [V13.7] 高阶物理张量：支持相位(phi)和频率(omega)的完整物理描述
    
    用于替代简单的数值加减，实现真正的物理动力学模型。
    """
    amplitude: float = 1.0  # 振幅
    phase: float = 0.0      # 相位 (phi, 弧度)
    frequency: float = 1.0   # 频率 (omega, rad/s)
    damping: float = 0.0    # 阻尼系数
    impedance_real: float = 1.0  # 阻抗实部 (R)
    impedance_imag: float = 0.0  # 阻抗虚部 (X)
    
    def to_complex(self) -> complex:
        """转换为复数形式 Z = R + jX"""
        return complex(self.impedance_real, self.impedance_imag)
    
    def magnitude(self) -> float:
        """计算阻抗模长 |Z| = sqrt(R² + X²)"""
        return math.sqrt(self.impedance_real**2 + self.impedance_imag**2)
    
    def phase_angle(self) -> float:
        """计算阻抗相位角 arg(Z) = atan2(X, R)"""
        return math.atan2(self.impedance_imag, self.impedance_real)

@dataclass
class ExpectationVector:
    """
    [V13.7 升级] 期望向量：支持张量注入
    
    每个元素现在可以携带完整的物理张量信息，而不仅仅是标量值。
    """
    elements: Dict[str, float] = field(default_factory=lambda: {
        "wood": 1.0, "fire": 1.0, "earth": 1.0, "metal": 1.0, "water": 1.0
    })
    indicators: Dict[str, float] = field(default_factory=dict)
    source: str = "base"
    # [V13.7] 新增：张量字典，存储每个元素的完整物理信息
    tensors: Dict[str, PhysicsTensor] = field(default_factory=dict)

    def clone(self):
        return ExpectationVector(
            elements=self.elements.copy(),
            indicators=self.indicators.copy(),
            source=self.source,
            tensors={k: PhysicsTensor(
                amplitude=v.amplitude,
                phase=v.phase,
                frequency=v.frequency,
                damping=v.damping,
                impedance_real=v.impedance_real,
                impedance_imag=v.impedance_imag
            ) for k, v in self.tensors.items()}
        )
    
    def get_tensor(self, element: str) -> PhysicsTensor:
        """获取元素的物理张量，如果不存在则创建默认张量"""
        if element not in self.tensors:
            self.tensors[element] = PhysicsTensor(
                amplitude=self.elements.get(element, 1.0)
            )
        return self.tensors[element]
    
    def set_tensor(self, element: str, tensor: PhysicsTensor):
        """设置元素的物理张量，并同步更新标量值"""
        self.tensors[element] = tensor
        self.elements[element] = tensor.amplitude

class InfluenceFactor:
    """
    [V13.7 升级] 影响因子基类：支持高阶张量注入
    
    现在可以返回包含相位(phi)和频率(omega)的完整物理张量。
    """
    def __init__(self, name: str, nonlinear_type: NonlinearType, weight: float = 1.0, enabled: bool = True, metadata: Dict = None):
        self.name = name
        self.type = nonlinear_type
        self.weight = weight
        self.enabled = enabled
        self.metadata = metadata or {}
        self._logs = []

    def apply_nonlinear_correction(self, base_e: ExpectationVector, context: Dict[str, Any] = None) -> ExpectationVector:
        """
        [V13.7] 应用非线性物理修正
        
        可以返回包含相位和频率的张量，而不仅仅是标量值。
        """
        return base_e
    
    def get_physics_tensor(self, element: str, base_amplitude: float, context: Dict[str, Any] = None) -> PhysicsTensor:
        """
        [V13.7] 获取物理张量（钩子函数）
        
        子类可以重写此方法，返回包含相位和频率的完整物理描述。
        默认返回简单的标量张量。
        """
        return PhysicsTensor(amplitude=base_amplitude)

    def log(self, msg: str):
        self._logs.append(msg)

class InfluenceBus:
    """The 'God Plug-in' Registry & Orchestrator."""
    def __init__(self):
        self._factors: List[InfluenceFactor] = []
        self._active_verdict = {}

    def register(self, factor: InfluenceFactor):
        self._factors.append(factor)

    @property
    def active_factors(self) -> List[InfluenceFactor]:
        return [f for f in self._factors if f.enabled]

    @property
    def factor_count(self) -> int:
        return len(self.active_factors)

    def arbitrate_environment(self, base_waves: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate multiple factors to modify the base wave field.
        Returns a modified set of waves or a unified correction map.
        """
        # 1. Create expectation vector from waves
        e_vector = ExpectationVector(
            elements={k.lower(): v.amplitude for k, v in base_waves.items()},
            source="bus_init"
        )

        # 2. Sequential application of active factors (Non-linear stacking)
        for factor in self.active_factors:
            e_vector = factor.apply_nonlinear_correction(e_vector, context)

        # 3. Store result for telemetry
        self._active_verdict = {
            "expectation": e_vector,
            "logs": {f.name: f._logs for f in self.active_factors}
        }

        return self._active_verdict
