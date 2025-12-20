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
                
                # 1. 五行生克关系（传入字符以支持特殊效应检测）
                gen_weight = self._get_generation_weight(
                    node_j.element, node_i.element, flow_config, 
                    source_char=node_j.char, target_char=node_i.char
                )
                
                control_weight = self._get_control_weight(
                    node_j.element, node_i.element, flow_config,
                    source_char=node_j.char, target_char=node_i.char
                )

                # [V10.0 Group H] 解冲逻辑 (Resolution Protocol)
                # 如果 Source 节点处于贪合状态 (Locked)，则阻断其克制路径 (Control)
                # 物理含义：贪合忘克
                if getattr(node_j, 'is_locked', False) and control_weight < 0:
                    control_weight = 0.0

                weight += gen_weight
                weight += control_weight
                
                # [V14.0] 比劫传导（Peer Flow）：同五行之间的能量传输
                # 比劫是朋友关系，应该无损或低损传输，不像母子关系那样耗气
                # 但需要控制效率，避免正反馈循环导致能量爆炸
                if node_j.element == node_i.element and node_j != node_i:
                    peer_flow_efficiency = 0.13  # [V14.3] 朋友互助效率（从0.12提高到0.13，适度增强）
                    weight += peer_flow_efficiency
                
                # 1.5 特殊效应：润局（水润土生金）
                # 如果土生金，且全局存在水，增强权重
                if (node_j.element == 'earth' and node_i.element == 'metal' and
                    (node_j.char in ['未', '戌'] or node_j.char in ['丑', '辰'])):
                    # 检查是否有水节点存在
                    has_water = any(n.element == 'water' for n in self.engine.nodes 
                                   if n.char in ['亥', '子'])
                    if has_water:
                        moisture_boost = flow_config.get('earthMetalMoistureBoost', 1.5)
                        # 增强土生金的权重
                        if gen_weight > 0:
                            weight = weight - gen_weight + (gen_weight * moisture_boost)
                        else:
                            # 如果原本没有生权重（不应该发生），添加一个
                            generation_efficiency = flow_config.get('generationEfficiency', 1.2)
                            weight += 0.6 * generation_efficiency * (moisture_boost - 1.0)
                
                # 2. 天干五合
                # [V13.8] 矩阵解耦：合化增益不应进入邻接矩阵！
                if node_i.node_type == 'stem' and node_j.node_type == 'stem':
                    combo_weight = self._get_stem_combination_weight(
                        node_i.char, node_j.char, interactions_config
                    )
                    # [V13.8] 只保留小的连接权重（0.1），不包含 Bonus
                    if combo_weight > 0:
                        weight += 0.1  # 天干合连接权重（小值，表示连接存在）
                
                # 3. 地支合局（三合、三会、六合）
                # [V13.8] 矩阵解耦：合化增益不应进入邻接矩阵！
                # 邻接矩阵只能包含传输效率（~0.7），不能包含 Bonus（2.0）
                # Bonus 应该在传播前作为一次性修正应用到初始能量
                # 这里只保留一个小的连接权重（表示合局的存在），不包含 Bonus
                if node_i.node_type == 'branch' and node_j.node_type == 'branch':
                    combo_weight = self._get_branch_combo_weight(
                        node_i.char, node_j.char, combo_physics, branch_events
                    )
                    # [V13.8] 只保留小的连接权重（0.1），不包含 Bonus
                    if combo_weight > 0:
                        weight += 0.1  # 合局连接权重（小值，表示连接存在）
                
                # 4. 冲（Clash）
                weight += self._get_clash_weight(
                    node_i.char, node_j.char, node_i.node_type, node_j.node_type,
                    branch_events
                )
                
                # 5. 距离衰减（空间衰减）
                # [V59.0] 透干印星豁免距离衰减：如果节点是透干印星（天干节点且是印星），不应用距离衰减
                # 因为透干印星的通关能力不受距离限制
                is_exposed_resource = False
                if node_j.node_type == 'stem':
                    # 检查 node_j 是否是透干印星
                    # 从节点中动态获取日主元素（因为可能化气）
                    dm_element = None
                    for node in self.engine.nodes:
                        if node.pillar_idx == 2 and node.node_type == 'stem':
                            dm_element = node.element
                            break
                    if dm_element:
                        resource_element = None
                        for elem, target in GENERATION.items():
                            if target == dm_element:
                                resource_element = elem
                                break
                        if resource_element and node_j.element == resource_element:
                            is_exposed_resource = True
                
                distance = abs(node_i.pillar_idx - node_j.pillar_idx)
                if distance > 0 and not is_exposed_resource:  # 透干印星豁免距离衰减
                    spatial_config = flow_config.get('spatialDecay', {'gap1': 0.6, 'gap2': 0.3})
                    if distance == 1:
                        weight *= spatial_config.get('gap1', 0.6)
                    elif distance >= 2:
                        weight *= spatial_config.get('gap2', 0.3)
                
                A[i][j] = weight
        
        # [V55.0] 添加大运的 Support Link（静态叠加）
        self._add_dayun_support_links(A)
        
        # [V55.0] 添加流年的引动逻辑（动态触发）
        self._add_liunian_trigger_links(A)
        
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
    
    def _get_generation_weight(self, source_element: str, target_element: str,
                               flow_config: Dict, source_char: str = None,
                               target_char: str = None) -> float:
        """
        计算生的权重（正数：source 生 target）
        
        Args:
            source_element: 源元素
            target_element: 目标元素
            flow_config: 流程配置
            source_char: 源字符（用于特殊检测，如润局）
            target_char: 目标字符（用于特殊检测）
        
        [V58.1] Seasonal Dominance (得令者昌) - Fix Bruce Lee
        - 冬季（亥/子/丑月）：增强水生木的效率
        """
        if source_element in GENERATION and GENERATION[source_element] == target_element:
            generation_efficiency = flow_config.get('generationEfficiency', 1.2)
            base_weight = 0.6 * generation_efficiency
            
            # [V58.2] Seasonal Dominance Lock (季节性优势锁定) - Fix Bruce Lee
            # 检查当前季节（月令）
            is_winter = False
            month_branch = None
            if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 1:
                month_branch = self.engine.bazi[1][1] if len(self.engine.bazi[1]) > 1 else None
                # 冬季：亥、子、丑月
                if month_branch in ['亥', '子', '丑']:
                    is_winter = True
            
            # [V58.2] 如果是冬季，且是水生木，增强生成效率（即使水很冷，只要有木，水就会流向木）
            if is_winter and source_element == 'water' and target_element == 'wood':
                # 水生木效率提升 50%
                base_weight *= 1.5
            
            # [V58.2] 当令五行能量加成：如果源元素是当令五行，增强生成效率
            if month_branch:
                month_element = self.engine.BRANCH_ELEMENTS.get(month_branch, 'earth')
                if source_element == month_element:
                    # 当令五行生其他元素：效率提升 30%
                    base_weight *= 1.3
            
            # [V58.3] 湿土生金润局优化：如果土生金，根据土的干湿程度调整权重
            if source_element == 'earth' and target_element == 'metal':
                # 检查是否是湿土（丑、辰）
                is_moist_earth = False
                if source_char:
                    # 湿土：丑、辰
                    if source_char in ['丑', '辰']:
                        is_moist_earth = True
                
                # [V58.3] 湿土生金效率更高
                if is_moist_earth:
                    base_weight *= 1.3  # 湿土生金效率提升 30%
                else:
                    # 燥土（未、戌）：检查是否有润局（水能量 > 3.0）
                    # 计算全局水能量（使用概率分布）
                    water_energy = ProbValue(0.0, std_dev_percent=0.1)
                    if hasattr(self.engine, 'nodes'):
                        for node in self.engine.nodes:
                            if node.element == 'water':
                                # V13.0: 使用 ProbValue（概率分布）
                                energy = node.initial_energy if hasattr(node, 'initial_energy') else node.current_energy
                                water_energy = water_energy + energy
                    
                    # [V59.0] Absolute Climate Boost (绝对润局增幅) - Fix REAL_S_006
                    # 如果水能量 > 3.0（润局），将土生金的增幅提高到 1.5x
                    # V13.0: 使用 ProbValue 的均值进行比较
                    if water_energy.mean > 3.0:
                        base_weight *= 1.5  # 润局时，燥土生金效率提升 50%（从 1.3 提升到 1.5）
                    else:
                        # 普通燥土生金：使用默认权重
                        moisture_boost = flow_config.get('earthMetalMoistureBoost', 1.0)
                        base_weight *= moisture_boost
            
            return base_weight
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
    
    def _get_clash_weight(self, char1: str, char2: str, type1: str, type2: str,
                          branch_events: Dict) -> float:
        """计算冲的权重（负数：破坏性）"""
        if type1 == 'branch' and type2 == 'branch':
            if (char1, char2) in BRANCH_CLASHES or (char2, char1) in BRANCH_CLASHES:
                clash_damping = branch_events.get('clashDamping', 0.3)
                clash_score = branch_events.get('clashScore', -5.0)
                
                # [V58.1] Commander Immunity (提纲免死金牌) - Fix Wu Zetian
                # 检查被冲的节点是否是月令地支（Month Branch）
                is_month_branch_clashed = False
                if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 1:
                    month_branch = self.engine.bazi[1][1] if len(self.engine.bazi[1]) > 1 else None
                    if month_branch and (char1 == month_branch or char2 == month_branch):
                        is_month_branch_clashed = True
                        # 月令被冲：至少保留 80% 能量（普通地支可能只剩 40%）
                        # 调整 clash_damping：从 0.3 提升到 0.8（保留更多能量）
                        clash_damping = max(clash_damping, 0.8)  # 至少保留 80% 能量
                
                # [V57.2] 阳刃金刚盾：检查所有参与冲的地支节点，如果其中一个是日主的阳刃（帝旺位），完全豁免冲的影响
                is_yangren_shielded = False
                if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 2:
                    day_pillar = self.engine.bazi[2]
                    if len(day_pillar) >= 2:
                        day_master = day_pillar[0]
                        # 检查 char1 和 char2 是否都是日主的阳刃（帝旺位）
                        life_stage1 = TWELVE_LIFE_STAGES.get((day_master, char1))
                        life_stage2 = TWELVE_LIFE_STAGES.get((day_master, char2))
                        # 如果其中一个是阳刃（帝旺位），则完全豁免冲的影响
                        if life_stage1 == '帝旺' or life_stage2 == '帝旺':
                            is_yangren_shielded = True
                
                if is_yangren_shielded:
                    # [V57.2] 阳刃金刚盾：完全豁免冲的影响（damping = 1.0，即无损）
                    clash_damping = 1.0  # 完全豁免，不损失能量
                    # 或者直接返回 0（不产生负权重）
                    return 0.0
                
                # 冲的破坏性（负数，归一化为权重）
                return clash_score / 10.0 * clash_damping
        return 0.0
    
    def _add_dayun_support_links(self, A: np.ndarray):
        """
        [V55.0] 添加大运的 Support Link（静态叠加）
        
        大运节点与原局日主及所有同五行/相生节点建立"Support Link"（静态能量注入）。
        物理含义：改变背景场域（如进入火运，全局火能量底噪提升）。
        """
        # 找到大运节点
        dayun_nodes = []
        for i, node in enumerate(self.engine.nodes):
            if hasattr(node, 'dayun_weight'):
                dayun_nodes.append(i)
        
        if not dayun_nodes:
            return
        
        # 找到日主节点
        dm_indices = []
        for i, node in enumerate(self.engine.nodes):
            if node.pillar_idx == 2 and node.node_type == 'stem':
                dm_indices.append(i)
        
        # 大运节点对所有原局节点建立 Support Link
        for dayun_idx in dayun_nodes:
            dayun_node = self.engine.nodes[dayun_idx]
            dayun_element = dayun_node.element
            
            for i, natal_node in enumerate(self.engine.nodes):
                # 跳过非原局节点（大运、流年）
                if natal_node.pillar_idx >= 4:
                    continue
                
                natal_element = natal_node.element
                
                # 1. 同五行：直接支持（共振）
                if natal_element == dayun_element:
                    A[i][dayun_idx] += 0.3  # Support Link 权重
                
                # 2. 相生关系：大运生原局（注入能量）
                elif GENERATION.get(dayun_element) == natal_element:
                    A[i][dayun_idx] += 0.4  # 生关系权重更高
                
                # 3. 日主特殊加成：大运对日主的支持
                if i in dm_indices:
                    # 如果大运生日主或与日主同五行，额外加成
                    if GENERATION.get(dayun_element) == natal_element or dayun_element == natal_element:
                        A[i][dayun_idx] += 0.2
    
    def _add_liunian_trigger_links(self, A: np.ndarray):
        """
        [V55.0] 添加流年的引动逻辑（动态触发）
        
        流年节点作为"高能粒子"射入图网络，优先级最高。
        流年与原局/大运的冲（Clash）和合（Combine）判定优先于原局内部关系。
        被流年冲合的节点，其能量活跃度瞬间翻倍。
        """
        from core.engine_graph.constants import LIFE_STAGE_COEFFICIENTS
        
        # 找到流年节点
        liunian_nodes = []
        for i, node in enumerate(self.engine.nodes):
            if hasattr(node, 'is_liunian') and node.is_liunian:
                liunian_nodes.append(i)
        
        if not liunian_nodes:
            return
        
        # 找到流年地支节点（用于冲合判定）
        liunian_branch_idx = None
        liunian_stem_idx = None
        for idx in liunian_nodes:
            node = self.engine.nodes[idx]
            if node.node_type == 'branch':
                liunian_branch_idx = idx
            elif node.node_type == 'stem':
                liunian_stem_idx = idx
        
        # 1. 流年地支冲原局/大运地支（引动）
        if liunian_branch_idx is not None:
            liunian_branch = self.engine.nodes[liunian_branch_idx].char
            
            for i, node in enumerate(self.engine.nodes):
                if i == liunian_branch_idx:
                    continue
                
                # 只处理地支节点
                if node.node_type != 'branch':
                    continue
                
                natal_branch = node.char
                
                # 检查是否相冲（BRANCH_CLASHES 是字典，不是 tuple 集合）
                is_clash = (BRANCH_CLASHES.get(liunian_branch) == natal_branch or 
                           BRANCH_CLASHES.get(natal_branch) == liunian_branch)
                
                if is_clash:
                    # [V55.0] 墓库冲开检测（Storehouse Opening）
                    is_storehouse = natal_branch in ['辰', '戌', '丑', '未']
                    is_storehouse_opened = False
                    
                    if is_storehouse:
                        # 检查是否满足冲开条件
                        # 条件：被冲节点是墓库，且流年是对应的冲支
                        storehouse_clash_map = {'辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
                        if storehouse_clash_map.get(natal_branch) == liunian_branch:
                            # 检查库中能量（简化：使用节点当前能量）
                            storage_energy = node.current_energy
                            vault_threshold = self.config.get('vault', {}).get('threshold', 15.0)
                            
                            # V13.0: 处理 ProbValue（概率值）
                            storage_energy_val = float(storage_energy) if isinstance(storage_energy, ProbValue) else storage_energy
                            if storage_energy_val >= vault_threshold:
                                # 库被冲开：能量释放（能量翻倍）
                                is_storehouse_opened = True
                                node.is_activated = True
                                node.activation_factor = 1.5  # 库开能量释放
                                node.storehouse_opened = True
                                node.trigger_events = getattr(node, 'trigger_events', [])
                                node.trigger_events.append(f"{liunian_branch}冲开{natal_branch}库")
                                
                                # 流年冲开库：建立强连接（能量释放）
                                A[i][liunian_branch_idx] += 1.0  # 冲开的正权重（能量释放）
                    
                    if not is_storehouse_opened:
                        # [V55.0] 检测冲提纲（月支被冲）- 极其严重
                        # 方法1：检查节点是否为月支（pillar_idx == 1 且是地支）
                        is_month_pillar_by_idx = (node.pillar_idx == 1 and node.node_type == 'branch')
                        
                        # 方法2：检查 pillar_name
                        is_month_pillar_by_name = (hasattr(node, 'pillar_name') and node.pillar_name == 'month')
                        
                        # 方法3：检查被冲的地支是否是月支（最可靠的方法）
                        month_branch_in_bazi = None
                        if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 1:
                            month_branch_in_bazi = self.engine.bazi[1][1] if len(self.engine.bazi[1]) > 1 else None
                        is_month_branch = (natal_branch == month_branch_in_bazi) if month_branch_in_bazi else False
                        
                        if is_month_pillar_by_idx or is_month_pillar_by_name or is_month_branch:
                            # 冲提纲：根基动摇，严重扣分
                            node.is_activated = True
                            node.activation_factor = 0.15  # 能量大幅下降（根基动摇，更严重）
                            node.instability_penalty = 0.7  # 高不稳定性
                            node.trigger_events = getattr(node, 'trigger_events', [])
                            node.trigger_events.append(f"{liunian_branch}冲提纲({natal_branch})")
                            
                            # 流年冲提纲：极其严重的负权重
                            A[i][liunian_branch_idx] -= 4.0  # 冲提纲的负权重（极其严重，提升）
                            
                            # [V55.0] 冲提纲时，日主能量也受影响
                            for dm_node in self.engine.nodes:
                                if dm_node.pillar_idx == 2 and dm_node.node_type == 'stem':
                                    dm_node.trigger_events = getattr(dm_node, 'trigger_events', [])
                                    dm_node.trigger_events.append(f"冲提纲影响日主")
                                    # 日主能量也受影响
                                    dm_node.activation_factor = getattr(dm_node, 'activation_factor', 1.0) * 0.7
                                    break
                        else:
                            # 普通冲：能量受损，但不稳定性增加
                            node.is_activated = True
                            node.activation_factor = 0.5  # 能量减半（受损）
                            node.instability_penalty = 0.3  # 不稳定性惩罚
                            node.trigger_events = getattr(node, 'trigger_events', [])
                            node.trigger_events.append(f"{liunian_branch}冲{natal_branch}")
                            
                            # 流年冲原局：流年对原局的影响权重极高（负权重）
                            A[i][liunian_branch_idx] -= 1.5  # 冲的负权重（强烈冲击）
        
        # 2. 流年天干合原局天干（羁绊/化气）
        if liunian_stem_idx is not None:
            liunian_stem = self.engine.nodes[liunian_stem_idx].char
            liunian_stem_element = self.engine.nodes[liunian_stem_idx].element
            
            for i, node in enumerate(self.engine.nodes):
                if i == liunian_stem_idx:
                    continue
                
                # 只处理天干节点
                if node.node_type != 'stem':
                    continue
                
                natal_stem = node.char
                natal_element = node.element
                
                # 检查是否相合
                combo_key = tuple(sorted([liunian_stem, natal_stem]))
                if combo_key in STEM_COMBINATIONS or (liunian_stem, natal_stem) in STEM_COMBINATIONS:
                    # 合化：视为羁绊或化气
                    node.is_activated = True
                    node.activation_factor = 1.5  # 合的能量增强
                    node.trigger_events = getattr(node, 'trigger_events', [])
                    node.trigger_events.append(f"{liunian_stem}合{natal_stem}")
                    
                    # 流年合原局：建立强连接
                    A[i][liunian_stem_idx] += 1.2  # 合的权重
                    
                    # [V55.0] 检测官印相生：如果流年是官杀，合化后可能转化为印星
                    # 找到日主
                    for dm_node in self.engine.nodes:
                        if dm_node.pillar_idx == 2 and dm_node.node_type == 'stem':
                            dm_element = dm_node.element
                            
                            # 检查是否官印相生（流年官杀 -> 合化 -> 印星 -> 日主）
                            officer_element = None
                            for attacker, defender in CONTROL.items():
                                if defender == dm_element:
                                    officer_element = attacker
                                    break
                            resource_element = None
                            for elem, target in GENERATION.items():
                                if target == dm_element:
                                    resource_element = elem
                                    break
                            
                            # 如果流年是官杀，且原局有印星，可能官印相生
                            if liunian_stem_element == officer_element and resource_element:
                                # 检查是否有印星节点
                                for res_node in self.engine.nodes:
                                    if res_node.element == resource_element:
                                        # 官印相生：加分
                                        node.trigger_events.append(f"官印相生")
                                        break
                            break
        
        # 3. [V55.0] 检测流年地支为日主强根（帝旺、临官等）
        if liunian_branch_idx is not None:
            liunian_branch = self.engine.nodes[liunian_branch_idx].char
            
            # 找到日主节点（需要从 analyze 方法传入 day_master）
            # 这里我们需要从节点中找到日主
            day_master_char = None
            for node in self.engine.nodes:
                if node.pillar_idx == 2 and node.node_type == 'stem':
                    day_master_char = node.char
                    break
            
            if day_master_char:
                # 检查流年地支是否为日主的强根
                life_stage = TWELVE_LIFE_STAGES.get((day_master_char, liunian_branch))
                
                if life_stage in ['帝旺', '临官', '长生']:
                    # 找到日主节点索引
                    for i, node in enumerate(self.engine.nodes):
                        if node.pillar_idx == 2 and node.node_type == 'stem' and node.char == day_master_char:
                            # 流年是日主的强根：大幅提升日主能量
                            strong_root_bonus = LIFE_STAGE_COEFFICIENTS.get(life_stage, 1.5)
                            node.is_activated = True
                            node.activation_factor = strong_root_bonus  # 强根加成
                            node.trigger_events = getattr(node, 'trigger_events', [])
                            node.trigger_events.append(f"流年{liunian_branch}为日主{life_stage}(强根)")
                            
                            # 流年强根对日主的支持权重极高
                            A[i][liunian_branch_idx] += 2.5  # 强根支持的正权重（提升）
                            break
        
        # 4. 流年对所有节点的基础影响（流年是君，权力最大）
        for liunian_idx in liunian_nodes:
            liunian_node = self.engine.nodes[liunian_idx]
            liunian_element = liunian_node.element
            
            for i, node in enumerate(self.engine.nodes):
                if i == liunian_idx:
                    continue
                
                # 流年对所有节点都有基础影响（但权重较小）
                # 这个影响会在传播中体现
                if abs(A[i][liunian_idx]) < 0.1:  # 如果没有其他关系
                    # 根据五行关系添加基础权重
                    if GENERATION.get(liunian_element) == node.element:
                        A[i][liunian_idx] += 0.2  # 流年生原局
                    elif CONTROL.get(liunian_element) == node.element:
                        A[i][liunian_idx] -= 0.2  # 流年克原局

