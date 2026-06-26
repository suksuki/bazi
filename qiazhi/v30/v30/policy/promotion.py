from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.contracts import V30Model
from v30.policy.runtime_pointer import PolicyArtifact, PolicyFamily, RuntimePointer, RuntimePointerStore


class PolicyCandidate(V30Model):
    candidate_id: str
    family: PolicyFamily
    base_artifact_id: str
    payload: dict[str, Any]
    created_at: datetime
    change_summary: str


class PromotionResult(V30Model):
    candidate_id: str
    family: PolicyFamily
    promoted: bool
    validation_run_id: str
    artifact_id: str = ""
    previous_artifact_id: str = ""
    failures: list[str] = []
    pointer_status: str = ""


def make_baseline_candidate(
    *,
    candidate_id: str,
    family: PolicyFamily = "structure_policy",
    payload: dict[str, Any] | None = None,
    change_summary: str = "baseline candidate",
) -> PolicyCandidate:
    return PolicyCandidate(
        candidate_id=candidate_id,
        family=family,
        base_artifact_id=f"{family}.v30-baseline",
        payload=payload or _default_candidate_payload(family),
        created_at=datetime.now(timezone.utc),
        change_summary=change_summary,
    )


def _default_candidate_payload(family: PolicyFamily) -> dict[str, Any]:
    payload: dict[str, Any] = {"mode": "candidate", "family": family}
    if family == "structure_policy":
        payload["weights"] = {
            "mechanism.hidden_factor_dialogue_probe": 1.0,
            "mechanism.ten_god_visibility_context": 1.0,
            "mechanism.useful_god_candidate_gate": 1.0,
            "mechanism.branch_relation_dynamic_review": 1.0,
        }
    if family == "question_policy":
        payload["weights"] = {
            "topic_weights": {"*": 1.0},
            "intent_weights": {"*": 1.0},
            "stage_weights": {"*": 1.0},
            "question_weights": {"*": 1.0},
        }
    if family == "rule_policy":
        payload["weights"] = {
            "rule_weights": {"*": 1.0},
            "domain_weights": {"*": 1.0},
        }
    return payload


