#!/usr/bin/env python3
"""
Outlier Autopsy Script (V38.0)
===============================

对极端Balanced案例进行深度分析，追踪能量来源。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import copy
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

# 五行生克关系
GENERATION = {
    'wood': 'fire',
    'fire': 'earth',
    'earth': 'metal',
    'metal': 'water',
    'water': 'wood'
}


def load_golden_cases(data_path: Path = None) -> List[Dict[str, Any]]:
    """加载测试案例"""
    if data_path is None:
        data_path = project_root / "data" / "golden_cases.json"
    
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            return cases
    return []


def find_extreme_balanced_cases(cases: List[Dict[str, Any]], config: Dict) -> Tuple[Dict, Dict]:
    """
    找到Balanced案例中分数最高和最低的两个案例
    
    Returns:
        (highest_case_result, lowest_case_result)
    """
    engine = GraphNetworkEngine(config=config)
    
    balanced_results = []
    
    for case in cases:
        if case.get('true_label') != 'Balanced':
            continue
        
        try:
            result = engine.analyze(
                bazi=case['bazi'],
                day_master=case['day_master'],
                luck_pillar=None,
                year_pillar=None,
                geo_modifiers=None
            )
            
            strength_score = result.get('strength_score', 0.0)
            balanced_results.append({
                'case': case,
                'result': result,
                'score': strength_score
            })
        except Exception as e:
            print(f"⚠️  案例 {case.get('id')} 出错: {e}")
            continue
    
    if not balanced_results:
        return None, None
    
    # 找到最高和最低
    highest = max(balanced_results, key=lambda x: x['score'])
    lowest = min(balanced_results, key=lambda x: x['score'])
    
    return highest, lowest


def get_node_by_element(nodes: List[Any], element: str) -> List[Any]:
    """根据元素找到节点"""
    return [node for node in nodes if node.element == element]


def get_node_by_id(nodes: List[Any], node_id: str) -> Any:
    """根据ID找到节点"""
    for node in nodes:
        if node.node_id == node_id:
            return node
    return None


def analyze_energy_flow(case: Dict[str, Any], result: Dict[str, Any], 
                        engine: GraphNetworkEngine, config: Dict):
    """
    深度分析能量流向
    """
    print("=" * 80)
    print("🔬 深度能量追踪分析")
    print("=" * 80)
    print()
    
    case_id = case.get('id', 'Unknown')
    bazi = case['bazi']
    day_master = case['day_master']
    description = case.get('description', '')
    
    print(f"📋 案例信息:")
    print(f"   ID: {case_id}")
    print(f"   Bazi: {bazi}")
    print(f"   日主: {day_master}")
    print(f"   描述: {description}")
    print(f"   最终分数: {result.get('strength_score', 0.0):.1f}%")
    print()
    
    # 获取节点和邻接矩阵
    nodes = engine.nodes
    adjacency_matrix = engine.adjacency_matrix
    
    # 确定日主元素
    dm_element_map = {
        '甲': 'wood', '乙': 'wood', '丙': 'fire', '丁': 'fire', '戊': 'earth',
        '己': 'earth', '庚': 'metal', '辛': 'metal', '壬': 'water', '癸': 'water'
    }
    dm_element = dm_element_map.get(day_master, 'metal')
    
    # 确定印（Resource）元素
    resource_element = None
    for elem, target in GENERATION.items():
        if target == dm_element:
            resource_element = elem
            break
    
    print(f"🔍 元素映射:")
    
    # [V39.1] 检查化气情况
    day_master_element_before = engine.STEM_ELEMENTS.get(day_master, 'metal')
    day_master_element_after = None
    
    # 重新运行一次，检查化气是否发生
    test_engine = GraphNetworkEngine(config=engine.config)
    test_result = test_engine.analyze(
        bazi=bazi,
        day_master=day_master,
        luck_pillar=None,
        year_pillar=None,
        geo_modifiers=None
    )
    
    # 检查日主节点实际元素（可能被化气修改）
    dm_node_actual = None
    for node in test_engine.nodes:
        if node.char == day_master and node.node_type == 'stem' and node.pillar_idx == 2:
            dm_node_actual = node
            break
    
    if dm_node_actual:
        day_master_element_after = dm_node_actual.element
        if day_master_element_after != day_master_element_before:
            print(f"   ⚡ 化气检测:")
            print(f"      日主元素 (化气前): {day_master_element_before}")
            print(f"      化气触发: ✅ ({day_master} 与 另一个天干 合化)")
            print(f"      日主元素 (化气后): {day_master_element_after}")
        else:
            print(f"      日主元素 (无化气): {day_master_element_before}")
    
    print(f"   当前日主元素: {dm_element}")
    print(f"   印元素: {resource_element}")
    print()
    
    # Phase 1: 初始能量分析
    print("=" * 80)
    print("📊 Phase 1: 初始能量分析")
    print("=" * 80)
    
    dm_nodes_init = []
    resource_nodes_init = []
    total_init_dm = 0.0
    total_init_resource = 0.0
    
    for node in nodes:
        if node.element == dm_element:
            dm_nodes_init.append({
                'id': node.node_id,
                'char': node.char,
                'type': node.node_type,
                'energy': node.initial_energy
            })
            total_init_dm += node.initial_energy
        elif resource_element and node.element == resource_element:
            resource_nodes_init.append({
                'id': node.node_id,
                'char': node.char,
                'type': node.node_type,
                'energy': node.initial_energy
            })
            total_init_resource += node.initial_energy
    
    print(f"\n日主 ({dm_element}) 初始能量:")
    for node_info in dm_nodes_init:
        print(f"   {node_info['char']:2s} ({node_info['type']:5s}): {node_info['energy']:6.3f}")
    print(f"   合计: {total_init_dm:.3f}")
    
    if resource_element:
        print(f"\n印 ({resource_element}) 初始能量:")
        for node_info in resource_nodes_init:
            print(f"   {node_info['char']:2s} ({node_info['type']:5s}): {node_info['energy']:6.3f}")
        print(f"   合计: {total_init_resource:.3f}")
    
    # 计算初始阵营能量占比
    total_init_all = sum(node.initial_energy for node in nodes)
    init_self_team = total_init_dm + total_init_resource
    init_ratio = (init_self_team / total_init_all * 100) if total_init_all > 0 else 0.0
    print(f"\n初始阵营占比: {init_self_team:.3f} / {total_init_all:.3f} = {init_ratio:.1f}%")
    print()
    
    # Phase 3: 最终能量分析
    print("=" * 80)
    print("📊 Phase 3: 最终能量分析")
    print("=" * 80)
    
    total_final_dm = 0.0
    total_final_resource = 0.0
    dm_nodes_final = []
    resource_nodes_final = []
    
    final_energies = result.get('final_energy', [])
    
    for i, node in enumerate(nodes):
        final_energy = final_energies[i] if i < len(final_energies) else node.current_energy
        
        if node.element == dm_element:
            dm_nodes_final.append({
                'id': node.node_id,
                'char': node.char,
                'type': node.node_type,
                'energy': final_energy,
                'delta': final_energy - node.initial_energy
            })
            total_final_dm += final_energy
        elif resource_element and node.element == resource_element:
            resource_nodes_final.append({
                'id': node.node_id,
                'char': node.char,
                'type': node.node_type,
                'energy': final_energy,
                'delta': final_energy - node.initial_energy
            })
            total_final_resource += final_energy
    
    print(f"\n日主 ({dm_element}) 最终能量:")
    for node_info in dm_nodes_final:
        delta_str = f"({node_info['delta']:+.3f})" if 'delta' in node_info else ""
        print(f"   {node_info['char']:2s} ({node_info['type']:5s}): {node_info['energy']:6.3f} {delta_str}")
    print(f"   合计: {total_final_dm:.3f} (变化: {total_final_dm - total_init_dm:+.3f})")
    
    if resource_element:
        print(f"\n印 ({resource_element}) 最终能量:")
        for node_info in resource_nodes_final:
            delta_str = f"({node_info['delta']:+.3f})" if 'delta' in node_info else ""
            print(f"   {node_info['char']:2s} ({node_info['type']:5s}): {node_info['energy']:6.3f} {delta_str}")
        print(f"   合计: {total_final_resource:.3f} (变化: {total_final_resource - total_init_resource:+.3f})")
    
    # 计算最终阵营能量占比
    total_final_all = sum(final_energies) if final_energies else sum(node.current_energy for node in nodes)
    final_self_team = total_final_dm + total_final_resource
    final_ratio = (final_self_team / total_final_all * 100) if total_final_all > 0 else 0.0
    print(f"\n最终阵营占比: {final_self_team:.3f} / {total_final_all:.3f} = {final_ratio:.1f}%")
    print(f"占比变化: {final_ratio - init_ratio:+.1f}%")
    print()
    
    # 关键流向分析：Top 3 入边（指向日主）
    print("=" * 80)
    print("🔍 关键流向分析: Top 3 指向日主的入边")
    print("=" * 80)
    
    # 找到所有日主节点的索引
    dm_node_indices = [i for i, node in enumerate(nodes) if node.element == dm_element]
    
    incoming_edges = []
    for dm_idx in dm_node_indices:
        dm_node = nodes[dm_idx]
        for src_idx in range(len(nodes)):
            if src_idx == dm_idx:
                continue
            weight = adjacency_matrix[src_idx][dm_idx]
            if abs(weight) > 0.001:  # 只考虑有意义的权重
                src_node = nodes[src_idx]
                incoming_edges.append({
                    'source': src_node.char,
                    'source_type': src_node.node_type,
                    'source_element': src_node.element,
                    'target': dm_node.char,
                    'target_type': dm_node.node_type,
                    'weight': weight,
                    'source_idx': src_idx,
                    'target_idx': dm_idx
                })
    
    # 按权重绝对值排序
    incoming_edges.sort(key=lambda x: abs(x['weight']), reverse=True)
    
    print(f"\n找到 {len(incoming_edges)} 条指向日主的边")
    print("\nTop 10 最大权重入边:")
    for i, edge in enumerate(incoming_edges[:10], 1):
        weight_str = f"{edge['weight']:+.4f}"
        edge_type = "生" if edge['weight'] > 0 else "克"
        print(f"   {i:2d}. {edge['source']:2s} ({edge['source_element']:5s}) "
              f"--[{weight_str:>8s}]--> {edge['target']:2s} ({edge_type})")
    print()
    
    # 关键流向分析：Top 3 出边（日主流出）
    print("=" * 80)
    print("🔍 关键流向分析: Top 3 日主流出的出边")
    print("=" * 80)
    
    outgoing_edges = []
    for dm_idx in dm_node_indices:
        dm_node = nodes[dm_idx]
        for tgt_idx in range(len(nodes)):
            if tgt_idx == dm_idx:
                continue
            weight = adjacency_matrix[dm_idx][tgt_idx]
            if abs(weight) > 0.001:  # 只考虑有意义的权重
                tgt_node = nodes[tgt_idx]
                outgoing_edges.append({
                    'source': dm_node.char,
                    'source_type': dm_node.node_type,
                    'target': tgt_node.char,
                    'target_type': tgt_node.node_type,
                    'target_element': tgt_node.element,
                    'weight': weight,
                    'source_idx': dm_idx,
                    'target_idx': tgt_idx
                })
    
    # 按权重绝对值排序
    outgoing_edges.sort(key=lambda x: abs(x['weight']), reverse=True)
    
    print(f"\n找到 {len(outgoing_edges)} 条日主流出的边")
    print("\nTop 10 最大权重出边:")
    for i, edge in enumerate(outgoing_edges[:10], 1):
        weight_str = f"{edge['weight']:+.4f}"
        edge_type = "生" if edge['weight'] > 0 else "克"
        print(f"   {i:2d}. {edge['source']:2s} --[{weight_str:>8s}]--> "
              f"{edge['target']:2s} ({edge['target_element']:5s}) ({edge_type})")
    print()
    
    # 诊断结论
    print("=" * 80)
    print("🏥 诊断结论")
    print("=" * 80)
    
    energy_growth = final_ratio - init_ratio
    
    if init_ratio > 60.0:
        print("⚠️  初始能量占比就很高 (>60%)，可能是Phase 1计算问题")
    elif energy_growth > 20.0:
        print("⚠️  能量在传导中暴涨 (+20%+)，可能存在正反馈闭环")
        print(f"   建议: 检查是否存在能量循环路径（如 印->身->印 或 比劫->身->比劫）")
    elif energy_growth < -20.0:
        print("⚠️  能量在传导中大幅流失 (-20%+)，可能存在过度泄耗")
        print(f"   建议: 检查是否被多路克制或泄耗")
    else:
        print("✓ 能量变化相对正常")
    
    print()
    print("=" * 80)


def main():
    """主函数"""
    print("=" * 80)
    print("🔬 Outlier Autopsy (V38.0) - 极端Balanced案例深度分析")
    print("=" * 80)
    print()
    
    # 1. 加载配置和案例
    print("📋 加载测试案例和配置...")
    cases = load_golden_cases()
    
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(config, user_config)
    
    balanced_cases = [c for c in cases if c.get('true_label') == 'Balanced']
    print(f"   找到 {len(balanced_cases)} 个Balanced案例")
    print()
    
    # 2. 找到极端案例
    print("🔍 分析所有Balanced案例，寻找极端值...")
    highest, lowest = find_extreme_balanced_cases(balanced_cases, config)
    
    if not highest or not lowest:
        print("❌ 未找到Balanced案例")
        return
    
    print(f"✅ 找到最高分案例: {highest['case'].get('id')} ({highest['score']:.1f}%)")
    print(f"✅ 找到最低分案例: {lowest['case'].get('id')} ({lowest['score']:.1f}%)")
    print()
    
    # 3. 深度分析最高分案例
    print("\n" + "=" * 80)
    print("🔬 案例1: 最高分Balanced案例（疑似假身旺）")
    print("=" * 80)
    print()
    
    # 重新初始化引擎以获取完整内部状态
    engine1 = GraphNetworkEngine(config=config)
    result1 = engine1.analyze(
        bazi=highest['case']['bazi'],
        day_master=highest['case']['day_master'],
        luck_pillar=None,
        year_pillar=None,
        geo_modifiers=None
    )
    analyze_energy_flow(highest['case'], result1, engine1, config)
    
    # 4. 深度分析最低分案例
    print("\n" + "=" * 80)
    print("🔬 案例2: 最低分Balanced案例（疑似假身弱）")
    print("=" * 80)
    print()
    
    engine2 = GraphNetworkEngine(config=config)
    result2 = engine2.analyze(
        bazi=lowest['case']['bazi'],
        day_master=lowest['case']['day_master'],
        luck_pillar=None,
        year_pillar=None,
        geo_modifiers=None
    )
    analyze_energy_flow(lowest['case'], result2, engine2, config)
    
    print("\n" + "=" * 80)
    print("✅ 尸检完成")
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

