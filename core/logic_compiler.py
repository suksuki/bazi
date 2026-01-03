"""
LKV-to-FDS 逻辑编译器 (Logic Compiler)
=====================================
将 LKV 中的古典逻辑协议编译为 FDS 可执行的海选代码

架构定位：
- LKV: 逻辑指挥官（提供规则）
- FDS: 执行工兵（全量扫描）

Version: 1.0
Compliance: FDS-LKV-LOGIC V1.0
"""

import logging
from typing import Dict, List, Any, Callable, Optional

logger = logging.getLogger(__name__)


# 导入协议
from core.protocol_checker import LOGIC_PROTOCOLS, YANG_REN_MAP


class LogicCompiler:
    """
    LKV-to-FDS 逻辑编译器
    
    将知识库中的 JSON 协议转换为可执行的 Python 过滤函数
    """
    
    def __init__(self):
        self.protocols = LOGIC_PROTOCOLS
        self._compiled_filters: Dict[str, Callable] = {}
    
    def compile(self, pattern_id: str) -> Callable:
        """
        编译指定格局的过滤函数
        
        Args:
            pattern_id: 格局 ID (支持 A-01 或 A-01@子 格式)
            
        Returns:
            可执行的过滤函数 (bazi: Dict) -> bool
        """
        if pattern_id in self._compiled_filters:
            return self._compiled_filters[pattern_id]
        
        # 解析动态 ID
        base_id = pattern_id.split("@")[0]
        target_branch = pattern_id.split("@")[1] if "@" in pattern_id else None
        
        # 0. 检查是否存在矩阵重写 (Matrix Override)
        # 解决相变干扰或丰度异常
        if pattern_id in self.MATRIX_OVERRIDES:
            override_logic = self.MATRIX_OVERRIDES[pattern_id]
            
            def override_filter(bazi: Dict) -> bool:
                # 必须满足地支条件
                if target_branch and bazi.get("month_branch") != target_branch:
                    return False
                # 执行重写逻辑
                return override_logic(bazi, self)
                
            override_filter.__name__ = f"filter_{pattern_id.replace('-', '_').replace('@', '_')}_OVERRIDE"
            override_filter.__doc__ = f"LKV 矩阵重写: {pattern_id}"
            self._compiled_filters[pattern_id] = override_filter
            logger.info(f"🔧 应用矩阵重写: {pattern_id}")
            return override_filter

        if base_id not in self.protocols:
            raise ValueError(f"未知格局协议: {base_id}")
        
        protocol = self.protocols[base_id]
        
        # 动态生成过滤函数
        def compiled_filter(bazi: Dict) -> bool:
            # 1. 如果指定了月令地支 (Sub-Pattern)，优先检查
            if target_branch:
                if bazi.get("month_branch") != target_branch:
                    return False
            
            # 2. 执行基础协议检查
            return self._execute_protocol(bazi, protocol)
        
        # 添加元数据
        compiled_filter.__name__ = f"filter_{pattern_id.replace('-', '_').replace('@', '_')}"
        sub_info = f" [Month: {target_branch}]" if target_branch else ""
        compiled_filter.__doc__ = f"编译自 LKV 协议: {protocol['name']}{sub_info}"
        
        self._compiled_filters[pattern_id] = compiled_filter
        logger.info(f"✅ 编译完成: {pattern_id} ({protocol['name']}{sub_info})")
        
        return compiled_filter

    # ============================================================
    # 矩阵重写 (Matrix Overrides)
    # 针对物理异象的手术刀式修正
    # ============================================================
    
    def _override_d02_wu(bazi: Dict, compiler) -> bool:
        """
        [Ghost Recovery] D-02@午 (偏财格@午)
        午月火旺，金(财)易被克死。
        Strategy: Relaxed. Allow Pian Cai in stems + generic Wealth/Power support.
        """
        stems = bazi.get("stems", [])
        
        # DEBUG: Check what stems we are seeing for Wu month
        # print(f"DEBUG D-02@Wu: {bazi}") 
        
        # 核心：必须透偏财
        if "pian_cai" not in stems and "zheng_cai" not in stems:
            return False
            
        # Relaxed - just check it exists. 
        # In mock data, maybe `rob_count` is often high?
        
        # 补偿：可以是七杀格兼财 (火生土食伤生财 or 火克金?)
        # 只要不是比劫夺财即可
        rob_count = stems.count('bi_jian') + stems.count('jie_cai')
        if rob_count > 1: # 稍微严一点，因为失去了月令支持
            return False
            
        return True

    def _override_d01_xu(bazi: Dict, compiler) -> bool:
        """
        [Dehydration] D-01@戌 (正财格@戌)
        戌月土重，易混杂比劫或印星。
        策略：强制要求财星双透或有强根，且严禁比劫混杂。
        """
        stems = bazi.get("stems", [])
        
        # F1: 必须透正财
        if "zheng_cai" not in stems:
            return False
            
        # F2: 丰度压降 - 严禁比劫 (Rob wealth count > 1 即杀)
        rob_count = stems.count('bi_jian') + stems.count('jie_cai')
        if rob_count >= 1: # 严格脱水
            return False
            
        # F3: 必须有官杀护财 (增强物理稳定性)
        has_protection = any(s in stems for s in ['zheng_guan', 'qi_sha'])
        if not has_protection:
            return False
            
        return True

    MATRIX_OVERRIDES = {
        "D-02@午": _override_d02_wu,
        "D-01@戌": _override_d01_xu
    }
    
    def compile_all(self) -> Dict[str, Callable]:
        """编译所有格局的过滤函数"""
        for pattern_id in self.protocols:
            self.compile(pattern_id)
        return self._compiled_filters
    
    def _execute_protocol(self, bazi: Dict, protocol: Dict) -> bool:
        """执行协议检查"""
        # 1. 强制条件必须全部满足
        for rule in protocol.get("mandatory", []):
            if not self._eval_rule(bazi, rule):
                return False
        
        # 2. 可选条件至少满足一个（如果有的话）
        optional = protocol.get("optional_or", [])
        if optional:
            if not any(self._eval_rule(bazi, r) for r in optional):
                return False
        
        # 3. 禁忌条件不能触发
        for rule in protocol.get("forbidden", []):
            if self._eval_forbidden(bazi, rule):
                return False
        
        return True
    
    def _eval_rule(self, bazi: Dict, rule: str) -> bool:
        """评估单条规则"""
        stems = bazi.get("stems", [])
        month_main = bazi.get("month_main", "")
        day_master = bazi.get("day_master", "")
        month_branch = bazi.get("month_branch", "")
        
        # 规则解析
        if "stems.contains" in rule:
            shen = rule.split("'")[1] if "'" in rule else ""
            return shen in stems
        elif "month_main ==" in rule:
            expected = rule.split("'")[1] if "'" in rule else ""
            return month_main == expected
        elif "is_yang_stem" in rule:
            return day_master in ['甲', '丙', '戊', '庚', '壬']
        elif "is_sheep_blade" in rule:
            expected = YANG_REN_MAP.get(day_master)
            return month_branch == expected
        
        return False
    
    def _eval_forbidden(self, bazi: Dict, rule: str) -> bool:
        """评估禁忌规则"""
        stems = bazi.get("stems", [])
        
        if "枭神夺食" in rule or "pian_yin without pian_cai" in rule:
            return "pian_yin" in stems and "pian_cai" not in stems
        elif "伤官见官" in rule or "zheng_guan without zheng_yin" in rule:
            return "zheng_guan" in stems and "zheng_yin" not in stems
        elif "财多破印" in rule or "wealth_count > 2" in rule:
            wealth_count = stems.count("zheng_cai") + stems.count("pian_cai")
            return wealth_count > 2
        elif "比劫争财" in rule or "rob_count > 2" in rule:
            rob_count = stems.count("bi_jian") + stems.count("jie_cai")
            if "without protection" in rule or "无制" in rule:
                has_protection = "zheng_guan" in stems or "qi_sha" in stems
                return rob_count > 2 and not has_protection
            return rob_count > 2
        
        return False
    
    def get_protocol_sql(self, pattern_id: str) -> str:
        """
        生成伪 SQL 查询（用于调试和文档）
        
        Args:
            pattern_id: 格局 ID
            
        Returns:
            伪 SQL 字符串
        """
        if pattern_id not in self.protocols:
            return f"-- 未知格局: {pattern_id}"
        
        protocol = self.protocols[pattern_id]
        
        conditions = []
        for rule in protocol.get("mandatory", []):
            conditions.append(f"({rule})")
        
        optional = protocol.get("optional_or", [])
        if optional:
            or_clause = " OR ".join(f"({r})" for r in optional)
            conditions.append(f"({or_clause})")
        
        for rule in protocol.get("forbidden", []):
            conditions.append(f"NOT ({rule})")
        
        where_clause = " AND ".join(conditions)
        
        return f"""
-- LKV-Compiled SQL for {pattern_id} ({protocol['name']})
-- Semantic Reference: {protocol.get('semantic_ref', 'N/A')}

SELECT uid, tensor 
FROM holographic_universe_518k
WHERE {where_clause}
"""


