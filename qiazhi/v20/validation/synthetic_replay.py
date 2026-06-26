from __future__ import annotations

from typing import Any

from v20.access.projection import project_runtime_for_role
from v20.api.runtime import run_runtime_from_pillars
from v20.validation.synthetic_schema import SyntheticBaziCase, minimal_synthetic_bazi_cases


DEFAULT_REPLAY_ROLES: tuple[str, ...] = ("guest", "user", "analyst", "admin")


def replay_synthetic_bazi_case(
    case: SyntheticBaziCase,
    *,
    role_keys: tuple[str, ...] = DEFAULT_REPLAY_ROLES,
) -> dict[str, Any]:
    runtime = run_runtime_from_pillars(
        *case.pillar_displays,
        input_id=case.case_id,
        question_key=_first(case.expected.question_keys),
        flow_year_pillar=str(case.time_context.get("flow_year_pillar") or ""),
        luck_pillar=str(case.time_context.get("luck_pillar") or ""),
        flow_month_pillar=str(case.time_context.get("flow_month_pillar") or ""),
        llm_mode="deterministic",
    )
    role_views = {
        role_key: project_runtime_for_role(runtime, role_key)
        for role_key in role_keys
    }
    actual = normalize_synthetic_runtime_actual(runtime, role_views=role_views)
    return {
        "version": "v20.synthetic_bazi_case_replay.v1",
        "case_id": case.case_id,
        "case_type": case.case_type,
        "target_pattern": case.target_pattern,
        "actual": actual,
        "role_view_count": len(role_views),
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_REPLAY_IS_DRY_RUN",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_POLICY_POINTER_MUTATION",
            "NO_LLM_EXECUTION",
        ],
    }


def run_synthetic_bazi_replay(
    cases: tuple[SyntheticBaziCase, ...] | None = None,
    *,
    max_cases: int | None = None,
    role_keys: tuple[str, ...] = DEFAULT_REPLAY_ROLES,
) -> dict[str, Any]:
    selected = tuple(cases or minimal_synthetic_bazi_cases())
    if max_cases is not None and max_cases > 0:
        selected = selected[:max_cases]
    results = [replay_synthetic_bazi_case(case, role_keys=role_keys) for case in selected]
    role_answer_governance = _role_answer_governance_summary(results)
    return {
        "version": "v20.synthetic_bazi_replay_report.v1",
        "case_count": len(results),
        "input_case_count": len(cases or minimal_synthetic_bazi_cases()),
        "role_keys": role_keys,
        "role_answer_governance_summary": role_answer_governance,
        "results": results,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_REPLAY_REPORT_ONLY",
            "ROLE_ANSWER_GOVERNANCE_FEEDS_TRAINING_SIGNAL",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_POLICY_POINTER_MUTATION",
        ],
    }


