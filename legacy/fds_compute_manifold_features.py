#!/usr/bin/env python3
"""
FDS 全量统计特征提取脚本 (Full Feature Extraction)
==================================================
[第017号工程指令] 从所有逻辑匹配样本中计算流形特征

**目标**：
- 遍历所有符合古典逻辑规则的命中样本
- 计算5D均值向量 (μ) 和协方差矩阵 (Σ)
- 将结果存入registry文件的feature_anchors字段

**输入**：
- pattern_id: 格局ID（如 A-01）
- manifest: 格局配置文件路径
- data: 样本数据文件路径

**输出**：
- 更新registry文件，添加feature_anchors.standard_manifold
"""

import argparse
import json
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# 强制依赖
try:
    from json_logic import jsonLogic
except ImportError:
    print("❌ Critical: json-logic-quibble missing. Run: pip install json-logic-quibble")
    sys.exit(1)

REGISTRY_DIR = Path("./registry/holographic_pattern")
MANIFEST_DIR = Path("./config/patterns")
DEFAULT_DATA = "./data/holographic_universe_518k.jsonl"


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """加载manifest文件"""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_weights_matrix(manifest: Dict[str, Any]) -> tuple:
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


def compute_manifold_features(
    pattern_id: str,
    manifest_path: str,
    data_path: str
) -> tuple:
    """
    从所有逻辑匹配样本中计算流形特征
    
    返回: (mean_vector, covariance_matrix, sample_count)
    """
    print(f"🚀 开始计算 {pattern_id} 的全量统计特征...")
    
    # 1. 加载manifest
    manifest = load_manifest(manifest_path)
    weights_matrix, gods_list = get_weights_matrix(manifest)
    god_index_map = {g: i for i, g in enumerate(gods_list)}
    
    # 2. 提取逻辑规则
    logic_expression = manifest['classical_logic_rules']['expression']
    
    # 3. 遍历所有样本，收集逻辑匹配样本的5D张量
    print(f"📊 扫描样本数据: {data_path}")
    tensors = []
    total_samples = 0
    matched_samples = 0
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"数据文件不存在: {data_path}")
    
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
                    tensors.append(tensor)
                
                # 进度提示
                if line_num % 50000 == 0:
                    print(f"   进度: {line_num:,} 行，匹配: {matched_samples:,} ({len(tensors):,} 张量)", end='\r')
                    
            except (json.JSONDecodeError, KeyError, Exception) as e:
                continue
    
    print()  # 换行
    
    if len(tensors) == 0:
        raise ValueError(f"未找到任何匹配样本，无法计算流形特征")
    
    # 4. 转换为numpy数组
    tensor_array = np.array(tensors)  # (N, 5)
    
    print(f"✅ 收集到 {len(tensors):,} 个匹配样本的5D张量")
    
    # 5. 计算均值向量
    mean_vector = np.mean(tensor_array, axis=0)
    
    # 6. 计算协方差矩阵
    # numpy.cov默认计算行变量之间的协方差，我们需要列变量（维度）之间的协方差
    # 所以需要转置，或者使用rowvar=False
    covariance_matrix = np.cov(tensor_array, rowvar=False)  # rowvar=False表示每列是一个变量
    
    print(f"✅ 均值向量 (μ): {mean_vector}")
    print(f"✅ 协方差矩阵 (Σ) 形状: {covariance_matrix.shape}")
    print(f"✅ 协方差矩阵对角线（各维度方差）: {np.diag(covariance_matrix)}")
    
    return mean_vector, covariance_matrix, len(tensors)


def update_registry_with_features(
    pattern_id: str,
    mean_vector: np.ndarray,
    covariance_matrix: np.ndarray,
    sample_count: int
):
    """
    更新registry文件，添加feature_anchors字段
    """
    registry_path = REGISTRY_DIR / f"{pattern_id}.json"
    
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry文件不存在: {registry_path}")
    
    # 读取现有registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry_data = json.load(f)
    
    # 确保data字段存在
    if 'data' not in registry_data:
        registry_data['data'] = {}
    
    # 创建或更新feature_anchors
    if 'feature_anchors' not in registry_data['data']:
        registry_data['data']['feature_anchors'] = {}
    
    # 添加standard_manifold
    registry_data['data']['feature_anchors']['standard_manifold'] = {
        'mean_vector': mean_vector.tolist(),
        'covariance_matrix': covariance_matrix.tolist(),
        'sample_count': sample_count,
        'computation_method': 'full_matched_samples',
        'description': '从所有逻辑匹配样本计算的统计流形特征'
    }
    
    # 写回文件
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已更新registry文件: {registry_path}")
    print(f"   feature_anchors.standard_manifold 已写入")


def main():
    parser = argparse.ArgumentParser(
        description='FDS 全量统计特征提取（从所有匹配样本计算流形特征）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fds_compute_manifold_features.py --target A-01
  python fds_compute_manifold_features.py --target A-01 --manifest config/patterns/manifest_A01.json
        """
    )
    
    parser.add_argument(
        '--target',
        required=True,
        help='格局ID（如 A-01）'
    )
    
    parser.add_argument(
        '--manifest',
        help='Manifest文件路径（可选，默认从config/patterns/查找）'
    )
    
    parser.add_argument(
        '--data',
        default=DEFAULT_DATA,
        help=f'数据文件路径（默认: {DEFAULT_DATA}）'
    )
    
    args = parser.parse_args()
    
    # 确定manifest路径
    if args.manifest:
        manifest_path = args.manifest
    else:
        pattern_id = args.target
        possible_names = [
            f"manifest_{pattern_id}.json",
            f"manifest_{pattern_id.replace('-', '')}.json",
            f"{pattern_id}.json"
        ]
        manifest_path = None
        for name in possible_names:
            path = MANIFEST_DIR / name
            if path.exists():
                manifest_path = str(path)
                break
        
        if manifest_path is None:
            print(f"❌ 错误: 未找到manifest文件，尝试了: {possible_names}")
            sys.exit(1)
    
    try:
        # 计算流形特征
        mean_vector, covariance_matrix, sample_count = compute_manifold_features(
            args.target,
            manifest_path,
            args.data
        )
        
        # 更新registry
        update_registry_with_features(
            args.target,
            mean_vector,
            covariance_matrix,
            sample_count
        )
        
        print("\n✅ 全量统计特征提取完成！")
        print(f"   均值向量维度: {mean_vector.shape}")
        print(f"   协方差矩阵维度: {covariance_matrix.shape}")
        print(f"   样本数量: {sample_count:,}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

