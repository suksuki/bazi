import math
from typing import Dict, List, Optional

class WavePhysicsEngine:
    """
    V12.0 波动力学交互引擎
    负责处理非线性干涉 (Interference) 与共振 (Resonance)
    核心哲学：能量是波的强度，交互是波的干涉。
    """
    
    @staticmethod
    def compute_interference(energy_a: float, energy_b: float, interaction_type: str, params: Dict) -> float:
        """
        计算波的叠加干涉
        公式: E_net = A_net^2 = A_1^2 + A_2^2 + 2 * A_1 * A_2 * cos(theta)
        
        :param energy_a: 粒子A能量 (强度)
        :param energy_b: 粒子B能量 (强度)
        :param interaction_type: clash(冲), combine(合), harm(害), stem_combine(干合)
        :param params: 物理参数字典
        """
        # 1. 能量转振幅 (Amplitude): E = A^2 -> A = sqrt(E)
        amp_a = math.sqrt(max(0, energy_a))
        amp_b = math.sqrt(max(0, energy_b))
        
        # 2. 获取相位角 (Phase Angle) theta
        # clash -> 趋向 180度 (PI, 相消干涉)
        # combine -> 趋向 0度 (0, 相长干涉)
        # 从配置中读取，支持弧度。默认 90度 (PI/2, 正交无关)
        theta = params.get(f"{interaction_type}_phase", math.pi * 0.5)
        
        # 3. 计算干涉项 (Interference Term)
        interference_term = 2 * amp_a * amp_b * math.cos(theta)
        
        # 4. 叠加后的总能量
        energy_net = energy_a + energy_b + interference_term
        
        # 5. 应用熵增/损耗 (Entropy Loss)
        # 对应参数文件中的物理损耗
        entropy = params.get(f"{interaction_type}_entropy", 0.95)
        
        return max(0, energy_net) * entropy

    @staticmethod
    def compute_resonance(energies: List[float], q_factor: float) -> float:
        """
        计算腔体共振 (Resonance) - 用于处理多体交互（如丑未戌三刑）
        公式: E_net = (Sum E_i) * Q
        
        :param energies: 参与交互的各节点能量列表
        :param q_factor: 品质因数 (Quality Factor)，共振放大倍率
        """
        base_sum = sum(energies)
        return max(0, base_sum * q_factor)
