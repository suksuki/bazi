from __future__ import annotations

import json
from typing import Any, Iterable

from core.life_domains import domain_reasoning_protocol
from core.mingli_agent.contracts import (
    AssertionGateDecision,
    AssertionGateReceipt,
    ChartWorldInstance,
    DomainCausalReading,
    MingliCognitiveRecord,
    MingliCognitiveDraft,
)
from core.mingli_agent.fact_review import audit_professional_facts, repair_locked_fact_assertions
from core.mingli_agent.reasoning_normalization import (
    _apply_scope_boundary,
    _filter_evidence_refs,
    _soften_prediction_text,
)
from core.mingli_agent.reasoning_validation import _semantic_text_errors


_VISIBLE_TEXT_KEYS = {
    "first_look",
    "whole_chart_thesis",
    "observation",
    "why_it_matters",
    "name",
    "thesis",
    "path_statement",
    "body_function_relation",
    "candidate",
    "role",
    "why_useful",
    "when_harmful",
    "claim",
    "rationale",
    "why_predicted",
    "disconfirming_answer",
    "integrated_thesis",
    "current_stage_note",
}


def isolate_cognition_assertions(
    *,
    draft: MingliCognitiveDraft,
    world: ChartWorldInstance,
) -> tuple[MingliCognitiveDraft, AssertionGateReceipt]:
    """Keep valid assertions moving while isolating only the invalid item."""

    original = draft.model_dump(mode="json")
    scoped = _apply_scope_boundary(draft)
    softened_payload = _rewrite_visible_text(scoped.model_dump(mode="json"))
    repaired_payload, _locked_repairs = repair_locked_fact_assertions(
        payload=softened_payload,
        world=world,
    )
    payload = _filter_evidence_refs(
        MingliCognitiveDraft.model_validate(repaired_payload),
        world=world,
    ).model_dump(mode="json")
    decisions: list[AssertionGateDecision] = []

    def decide(
        *,
        assertion_ref: str,
        assertion_kind: str,
        field_path: str,
        original_value: Any,
        projected_value: Any,
        original_refs: Iterable[str],
        projected_refs: Iterable[str],
        candidate_reasons: Iterable[str] = (),
    ) -> AssertionGateDecision:
        original_text = _text(original_value)
        projected_text = _text(projected_value)
        accepted_refs = _unique(str(item) for item in projected_refs if str(item))
        original_ref_values = _unique(str(item) for item in original_refs if str(item))
        rejected_refs = [item for item in original_ref_values if item not in accepted_refs]
        fact_issues = [
            item
            for item in audit_professional_facts(
                text=projected_text,
                world=world,
                claim_ref=assertion_ref,
            )
            if item.severity in {"hard", "major"}
        ]
        semantic_errors = _semantic_text_errors(
            text=projected_text,
            world=world,
            include_deterministic=False,
        )
        reasons = [
            *(f"hard_fact:{item.issue_type}" for item in fact_issues),
            *(f"semantic:{item.split(':', 1)[0]}" for item in semantic_errors),
        ]
        candidate_reason_values = _unique(str(item) for item in candidate_reasons if str(item))
        if fact_issues or semantic_errors:
            disposition = "suppressed"
        elif candidate_reason_values or (original_ref_values and not accepted_refs):
            disposition = "candidate"
            reasons.extend(candidate_reason_values or ["evidence_unbound"])
        elif original_text != projected_text or rejected_refs:
            disposition = "repaired"
            if original_text != projected_text:
                reasons.append("local_wording_or_fact_repair")
            if rejected_refs:
                reasons.append("unknown_evidence_removed")
        else:
            disposition = "accepted"
        decision = AssertionGateDecision(
            assertion_ref=assertion_ref,
            assertion_kind=assertion_kind,
            field_path=field_path,
            disposition=disposition,
            reason_codes=_unique(reasons),
            accepted_evidence_refs=accepted_refs,
            rejected_evidence_refs=rejected_refs,
            original_text=original_text,
            projected_text=projected_text if disposition in {"accepted", "repaired"} else "",
        )
        decisions.append(decision)
        return decision

    top_refs = original.get("evidence_refs") or []
    projected_top_refs = payload.get("evidence_refs") or []
    first_look = decide(
        assertion_ref="baseline:first-look",
        assertion_kind="baseline_summary",
        field_path="first_look",
        original_value=original.get("first_look"),
        projected_value=payload.get("first_look"),
        original_refs=top_refs,
        projected_refs=projected_top_refs,
    )
    thesis = decide(
        assertion_ref="baseline:whole-chart-thesis",
        assertion_kind="whole_chart_claim",
        field_path="whole_chart_thesis",
        original_value=original.get("whole_chart_thesis"),
        projected_value=payload.get("whole_chart_thesis"),
        original_refs=top_refs,
        projected_refs=projected_top_refs,
    )
    if first_look.disposition not in {"accepted", "repaired"}:
        payload["first_look"] = "命盘事实已经建立，整盘重心仍在逐条核验。"
    if thesis.disposition not in {"accepted", "repaired"}:
        payload["whole_chart_thesis"] = "当前只展示已经通过事实核验的命盘内容。"

    payload["salient_phenomena"] = _filter_items(
        original_items=original.get("salient_phenomena") or [],
        projected_items=payload.get("salient_phenomena") or [],
        ref_key="phenomenon_id",
        kind="salient_phenomenon",
        field_path="salient_phenomena",
        text_keys=("observation", "why_it_matters"),
        evidence_keys=("evidence_refs",),
        decide=decide,
    )

    hypotheses = _filter_items(
        original_items=original.get("hypotheses") or [],
        projected_items=payload.get("hypotheses") or [],
        ref_key="hypothesis_id",
        kind="hypothesis",
        field_path="hypotheses",
        text_keys=("name", "thesis"),
        evidence_keys=("supporting_evidence_refs", "counter_evidence_refs"),
        decide=decide,
    )
    selected_id = str(payload.get("selected_hypothesis_id") or "")
    if selected_id not in {str(item.get("hypothesis_id") or "") for item in hypotheses}:
        selected = next((item for item in hypotheses if item.get("status") == "primary"), None)
        selected = selected or (hypotheses[0] if hypotheses else None)
        selected_id = str((selected or {}).get("hypothesis_id") or "")
        if selected is not None:
            for item in hypotheses:
                item["status"] = "primary" if item is selected else "alternative"
    payload["hypotheses"] = hypotheses
    payload["selected_hypothesis_id"] = selected_id

    original_work = original.get("work_path") or {}
    projected_work = payload.get("work_path") or {}
    work_decision = decide(
        assertion_ref="baseline:work-path",
        assertion_kind="work_path",
        field_path="work_path",
        original_value={
            key: original_work.get(key)
            for key in ("path_statement", "source", "transformations", "target", "body_function_relation")
        },
        projected_value={
            key: projected_work.get(key)
            for key in ("path_statement", "source", "transformations", "target", "body_function_relation")
        },
        original_refs=original_work.get("evidence_refs") or [],
        projected_refs=projected_work.get("evidence_refs") or [],
        candidate_reasons=(
            ["work_path_incomplete"]
            if not projected_work.get("source") or not projected_work.get("target")
            else []
        ),
    )
    if work_decision.disposition not in {"accepted", "repaired"}:
        payload["work_path"] = {
            **projected_work,
            "path_statement": "主作用路径仍在核验，当前不作为正式结论。",
            "source": [],
            "transformations": [],
            "target": [],
            "body_function_relation": "未提交",
            "closure": "uncertain",
            "success_conditions": [],
            "failure_conditions": ["需要更多可追溯证据。"],
            "evidence_refs": [],
            "candidate_path_refs": [],
            "competing_path_refs": [],
            "comparison_reasons": [],
            "structured_candidate": None,
        }

    payload["useful_god_reasoning"] = _filter_items(
        original_items=original.get("useful_god_reasoning") or [],
        projected_items=payload.get("useful_god_reasoning") or [],
        ref_key=None,
        kind="strategy_dimension",
        field_path="useful_god_reasoning",
        text_keys=("candidate", "role", "why_useful", "when_harmful"),
        evidence_keys=("evidence_refs", "counter_evidence_refs"),
        decide=decide,
        candidate_reason=lambda item: (
            ["strategy_conditions_missing"]
            if not item.get("question_answered")
            or not item.get("applicable_conditions")
            or not item.get("invalidating_conditions")
            else []
        ),
    )
    payload["portrait"] = _filter_items(
        original_items=original.get("portrait") or [],
        projected_items=payload.get("portrait") or [],
        ref_key="assertion_id",
        kind="portrait_assertion",
        field_path="portrait",
        text_keys=("claim", "rationale"),
        evidence_keys=("evidence_refs", "counter_evidence_refs"),
        decide=decide,
        candidate_reason=lambda item: (
            ["assertion_not_supported"]
            if item.get("epistemic_status") != "supported"
            else []
        ),
    )
    payload["prior_predictions"] = _filter_items(
        original_items=original.get("prior_predictions") or [],
        projected_items=payload.get("prior_predictions") or [],
        ref_key="prediction_id",
        kind="prior_prediction",
        field_path="prior_predictions",
        text_keys=("claim", "why_predicted"),
        evidence_keys=("evidence_refs",),
        decide=decide,
    )

    if isinstance(payload.get("dual_lens"), dict):
        original_dual = original.get("dual_lens") or {}
        projected_dual = payload.get("dual_lens") or {}
        observations = _filter_items(
            original_items=original_dual.get("palace_observations") or [],
            projected_items=projected_dual.get("palace_observations") or [],
            ref_key="observation_id",
            kind="dual_lens_observation",
            field_path="dual_lens.palace_observations",
            text_keys=("claim", "why_it_matters"),
            evidence_keys=("evidence_refs",),
            decide=decide,
        )
        projected_dual["palace_observations"] = observations
        if not observations:
            payload["dual_lens"] = None

    gated = MingliCognitiveDraft.model_validate(payload)
    accepted_count = sum(item.disposition == "accepted" for item in decisions)
    repaired_count = sum(item.disposition == "repaired" for item in decisions)
    candidate_count = sum(item.disposition == "candidate" for item in decisions)
    suppressed_count = sum(item.disposition == "suppressed" for item in decisions)
    accepted_refs = {
        item.assertion_ref
        for item in decisions
        if item.disposition in {"accepted", "repaired"}
    }
    has_support = bool(
        accepted_refs
        & {
            "baseline:work-path",
            *(str(item.get("phenomenon_id") or "") for item in payload["salient_phenomena"]),
            *(str(item.get("hypothesis_id") or "") for item in payload["hypotheses"]),
        }
    )
    whole_chart_claim_available = bool(
        has_support
        and (
            "baseline:whole-chart-thesis" in accepted_refs
            or "baseline:first-look" in accepted_refs
        )
    )
    return gated, AssertionGateReceipt(
        decisions=decisions,
        accepted_count=accepted_count,
        repaired_count=repaired_count,
        candidate_count=candidate_count,
        suppressed_count=suppressed_count,
        whole_chart_claim_available=whole_chart_claim_available,
    )


