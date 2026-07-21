from __future__ import annotations

import json

from core.life_domains import LifeDomain, domain_reasoning_protocol
from core.mingli_agent.contracts import (
    ChartWorldInstance,
    DomainCausalReading,
    EpistemicReviewReceipt,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    ReviewIssue,
)
from core.mingli_agent.fact_review import assertive_claim_text, audit_professional_facts
from core.mingli_agent.reliability import domain_baseline_override_reason
from core.mingli_agent.reasoning_normalization import (
    _all_citations,
    _baseline_cognitive_reference_ids,
    _domain_reading_citations,
)
from core.mingli_agent.reasoning_utils import _unique
from core.mingli_agent.reasoning_validation import _citation_allowed, _semantic_text_errors


def review_cognition(
    *,
    draft: MingliCognitiveDraft,
    world: ChartWorldInstance,
    model: str,
    repaired: bool = False,
) -> EpistemicReviewReceipt:
    issues: list[ReviewIssue] = []
    allowed = set(world.allowed_evidence_refs)
    cited = _all_citations(draft)
    unknown = sorted(ref for ref in cited if not _citation_allowed(ref=ref, allowed=allowed))
    if unknown:
        issues.append(ReviewIssue(code="unknown_evidence_refs", severity="error", message=", ".join(unknown[:12])))
    if len(draft.hypotheses) < 2:
        issues.append(ReviewIssue(code="insufficient_competing_hypotheses", severity="warning", message="本轮只保留一个事实安全的命局假设"))
    hypothesis_ids = {item.hypothesis_id for item in draft.hypotheses}
    if draft.selected_hypothesis_id not in hypothesis_ids:
        issues.append(ReviewIssue(code="selected_hypothesis_missing", severity="error", message=draft.selected_hypothesis_id))
    if not any(item.status == "primary" and item.hypothesis_id == draft.selected_hypothesis_id for item in draft.hypotheses):
        issues.append(ReviewIssue(code="primary_status_mismatch", severity="error", message="主假设标记不一致"))
    if not draft.prior_predictions:
        issues.append(ReviewIssue(code="missing_prior_predictions", severity="warning", message="本轮没有保留可安全展示的先验判断"))
    if len({item.claim for item in draft.prior_predictions}) != len(draft.prior_predictions):
        issues.append(ReviewIssue(code="repeated_prior_predictions", severity="error", message="先验预测重复"))
    generated_domains = [item for item in (draft.career, draft.wealth) if item is not None]
    if any(len(item.causal_chain) < 2 for item in generated_domains):
        issues.append(ReviewIssue(code="thin_domain_causal_chain", severity="error", message="已生成领域需要完整因果链"))
    if not draft.work_path.failure_conditions:
        issues.append(ReviewIssue(code="work_path_without_failure_conditions", severity="warning", message="主做功尚未补充失效条件"))
    if not any(item.rejection_reason for item in draft.hypotheses if item.status == "alternative"):
        issues.append(ReviewIssue(code="alternatives_not_compared", severity="warning", message="替代假设缺少放弃原因"))
    if any(item.lens == "mixed" for item in draft.useful_god_reasoning):
        issues.append(ReviewIssue(
            code="ambiguous_strategy_dimension",
            severity="error",
            message="调候、扶抑、结构、制化、做功与时序不能压缩成 mixed 用神结论",
        ))
    for item in draft.useful_god_reasoning:
        if not item.question_answered.strip():
            issues.append(ReviewIssue(
                code="strategy_question_missing",
                severity="error",
                message=f"{item.candidate}:{item.lens} 没有说明正在回答哪一个命理问题",
            ))
        if not item.applicable_conditions or not item.invalidating_conditions:
            issues.append(ReviewIssue(
                code="strategy_conditions_missing",
                severity="error",
                message=f"{item.candidate}:{item.lens} 缺少成立或失效条件",
            ))
    generic = ("有机会也有挑战", "保持积极心态", "平衡工作与生活", "相信自己", "顺其自然")
    draft_payload = draft.model_dump(mode="json")
    corpus = json.dumps(draft_payload, ensure_ascii=False)
    assertive_text = assertive_claim_text(draft_payload)
    for phrase in generic:
        if phrase in corpus:
            issues.append(ReviewIssue(code="generic_advice", severity="warning", message=phrase))
    for error in _semantic_text_errors(text=assertive_text, world=world, include_deterministic=False):
        issues.append(ReviewIssue(code="mingli_fact_conflict", severity="error", message=error))
    for fact_issue in audit_professional_facts(text=assertive_text, world=world, claim_ref="whole_chart_cognition"):
        issues.append(
            ReviewIssue(
                code=f"professional_fact:{fact_issue.issue_type}",
                severity="error" if fact_issue.severity in {"hard", "major"} else "warning",
                message=(
                    f"{fact_issue.original_text} | {fact_issue.canonical_fact_ref} | "
                    f"{fact_issue.modality} | {fact_issue.disposition}"
                ),
            )
        )
    traceability = 1.0 if not cited else round(sum(_citation_allowed(ref=ref, allowed=allowed) for ref in cited) / len(cited), 3)
    return _finalize_review(
        issues=issues,
        fact_traceability_rate=traceability,
        model=model,
        repaired=repaired,
        competing=_cognition_has_unresolved_competition(draft),
    )

