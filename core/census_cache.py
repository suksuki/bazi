"""
海选结果全息缓存 (Census Cache Layer)
=====================================
缓存海选结果和特征重心，实现毫秒级预测响应

架构定位：
- 将海选 ID 集合和特征重心 (μ, Σ) 缓存到内存
- 新用户输入时进行"指纹快速比对"
- 命中缓存直接秒出报告

Version: 1.0
Compliance: FDS-LKV V1.0
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class CensusCache:
    """
    海选结果全息缓存
    
    缓存结构：
    - pattern_id -> {
        "mean_vector": [E, O, M, S, R],
        "covariance": [[...]],
        "sample_count": N,
        "abundance": float,
        "sample_ids": [uid1, uid2, ...],
        "cached_at": timestamp
      }
    """
    
    def __init__(self, cache_dir: str = None):
        """
        初始化缓存
        
        Args:
            cache_dir: 缓存目录（None 则使用内存缓存）
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._memory_cache: Dict[str, Dict] = {}
        self._load_persisted_cache()
    
    def _load_persisted_cache(self):
        """加载持久化缓存"""
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        pattern_id = data.get("pattern_id")
                        if pattern_id:
                            self._memory_cache[pattern_id] = data
                            logger.debug(f"加载缓存: {pattern_id}")
                except Exception as e:
                    logger.warning(f"缓存加载失败: {cache_file}: {e}")
    
    def cache_census_result(
        self, 
        pattern_id: str, 
        samples: List[Dict],
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        缓存海选结果
        
        Args:
            pattern_id: 格局 ID
            samples: 海选样本列表 [{"uid": ..., "tensor": {...}}, ...]
            metadata: 额外元数据
            
        Returns:
            缓存摘要
        """
        if not samples:
            return {"cached": False, "reason": "空样本集"}
        
        # 提取张量
        tensors = []
        sample_ids = []
        
        for sample in samples:
            tensor = sample.get("tensor", {})
            if tensor:
                tensors.append([
                    tensor.get("E", 0),
                    tensor.get("O", 0),
                    tensor.get("M", 0),
                    tensor.get("S", 0),
                    tensor.get("R", 0)
                ])
                sample_ids.append(sample.get("uid"))
        
        if not tensors:
            return {"cached": False, "reason": "无有效张量"}
        
        # 计算特征重心
        tensor_array = np.array(tensors)
        mean_vector = np.mean(tensor_array, axis=0).tolist()
        
        # 计算协方差（如果样本足够）
        if len(tensors) >= 5:
            covariance = np.cov(tensor_array.T).tolist()
        else:
            covariance = np.eye(5).tolist()
        
        # 构建缓存对象
        cache_obj = {
            "pattern_id": pattern_id,
            "mean_vector": mean_vector,
            "covariance": covariance,
            "sample_count": len(sample_ids),
            "abundance": len(sample_ids) / 518400,
            "sample_ids": sample_ids[:1000],  # 只存前 1000 个 ID
            "cached_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # 写入内存
        self._memory_cache[pattern_id] = cache_obj
        
        # 持久化（可选）
        if self.cache_dir:
            self._persist_cache(pattern_id, cache_obj)
        
        logger.info(f"✅ 缓存完成: {pattern_id} ({len(sample_ids)} 样本, μ={mean_vector[:3]}...)")
        
        return {
            "cached": True,
            "pattern_id": pattern_id,
            "sample_count": len(sample_ids),
            "mean_vector": mean_vector
        }
    
    def _persist_cache(self, pattern_id: str, cache_obj: Dict):
        """持久化缓存到磁盘"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"{pattern_id}.cache"
        with open(cache_file, 'w') as f:
            json.dump(cache_obj, f, ensure_ascii=False, indent=2)
    
    def get_cached_manifold(self, pattern_id: str) -> Optional[Dict]:
        """获取缓存的流形特征"""
        return self._memory_cache.get(pattern_id)
    
    def fingerprint_match(
        self, 
        tensor_5d: List[float],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        指纹快速比对
        
        计算输入张量与所有缓存流形的距离，返回最相似的 Top K
        
        Args:
            tensor_5d: 输入八字的 5D 张量
            top_k: 返回数量
            
        Returns:
            匹配结果列表 [{pattern_id, distance, similarity, ...}]
        """
        if not self._memory_cache:
            return []
        
        input_tensor = np.array(tensor_5d)
        matches = []
        
        for pattern_id, cache_obj in self._memory_cache.items():
            mean = np.array(cache_obj["mean_vector"])
            cov = np.array(cache_obj["covariance"])
            
            # 计算马氏距离
            try:
                diff = input_tensor - mean
                inv_cov = np.linalg.inv(cov)
                m_dist = float(np.sqrt(np.dot(np.dot(diff, inv_cov), diff)))
            except:
                # 协方差矩阵不可逆时使用欧氏距离
                m_dist = float(np.linalg.norm(input_tensor - mean))
            
            # 计算余弦相似度
            cos_sim = float(np.dot(input_tensor, mean) / (
                np.linalg.norm(input_tensor) * np.linalg.norm(mean) + 1e-10
            ))
            
            matches.append({
                "pattern_id": pattern_id,
                "pattern_name": cache_obj.get("metadata", {}).get("name", pattern_id),
                "mahalanobis_distance": m_dist,
                "cosine_similarity": cos_sim,
                "sample_count": cache_obj["sample_count"],
                "abundance": cache_obj["abundance"]
            })
        
        # 按马氏距离排序
        matches.sort(key=lambda x: x["mahalanobis_distance"])
        
        return matches[:top_k]
    
    def instant_predict(
        self, 
        tensor_5d: List[float],
        threshold: float = 2.5
    ) -> Dict[str, Any]:
        """
        毫秒级瞬时预测
        
        通过缓存直接判定，无需重新海选
        
        Args:
            tensor_5d: 输入八字的 5D 张量
            threshold: 入格阈值
            
        Returns:
            预测结果
        """
        import time
        start = time.perf_counter()
        
        # 指纹比对
        matches = self.fingerprint_match(tensor_5d, top_k=3)
        
        if not matches:
            return {
                "success": False,
                "reason": "缓存为空",
                "latency_ms": (time.perf_counter() - start) * 1000
            }
        
        # 取最佳匹配
        best = matches[0]
        
        # 判定
        if best["mahalanobis_distance"] < threshold:
            verdict = "STANDARD_MATCH"
            confidence = min(0.95, best["cosine_similarity"])
        elif best["mahalanobis_distance"] < threshold * 1.5:
            verdict = "MARGINAL_MATCH"
            confidence = 0.6
        else:
            verdict = "NO_MATCH"
            confidence = 0.3
        
        latency = (time.perf_counter() - start) * 1000
        
        return {
            "success": True,
            "best_match": best,
            "all_matches": matches,
            "verdict": verdict,
            "confidence": confidence,
            "latency_ms": latency,
            "cache_hit": True
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_samples = sum(c["sample_count"] for c in self._memory_cache.values())
        return {
            "cached_patterns": len(self._memory_cache),
            "total_samples": total_samples,
            "patterns": list(self._memory_cache.keys())
        }


# 全局单例
_census_cache: Optional[CensusCache] = None


def get_census_cache() -> CensusCache:
    """获取 CensusCache 单例"""
    global _census_cache
    if _census_cache is None:
        _census_cache = CensusCache()
    return _census_cache


# ============================================================
# 预测流程整合
# ============================================================

class FastPredictor:
    """
    快速预测器
    
    整合 LKV + FDS + Cache 的完整预测流程
    
    路径策略：
    - Green Path (D_M < 2.0): 信任缓存，秒出报告
    - Yellow Path (2.0 <= D_M < 3.5): 缓存 + LKV 深度审计
    - Red Path (D_M >= 3.5): 启动奇点溯源
    """
    
    # 二次穿透阈值
    GREEN_THRESHOLD = 2.0   # 信任缓存
    YELLOW_THRESHOLD = 3.5  # 深度审计
    
    def __init__(self):
        self.cache = get_census_cache()
        self._protocol_checker = None
        self._report_generator = None
        self._vault_manager = None
    
    def predict(
        self, 
        bazi: Dict,
        tensor_5d: List[float],
        use_cache: bool = True,
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        完整预测流程（带语义勋章）
        """
        import time
        start = time.perf_counter()
        
        if use_cache:
            cache_result = self.cache.instant_predict(tensor_5d)
            
            if cache_result["success"]:
                best = cache_result["best_match"]
                m_dist = best["mahalanobis_distance"]
                
                # 路径判定
                if m_dist < self.GREEN_THRESHOLD:
                    path = "GREEN"
                elif m_dist < self.YELLOW_THRESHOLD:
                    path = "YELLOW"
                else:
                    path = "RED"
                
                # 逻辑审计
                logic_result = self._check_logic(bazi, best["pattern_id"])
                dual_match = logic_result["passed"] and cache_result["verdict"] == "STANDARD_MATCH"
                
                result = {
                    "method": "CACHE_HIT",
                    "path": path,
                    "latency_ms": (time.perf_counter() - start) * 1000,
                    "pattern_id": best["pattern_id"],
                    "pattern_name": best["pattern_name"],
                    "mahalanobis_distance": m_dist,
                    "physics_verdict": cache_result["verdict"],
                    "logic_verdict": "PASSED" if logic_result["passed"] else "FAILED",
                    "confidence": cache_result["confidence"],
                    "dual_match": dual_match
                }
                
                if generate_report:
                    result["report"] = self._generate_report(tensor_5d, best, logic_result, path)
                
                return result
        
        return self._full_predict(bazi, tensor_5d, generate_report)
    
    def _check_logic(self, bazi: Dict, pattern_id: str) -> Dict:
        if self._protocol_checker is None:
            from core.protocol_checker import get_protocol_checker
            self._protocol_checker = get_protocol_checker()
        return self._protocol_checker.check_bazi(bazi, pattern_id)
    
    def _generate_report(self, tensor: List[float], match: Dict, logic: Dict, path: str) -> str:
        E, O, M, S, R = tensor
        path_desc = {"GREEN": "✅ 标准匹配", "YELLOW": "⚠️ 边缘态", "RED": "🔴 异常态"}.get(path, "?")
        
        return f"""【QGA-VV 审计报告】
格局: {match['pattern_id']} ({match['pattern_name']})
判定: {path_desc} ({path} Path)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【物理态】
E={E:.3f} | O={O:.3f} | M={M:.3f} | S={S:.3f} | R={R:.3f}
马氏距离: {match['mahalanobis_distance']:.4f}

【逻辑审计】
状态: {'✅ 通过' if logic['passed'] else '❌ 未通过'}
{''.join(f'  {d}' + chr(10) for d in logic.get('details', [])[:2])}
【双轨验证】
{'✅ 通过' if logic['passed'] else '⚠️ 仅物理命中'}
置信度: {match.get('cosine_similarity', 0):.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    def _full_predict(self, bazi: Dict, tensor_5d: List[float], generate_report: bool) -> Dict:
        return {"method": "FULL_COMPUTE", "message": "需要执行完整预测流程"}


def get_fast_predictor() -> FastPredictor:
    return FastPredictor()

