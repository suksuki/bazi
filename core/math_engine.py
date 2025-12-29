"""
QGA 数学内核引擎 (Math Engine)
封装所有数学计算函数，支持向量化操作

基于FDS-V1.1规范，从Step 3和Step 4验证成功的代码中提取
"""

import numpy as np
import math
from typing import Union, Dict, List, Tuple


def sigmoid_variant(x: Union[float, np.ndarray], k: float = 1.0, x0: float = 0.0) -> Union[float, np.ndarray]:
    """
    Sigmoid激活函数（支持向量化输入）
    
    公式: 1 / (1 + exp(-k * (x - x0)))
    
    Args:
        x: 输入值（可以是标量或numpy数组）
        k: 陡峭度参数（默认1.0）
        x0: 中心点偏移（默认0.0）
        
    Returns:
        Sigmoid输出值（与输入同类型）
        
    Example:
        >>> sigmoid_variant(0.0, k=1.0, x0=0.0)
        0.5
        >>> sigmoid_variant([0.0, 1.0, 2.0], k=1.0, x0=0.0)
        array([0.5, 0.731..., 0.880...])
    """
    if isinstance(x, np.ndarray):
        return 1.0 / (1.0 + np.exp(-k * (x - x0)))
    else:
        return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def tensor_normalize(vector: Dict[str, float]) -> Dict[str, float]:
    """
    张量归一化（单位向量约束）
    
    确保权重向量满足归一化原则：∑|w_i| = 1
    
    公式: w_i_new = w_i_old / ∑|w_i|
    
    Args:
        vector: 权重字典，如 {'E': 0.3, 'O': 0.5, 'M': 0.1, 'S': 0.05, 'R': 0.05}
        
    Returns:
        归一化后的权重字典
        
    Example:
        >>> tensor_normalize({'E': 0.3, 'O': 0.5, 'M': 0.1, 'S': 0.05, 'R': 0.05})
        {'E': 0.3, 'O': 0.5, 'M': 0.1, 'S': 0.05, 'R': 0.05}  # 已经归一化
        >>> tensor_normalize({'E': 0.6, 'O': 0.8, 'M': 0.2})
        {'E': 0.375, 'O': 0.5, 'M': 0.125}  # 归一化后
    """
    total = sum(abs(v) for v in vector.values())
    
    if total == 0:
        return vector  # 避免除零
    
    return {k: round(v / total, 4) for k, v in vector.items()}


def check_normalized(vector: Dict[str, float], tolerance: float = 0.01) -> bool:
    """
    检查权重向量是否已归一化
    
    Args:
        vector: 权重字典
        tolerance: 容差（默认0.01）
        
    Returns:
        是否归一化（在容差范围内）
    """
    total = sum(abs(v) for v in vector.values())
    return abs(total - 1.0) < tolerance


def phase_change_determination(
    energy: float,
    threshold: float = 0.8,
    trigger: bool = False
) -> str:
    """
    相变判定（基于FDS-V1.1规范）
    
    判断系统处于哪种状态：
    - TUNNELING: 能量爆发（能量高且触发）
    - COLLAPSE: 结构坍塌（能量低且触发）
    - STABLE: 稳定态
    
    Args:
        energy: 能量值（归一化到0-1）
        threshold: 临界阈值（默认0.8）
        trigger: 是否有外部触发（如冲、合）
        
    Returns:
        相变状态字符串：'TUNNELING', 'COLLAPSE', 'STABLE'
    """
    if energy > threshold and trigger:
        return 'TUNNELING'  # 隧穿效应：能量爆发
    elif energy < threshold and trigger:
        return 'COLLAPSE'   # 结构坍塌：能量湮灭
    else:
        return 'STABLE'     # 稳定态


def calculate_s_balance(e_blade: float, e_kill: float) -> float:
    """
    计算平衡度（核心方程）
    
    公式: S_balance = E_blade / E_kill
    
    Args:
        e_blade: 羊刃能量
        e_kill: 七杀能量
        
    Returns:
        平衡度值
        
    Note:
        - S_balance ≈ 1.0 → 共振态（大贵）
        - S_balance > 1.2 → 能量溢出（破财）
        - S_balance < 0.8 → 场强压垮（夭折）
    """
    if e_kill == 0:
        return float('inf') if e_blade > 0 else 0.0
    
    return e_blade / e_kill


def calculate_flow_factor(s_base: float, e_seal: float) -> float:
    """
    计算通关因子（Flow Factor）
    
    公式: S_risk = S_base / (1 + E_seal)
    
    物理意义：印星的存在作为分母上的安全系数，印星越有力，风险越小
    
    Args:
        s_base: 基础应力值
        e_seal: 印星能量
        
    Returns:
        修正后的应力值
    """
    return s_base / (1.0 + e_seal)