def review_domain_reading(
    *,
    reading: DomainCausalReading,
    world: ChartWorldInstance,
    model: str,
    repaired: bool = False,
    baseline_record: MingliCognitiveRecord | None = None,
    expected_domain: LifeDomain | None = None,
) -> EpistemicReviewReceipt:
    issues: list[ReviewIssue] = []
    allowed = set(world.allowed_evidence_refs)
    if baseline_record is not None:
        allowed.update(_baseline_cognitive_reference_ids(baseline_record))
    cited = _domain_reading_citations(reading)
    unknown = sorted(ref for ref in cited if not _citation_allowed(ref=ref, allowed=allowed))
    if unknown:
        issues.append(ReviewIssue(code="unknown_evidence_refs", severity="error", message=", ".join(unknown[:12])))
    if not 2 <= len(reading.causal_chain) <= 6:
        issues.append(ReviewIssue(code="invalid_causal_chain", severity="error", message="领域因果链需要保持可理解的完整路径"))
    if not reading.assertions:
        issues.append(ReviewIssue(code="thin_domain_assertions", severity="error", message="领域至少需要一条可证伪断言"))
    if any(item.domain != reading.domain for item in reading.assertions):
        issues.append(ReviewIssue(code="domain_scope_leakage", severity="error", message="领域断言越界"))
    if expected_domain is not None and reading.domain != expected_domain:
        issues.append(ReviewIssue(
            code="domain_scope_leakage",
            severity="error",
            message=f"请求领域为 {expected_domain.value}，模型却返回 {reading.domain.value}",
        ))
    if reading.next_probe is not None and len(reading.next_probe.options) < 2:
        issues.append(ReviewIssue(code="invalid_domain_probe", severity="error", message="已经提出的问题需要提供可区分的回答方式"))
    elif reading.next_probe is not None and len(reading.next_probe.distinguishes_hypothesis_refs) < 2:
        issues.append(ReviewIssue(code="thin_domain_probe_targets", severity="warning", message="当前问题尚未充分区分两条断言"))
    elif reading.next_probe is not None:
        probe_targets = set(reading.next_probe.distinguishes_hypothesis_refs)
        known_targets = {item.assertion_id for item in reading.assertions}
        if baseline_record is not None:
            known_targets.update(item.hypothesis_id for item in baseline_record.cognition.hypotheses)
        unknown_targets = sorted(probe_targets - known_targets)
        if unknown_targets:
            issues.append(ReviewIssue(
                code="invalid_domain_probe",
                severity="error",
                message=f"Probe 引用了不存在的专题断言或整盘假设：{', '.join(unknown_targets)}",
            ))
    reading_payload = reading.model_dump(mode="json")
    corpus = json.dumps(reading_payload, ensure_ascii=False)
    assertive_text = assertive_claim_text(reading_payload)
    for phrase in ("有机会也有挑战", "保持积极心态", "顺其自然", "因人而异"):
        if phrase in corpus:
            issues.append(ReviewIssue(code="generic_domain_advice", severity="error", message=phrase))
    protocol = domain_reasoning_protocol(reading.domain)
    for forbidden in protocol.forbidden_claims:
        if forbidden in corpus:
            issues.append(ReviewIssue(code="forbidden_domain_claim", severity="error", message=forbidden))
    for forbidden in _forbidden_domain_tokens(reading.domain):
        if forbidden in corpus:
            issues.append(ReviewIssue(code="high_risk_domain_claim", severity="error", message=forbidden))
    for error in _semantic_text_errors(text=assertive_text, world=world, include_deterministic=False):
        issues.append(ReviewIssue(code="mingli_fact_conflict", severity="error", message=error))
    for fact_issue in audit_professional_facts(
        text=assertive_text,
        world=world,
        claim_ref=f"domain:{reading.domain.value}",
    ):
        issues.append(
            ReviewIssue(
                code=f"professional_fact:{fact_issue.issue_type}",
                severity="error" if fact_issue.severity in {"hard", "major"} else "warning",
                message=(
                    f"{fact_issue.original_text} | {fact_issue.canonical_fact_ref} | "
                    f"{fact_issue.modality} | {fact_issue.disposition}"
                ),
            )
        )
    if baseline_record is not None:
        override_reason = domain_baseline_override_reason(reading=reading, record=baseline_record)
        if override_reason:
            issues.append(ReviewIssue(
                code="baseline_override_attempt",
                severity="error",
                message=override_reason,
            ))
    traceability = 1.0 if not cited else round(sum(_citation_allowed(ref=ref, allowed=allowed) for ref in cited) / len(cited), 3)
    competing = bool(reading.assertions) and not any(
        item.epistemic_status == "supported" for item in reading.assertions
    )
    return _finalize_review(
        issues=issues,
        fact_traceability_rate=traceability,
        model=model,
        repaired=repaired,
        competing=competing,
    )

