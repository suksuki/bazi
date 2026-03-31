#!/usr/bin/env python3
"""
FDS 阈值校准脚本 (Threshold Calibration)
========================================
[第019号工程指令] 逆向阈值锚定

**目标**：
- 计算所有逻辑匹配样本的马氏距离分布
- 使用二分法搜索最优阈值，使物理识别率接近基准丰度
- 将最优阈值写入registry

**流程**：
1. 计算所有匹配样本的马氏距离分布
2. 二分法搜索最优阈值（目标：物理识别率 ≈ 基准丰度21.79%）
3. 更新registry文件
"""

import argparse
import json
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from scipy import stats

# 强制依赖
try:
    from json_logic import jsonLogic
except ImportError:
    print("❌ Critical: json-logic-quibble missing. Run: pip install json-logic-quibble")
    sys.exit(1)

REGISTRY_DIR = Path("./registry/holographic_pattern")
MANIFEST_DIR = Path("./config/patterns")
DEFAULT_DATA = "./data/holographic_universe_518k.jsonl"


def load_registry(pattern_id: str) -> Dict[str, Any]:
    """从registry目录加载格局数据"""
    registry_path = REGISTRY_DIR / f"{pattern_id}.json"
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry文件不存在: {registry_path}")
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_manifest(pattern_id: str) -> Dict[str, Any]:
    """从manifest目录加载格局配置"""
    possible_names = [
        f"manifest_{pattern_id}.json",
        f"manifest_{pattern_id.replace('-', '')}.json",
        f"{pattern_id}.json"
    ]
    
    for name in possible_names:
        path = MANIFEST_DIR / name
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    raise FileNotFoundError(f"Manifest文件不存在，尝试了: {possible_names}")


def get_weights_matrix(manifest: Dict[str, Any]) -> Tuple[np.ndarray, list]:
    """从manifest构建权重矩阵（10x5）"""
    tmm = manifest['tensor_mapping_matrix']
    gods = tmm['ten_gods']
    matrix = []
    for god in gods:
        matrix.append(tmm['weights'][god])
    return np.array(matrix), gods


def calculate_5d_tensor(case_ten_gods: Dict[str, int], weights_matrix: np.ndarray, god_index_map: Dict[str, int]) -> np.ndarray:
    """计算样本的5D张量"""
    vec = np.zeros(10)
    for god, val in case_ten_gods.items():
        if god in god_index_map:
            vec[god_index_map[god]] = float(val)
    tensor = np.dot(weights_matrix.T, vec)
    return tensor


def compute_mahalanobis_distance(tensor: np.ndarray, mean: np.ndarray, cov_matrix: np.ndarray) -> float:
    """计算马氏距离"""
    diff = tensor - mean
    try:
        inv_cov = np.linalg.pinv(cov_matrix)
        mahal_dist = np.sqrt(np.dot(np.dot(diff, inv_cov), diff))
        return mahal_dist
    except np.linalg.LinAlgError:
        # 降级为欧氏距离
        return np.sqrt(np.dot(diff, diff))


