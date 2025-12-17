"""
非线性激活函数模块 (Nonlinear Activation Functions)
====================================================

V10.0 优化：从硬编码 if/else 转向非线性 Soft-thresholding 模型

核心功能：
1. Softplus/Sigmoid 软阈值函数
2. 相变能量模型 (Phase Transition Energy Model)
3. 量子隧穿概率模型
4. 多因素综合影响计算

作者: Antigravity Team
版本: V10.0
日期: 2025-01-XX
"""

import numpy as np
from typing import Dict, Tuple, Optional

try:
    from scipy.special import softplus, expit
    HAS_SCIPY = True
except ImportError:
    # 手动实现 softplus 和 expit
    HAS_SCIPY = False
    
    def softplus(x):
        """手动实现 softplus: log(1 + exp(x))"""
        # 防止溢出
        if x > 20:
            return x
        return np.log1p(np.exp(x))
    
    def expit(x):
        """手动实现 expit (sigmoid): 1 / (1 + exp(-x))"""
        # 防止溢出
        if x > 20:
            return 1.0
        if x < -20:
            return 0.0
        return 1.0 / (1.0 + np.exp(-x))


class NonlinearActivation:
    """非线性激活函数集合，用于模拟相变和量子隧穿效应"""
    
    @staticmethod
    def softplus_threshold(x: float, threshold: float = 0.5, scale: float = 10.0) -> float:
        """
        Softplus 软阈值函数
        
        用于模拟能量在临界点处的平滑过渡，避免硬编码的 if/else 跳跃。
        
        Args:
            x: 输入值（如身强归一化值）
            threshold: 阈值（临界点）
            scale: 缩放因子，控制过渡的陡峭程度
        
        Returns:
            平滑的激活值 [0, 1]
        """
        k = scale
        numerator = softplus(k * (x - threshold))
        denominator = 1 + softplus(k * (x - threshold))
        return numerator / denominator if denominator > 0 else 0.0
    
    @staticmethod
    def sigmoid_threshold(x: float, threshold: float = 0.5, steepness: float = 10.0) -> float:
        """
        Sigmoid 软阈值函数
        
        用于模拟相变点处的平滑过渡。
        
        Args:
            x: 输入值
            threshold: 阈值（相变点）
            steepness: 陡峭度，控制过渡的平滑程度
        
        Returns:
            平滑的激活值 [0, 1]
        """
        k = steepness
        return expit(k * (x - threshold))
    
    @staticmethod
    def phase_transition_energy(
        strength_normalized: float,
        clash_intensity: float = 1.0,
        trine_effect: float = 0.0,
        base_energy: float = 100.0,
        phase_point: float = 0.5,
        critical_exponent: float = 2.0
    ) -> float:
        """
        相变能量模型 (Phase Transition Energy Model)
        
        模拟热力学相变：当能量密度超过临界点时，触发整体结构的"气化"或"晶裂"，
        改变其对日主的做功效率。
        
        基于 Landau 相变理论：
        E = E_base × (1 + α × (x - x_c)^β)
        
        Args:
            strength_normalized: 身强归一化值 [0, 1]
            clash_intensity: 冲的强度 [0, 1]（考虑冲的类型、距离等）
            trine_effect: 三刑效应 [0, 1]（三刑的完整程度）
            base_energy: 基础能量（如 100.0）
            phase_point: 相变点（临界点，如 0.5）
            critical_exponent: 临界指数（控制相变的陡峭程度）
        
        Returns:
            相变后的能量值
        """
        # 综合激活因子
        activation = NonlinearActivation.sigmoid_threshold(
            strength_normalized,
            threshold=phase_point,
            steepness=10.0
        )
        
        # 多因素综合影响
        # 1. 身强激活因子
        strength_factor = activation
        
        # 2. 冲的强度因子（冲越强，能量释放越大）
        clash_factor = 0.5 + 0.5 * clash_intensity  # [0.5, 1.0]
        
        # 3. 三刑效应因子（三刑增强能量释放）
        trine_factor = 1.0 + 0.3 * trine_effect  # [1.0, 1.3]
        
        # 4. 相变修正（当超过临界点时，触发非线性增长）
        if strength_normalized > phase_point:
            # 超临界相变：能量非线性增长
            excess = strength_normalized - phase_point
            phase_multiplier = 1.0 + (excess ** critical_exponent) * 0.5
        else:
            # 亚临界：能量线性衰减
            deficit = phase_point - strength_normalized
            phase_multiplier = 1.0 - deficit * 0.5
        
        # 综合能量计算
        final_energy = base_energy * strength_factor * clash_factor * trine_factor * phase_multiplier
        
        return final_energy
    
    @staticmethod
    def quantum_tunneling_probability(
        barrier_height: float,
        particle_energy: float,
        barrier_width: float = 1.0
    ) -> float:
        """
        量子隧穿概率模型
        
        用于模拟"墓库开启"的量子隧穿效应。
        即使能量不足以直接突破库的屏障，也有一定概率通过隧穿效应开启。
        
        基于 WKB 近似：
        P = exp(-2 * k * width)
        k = sqrt(2m(V - E)) / ħ
        
        Args:
            barrier_height: 屏障高度（库的封闭强度）
            particle_energy: 粒子能量（冲的能量）
            barrier_width: 屏障宽度（库的厚度）
        
        Returns:
            隧穿概率 [0, 1]
        """
        if particle_energy >= barrier_height:
            return 1.0  # 能量足够，直接突破
        
        # 能量不足，计算隧穿概率
        energy_deficit = barrier_height - particle_energy
        if energy_deficit <= 0:
            return 1.0
        
        # 简化的隧穿概率公式
        tunneling_prob = np.exp(-2.0 * np.sqrt(energy_deficit) * barrier_width)
        
        return max(0.0, min(1.0, tunneling_prob))
    
    @staticmethod
    def calculate_vault_energy_nonlinear(
        strength_normalized: float,
        clash_type: str,  # '冲' or '合'
        clash_intensity: float,  # 冲的强度 [0, 1]
        has_trine: bool,  # 是否有三刑
        trine_completeness: float = 1.0,  # 三刑完整程度 [0, 1]
        base_bonus: float = 100.0,
        base_penalty: float = -120.0,
        config: Optional[Dict] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        非线性财库能量计算
        
        使用 Soft-thresholding 和相变模型，替代硬编码的 if/else。
        
        Args:
            strength_normalized: 身强归一化值 [0, 1]
            clash_type: 冲的类型 ('冲' or '合')
            clash_intensity: 冲的强度 [0, 1]
            has_trine: 是否有三刑
            trine_completeness: 三刑完整程度 [0, 1]
            base_bonus: 基础加成（身强时）
            base_penalty: 基础惩罚（身弱时）
            config: 配置参数（可选）
        
        Returns:
            (最终能量值, 详细分解字典)
        """
        if config is None:
            config = {}
        
        # 从配置读取参数，或使用默认值
        # [V10.1] 支持新的参数名称（用于贝叶斯优化）
        threshold = config.get('threshold', config.get('strength_threshold', 0.5))
        scale = config.get('scale', config.get('strength_beta', 10.0))  # strength_beta 对应 scale
        steepness = config.get('steepness', config.get('clash_k', 10.0))  # clash_k 对应 steepness
        phase_point = config.get('phase_point', 0.5)
        critical_exponent = config.get('critical_exponent', 2.0)
        barrier_height = config.get('barrier_height', 0.6)
        barrier_width = config.get('barrier_width', 1.0)
        
        # [V10.1] 三刑和隧穿参数
        trine_boost = config.get('trine_boost', config.get('trine_effect_weight', 0.3))
        tunneling_factor = config.get('tunneling_factor', 0.1)
        
        details = {}
        
        # 1. 身强激活因子（使用 Softplus 软阈值）
        strength_activation = NonlinearActivation.softplus_threshold(
            strength_normalized,
            threshold=threshold,
            scale=scale
        )
        details['strength_activation'] = strength_activation
        
        # 2. 冲的强度因子
        clash_factor = 0.5 + 0.5 * clash_intensity
        details['clash_factor'] = clash_factor
        
        # 3. 三刑效应因子
        # [V10.1] 使用 trine_boost 参数
        if has_trine:
            trine_factor = 1.0 + trine_boost * trine_completeness
        else:
            trine_factor = 1.0
        details['trine_factor'] = trine_factor
        
        # 4. 相变能量计算
        phase_energy = NonlinearActivation.phase_transition_energy(
            strength_normalized=strength_normalized,
            clash_intensity=clash_intensity,
            trine_effect=trine_completeness if has_trine else 0.0,
            base_energy=base_bonus,
            phase_point=phase_point,
            critical_exponent=critical_exponent
        )
        details['phase_energy'] = phase_energy
        
        # 5. 量子隧穿概率（考虑库的封闭强度）
        particle_energy = strength_normalized * clash_intensity
        base_tunneling_prob = NonlinearActivation.quantum_tunneling_probability(
            barrier_height=barrier_height,
            particle_energy=particle_energy,
            barrier_width=barrier_width
        )
        # [V10.1] 应用 tunneling_factor 缩放
        tunneling_prob = base_tunneling_prob * tunneling_factor
        details['tunneling_prob'] = tunneling_prob
        details['base_tunneling_prob'] = base_tunneling_prob
        
        # 6. 综合能量计算
        # 如果身强，使用正向能量；如果身弱，使用负向能量
        if strength_normalized > threshold:
            # 身强：财富爆发
            base = base_bonus
            polarity = 1.0
        else:
            # 身弱：库塌损失
            base = abs(base_penalty)
            polarity = -1.0
        
        # 非线性修正
        nonlinear_correction = strength_activation * clash_factor * trine_factor * tunneling_prob
        
        final_energy = base * nonlinear_correction * polarity
        
        details['base_energy'] = base
        details['nonlinear_correction'] = nonlinear_correction
        details['final_energy'] = final_energy
        
        return final_energy, details
    
    @staticmethod
    def calculate_penalty_nonlinear(
        strength_normalized: float,
        penalty_type: str,  # 'clash_commander', 'seven_kill', '截脚'
        intensity: float = 1.0,  # 强度 [0, 1]
        has_help: bool = False,
        has_mediation: bool = False,
        base_penalty: float = -100.0,
        config: Optional[Dict] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        非线性惩罚计算
        
        用于冲提纲、七杀攻身等惩罚机制。
        
        Args:
            strength_normalized: 身强归一化值 [0, 1]
            penalty_type: 惩罚类型
            intensity: 强度 [0, 1]
            has_help: 是否有帮身
            has_mediation: 是否有通关
            base_penalty: 基础惩罚
            config: 配置参数（可选）
        
        Returns:
            (最终惩罚值, 详细分解字典)
        """
        if config is None:
            config = {}
        
        details = {}
        
        # 1. 基础惩罚强度
        base_intensity = intensity
        details['base_intensity'] = base_intensity
        
        # 2. 帮身缓解因子
        if has_help:
            help_factor = 0.6  # 有帮身，缓解 40%
        else:
            help_factor = 1.0
        details['help_factor'] = help_factor
        
        # 3. 通关缓解因子
        if has_mediation:
            mediation_factor = 0.3  # 有通关，缓解 70%
        else:
            mediation_factor = 1.0
        details['mediation_factor'] = mediation_factor
        
        # 4. 身强缓解因子（身强更能承受惩罚）
        # [V10.0] 优化：对于身强的情况，特别是 strength_normalized > 0.9 时，大幅降低惩罚
        if strength_normalized > 0.9:
            # 身极强：惩罚减少到 20-30%
            strength_factor = 0.2 + 0.1 * (1.0 - strength_normalized)  # [0.2, 0.3]
        elif strength_normalized > 0.7:
            # 身强：惩罚减少到 30-50%
            strength_factor = 0.3 + 0.2 * ((strength_normalized - 0.7) / 0.2)  # [0.3, 0.5]
        elif strength_normalized > 0.5:
            # 身稍强：惩罚减少到 50-70%
            strength_factor = 0.5 + 0.2 * ((strength_normalized - 0.5) / 0.2)  # [0.5, 0.7]
        else:
            # 身弱：惩罚加重
            strength_factor = 1.0 + (0.5 - strength_normalized)  # [1.0, 1.5]
        details['strength_factor'] = strength_factor
        
        # 5. 综合惩罚计算
        final_penalty = base_penalty * base_intensity * help_factor * mediation_factor * strength_factor
        
        details['final_penalty'] = final_penalty
        
        return final_penalty, details

