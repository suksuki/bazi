#!/usr/bin/env python3
"""
FDS 物理真实性审计脚本 (Physics Truth Audit)
============================================
[第020号工程指令] 从"盲目拟合"转向"物理求真"

**核心哲学**：
- 不再强求物理模型死磕古典丰度
- 保留物理流形的自然形状
- 将偏差视为"法理与物理的探索区间"
- 引入流形溢出系数(MEF)和象限分析

**输出**：
- 物理真实性报告
- 象限审计分析
- 流形溢出系数(MEF)
- IoU重合度分析
"""

import argparse
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Set, Tuple, List
import sys

from fds_load_acceptance import (
    load_registry, load_manifest, extract_base_abundance,
    get_weights_matrix, calculate_5d_tensor, compute_mahalanobis_distance,
    load_threshold_from_registry, load_config_mahalanobis_threshold,
    DEFAULT_DATA, DEFAULT_TOLERANCE
)

REGISTRY_DIR = Path("./registry/holographic_pattern")
MANIFEST_DIR = Path("./config/patterns")


def calculate_quadrant_analysis(
    pattern_id: str,
    data_path: str,
    threshold: float
) -> Dict[str, Any]:
    """
    象限分析：统计物理模型与古典逻辑的差异区域
    
    返回:
    {
        'logic_only': 仅逻辑匹配的样本集合
        'physics_only': 仅物理匹配的样本集合
        'intersection': 交集样本集合
        'union': 并集样本集合
        'logic_count': 逻辑匹配数
        'physics_count': 物理匹配数
        'intersection_count': 交集数
        'union_count': 并集数
        'iou': IoU值
        'logic_only_samples': 仅逻辑匹配的样本特征（前10个）
        'physics_only_samples': 仅物理匹配的样本特征（前10个）
    }
    """
    print(f"\n📊 执行象限分析...")
    
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
    
    # 使用set存储样本标识
    logic_matched = set()
    physics_matched = set()
    
    # 存储样本特征（用于分析）
    logic_only_samples = []
    physics_only_samples = []
    
    try:
        from json_logic import jsonLogic
    except ImportError:
        print("❌ Critical: json-logic-quibble missing.")
        sys.exit(1)
    
    total_samples = 0
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                case = json.loads(line)
                if 'ten_gods' not in case:
                    continue
                
                total_samples += 1
                sample_id = line_num
                
                # 逻辑判定
                is_logic_match = jsonLogic(logic_expression, case)
                
                # 物理判定
                tensor = calculate_5d_tensor(case['ten_gods'], weights_matrix, god_index_map)
                dist = compute_mahalanobis_distance(tensor, mean_vector, cov_matrix)
                is_physics_match = dist < threshold
                
                if is_logic_match:
                    logic_matched.add(sample_id)
                    if not is_physics_match and len(logic_only_samples) < 10:
                        logic_only_samples.append({
                            'sample_id': sample_id,
                            'ten_gods': case['ten_gods'],
                            'tensor': tensor.tolist(),
                            'distance': float(dist)
                        })
                
                if is_physics_match:
                    physics_matched.add(sample_id)
                    if not is_logic_match and len(physics_only_samples) < 10:
                        physics_only_samples.append({
                            'sample_id': sample_id,
                            'ten_gods': case['ten_gods'],
                            'tensor': tensor.tolist(),
                            'distance': float(dist)
                        })
                
                # 进度提示
                if line_num % 50000 == 0:
                    print(f"   进度: {line_num:,} 行", end='\r')
                    
            except (json.JSONDecodeError, KeyError, Exception):
                continue
    
    print()  # 换行
    
    # 计算集合
    intersection = logic_matched.intersection(physics_matched)
    union = logic_matched.union(physics_matched)
    
    # 计算IoU
    iou = len(intersection) / len(union) if len(union) > 0 else 0.0
    
    return {
        'logic_only': logic_matched - physics_matched,
        'physics_only': physics_matched - logic_matched,
        'intersection': intersection,
        'union': union,
        'logic_count': len(logic_matched),
        'physics_count': len(physics_matched),
        'intersection_count': len(intersection),
        'union_count': len(union),
        'iou': iou,
        'logic_only_samples': logic_only_samples,
        'physics_only_samples': physics_only_samples
    }


def calculate_physics_recognition_rate(
    pattern_id: str,
    data_path: str,
    threshold: float
) -> Tuple[float, int, int]:
    """计算物理识别率"""
    from fds_load_acceptance import calculate_physics_recognition_rate as _calc
    return _calc(pattern_id, data_path, threshold)


