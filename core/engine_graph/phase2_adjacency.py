"""
Phase 2: 邻接矩阵构建模块
========================

负责构建图网络的邻接矩阵，将生克制化转化为矩阵权重。

包括：
- 邻接矩阵构建（生克、合化、冲等）
- 关系类型矩阵（用于 GAT）
- 权重计算（生、克、合、冲）
- 通关逻辑（Mediation）
- 大运和流年链接
"""

import math
import numpy as np
from typing import Dict, List, Any, Optional
from core.engine_graph.graph_node import GraphNode
from core.engine_graph.constants import TWELVE_LIFE_STAGES
from core.processors.physics import PhysicsProcessor, GENERATION, CONTROL
from core.math import ProbValue
from core.interactions import BRANCH_CLASHES, BRANCH_SIX_COMBINES, STEM_COMBINATIONS


class AdjacencyMatrixBuilder:
    """负责构建图网络的邻接矩阵"""
    
    def __init__(self, engine: 'GraphNetworkEngine'):
        """
        初始化邻接矩阵构建器。
        
        Args:
            engine: GraphNetworkEngine 实例，用于访问共享状态
        """
        self.engine = engine
        self.config = engine.config
    
    def build_adjacency_matrix(self) -> np.ndarray:
        """
        Phase 2: 构建邻接矩阵 A，将生克制化转化为矩阵权重。
        
        矩阵元素 A[i][j] 表示节点 j 对节点 i 的影响：
        - 正数：生（Generation）或合（Combination）
        - 负数：克（Control）或冲（Clash）
        - 零：无直接关系
        
        Returns:
            邻接矩阵 A [N x N]，其中 N 是节点数
        """
        if not hasattr(self.engine, 'nodes') or not self.engine.nodes:
            raise ValueError("必须先执行 initialize_nodes() 以创建节点")
        
        N = len(self.engine.nodes)
        A = np.zeros((N, N))
        
        interactions_config = self.config.get('interactions', {})
        flow_config = self.config.get('flow', {})
        
        # 获取交互参数
        combo_physics = interactions_config.get('comboPhysics', {})
        branch_events = interactions_config.get('branchEvents', {})
        flow_params = flow_config.get('resourceImpedance', {})
        
        # 遍历所有节点对
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue  # 自连接暂时设为0（可以后续添加）
                
                node_i = self.engine.nodes[i]
                node_j = self.engine.nodes[j]
                
                weight = 0.0
                
                # 1. 场势耦合 (Field Coupling) - 取代线性生克
                # 生 (Generation)
                if node_j.element in GENERATION and GENERATION[node_j.element] == node_i.element:
                     weight += self._calculate_field_coupling(node_j, node_i, 'generate', flow_config, distance=abs(node_i.pillar_idx - node_j.pillar_idx))
                
                # 克 (Control)
                elif node_j.element in CONTROL and CONTROL[node_j.element] == node_i.element:
                     # 检查通关逻辑 (Mediation)
                     mediation_factor = 1.0
                     # ... (保留通关检测简版，或移至耦合函数内) ...
                     # 这里简化：如果被锁定，则不克
                     if getattr(node_j, 'is_locked', False):
                         weight += 0
                     else:
                         weight += self._calculate_field_coupling(node_j, node_i, 'control', flow_config, distance=abs(node_i.pillar_idx - node_j.pillar_idx))
                         
                # 2. 比劫 (Peer)
                if node_j.element == node_i.element and node_j != node_i:
                    # 弱耦合
                    weight += 0.13 * math.exp(-0.1 * abs(node_i.pillar_idx - node_j.pillar_idx))

                # 3. 结构性连接 (Structure Types for GNN)
                # 天干五合 / 地支合冲 仅作为拓扑连接存在
                # 实际物理效应已移至 WavePhysicsEngine (QuantumEntanglement)
                # 这里只保留 sign (正负号) 用于 GAT 识别关系类型
                
                # 合
                is_combine = False
                if node_i.node_type == 'stem' and node_j.node_type == 'stem':
                     combo_weight = self._get_stem_combination_weight(node_i.char, node_j.char, interactions_config)
                     if combo_weight > 0: is_combine = True
                elif node_i.node_type == 'branch' and node_j.node_type == 'branch':
                     combo_weight = self._get_branch_combo_weight(node_i.char, node_j.char, combo_physics, branch_events)
                     if combo_weight > 0: is_combine = True
                
                if is_combine:
                    weight += 0.1 # 拓扑连接

                # 冲
                if node_i.node_type == node_j.node_type and node_i.node_type == 'branch':
                     if (BRANCH_CLASHES.get(node_i.char) == node_j.char or BRANCH_CLASHES.get(node_j.char) == node_i.char):
                         weight -= 0.1 # 拓扑负连接

                A[i][j] = weight
        
        # [V55.0] 添加大运的 Support Link（静态叠加）
        self._add_dayun_support_links(A)
        
        
        # [V12.0 The Purge] 移除 _add_liunian_trigger_links old logic
        # 流年作用已全部迁移至 QuantumEntanglementProcessor (Wave Physics)
        
        # [V10.0] 如果启用 GAT，使用动态注意力机制替代固定矩阵
        if self.engine.use_gat and self.engine.gat_builder is not None:
            # 构建关系类型矩阵
            relation_types = self._build_relation_types_matrix()
            
            # 获取节点能量向量
            node_energies = self.engine.H0.reshape(-1, 1) if self.engine.H0 is not None else np.ones((N, 1))
            
            # 使用 GAT 构建动态邻接矩阵
            A_dynamic = self.engine.gat_builder.build_dynamic_adjacency_matrix(
                nodes=self.engine.nodes,
                node_energies=node_energies,
                relation_types=relation_types,
                base_adjacency=A  # 使用固定矩阵作为先验知识
            )
            
            # 混合固定矩阵和动态矩阵（可配置混合比例）
            gat_mix_ratio = self.config.get('gat', {}).get('gat_mix_ratio', 0.5)  # 默认 50% 动态，50% 固定
            A = (1 - gat_mix_ratio) * A + gat_mix_ratio * A_dynamic
        
        self.engine.adjacency_matrix = A
        return A
    
    def _build_relation_types_matrix(self) -> np.ndarray:
        """
        [V10.0] 构建关系类型矩阵
        
        用于 GAT 注意力机制，标识节点间的关系类型。
        
        Returns:
            关系类型矩阵 [N x N]:
            - 1: 生 (Generation)
            - -1: 克 (Control)
            - 2: 合 (Combination)
            - -2: 冲 (Clash)
            - 0: 无关系
        """
        N = len(self.engine.nodes)
        relation_types = np.zeros((N, N))
        
        # 地支冲关系
        clashes = {'子': '午', '午': '子', '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
                   '辰': '戌', '戌': '辰', '丑': '未', '未': '丑', '巳': '亥', '亥': '巳'}
        
        # 天干五合
        stem_combinations = {
            '甲': '己', '己': '甲',
            '乙': '庚', '庚': '乙',
            '丙': '辛', '辛': '丙',
            '丁': '壬', '壬': '丁',
            '戊': '癸', '癸': '戊'
        }
        
        # 地支六合
        branch_combinations = {
            '子': '丑', '丑': '子',
            '寅': '亥', '亥': '寅',
            '卯': '戌', '戌': '卯',
            '辰': '酉', '酉': '辰',
            '午': '未', '未': '午',
            '申': '巳', '巳': '申'
        }
        
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                
                node_i = self.engine.nodes[i]
                node_j = self.engine.nodes[j]
                
                # 1. 检查生克关系
                if GENERATION.get(node_j.element) == node_i.element:
                    relation_types[i, j] = 1  # 生
                elif CONTROL.get(node_j.element) == node_i.element:
                    relation_types[i, j] = -1  # 克
                
                # 2. 检查天干五合
                if (node_i.node_type == 'stem' and node_j.node_type == 'stem' and
                    stem_combinations.get(node_i.char) == node_j.char):
                    relation_types[i, j] = 2  # 合
                
                # 3. 检查地支六合
                if (node_i.node_type == 'branch' and node_j.node_type == 'branch' and
                    branch_combinations.get(node_i.char) == node_j.char):
                    relation_types[i, j] = 2  # 合
                
                # 4. 检查冲关系
                if (node_i.node_type == 'branch' and node_j.node_type == 'branch' and
                    clashes.get(node_i.char) == node_j.char):
                    relation_types[i, j] = -2  # 冲
        
        return relation_types
    
    def _calculate_field_coupling(self, source_node, target_node, type: str, flow_config: Dict, distance: int = 0) -> float:
        """
        [V12.0] 场势耦合 (Field Potential Coupling)
        替代线性的生克权重。
        
        W = C_base * Sigmoid(E_src - E_thresh) * Exp(-lambda * distance)
        """
        # 1. 基础耦合系数
        base = 0.8 if type == 'generate' else -0.4
        
        # 2. 源强度激活 (Source Activation)
        # 只有能量强的源才能建立有效场
        e_src = float(source_node.initial_energy.mean if isinstance(source_node.initial_energy, ProbValue) else source_node.initial_energy)
        # Sigmoid: 能量 > 0.5 开始激活，> 3.0 满载
        # k=2.0 陡度
        activation = 1.0 / (1.0 + math.exp(-2.0 * (e_src - 1.5))) 
        
        # 3. 距离衰减 (Inverse Square or Exponential)
        # 邻柱 (d=1) -> 0.81
        # 隔柱 (d=2) -> 0.67
        decay_lambda = 0.2
        spatial_factor = math.exp(-decay_lambda * distance)
        
        # 透干豁免：如果源是天干且透出，衰减减弱
        if source_node.node_type == 'stem' and getattr(source_node, 'is_exposed', False):
            spatial_factor = max(spatial_factor, 0.9)
            
        return base * activation * spatial_factor

    def _get_generation_weight(self, *args, **kwargs):
        """Deprecated legacy wrapper"""
        return 0.0

    def _get_control_weight(self, *args, **kwargs):
        """Deprecated legacy wrapper"""
        return 0.0
    
    def _get_control_weight(self, source_element: str, target_element: str,
                            flow_config: Dict, source_char: str = None,
                            target_char: str = None) -> float:
        """
        计算克的权重（负数：source 克 target）
        
        [V52.0] 任务 A：通关导管逻辑
        - 如果存在通关神（中间元素），计算导管容量
        - 只有当通关神足够强时，才能转化掉克制力
        
        [V58.1] Seasonal Dominance (得令者昌) - Fix Bruce Lee
        - 冬季（亥/子/丑月）：削弱土克水，增强水生木
        """
        if source_element in CONTROL and CONTROL[source_element] == target_element:
            control_impact = flow_config.get('controlImpact', 0.7)
            base_control = -0.3 * control_impact
            
            # [V58.2] Seasonal Dominance Lock (季节性优势锁定) - Fix Bruce Lee
            # 检查当前季节（月令）
            is_winter = False
            if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 1:
                month_branch = self.engine.bazi[1][1] if len(self.engine.bazi[1]) > 1 else None
                # 冬季：亥、子、丑月
                if month_branch in ['亥', '子', '丑']:
                    is_winter = True
            
            # [V58.2] 如果是冬季，且是土克水，大幅削弱克制效率（冻土不能止水）
            if is_winter and source_element == 'earth' and target_element == 'water':
                # 冻土不克水：克制效率降低到 10%（几乎无效）
                base_control *= 0.1
            
            # [V52.0] 任务 A：检查通关机制
            enable_mediation = flow_config.get('enable_mediation', True)
            if enable_mediation:
                # 查找通关神（中间元素）
                # 例如：金克木，如果有水，则水是通关神（金生水，水生木）
                mediator_element = self._find_mediator_element(source_element, target_element)
                
                if mediator_element:
                    # 计算通关神的能量（导管容量）
                    mediator_energy = self._calculate_mediator_energy(mediator_element)
                    source_energy = self._get_node_energy_by_element(source_element)
                    
                    # V13.0: 使用 ProbValue.mean 进行比较（保留概率分布）
                    # 导管容量 = Min(源能量, 通关神能量) - 使用均值进行比较
                    source_energy_abs = abs(source_energy.mean)
                    mediator_energy_mean = mediator_energy.mean
                    conduit_capacity = min(source_energy_abs, mediator_energy_mean)
                    
                    # 如果通关神能量 >= 源能量的 80%，则完全转化
                    # 否则，按比例减少克制力
                    if mediator_energy_mean >= source_energy_abs * 0.8:
                        # 完全通关：克制力转化为生成力
                        generation_efficiency = flow_config.get('generationEfficiency', 1.2)
                        return 0.3 * generation_efficiency  # 转化为生（正数）
                    elif mediator_energy_mean >= source_energy_abs * 0.5:
                        # 部分通关：减少 50% 克制力
                        return base_control * 0.5
                    elif mediator_energy_mean >= source_energy_abs * 0.3:
                        # 弱通关：减少 30% 克制力
                        return base_control * 0.7
                    # 否则，通关神太弱，无法通关，保持原克制力
            
            return base_control
        return 0.0
    
    def _find_mediator_element(self, source_element: str, target_element: str) -> Optional[str]:
        """
        [V52.0] 查找通关神（中间元素）
        
        规则：
        - 如果 source 生 mediator 且 mediator 生 target，则 mediator 是通关神
        - 例如：金克木，如果有水（金生水，水生木），则水是通关神
        """
        # 检查所有可能的中间元素
        for mediator in ['wood', 'fire', 'earth', 'metal', 'water']:
            # 检查：source 生 mediator 且 mediator 生 target
            if (mediator in GENERATION and GENERATION[mediator] == target_element and
                source_element in GENERATION and GENERATION[source_element] == mediator):
                return mediator
        
        # 特殊规则：官杀护财（Officer Shield）
        # 如果 source 是劫财（比肩），target 是财，且存在官杀（克比肩），则官杀是通关神
        # 这里简化处理：如果存在官杀元素，且官杀克 source，则视为护财
        if source_element == target_element:  # 比肩劫财
            # 查找官杀（克 source 的元素）
            for element in CONTROL:
                if CONTROL[element] == source_element:
                    # 检查是否存在这个元素
                    if any(n.element == element for n in self.engine.nodes):
                        return element
        
        return None
    
    def _calculate_mediator_energy(self, mediator_element: str) -> ProbValue:
        """
        [V52.0] 计算通关神的能量（导管容量）
        
        返回所有该元素节点的能量总和（使用概率分布）
        """
        total_energy = ProbValue(0.0, std_dev_percent=0.1)
        for node in self.engine.nodes:
            if node.element == mediator_element:
                # 使用当前能量（如果已计算）或初始能量
                if hasattr(node, 'current_energy'):
                    # V13.0: 使用 ProbValue 比较（保留概率分布）
                    # [V13.9] 修复：确保 current_energy 是 ProbValue 类型
                    if isinstance(node.current_energy, ProbValue):
                        if node.current_energy.mean > 0:
                            energy = node.current_energy
                        else:
                            energy = node.initial_energy if isinstance(node.initial_energy, ProbValue) else ProbValue(float(node.initial_energy), std_dev_percent=0.1)
                    else:
                        # 如果不是 ProbValue，转换为 ProbValue
                        energy = ProbValue(float(node.current_energy), std_dev_percent=0.1)
                else:
                    energy = node.initial_energy if isinstance(node.initial_energy, ProbValue) else ProbValue(float(node.initial_energy), std_dev_percent=0.1)
                # 使用 ProbValue 累加（保留概率分布）
                total_energy = total_energy + energy
        return total_energy
    
    def _get_node_energy_by_element(self, element: str) -> ProbValue:
        """获取指定元素的总能量（使用概率分布）"""
        total_energy = ProbValue(0.0, std_dev_percent=0.1)
        for node in self.engine.nodes:
            if node.element == element:
                if hasattr(node, 'current_energy'):
                    # V13.0: 使用 ProbValue 比较（保留概率分布）
                    # [V13.9] 修复：确保 current_energy 是 ProbValue 类型
                    if isinstance(node.current_energy, ProbValue):
                        if node.current_energy.mean > 0:
                            energy = node.current_energy
                        else:
                            energy = node.initial_energy if isinstance(node.initial_energy, ProbValue) else ProbValue(float(node.initial_energy), std_dev_percent=0.1)
                    else:
                        # 如果不是 ProbValue，转换为 ProbValue
                        energy = ProbValue(float(node.current_energy), std_dev_percent=0.1)
                else:
                    energy = node.initial_energy if isinstance(node.initial_energy, ProbValue) else ProbValue(float(node.initial_energy), std_dev_percent=0.1)
                # 使用 ProbValue 累加（保留概率分布）
                total_energy = total_energy + energy
        return total_energy
    
    def _get_stem_combination_weight(self, stem1: str, stem2: str,
                                     interactions_config: Dict) -> float:
        """计算天干五合的权重"""
        stem_combo_config = interactions_config.get('stemFiveCombination', {})
        threshold = stem_combo_config.get('threshold', 0.8)
        bonus = stem_combo_config.get('bonus', 2.0)
        
        # 检查是否五合
        if (stem1, stem2) in STEM_COMBINATIONS or (stem2, stem1) in STEM_COMBINATIONS:
            # 五合成功化气（简化：假设成功）
            return 1.5 * bonus  # 强正连接
        return 0.0
    
    def _get_branch_combo_weight(self, branch1: str, branch2: str,
                                 combo_physics: Dict, branch_events: Dict) -> float:
        """
        [V13.5] 计算地支合局的权重（三会、三合、半合、拱合、六合）
        
        物理模型：
        - 三会 (Three Meetings): 方局，力量最强（纯暴力）
        - 三合 (Three Harmony): 120°相位，共振质变，能量翻倍
        - 半合 (Half Harmony): 不完全共振，能量中等提升
        - 拱合 (Arch Harmony): 缺中神，虚拱，能量微升
        - 六合 (Six Harmony): 磁力吸附，物理羁绊，能量提升但活性降低
        
        [V13.8] 矩阵解耦：这里只返回基础连接权重（0.5），不包含 Bonus
        Bonus 应该在传播前作为一次性修正应用到初始能量
        """
        # [V13.9] 三会局定义（方局，力量最强）
        three_meeting_groups = [
            {'亥', '子', '丑'},  # 三会水（北方）
            {'寅', '卯', '辰'},  # 三会木（东方）
            {'巳', '午', '未'},  # 三会火（南方）
            {'申', '酉', '戌'},  # 三会金（西方）
        ]
        
        # [V13.9] 三会局检测（优先级最高）
        for group in three_meeting_groups:
            if branch1 in group and branch2 in group:
                return 0.5  # 基础连接权重，表示存在三会关系，但增益在 _apply_quantum_entanglement_once 中处理
        
        # [V13.5] 六合检测（磁力吸附，物理羁绊）
        if BRANCH_SIX_COMBINES.get(branch1) == branch2:
            return 0.5  # 基础连接权重
        
        # [V13.5] 三合局定义（120°相位，共振质变）
        trine_groups = [
            {'申', '子', '辰'},  # 三合水
            {'亥', '卯', '未'},  # 三合木
            {'寅', '午', '戌'},  # 三合火
            {'巳', '酉', '丑'},  # 三合金
        ]
        
        # [V13.5] 半合定义（生旺半合、墓旺半合）
        # 生旺半合：生位+旺位（如申-子，子-辰）
        # 墓旺半合：墓位+旺位（如子-辰，辰-申）
        half_harmony_pairs = [
            # 水局半合
            ('申', '子'), ('子', '申'),  # 生旺半合
            ('子', '辰'), ('辰', '子'),  # 墓旺半合
            # 木局半合
            ('亥', '卯'), ('卯', '亥'),  # 生旺半合
            ('卯', '未'), ('未', '卯'),  # 墓旺半合
            # 火局半合
            ('寅', '午'), ('午', '寅'),  # 生旺半合
            ('午', '戌'), ('戌', '午'),  # 墓旺半合
            # 金局半合
            ('巳', '酉'), ('酉', '巳'),  # 生旺半合
            ('酉', '丑'), ('丑', '酉'),  # 墓旺半合
        ]
        
        # [V13.5] 拱合定义（生墓半合，缺中神，虚拱）
        # 拱合：生位+墓位，缺旺位（如申-辰，缺子）
        arch_harmony_pairs = [
            # 水局拱合
            ('申', '辰'), ('辰', '申'),  # 缺子
            # 木局拱合
            ('亥', '未'), ('未', '亥'),  # 缺卯
            # 火局拱合
            ('寅', '戌'), ('戌', '寅'),  # 缺午
            # 金局拱合
            ('巳', '丑'), ('丑', '巳'),  # 缺酉
        ]
        
        # [V13.5] 三合检测（完整三合，需要第三个节点，这里只检测两两关系的基础权重）
        for group in trine_groups:
            if branch1 in group and branch2 in group:
                return 0.5  # 基础连接权重，表示存在三合关系，但增益在 _apply_quantum_entanglement_once 中处理
        
        # [V13.5] 半合检测
        if (branch1, branch2) in half_harmony_pairs:
            return 0.5  # 基础连接权重，表示存在半合关系，但增益在 _apply_quantum_entanglement_once 中处理
        
        # [V13.5] 拱合检测（缺中神，虚拱）
        if (branch1, branch2) in arch_harmony_pairs:
            return 0.5  # 基础连接权重，表示存在拱合关系，但增益在 _apply_quantum_entanglement_once 中处理
        
        return 0.0
    
    
    def _add_liunian_trigger_links(self, A: np.ndarray):
        """Deprecated legacy function. Liunian logic is now in QuantumEntanglementProcessor."""
        pass

