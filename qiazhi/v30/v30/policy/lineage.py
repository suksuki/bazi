from __future__ import annotations

from typing import Any

from pydantic import Field

from v30.config import V30Settings
from v30.contracts import V30Model
from v30.policy.runtime_pointer import PolicyFamily, RuntimePointerStore
from v30.storage.artifacts import search_validation_artifacts


PROMOTION_LINEAGE_VERSION = "v30.promotion_lineage.v1"
LINEAGE_POLICY_FAMILIES: tuple[PolicyFamily, ...] = (
    "structure_policy",
    "mainline_policy",
    "question_policy",
    "rule_policy",
)


class PromotionLineageGraph(V30Model):
    lineage_id: str
    version: str
    family: PolicyFamily
    active_artifact_id: str
    previous_artifact_id: str = ""
    candidate_id: str
    validation_run_id: str = ""
    runtime_pointer: dict[str, Any] = Field(default_factory=dict)
    policy_artifact_summary: dict[str, Any] = Field(default_factory=dict)
    validation_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    active_runtime_trace_summary: dict[str, Any] = Field(default_factory=dict)
    rollback_pointer: dict[str, Any] = Field(default_factory=dict)
    boundaries: list[str] = Field(default_factory=list)


def build_promotion_lineage(
    *,
    family: PolicyFamily,
    settings: V30Settings | None = None,
    store: RuntimePointerStore | None = None,
) -> PromotionLineageGraph:
    from v30.runtime import create_smoke_runtime

    store = store or RuntimePointerStore(settings)
    pointer = store.load_pointer(family)
    artifact = store.load_artifact(family, pointer.active_artifact_id)
    runtime = create_smoke_runtime(
        reading_id=f"v30-lineage-{family}",
        policy_payload_overrides=_active_policy_payloads(store),
        active_policy_version_overrides=store.active_versions(LINEAGE_POLICY_FAMILIES),
    )
    return PromotionLineageGraph(
        lineage_id=f"{family}:{pointer.active_artifact_id}:lineage",
        version=PROMOTION_LINEAGE_VERSION,
        family=family,
        active_artifact_id=pointer.active_artifact_id,
        previous_artifact_id=pointer.previous_artifact_id,
        candidate_id=artifact.candidate_id,
        validation_run_id=pointer.validation_run_id,
        runtime_pointer=pointer.model_dump(mode="json"),
        policy_artifact_summary=_policy_artifact_summary(artifact.model_dump(mode="json")),
        validation_artifacts=_validation_artifacts(
            settings=settings or getattr(store, "_settings", None),
            family=family,
            candidate_id=artifact.candidate_id,
            artifact_payload=artifact.model_dump(mode="json"),
        ),
        active_runtime_trace_summary=_runtime_trace_summary(runtime, family),
        rollback_pointer=pointer.rollback_pointer,
        boundaries=[
            "promotion_lineage_is_diagnostic_not_policy_mutation",
            "promotion_lineage_does_not_create_chart_facts",
            "promotion_lineage_reads_existing_pointer_artifact_validation_and_trace_state",
        ],
    )


def _active_policy_payloads(store: RuntimePointerStore) -> dict[str, dict[str, object]]:
    payloads: dict[str, dict[str, object]] = {}
    for family in LINEAGE_POLICY_FAMILIES:
        artifact = store.load_active_artifact(family)
        payloads[family] = artifact.payload
    return payloads


def _policy_artifact_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    validation = artifact.get("validation_summary", {})
    metrics = artifact.get("metrics", {})
    payload = artifact.get("payload", {})
    weights = payload.get("weights", {}) if isinstance(payload, dict) else {}
    return {
        "artifact_id": artifact.get("artifact_id", ""),
        "version": artifact.get("version", ""),
        "candidate_id": artifact.get("candidate_id", ""),
        "family": artifact.get("family", ""),
        "created_at": artifact.get("created_at", ""),
        "metric_keys": sorted(metrics.keys()) if isinstance(metrics, dict) else [],
        "validation_keys": sorted(validation.keys()) if isinstance(validation, dict) else [],
        "weight_keys": sorted(weights.keys()) if isinstance(weights, dict) else [],
        "compatible_runtime_version": artifact.get("compatible_runtime_version", ""),
    }


def _validation_artifacts(
    *,
    settings: V30Settings | None,
    family: PolicyFamily,
    candidate_id: str,
    artifact_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    validation_summary = artifact_payload.get("validation_summary", {})
    if isinstance(validation_summary, dict):
        corpus = validation_summary.get("corpus_518k_sample", {})
        if isinstance(corpus, dict):
            rows.append(
                {
                    "source": "policy_artifact.validation_summary.corpus_518k_sample",
                    "family": "518k_validation",
                    "run_id": corpus.get("run_id", ""),
                    "artifact_record_id": corpus.get("artifact_record_id", ""),
                    "artifact_uri": corpus.get("artifact_uri", ""),
                    "promotion_signal": corpus.get("promotion_signal", ""),
                }
            )
        comparison = validation_summary.get("question_policy_comparison", {})
        if isinstance(comparison, dict) and comparison:
            rows.append(
                {
                    "source": "policy_artifact.validation_summary.question_policy_comparison",
                    "family": "question_policy_comparison",
                    "candidate_id": comparison.get("candidate_id", ""),
                    "artifact_record_id": comparison.get("artifact_record_id", ""),
                    "artifact_uri": comparison.get("artifact_uri", ""),
                    "top_question_changed": comparison.get("top_question_changed", False),
                }
            )
    rows.extend(_discovered_validation_artifacts(settings=settings, family=family, candidate_id=candidate_id))
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (str(row.get("family", "")), str(row.get("artifact_record_id", "")), str(row.get("artifact_uri", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _discovered_validation_artifacts(
    *,
    settings: V30Settings | None,
    family: PolicyFamily,
    candidate_id: str,
) -> list[dict[str, Any]]:
    if family != "question_policy" or not candidate_id:
        return []
    result = search_validation_artifacts(
        settings=settings,
        family="question_policy_comparison",
        candidate_id=candidate_id,
        limit=10,
    )
    rows: list[dict[str, Any]] = []
    for artifact in result.artifacts:
        payload = artifact.payload
        rows.append(
            {
                "source": "validation_artifact_discovery",
                "family": artifact.family,
                "candidate_id": payload.get("candidate_id", ""),
                "artifact_record_id": artifact.artifact_record_id,
                "artifact_uri": artifact.runtime_path or payload.get("artifact_uri", ""),
                "backend": result.backend,
                "searchable": result.searchable,
            }
        )
    return rows


def _runtime_trace_summary(runtime, family: PolicyFamily) -> dict[str, Any]:
    versions = runtime.question_plan.policy_effect.get("active_policy_versions", {})
    return {
        "reading_id": runtime.reading_id,
        "trace_id": runtime.trace_id,
        "family": family,
        "active_policy_versions": versions if isinstance(versions, dict) else {},
        "family_consumed": isinstance(versions, dict) and bool(versions.get(family)),
        "question_count": len(runtime.question_plan.recommended_questions),
        "top_question_id": (
            str(runtime.question_plan.recommended_questions[0].get("question_id"))
            if runtime.question_plan.recommended_questions
            else ""
        ),
        "mainline_quality_gate": runtime.mainline_state.quality_gate,
    }