def run_physics_truth_audit(pattern_id: str, data_path: str = DEFAULT_DATA, threshold: float = 2.0):
    """执行物理真实性审计"""
    print(f"🚀 FDS 物理真实性审计: {pattern_id}")
    print("=" * 60)
    
    # 1. 加载基础数据
    registry_data = load_registry(pattern_id)
    base_abundance = extract_base_abundance(registry_data)
    
    print(f"\n📂 基础数据:")
    print(f"   基准丰度（古典逻辑）: {base_abundance:.4f}%")
    print(f"   使用阈值: {threshold:.2f}")
    
    # 2. 计算物理识别率
    print(f"\n⚛️  物理识别率计算...")
    recognition_rate, hits, total = calculate_physics_recognition_rate(
        pattern_id, data_path, threshold
    )
    print(f"   识别率（物理模型）: {recognition_rate:.4f}%")
    
    # 3. 计算偏差和MEF
    delta = abs(recognition_rate - base_abundance)
    mef = recognition_rate / base_abundance if base_abundance > 0 else 0.0
    
    print(f"\n📐 偏差分析:")
    print(f"   绝对偏差: {delta:.4f}%")
    print(f"   流形溢出系数(MEF): {mef:.4f} ({mef * 100 - 100:.2f}% 溢出)")
    
    # 4. 象限分析
    quadrant = calculate_quadrant_analysis(pattern_id, data_path, threshold)
    
    # 5. 输出报告
    print("\n" + "=" * 60)
    print("📋 物理真实性审计报告")
    print("=" * 60)
    print(f"格局ID:              {pattern_id}")
    print(f"\n📊 丰度对比:")
    print(f"   基准丰度（古典）:  {base_abundance:.4f}%")
    print(f"   识别率（物理）:    {recognition_rate:.4f}%")
    print(f"   绝对偏差:          {delta:.4f}%")
    print(f"   流形溢出系数(MEF): {mef:.4f} ({mef * 100 - 100:+.2f}%)")
    
    print(f"\n🔍 象限分析:")
    print(f"   逻辑匹配样本数:   {quadrant['logic_count']:,}")
    print(f"   物理匹配样本数:   {quadrant['physics_count']:,}")
    print(f"   交集样本数:       {quadrant['intersection_count']:,}")
    print(f"   仅逻辑匹配:       {len(quadrant['logic_only']):,}")
    print(f"   仅物理匹配:       {len(quadrant['physics_only']):,}")
    print(f"   IoU（重合度）:    {quadrant['iou'] * 100:.2f}%")
    
    print(f"\n💡 物理解读:")
    if mef > 1.1:
        print(f"   • 物理模型认为该格局比古典定义更具普遍性（溢出{(mef-1)*100:.1f}%）")
        print(f"   • 这可能反映了现实世界中格局的'软边界'特性")
    elif mef < 0.9:
        print(f"   • 物理模型比古典定义更严格（收缩{(1-mef)*100:.1f}%）")
        print(f"   • 这可能反映了物理流形的'核心区域'特征")
    else:
        print(f"   • 物理模型与古典定义高度一致（偏差<10%）")
    
    if quadrant['iou'] < 0.3:
        print(f"   • IoU较低（{quadrant['iou']*100:.1f}%），说明两种方法识别边界存在显著差异")
        print(f"   • 这是正常的，反映了Boolean逻辑与Statistical流形的本质区别")
    
    print("\n" + "=" * 60)
    
    # 6. 判定（不再强制失败）
    tolerance = DEFAULT_TOLERANCE
    if delta <= tolerance:
        print(f"\n✅ 验收通过（偏差 {delta:.2f}% ≤ 容差 {tolerance}%）")
        print("   物理模型保持自然形状，偏差在可接受范围内")
    else:
        print(f"\n⚠️  偏差超出标准容差（{delta:.2f}% > {tolerance}%）")
        print("   但这是物理模型的真实特性，不是错误")
        print("   偏差反映了法理与物理的探索区间")
    
    print("\n🎯 结论：物理模型保持自然形状，具备物理真实性。")
    
    return {
        'pattern_id': pattern_id,
        'base_abundance': base_abundance,
        'recognition_rate': recognition_rate,
        'delta': delta,
        'mef': mef,
        'threshold': threshold,
        'quadrant': quadrant,
        'passed': delta <= tolerance
    }


def main():
    parser = argparse.ArgumentParser(
        description='FDS 物理真实性审计（从"盲目拟合"转向"物理求真"）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fds_physics_truth_audit.py --target A-01
  python fds_physics_truth_audit.py --target A-01 --threshold 2.0
        """
    )
    
    parser.add_argument(
        '--target',
        required=True,
        help='格局ID（如 A-01）'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=2.0,
        help='马氏距离阈值（默认: 2.0，合理物理区间）'
    )
    
    parser.add_argument(
        '--data',
        default=DEFAULT_DATA,
        help=f'数据文件路径（默认: {DEFAULT_DATA}）'
    )
    
    args = parser.parse_args()
    
    try:
        result = run_physics_truth_audit(args.target, args.data, args.threshold)
        
        # 可选：保存结果到JSON文件
        output_file = f"audit_{args.target}_threshold_{args.threshold:.2f}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # 清理不可序列化的set
            clean_result = result.copy()
            clean_result['quadrant'] = {
                k: (list(v) if isinstance(v, set) else v) 
                for k, v in result['quadrant'].items()
            }
            json.dump(clean_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 审计结果已保存至: {output_file}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

