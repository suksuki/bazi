"""V12 M2.2：语义监军（Semantic Auditor）与自动重试编排。"""

from __future__ import annotations

from typing import Callable, Iterable, List, Literal

from pydantic import BaseModel, Field

from app.logic.brain.psv_engine import PSVSymbol

AuditState = Literal["PASS", "REJECT", "FLAG"]


class AuditResult(BaseModel):
    """叙事-物理一致性审计结果。"""

    model_config = {"extra": "forbid"}

    is_passed: bool
    reason_code: str
    feedback_for_llm: str
    audit_state: AuditState = "PASS"
    matched_rules: List[str] = Field(default_factory=list)
    conflict_excerpt: str = ""


class DissentBlock(BaseModel):
    """自动重试耗尽后的逻辑异议块。"""

    model_config = {"extra": "forbid"}

    block_kind: str = "LOGIC_CONFLICT"
    protocol: str = "logic_integrity_guard.v1"
    severity: str = "blocking"
    reason_code: str = "LIG_RETRY_EXHAUSTED"
    summary: str = ""


class BrainHubRunResult(BaseModel):
    """BrainHub 模拟执行结果。"""

    model_config = {"extra": "forbid"}

    final_narrative: str
    audit: AuditResult
    retry_count: int = 0
    last_auto_retry_prompt: str = ""
    dissent_block: DissentBlock | None = None


def _normalize_text(text: str) -> str:
    return " ".join(str(text or "").strip().lower().split())


def _axis_label(axis: str) -> str:
    return {
        "WEALTH": "财星",
        "OFFICER": "官杀",
        "ELEMENT_BALANCE": "五行平衡",
    }.get(axis, axis)


def _rule_hint_from_evidence(evidence: Iterable[str]) -> str:
    joined = " | ".join([str(x) for x in evidence if isinstance(x, str)])
    if "rule:psv.robber_wealth_pierce_ratio" in joined:
        return "比劫穿透"
    if "rule:psv.element_normalized_spread" in joined:
        return "五行失衡扩散"
    if "rule:psv.l2_primary_with_intention" in joined:
        return "格局主轴与意志定调"
    return "物理证据链"


class SemanticAuditor:
    """
    关键词级轻量审计器：
    - NEG 物理 + 强正叙事 => REJECT
    - POS 物理 + 强负叙事 => REJECT
    - STRONG 偏向 + 轴词缺失 => FLAG
    """

    def __init__(self) -> None:
        self._lexicon = {
            "WEALTH": {
                "positive": ("财星高照", "大发横财", "财运亨通", "爆发", "财源广进", "暴富"),
                "negative": ("破财", "漏财", "亏损", "财务受损", "失财"),
                "axis": ("财", "财富", "财运", "财星"),
            },
            "OFFICER": {
                "positive": ("稳定", "升职", "掌权", "受器重", "仕途顺"),
                "negative": ("官非", "失势", "压力失控", "受罚", "仕途受阻"),
                "axis": ("官", "官杀", "事业", "仕途"),
            },
            "ELEMENT_BALANCE": {
                "positive": ("平衡", "调和", "稳定", "顺畅"),
                "negative": ("剧变", "失衡", "偏枯", "冲突加剧", "失稳"),
                "axis": ("五行", "气场", "平衡", "结构"),
            },
        }

    def audit(self, narrative: str, psv_list: List[PSVSymbol]) -> AuditResult:
        text = _normalize_text(narrative)
        if not text:
            return AuditResult(
                is_passed=False,
                reason_code="LIG_EMPTY_NARRATIVE",
                audit_state="REJECT",
                feedback_for_llm="叙事为空，请基于 PSV 轴向生成可审计结论。",
                matched_rules=["empty.narrative"],
            )

        flag_hits: List[str] = []
        for psv in psv_list:
            axis = str(psv.axis or "").strip().upper()
            terms = self._lexicon.get(axis)
            if not terms:
                continue

            pos_hits = [w for w in terms["positive"] if w in text]
            neg_hits = [w for w in terms["negative"] if w in text]
            axis_hits = [w for w in terms["axis"] if w in text]
            excerpt = ",".join(pos_hits or neg_hits)
            hint = _rule_hint_from_evidence(psv.evidence)
            refs = "; ".join(psv.evidence[:3]) if psv.evidence else "none"
            label = _axis_label(axis)

            if psv.polarity == "STRONG_NEGATIVE" and pos_hits:
                return AuditResult(
                    is_passed=False,
                    audit_state="REJECT",
                    reason_code="LIG_AXIS_POS_MISMATCH",
                    conflict_excerpt=excerpt,
                    matched_rules=[f"{axis}.neg_vs_pos"],
                    feedback_for_llm=(
                        f"[AUTO_RETRY_REQUIRED] 物理轴 {axis}:{psv.polarity} 与叙事强正冲突。"
                        f"冲突词：{excerpt}。证据提示：{hint}。"
                        f"请改写为审慎表达，不得宣称{label}爆发式利好。Evidence Refs: {refs}"
                    ),
                )

            if psv.polarity in ("STRONG_POSITIVE", "MILD_POSITIVE") and neg_hits:
                return AuditResult(
                    is_passed=False,
                    audit_state="REJECT",
                    reason_code="LIG_AXIS_NEG_MISMATCH",
                    conflict_excerpt=excerpt,
                    matched_rules=[f"{axis}.pos_vs_neg"],
                    feedback_for_llm=(
                        f"[AUTO_RETRY_REQUIRED] 物理轴 {axis}:{psv.polarity} 与叙事强负冲突。"
                        f"冲突词：{excerpt}。请修正为与物理方向一致的中性或正向措辞。"
                        f"Evidence Refs: {refs}"
                    ),
                )

            if psv.polarity in ("STRONG_NEGATIVE", "STRONG_POSITIVE") and not axis_hits:
                flag_hits.append(f"{axis}.ambiguous")

        if flag_hits:
            return AuditResult(
                is_passed=True,
                audit_state="FLAG",
                reason_code="LIG_AMBIGUOUS_NARRATIVE",
                matched_rules=flag_hits,
                feedback_for_llm="叙事对关键轴描述偏模糊，建议补充与 PSV 一致的明确措辞。",
            )

        return AuditResult(
            is_passed=True,
            audit_state="PASS",
            reason_code="PASS",
            feedback_for_llm="语义与 PSV 方向一致。",
        )

    def build_auto_retry_prompt(self, narrative: str, psv_list: List[PSVSymbol], audit: AuditResult) -> str:
        summary = ", ".join([f"{s.axis}:{s.polarity}" for s in psv_list]) or "N/A"
        refs: List[str] = []
        for s in psv_list:
            refs.extend([str(e) for e in s.evidence[:2]])
        refs_text = " | ".join(refs) if refs else "none"
        excerpt = audit.conflict_excerpt or "(未定位到摘录)"
        return (
            "[AUTO_RETRY_PROMPT]\n"
            f"- PHYSICAL_SENTIMENT_SUMMARY: {summary}\n"
            f"- CONFLICT_EXCERPT: {excerpt}\n"
            "- FORBIDDEN_STANCE: 禁止与物理极性相反的强措辞（如负向轴写成大吉爆发）。\n"
            "- REQUIRED_ALIGNMENT: 叙事必须与 PSV 同向，无法确认时使用中性/审慎表达。\n"
            f"- Evidence Refs: {refs_text}\n"
            f"- 审计反馈: {audit.feedback_for_llm}\n"
            f"- 原始叙事: {narrative.strip()}\n"
        )


