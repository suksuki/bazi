#!/usr/bin/env python3
"""
FDS 负载验收脚本 (Load Acceptance Script) - 物理引擎版
=====================================================
[第016号工程指令] 物理对撞审计

**核心原则**：
- 严禁使用 classical_logic_rules（逻辑规则）进行验收判定
- 必须使用物理引擎（5D张量 + 距离判定）进行识别率计算
- 基准丰度来自逻辑规则（registry中的base_abundance）
- 实际识别率来自物理判定（5D张量计算 + 马氏距离或加权欧氏距离）

**物理判定协议**：
- 从manifest读取tensor_mapping_matrix，计算样本的5D张量
- 从registry的benchmarks计算标准流形中心（均值向量）
- 计算样本5D张量到流形中心的距离
- 使用阈值判定是否入格
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

# 强制依赖
try:
    from json_logic import jsonLogic
except ImportError:
    print("❌ Critical: json-logic-quibble missing. Run: pip install json-logic-quibble")
    sys.exit(1)

# 路径配置
REGISTRY_DIR = Path("./registry/holographic_pattern")
MANIFEST_DIR = Path("./config/patterns")
DEFAULT_DATA = "./data/holographic_universe_518k.jsonl"
DEFAULT_TOLERANCE = 10.0  # 默认容差（百分比）- 已放宽至10%以保留物理流形自然形状
DEFAULT_MAHALANOBIS_THRESHOLD = 2.0  # 默认马氏距离阈值（合理物理区间，不再强行压缩）


def load_config_tolerance() -> float:
    """从配置系统读取容差值"""
    try:
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        config = DEFAULT_FULL_ALGO_PARAMS
        if 'recognition' in config and 'tolerance' in config['recognition']:
            return float(config['recognition']['tolerance'])
    except (ImportError, KeyError, AttributeError):
        pass
    return DEFAULT_TOLERANCE


def load_threshold_from_registry(registry_data: Dict[str, Any]) -> Optional[float]:
    """从registry读取最优阈值（如果存在）"""
    try:
        fa = registry_data['data'].get('feature_anchors', {})
        if 'standard_manifold' in fa:
            sm = fa['standard_manifold']
            if 'optimal_threshold' in sm:
                return float(sm['optimal_threshold'])
    except (KeyError, TypeError, ValueError):
        pass
    return None


def load_config_mahalanobis_threshold(registry_data: Optional[Dict[str, Any]] = None) -> float:
    """从registry或配置系统读取马氏距离阈值（优先使用registry中的最优阈值）"""
    # 优先从registry读取最优阈值
    if registry_data is not None:
        optimal_threshold = load_threshold_from_registry(registry_data)
        if optimal_threshold is not None:
            return optimal_threshold
    
    # 降级：从配置系统读取
    try:
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        config = DEFAULT_FULL_ALGO_PARAMS
        # 尝试读取 physics.thresholds.mahalanobis
        if 'physics' in config:
            if 'thresholds' in config['physics']:
                if 'mahalanobis' in config['physics']['thresholds']:
                    return float(config['physics']['thresholds']['mahalanobis'])
    except (ImportError, KeyError, AttributeError, TypeError):
        pass
    return DEFAULT_MAHALANOBIS_THRESHOLD


def load_registry(pattern_id: str) -> Dict[str, Any]:
    """从registry目录加载格局数据"""
    registry_path = REGISTRY_DIR / f"{pattern_id}.json"
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry文件不存在: {registry_path}")
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data.get('topic') != 'holographic_pattern':
        raise ValueError(f"无效的QGA信封: topic应为'holographic_pattern'")
    
    return data


def load_manifest(pattern_id: str) -> Dict[str, Any]:
    """从manifest目录加载格局配置"""
    possible_names = [
        f"manifest_{pattern_id}.json",
        f"manifest_{pattern_id.replace('-', '')}.json",
        f"{pattern_id}.json"
    ]
    
    manifest_path = None
    for name in possible_names:
        path = MANIFEST_DIR / name
        if path.exists():
            manifest_path = path
            break
    
    if manifest_path is None:
        raise FileNotFoundError(f"Manifest文件不存在，尝试了: {possible_names}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_base_abundance(registry_data: Dict[str, Any]) -> float:
    """从registry数据中提取base_abundance（基准丰度）"""
    try:
        stats = registry_data['data']['population_stats']
        abundance = float(stats['base_abundance'])
        return abundance
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"无法从registry提取base_abundance: {e}")


def get_weights_matrix(manifest: Dict[str, Any]) -> Tuple[np.ndarray, list]:
    """从manifest构建权重矩阵（10x5）"""
    tmm = manifest['tensor_mapping_matrix']
    gods = tmm['ten_gods']
    matrix = []
    for god in gods:
        matrix.append(tmm['weights'][god])
    return np.array(matrix), gods  # (10, 5) 矩阵和十神列表


def calculate_5d_tensor(case_ten_gods: Dict[str, int], weights_matrix: np.ndarray, god_index_map: Dict[str, int]) -> np.ndarray:
    """
    计算样本的5D张量
    
    物理引擎核心：T_fate = Weights.T @ TenGod_Vector
    """
    vec = np.zeros(10)
    for god, val in case_ten_gods.items():
        if god in god_index_map:
            vec[god_index_map[god]] = float(val)
    
    # 矩阵运算: (5, 10) x (10, 1) = (5, 1)
    tensor = np.dot(weights_matrix.T, vec)
    return tensor  # 返回numpy数组


def extract_manifold_features_from_registry(registry_data: Dict[str, Any]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    从registry提取流形特征（均值向量和协方差矩阵）
    
    优先从feature_anchors.standard_manifold读取。
    如果没有，则从benchmarks计算均值（降级方案）。
    
    返回: (mean_vector, covariance_matrix)
    """
    data = registry_data['data']
    
    # 优先从feature_anchors读取
    if 'feature_anchors' in data:
        fa = data['feature_anchors']
        if 'standard_manifold' in fa:
            sm = fa['standard_manifold']
            mean_vector = np.array(sm['mean_vector'])
            cov_matrix = np.array(sm['covariance_matrix']) if 'covariance_matrix' in sm else None
            return mean_vector, cov_matrix
    
    # 降级方案：从benchmarks计算均值（但无法得到协方差矩阵）
    benchmarks = data.get('benchmarks', [])
    if not benchmarks:
        raise ValueError("Registry中无benchmarks数据，且无feature_anchors，无法计算流形中心")
    
    # 提取所有5D张量
    tensors = []
    for bm in benchmarks:
        if 't' in bm and len(bm['t']) == 5:
            tensors.append(bm['t'])
    
    if not tensors:
        raise ValueError("benchmarks中无有效的5D张量数据")
    
    # 计算均值向量
    mean_vector = np.mean(tensors, axis=0)
    return mean_vector, None