def promote_candidate_if_valid(
    candidate: PolicyCandidate,
    *,
    store: RuntimePointerStore | None = None,
    validation_artifact_dir: str | Path | None = None,
    validation_mode: str = "strict",
) -> PromotionResult:
    from v30.runtime import create_smoke_runtime

    store = store or RuntimePointerStore()
    payload_overrides = {candidate.family: candidate.payload}
    version_overrides = {candidate.family: f"{candidate.family}.{candidate.candidate_id}"}
    question_policy_comparison = None
    if candidate.family == "question_policy":
        from v30.policy.comparison import build_question_policy_comparison, persist_question_policy_comparison

        comparison_families: tuple[PolicyFamily, ...] = (
            "structure_policy",
            "mainline_policy",
            "question_policy",
            "rule_policy",
        )
        comparison_runtime = create_smoke_runtime(
            reading_id=f"{candidate.candidate_id}:question-policy-comparison",
            policy_payload_overrides={
                family: store.load_active_artifact(family).payload
                for family in comparison_families
                if family in {"structure_policy", "question_policy", "rule_policy"}
            },
            active_policy_version_overrides=store.active_versions(comparison_families),
        )
        question_policy_comparison = persist_question_policy_comparison(
            build_question_policy_comparison(
                comparison_runtime,
                candidate_id=candidate.candidate_id,
                candidate_payload=candidate.payload,
                candidate_question_policy_id=f"{candidate.family}.{candidate.candidate_id}",
            ),
            settings=getattr(store, "_settings", None),
        )
    if validation_mode == "smoke":
        create_smoke_runtime(
            reading_id=f"{candidate.candidate_id}:promotion-smoke",
            policy_payload_overrides=payload_overrides,
            active_policy_version_overrides=version_overrides,
        )
        synthetic_validation_summary: dict[str, Any] = {
            "suite_id": f"v30.synthetic.promotion.{candidate.family}.smoke-skipped",
            "tier": "promotion_smoke",
            "passed": True,
            "case_count": 0,
            "passed_count": 0,
            "failures": [],
            "boundary": "promotion_smoke_mode_validates_runtime_policy_consumption_without_running_synthetic_all",
        }
        synthetic_case_count = 0
        synthetic_passed_count = 0
        corpus_validation_summary: dict[str, Any] = {
            "run_id": f"v30.518k.sample.{candidate.family}.smoke-skipped",
            "mode": "sample",
            "case_count": 0,
            "promotion_signal": "smoke_skipped",
            "failure_clusters": [],
            "boundary": "promotion_smoke_mode_skips_518k_sample_for_fast_unit_regression_only",
        }
        corpus_validation_case_count = 0
        corpus_validation_signal = "smoke_skipped"
        validation_run_id = f"{synthetic_validation_summary['suite_id']}+{corpus_validation_summary['run_id']}"
        promotion_reason = "runtime_policy_consumption_passed_smoke_mode_heavy_gates_skipped"
    else:
        from v30.validation import run_518k_validation, run_synthetic_tier

        validation = run_synthetic_tier(
            "all",
            suite_id=f"v30.synthetic.promotion.{candidate.family}.all",
            policy_payload_overrides=payload_overrides,
            active_policy_version_overrides=version_overrides,
        )
        validation_run_id = validation.suite_id
        if not validation.passed:
            return PromotionResult(
                candidate_id=candidate.candidate_id,
                family=candidate.family,
                promoted=False,
                validation_run_id=validation_run_id,
                failures=[failure for result in validation.results for failure in result.failures],
            )
        corpus_validation = run_518k_validation(
            mode="sample",
            limit=8,
            artifact_dir=validation_artifact_dir,
            policy_payload_overrides=payload_overrides,
            active_policy_version_overrides=version_overrides,
        )
        validation_run_id = f"{validation.suite_id}+{corpus_validation.run_id}"
        if corpus_validation.promotion_signal != "eligible":
            return PromotionResult(
                candidate_id=candidate.candidate_id,
                family=candidate.family,
                promoted=False,
                validation_run_id=validation_run_id,
                failures=[
                    str(row.get("cluster_key", "unknown_518k_failure"))
                    for row in corpus_validation.failure_clusters
                ],
            )
        synthetic_validation_summary = validation.model_dump(mode="json")
        synthetic_case_count = validation.case_count
        synthetic_passed_count = validation.passed_count
        corpus_validation_summary = corpus_validation.model_dump(mode="json")
        corpus_validation_case_count = corpus_validation.case_count
        corpus_validation_signal = corpus_validation.promotion_signal
        promotion_reason = "synthetic_all_and_518k_sample_passed"

    previous = store.load_pointer(candidate.family)
    artifact_validation_summary = _sanitize_promotion_artifact_value(
        {
            "synthetic": synthetic_validation_summary,
            "corpus_518k_sample": corpus_validation_summary,
            "question_policy_comparison": (
                question_policy_comparison.model_dump(mode="json")
                if question_policy_comparison is not None
                else {}
            ),
        }
    )
    artifact = PolicyArtifact(
        artifact_id=f"{candidate.family}.{candidate.candidate_id}",
        family=candidate.family,
        version="v30.policy_artifact.v1",
        candidate_id=candidate.candidate_id,
        payload=candidate.payload,
        created_at=datetime.now(timezone.utc),
        validation_summary=artifact_validation_summary if isinstance(artifact_validation_summary, dict) else {},
        metrics={
            "synthetic_case_count": synthetic_case_count,
            "synthetic_passed_count": synthetic_passed_count,
            "corpus_518k_sample_case_count": corpus_validation_case_count,
            "corpus_518k_promotion_signal": corpus_validation_signal,
            "question_policy_comparison_changed_rank_count": (
                question_policy_comparison.changed_rank_count if question_policy_comparison is not None else 0
            ),
            "question_policy_comparison_weighted_delta_count": (
                question_policy_comparison.weighted_delta_count if question_policy_comparison is not None else 0
            ),
        },
    )
    pointer = RuntimePointer(
        family=candidate.family,
        active_artifact_id=artifact.artifact_id,
        active_artifact_version=artifact.version,
        previous_artifact_id=previous.active_artifact_id,
        validation_run_id=validation_run_id,
        promotion_reason=promotion_reason,
        env=previous.env,
        updated_at=datetime.now(timezone.utc),
        updated_by="v30.policy.promotion",
        rollback_pointer={
            "family": previous.family,
            "active_artifact_id": previous.active_artifact_id,
            "active_artifact_version": previous.active_artifact_version,
        },
    )
    store.save_artifact(artifact)
    store.save_pointer(pointer)
    return PromotionResult(
        candidate_id=candidate.candidate_id,
        family=candidate.family,
        promoted=True,
        validation_run_id=validation_run_id,
        artifact_id=artifact.artifact_id,
        previous_artifact_id=previous.active_artifact_id,
        pointer_status=pointer.status,
    )


def _sanitize_promotion_artifact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key).replace("v20", "legacy_reference"): _sanitize_promotion_artifact_value(row) for key, row in value.items()}
    if isinstance(value, list):
        return [_sanitize_promotion_artifact_value(row) for row in value]
    if isinstance(value, str):
        return value.replace("v20", "legacy_reference").replace("V20", "LegacyReference")
    return value
