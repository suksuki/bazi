from __future__ import annotations

from v30.presentation.branch_cards import (
    branch_cards_from_conflict_audit,
    conflict_cards_for_legacy_surface,
    domain_label,
)
from v30.presentation.leakage_guard import scan_product_payload
from v30.presentation.product_contracts import (
    PRODUCT_CONTRACT_VERSION,
    ProductProjectionBundle,
    ProductVerdictCard,
)


DIAGNOSTIC_ROLES = {"practitioner", "admin", "analyst", "lab"}


def output_runtime_contract() -> dict[str, object]:
    return {
        "version": "v30.output_runtime_product_projection_contract.v1",
        "runtime_order": [
            "InternalRuntimeObjects",
            "ProductProjection",
            "ProductCards",
            "LLMExpression",
            "AcceptanceRepairSalvage",
            "FinalUserVisibleProjection",
            "SurfaceOrchestrator",
        ],
        "decision_authority": "DecisionEngineVerdict",
        "llm_role": "expression_after_product_projection_not_final_decision",
        "leakage_guard": "v30.presentation.leakage_guard",
        "product_projection_module": "v30.presentation.product_projection",
        "chart_fact_mutation_allowed": False,
        "verdict_mutation_allowed": False,
        "boundary": "output_runtime_contract_turns_internal_objects_into_user_visible_product_without_chart_fact_mutation",
    }


def build_decision_workbench_product_surface(central: object, *, role_key: str) -> dict[str, object]:
    central_dict = central if isinstance(central, dict) else {}
    verdicts = [row for row in _as_list(central_dict.get("decision_verdicts")) if isinstance(row, dict)]
    conflict_summary = central_dict.get("conflict_resolver_summary", {})
    conflict_summary = conflict_summary if isinstance(conflict_summary, dict) else {}
    conflict_audit = [row for row in _as_list(central_dict.get("conflict_resolver_audit")) if isinstance(row, dict)]
    diagnostic = role_key in DIAGNOSTIC_ROLES

    product_verdict_cards = product_verdict_cards_from_verdicts(verdicts, role_key=role_key)
    product_branch_cards = branch_cards_from_conflict_audit(conflict_audit, role_key=role_key)
    product_projection = _product_projection_payload(
        role_key=role_key,
        verdict_cards=product_verdict_cards,
        branch_cards=product_branch_cards,
    )

    verdict_cards = _legacy_verdict_cards(verdicts, product_verdict_cards, diagnostic=diagnostic)
    conflict_cards = conflict_cards_for_legacy_surface(product_branch_cards, diagnostic=diagnostic)
    payload = {
        "version": "v30.decision_workbench_surface.v1",
        "status": "ready" if verdict_cards else "pending",
        "visible_detail_level": "practitioner_calibration" if diagnostic else "customer_summary",
        "product_projection": product_projection,
        "summary": {
            "verdict_count": len(verdicts),
            "visible_verdict_count": len(verdict_cards),
            "branch_card_count": len(product_branch_cards),
            "conflict_count": _int_count(conflict_summary.get("conflict_count")),
            "domain_count": _int_count(conflict_summary.get("domain_count")),
            "signal_bound_candidate_count": _int_count(conflict_summary.get("signal_bound_candidate_count")),
            "candidate_signal_count": _int_count(conflict_summary.get("candidate_signal_count")),
            "score_mutation_allowed": False,
            "verdict_mutation_allowed": False,
            "boundary": "decision_workbench_summary_is_public_or_role_gated_projection_not_score_authority",
        },
        "verdict_cards": verdict_cards,
        "conflict_cards": conflict_cards,
        "calibration": {
            "needed": bool(conflict_cards),
            "role_can_calibrate": diagnostic,
            "interaction_source": "产品分支卡片和命理师校准卡",
            "selection_endpoint": "/api/v30/readings/{reading_id}/practitioner/selections",
            "customer_policy": "普通用户只看主判断、必要分支和建议，不直接修改分支权重。",
            "practitioner_policy": "命理师可标记更像这个表现、作为辅助参考、暂不采用或需要追问确认；反馈只更新中枢权重和训练信号。",
            "boundary": "decision_calibration_updates_weights_not_chart_facts",
        },
        "leakage_scan": {},
        "boundary": "decision_workbench_is_user_facing_decision_orchestrator_projection",
    }
    if diagnostic:
        payload["output_runtime_contract"] = output_runtime_contract()
    scan = scan_product_payload(_scan_payload(payload), role_key=role_key)
    product_projection["leakage_scan"] = scan
    payload["leakage_scan"] = scan
    if not diagnostic:
        return payload
    return {
        **payload,
        "training_signal": {
            "version": "v30.training_signal.decision_workbench_surface.v1",
            "trainable": True,
            "targets": [
                "product_projection_readability",
                "branch_card_calibration_quality",
                "practitioner_selection_alignment",
                "ui_decision_output_actionability",
            ],
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "raw_rule_truth",
            ],
            "boundary": "decision_workbench_training_signal_trains_projection_and_policy_not_chart_facts",
        },
    }


