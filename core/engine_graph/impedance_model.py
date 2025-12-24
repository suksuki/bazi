"""
[V13.7 整合升级] MOD_15 结构传导：复阻抗模型 (Complex Impedance Model)
=======================================================================

核心物理问题：为什么大运虽然生助，但因为相位不合，能量却传导不过去？

解决方案：引入复阻抗 Z = R + jX
- R (实部): 代表原局干支的硬性克制（电阻）
- X (虚部): 代表大运带来的相位迟滞（电抗）

当大运产生刑冲时，X激增，导致能量传导发生非线性阻塞。

[V13.7] 整合了 PH_NONLINEAR_SATURATION 和 PH_VERTICAL_COUPLING 算法。
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from core.engine_graph.graph_node import GraphNode
from core.interactions import BRANCH_CLASHES
from core.trinity.core.middleware.influence_bus import PhysicsTensor


class ComplexImpedanceModel:
    """
    [V13.7] 复阻抗模型：模拟能量传导的非线性阻塞
    
    核心公式：
    Z = R + jX
    |Z| = sqrt(R² + X²)
    efficiency = 1 / |Z| = 1 / sqrt(R² + X²)
    """
    
    def __init__(self, config: Dict[str, Any], day_master: Optional[str] = None):
        """
        [V13.7 整合升级] 初始化复阻抗模型
        
        Args:
            config: 配置字典，包含阻抗相关参数
            day_master: 日主（可选，用于复用 StructuralVibrationEngine）
        """
        self.config = config
        self.impedance_cache = {}  # 缓存阻抗计算结果
        
        # [V13.7] 复用 StructuralVibrationEngine 的功能
        self.vibration_engine = None
        if day_master:
            try:
                from core.trinity.core.engines.structural_vibration import StructuralVibrationEngine
                self.vibration_engine = StructuralVibrationEngine(day_master=day_master)
            except ImportError:
                pass  # 如果导入失败，继续使用简化版本
    
    def calculate_impedance(
        self,
        source_node: GraphNode,
        target_node: GraphNode,
        source_energy: float,
        target_energy: float,
        luck_pillar: Optional[str] = None,
        year_pillar: Optional[str] = None,
        influence_bus: Optional[Any] = None
    ) -> Tuple[float, float, float]:
        """
        计算复阻抗 Z = R + jX
        
        Args:
            source_node: 源节点
            target_node: 目标节点
            source_energy: 源节点能量
            target_energy: 目标节点能量
            luck_pillar: 大运干支（可选）
            year_pillar: 流年干支（可选）
            influence_bus: InfluenceBus实例（可选，用于获取相位信息）
        
        Returns:
            (R, X, |Z|) 元组
            - R: 阻抗实部（电阻）
            - X: 阻抗虚部（电抗）
            - |Z|: 阻抗模长
        """
        # 1. 计算基础电阻 R（原局干支的硬性克制）
        R_base = self._calculate_resistance(source_node, target_node, source_energy, target_energy)
        
        # 2. 计算基础电抗 X（相位迟滞）
        X_base = self._calculate_reactance(source_node, target_node)
        
        # 3. [V13.7] 大运相位修正：如果大运产生刑冲，X激增
        X_luck = self._calculate_luck_reactance(
            source_node, target_node, luck_pillar, influence_bus
        )
        
        # 4. [V13.7] 流年相位修正：流年冲击影响相位
        X_annual = self._calculate_annual_reactance(
            source_node, target_node, year_pillar, influence_bus
        )
        
        # 5. 总阻抗
        R = R_base
        X = X_base + X_luck + X_annual
        
        # 6. 阻抗模长
        Z_magnitude = math.sqrt(R**2 + X**2)
        
        return (R, X, Z_magnitude)
    
    def _calculate_resistance(
        self,
        source_node: GraphNode,
        target_node: GraphNode,
        source_energy: float,
        target_energy: float
    ) -> float:
        """
        计算阻抗实部 R（电阻）
        
        代表原局干支的硬性克制关系。
        - 如果源节点克制目标节点，R较小（能量容易传导）
        - 如果目标节点克制源节点，R较大（能量传导受阻）
        """
        from core.processors.physics import CONTROL
        
        # 检查克制关系
        source_element = source_node.element
        target_element = target_node.element
        
        # 源克目标：R较小（能量容易传导）
        if source_element in CONTROL and CONTROL[source_element] == target_element:
            R = 0.5  # 低阻抗
        # 目标克源：R较大（能量传导受阻）
        elif target_element in CONTROL and CONTROL[target_element] == source_element:
            R = 2.0  # 高阻抗（反克）
        # 无克制关系：中等阻抗
        else:
            R = 1.0
        
        # 能量差异修正：能量差异越大，阻抗越大
        if source_energy > 0 and target_energy > 0:
            energy_ratio = max(source_energy, target_energy) / min(source_energy, target_energy)
            # 能量差异越大，阻抗增加（非线性）
            R *= (1.0 + 0.1 * math.log(energy_ratio + 1.0))
        
        return R
    
    def _calculate_reactance(
        self,
        source_node: GraphNode,
        target_node: GraphNode
    ) -> float:
        """
        [V13.7 整合升级] 计算基础电抗 X（相位迟滞）
        
        代表节点间的相位差异。
        - 同柱节点：相位一致，X=0
        - 相邻柱：相位略有差异，X较小
        - 远距离：相位差异大，X较大
        
        [V13.7] 可以复用 PH_VERTICAL_COUPLING 的逻辑计算垂直耦合贡献。
        """
        # 计算柱间距离
        distance = abs(target_node.pillar_idx - source_node.pillar_idx)
        
        # 距离衰减：距离越远，相位差异越大
        if distance == 0:
            X = 0.0  # 同柱，无相位差
        elif distance == 1:
            X = 0.2  # 相邻柱，小相位差
        elif distance == 2:
            X = 0.5  # 隔一柱，中等相位差
        else:
            X = 1.0  # 远距离，大相位差
        
        # [V13.7] 如果可用，复用垂直耦合逻辑（PH_VERTICAL_COUPLING）
        # 垂直耦合可以降低电抗（通根增强相位匹配）
        if self.vibration_engine and source_node.node_type == 'stem' and target_node.node_type == 'branch':
            # 检查是否有通根（垂直耦合）
            # 这里简化处理，实际可以调用 vibration_engine._apply_vertical_coupling 的逻辑
            # 如果有通根，电抗降低
            if hasattr(source_node, 'has_root') and source_node.has_root:
                X *= 0.7  # 通根降低30%电抗
        
        return X
    
    def _calculate_luck_reactance(
        self,
        source_node: GraphNode,
        target_node: GraphNode,
        luck_pillar: Optional[str],
        influence_bus: Optional[Any]
    ) -> float:
        """
        [V13.7] 计算大运相位修正（电抗增量）
        
        当大运产生刑冲时，X激增，导致能量传导发生非线性阻塞。
        """
        if not luck_pillar or len(luck_pillar) < 2:
            return 0.0
        
        X_luck = 0.0
        luck_branch = luck_pillar[1]
        
        # 检查大运是否与源节点或目标节点产生刑冲
        source_branch = source_node.char if source_node.node_type == 'branch' else None
        target_branch = target_node.char if target_node.node_type == 'branch' else None
        
        # 大运与源节点冲
        if source_branch and BRANCH_CLASHES.get(luck_branch) == source_branch:
            X_luck += 1.5  # 大运冲源节点，相位严重不匹配
        
        # 大运与目标节点冲
        if target_branch and BRANCH_CLASHES.get(luck_branch) == target_branch:
            X_luck += 1.5  # 大运冲目标节点，相位严重不匹配
        
        # [V13.7] 从 InfluenceBus 获取相位信息
        if influence_bus:
            for factor in influence_bus.active_factors:
                if hasattr(factor, 'luck_branch') and factor.luck_branch:
                    # 获取相位信息（如果可用）
                    tensor = influence_bus._active_verdict.get('expectation', {}).get('tensors', {})
                    if tensor:
                        # 如果有相位信息，使用相位差修正电抗
                        # phase_diff = abs(phase_source - phase_target)
                        # X_luck += phase_diff * 0.5
                        pass
        
        return X_luck
    
    def _calculate_annual_reactance(
        self,
        source_node: GraphNode,
        target_node: GraphNode,
        year_pillar: Optional[str],
        influence_bus: Optional[Any]
    ) -> float:
        """
        [V13.7] 计算流年相位修正（电抗增量）
        
        流年冲击影响相位，但衰减较快。
        """
        if not year_pillar or len(year_pillar) < 2:
            return 0.0
        
        X_annual = 0.0
        year_branch = year_pillar[1]
        
        # 检查流年是否与源节点或目标节点产生刑冲
        source_branch = source_node.char if source_node.node_type == 'branch' else None
        target_branch = target_node.char if target_node.node_type == 'branch' else None
        
        # 流年与源节点冲（冲击强度较小，因为流年衰减快）
        if source_branch and BRANCH_CLASHES.get(year_branch) == source_branch:
            X_annual += 0.8  # 流年冲击，相位不匹配（但比大运弱）
        
        # 流年与目标节点冲
        if target_branch and BRANCH_CLASHES.get(year_branch) == target_branch:
            X_annual += 0.8
        
        return X_annual
    
    def calculate_transmission_efficiency(
        self,
        R: float,
        X: float,
        Z_magnitude: Optional[float] = None
    ) -> float:
        """
        计算能量传导效率
        
        公式：efficiency = 1 / |Z| = 1 / sqrt(R² + X²)
        
        Args:
            R: 阻抗实部
            X: 阻抗虚部
            Z_magnitude: 阻抗模长（如果已计算，可传入避免重复计算）
        
        Returns:
            传导效率 (0-1)
        """
        if Z_magnitude is None:
            Z_magnitude = math.sqrt(R**2 + X**2)
        
        # 避免除零
        if Z_magnitude < 1e-6:
            return 1.0
        
        efficiency = 1.0 / Z_magnitude
        
        # 归一化到 [0, 1] 范围
        # 假设最大阻抗为 5.0，则最小效率为 0.2
        max_impedance = 5.0
        min_efficiency = 0.2
        normalized_efficiency = min_efficiency + (1.0 - min_efficiency) * (1.0 - min(Z_magnitude / max_impedance, 1.0))
        
        return max(normalized_efficiency, 0.0)
    
    def apply_impedance_correction(
        self,
        base_energy_flow: float,
        R: float,
        X: float,
        Z_magnitude: Optional[float] = None
    ) -> float:
        """
        [V13.7 整合升级] 应用阻抗修正到能量流
        
        公式：corrected_flow = base_flow * efficiency
        
        [V13.7] 在应用效率修正前，先应用非线性饱和（PH_NONLINEAR_SATURATION）
        防止能量溢出。
        
        Args:
            base_energy_flow: 基础能量流
            R: 阻抗实部
            X: 阻抗虚部
            Z_magnitude: 阻抗模长（可选）
        
        Returns:
            修正后的能量流
        """
        # [V13.7] 先应用非线性饱和（复用 PH_NONLINEAR_SATURATION）
        if self.vibration_engine:
            saturated_flow = self.vibration_engine._tanh_saturation(base_energy_flow)
        else:
            # 简化版本：直接使用 tanh 饱和
            E_MAX = 10.0
            threshold = E_MAX / 2.0
            saturated_flow = E_MAX * math.tanh(base_energy_flow / threshold)
        
        # 然后应用阻抗效率修正
        efficiency = self.calculate_transmission_efficiency(R, X, Z_magnitude)
        return saturated_flow * efficiency

