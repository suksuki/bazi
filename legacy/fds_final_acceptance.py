#!/usr/bin/env python3
"""
FDS 最终验收脚本 (Final Acceptance with IoU)
============================================
[第019号工程指令] 最终对撞验收与IoU计算

**目标**：
- 使用最优阈值执行最终验收测试
- 计算逻辑匹配集合与物理判定集合的交集率（IoU）
- 生成结案报告
"""

import argparse
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Set, Tuple
import sys

from fds_load_acceptance import (
    load_registry, load_manifest, extract_base_abundance,
    get_weights_matrix, calculate_5d_tensor, compute_mahalanobis_distance,
    load_threshold_from_registry, load_config_mahalanobis_threshold,
    DEFAULT_DATA
)

REGISTRY_DIR = Path("./registry/holographic_pattern")
MANIFEST_DIR = Path("./config/patterns")


def calculate_iou(
    pattern_id: str,
    data_path: str,
    threshold: float
) -> Tuple[float, int, int, int]:
    """
    计算逻辑匹配集合与物理判定集合的交集率（IoU）
    
    返回: (IoU, 逻辑匹配数, 物理匹配数, 交集数)
    """
    print(f"\n📊 计算IoU（逻辑匹配 vs 物理判定）...")
    
    # 加载数据
    registry_data = load_registry(pattern_id)
    manifest = load_manifest(pattern_id)
    
    # 提取流形特征
    fa = registry_data['data']['feature_anchors']['standard_manifold']
    mean_vector = np.array(fa['mean_vector'])
    cov_matrix = np.array(fa['covariance_matrix'])
    
    # 构建权重矩阵
    weights_matrix, gods_list = get_weights_matrix(manifest)
    god_index_map = {g: i for i, g in enumerate(gods_list)}
    
    # 提取逻辑规则
    logic_expression = manifest['classical_logic_rules']['expression']
    
    # 使用set来存储匹配的样本索引（使用行号作为标识）
    logic_matched = set()
    physics_matched = set()
    intersection = set()
    
    total_samples = 0
    
    try:
        from json_logic import jsonLogic
    except ImportError:
        print("❌ Critical: json-logic-quibble missing.")
        sys.exit(1)
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                case = json.loads(line)
                if 'ten_gods' not in case:
                    continue
                
                total_samples += 1
                sample_id = line_num  # 使用行号作为样本ID
                
                # 逻辑判定
                is_logic_match = jsonLogic(logic_expression, case)
                if is_logic_match:
                    logic_matched.add(sample_id)
                
                # 物理判定
                tensor = calculate_5d_tensor(case['ten_gods'], weights_matrix, god_index_map)
                dist = compute_mahalanobis_distance(tensor, mean_vector, cov_matrix)
                is_physics_match = dist < threshold
                if is_physics_match:
                    physics_matched.add(sample_id)
                
                # 交集
                if is_logic_match and is_physics_match:
                    intersection.add(sample_id)
                
                # 进度提示
                if line_num % 50000 == 0:
                    print(f"   进度: {line_num:,} 行，逻辑匹配: {len(logic_matched):,}，物理匹配: {len(physics_matched):,}，交集: {len(intersection):,}", end='\r')
                    
            except (json.JSONDecodeError, KeyError, Exception):
                continue
    
    print()  # 换行
    
    # 计算IoU
    union_size = len(logic_matched.union(physics_matched))
    intersection_size = len(intersection)
    iou = intersection_size / union_size if union_size > 0 else 0.0
    
    return iou, len(logic_matched), len(physics_matched), intersection_size


def run_final_acceptance(pattern_id: str, data_path: str = DEFAULT_DATA):
    """执行最终验收测试"""
    print(f"🚀 FDS 最终验收测试（结案验收）: {pattern_id}")
    print("=" * 60)
    
    # 1. 加载数据
    registry_data = load_registry(pattern_id)
    base_abundance = extract_base_abundance(registry_data)
    
    # 2. 读取最优阈值
    threshold = load_config_mahalanobis_threshold(registry_data)
    threshold_source = "registry最优阈值" if load_threshold_from_registry(registry_data) is not None else "配置默认值"
    
    print(f"\n📂 基础数据:")
    print(f"   基准丰度: {base_abundance:.4f}%")
    print(f"   最优阈值: {threshold:.4f} ({threshold_source})")
    
    # 3. 使用最优阈值计算识别率（复用现有函数）
    from fds_load_acceptance import calculate_physics_recognition_rate
    recognition_rate, hits, total = calculate_physics_recognition_rate(
        pattern_id, data_path, threshold
    )
    
    # 4. 计算偏差
    delta = abs(recognition_rate - base_abundance)
    
    # 5. 计算IoU
    iou, logic_count, physics_count, intersection_count = calculate_iou(
        pattern_id, data_path, threshold
    )
    
    # 6. 判定
    from fds_load_acceptance import load_config_tolerance
    tolerance = load_config_tolerance()
    passed = delta <= tolerance
    
    # 输出最终报告
    print("\n" + "=" * 60)
    print("📋 最终验收报告（结案审计）")
    print("=" * 60)
    print(f"格局ID:              {pattern_id}")
    print(f"基准丰度（逻辑）:    {base_abundance:.4f}%")
    print(f"识别率（物理）:      {recognition_rate:.4f}%")
    print(f"绝对偏差:            {delta:.4f}%")
    print(f"系统容差:            {tolerance:.2f}%")
    print(f"判定结果:            {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"\n📊 集合分析（IoU计算）:")
    print(f"   逻辑匹配样本数:   {logic_count:,}")
    print(f"   物理匹配样本数:   {physics_count:,}")
    print(f"   交集样本数:       {intersection_count:,}")
    print(f"   并集样本数:       {logic_count + physics_count - intersection_count:,}")
    print(f"   IoU（交集率）:    {iou * 100:.2f}%")
    print("=" * 60)
    
    if passed:
        print("\n🎉 A-01格局已通过最终验收，具备结案资格！")
    else:
        print("\n⚠️  A-01格局未通过验收，需要进一步调整。")
    
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(
        description='FDS 最终验收测试（结案验收与IoU计算）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fds_final_acceptance.py --target A-01
        """
    )
    
    parser.add_argument(
        '--target',
        required=True,
        help='格局ID（如 A-01）'
    )
    
    parser.add_argument(
        '--data',
        default=DEFAULT_DATA,
        help=f'数据文件路径（默认: {DEFAULT_DATA}）'
    )
    
    args = parser.parse_args()
    
    try:
        exit_code = run_final_acceptance(args.target, args.data)
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

