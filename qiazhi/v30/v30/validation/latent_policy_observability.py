from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime


LATENT_POLICY_OBSERVABILITY_VERSION = "v30.latent_policy_observability_readiness.v1"


def run_latent_policy_observability_readiness(
    *,
    reading_id: str = "hf-r25-latent-policy-observability",
) -> dict[str, Any]:
    runtime = create_smoke_runtime(
        reading_id,
        policy_payload_overrides={
            "question_policy": _latent_policy_payload(),
            "rule_policy": _latent_policy_payload(),
        },
        active_policy_version_overrides={
            "question_policy": "question_policy.hf-r25-latent-observability",
            "rule_policy": "rule_policy.hf-r25-latent-observability",
        },
    )
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    return build_latent_policy_observability_readiness(
        runtime_payload=runtime.model_dump(mode="json"),
        user_view=user_view,
        admin_view=admin_view,
    )


def build_latent_policy_observability_readiness(
    *,
    runtime_payload: Mapping[str, Any],
    user_view: Mapping[str, Any],
    admin_view: Mapping[str, Any],
) -> dict[str, Any]:
    admin_diag = _mapping(admin_view.get("diagnostics"))
    observability = _mapping(admin_diag.get("latent_policy_observability"))
    user_rendered = str(
        {
            "reading_surface": user_view.get("reading_surface", {}),
            "questions": user_view.get("questions", []),
            "answer_panel": user_view.get("answer_panel", {}),
            "diagnostics": user_view.get("diagnostics", {}),
        }
    )
    checks = _checks(runtime_payload=runtime_payload, user_rendered=user_rendered, observability=observability)
    decision = _decision(checks)
    return {
        "version": LATENT_POLICY_OBSERVABILITY_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "task": {
            "task_id": "HF-R2.5",
            "title": "Latent Policy Observability And Admin Validation Surface",
            "scope": "admin-visible latent Bazi attribute policy, affected questions, and no-chart-fact training boundary",
        },
        "observability": observability,
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "pointer_promotion_allowed": False,
            "boundary": "hf_r25_is_observability_and_validation_surface_not_policy_promotion",
        },
        "next_mainline_selection": {
            "task_id": "HF-R2.6" if decision["readiness_ready"] else "HF-R2.5-FIX",
            "title": "Latent Attribute Admin Training Review" if decision["readiness_ready"] else "Repair Latent Policy Observability",
            "scope": [
                "connect observability rows to admin/training UI",
                "keep latent policy training bounded to personalization and question strategy",
            ] if decision["readiness_ready"] else [
                "repair missing admin observability, influenced-question rows, or no-mutation boundaries",
            ],
        },
        "boundary": "latent_policy_observability_readiness_validates_admin_visibility_without_reopening_core_bazi_facts",
    }


def _checks(
    *,
    runtime_payload: Mapping[str, Any],
    user_rendered: str,
    observability: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "admin_latent_policy_observability_present",
            "passed": observability.get("version") == "v30.latent_policy_observability.v1",
            "observed": {
                "version": observability.get("version"),
                "status": observability.get("status"),
                "customer_visible": observability.get("customer_visible"),
            },
        },
        {
            "check_id": "question_and_rule_policy_visible",
            "passed": bool(_mapping(observability.get("question_policy"))) and bool(_mapping(observability.get("rule_policy"))),
            "observed": {
                "question_source": _mapping(observability.get("question_policy")).get("source_signal_id"),
                "rule_source": _mapping(observability.get("rule_policy")).get("source_signal_id"),
            },
        },
        {
            "check_id": "influenced_questions_are_diagnosable",
            "passed": int(observability.get("influenced_question_count") or 0) >= 1,
            "observed": {
                "count": observability.get("influenced_question_count"),
                "questions": observability.get("influenced_questions", []),
            },
        },
        {
            "check_id": "training_boundary_blocks_chart_facts",
            "passed": _training_boundary_ok(_mapping(observability.get("training_boundary"))),
            "observed": observability.get("training_boundary", {}),
        },
        {
            "check_id": "customer_projection_hides_latent_policy_observability",
            "passed": "latent_policy_observability" not in user_rendered
            and "latent_bazi_attribute_policy" not in user_rendered,
            "observed": {
                "latent_policy_observability_visible": "latent_policy_observability" in user_rendered,
                "latent_bazi_attribute_policy_visible": "latent_bazi_attribute_policy" in user_rendered,
            },
        },
        {
            "check_id": "runtime_chart_facts_remain_deterministic",
            "passed": _runtime_fingerprint_ready(runtime_payload),
            "observed": {
                "day_master": _nested(runtime_payload, "chart_context", "day_master"),
                "day_master_element": _nested(runtime_payload, "chart_context", "day_master_element"),
                "natal_pillar_count": len(_mapping(_nested(runtime_payload, "chart_context", "natal_pillars")).get("pillars", {})),
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    return {
        "readiness_ready": not failed,
        "decision_status": "hf_r25_latent_policy_observability_ready" if not failed else "hf_r25_latent_policy_observability_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "rationale": (
            "Admin can inspect latent policy influence and training boundaries without exposing it to customer views."
            if not failed
            else "Repair latent policy observability before using it as a training/admin review surface."
        ),
    }


def _training_boundary_ok(boundary: Mapping[str, Any]) -> bool:
    blocked = set(str(row) for row in boundary.get("blocked_training_routes", []) if row)
    return (
        boundary.get("can_tune_latent_inference") is True
        and boundary.get("can_tune_question_strategy") is True
        and boundary.get("can_tune_individualized_projection") is True
        and boundary.get("can_tune_chart_facts") is False
        and boundary.get("chart_fact_mutation_allowed") is False
        and {"chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"} <= blocked
    )


def _runtime_fingerprint_ready(runtime_payload: Mapping[str, Any]) -> bool:
    context = _mapping(runtime_payload.get("chart_context"))
    natal = _mapping(context.get("natal_pillars"))
    pillars = _mapping(natal.get("pillars"))
    return bool(context.get("day_master")) and bool(context.get("day_master_element")) and len(pillars) == 4


def _latent_policy_payload() -> dict[str, Any]:
    return {
        "weights": {
            "latent_bazi_attribute_policy": {
                "version": "v30.latent_bazi_attribute_policy.v1",
                "mode": "latent_personalization_candidate_not_chart_fact",
                "source_signal_id": "v30.training_signal.latent_bazi_attribute_alignment",
                "reverse_inference_weight": 1.08,
                "question_need_weight": 1.08,
                "individualized_projection_weight": 1.06,
                "domain_bias_weights": {"career_bias": 1.03, "wealth_bias": 1.03, "relationship_bias": 1.02},
                "ten_god_modifier_weights": {"authority": 1.03, "resource": 1.03, "wealth": 1.02},
                "global_attribute_weights": {"resource_index": 1.03, "risk_index": 1.02, "stability_index": 1.02},
                "blocked_training_routes": ["calendar_conversion", "chart_facts", "flow_timing", "luck_cycle"],
                "can_tune_latent_inference": True,
                "can_tune_question_strategy": True,
                "can_tune_individualized_projection": True,
                "can_tune_chart_facts": False,
                "boundary": "latent_bazi_attribute_policy_trains_personalization_not_chart_facts",
            }
        }
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _nested(payload: Mapping[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current
