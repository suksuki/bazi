from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from v30.brain import build_recommendation_brain_context
from v30.config import V30Settings, load_settings
from v30.contracts import CoreRuntimeResult, V30Model
from v30.knowledge import KnowledgeRulePortraitSignal
from v30.questions import recommend_questions


QUESTION_POLICY_COMPARISON_VERSION = "v30.question_policy_comparison.v1"


class QuestionPolicyDecisionDelta(V30Model):
    question_id: str
    active_rank: int | None = None
    candidate_rank: int | None = None
    rank_delta: int | None = None
    active_score: float = 0.0
    candidate_score: float = 0.0
    score_delta: float = 0.0
    active_policy_weight: float = 1.0
    candidate_policy_weight: float = 1.0
    policy_weight_delta: float = 0.0
    active_reasons: list[str] = Field(default_factory=list)
    candidate_reasons: list[str] = Field(default_factory=list)
    added_reasons: list[str] = Field(default_factory=list)
    removed_reasons: list[str] = Field(default_factory=list)


class QuestionPolicyComparisonArtifact(V30Model):
    comparison_id: str
    version: str
    reading_id: str
    trace_id: str
    candidate_id: str
    active_question_policy_id: str
    candidate_question_policy_id: str
    active_top_question_id: str | None = None
    candidate_top_question_id: str | None = None
    top_question_changed: bool = False
    changed_rank_count: int = 0
    weighted_delta_count: int = 0
    max_score_delta: float = 0.0
    max_policy_weight_delta: float = 0.0
    decision_deltas: list[QuestionPolicyDecisionDelta] = Field(default_factory=list)
    summary: dict[str, object] = Field(default_factory=dict)
    artifact_uri: str | None = None
    artifact_record_id: str | None = None
    artifact_search_backend: str = "json_fallback"
    artifact_searchable: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    boundaries: list[str] = Field(default_factory=list)


def build_question_policy_comparison(
    runtime: CoreRuntimeResult,
    *,
    candidate_id: str,
    candidate_payload: dict[str, Any],
    candidate_question_policy_id: str,
) -> QuestionPolicyComparisonArtifact:
    active_rows = runtime.question_plan.recommended_questions
    candidate_rows = _candidate_recommendations(
        runtime,
        candidate_payload=candidate_payload,
        candidate_question_policy_id=candidate_question_policy_id,
    )
    deltas = _decision_deltas(active_rows, candidate_rows)
    active_top = str(active_rows[0].get("question_id")) if active_rows else None
    candidate_top = str(candidate_rows[0].get("question_id")) if candidate_rows else None
    active_policy_id = str(
        (active_rows[0].get("policy_version") if active_rows else "")
        or _dict(runtime.question_plan.policy_effect.get("active_policy_versions")).get("question_policy")
        or ""
    )
    return QuestionPolicyComparisonArtifact(
        comparison_id=f"{candidate_id}:question-policy-comparison",
        version=QUESTION_POLICY_COMPARISON_VERSION,
        reading_id=runtime.reading_id,
        trace_id=runtime.trace_id,
        candidate_id=candidate_id,
        active_question_policy_id=active_policy_id,
        candidate_question_policy_id=candidate_question_policy_id,
        active_top_question_id=active_top,
        candidate_top_question_id=candidate_top,
        top_question_changed=active_top != candidate_top,
        changed_rank_count=sum(1 for row in deltas if row.rank_delta not in {None, 0}),
        weighted_delta_count=sum(1 for row in deltas if row.policy_weight_delta != 0.0),
        max_score_delta=max((abs(row.score_delta) for row in deltas), default=0.0),
        max_policy_weight_delta=max((abs(row.policy_weight_delta) for row in deltas), default=0.0),
        decision_deltas=deltas,
        summary={
            "active_decision_count": len(active_rows),
            "candidate_decision_count": len(candidate_rows),
            "top_question_changed": active_top != candidate_top,
            "candidate_weight_buckets": sorted(_dict(candidate_payload.get("weights")).keys()),
            "boundary": "question_policy_comparison_diagnostic_not_runtime_mutation",
        },
        boundaries=[
            "question_policy_comparison_is_candidate_diagnostic_not_chart_fact",
            "comparison_recomputes_recommendations_without_mutating_runtime_trace",
            "promotion_still_requires_synthetic_all_and_518k_sample",
        ],
    )