class KnowledgeDrivenCensus:
    """
    知识驱动型海选引擎
    
    实现 LKV 驱动 + FDS 执行的协同架构
    """
    
    def __init__(self):
        self.compiler = LogicCompiler()
        self._census_engine = None
    
    def _get_census_engine(self):
        """延迟加载 CensusEngine"""
        if self._census_engine is None:
            from core.census_engine import ClassicalCensusEngine
            self._census_engine = ClassicalCensusEngine()
        return self._census_engine
    
    def request_census(
        self, 
        pattern_id: str,
        limit: int = None,
        include_tensor: bool = True
    ) -> Dict[str, Any]:
        """
        LKV 提交海选申请
        
        流程:
        1. LKV 编译协议 -> 生成过滤函数
        2. FDS 执行全量扫描 -> 返回样本集
        3. 返回结果 + 统计
        
        Args:
            pattern_id: 格局 ID
            limit: 扫描限制
            include_tensor: 是否包含张量
            
        Returns:
            海选结果
        """
        logger.info(f"📜 LKV 收到海选申请: {pattern_id}")
        
        # 1. 编译协议
        filter_func = self.compiler.compile(pattern_id)
        logger.info(f"⚙️ 协议编译完成")
        
        # 2. 调用 FDS 执行
        engine = self._get_census_engine()
        logger.info(f"🔍 FDS 开始全量扫描...")
        
        result = engine.census(pattern_id, limit=limit, include_tensor=include_tensor)
        
        # 3. 添加 LKV 元数据
        protocol = self.compiler.protocols.get(pattern_id, {})
        result["lkv_metadata"] = {
            "pattern_name": protocol.get("name", ""),
            "category": protocol.get("category", ""),
            "semantic_ref": protocol.get("semantic_ref", ""),
            "compiled_sql": self.compiler.get_protocol_sql(pattern_id)
        }
        
        logger.info(f"✅ 海选完成: {result['matched_count']} 样本")
        
        return result
    
    def audit_samples(
        self, 
        samples: List[Dict], 
        pattern_id: str,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        LKV 抽检样本合规性
        
        Args:
            samples: FDS 返回的样本
            pattern_id: 格局 ID
            sample_size: 抽检数量
            
        Returns:
            审计结果
        """
        from core.protocol_checker import get_protocol_checker
        checker = get_protocol_checker()
        
        # 抽样
        audit_samples = samples[:sample_size]
        
        passed = 0
        failed = 0
        
        for sample in audit_samples:
            # 模拟八字结构（实际需要从样本提取）
            bazi = self._sample_to_bazi(sample)
            result = checker.check_bazi(bazi, pattern_id)
            if result["passed"]:
                passed += 1
            else:
                failed += 1
        
        compliance_rate = passed / len(audit_samples) if audit_samples else 0
        
        return {
            "pattern_id": pattern_id,
            "audited_count": len(audit_samples),
            "passed": passed,
            "failed": failed,
            "compliance_rate": compliance_rate,
            "verdict": "合规" if compliance_rate > 0.95 else "需复查"
        }
    
    def _sample_to_bazi(self, sample: Dict) -> Dict:
        """将样本转换为八字结构（简化演示）"""
        uid = sample.get("uid", 0)
        tensor = sample.get("tensor", {})
        
        day_masters = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        month_branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        return {
            "uid": uid,
            "day_master": day_masters[uid % 10],
            "month_branch": month_branches[uid % 12],
            "month_main": "zheng_guan" if tensor.get("O", 0) > 0.5 else "pian_cai",
            "stems": ["qi_sha"] if tensor.get("O", 0) > 0.4 else ["zheng_cai"]
        }


# 全局单例
_knowledge_census: Optional[KnowledgeDrivenCensus] = None


def get_knowledge_census() -> KnowledgeDrivenCensus:
    """获取 KnowledgeDrivenCensus 单例"""
    global _knowledge_census
    if _knowledge_census is None:
        _knowledge_census = KnowledgeDrivenCensus()
    return _knowledge_census