def _finalize_review(
    *,
    issues: list[ReviewIssue],
    fact_traceability_rate: float,
    model: str,
    repaired: bool,
    competing: bool,
) -> EpistemicReviewReceipt:
    classified = [_classify_review_issue(item) for item in issues]
    hard_failures = [item.code for item in classified if item.blocks_commit]
    repairable = [item.code for item in classified if item.repairable]
    disposition = "blocked" if hard_failures else "competing" if competing else "reliable"
    return EpistemicReviewReceipt(
        passed=not hard_failures,
        issues=classified,
        fact_traceability_rate=fact_traceability_rate,
        model=model,
        repaired=repaired,
        disposition=disposition,
        commit_eligible=disposition == "reliable",
        hard_failure_codes=_unique(hard_failures),
        repairable_issue_codes=_unique(repairable),
        gate_version="mingli_reliability_gate_v1",
    )

def _classify_review_issue(issue: ReviewIssue) -> ReviewIssue:
    code = issue.code
    if code == "mingli_fact_conflict" or code.startswith("professional_fact:"):
        category = "chart_fact"
        repairable = False
    elif code == "unknown_evidence_refs":
        category = "evidence"
        repairable = True
    elif code in {
        "selected_hypothesis_missing",
        "primary_status_mismatch",
        "repeated_prior_predictions",
        "ambiguous_strategy_dimension",
        "strategy_question_missing",
        "strategy_conditions_missing",
        "baseline_override_attempt",
    }:
        category = "semantic_consistency"
        repairable = code not in {"baseline_override_attempt"}
    elif code in {"forbidden_domain_claim", "high_risk_domain_claim", "domain_scope_leakage"}:
        category = "safety"
        repairable = True
    elif code in {
        "thin_domain_causal_chain",
        "invalid_causal_chain",
        "thin_domain_assertions",
        "invalid_domain_probe",
    }:
        category = "completeness"
        repairable = True
    elif "hypothes" in code or code in {"alternatives_not_compared", "thin_domain_probe_targets"}:
        category = "hypothesis_competition"
        repairable = issue.severity == "error"
    else:
        category = "quality"
        repairable = issue.severity == "error"
    return issue.model_copy(update={
        "category": category,
        "blocks_commit": issue.severity == "error",
        "repairable": repairable,
    })

def _cognition_has_unresolved_competition(draft: MingliCognitiveDraft) -> bool:
    selected = next(
        (item for item in draft.hypotheses if item.hypothesis_id == draft.selected_hypothesis_id),
        None,
    )
    if selected is None or selected.confidence == "low":
        return True
    confidence_rank = {"low": 1, "medium": 2, "high": 3}
    for item in draft.hypotheses:
        if item.hypothesis_id == draft.selected_hypothesis_id:
            continue
        if not item.rejection_reason.strip():
            return True
        if item.status == "unresolved" and confidence_rank[item.confidence] >= confidence_rank[selected.confidence]:
            return True
        if (
            confidence_rank[item.confidence] >= confidence_rank[selected.confidence]
            and not item.rejection_reason.strip()
        ):
            return True
    return False

def _review_requires_one_repair(receipt: EpistemicReviewReceipt) -> bool:
    blocking = [item for item in receipt.issues if item.blocks_commit]
    return bool(blocking) and all(item.repairable for item in blocking)

def _forbidden_domain_tokens(domain: LifeDomain) -> tuple[str, ...]:
    return {
        LifeDomain.RELATIONSHIP: ("一定结婚", "必然结婚", "一定离婚", "必然离婚", "婚期就在"),
        LifeDomain.CHILDREN_LEGACY: ("一定生育", "必然生育", "生几个", "生男", "生女"),
        LifeDomain.HEALTH_VITALITY: ("诊断为", "患有", "癌症", "肿瘤", "心脏病", "肝病", "寿命", "死亡时间"),
        LifeDomain.LIFE_TIMING: ("一定会发生", "必然发生", "保证在", "灾祸日期", "发财年份"),
    }.get(domain, ())
