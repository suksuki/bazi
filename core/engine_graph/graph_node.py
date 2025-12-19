"""
图网络节点定义
==============

定义 GraphNode 类，表示图网络中的一个节点（八字粒子）。
"""

from core.prob_math import ProbValue


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
        
        # V13.0: 初始能量（在 Phase 1 中计算）- 使用 ProbValue 表示概率分布
        self.initial_energy = ProbValue(0.0, std_dev_percent=0.1)
        
        # V13.0: 当前能量（在 Phase 3 传播中更新）- 使用 ProbValue 表示概率分布
        self.current_energy = ProbValue(0.0, std_dev_percent=0.1)
        
        # 节点属性（用于物理规则）
        self.has_root = False  # 是否有通根
        self.is_same_pillar = False  # 是否自坐强根
        self.is_exposed = False  # 是否透干
        self.hidden_stems_energy = {}  # 藏干能量分布（壳核模型）

