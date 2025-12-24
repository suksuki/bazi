"""
量子纠缠模块 (Quantum Entanglement)
===================================

负责检测和应用干支的合化与刑冲（三会、三合、半合、拱合、六合、天干五合）

在传播之前，只应用一次！
合化是结构性的，只应计算一次，不应在循环中重复应用。
合化增益应该作为一次性修正应用到初始能量（H0），而不是通过矩阵乘法重复应用。
"""

import math
from typing import Dict, List, Any, Set
from core.math import ProbValue
from core.interactions import BRANCH_SIX_COMBINES, STEM_COMBINATIONS
from core.engine_graph.wave_physics import WavePhysicsEngine


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
        """
        if not hasattr(self.engine, 'H0') or self.engine.H0 is None:
            return
        
        interactions_config = self.config.get('interactions', {})
        branch_events = interactions_config.get('branchEvents', {})
        combo_physics = interactions_config.get('comboPhysics', {})
        # V11.0: 墓库配置适配
        vault_config = interactions_config.get('vault', interactions_config.get('vaultPhysics', {}))
        
        # 收集所有地支节点
        branch_nodes = [(i, node) for i, node in enumerate(self.engine.nodes) 
                       if node.node_type == 'branch']
        branch_chars = {node.char for _, node in branch_nodes}
        
        # [V15.3] 调试信息
        debug_info = {
            'detected_matches': [],
            'node_changes': [],
            'energy_snapshots': {}
        }
        
        self._apply_branch_harmonies(branch_nodes, branch_chars, branch_events, combo_physics, debug_info)
        self._apply_stem_harmonies(interactions_config, debug_info)
        self._apply_branch_clashes(branch_nodes, branch_events, vault_config, debug_info)
        self._apply_branch_punishments(branch_nodes, branch_events, debug_info)
        
        # [V15.3] 保存调试信息到引擎
        self.engine._quantum_entanglement_debug = debug_info

    def _apply_branch_harmonies(self, branch_nodes, branch_chars, branch_events, combo_physics, debug_info):
        """处理地支合局 (三会、三合、半合、拱合、六合)"""
        # 三会局定义
        three_meeting_groups = [
            ({'亥', '子', '丑'}, 'water'), ({'寅', '卯', '辰'}, 'wood'),
            ({'巳', '午', '未'}, 'fire'), ({'申', '酉', '戌'}, 'metal'),
        ]
        # 三合局定义
        trine_groups = [
            ({'申', '子', '辰'}, 'water'), ({'亥', '卯', '未'}, 'wood'),
            ({'寅', '午', '戌'}, 'fire'), ({'巳', '酉', '丑'}, 'metal'),
        ]
        
        # 1. 三会方局 (Three Meeting) - 多体共振
        for group, element in three_meeting_groups:
            if group.issubset(branch_chars):
                indices = [i for i, node in branch_nodes if node.char in group]
                if len(indices) >= 3:
                    # 获取能量及Q值
                    energies = [float(self.engine.nodes[idx].initial_energy.mean if isinstance(self.engine.nodes[idx].initial_energy, ProbValue) else self.engine.nodes[idx].initial_energy) for idx in indices]
                    q_factor = combo_physics.get('threeMeetingQ', 2.5) # 强共振
                    
                    # 计算共振总能量
                    energy_net = WavePhysicsEngine.compute_resonance(energies, q_factor)
                    tag = f"ThreeMeeting({element})"
                    
                    # 记录并分配
                    if f"{tag} Reson" not in debug_info['detected_matches']:
                         debug_info['detected_matches'].append(f"🔗 {tag} 共振激活! Net={energy_net:.2f}")
                    
                    self._distribute_wave_energy(indices, energies, energy_net, element, tag, debug_info)

        # 2. 三合局 (Trine Harmony) - 多体共振
        for group, element in trine_groups:
            if group.issubset(branch_chars):
                indices = [i for i, node in branch_nodes if node.char in group]
                if len(indices) >= 3:
                    energies = [float(self.engine.nodes[idx].initial_energy.mean if isinstance(self.engine.nodes[idx].initial_energy, ProbValue) else self.engine.nodes[idx].initial_energy) for idx in indices]
                    q_factor = branch_events.get('threeHarmony', {}).get('resonanceQ', 2.0)
                    
                    energy_net = WavePhysicsEngine.compute_resonance(energies, q_factor)
                    tag = f"ThreeHarmony({element})"
                    
                    if f"{tag} Reson" not in debug_info['detected_matches']:
                         debug_info['detected_matches'].append(f"🔗 {tag} 共振激活! Net={energy_net:.2f}")
                    
                    self._distribute_wave_energy(indices, energies, energy_net, element, tag, debug_info)

        # 3. 处理二合局 (六合、半合、拱合) - 双体干涉
        processed_pairs = set()
        
        # 六合映射
        six_combine_map = {
            frozenset({'子', '丑'}): 'earth', frozenset({'寅', '亥'}): 'wood',
            frozenset({'卯', '戌'}): 'fire', frozenset({'辰', '酉'}): 'metal',
            frozenset({'巳', '申'}): 'water', frozenset({'午', '未'}): 'earth',
        }
        # 半合与拱合映射
        half_harmony_map = {
            frozenset({'申', '子'}): 'water', frozenset({'子', '辰'}): 'water',
            frozenset({'亥', '卯'}): 'wood', frozenset({'卯', '未'}): 'wood',
            frozenset({'寅', '午'}): 'fire', frozenset({'午', '戌'}): 'fire',
            frozenset({'巳', '酉'}): 'metal', frozenset({'酉', '丑'}): 'metal',
        }
        arch_harmony_map = {
            frozenset({'申', '辰'}): 'water', frozenset({'亥', '未'}): 'wood',
            frozenset({'寅', '戌'}): 'fire', frozenset({'巳', '丑'}): 'metal',
        }

        for i, (idx1, node1) in enumerate(branch_nodes):
            for j, (idx2, node2) in enumerate(branch_nodes):
                if i >= j: continue
                pair = frozenset({node1.node_id, node2.node_id})
                if pair in processed_pairs: continue
                
                chars = frozenset({node1.char, node2.char})
                
                interaction_type = None
                target_element = None
                phase_rad = 0.0
                entropy = 0.95
                
                # Check Six Harmony (同相)
                if chars in six_combine_map:
                    interaction_type = "sixHarmony"
                    target_element = six_combine_map[chars]
                    phase_rad = 0.1  # 接近 0度
                    entropy = 0.98
                # Check Half Harmony (30度)
                elif chars in half_harmony_map:
                    interaction_type = "halfHarmony"
                    target_element = half_harmony_map[chars]
                    phase_rad = 0.52 # ~30度
                    entropy = 0.90
                # Check Arch Harmony (45度)
                elif chars in arch_harmony_map:
                    interaction_type = "archHarmony"
                    target_element = arch_harmony_map[chars]
                    phase_rad = 0.78 # ~45度
                    entropy = 0.85
                
                if interaction_type:
                    processed_pairs.add(pair)
                    
                    e1 = float(node1.initial_energy.mean if isinstance(node1.initial_energy, ProbValue) else node1.initial_energy)
                    e2 = float(node2.initial_energy.mean if isinstance(node2.initial_energy, ProbValue) else node2.initial_energy)
                    
                    # 构造参数
                    params = {
                        f"{interaction_type}_phase": phase_rad,
                        f"{interaction_type}_entropy": entropy
                    }
                    
                    # 计算干涉
                    energy_net = WavePhysicsEngine.compute_interference(e1, e2, interaction_type, params)
                    
                    if f"{interaction_type} Wave" not in debug_info['detected_matches']:
                        debug_info['detected_matches'].append(f"🌊 {interaction_type} 干涉: {node1.char}+{node2.char} -> Net={energy_net:.2f}")
                    
                    # 分配能量并转化
                    self._distribute_wave_energy([idx1, idx2], [e1, e2], energy_net, target_element, interaction_type, debug_info)

    def _apply_branch_clashes(self, branch_nodes, branch_events, vault_config, debug_info):
        """
        [V11.0] 处理地支冲 (Clash) 与墓库开启逻辑
        """
        from core.interactions import BRANCH_CLASHES
        
        # 墓库映射
        VAULT_ELEMENTS = {'辰': 'water', '戌': 'fire', '丑': 'metal', '未': 'wood'}
        
        processed_pairs = set()
        for i, (idx1, node1) in enumerate(branch_nodes):
            for j, (idx2, node2) in enumerate(branch_nodes):
                if i >= j: continue
                pair = frozenset({node1.node_id, node2.node_id})
                if pair in processed_pairs: continue
                
                if BRANCH_CLASHES.get(node1.char) == node2.char:
                    processed_pairs.add(pair)
                    debug_info['detected_matches'].append(f"Clash: {node1.char} vs {node2.char}")
                    
                    # 检查是否涉及墓库
                    vault_found = False
                    is_vault_1 = node1.char in VAULT_ELEMENTS
                    is_vault_2 = node2.char in VAULT_ELEMENTS
                    
                    if is_vault_1 or is_vault_2:
                        vault_found = True
                        # V12.0: 物理判定 - 只要冲的一方能量足够大，就能冲开墓库
                        # 取两者能量最大值作为冲击力
                        e1 = self.engine.H0[idx1].mean if isinstance(self.engine.H0[idx1], ProbValue) else float(self.engine.H0[idx1])
                        e2 = self.engine.H0[idx2].mean if isinstance(self.engine.H0[idx2], ProbValue) else float(self.engine.H0[idx2])
                        impact_energy = max(e1, e2)
                        
                        threshold = vault_config.get('threshold', 3.5)
                        
                        if impact_energy >= threshold:
                            # 冲开 (Open Bonus)
                            bonus = vault_config.get('openBonus', 1.8)
                            tag = "VaultOpen"
                            # 用符号标记，避免刷屏
                            if f"🚀 {node1.char}-{node2.char} Open" not in debug_info['detected_matches']:
                                debug_info['detected_matches'].append(f"🚀 {node1.char} vs {node2.char} 财库冲开！(Impact={impact_energy:.2f} >= {threshold})")
                        else:
                            # 冲不破反受损 (Break Penalty)
                            bonus = vault_config.get('breakPenalty', 0.5)
                            tag = "TombBreak"
                            if f"💥 {node1.char}-{node2.char} Break" not in debug_info['detected_matches']:
                                debug_info['detected_matches'].append(f"💥 {node1.char} vs {node2.char} 墓库冲破！(Impact={impact_energy:.2f} < {threshold})")
                        
                        # 应用能量修正 (对双方都应用，因为是相互作用)
                        self._apply_energy_modifier(idx1, bonus, debug_info)
                        self._apply_energy_modifier(idx2, bonus, debug_info)
                        
                        # V11.0: 同时也激活涉及元素的其他节点 (共振)
                        if is_vault_1:
                            v_elem = VAULT_ELEMENTS[node1.char]
                            for k, t_node in enumerate(self.engine.nodes):
                                if t_node.element == v_elem and k != idx1 and k != idx2:
                                    self._apply_energy_modifier(k, bonus, debug_info)
                        if is_vault_2:
                            v_elem = VAULT_ELEMENTS[node2.char]
                            for k, t_node in enumerate(self.engine.nodes):
                                if t_node.element == v_elem and k != idx1 and k != idx2:
                                    self._apply_energy_modifier(k, bonus, debug_info)
                    
                    if not vault_found:
                        # [V12.0] 普通冲：应用波相消干涉 (Destructive Interference)
                        e1 = float(node1.initial_energy.mean if isinstance(node1.initial_energy, ProbValue) else node1.initial_energy)
                        e2 = float(node2.initial_energy.mean if isinstance(node2.initial_energy, ProbValue) else node2.initial_energy)
                        
                        # 获取物理参数 (相位角与熵)
                        physics_params = {
                            "clash_phase": branch_events.get("clashPhase", math.pi * 0.95), # 接近180度
                            "clash_entropy": branch_events.get("clashEntropy", 0.6)        # 热损耗
                        }
                        
                        # 计算叠加后的剩余总能量
                        energy_net = WavePhysicsEngine.compute_interference(e1, e2, "clash", physics_params)
                        
                        # 按比例分配回原节点（简单物理：剩余能量平分）
                        multiplier1 = (energy_net / 2.0) / e1 if e1 > 0 else 0
                        multiplier2 = (energy_net / 2.0) / e2 if e2 > 0 else 0
                        
                        self._apply_energy_modifier(idx1, multiplier1, debug_info)
                        self._apply_energy_modifier(idx2, multiplier2, debug_info)

    def _distribute_wave_energy(self, indices, base_energies, net_energy, target_element, match_type, debug_info):
        """
        [V12.0] 波动力学能量分配器
        将干涉/共振后的总能量 Net Energy 重新分配给参与节点，并执行元素转化。
        分配原则：按原能量比例分配 (Proportional Distribution)。
        """
        total_base = sum(base_energies)
        if total_base <= 0: return

        # 计算每个节点的增益倍数 (用于记录 change)
        # Multiplier = (Net * (Base/Total)) / Base = Net / Total
        # 所以每个节点的倍数是一样的
        global_multiplier = net_energy / total_base

        for idx, node in zip(indices, [self.engine.nodes[i] for i in indices]):
            old_element = node.element
            
            # 应用能量
            self._apply_energy_modifier(idx, global_multiplier, debug_info)
            node.is_locked = True
            
            # 元素转化
            if target_element and node.element != target_element:
                node.element = target_element
                node.original_element = old_element
                debug_info['node_changes'].append(f"{match_type}: {node.char}({old_element}) -> {node.char}({target_element})")

        # 天干引动 (Stem Activation)
        # 如果地支成局，同五行天干也会受到“共振”
        if target_element:
            for i, node in enumerate(self.engine.nodes):
                if node.node_type == 'stem' and node.element == target_element:
                    # 天干受到 30% 的共振增益
                    self._apply_energy_modifier(i, 1.3, debug_info)

    def _apply_branch_punishments(self, branch_nodes, branch_events, debug_info):
        """
        [V11.1] 处理地支刑 (Punishment)
        区分通用刑（损耗）与土刑（激旺）
        """
        punishment_groups = [
            ({'寅', '巳', '申'}, 'general'), # 寅巳申三刑
            ({'丑', '未', '戌'}, 'earth'),   # 丑未戌三刑
            ({'子', '卯'}, 'general'),       # 子卯相刑
            ({'辰'}, 'earth_self'),          # 辰辰自刑
            ({'午'}, 'self'),                # 午午自刑
            ({'酉'}, 'self'),                # 酉酉自刑
            ({'亥'}, 'self'),                # 亥亥自刑
        ]
        
        branch_chars = {node.char for _, node in branch_nodes}
        penalty = branch_events.get('punishmentPenalty', 0.3)
        earth_bonus = branch_events.get('earthlyPunishmentBonus', 1.3)
        
        # 1. 三刑处理
        for group, p_type in punishment_groups:
            if len(group) > 1 and group.issubset(branch_chars):
                indices = [i for i, node in branch_nodes if node.char in group]
                
                # [V12.0] 波动力学路径
                res_energies = [float(self.engine.nodes[idx].initial_energy.mean if isinstance(self.engine.nodes[idx].initial_energy, ProbValue) else self.engine.nodes[idx].initial_energy) for idx in indices]
                
                if p_type in ['earth', 'earth_self']:
                    # 土刑共振 (Resonance)
                    q_factor = branch_events.get('resonanceQ', 1.3)
                    energy_net = WavePhysicsEngine.compute_resonance(res_energies, q_factor)
                else:
                    # 通用刑干涉 (Interference)
                    e1 = res_energies[0]
                    # 简化多体为两体干涉或逐个叠加
                    e2 = sum(res_energies[1:])
                    physics_params = {
                        "punish_phase": branch_events.get("punishPhase", math.pi * 0.8), # 反相
                        "punish_entropy": branch_events.get("punishEntropy", 0.7)
                    }
                    energy_net = WavePhysicsEngine.compute_interference(e1, e2, "punish", physics_params)
                
                debug_info['detected_matches'].append(f"{p_type.capitalize()} Punishment (Wave): {group} -> Net={energy_net:.2f}")
                
                # 分配能量
                total_base = sum(res_energies)
                for idx, e_base in zip(indices, res_energies):
                    multiplier = (energy_net * (e_base / total_base)) / e_base if e_base > 0 else 0
                    self._apply_energy_modifier(idx, multiplier, debug_info)
            
            # 2. 自刑处理
            elif len(group) == 1:
                char = list(group)[0]
                indices = [i for i, node in branch_nodes if node.char == char]
                if len(indices) >= 2:
                    multiplier = earth_bonus if p_type == 'earth_self' else penalty
                    debug_info['detected_matches'].append(f"Self-Punishment: {char}")
                    for idx in indices:
                        self._apply_energy_modifier(idx, multiplier, debug_info)

    def _apply_energy_modifier(self, idx, multiplier, debug_info):
        """统一应用能量乘数"""
        if isinstance(self.engine.H0[idx], ProbValue):
            self.engine.H0[idx] = self.engine.H0[idx] * multiplier
        else:
            self.engine.H0[idx] = ProbValue(float(self.engine.H0[idx]) * multiplier, std_dev_percent=0.1)
        
        self.engine.nodes[idx].initial_energy = self.engine.H0[idx]
        self.engine.nodes[idx].current_energy = self.engine.H0[idx]

    def _apply_stem_harmonies(self, interactions_config, debug_info):
        """
        [V13.7 物理化升级] 处理天干五合：引入地理能垒修正（阿伦尼乌斯公式）
        
        核心公式：P_transform = A * exp(-E_a / (k_B * T_geo))
        - E_a: 活化能垒（受地理环境影响）
        - T_geo: 地理温度（从InfluenceBus获取）
        - k_B: 玻尔兹曼常数（归一化为1.0）
        
        火区环境下，化火成功率遵循阿伦尼乌斯公式修正。
        """
        stem_nodes = [(i, node) for i, node in enumerate(self.engine.nodes) if node.node_type == 'stem']
        processed_pairs = set()
        
        stem_combine_map = {
            ('甲', '己'): 'earth', ('乙', '庚'): 'metal', ('丙', '辛'): 'water',
            ('丁', '壬'): 'wood', ('戊', '癸'): 'fire',
        }
        
        # [V13.7] 提取地理修正（从engine的geo_modifiers或InfluenceBus）
        geo_modifiers = getattr(self.engine, 'geo_modifiers', {}) or {}
        geo_temperature = 1.0  # 默认地理温度
        for elem, factor in geo_modifiers.items():
            if elem.lower() == 'fire' and factor > 1.0:
                # 火区环境：提高地理温度，降低化火能垒
                geo_temperature = factor
                break
        
        for i, (idx1, node1) in enumerate(stem_nodes):
            for j, (idx2, node2) in enumerate(stem_nodes):
                if i >= j: continue
                pair = frozenset({node1.node_id, node2.node_id})
                if pair in processed_pairs: continue
                
                chars = (node1.char, node2.char)
                target_element = stem_combine_map.get(chars) or stem_combine_map.get((chars[1], chars[0]))
                
                if target_element:
                    processed_pairs.add(pair)
                    cfg = interactions_config.get('stemFiveCombination', {})
                    base_threshold = cfg.get('threshold', 3.0)
                    bonus = cfg.get('bonus', 1.5)
                    penalty_val = cfg.get('penalty', 0.7)
                    
                    e1 = float(self.engine.H0[idx1].mean if isinstance(self.engine.H0[idx1], ProbValue) else self.engine.H0[idx1])
                    e2 = float(self.engine.H0[idx2].mean if isinstance(self.engine.H0[idx2], ProbValue) else self.engine.H0[idx2])
                    
                    # [V13.7] 使用整合后的合化相位判定算法（包含阿伦尼乌斯公式修正）
                    from core.trinity.core.assets.combination_phase_logic import check_combination_phase
                    
                    # 计算月令能量（归一化到0-1范围）
                    # base_threshold 通常是 3.0，我们需要将能量归一化
                    avg_energy = (e1 + e2) / 2.0
                    month_energy_normalized = avg_energy / max(base_threshold, 1.0)  # 归一化
                    
                    # 调用整合后的算法
                    combo_result = check_combination_phase(
                        stems=[node1.char, node2.char],
                        month_energy=month_energy_normalized,
                        geo_temperature=geo_temperature,
                        target_element=target_element
                    )
                    
                    # [V12.0] 天干五合波动力学化（使用算法返回的结果）
                    if combo_result.get("status") == "PHASE_TRANSITION":
                        # 成功合化：强相长干涉 (Phase = 0)
                        params = {"stem_combine_phase": 0.05, "stem_combine_entropy": 0.95}
                        energy_net = WavePhysicsEngine.compute_interference(e1, e2, "stem_combine", params)
                        
                        # [V13.7] 记录地理修正信息（从算法结果中获取）
                        geo_correction = combo_result.get("geo_correction", {})
                        if geo_correction.get("applied"):
                            debug_info['detected_matches'].append(
                                f"🔥 化火成功（地理能垒修正）: {node1.char}+{node2.char} -> {target_element} "
                                f"(E_a={geo_correction.get('E_a', 0):.3f}, T_geo={geo_correction.get('T_geo', 1.0):.2f}, "
                                f"P={geo_correction.get('transform_probability', 1.0):.3f})"
                            )
                        
                        # 分配能量
                        self._distribute_wave_energy([idx1, idx2], [e1, e2], energy_net, target_element, "StemFiveCombine", debug_info)
                    else:
                        # 羁绊：相消干涉 (Destructive Interference)
                        # Phase = 120度 (阻滞)
                        params = {"stem_bind_phase": 2.09, "stem_bind_entropy": 0.8} 
                        energy_net = WavePhysicsEngine.compute_interference(e1, e2, "stem_bind", params)
                        
                        # 分配惩罚
                        self._distribute_wave_energy([idx1, idx2], [e1, e2], energy_net, None, "StemBind", debug_info)
                        debug_info['detected_matches'].append(f"StemBind (Wave): {node1.char}+{node2.char} -> Net={energy_net:.2f}")
