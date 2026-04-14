from __future__ import annotations

from app.logic.brain.psv_engine import PSVSymbol
from app.logic.brain.semantic_auditor import BrainHub, SemanticAuditor


def _psv(axis: str, polarity: str, evidence: list[str] | None = None) -> PSVSymbol:
    return PSVSymbol(
        axis=axis,
        polarity=polarity,  # type: ignore[arg-type]
        strength=0.9,
        evidence=evidence or [],
        fingerprint=f"{axis}-{polarity}",
    )


def test_semantic_auditor_pass_when_narrative_aligned() -> None:
    auditor = SemanticAuditor()
    psv_list = [_psv("OFFICER", "STRONG_POSITIVE", ["rule:psv.l2_primary_with_intention"])]
    narrative = "本阶段事业稳定推进，官杀轴有承压但总体向好。"
    ret = auditor.audit(narrative, psv_list)
    assert ret.is_passed is True
    assert ret.audit_state in ("PASS", "FLAG")
    assert ret.reason_code in ("PASS", "LIG_AMBIGUOUS_NARRATIVE")


def test_semantic_auditor_rejects_wealth_hallucination_with_retry_hint() -> None:
    auditor = SemanticAuditor()
    psv_list = [
        _psv(
            "WEALTH",
            "STRONG_NEGATIVE",
            ["rule:psv.robber_wealth_pierce_ratio", "dynamic_inference.l1_audit.l1_robber_wealth_v1"],
        )
    ]
    narrative = "你这盘财星高照，近期大发横财，财运直接爆发。"
    ret = auditor.audit(narrative, psv_list)
    assert ret.is_passed is False
    assert ret.reason_code == "LIG_AXIS_POS_MISMATCH"
    assert "比劫穿透" in ret.feedback_for_llm


def test_brain_hub_auto_retry_exhausted_to_dissent_block() -> None:
    psv_list = [_psv("WEALTH", "STRONG_NEGATIVE", ["rule:psv.robber_wealth_pierce_ratio"])]
    hub = BrainHub(max_auto_retry=2)

    def _always_hallucinate(prompt: str, pass_index: int) -> str:
        return "财运亨通，大发横财，爆发增长。"

    result = hub.run_with_auto_retry("请给出财富分析", psv_list, _always_hallucinate)
    assert result.audit.reason_code == "LIG_RETRY_EXHAUSTED"
    assert result.retry_count == 2
    assert result.dissent_block is not None
    assert result.dissent_block.block_kind == "LOGIC_CONFLICT"
    assert "比劫穿透" in result.last_auto_retry_prompt