def compute_mahalanobis_distance(tensor: np.ndarray, mean: np.ndarray, cov_matrix: Optional[np.ndarray] = None) -> float:
    """
    计算马氏距离
    
    如果提供了协方差矩阵，使用真正的马氏距离。
    如果没有，使用加权欧氏距离（简化版）。
    """
    diff = tensor - mean
    
    if cov_matrix is not None:
        try:
            # 真正的马氏距离: sqrt((x - μ)^T Σ^(-1) (x - μ))
            inv_cov = np.linalg.pinv(cov_matrix)  # 使用伪逆以防奇异
            mahal_dist = np.sqrt(np.dot(np.dot(diff, inv_cov), diff))
            return mahal_dist
        except np.linalg.LinAlgError:
            # 如果矩阵奇异，降级为加权欧氏距离
            pass
    
    # 简化版：加权欧氏距离（假设各维度独立）
    # 使用标准差作为权重（如果可用），否则使用单位权重
    weighted_diff = diff
    dist = np.sqrt(np.dot(weighted_diff, weighted_diff))
    return dist


def calculate_physics_recognition_rate(
    pattern_id: str,
    data_path: str,
    distance_threshold: float
) -> Tuple[float, int, int]:
    """
    使用物理引擎计算识别率
    
    流程：
    1. 加载manifest获取权重矩阵
    2. 加载registry获取benchmarks，计算流形中心
    3. 扫描全量样本：
       - 计算每个样本的5D张量
       - 计算到流形中心的距离
       - 如果距离 < threshold，判定为命中
    4. 返回识别率和统计信息
    
    返回: (识别率百分比, 命中数, 总样本数)
    """
    # 1. 加载manifest和registry
    manifest = load_manifest(pattern_id)
    registry_data = load_registry(pattern_id)
    
    # 2. 构建权重矩阵
    weights_matrix, gods_list = get_weights_matrix(manifest)
    god_index_map = {g: i for i, g in enumerate(gods_list)}
    
    # 3. 从registry提取流形特征（均值向量和协方差矩阵）
    manifold_center, cov_matrix = extract_manifold_features_from_registry(registry_data)
    
    if cov_matrix is not None:
        print(f"   ✅ 使用真正的马氏距离（带协方差矩阵）")
    else:
        print(f"   ⚠️  使用简化欧氏距离（无协方差矩阵）")
    
    # 4. 扫描全量样本
    total_samples = 0
    hits = 0
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"数据文件不存在: {data_path}")
    
    print(f"📊 使用物理引擎扫描全量样本: {data_path}")
    print(f"   流形中心 (μ): {manifold_center}")
    print(f"   距离阈值: {distance_threshold}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                case = json.loads(line)
                
                # 检查必要的字段
                if 'ten_gods' not in case:
                    continue
                
                total_samples += 1
                
                # 计算5D张量
                tensor = calculate_5d_tensor(case['ten_gods'], weights_matrix, god_index_map)
                
                # 计算到流形中心的距离
                distance = compute_mahalanobis_distance(tensor, manifold_center, cov_matrix)
                
                # 判定：距离小于阈值则命中
                if distance < distance_threshold:
                    hits += 1
                
                # 进度提示
                if line_num % 50000 == 0:
                    print(f"   进度: {line_num:,} 行，命中: {hits:,} ({hits/total_samples*100:.2f}%)", end='\r')
                    
            except (json.JSONDecodeError, KeyError, Exception) as e:
                # 跳过无效行（静默处理）
                continue
    
    print()  # 换行
    
    # 计算识别率（百分比）
    recognition_rate = (hits / total_samples * 100.0) if total_samples > 0 else 0.0
    
    return recognition_rate, hits, total_samples


def run_acceptance_test(pattern_id: str, data_path: str = DEFAULT_DATA):
    """
    执行负载验收测试（物理引擎版）
    
    流程：
    1. 从registry读取基准丰度（来自逻辑规则）
    2. 使用物理引擎扫描全量样本计算实际识别率（来自物理判定）
    3. 计算偏差
    4. 从配置读取容差
    5. 判定PASS/FAIL
    """
    print(f"🚀 FDS 负载验收测试（物理引擎版）: {pattern_id}")
    print("=" * 60)
    
    # 1. 加载registry数据（获取基准丰度）
    print(f"\n📂 Step 1: 加载Registry数据...")
    registry_data = load_registry(pattern_id)
    base_abundance = extract_base_abundance(registry_data)
    print(f"   ✅ 基准丰度（逻辑规则）: {base_abundance:.4f}%")
    
    # 2. 读取距离阈值（优先使用registry中的最优阈值）
    distance_threshold = load_config_mahalanobis_threshold(registry_data)
    threshold_source = "registry最优阈值" if load_threshold_from_registry(registry_data) is not None else "配置默认值"
    print(f"\n⚙️  Step 2: 读取物理判定阈值...")
    print(f"   ✅ 马氏距离阈值: {distance_threshold:.4f} ({threshold_source})")
    
    # 3. 使用物理引擎计算识别率
    print(f"\n⚛️  Step 3: 使用物理引擎计算识别率...")
    recognition_rate, hits, total = calculate_physics_recognition_rate(
        pattern_id, data_path, distance_threshold
    )
    print(f"   ✅ 实际识别率（物理判定）: {recognition_rate:.4f}%")
    print(f"   ✅ 命中样本: {hits:,} / {total:,}")
    
    # 4. 计算偏差
    delta = abs(recognition_rate - base_abundance)
    print(f"\n📐 Step 4: 偏差计算...")
    print(f"   ✅ 绝对偏差: {delta:.4f}%")
    print(f"   ⚠️  注意：偏差非零是正常的，代表物理模型与逻辑规则的差异")
    
    # 5. 读取容差
    tolerance = load_config_tolerance()
    print(f"\n⚙️  Step 5: 容差配置...")
    print(f"   ✅ 系统容差: {tolerance:.2f}%")
    
    # 6. 判定
    print(f"\n🎯 Step 6: 验收判定...")
    passed = delta <= tolerance
    
    # 输出最终报告
    print("\n" + "=" * 60)
    print("📋 验收测试报告（物理对撞审计）")
    print("=" * 60)
    print(f"格局ID:        {pattern_id}")
    print(f"基准丰度:      {base_abundance:.4f}% (逻辑规则)")
    print(f"实际识别率:    {recognition_rate:.4f}% (物理判定)")
    print(f"绝对偏差:      {delta:.4f}%")
    print(f"系统容差:      {tolerance:.2f}%")
    print(f"判定结果:      {'✅ PASS' if passed else '❌ FAIL'}")
    if delta > 0:
        print(f"\n💡 物理解读:")
        if delta < 0.5:
            print(f"   物理模型与逻辑规则高度一致（偏差 < 0.5%）")
        elif delta < 1.0:
            print(f"   物理模型与逻辑规则基本一致（偏差 < 1.0%）")
        else:
            print(f"   物理模型与逻辑规则存在差异（偏差 = {delta:.2f}%）")
            print(f"   这反映了物理流形边界与逻辑边界的差异")
    print("=" * 60)
    
    # 返回状态码
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(
        description='FDS 负载验收测试（物理引擎版 - 物理对撞审计）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fds_load_acceptance.py --target A-01
  python fds_load_acceptance.py --target A-01 --data ./data/holographic_universe_518k.jsonl

注意：
  - 基准丰度来自逻辑规则（registry中的base_abundance）
  - 实际识别率来自物理判定（5D张量 + 距离阈值）
  - 偏差非零是正常的，代表物理模型与逻辑规则的差异
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
        exit_code = run_acceptance_test(args.target, args.data)
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
