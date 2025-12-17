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
from core.nonlinear_activation import NonlinearActivation
from core.bayesian_inference import BayesianInference
from core.gat_attention import GATAdjacencyBuilder
from core.transformer_temporal import TemporalTransformer, MultiScaleTemporalFusion

# [V52.0] 十二长生表 (12 Life Stages Table)
# 定义天干在各地支的长生状态
TWELVE_LIFE_STAGES = {
    # 甲木 (Yang Wood)
    ('甲', '亥'): '长生', ('甲', '子'): '沐浴', ('甲', '丑'): '冠带', ('甲', '寅'): '临官',
    ('甲', '卯'): '帝旺', ('甲', '辰'): '衰', ('甲', '巳'): '病', ('甲', '午'): '死',
    ('甲', '未'): '墓', ('甲', '申'): '绝', ('甲', '酉'): '胎', ('甲', '戌'): '养',
    # 乙木 (Yin Wood) - 与甲木相反
    ('乙', '午'): '长生', ('乙', '巳'): '沐浴', ('乙', '辰'): '冠带', ('乙', '卯'): '临官',
    ('乙', '寅'): '帝旺', ('乙', '丑'): '衰', ('乙', '子'): '病', ('乙', '亥'): '死',
    ('乙', '戌'): '墓', ('乙', '酉'): '绝', ('乙', '申'): '胎', ('乙', '未'): '养',
    # 丙火 (Yang Fire)
    ('丙', '寅'): '长生', ('丙', '卯'): '沐浴', ('丙', '辰'): '冠带', ('丙', '巳'): '临官',
    ('丙', '午'): '帝旺', ('丙', '未'): '衰', ('丙', '申'): '病', ('丙', '酉'): '死',
    ('丙', '戌'): '墓', ('丙', '亥'): '绝', ('丙', '子'): '胎', ('丙', '丑'): '养',
    # 丁火 (Yin Fire) - 与丙火相反
    ('丁', '酉'): '长生', ('丁', '申'): '沐浴', ('丁', '未'): '冠带', ('丁', '午'): '临官',
    ('丁', '巳'): '帝旺', ('丁', '辰'): '衰', ('丁', '卯'): '病', ('丁', '寅'): '死',
    ('丁', '丑'): '墓', ('丁', '子'): '绝', ('丁', '亥'): '胎', ('丁', '戌'): '养',
    # 戊土 (Yang Earth) - 与丙火相同
    ('戊', '寅'): '长生', ('戊', '卯'): '沐浴', ('戊', '辰'): '冠带', ('戊', '巳'): '临官',
    ('戊', '午'): '帝旺', ('戊', '未'): '衰', ('戊', '申'): '病', ('戊', '酉'): '死',
    ('戊', '戌'): '墓', ('戊', '亥'): '绝', ('戊', '子'): '胎', ('戊', '丑'): '养',
    # 己土 (Yin Earth) - 与丁火相同
    ('己', '酉'): '长生', ('己', '申'): '沐浴', ('己', '未'): '冠带', ('己', '午'): '临官',
    ('己', '巳'): '帝旺', ('己', '辰'): '衰', ('己', '卯'): '病', ('己', '寅'): '死',
    ('己', '丑'): '墓', ('己', '子'): '绝', ('己', '亥'): '胎', ('己', '戌'): '养',
    # 庚金 (Yang Metal)
    ('庚', '巳'): '长生', ('庚', '午'): '沐浴', ('庚', '未'): '冠带', ('庚', '申'): '临官',
    ('庚', '酉'): '帝旺', ('庚', '戌'): '衰', ('庚', '亥'): '病', ('庚', '子'): '死',
    ('庚', '丑'): '墓', ('庚', '寅'): '绝', ('庚', '卯'): '胎', ('庚', '辰'): '养',
    # 辛金 (Yin Metal) - 与庚金相反
    ('辛', '子'): '长生', ('辛', '亥'): '沐浴', ('辛', '戌'): '冠带', ('辛', '酉'): '临官',
    ('辛', '申'): '帝旺', ('辛', '未'): '衰', ('辛', '午'): '病', ('辛', '巳'): '死',
    ('辛', '辰'): '墓', ('辛', '卯'): '绝', ('辛', '寅'): '胎', ('辛', '丑'): '养',
    # 壬水 (Yang Water)
    ('壬', '申'): '长生', ('壬', '酉'): '沐浴', ('壬', '戌'): '冠带', ('壬', '亥'): '临官',
    ('壬', '子'): '帝旺', ('壬', '丑'): '衰', ('壬', '寅'): '病', ('壬', '卯'): '死',
    ('壬', '辰'): '墓', ('壬', '巳'): '绝', ('壬', '午'): '胎', ('壬', '未'): '养',
    # 癸水 (Yin Water) - 与壬水相反
    ('癸', '卯'): '长生', ('癸', '寅'): '沐浴', ('癸', '丑'): '冠带', ('癸', '子'): '临官',
    ('癸', '亥'): '帝旺', ('癸', '戌'): '衰', ('癸', '酉'): '病', ('癸', '申'): '死',
    ('癸', '未'): '墓', ('癸', '午'): '绝', ('癸', '巳'): '胎', ('癸', '辰'): '养',
}

