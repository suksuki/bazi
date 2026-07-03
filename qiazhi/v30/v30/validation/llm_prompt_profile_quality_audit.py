from __future__ import annotations

from v30.llm import build_thinking_step_prompt_request
from v30.presentation.thinking import build_thinking_projection
from v30.runtime import create_smoke_runtime


LLM_PROMPT_PROFILE_QUALITY_AUDIT_VERSION = "v30.llm_prompt_profile_quality_audit.v1"

_GENERIC_SELF_CHECK_TOKENS = (
    "Is it concrete",
    "Is the structure correct",
    "required keys",
    "JSON with",
    "schema",
)


def run_llm_prompt_profile_quality_audit(reading_id: str = "llm-prompt-profile-quality-audit") -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id, locale="zh")
    thinking = build_thinking_projection(runtime)
    stage_results = []
    for step in thinking.get("steps", []):
        if not isinstance(step, dict):
            continue
        request = build_thinking_step_prompt_request(
            runtime,
            step,
            role_key="admin",
            locale="zh",
            client="admin",
        )
        stage_results.append(_stage_result(step, request))
    checks = [
        {
            "check_id": "every_stage_has_prompt_profile",
            "passed": bool(stage_results) and all(row["profile_id"] for row in stage_results),
            "observed": {"stage_count": len(stage_results)},
        },
        {
            "check_id": "prompt_profiles_are_stage_local",
            "passed": all(row["stage_local"] for row in stage_results),
            "observed": {row["stage_id"]: row["stage_local"] for row in stage_results},
        },
        {
            "check_id": "stage_point_and_option_context_available",
            "passed": all(row["stage_point_context_ready"] for row in stage_results)
            and any(row["option_context_count"] > 0 for row in stage_results),
            "observed": {
                row["stage_id"]: {
                    "stage_points": row["stage_point_count"],
                    "option_sets": row["option_context_count"],
                }
                for row in stage_results
            },
        },
        {
            "check_id": "prompt_contract_blocks_runtime_mutation",
            "passed": all(row["chart_fact_mutation_allowed"] is False for row in stage_results),
            "observed": {row["stage_id"]: row["chart_fact_mutation_allowed"] for row in stage_results},
        },
        {
            "check_id": "self_check_template_language_not_in_profiles",
            "passed": all(not row["self_check_template_risk"] for row in stage_results),
            "observed": {
                row["stage_id"]: row["self_check_template_risk"]
                for row in stage_results
                if row["self_check_template_risk"]
            },
        },
    ]
    ready = all(row["passed"] for row in checks)
    return {
        "version": LLM_PROMPT_PROFILE_QUALITY_AUDIT_VERSION,
        "status": "completed" if ready else "blocked",
        "stage_count": len(stage_results),
        "stage_results": stage_results,
        "checks": checks,
        "quality_examples": _quality_examples(stage_results),
        "live_smoke": {
            "llm_execution_performed": False,
            "latency_ms": None,
            "candidate_count": None,
            "hard_failure_count": None,
            "reason": "offline_contract_audit_first_live_smoke_can_record_same_fields",
        },
        "decision": {
            "prompt_profile_quality_ready": ready,
            "live_llm_smoke_required_next": True,
            "chart_fact_mutation_allowed": False,
        },
        "boundary": "llm_prompt_profile_quality_audit_checks_context_and_contract_without_executing_llm",
    }


def _stage_result(step: dict[str, object], request: dict[str, object]) -> dict[str, object]:
    context = request.get("context_pack", {})
    context = context if isinstance(context, dict) else {}
    profile = context.get("prompt_profile", {})
    profile = profile if isinstance(profile, dict) else {}
    stage = context.get("stage", {})
    stage = stage if isinstance(stage, dict) else {}
    point_set = stage.get("stage_point_set", {})
    point_set = point_set if isinstance(point_set, dict) else {}
    option_projection = point_set.get("text_option_projection", {})
    option_projection = option_projection if isinstance(option_projection, dict) else {}
    prompt_text = " ".join(
        str(profile.get(key) or "")
        for key in ("scene", "task", "answer_shape")
    )
    prompt_text += " " + " ".join(str(row) for row in profile.get("avoid", []) if row)
    return {
        "stage_id": str(step.get("step_id") or ""),
        "title": str(step.get("title") or ""),
        "profile_id": str(profile.get("profile_id") or ""),
        "scene": str(profile.get("scene") or ""),
        "answer_shape": str(profile.get("answer_shape") or ""),
        "stage_local": _profile_is_stage_local(profile, stage_id=str(step.get("step_id") or "")),
        "stage_point_context_ready": bool(point_set.get("selected_count") is not None),
        "stage_point_count": int(point_set.get("selected_count") or 0),
        "option_context_count": int(option_projection.get("option_set_count") or 0),
        "context_pack": str(context.get("context_pack") or ""),
        "module_context_rows": len(context.get("module_context", [])) if isinstance(context.get("module_context"), list) else 0,
        "chart_fact_mutation_allowed": bool(request.get("chart_fact_mutation_allowed")),
        "self_check_template_risk": any(token.lower() in prompt_text.lower() for token in _GENERIC_SELF_CHECK_TOKENS),
        "boundary": "stage_prompt_profile_quality_row_is_offline_contract_observation",
    }


def _profile_is_stage_local(profile: dict[str, object], *, stage_id: str) -> bool:
    if stage_id == "final_report":
        return str(profile.get("scene") or "") == "final_stage_synthesis"
    text = " ".join(
        [
            str(profile.get("task") or ""),
            str(profile.get("answer_shape") or ""),
            " ".join(str(row) for row in profile.get("avoid", []) if row),
        ]
    )
    return "跨页" in text or "本页" in text or "stage" in text.lower()


def _quality_examples(stage_results: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in stage_results[:6]:
        rows.append({
            "stage_id": row["stage_id"],
            "profile_id": row["profile_id"],
            "quality_target": "本页证据 -> 本页机制 -> 明确结论/建议",
            "option_context_count": row["option_context_count"],
        })
    return rows
