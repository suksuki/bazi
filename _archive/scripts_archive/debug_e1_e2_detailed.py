#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试 E1 和 E2 案例：查看矩阵乘法后的中间结果
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.prob_math import ProbValue
from core.engines.flow_engine import FlowEngine
from core.processors.physics import CONTROL
import numpy as np

def deep_merge(base, update):
    """递归合并配置"""
    for key, value in update.items():
        if key.startswith('_'):
            continue
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value

def analyze_control_damage(case_id, case):
    """详细分析克制伤害计算"""
    print("\n" + "=" * 80)
    print(f"📊 详细分析克制伤害: {case_id}")
    print("=" * 80)
    
    # 加载配置
    config = DEFAULT_FULL_ALGO_PARAMS.copy()
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        deep_merge(config, user_config)
    
    # 创建验证器
    verifier = Phase2Verifier(config)
    
    # 初始化
    verifier.engine.initialize_nodes(case['bazi'], case['day_master'])
    verifier.engine._apply_quantum_entanglement_once()
    verifier.engine.build_adjacency_matrix()
    
    H0 = verifier.engine.H0
    A = verifier.engine.adjacency_matrix
    N = len(verifier.engine.nodes)
    
    # 找出所有水节点和火节点
    water_nodes = []
    fire_nodes = []
    for i, node in enumerate(verifier.engine.nodes):
        if node.element == 'water':
            water_nodes.append((i, node))
        elif node.element == 'fire':
            fire_nodes.append((i, node))
    
    print(f"水节点: {len(water_nodes)} 个")
    print(f"火节点: {len(fire_nodes)} 个")
    print()
    
    # 模拟传播过程：矩阵乘法（只包含生关系和比劫关系）
    print("🔹 步骤 1: 矩阵乘法（只包含生关系和比劫关系）")
    print("-" * 80)
    
    temp_adjacency = A.copy()
    for i in range(N):
        for j in range(N):
            if i != j:
                node_j = verifier.engine.nodes[j]
                node_i = verifier.engine.nodes[i]
                weight = temp_adjacency[i][j]
                # 如果是克制关系（负权重），临时设为0
                is_control = (node_j.element in CONTROL and 
                             CONTROL[node_j.element] == node_i.element and 
                             weight < 0)
                if is_control:
                    temp_adjacency[i][j] = 0.0
    
    # 矩阵乘法
    H_after_matrix = temp_adjacency @ H0
    
    print("矩阵乘法后的火节点能量:")
    for fire_idx, fire_node in fire_nodes:
        h_after = H_after_matrix[fire_idx]
        h_after_val = h_after.mean if isinstance(h_after, ProbValue) else float(h_after)
        h0_val = H0[fire_idx].mean if isinstance(H0[fire_idx], ProbValue) else float(H0[fire_idx])
        print(f"  Node {fire_idx} ({fire_node.char}): {h0_val:.4f} → {h_after_val:.4f} "
              f"(变化: {h_after_val - h0_val:+.4f})")
    
    # 计算火元素总能量
    fire_total_after_matrix = ProbValue(0.0, std_dev_percent=0.1)
    for fire_idx, fire_node in fire_nodes:
        h_after = H_after_matrix[fire_idx]
        if isinstance(h_after, ProbValue):
            fire_total_after_matrix = fire_total_after_matrix + h_after
        else:
            fire_total_after_matrix = fire_total_after_matrix + ProbValue(float(h_after), std_dev_percent=0.1)
    
    fire_total_h0 = ProbValue(0.0, std_dev_percent=0.1)
    for fire_idx, fire_node in fire_nodes:
        h0 = H0[fire_idx]
        if isinstance(h0, ProbValue):
            fire_total_h0 = fire_total_h0 + h0
        else:
            fire_total_h0 = fire_total_h0 + ProbValue(float(h0), std_dev_percent=0.1)
    
    print(f"\n火元素总能量:")
    print(f"  H0: {fire_total_h0.mean:.4f}")
    print(f"  矩阵乘法后: {fire_total_after_matrix.mean:.4f}")
    print(f"  变化: {fire_total_after_matrix.mean - fire_total_h0.mean:+.4f}")
    
    # 步骤 2: 计算克制伤害
    print("\n🔹 步骤 2: 克制伤害计算")
    print("-" * 80)
    
    flow_config = config.get('flow', {})
    base_impact = flow_config.get('controlImpact', 0.8)
    
    print(f"controlImpact = {base_impact}")
    print()
    
    total_damage = 0.0
    for fire_idx, fire_node in fire_nodes:
        print(f"火节点 {fire_idx} ({fire_node.char}):")
        
        # 找到最强的攻击者
        max_attacker_energy = ProbValue(0.0, std_dev_percent=0.1)
        max_weight = 0.0
        max_attacker_idx = -1
        
        for water_idx, water_node in water_nodes:
            weight = A[fire_idx, water_idx]
            if weight < 0:  # 负权重表示克
                attacker_energy = H0[water_idx] if isinstance(H0[water_idx], ProbValue) else ProbValue(float(H0[water_idx]), std_dev_percent=0.1)
                if abs(weight) > max_weight:
                    max_attacker_energy = attacker_energy
                    max_weight = abs(weight)
                    max_attacker_idx = water_idx
        
        if max_attacker_idx >= 0:
            attacker_val = max_attacker_energy.mean
            target_energy_snapshot = H0[fire_idx] if isinstance(H0[fire_idx], ProbValue) else ProbValue(float(H0[fire_idx]), std_dev_percent=0.1)
            defender_val = target_energy_snapshot.mean
            
            target_energy_current = H_after_matrix[fire_idx] if isinstance(H_after_matrix[fire_idx], ProbValue) else ProbValue(float(H_after_matrix[fire_idx]), std_dev_percent=0.1)
            target_energy_current_val = target_energy_current.mean
            
            print(f"  攻击者: Node {max_attacker_idx}, 能量={attacker_val:.4f}, 权重={max_weight:.4f}")
            print(f"  防御者快照能量: {defender_val:.4f}")
            print(f"  防御者当前能量（矩阵乘法后）: {target_energy_current_val:.4f}")
            
            # 使用 Sigmoid 公式计算伤害
            damage_value = FlowEngine.calculate_control_damage(attacker_val, defender_val, base_impact)
            
            # 伤害限制
            max_allowed_damage_by_snapshot = max(defender_val * 0.5, 0.0)
            max_allowed_damage_by_current = max(target_energy_current_val * 0.9, 0.0)
            actual_damage = min(damage_value, max_allowed_damage_by_snapshot, max_allowed_damage_by_current)
            
            print(f"  Sigmoid伤害: {damage_value:.4f}")
            print(f"  快照能量50%限制: {max_allowed_damage_by_snapshot:.4f}")
            print(f"  当前能量90%限制: {max_allowed_damage_by_current:.4f}")
            print(f"  实际伤害: {actual_damage:.4f}")
            print(f"  最终能量: {target_energy_current_val:.4f} - {actual_damage:.4f} = {target_energy_current_val - actual_damage:.4f}")
            
            total_damage += actual_damage
        else:
            print(f"  (无攻击者)")
    
    print(f"\n总伤害: {total_damage:.4f}")
    
    # 步骤 3: 最终结果
    print("\n🔹 步骤 3: 最终结果对比")
    print("-" * 80)
    
    # 执行实际传播
    H_final = verifier.engine.propagate(max_iterations=1, damping=1.0)
    
    fire_total_final = ProbValue(0.0, std_dev_percent=0.1)
    for fire_idx, fire_node in fire_nodes:
        h_final = H_final[fire_idx]
        if isinstance(h_final, ProbValue):
            fire_total_final = fire_total_final + h_final
        else:
            fire_total_final = fire_total_final + ProbValue(float(h_final), std_dev_percent=0.1)
    
    print(f"初始能量: {fire_total_h0.mean:.4f}")
    print(f"矩阵乘法后: {fire_total_after_matrix.mean:.4f}")
    print(f"最终能量: {fire_total_final.mean:.4f}")
    print(f"能量比率: {fire_total_final.mean / fire_total_h0.mean:.4f} (预期: {case.get('expected_energy_ratio', 1.0):.4f})")

def main():
    # E1 案例
    e1_case = {
        'id': 'E1_Water_Fire',
        'bazi': ['壬子', '丙午', '壬子', '壬子'],
        'day_master': '壬',
        'gender': '男',
        'monitor_target': 'Fire',
        'expected_energy_ratio': 0.5,
        'desc': '水火激战 - 强水克火，火能量应急剧下降'
    }
    
    # E2 案例
    e2_case = {
        'id': 'E2_Weak_Ctrl',
        'bazi': ['壬午', '丙午', '丙午', '丙午'],
        'day_master': '壬',
        'gender': '男',
        'monitor_target': 'Fire',
        'expected_energy_ratio': 0.9,
        'desc': '杯水车薪 - 弱水克强火，火能量下降不明显（甚至反克）'
    }
    
    analyze_control_damage('E1_Water_Fire', e1_case)
    analyze_control_damage('E2_Weak_Ctrl', e2_case)

if __name__ == '__main__':
    main()

