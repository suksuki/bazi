#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 F6 案例：检查合而不化的检测逻辑
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.prob_math import ProbValue

def deep_merge(base, update):
    """递归合并配置"""
    for key, value in update.items():
        if key.startswith('_'):
            continue
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value

def main():
    # F6 案例
    f6_case = {
        'id': 'F6_Fail_Combine',
        'bazi': ['甲寅', '己酉', '甲子', '甲子'],
        'day_master': '甲',
        'gender': '男',
        'monitor_target': 'Earth',
        'expected_energy_ratio': 0.8,
        'desc': '甲己合而不化 - 月令不支持，形成羁绊，双方能量均受损'
    }
    
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
    verifier.engine.initialize_nodes(f6_case['bazi'], f6_case['day_master'])
    verifier.engine._apply_quantum_entanglement_once()
    verifier.engine.build_adjacency_matrix()
    
    # 检查调试信息
    debug_info = getattr(verifier.engine, '_quantum_entanglement_debug', {})
    print("调试信息:")
    print(f"  detected_matches: {debug_info.get('detected_matches', [])}")
    print(f"  node_changes: {debug_info.get('node_changes', [])}")
    print()
    
    # 检查节点
    print("节点信息:")
    for i, node in enumerate(verifier.engine.nodes):
        if node.char in ['甲', '己']:
            print(f"  Node {i}: {node.char} ({node.element}), pillar={node.pillar_idx}, type={node.node_type}")
    
    # 执行传播
    H_final = verifier.engine.propagate(max_iterations=1, damping=1.0)
    
    # 检查最终能量
    print("\n最终能量:")
    H0 = verifier.engine.H0
    for i, node in enumerate(verifier.engine.nodes):
        if node.char in ['甲', '己']:
            h0 = H0[i]
            h0_val = h0.mean if isinstance(h0, ProbValue) else float(h0)
            h_final = H_final[i]
            h_final_val = h_final.mean if isinstance(h_final, ProbValue) else float(h_final)
            ratio = h_final_val / h0_val if h0_val > 0 else 0.0
            print(f"  Node {i} ({node.char}): {h0_val:.4f} → {h_final_val:.4f} (比率: {ratio:.4f})")
    
    # 检查土元素总能量
    earth_total_h0 = ProbValue(0.0, std_dev_percent=0.1)
    earth_total_final = ProbValue(0.0, std_dev_percent=0.1)
    for i, node in enumerate(verifier.engine.nodes):
        if node.element == 'earth':
            h0 = H0[i]
            h0_val = h0 if isinstance(h0, ProbValue) else ProbValue(float(h0), std_dev_percent=0.1)
            earth_total_h0 = earth_total_h0 + h0_val
            
            h_final = H_final[i]
            h_final_val = h_final if isinstance(h_final, ProbValue) else ProbValue(float(h_final), std_dev_percent=0.1)
            earth_total_final = earth_total_final + h_final_val
    
    ratio = earth_total_final.mean / earth_total_h0.mean if earth_total_h0.mean > 0 else 0.0
    print(f"\n土元素总能量:")
    print(f"  H0: {earth_total_h0.mean:.4f}")
    print(f"  H_final: {earth_total_final.mean:.4f}")
    print(f"  比率: {ratio:.4f} (预期: 0.8)")

if __name__ == '__main__':
    main()