# [V52.0] 十二长生系数表 (Life Stage Coefficients)
LIFE_STAGE_COEFFICIENTS = {
    '长生': 1.5,   # 活力极强
    '帝旺': 1.5,   # 能量巅峰
    '临官': 1.5,   # 建禄，强根
    '冠带': 1.2,   # 成长中
    '沐浴': 1.0,   # 基础值
    '胎': 0.8,     # 萌芽
    '养': 0.8,     # 孕育
    '衰': 0.5,     # 衰退
    '病': 0.5,     # 虚弱
    '死': 0.5,     # 无活力
    '墓': 0.3,     # 被困
    '绝': 0.3,     # 极弱
}


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
        
        # [V55.0] 保存八字信息，用于冲提纲检测
        self.bazi: List[str] = []
        
        # 物理处理器（用于计算初始能量）
        self.physics_processor = PhysicsProcessor()
        
        # [V10.0] GAT 邻接矩阵构建器（可选）
        self.use_gat = config.get('use_gat', False)  # 默认使用传统固定矩阵
        if self.use_gat:
            self.gat_builder = GATAdjacencyBuilder(config)
        else:
            self.gat_builder = None
        
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
                # [V52.0] 任务 B：记录通根地支，用于十二长生系数计算
                stem_node.root_branch = branch_char
            
            # 计算地支的藏干能量（壳核模型）
            branch_node.hidden_stems_energy = self._calculate_hidden_stems_energy(
                branch_char, physics_config
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
            
            # [V55.0] 大运权重：大运重地支，地支权重 = 1.2x 月令权重
            month_weight = pillar_weights.get('month', 1.2)
            dayun_branch_weight = month_weight * 1.2  # 大运地支权重
            dayun_stem_weight = month_weight * 0.8     # 大运天干权重
            
            luck_stem_node = GraphNode(
                node_id=node_id, char=luck_stem, node_type='stem',
                element=self.STEM_ELEMENTS.get(luck_stem, 'earth'),
                pillar_idx=4, pillar_name='luck_stem'
            )
            luck_stem_node.dayun_weight = dayun_stem_weight  # [V55.0] 标记大运权重
            node_id += 1
            
            luck_branch_node = GraphNode(
                node_id=node_id, char=luck_branch, node_type='branch',
                element=self.BRANCH_ELEMENTS.get(luck_branch, 'earth'),
                pillar_idx=4, pillar_name='luck_branch'
            )
            luck_branch_node.dayun_weight = dayun_branch_weight  # [V55.0] 标记大运权重
            node_id += 1
            
            self.nodes.append(luck_stem_node)
            self.nodes.append(luck_branch_node)
        
        # 3. [V55.0] 添加流年节点（动态引动层）
        if year_pillar and len(year_pillar) >= 2:
            year_stem = year_pillar[0]
            year_branch = year_pillar[1]
            
            # [V55.0] 流年权重：流年是君，权力最大，但衰减极快
            # 初始能量极高，但会在传播中快速衰减
            year_stem_node = GraphNode(
                node_id=node_id, char=year_stem, node_type='stem',
                element=self.STEM_ELEMENTS.get(year_stem, 'earth'),
                pillar_idx=5, pillar_name='year_stem'
            )
            year_stem_node.is_liunian = True  # [V55.0] 标记为流年节点
            year_stem_node.liunian_power = 2.0  # [V55.0] 流年权力系数
            node_id += 1
            
            year_branch_node = GraphNode(
                node_id=node_id, char=year_branch, node_type='branch',
                element=self.BRANCH_ELEMENTS.get(year_branch, 'earth'),
                pillar_idx=5, pillar_name='year_branch'
            )
            year_branch_node.is_liunian = True  # [V55.0] 标记为流年节点
            year_branch_node.liunian_power = 2.0  # [V55.0] 流年权力系数
            node_id += 1
            
            self.nodes.append(year_stem_node)
            self.nodes.append(year_branch_node)
        
        # 4. 计算初始能量（应用所有物理规则）
        H0 = np.zeros(len(self.nodes))
        
        for i, node in enumerate(self.nodes):
            # [V55.0] 大运节点使用特殊权重
            if hasattr(node, 'dayun_weight'):
                # 大运节点：使用大运权重计算能量
                base_energy = self._calculate_node_initial_energy(
                    node, pillar_weights, structure_config, geo_modifiers
                )
                energy = base_energy * node.dayun_weight
            elif hasattr(node, 'is_liunian') and node.is_liunian:
                # [V55.0] 流年节点：初始能量极高（流年是君）
                base_energy = self._calculate_node_initial_energy(
                    node, pillar_weights, structure_config, geo_modifiers
                )
                energy = base_energy * node.liunian_power * 1.5  # 流年初始能量增强
            else:
                # 原局节点：正常计算
                energy = self._calculate_node_initial_energy(
                    node, pillar_weights, structure_config, geo_modifiers
                )
            
            # [V58.2] Seasonal Dominance Lock: 当令五行初始能量加成
            # 检查节点元素是否是当令五行（月令元素）
            if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 1:
                month_branch = self.bazi[1][1] if len(self.bazi[1]) > 1 else None
                if month_branch:
                    month_element = self.BRANCH_ELEMENTS.get(month_branch, 'earth')
                    # 如果节点元素是当令五行，初始能量获得 1.3x 季节加成
                    if node.element == month_element:
                        energy *= 1.3
            
            node.initial_energy = energy
            node.current_energy = energy
            H0[i] = energy
        
        # [V59.0] Absolute Self-Punishment (绝对自刑惩罚) - Fix REAL_W_010
        # 在节点初始化完成后，检测自刑并直接削减节点初始能量
        if hasattr(self, 'bazi') and self.bazi:
            branches = [p[1] for p in self.bazi if len(p) >= 2]
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
            if self_punishment_branches:
                for i, node in enumerate(self.nodes):
                    # 如果是自刑地支节点本身，直接削减
                    if node.node_type == 'branch' and node.char in self_punishment_branches:
                        # 强制削减 80% 初始能量（只保留 20%）
                        node.initial_energy *= 0.2
                        node.current_energy *= 0.2
                        H0[i] *= 0.2
                    # 如果是自刑地支藏干对应的天干节点，也削减
                    elif node.node_type == 'stem':
                        # 检查该天干是否在自刑地支的藏干中
                        from core.processors.physics import PhysicsProcessor
                        for branch_char in self_punishment_branches:
                            hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
                            for hidden_stem, _ in hidden_map:
                                if node.char == hidden_stem:
                                    # 该天干是自刑地支的藏干，削减其初始能量
                                    node.initial_energy *= 0.2
                                    node.current_energy *= 0.2
                                    H0[i] *= 0.2
                                    break
        
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
            
            # [V52.0] 任务 B：应用十二长生系数
            life_stage_coefficient = 1.0  # 默认系数
            if hasattr(node, 'root_branch') and node.root_branch:
                # 查找天干在地支的长生状态
                life_stage = TWELVE_LIFE_STAGES.get((node.char, node.root_branch), None)
                if life_stage:
                    life_stage_coefficient = LIFE_STAGE_COEFFICIENTS.get(life_stage, 1.0)
            
            if node.is_same_pillar:
                # 自坐强根加成更大
                same_pillar_bonus = structure_config.get('samePillarBonus', 1.2)
                energy *= same_pillar_bonus * life_stage_coefficient  # [V52.0] 乘以十二长生系数
            else:
                # 普通通根（需要查找其他柱的通根地支）
                # 遍历所有节点，找到通根的地支
                root_branch_found = None
                if hasattr(node, 'root_branch'):
                    root_branch_found = node.root_branch
                else:
                    # 如果没有记录，尝试从其他节点查找
                    for other_node in self.nodes:
                        if (other_node.node_type == 'branch' and 
                            other_node.pillar_idx == node.pillar_idx and
                            self._has_root(node.char, other_node.char)):
                            root_branch_found = other_node.char
                            break
                
                if root_branch_found:
                    life_stage = TWELVE_LIFE_STAGES.get((node.char, root_branch_found), None)
                    if life_stage:
                        life_stage_coefficient = LIFE_STAGE_COEFFICIENTS.get(life_stage, 1.0)
                
                energy *= (1.0 + (root_weight - 1.0) * 0.5) * life_stage_coefficient  # [V52.0] 乘以十二长生系数
        
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
                weight += self._get_control_weight(
                    node_j.element, node_i.element, flow_config,
                    source_char=node_j.char, target_char=node_i.char
                )
                
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
                # [V59.0] 透干印星豁免距离衰减：如果节点是透干印星（天干节点且是印星），不应用距离衰减
                # 因为透干印星的通关能力不受距离限制
                is_exposed_resource = False
                if node_j.node_type == 'stem':
                    # 检查 node_j 是否是透干印星
                    from core.processors.physics import GENERATION
                    # 从节点中动态获取日主元素（因为可能化气）
                    dm_element = None
                    for node in self.nodes:
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
        if self.use_gat and self.gat_builder is not None:
            # 构建关系类型矩阵
            relation_types = self._build_relation_types_matrix()
            
            # 获取节点能量向量
            node_energies = self.H0.reshape(-1, 1) if self.H0 is not None else np.ones((N, 1))
            
            # 使用 GAT 构建动态邻接矩阵
            A_dynamic = self.gat_builder.build_dynamic_adjacency_matrix(
                nodes=self.nodes,
                node_energies=node_energies,
                relation_types=relation_types,
                base_adjacency=A  # 使用固定矩阵作为先验知识
            )
            
            # 混合固定矩阵和动态矩阵（可配置混合比例）
            gat_mix_ratio = self.config.get('gat', {}).get('gat_mix_ratio', 0.5)  # 默认 50% 动态，50% 固定
            A = (1 - gat_mix_ratio) * A + gat_mix_ratio * A_dynamic
        
        self.adjacency_matrix = A
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
        N = len(self.nodes)
        relation_types = np.zeros((N, N))
        
        from core.processors.physics import GENERATION, CONTROL
        
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
                
                node_i = self.nodes[i]
                node_j = self.nodes[j]
                
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
            if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 1:
                month_branch = self.bazi[1][1] if len(self.bazi[1]) > 1 else None
                # 冬季：亥、子、丑月
                if month_branch in ['亥', '子', '丑']:
                    is_winter = True
            
            # [V58.2] 如果是冬季，且是水生木，增强生成效率（即使水很冷，只要有木，水就会流向木）
            if is_winter and source_element == 'water' and target_element == 'wood':
                # 水生木效率提升 50%
                base_weight *= 1.5
            
            # [V58.2] 当令五行能量加成：如果源元素是当令五行，增强生成效率
            if month_branch:
                month_element = self.BRANCH_ELEMENTS.get(month_branch, 'earth')
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
                    # 计算全局水能量
                    water_energy = 0.0
                    if hasattr(self, 'nodes'):
                        for node in self.nodes:
                            if node.element == 'water':
                                water_energy += node.initial_energy if hasattr(node, 'initial_energy') else node.current_energy
                    
                    # [V59.0] Absolute Climate Boost (绝对润局增幅) - Fix REAL_S_006
                    # 如果水能量 > 3.0（润局），将土生金的增幅提高到 1.5x
                    if water_energy > 3.0:
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
            if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 1:
                month_branch = self.bazi[1][1] if len(self.bazi[1]) > 1 else None
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
                    
                    # 导管容量 = Min(源能量, 通关神能量)
                    conduit_capacity = min(abs(source_energy), mediator_energy)
                    
                    # 如果通关神能量 >= 源能量的 80%，则完全转化
                    # 否则，按比例减少克制力
                    if mediator_energy >= abs(source_energy) * 0.8:
                        # 完全通关：克制力转化为生成力
                        generation_efficiency = flow_config.get('generationEfficiency', 1.2)
                        return 0.3 * generation_efficiency  # 转化为生（正数）
                    elif mediator_energy >= abs(source_energy) * 0.5:
                        # 部分通关：减少 50% 克制力
                        return base_control * 0.5
                    elif mediator_energy >= abs(source_energy) * 0.3:
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
        # 五行生克关系
        # GENERATION: {'wood': 'fire', 'fire': 'earth', 'earth': 'metal', 'metal': 'water', 'water': 'wood'}
        # CONTROL: {'wood': 'earth', 'fire': 'metal', 'earth': 'water', 'metal': 'wood', 'water': 'fire'}
        
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
                    if any(n.element == element for n in self.nodes):
                        return element
        
        return None
    
    def _calculate_mediator_energy(self, mediator_element: str) -> float:
        """
        [V52.0] 计算通关神的能量（导管容量）
        
        返回所有该元素节点的能量总和
        """
        total_energy = 0.0
        for node in self.nodes:
            if node.element == mediator_element:
                # 使用当前能量（如果已计算）或初始能量
                energy = node.current_energy if hasattr(node, 'current_energy') and node.current_energy > 0 else node.initial_energy
                total_energy += abs(energy)
        return total_energy
    
    def _get_node_energy_by_element(self, element: str) -> float:
        """获取指定元素的总能量"""
        total_energy = 0.0
        for node in self.nodes:
            if node.element == element:
                energy = node.current_energy if hasattr(node, 'current_energy') and node.current_energy > 0 else node.initial_energy
                total_energy += abs(energy)
        return total_energy
    
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
                
                # [V58.1] Commander Immunity (提纲免死金牌) - Fix Wu Zetian
                # 检查被冲的节点是否是月令地支（Month Branch）
                is_month_branch_clashed = False
                if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 1:
                    month_branch = self.bazi[1][1] if len(self.bazi[1]) > 1 else None
                    if month_branch and (char1 == month_branch or char2 == month_branch):
                        is_month_branch_clashed = True
                        # 月令被冲：至少保留 80% 能量（普通地支可能只剩 40%）
                        # 调整 clash_damping：从 0.3 提升到 0.8（保留更多能量）
                        clash_damping = max(clash_damping, 0.8)  # 至少保留 80% 能量
                
                # [V57.2] 阳刃金刚盾：检查所有参与冲的地支节点，如果其中一个是日主的阳刃（帝旺位），完全豁免冲的影响
                is_yangren_shielded = False
                if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 2:
                    day_pillar = self.bazi[2]
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
        
        # [V57.2] 识别阳刃节点（在传播前标记，用于保护）
        yangren_node_indices = []
        if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 2:
            day_pillar = self.bazi[2]
            if len(day_pillar) >= 2:
                day_master = day_pillar[0]
                for i, node in enumerate(self.nodes):
                    if node.node_type == 'branch':
                        life_stage = TWELVE_LIFE_STAGES.get((day_master, node.char))
                        if life_stage == '帝旺':
                            yangren_node_indices.append(i)
                            # 标记节点为阳刃
                            node.is_yangren = True
        
        # [V58.2] Commander Absolute Immunity (月令绝对免疫) - Fix Wu Zetian
        # 识别月令节点及其对日主的生助连接
        month_branch_nodes = []
        month_branch_char = None
        if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 1:
            month_branch_char = self.bazi[1][1] if len(self.bazi[1]) > 1 else None
            if month_branch_char:
                # 找到月支节点及其藏干节点
                for i, node in enumerate(self.nodes):
                    if (node.node_type == 'branch' and node.char == month_branch_char and 
                        node.pillar_idx == 1):  # 月支
                        month_branch_nodes.append(i)
                    # 检查藏干节点（如果月支藏干中有生助日主的元素）
                    if node.node_type == 'branch' and node.char == month_branch_char:
                        from core.processors.physics import PhysicsProcessor
                        hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(month_branch_char, [])
                        for hidden_stem, _ in hidden_map:
                            hidden_element = self.STEM_ELEMENTS.get(hidden_stem, 'earth')
                            # 如果藏干元素生助日主（印星或比劫），也标记为月令相关节点
                            from core.processors.physics import GENERATION
                            resource_element = None
                            for elem, target in GENERATION.items():
                                if target == dm_element:
                                    resource_element = elem
                                    break
                            if hidden_element == resource_element or hidden_element == dm_element:
                                # 找到对应的天干节点
                                for j, other_node in enumerate(self.nodes):
                                    if other_node.char == hidden_stem and other_node.node_type == 'stem':
                                        if j not in month_branch_nodes:
                                            month_branch_nodes.append(j)
        
        for iteration in range(max_iterations):
            # 矩阵乘法：能量传播
            H_new = self.adjacency_matrix @ H
            
            # 应用阻尼（防止发散）
            H = damping * H_new + (1 - damping) * self.H0
            
            # [V58.2] Commander Absolute Immunity (月令绝对免疫) - Fix Wu Zetian
            # 确保月令节点对日主的生助权重锁定为 1.0（无损传输）
            if month_branch_nodes and dm_indices and self.adjacency_matrix is not None:
                for month_idx in month_branch_nodes:
                    month_node = self.nodes[month_idx]
                    # 检查月令节点是否生助日主
                    from core.processors.physics import GENERATION
                    resource_element = None
                    for elem, target in GENERATION.items():
                        if target == dm_element:
                            resource_element = elem
                            break
                    
                    # 如果月令节点是印星（生我的）或比劫（同我的），锁定其对日主的生助权重
                    is_helping_dm = (month_node.element == resource_element or 
                                    month_node.element == dm_element)
                    
                    if is_helping_dm:
                        for dm_idx in dm_indices:
                            # 锁定月令对日主的生助权重为 1.0（无损传输）
                            current_weight = self.adjacency_matrix[dm_idx][month_idx]
                            if current_weight > 0:  # 如果是生助关系（正权重）
                                # 强制锁定为 1.0，确保能量无损传输
                                self.adjacency_matrix[dm_idx][month_idx] = max(
                                    current_weight, 1.0
                                )
                            # 如果月令节点能量低于初始能量的 80%，强制恢复到初始能量的 80%
                            if H[month_idx] < self.H0[month_idx] * 0.8:
                                H[month_idx] = self.H0[month_idx] * 0.8
            
            # [V57.2] 阳刃金刚盾：保护阳刃节点，确保能量不被过度削弱
            # [V57.4] 增强：如果阳刃节点被冲，不仅豁免，还要能量加成（越冲越旺）
            for i in yangren_node_indices:
                node = self.nodes[i]
                # 检查是否被冲
                is_clashed = False
                if hasattr(self, 'bazi') and self.bazi:
                    from core.interactions import BRANCH_CLASHES
                    for pillar in self.bazi:
                        if len(pillar) >= 2:
                            other_branch = pillar[1]
                            if BRANCH_CLASHES.get(node.char) == other_branch:
                                is_clashed = True
                                break
                
                if is_clashed:
                    # [V57.4] 阳刃逢冲，其性更烈 - 能量加成 50%
                    H[i] *= 1.5
                else:
                    # 如果阳刃节点能量低于初始能量的 50%，强制恢复到初始能量的 80%
                    if H[i] < self.H0[i] * 0.5:
                        H[i] = self.H0[i] * 0.8
            
            # [V55.0] 处理激活节点的能量变化（流年引动）
            for i, node in enumerate(self.nodes):
                if hasattr(node, 'is_activated') and node.is_activated:
                    activation_factor = getattr(node, 'activation_factor', 1.0)
                    instability_penalty = getattr(node, 'instability_penalty', 0.0)
                    # 能量翻倍，但不稳定性增加
                    H[i] *= activation_factor
                    # 应用不稳定性惩罚（能量波动）
                    if instability_penalty > 0:
                        H[i] *= (1.0 - instability_penalty * np.random.uniform(0.0, 0.2))
            
            # [V55.0] 流年节点能量快速衰减（只管一年）
            for i, node in enumerate(self.nodes):
                if hasattr(node, 'is_liunian') and node.is_liunian:
                    # 每次迭代衰减 10%（快速衰减）
                    H[i] *= 0.9
            
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
        
        # [V57.0] 计算根气状态（用于虚浮比劫惩罚）
        # [V58.3] 检测自刑地支（用于根气惩罚）
        self_punishment_branches = set()
        if hasattr(self, 'bazi') and self.bazi:
            branches = [p[1] for p in self.bazi if len(p) >= 2]
            self_punishments = {'辰', '午', '酉', '亥'}
            branch_counts = {}
            for branch in branches:
                branch_counts[branch] = branch_counts.get(branch, 0) + 1
            for branch, count in branch_counts.items():
                if branch in self_punishments and count >= 2:
                    self_punishment_branches.add(branch)
        
        total_root_energy = 0.0
        from core.processors.physics import PhysicsProcessor
        for node in self.nodes:
            if node.node_type == 'branch':
                branch_char = node.char
                hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
                for hidden_stem, weight in hidden_map:
                    hidden_element = self.STEM_ELEMENTS.get(hidden_stem, 'earth')
                    if hidden_element == dm_element:
                        root_energy = weight * node.current_energy * 0.1
                        # [V58.3] 自刑惩罚：如果地支有自刑，根气贡献乘以 0.2（根源削减）
                        if branch_char in self_punishment_branches:
                            root_energy *= 0.2  # 自刑根气惩罚：只保留 20% 贡献
                        total_root_energy += root_energy
        
        # 累加所有节点的能量
        for node in self.nodes:
            node_energy = node.current_energy
            total_energy += node_energy
            
            # [V57.0] 虚浮比劫惩罚：如果无根，天干比劫的能量贡献大幅降低
            is_peer_stem = False
            if node.element == dm_element and node.node_type == 'stem' and node.pillar_idx != 2:
                # 这是比劫天干（非日主本身）
                is_peer_stem = True
            
            # [V57.2] 阳刃节点能量加成：如果是阳刃节点，能量贡献增加 50%
            if hasattr(node, 'is_yangren') and node.is_yangren:
                node_energy *= 1.5
            
            # 累加日主阵营能量
            if node.element == dm_element:  # Self 或 Peer（同我）
                if is_peer_stem and total_root_energy < 0.5:
                    # [V57.0] 无根比劫惩罚：能量贡献降低到 20%
                    node_energy *= 0.2
                self_team_energy += node_energy
            elif resource_element and node.element == resource_element:  # Resource（生我的）
                self_team_energy += node_energy
        
        # 计算占比分数（0-100）
        if total_energy > 0:
            strength_score = (self_team_energy / total_energy) * 100.0
        else:
            strength_score = 0.0
        
        # [V52.0] 任务 C：显式计算净作用力 (Net Force Calculation)
        # [V54.0] 增强：添加流向检测和顺生加成
        # 在 Phase 3 结束后，显式计算日主受到的净作用力
        net_force_result = self._calculate_net_force(dm_element, resource_element)
        total_push = net_force_result['total_push']  # 印/比（推力）
        total_pull = net_force_result['total_pull']   # 克/泄/耗（拉力）
        net_force_balance = net_force_result['balance_ratio']  # 平衡比例
        
        # [V54.0] 流向加成（Flow Boost）：检查能量是否向日主汇聚
        flow_bonus = net_force_result.get('flow_bonus', 0.0)
        if flow_bonus > 0:
            # 顺流加成：如果能量向日主汇聚，给予额外分数
            strength_score += flow_bonus * 10.0  # 最多加10分
        
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
        
        # [V54.0] 矢量抵消 (Net Force Cancellation) - 增强版
        # 计算净力比：abs(Force_In - Force_Out) / (Force_In + Force_Out)
        force_sum = total_push + total_pull
        if force_sum > 0:
            net_ratio = abs(total_push - total_pull) / force_sum
        else:
            net_ratio = 1.0
        
        # [V10.0] 核心分析师建议：格局极性锁定
        # 禁用净力抵消对极弱格局的干预
        # 如果 strength_normalized < 0.45 且日主根基虚脱，强制锁定为 Weak 或 Extreme_Weak
        normalized_score_before_override = strength_score / 100.0
        is_extreme_weak_candidate = normalized_score_before_override < 0.45
        
        # 如果净力差小于 15%（净力差小于 15%），强制判定为动态平衡
        net_force_threshold = 0.15  # 15% 容差
        if net_ratio < net_force_threshold:
            # [V10.0] 格局极性锁定：极弱格局不受净力抵消机制影响
            if is_extreme_weak_candidate:
                # 极弱格局：保持 Weak 标签，不应用净力抵消
                # 但可以轻微修正分数（不超过阈值）
                if strength_label == "Weak":
                    # 保持 Weak，不强制改为 Balanced
                    net_force_override = False
                else:
                    # 如果原本是 Balanced，但归一化值 < 0.45，强制改为 Weak
                    strength_label = "Weak"
                    net_force_override = False
            else:
                # 非极弱格局：正常应用净力抵消机制
                # 推力与拉力接近平衡，强制判定为 Balanced
                # 同时修正分数：向 0.5 (Balanced) 拉拢
                normalized_score = strength_score / 100.0  # 归一化到 0-1
                balanced_score = 0.5 + (normalized_score - 0.5) * 0.5  # 衰减偏离度
                strength_score = balanced_score * 100.0  # 转回 0-100
                strength_label = "Balanced"
                net_force_override = True
        else:
            net_force_override = False
        
        # [V10.0] 极弱格局最终确认：如果归一化值 < 0.45，强制为 Weak
        if normalized_score_before_override < 0.45 and strength_label != "Weak":
            strength_label = "Weak"
        
        # [V40.0] 特殊格局检测：专旺格/从旺格
        special_pattern = self._detect_special_pattern(dm_element, strength_score)
        if special_pattern:
            strength_label = special_pattern  # 覆盖为 "Special_Strong"
        
        # [V9.3 MCP] 计算格局不确定性
        uncertainty = self._calculate_pattern_uncertainty(
            strength_score, strength_label, self.bazi if hasattr(self, 'bazi') else [], dm_element, special_pattern
        )
        
        return {
            'strength_score': strength_score,
            'strength_label': strength_label,
            'self_team_energy': self_team_energy,
            'total_energy': total_energy,
            'dm_element': dm_element,
            'resource_element': resource_element,
            'special_pattern': special_pattern if special_pattern else None,
            # [V52.0] 净作用力信息
            'net_force': {
                'total_push': total_push,
                'total_pull': total_pull,
                'balance_ratio': net_force_balance,
                'override': net_force_override
            },
            # [V9.3 MCP] 格局不确定性
            'uncertainty': self._calculate_pattern_uncertainty(
                strength_score, strength_label, self.bazi if hasattr(self, 'bazi') else [], dm_element, special_pattern
            )
        }
    
    def _calculate_pattern_uncertainty(self, strength_score: float, strength_label: str, 
                                       bazi: List[str], dm_element: str, 
                                       special_pattern: Optional[str]) -> Dict[str, Any]:
        """
        [V9.3 MCP] 计算格局不确定性
        
        针对极弱格局或多冲格局，计算转化为从格的概率和预测结果的波动范围。
        
        Args:
            strength_score: 身强分数 (0-100)
            strength_label: 身强标签
            bazi: 八字列表
            dm_element: 日主元素
            special_pattern: 特殊格局（如果有）
            
        Returns:
            Dict containing:
            - has_uncertainty: 是否有不确定性
            - pattern_type: 格局类型
            - follower_probability: 转化为从格的概率 (0-1)
            - volatility_range: 预测结果波动范围
            - warning_message: 警告消息
        """
        uncertainty = {
            'has_uncertainty': False,
            'pattern_type': 'Normal',
            'follower_probability': 0.0,
            'volatility_range': 0.0,
            'warning_message': ''
        }
        
        # 检查极弱格局
        is_extreme_weak = strength_score < 30.0 and strength_label in ['Weak', 'Very_Weak']
        
        # 检查多冲格局（计算冲的数量）
        clash_count = 0
        clashes = {'子': '午', '午': '子', '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
                   '辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
        if bazi and len(bazi) >= 2:
            branches = [p[1] for p in bazi if len(p) >= 2]
            clash_pairs = set()
            for i, b1 in enumerate(branches):
                for j, b2 in enumerate(branches):
                    if i != j and clashes.get(b1) == b2:
                        pair = tuple(sorted([b1, b2]))
                        clash_pairs.add(pair)
            clash_count = len(clash_pairs)
        
        is_multi_clash = clash_count >= 2
        
        # 计算不确定性
        if is_extreme_weak:
            uncertainty['has_uncertainty'] = True
            uncertainty['pattern_type'] = 'Extreme_Weak'
            # 极弱格局：根据强度分数计算转化为从格的概率
            # 分数越低，转化概率越高
            uncertainty['follower_probability'] = max(0.0, min(1.0, (30.0 - strength_score) / 30.0 * 0.5))
            uncertainty['volatility_range'] = 40.0  # 预测结果可能波动 ±40分
            uncertainty['warning_message'] = f"⚠️ **极弱格局警告**: 身强分数 {strength_score:.1f}，有 {uncertainty['follower_probability']*100:.0f}% 概率转化为从格，预测结果存在较大波动（±{uncertainty['volatility_range']:.0f}分）。"
        
        elif is_multi_clash:
            uncertainty['has_uncertainty'] = True
            uncertainty['pattern_type'] = 'Multi_Clash'
            # 多冲格局：冲越多，不确定性越高
            uncertainty['follower_probability'] = min(0.4, clash_count * 0.15)
            uncertainty['volatility_range'] = clash_count * 15.0  # 每个冲增加15分波动
            uncertainty['warning_message'] = f"⚠️ **多冲格局警告**: 检测到 {clash_count} 对相冲，格局不稳定，预测结果存在波动（±{uncertainty['volatility_range']:.0f}分）。"
        
        elif special_pattern == 'Special_Follow':
            uncertainty['has_uncertainty'] = True
            uncertainty['pattern_type'] = 'Follower_Grid'
            uncertainty['follower_probability'] = 0.8  # 已是从格，但可能转化回正常格局
            uncertainty['volatility_range'] = 30.0
            uncertainty['warning_message'] = f"ℹ️ **从格格局**: 已识别为从格，预测结果相对稳定，但需注意流年大运变化可能导致格局转化。"
        
        return uncertainty
    
    def _calculate_net_force(self, dm_element: str, resource_element: Optional[str]) -> Dict[str, float]:
        """
        [V52.0] 任务 C：显式计算日主受到的净作用力 (Net Force Calculation)
        
        在 Phase 3 传播结束后，显式计算日主受到的：
        - Total_Push (推力): 印星（生我）+ 比劫（同我）
        - Total_Pull (拉力): 官杀（克我）+ 食伤（我生）+ 财星（我克）
        
        如果推力与拉力差值小于阈值，判定为"受力平衡态"（Balanced）。
        
        Args:
            dm_element: 日主元素
            resource_element: 资源元素（生我的元素）
        
        Returns:
            包含 total_push, total_pull, balance_ratio 的字典
        """
        from core.processors.physics import GENERATION, CONTROL
        
        # 找到日主节点索引
        dm_indices = []
        for i, node in enumerate(self.nodes):
            if node.element == dm_element and node.pillar_idx == 2 and node.node_type == 'stem':
                dm_indices.append(i)
        
        if not dm_indices:
            # 如果找不到日主节点，返回零值
            return {
                'total_push': 0.0,
                'total_pull': 0.0,
                'balance_ratio': 0.0
            }
        
        # 确定十神关系
        # Push (推力): Resource (印星) + Self (比劫)
        # Pull (拉力): Officer (官杀) + Output (食伤) + Wealth (财星)
        
        # 确定各元素关系
        output_element = GENERATION.get(dm_element)  # 我生的（食伤）
        wealth_element = CONTROL.get(dm_element)    # 我克的（财星）
        officer_element = None  # 克我的（官杀）
        for attacker, defender in CONTROL.items():
            if defender == dm_element:
                officer_element = attacker
                break
        
        total_push = 0.0  # 推力（印 + 比）
        total_pull = 0.0  # 拉力（官杀 + 食伤 + 财）
        
        # 遍历所有节点，计算它们对日主的净作用力
        for i, node in enumerate(self.nodes):
            if i in dm_indices:
                continue  # 跳过日主自己
            
            node_energy = node.current_energy
            if node_energy <= 0:
                continue
            
            # 获取邻接矩阵中的权重（节点 i 对日主的影响）
            # A[dm_idx][i] 表示节点 i 对日主的影响
            # 正数 = 推力（生/合），负数 = 拉力（克/冲）
            force_weight = 0.0
            for dm_idx in dm_indices:
                if dm_idx < len(self.nodes) and i < len(self.nodes) and self.adjacency_matrix is not None:
                    # 注意：邻接矩阵 A[i][j] 表示 j 对 i 的影响
                    # 所以 A[dm_idx][i] 表示节点 i 对日主的影响
                    force_weight += self.adjacency_matrix[dm_idx][i]
            
            # 根据元素关系和权重符号分类计算作用力
            # 使用节点能量 × 权重绝对值作为作用力大小
            force_magnitude = node_energy * abs(force_weight) if abs(force_weight) > 0.01 else node_energy * 0.1
            
            if node.element == dm_element:
                # 比劫（同我）- 推力（同元素共振）
                total_push += force_magnitude
            elif resource_element and node.element == resource_element:
                # 印星（生我）- 推力
                if force_weight > 0:  # 生关系（正权重）
                    total_push += force_magnitude
                else:
                    # 即使权重为负，印星本身也是推力（只是可能被其他因素削弱）
                    total_push += node_energy * 0.3
            elif officer_element and node.element == officer_element:
                # 官杀（克我）- 拉力
                if force_weight < 0:  # 克关系（负权重）
                    total_pull += force_magnitude
                else:
                    # 即使权重为正，官杀本身也是拉力
                    total_pull += node_energy * 0.3
            elif output_element and node.element == output_element:
                # 食伤（我生）- 拉力（泄气）
                # 食伤会消耗日主能量，所以是拉力
                if force_weight > 0:  # 生关系（日主生食伤）
                    total_pull += force_magnitude * 0.8  # 泄气系数
                else:
                    total_pull += node_energy * 0.2
            elif wealth_element and node.element == wealth_element:
                # 财星（我克）- 拉力（耗气）
                # 克财星会消耗日主能量，所以是拉力
                if force_weight < 0:  # 克关系（日主克财）
                    total_pull += force_magnitude * 0.6  # 耗气系数
                else:
                    total_pull += node_energy * 0.2
        
        # 计算平衡比例：如果推力与拉力接近，比例接近0
        total_force = total_push + total_pull
        if total_force > 0:
            balance_ratio = (total_push - total_pull) / total_force
        else:
            balance_ratio = 0.0
        
        # [V54.0] 流向检测（Directional Flow Detection）
        # 检查能量流向是否为 Year -> Month -> Day -> Hour (顺流)
        flow_bonus = 0.0
        pillar_energies = {}
        for i, node in enumerate(self.nodes):
            if node.pillar_name in ['year', 'month', 'day', 'hour']:
                pillar_energies[node.pillar_name] = node.current_energy
        
        # 检查是否顺流（能量向日主汇聚）
        if len(pillar_energies) >= 3:
            year_e = pillar_energies.get('year', 0.0)
            month_e = pillar_energies.get('month', 0.0)
            day_e = pillar_energies.get('day', 0.0)
            hour_e = pillar_energies.get('hour', 0.0)
            
            # 如果 Year > Month > Day（能量向日主汇聚），给予加成
            if year_e > month_e and month_e > day_e:
                # 计算汇聚强度
                convergence_ratio = (year_e - day_e) / max(year_e, 1.0)
                if convergence_ratio > 0.2:  # 汇聚明显
                    flow_bonus = min(convergence_ratio, 0.3)  # 最多30%加成
        
        return {
            'total_push': total_push,
            'total_pull': total_pull,
            'balance_ratio': balance_ratio,
            'flow_bonus': flow_bonus
        }
    
    def _detect_special_pattern(self, dm_element: str, strength_score: float) -> Optional[str]:
        """
        [V40.0] 检测特殊格局：专旺格/从旺格/阳刃格
        
        判定条件：
        1. 全盘中能量最大的五行占比 > 65%（某一行独大）
        2. 日主强度分数 > 80.0（极强）
        3. [V57.0] 阳刃格：日支为日主帝旺位
        
        如果满足，返回 "Special_Strong"，表示这是合法的专旺/从旺格局。
        
        Args:
            dm_element: 日主元素
            strength_score: 强度分数
        
        Returns:
            "Special_Strong" 如果检测到特殊格局，否则 None
        """
        # [V57.0] 阳刃格检测：检查所有地支，如果其中一个是日主的帝旺位，判定为阳刃格
        # [V58.0] 修复：不仅检查日支，还要检查所有地支（如乾隆的酉在月支）
        if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 2:
            day_pillar = self.bazi[2]
            if len(day_pillar) >= 2:
                day_master = day_pillar[0]
                # 检查所有地支，看是否有阳刃（帝旺位）
                has_yangren = False
                yangren_branch = None
                for pillar in self.bazi:
                    if len(pillar) >= 2:
                        branch = pillar[1]
                        life_stage = TWELVE_LIFE_STAGES.get((day_master, branch))
                        if life_stage == '帝旺':
                            has_yangren = True
                            yangren_branch = branch
                            break
                
                if has_yangren:
                    # [V58.0] 检查是否有自刑（羊刃倒戈的特殊情况）
                    # 如果阳刃地支出现两次或以上，可能是自刑，需要进一步判断
                    branches = [p[1] for p in self.bazi if len(p) >= 2]
                    self_punishments = {'辰', '午', '酉', '亥'}
                    has_self_punishment = yangren_branch in self_punishments and branches.count(yangren_branch) >= 2
                    
                    if has_self_punishment:
                        # [V57.4] 羊刃倒戈：虽然根气强，但因为自刑，不能算阳刃格
                        # 如果 Force Out 远大于 Force In，判定为倒戈（弱格）
                        # 暂时只检查分数：如果分数较低（< 45%），判定为倒戈
                        if strength_score < 45.0:
                            return None
                    
                    # [V57.0] 检查是否是"羊刃倒戈"（特殊弱格）
                    # 羊刃倒戈特征：虽然根气强，但 Force Out 远大于 Force In
                    # 注意：这里无法直接获取 net_force，需要从外部传入或延迟判断
                    # 暂时只检查分数：如果分数极低（< 20%），可能是倒戈，不判定为阳刃格
                    if strength_score < 20.0:
                        # 可能是羊刃倒戈，不判定为阳刃格
                        return None
                    # 阳刃格：即使分数较低，也应判定为 Strong（抗杀格）
                    return "Special_Strong"
        
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
            # [V58.0] 检查是否有自刑或冲克（格局不纯，不能算专旺）
            has_instability = False
            if hasattr(self, 'bazi') and self.bazi:
                branches = [p[1] for p in self.bazi if len(p) >= 2]
                # 自刑检测：辰、午、酉、亥出现两次或以上
                self_punishments = {'辰', '午', '酉', '亥'}
                for branch in self_punishments:
                    if branches.count(branch) >= 2:
                        has_instability = True
                        break
                
                # 冲克检测：如果存在六冲，格局不纯
                if not has_instability:
                    from core.interactions import BRANCH_CLASHES
                    clash_pairs = set()
                    for i, b1 in enumerate(branches):
                        for j, b2 in enumerate(branches):
                            if i != j and BRANCH_CLASHES.get(b1) == b2:
                                clash_pairs.add(tuple(sorted([b1, b2])))
                    if len(clash_pairs) >= 2:  # 如果有2对或以上的冲，视为格局不纯
                        has_instability = True
            
            # 如果有自刑或严重冲克，不能算专旺格
            if has_instability:
                # 即使能量很强，但因为自刑/冲克，不能算专旺，只能算普通身强（甚至因为内耗变弱）
                return None
            
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
    
    def _apply_self_punishment_damping(self, day_master: str):
        """
        [V57.4] 自刑内耗惩罚（Self-Punishment Damping）
        
        在能量传播之前，从源头削减自刑地支的能量，模拟内耗。
        
        自刑地支：辰、午、酉、亥
        如果某个自刑地支出现 >= 2 次，所有属于该地支的节点能量削减 60%。
        
        Args:
            day_master: 日主天干
        """
        if not hasattr(self, 'bazi') or not self.bazi:
            return
        
        # 统计地支出现次数
        branches = [p[1] for p in self.bazi if len(p) >= 2]
        branch_counts = {}
        for branch in branches:
            branch_counts[branch] = branch_counts.get(branch, 0) + 1
        
        # 自刑地支组
        self_punishments = {'辰', '午', '酉', '亥'}
        
        # 检查每个自刑地支
        for branch, count in branch_counts.items():
            if branch in self_punishments and count >= 2:
                # [V57.4] 根据自刑次数调整惩罚强度
                # 2次：削减 50% (0.5)
                # 3次：削减 70% (0.3)
                # 4次：削减 80% (0.2)
                if count == 2:
                    penalty_factor = 0.5
                elif count == 3:
                    penalty_factor = 0.3
                else:  # count >= 4
                    penalty_factor = 0.2
                
                # 找到所有属于该地支的节点（主能量和藏干）
                for node in self.nodes:
                    if node.node_type == 'branch' and node.char == branch:
                        # 主能量削减
                        original_energy = node.initial_energy
                        node.initial_energy *= penalty_factor
                        node.current_energy = node.initial_energy  # 同步更新当前能量
                        
                        # 更新 H0 向量
                        if self.H0 is not None:
                            self.H0[node.node_id] = node.initial_energy
                        
                        # 记录日志
                        if not hasattr(node, 'trigger_events'):
                            node.trigger_events = []
                        penalty_pct = int((1.0 - penalty_factor) * 100)
                        node.trigger_events.append(f"⚔️ 自刑内耗: {branch}x{count}, 能量折损 {penalty_pct}%")
        
        # 同时更新 H0 向量中所有相关节点的能量
        if self.H0 is not None:
            for i, node in enumerate(self.nodes):
                if i < len(self.H0):
                    self.H0[i] = node.initial_energy
    
    def _apply_mediation_logic(self, day_master: str):
        """
        [V54.0] 通关逻辑（Mediation Logic）
        
        当存在克制关系 (A -> 克 -> B) 时，如果存在中间节点 C (A -> 生 -> C -> 生 -> B)，
        则克制关系应转化为相生关系（官印相生）。
        
        实现：
        1. 扫描所有指向日主的强克制边（官杀）
        2. 寻找通关神（印星），检查是否存在路径：克神 -> 生 -> 印星 -> 生 -> 日主
        3. 如果满足，将克制权重减弱，增强生印的力量
        """
        from core.processors.physics import GENERATION, CONTROL
        
        # 获取日主元素
        dm_element = self.STEM_ELEMENTS.get(day_master, 'metal')
        
        # 找到日主节点索引
        dm_indices = []
        for i, node in enumerate(self.nodes):
            if node.element == dm_element and node.pillar_idx == 2 and node.node_type == 'stem':
                dm_indices.append(i)
        
        if not dm_indices or self.adjacency_matrix is None:
            return
        
        # 确定资源元素（印星，生我的）
        resource_element = None
        for elem, target in GENERATION.items():
            if target == dm_element:
                resource_element = elem
                break
        
        # 确定官杀元素（克我的）
        officer_element = None
        for attacker, defender in CONTROL.items():
            if defender == dm_element:
                officer_element = attacker
                break
        
        if not resource_element or not officer_element:
            return
        
        # 找到所有官杀节点（克我的）
        officer_nodes = []
        resource_nodes = []
        for i, node in enumerate(self.nodes):
            if node.element == officer_element:
                officer_nodes.append(i)
            elif node.element == resource_element:
                resource_nodes.append(i)
        
        # 对每个官杀节点，检查是否存在通关路径
        for officer_idx in officer_nodes:
            # 检查官杀对日主的直接克制权重
            for dm_idx in dm_indices:
                kill_weight = self.adjacency_matrix[dm_idx][officer_idx]
                
                # [V59.0] 降低阈值以识别更多通关情况（特别是透干印星）
                # 如果克制权重为负（即使很小，只要有克制，就应该检查通关）
                # 或者如果存在透干印星，强制检查通关（即使克制权重很小）
                has_exposed_resource = any(
                    node.node_type == 'stem' and node.element == resource_element 
                    for node in self.nodes
                )
                
                # 如果克制权重为负，或者存在透干印星，都应该检查通关
                if kill_weight < -0.01 or (has_exposed_resource and kill_weight < 0):
                    # 寻找印星节点，检查是否存在通关路径
                    best_resource_idx = None
                    best_mediation_strength = 0.0
                    
                    for resource_idx in resource_nodes:
                        # 检查路径：官杀 -> 生 -> 印星 -> 生 -> 日主
                        # 1. 官杀生印星（官杀 -> 印星）
                        kill_to_resource = self.adjacency_matrix[resource_idx][officer_idx]
                        # 2. 印星生日主（印星 -> 日主）
                        resource_to_dm = self.adjacency_matrix[dm_idx][resource_idx]
                        
                        # [V59.0] 降低阈值以识别更多通关情况（特别是透干印星）
                        # 对于透干印星，路径权重阈值应该更低（0.01），因为透干印星转化效率高
                        resource_node = self.nodes[resource_idx]
                        is_exposed = resource_node.node_type == 'stem'  # 天干即为透干
                        
                        # 透干印星：路径权重阈值降低到 0.01（从 0.05 降低）
                        # 非透干印星：保持原阈值 0.05
                        path_threshold = 0.01 if is_exposed else 0.05
                        
                        # 如果两条路径都存在（权重为正），说明有通关
                        if kill_to_resource > path_threshold and resource_to_dm > path_threshold:
                            # [V58.3] 检查印星是否透干（透干印星忽略 Capacity Check）
                            resource_node = self.nodes[resource_idx]
                            is_exposed = resource_node.node_type == 'stem'  # 天干即为透干
                            
                            # 计算通关强度（取两条路径的最小值）
                            mediation_strength = min(kill_to_resource, resource_to_dm)
                            # 还要考虑印星的能量（有气才能通关）
                            resource_energy = self.nodes[resource_idx].current_energy
                            kill_energy = self.nodes[officer_idx].current_energy
                            
                            # [V58.3] 透干印星：忽略 Capacity Check 限制（转化效率高）
                            if is_exposed:
                                # 透干印星：直接计算通关强度，不检查容量
                                # 透干印星转化效率大幅提升（2.0倍），确保能触发通关
                                total_strength = mediation_strength * 2.0  # 透干印星转化效率提升（从1.5提升到2.0）
                                if total_strength > best_mediation_strength:
                                    best_mediation_strength = total_strength
                                    best_resource_idx = resource_idx
                            else:
                                # [V54.0] Capacity Check: 非透干印星能量必须足够大（>= 克制能量的 30%）
                                # 否则通关失败（水多木漂/土多金埋）
                                capacity_threshold = kill_energy * 0.3
                                if resource_energy >= capacity_threshold:
                                    # 计算通关强度（考虑容量）
                                    total_strength = mediation_strength * min(1.0, resource_energy / max(kill_energy, 1.0))
                                    if total_strength > best_mediation_strength:
                                        best_mediation_strength = total_strength
                                        best_resource_idx = resource_idx
                    
                    # [V57.0] 降低阈值以识别更多通关情况
                    # [V58.3] 对于透干印星，进一步降低阈值（透干印星转化效率高，即使路径权重较小也能通关）
                    resource_node = None
                    is_exposed_mediation = False
                    if best_resource_idx is not None:
                        resource_node = self.nodes[best_resource_idx]
                        is_exposed_mediation = resource_node.node_type == 'stem'  # 天干即为透干
                    
                    # [V59.0] 透干印星：阈值降低到 0.01（从 0.05 进一步降低）
                    # 非透干印星：保持原阈值 0.1
                    mediation_threshold = 0.01 if is_exposed_mediation else 0.1
                    
                    # 如果找到通关路径，重构拓扑
                    if best_resource_idx is not None and best_mediation_strength > mediation_threshold:
                        # [V57.0] 检查印星是否透干（提升转化效率）
                        resource_node = self.nodes[best_resource_idx]
                        is_exposed = resource_node.node_type == 'stem'  # 天干即为透干
                        
                        # [V59.0] Absolute Mediation Boost (绝对通关转化) - Fix REAL_B_011
                        # 如果通关神是透干印星，强制提升转化效率到 3.0x，直接克制削减到 0.01
                        if is_exposed:
                            # 1. [V59.0] 绝对削弱直接克制（官杀 -> 日主）：削减到 0.01（几乎完全切断）
                            self.adjacency_matrix[dm_idx][officer_idx] *= 0.01
                            
                            # 2. [V59.0] 透干印星：强制提升转化效率到 3.0（绝对转化）
                            # 同时增强印星生日主的权重
                            self.adjacency_matrix[best_resource_idx][officer_idx] *= 3.0  # 官杀 -> 印星
                            self.adjacency_matrix[dm_idx][best_resource_idx] *= 1.5  # 印星 -> 日主（额外增强）
                            
                            # [V59.0] Log: 记录绝对通关
                            officer_char = self.nodes[officer_idx].char
                            resource_char = self.nodes[best_resource_idx].char
                            dm_char = self.nodes[dm_idx].char
                            if not hasattr(self.nodes[best_resource_idx], 'trigger_events'):
                                self.nodes[best_resource_idx].trigger_events = []
                            self.nodes[best_resource_idx].trigger_events.append(
                                f"🌉 绝对通关: 透干印星 {resource_char} 启动 ({officer_char} -> {resource_char} -> {dm_char})"
                            )
                        else:
                            # 非透干印星：使用原有逻辑
                            # 1. 大幅削弱直接克制（官杀 -> 日主）
                            self.adjacency_matrix[dm_idx][officer_idx] *= 0.2
                            
                            # 2. 增强生印的力量（官杀 -> 印星）
                            self.adjacency_matrix[best_resource_idx][officer_idx] *= 1.5
                            
                            # Log: 记录通关成功
                            officer_char = self.nodes[officer_idx].char
                            resource_char = self.nodes[best_resource_idx].char
                            dm_char = self.nodes[dm_idx].char
                            if not hasattr(self.nodes[best_resource_idx], 'trigger_events'):
                                self.nodes[best_resource_idx].trigger_events = []
                            self.nodes[best_resource_idx].trigger_events.append(
                                f"🌉 通关成功: {officer_char} -> {resource_char} -> {dm_char}"
                            )
                        
                        # 也在日主节点记录
                        if not hasattr(self.nodes[dm_idx], 'trigger_events'):
                            self.nodes[dm_idx].trigger_events = []
                        officer_char = self.nodes[officer_idx].char
                        resource_char = self.nodes[best_resource_idx].char
                        dm_char = self.nodes[dm_idx].char
                        self.nodes[dm_idx].trigger_events.append(
                            f"🌉 官印相生: {officer_char}生{resource_char}生{dm_char}"
                        )
    
    def _detect_officer_resource_mediation(self, day_master: str, luck_pillar: str = None, year_pillar: str = None):
        """
        [V55.0] 检测官印相生（流年/大运的官杀通过印星通关）
        
        特别处理：如果流年是官杀，大运是印星，形成官印相生，大幅加分
        """
        from core.processors.physics import GENERATION, CONTROL
        
        # 获取日主元素
        dm_element = self.STEM_ELEMENTS.get(day_master, 'metal')
        
        # 确定官杀元素和印星元素
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
        
        if not officer_element or not resource_element:
            return
        
        # 检查流年是否是官杀
        year_is_officer = False
        if year_pillar and len(year_pillar) >= 2:
            year_stem = year_pillar[0]
            year_stem_element = self.STEM_ELEMENTS.get(year_stem, 'earth')
            if year_stem_element == officer_element:
                year_is_officer = True
        
        # 检查大运是否是印星
        luck_is_resource = False
        if luck_pillar and len(luck_pillar) >= 2:
            luck_stem = luck_pillar[0]
            luck_branch = luck_pillar[1]
            luck_stem_element = self.STEM_ELEMENTS.get(luck_stem, 'earth')
            luck_branch_element = self.BRANCH_ELEMENTS.get(luck_branch, 'earth')
            if luck_stem_element == resource_element or luck_branch_element == resource_element:
                luck_is_resource = True
        
        # 如果流年是官杀，大运是印星，形成官印相生
        if year_is_officer and luck_is_resource:
            # 找到日主节点，记录官印相生事件
            for node in self.nodes:
                if node.pillar_idx == 2 and node.node_type == 'stem' and node.char == day_master:
                    node.trigger_events = getattr(node, 'trigger_events', [])
                    node.trigger_events.append("官印相生(流年官杀+大运印星)")
                    # 大幅提升日主能量
                    node.activation_factor = getattr(node, 'activation_factor', 1.0) * 1.8
                    break
    
    def _add_dayun_support_links(self, A: np.ndarray):
        """
        [V55.0] 添加大运的 Support Link（静态叠加）
        
        大运节点与原局日主及所有同五行/相生节点建立"Support Link"（静态能量注入）。
        物理含义：改变背景场域（如进入火运，全局火能量底噪提升）。
        """
        from core.processors.physics import GENERATION
        
        # 找到大运节点
        dayun_nodes = []
        for i, node in enumerate(self.nodes):
            if hasattr(node, 'dayun_weight'):
                dayun_nodes.append(i)
        
        if not dayun_nodes:
            return
        
        # 找到日主节点
        dm_indices = []
        for i, node in enumerate(self.nodes):
            if node.pillar_idx == 2 and node.node_type == 'stem':
                dm_indices.append(i)
        
        # 大运节点对所有原局节点建立 Support Link
        for dayun_idx in dayun_nodes:
            dayun_node = self.nodes[dayun_idx]
            dayun_element = dayun_node.element
            
            for i, natal_node in enumerate(self.nodes):
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
        from core.interactions import BRANCH_CLASHES, STEM_COMBINATIONS
        
        # 找到流年节点
        liunian_nodes = []
        for i, node in enumerate(self.nodes):
            if hasattr(node, 'is_liunian') and node.is_liunian:
                liunian_nodes.append(i)
        
        if not liunian_nodes:
            return
        
        # 找到流年地支节点（用于冲合判定）
        liunian_branch_idx = None
        liunian_stem_idx = None
        for idx in liunian_nodes:
            node = self.nodes[idx]
            if node.node_type == 'branch':
                liunian_branch_idx = idx
            elif node.node_type == 'stem':
                liunian_stem_idx = idx
        
        # 1. 流年地支冲原局/大运地支（引动）
        if liunian_branch_idx is not None:
            liunian_branch = self.nodes[liunian_branch_idx].char
            
            for i, node in enumerate(self.nodes):
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
                            
                            if storage_energy >= vault_threshold:
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
                        if len(self.bazi) > 1 and len(self.bazi[1]) > 1:
                            month_branch_in_bazi = self.bazi[1][1]
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
                            for dm_node in self.nodes:
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
            liunian_stem = self.nodes[liunian_stem_idx].char
            liunian_stem_element = self.nodes[liunian_stem_idx].element
            
            for i, node in enumerate(self.nodes):
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
                    for dm_node in self.nodes:
                        if dm_node.pillar_idx == 2 and dm_node.node_type == 'stem':
                            dm_element = dm_node.element
                            from core.processors.physics import GENERATION, CONTROL
                            
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
                                for res_node in self.nodes:
                                    if res_node.element == resource_element:
                                        # 官印相生：加分
                                        node.trigger_events.append(f"官印相生")
                                        break
                            break
        
        # 3. [V55.0] 检测流年地支为日主强根（帝旺、临官等）
        if liunian_branch_idx is not None:
            liunian_branch = self.nodes[liunian_branch_idx].char
            
            # 找到日主节点（需要从 analyze 方法传入 day_master）
            # 这里我们需要从节点中找到日主
            day_master_char = None
            for node in self.nodes:
                if node.pillar_idx == 2 and node.node_type == 'stem':
                    day_master_char = node.char
                    break
            
            if day_master_char:
                # 检查流年地支是否为日主的强根
                life_stage = TWELVE_LIFE_STAGES.get((day_master_char, liunian_branch))
                
                if life_stage in ['帝旺', '临官', '长生']:
                    # 找到日主节点索引
                    for i, node in enumerate(self.nodes):
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
            liunian_node = self.nodes[liunian_idx]
            liunian_element = liunian_node.element
            
            for i, node in enumerate(self.nodes):
                if i == liunian_idx:
                    continue
                
                # 流年对所有节点都有基础影响（但权重较小）
                # 这个影响会在传播中体现
                if abs(A[i][liunian_idx]) < 0.1:  # 如果没有其他关系
                    # 根据五行关系添加基础权重
                    from core.processors.physics import GENERATION, CONTROL
                    if GENERATION.get(liunian_element) == node.element:
                        A[i][liunian_idx] += 0.2  # 流年生原局
                    elif CONTROL.get(liunian_element) == node.element:
                        A[i][liunian_idx] -= 0.2  # 流年克原局
    
    def _detect_follower_grid(self, day_master: str, strength_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        [V54.0] 从格判定（Follower Grid Detection）
        
        当日主极弱且无根，且某一种异党五行极强时，判定为从格（Follower），视为"假强"。
        
        判定条件：
        1. 日主几乎无根（rooting_score < 0.5）
        2. 异党（财/官/食）能量占比 > 65%
        3. 日主强度分数 < 30.0（极弱）
        
        如果满足，返回 "Special_Strong"（从旺/从格），表示这是一种特殊的强格局。
        
        Args:
            day_master: 日主天干
            strength_data: 强度数据（包含 strength_score, self_team_energy, total_energy 等）
        
        Returns:
            如果检测到从格，返回 {'label': 'Special_Strong', 'reason': 'Follower Grid'}，否则 None
        """
        from core.processors.physics import GENERATION, CONTROL
        
        # 获取日主元素
        dm_element = self.STEM_ELEMENTS.get(day_master, 'metal')
        
        # [V57.0] 例外处理：阳刃格不应被判定为从格
        # 阳刃格特征：日支为日主的帝旺位（如庚午、甲卯等）
        is_yangren = False
        if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 2:
            day_pillar = self.bazi[2]
            if len(day_pillar) >= 2:
                day_branch = day_pillar[1]
                life_stage = TWELVE_LIFE_STAGES.get((day_master, day_branch))
                if life_stage == '帝旺':
                    is_yangren = True
        
        # [V57.0] 例外处理：羊刃倒戈（特殊弱格）
        # 特征：日支是帝旺，但 Force Out 远大于 Force In，且 Ratio < 30%
        is_yangren_daoge = False
        if is_yangren:
            net_force = strength_data.get('net_force', {})
            force_in = net_force.get('total_push', 0.0)
            force_out = net_force.get('total_pull', 0.0)
            strength_score = strength_data.get('strength_score', 0.0)
            if force_out > force_in * 3.0 and strength_score < 30.0:
                # 羊刃倒戈：虽然根气强，但被严重克制
                is_yangren_daoge = True
        
        # 如果是阳刃格且不是倒戈，直接返回 None（不应判定为从格）
        if is_yangren and not is_yangren_daoge:
            return None
        
        # 条件1：检查日主强度（必须极弱）
        strength_score = strength_data.get('strength_score', 0.0)
        if strength_score >= 30.0:
            return None  # 不够弱，不是从格
        
        # 条件2：检查通根（必须几乎无根）
        # [V54.0] 计算日主在地支中的根气（Total_Root_Energy）
        # 包括：1) 地支藏干中的日主同五行 2) 十二长生强根位置
        from core.processors.physics import PhysicsProcessor
        
        total_root_energy = 0.0
        
        # 方法1：检查地支藏干中的日主同五行
        # [V58.3] 检测自刑地支（用于根气惩罚）
        self_punishment_branches = set()
        if hasattr(self, 'bazi') and self.bazi:
            branches = [p[1] for p in self.bazi if len(p) >= 2]
            self_punishments = {'辰', '午', '酉', '亥'}
            branch_counts = {}
            for branch in branches:
                branch_counts[branch] = branch_counts.get(branch, 0) + 1
            for branch, count in branch_counts.items():
                if branch in self_punishments and count >= 2:
                    self_punishment_branches.add(branch)
        
        for node in self.nodes:
            if node.node_type == 'branch':
                branch_char = node.char
                # 获取地支藏干
                hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
                for hidden_stem, weight in hidden_map:
                    hidden_element = self.STEM_ELEMENTS.get(hidden_stem, 'earth')
                    if hidden_element == dm_element:
                        # [V57.0] 根气抗冲：如果是临官/帝旺位，即使被冲也不打折
                        life_stage = TWELVE_LIFE_STAGES.get((day_master, branch_char))
                        is_strong_root = life_stage in ['临官', '帝旺']
                        
                        # 检查是否被冲
                        is_clashed = False
                        if hasattr(self, 'bazi') and self.bazi:
                            from core.interactions import BRANCH_CLASHES
                            for pillar in self.bazi:
                                if len(pillar) >= 2:
                                    other_branch = pillar[1]
                                    if BRANCH_CLASHES.get(branch_char) == other_branch:
                                        is_clashed = True
                                        break
                        
                        # [V58.3] 自刑惩罚：如果地支有自刑，根气贡献乘以 0.2（根源削减）
                        root_energy = weight * node.current_energy * 0.1
                        if branch_char in self_punishment_branches:
                            root_energy *= 0.2  # 自刑根气惩罚：只保留 20% 贡献
                        
                        # 如果是强根（临官/帝旺），即使被冲也不打折（但自刑惩罚仍然生效）
                        # 注意：自刑惩罚优先于强根抗冲
                        
                        total_root_energy += root_energy
        
        # 方法2：检查十二长生强根位置
        for node in self.nodes:
            if node.node_type == 'branch':
                life_stage = TWELVE_LIFE_STAGES.get((day_master, node.char))
                if life_stage in ['长生', '临官', '帝旺', '冠带']:
                    coefficient = LIFE_STAGE_COEFFICIENTS.get(life_stage, 1.0)
                    # [V57.0] 强根抗冲：临官/帝旺即使被冲也不打折
                    is_strong_root = life_stage in ['临官', '帝旺']
                    is_clashed = False
                    if hasattr(self, 'bazi') and self.bazi:
                        from core.interactions import BRANCH_CLASHES
                        for pillar in self.bazi:
                            if len(pillar) >= 2:
                                other_branch = pillar[1]
                                if BRANCH_CLASHES.get(node.char) == other_branch:
                                    is_clashed = True
                                    break
                    
                    root_energy = node.current_energy * coefficient * 0.1
                    
                    # [V58.3] 自刑惩罚：如果地支有自刑，根气贡献乘以 0.2（根源削减）
                    if node.char in self_punishment_branches:
                        root_energy *= 0.2  # 自刑根气惩罚：只保留 20% 贡献
                    
                    # 注意：自刑惩罚优先于强根抗冲
                    
                    total_root_energy += root_energy
        
        # [V54.0] 判定条件：Total_Root_Energy < 1.0（微根/无根）
        if total_root_energy >= 1.0:
            return None  # 有根，不是从格
        
        # 条件3：检查异党能量占比（财/官/食）
        # 确定异党元素
        output_element = GENERATION.get(dm_element)  # 食伤（我生的）
        wealth_element = CONTROL.get(dm_element)      # 财星（我克的）
        officer_element = None  # 官杀（克我的）
        for attacker, defender in CONTROL.items():
            if defender == dm_element:
                officer_element = attacker
                break
        
        # 计算异党总能量
        hetero_energy = 0.0
        total_energy = strength_data.get('total_energy', 1.0)
        
        for node in self.nodes:
            node_energy = node.current_energy
            if node.element == output_element or node.element == wealth_element or node.element == officer_element:
                hetero_energy += node_energy
        
        # 异党占比
        hetero_ratio = hetero_energy / total_energy if total_energy > 0 else 0.0
        
        # [V57.0] 判定条件：Force_Out_Ratio > 0.7（异党极强）- 降低阈值以识别更多从格
        force_out_ratio = hetero_ratio
        
        # [V57.0] 例外处理：阳刃格不应被判定为从格
        # [V57.4] 修复：检查所有地支，如果其中一个是日主的帝旺位，判定为阳刃格（如乾隆的酉在月支）
        is_yangren = False
        if hasattr(self, 'bazi') and self.bazi and len(self.bazi) > 2:
            day_pillar = self.bazi[2]
            if len(day_pillar) >= 2:
                day_master_char = day_pillar[0]
                # 检查所有地支，看是否有阳刃（帝旺位）
                for pillar in self.bazi:
                    if len(pillar) >= 2:
                        branch = pillar[1]
                        life_stage = TWELVE_LIFE_STAGES.get((day_master_char, branch))
                        if life_stage == '帝旺':
                            is_yangren = True
                            break
        
        # [V58.0] 收紧从格判定条件：必须同时满足无根、异党极强、且不是阳刃格
        # [V57.4] 进一步收紧：异党占比 > 80%，且无根（total_root_energy < 0.3），且不是阳刃格
        if force_out_ratio > 0.80 and total_root_energy < 0.3 and not is_yangren:
            # [V54.0] 日主放弃抵抗，顺从大势
            # Result: total_strength 设为 0.9 (视为特殊的 Strong - 能任财官)
            return {
                'label': 'Special_Follow',  # 改为 Special_Follow
                'reason': 'Follower Grid',
                'hetero_ratio': hetero_ratio,
                'rooting_score': total_root_energy,
                'strength_score': 90.0  # 设为 90 分（特殊的强）
            }
        
        # [V54.0] 判断专旺 (Vibrant)
        # 条件：Force_In_Ratio > 0.85（日主阵营极强）
        self_team_energy = strength_data.get('self_team_energy', 0.0)
        force_in_ratio = self_team_energy / total_energy if total_energy > 0 else 0.0
        
        if force_in_ratio > 0.85:
            # [V58.0] 检查是否有自刑或冲克（格局不纯，不能算专旺）
            has_instability = False
            if hasattr(self, 'bazi') and self.bazi:
                branches = [p[1] for p in self.bazi if len(p) >= 2]
                # 自刑检测：辰、午、酉、亥出现两次或以上
                self_punishments = {'辰', '午', '酉', '亥'}
                for branch in self_punishments:
                    if branches.count(branch) >= 2:
                        has_instability = True
                        break
                
                # 冲克检测：如果存在六冲，格局不纯
                if not has_instability:
                    from core.interactions import BRANCH_CLASHES
                    clash_pairs = set()
                    for i, b1 in enumerate(branches):
                        for j, b2 in enumerate(branches):
                            if i != j and BRANCH_CLASHES.get(b1) == b2:
                                clash_pairs.add(tuple(sorted([b1, b2])))
                    if len(clash_pairs) >= 2:  # 如果有2对或以上的冲，视为格局不纯
                        has_instability = True
            
            # 如果有自刑或严重冲克，不能算专旺格
            if has_instability:
                # 即使能量很强，但因为自刑/冲克，不能算专旺，只能算普通身强（甚至因为内耗变弱）
                return None
            
            # 气势不可逆
            return {
                'label': 'Special_Vibrant',
                'reason': 'Vibrant Grid',
                'force_in_ratio': force_in_ratio,
                'strength_score': 95.0  # 设为 95 分
            }
        
        return None
    
    def _calculate_dynamic_score(self, strength_data: Dict[str, Any],
                                  luck_pillar: str = None, year_pillar: str = None) -> float:
        """
        [V55.0] 动态评分计算
        
        公式：Score_Dynamic = (Score_Natal × 0.6) + (Score_Dayun × 0.3) + (Score_Liunian_Impact × 0.1)
        
        流年影响虽只有 0.1，但因其具备"引动"特性，能瞬间改变原局的旺衰倾向。
        """
        natal_score = strength_data.get('strength_score', 0.0)
        
        # 计算大运影响（如果有）
        dayun_score = 0.0
        if luck_pillar:
            # 大运的影响：如果大运生日主或与日主同五行，提升分数
            dayun_impact = self._calculate_dayun_impact(luck_pillar, strength_data)
            dayun_score = natal_score + dayun_impact
        
        # 计算流年影响（如果有）
        liunian_impact = 0.0
        if year_pillar:
            # 流年的影响：引动效应（冲合）
            liunian_impact = self._calculate_liunian_impact(year_pillar, strength_data)
        
        # 动态评分
        if luck_pillar and year_pillar:
            dynamic_score = (natal_score * 0.6) + (dayun_score * 0.3) + (liunian_impact * 0.1)
        elif luck_pillar:
            dynamic_score = (natal_score * 0.7) + (dayun_score * 0.3)
        else:
            dynamic_score = natal_score
        
        return max(0.0, min(100.0, dynamic_score))  # 限制在 0-100
    
    def _calculate_dayun_impact(self, luck_pillar: str, strength_data: Dict[str, Any]) -> float:
        """计算大运对原局的影响（静态叠加）"""
        if len(luck_pillar) < 2:
            return 0.0
        
        luck_stem = luck_pillar[0]
        luck_branch = luck_pillar[1]
        
        # 获取日主元素
        dm_element = strength_data.get('dm_element', 'metal')
        resource_element = strength_data.get('resource_element')
        
        # 大运元素
        luck_stem_element = self.STEM_ELEMENTS.get(luck_stem, 'earth')
        luck_branch_element = self.BRANCH_ELEMENTS.get(luck_branch, 'earth')
        
        impact = 0.0
        from core.processors.physics import GENERATION
        
        # 如果大运生日主或与日主同五行，提升分数
        if GENERATION.get(luck_stem_element) == dm_element or luck_stem_element == dm_element:
            impact += 5.0  # 大运天干支持日主
        if GENERATION.get(luck_branch_element) == dm_element or luck_branch_element == dm_element:
            impact += 8.0  # 大运地支支持日主（更重要）
        
        # 如果大运生印星，间接支持日主
        if resource_element:
            if GENERATION.get(luck_stem_element) == resource_element or luck_stem_element == resource_element:
                impact += 3.0
            if GENERATION.get(luck_branch_element) == resource_element or luck_branch_element == resource_element:
                impact += 5.0
        
        return impact
    
    def _calculate_liunian_impact(self, year_pillar: str, strength_data: Dict[str, Any]) -> float:
        """计算流年对原局的影响（动态引动）"""
        if len(year_pillar) < 2:
            return 0.0
        
        year_stem = year_pillar[0]
        year_branch = year_pillar[1]
        
        # 获取日主元素
        dm_element = strength_data.get('dm_element', 'metal')
        
        # 流年元素
        year_stem_element = self.STEM_ELEMENTS.get(year_stem, 'earth')
        year_branch_element = self.BRANCH_ELEMENTS.get(year_branch, 'earth')
        
        impact = 0.0
        from core.processors.physics import GENERATION, CONTROL
        from core.interactions import BRANCH_CLASHES
        
        # 检查流年是否冲原局地支（引动）
        for node in self.nodes:
            if node.pillar_idx < 4 and node.node_type == 'branch':
                clash_pair = tuple(sorted([year_branch, node.char]))
                if clash_pair in BRANCH_CLASHES or (year_branch, node.char) in BRANCH_CLASHES:
                    # 被引动：能量波动（可能好也可能坏）
                    if node.element == dm_element:
                        impact -= 10.0  # 冲日主根气，大幅下降
                    else:
                        impact -= 5.0  # 冲其他地支，中等下降
        
        # 检查流年是否克日主
        officer_element = None
        for attacker, defender in CONTROL.items():
            if defender == dm_element:
                officer_element = attacker
                break
        
        if year_stem_element == officer_element or year_branch_element == officer_element:
            impact -= 8.0  # 流年克日主
        
        # 检查流年是否生日主
        resource_element = None
        for elem, target in GENERATION.items():
            if target == dm_element:
                resource_element = elem
                break
        
        if year_stem_element == resource_element or year_branch_element == resource_element:
            impact += 6.0  # 流年生日主，提升
        
        return impact
    
    def _get_dynamic_label(self, dynamic_score: float) -> str:
        """根据动态评分获取标签"""
        grading_config = self.config.get('grading', {})
        strong_threshold = grading_config.get('strong_threshold', 60.0)
        weak_threshold = grading_config.get('weak_threshold', 40.0)
        
        if dynamic_score >= strong_threshold:
            return "Strong"
        elif dynamic_score >= weak_threshold:
            return "Balanced"
        else:
            return "Weak"
    
    def simulate_timeline(self, bazi: List[str], day_master: str, gender: str,
                         start_year: int, duration: int = 10,
                         use_transformer: bool = False) -> List[Dict[str, Any]]:
        """
        [V55.0] 时间线推演：批量推演未来 N 年的运势曲线
        
        [V10.0] 新增 Transformer 时序建模支持
        
        Args:
            bazi: 八字列表
            day_master: 日主天干
            gender: 性别（用于计算大运）
            start_year: 起始年份
            duration: 推演年数（默认 10 年）
            use_transformer: 是否使用 Transformer 时序建模（默认 False）
        
        Returns:
            包含每年运势数据的列表
        """
        timeline = []
        
        # 计算大运（需要 BaziProfile）
        # 注意：simulate_timeline 需要出生日期才能准确计算大运
        # 这里简化处理，如果没有提供出生日期，则使用近似方法
        profile = None
        # 如果需要准确的大运计算，应该在调用时提供 BaziProfile
        
        for year_offset in range(duration):
            current_year = start_year + year_offset
            
            # 计算流年（天干地支）
            # 简化：天干 = (current_year - 4) % 10，地支 = (current_year - 4) % 12
            gan_index = (current_year - 4) % 10
            zhi_index = (current_year - 4) % 12
            gan_list = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            zhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            year_stem = gan_list[gan_index]
            year_branch = zhi_list[zhi_index]
            year_pillar = year_stem + year_branch
            
            # 计算大运
            current_dayun = None
            if profile:
                current_dayun = profile.get_luck_pillar_at(current_year)
            
            # 分析该年的运势
            result = self.analyze(
                bazi=bazi,
                day_master=day_master,
                luck_pillar=current_dayun,
                year_pillar=year_pillar
            )
            
            wealth_result = self.calculate_wealth_index(
                bazi=bazi,
                day_master=day_master,
                gender=gender,
                luck_pillar=current_dayun,
                year_pillar=year_pillar
            )
            
            timeline.append({
                'year': current_year,
                'year_pillar': year_pillar,
                'luck_pillar': current_dayun,
                'strength_score': result.get('strength_score', 0.0),
                'strength_label': result.get('strength_label', 'Unknown'),
                'wealth_index': wealth_result.get('wealth_index', 0.0),
                'confidence_interval': wealth_result.get('confidence_interval', {}),
                'details': wealth_result.get('details', [])
            })
        
        # [V10.0] 如果启用 Transformer，使用时序建模优化结果
        if use_transformer and len(timeline) >= 3:
            transformer_config = self.config.get('transformer', {})
            transformer = TemporalTransformer(transformer_config)
            
            # 使用 Transformer 捕捉长程依赖
            encoded_features, _ = transformer.forward(timeline)
            
            # 基于 Transformer 特征调整结果（简化版）
            # 实际应该使用更复杂的后处理
            for i, item in enumerate(timeline):
                if i < len(encoded_features):
                    # 使用 Transformer 特征微调（简化版）
                    # 实际应该使用更复杂的融合方法
                    # 这里暂时不做调整，保持原结果
                    pass
        
        return timeline
    
    def _collect_trigger_events(self) -> List[str]:
        """[V55.0] 收集所有触发事件"""
        trigger_events = []
        for node in self.nodes:
            if hasattr(node, 'trigger_events') and node.trigger_events:
                trigger_events.extend(node.trigger_events)
        return list(set(trigger_events))  # 去重
    
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
        # [V59.0] 如果已经通关，不应该再惩罚日主
        has_mediation = False
        for node in self.nodes:
            if hasattr(node, 'trigger_events') and node.trigger_events:
                for event in node.trigger_events:
                    event_str = str(event)
                    if '通关' in event_str or '官印相生' in event_str or '绝对通关' in event_str:
                        has_mediation = True
                        break
                if has_mediation:
                    break
        
        if self_energy_init > 0 and officer_energy_init > 0 and not has_mediation:
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
        # [V56.3 修复] 确保 luck_pillar 是字符串类型
        if luck_pillar is not None:
            if not isinstance(luck_pillar, str):
                luck_pillar = str(luck_pillar) if luck_pillar else None
            if luck_pillar and len(luck_pillar) < 2:
                luck_pillar = None
        
        # [V55.0] 保存八字信息
        self.bazi = bazi
        
        # Phase 1: 节点初始化
        H0 = self.initialize_nodes(bazi, day_master, luck_pillar, year_pillar, geo_modifiers)
        
        # Phase 2: 构建邻接矩阵
        A = self.build_adjacency_matrix()
        
        # [V57.4] 应用自刑惩罚（在传播之前，从源头削减能量）
        self._apply_self_punishment_damping(day_master)
        
        # [V54.0] 应用通关逻辑（Mediation Logic）- 在传播之前重构拓扑
        self._apply_mediation_logic(day_master)
        
        # [V55.0] 检测官印相生（流年官杀+大运印星）
        self._detect_officer_resource_mediation(day_master, luck_pillar, year_pillar)
        
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
        
        # [V54.0] 检测从格/专旺（Follower/Vibrant Grid）- 在返回结果前
        follower_result = self._detect_follower_grid(day_master, strength_data)
        if follower_result:
            strength_data['strength_label'] = follower_result['label']
            strength_data['follower_grid'] = True
            # [V54.0] 如果检测到特殊格局，覆盖 strength_score
            if 'strength_score' in follower_result:
                strength_data['strength_score'] = follower_result['strength_score']
        
        # [V55.0] 动态评分计算（考虑大运和流年的影响）
        dynamic_score = self._calculate_dynamic_score(
            strength_data, luck_pillar, year_pillar
        )
        strength_data['dynamic_score'] = dynamic_score
        strength_data['dynamic_label'] = self._get_dynamic_label(dynamic_score)
        
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
            # [V55.0] 动态评分和触发事件
            'dynamic_score': strength_data.get('dynamic_score', strength_data['strength_score']),
            'dynamic_label': strength_data.get('dynamic_label', strength_data['strength_label']),
            'trigger_events': self._collect_trigger_events(),
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
    
    def _get_element_str(self, char: str) -> str:
        """
        辅助方法：获取字符的五行元素
        """
        # 先查天干
        if char in self.STEM_ELEMENTS:
            return self.STEM_ELEMENTS[char]
        # 再查地支
        if char in self.BRANCH_ELEMENTS:
            return self.BRANCH_ELEMENTS[char]
        return 'earth'  # 默认
    
    def calculate_wealth_index(self, bazi: List[str], day_master: str, gender: str,
                               luck_pillar: str = None, year_pillar: str = None):
        """
        [V56.1] 修正版财富引擎
        修复了 2008 冲提纲未识别和身弱财变债的问题
        
        核心逻辑：
        1. 冲提纲（一票否决）：直接 -150 分
        2. 身弱财多（极性反转）：财变债，乘以 -1.2
        3. 食伤生财（权重提升）：乘以 1.5
        
        Args:
            bazi: 八字列表
            day_master: 日主天干
            gender: 性别
            luck_pillar: 大运干支（如 "戊戌"）
            year_pillar: 流年干支（如 "辛丑"）
        
        Returns:
            dict: {
                'wealth_index': float,
                'details': List[str]
            }
        """
        from core.processors.physics import GENERATION, CONTROL
        
        # [V56.3 修复] 确保 luck_pillar 是字符串类型
        if luck_pillar is not None:
            if not isinstance(luck_pillar, str):
                luck_pillar = str(luck_pillar) if luck_pillar else None
            if luck_pillar and len(luck_pillar) < 2:
                luck_pillar = None
        
        # 1. 基础物理计算
        # [V10.0] 强制上下文统一：使用 analyze() 的结果，确保旺衰判定与财富计算一致
        result = self.analyze(bazi, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
        strength_score = result.get('strength_score', 50.0)  # 0-100
        strength_normalized = strength_score / 100.0  # 归一化到 0-1
        strength_label = result.get('strength_label', 'Balanced')
        
        # [V10.0] 调试日志：记录旺衰判定结果
        if strength_normalized < 0.45 and strength_label == 'Strong':
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[V10.0] 旺衰判定不一致: strength_score={strength_score}, strength_normalized={strength_normalized}, strength_label={strength_label}")
        
        # 2. 基础定义
        if not year_pillar or len(year_pillar) < 2:
            return {'wealth_index': 0.0, 'details': ['无流年信息']}
        
        year_stem = year_pillar[0]
        year_branch = year_pillar[1]
        month_branch = bazi[1][1] if len(bazi) > 1 and len(bazi[1]) > 1 else None
        
        wealth_energy = 0.0
        details = []
        
        # 辅助映射
        elem_map = {'wood': 0, 'fire': 1, 'earth': 2, 'metal': 3, 'water': 4}
        
        # 获取日主元素
        dm_element = self.STEM_ELEMENTS.get(day_master, 'wood')
        dm_idx = elem_map.get(dm_element, 0)
        
        # 我克为财，我生为食伤，克我为官
        wealth_idx = (dm_idx + 2) % 5
        output_idx = (dm_idx + 1) % 5
        officer_idx = (dm_idx + 3) % 5  # [V61.2] 官杀索引
        
        # 获取流年五行
        stem_elem = self._get_element_str(year_stem)
        branch_elem = self._get_element_str(year_branch)
        stem_idx = elem_map.get(stem_elem, 2)
        branch_idx = elem_map.get(branch_elem, 2)
        
        # A. 计算流年财气 (Opportunity)
        # A1. 天干透财
        if stem_idx == wealth_idx:
            wealth_energy += 50.0
            details.append(f"天干透财({year_stem})")
        
        # A2. 地支食伤生财 (Multiplier - 2002修正)
        # [V10.0] 显式激活"食伤生财"通道，增加 opportunity_bonus
        if branch_idx == output_idx:
            base_output_wealth = 30.0 * 1.5  # 基础权重
            # [V10.0] 食伤生财通道：增加 opportunity_bonus
            generation_efficiency = self.config.get('flow', {}).get('generationEfficiency', 1.2)
            opportunity_bonus = 15.0 * generation_efficiency  # 机会加成
            
            # [V10.0] 核心分析师建议：泄气惩罚
            # 针对极弱格局，将"食伤生财"的opportunity_bonus反转为exhaustion_penalty
            if strength_normalized < 0.3:
                # 极弱格局：食伤是"泄气"而非"生财"
                exhaustion_penalty = opportunity_bonus * 2.0  # 泄气惩罚加倍
                wealth_energy += base_output_wealth - exhaustion_penalty  # 减去泄气惩罚
                details.append(f"食伤生财({year_branch})[基础: {base_output_wealth:.1f}, 泄气惩罚: -{exhaustion_penalty:.1f}]")
            elif strength_normalized < 0.45:
                # 身弱格局：食伤部分泄气
                exhaustion_penalty = opportunity_bonus * 0.5  # 泄气惩罚减半
                wealth_energy += base_output_wealth + (opportunity_bonus - exhaustion_penalty)  # 部分抵消
                details.append(f"食伤生财({year_branch})[基础: {base_output_wealth:.1f}, 机会加成: {opportunity_bonus:.1f}, 泄气惩罚: -{exhaustion_penalty:.1f}]")
            else:
                # 身强格局：正常食伤生财
                wealth_energy += base_output_wealth + opportunity_bonus
                details.append(f"食伤生财({year_branch})[基础: {base_output_wealth:.1f}, 机会加成: {opportunity_bonus:.1f}]")
        
        # A3. 地支坐财
        if branch_idx == wealth_idx:
            wealth_energy += 40.0
            details.append(f"地支坐财({year_branch})")
        
        # B. 墓库隧穿 (Tunneling) - 暴富逻辑
        vaults = {'辰', '戌', '丑', '未'}
        # 墓库对应的五行元素（库中存储的元素）
        vault_elements = {'辰': 'water', '戌': 'fire', '丑': 'metal', '未': 'wood'}
        clashes = {'子': '午', '午': '子', '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
                   '辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
        # [V61.0] 六合关系：用于检测"合开财库"
        combinations = {
            '子': '丑', '丑': '子',  # 子丑合
            '寅': '亥', '亥': '寅',  # 寅亥合
            '卯': '戌', '戌': '卯',  # 卯戌合
            '辰': '酉', '酉': '辰',  # 辰酉合
            '午': '未', '未': '午',  # 午未合
            '申': '巳', '巳': '申',  # 申巳合
        }
        
        treasury_opened = False  # [V56.2] 标记是否开库
        treasury_collapsed = False  # [V60.0] 标记是否库塌
        
        # B1. 检查是否冲开了原局的财库
        for pillar in bazi:
            if len(pillar) < 2:
                continue
            p_branch = pillar[1]
            if p_branch in vaults and clashes.get(p_branch) == year_branch:
                # [V59.1] 检查这个库是否是财库（库中存储的元素是否是日主的财星）
                vault_element = vault_elements.get(p_branch)
                if vault_element and elem_map.get(vault_element) == wealth_idx:
                    # [V10.0] 使用非线性模型替代硬编码 if/else
                    # 检测三刑效应
                    has_trine = False
                    trine_completeness = 0.0
                    if p_branch == '丑' and year_branch == '未':
                        # 检查是否有戌（丑未戌三刑）
                        for p in bazi:
                            if len(p) >= 2 and p[1] == '戌':
                                has_trine = True
                                trine_completeness = 1.0
                                break
                    elif p_branch == '未' and year_branch == '丑':
                        # 检查是否有戌（丑未戌三刑）
                        for p in bazi:
                            if len(p) >= 2 and p[1] == '戌':
                                has_trine = True
                                trine_completeness = 1.0
                                break
                    
                    # 使用非线性模型计算财库能量
                    clash_intensity = 1.0  # 冲的强度
                    vault_energy, vault_details = NonlinearActivation.calculate_vault_energy_nonlinear(
                        strength_normalized=strength_normalized,
                        clash_type='冲',
                        clash_intensity=clash_intensity,
                        has_trine=has_trine,
                        trine_completeness=trine_completeness,
                        base_bonus=100.0,
                        base_penalty=-120.0,
                        config=self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                    )
                    
                    wealth_energy += vault_energy
                    if vault_energy > 0:
                        details.append(f"🏆 冲开财库(财富爆发)({year_branch}冲{p_branch})[非线性模型: {vault_energy:.1f}]")
                        treasury_opened = True
                    else:
                        details.append(f"💥 财库坍塌(结构崩塌)({year_branch}冲{p_branch})[非线性模型: {vault_energy:.1f}]")
                        treasury_collapsed = True
                    break
        
        # B1.5. [V61.0] 检查是否合开了原局的财库或官库（如寅合未）
        # [V61.3] 扩展：检查流年地支和大运地支是否都能触发合开库
        if not treasury_opened and not treasury_collapsed:
            for pillar in bazi:
                if len(pillar) < 2:
                    continue
                p_branch = pillar[1]
                # 检查流年地支是否与原局库"合"（不能是相同地支）
                year_combines_vault = (p_branch in vaults and year_branch != p_branch and combinations.get(year_branch) == p_branch)
                # [V61.3] 也检查大运地支是否与原局库"合"（大运和流年共同作用，不能是相同地支）
                luck_combines_vault = False
                if luck_pillar and len(luck_pillar) >= 2:
                    luck_branch = luck_pillar[1]
                    luck_combines_vault = (p_branch in vaults and luck_branch != p_branch and combinations.get(luck_branch) == p_branch)
                
                if year_combines_vault or luck_combines_vault:
                    vault_element = vault_elements.get(p_branch)
                    is_wealth_vault = (vault_element and elem_map.get(vault_element) == wealth_idx)
                    is_officer_vault = (vault_element and elem_map.get(vault_element) == officer_idx)
                    
                    # [V61.3] 确定是流年还是大运触发的合
                    if year_combines_vault:
                        trigger_branch = year_branch
                        trigger_source = "流年"
                    elif luck_combines_vault and luck_pillar and len(luck_pillar) >= 2:
                        trigger_branch = luck_pillar[1]
                        trigger_source = "大运"
                    else:
                        trigger_branch = year_branch
                        trigger_source = "流年"
                    
                    # [V61.2] 检查财库或官库
                    if is_wealth_vault:
                        # [V10.0] 使用非线性模型替代硬编码 if/else
                        clash_intensity = 0.8  # 合的强度略低于冲
                        vault_energy, vault_details = NonlinearActivation.calculate_vault_energy_nonlinear(
                            strength_normalized=strength_normalized,
                            clash_type='合',
                            clash_intensity=clash_intensity,
                            has_trine=False,  # 合开通常不涉及三刑
                            trine_completeness=0.0,
                            base_bonus=100.0,
                            base_penalty=-120.0,
                            config=self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                        )
                        
                        wealth_energy += vault_energy
                        if vault_energy > 0:
                            details.append(f"🏆 合开财库(财富爆发)({trigger_source}{trigger_branch}合{p_branch})[非线性模型: {vault_energy:.1f}]")
                            treasury_opened = True
                        else:
                            details.append(f"💥 财库坍塌(合开导致)({trigger_source}{trigger_branch}合{p_branch})[非线性模型: {vault_energy:.1f}]")
                            treasury_collapsed = True
                        break
                    elif is_officer_vault:
                        # [V61.2] 合开官库：官印相生或官生财，也能带来财富（但加成较小）
                        if strength_normalized > 0.5:
                            # 身强：官库打开，官生财
                            treasury_bonus = 80.0  # 官库打开比财库打开加成稍小
                            wealth_energy += treasury_bonus
                            details.append(f"🏆 合开官库(官生财)({trigger_source}{trigger_branch}合{p_branch})")
                            treasury_opened = True
                        else:
                            # 身弱：官库打开也可能带来财富（通过官印相生），但需要检查是否有印星
                            if has_help:  # 有帮身（印星或比劫）
                                treasury_bonus = 60.0
                                wealth_energy += treasury_bonus
                                details.append(f"🏆 合开官库(官印相生)({trigger_source}{trigger_branch}合{p_branch})")
                                treasury_opened = True
                            else:
                                # 无帮身：官库打开可能导致压力
                                treasury_penalty = -80.0
                                wealth_energy += treasury_penalty
                                details.append(f"💥 官库打开(压力)({trigger_source}{trigger_branch}合{p_branch})")
                                treasury_collapsed = True
                        break
        
        # B1.6. [V61.4] 检查三合局引动库
        # 如果大运和流年形成三合局，且原局有对应的库，也可能触发开库
        if not treasury_opened and not treasury_collapsed:
            trine_groups = [
                {'申', '子', '辰'},  # 三合水
                {'亥', '卯', '未'},  # 三合木
                {'寅', '午', '戌'},  # 三合火
                {'巳', '酉', '丑'},  # 三合金
            ]
            
            # 收集所有地支（原局 + 流年 + 大运）
            all_branches = []
            for pillar in bazi:
                if len(pillar) >= 2:
                    all_branches.append(pillar[1])
            all_branches.append(year_branch)
            if luck_pillar and len(luck_pillar) >= 2:
                all_branches.append(luck_pillar[1])
            
            # 检查每个三合局
            for trine_group in trine_groups:
                branches_in_trine = [b for b in all_branches if b in trine_group]
                if len(branches_in_trine) >= 3:  # 三合局成立
                    # 检查原局是否有库在三合局中
                    for pillar in bazi:
                        if len(pillar) < 2:
                            continue
                        p_branch = pillar[1]
                        if p_branch in vaults and p_branch in trine_group:
                            vault_element = vault_elements.get(p_branch)
                            is_wealth_vault = (vault_element and elem_map.get(vault_element) == wealth_idx)
                            is_officer_vault = (vault_element and elem_map.get(vault_element) == officer_idx)
                            
                            # 三合局引动库：身强时财富爆发
                            if is_wealth_vault or is_officer_vault:
                                if strength_normalized > 0.5:
                                    treasury_bonus = 100.0 if is_wealth_vault else 80.0
                                    wealth_energy += treasury_bonus
                                    vault_type = "财库" if is_wealth_vault else "官库"
                                    details.append(f"🏆 三合局引动{vault_type}(财富爆发)(三合局成立)")
                                    treasury_opened = True
                                    break
                    if treasury_opened:
                        break
        
        # B2. 检查流年地支本身是否是财库（2021年修正）
        # 如果流年地支是财库（辰戌丑未），且原局有对应的冲支，也可能触发库开
        if year_branch in vaults and not treasury_opened:
            clash_key = clashes.get(year_branch)
            if clash_key:
                # 检查原局是否有对应的冲支
                for pillar in bazi:
                    if len(pillar) < 2:
                        continue
                    p_branch = pillar[1]
                    if p_branch == clash_key:
                        # [V56.2] 增强流年财库被引动的财富能量
                        treasury_bonus = 80.0 if strength_normalized > 0.5 else 60.0
                        wealth_energy += treasury_bonus
                        details.append(f"🚀 流年财库({year_branch})被引动")
                        treasury_opened = True
                        break
        
        # B3. [V60.0] 增强官印相生机制
        # 扩展判断条件：流年官杀 + 大运印星（天干或地支）
        # 特别检查：大运地支是否是印星（如亥水生甲木）
        
        # [V60.2] 确定官杀元素和印星元素（提前定义，以便后续使用）
        officer_element = None
        for attacker, defender in CONTROL.items():
            if defender == dm_element:
                officer_element = attacker
                break
        
        resource_element = None
        for source, target in GENERATION.items():
            if target == dm_element:
                resource_element = source
                break
        
        # 检查流年天干是否是官杀
        year_is_officer = (stem_elem == officer_element)
        # 检查流年地支是否是官杀库（如辛丑，丑是金库）
        year_branch_is_officer_vault = False
        if year_branch in vaults:
            vault_element = vault_elements.get(year_branch)  # 返回 'metal', 'wood', 'fire', 'water'
            # [V60.1] 修复：直接比较字符串，确保 officer_element 是字符串类型
            if vault_element and vault_element == officer_element:
                year_branch_is_officer_vault = True
        
        # [V60.3] 检查大运是否是印星（即使 luck_pillar 为空，也检查流年本身）
        luck_is_resource = False
        if luck_pillar and len(luck_pillar) >= 2:
            luck_stem = luck_pillar[0]
            luck_branch = luck_pillar[1]
            luck_stem_elem = self._get_element_str(luck_stem)
            luck_branch_elem = self._get_element_str(luck_branch)
            luck_is_resource = (luck_stem_elem == resource_element or luck_branch_elem == resource_element)
        
        # [V60.6] 扩展判断：流年官杀（天干或库）+ 大运印星（天干或地支）
        # 如果流年天干是官杀，且大运是印星，触发官印相生
        # [V60.6] 修复：确保判断逻辑正确，包括检查流年地支是否是官杀库
        # 特别处理：如果流年地支是官杀库（如辛丑，丑是金库），且大运是印星，也应该触发
        # 注意：官印相生应该在计算 final_index 之前就增加 wealth_energy，这样后续的"身弱财重"判断才能正确
        # [V60.7] 修复：确保 luck_pillar 正确传递，并添加调试信息
        if luck_pillar and len(luck_pillar) >= 2:
            # 重新计算 luck_is_resource（确保使用最新的 luck_pillar）
            luck_stem_check = luck_pillar[0]
            luck_branch_check = luck_pillar[1]
            luck_stem_elem_check = self._get_element_str(luck_stem_check)
            luck_branch_elem_check = self._get_element_str(luck_branch_check)
            luck_is_resource = (luck_stem_elem_check == resource_element or luck_branch_elem_check == resource_element)
        
        if (year_is_officer or year_branch_is_officer_vault) and luck_is_resource:
            # 官印相生：官杀通过印星通关，转化为财富能量
            # [V60.0] 提升权重，特别是身弱时
            officer_resource_bonus = 80.0 if strength_normalized < 0.45 else 60.0
            wealth_energy += officer_resource_bonus
            if year_branch_is_officer_vault:
                details.append(f"🌟 官印相生(流年官杀库+大运印星)")
            else:
                details.append(f"🌟 官印相生(流年官杀+大运印星)")
        
        # [V61.7] 检查流年和大运都是官库的情况（双库共振）
        # 如果流年地支是官库，且大运地支也是官库（相同），可能形成"双库共振"
        if year_branch_is_officer_vault and luck_pillar and len(luck_pillar) >= 2:
            luck_branch = luck_pillar[1]
            if luck_branch in vaults:
                luck_vault_element = vault_elements.get(luck_branch)
                if luck_vault_element and luck_vault_element == officer_element:
                    # 双库共振：流年和大运都是官库，形成共振效应
                    # 即使没有官印相生，双库共振也能带来财富（通过官生财）
                    double_vault_bonus = 100.0 if strength_normalized > 0.4 else 80.0
                    wealth_energy += double_vault_bonus
                    details.append(f"🏆 双库共振(流年和大运都是官库)({year_branch}+{luck_branch})")
                    treasury_opened = True
        
        # D. 承载力与极性反转 (Capacity & Inversion)
        final_index = 0.0
        
        # 检查是否有帮身元素（强根、印星、比劫）
        has_help = False
        help_type = None
        strong_root_bonus = 0.0  # [V56.2] 强根对财富的直接加成
        strong_root_type = None
        
        # C1. 检查流年地支是否是日主的强根（帝旺、临官、长生）
        if day_master and year_branch:
            life_stage = TWELVE_LIFE_STAGES.get((day_master, year_branch))
            if life_stage in ['帝旺', '临官', '长生']:
                has_help = True
                help_type = f"流年{year_branch}为日主{life_stage}(强根)"
                details.append(help_type)
                strong_root_type = life_stage
                # [V56.2] 强根直接增加财富能量（身弱得强根效果更明显）
                if life_stage == '帝旺':
                    strong_root_bonus = 40.0 if strength_normalized < 0.45 else 25.0
                elif life_stage == '临官':
                    strong_root_bonus = 30.0 if strength_normalized < 0.45 else 20.0
                else:  # 长生
                    strong_root_bonus = 20.0 if strength_normalized < 0.45 else 15.0
                wealth_energy += strong_root_bonus
        
        # C2. 检查流年天干/地支是否是印星或比劫
        # [V60.2] 如果 B3 部分已经定义了 resource_element，这里不需要重新定义
        # resource_element 已在 B3 部分定义，这里不需要重新定义
        
        peer_element = dm_element  # 比劫
        
        if not has_help:
            if stem_elem == resource_element or branch_elem == resource_element:
                has_help = True
                help_type = "流年印星帮身"
                details.append(help_type)
            elif stem_elem == peer_element or branch_elem == peer_element:
                has_help = True
                help_type = "流年比劫帮身"
                details.append(help_type)
        
        # C3. 检查大运是否帮身
        if luck_pillar and len(luck_pillar) >= 2:
            luck_stem = luck_pillar[0]
            luck_branch = luck_pillar[1]
            luck_stem_elem = self._get_element_str(luck_stem)
            luck_branch_elem = self._get_element_str(luck_branch)
            
            if not has_help:
                if luck_stem_elem == resource_element or luck_branch_elem == resource_element:
                    has_help = True
                    help_type = "大运印星帮身"
                    details.append(help_type)
                    # [V10.0] 大运印星帮身时，直接增加财富能量（非线性增强）
                    luck_seal_help_bonus = 30.0 if strength_normalized < 0.45 else 20.0
                    wealth_energy += luck_seal_help_bonus
                    details.append(f"🌟 大运印星帮身加成(+{luck_seal_help_bonus:.1f})")
                elif luck_stem_elem == peer_element or luck_branch_elem == peer_element:
                    has_help = True
                    help_type = "大运比劫帮身"
                    details.append(help_type)
            
            # 检查大运地支是否是强根
            if day_master and luck_branch:
                luck_life_stage = TWELVE_LIFE_STAGES.get((day_master, luck_branch))
                if luck_life_stage in ['帝旺', '临官', '长生']:
                    has_help = True
                    help_type = f"大运{luck_branch}为日主{luck_life_stage}(强根)"
                    details.append(help_type)
                    # [V60.0] 增强大运强根的权重，特别是身弱时
                    # 即使流年有强根，大运强根也应该增加财富能量（叠加效应）
                    if luck_life_stage == '帝旺':
                        luck_strong_root_bonus = 40.0 if strength_normalized < 0.45 else 25.0
                    elif luck_life_stage == '临官':
                        luck_strong_root_bonus = 35.0 if strength_normalized < 0.45 else 20.0
                    else:  # 长生
                        luck_strong_root_bonus = 30.0 if strength_normalized < 0.45 else 15.0
                    
                    # [V60.0] 大运强根总是增加财富能量（与流年强根叠加）
                    wealth_energy += luck_strong_root_bonus
                    strong_root_bonus += luck_strong_root_bonus  # 累加到总强根加成
                    if not strong_root_type:
                        strong_root_type = luck_life_stage  # 如果流年没有强根，使用大运强根类型
        
        # [V10.0] 强制上下文统一：确保使用 analyze() 的结果，不再二次计算
        # 使用 V10.0 概率波输出，确保旺衰判定与财富计算一致
        dm_strength = strength_normalized  # 直接使用 analyze() 的结果
        
        # [V10.0] 关键修复：身强时不应该应用身弱惩罚
        # 彻底杜绝身强时的身弱惩罚
        apply_weak_penalty = (dm_strength < 0.45)
        
        # 关键修正：身弱财多 = 破财，但有帮身时可以担财
        # [V61.8] 特殊机制优先：如果触发了双库共振、官印相生或开库，即使身弱也不反转
        special_mechanism_triggered = treasury_opened or (year_branch_is_officer_vault and luck_pillar and len(luck_pillar) >= 2 and luck_pillar[1] in vaults)
        
        if apply_weak_penalty:  # [V10.0] 使用统一的判断条件
            if wealth_energy > 0:
                if has_help:
                    # [V56.2] 有帮身：可以担财，根据强根类型调整承载力
                    # [V59.1] 修复1995年：身弱得强根但无财透时，应该给予更高的基础财富能量
                    # 检查是否有财星透出（天干透财或地支坐财）
                    has_wealth_exposed = False
                    if stem_idx == wealth_idx or branch_idx == wealth_idx:
                        has_wealth_exposed = True
                    
                    # [V10.0] 激活"印星特权"加成：针对"身弱用印"命局，增强印星帮身的加成
                    # 检查是否是印星帮身（而非比劫帮身）
                    is_seal_help = False
                    if help_type and ("印星" in help_type or "印" in help_type):
                        is_seal_help = True
                    
                    # [V10.0] 印星帮身：非线性增强（量子隧穿效应）
                    seal_additional_bonus = 0.0
                    if is_seal_help:
                        # [V10.0] 核心分析师建议：印星特权条件化
                        # 如果has_leg_cutting且is_extreme_weak，禁用seal_privilege_bonus
                        # 检查是否会在后面检测到截脚结构（提前检查）
                        has_leg_cutting_condition = False
                        if year_stem and year_branch:
                            year_stem_elem_check = self._get_element_str(year_stem)
                            year_branch_elem_check = self._get_element_str(year_branch)
                            if year_stem_elem_check in CONTROL and CONTROL[year_stem_elem_check] == year_branch_elem_check:
                                has_leg_cutting_condition = True
                        
                        is_extreme_weak_condition = strength_normalized < 0.3
                        
                        if has_leg_cutting_condition and is_extreme_weak_condition:
                            # 极弱格局 + 截脚结构：印星参与截脚，禁用特权加成
                            details.append(f"⚠️ 印星特权禁用(极弱+截脚，印星转为忌神)")
                        else:
                            seal_additional_bonus = 30.0  # 印星特权加成
                            wealth_energy += seal_additional_bonus
                            details.append(f"🌟 印星特权加成(+{seal_additional_bonus:.1f})")
                    
                    if strong_root_type == '帝旺':
                        # 身弱得帝旺强根，承载力大幅提升
                        final_index = wealth_energy * 1.0  # 从0.8提升到1.0
                    elif strong_root_type == '临官':
                        final_index = wealth_energy * 0.9  # 从0.8提升到0.9
                    elif strong_root_type == '长生':
                        # [V59.1] 长生强根：如果无财透，给予更高的基础财富能量（创业/起步加成）
                        if not has_wealth_exposed:
                            # 无财透但得强根：创业/起步加成，给予更高的基础财富能量
                            final_index = wealth_energy * 1.0 + 40.0  # 强根能量 + 创业加成
                            details.append("🚀 身弱得强根创业加成")
                        else:
                            final_index = wealth_energy * 0.8  # 有财透时保持原值
                    else:
                        # [V10.0] 无强根但有印星帮身时，也给予较高加成
                        if is_seal_help:
                            final_index = wealth_energy * 0.95  # 印星帮身时接近1.0
                        else:
                            final_index = wealth_energy * 0.8  # 保持原值
                    details.append("✅ 身弱得助，可担财")
                elif special_mechanism_triggered:
                    # [V61.8] 特殊机制触发（双库共振、官印相生、开库）：即使身弱也不反转
                    # 特殊机制的能量足够大，可以抵消身弱的影响
                    final_index = wealth_energy * 0.9  # 轻微折扣，但不反转
                    details.append("✅ 特殊机制触发，身弱可担财")
                else:
                    # [V10.0] 核心分析师建议：完善从格判定
                    # 正确区分"从财格"与"身弱不从"
                    # 从格条件：身极弱 + 财星强旺 + 无帮身
                    is_from_pattern = (
                        strength_normalized < 0.45 and  # 身极弱
                        (has_wealth_exposed or wealth_energy > 50.0) and  # 财星强旺（放宽条件）
                        not has_help  # 无帮身
                    )
                    
                    if is_from_pattern:
                        # 从格：财星为用神，不反转
                        # 如果满足从格，财富能量应为正向（Wealth×1.0）
                        final_index = wealth_energy * 1.0
                        details.append("🌟 从财格: 财星为用神，不反转")
                    else:
                        # 非从格：身弱财重，财变债
                        # 如果不从且见截脚，触发"极向反转"（Wealth×−1.5）
                        if wealth_energy > 50.0:  # 提高财重阈值
                            final_index = wealth_energy * -1.5  # 增强反转系数（从-1.2到-1.5）
                            details.append("💸 身弱财重: 变债务")
                        else:
                            # 财不重时，仍然反转但系数较小
                            final_index = wealth_energy * -1.2
                            details.append("💸 身弱财多: 变债务")
            else:
                # [V56.3] 身弱时，即使没有特殊事件，也应该有基础财富能量（但为负值，表示消耗）
                # [V56.2] 如果只有强根但没有财，也应该有基础财富能量
                if strong_root_bonus > 0:
                    # [V59.1] 修复1995年：如果只有强根没有财，且是长生强根，给予创业加成
                    if strong_root_type == '长生':
                        final_index = strong_root_bonus * 1.0 + 40.0  # 强根能量 + 创业加成
                        details.append(f"🚀 强根创业加成({final_index:.1f})")
                    else:
                        final_index = strong_root_bonus * 0.6  # 强根带来基础财富
                        details.append(f"强根基础财富({strong_root_bonus * 0.6:.1f})")
                else:
                    # [V10.0] 修复：确保只在真正身弱时应用基础消耗
                    # [V56.3] 身弱且无帮身时，基础财富为负（消耗）
                    if dm_strength < 0.45:  # [V10.0] 双重检查，确保不会在身强时应用
                        base_wealth = -10.0 - (1.0 - dm_strength) * 10.0  # -10到-20分
                        final_index = base_wealth
                        details.append(f"身弱基础消耗({base_wealth:.1f})")
                    else:
                        # [V10.0] 身强时不应该有基础消耗
                        base_wealth = dm_strength * 15.0  # 身强时基础财富0-15分
                        final_index = base_wealth
                        details.append(f"身强基础财富({base_wealth:.1f})")
        else:
            # 身强任财
            # [V56.2] 身强时，如果有库开或官印相生，额外加成
            bonus = 1.2 if strength_normalized > 0.6 else 1.0
            if treasury_opened:
                bonus *= 1.3  # 库开时额外30%加成
            
            # [V56.3] 即使没有特殊事件，身强时也应该有基础财富能量
            # 基于日主强弱和流年基础能量
            if wealth_energy == 0.0:
                # 基础财富能量：身强时，即使没有特殊事件，也有基础财富潜力
                # 根据身强程度给予基础值（0-20分）
                base_wealth = strength_normalized * 15.0  # 身强时基础财富0-15分
                wealth_energy = base_wealth
                details.append(f"基础财富能量({base_wealth:.1f})")
            
            final_index = wealth_energy * bonus
            if wealth_energy > 0:
                details.append("💪 身旺任财")
        
        # E. [V60.5] 截脚结构检测（移到强根之后应用，根据帮身情况和财富能量调整惩罚）
        # 截脚 = 流年天干克流年地支，导致地支能量被削弱
        # [V60.5] 修复：截脚结构惩罚应该根据是否有帮身和财富能量来调整，避免过度惩罚或不足
        if year_stem and year_branch:
            year_stem_elem = self._get_element_str(year_stem)
            year_branch_elem = self._get_element_str(year_branch)
            
            # 检查是否是天干克地支（截脚）
            if year_stem_elem in CONTROL and CONTROL[year_stem_elem] == year_branch_elem:
                # [V60.5] 截脚结构惩罚：根据身强身弱、是否有帮身和财富能量来调整
                # [V10.0] 核心分析师建议：对于极弱格局，截脚惩罚应该是固定严重惩罚，不依赖wealth_energy
                if strength_normalized < 0.3:
                    # 极弱格局：截脚惩罚不依赖wealth_energy，直接使用固定严重惩罚
                    # 结构性坍塌：截脚意味着仅存的一点"印星护卫"或"气机"被切断
                    base_penalty = -100.0  # 极弱格局固定严重惩罚
                    # 使用非线性模型计算惩罚（但强度设为1.0，不依赖wealth_factor）
                    leg_cutting_penalty, penalty_details = NonlinearActivation.calculate_penalty_nonlinear(
                        strength_normalized=strength_normalized,
                        penalty_type='leg_cutting',
                        intensity=1.0,  # 极弱格局时强度设为1.0，不依赖wealth_factor
                        has_help=has_help,
                        has_mediation=False,  # 截脚结构通常无通关
                        base_penalty=base_penalty,
                        config=self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                    )
                    # [V10.0] 核心分析师建议：截脚惩罚指数化
                    # 极弱格局：结构性坍塌，惩罚2.5x-4.5x（贝叶斯调优：上限从3.0调至4.5）
                    extreme_weak_multiplier = 2.5 + (0.3 - strength_normalized) * 4.0  # 2.5-4.5
                    leg_cutting_penalty = leg_cutting_penalty * extreme_weak_multiplier
                else:
                    # 非极弱格局：正常计算，依赖wealth_factor
                    wealth_factor = min(1.0, max(0.3, wealth_energy / 50.0))  # 0.3-1.0的系数
                    
                    # 根据身强身弱决定基础惩罚
                    if strength_normalized < 0.45:
                        base_penalty = -60.0  # 身弱格局
                    else:
                        base_penalty = -50.0  # 身强格局
                    
                    # 使用非线性模型计算惩罚
                    leg_cutting_penalty, penalty_details = NonlinearActivation.calculate_penalty_nonlinear(
                        strength_normalized=strength_normalized,
                        penalty_type='leg_cutting',
                        intensity=wealth_factor,  # 使用财富因子作为强度
                        has_help=has_help,
                        has_mediation=False,  # 截脚结构通常无通关
                        base_penalty=base_penalty,
                        config=self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                    )
                    
                    # [V10.0] 核心分析师建议：截脚惩罚指数化
                    if strength_normalized < 0.45:
                        # 身弱格局：惩罚增加50%
                        leg_cutting_penalty = leg_cutting_penalty * 1.5
                    else:
                        # 身强格局：正常惩罚（1.0x）
                        pass
                    
                    # 应用财富因子
                    leg_cutting_penalty = leg_cutting_penalty * wealth_factor
                
                details.append(f"⚠️ 截脚结构(天干克地支，削弱地支能量)[非线性模型: {leg_cutting_penalty:.1f}]")
                
                # [V60.5] 应用截脚结构惩罚到 final_index（在所有正面因素之后）
                final_index += leg_cutting_penalty
        
        # F0. [V61.9] 七杀攻身检测：优先于其他因素（除了冲提纲和特殊机制）
        # 如果流年天干是七杀，且身弱或无通关，应该识别为危机
        # [V61.10] 但特殊机制（双库共振、官印相生、开库）优先于七杀攻身
        seven_kill_attack = False
        seven_kill_penalty = 0.0
        
        if year_stem:
            # 检查流年天干是否是七杀（克日主的元素）
            year_stem_elem = self._get_element_str(year_stem)
            if year_stem_elem == officer_element:
                # 流年天干是官杀，检查是否有通关机制
                has_seven_kill_mediation = False
                
                # 检查是否有印星通关（官印相生）
                if luck_pillar and len(luck_pillar) >= 2:
                    luck_stem = luck_pillar[0]
                    luck_branch = luck_pillar[1]
                    luck_stem_elem = self._get_element_str(luck_stem)
                    luck_branch_elem = self._get_element_str(luck_branch)
                    if luck_stem_elem == resource_element or luck_branch_elem == resource_element:
                        has_seven_kill_mediation = True
                
                # 检查流年地支是否是印星
                if branch_elem == resource_element:
                    has_seven_kill_mediation = True
                
                # [V61.14] 检查是否有针对流年七杀的通关事件
                # 只有直接化解流年七杀的通关才能抵消七杀攻身
                # 原局的通关不能化解流年七杀攻身
                trigger_events = result.get('trigger_events', [])
                for event in trigger_events:
                    event_str = str(event)
                    # 检查是否是针对流年七杀的通关
                    # 如果通关涉及流年天干（七杀），才能化解
                    if ('通关' in event_str or '官印相生' in event_str) and year_stem in event_str:
                        has_seven_kill_mediation = True
                        break
                    # 或者，如果大运是印星，且流年地支是印星，也可能通关
                    if luck_pillar and len(luck_pillar) >= 2:
                        luck_branch = luck_pillar[1]
                        if branch_elem == resource_element and luck_branch_elem == resource_element:
                            # 流年地支和大运地支都是印星，可能形成通关
                            has_seven_kill_mediation = True
                            break
                
                # [V61.10] 检查是否有特殊机制（双库共振、开库等）
                # 这些机制优先于七杀攻身
                has_special_mechanism = treasury_opened or (year_branch_is_officer_vault and luck_pillar and len(luck_pillar) >= 2 and luck_pillar[1] in vaults)
                
                # [V10.0] 使用非线性模型替代硬编码 if/else
                if not has_seven_kill_mediation and not has_special_mechanism:
                    seven_kill_attack = True
                    # 根据身强身弱决定基础惩罚
                    if strength_normalized < 0.4:
                        base_penalty = -100.0  # 身极弱
                    elif strength_normalized < 0.5:
                        base_penalty = -80.0  # 身弱
                    else:
                        base_penalty = -60.0  # 身强但杀重
                    
                    # 检查是否有财星透出（杀重身轻的典型情况）
                    has_wealth_exposed = (stem_idx == wealth_idx or branch_idx == wealth_idx)
                    intensity = 1.0 if has_wealth_exposed else 0.9
                    
                    # 使用非线性模型计算惩罚
                    seven_kill_penalty, penalty_details = NonlinearActivation.calculate_penalty_nonlinear(
                        strength_normalized=strength_normalized,
                        penalty_type='seven_kill',
                        intensity=intensity,
                        has_help=False,  # 七杀攻身时通常无帮身
                        has_mediation=has_seven_kill_mediation,
                        base_penalty=base_penalty,
                        config=self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                    )
                    
                    if strength_normalized < 0.4:
                        details.append(f"💀 七杀攻身(身极弱，无通关)({year_stem}克{day_master})[非线性模型: {seven_kill_penalty:.1f}]")
                    elif strength_normalized < 0.5:
                        details.append(f"💀 七杀攻身(身弱，无通关)({year_stem}克{day_master})[非线性模型: {seven_kill_penalty:.1f}]")
                    else:
                        details.append(f"💀 七杀攻身(杀重身轻)({year_stem}克{day_master})[非线性模型: {seven_kill_penalty:.1f}]")
                elif has_special_mechanism:
                    # [V61.10] 有特殊机制：七杀攻身的影响被特殊机制抵消
                    # 不应用惩罚，或只应用轻微惩罚
                    details.append(f"✅ 七杀攻身被特殊机制化解({year_stem}克{day_master})")
                else:
                    # 有通关：七杀攻身的影响被化解，但仍可能有轻微影响
                    # 使用非线性模型计算轻微惩罚
                    seven_kill_penalty, penalty_details = NonlinearActivation.calculate_penalty_nonlinear(
                        strength_normalized=strength_normalized,
                        penalty_type='seven_kill',
                        intensity=0.2,  # 有通关，强度降低
                        has_help=False,
                        has_mediation=True,
                        base_penalty=-20.0,
                        config=self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                    )
                    # [V10.0] 专项修复：强制激活"食神制杀/伤官配印"特权
                    # 检查是否有印星通关且流年见强根（食神制杀的典型情况）
                    has_strong_root_for_mediation = False
                    if day_master and year_branch:
                        life_stage = TWELVE_LIFE_STAGES.get((day_master, year_branch))
                        if life_stage in ['帝旺', '临官', '长生']:
                            has_strong_root_for_mediation = True
                    
                    # [V10.0] 检查大运是否有印星（丁火等）
                    has_luck_seal = False
                    if luck_pillar and len(luck_pillar) >= 2:
                        luck_stem = luck_pillar[0]
                        luck_stem_elem = self._get_element_str(luck_stem)
                        if luck_stem_elem == resource_element:
                            has_luck_seal = True
                    
                    # [V10.0] 检查流年地支是否是印星强根（午火等）
                    has_year_branch_seal = False
                    if branch_elem == resource_element:
                        has_year_branch_seal = True
                    
                    # [V10.0] 强制激活"制化豁免"协议
                    # 条件：七杀攻身 + (大运印星 OR 流年地支印星) + 强根
                    pathway_activated = False
                    if (has_seven_kill_mediation or has_luck_seal or has_year_branch_seal) and has_strong_root_for_mediation:
                        pathway_activated = True
                    
                    if pathway_activated:
                        # [V10.0] 核心分析师建议：应用"制化优先"原则
                        # 当流年见印星强根时，强制下调80%的惩罚，并赋予"名利双收"的加成
                        nonlinear_config = self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                        
                        # 1. 制化豁免：将七杀惩罚力度强制缩减 80%（根据核心分析师建议）
                        seal_conduction_multiplier = nonlinear_config.get('seal_conduction_multiplier', 1.7445)
                        reduction_factor = 0.80 * (seal_conduction_multiplier / 2.0)  # 根据优化参数调整，基础缩减80%
                        base_penalty = -20.0 * (1 - reduction_factor)  # 缩减80%
                        intensity = 0.05  # 极低强度
                        
                        # 重新计算惩罚
                        seven_kill_penalty, penalty_details = NonlinearActivation.calculate_penalty_nonlinear(
                            strength_normalized=strength_normalized,
                            penalty_type='seven_kill',
                            intensity=intensity,
                            has_help=False,
                            has_mediation=True,
                            base_penalty=base_penalty,
                            config=nonlinear_config
                        )
                        
                        # 2. 能量转化：将甲木的部分能量转化为名利加成
                        # 应用 opportunity_scaling 参数（贝叶斯优化结果：1.8952）
                        opportunity_scaling = nonlinear_config.get('opportunity_scaling', 1.8952)
                        luck_pillar_weight = 0.5 if has_luck_seal else 0.3
                        base_opportunity = 45.0 * luck_pillar_weight
                        opportunity_bonus = base_opportunity * opportunity_scaling
                        
                        # 3. 印星特权加成（贝叶斯优化结果：seal_bonus = 43.76）
                        seal_bonus = nonlinear_config.get('seal_bonus', 43.76)
                        seal_multiplier = nonlinear_config.get('seal_multiplier', 0.8538)
                        
                        # 先应用印星直接加成
                        wealth_energy += seal_bonus
                        
                        # 再应用机会加成
                        wealth_energy += opportunity_bonus
                        
                        # 最后应用印星乘数效应
                        wealth_energy = wealth_energy * seal_multiplier
                        
                        # [V10.0] 核心分析师建议：重新计算 final_index，确保加成生效
                        # 根据身强身弱情况，重新计算 final_index
                        if strength_normalized >= 0.5:
                            # 身强：直接使用财富能量
                            bonus = 1.2 if strength_normalized > 0.6 else 1.0
                            final_index = wealth_energy * bonus
                        else:
                            # 身弱：根据强根类型调整
                            if has_strong_root_for_mediation:
                                # 获取强根类型
                                life_stage_for_index = TWELVE_LIFE_STAGES.get((day_master, year_branch), None)
                                if life_stage_for_index == '临官':
                                    final_index = wealth_energy * 0.9
                                elif life_stage_for_index in ['帝旺', '长生']:
                                    final_index = wealth_energy * 1.0
                                else:
                                    final_index = wealth_energy * 0.9
                            else:
                                final_index = wealth_energy * 0.8
                        
                        # 标记触发事件
                        details.append(f"🌟 触发：食神制杀（化杀为权），财富阶跃({year_stem}克{day_master})[惩罚缩减: {seven_kill_penalty:.1f}, 印星加成: {seal_bonus:.1f}, 机会加成: {opportunity_bonus:.1f}, 乘数: {seal_multiplier:.4f}, 最终指数: {final_index:.1f}]")
                    else:
                        details.append(f"⚠️ 七杀攻身(有通关，影响减轻)({year_stem}克{day_master})[非线性模型: {seven_kill_penalty:.1f}]")
        
        # 如果七杀攻身且无通关且无特殊机制，直接应用惩罚（优先于其他因素）
        if seven_kill_attack and seven_kill_penalty < -50.0:
            # 七杀攻身是严重危机，直接返回负值
            return {
                'wealth_index': seven_kill_penalty,
                'details': details,
                'strength_score': strength_score,
                'strength_label': strength_label,
                'opportunity': wealth_energy if wealth_energy > 0 else 0.0
            }
        
        # F. [V61.0] 修复冲提纲判断：优先检查，优先于其他因素
        clash_commander = False
        has_mediation = False  # [V60.0] 检查是否有通关机制
        
        # 提前检查冲提纲（在计算财富能量之前）
        if month_branch and clashes.get(month_branch) == year_branch:
            clash_commander = True
            
            # [V61.6] 从 analyze 结果中检查是否有针对冲提纲的通关机制
            # 只有通关机制直接化解子午冲时，才能抵消冲提纲的影响
            trigger_events = result.get('trigger_events', [])
            for event in trigger_events:
                event_str = str(event)
                # 检查是否有关键字，但需要进一步判断是否针对冲提纲
                # 子午冲的通关：需要水（子）或火（午）作为通关神
                # 例如：子 -> 木 -> 午，或 午 -> 土 -> 子
                if '通关' in event_str or '官印相生' in event_str or '绝对通关' in event_str:
                    # [V61.6] 简化：如果有通关机制，暂时认为可以部分化解
                    # 但冲提纲的影响仍然存在，只是减轻
                    has_mediation = True
                    break
            
            # 也检查是否有官印相生（通关机制）
            if not has_mediation and luck_pillar and len(luck_pillar) >= 2:
                luck_stem = luck_pillar[0]
                luck_branch = luck_pillar[1]
                luck_stem_elem = self._get_element_str(luck_stem)
                luck_branch_elem = self._get_element_str(luck_branch)
                
                # 检查是否有官印相生（这是通关的一种）
                if resource_element and officer_element:
                    # 检查流年是否是官杀（天干或库）
                    year_is_officer_for_mediation = (stem_elem == officer_element)
                    year_branch_is_officer_vault_for_mediation = False
                    if year_branch in vaults:
                        vault_element_for_mediation = vault_elements.get(year_branch)
                        if vault_element_for_mediation and vault_element_for_mediation == officer_element:
                            year_branch_is_officer_vault_for_mediation = True
                    
                    # 检查大运是否是印星
                    luck_is_resource_for_mediation = (luck_stem_elem == resource_element or luck_branch_elem == resource_element)
                    
                    if (year_is_officer_for_mediation or year_branch_is_officer_vault_for_mediation) and luck_is_resource_for_mediation:
                        has_mediation = True
            
            # [V61.0] 冲提纲优先判断：如果无帮身且无通关，直接返回负值（一票否决）
            # 注意：这里需要先检查帮身，但帮身是在后面计算的，所以先检查是否有强根、印星、比劫
            # 临时检查是否有帮身（简化版，主要检查流年和大运）
            temp_has_help = False
            if day_master and year_branch:
                life_stage = TWELVE_LIFE_STAGES.get((day_master, year_branch))
                if life_stage in ['帝旺', '临官', '长生']:
                    temp_has_help = True
            if not temp_has_help:
                if stem_elem == resource_element or branch_elem == resource_element:
                    temp_has_help = True
                elif stem_elem == dm_element or branch_elem == dm_element:
                    temp_has_help = True
            if not temp_has_help and luck_pillar and len(luck_pillar) >= 2:
                luck_stem = luck_pillar[0]
                luck_branch = luck_pillar[1]
                luck_stem_elem = self._get_element_str(luck_stem)
                luck_branch_elem = self._get_element_str(luck_branch)
                if luck_stem_elem == resource_element or luck_branch_elem == resource_element:
                    temp_has_help = True
                elif luck_stem_elem == dm_element or luck_branch_elem == dm_element:
                    temp_has_help = True
                if day_master and luck_branch:
                    luck_life_stage = TWELVE_LIFE_STAGES.get((day_master, luck_branch))
                    if luck_life_stage in ['帝旺', '临官', '长生']:
                        temp_has_help = True
            
            # [V10.0] 使用非线性模型替代硬编码 if/else
            # [V10.0] 优化：身强且有印星通关时，冲提纲转为正面机会
            # 计算冲提纲的惩罚强度
            clash_intensity = 1.0  # 冲提纲的强度最高
            
            # [V10.0] 关键优化：身强且有印星通关时，大幅降低惩罚
            # 检查是否有印星通关（大运或流年）
            has_seal_mediation = False
            if luck_pillar and len(luck_pillar) >= 2:
                luck_stem_elem = self._get_element_str(luck_pillar[0])
                luck_branch_elem = self._get_element_str(luck_pillar[1])
                if luck_stem_elem == resource_element or luck_branch_elem == resource_element:
                    has_seal_mediation = True
            if branch_elem == resource_element or stem_elem == resource_element:
                has_seal_mediation = True
            
            # [V10.0] 身强且有印星通关时，冲提纲转为"变动中的机会"
            # [V10.0] 优化：对于身极强（strength_normalized > 0.9）且有印星通关的情况，进一步降低惩罚
            if strength_normalized >= 0.9 and has_seal_mediation:
                # 身极强且有印星通关：冲提纲转为正面机会
                base_penalty = -10.0  # 极低惩罚（从-120降到-10）
                clash_intensity = 0.1  # 极低强度
                details.append(f"🌟 冲提纲(身极强+印星通关，转为机会)({year_branch}冲{month_branch})")
            elif strength_normalized >= 0.7 and has_seal_mediation:
                # 身强且有印星通关：冲提纲转为变动中的机会
                base_penalty = -20.0  # 大幅降低惩罚（从-120降到-20）
                clash_intensity = 0.2  # 降低强度
                details.append(f"🌟 冲提纲(身强+印星通关，转为机会)({year_branch}冲{month_branch})")
            elif strength_normalized >= 0.5 and has_seal_mediation:
                # 身稍强且有印星通关：冲提纲惩罚减轻
                base_penalty = -30.0  # 降低惩罚（从-120降到-30）
                clash_intensity = 0.3  # 降低强度
                details.append(f"🌟 冲提纲(身稍强+印星通关，转为机会)({year_branch}冲{month_branch})")
            elif strength_normalized >= 0.9:
                # 身极强但无印星通关：惩罚仍然大幅降低
                base_penalty = -40.0 if treasury_collapsed else -30.0
                clash_intensity = 0.4
                details.append(f"⚠️ 冲提纲(身极强，影响减轻)({year_branch}冲{month_branch})")
            elif strength_normalized >= 0.7:
                # 身强但无印星通关：惩罚适度降低
                base_penalty = -60.0 if treasury_collapsed else -50.0
                clash_intensity = 0.6
                details.append(f"⚠️ 冲提纲(身强，影响减轻)({year_branch}冲{month_branch})")
            else:
                base_penalty = -150.0 if treasury_collapsed else -120.0
            
            clash_penalty_value, penalty_details = NonlinearActivation.calculate_penalty_nonlinear(
                strength_normalized=strength_normalized,
                penalty_type='clash_commander',
                intensity=clash_intensity,
                has_help=temp_has_help,
                has_mediation=has_mediation or has_seal_mediation,  # [V10.0] 包含印星通关
                base_penalty=base_penalty,
                config=self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
            )
            
            # [V10.0] 优化：身强且有印星通关时，不直接返回，继续计算其他因素
            if not temp_has_help and not has_mediation and not (strength_normalized >= 0.5 and has_seal_mediation):
                # 无帮身且无通关且非身强印星通关：毁灭性打击，直接返回负值
                if treasury_collapsed:
                    details.append(f"💀 冲提纲+库塌(双重灾难)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                else:
                    details.append(f"💀 灾难: 冲提纲(结构崩塌)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                
                # [V61.0] 直接返回，不再计算其他因素
                return {
                    'wealth_index': clash_penalty_value,
                    'details': details,
                    'strength_score': strength_score,
                    'strength_label': strength_label,
                    'opportunity': wealth_energy if wealth_energy > 0 else 0.0
                }
            elif not has_mediation:
                # [V61.5] 有帮身但无通关：冲提纲仍有严重惩罚，但可以部分抵消
                # [V61.16] 如果有特殊机制（开库、双库共振等），冲提纲的惩罚应该减轻
                if treasury_opened:
                    # 有开库：冲提纲的影响被开库抵消大部分
                    clash_penalty_value = -40.0 if treasury_collapsed else -30.0
                    if treasury_collapsed:
                        details.append(f"⚠️ 冲提纲+库塌(有帮身和开库，影响减轻)({year_branch}冲{month_branch})")
                    else:
                        details.append(f"⚠️ 冲提纲(有帮身和开库，影响减轻)({year_branch}冲{month_branch})")
                    # 应用惩罚，但不直接返回，继续计算其他因素
                    final_index = clash_penalty_value
                    # 继续正常计算，但冲提纲惩罚已应用
                else:
                    # 无开库：冲提纲仍有严重惩罚
                    # [V61.17] 如果有强根或印星帮身，冲提纲的惩罚应该减轻，并且应该继续计算其他正面因素
                    # 检查是否有强根或印星帮身
                    has_strong_help = False
                    if strong_root_type in ['帝旺', '临官', '长生']:
                        has_strong_help = True
                    # 检查大运是否是印星
                    if luck_pillar and len(luck_pillar) >= 2:
                        luck_stem = luck_pillar[0]
                        luck_stem_elem = self._get_element_str(luck_stem)
                        if luck_stem_elem == resource_element:
                            has_strong_help = True
                    
                    if has_strong_help:
                        # 有强根或印星帮身：冲提纲的惩罚减轻，但继续计算其他因素
                        # [V10.0] 使用非线性模型的结果，而不是硬编码值
                        # clash_penalty_value 已经在前面通过 NonlinearActivation.calculate_penalty_nonlinear 计算
                        # 对于有强根或印星帮身的情况，非线性模型已经考虑了这些因素
                        if treasury_collapsed:
                            details.append(f"⚠️ 冲提纲+库塌(有强根/印星帮身，影响减轻)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                        else:
                            details.append(f"⚠️ 冲提纲(有强根/印星帮身，影响减轻)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                        # 应用惩罚，但不直接返回，继续计算其他因素
                        # [V10.0] 对于身强的情况，final_index 应该先被设置为 wealth_energy * bonus，然后再加上 clash_penalty_value
                        # 但是，由于冲提纲的惩罚是在 final_index 计算之后应用的，所以这里应该累加，而不是覆盖
                        # 注意：final_index 已经在 D 部分（第3743行）被设置为 wealth_energy * bonus
                        final_index += clash_penalty_value
                        # 继续正常计算，但冲提纲惩罚已应用
                    else:
                        # 无强根或印星帮身：冲提纲仍有严重惩罚
                        # [V10.0] 使用非线性模型的结果，而不是硬编码值
                        # clash_penalty_value 已经在前面通过 NonlinearActivation.calculate_penalty_nonlinear 计算
                        # 对于身强的情况，非线性模型已经根据身强程度降低了惩罚
                        if strength_normalized >= 0.7:
                            # 身强：使用非线性模型的结果，继续计算其他因素
                            if treasury_collapsed:
                                details.append(f"⚠️ 冲提纲+库塌(身强，影响减轻)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                            else:
                                details.append(f"⚠️ 冲提纲(身强，影响减轻)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                            # 应用惩罚，但不直接返回，继续计算其他因素
                            # [V10.0] 对于身强的情况，final_index 应该先被设置为 wealth_energy * bonus，然后再加上 clash_penalty_value
                            # 注意：final_index 已经在 D 部分（第3743行）被设置为 wealth_energy * bonus
                            final_index += clash_penalty_value
                        else:
                            # 身弱或身稍强：冲提纲仍有严重惩罚
                            if treasury_collapsed:
                                details.append(f"💀 冲提纲+库塌(有帮身但仍有严重损失)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                            else:
                                details.append(f"💀 冲提纲(有帮身但结构受损)({year_branch}冲{month_branch})[非线性模型: {clash_penalty_value:.1f}]")
                            
                            # 应用冲提纲惩罚到 final_index
                            final_index = clash_penalty_value
                            # 不再计算其他正面因素（冲提纲优先）
                            return {
                                'wealth_index': final_index,
                                'details': details,
                                'strength_score': strength_score,
                                'strength_label': strength_label,
                                'opportunity': wealth_energy if wealth_energy > 0 else 0.0
                            }
            else:
                # [V10.0] 有通关：冲提纲的影响被部分化解或转为机会
                # [V61.6] 有通关但冲提纲影响仍然存在，只是减轻
                # [V61.15] 如果有特殊机制（开库、双库共振等），冲提纲的惩罚应该大幅减轻
                
                # [V10.0] 关键优化：身强且有印星通关时，冲提纲转为正面机会
                if strength_normalized >= 0.5 and has_seal_mediation:
                    # 身强且有印星通关：冲提纲转为正面机会
                    # [V10.0] 应用贝叶斯优化参数：opportunity_scaling = 1.8952
                    nonlinear_config = self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
                    opportunity_scaling = nonlinear_config.get('opportunity_scaling', 1.8952)
                    base_opportunity = 40.0  # 基础机会加成
                    opportunity_bonus = base_opportunity * opportunity_scaling
                    
                    # 应用印星特权加成（贝叶斯优化结果：seal_bonus = 43.76）
                    seal_bonus = nonlinear_config.get('seal_bonus', 43.76)
                    seal_multiplier = nonlinear_config.get('seal_multiplier', 0.8538)
                    
                    # 先应用印星直接加成
                    wealth_energy += seal_bonus
                    
                    # 再应用机会加成
                    wealth_energy += opportunity_bonus
                    
                    # 最后应用印星乘数效应
                    wealth_energy = wealth_energy * seal_multiplier
                    
                    # [V10.0] 核心分析师建议：重新计算 final_index，确保加成生效
                    # 根据身强身弱情况，重新计算 final_index
                    if strength_normalized >= 0.5:
                        # 身强：直接使用财富能量
                        bonus = 1.2 if strength_normalized > 0.6 else 1.0
                        final_index = wealth_energy * bonus
                    else:
                        # 身弱：根据强根类型调整
                        final_index = wealth_energy * 0.9
                    
                    # 更新详情
                    details.append(f"💰 冲提纲转为机会加成: {opportunity_bonus:.1f} (缩放: {opportunity_scaling:.4f})")
                    details.append(f"💰 印星特权加成: {seal_bonus:.1f}, 乘数: {seal_multiplier:.4f}, 最终指数: {final_index:.1f}")
                    
                    # 跳过后续的惩罚逻辑
                    pass
                elif treasury_opened:
                    # 有开库：冲提纲的影响被开库抵消大部分
                    clash_penalty = -20.0 if treasury_collapsed else -15.0
                    if treasury_collapsed:
                        details.append(f"⚠️ 冲提纲+库塌(有通关和开库，影响减轻)({year_branch}冲{month_branch})")
                    else:
                        details.append(f"⚠️ 冲提纲(有通关和开库，影响减轻)({year_branch}冲{month_branch})")
                    # 应用冲提纲惩罚（在final_index计算之后）
                    final_index += clash_penalty
                else:
                    # 无开库且非身强印星通关：冲提纲的惩罚应该仍然应用，但可以部分抵消
                    clash_penalty = -60.0 if treasury_collapsed else -50.0
                    if treasury_collapsed:
                        details.append(f"⚠️ 冲提纲+库塌(有通关但仍有损失)({year_branch}冲{month_branch})")
                    else:
                        details.append(f"⚠️ 冲提纲(有通关但结构受损)({year_branch}冲{month_branch})")
                    # 应用冲提纲惩罚（在final_index计算之后）
                    final_index += clash_penalty
                # 继续正常计算，但冲提纲惩罚已应用（如果适用）
        
        # G. [V10.0] 非线性阻尼机制 - 防止过拟合（核心分析师建议）
        # 在能量超过80分后自动减缓增长斜率，以实现三年的整体平衡
        nonlinear_config = self.config.get('nonlinear', {}) if hasattr(self, 'config') else {}
        damping_config = nonlinear_config.get('nonlinear_damping', {})
        
        if damping_config.get('enabled', True):
            damping_threshold = damping_config.get('threshold', 80.0)
            damping_rate = damping_config.get('damping_rate', 0.3)
            max_value = damping_config.get('max_value', 100.0)
            
            if final_index > damping_threshold:
                # 计算超出阈值的部分
                excess = final_index - damping_threshold
                # 应用非线性阻尼：超出部分按阻尼率缩减
                damped_excess = excess * (1.0 - damping_rate)
                final_index = damping_threshold + damped_excess
                details.append(f"🔧 非线性阻尼(阈值: {damping_threshold:.1f}, 阻尼率: {damping_rate:.2f}, 调整后: {final_index:.2f})")
            
            # 硬上限限制
            if final_index > max_value:
                final_index = max_value
                details.append(f"🔧 硬上限限制: {max_value:.1f}")
        
        # G. 限制范围（保持原有的下限限制）
        final_index = max(-100.0, min(100.0, final_index))
        
        # [V10.0] 贝叶斯推理：计算置信区间
        # 检测关键机制以估计不确定性
        has_clash = clash_commander if 'clash_commander' in locals() else False
        has_trine_detected = any('三刑' in d or 'trine' in d.lower() for d in details)
        
        uncertainty_factors = BayesianInference.estimate_uncertainty_factors(
            strength_normalized=strength_normalized,
            clash_intensity=1.0 if has_clash else 0.0,
            has_trine=has_trine_detected,
            has_mediation=has_mediation if 'has_mediation' in locals() else False,
            has_help=has_help if 'has_help' in locals() else False
        )
        
        confidence_interval = BayesianInference.calculate_confidence_interval(
            point_estimate=final_index,
            uncertainty_factors=uncertainty_factors,
            confidence_level=0.95
        )
        
        # [V10.1] 计算概率分布（如果启用）
        probabilistic_config = self.config.get('probabilistic_energy', {})
        use_probabilistic = probabilistic_config.get('use_probabilistic_energy', False)
        wealth_distribution = None
        
        if use_probabilistic:
            # 定义参数扰动范围
            parameter_ranges = {
                'strength_normalized': (
                    max(0.0, strength_normalized - 0.1),
                    min(1.0, strength_normalized + 0.1)
                ),
                'clash_intensity': (0.8, 1.2) if has_clash else (0.0, 0.2),
                'trine_effect': (0.0, 1.0) if has_trine_detected else (0.0, 0.1),
            }
            
            # 蒙特卡洛模拟生成概率分布
            monte_carlo_result = BayesianInference.monte_carlo_simulation(
                base_estimate=final_index,
                parameter_ranges=parameter_ranges,
                n_samples=1000,
                confidence_level=0.95
            )
            
            wealth_distribution = {
                "mean": monte_carlo_result.get('mean', final_index),
                "std": monte_carlo_result.get('std', uncertainty_factors.get('base_uncertainty', 5.0)),
                "percentiles": monte_carlo_result.get('percentiles', {}),
                "samples_count": 1000
            }
        
        return {
            "wealth_index": final_index,  # 点估计（向后兼容）
            "details": details,
            "opportunity": wealth_energy,
            "capacity": -1.2 if strength_normalized < 0.45 and wealth_energy > 0 else (1.2 if strength_normalized > 0.6 else 1.0),
            "strength_score": strength_score,
            "strength_label": strength_label,
            # [V10.0] 贝叶斯推理结果
            "confidence_interval": confidence_interval,
            "uncertainty_factors": uncertainty_factors,
            # [V10.1] 概率分布（如果启用）
            "wealth_distribution": wealth_distribution
        }