def persist_question_policy_comparison(
    comparison: QuestionPolicyComparisonArtifact,
    *,
    settings: V30Settings | None = None,
) -> QuestionPolicyComparisonArtifact:
    settings = settings or load_settings()
    root = settings.runtime_dir / "validation" / "question_policy_comparisons"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{_safe_file_id(comparison.candidate_id)}.json"
    comparison = comparison.model_copy(update={"artifact_uri": str(path)})
    from v30.storage.artifacts import index_question_policy_comparison_artifact

    search_meta = index_question_policy_comparison_artifact(comparison, settings=settings)
    comparison = comparison.model_copy(
        update={
            "artifact_record_id": search_meta.artifact_record_id,
            "artifact_search_backend": search_meta.artifact_search_backend,
            "artifact_searchable": search_meta.artifact_searchable,
        }
    )
    path.write_text(json.dumps(comparison.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    _write_index(root, comparison)
    return comparison


def load_question_policy_comparison(
    *,
    candidate_id: str | None = None,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    settings = settings or load_settings()
    root = settings.runtime_dir / "validation" / "question_policy_comparisons"
    if candidate_id:
        path = root / f"{_safe_file_id(candidate_id)}.json"
        return _load_json(path)
    index = _load_json(root / "index.json")
    latest_id = str(index.get("latest_candidate_id") or "")
    if not latest_id:
        return {}
    return _load_json(root / f"{_safe_file_id(latest_id)}.json")


def _candidate_recommendations(
    runtime: CoreRuntimeResult,
    *,
    candidate_payload: dict[str, Any],
    candidate_question_policy_id: str,
) -> list[dict[str, object]]:
    active_versions = _dict(runtime.question_plan.policy_effect.get("active_policy_versions"))
    active_versions["question_policy"] = candidate_question_policy_id
    hidden_factor_state = _dict(runtime.question_plan.policy_effect.get("hidden_factor_state"))
    hidden_factor_calibration = _dict(runtime.question_plan.policy_effect.get("hidden_factor_calibration"))
    hidden_factor_status = str(hidden_factor_state.get("status") or hidden_factor_calibration.get("status") or "unknown")
    central_brain_context = build_recommendation_brain_context(
        reading_id=runtime.reading_id,
        role_key=runtime.question_plan.role_key,
        active_mainline_id=runtime.mainline_state.mainline_id,
        time_status=str(runtime.chart_context.time_layers.get("status", "not_provided")),
        hidden_factor_status=hidden_factor_status,
    )
    return recommend_questions(
        runtime.question_anchors,
        structure=runtime.structure_state,
        mainline=runtime.mainline_state,
        evidence=runtime.feature_evidence,
        active_policy_versions={str(key): str(value) for key, value in active_versions.items()},
        knowledge_rule_portrait_signals=[
            KnowledgeRulePortraitSignal.model_validate(row)
            for row in runtime.question_plan.knowledge_rule_portrait_signals
        ],
        macro_dimension_signals=_list_dict(runtime.question_plan.policy_effect.get("macro_dimension_signals")),
        question_policy=candidate_payload,
        hidden_factor_state=hidden_factor_state,
        question_outcomes=_list_dict(runtime.question_plan.session_state.get("question_outcomes")),
        central_brain_context=central_brain_context,
        practical_reading_context=_dict(runtime.question_plan.policy_effect.get("practical_reading_context")),
        model_signal_summary=_dict(runtime.question_plan.policy_effect.get("model_signal_summary")),
    )


def _decision_deltas(
    active_rows: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
) -> list[QuestionPolicyDecisionDelta]:
    active_by_question = {str(row.get("question_id")): (index, row) for index, row in enumerate(active_rows, start=1)}
    candidate_by_question = {str(row.get("question_id")): (index, row) for index, row in enumerate(candidate_rows, start=1)}
    question_ids = sorted(set(active_by_question) | set(candidate_by_question))
    rows: list[QuestionPolicyDecisionDelta] = []
    for question_id in question_ids:
        active_rank, active = active_by_question.get(question_id, (None, {}))
        candidate_rank, candidate = candidate_by_question.get(question_id, (None, {}))
        active_score = _float(active.get("score"))
        candidate_score = _float(candidate.get("score"))
        active_weight = _float(active.get("policy_weight"), default=1.0)
        candidate_weight = _float(candidate.get("policy_weight"), default=1.0)
        active_reasons = _str_list(active.get("reasons"))
        candidate_reasons = _str_list(candidate.get("reasons"))
        rows.append(
            QuestionPolicyDecisionDelta(
                question_id=question_id,
                active_rank=active_rank,
                candidate_rank=candidate_rank,
                rank_delta=(active_rank - candidate_rank) if active_rank is not None and candidate_rank is not None else None,
                active_score=active_score,
                candidate_score=candidate_score,
                score_delta=round(candidate_score - active_score, 3),
                active_policy_weight=active_weight,
                candidate_policy_weight=candidate_weight,
                policy_weight_delta=round(candidate_weight - active_weight, 3),
                active_reasons=active_reasons,
                candidate_reasons=candidate_reasons,
                added_reasons=sorted(set(candidate_reasons) - set(active_reasons)),
                removed_reasons=sorted(set(active_reasons) - set(candidate_reasons)),
            )
        )
    return sorted(rows, key=lambda row: (row.candidate_rank or 9999, row.active_rank or 9999, row.question_id))


def _write_index(root: Path, comparison: QuestionPolicyComparisonArtifact) -> None:
    index_path = root / "index.json"
    index = _load_json(index_path)
    entries = [row for row in index.get("entries", []) if isinstance(row, dict)]
    entries = [row for row in entries if row.get("candidate_id") != comparison.candidate_id]
    entries.append(
        {
            "candidate_id": comparison.candidate_id,
            "comparison_id": comparison.comparison_id,
            "artifact_uri": comparison.artifact_uri,
            "artifact_record_id": comparison.artifact_record_id,
            "artifact_search_backend": comparison.artifact_search_backend,
            "artifact_searchable": comparison.artifact_searchable,
            "active_question_policy_id": comparison.active_question_policy_id,
            "candidate_question_policy_id": comparison.candidate_question_policy_id,
            "top_question_changed": comparison.top_question_changed,
            "changed_rank_count": comparison.changed_rank_count,
            "weighted_delta_count": comparison.weighted_delta_count,
            "created_at": comparison.created_at.isoformat(),
        }
    )
    index_path.write_text(
        json.dumps(
            {
                "index_id": "v30.question_policy_comparison_index.v1",
                "latest_candidate_id": comparison.candidate_id,
                "run_count": len(entries),
                "entries": entries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list_dict(value: object) -> list[dict[str, object]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _float(value: object, *, default: float = 0.0) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def _safe_file_id(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")
