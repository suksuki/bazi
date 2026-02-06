#!/usr/bin/env python3
"""
FDS 子格局质心计算脚本 (Sub-pattern Centroids Calculator)
==========================================================
[第017号工程指令] 子格局锚点固化

**目标**：
- 计算A-01-S1和A-01-S2的5D质心向量
- 将质心写回registry文件作为永久物理锚点

**核心原则**：
- 质心即真相：质心作为永久物理锚点，不再依赖实时计算
- 脱离复杂依赖：计算结果固化到registry，知识生成器只需比对静态锚点
"""

import argparse
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 路径配置
REGISTRY_DIR = Path("./registry/holographic_pattern")
MANIFEST_DIR = Path("./config/patterns")
DEFAULT_DATA = "./data/holographic_universe_518k.jsonl"

# 尝试导入json_logic，如果失败则使用手动实现
try:
    from json_logic import jsonLogic
    HAS_JSON_LOGIC = True
except ImportError:
    HAS_JSON_LOGIC = False
    print("⚠️ json-logic-quibble未安装，将使用简化逻辑判断")


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
    return tensor


def evaluate_simple_logic(logic_expr: Dict[str, Any], case: Dict[str, Any]) -> bool:
    """
    简化的逻辑表达式求值（用于替代json_logic）
    仅支持基本的比较操作和逻辑组合
    """
    if not isinstance(logic_expr, dict):
        return False
    
    # 处理 "and" 操作
    if "and" in logic_expr:
        conditions = logic_expr["and"]
        return all(evaluate_simple_logic(cond, case) for cond in conditions)
    
    # 处理 "or" 操作
    if "or" in logic_expr:
        conditions = logic_expr["or"]
        return any(evaluate_simple_logic(cond, case) for cond in conditions)
    
    # 处理比较操作: {">=": [var, value]} 或 {">": [var, value]} 或 {"<": [var, value]}
    for op, args in logic_expr.items():
        if op in [">=", ">", "<", "<=", "=="]:
            if len(args) != 2:
                return False
            
            # 解析变量或值
            def get_value(arg):
                if isinstance(arg, dict) and "var" in arg:
                    var_path = arg["var"]
                    # 支持嵌套路径，如 "ten_gods.ZG"
                    parts = var_path.split(".")
                    val = case
                    for part in parts:
                        if isinstance(val, dict):
                            val = val.get(part, 0)
                        else:
                            return 0
                    return float(val) if isinstance(val, (int, float)) else 0
                return float(arg) if isinstance(arg, (int, float)) else 0
            
            left = get_value(args[0])
            right = get_value(args[1])
            
            if op == ">=":
                return left >= right
            elif op == ">":
                return left > right
            elif op == "<":
                return left < right
            elif op == "<=":
                return left <= right
            elif op == "==":
                return left == right
    
    return False