def compute_mahalanobis_distances_for_matched_samples(
    pattern_id: str,
    data_path: str
) -> Tuple[List[float], int]:
    """
    计算所有逻辑匹配样本的马氏距离
    
    返回: (距离列表, 匹配样本数)
    """
    print(f"🚀 开始计算 {pattern_id} 匹配样本的马氏距离分布...")
    
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
    
    # 计算所有匹配样本的马氏距离
    distances = []
    total_samples = 0
    matched_samples = 0
    
    print(f"📊 扫描样本数据: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                case = json.loads(line)
                total_samples += 1
                
                # 逻辑过滤
                if jsonLogic(logic_expression, case):
                    matched_samples += 1
                    
                    # 计算5D张量
                    tensor = calculate_5d_tensor(case['ten_gods'], weights_matrix, god_index_map)
                    
                    # 计算马氏距离
                    dist = compute_mahalanobis_distance(tensor, mean_vector, cov_matrix)
                    distances.append(dist)
                
                # 进度提示
                if line_num % 50000 == 0:
                    print(f"   进度: {line_num:,} 行，匹配: {matched_samples:,}", end='\r')
                    
            except (json.JSONDecodeError, KeyError, Exception):
                continue
    
    print()  # 换行
    
    print(f"✅ 收集到 {matched_samples:,} 个匹配样本的马氏距离")
    
    return distances, matched_samples


def calculate_physics_recognition_rate_with_threshold(
    pattern_id: str,
    data_path: str,
    threshold: float
) -> Tuple[float, int, int]:
    """
    使用指定阈值计算物理识别率
    
    返回: (识别率百分比, 命中数, 总样本数)
    """
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
    
    # 扫描全量样本
    total_samples = 0
    hits = 0
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                case = json.loads(line)
                if 'ten_gods' not in case:
                    continue
                
                total_samples += 1
                
                # 计算5D张量
                tensor = calculate_5d_tensor(case['ten_gods'], weights_matrix, god_index_map)
                
                # 计算马氏距离
                dist = compute_mahalanobis_distance(tensor, mean_vector, cov_matrix)
                
                # 判定
                if dist < threshold:
                    hits += 1
                    
            except (json.JSONDecodeError, KeyError, Exception):
                continue
    
    recognition_rate = (hits / total_samples * 100.0) if total_samples > 0 else 0.0
    return recognition_rate, hits, total_samples


def binary_search_optimal_threshold(
    pattern_id: str,
    data_path: str,
    target_abundance: float,
    search_range: Tuple[float, float] = (1.0, 3.5),
    tolerance: float = 0.01,  # 目标偏差容忍度（百分比）
    max_iterations: int = 20
) -> Tuple[float, float]:
    """
    二分法搜索最优阈值
    
    返回: (最优阈值, 对应的识别率)
    """
    print(f"\n🔍 二分法搜索最优阈值（目标丰度: {target_abundance:.4f}%）")
    print(f"   搜索范围: [{search_range[0]:.2f}, {search_range[1]:.2f}]")
    
    low, high = search_range
    
    for iteration in range(max_iterations):
        mid = (low + high) / 2.0
        
        # 使用当前阈值计算识别率
        recognition_rate, _, _ = calculate_physics_recognition_rate_with_threshold(
            pattern_id, data_path, mid
        )
        
        error = abs(recognition_rate - target_abundance)
        
        print(f"   迭代 {iteration + 1}: 阈值={mid:.4f}, 识别率={recognition_rate:.4f}%, 偏差={error:.4f}%")
        
        # 检查是否达到目标
        if error <= tolerance:
            print(f"   ✅ 找到最优阈值: {mid:.4f}（识别率={recognition_rate:.4f}%，偏差={error:.4f}%）")
            return mid, recognition_rate
        
        # 二分法调整
        if recognition_rate < target_abundance:
            # 识别率过低，需要提高阈值（扩大范围，包含更多样本）
            low = mid
        else:
            # 识别率过高，需要降低阈值（缩小范围，排除更多样本）
            high = mid
        
        # 检查搜索范围是否足够小
        if (high - low) < 0.001:
            print(f"   ⚠️  搜索范围已足够小，停止搜索")
            break
    
    # 使用最后的中值作为最优阈值
    optimal_threshold = (low + high) / 2.0
    final_rate, _, _ = calculate_physics_recognition_rate_with_threshold(
        pattern_id, data_path, optimal_threshold
    )
    
    print(f"   ✅ 最终阈值: {optimal_threshold:.4f}（识别率={final_rate:.4f}%，偏差={abs(final_rate - target_abundance):.4f}%）")
    
    return optimal_threshold, final_rate


def update_registry_threshold(pattern_id: str, threshold: float):
    """更新registry文件，添加最优阈值"""
    registry_path = REGISTRY_DIR / f"{pattern_id}.json"
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry_data = json.load(f)
    
    # 确保feature_anchors存在
    if 'feature_anchors' not in registry_data['data']:
        registry_data['data']['feature_anchors'] = {}
    
    # 更新standard_manifold，添加阈值
    if 'standard_manifold' not in registry_data['data']['feature_anchors']:
        registry_data['data']['feature_anchors']['standard_manifold'] = {}
    
    registry_data['data']['feature_anchors']['standard_manifold']['optimal_threshold'] = threshold
    registry_data['data']['feature_anchors']['standard_manifold']['calibration_method'] = 'binary_search'
    
    # 写回文件
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已更新registry文件: {registry_path}")
    print(f"   optimal_threshold = {threshold:.4f}")


def main():
    parser = argparse.ArgumentParser(
        description='FDS 阈值校准（逆向阈值锚定）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fds_threshold_calibration.py --target A-01
  python fds_threshold_calibration.py --target A-01 --data ./data/holographic_universe_518k.jsonl
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
    
    parser.add_argument(
        '--skip-distribution',
        action='store_true',
        help='跳过距离分布计算，直接进行阈值搜索'
    )
    
    args = parser.parse_args()
    
    try:
        # 加载registry获取基准丰度
        registry_data = load_registry(args.target)
        base_abundance = registry_data['data']['population_stats']['base_abundance']
        print(f"🎯 基准丰度: {base_abundance:.4f}%")
        
        # 任务1：计算马氏距离分布
        if not args.skip_distribution:
            distances, matched_count = compute_mahalanobis_distances_for_matched_samples(
                args.target, args.data
            )
            
            distances_array = np.array(distances)
            
            print(f"\n📊 马氏距离分布统计:")
            print(f"   样本数: {len(distances):,}")
            print(f"   最小值: {distances_array.min():.4f}")
            print(f"   最大值: {distances_array.max():.4f}")
            print(f"   平均值: {distances_array.mean():.4f}")
            print(f"   中位数: {np.median(distances_array):.4f}")
            print(f"   标准差: {distances_array.std():.4f}")
            print(f"\n   分位点:")
            print(f"     25%: {np.percentile(distances_array, 25):.4f}")
            print(f"     50%: {np.percentile(distances_array, 50):.4f}")
            print(f"     75%: {np.percentile(distances_array, 75):.4f}")
            print(f"     85%: {np.percentile(distances_array, 85):.4f}")
            print(f"     90%: {np.percentile(distances_array, 90):.4f}")
            print(f"     95%: {np.percentile(distances_array, 95):.4f}")
            print(f"     99%: {np.percentile(distances_array, 99):.4f}")
        
        # 任务2：二分法搜索最优阈值
        optimal_threshold, optimal_rate = binary_search_optimal_threshold(
            args.target,
            args.data,
            base_abundance,
            search_range=(1.0, 3.5),
            tolerance=0.01,  # 1%容忍度
            max_iterations=20
        )
        
        # 任务3：更新registry
        update_registry_threshold(args.target, optimal_threshold)
        
        # 任务4：最终报告
        print("\n" + "=" * 60)
        print("📋 阈值校准报告")
        print("=" * 60)
        print(f"格局ID:        {args.target}")
        print(f"基准丰度:      {base_abundance:.4f}%")
        print(f"最优阈值:      {optimal_threshold:.4f}")
        print(f"识别率:        {optimal_rate:.4f}%")
        print(f"绝对偏差:      {abs(optimal_rate - base_abundance):.4f}%")
        print(f"相对偏差:      {abs(optimal_rate - base_abundance) / base_abundance * 100:.2f}%")
        print("=" * 60)
        
        print("\n✅ 阈值校准完成！")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

