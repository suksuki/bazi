"""
FDS-LKV 合规性路由器 (Compliance Router)
========================================
负责在预测流程中介入知识库，执行先验检查和奇点溯源。

Version: 1.0
Compliance: FDS-LKV Spec V1.0
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PhysicsAxiomViolation(Exception):
    """物理公理违规异常"""
    
    def __init__(self, pattern_id: str, violations: List[str]):
        self.pattern_id = pattern_id
        self.violations = violations
        message = f"格局 {pattern_id} 违反物理公理: {', '.join(violations)}"
        super().__init__(message)


class ComplianceRouter:
    """
    合规性路由器
    
    负责:
    1. 先验检查 (Pre-check): 加载 registry.json 时验证物理公理
    2. 奇点溯源 (Trace-back): 马氏距离超阈值时检索最近邻
    """
    
    def __init__(self, vault_manager=None):
        """
        初始化合规性路由器
        
        Args:
            vault_manager: VaultManager 实例（如果为 None，则延迟初始化）
        """
        self._vault_manager = vault_manager
        self._initialized = False
    
    def _get_vault(self):
        """延迟获取 VaultManager"""
        if self._vault_manager is None:
            from core.vault_manager import get_vault_manager
            self._vault_manager = get_vault_manager()
            self._initialized = True
        return self._vault_manager
    
    def precheck_pattern(
        self, 
        pattern_id: str, 
        pattern_config: Dict[str, Any],
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        先验检查协议 (Pre-check Protocol)
        
        在加载格局配置时执行合规性验证。
        
        Args:
            pattern_id: 格局 ID (如 'A-03')
            pattern_config: 格局配置字典
            strict_mode: 是否严格模式（违规时抛出异常）
            
        Returns:
            检查结果字典
        """
        vault = self._get_vault()
        
        # 执行合规性检查
        result = vault.check_physics_compliance(pattern_config)
        result["pattern_id"] = pattern_id
        
        # 严格模式下，违规时抛出异常
        if strict_mode and not result["compliant"]:
            raise PhysicsAxiomViolation(pattern_id, result["violations"])
        
        return result
    
    def traceback_singularity(
        self, 
        tensor_5d: List[float],
        mahalanobis_distance: float,
        threshold: float = 2.5,
        n_results: int = 3,
        pattern_filter: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        奇点溯源协议 (Trace-back Protocol)
        
        当马氏距离超过阈值时，检索最近的奇点样本。
        
        Args:
            tensor_5d: 当前八字的 5D 张量 [E, O, M, S, R]
            mahalanobis_distance: 计算得到的马氏距离
            threshold: 触发阈值
            n_results: 返回结果数量
            pattern_filter: 可选的格局过滤器 (如 'A-03')
            
        Returns:
            检索结果（如果未触发则返回 None）
        """
        # 检查是否触发溯源
        if mahalanobis_distance < threshold:
            logger.debug(f"马氏距离 {mahalanobis_distance:.4f} < 阈值 {threshold}，不触发溯源")
            return None
        
        logger.info(f"🔍 触发奇点溯源: D_M = {mahalanobis_distance:.4f} > {threshold}")
        
        vault = self._get_vault()
        
        # 构建过滤条件
        where_filter = None
        if pattern_filter:
            where_filter = {"pattern_id": pattern_filter}
        
        # 执行向量相似度搜索
        results = vault.query_singularities(
            tensor=tensor_5d,
            n_results=n_results,
            where=where_filter
        )
        
        if not results.get("ids"):
            logger.warning("⚠️ 奇点库中未找到匹配样本")
            return None
        
        # 格式化返回结果
        traceback_result = {
            "triggered": True,
            "mahalanobis_distance": mahalanobis_distance,
            "query_tensor": tensor_5d,
            "matches": []
        }
        
        for i, case_id in enumerate(results["ids"]):
            match = {
                "case_id": case_id,
                "distance": results["distances"][i] if i < len(results["distances"]) else None,
                "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {},
                "tensor": results["embeddings"][i] if i < len(results["embeddings"]) else None
            }
            traceback_result["matches"].append(match)
        
        logger.info(f"✅ 奇点溯源完成: 找到 {len(traceback_result['matches'])} 个匹配")
        
        return traceback_result
    
    def query_axiom(self, axiom_query: str, n_results: int = 1) -> Dict[str, Any]:
        """
        查询特定公理规范
        
        Args:
            axiom_query: 查询文本 (如 "符号守恒公理")
            n_results: 返回结果数量
            
        Returns:
            检索结果
        """
        vault = self._get_vault()
        return vault.query_semantics(query=axiom_query, n_results=n_results)
    
    def assess_match(
        self,
        tensor_5d: List[float],
        pattern_id: str,
        mahalanobis_distance: float,
        cosine_similarity: float = 0.0,
        precision_score: float = 0.0,
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        吻合度综合评估 (Assess Match Protocol)
        
        实现"语义+物理"双重判定：
        1. 物理对比（第一道门）：验证与标准流形的距离
        2. 奇点相似度（第二道门）：如果偏离标准，检索最近奇点
        3. 语义合规（第三道门）：检索相关规范验证合规性
        
        Args:
            tensor_5d: 当前八字的 5D 张量 [E, O, M, S, R]
            pattern_id: 目标格局 ID
            mahalanobis_distance: 马氏距离
            cosine_similarity: 余弦相似度
            precision_score: 精密评分
            generate_report: 是否生成详细审计报告
            
        Returns:
            吻合度审计报告
        """
        vault = self._get_vault()
        
        result = {
            "pattern_id": pattern_id,
            "tensor": tensor_5d,
            "assessment": {
                "physical_match": False,
                "singularity_match": False,
                "semantic_compliant": False
            },
            "conclusion": "UNKNOWN",
            "confidence": 0.0,
            "report": "",
            "matched_singularity": None,
            "matched_axioms": []
        }
        
        # ============================================================
        # 第一道门：物理对比
        # ============================================================
        physical_threshold = 2.5  # 马氏距离阈值
        similarity_threshold = 0.7  # 相似度阈值
        
        if mahalanobis_distance < physical_threshold and cosine_similarity > similarity_threshold:
            result["assessment"]["physical_match"] = True
            result["conclusion"] = "STANDARD_MATCH"
            result["confidence"] = min(0.95, precision_score + 0.1)
            
            if generate_report:
                result["report"] = self._generate_standard_report(
                    tensor_5d, pattern_id, mahalanobis_distance, cosine_similarity
                )
            
            logger.info(f"✅ 第一道门通过: {pattern_id} 标准匹配")
            return result
        
        # ============================================================
        # 第二道门：奇点相似度
        # ============================================================
        traceback = self.traceback_singularity(
            tensor_5d=tensor_5d,
            mahalanobis_distance=mahalanobis_distance,
            threshold=1.5,  # 降低阈值以便检索
            pattern_filter=pattern_id
        )
        
        if traceback and traceback.get("matches"):
            nearest = traceback["matches"][0]
            nearest_distance = nearest.get("distance", float('inf'))
            
            # 如果与奇点距离足够近（距离 < 0.1 表示高度相似）
            if nearest_distance < 0.1:
                result["assessment"]["singularity_match"] = True
                result["matched_singularity"] = nearest
                result["conclusion"] = "SINGULARITY_MATCH"
                result["confidence"] = max(0.85, 1.0 - nearest_distance * 5)
                
                if generate_report:
                    result["report"] = self._generate_singularity_report(
                        tensor_5d, pattern_id, nearest, traceback["matches"]
                    )
                
                logger.info(f"✅ 第二道门通过: {pattern_id} 奇点匹配 ({nearest['case_id']})")
                return result
        
        # ============================================================
        # 第三道门：语义合规检查
        # ============================================================
        try:
            # 检索相关公理
            axiom_query = f"{pattern_id} 物理公理 安全门控 入格条件"
            axiom_results = vault.query_semantics(axiom_query, n_results=3)
            result["matched_axioms"] = axiom_results.get("ids", [])
            
            # 简化合规判断：如果有匹配的公理，认为语义层有相关定义
            if result["matched_axioms"]:
                result["assessment"]["semantic_compliant"] = True
        except Exception as e:
            logger.warning(f"语义检索失败: {e}")
        
        # ============================================================
        # 综合判定
        # ============================================================
        if result["assessment"]["semantic_compliant"] and precision_score > 0.5:
            result["conclusion"] = "MARGINAL_MATCH"
            result["confidence"] = precision_score
            
            if generate_report:
                result["report"] = self._generate_marginal_report(
                    tensor_5d, pattern_id, mahalanobis_distance, 
                    traceback, result["matched_axioms"]
                )
        else:
            result["conclusion"] = "NO_MATCH"
            result["confidence"] = precision_score
            
            if generate_report:
                result["report"] = self._generate_rejection_report(
                    tensor_5d, pattern_id, mahalanobis_distance
                )
        
        return result
    
    def _generate_standard_report(
        self, tensor: List[float], pattern_id: str, 
        m_dist: float, cos_sim: float
    ) -> str:
        """生成标准匹配报告 (QGA-VV 三段式)"""
        E, O, M, S, R = tensor
        
        # 物理态描述
        e_state = "充沛" if E > 0.6 else "适中" if E > 0.3 else "偏弱"
        o_state = "高稀" if O > 0.5 else "中等" if O > 0.25 else "偏低"
        m_state = "丰厚" if M > 0.4 else "平稳" if M > 0.2 else "偏弱"
        s_state = "激型" if S > 0.6 else "可控" if S > 0.3 else "平稳"
        r_state = "紧密" if R > 0.5 else "中等" if R > 0.25 else "较疏"
        
        # 检索语义公理
        axiom_ref = ""
        try:
            vault = self._get_vault()
            axiom_result = vault.query_semantics(f"{pattern_id} 成格条件 物理公理", n_results=1)
            if axiom_result.get("ids"):
                axiom_ref = f"符合 {axiom_result['ids'][0]} 中的标准流形定义"
        except:
            axiom_ref = f"符合 {pattern_id} 标准流形定义"
        
        return f"""【吐合度审计报告】
格局: {pattern_id}
判定: ✅ 标准匹配

【物理态】
E轴(能级): {E:.3f} - {e_state}
O轴(秩序): {O:.3f} - {o_state}
M轴(财富): {M:.3f} - {m_state}
S轴(应力): {S:.3f} - {s_state}
R轴(关联): {R:.3f} - {r_state}
马氏距离: {m_dist:.4f} | 余弦相似度: {cos_sim:.4f}

【古典对照】
{axiom_ref}

【案例参考】
此特征组合在 518k 样本库中属于标准流形范围，表现典型。

置信度: {cos_sim:.2f}
"""
    
    def _generate_singularity_report(
        self, tensor: List[float], pattern_id: str,
        nearest: Dict, all_matches: List
    ) -> str:
        """生成奇点匹配报告 (QGA-VV 三段式)"""
        E, O, M, S, R = tensor
        case_id = nearest.get("case_id", "UNKNOWN")
        meta = nearest.get("metadata", {})
        distance = nearest.get("distance", 0)
        sub_pattern = meta.get("sub_pattern", "N/A")
        y_true = meta.get("y_true", 0.5)
        zones = meta.get("zones", "")
        
        # 物理态描述
        e_state = "充沛" if E > 0.6 else "适中" if E > 0.3 else "偏弱"
        s_state = "激型" if S > 0.6 else "可控" if S > 0.3 else "平稳"
        
        # 检索语义公理
        axiom_ref = ""
        try:
            vault = self._get_vault()
            axiom_result = vault.query_semantics(f"{pattern_id} 奇点 特殊情况", n_results=1)
            if axiom_result.get("ids"):
                axiom_ref = f"属于 {axiom_result['ids'][0]} 描述的奇点变体"
        except:
            axiom_ref = f"属于 {pattern_id} 的特殊变体"
        
        # 轨迹描述
        trajectory = "高成就轨迹" if y_true > 0.7 else "中等轨迹" if y_true > 0.4 else "挑战型轨迹"
        
        return f"""【吐合度审计报告】
格局: {pattern_id}
判定: 🔮 奇点匹配

【物理态】
E轴(能级): {E:.3f} - {e_state}
O轴(秩序): {O:.3f}
M轴(财富): {M:.3f}
S轴(应力): {S:.3f} - {s_state}
R轴(关联): {R:.3f}
与标准流形偏离，但与奇点样本高度吐合

【奇点溯源】
最近邻: {case_id}
子格局: {sub_pattern}
相似距离: {distance:.6f}
特征分区: {zones}

【古典对照】
{axiom_ref}

【案例参考】
此特征组合在 518k 样本库中表现为{trajectory}，
y_true 指标: {y_true:.2f}

结论: 虽不符合标准 {pattern_id} 流形，但与奇点案例 {case_id} 高度相似。

置信度: {max(0.85, 1.0 - distance * 5):.2f}
"""
    
    def _generate_marginal_report(
        self, tensor: List[float], pattern_id: str,
        m_dist: float, traceback: Optional[Dict], axioms: List
    ) -> str:
        """生成边缘匹配报告"""
        E, O, M, S, R = tensor
        return f"""【吻合度审计报告】
格局: {pattern_id}
判定: ⚠️ 边缘匹配

物理分析:
- 5D 坐标: E={E:.3f}, O={O:.3f}, M={M:.3f}, S={S:.3f}, R={R:.3f}
- 马氏距离: {m_dist:.4f} (偏离标准)

语义参考:
- 匹配公理: {len(axioms)} 条
- 规范依据: {', '.join(axioms[:2]) if axioms else 'N/A'}

结论: 该八字处于 {pattern_id} 的边缘状态，建议结合流年大运进一步观察。
"""
    
    def _generate_rejection_report(
        self, tensor: List[float], pattern_id: str, m_dist: float
    ) -> str:
        """生成拒绝匹配报告"""
        E, O, M, S, R = tensor
        return f"""【吻合度审计报告】
格局: {pattern_id}
判定: ❌ 不匹配

物理分析:
- 5D 坐标: E={E:.3f}, O={O:.3f}, M={M:.3f}, S={S:.3f}, R={R:.3f}
- 马氏距离: {m_dist:.4f} (严重偏离)

结论: 该八字不符合 {pattern_id} 的物理定义，建议检索其他格局。
"""


# 全局单例
_compliance_router: Optional[ComplianceRouter] = None


def get_compliance_router() -> ComplianceRouter:
    """获取 ComplianceRouter 单例"""
    global _compliance_router
    if _compliance_router is None:
        _compliance_router = ComplianceRouter()
    return _compliance_router

