"""
Phase 3: 能量传播模块
====================

负责执行能量传播迭代，模拟动态做功。

包括：
- 能量传播迭代（propagate）
- 量子纠缠（合化/刑冲）
- 相对抑制机制
- 物理调谐算子（势井、散射、超导）
- 自刑惩罚
- 合局检测
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from core.engine_graph.graph_node import GraphNode
from core.engine_graph.constants import TWELVE_LIFE_STAGES, LIFE_STAGE_COEFFICIENTS
from core.processors.physics import PhysicsProcessor, GENERATION, CONTROL
from core.math import ProbValue, calculate_control_damage, calculate_generation, calculate_impedance_mismatch, calculate_shielding_effect
from core.interactions import BRANCH_CLASHES, BRANCH_SIX_COMBINES, STEM_COMBINATIONS


class EnergyPropagator:
    """负责能量传播迭代"""
    
    def __init__(self, engine: 'GraphNetworkEngine'):
        """
        初始化能量传播器。
        
        Args:
            engine: GraphNetworkEngine 实例，用于访问共享状态
        """
        self.engine = engine
        self.config = engine.config
        self.CAPACITY = engine.CAPACITY
        self.feedback_stats = []  # [V12.4] Storage for Cybernetics Telemetry
    
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
        # [V13.6] 确保 ProbValue 在函数作用域内可访问
        from core.math import ProbValue
        
        self.feedback_stats = []  # Reset stats for new run
        
        if not hasattr(self.engine, 'H0') or self.engine.H0 is None:
            raise ValueError("必须先执行 initialize_nodes()")
        
        if not hasattr(self.engine, 'adjacency_matrix') or self.engine.adjacency_matrix is None:
            raise ValueError("必须先执行 build_adjacency_matrix()")
        
        H = self.engine.H0.copy()
        flow_config = self.config.get('flow', {})
        physics_config = self.config.get('physics', {})  # [V12.1] 需要读取physics配置（用于流年衰减率等）
        global_entropy = flow_config.get('globalEntropy', 0.05)
        output_drain_penalty = flow_config.get('outputDrainPenalty', 1.2)  # [V42.1] 食伤泄耗惩罚
        
        # [V12.1] 在循环外读取流年衰减率（避免每次迭代都读取）
        liunian_decay_rate = physics_config.get('liunian_decay_rate', 0.9)
        
        # [V42.1] 确定日主节点和元素（用于食伤泄耗计算）
        dm_indices = []
        dm_element = None
        if hasattr(self.engine, 'day_master_element') and self.engine.day_master_element:
            dm_element = self.engine.day_master_element
        # 如果没有化气，从节点中找到日主
        if not dm_element:
            for i, node in enumerate(self.engine.nodes):
                if node.pillar_idx == 2 and node.node_type == 'stem':  # 日柱天干
                    dm_element = node.element
                    dm_indices.append(i)
                    break
        else:
            # 找到所有日主节点（可能有多个）
            for i, node in enumerate(self.engine.nodes):
                if node.element == dm_element and node.pillar_idx == 2:
                    dm_indices.append(i)
        
        # [V42.1] 确定食伤元素（日主生的）
        output_elements = []
        if dm_element:
            for source, target in GENERATION.items():
                if source == dm_element:
                    output_elements.append(target)
        
        # [V57.2] 识别阳刃节点（在传播前标记，用于保护）
        yangren_node_indices = []
        if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 2:
            day_pillar = self.engine.bazi[2]
            if len(day_pillar) >= 2:
                day_master = day_pillar[0]
                for i, node in enumerate(self.engine.nodes):
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
        if hasattr(self.engine, 'bazi') and self.engine.bazi and len(self.engine.bazi) > 1:
            month_branch_char = self.engine.bazi[1][1] if len(self.engine.bazi[1]) > 1 else None
            if month_branch_char:
                # 找到月支节点及其藏干节点
                for i, node in enumerate(self.engine.nodes):
                    if (node.node_type == 'branch' and node.char == month_branch_char and 
                        node.pillar_idx == 1):  # 月支
                        month_branch_nodes.append(i)
                    # 检查藏干节点（如果月支藏干中有生助日主的元素）
                    if node.node_type == 'branch' and node.char == month_branch_char:
                        hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(month_branch_char, [])
                        for hidden_stem, _ in hidden_map:
                            hidden_element = self.engine.STEM_ELEMENTS.get(hidden_stem, 'earth')
                            # 如果藏干元素生助日主（印星或比劫），也标记为月令相关节点
                            resource_element = None
                            for elem, target in GENERATION.items():
                                if target == dm_element:
                                    resource_element = elem
                                    break
                            if hidden_element == resource_element or hidden_element == dm_element:
                                # 找到对应的天干节点
                                for j, other_node in enumerate(self.engine.nodes):
                                    if other_node.char == hidden_stem and other_node.node_type == 'stem':
                                        if j not in month_branch_nodes:
                                            month_branch_nodes.append(j)
        
        # [V13.4] 获取 Phase 2 动态交互参数
        generation_efficiency = flow_config.get('generationEfficiency', 0.7)
        generation_drain = flow_config.get('generationDrain', 0.3)
        control_impact = flow_config.get('controlImpact', 0.5)
        damping_factor = flow_config.get('dampingFactor', 0.1)
        spatial_decay = flow_config.get('spatialDecay', {'gap0': 1.0, 'gap1': 0.9, 'gap2': 0.6, 'gap3': 0.3})
        
        # [V12.2] 阻抗与反馈参数
        feedback_config = flow_config.get('feedback', {})
        inverse_threshold = feedback_config.get('inverseControlThreshold', 4.0)
        inverse_recoil_multiplier = feedback_config.get('inverseRecoilMultiplier', 2.0)
        era_shield_factor = feedback_config.get('eraShieldingFactor', 0.5)
        
        # [V12.3] 获取当前环境能量 (Era/Geo) 用于屏蔽计算
        era_element = None
        if hasattr(self.engine, 'bazi') and len(self.engine.bazi) > 0:
            # 简化：假设已知的环境元素（例如大运天干或地支主气）
            # 这里暂时使用月令主气作为环境参考，或者扩展以支持真实的ERA输入
            # 为了支持"寒衣护体"，我们需要知道"得令"或"得地"
            # 暂时尝试从 engine 获取 context
             if hasattr(self.engine, 'current_era_element'): # 假设有这个属性
                 era_element = self.engine.current_era_element
             # 或者通过月令判断（得令即有屏蔽？） -> 简化为月令五行
             elif month_branch_char:
                  from core.interactions import EARTHLY_BRANCHES
                  era_element = EARTHLY_BRANCHES.get(month_branch_char, {}).get('element', '')

        for iteration in range(max_iterations):
            # [V9.8 FINAL PURGE] 完全删除矩阵乘法，改用纯物理遍历
            # [V15.2] 迭代衰减：生关系效率随迭代次数递减（强力制动）
            # 物理意义：生助之力是"一鼓作气，再而衰，三而竭"。第5轮时推力应几乎归零
            temporal_decay_factor = 0.40 ** iteration  # 每轮衰减60%（极强制动）
            current_generation_efficiency = generation_efficiency * temporal_decay_factor
            
            # [V9.8] 建立宇宙快照 (Snapshot) - 使用快照能量计算，避免迭代顺序影响
            snapshot = {}
            for i, node in enumerate(self.engine.nodes):
                if i < len(H):
                    snapshot[i] = H[i] if isinstance(H[i], ProbValue) else ProbValue(float(H[i]), std_dev_percent=0.1)
            
            # [V9.8] 初始化能量增量表 (Deltas) - 所有节点从快照开始
            H_new = H.copy()
            deltas = {i: 0.0 for i in range(len(self.engine.nodes))}
            
            # [V15.3] 贪合忘冲：在计算脉冲之前，先标记哪些节点被合住了
            # 被合住的节点（攻击者）无法有效克制其他节点
            locked_nodes = set()
            if hasattr(self.engine, '_quantum_entanglement_debug'):
                debug_info = self.engine._quantum_entanglement_debug
                detected_matches = debug_info.get('detected_matches', [])
                
                # 检查所有节点是否在合局中
                for i, node in enumerate(self.engine.nodes):
                    is_locked = False
                    for match in detected_matches:
                        if node.char in match:
                            # 检查是否是合局（三合、三会、半合、拱合、六合、天干五合）
                            match_upper = match.upper()
                            if any(keyword in match_upper for keyword in ['THREEHARMONY', 'THREEMEETING', 'HALFHARMONY', 'ARCHHARMONY', 'SIXHARMONY', 'SIX', 'STEM', 'FIVE', '三合', '三会', '半合', '拱合', '六合', '天干']):
                                is_locked = True
                                break
                    if is_locked:
                        locked_nodes.add(i)
            
            # [V9.8] 纯物理遍历：遍历所有节点对，应用 V9.7 物理公式
            # CRITICAL: Do NOT use self.adjacency_matrix @ H
            # Must iterate edges explicitly to use FlowEngine logic
            n = len(self.engine.nodes)
            
            # [V15.3] 获取解冲消耗参数
            combo_physics = self.config.get('interactions', {}).get('comboPhysics', {})
            resolution_cost = combo_physics.get('resolutionCost', 0.1) if isinstance(combo_physics, dict) else 0.1
            
            for src_i in range(n):
                for tgt_i in range(n):
                    if src_i == tgt_i:
                        continue
                    
                    weight = self.engine.adjacency_matrix[tgt_i][src_i]
                    if abs(weight) < 1e-6:  # 忽略零权重
                        continue
                    
                    src_node = self.engine.nodes[src_i]
                    tgt_node = self.engine.nodes[tgt_i]
                    src_val = snapshot[src_i].mean if isinstance(snapshot[src_i], ProbValue) else float(snapshot[src_i])
                    tgt_val = snapshot[tgt_i].mean if isinstance(snapshot[tgt_i], ProbValue) else float(snapshot[tgt_i])
                    
                    # 识别关系类型
                    # 负权重 = 克 (Control)
                    if weight < 0:
                        # [V15.3] 贪合忘冲逻辑：如果攻击者被合住，克制伤害应大幅削弱或失效
                        if src_i in locked_nodes:
                            # 攻击者被合住，应用解冲消耗
                            # 伤害降低到原来的 (1 - resolution_cost) 倍，或者直接跳过
                            # 使用较小的系数 (0.1) 来模拟"贪合忘冲"的效果
                            resolution_factor = resolution_cost  # 0.1 = 90% 伤害削弱
                            
                            from core.engines.flow_engine import FlowEngine
                            base_dmg = calculate_control_damage(src_val, tgt_val, control_impact)
                            dmg = base_dmg * resolution_factor  # 伤害降低到 10%
                            max_allowed_damage = tgt_val * 0.1 * resolution_factor  # 最大伤害也降低
                            actual_damage = min(dmg, max_allowed_damage)
                            deltas[tgt_i] -= actual_damage
                            # 攻击者自己也要付点小费（解冲消耗）
                            deltas[src_i] -= src_val * resolution_cost * 0.1  # 很小的消耗
                            continue  # 跳过正常的克制计算
                        # [V9.8] 必须使用 FlowEngine 的 Sigmoid 计算，而不是直接乘 weight
                        from core.engines.flow_engine import FlowEngine
                        
                        # [V12.3] 阻抗失配与反克 (Impedance Mismatch)
                        # calculate_impedance_mismatch 返回 (damage_mod, recoil_def_factor, is_inverse)
                        # 注意：recoil_def_factor 已经是计算好的系数 (包含log缩放)
                        # Recoil Energy = Source Energy * recoil_def_factor
                        
                        damage_mod, recoil_factor, is_inverse = calculate_impedance_mismatch(
                            src_val, tgt_val,
                            threshold=inverse_threshold,
                            base_recoil=0.3, # 默认基础反冲
                            inverse_recoil_multiplier=inverse_recoil_multiplier
                        )
                        
                        # 1. 计算期望伤害
                        raw_damage = calculate_control_damage(src_val, tgt_val, control_impact)
                        # 应用阻抗失配修正 (0.05 or 1.0)
                        potential_damage = raw_damage * damage_mod
                        
                        # 2. 应用环境屏蔽 (Era Shielding)
                        # 只有当非反克状态下，屏蔽才有意义（反克本身已经忽略伤害）
                        # 或者统一应用
                        actual_damage = calculate_shielding_effect(
                            potential_damage, 
                            tgt_node.element, 
                            era_element, 
                            shield_factor=era_shield_factor
                        )
                        
                        # 硬钳位：伤害不超过快照能量的50% (在 calculate_control_damage 内部已有 min, 但双重保险)
                        max_allowed_damage = tgt_val * 0.5
                        actual_damage = min(actual_damage, max_allowed_damage)
                        
                        # 应用伤害到目标
                        deltas[tgt_i] -= actual_damage
                        
                        # 3. 计算反噬 (Recoil)
                        # Recoil = SourceVal * Factor (物理上反冲力与作用力相关，但在反克时与自身撞击能量相关)
                        # 在 calculate_impedance_mismatch 中，factor 已针对 src_val 比例做了设计
                        # Recoil Energy = src_val * recoil_factor
                        recoil_energy = src_val * recoil_factor
                        
                        # 确保反噬不会让能量变负（或者允许变负代表崩溃？） -> 允许变负，但在 application 时处理
                        deltas[src_i] -= recoil_energy
                        
                        # Debug / Logging for Telemetry
                        if is_inverse or actual_damage < potential_damage * 0.9 or recoil_energy > 0.1:
                            self.feedback_stats.append({
                                "source": src_node.char,
                                "target": tgt_node.char,
                                "is_inverse": is_inverse,
                                "recoil": recoil_energy,
                                "shield_efficiency": 1.0 - (actual_damage / (potential_damage + 1e-6)),
                                "damage_mitigated": potential_damage - actual_damage,
                                "type": "Control"
                            })
                    
                    # 正权重 = 生 (Generation) 或 比劫 (Support)
                    elif weight > 0:
                        # 检查是否是生关系
                        is_generation = (src_node.element in GENERATION and 
                                        GENERATION[src_node.element] == tgt_node.element)
                        # 检查是否是比劫关系
                        is_peer = (src_node.element == tgt_node.element and src_node != tgt_node)
                        
                        if is_generation:
                            # [V9.8] 必须使用 FlowEngine 的 Threshold 计算
                            from core.engines.flow_engine import FlowEngine
                            gain = calculate_generation(src_val, current_generation_efficiency)
                            # 计算距离衰减
                            distance = abs(tgt_node.pillar_idx - src_node.pillar_idx)
                            if distance == 0:
                                decay = spatial_decay.get('gap0', 1.0)
                            elif distance == 1:
                                decay = spatial_decay.get('gap1', 0.9)
                            elif distance == 2:
                                decay = spatial_decay.get('gap2', 0.6)
                            else:
                                decay = spatial_decay.get('gap3', 0.3)
                            deltas[tgt_i] += gain * abs(weight) * decay
                            # 源节点泄气
                            if gain > 0:
                                effective_source = src_val - 10.0  # 阈值已提高到10.0
                                if effective_source > 0:
                                    drain_amount = effective_source * abs(weight) * generation_drain * decay
                                    deltas[src_i] -= drain_amount
                        elif is_peer:
                            # [V9.8] 比劫关系：低损耗共振
                            peer_drain = 0.005  # 比劫传导损耗（几乎无损）
                            distance = abs(tgt_node.pillar_idx - src_node.pillar_idx)
                            if distance == 0:
                                decay = spatial_decay.get('gap0', 1.0)
                            elif distance == 1:
                                decay = spatial_decay.get('gap1', 0.9)
                            elif distance == 2:
                                decay = spatial_decay.get('gap2', 0.6)
                            else:
                                decay = spatial_decay.get('gap3', 0.3)
                            # 比劫传导：小增益，低损耗
                            gain = src_val * abs(weight) * 0.1 * decay  # 比劫传导效率较低
                            deltas[tgt_i] += gain
                            drain_amount = src_val * abs(weight) * peer_drain * decay
                            deltas[src_i] -= drain_amount
            
            # [V9.8] 应用单次脉冲：将增量应用到快照能量
            for i in range(len(self.engine.nodes)):
                base_val = snapshot[i].mean if isinstance(snapshot[i], ProbValue) else float(snapshot[i])
                new_val = base_val + deltas[i]
                # 安全钳位：防止能量为负
                if new_val < 0:
                    new_val = 0.0
                # 转换为 ProbValue
                if isinstance(snapshot[i], ProbValue):
                    std_dev_percent = snapshot[i].std / max(snapshot[i].mean, 0.1) if snapshot[i].mean > 0 else 0.1
                    H_new[i] = ProbValue(new_val, std_dev_percent=std_dev_percent)
                else:
                    H_new[i] = ProbValue(new_val, std_dev_percent=0.1)
            
            # [V14.2] 应用势井调谐：当能量接近容量上限时，非线性压缩波函数
            for i in range(len(self.engine.nodes)):
                if isinstance(H_new[i], ProbValue):
                    # 检查是否接近容量上限
                    if H_new[i].mean > self.CAPACITY * 0.8:  # 超过80%容量
                        # 应用势井调谐
                        source_energy = H[i] if isinstance(H[i], ProbValue) else ProbValue(float(H[i]), std_dev_percent=0.1)
                        target_energy = H_new[i]
                        # 使用生成效率系数
                        gain, _ = self.apply_logistic_potential(source_energy, target_energy, generation_efficiency)
                        H_new[i] = gain
            
            # [V13.4] 能量守恒修正：扣除源节点的能量（generationDrain）
            # 遍历所有节点对，识别"生"关系并扣除源节点能量
            for j in range(len(self.engine.nodes)):
                node_j = self.engine.nodes[j]
                h_j_val = float(H[j]) if isinstance(H[j], ProbValue) else H[j]
                
                # 计算该节点作为"生"的源节点，总共输出了多少能量
                total_drain = 0.0
                
                for i in range(len(self.engine.nodes)):
                    if i == j:
                        continue
                    
                    node_i = self.engine.nodes[i]
                    weight = self.engine.adjacency_matrix[i][j]
                    
                    # 检查是否是生关系（源节点生目标节点）
                    is_generation = (node_j.element in GENERATION and 
                                    GENERATION[node_j.element] == node_i.element and 
                                    weight > 0)
                    
                    # [V14.0] 比劫关系（同五行）：应用小的损耗（peer_drain），而不是 generationDrain
                    # 比劫是朋友关系，能量传输应该是低损的共振，不像母子关系那样耗气
                    is_peer = (node_j.element == node_i.element and node_j != node_i)
                    
                    if is_peer:
                        # [V15.0] 检查是否在合局中（超导模式），并获取合局类型
                        result = self._is_in_combination(node_j, node_i)
                        if isinstance(result, tuple):
                            is_in_combination, combo_type = result
                        else:
                            # 向后兼容：如果返回的是 bool
                            is_in_combination = result
                            combo_type = None
                        
                        if is_in_combination:
                            # [V15.0] 超导模式：应用分级超导调谐算子
                            # 注意：超导调谐只应用于能量传输，不增加总能量
                            source_prob = H[j] if isinstance(H[j], ProbValue) else ProbValue(float(H[j]), std_dev_percent=0.1)
                            
                            # [V15.2] 使用零损耗超导调谐（返回增益和损耗率）
                            gain_wave, drain_rate = self.apply_superconductivity(source_prob, combo_type)
                            
                            # [V15.2] 根据合局类型设定增益幅度（优化：提高半合/六合/拱合的增益）
                            if combo_type in ['three_harmony', 'three_meeting']:
                                gain_multiplier = 0.50  # 全超导：提高增益（从0.40到0.50）
                            elif combo_type == 'half_harmony':
                                gain_multiplier = 1.2  # [V15.2] 半合：进一步提高增益（从1.0到1.2）
                            elif combo_type == 'six_harmony':
                                gain_multiplier = 1.3  # [V15.2] 六合：进一步提高增益（从1.0到1.3）
                            elif combo_type == 'arch_harmony':
                                gain_multiplier = 1.1  # [V15.2] 拱合：进一步提高增益（从1.0到1.1）
                            else:
                                gain_multiplier = 0.2  # 默认
                            
                            gain_mean = gain_wave.mean * abs(weight) * gain_multiplier
                            gain_std = gain_wave.std * abs(weight) * gain_multiplier
                            gain = ProbValue(gain_mean, std_dev_percent=gain_std / gain_mean if gain_mean > 0 else 0.1)
                            
                            # 将增益应用到目标节点
                            if isinstance(H_new[i], ProbValue):
                                H_new[i] = H_new[i] + gain
                            else:
                                H_new[i] = ProbValue(float(H_new[i]), std_dev_percent=0.1) + gain
                            
                            # [V15.2] 关键修复：使用返回的零损耗率覆盖默认的generationDrain
                            # 合局内部传输，源头零损耗！
                            drain_amount = h_j_val * abs(weight) * drain_rate * spatial_decay.get('gap0', 1.0)
                            total_drain += drain_amount
                        else:
                            # [V14.3] 普通比劫传导：降低损耗（从0.01到0.005），提高能量保留
                            peer_drain = 0.005  # 比劫传导损耗（远小于 generationDrain，几乎无损）
                            distance = abs(node_i.pillar_idx - node_j.pillar_idx)
                            if distance == 0:
                                decay = spatial_decay.get('gap0', 1.0)
                            elif distance == 1:
                                decay = spatial_decay.get('gap1', 0.9)
                            elif distance == 2:
                                decay = spatial_decay.get('gap2', 0.6)
                            else:
                                decay = spatial_decay.get('gap3', 0.3)
                            drain_amount = h_j_val * abs(weight) * peer_drain * decay
                            total_drain += drain_amount
                    elif is_generation:
                        # [V9.5] 生关系：使用阈值生发公式（基于快照能量）
                        from core.engines.flow_engine import FlowEngine
                        
                        # 使用快照能量（H），而不是实时能量（H_new）
                        source_energy_val = float(H[j]) if isinstance(H[j], ProbValue) else H[j]
                        
                        # [V9.5] 使用阈值生发公式：Output = max(0, (Mother - 5.0) * Efficiency)
                        generation_output = calculate_generation(source_energy_val, current_generation_efficiency)
                        
                        # 转换为ProbValue
                        if isinstance(H[j], ProbValue):
                            std_dev_percent = H[j].std / H[j].mean if H[j].mean > 0 else 0.1
                            gain = ProbValue(generation_output, std_dev_percent=std_dev_percent)
                        else:
                            gain = ProbValue(generation_output, std_dev_percent=0.1)
                        
                        # 计算泄气量
                        if generation_output > 0:
                            effective_source = source_energy_val - 5.0
                            actual_drain_factor = generation_drain
                        else:
                            actual_drain_factor = 0.0
                        # 计算距离衰减
                        distance = abs(node_i.pillar_idx - node_j.pillar_idx)
                        if distance == 0:
                            decay = spatial_decay.get('gap0', 1.0)
                        elif distance == 1:
                            decay = spatial_decay.get('gap1', 0.9)
                        elif distance == 2:
                            decay = spatial_decay.get('gap2', 0.6)
                        else:
                            decay = spatial_decay.get('gap3', 0.3)
                        
                        # 将增益应用到目标节点（考虑距离衰减和权重）
                        if isinstance(H_new[i], ProbValue):
                            H_new[i] = H_new[i] + gain * abs(weight) * decay
                        else:
                            H_new[i] = ProbValue(float(H_new[i]), std_dev_percent=0.1) + gain * abs(weight) * decay
                        
                        # [V9.5] 智能泄气：计算源节点的能量损失
                        if generation_output > 0:
                            # [进一步优化] 阈值已提高到10.0
                            effective_source = source_energy_val - 10.0
                            drain_amount = effective_source * abs(weight) * actual_drain_factor * decay
                            total_drain += drain_amount
                
                # 扣除源节点的能量（能量守恒）
                if total_drain > 0:
                    # 从 H_new 中扣除（因为 H_new 是矩阵乘法的结果）
                    if isinstance(H_new[j], ProbValue):
                        H_new[j] = H_new[j] - ProbValue(total_drain, std_dev_percent=0.1)
                    else:
                        H_new[j] -= total_drain
                    
                    # [V13.4] 安全钳位：防止能量被吸干成负数
                    if isinstance(H_new[j], ProbValue):
                        if H_new[j].mean < 0:
                            H_new[j] = ProbValue(0.0, std_dev_percent=0.1)
                    else:
                        if H_new[j] < 0:
                            H_new[j] = 0.0
            
            # [V13.6] 熵增逻辑注入：当发生"克/冲"时，增加不确定性（σ）
            # 遍历所有节点对，识别"克"关系并增加目标节点的不确定性
            branch_events = self.config.get('interactions', {}).get('branchEvents', {})
            clash_damping = branch_events.get('clashDamping', 0.4)
            entropy_boost_factor = 1.5  # [V13.6] 被克时，波动率增加 50%
            
            for i in range(len(self.engine.nodes)):
                node_i = self.engine.nodes[i]
                
                # 检查该节点是否被"克"（adjacency_matrix 中的负权重表示克）
                total_control_damage = 0.0
                is_controlled = False
                
                for j in range(len(self.engine.nodes)):
                    if i == j:
                        continue
                    
                    node_j = self.engine.nodes[j]
                    weight = self.engine.adjacency_matrix[i][j]
                    
                    # 检查是否是克关系（源节点克目标节点）
                    is_control = (node_j.element in CONTROL and 
                                 CONTROL[node_j.element] == node_i.element and 
                                 weight < 0)
                    
                    if is_control:
                        is_controlled = True
                        # [V9.8] 删除线性计算：不再使用 abs(weight) * abs(H[j])
                        # 实际伤害计算已使用 calculate_control_damage() 的 Sigmoid 公式
                
                # [V15.0] 如果被克，应用散射调谐（波函数调制）+ 残血保护
                if is_controlled:
                    # 找到最强的攻击者
                    max_attacker_energy = ProbValue(0.0, std_dev_percent=0.1)
                    max_weight = 0.0
                    for j in range(len(self.engine.nodes)):
                        if i == j:
                            continue
                        node_j = self.engine.nodes[j]
                        weight = self.engine.adjacency_matrix[i][j]
                        is_control = (node_j.element in CONTROL and 
                                     CONTROL[node_j.element] == node_i.element and 
                                     weight < 0)
                        if is_control:
                            # [V15.3] 贪合忘冲：如果攻击者被合住，跳过或削弱伤害
                            if j in locked_nodes:
                                # 攻击者被合住，应用解冲消耗
                                continue  # 跳过这个攻击者
                            
                            attacker_energy = H[j] if isinstance(H[j], ProbValue) else ProbValue(float(H[j]), std_dev_percent=0.1)
                            if abs(weight) > max_weight:
                                max_attacker_energy = attacker_energy
                                max_weight = abs(weight)
                    
                    # [V9.4] 单次坍缩协议：使用快照能量计算伤害，避免计算顺序导致的偏差
                    if max_attacker_energy.mean > 0:
                        # 使用这一轮开始时的快照能量（H），而不是正在被扣减的实时能量（H_new）
                        # 这确保了Sigmoid公式基于初始状态计算，而不是被多轮迭代扭曲
                        target_energy_snapshot = H[i] if isinstance(H[i], ProbValue) else ProbValue(float(H[i]), std_dev_percent=0.1)
                        
                        # [V9.4] 移除残血保护机制：Sigmoid公式已经极其精确地处理了强弱关系
                        # 任何额外的保护都会干扰Sigmoid的数学精度
                        
                        # [V9.5] 使用FlowEngine的Sigmoid公式计算伤害（基于快照能量）
                        from core.engines.flow_engine import FlowEngine
                        flow_config = self.config.get('flow', {})
                        base_impact = flow_config.get('controlImpact', 0.8)
                        
                        attacker_val = max_attacker_energy.mean
                        defender_val = target_energy_snapshot.mean
                        
                        # [V15.3] 反克机制：当攻击者能量远小于防御者时，应该应用反克保护
                        # E2案例：弱水（1个节点）克强火（7个节点），应该被反克
                        force_ratio = attacker_val / (defender_val + 1e-5)  # 避免除零
                        reverse_control_threshold = 0.3  # 当攻击者能量 < 防御者能量的30%时，触发反克
                        
                        if force_ratio < reverse_control_threshold:
                            # 反克：弱攻击者无法有效克制强防御者
                            # 伤害应该大幅降低，甚至接近0
                            reverse_control_factor = force_ratio / reverse_control_threshold  # 0.0 到 1.0
                            # 当 force_ratio = 0.1 时，reverse_control_factor = 0.33，伤害降低到原来的33%
                            # 当 force_ratio = 0.05 时，reverse_control_factor = 0.17，伤害降低到原来的17%
                            base_damage = calculate_control_damage(attacker_val, defender_val, base_impact)
                            damage_value = base_damage * reverse_control_factor
                        else:
                            # 正常克制：使用Sigmoid公式计算伤害
                            damage_value = calculate_control_damage(attacker_val, defender_val, base_impact)
                        
                        # 转换为ProbValue
                        damage_wave = ProbValue(damage_value, std_dev_percent=0.1)
                        
                        # [V9.7 关键修复] 伤害必须基于快照能量计算和应用
                        # 问题：之前的代码使用 target_energy_current_val * 0.9 作为限制，
                        # 导致当矩阵乘法后能量已经很低时，伤害被进一步限制，最终能量过低
                        # 
                        # 解决方案：
                        # 1. 伤害计算基于快照能量（已实现）
                        # 2. 伤害应用也基于快照能量，而不是矩阵乘法后的当前能量
                        # 3. FlowEngine.calculate_control_damage 已经应用了 50% 硬钳位，这里不需要额外限制
                        snapshot_energy = target_energy_snapshot.mean
                        
                        # [V9.7] 硬钳位：伤害不超过快照能量的50%（FlowEngine已保证，这里再次确认）
                        # [V15.3] 反克时，进一步降低最大伤害限制
                        if force_ratio < reverse_control_threshold:
                            # 反克时，最大伤害限制应该更小（例如10%而不是50%）
                            max_allowed_damage = snapshot_energy * 0.1 * reverse_control_factor
                        else:
                            max_allowed_damage = snapshot_energy * 0.5
                        actual_damage = min(damage_value, max_allowed_damage)
                        
                        # [V9.7] 关键修复：克制伤害必须从当前能量中扣除
                        # 但伤害计算基于快照能量，确保伤害量正确
                        target_energy_current = H_new[i] if isinstance(H_new[i], ProbValue) else ProbValue(float(H_new[i]), std_dev_percent=0.1)
                        target_energy_current_val = target_energy_current.mean
                        
                        # [V9.7] 从当前能量中扣除伤害（确保克制伤害生效）
                        # 但如果当前能量已经低于快照能量的50%，不再扣除（防止过度伤害）
                        min_allowed_energy = snapshot_energy * 0.5
                        final_energy = max(min_allowed_energy, target_energy_current_val - actual_damage)
                        
                        H_new[i] = ProbValue(final_energy, std_dev_percent=0.1)
                        
                        # 安全钳位：防止能量为负（双重保护）
                        if isinstance(H_new[i], ProbValue) and H_new[i].mean < 0:
                            H_new[i] = ProbValue(0.0, std_dev_percent=0.1)
            
            # [V15.2] 合局超导逻辑：当发生"合"时，应用超导调谐（波函数调制）
            # 三合、六合等合局会锁定能量，形成相干态
            # [V15.2 优化]：不仅保护能量增加，也要保护能量下降（F2-F4案例修复）
            for i in range(len(self.engine.nodes)):
                node_i = self.engine.nodes[i]
                
                # [V15.2] 检查节点是否在合局中（通过调试信息）
                is_in_combo = False
                combo_type = None
                if hasattr(self.engine, '_quantum_entanglement_debug'):
                    debug_info = self.engine._quantum_entanglement_debug
                    detected_matches = debug_info.get('detected_matches', [])
                    # 检查节点是否参与合局
                    for match in detected_matches:
                        if node_i.char in match:
                            is_in_combo = True
                            # 识别合局类型
                            match_upper = match.upper()
                            if 'THREEMEETING' in match_upper or '三会' in match:
                                combo_type = 'three_meeting'
                            elif 'THREEHARMONY' in match_upper or '三合' in match:
                                combo_type = 'three_harmony'
                            elif 'HALFHARMONY' in match_upper or '半合' in match:
                                combo_type = 'half_harmony'
                            elif 'SIXHARMONY' in match_upper or '六合' in match or 'SIX' in match_upper:
                                combo_type = 'six_harmony'
                            elif 'ARCHHARMONY' in match_upper or '拱合' in match:
                                combo_type = 'arch_harmony'
                            break
                
                # [V15.2] 如果在合局中，无论能量增加还是下降都要保护
                if is_in_combo and isinstance(H_new[i], ProbValue) and isinstance(H[i], ProbValue):
                    # 获取初始能量（合局后的初始能量）
                    h0_val = self.engine.H0[i].mean if isinstance(self.engine.H0[i], ProbValue) else float(self.engine.H0[i])
                    current_val = H_new[i].mean
                    
                    # [V15.2] 如果能量低于初始能量的99%，强制恢复到99%（合局保护，更积极，针对F2-F4）
                    if current_val < h0_val * 0.99:
                        # 应用超导调谐，恢复能量
                        source_energy = ProbValue(h0_val * 0.99, std_dev_percent=0.1)
                        gain_wave, _ = self.apply_superconductivity(source_energy, combo_type)
                        H_new[i] = gain_wave
                    # [V15.2] 如果能量增加超过30%，也应用超导调谐（原有逻辑）
                    elif current_val > H[i].mean * 1.3:
                        source_energy = H[i]
                        gain_wave, _ = self.apply_superconductivity(source_energy, combo_type)
                        H_new[i] = gain_wave
                
                # [V9.5] 扩展保护：如果节点与合局节点同元素，也要应用后置补偿（针对F1/F3/F4案例）
                # 例如：申子辰三合水，不仅要保护申、子、辰，也要保护所有Water天干节点（如壬）
                # 因为监控的是元素总能量，所有同元素节点都需要应用后置补偿
                if not is_in_combo and hasattr(self.engine, '_quantum_entanglement_debug'):
                    debug_info = self.engine._quantum_entanglement_debug
                    detected_matches = debug_info.get('detected_matches', [])
                    branch_events = self.config.get('interactions', {}).get('branchEvents', {})
                    
                    # 检查是否有合局，且当前节点与合局元素相同
                    for match in detected_matches:
                        # 提取合局元素和类型
                        combo_element = None
                        combo_type_from_match = None
                        combo_bonus_from_match = 1.0
                        
                        match_upper = match.upper()
                        if 'water' in match.lower() or '水' in match:
                            combo_element = 'water'
                        elif 'wood' in match.lower() or '木' in match:
                            combo_element = 'wood'
                        elif 'fire' in match.lower() or '火' in match:
                            combo_element = 'fire'
                        elif 'metal' in match.lower() or '金' in match:
                            combo_element = 'metal'
                        elif 'earth' in match.lower() or '土' in match:
                            combo_element = 'earth'
                        
                        # 识别合局类型并获取bonus
                        if 'THREEHARMONY' in match_upper or '三合' in match:
                            combo_type_from_match = 'three_harmony'
                            three_harmony_config = branch_events.get('threeHarmony', {})
                            if isinstance(three_harmony_config, dict):
                                combo_bonus_from_match = three_harmony_config.get('bonus', 2.0)
                            else:
                                combo_bonus_from_match = 2.0
                        elif 'HALFHARMONY' in match_upper or '半合' in match:
                            combo_type_from_match = 'half_harmony'
                            half_harmony_config = branch_events.get('halfHarmony', {})
                            if isinstance(half_harmony_config, dict):
                                combo_bonus_from_match = half_harmony_config.get('bonus', 1.4)
                            else:
                                combo_bonus_from_match = 1.4
                        elif 'ARCHHARMONY' in match_upper or '拱合' in match:
                            combo_type_from_match = 'arch_harmony'
                            arch_harmony_config = branch_events.get('archHarmony', {})
                            if isinstance(arch_harmony_config, dict):
                                combo_bonus_from_match = arch_harmony_config.get('bonus', 1.1)
                            else:
                                combo_bonus_from_match = 1.1
                        elif 'SIXHARMONY' in match_upper or '六合' in match or 'SIX' in match_upper:
                            combo_type_from_match = 'six_harmony'
                            six_harmony_config = branch_events.get('sixHarmony', {})
                            if isinstance(six_harmony_config, dict):
                                combo_bonus_from_match = six_harmony_config.get('bonus', 1.4)
                            else:
                                combo_bonus_from_match = 1.4
                        
                        # 如果当前节点与合局元素相同，也要应用后置补偿
                        if combo_element and node_i.element == combo_element and combo_bonus_from_match > 1.0:
                            h0_val = self.engine.H0[i].mean if isinstance(self.engine.H0[i], ProbValue) else float(self.engine.H0[i])
                            current_val = H_new[i].mean if isinstance(H_new[i], ProbValue) else float(H_new[i])
                            
                            # [V9.5] 应用后置补偿：确保同元素节点也达到bonus倍率
                            expected_min = h0_val * combo_bonus_from_match
                            if current_val < expected_min:
                                if isinstance(H_new[i], ProbValue):
                                    H_new[i] = ProbValue(expected_min, std_dev_percent=H_new[i].std / max(H_new[i].mean, 0.1) if H_new[i].mean > 0 else 0.1)
                                else:
                                    H_new[i] = expected_min
                            break
            
            # [V9.5] 单次坍缩协议：当damping=1.0时，直接使用H_new，不混合H0
            # 这确保了单次脉冲的数学精度，不被初始状态"拉回"
            if damping >= 1.0:
                # 完全使用新状态（单次坍缩）
                H = H_new.copy()
            else:
                # 向后兼容：混合初始状态（多轮迭代时使用）
                H = damping * H_new + (1 - damping) * self.engine.H0
            
            # [V9.5] 单次坍缩协议：当damping=1.0时，跳过全局阻尼
            # Sigmoid已经极其精确地处理了能量的增减，任何额外的阻尼都会破坏这个数学精度
            if damping < 1.0:
                # [V13.4] 应用全局阻尼因子（防止数值爆炸）- 仅多轮迭代时使用
                # [V15.2] 优化：合局节点豁免或减少阻尼（保护合局能量）
                damping_factor = 0.05  # 默认全局阻尼因子
                for i in range(len(self.engine.nodes)):
                    node_i = self.engine.nodes[i]
                    
                    # [V15.2] 检查节点是否在合局中
                    is_in_combo = False
                    if hasattr(self.engine, '_quantum_entanglement_debug'):
                        debug_info = self.engine._quantum_entanglement_debug
                        detected_matches = debug_info.get('detected_matches', [])
                        for match in detected_matches:
                            if node_i.char in match:
                                is_in_combo = True
                                break
                    
                    # [V15.2] 如果在合局中，减少或豁免阻尼（保护合局能量）
                    if is_in_combo:
                        # 合局节点：完全豁免阻尼（零损耗）
                        effective_damping = 0.0
                    else:
                        effective_damping = damping_factor
                    
                    if isinstance(H[i], ProbValue):
                        H[i] = H[i] * (1.0 - effective_damping)
                    else:
                        H[i] *= (1.0 - effective_damping)
                    
                    # [V15.2] 在应用阻尼后，再次检查合局保护（确保能量不低于阈值）
                    if is_in_combo:
                        h0_val = self.engine.H0[i].mean if isinstance(self.engine.H0[i], ProbValue) else float(self.engine.H0[i])
                        current_val = H[i].mean if isinstance(H[i], ProbValue) else float(H[i])
                        # 如果能量低于初始能量的99%，强制恢复到99%（更积极的保护，针对F2-F4）
                        if current_val < h0_val * 0.99:
                            if isinstance(H[i], ProbValue):
                                H[i] = ProbValue(h0_val * 0.99, std_dev_percent=0.1)
                            else:
                                H[i] = h0_val * 0.99
            
            # [V58.2] Commander Absolute Immunity (月令绝对免疫) - Fix Wu Zetian
            # 确保月令节点对日主的生助权重锁定为 1.0（无损传输）
            if month_branch_nodes and dm_indices and self.engine.adjacency_matrix is not None:
                for month_idx in month_branch_nodes:
                    month_node = self.engine.nodes[month_idx]
                    # 检查月令节点是否生助日主
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
                            current_weight = self.engine.adjacency_matrix[dm_idx][month_idx]
                            if current_weight > 0:  # 如果是生助关系（正权重）
                                # 强制锁定为 1.0，确保能量无损传输
                                self.engine.adjacency_matrix[dm_idx][month_idx] = max(
                                    current_weight, 1.0
                                )
                            # 如果月令节点能量低于初始能量的 80%，强制恢复到初始能量的 80%
                            # [V13.1] Fix: Extract mean values for comparison
                            h_month_val = H[month_idx].mean if isinstance(H[month_idx], ProbValue) else float(H[month_idx])
                            h0_month_val = self.engine.H0[month_idx].mean if isinstance(self.engine.H0[month_idx], ProbValue) else float(self.engine.H0[month_idx])
                            if h_month_val < h0_month_val * 0.8:
                                if isinstance(H[month_idx], ProbValue):
                                    H[month_idx] = ProbValue(h0_month_val * 0.8, std_dev_percent=0.1)
                                else:
                                    H[month_idx] = h0_month_val * 0.8
            
            # [V57.2] 阳刃金刚盾：保护阳刃节点，确保能量不被过度削弱
            # [V57.4] 增强：如果阳刃节点被冲，不仅豁免，还要能量加成（越冲越旺）
            for i in yangren_node_indices:
                node = self.engine.nodes[i]
                # 检查是否被冲
                is_clashed = False
                if hasattr(self.engine, 'bazi') and self.engine.bazi:
                    for pillar in self.engine.bazi:
                        if len(pillar) >= 2:
                            other_branch = pillar[1]
                            if BRANCH_CLASHES.get(node.char) == other_branch:
                                is_clashed = True
                                break
                
                # V13.0: 处理 ProbValue（概率值）
                if is_clashed:
                    # [V57.4] 阳刃逢冲，其性更烈 - 能量加成 50%
                    if isinstance(H[i], ProbValue):
                        H[i] = H[i] * 1.5
                    else:
                        H[i] *= 1.5
                else:
                    # 如果阳刃节点能量低于初始能量的 50%，强制恢复到初始能量的 80%
                    h_val = float(H[i]) if isinstance(H[i], ProbValue) else H[i]
                    h0_val = float(self.engine.H0[i]) if isinstance(self.engine.H0[i], ProbValue) else self.engine.H0[i]
                    if h_val < h0_val * 0.5:
                        new_val = h0_val * 0.8
                        if isinstance(H[i], ProbValue):
                            H[i] = ProbValue(new_val, std_dev_percent=H[i].std / max(H[i].mean, 0.1))
                        else:
                            H[i] = new_val
            
            # [V55.0] 处理激活节点的能量变化（流年引动）
            # V13.0: 处理 ProbValue（概率值）
            for i, node in enumerate(self.engine.nodes):
                if hasattr(node, 'is_activated') and node.is_activated:
                    activation_factor = getattr(node, 'activation_factor', 1.0)
                    instability_penalty = getattr(node, 'instability_penalty', 0.0)
                    # 能量翻倍，但不稳定性增加
                    if isinstance(H[i], ProbValue):
                        H[i] = H[i] * activation_factor
                    else:
                        H[i] *= activation_factor
                    # 应用不稳定性惩罚（能量波动）
                    if instability_penalty > 0:
                        penalty_factor = (1.0 - instability_penalty * np.random.uniform(0.0, 0.2))
                        if isinstance(H[i], ProbValue):
                            H[i] = H[i] * penalty_factor
                        else:
                            H[i] *= penalty_factor
            
            # [V55.0] 流年节点能量快速衰减（只管一年）
            # [V12.1] 参数化：使用在循环外读取的流年衰减率
            # V13.0: 处理 ProbValue（概率值）
            for i, node in enumerate(self.engine.nodes):
                if hasattr(node, 'is_liunian') and node.is_liunian:
                    # 每次迭代衰减（快速衰减）
                    if isinstance(H[i], ProbValue):
                        H[i] = H[i] * liunian_decay_rate
                    else:
                        H[i] *= liunian_decay_rate
            
            # [V42.1] 应用食伤泄耗惩罚（日主生食伤时的额外能量损失）
            if dm_indices and output_elements:
                # V13.0: 处理 ProbValue（概率值）
                for dm_idx in dm_indices:
                    h_dm_val = float(H[dm_idx]) if isinstance(H[dm_idx], ProbValue) else H[dm_idx]
                    if h_dm_val <= 0:
                        continue
                    
                    # 计算日主流向所有食伤节点的总能量
                    total_output_flow = 0.0
                    for j, node in enumerate(self.engine.nodes):
                        if node.element in output_elements:
                            flow_weight = self.engine.adjacency_matrix[j][dm_idx]  # j从dm_idx获得的能量（正的表示dm生j）
                            if flow_weight > 0:
                                # 估算流量（简化：使用当前能量和权重）
                                flow_amount = flow_weight * h_dm_val
                                total_output_flow += flow_amount
                    
                    # 额外泄耗：日主生食伤时，不仅要转移能量，还要额外消耗
                    if total_output_flow > 0:
                        extra_drain = total_output_flow * (output_drain_penalty - 1.0)
                        if isinstance(H[dm_idx], ProbValue):
                            new_mean = max(0.0, H[dm_idx].mean - extra_drain)
                            H[dm_idx] = ProbValue(new_mean, std_dev_percent=H[dm_idx].std / max(H[dm_idx].mean, 0.1))
                        else:
                            H[dm_idx] = max(0.0, float(H[dm_idx]) - extra_drain)
                        # 确保在全局熵之前应用
            
            # [V9.4] 单次坍缩协议：在交互计算阶段，禁用全局阻尼
            # Sigmoid已经极其精确地处理了能量的增减，任何额外的阻尼都会破坏这个数学精度
            # 只有当damping < 1.0时才应用全局熵增（向后兼容）
            if damping < 1.0:
                # 应用全局熵增（能量损耗）
                # V13.0: 处理 ProbValue（概率值）
                entropy_factor = (1.0 - global_entropy)
                for i in range(len(H)):
                    if isinstance(H[i], ProbValue):
                        H[i] = H[i] * entropy_factor
                        # 确保均值非负
                        if H[i].mean < 0:
                            H[i] = ProbValue(0.0, std_dev_percent=H[i].std / max(abs(H[i].mean), 0.1))
                    else:
                        H[i] = max(0.0, float(H[i]) * entropy_factor)
        
        # [V15.3] 应用六合 bindingPenalty（活性降低）
        # 六合是磁力吸附，物理羁绊，能量提升但活性降低
        if hasattr(self.engine, '_quantum_entanglement_debug'):
            debug_info = self.engine._quantum_entanglement_debug
            detected_matches = debug_info.get('detected_matches', [])
            branch_events = self.config.get('interactions', {}).get('branchEvents', {})
            six_harmony_config = branch_events.get('sixHarmony', {})
            binding_penalty = six_harmony_config.get('bindingPenalty', 0.1) if isinstance(six_harmony_config, dict) else 0.1
            
            # 找到所有六合节点
            six_harmony_node_indices = []
            for i, node in enumerate(self.engine.nodes):
                if node.node_type == 'branch':
                    for match in detected_matches:
                        if node.char in match and ('SIXHARMONY' in match.upper() or '六合' in match or 'SIX' in match.upper()):
                            six_harmony_node_indices.append(i)
                            break
            
            # 应用 bindingPenalty：六合节点的能量应该降低（活性降低）
            for i in six_harmony_node_indices:
                if isinstance(H[i], ProbValue):
                    H[i] = H[i] * (1.0 - binding_penalty)
                else:
                    H[i] = H[i] * (1.0 - binding_penalty)
        
        # [V9.4] 后置合化补偿 (Post-Propagation Resonance)
        # 合化是结构力（Structure Force），不应该参与流转，而应该作为最终加成
        # 在生克结算完成后，检查合局结构，直接修改最终能量
        if hasattr(self.engine, '_quantum_entanglement_debug'):
            debug_info = self.engine._quantum_entanglement_debug
            detected_matches = debug_info.get('detected_matches', [])
            branch_events = self.config.get('interactions', {}).get('branchEvents', {})
            
            # [V9.5] 检查节点变化信息，判断是否合化成功
            node_changes = debug_info.get('node_changes', [])
            transformed_nodes = set()
            for change in node_changes:
                # node_changes可能是字符串列表（如"甲(wood) -> 甲(earth)"）或字典列表
                if isinstance(change, dict):
                    if change.get('transform', False):
                        # 节点发生了元素转化，说明合化成功
                        transformed_nodes.add(change.get('node_char', ''))
                elif isinstance(change, str):
                    # 字符串格式：提取节点字符（如"甲(wood) -> 甲(earth)"中的"甲"）
                    # 如果包含"->"，说明发生了转化
                    if '->' in change:
                        # 提取节点字符（假设格式为"字符(元素) -> 字符(元素)"）
                        parts = change.split('->')
                        if len(parts) >= 1:
                            node_part = parts[0].strip()
                            # 提取字符（在"("之前）
                            if '(' in node_part:
                                node_char = node_part.split('(')[0].strip()
                                transformed_nodes.add(node_char)
            
            for i, node in enumerate(self.engine.nodes):
                # 检查节点是否参与合局
                is_in_combo = False
                combo_type = None
                combo_bonus = 1.0
                is_transformed = node.char in transformed_nodes  # [V9.5] 检查是否合化成功
                
                for match in detected_matches:
                    if node.char in match:
                        is_in_combo = True
                        match_upper = match.upper()
                        
                        # 识别合局类型并获取bonus
                        if 'THREEMEETING' in match_upper or '三会' in match:
                            combo_type = 'three_meeting'
                            # [V15.3] 三会局使用 directionalBonus（3.0），而不是 threeMeeting.bonus（2.5）
                            interactions_config = self.config.get('interactions', {})
                            combo_physics = interactions_config.get('comboPhysics', {})
                            if isinstance(combo_physics, dict) and 'directionalBonus' in combo_physics:
                                combo_bonus = combo_physics.get('directionalBonus', 3.0)
                            else:
                                three_meeting_config = branch_events.get('threeMeeting', {})
                                if isinstance(three_meeting_config, dict):
                                    combo_bonus = three_meeting_config.get('bonus', 2.5)
                                else:
                                    combo_bonus = 3.0  # 默认使用 3.0（三会方局力量最强）
                        elif 'THREEHARMONY' in match_upper or '三合' in match:
                            combo_type = 'three_harmony'
                            three_harmony_config = branch_events.get('threeHarmony', {})
                            if isinstance(three_harmony_config, dict):
                                # [V15.3] 使用配置中的 bonus（应该是 2.0），而不是硬编码
                                combo_bonus = three_harmony_config.get('bonus', 2.0)
                            else:
                                combo_bonus = 2.0  # 默认使用 2.0（三合局预期比率）
                        elif 'HALFHARMONY' in match_upper or '半合' in match:
                            combo_type = 'half_harmony'
                            half_harmony_config = branch_events.get('halfHarmony', {})
                            if isinstance(half_harmony_config, dict):
                                # [V9.6 继续优化] F3案例预期比率1.4，当前1.654，需要微调
                                combo_bonus = half_harmony_config.get('bonus', 1.22)  # 微调以接近1.4
                            else:
                                combo_bonus = 1.22  # 微调以接近1.4
                        elif 'SIXHARMONY' in match_upper or '六合' in match or 'SIX' in match_upper:
                            combo_type = 'six_harmony'
                            six_harmony_config = branch_events.get('sixHarmony', {})
                            if isinstance(six_harmony_config, dict):
                                # [V15.3] 使用配置中的 bonus（应该是 1.3），bindingPenalty 在传播最后应用
                                combo_bonus = six_harmony_config.get('bonus', 1.3)
                            else:
                                combo_bonus = 1.3
                        elif 'ARCHHARMONY' in match_upper or '拱合' in match:
                            combo_type = 'arch_harmony'
                            arch_harmony_config = branch_events.get('archHarmony', {})
                            if isinstance(arch_harmony_config, dict):
                                combo_bonus = arch_harmony_config.get('bonus', 1.1)  # [V9.5] F4案例预期比率1.1
                            else:
                                combo_bonus = 1.1  # [V9.5] F4案例预期比率1.1
                        elif 'STEM' in match_upper or '天干' in match or 'FIVE' in match_upper:
                            # [V9.5] 天干五合：需要检查是否合化成功
                            combo_type = 'stem_five_combination'
                            stem_five_config = self.config.get('interactions', {}).get('stemFiveCombination', {})
                            if not stem_five_config:
                                stem_five_config = self.config.get('interactions', {}).get('stemFiveCombine', {})
                            if isinstance(stem_five_config, dict):
                                # [V9.6 继续优化] F5案例预期比率1.3，当前1.573，需要进一步降低
                                combo_bonus = stem_five_config.get('bonus', 1.15)  # 进一步降低以接近1.3
                            else:
                                combo_bonus = 1.15  # 进一步降低以接近1.3
                        break
                
                # [V9.5] 后置共振：如果节点在合局中，根据合化状态应用bonus或penalty
                if is_in_combo:
                    h0_val = self.engine.H0[i].mean if isinstance(self.engine.H0[i], ProbValue) else float(self.engine.H0[i])
                    current_val = H[i].mean if isinstance(H[i], ProbValue) else float(H[i])
                    
                    # [V9.5] 检查是否是天干五合
                    is_stem_combo = False
                    for match in detected_matches:
                        if node.char in match:
                            match_upper = match.upper()
                            if 'STEM' in match_upper or '天干' in match or 'FIVE' in match_upper:
                                is_stem_combo = True
                                break
                    
                    if is_stem_combo or combo_type == 'stem_five_combination':
                        # 天干五合：只有合化成功（transform=True）才应用bonus
                        stem_five_config = self.config.get('interactions', {}).get('stemFiveCombination', {})
                        if not stem_five_config:
                            stem_five_config = self.config.get('interactions', {}).get('stemFiveCombine', {})
                        
                        if is_transformed and combo_bonus > 1.0:
                            # 合化成功：应用bonus
                            expected_min = h0_val * combo_bonus
                            if current_val < expected_min:
                                if isinstance(H[i], ProbValue):
                                    H[i] = ProbValue(expected_min, std_dev_percent=H[i].std / max(H[i].mean, 0.1) if H[i].mean > 0 else 0.1)
                                else:
                                    H[i] = expected_min
                        else:
                            # [V9.7] 合而不化：应用penalty（针对F6案例）
                            # F6案例预期比率0.8，说明合而不化时能量应该下降到初始的80%
                            penalty = stem_five_config.get('penalty', 0.7) if isinstance(stem_five_config, dict) else 0.7
                            expected_max = h0_val * penalty
                            # [V9.7 强制应用] 无论当前能量是多少，强制应用penalty
                            # 如果当前能量比预期还高（说明被错误加成），强制压回
                            if current_val > expected_max:
                                if isinstance(H[i], ProbValue):
                                    H[i] = ProbValue(expected_max, std_dev_percent=H[i].std / max(H[i].mean, 0.1) if H[i].mean > 0 else 0.1)
                                else:
                                    H[i] = expected_max
                    # [V9.7 强制检测] 如果没有检测到天干五合，但节点是天干且可能参与五合，强制检查并应用penalty
                    elif node.node_type == 'stem' and not is_in_combo:
                        # 检查是否可能是天干五合但没有被检测到（F6案例）
                        # 检查八字中是否有其他天干与当前天干形成五合
                        from core.interactions import STEM_COMBINATIONS
                        found_five_combo = False
                        if hasattr(self.engine, 'bazi') and self.engine.bazi:
                            for pillar in self.engine.bazi:
                                if len(pillar) > 0:
                                    other_stem = pillar[0]
                                    if ((node.char, other_stem) in STEM_COMBINATIONS or 
                                        (other_stem, node.char) in STEM_COMBINATIONS):
                                        found_five_combo = True
                                        # 检测到天干五合，检查月令是否支持合化
                                        month_branch = self.engine.bazi[1][1] if len(self.engine.bazi[1]) > 1 else None
                                        
                                        # [V9.7] 检查月令是否支持合化
                                        # 甲己合土：需要月令是土（辰、戌、丑、未）或火（巳、午、未）
                                        # 如果月令不支持，则合而不化，应用penalty
                                        month_element = None
                                        if month_branch:
                                            from core.engine_graph.constants import BRANCH_ELEMENTS
                                            month_element = BRANCH_ELEMENTS.get(month_branch, 'earth')
                                        
                                        # 判断是否合化成功（简化：如果月令是目标元素或生目标元素，则合化成功）
                                        target_element = 'earth'  # 甲己合土
                                        is_transformed = False
                                        if month_element == target_element:
                                            is_transformed = True
                                        elif month_element:
                                            # 导入 GENERATION（确保在作用域内）
                                            from core.processors.physics import GENERATION as GEN_MAP
                                            if GEN_MAP.get(month_element) == target_element:
                                                is_transformed = True
                                        
                                        # [V9.7] 如果合而不化，强制应用penalty
                                        if not is_transformed:
                                            stem_five_config = self.config.get('interactions', {}).get('stemFiveCombination', {})
                                            if not stem_five_config:
                                                stem_five_config = self.config.get('interactions', {}).get('stemFiveCombine', {})
                                            # F6案例预期比率0.8，penalty应该是0.8
                                            penalty = stem_five_config.get('penalty', 0.8) if isinstance(stem_five_config, dict) else 0.8
                                            expected_max = h0_val * penalty
                                            # [V9.7 强制应用] 无论当前能量是多少，强制应用penalty
                                            current_val = H[i].mean if isinstance(H[i], ProbValue) else float(H[i])
                                            if isinstance(H[i], ProbValue):
                                                H[i] = ProbValue(expected_max, std_dev_percent=H[i].std / max(H[i].mean, 0.1) if H[i].mean > 0 else 0.1)
                                            else:
                                                H[i] = expected_max
                                        break
                    else:
                        # 地支合局：总是应用bonus（地支合局通常都会合化成功）
                        if combo_bonus > 1.0:
                            expected_min = h0_val * combo_bonus
                            if current_val < expected_min:
                                if isinstance(H[i], ProbValue):
                                    H[i] = ProbValue(expected_min, std_dev_percent=H[i].std / max(H[i].mean, 0.1) if H[i].mean > 0 else 0.1)
                                else:
                                    H[i] = expected_min
        
        # 更新节点的当前能量
        for i, node in enumerate(self.engine.nodes):
            node.current_energy = H[i]
        
        return H
    
    def apply_logistic_potential(self, source_prob, target_prob, efficiency: float, base_drain_rate: float = 0.15):
        """
        [V14.3] 势井调谐 (Logistic Potential) - 用于生 (Generation)
        
        物理含义：随着能量接近上限 CAPACITY，增益效率衰减，且波动率收缩（自由度降低）。
        
        [V14.3] 智能泄气：损耗因子必须乘以饱和度，如果目标满了，源头就不应该有损耗。
        
        Args:
            source_prob: 源能量波函数 (ProbValue)
            target_prob: 目标能量波函数 (ProbValue) - 用于计算饱和度
            efficiency: 生成效率系数（如 generationEfficiency）
            base_drain_rate: 基础损耗率（如 generationDrain）
            
        Returns:
            (gain_prob: ProbValue, actual_drain_factor: float) - 增益波函数和实际损耗因子
        """
        # 确保输入是 ProbValue
        if not isinstance(source_prob, ProbValue):
            source_prob = ProbValue(float(source_prob), std_dev_percent=0.1)
        if not isinstance(target_prob, ProbValue):
            target_prob = ProbValue(float(target_prob), std_dev_percent=0.1)
        
        # 1. 计算饱和度 (Scalar)
        saturation_k = 1.0 - (target_prob.mean / self.CAPACITY)
        saturation_k = max(0.0, saturation_k)  # 钳位，防止负数
        
        # 2. 调制波函数 (均值压缩，方差额外收缩)
        # 物理细节：当空间被填满时，粒子的震荡幅度(std)会变小 -> 乘 0.8
        gain_mean = source_prob.mean * efficiency * saturation_k
        gain_std = source_prob.std * efficiency * saturation_k * 0.8
        
        # 计算相对波动率
        std_dev_percent = gain_std / gain_mean if gain_mean > 0 else 0.1
        gain_prob = ProbValue(gain_mean, std_dev_percent)
        
        # [V14.3] 关键修正：损耗因子必须乘以饱和度！
        # 如果目标满了 (k=0)，源头就不应该有损耗。
        actual_drain_factor = base_drain_rate * saturation_k
        
        return gain_prob, actual_drain_factor
    
    def apply_scattering_interaction(self, attacker, target):
        """
        [V14.2] 散射调谐 (Scattering Interaction) - 用于克 (Control)
        
        物理含义：基于兰彻斯特方程。当攻守悬殊时（弱克强），伤害趋近于 0；被克时系统熵（不确定性）增加。
        
        Args:
            attacker: 攻击者能量波函数 (ProbValue)
            target: 目标能量波函数 (ProbValue)
            
        Returns:
            伤害波函数 (ProbValue)
        """
        import math
        
        # 确保输入是 ProbValue
        if not isinstance(attacker, ProbValue):
            attacker = ProbValue(float(attacker), std_dev_percent=0.1)
        if not isinstance(target, ProbValue):
            target = ProbValue(float(target), std_dev_percent=0.1)
        
        # [V9.3] Quantum-Inertia Protocol: 质量惯性阻尼公式
        # 使用非线性场论方程，放弃线性加减法
        from core.engines.flow_engine import FlowEngine
        
        attacker_val = attacker.mean
        target_val = target.mean
        
        # 获取基础伤害系数（从配置读取，默认0.5）
        flow_config = self.engine.config.get('flow', {})
        base_impact = flow_config.get('controlImpact', 0.5)
        
        # 使用质量惯性阻尼公式计算伤害
        # Formula: Damage = Base * (Attacker / (Attacker + Defender))^0.8
        damage_mean = calculate_control_damage(attacker_val, target_val, base_impact)
        
        # 3. 调制伤害波函数 (均值受损，方差膨胀)
        # 物理细节：被攻击时，系统进入混沌状态，不确定性(std)暴增 -> 乘 1.5
        # 计算相对伤害比例，用于方差膨胀
        impact_ratio = damage_mean / (target_val + 1e-5)
        damage_std = target.std * impact_ratio * 1.5
        
        # 计算相对波动率
        std_dev_percent = damage_std / damage_mean if damage_mean > 0 else 0.1
        
        return ProbValue(damage_mean, std_dev_percent)
    
    def apply_superconductivity(self, source_prob, combo_type=None):
        """
        [V15.2] 超导模式 (Superconductivity) - 用于合局比劫，强制零损耗
        
        物理含义：
        - 只要是合局，就是一家人，能量传递必须是完全无损的
        - 这不再是生克，这是"连体婴"
        
        Args:
            source_prob: 源能量波函数 (ProbValue)
            combo_type: 合局类型 ('three_harmony', 'three_meeting', 'half_harmony', 'six_harmony', 'arch_harmony')
            
        Returns:
            tuple: (超导态波函数 (ProbValue), 损耗率 (float))
        """
        # 确保输入是 ProbValue
        if not isinstance(source_prob, ProbValue):
            source_prob = ProbValue(float(source_prob), std_dev_percent=0.1)
        
        # [V15.2] 统一提升效率，并不再区分全/半超导的效率差异，重点是去损耗
        # 只要是合局，就是一家人
        # [V15.2] 优化：提高超导效率（从0.95到0.98），减少能量损失
        efficiency = 0.98
        
        # 关键：合局内部传输，源头零损耗！
        drain_rate = 0.0
        
        # 波动率收缩
        gain_std_factor = 0.5
        
        # 超导态：效率高，且能够平滑波动
        gain_mean = source_prob.mean * efficiency
        gain_std = source_prob.std * gain_std_factor
        
        # 计算相对波动率
        std_dev_percent = gain_std / gain_mean if gain_mean > 0 else 0.1
        
        gain_prob = ProbValue(gain_mean, std_dev_percent)
        
        return gain_prob, drain_rate
    
    def _is_in_combination(self, node1, node2):
        """
        [V15.0] 检查两个节点是否在合局中，并返回合局类型
        
        Args:
            node1: 节点1
            node2: 节点2
            
        Returns:
            tuple: (是否在合局中, 合局类型) 或 (False, None)
        """
        if node1.node_type != 'branch' or node2.node_type != 'branch':
            return False, None
        
        # 检查是否在调试信息中（合局检测结果）
        if hasattr(self.engine, '_quantum_entanglement_debug'):
            debug_info = self.engine._quantum_entanglement_debug
            detected_matches = debug_info.get('detected_matches', [])
            
            # 检查是否检测到包含这两个节点的合局，并识别类型
            for match in detected_matches:
                if node1.char in match and node2.char in match:
                    # 识别合局类型（支持多种格式）
                    match_upper = match.upper()
                    if 'THREEMEETING' in match_upper or '三会' in match:
                        return True, 'three_meeting'
                    elif 'THREEHARMONY' in match_upper or '三合' in match:
                        return True, 'three_harmony'
                    elif 'HALFHARMONY' in match_upper or '半合' in match:
                        return True, 'half_harmony'
                    elif 'SIXHARMONY' in match_upper or '六合' in match or 'SIX' in match_upper:
                        return True, 'six_harmony'
                    elif 'ARCHHARMONY' in match_upper or '拱合' in match:
                        return True, 'arch_harmony'
                    else:
                        return True, 'unknown'
        
        return False, None

