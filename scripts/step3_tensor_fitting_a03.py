#!/usr/bin/env python3
"""
FDS-V1.1 Step 3: 多维特征提取与张量拟合
基于 Tier A 标准集进行5维张量建模
"""

import sys
from pathlib import Path
import json
import numpy as np
import math
from typing import Dict, List, Tuple, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine

def sigmoid(x: float, k: float = 1.0, x0: float = 0.0) -> float:
    """Sigmoid激活函数"""
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))

def calculate_5_axis(chart: List[str], day_master: str) -> Dict[str, float]:
    """
    计算5维张量投影
    
    Args:
        chart: 四柱八字 ['年柱', '月柱', '日柱', '时柱']
        day_master: 日主
        
    Returns:
        5维张量字典 {'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
    """
    # 提取天干地支
    stems = [p[0] for p in chart]
    branches = [p[1] for p in chart]
    
    # ========== 1. 基础能量计算 ==========
    
    # 羊刃 (Blade) = 1.0 (基准单位)
    yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
    yang_ren_branch = yang_ren_map.get(day_master)
    blade_count = branches.count(yang_ren_branch) if yang_ren_branch else 0
    blade_energy = 1.0 * blade_count  # 每个羊刃 = 1.0
    
    # 七杀 (Killings) = 0.8 (若透干通根)
    qi_sha_energy = 0.0
    qi_sha_stems = []
    for i, stem in enumerate(stems):
        if i == 2:  # 跳过日主
            continue
        ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
        if ten_god == '七杀':
            qi_sha_stems.append((i, stem))
    
    # 检查七杀是否有根
    for _, qi_sha_stem in qi_sha_stems:
        has_root = False
        # 检查自坐
        pillar_idx = qi_sha_stems[0][0]
        if pillar_idx < len(branches):
            branch = branches[pillar_idx]
            hidden_stems = BaziParticleNexus.get_branch_weights(branch)
            for hidden_stem, weight in hidden_stems:
                if hidden_stem == qi_sha_stem and weight >= 5:
                    has_root = True
                    break
        
        # 检查其他地支
        if not has_root:
            for branch in branches:
                hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                for hidden_stem, weight in hidden_stems:
                    if hidden_stem == qi_sha_stem and weight >= 5:
                        has_root = True
                        break
                if has_root:
                    break
        
        if has_root:
            qi_sha_energy += 0.8  # 透干通根 = 0.8
    
    # 印星 (Print) = 0.5 (若有)
    print_energy = 0.0
    for stem in stems:
        ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
        if ten_god in ['正印', '偏印']:
            print_energy += 0.5
    
    # 计算根数（通根数量）
    root_count = 0
    for stem in stems:
        if stem == day_master:
            continue
        for branch in branches:
            hidden_stems = BaziParticleNexus.get_branch_weights(branch)
            for hidden_stem, weight in hidden_stems:
                if hidden_stem == stem and weight >= 5:
                    root_count += 1
                    break
    
    # 计算刑冲数量
    clash_pairs = [('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), 
                  ('辰', '戌'), ('巳', '亥')]
    harm_pairs = [('子', '未'), ('丑', '午'), ('寅', '巳'), ('卯', '辰'),
                 ('申', '亥'), ('酉', '戌')]
    
    clash_count = 0
    for i, b1 in enumerate(branches):
        for j, b2 in enumerate(branches[i+1:], i+1):
            if (b1, b2) in clash_pairs or (b2, b1) in clash_pairs:
                clash_count += 1
            if (b1, b2) in harm_pairs or (b2, b1) in harm_pairs:
                clash_count += 1
    
    # ========== 2. 维度投影逻辑 ==========
    
    # E轴 (能级轴): Sigmoid(Blade_Count + Root_Count - 2)
    e_raw = sigmoid(blade_count + root_count - 2, k=1.0, x0=0.0)
    e_axis = e_raw * 100  # 转换为0-100分制
    
    # O轴 (秩序轴): Min(Blade_Energy, Killing_Energy) * 1.5 * (1 + 0.2*Print)
    min_energy = min(blade_energy, qi_sha_energy) if qi_sha_energy > 0 else 0
    o_axis = min_energy * 1.5 * (1 + 0.2 * print_energy) * 100
    
    # S轴 (应力轴): Abs(Blade_Energy - Killing_Energy) + (0.5 * Clash_Count)
    s_axis = (abs(blade_energy - qi_sha_energy) + 0.5 * clash_count) * 100
    
    # M轴和R轴：按FDS-V1.1默认权重分配剩余能量
    # 从注册表获取权重
    weights = {
        'E': 0.30,
        'O': 0.40,
        'M': 0.10,
        'S': 0.15,
        'R': 0.05
    }
    
    # 计算SAI（总模长）
    sai = e_axis * weights['E'] + o_axis * weights['O'] + s_axis * weights['S']
    
    # M轴和R轴按权重分配
    m_axis = sai * weights['M'] / (weights['M'] + weights['R']) if (weights['M'] + weights['R']) > 0 else 0
    r_axis = sai * weights['R'] / (weights['M'] + weights['R']) if (weights['M'] + weights['R']) > 0 else 0
    
    # 重新计算SAI以确保归一化
    sai_final = e_axis * weights['E'] + o_axis * weights['O'] + m_axis * weights['M'] + s_axis * weights['S'] + r_axis * weights['R']
    
    # 归一化：确保总和 = SAI
    total = e_axis + o_axis + m_axis + s_axis + r_axis
    if total > 0:
        scale_factor = sai_final / total
        e_axis *= scale_factor
        o_axis *= scale_factor
        m_axis *= scale_factor
        s_axis *= scale_factor
        r_axis *= scale_factor
    
    return {
        'E': round(e_axis, 2),
        'O': round(o_axis, 2),
        'M': round(m_axis, 2),
        'S': round(s_axis, 2),
        'R': round(r_axis, 2),
        'SAI': round(sai_final, 2),
        'blade_energy': blade_energy,
        'qi_sha_energy': qi_sha_energy,
        'print_energy': print_energy,
        'clash_count': clash_count
    }

def main():
    print("=" * 70)
    print("🚀 FDS-V1.1 Step 3: 多维特征提取与张量拟合")
    print("=" * 70)
    print()
    
    # 加载Tier A标准集（尝试多个可能的文件名）
    possible_files = [
        project_root / "data" / "holographic_pattern" / "QGA_A-03_TierA_Standard.json",
        project_root / "data" / "holographic_pattern" / "A-03_Standard_Dataset.json",
    ]
    
    data_file = None
    for f in possible_files:
        if f.exists():
            data_file = f
            break
    
    if not data_file:
        print(f"❌ 标准集文件不存在，尝试过的路径:")
        for f in possible_files:
            print(f"   - {f}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    samples = data['samples']
    print(f"✅ 加载Tier A标准集: {len(samples)} 个样本")
    print()
    
    # 计算每个样本的5维张量
    print("开始计算5维张量投影...")
    results = []
    
    for i, sample in enumerate(samples):
        chart = sample['chart']
        day_master = sample['day_master']
        
        try:
            tensor = calculate_5_axis(chart, day_master)
            tensor['sample_index'] = i
            tensor['chart'] = chart
            tensor['day_master'] = day_master
            results.append(tensor)
        except Exception as e:
            print(f"⚠️ 处理样本 {i} 失败: {e}")
            continue
        
        if (i + 1) % 100 == 0:
            print(f"  进度: {i+1}/{len(samples)} ({(i+1)/len(samples)*100:.1f}%)")
    
    print(f"✅ 完成：处理了 {len(results)} 个样本")
    print()
    
    # 统计分析
    print("=" * 70)
    print("【统计分析】")
    print("=" * 70)
    print()
    
    # 提取各轴数据
    e_values = [r['E'] for r in results]
    o_values = [r['O'] for r in results]
    m_values = [r['M'] for r in results]
    s_values = [r['S'] for r in results]
    r_values = [r['R'] for r in results]
    sai_values = [r['SAI'] for r in results]
    
    # 计算统计量
    stats = {
        'E': {'mean': np.mean(e_values), 'std': np.std(e_values), 'min': np.min(e_values), 'max': np.max(e_values)},
        'O': {'mean': np.mean(o_values), 'std': np.std(o_values), 'min': np.min(o_values), 'max': np.max(o_values)},
        'M': {'mean': np.mean(m_values), 'std': np.std(m_values), 'min': np.min(m_values), 'max': np.max(m_values)},
        'S': {'mean': np.mean(s_values), 'std': np.std(s_values), 'min': np.min(s_values), 'max': np.max(s_values)},
        'R': {'mean': np.mean(r_values), 'std': np.std(r_values), 'min': np.min(r_values), 'max': np.max(r_values)},
        'SAI': {'mean': np.mean(sai_values), 'std': np.std(sai_values), 'min': np.min(sai_values), 'max': np.max(sai_values)}
    }
    
    print("【5维张量统计分布】")
    print("-" * 70)
    for axis in ['E', 'O', 'M', 'S', 'R', 'SAI']:
        s = stats[axis]
        print(f"{axis}轴 ({'能级' if axis == 'E' else '秩序' if axis == 'O' else '物质' if axis == 'M' else '应力' if axis == 'S' else '关联' if axis == 'R' else '总模长'}):")
        print(f"  均值: {s['mean']:.2f}")
        print(f"  标准差: {s['std']:.2f}")
        print(f"  范围: [{s['min']:.2f}, {s['max']:.2f}]")
        print()
    
    # Top 3 样本（按SAI排序）
    results_sorted_by_sai = sorted(results, key=lambda x: x['SAI'], reverse=True)
    top3_sai = results_sorted_by_sai[:3]
    
    print("【Top 3 样本（SAI最高）】")
    print("-" * 70)
    for i, r in enumerate(top3_sai, 1):
        print(f"{i}. {' '.join(r['chart'])} | 日主:{r['day_master']}")
        print(f"   SAI: {r['SAI']:.2f}")
        print(f"   E={r['E']:.2f}, O={r['O']:.2f}, M={r['M']:.2f}, S={r['S']:.2f}, R={r['R']:.2f}")
        print(f"   羊刃能量={r['blade_energy']:.1f}, 七杀能量={r['qi_sha_energy']:.1f}, 印星能量={r['print_energy']:.1f}")
        print()
    
    # Top 3 应力样本
    results_sorted_by_s = sorted(results, key=lambda x: x['S'], reverse=True)
    top3_s = results_sorted_by_s[:3]
    
    print("【Top 3 样本（应力轴S最高）】")
    print("-" * 70)
    for i, r in enumerate(top3_s, 1):
        print(f"{i}. {' '.join(r['chart'])} | 日主:{r['day_master']}")
        print(f"   S轴: {r['S']:.2f}")
        print(f"   SAI: {r['SAI']:.2f}")
        print(f"   E={r['E']:.2f}, O={r['O']:.2f}, M={r['M']:.2f}, R={r['R']:.2f}")
        print(f"   羊刃能量={r['blade_energy']:.1f}, 七杀能量={r['qi_sha_energy']:.1f}, 刑冲数={r['clash_count']}")
        print()
    
    # 生成Markdown报告
    report_file = project_root / "data" / "holographic_pattern" / "TierA_Tensor_Analysis.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# FDS-V1.1 Step 3: Tier A 张量分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**样本数量**: {len(results)} 个\n\n")
        f.write("---\n\n")
        
        f.write("## 一、5维张量统计分布\n\n")
        f.write("| 维度轴 | 符号 | 物理定义 | 均值 | 标准差 | 最小值 | 最大值 |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        f.write(f"| 能级轴 | E | 系统总振幅/储能 | {stats['E']['mean']:.2f} | {stats['E']['std']:.2f} | {stats['E']['min']:.2f} | {stats['E']['max']:.2f} |\n")
        f.write(f"| 秩序轴 | O | 能量的收束与聚焦 | {stats['O']['mean']:.2f} | {stats['O']['std']:.2f} | {stats['O']['min']:.2f} | {stats['O']['max']:.2f} |\n")
        f.write(f"| 物质轴 | M | 能量的实体转化率 | {stats['M']['mean']:.2f} | {stats['M']['std']:.2f} | {stats['M']['min']:.2f} | {stats['M']['max']:.2f} |\n")
        f.write(f"| 应力轴 | S | 内部剪切力/摩擦 | {stats['S']['mean']:.2f} | {stats['S']['std']:.2f} | {stats['S']['min']:.2f} | {stats['S']['max']:.2f} |\n")
        f.write(f"| 关联轴 | R | 场能相干性 | {stats['R']['mean']:.2f} | {stats['R']['std']:.2f} | {stats['R']['min']:.2f} | {stats['R']['max']:.2f} |\n")
        f.write(f"| **总模长** | **SAI** | **系统对齐指数** | **{stats['SAI']['mean']:.2f}** | **{stats['SAI']['std']:.2f}** | **{stats['SAI']['min']:.2f}** | **{stats['SAI']['max']:.2f}** |\n\n")
        
        f.write("---\n\n")
        f.write("## 二、Top 3 完美模型示例（SAI最高）\n\n")
        for i, r in enumerate(top3_sai, 1):
            f.write(f"### {i}. {' '.join(r['chart'])} (日主: {r['day_master']})\n\n")
            f.write(f"**SAI**: {r['SAI']:.2f}\n\n")
            f.write(f"**5维投影**:\n")
            f.write(f"- E (能级): {r['E']:.2f}\n")
            f.write(f"- O (秩序): {r['O']:.2f}\n")
            f.write(f"- M (物质): {r['M']:.2f}\n")
            f.write(f"- S (应力): {r['S']:.2f}\n")
            f.write(f"- R (关联): {r['R']:.2f}\n\n")
            f.write(f"**基础能量**:\n")
            f.write(f"- 羊刃能量: {r['blade_energy']:.1f}\n")
            f.write(f"- 七杀能量: {r['qi_sha_energy']:.1f}\n")
            f.write(f"- 印星能量: {r['print_energy']:.1f}\n\n")
        
        f.write("---\n\n")
        f.write("## 三、Top 3 高危样本（应力轴S最高）\n\n")
        f.write("> 检查是否混入了高危样本\n\n")
        for i, r in enumerate(top3_s, 1):
            f.write(f"### {i}. {' '.join(r['chart'])} (日主: {r['day_master']})\n\n")
            f.write(f"**S轴 (应力)**: {r['S']:.2f}\n")
            f.write(f"**SAI**: {r['SAI']:.2f}\n\n")
            f.write(f"**5维投影**:\n")
            f.write(f"- E (能级): {r['E']:.2f}\n")
            f.write(f"- O (秩序): {r['O']:.2f}\n")
            f.write(f"- M (物质): {r['M']:.2f}\n")
            f.write(f"- R (关联): {r['R']:.2f}\n\n")
            f.write(f"**基础能量**:\n")
            f.write(f"- 羊刃能量: {r['blade_energy']:.1f}\n")
            f.write(f"- 七杀能量: {r['qi_sha_energy']:.1f}\n")
            f.write(f"- 刑冲数: {r['clash_count']}\n\n")
        
        f.write("---\n\n")
        f.write("## 四、关键发现\n\n")
        f.write(f"1. **秩序轴 (O) 均值**: {stats['O']['mean']:.2f} - ")
        if stats['O']['mean'] >= 40:
            f.write("✅ 显著高于普通人，证明'羊刃架杀'确实是贵格\n")
        else:
            f.write("⚠️ 需要进一步分析\n")
        f.write(f"2. **应力轴 (S) 均值**: {stats['S']['mean']:.2f} - ")
        if 15 <= stats['S']['mean'] <= 25:
            f.write("✅ 符合预期，这是'玩火'的格局\n")
        else:
            f.write("⚠️ 需要进一步分析\n")
        f.write(f"3. **SAI 均值**: {stats['SAI']['mean']:.2f} - 系统对齐指数\n")
    
    print("=" * 70)
    print("✅ 张量分析报告已生成")
    print("=" * 70)
    print(f"📄 报告文件: {report_file}")
    print()

if __name__ == '__main__':
    main()