def product_verdict_cards_from_verdicts(verdicts: list[dict[str, object]], *, role_key: str) -> list[dict[str, object]]:
    diagnostic = role_key in DIAGNOSTIC_ROLES
    rows: list[dict[str, object]] = []
    limit = 8 if diagnostic else 5
    for index, verdict in enumerate(verdicts[:limit], start=1):
        domain = str(verdict.get("domain") or "")
        allowed = [str(row) for row in _as_list(verdict.get("allowed_assertions")) if str(row)][:2]
        advice = [str(row) for row in _as_list(verdict.get("advice_points")) if str(row)][:3]
        confidence = _bounded_float(verdict.get("confidence"), 0.0)
        card = ProductVerdictCard(
            card_id=f"verdict-card:{domain or 'overall'}:{index}",
            source_verdict_id=str(verdict.get("verdict_id") or "") if diagnostic else "",
            domain=domain,
            domain_label=domain_label(domain),
            title=str(verdict.get("headline") or allowed[0] or domain_label(domain)),
            primary_text=allowed[0] if allowed else str(verdict.get("headline") or ""),
            advice_points=advice,
            confidence=confidence,
            confidence_label=_confidence_label(confidence),
            assertion_level=str(verdict.get("assertion_level") or ""),
            evidence_count=len(_as_list(verdict.get("evidence_refs"))),
            counter_evidence_count=len(_as_list(verdict.get("counter_evidence_refs"))),
            branch_hint="有备选分支" if _as_list(verdict.get("alternative_branch_ids")) else "",
            role_visibility=(
                ["practitioner", "admin", "analyst", "lab"]
                if diagnostic
                else ["guest", "user"]
            ),
            allowed_user_text=([allowed[0]] if allowed else []) + advice[:2],
            forbidden_user_text=["internal policy keys", "training/debug fields", "raw runtime status"],
            diagnostic_trace=_decision_trace(verdict) if diagnostic else {},
        )
        rows.append(_strip_empty(card.model_dump(mode="json"), diagnostic=diagnostic))
    return rows


def _product_projection_payload(
    *,
    role_key: str,
    verdict_cards: list[dict[str, object]],
    branch_cards: list[dict[str, object]],
) -> dict[str, object]:
    diagnostic = role_key in DIAGNOSTIC_ROLES
    bundle = ProductProjectionBundle(
        role_key=role_key,
        verdict_cards=[],
        branch_cards=[],
    ).model_dump(mode="json")
    return {
        **bundle,
        "contract_version": PRODUCT_CONTRACT_VERSION,
        "verdict_cards": [_strip_empty(row, diagnostic=diagnostic) for row in verdict_cards],
        "branch_cards": [_strip_empty(row, diagnostic=diagnostic) for row in branch_cards],
        "advice_cards": [],
        "probe_cards": [],
        "conversation_seeds": [],
        "surface_policy": {
            "user_reads_product_cards": True,
            "practitioner_calibrates_branch_cards": diagnostic,
            "llm_expression_after_projection": True,
            "boundary": "product_projection_surface_policy_keeps_decision_and_expression_separate",
        },
    }


def _legacy_verdict_cards(
    verdicts: list[dict[str, object]],
    product_cards: list[dict[str, object]],
    *,
    diagnostic: bool,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for verdict, product_card in zip(verdicts, product_cards, strict=False):
        rows.append(
            {
                "verdict_id": str(verdict.get("verdict_id") or "") if diagnostic else "",
                "domain": str(product_card.get("domain") or ""),
                "domain_label": str(product_card.get("domain_label") or ""),
                "headline": str(product_card.get("title") or ""),
                "assertion_level": str(product_card.get("assertion_level") or ""),
                "confidence": _bounded_float(product_card.get("confidence")),
                "primary_text": str(product_card.get("primary_text") or ""),
                "advice_points": _as_list(product_card.get("advice_points")),
                "has_alternative_branch": bool(_as_list(verdict.get("alternative_branch_ids"))),
                "next_question_count": len(_as_list(verdict.get("next_question_slots"))),
                "evidence_count": _int_count(product_card.get("evidence_count")),
                "counter_evidence_count": _int_count(product_card.get("counter_evidence_count")),
                "diagnostic_trace": _decision_trace(verdict) if diagnostic else {},
                "product_card_id": str(product_card.get("card_id") or ""),
                "boundary": "legacy_verdict_card_uses_product_verdict_card_projection",
            }
        )
    return rows


def _decision_trace(verdict: dict[str, object]) -> dict[str, object]:
    trace = verdict.get("trace", {})
    trace = trace if isinstance(trace, dict) else {}
    conflict = trace.get("conflict_resolver", {})
    conflict = conflict if isinstance(conflict, dict) else {}
    return {
        "source_candidate_id": str(trace.get("source_candidate_id") or ""),
        "source_claim_id": str(trace.get("source_claim_id") or ""),
        "candidate_signal_count": len(_as_list(trace.get("source_signal_ids"))),
        "conflict_count": _int_count(conflict.get("conflict_count")),
        "top_source_signal_count": _int_count(conflict.get("top_source_signal_count")),
        "score_mutation_allowed": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "diagnostic_trace_is_role_gated_and_read_only",
    }


def _scan_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"leakage_scan", "training_signal"}
    }


def _strip_empty(value: object, *, diagnostic: bool) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, child in value.items():
            if key == "forbidden_user_text":
                continue
            if not diagnostic and key in {
                "source_verdict_id",
                "source_conflict_id",
                "source_candidate_ids",
                "diagnostic_trace",
                "signal_bound_candidate_count",
                "candidate_signal_count",
                "practitioner_actions",
                "practitioner_summary",
            }:
                continue
            cleaned = _strip_empty(child, diagnostic=diagnostic)
            if cleaned in ("", [], {}, None):
                continue
            result[key] = cleaned
        return result
    if isinstance(value, list):
        return [
            item
            for item in (_strip_empty(row, diagnostic=diagnostic) for row in value)
            if item not in ("", [], {}, None)
        ]
    return value


def _confidence_label(value: float) -> str:
    if value >= 0.72:
        return "证据较集中"
    if value >= 0.55:
        return "证据支持"
    if value >= 0.38:
        return "需要保留边界"
    return "待校准"


def _bounded_float(value: object, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _int_count(value: object, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
