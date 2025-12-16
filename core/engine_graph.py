"""
Antigravity Graph Network Engine (Physics-Initialized GNN)
==========================================================

基于图神经网络的八字算法引擎，严格遵循"物理初始化图网络"模型。

架构说明：
- Phase 1: Node Initialization (节点初始化) - 应用所有基础物理规则
- Phase 2: Adjacency Matrix Construction (邻接矩阵构建) - 将生克制化转化为矩阵权重
- Phase 3: Propagation (传播迭代) - 模拟动态做功与传导

确保所有核心理论（月令、通根、壳核、生克制化）都被完整保留并强化。

版本: V10.0-Graph
作者: Antigravity Team
日期: 2025-01-16
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from copy import deepcopy

from core.processors.physics import PhysicsProcessor, GENERATION, CONTROL
from core.processors.base import BaseProcessor
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


class GraphNode:
    """图网络节点，表示一个八字粒子"""
    
    def __init__(self, node_id: int, char: str, node_type: str, element: str, 
                 pillar_idx: int, pillar_name: str):
        """
        初始化节点。
        
        Args:
            node_id: 节点唯一ID（0-11）
            char: 天干或地支字符
            node_type: 'stem' 或 'branch'
            element: 五行元素 ('wood', 'fire', 'earth', 'metal', 'water')
            pillar_idx: 所属柱的索引 (0=年, 1=月, 2=日, 3=时)
            pillar_name: 所属柱的名称 ('year', 'month', 'day', 'hour')
        """
        self.node_id = node_id
        self.char = char
        self.node_type = node_type
        self.element = element
        self.pillar_idx = pillar_idx
        self.pillar_name = pillar_name
        
        # 初始能量（在 Phase 1 中计算）
        self.initial_energy = 0.0
        
        # 当前能量（在 Phase 3 传播中更新）
        self.current_energy = 0.0
        
        # 节点属性（用于物理规则）
        self.has_root = False  # 是否有通根
        self.is_same_pillar = False  # 是否自坐强根
        self.is_exposed = False  # 是否透干
        self.hidden_stems_energy = {}  # 藏干能量分布（壳核模型）


class GraphNetworkEngine:
    """
    图网络引擎 - 物理初始化的图神经网络模型
    
    严格遵循三阶段架构：
    1. Node Initialization: 计算初始能量向量 H^(0)
    2. Adjacency Matrix: 构建关系矩阵 A
    3. Propagation: 迭代传播 H^(t+1) = A * H^(t)
    """
    
    VERSION = "10.0-Graph"
    
    def __init__(self, config: Dict = None):
        """
        初始化图网络引擎。
        
        Args:
            config: 参数配置（使用 DEFAULT_FULL_ALGO_PARAMS 结构）
        """
        self.config = config or DEFAULT_FULL_ALGO_PARAMS
        
        # 节点列表（12个节点：4天干 + 4地支 + 2大运 + 2流年）
        self.nodes: List[GraphNode] = []
        
        # 初始能量向量 H^(0) [12 x 1]
        self.H0: np.ndarray = None
        
        # 邻接矩阵 A [12 x 12]
        self.adjacency_matrix: np.ndarray = None
        
        # 物理处理器（用于计算初始能量）
        self.physics_processor = PhysicsProcessor()
        
        # 元素映射
        self.STEM_ELEMENTS = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water'
        }
        
        self.BRANCH_ELEMENTS = {
            '子': 'water', '丑': 'earth', '寅': 'wood', '卯': 'wood',
            '辰': 'earth', '巳': 'fire', '午': 'fire', '未': 'earth',
            '申': 'metal', '酉': 'metal', '戌': 'earth', '亥': 'water'
        }
    
    # ===========================================
    # Phase 1: Node Initialization (节点初始化)
    # ===========================================
    
    def initialize_nodes(self, bazi: List[str], day_master: str, 
                        luck_pillar: str = None, year_pillar: str = None,
                        geo_modifiers: Dict[str, float] = None) -> np.ndarray:
        """
        Phase 1: 初始化节点并计算初始能量向量 H^(0)。
        
        在此阶段应用所有基础物理规则：
        1. Seasonality (月令权重): pg_month
        2. Rooting (通根): root_w
        3. Geography (空间修正): K_geo
        4. Shell-Core (壳核): Hidden Stems ratios
        
        Args:
            bazi: 八字列表 [年柱, 月柱, 日柱, 时柱]
            day_master: 日主天干
            luck_pillar: 大运柱（可选）
            year_pillar: 流年柱（可选）
            geo_modifiers: 地理修正系数（可选）
        
        Returns:
            初始能量向量 H^(0) [12 x 1]
        """
        self.nodes = []
        node_id = 0
        
        # 获取参数配置
        physics_config = self.config.get('physics', {})
        structure_config = self.config.get('structure', {})
        pillar_weights = physics_config.get('pillarWeights', {
            'year': 0.8, 'month': 1.2, 'day': 1.0, 'hour': 0.9
        })
        
        # 1. 创建原局节点（8个：4天干 + 4地支）
        pillar_names = ['year', 'month', 'day', 'hour']
        
        # 存储日主节点引用和月支，用于化气判断
        day_master_node = None
        month_branch_char = None
        
        for idx, pillar in enumerate(bazi):
            if len(pillar) < 2:
                continue
            
            stem_char = pillar[0]
            branch_char = pillar[1]
            p_name = pillar_names[idx]
            
            # 保存月支，用于化气判断
            if idx == 1:  # 月柱
                month_branch_char = branch_char
            
            # 天干节点
            stem_element = self.STEM_ELEMENTS.get(stem_char, 'earth')
            stem_node = GraphNode(
                node_id=node_id, char=stem_char, node_type='stem',
                element=stem_element, pillar_idx=idx, pillar_name=p_name
            )
            node_id += 1
            
            # 保存日主节点引用
            if idx == 2 and stem_char == day_master:  # 日柱且是日主
                day_master_node = stem_node
                self.day_master_element = stem_element  # 初始化日主元素
            
            # 地支节点
            branch_element = self.BRANCH_ELEMENTS.get(branch_char, 'earth')
            branch_node = GraphNode(
                node_id=node_id, char=branch_char, node_type='branch',
                element=branch_element, pillar_idx=idx, pillar_name=p_name
            )
            node_id += 1
            
            self.nodes.append(stem_node)
            self.nodes.append(branch_node)
            
            # 检查通根（天干在地支藏干中出现）
            if self._has_root(stem_char, branch_char):
                stem_node.has_root = True
                stem_node.is_same_pillar = True  # 自坐强根
            
            # 计算地支的藏干能量（壳核模型）
            branch_node.hidden_stems_energy = self._calculate_hidden_stems_energy(
                branch_char, physics_config
            )
        
        # [V39.0] 在计算能量之前，先应用化气逻辑
        if day_master_node and month_branch_char:
            self._apply_stem_transformation(bazi, day_master, day_master_node, month_branch_char)
        
        # 2. 添加大运和流年节点（如果提供）
        if luck_pillar and len(luck_pillar) >= 2:
            luck_stem = luck_pillar[0]
            luck_branch = luck_pillar[1]
            
            luck_stem_node = GraphNode(
                node_id=node_id, char=luck_stem, node_type='stem',
                element=self.STEM_ELEMENTS.get(luck_stem, 'earth'),
                pillar_idx=4, pillar_name='luck_stem'
            )
            node_id += 1
            
            luck_branch_node = GraphNode(
                node_id=node_id, char=luck_branch, node_type='branch',
                element=self.BRANCH_ELEMENTS.get(luck_branch, 'earth'),
                pillar_idx=4, pillar_name='luck_branch'
            )
            node_id += 1
            
            self.nodes.append(luck_stem_node)
            self.nodes.append(luck_branch_node)
        
        if year_pillar and len(year_pillar) >= 2:
            year_stem = year_pillar[0]
            year_branch = year_pillar[1]
            
            year_stem_node = GraphNode(
                node_id=node_id, char=year_stem, node_type='stem',
                element=self.STEM_ELEMENTS.get(year_stem, 'earth'),
                pillar_idx=5, pillar_name='year_stem'
            )
            node_id += 1
            
            year_branch_node = GraphNode(
                node_id=node_id, char=year_branch, node_type='branch',
                element=self.BRANCH_ELEMENTS.get(year_branch, 'earth'),
                pillar_idx=5, pillar_name='year_branch'
            )
            node_id += 1
            
            self.nodes.append(year_stem_node)
            self.nodes.append(year_branch_node)
        
        # 3. 计算初始能量（应用所有物理规则）
        H0 = np.zeros(len(self.nodes))
        
        for i, node in enumerate(self.nodes):
            energy = self._calculate_node_initial_energy(
                node, pillar_weights, structure_config, geo_modifiers
            )
            node.initial_energy = energy
            node.current_energy = energy
            H0[i] = energy
        
        self.H0 = H0
        return H0
    
    def _apply_stem_transformation(self, bazi: List[str], day_master: str, 
                                   day_master_node: GraphNode, month_branch_char: str):
        """
        [V39.0] 天干五合化气逻辑 (Stem Transformation / Hua Qi)
        
        检查日主是否参与天干五合，并验证化气条件。如果条件满足，修改节点元素。
        
        Args:
            bazi: 八字列表
            day_master: 日主天干
            day_master_node: 日主节点对象
            month_branch_char: 月支字符
        """
        from core.interactions import STEM_COMBINATIONS
        
        # 天干五合映射
        STEM_TRANSFORMATIONS = {
            ('甲', '己'): 'earth',  # 甲己化土
            ('己', '甲'): 'earth',
            ('乙', '庚'): 'metal',  # 乙庚化金
            ('庚', '乙'): 'metal',
            ('丙', '辛'): 'water',  # 丙辛化水
            ('辛', '丙'): 'water',
            ('丁', '壬'): 'wood',   # 丁壬化木
            ('壬', '丁'): 'wood',
            ('戊', '癸'): 'fire',   # 戊癸化火
            ('癸', '戊'): 'fire'
        }
        
        # 化气条件：月令必须支持化气五行
        TRANSFORM_CONDITIONS = {
            'earth': ['辰', '戌', '丑', '未', '巳', '午'],  # 土旺或火生土
            'metal': ['申', '酉', '辰', '戌', '丑', '未'],  # 金旺或土生金
            'water': ['亥', '子', '申', '酉'],              # 水旺或金生水
            'wood': ['寅', '卯', '亥', '子'],               # 木旺或水生木
            'fire': ['巳', '午', '寅', '卯']                # 火旺或木生火
        }
        
        # 查找日主参与的五合
        other_stem = None
        transform_element = None
        
        for pillar in bazi:
            if len(pillar) < 1:
                continue
            other_char = pillar[0]
            if other_char != day_master:
                pair = (day_master, other_char)
                if pair in STEM_TRANSFORMATIONS:
                    other_stem = other_char
                    transform_element = STEM_TRANSFORMATIONS[pair]
                    break
        
        if not transform_element or not other_stem:
            # 没有找到五合，不化气
            return
        
        # 验证化气条件：月令是否支持
        if month_branch_char not in TRANSFORM_CONDITIONS.get(transform_element, []):
            # 月令不支持化气，不化
            return
        
        # 找到另一个参与合化的天干节点
        other_stem_node = None
        for node in self.nodes:
            if node.char == other_stem and node.node_type == 'stem':
                other_stem_node = node
                break
        
        if not other_stem_node:
            return
        
        # 执行化气：修改元素属性
        # [V39.1] 减少日志输出（仅在调试时启用）
        # print(f"  [化气检测] {day_master}与{other_stem}合化{transform_element}（月令{month_branch_char}支持）")
        
        # 修改日主元素
        old_dm_element = day_master_node.element
        day_master_node.element = transform_element
        self.day_master_element = transform_element
        
        # 修改另一个天干元素
        other_stem_node.element = transform_element
        
        # print(f"  [化气完成] {day_master}元素从{old_dm_element}变为{transform_element}")
    
    def _has_root(self, stem_char: str, branch_char: str) -> bool:
        """检查天干是否在地支藏干中（通根）"""
        from core.processors.physics import PhysicsProcessor
        hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
        return any(stem_char == hidden[0] for hidden in hidden_map)
    
    def _calculate_hidden_stems_energy(self, branch_char: str, 
                                       physics_config: Dict) -> Dict[str, float]:
        """
        计算地支的藏干能量（壳核模型）。
        
        使用 60/30/10 或配置的比率。
        """
        from core.processors.physics import PhysicsProcessor
        hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
        
        ratios = physics_config.get('hiddenStemRatios', {
            'main': 0.60, 'middle': 0.30, 'remnant': 0.10
        })
        
        energy_dist = {}
        ratio_values = [ratios.get('main', 0.6), ratios.get('middle', 0.3), 
                       ratios.get('remnant', 0.1)]
        
        for idx, (stem_char, weight) in enumerate(hidden_map):
            if idx < len(ratio_values):
                element = self.STEM_ELEMENTS.get(stem_char, 'earth')
                energy = weight * ratio_values[idx] / 10.0  # 归一化
                energy_dist[element] = energy_dist.get(element, 0.0) + energy
        
        return energy_dist
    
    def _calculate_node_initial_energy(self, node: GraphNode,
                                      pillar_weights: Dict[str, float],
                                      structure_config: Dict,
                                      geo_modifiers: Dict[str, float] = None) -> float:
        """
        计算节点的初始能量，应用所有基础物理规则。
        
        规则包括：
        - 月令权重 (pg_month)
        - 通根加成 (root_w)
        - 自坐强根 (same_pillar_bonus)
        - 地理修正 (geo_modifiers)
        - 壳核模型（地支）
        """
        BASE_SCORE = 10.0
        
        # 基础能量
        energy = BASE_SCORE
        
        # 1. 宫位权重（月令最重要）
        pillar_weight = pillar_weights.get(node.pillar_name, 1.0)
        if node.pillar_name == 'month':
            # 月令权重通常更高（默认 1.2-1.8）
            pillar_weight = pillar_weights.get('month', 1.2)
        energy *= pillar_weight
        
        # 2. 通根加成（天干）
        if node.node_type == 'stem' and node.has_root:
            root_weight = structure_config.get('rootingWeight', 1.0)
            if node.is_same_pillar:
                # 自坐强根加成更大
                same_pillar_bonus = structure_config.get('samePillarBonus', 1.2)
                energy *= same_pillar_bonus
            else:
                # 普通通根
                energy *= (1.0 + (root_weight - 1.0) * 0.5)
        
        # 3. 透干加成（天干透出）
        if node.node_type == 'stem' and node.is_exposed:
            exposed_boost = structure_config.get('exposedBoost', 1.5)
            energy *= exposed_boost
        
        # 4. 壳核模型（地支：使用藏干能量）
        if node.node_type == 'branch' and node.hidden_stems_energy:
            # 地支的能量来自藏干的加权和
            total_hidden = sum(node.hidden_stems_energy.values())
            energy = BASE_SCORE * pillar_weight * total_hidden
        
        # 5. 地理修正
        if geo_modifiers and node.element in geo_modifiers:
            energy *= geo_modifiers[node.element]
        
        # 6. 空亡修正（如果配置）
        void_penalty = structure_config.get('voidPenalty', 1.0)
        energy *= void_penalty  # 默认不折损
        
        return energy
    
    # ===========================================
    # Phase 2: Adjacency Matrix Construction
    # ===========================================
    
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
        N = len(self.nodes)
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
                
                node_i = self.nodes[i]
                node_j = self.nodes[j]
                
                weight = 0.0
                
                # 1. 五行生克关系（传入字符以支持特殊效应检测）
                gen_weight = self._get_generation_weight(
                    node_j.element, node_i.element, flow_config, 
                    source_char=node_j.char, target_char=node_i.char
                )
                weight += gen_weight
                weight += self._get_control_weight(node_j.element, node_i.element, flow_config)
                
                # 1.5 特殊效应：润局（水润土生金）
                # 如果土生金，且全局存在水，增强权重
                if (node_j.element == 'earth' and node_i.element == 'metal' and
                    (node_j.char in ['未', '戌'] or node_j.char in ['丑', '辰'])):
                    # 检查是否有水节点存在
                    has_water = any(n.element == 'water' for n in self.nodes 
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
                if node_i.node_type == 'stem' and node_j.node_type == 'stem':
                    weight += self._get_stem_combination_weight(
                        node_i.char, node_j.char, interactions_config
                    )
                
                # 3. 地支合局（三合、三会、六合）
                if node_i.node_type == 'branch' and node_j.node_type == 'branch':
                    weight += self._get_branch_combo_weight(
                        node_i.char, node_j.char, combo_physics, branch_events
                    )
                
                # 4. 冲（Clash）
                weight += self._get_clash_weight(
                    node_i.char, node_j.char, node_i.node_type, node_j.node_type,
                    branch_events
                )
                
                # 5. 距离衰减（空间衰减）
                distance = abs(node_i.pillar_idx - node_j.pillar_idx)
                if distance > 0:
                    spatial_config = flow_config.get('spatialDecay', {'gap1': 0.6, 'gap2': 0.3})
                    if distance == 1:
                        weight *= spatial_config.get('gap1', 0.6)
                    elif distance >= 2:
                        weight *= spatial_config.get('gap2', 0.3)
                
                A[i][j] = weight
        
        self.adjacency_matrix = A
        return A
    
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
        """
        if source_element in GENERATION and GENERATION[source_element] == target_element:
            generation_efficiency = flow_config.get('generationEfficiency', 1.2)
            base_weight = 0.6 * generation_efficiency
            
            # 特殊处理：润局效应（水润土生金）
            # 如果土生金，且存在水（如亥），增强权重
            if source_element == 'earth' and target_element == 'metal':
                # 检查是否有水存在（简化：如果源字符是未/戌，且图中有亥/子）
                # 这里我们只检查基础权重，润局效应在矩阵构建时通过检查全局水节点来增强
                moisture_boost = flow_config.get('earthMetalMoistureBoost', 1.0)
                base_weight *= moisture_boost
            
            return base_weight
        return 0.0
    
    def _get_control_weight(self, source_element: str, target_element: str,
                            flow_config: Dict) -> float:
        """计算克的权重（负数：source 克 target）"""
        if source_element in CONTROL and CONTROL[source_element] == target_element:
            control_impact = flow_config.get('controlImpact', 0.7)
            # 克的阻尼率（负数）
            return -0.3 * control_impact
        return 0.0
    
    def _get_stem_combination_weight(self, stem1: str, stem2: str,
                                     interactions_config: Dict) -> float:
        """计算天干五合的权重"""
        from core.interactions import STEM_COMBINATIONS
        
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
        """计算地支合局的权重（三合、三会、六合）"""
        from core.interactions import BRANCH_SIX_COMBINES
        
        # 六合检测
        if BRANCH_SIX_COMBINES.get(branch1) == branch2:
            six_harmony = branch_events.get('sixHarmony', 5.0)
            return six_harmony / 10.0  # 归一化为权重
        
        # 三合检测（需要第三个节点，这里只检测两两关系的基础权重）
        # 完整的三合检测需要在矩阵构建时考虑三个节点的组合
        trine_bonus = combo_physics.get('trineBonus', 2.5)
        
        # 三合局定义（简化：只检测常见组合）
        trine_groups = [
            {'申', '子', '辰'},  # 三合水
            {'亥', '卯', '未'},  # 三合木
            {'寅', '午', '戌'},  # 三合火
            {'巳', '酉', '丑'},  # 三合金
        ]
        
        for group in trine_groups:
            if branch1 in group and branch2 in group:
                return trine_bonus / 10.0  # 归一化
        
        return 0.0
    
    def _get_clash_weight(self, char1: str, char2: str, type1: str, type2: str,
                         branch_events: Dict) -> float:
        """计算冲的权重（负数：破坏性）"""
        if type1 == 'branch' and type2 == 'branch':
            from core.interactions import BRANCH_CLASHES
            if (char1, char2) in BRANCH_CLASHES or (char2, char1) in BRANCH_CLASHES:
                clash_damping = branch_events.get('clashDamping', 0.3)
                clash_score = branch_events.get('clashScore', -5.0)
                # 冲的破坏性（负数，归一化为权重）
                return clash_score / 10.0 * clash_damping
        return 0.0
    
    # ===========================================
    # Phase 3: Propagation (传播迭代)
    # ===========================================
    
    def propagate(self, max_iterations: int = 10, damping: float = 0.9) -> np.ndarray:
        """
        Phase 3: 执行传播迭代，模拟动态做功。
        
        迭代公式：H^(t+1) = damping * A * H^(t) + (1-damping) * H^(0)
        
        这模拟了：
        - 能量从 Source 流向 Sink 的过程
        - Flow（流通）和 Blockage（阻滞）
        - 系统的动态平衡
        
        Args:
            max_iterations: 最大迭代次数
            damping: 阻尼系数（0-1），防止发散
        
        Returns:
            最终能量向量 H^(final) [N x 1]
        """
        if self.H0 is None or self.adjacency_matrix is None:
            raise ValueError("必须先执行 initialize_nodes() 和 build_adjacency_matrix()")
        
        H = self.H0.copy()
        flow_config = self.config.get('flow', {})
        global_entropy = flow_config.get('globalEntropy', 0.05)
        output_drain_penalty = flow_config.get('outputDrainPenalty', 1.2)  # [V42.1] 食伤泄耗惩罚
        
        # [V42.1] 确定日主节点和元素（用于食伤泄耗计算）
        dm_indices = []
        dm_element = None
        if hasattr(self, 'day_master_element') and self.day_master_element:
            dm_element = self.day_master_element
        # 如果没有化气，从节点中找到日主
        if not dm_element:
            for i, node in enumerate(self.nodes):
                if node.pillar_idx == 2 and node.node_type == 'stem':  # 日柱天干
                    dm_element = node.element
                    dm_indices.append(i)
                    break
        else:
            # 找到所有日主节点（可能有多个）
            for i, node in enumerate(self.nodes):
                if node.element == dm_element and node.pillar_idx == 2:
                    dm_indices.append(i)
        
        # [V42.1] 确定食伤元素（日主生的）
        output_elements = []
        if dm_element:
            from core.processors.physics import GENERATION
            for source, target in GENERATION.items():
                if source == dm_element:
                    output_elements.append(target)
        
        for iteration in range(max_iterations):
            # 矩阵乘法：能量传播
            H_new = self.adjacency_matrix @ H
            
            # 应用阻尼（防止发散）
            H = damping * H_new + (1 - damping) * self.H0
            
            # [V42.1] 应用食伤泄耗惩罚（日主生食伤时的额外能量损失）
            if dm_indices and output_elements:
                for dm_idx in dm_indices:
                    if H[dm_idx] <= 0:
                        continue
                    
                    # 计算日主流向所有食伤节点的总能量
                    total_output_flow = 0.0
                    for j, node in enumerate(self.nodes):
                        if node.element in output_elements:
                            flow_weight = self.adjacency_matrix[j][dm_idx]  # j从dm_idx获得的能量（正的表示dm生j）
                            if flow_weight > 0:
                                # 估算流量（简化：使用当前能量和权重）
                                flow_amount = flow_weight * H[dm_idx]
                                total_output_flow += flow_amount
                    
                    # 额外泄耗：日主生食伤时，不仅要转移能量，还要额外消耗
                    if total_output_flow > 0:
                        extra_drain = total_output_flow * (output_drain_penalty - 1.0)
                        H[dm_idx] = max(0.0, H[dm_idx] - extra_drain)
                        # 确保在全局熵之前应用
            
            # 应用全局熵增（能量损耗）
            H *= (1.0 - global_entropy)
            
            # 确保能量非负（物理约束）
            H = np.maximum(H, 0.0)
        
        # 更新节点的当前能量
        for i, node in enumerate(self.nodes):
            node.current_energy = H[i]
        
        return H
    
    # ===========================================
    # 辅助方法：计算宏观得分
    # ===========================================
    
    def calculate_strength_score(self, day_master: str) -> Dict[str, Any]:
        """
        计算身旺分数（占比法）- 标准化的百分制评分。
        
        使用公式：Strength_Score = (Self_Team / Total_Energy) * 100.0
        
        Args:
            day_master: 日主天干（如 '庚'）
        
        Returns:
            包含 strength_score, strength_label, self_team_energy, total_energy 的字典
        """
        # 获取日主元素（优先使用化气后的元素）
        if self.day_master_element:
            dm_element = self.day_master_element
        else:
            dm_element = self.STEM_ELEMENTS.get(day_master, 'metal')
        
        # 计算日主阵营能量
        # Self_Team = Self(日主) + Resource(生我的) + Peer(同我的)
        self_team_energy = 0.0
        total_energy = 0.0
        
        # 确定资源元素（生我的元素）
        resource_element = None
        for elem, target in GENERATION.items():
            if target == dm_element:
                resource_element = elem
                break
        
        # 累加所有节点的能量
        for node in self.nodes:
            node_energy = node.current_energy
            total_energy += node_energy
            
            # 累加日主阵营能量
            if node.element == dm_element:  # Self 或 Peer（同我）
                self_team_energy += node_energy
            elif resource_element and node.element == resource_element:  # Resource（生我的）
                self_team_energy += node_energy
        
        # 计算占比分数（0-100）
        if total_energy > 0:
            strength_score = (self_team_energy / total_energy) * 100.0
        else:
            strength_score = 0.0
        
        # 判断身强身弱（基于占比）- 使用动态阈值
        grading_config = self.config.get('grading', {})
        strong_threshold = grading_config.get('strong_threshold', 60.0)
        weak_threshold = grading_config.get('weak_threshold', 40.0)
        
        # 确保阈值合理
        strong_threshold = max(weak_threshold + 10.0, strong_threshold)
        weak_threshold = min(strong_threshold - 10.0, weak_threshold)
        
        # 基础判定
        if strength_score >= strong_threshold:
            strength_label = "Strong"
        elif strength_score >= weak_threshold:
            strength_label = "Balanced"
        else:
            strength_label = "Weak"
        
        # [V40.0] 特殊格局检测：专旺格/从旺格
        special_pattern = self._detect_special_pattern(dm_element, strength_score)
        if special_pattern:
            strength_label = special_pattern  # 覆盖为 "Special_Strong"
        
        return {
            'strength_score': strength_score,
            'strength_label': strength_label,
            'self_team_energy': self_team_energy,
            'total_energy': total_energy,
            'dm_element': dm_element,
            'resource_element': resource_element,
            'special_pattern': special_pattern if special_pattern else None
        }
    
    def _detect_special_pattern(self, dm_element: str, strength_score: float) -> Optional[str]:
        """
        [V40.0] 检测特殊格局：专旺格/从旺格
        
        判定条件：
        1. 全盘中能量最大的五行占比 > 65%（某一行独大）
        2. 日主强度分数 > 80.0（极强）
        
        如果满足，返回 "Special_Strong"，表示这是合法的专旺/从旺格局。
        
        Args:
            dm_element: 日主元素
            strength_score: 强度分数
        
        Returns:
            "Special_Strong" 如果检测到特殊格局，否则 None
        """
        if strength_score < 80.0:
            return None  # 强度不够，不是特殊格局
        
        # 计算五行的能量分布
        element_energies = {
            'wood': 0.0,
            'fire': 0.0,
            'earth': 0.0,
            'metal': 0.0,
            'water': 0.0
        }
        
        total_energy = 0.0
        for node in self.nodes:
            node_energy = node.current_energy
            element_energies[node.element] = element_energies.get(node.element, 0.0) + node_energy
            total_energy += node_energy
        
        if total_energy <= 0:
            return None
        
        # 找到能量最大的五行及其占比
        max_element = max(element_energies, key=element_energies.get)
        max_ratio = element_energies[max_element] / total_energy
        
        # 判定：如果某一行占比 > 65%，且日主极强，则为专旺格
        if max_ratio > 0.65:
            # 检查日主是否属于这一行（专旺）或生这一行（从旺）
            if dm_element == max_element:
                # 日主就是独大的那一行：专旺格
                return "Special_Strong"
            else:
                # 检查是否"从"这一行（日主生这一行，或被这一行生）
                from core.processors.physics import GENERATION
                # 如果独大的行生日主（日主被生），可能也是从旺的一种
                for source, target in GENERATION.items():
                    if source == max_element and target == dm_element:
                        # 独大的行生日主：从印格/从势格
                        return "Special_Strong"
                # 如果日主生独大的行，也可能是从儿格
                if GENERATION.get(dm_element) == max_element:
                    # 日主生独大的行：从儿格
                    return "Special_Strong"
        
        return None
    
    def _apply_relative_suppression(self, day_master: str):
        """
        [V43.0] 相对抑制机制（应力屈服物理模型）
        
        在传播结束后，根据官杀、财星、食伤对日主的相对压力，
        对日主能量进行非线性惩罚。
        
        这解决了"全局熵无法改变占比"的问题。
        """
        # 先检查特殊格局，避免误伤专旺格
        if hasattr(self, 'day_master_element') and self.day_master_element:
            dm_element = self.day_master_element
        else:
            dm_element = self.STEM_ELEMENTS.get(day_master, 'metal')
        
        # 快速检查是否可能是特殊格局（如果强度很高，可能是专旺）
        # 这里简化处理：如果日主能量占比很高，跳过抑制
        total_energy = sum(node.current_energy for node in self.nodes)
        if total_energy <= 0:
            return
        
        dm_energy = sum(node.current_energy for node in self.nodes 
                        if node.element == dm_element)
        dm_ratio = dm_energy / total_energy if total_energy > 0 else 0.0
        
        # 如果日主占比已经很高（>80%），可能是专旺格，跳过抑制
        if dm_ratio > 0.80:
            return
        
        # 确定十神关系
        from core.processors.physics import GENERATION, CONTROL
        
        # Officer (官杀): 克我的
        officer_elements = []
        for source, target in CONTROL.items():
            if target == dm_element:
                officer_elements.append(source)
        
        # Wealth (财): 我克的
        wealth_elements = []
        for source, target in CONTROL.items():
            if source == dm_element:
                wealth_elements.append(target)
        
        # Resource (印): 生我的
        resource_elements = []
        for source, target in GENERATION.items():
            if target == dm_element:
                resource_elements.append(source)
        
        # Output (食伤): 我生的
        output_elements = []
        for source, target in GENERATION.items():
            if source == dm_element:
                output_elements.append(target)
        
        # Peer (比劫): 同我的
        peer_elements = [dm_element]
        
        # 计算各阵营能量（使用初始能量，因为传播后所有能量都衰减了）
        # [V43.0] 关键修正：使用初始能量比，因为传播后所有能量都等比例衰减
        self_energy_init = sum(node.initial_energy for node in self.nodes 
                              if node.element == dm_element)
        officer_energy_init = sum(node.initial_energy for node in self.nodes 
                                 if node.element in officer_elements)
        wealth_energy_init = sum(node.initial_energy for node in self.nodes 
                                if node.element in wealth_elements)
        resource_energy_init = sum(node.initial_energy for node in self.nodes 
                                  if node.element in resource_elements)
        output_energy_init = sum(node.initial_energy for node in self.nodes 
                                if node.element in output_elements)
        peer_energy_init = sum(node.initial_energy for node in self.nodes 
                              if node.element in peer_elements) - self_energy_init  # 排除日主本身
        
        # 同时获取当前能量（用于计算抑制强度）
        self_energy = sum(node.current_energy for node in self.nodes 
                         if node.element == dm_element)
        
        # Case A: Officer Stress (官杀克身)
        # [V43.0] 使用初始能量比，但考虑日主阵营（日主+印+比劫）vs 官杀
        if self_energy_init > 0 and officer_energy_init > 0:
            # 计算日主阵营初始能量（日主+印+比劫）
            self_team_init = self_energy_init + resource_energy_init + peer_energy_init
            ratio_kill = officer_energy_init / self_team_init if self_team_init > 0 else 0
            # 条件：官杀明显强于日主阵营 (Ratio > 0.6，降低阈值) 且没有强印化解
            if ratio_kill > 0.6 and resource_energy_init < officer_energy_init * 0.5:
                # 日主发生屈服：压力越大，有效支撑力越小（反比衰减）
                suppression_factor = max(0.2, 1.0 / (ratio_kill * 2.0))  # 更激进的惩罚
                for node in self.nodes:
                    if node.element == dm_element:
                        node.current_energy *= suppression_factor
        
        # Case B: Wealth Burden (财多压身)
        # [V43.0] 使用初始能量比，但考虑日主阵营（日主+印+比劫）vs 财星
        if self_energy_init > 0 and wealth_energy_init > 0:
            # 计算日主阵营初始能量（日主+印+比劫）
            self_team_init = self_energy_init + resource_energy_init + peer_energy_init
            # 如果财星能量接近或超过日主阵营，说明财多压身
            ratio_wealth = wealth_energy_init / self_team_init if self_team_init > 0 else 0
            # 条件：财气过重 (Ratio > 0.6，进一步降低阈值) 且比劫无力
            if ratio_wealth > 0.6 and peer_energy_init < wealth_energy_init * 0.3:
                # 日主被耗干：根据比例调整惩罚
                # 如果财星能量超过日主阵营的60%，就开始惩罚
                penalty = max(0.2, 1.0 - (ratio_wealth - 0.6) * 3.0)  # 更激进的惩罚
                for node in self.nodes:
                    if node.element == dm_element:
                        node.current_energy *= penalty
        
        # Case C: Output Drain (食伤泄气)
        # [V43.0] 使用初始能量比
        if self_energy_init > 0 and output_energy_init > 0:
            # 条件：食伤能量大于日主
            if output_energy_init > self_energy_init:
                # 日主被泄：固定惩罚
                for node in self.nodes:
                    if node.element == dm_element:
                        node.current_energy *= 0.7
        
        # 确保能量非负
        for node in self.nodes:
            node.current_energy = max(0.0, node.current_energy)
    
    def calculate_domain_scores(self, day_master: str) -> Dict[str, float]:
        """
        基于传播后的能量计算宏观得分（财富、事业、感情）。
        
        这是 Layer 2 的投影层，将十神能量映射为宏观之相。
        """
        # 聚合各元素的能量
        element_energy = {'wood': 0.0, 'fire': 0.0, 'earth': 0.0, 
                         'metal': 0.0, 'water': 0.0}
        
        for node in self.nodes:
            if node.current_energy > 0:
                element_energy[node.element] += node.current_energy
        
        # 这里应该调用 DomainProcessor 或类似逻辑
        # 简化实现：返回基础能量分布
        return {
            'wealth': element_energy.get('earth', 0.0) + element_energy.get('metal', 0.0),
            'career': element_energy.get('metal', 0.0) + element_energy.get('fire', 0.0),
            'relationship': element_energy.get('wood', 0.0) + element_energy.get('water', 0.0),
        }
    
    def analyze(self, bazi: List[str], day_master: str, 
                luck_pillar: str = None, year_pillar: str = None,
                geo_modifiers: Dict[str, float] = None) -> Dict[str, Any]:
        """
        完整的图网络分析流程。
        
        执行三个阶段并返回结果。
        """
        # Phase 1: 节点初始化
        H0 = self.initialize_nodes(bazi, day_master, luck_pillar, year_pillar, geo_modifiers)
        
        # Phase 2: 构建邻接矩阵
        A = self.build_adjacency_matrix()
        
        # Phase 3: 传播迭代
        H_final = self.propagate(max_iterations=10, damping=0.9)
        
        # [V43.0] 应用相对抑制机制（应力屈服）- 在传播结束后，计算分数前
        self._apply_relative_suppression(day_master)
        
        # 重新更新能量向量（抑制后）
        for i, node in enumerate(self.nodes):
            H_final[i] = node.current_energy
        
        # 计算宏观得分
        domain_scores = self.calculate_domain_scores(day_master)
        
        # 计算标准化身旺分数（占比法）- 核心逻辑固化
        strength_data = self.calculate_strength_score(day_master)
        
        return {
            'initial_energy': H0.tolist(),
            'final_energy': H_final.tolist(),
            'adjacency_matrix': A.tolist(),
            'domain_scores': domain_scores,
            # 标准化身旺分数（0-100分）- 核心输出
            'strength_score': strength_data['strength_score'],
            'strength_label': strength_data['strength_label'],
            'self_team_energy': strength_data['self_team_energy'],
            'total_energy': strength_data['total_energy'],
            'nodes': [
                {
                    'id': node.node_id,
                    'char': node.char,
                    'type': node.node_type,
                    'node_type': node.node_type,  # 兼容两种命名
                    'element': node.element,
                    'pillar_idx': node.pillar_idx,
                    'pillar_name': node.pillar_name,
                    'initial_energy': node.initial_energy,
                    'final_energy': node.current_energy
                }
                for node in self.nodes
            ]
        }

