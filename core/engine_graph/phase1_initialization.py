"""
Phase 1: 节点初始化模块
======================

负责节点初始化和初始能量计算，应用所有基础物理规则。

包括：
- 节点创建（原局、大运、流年）
- 化气逻辑（天干五合）
- 通根检测
- 藏干能量计算
- 初始能量计算（月令、通根、壳核等）
"""

import numpy as np
from typing import Dict, List, Any, Optional
from core.engine_graph.graph_node import GraphNode
from core.engine_graph.constants import TWELVE_LIFE_STAGES, LIFE_STAGE_COEFFICIENTS
from core.processors.physics import PhysicsProcessor, GENERATION, CONTROL
from core.math import ProbValue
from core.math import saturation_curve


class NodeInitializer:
    """负责节点初始化和初始能量计算"""
    
    def __init__(self, engine: 'GraphNetworkEngine'):
        """
        初始化节点初始化器。
        
        Args:
            engine: GraphNetworkEngine 实例，用于访问共享状态
        """
        self.engine = engine
        self.config = engine.config
    
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
        # V13.1: 必须在开头设置 self.engine.bazi，否则季节系数无法应用
        self.engine.bazi = bazi
        
        self.engine.nodes = []
        node_id = 0
        
        # 获取参数配置
        physics_config = self.config.get('physics', {})
        structure_config = self.config.get('structure', {})
        pillar_weights = physics_config.get('pillarWeights', {
            'year': 0.8, 'month': 1.2, 'day': 1.0, 'hour': 0.9
        })
        
        # [V11.0] 时空权重
        spacetime_config = self.config.get('spacetime', {})
        luck_pillar_weight = spacetime_config.get('luckPillarWeight', 1.0)
        annual_pillar_weight = spacetime_config.get('annualPillarWeight', 1.2)
        
        # [V11.0] 计算地理与时代宏观修正系数
        macro_config = self.config.get('interactions', {}).get('macroPhysics', {})
        geo_config = spacetime_config.get('geo', {})
        era_config = spacetime_config.get('era', {})
        era_bonus = era_config.get('eraBonus', macro_config.get('eraBonus', 0.2))
        
        # 初始化或合并地理修正
        if geo_modifiers is None:
            geo_modifiers = {}
        else:
            geo_modifiers = geo_modifiers.copy()
            
        # 融合时代修正：九运离火加持火 (V11.0 时代场)
        era_element = era_config.get('eraElement') or macro_config.get('eraElement')
        if era_element and era_element.lower() == 'fire':
            geo_modifiers['fire'] = geo_modifiers.get('fire', 1.0) * (1.0 + era_bonus)
            geo_modifiers['water'] = geo_modifiers.get('water', 1.0) * (1.0 - era_bonus * 0.5)
        
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
            stem_element = self.engine.STEM_ELEMENTS.get(stem_char, 'earth')
            stem_node = GraphNode(
                node_id=node_id, char=stem_char, node_type='stem',
                element=stem_element, pillar_idx=idx, pillar_name=p_name
            )
            node_id += 1
            
            # 保存日主节点引用
            if idx == 2 and stem_char == day_master:  # 日柱且是日主
                day_master_node = stem_node
                self.engine.day_master_element = stem_element  # 初始化日主元素
            
            # 地支节点
            branch_element = self.engine.BRANCH_ELEMENTS.get(branch_char, 'earth')
            branch_node = GraphNode(
                node_id=node_id, char=branch_char, node_type='branch',
                element=branch_element, pillar_idx=idx, pillar_name=p_name
            )
            node_id += 1
            
            self.engine.nodes.append(stem_node)
            self.engine.nodes.append(branch_node)
            
            # 检查通根（天干在地支藏干中出现）
            if self._has_root(stem_char, branch_char):
                stem_node.has_root = True
                stem_node.is_same_pillar = True  # 自坐强根
                # [V52.0] 任务 B：记录通根地支，用于十二长生系数计算
                stem_node.root_branch = branch_char
            
            # 计算地支的藏干能量（壳核模型）- V11.0 传入地理修正
            branch_node.hidden_stems_energy = self._calculate_hidden_stems_energy(
                branch_char, physics_config, geo_modifiers
            )
        
        # [V39.0] 在计算能量之前，先应用化气逻辑
        if day_master_node and month_branch_char:
            self._apply_stem_transformation(bazi, day_master, day_master_node, month_branch_char)
        
        # 2. [V55.0] 添加大运节点（静态叠加层）
        # [V56.3 修复] 确保 luck_pillar 是字符串类型
        if luck_pillar:
            if not isinstance(luck_pillar, str):
                luck_pillar = str(luck_pillar) if luck_pillar else ""
        if luck_pillar and len(luck_pillar) >= 2:
            luck_stem = luck_pillar[0]
            luck_branch = luck_pillar[1]
            
            # [V11.0] 使用 spacetime.luckPillarWeight 作为基准权重
            dayun_branch_multiplier = physics_config.get('dayun_branch_multiplier', 1.2)
            dayun_stem_multiplier = physics_config.get('dayun_stem_multiplier', 0.8)
            dayun_branch_weight = luck_pillar_weight * dayun_branch_multiplier
            dayun_stem_weight = luck_pillar_weight * dayun_stem_multiplier
            
            luck_stem_node = GraphNode(
                node_id=node_id, char=luck_stem, node_type='stem',
                element=self.engine.STEM_ELEMENTS.get(luck_stem, 'earth'),
                pillar_idx=4, pillar_name='luck_stem'
            )
            luck_stem_node.dayun_weight = dayun_stem_weight  # [V55.0] 标记大运权重
            node_id += 1
            
            luck_branch_node = GraphNode(
                node_id=node_id, char=luck_branch, node_type='branch',
                element=self.engine.BRANCH_ELEMENTS.get(luck_branch, 'earth'),
                pillar_idx=4, pillar_name='luck_branch'
            )
            luck_branch_node.dayun_weight = dayun_branch_weight  # [V55.0] 标记大运权重
            node_id += 1
            
            self.engine.nodes.append(luck_stem_node)
            self.engine.nodes.append(luck_branch_node)
        
        # 3. [V55.0] 添加流年节点（动态引动层）
        if year_pillar and len(year_pillar) >= 2:
            year_stem = year_pillar[0]
            year_branch = year_pillar[1]
            
            # [V55.0] 流年权重：流年是君，权力最大，但衰减极快
            # 初始能量极高，但会在传播中快速衰减
            year_stem_node = GraphNode(
                node_id=node_id, char=year_stem, node_type='stem',
                element=self.engine.STEM_ELEMENTS.get(year_stem, 'earth'),
                pillar_idx=5, pillar_name='year_stem'
            )
            year_stem_node.is_liunian = True  # [V55.0] 标记为流年节点
            # [V11.0] 使用 spacetime.annualPillarWeight 作为流年权力系数
            year_stem_node.liunian_power = annual_pillar_weight
            node_id += 1
            
            year_branch_node = GraphNode(
                node_id=node_id, char=year_branch, node_type='branch',
                element=self.engine.BRANCH_ELEMENTS.get(year_branch, 'earth'),
                pillar_idx=5, pillar_name='year_branch'
            )
            year_branch_node.is_liunian = True  # [V55.0] 标记为流年节点
            year_branch_node.liunian_power = annual_pillar_weight
            node_id += 1
            
            self.engine.nodes.append(year_stem_node)
            self.engine.nodes.append(year_branch_node)
        
        # 4. 计算初始能量（应用所有物理规则）
        # [V13.5] Fix: Must use dtype=object to hold ProbValue objects, otherwise they collapse to float
        H0 = np.zeros(len(self.engine.nodes), dtype=object)
        
        for i, node in enumerate(self.engine.nodes):
            # [V55.0] 大运节点使用特殊权重
            if hasattr(node, 'dayun_weight'):
                # 大运节点：使用大运权重计算能量
                base_energy = self._calculate_node_initial_energy(
                    node, pillar_weights, structure_config, geo_modifiers
                )
                energy = base_energy * node.dayun_weight
            elif hasattr(node, 'is_liunian') and node.is_liunian:
                # [V55.0] 流年节点：初始能量极高（流年是君）
                # [V12.1] 参数化：流年初始能量增强倍数（1.5倍）可以考虑参数化，但暂时保持
                base_energy = self._calculate_node_initial_energy(
                    node, pillar_weights, structure_config, geo_modifiers
                )
                # V13.0: 流年能量增强（ProbValue 乘法）
                energy = base_energy * node.liunian_power * 1.5  # 流年初始能量增强
            else:
                # 原局节点：正常计算
                energy = self._calculate_node_initial_energy(
                    node, pillar_weights, structure_config, geo_modifiers
                )
            
            # [V58.2] Seasonal Dominance Lock: 当令五行初始能量加成
            # [V13.1] 参数清洗：删除 season_dominance_boost，完全由 seasonWeights.wang 和 pillarWeights.month 决定
            # 检查节点元素是否是当令五行（月令元素）
            if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 1:
                month_branch = self.engine.bazi[1][1] if len(self.engine.bazi[1]) > 1 else None
                if month_branch:
                    month_element = self.engine.BRANCH_ELEMENTS.get(month_branch, 'earth')
                    
                    # V12.5: 细分月令关系，修正"生克不分"的逻辑漏洞
                    # V13.0: 使用统一的 season_factor 系数，并调整不确定度
                    # V13.1: 从配置文件读取 seasonWeights，确保泄气(0.90)和被克(0.45)有显著差异
                    season_weights = physics_config.get('seasonWeights', {
                        'wang': 1.20, 'xiang': 1.00, 'xiu': 0.90, 'qiu': 0.60, 'si': 0.45
                    })
                    season_factor = 1.0  # 默认系数
                    season_std_boost = 1.0  # 不确定度调整系数
                    
                    if node.element == month_element:
                        # 1. 得令：节点元素与月令元素相同（如甲生寅月）
                        # V13.1: 使用 seasonWeights.wang，不再使用 season_dominance_boost（避免能量通胀）
                        season_factor = season_weights.get('wang', 1.2)
                        # V13.0: 得令最稳，不确定度不变（已经是 5%）
                        season_std_boost = 1.0
                    elif month_element in GENERATION and GENERATION[month_element] == node.element:
                        # 2. 得生：月令生节点（如甲生子月，水生木）
                        season_factor = season_weights.get('xiang', 1.0)  # V12.5: 使用配置值
                        # V13.0: 得生较稳，不确定度略增（10%）
                        season_std_boost = 1.0
                    elif node.element in GENERATION and GENERATION[node.element] == month_element:
                        # 3. 泄气：节点生月令（如甲生午月，木生火）
                        # V13.1: 强制区分泄气和被克，使用配置值 0.85（稍微降低，但仍显著高于被克）
                        season_factor = season_weights.get('xiu', 0.85)  # 泄气：0.85（必须显著高于被克 0.5）
                        # V13.0: 泄气是正常能量流动，不确定度正常（15%）
                        season_std_boost = 1.5
                    elif month_element in CONTROL and CONTROL[month_element] == node.element:
                        # 4. 被克：月令克节点（如甲生申月，金克木）
                        # V13.1: 强制区分被克和泄气，使用配置值 0.5（严厉惩罚，显著弱于泄气 0.85）
                        season_factor = season_weights.get('si', 0.5)  # 被克：0.5（必须显著弱于泄气 0.85）
                        # V13.0: 被克是战争状态，不确定度极大（30%+）
                        season_std_boost = 3.0
                    elif node.element in CONTROL and CONTROL[node.element] == month_element:
                        # 5. 我克月令（耗）：节点克月令（如甲生未月，木克土）
                        season_factor = season_weights.get('qiu', 0.6)  # V12.5: 使用配置值
                        # V13.0: 我克月令，不确定度中等（20%）
                        season_std_boost = 2.0
                    else:
                        # 其他情况（如相冲等）：保持原样
                        season_factor = 1.0
                        season_std_boost = 1.0
                    
                    # V13.0: 应用季节系数（ProbValue 乘法）
                    energy = energy * season_factor
                    # V13.0: 调整不确定度
                    # V13.0: 调整不确定度 - 确保转换为 ProbValue
                    std_dev_percent = 0.1 * season_std_boost
                    if isinstance(energy, ProbValue):
                        # 如果已经是 ProbValue (来自乘法)，我们可能需要根据季节状态增加不确定度
                        # 例如被克时，不确定度应该很大
                         current_std_percent = energy.std / energy.mean if energy.mean != 0 else 0.1
                         final_std_percent = max(current_std_percent, std_dev_percent)
                         energy = ProbValue(energy.mean, final_std_percent)
                    else:
                         energy = ProbValue(float(energy), std_dev_percent)
                         
                    # Store in H0 (as object)
                    H0[i] = energy
                    
                    # Store in H0 (as object)
                    H0[i] = energy
            
            # V13.0: 确保能量是 ProbValue（概率值）
            if not isinstance(energy, ProbValue):
                # 如果还是 float，转换为 ProbValue（使用默认不确定度）
                energy = ProbValue(energy, std_dev_percent=0.1)
            
            node.initial_energy = energy
            node.current_energy = energy
            # V13.0: H0 存储 ProbValue（全程使用概率分布）
            H0[i] = energy  # 保留 ProbValue，不使用 float
        
        # [V59.0] Absolute Self-Punishment (绝对自刑惩罚) - Fix REAL_W_010
        # 在节点初始化完成后，检测自刑并直接削减节点初始能量
        if hasattr(self.engine, 'bazi') and self.engine.bazi:
            branches = [p[1] for p in self.engine.bazi if len(p) >= 2]
            self_punishments = {'辰', '午', '酉', '亥'}
            branch_counts = {}
            for branch in branches:
                branch_counts[branch] = branch_counts.get(branch, 0) + 1
            
            # 检测自刑地支（出现 >= 2 次）
            self_punishment_branches = set()
            for branch, count in branch_counts.items():
                if branch in self_punishments and count >= 2:
                    self_punishment_branches.add(branch)
            
            # 如果检测到自刑，削减所有对应地支的节点初始能量
            # [V12.1] 参数化：从配置读取自刑惩罚系数
            self_punishment_damping = physics_config.get('self_punishment_damping', 0.2)
            if self_punishment_branches:
                for i, node in enumerate(self.engine.nodes):
                    # 如果是自刑地支节点本身，直接削减
                    if node.node_type == 'branch' and node.char in self_punishment_branches:
                        # 自刑惩罚：只保留配置的比例（默认20%）
                        node.initial_energy *= self_punishment_damping
                        node.current_energy *= self_punishment_damping
                        H0[i] *= self_punishment_damping
                    # 如果是自刑地支藏干对应的天干节点，也削减
                    elif node.node_type == 'stem':
                        # 检查该天干是否在自刑地支的藏干中
                        for branch_char in self_punishment_branches:
                            hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
                            for hidden_stem, _ in hidden_map:
                                if node.char == hidden_stem:
                                    # 该天干是自刑地支的藏干，削减其初始能量
                                    node.initial_energy *= self_punishment_damping
                                    node.current_energy *= self_punishment_damping
                                    H0[i] *= self_punishment_damping
                                    break
        
        self.engine.H0 = H0
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
        for node in self.engine.nodes:
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
        self.engine.day_master_element = transform_element
        
        # 修改另一个天干元素
        other_stem_node.element = transform_element
        
        # print(f"  [化气完成] {day_master}元素从{old_dm_element}变为{transform_element}")
    
    def _has_root(self, stem_char: str, branch_char: str) -> bool:
        """检查天干是否在地支藏干中（通根）"""
        hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
        return any(stem_char == hidden[0] for hidden in hidden_map)
    
    def _calculate_hidden_stems_energy(self, branch_char: str, 
                                       physics_config: Dict,
                                       geo_modifiers: Dict[str, float] = None) -> Dict[str, float]:
        """
        计算地支的藏干能量（壳核模型）。
        
        使用 60/30/10 或配置的比率。
        """
        hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
        
        ratios = physics_config.get('hiddenStemRatios', {
            'main': 0.60, 'middle': 0.30, 'remnant': 0.10
        })
        
        energy_dist = {}
        ratio_values = [ratios.get('main', 0.6), ratios.get('middle', 0.3), 
                       ratios.get('remnant', 0.1)]
        
        for idx, (stem_char, weight) in enumerate(hidden_map):
            if idx < len(ratio_values):
                element = self.engine.STEM_ELEMENTS.get(stem_char, 'earth')
                energy = weight * ratio_values[idx] / 10.0  # 归一化
                
                # [V11.0] 应用地理/时代环境修正到隐藏气分布
                if geo_modifiers and element in geo_modifiers:
                    energy *= geo_modifiers[element]
                    
                energy_dist[element] = energy_dist.get(element, 0.0) + energy
        
        return energy_dist
    
    def _calculate_node_initial_energy(self, node: GraphNode,
                                      pillar_weights: Dict[str, float],
                                      structure_config: Dict,
                                      geo_modifiers: Dict[str, float] = None):
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
        # V12.4: 强制权重阶梯，确保物理逻辑正确（Day > Hour > Year）
        pillar_weight = pillar_weights.get(node.pillar_name, 1.0)
        if node.pillar_name == 'month':
            # V12.4: 月令权重（最高，但保持合理范围）
            pillar_weight = pillar_weights.get('month', 1.2)
        elif node.pillar_name == 'day':
            # V12.5: 日支权重（必须是最高的之一，确保坐下强于时支）
            pillar_weight = pillar_weights.get('day', 1.2)
        elif node.pillar_name == 'hour':
            # V12.4: 时支权重（必须 < day）
            pillar_weight = pillar_weights.get('hour', 0.9)
        elif node.pillar_name == 'year':
            # V12.4: 年支权重（最低）
            pillar_weight = pillar_weights.get('year', 0.7)
        energy *= pillar_weight
        
        # 2. 通根加成（天干）- V12.2: 使用非线性饱和函数
        if node.node_type == 'stem' and node.has_root:
            root_weight = structure_config.get('rootingWeight', 1.0)
            
            # [V52.0] 任务 B：应用十二长生系数
            # [V10.3 核心分析师建议] 重构通根加权：引入 Effective_Rooting_Bonus
            life_stage_coefficient = 1.0  # 默认系数
            effective_rooting_bonus = 1.0  # 有效通根加成（默认1.0，主气根时柱x2.5）
            root_branch_found = None
            
            if hasattr(node, 'root_branch') and node.root_branch:
                root_branch_found = node.root_branch
            else:
                # 如果没有记录，尝试从其他节点查找
                for other_node in self.engine.nodes:
                    if (other_node.node_type == 'branch' and 
                        other_node.pillar_idx == node.pillar_idx and
                        self._has_root(node.char, other_node.char)):
                        root_branch_found = other_node.char
                        break
            
            # V12.2: 计算所有根的总强度（加权求和）
            total_root_strength = 0.0
            root_count = 0
            
            if root_branch_found:
                # 查找天干在地支的长生状态
                life_stage = TWELVE_LIFE_STAGES.get((node.char, root_branch_found), None)
                if life_stage:
                    life_stage_coefficient = LIFE_STAGE_COEFFICIENTS.get(life_stage, 1.0)
                    
                    # [V13.1] 阳刃特例：阳干见帝旺为"阳刃"，系数强制修正为1.80
                    if life_stage == '帝旺':
                        # 检查是否为阳干（甲、丙、戊、庚、壬）
                        yang_stems = ['甲', '丙', '戊', '庚', '壬']
                        if node.char in yang_stems:
                            life_stage_coefficient = 1.80  # V2.6 附录A：阳刃特例
                    
                    # [V13.1] 墓库特例：开库后系数从0.5跃迁至1.5（在开库检测后处理）
                    # 注意：墓库开库检测在传播阶段进行，这里只处理基础系数
                
                # [V10.3] 核心逻辑：如果时支有主气根（临官/帝旺），应用2.5倍动态提权
                # 主气根判定：临官或帝旺位（十二长生强根）
                is_main_qi_root = life_stage in ['临官', '帝旺']
                
                # 检查通根地支是否在时支（hour pillar，pillar_idx == 3）
                root_branch_pillar_idx = None
                for other_node in self.engine.nodes:
                    if other_node.node_type == 'branch' and other_node.char == root_branch_found:
                        root_branch_pillar_idx = other_node.pillar_idx
                        break
                
                is_hour_pillar_root = (root_branch_pillar_idx == 3) if root_branch_pillar_idx is not None else False
                
                if is_main_qi_root and is_hour_pillar_root:
                    effective_rooting_bonus = 2.5
                else:
                    effective_rooting_bonus = 1.0
                
                # V12.2: 计算根强度（考虑长生状态和位置）
                root_strength = 1.0 * life_stage_coefficient * effective_rooting_bonus
                total_root_strength += root_strength
                root_count += 1
            
            # 查找其他柱的通根（如果有）
            for other_node in self.engine.nodes:
                if (other_node.node_type == 'branch' and 
                    other_node.pillar_idx != node.pillar_idx and
                    self._has_root(node.char, other_node.char)):
                    # 计算这个根的长生状态
                    other_life_stage = TWELVE_LIFE_STAGES.get((node.char, other_node.char), None)
                    other_life_coeff = LIFE_STAGE_COEFFICIENTS.get(other_life_stage, 1.0) if other_life_stage else 1.0
                    other_root_strength = 0.5 * other_life_coeff  # 远根权重降低
                    total_root_strength += other_root_strength
                    root_count += 1
            
            # V12.2: 应用饱和函数（防止无限叠加，模拟边际递减）
            # V12.5: 修正 - 确保 samePillarBonus 在饱和函数之后独立应用，且不参与饱和计算
            if total_root_strength > 0:
                # 使用饱和曲线：第一个根最重要，后面递减
                saturation_max = structure_config.get('rootingSaturationMax', 2.5)  # 可配置的最大加成
                saturation_steepness = structure_config.get('rootingSaturationSteepness', 0.8)  # 可配置的陡峭度
                
                # V12.5: 先计算基础通根加成（饱和函数）- 只计算根气强度，不包含自坐加成
                base_root_bonus = saturation_curve(
                    total_root_strength, 
                    max_val=saturation_max, 
                    steepness=saturation_steepness
                )
                
                # V12.5: 应用基础通根加成（非线性饱和）
                energy *= (1.0 + base_root_bonus)
        
        # V12.5: 自坐强根是独立的线性乘数，必须在饱和函数之后应用
        # 这是物理结构优势，确保日支(坐下)永远比时支强
        # 必须确保：只要 node.is_same_pillar == True，能量必须乘上 samePillarBonus
        # 这是解决 Group B (B3 Gap 不够) 的关键
        if node.is_same_pillar:
            same_pillar_bonus = structure_config.get('samePillarBonus', 1.6)
            # 独立乘数，不被饱和函数压平，确保日支能量 > 年时支
            energy *= same_pillar_bonus
        
        # 3. 透干加成（天干透出）
        if node.node_type == 'stem' and node.is_exposed:
            exposed_boost = structure_config.get('exposedBoost', 1.5)
            energy *= exposed_boost
        
        # 4. 壳核模型（地支：使用藏干能量）
        if node.node_type == 'branch' and node.hidden_stems_energy:
            # 地支的能量来自藏干的加权和
            total_hidden = sum(node.hidden_stems_energy.values())
            # V12.6: 修复 Bug - 之前此处直接赋值覆盖了 pillar_weight 和 geo_modifiers
            energy = BASE_SCORE * pillar_weight * total_hidden
        
        # 5. 地理修正
        if geo_modifiers and node.element in geo_modifiers:
            energy *= geo_modifiers[node.element]
        
        # 6. 空亡修正（如果配置）
        void_penalty = structure_config.get('voidPenalty', 1.0)
        energy *= void_penalty  # 默认不折损
        
        return energy

