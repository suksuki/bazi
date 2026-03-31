"""
Protocol Checker - 古典逻辑协议审计器
====================================
实现"逻辑即代码"的双重比对闭环

Version: 1.0
Compliance: FDS-LKV-LOGIC V1.0
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# 古典格局逻辑协议包 (Logic-as-Code)
# ============================================================
LOGIC_PROTOCOLS = {
    "A-01": {
        "name": "正官格",
        "category": "POWER",
        "mandatory": ["month_main == 'zheng_guan'", "stems.contains('zheng_guan')"],
        "optional_or": [],
        "forbidden": ["stems.contains('shang_guan')", "stems.contains('qi_sha')"],
        "semantic_ref": "AXIOM_A-01"
    },
    "A-02": {
        "name": "七杀格",
        "category": "POWER",
        "mandatory": ["month_main == 'qi_sha'", "stems.contains('qi_sha')"],
        "optional_or": ["stems.contains('shi_shen')", "stems.contains('zheng_yin')", "stems.contains('pian_yin')"],
        "forbidden": [],
        "semantic_ref": "AXIOM_A-02"
    },
    "A-03": {
        "name": "羊刃格",
        "category": "POWER",
        "mandatory": ["is_yang_stem(day_master)", "is_sheep_blade(day_master, month_branch)"],
        "optional_or": ["stems.contains('qi_sha')", "stems.contains('zheng_guan')"],
        "forbidden": ["wealth_count > 2"],
        "semantic_ref": "AXIOM_A-03"
    },
    "A-04": {
        "name": "伤官伤尽格",
        "category": "REBEL",
        "mandatory": ["month_main == 'shang_guan'", "stems.contains('shang_guan')"],
        "optional_or": ["stems.contains('zheng_cai')", "stems.contains('pian_cai')"],
        "forbidden": ["stems.contains('zheng_guan')"],
        "semantic_ref": "AXIOM_A-04"
    },
    "B-01": {
        "name": "食神格",
        "category": "OUTPUT",
        "mandatory": ["month_main == 'shi_shen'"],
        "optional_or": ["stems.contains('zheng_cai')", "stems.contains('pian_cai')"],
        "forbidden": ["枭神夺食: pian_yin without pian_cai"],
        "semantic_ref": "AXIOM_B-01"
    },
    "B-02": {
        "name": "伤官格",
        "category": "OUTPUT",
        "mandatory": ["month_main == 'shang_guan'", "stems.contains('shang_guan')"],
        "optional_or": ["stems.contains('zheng_cai')", "stems.contains('pian_cai')", "stems.contains('zheng_yin')"],
        "forbidden": ["伤官见官: zheng_guan without zheng_yin"],
        "semantic_ref": "AXIOM_B-02"
    },
    "C-01": {
        "name": "正印格",
        "category": "RESOURCE",
        "mandatory": ["month_main == 'zheng_yin'", "stems.contains('zheng_yin')"],
        "optional_or": ["stems.contains('zheng_guan')", "stems.contains('qi_sha')"],
        "forbidden": ["财多破印: wealth_count > 2"],
        "semantic_ref": "AXIOM_C-01"
    },
    "C-02": {
        "name": "偏印格",
        "category": "RESOURCE",
        "mandatory": ["month_main == 'pian_yin'", "stems.contains('pian_yin')"],
        "optional_or": [],
        "forbidden": ["枭神夺食: shi_shen without pian_cai"],
        "semantic_ref": "AXIOM_C-02"
    },
    "D-01": {
        "name": "正财格",
        "category": "WEALTH",
        "mandatory": ["month_main == 'zheng_cai'", "stems.contains('zheng_cai')"],
        "optional_or": ["stems.contains('shi_shen')", "stems.contains('zheng_guan')"],
        "forbidden": ["比劫争财: rob_count > 2"],
        "semantic_ref": "AXIOM_D-01"
    },
    "D-02": {
        "name": "偏财格",
        "category": "WEALTH",
        "mandatory": ["month_main == 'pian_cai'", "stems.contains('pian_cai')"],
        "optional_or": ["stems.contains('zheng_guan')", "stems.contains('qi_sha')"],
        "forbidden": ["比劫争财无制: rob_count > 2 without protection"],
        "semantic_ref": "AXIOM_D-02"
    }
}

# 羊刃对照表
YANG_REN_MAP = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}


class ProtocolChecker:
    """
    古典逻辑协议审计器
    
    实现双重比对闭环：
    1. 逻辑审计：检查干支是否命中协议规则
    2. 物理比对：结合 FDS 的马氏距离判定
    3. 冲突判定：综合输出审计结论
    """
    
    def __init__(self):
        self.protocols = LOGIC_PROTOCOLS
    
    def check_bazi(self, bazi: Dict, pattern_id: str) -> Dict[str, Any]:
        """
        检查八字是否符合指定格局的古典逻辑
        
        Args:
            bazi: 八字数据 (day_master, month_branch, month_main, stems)
            pattern_id: 格局 ID
            
        Returns:
            审计结果
        """
        if pattern_id not in self.protocols:
            return {"passed": False, "reason": f"未知格局: {pattern_id}"}
        
        protocol = self.protocols[pattern_id]
        result = {
            "pattern_id": pattern_id,
            "pattern_name": protocol["name"],
            "mandatory_passed": True,
            "optional_passed": True,
            "forbidden_triggered": False,
            "details": []
        }
        
        # 1. 检查 mandatory 规则
        for rule in protocol["mandatory"]:
            passed = self._eval_rule(bazi, rule)
            if not passed:
                result["mandatory_passed"] = False
                result["details"].append(f"❌ 必要条件未满足: {rule}")
        
        # 2. 检查 optional_or 规则
        if protocol["optional_or"]:
            any_passed = any(self._eval_rule(bazi, r) for r in protocol["optional_or"])
            if not any_passed:
                result["optional_passed"] = False
                result["details"].append("⚠️ 可选条件均未满足")
        
        # 3. 检查 forbidden 规则
        for rule in protocol["forbidden"]:
            triggered = self._eval_forbidden(bazi, rule)
            if triggered:
                result["forbidden_triggered"] = True
                result["details"].append(f"🚫 禁忌触发: {rule}")
        
        # 综合判定
        result["passed"] = (
            result["mandatory_passed"] and 
            result["optional_passed"] and 
            not result["forbidden_triggered"]
        )
        
        return result
    
    def _eval_rule(self, bazi: Dict, rule: str) -> bool:
        """评估单条规则"""
        stems = bazi.get("stems", [])
        month_main = bazi.get("month_main", "")
        day_master = bazi.get("day_master", "")
        month_branch = bazi.get("month_branch", "")
        
        # 解析规则
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
        
        if "枭神夺食" in rule:
            return "pian_yin" in stems and "pian_cai" not in stems
        elif "伤官见官" in rule:
            return "zheng_guan" in stems and "zheng_yin" not in stems
        elif "财多破印" in rule:
            wealth_count = stems.count("zheng_cai") + stems.count("pian_cai")
            return wealth_count > 2
        elif "比劫争财" in rule:
            rob_count = stems.count("bi_jian") + stems.count("jie_cai")
            if "without protection" in rule or "无制" in rule:
                has_protection = "zheng_guan" in stems or "qi_sha" in stems
                return rob_count > 2 and not has_protection
            return rob_count > 2
        
        return False
    
    def dual_match(
        self, 
        bazi: Dict, 
        pattern_id: str, 
        mahalanobis_distance: float,
        threshold: float = 2.5
    ) -> Dict[str, Any]:
        """
        双重比对闭环
        
        Args:
            bazi: 八字数据
            pattern_id: 格局 ID
            mahalanobis_distance: 马氏距离
            threshold: 物理稳态阈值
            
        Returns:
            综合审计结果
        """
        # 1. 逻辑审计
        logic_result = self.check_bazi(bazi, pattern_id)
        logic_passed = logic_result["passed"]
        
        # 2. 物理比对
        physics_stable = mahalanobis_distance < threshold
        
        # 3. 冲突判定
        if logic_passed and physics_stable:
            conclusion = "STANDARD_MATCH"
            verdict = "标准成格"
        elif logic_passed and not physics_stable:
            conclusion = "NOMINAL_ONLY"
            verdict = "有名无实/格局破损"
        elif not logic_passed and physics_stable:
            conclusion = "ANOMALY_PATH"
            verdict = "异路功名/奇点坍缩"
        else:
            conclusion = "NO_MATCH"
            verdict = "不入此格"
        
        return {
            "pattern_id": pattern_id,
            "pattern_name": self.protocols.get(pattern_id, {}).get("name", ""),
            "logic_audit": logic_result,
            "physics_audit": {
                "mahalanobis_distance": mahalanobis_distance,
                "threshold": threshold,
                "stable": physics_stable
            },
            "conclusion": conclusion,
            "verdict": verdict
        }
    
    def generate_audit_report(self, dual_result: Dict) -> str:
        """生成审计报告"""
        logic = dual_result["logic_audit"]
        physics = dual_result["physics_audit"]
        
        report = f"""【古典逻辑审计报告】
格局: {dual_result['pattern_id']} ({dual_result['pattern_name']})
判定: {dual_result['verdict']}

【逻辑层】
必要条件: {'✅ 通过' if logic['mandatory_passed'] else '❌ 未通过'}
可选条件: {'✅ 通过' if logic['optional_passed'] else '⚠️ 未满足'}
禁忌检测: {'🚫 触发' if logic['forbidden_triggered'] else '✅ 无'}
"""
        
        if logic['details']:
            report += "\n详情:\n" + "\n".join(f"  {d}" for d in logic['details'])
        
        report += f"""

【物理层】
马氏距离: {physics['mahalanobis_distance']:.4f}
稳态阈值: {physics['threshold']:.2f}
稳态判定: {'✅ 稳定' if physics['stable'] else '⚠️ 偏离'}

【综合结论】
{dual_result['conclusion']}: {dual_result['verdict']}
"""
        return report


# 全局单例
_protocol_checker: Optional[ProtocolChecker] = None


def get_protocol_checker() -> ProtocolChecker:
    """获取 ProtocolChecker 单例"""
    global _protocol_checker
    if _protocol_checker is None:
        _protocol_checker = ProtocolChecker()
    return _protocol_checker