def accepted_assertion_refs(receipt: AssertionGateReceipt) -> set[str]:
    return {
        item.assertion_ref
        for item in receipt.decisions
        if item.disposition in {"accepted", "repaired"}
    }


def isolate_domain_assertions(
    *,
    reading: DomainCausalReading,
    world: ChartWorldInstance,
    baseline_record: MingliCognitiveRecord,
) -> tuple[DomainCausalReading, AssertionGateReceipt]:
    """Project only locally valid domain assertions without a repair generation."""

    allowed = set(world.allowed_evidence_refs)
    allowed.update({
        baseline_record.record_id,
        *(item.phenomenon_id for item in baseline_record.cognition.salient_phenomena),
        *(item.hypothesis_id for item in baseline_record.cognition.hypotheses),
        *(item.assertion_id for item in baseline_record.cognition.portrait),
    })
    decisions: list[AssertionGateDecision] = []
    accepted_assertions = []
    forbidden_tokens = _domain_projection_forbidden_tokens(reading)
    for item in reading.assertions:
        original_text = f"{item.claim} {item.rationale}".strip()
        claim = _soften_prediction_text(item.claim)
        rationale = _soften_prediction_text(item.rationale)
        projected_text = f"{claim} {rationale}".strip()
        accepted_evidence = [ref for ref in item.evidence_refs if ref in allowed]
        accepted_counter = [ref for ref in item.counter_evidence_refs if ref in allowed]
        rejected = [
            ref
            for ref in [*item.evidence_refs, *item.counter_evidence_refs]
            if ref not in allowed
        ]
        fact_issues = [
            issue
            for issue in audit_professional_facts(
                text=projected_text,
                world=world,
                claim_ref=item.assertion_id,
            )
            if issue.severity in {"hard", "major"}
        ]
        semantic_errors = _semantic_text_errors(
            text=projected_text,
            world=world,
            include_deterministic=False,
        )
        reasons = [
            *(f"hard_fact:{issue.issue_type}" for issue in fact_issues),
            *(f"semantic:{error.split(':', 1)[0]}" for error in semantic_errors),
        ]
        if item.domain != reading.domain:
            reasons.append("domain_scope_leakage")
        unsafe_token = next((token for token in forbidden_tokens if token in projected_text), "")
        if unsafe_token:
            reasons.append("unsafe_or_generic_domain_claim")
        if fact_issues or semantic_errors or item.domain != reading.domain or unsafe_token:
            disposition = "suppressed"
        elif item.epistemic_status != "supported" or not accepted_evidence:
            disposition = "candidate"
            reasons.append(
                "assertion_not_supported"
                if item.epistemic_status != "supported"
                else "evidence_unbound"
            )
        elif original_text != projected_text or rejected:
            disposition = "repaired"
            reasons.append("local_wording_or_evidence_repair")
        else:
            disposition = "accepted"
        decisions.append(AssertionGateDecision(
            assertion_ref=item.assertion_id,
            assertion_kind="domain_assertion",
            field_path=f"assertions.{len(decisions)}",
            disposition=disposition,
            reason_codes=_unique(reasons),
            accepted_evidence_refs=accepted_evidence,
            rejected_evidence_refs=_unique(rejected),
            original_text=original_text,
            projected_text=projected_text if disposition in {"accepted", "repaired"} else "",
        ))
        if disposition in {"accepted", "repaired"}:
            accepted_assertions.append(item.model_copy(update={
                "claim": claim,
                "rationale": rationale,
                "evidence_refs": accepted_evidence,
                "counter_evidence_refs": accepted_counter,
            }))

    safe_lists: dict[str, list[str]] = {}
    for field_name in (
        "causal_chain",
        "stable_tendencies",
        "favorable_environments",
        "adverse_environments",
        "opportunity_conditions",
        "risk_conditions",
        "prior_directions",
        "unknowns",
    ):
        safe_values: list[str] = []
        for index, original_text in enumerate(getattr(reading, field_name)):
            projected_text = _soften_prediction_text(original_text)
            issues = [
                issue
                for issue in audit_professional_facts(
                    text=projected_text,
                    world=world,
                    claim_ref=f"domain:{field_name}:{index}",
                )
                if issue.severity in {"hard", "major"}
            ]
            semantic_errors = _semantic_text_errors(
                text=projected_text,
                world=world,
                include_deterministic=False,
            )
            unsafe_token = next((token for token in forbidden_tokens if token in projected_text), "")
            disposition = "suppressed" if issues or semantic_errors or unsafe_token else (
                "repaired" if original_text != projected_text else "accepted"
            )
            decisions.append(AssertionGateDecision(
                assertion_ref=f"domain:{field_name}:{index}",
                assertion_kind="domain_supporting_statement",
                field_path=f"{field_name}.{index}",
                disposition=disposition,
                reason_codes=_unique([
                    *(f"hard_fact:{issue.issue_type}" for issue in issues),
                    *(f"semantic:{error.split(':', 1)[0]}" for error in semantic_errors),
                    *(["unsafe_or_generic_domain_claim"] if unsafe_token else []),
                    *(["local_wording_repair"] if disposition == "repaired" else []),
                ]),
                original_text=original_text,
                projected_text=projected_text if disposition != "suppressed" else "",
            ))
            if disposition != "suppressed":
                safe_values.append(projected_text)
        safe_lists[field_name] = safe_values

    if accepted_assertions and len(safe_lists["causal_chain"]) < 2:
        first = accepted_assertions[0]
        safe_lists["causal_chain"] = [first.rationale, first.claim]
        decisions.append(AssertionGateDecision(
            assertion_ref="domain:causal-chain-projection",
            assertion_kind="domain_causal_chain",
            field_path="causal_chain",
            disposition="repaired",
            reason_codes=["projected_from_accepted_assertion"],
            accepted_evidence_refs=list(first.evidence_refs),
            projected_text=f"{first.rationale} → {first.claim}",
        ))

    timing_note = _soften_prediction_text(reading.timing_note)
    timing_issues = audit_professional_facts(
        text=timing_note,
        world=world,
        claim_ref="domain:timing-note",
    )
    if (
        any(item.severity in {"hard", "major"} for item in timing_issues)
        or any(token in timing_note for token in forbidden_tokens)
    ):
        timing_note = "当前专题不增加未经核验的时间结论。"

    known_probe_targets = {
        *(item.assertion_id for item in accepted_assertions),
        *(item.hypothesis_id for item in baseline_record.cognition.hypotheses),
    }
    next_probe = reading.next_probe
    if next_probe is not None:
        targets = [
            ref for ref in next_probe.distinguishes_hypothesis_refs if ref in known_probe_targets
        ]
        next_probe = (
            next_probe.model_copy(update={"distinguishes_hypothesis_refs": targets})
            if len(targets) >= 2 and len(next_probe.options) >= 2
            else None
        )

    projected = reading.model_copy(update={
        **safe_lists,
        "assertions": accepted_assertions,
        "timing_note": timing_note,
        "next_probe": next_probe,
    })
    return projected, AssertionGateReceipt(
        decisions=decisions,
        accepted_count=sum(item.disposition == "accepted" for item in decisions),
        repaired_count=sum(item.disposition == "repaired" for item in decisions),
        candidate_count=sum(item.disposition == "candidate" for item in decisions),
        suppressed_count=sum(item.disposition == "suppressed" for item in decisions),
        whole_chart_claim_available=bool(accepted_assertions),
    )


