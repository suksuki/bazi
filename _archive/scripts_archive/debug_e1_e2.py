#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 E1 和 E2 案例的详细算法流程
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.prob_math import ProbValue
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

def analyze_case(case_id, case):
    """详细分析单个案例"""
    print("\n" + "=" * 80)
    print(f"📊 详细分析: {case_id}")
    print("=" * 80)
    print(f"八字: {case['bazi']}")
    print(f"日主: {case['day_master']}")
    print(f"监控目标: {case.get('monitor_target', '日主')}")
    print(f"预期能量比率: {case.get('expected_energy_ratio', 'N/A')}")
    print()
    
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
    
    # 1. 分析初始能量
    print("🔹 步骤 1: 初始能量 (H0)")
    print("-" * 80)
    H0 = verifier.engine.H0
    monitor_target = case.get('monitor_target', None)
    
    if monitor_target:
        initial_energy = verifier._get_element_energy(H0, monitor_target)
        print(f"初始 {monitor_target} 总能量: μ={initial_energy.mean:.4f}, σ={initial_energy.std:.4f}")
        
        # 列出所有该元素的节点
        print(f"\n所有 {monitor_target} 节点:")
        for i, node in enumerate(verifier.engine.nodes):
            if node.element == monitor_target.lower():
                energy = H0[i]
                if isinstance(energy, ProbValue):
                    print(f"  Node {i}: {node.char} ({node.node_type}, pillar={node.pillar_idx}) "
                          f"→ μ={energy.mean:.4f}, σ={energy.std:.4f}")
                else:
                    print(f"  Node {i}: {node.char} ({node.node_type}, pillar={node.pillar_idx}) "
                          f"→ {float(energy):.4f}")
    else:
        initial_energy = verifier._get_node_energy(H0, case['day_master'], pillar_idx=2, node_type='stem')
        print(f"初始日主能量: μ={initial_energy.mean:.4f}, σ={initial_energy.std:.4f}")
    
    # 2. 分析邻接矩阵
    print("\n🔹 步骤 2: 邻接矩阵 (A)")
    print("-" * 80)
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
    
    print(f"水节点数量: {len(water_nodes)}")
    for i, node in water_nodes:
        print(f"  Node {i}: {node.char} ({node.node_type}, pillar={node.pillar_idx})")
    
    print(f"\n火节点数量: {len(fire_nodes)}")
    for i, node in fire_nodes:
        print(f"  Node {i}: {node.char} ({node.node_type}, pillar={node.pillar_idx})")
    
    # 分析水克火的关系
    print(f"\n🔍 水克火关系分析:")
    flow_config = config.get('flow', {})
    control_impact = flow_config.get('controlImpact', 0.5)
    print(f"  controlImpact = {control_impact}")
    print(f"  基础控制权重 = -0.3 * {control_impact} = {-0.3 * control_impact:.4f}")
    
    total_attack_weight = 0.0
    for fire_idx, fire_node in fire_nodes:
        print(f"\n  火节点 {fire_idx} ({fire_node.char}) 受到的攻击:")
        fire_attacks = []
        for water_idx, water_node in water_nodes:
            weight = A[fire_idx, water_idx]
            if weight < 0:  # 负权重表示克
                fire_attacks.append((water_idx, water_node, weight))
                total_attack_weight += abs(weight)
                print(f"    被 Node {water_idx} ({water_node.char}) 攻击: 权重 = {weight:.4f}")
        
        if not fire_attacks:
            print(f"    (无直接攻击)")
    
    print(f"\n  总攻击权重: {total_attack_weight:.4f}")
    
    # 3. 分析传播过程
    print("\n🔹 步骤 3: 能量传播 (H_final = A @ H0)")
    print("-" * 80)
    
    # 计算传播
    H_final = verifier.engine.propagate(max_iterations=1, damping=1.0)
    
    if monitor_target:
        final_energy = verifier._get_element_energy(H_final, monitor_target)
        print(f"最终 {monitor_target} 总能量: μ={final_energy.mean:.4f}, σ={final_energy.std:.4f}")
        
        # 列出所有该元素的节点
        print(f"\n所有 {monitor_target} 节点（传播后）:")
        for i, node in enumerate(verifier.engine.nodes):
            if node.element == monitor_target.lower():
                energy = H_final[i]
                if isinstance(energy, ProbValue):
                    print(f"  Node {i}: {node.char} ({node.node_type}, pillar={node.pillar_idx}) "
                          f"→ μ={energy.mean:.4f}, σ={energy.std:.4f}")
                else:
                    print(f"  Node {i}: {node.char} ({node.node_type}, pillar={node.pillar_idx}) "
                          f"→ {float(energy):.4f}")
    else:
        final_energy = verifier._get_node_energy(H_final, case['day_master'], pillar_idx=2, node_type='stem')
        print(f"最终日主能量: μ={final_energy.mean:.4f}, σ={final_energy.std:.4f}")
    
    # 计算能量比率
    energy_ratio = final_energy.mean / initial_energy.mean if initial_energy.mean != 0 else 0.0
    expected_ratio = case.get('expected_energy_ratio', 1.0)
    error_percent = abs(energy_ratio - expected_ratio) / expected_ratio * 100 if expected_ratio > 0 else 100.0
    
    print(f"\n📈 结果:")
    print(f"  初始能量: μ={initial_energy.mean:.4f}")
    print(f"  最终能量: μ={final_energy.mean:.4f}")
    print(f"  能量比率: {energy_ratio:.4f} (预期: {expected_ratio:.4f})")
    print(f"  误差: {error_percent:.1f}%")
    
    # 4. 详细矩阵计算（仅对火节点）
    if monitor_target and monitor_target.lower() == 'fire':
        print("\n🔹 步骤 4: 详细矩阵计算（火节点）")
        print("-" * 80)
        
        for fire_idx, fire_node in fire_nodes:
            print(f"\n火节点 {fire_idx} ({fire_node.char}):")
            
            # 初始能量
            h0_val = H0[fire_idx]
            h0_mean = h0_val.mean if isinstance(h0_val, ProbValue) else float(h0_val)
            print(f"  H0[{fire_idx}] = {h0_mean:.4f}")
            
            # 计算 A @ H0 的结果
            h_final_val = H_final[fire_idx]
            h_final_mean = h_final_val.mean if isinstance(h_final_val, ProbValue) else float(h_final_val)
            print(f"  H_final[{fire_idx}] = {h_final_mean:.4f}")
            
            # 详细计算过程
            print(f"  计算过程:")
            sum_contrib = 0.0
            for j in range(N):
                weight = A[fire_idx, j]
                if abs(weight) > 1e-6:  # 只显示非零权重
                    h0_j = H0[j]
                    h0_j_mean = h0_j.mean if isinstance(h0_j, ProbValue) else float(h0_j)
                    contrib = weight * h0_j_mean
                    sum_contrib += contrib
                    node_j = verifier.engine.nodes[j]
                    print(f"    + A[{fire_idx},{j}] * H0[{j}] = {weight:.4f} * {h0_j_mean:.4f} = {contrib:.4f} "
                          f"({node_j.char}, {node_j.element})")
            
            print(f"  总和 = {sum_contrib:.4f}")
            print(f"  实际结果 = {h_final_mean:.4f}")
            print(f"  差异 = {abs(sum_contrib - h_final_mean):.6f}")

def main():
    """主函数"""
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
    
    analyze_case('E1_Water_Fire', e1_case)
    analyze_case('E2_Weak_Ctrl', e2_case)

if __name__ == '__main__':
    main()