def normalize_synthetic_runtime_actual(
    runtime: dict[str, Any],
    *,
    role_views: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    feature_domains = _feature_domains(runtime)
    decision_domains = _decision_domains(runtime)
    portrait_labels = _portrait_labels(runtime)
    questions = _questions(runtime)
    roles = {
        role_key: _role_view_summary(role_key, view)
        for role_key, view in (role_views or {}).items()
    }
    return {
        "version": "v20.synthetic_runtime_actual.v1",
        "feature_domains": feature_domains,
        "decision_domains": decision_domains,
        "portrait_labels": portrait_labels,
        "question_keys": tuple(row["question_key"] for row in questions if row["question_key"]),
        "question_domains": tuple(sorted({row["domain"] for row in questions if row["domain"]})),
        "question_stages": tuple(sorted({row["stage"] for row in questions if row["stage"]})),
        "selected_question_key": _dict_str(runtime.get("selected_question"), "question_key"),
        "answer_text": str(runtime.get("answer_text") or ""),
        "role_views": roles,
        "runtime_mutation": False,
        "guardrails": [
            "NORMALIZED_ACTUAL_IS_REPLAY_MATERIAL",
            "NO_PRIVATE_TEXT_CAPTURED",
            "NO_RUNTIME_MUTATION",
        ],
    }


def _role_view_summary(role_key: str, view: dict[str, Any]) -> dict[str, Any]:
    questions = _questions(view)
    role_view_model = view.get("role_view_model", {})
    question_profile = role_view_model.get("question_profile", {}) if isinstance(role_view_model, dict) else {}
    visibility_profile = role_view_model.get("visibility_profile", {}) if isinstance(role_view_model, dict) else {}
    answer_profile = view.get("role_answer_profile", {})
    answer_governance = answer_profile.get("answer_governance_profile", {}) if isinstance(answer_profile, dict) else {}
    if not isinstance(answer_governance, dict):
        answer_governance = {}
    return {
        "role_key": role_key,
        "question_count": len(questions),
        "question_keys": tuple(row["question_key"] for row in questions if row["question_key"]),
        "question_stages": tuple(sorted({row["stage"] for row in questions if row["stage"]})),
        "question_style": _dict_str(question_profile, "style"),
        "voice_profile": _dict_str(question_profile, "voice_profile"),
        "question_narrative_quality": _question_narrative_quality(questions),
        "visibility_level": _dict_str(visibility_profile, "level"),
        "answer_governance_quality_band": str(answer_governance.get("quality_band", "")),
        "answer_governance_quality_score": float(answer_governance.get("quality_score", 0.0) or 0.0),
        "answer_boundary_density": str(answer_governance.get("boundary_density", "")),
        "answer_style_policy": str(answer_governance.get("style_policy", "")),
        "runtime_mutation": False,
    }


def _question_narrative_quality(questions: list[dict[str, Any]]) -> dict[str, Any]:
    if not questions:
        return {
            "version": "v20.question_narrative_replay_quality.v1",
            "question_count": 0,
            "ready_count": 0,
            "ready_ratio": 0.0,
            "missing_fields": ("questions",),
        }
    required = ("voice_profile", "why_now", "bazi_basis", "boundary", "next_step")
    ready_count = 0
    missing: list[str] = []
    for question in questions:
        narrative = question.get("question_narrative", {})
        if not isinstance(narrative, dict):
            missing.append("question_narrative")
            continue
        row_missing = [field for field in required if not str(narrative.get(field, "")).strip()]
        if row_missing:
            missing.extend(row_missing)
            continue
        ready_count += 1
    return {
        "version": "v20.question_narrative_replay_quality.v1",
        "question_count": len(questions),
        "ready_count": ready_count,
        "ready_ratio": round(ready_count / max(1, len(questions)), 4),
        "missing_fields": tuple(sorted(set(missing))),
        "runtime_mutation": False,
    }


def _role_answer_governance_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for result in results:
        actual = result.get("actual", {})
        role_views = actual.get("role_views", {}) if isinstance(actual, dict) else {}
        for role_key, view in role_views.items() if isinstance(role_views, dict) else ():
            if not isinstance(view, dict):
                continue
            rows.append(
                {
                    "role_key": str(role_key),
                    "quality_score": float(view.get("answer_governance_quality_score", 0.0) or 0.0),
                    "quality_band": str(view.get("answer_governance_quality_band", "")),
                    "boundary_density": str(view.get("answer_boundary_density", "")),
                    "style_policy": str(view.get("answer_style_policy", "")),
                }
            )
    missing_profile = [
        row["role_key"]
        for row in rows
        if not row["quality_band"] or not row["boundary_density"] or not row["style_policy"]
    ]
    return {
        "version": "v20.role_answer_governance_replay_summary.v1",
        "role_view_count": len(rows),
        "average_quality_score": round(sum(row["quality_score"] for row in rows) / max(1, len(rows)), 4),
        "missing_profile_count": len(missing_profile),
        "missing_profile_roles": tuple(sorted(set(missing_profile))),
        "boundary_density_counts": _count_by(rows, "boundary_density"),
        "style_policy_counts": _count_by(rows, "style_policy"),
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_ANSWER_GOVERNANCE_REPLAY_SIGNAL_ONLY",
            "TRAINING_CAN_CONSUME_WITHOUT_HUMAN_REVIEW",
        ],
    }


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _feature_domains(runtime: dict[str, Any]) -> tuple[str, ...]:
    feature_layer = runtime.get("feature_layer", {})
    features = feature_layer.get("features", ()) if isinstance(feature_layer, dict) else ()
    return tuple(sorted({str(row.get("domain") or "") for row in features if isinstance(row, dict) and row.get("domain")}))


def _decision_domains(runtime: dict[str, Any]) -> tuple[str, ...]:
    decision_report = runtime.get("decision_report", {})
    decisions = decision_report.get("decisions", ()) if isinstance(decision_report, dict) else ()
    domains = {str(row.get("domain") or "") for row in decisions if isinstance(row, dict) and row.get("domain")}
    return tuple(sorted(domains))


def _portrait_labels(runtime: dict[str, Any]) -> tuple[str, ...]:
    decision_report = runtime.get("decision_report", {})
    portrait = decision_report.get("portrait_projection", {}) if isinstance(decision_report, dict) else {}
    axes = portrait.get("axes", ()) if isinstance(portrait, dict) else ()
    return tuple(str(row.get("label") or row.get("axis_id") or "") for row in axes if isinstance(row, dict))


def _questions(runtime: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = runtime.get("questions", ())
    questions: list[dict[str, Any]] = []
    for row in rows if isinstance(rows, (list, tuple)) else ():
        if not isinstance(row, dict):
            continue
        stage = str(row.get("question_stage") or row.get("measurement_stage") or row.get("role_view_level") or "")
        questions.append(
            {
                "question_key": str(row.get("question_key") or ""),
                "question_id": str(row.get("question_id") or ""),
                "domain": str(row.get("domain") or ""),
                "stage": stage,
                "question_narrative": row.get("question_narrative", {}) if isinstance(row.get("question_narrative"), dict) else {},
            }
        )
    return tuple(questions)


def _dict_str(payload: Any, key: str) -> str:
    return str(payload.get(key) or "") if isinstance(payload, dict) else ""


def _first(values: tuple[str, ...]) -> str:
    return str(values[0]) if values else ""