class BrainHub:
    """M2.2 模拟层：审计 + 自动重试（最多 2 次）。"""

    def __init__(self, auditor: SemanticAuditor | None = None, max_auto_retry: int = 2) -> None:
        self._auditor = auditor or SemanticAuditor()
        self._max_auto_retry = max(0, int(max_auto_retry))

    def run_with_auto_retry(
        self,
        base_prompt: str,
        psv_list: List[PSVSymbol],
        llm_call: Callable[[str, int], str],
    ) -> BrainHubRunResult:
        prompt = str(base_prompt or "")
        last_retry_prompt = ""
        last_narrative = ""
        last_audit = AuditResult(
            is_passed=False,
            reason_code="LIG_EMPTY_NARRATIVE",
            audit_state="REJECT",
            feedback_for_llm="尚未开始生成。",
        )

        for pass_index in range(self._max_auto_retry + 1):
            last_narrative = str(llm_call(prompt, pass_index) or "")
            last_audit = self._auditor.audit(last_narrative, psv_list)
            if last_audit.audit_state != "REJECT":
                return BrainHubRunResult(
                    final_narrative=last_narrative,
                    audit=last_audit,
                    retry_count=pass_index,
                    last_auto_retry_prompt=last_retry_prompt,
                )

            if pass_index >= self._max_auto_retry:
                dissent = DissentBlock(
                    reason_code="LIG_RETRY_EXHAUSTED",
                    summary=(
                        "自动重试已耗尽，仍未通过语义监军。"
                        f"last_reason={last_audit.reason_code}"
                    ),
                )
                return BrainHubRunResult(
                    final_narrative=last_narrative,
                    audit=AuditResult(
                        is_passed=False,
                        reason_code="LIG_RETRY_EXHAUSTED",
                        audit_state="REJECT",
                        feedback_for_llm=last_audit.feedback_for_llm,
                        matched_rules=last_audit.matched_rules,
                        conflict_excerpt=last_audit.conflict_excerpt,
                    ),
                    retry_count=pass_index,
                    last_auto_retry_prompt=last_retry_prompt,
                    dissent_block=dissent,
                )

            last_retry_prompt = self._auditor.build_auto_retry_prompt(last_narrative, psv_list, last_audit)
            prompt = f"{base_prompt.strip()}\n\n{last_retry_prompt}"

        return BrainHubRunResult(
            final_narrative=last_narrative,
            audit=last_audit,
            retry_count=self._max_auto_retry,
            last_auto_retry_prompt=last_retry_prompt,
        )


__all__ = [
    "AuditResult",
    "BrainHub",
    "BrainHubRunResult",
    "DissentBlock",
    "SemanticAuditor",
]
