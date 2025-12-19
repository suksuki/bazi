#!/usr/bin/env python3
"""
调试季节系数应用
检查 A3 和 A4 为什么能量相同
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

# 强制使用 V13.1 参数
config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
config['physics']['seasonWeights']['xiu'] = 0.85
config['physics']['seasonWeights']['si'] = 0.50

# A3: 甲生午月（泄气）
bazi_a3 = ["甲子", "丙午", "甲子", "甲子"]
# A4: 甲生申月（被克）
bazi_a4 = ["甲子", "丙申", "甲子", "甲子"]

print("="*80)
print("调试季节系数应用")
print("="*80)

# 测试 A3
print("\nA3_Summer: 甲生午月（泄气，系数应为 0.85）")
print("-"*80)
engine_a3 = GraphNetworkEngine(config=config)
# 检查 bazi 是否设置
print(f"初始化前 bazi: {hasattr(engine_a3, 'bazi')}")
H0_a3 = engine_a3.initialize_nodes(bazi_a3, "甲", "男")
print(f"初始化后 bazi: {hasattr(engine_a3, 'bazi')}, 值: {getattr(engine_a3, 'bazi', None)}")
engine_a3.H0 = H0_a3
engine_a3.build_adjacency_matrix()
engine_a3.propagate()

# 检查每个节点的能量和季节系数应用情况
print("\n节点能量详情:")
print("月令: 午 (火)")
for i, node in enumerate(engine_a3.nodes):
    if node.element == 'wood':  # 甲木节点
        energy = node.initial_energy
        # 检查季节系数是否应用
        # 甲木生午火 = 泄气，系数应为 0.85
        expected_factor = 0.85
        # 估算基础能量（如果季节系数正确应用）
        base_energy_est = energy.mean / expected_factor if expected_factor > 0 else energy.mean
        print(f"  {node.char:4s} ({node.pillar_name:6s}) | 元素: {node.element:6s} | 能量: {energy.mean:8.2f} ± {energy.std:6.2f} | 估算基础: {base_energy_est:.2f}")

# 计算总能量 - 检查初始能量和传播后能量
from core.prob_math import ProbValue
print("\n初始能量累加:")
initial_energy_a3 = ProbValue(0.0, std_dev_percent=0.1)
for node in engine_a3.nodes:
    if node.element == 'wood':  # 甲木节点
        initial_energy_a3 = initial_energy_a3 + node.initial_energy
        curr_energy = node.current_energy
        curr_mean = curr_energy.mean if hasattr(curr_energy, 'mean') else float(curr_energy)
        print(f"  {node.char} ({node.pillar_name}): {node.initial_energy.mean:.2f} -> {curr_mean:.2f}")
print(f"初始总能量: {initial_energy_a3.mean:.2f} ± {initial_energy_a3.std:.2f}")

print("\n传播后能量累加:")
self_team_energy_a3 = ProbValue(0.0, std_dev_percent=0.1)
for node in engine_a3.nodes:
    if node.element == 'wood':  # 甲木节点
        self_team_energy_a3 = self_team_energy_a3 + node.current_energy
print(f"传播后总能量: {self_team_energy_a3.mean:.2f} ± {self_team_energy_a3.std:.2f}")

# 测试 A4
print("\n" + "="*80)
print("A4_Autumn: 甲生申月（被克，系数应为 0.50）")
print("-"*80)
engine_a4 = GraphNetworkEngine(config=config)
H0_a4 = engine_a4.initialize_nodes(bazi_a4, "甲", "男")
engine_a4.H0 = H0_a4
engine_a4.build_adjacency_matrix()
engine_a4.propagate()

# 检查每个节点的能量和季节系数应用情况
print("\n节点能量详情:")
print("月令: 申 (金)")
for i, node in enumerate(engine_a4.nodes):
    if node.element == 'wood':  # 甲木节点
        energy = node.initial_energy
        # 检查季节系数是否应用
        # 申金克甲木 = 被克，系数应为 0.50
        expected_factor = 0.50
        # 估算基础能量（如果季节系数正确应用）
        base_energy_est = energy.mean / expected_factor if expected_factor > 0 else energy.mean
        print(f"  {node.char:4s} ({node.pillar_name:6s}) | 元素: {node.element:6s} | 能量: {energy.mean:8.2f} ± {energy.std:6.2f} | 估算基础: {base_energy_est:.2f}")

# 计算总能量 - 检查初始能量和传播后能量
print("\n初始能量累加:")
initial_energy_a4 = ProbValue(0.0, std_dev_percent=0.1)
for node in engine_a4.nodes:
    if node.element == 'wood':  # 甲木节点
        initial_energy_a4 = initial_energy_a4 + node.initial_energy
        curr_energy = node.current_energy
        curr_mean = curr_energy.mean if hasattr(curr_energy, 'mean') else float(curr_energy)
        print(f"  {node.char} ({node.pillar_name}): {node.initial_energy.mean:.2f} -> {curr_mean:.2f}")
print(f"初始总能量: {initial_energy_a4.mean:.2f} ± {initial_energy_a4.std:.2f}")

print("\n传播后能量累加:")
self_team_energy_a4 = ProbValue(0.0, std_dev_percent=0.1)
for node in engine_a4.nodes:
    if node.element == 'wood':  # 甲木节点
        self_team_energy_a4 = self_team_energy_a4 + node.current_energy
print(f"传播后总能量: {self_team_energy_a4.mean:.2f} ± {self_team_energy_a4.std:.2f}")

# 比较
print("\n" + "="*80)
print("对比分析")
print("="*80)
diff = self_team_energy_a3.mean - self_team_energy_a4.mean
ratio = self_team_energy_a3.mean / self_team_energy_a4.mean if self_team_energy_a4.mean > 0 else 0
print(f"A3 能量: {self_team_energy_a3.mean:.2f}")
print(f"A4 能量: {self_team_energy_a4.mean:.2f}")
print(f"差异: {diff:.2f}")
print(f"比值: {ratio:.2f} (预期: 0.85/0.50 = 1.70)")

if abs(diff) < 0.01:
    print("\n❌ 问题：A3 和 A4 能量完全相同！")
    print("   可能原因：")
    print("   1. 季节系数没有正确应用到所有节点")
    print("   2. 有其他因素抵消了差异")
else:
    print(f"\n✅ 有差异，但可能不够大（预期比值 1.70，实际 {ratio:.2f}）")

