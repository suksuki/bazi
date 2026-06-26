from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime


REAL_BAZI_PRODUCT_READING_ACCEPTANCE_VERSION = "v30.real_bazi_product_reading_acceptance.v1"

REQUIRED_PRODUCT_DOMAINS = ("career", "wealth", "relationship", "health", "timing")
FORBIDDEN_GENERIC_PRIMARY_TOKENS = (
    "Current chart",
    "supports strength and pattern candidate review",
    "可以进入具体问题",
    "当前只作为候选路径",
    "fallback",
)
FORBIDDEN_CUSTOMER_INTERNAL_TOKENS = (
    "policy_effect",
    "matched_rules",
    "rule_match_id",
    "feature_evidence",
    "raw_score",
    "storage_policy",
)


def run_real_bazi_product_reading_acceptance(
    *,
    reading_id: str = "rbd-s110-product-reading-acceptance",
) -> dict[str, Any]:
    runtime = create_smoke_runtime(
        reading_id,
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    return build_real_bazi_product_reading_acceptance(
        runtime_payload=runtime.model_dump(mode="json"),
        user_view=user_view,
        admin_view=admin_view,
    )


def build_real_bazi_product_reading_acceptance(
    *,
    runtime_payload: Mapping[str, Any],
    user_view: Mapping[str, Any],
    admin_view: Mapping[str, Any],
) -> dict[str, Any]:
    surface = _mapping(user_view.get("reading_surface"))
    diagnostics = _mapping(admin_view.get("diagnostics"))
    diagnosis = _mapping(diagnostics.get("real_bazi_diagnosis"))
    answer_panel = _mapping(user_view.get("answer_panel"))
    domain_rows = [_domain_row(surface, domain) for domain in REQUIRED_PRODUCT_DOMAINS]
    checks = _checks(surface, diagnosis, answer_panel, domain_rows)
    decision = _decision(checks)
    return {
        "version": REAL_BAZI_PRODUCT_READING_ACCEPTANCE_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["product_reading_acceptance_ready"] else "blocked",
        "task": {
            "task_id": "RBD-S1.10",
            "title": "Product Reading Acceptance Closeout",
            "scope": "normal_bazi_reading_output_must_be_rbd_backed",
        },
        "runtime_summary": {
            "reading_id": str(runtime_payload.get("reading_id") or ""),
            "trace_id": str(runtime_payload.get("trace_id") or ""),
            "answer_question_id": str(answer_panel.get("question_id") or ""),
            "surface_type": str(surface.get("surface_type") or ""),
        },
        "domain_acceptance_rows": domain_rows,
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "llm_live_smoke_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "product_reading_acceptance_is_read_only_runtime_acceptance_not_release_or_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "rbd_s110_accepts_product_reading_output_without_claiming_final_destiny_truth",
    }


def _checks(
    surface: Mapping[str, Any],
    diagnosis: Mapping[str, Any],
    answer_panel: Mapping[str, Any],
    domain_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    domain_ready = all(row.get("ready") for row in domain_rows)
    customer_text = str(surface)
    answer_text = str(answer_panel.get("text") or "")
    answer_has_rbd = any(token in answer_text for token in ("财官印", "官印相生", "结构路径", "财星", "官杀", "印星"))
    answer_generic = any(token in answer_text for token in FORBIDDEN_GENERIC_PRIMARY_TOKENS)
    claims = diagnosis.get("claims", [])
    paths = diagnosis.get("paths", [])
    portraits = diagnosis.get("portraits", [])
    claims = claims if isinstance(claims, list) else []
    paths = paths if isinstance(paths, list) else []
    portraits = portraits if isinstance(portraits, list) else []
    return [
        {
            "check_id": "rbd_admin_payload_ready",
            "passed": (
                diagnosis.get("version") == "v30.real_bazi_diagnosis.runtime_integration.v1"
                and diagnosis.get("status") == "ready"
                and len(claims) >= 45
                and len(paths) >= 8
                and len(portraits) >= 20
            ),
            "observed": {
                "version": diagnosis.get("version"),
                "status": diagnosis.get("status"),
                "claim_count": len(claims),
                "path_count": len(paths),
                "portrait_count": len(portraits),
            },
        },
        {
            "check_id": "customer_surface_rbd_backed_domains",
            "passed": domain_ready,
            "observed": {
                "ready_domains": [row["domain"] for row in domain_rows if row.get("ready")],
                "failed_domains": [row["domain"] for row in domain_rows if not row.get("ready")],
            },
        },
        {
            "check_id": "structure_path_visible_and_concrete",
            "passed": _structure_path_ready(surface),
            "observed": _structure_observation(surface),
        },
        {
            "check_id": "answer_panel_uses_rbd_not_generic_template",
            "passed": bool(answer_text) and answer_has_rbd and not answer_generic,
            "observed": {
                "answer_question_id": answer_panel.get("question_id"),
                "answer_has_rbd_terms": answer_has_rbd,
                "generic_token_hit": answer_generic,
                "answer_excerpt": answer_text[:180],
            },
        },
        {
            "check_id": "customer_projection_no_rbd_internal_leak",
            "passed": not any(token in customer_text for token in FORBIDDEN_CUSTOMER_INTERNAL_TOKENS),
            "observed": {
                "forbidden_hits": [
                    token for token in FORBIDDEN_CUSTOMER_INTERNAL_TOKENS
                    if token in customer_text
                ],
            },
        },
        {
            "check_id": "full_validation_remains_explicit",
            "passed": True,
            "observed": {
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
                "llm_live_smoke_required": False,
            },
        },
    ]


def _domain_row(surface: Mapping[str, Any], domain: str) -> dict[str, Any]:
    card = _domain_card(surface, domain)
    summary = str(card.get("diagnosis_summary") or "")
    claims = card.get("diagnosis_claims", [])
    paths = card.get("diagnosis_paths", [])
    portraits = card.get("portrait_dimensions", [])
    claims = claims if isinstance(claims, list) else []
    paths = paths if isinstance(paths, list) else []
    portraits = portraits if isinstance(portraits, list) else []
    generic_hit = any(token in summary for token in FORBIDDEN_GENERIC_PRIMARY_TOKENS)
    requires_portrait = domain != "timing"
    requires_path = domain != "timing"
    ready = (
        bool(summary)
        and not generic_hit
        and len(claims) >= (3 if domain != "timing" else 2)
        and (len(paths) >= 1 if requires_path else True)
        and (len(portraits) >= 1 if requires_portrait else True)
    )
    return {
        "domain": domain,
        "ready": ready,
        "summary": summary,
        "claim_count": len(claims),
        "path_count": len(paths),
        "portrait_count": len(portraits),
        "generic_token_hit": generic_hit,
        "boundary": "domain_acceptance_requires_customer_visible_rbd_summary_claims_paths_or_portraits",
    }


def _domain_card(surface: Mapping[str, Any], domain: str) -> Mapping[str, Any]:
    cards = surface.get("domain_cards", [])
    if not isinstance(cards, list):
        return {}
    for card in cards:
        if isinstance(card, Mapping) and card.get("domain") == domain:
            return card
    return {}


def _structure_path_ready(surface: Mapping[str, Any]) -> bool:
    observed = _structure_observation(surface)
    return (
        observed["top_path_count"] >= 2
        and observed["concrete_path_count"] >= 2
        and observed["generic_token_hit"] is False
    )


def _structure_observation(surface: Mapping[str, Any]) -> dict[str, Any]:
    structure = _mapping(surface.get("structure_dynamics"))
    paths = structure.get("top_paths", [])
    paths = paths if isinstance(paths, list) else []
    statements = [
        str(row.get("diagnosis_statement") or row.get("summary") or "")
        for row in paths
        if isinstance(row, Mapping)
    ]
    concrete = [
        text for text in statements
        if any(token in text for token in ("官印", "财官印", "食伤", "财星", "官杀", "印星"))
    ]
    generic_hit = any(
        token in " ".join(statements)
        for token in FORBIDDEN_GENERIC_PRIMARY_TOKENS
    )
    return {
        "top_path_count": len(paths),
        "concrete_path_count": len(concrete),
        "generic_token_hit": generic_hit,
        "first_statement": statements[0] if statements else "",
    }


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "product_reading_acceptance_ready": ready,
        "decision_status": "rbd_s110_product_reading_accepted" if ready else "rbd_s110_product_reading_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "blockers": ["product_reading_acceptance_checks_failed"] if failed else [],
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "RBD-backed product reading is accepted for the normal reading path."
            if ready
            else "RBD-backed product reading is blocked until failed checks are fixed."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("product_reading_acceptance_ready"):
        return {
            "task_id": "RBD-S1.11",
            "title": "Real-Case Distribution Replay For RBD",
            "selected_track": "real_bazi_diagnosis",
            "scope": [
                "run lightweight real-case and 518K sample replay against RBD acceptance metrics",
                "track generic-language rate and domain coverage",
                "keep full 518K explicit-only",
            ],
        }
    return {
        "task_id": "RBD-S1.10-FR",
        "title": "Product Reading Acceptance Failure Review",
        "selected_track": "real_bazi_diagnosis",
        "scope": ["repair failed product-reading acceptance checks before replay expansion"],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
