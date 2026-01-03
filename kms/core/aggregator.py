"""
聚合器 (Aggregator)
将多个codex条目聚合为pattern_manifest.json

基于: FDS_KMS_SPEC_v1.0-BETA.md 第4.1节
"""

from typing import Dict, Any, List, Optional
import numpy as np
import json


class Aggregator:
    """
    配置生成聚合器
    实现RC2规范中的聚合算法
    """
    
    # 十神代码到索引的映射
    TEN_GOD_TO_INDEX = {
        "ZG": 0, "PG": 1,
        "ZC": 2, "PC": 3,
        "ZS": 4, "PS": 5,
        "ZR": 6, "PR": 7,
        "ZB": 8, "PB": 9
    }
    
    # 维度到索引的映射
    DIMENSION_TO_INDEX = {
        "E": 0, "O": 1, "M": 2, "S": 3, "R": 4
    }
    
    @staticmethod
    def hard_tanh(x: float) -> float:
        """
        RC2规范: Hard Tanh 归一化
        保留物理意义，不进行线性缩放
        """
        return max(-1.0, min(1.0, x))
    
    @staticmethod
    def assemble_logic_tree(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 1: 逻辑树组装
        
        实现RC2规范中的逻辑树组装算法：
        - forming条件 → 加入AND根节点
        - breaking条件 → 检查是否有对应的saving条件
          - 有救: { "or": [ { "!": breaking }, saving ] }
          - 无救: { "!": breaking }
        
        Args:
            entries: codex条目列表
            
        Returns:
            组装后的JSONLogic表达式树
        """
        root = {"and": []}
        
        # 收集forming条件
        forming_conditions = [
            e["logic_extraction"]["expression_tree"]
            for e in entries
            if e.get("logic_extraction", {}).get("logic_type") == "forming_condition"
        ]
        root["and"].extend(forming_conditions)
        
        # 处理breaking和saving条件
        breaking_entries = [
            e for e in entries
            if e.get("logic_extraction", {}).get("logic_type") == "breaking_condition"
        ]
        saving_entries = [
            e for e in entries
            if e.get("logic_extraction", {}).get("logic_type") == "saving_condition"
        ]
        
        # 按target_pattern匹配
        saving_by_pattern = {}
        for s in saving_entries:
            pattern = s["logic_extraction"].get("target_pattern", "")
            if pattern not in saving_by_pattern:
                saving_by_pattern[pattern] = []
            saving_by_pattern[pattern].append(s["logic_extraction"]["expression_tree"])
        
        # 处理每个breaking条件
        for b in breaking_entries:
            pattern = b["logic_extraction"].get("target_pattern", "")
            breaking_expr = b["logic_extraction"]["expression_tree"]
            
            # 检查是否有对应的saving条件
            if pattern in saving_by_pattern and saving_by_pattern[pattern]:
                # Case A: 有救
                # { "or": [ { "!": breaking }, saving ] }
                saving_expr = saving_by_pattern[pattern][0]  # 取第一个
                root["and"].append({
                    "or": [
                        {"!": breaking_expr},
                        saving_expr
                    ]
                })
            else:
                # Case B: 无救
                # { "!": breaking }
                root["and"].append({"!": breaking_expr})
        
        return root
    
    @staticmethod
    def calculate_weighted_matrix(entries: List[Dict[str, Any]], 
                                  noise_std: float = 0.01) -> np.ndarray:
        """
        Step 2: 权重矩阵计算
        
        实现RC2规范中的加权平均算法：
        W[ten_god][axis] = Σ(w_mod_i × rel_score_i) / Σ(rel_score_i)
        
        Args:
            entries: codex条目列表
            noise_std: 高斯噪声标准差（用于稀疏填充）
            
        Returns:
            10×5的权重矩阵 (10神 × 5维)
        """
        matrix = np.zeros((10, 5))
        relevance_sums = np.zeros((10, 5))
        
        # 收集所有physics_impact
        for entry in entries:
            physics = entry.get("physics_impact")
            if not physics:
                continue
            
            target_ten_god = physics.get("target_ten_god")
            if target_ten_god not in Aggregator.TEN_GOD_TO_INDEX:
                continue
            
            row = Aggregator.TEN_GOD_TO_INDEX[target_ten_god]
            relevance = entry.get("relevance_score", 1.0)
            
            # 处理每个维度影响
            for dim_impact in physics.get("impact_dimensions", []):
                axis = dim_impact.get("axis")
                if axis not in Aggregator.DIMENSION_TO_INDEX:
                    continue
                
                col = Aggregator.DIMENSION_TO_INDEX[axis]
                weight_modifier = dim_impact.get("weight_modifier", 0.0)
                
                # 加权累加
                weighted_val = weight_modifier * relevance
                matrix[row, col] += weighted_val
                relevance_sums[row, col] += relevance
        
        # 执行加权平均（避免除以0）
        with np.errstate(divide='ignore', invalid='ignore'):
            final_matrix = matrix / relevance_sums
            final_matrix = np.nan_to_num(final_matrix)  # 0/0 -> 0
        
        # 稀疏填充：未定义的映射填入高斯噪声
        mask = relevance_sums == 0
        if mask.any():
            noise = np.random.normal(0, noise_std, size=(10, 5))
            final_matrix[mask] = noise[mask]
        
        # 执行Hard Tanh归一化
        vectorized_tanh = np.vectorize(Aggregator.hard_tanh)
        final_matrix = vectorized_tanh(final_matrix)
        
        return final_matrix
    
    @staticmethod
    def resolve_lock_conflicts(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Step 3: 锁定冲突解决
        
        检测并解决同一位置的锁定请求冲突
        
        Args:
            entries: codex条目列表
            
        Returns:
            解决冲突后的strong_correlation列表
        """
        # 收集所有锁定请求
        lock_requests = {}  # {(ten_god, axis): [requests]}
        
        for entry in entries:
            physics = entry.get("physics_impact")
            if not physics:
                continue
            
            target_ten_god = physics.get("target_ten_god")
            priority = entry.get("logic_extraction", {}).get("priority", 50)
            relevance = entry.get("relevance_score", 1.0)
            
            for dim_impact in physics.get("impact_dimensions", []):
                if not dim_impact.get("lock_request", False):
                    continue
                
                axis = dim_impact.get("axis")
                key = (target_ten_god, axis)
                
                if key not in lock_requests:
                    lock_requests[key] = []
                
                lock_requests[key].append({
                    "weight_modifier": dim_impact.get("weight_modifier", 0.0),
                    "priority": priority,
                    "relevance": relevance,
                    "reason": dim_impact.get("reason", ""),
                    "entry": entry
                })
        
        # 解决冲突
        strong_correlations = []
        
        for (ten_god, axis), requests in lock_requests.items():
            if len(requests) == 1:
                # 无冲突
                req = requests[0]
                strong_correlations.append({
                    "ten_god": ten_god,
                    "dimension": axis,
                    "reason": req["reason"]
                })
            else:
                # 检测冲突（符号相反）
                weights = [r["weight_modifier"] for r in requests]
                has_conflict = any(w1 * w2 < 0 for i, w1 in enumerate(weights) 
                                 for w2 in weights[i+1:])
                
                if has_conflict:
                    # 按优先级排序
                    requests.sort(key=lambda x: x["priority"], reverse=True)
                    
                    # 如果优先级相同，按relevance总和排序
                    if requests[0]["priority"] == requests[1]["priority"]:
                        # 计算relevance总和
                        relevance_sums = {}
                        for req in requests:
                            key = (req["priority"], req["weight_modifier"] > 0)
                            relevance_sums[key] = relevance_sums.get(key, 0) + req["relevance"]
                        
                        # 选择relevance总和高的
                        best_key = max(relevance_sums.items(), key=lambda x: x[1])[0]
                        requests = [r for r in requests 
                                  if (r["priority"], r["weight_modifier"] > 0) == best_key]
                    
                    # 如果仍相同，抛出异常
                    if len(requests) > 1 and requests[0]["priority"] == requests[1]["priority"]:
                        raise ValueError(
                            f"锁定冲突无法解决: {ten_god}-{axis}, "
                            f"优先级相同且relevance相同"
                        )
                
                # 使用最高优先级的请求
                req = requests[0]
                strong_correlations.append({
                    "ten_god": ten_god,
                    "dimension": axis,
                    "reason": req["reason"]
                })
        
        return strong_correlations
    
    @classmethod
    def generate_manifest(cls,
                          pattern_id: str,
                          pattern_name: str,
                          entries: List[Dict[str, Any]],
                          version: str = "3.0") -> Dict[str, Any]:
        """
        生成完整的pattern_manifest.json
        
        Args:
            pattern_id: 格局ID (如 "B-01")
            pattern_name: 格局名称 (如 "食神格")
            entries: codex条目列表
            version: 版本号
            
        Returns:
            完整的pattern_manifest.json字典
        """
        # Step 1: 组装逻辑树
        logic_tree = cls.assemble_logic_tree(entries)
        
        # Step 2: 计算权重矩阵
        weight_matrix = cls.calculate_weighted_matrix(entries)
        
        # Step 3: 解决锁定冲突
        strong_correlations = cls.resolve_lock_conflicts(entries)
        
        # 构建weights字典
        ten_gods = ["ZG", "PG", "ZC", "PC", "ZS", "PS", "ZR", "PR", "ZB", "PB"]
        dimensions = ["E", "O", "M", "S", "R"]
        
        weights = {}
        for i, ten_god in enumerate(ten_gods):
            weights[ten_god] = weight_matrix[i].tolist()
        
        # 构建manifest
        manifest = {
            "pattern_id": pattern_id,
            "version": version,
            "classical_logic_rules": {
                "format": "jsonlogic",
                "expression": logic_tree
            },
            "tensor_mapping_matrix": {
                "ten_gods": ten_gods,
                "dimensions": dimensions,
                "weights": weights,
                "strong_correlation": strong_correlations
            }
        }
        
        return manifest