def compute_subpattern_centroids(
    pattern_id: str,
    data_path: str,
    manifest_data: Dict[str, Any]
) -> Dict[str, List[float]]:
    """
    计算子格局的5D质心向量
    
    Returns:
        字典：{子格局ID: [5D质心向量]}
    """
    sub_defs = manifest_data.get("sub_pattern_definitions", {})
    if not sub_defs:
        print("⚠️ Manifest中无子格局定义")
        return {}
    
    # 构建权重矩阵
    weights_matrix, gods_list = get_weights_matrix(manifest_data)
    god_index_map = {g: i for i, g in enumerate(gods_list)}
    
    # 为每个子格局收集匹配样本的张量
    accumulators: Dict[str, List[np.ndarray]] = {key: [] for key in sub_defs.keys()}
    
    print(f"🔍 开始计算 {pattern_id} 的子格局质心...")
    print(f"   子格局数量: {len(sub_defs)}")
    
    total_scanned = 0
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                case = json.loads(line)
                total_scanned += 1
                
                for sub_id, sub_def in sub_defs.items():
                    logic = sub_def.get('logic')
                    if not logic:
                        continue
                    
                    try:
                        # 使用json_logic或简化逻辑判断
                        if HAS_JSON_LOGIC:
                            matched = jsonLogic(logic, case)
                        else:
                            matched = evaluate_simple_logic(logic, case)
                        
                        if matched:
                            tensor = calculate_5d_tensor(
                                case.get('ten_gods', {}),
                                weights_matrix,
                                god_index_map
                            )
                            accumulators[sub_id].append(tensor)
                    except Exception as e:
                        # 静默跳过错误样本
                        continue
                
                if total_scanned % 50000 == 0:
                    matched_counts = {k: len(v) for k, v in accumulators.items()}
                    print(f"   进度: {total_scanned:,} 行，匹配: {matched_counts}", end='\r')
            except json.JSONDecodeError:
                continue
    
    print()  # 换行
    
    # 计算每个子格局的质心（均值向量）
    centroids: Dict[str, List[float]] = {}
    for sub_id, tensors in accumulators.items():
        if not tensors:
            print(f"⚠️ {sub_id}: 无匹配样本，跳过")
            continue
        
        tensors_array = np.array(tensors)
        centroid = np.mean(tensors_array, axis=0)
        centroids[sub_id] = [float(x) for x in centroid]
        
        print(f"✅ {sub_id}: {len(tensors):,} 个样本")
        print(f"   质心向量: {[round(x, 4) for x in centroid]}")
    
    return centroids


def update_registry_with_centroids(pattern_id: str, centroids: Dict[str, List[float]]):
    """
    将子格局质心写回registry文件
    
    架构师要求：子格局质心必须作为"永久物理锚点"存在
    """
    registry_path = REGISTRY_DIR / f"{pattern_id}.json"
    
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry文件不存在: {registry_path}")
    
    # 读取现有registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry_data = json.load(f)
    
    # 确保feature_anchors结构存在
    if 'feature_anchors' not in registry_data['data']:
        registry_data['data']['feature_anchors'] = {}
    
    # 创建或更新subpattern_centroids
    if 'subpattern_centroids' not in registry_data['data']['feature_anchors']:
        registry_data['data']['feature_anchors']['subpattern_centroids'] = {}
    
    # 写入质心数据
    for sub_id, centroid in centroids.items():
        registry_data['data']['feature_anchors']['subpattern_centroids'][sub_id] = {
            'centroid_vector': centroid,
            'dimensions': ['E', 'O', 'M', 'S', 'R'],
            'calculation_method': 'full_matched_samples',
            'description': f'从所有逻辑匹配样本计算的{sub_id}质心向量'
        }
    
    # 保存更新后的registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 质心已写回registry: {registry_path}")
    print(f"   更新了 {len(centroids)} 个子格局的质心锚点")


def main():
    parser = argparse.ArgumentParser(
        description='FDS 子格局质心计算与锚点固化工具'
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
        # 1. 加载manifest
        manifest_data = load_manifest(args.target)
        print(f"✅ 已加载manifest: {args.target}")
        
        # 2. 计算子格局质心
        centroids = compute_subpattern_centroids(
            args.target,
            args.data,
            manifest_data
        )
        
        if not centroids:
            print("❌ 未计算出任何子格局质心，退出")
            return 1
        
        # 3. 写回registry
        update_registry_with_centroids(args.target, centroids)
        
        print("\n" + "=" * 60)
        print("📋 子格局质心固化报告")
        print("=" * 60)
        print(f"格局ID:        {args.target}")
        print(f"质心数量:      {len(centroids)}")
        for sub_id, centroid in centroids.items():
            print(f"  {sub_id}:     {[round(x, 4) for x in centroid]}")
        print("=" * 60)
        
        print("\n✅ 子格局质心固化完成！")
        print("   质心已作为永久物理锚点写入registry，知识生成器可直接使用")
        
        return 0
        
    except Exception as e:
        print(f"❌ 执行失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
