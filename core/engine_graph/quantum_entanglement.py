"""
量子纠缠模块 (Quantum Entanglement)
===================================

负责检测和应用干支的合化与刑冲（三会、三合、半合、拱合、六合、天干五合）

在传播之前，只应用一次！
合化是结构性的，只应计算一次，不应在循环中重复应用。
合化增益应该作为一次性修正应用到初始能量（H0），而不是通过矩阵乘法重复应用。
"""

from typing import Dict, List, Any, Set
from core.prob_math import ProbValue
from core.interactions import BRANCH_SIX_COMBINES, STEM_COMBINATIONS


class QuantumEntanglementProcessor:
    """量子纠缠处理器"""
    
    def __init__(self, engine: 'GraphNetworkEngine'):
        """
        初始化量子纠缠处理器
        
        Args:
            engine: GraphNetworkEngine 实例
        """
        self.engine = engine
        self.config = engine.config
    
    def apply_once(self):
        """
        [V15.3] 应用量子纠缠（合化/刑冲）- 在传播之前，只应用一次！
        
        检测并应用：
        1. 三会方局（directionalBonus ~3.0）
        2. 三合局（threeHarmony.bonus ~2.0）
        3. 半合（halfHarmony.bonus ~1.4）
        4. 拱合（archHarmony.bonus ~1.1）
        5. 六合（sixHarmony.bonus ~1.3, bindingPenalty ~0.1）
        6. 天干五合（stemFiveCombination.bonus/penalty）
        """
        if not hasattr(self.engine, 'H0') or self.engine.H0 is None:
            return
        
        interactions_config = self.config.get('interactions', {})
        branch_events = interactions_config.get('branchEvents', {})
        combo_physics = interactions_config.get('comboPhysics', {})
        
        # 1. 检测地支合局（三合、三会、半合、拱合、六合）
        # [V15.3] 三会局定义（方局，力量最强）
        three_meeting_groups = [
            {'亥', '子', '丑'},  # 三会水（北方）
            {'寅', '卯', '辰'},  # 三会木（东方）
            {'巳', '午', '未'},  # 三会火（南方）
            {'申', '酉', '戌'},  # 三会金（西方）
        ]
        
        # 三合局定义
        trine_groups = [
            {'申', '子', '辰'},  # 三合水
            {'亥', '卯', '未'},  # 三合木
            {'寅', '午', '戌'},  # 三合火
            {'巳', '酉', '丑'},  # 三合金
        ]
        
        # 半合定义
        half_harmony_pairs = [
            ('申', '子'), ('子', '申'), ('子', '辰'), ('辰', '子'),
            ('亥', '卯'), ('卯', '亥'), ('卯', '未'), ('未', '卯'),
            ('寅', '午'), ('午', '寅'), ('午', '戌'), ('戌', '午'),
            ('巳', '酉'), ('酉', '巳'), ('酉', '丑'), ('丑', '酉'),
        ]
        
        # 拱合定义
        arch_harmony_pairs = [
            ('申', '辰'), ('辰', '申'),
            ('亥', '未'), ('未', '亥'),
            ('寅', '戌'), ('戌', '寅'),
            ('巳', '丑'), ('丑', '巳'),
        ]
        
        # 收集所有地支节点
        branch_nodes = [(i, node) for i, node in enumerate(self.engine.nodes) 
                       if node.node_type == 'branch']
        branch_chars = {node.char for _, node in branch_nodes}
        
        # [V15.3] 调试信息：记录检测到的合局
        debug_info = {
            'detected_matches': [],
            'node_changes': [],
            'energy_snapshots': {}
        }
        
        # [V15.3] 三会局对应的元素映射
        three_meeting_element_map = {
            frozenset({'亥', '子', '丑'}): 'water',  # 三会水（北方）
            frozenset({'寅', '卯', '辰'}): 'wood',   # 三会木（东方）
            frozenset({'巳', '午', '未'}): 'fire',   # 三会火（南方）
            frozenset({'申', '酉', '戌'}): 'metal',  # 三会金（西方）
        }
        
        # [V15.3] 检测三会局（优先级最高，力量最强）
        for group in three_meeting_groups:
            group_frozen = frozenset(group)
            if group.issubset(branch_chars):
                meeting_node_indices = [i for i, node in branch_nodes if node.char in group]
                if len(meeting_node_indices) >= 3:
                    # [V15.3] 三会方局：使用 directionalBonus (3.0)，力量最强
                    # 从 comboPhysics 读取 directionalBonus，如果没有则使用 threeMeeting.bonus
                    if isinstance(combo_physics, dict) and 'directionalBonus' in combo_physics:
                        meeting_bonus = combo_physics.get('directionalBonus', 3.0)
                    else:
                        three_meeting_config = branch_events.get('threeMeeting', {})
                        if isinstance(three_meeting_config, dict):
                            meeting_bonus = three_meeting_config.get('bonus', 2.5)
                        else:
                            meeting_bonus = 3.0  # 默认使用 3.0（三会方局力量最强）
                    
                    three_meeting_config = branch_events.get('threeMeeting', {})
                    if isinstance(three_meeting_config, dict):
                        should_transform = three_meeting_config.get('transform', True)
                    else:
                        should_transform = True
                    
                    meeting_element = three_meeting_element_map.get(group_frozen, None)
                    group_str = '-'.join(sorted(group))
                    debug_info['detected_matches'].append(f"ThreeMeeting: {group_str} ({meeting_element})")
                    
                    # 应用 Bonus 到所有三会节点
                    for idx in meeting_node_indices:
                        old_element = self.engine.nodes[idx].element
                        if isinstance(self.engine.H0[idx], ProbValue):
                            self.engine.H0[idx] = self.engine.H0[idx] * meeting_bonus
                        else:
                            self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * meeting_bonus, std_dev_percent=0.1)
                        self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
                        self.engine.nodes[idx].current_energy = self.engine.H0[idx]
                        
                        # [V15.3] 元素转化：改变节点五行属性
                        if should_transform and meeting_element:
                            self.engine.nodes[idx].element = meeting_element
                            self.engine.nodes[idx].original_element = old_element  # 保存原始元素
                            debug_info['node_changes'].append(f"{self.engine.nodes[idx].char}({old_element}) -> {self.engine.nodes[idx].char}({meeting_element})")
                    
                    # 同时增强所有同元素的天干节点
                    if meeting_element:
                        for i, node in enumerate(self.engine.nodes):
                            if node.node_type == 'stem' and node.element == meeting_element:
                                if isinstance(self.engine.H0[i], ProbValue):
                                    self.engine.H0[i] = self.engine.H0[i] * meeting_bonus
                                else:
                                    self.engine.H0[i] = ProbValue(float(self.engine.H0[i]) * meeting_bonus, std_dev_percent=0.1)
                                self.engine.nodes[i].initial_energy = self.engine.H0[i]
                                self.engine.nodes[i].current_energy = self.engine.H0[i]
        
        # 检测三合局（完整三合）
        trine_element_map = {
            frozenset({'申', '子', '辰'}): 'water',  # 三合水
            frozenset({'亥', '卯', '未'}): 'wood',   # 三合木
            frozenset({'寅', '午', '戌'}): 'fire',   # 三合火
            frozenset({'巳', '酉', '丑'}): 'metal',  # 三合金
        }
        
        for group in trine_groups:
            group_frozen = frozenset(group)
            if group.issubset(branch_chars):
                trine_node_indices = [i for i, node in branch_nodes if node.char in group]
                if len(trine_node_indices) >= 3:
                    three_harmony_config = branch_events.get('threeHarmony', {})
                    if isinstance(three_harmony_config, dict):
                        three_bonus = three_harmony_config.get('bonus', 2.0)
                        should_transform = three_harmony_config.get('transform', True)
                    else:
                        three_bonus = 2.0
                        should_transform = True
                    
                    trine_element = trine_element_map.get(group_frozen, None)
                    group_str = '-'.join(sorted(group))
                    debug_info['detected_matches'].append(f"ThreeHarmony: {group_str} ({trine_element})")
                    
                    # 应用 Bonus 到所有三合节点
                    for idx in trine_node_indices:
                        old_element = self.engine.nodes[idx].element
                        if isinstance(self.engine.H0[idx], ProbValue):
                            self.engine.H0[idx] = self.engine.H0[idx] * three_bonus
                        else:
                            self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * three_bonus, std_dev_percent=0.1)
                        self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
                        self.engine.nodes[idx].current_energy = self.engine.H0[idx]
                        
                        if should_transform and trine_element:
                            self.engine.nodes[idx].element = trine_element
                            self.engine.nodes[idx].original_element = old_element
                            debug_info['node_changes'].append(f"{self.engine.nodes[idx].char}({old_element}) -> {self.engine.nodes[idx].char}({trine_element})")
                    
                    # 同时增强所有同元素的天干节点
                    if trine_element:
                        for i, node in enumerate(self.engine.nodes):
                            if node.node_type == 'stem' and node.element == trine_element:
                                if isinstance(self.engine.H0[i], ProbValue):
                                    self.engine.H0[i] = self.engine.H0[i] * three_bonus
                                else:
                                    self.engine.H0[i] = ProbValue(float(self.engine.H0[i]) * three_bonus, std_dev_percent=0.1)
                                self.engine.nodes[i].initial_energy = self.engine.H0[i]
                                self.engine.nodes[i].current_energy = self.engine.H0[i]
        
        # 检测半合
        half_harmony_element_map = {
            ('申', '子'): 'water', ('子', '申'): 'water', ('子', '辰'): 'water', ('辰', '子'): 'water',
            ('亥', '卯'): 'wood', ('卯', '亥'): 'wood', ('卯', '未'): 'wood', ('未', '卯'): 'wood',
            ('寅', '午'): 'fire', ('午', '寅'): 'fire', ('午', '戌'): 'fire', ('戌', '午'): 'fire',
            ('巳', '酉'): 'metal', ('酉', '巳'): 'metal', ('酉', '丑'): 'metal', ('丑', '酉'): 'metal',
        }
        
        for (branch1, branch2) in half_harmony_pairs:
            if branch1 in branch_chars and branch2 in branch_chars:
                node1_idx = next((i for i, node in branch_nodes if node.char == branch1), None)
                node2_idx = next((i for i, node in branch_nodes if node.char == branch2), None)
                if node1_idx is not None and node2_idx is not None:
                    half_harmony_config = branch_events.get('halfHarmony', {})
                    if isinstance(half_harmony_config, dict):
                        half_bonus = half_harmony_config.get('bonus', 1.4)
                        should_transform = half_harmony_config.get('transform', True)
                    else:
                        half_bonus = 1.4
                        should_transform = False
                    
                    half_element = half_harmony_element_map.get((branch1, branch2), None)
                    pair_str = f"{branch1}-{branch2}"
                    if half_element:
                        debug_info['detected_matches'].append(f"HalfHarmony: {pair_str} ({half_element})")
                    
                    # 应用 Bonus
                    for idx in [node1_idx, node2_idx]:
                        old_element = self.engine.nodes[idx].element
                        if isinstance(self.engine.H0[idx], ProbValue):
                            self.engine.H0[idx] = self.engine.H0[idx] * half_bonus
                        else:
                            self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * half_bonus, std_dev_percent=0.1)
                        self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
                        self.engine.nodes[idx].current_energy = self.engine.H0[idx]
                        
                        if should_transform and half_element:
                            self.engine.nodes[idx].element = half_element
                            self.engine.nodes[idx].original_element = old_element
                            debug_info['node_changes'].append(f"{self.engine.nodes[idx].char}({old_element}) -> {self.engine.nodes[idx].char}({half_element})")
        
        # 检测拱合
        arch_harmony_element_map = {
            ('申', '辰'): 'water', ('辰', '申'): 'water',
            ('亥', '未'): 'wood', ('未', '亥'): 'wood',
            ('寅', '戌'): 'fire', ('戌', '寅'): 'fire',
            ('巳', '丑'): 'metal', ('丑', '巳'): 'metal',
        }
        
        for (branch1, branch2) in arch_harmony_pairs:
            if branch1 in branch_chars and branch2 in branch_chars:
                node1_idx = next((i for i, node in branch_nodes if node.char == branch1), None)
                node2_idx = next((i for i, node in branch_nodes if node.char == branch2), None)
                if node1_idx is not None and node2_idx is not None:
                    arch_harmony_config = branch_events.get('archHarmony', {})
                    if isinstance(arch_harmony_config, dict):
                        arch_bonus = arch_harmony_config.get('bonus', 1.1)
                        should_transform = arch_harmony_config.get('transform', True)
                    else:
                        arch_bonus = 1.1
                        should_transform = False
                    
                    arch_element = arch_harmony_element_map.get((branch1, branch2), None)
                    pair_str = f"{branch1}-{branch2}"
                    if arch_element:
                        debug_info['detected_matches'].append(f"ArchHarmony: {pair_str} ({arch_element})")
                    
                    # 应用 Bonus
                    for idx in [node1_idx, node2_idx]:
                        old_element = self.engine.nodes[idx].element
                        if isinstance(self.engine.H0[idx], ProbValue):
                            self.engine.H0[idx] = self.engine.H0[idx] * arch_bonus
                        else:
                            self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * arch_bonus, std_dev_percent=0.1)
                        self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
                        self.engine.nodes[idx].current_energy = self.engine.H0[idx]
                        
                        if should_transform and arch_element:
                            self.engine.nodes[idx].element = arch_element
                            self.engine.nodes[idx].original_element = old_element
                            debug_info['node_changes'].append(f"{self.engine.nodes[idx].char}({old_element}) -> {self.engine.nodes[idx].char}({arch_element})")
        
        # 检测六合
        six_combine_element_map = {
            frozenset({'子', '丑'}): 'earth',  # 子丑合土
            frozenset({'寅', '亥'}): 'wood',   # 寅亥合木
            frozenset({'卯', '戌'}): 'fire',   # 卯戌合火
            frozenset({'辰', '酉'}): 'metal',  # 辰酉合金
            frozenset({'巳', '申'}): 'water',  # 巳申合水
            frozenset({'午', '未'}): 'earth',  # 午未合土
        }
        
        for branch1, branch2 in BRANCH_SIX_COMBINES.items():
            if branch1 in branch_chars and branch2 in branch_chars:
                node1_idx = next((i for i, node in branch_nodes if node.char == branch1), None)
                node2_idx = next((i for i, node in branch_nodes if node.char == branch2), None)
                if node1_idx is not None and node2_idx is not None:
                    six_harmony_config = branch_events.get('sixHarmony', {})
                    if isinstance(six_harmony_config, dict):
                        six_bonus = six_harmony_config.get('bonus', 1.3)
                        should_transform = six_harmony_config.get('transform', True)
                    else:
                        six_bonus = 1.3
                        should_transform = False
                    
                    combine_element = six_combine_element_map.get(frozenset({branch1, branch2}), None)
                    pair_str = f"{branch1}-{branch2}"
                    if combine_element:
                        debug_info['detected_matches'].append(f"SixHarmony: {pair_str} ({combine_element})")
                    
                    # 应用 Bonus
                    for idx in [node1_idx, node2_idx]:
                        old_element = self.engine.nodes[idx].element
                        if isinstance(self.engine.H0[idx], ProbValue):
                            self.engine.H0[idx] = self.engine.H0[idx] * six_bonus
                        else:
                            self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * six_bonus, std_dev_percent=0.1)
                        self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
                        self.engine.nodes[idx].current_energy = self.engine.H0[idx]
                        
                        if should_transform and combine_element:
                            self.engine.nodes[idx].element = combine_element
                            self.engine.nodes[idx].original_element = old_element
                            debug_info['node_changes'].append(f"{self.engine.nodes[idx].char}({old_element}) -> {self.engine.nodes[idx].char}({combine_element})")
        
        # 检测天干五合
        stem_combine_element_map = {
            ('甲', '己'): 'earth', ('己', '甲'): 'earth',  # 甲己合土
            ('乙', '庚'): 'metal', ('庚', '乙'): 'metal',  # 乙庚合金
            ('丙', '辛'): 'water', ('辛', '丙'): 'water',  # 丙辛合水
            ('丁', '壬'): 'wood', ('壬', '丁'): 'wood',   # 丁壬合木
            ('戊', '癸'): 'fire', ('癸', '戊'): 'fire',   # 戊癸合火
        }
        
        # 天干五合月令支持映射
        stem_combine_month_support = {
            'earth': ['辰', '未', '戌', '丑', '巳', '午'],  # 土月或火月
            'metal': ['申', '酉', '辰', '未', '戌', '丑'],  # 金月或土月
            'water': ['亥', '子', '申', '酉'],              # 水月或金月
            'wood': ['寅', '卯', '亥', '子'],               # 木月或水月
            'fire': ['巳', '午', '寅', '卯'],               # 火月或木月
        }
        
        # 获取月支
        month_branch = None
        if self.engine.bazi and len(self.engine.bazi) > 1:
            month_pillar = self.engine.bazi[1]
            if len(month_pillar) >= 2:
                month_branch = month_pillar[1]
        
        # 收集所有天干节点
        stem_nodes = [(i, node) for i, node in enumerate(self.engine.nodes) 
                     if node.node_type == 'stem']
        
        # 检测天干五合
        for i, (idx1, node1) in enumerate(stem_nodes):
            for j, (idx2, node2) in enumerate(stem_nodes):
                if i >= j:
                    continue
                
                stem1 = node1.char
                stem2 = node2.char
                
                # 检查是否是天干五合
                if (stem1, stem2) in stem_combine_element_map or (stem2, stem1) in stem_combine_element_map:
                    target_element = stem_combine_element_map.get((stem1, stem2)) or stem_combine_element_map.get((stem2, stem1))
                    
                    stem_combo_config = interactions_config.get('stemFiveCombination', {})
                    if not stem_combo_config:
                        stem_combo_config = interactions_config.get('stemFiveCombine', {})
                    
                    # [V15.3] 检查月令是否支持合化
                    can_transform = False
                    if month_branch and target_element:
                        supported_months = stem_combine_month_support.get(target_element, [])
                        can_transform = month_branch in supported_months
                    
                    # [V15.3] 根据合化结果应用不同的处理
                    if can_transform:
                        # 合化成功：应用 Bonus（合化产生新能量）
                        bonus = stem_combo_config.get('transformBonus', stem_combo_config.get('bonus', 1.2))
                        pair_str = f"{stem1}-{stem2}"
                        debug_info['detected_matches'].append(f"StemFiveCombine: {pair_str} -> {target_element} (成功)")
                        
                        for idx in [idx1, idx2]:
                            old_element = self.engine.nodes[idx].element
                            if isinstance(self.engine.H0[idx], ProbValue):
                                self.engine.H0[idx] = self.engine.H0[idx] * bonus
                            else:
                                self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * bonus, std_dev_percent=0.1)
                            self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
                            self.engine.nodes[idx].current_energy = self.engine.H0[idx]
                            
                            # [V15.3] 元素转化：改变节点五行属性
                            if target_element:
                                self.engine.nodes[idx].element = target_element
                                self.engine.nodes[idx].original_element = old_element
                                debug_info['node_changes'].append(f"{self.engine.nodes[idx].char}({old_element}) -> {self.engine.nodes[idx].char}({target_element})")
                    else:
                        # 合而不化：形成羁绊，双方能量受损
                        penalty = stem_combo_config.get('penalty', 0.8)  # 默认减少到80%
                        pair_str = f"{stem1}-{stem2}"
                        debug_info['detected_matches'].append(f"StemFiveCombine: {pair_str} -> {target_element} (失败-羁绊)")
                        
                        for idx in [idx1, idx2]:
                            if isinstance(self.engine.H0[idx], ProbValue):
                                self.engine.H0[idx] = self.engine.H0[idx] * penalty
                            else:
                                self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * penalty, std_dev_percent=0.1)
                            self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
                            self.engine.nodes[idx].current_energy = self.engine.H0[idx]
                            debug_info['node_changes'].append(f"{self.engine.nodes[idx].char}(羁绊-能量受损)")
        
        # [V15.3] 保存调试信息到引擎（用于后续输出）
        self.engine._quantum_entanglement_debug = debug_info