def _filter_items(
    *,
    original_items: list[dict[str, Any]],
    projected_items: list[dict[str, Any]],
    ref_key: str | None,
    kind: str,
    field_path: str,
    text_keys: tuple[str, ...],
    evidence_keys: tuple[str, ...],
    decide,
    candidate_reason=lambda item: (),
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, projected in enumerate(projected_items):
        original = original_items[index] if index < len(original_items) else projected
        ref = (
            str(projected.get(ref_key) or original.get(ref_key) or "")
            if ref_key
            else f"{field_path}:{index}"
        )
        original_refs = [
            ref_value
            for key in evidence_keys
            for ref_value in original.get(key) or []
        ]
        projected_refs = [
            ref_value
            for key in evidence_keys
            for ref_value in projected.get(key) or []
        ]
        decision = decide(
            assertion_ref=ref,
            assertion_kind=kind,
            field_path=f"{field_path}.{index}",
            original_value={key: original.get(key) for key in text_keys},
            projected_value={key: projected.get(key) for key in text_keys},
            original_refs=original_refs,
            projected_refs=projected_refs,
            candidate_reasons=candidate_reason(projected),
        )
        if decision.disposition in {"accepted", "repaired"}:
            output.append(projected)
    return output


def _rewrite_visible_text(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        return {child_key: _rewrite_visible_text(child, child_key) for child_key, child in value.items()}
    if isinstance(value, list):
        return [_rewrite_visible_text(child, key) for child in value]
    if isinstance(value, str) and key in _VISIBLE_TEXT_KEYS:
        return _soften_prediction_text(value)
    return value


def _domain_projection_forbidden_tokens(reading: DomainCausalReading) -> tuple[str, ...]:
    protocol = domain_reasoning_protocol(reading.domain)
    return tuple(dict.fromkeys([
        *protocol.forbidden_claims,
        "有机会也有挑战",
        "保持积极心态",
        "顺其自然",
        "因人而异",
        "一定结婚",
        "必然结婚",
        "一定离婚",
        "必然离婚",
        "一定生育",
        "必然生育",
        "诊断为",
        "患有",
        "寿命",
        "死亡时间",
        "一定会发生",
        "必然发生",
        "保证在",
        "灾祸日期",
        "发财年份",
    ]))


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


__all__ = [
    "accepted_assertion_refs",
    "isolate_cognition_assertions",
    "isolate_domain_assertions",
]
