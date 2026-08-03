from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.synthetic_experiment_contracts import (
    SyntheticExperimentDevGoldVersion,
    SyntheticExperimentEvaluatorVersion,
    SyntheticExperimentOutcome,
)

SYNTHETIC_SUITE_RUN_VERSION = "v60.mingli-synthetic-suite-run.002"
SYNTHETIC_SUITE_REVIEW_PROJECTION_VERSION = (
    "v60.mingli-synthetic-suite-review-projection.001"
)


class SyntheticSuiteCandidateIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_profile_ref: str = Field(min_length=1)
    agent_profile_hash: str = Field(min_length=64, max_length=64)
    provider_id: str = Field(min_length=1)
    model_ref: str = Field(min_length=1)
    model_digest: str = Field(min_length=64, max_length=64)
    provider_profile_ref: str = Field(min_length=1)
    provider_profile_hash: str = Field(min_length=64, max_length=64)
    prompt_ref: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=64, max_length=64)
    agent_reading_version: str | None = Field(default=None, min_length=1)


class SyntheticSuiteVariantReview(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    variant: Literal["A", "B"]
    reason_keys: tuple[str, ...]

    @model_validator(mode="after")
    def reasons_are_canonical(self) -> SyntheticSuiteVariantReview:
        if self.reason_keys != tuple(sorted(set(self.reason_keys))):
            raise ValueError("mingli_synthetic_suite_variant_reasons_invalid")
        return self


class SyntheticSuiteRunItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    position: int = Field(ge=1)
    experiment_ref: str = Field(min_length=1)
    definition_hash: str = Field(min_length=64, max_length=64)
    execution_status: Literal["SEALED", "ERROR"]
    experiment_run_ref: str | None = None
    experiment_run_hash: str | None = None
    outcome: SyntheticExperimentOutcome | None = None
    evaluator_version: SyntheticExperimentEvaluatorVersion | None = None
    dev_gold_version: SyntheticExperimentDevGoldVersion | None = None
    dev_gold_hash: str | None = None
    model_independence: Literal["PASS", "FAIL", "NOT_EVALUABLE"] | None = None
    changed_pass_count: int | None = Field(default=None, ge=0)
    hold_pass_count: int | None = Field(default=None, ge=0)
    review_contract_status: Literal["CURRENT", "SUPERSEDED"] | None = None
    review_required: bool
    review_reason_keys: tuple[str, ...]
    variant_reviews: tuple[SyntheticSuiteVariantReview, ...]
    error_code: str | None = None

    @model_validator(mode="after")
    def execution_shape_is_valid(self) -> SyntheticSuiteRunItem:
        if self.review_reason_keys != tuple(sorted(set(self.review_reason_keys))):
            raise ValueError("mingli_synthetic_suite_item_reasons_invalid")
        variant_keys = tuple(item.variant for item in self.variant_reviews)
        if variant_keys != tuple(sorted(set(variant_keys))):
            raise ValueError("mingli_synthetic_suite_variant_reviews_invalid")
        sealed_fields = (
            self.experiment_run_ref,
            self.experiment_run_hash,
            self.outcome,
            self.evaluator_version,
            self.dev_gold_version,
            self.dev_gold_hash,
            self.model_independence,
            self.changed_pass_count,
            self.hold_pass_count,
            self.review_contract_status,
        )
        if self.execution_status == "SEALED":
            if any(value is None for value in sealed_fields) or self.error_code is not None:
                raise ValueError("mingli_synthetic_suite_sealed_item_invalid")
            if len(self.experiment_run_hash or "") != 64 or len(self.dev_gold_hash or "") != 64:
                raise ValueError("mingli_synthetic_suite_sealed_hash_invalid")
            if variant_keys != ("A", "B"):
                raise ValueError("mingli_synthetic_suite_sealed_variants_invalid")
        elif (
            any(value is not None for value in sealed_fields)
            or not self.error_code
            or self.variant_reviews
        ):
            raise ValueError("mingli_synthetic_suite_error_item_invalid")
        if self.review_required != bool(self.review_reason_keys):
            raise ValueError("mingli_synthetic_suite_review_flag_invalid")
        variant_reason_union = {
            reason for item in self.variant_reviews for reason in item.reason_keys
        }
        if not variant_reason_union.issubset(set(self.review_reason_keys)):
            raise ValueError("mingli_synthetic_suite_variant_reason_unbound")
        return self


class SyntheticSuiteCounts(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    experiments: int = Field(ge=1)
    sealed: int = Field(ge=0)
    runner_errors: int = Field(ge=0)
    review_required: int = Field(ge=0)


class SyntheticSuiteOutcomeCounts(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    PASS: int = Field(ge=0)
    PRODUCT_SAFE_MODEL_FAIL: int = Field(ge=0)
    MODEL_FAIL: int = Field(ge=0)
    INVALID_EXPERIMENT: int = Field(ge=0)


class SyntheticSuiteErrorCluster(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal[
        "SERVER_REPAIR",
        "EXPECTED_CHECK_FAIL",
        "EXPERIMENT_INVALID",
        "CONTRACT_SUPERSEDED",
        "RUNNER_ERROR",
    ]
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    occurrence_count: int = Field(ge=1)
    experiment_count: int = Field(ge=1)
    experiment_refs: tuple[str, ...]
    member_occurrences: tuple[str, ...]


class SyntheticSuiteRunIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    suite_run_version: Literal[
        "v60.mingli-synthetic-suite-run.001",
        "v60.mingli-synthetic-suite-run.002",
    ]
    suite_ref: str = Field(min_length=1)
    suite_definition_hash: str = Field(min_length=64, max_length=64)
    suite_mode: Literal["DEV"]
    runner_version: Literal[
        "v60.mingli-synthetic-suite-runner.001",
        "v60.mingli-synthetic-suite-runner.002",
    ]
    candidate_identity: SyntheticSuiteCandidateIdentity | None
    status: Literal["COMPLETED", "COMPLETED_WITH_ERRORS"]
    items: tuple[SyntheticSuiteRunItem, ...] = Field(min_length=1)
    counts: SyntheticSuiteCounts
    outcomes: SyntheticSuiteOutcomeCounts
    error_clusters: tuple[SyntheticSuiteErrorCluster, ...]
    qualification_effect: Literal["DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION"]

    @model_validator(mode="after")
    def derived_summary_is_valid(self) -> SyntheticSuiteRunIdentity:
        positions = tuple(item.position for item in self.items)
        if positions != tuple(range(1, len(self.items) + 1)):
            raise ValueError("mingli_synthetic_suite_item_order_invalid")
        refs = tuple(item.experiment_ref for item in self.items)
        if len(refs) != len(set(refs)):
            raise ValueError("mingli_synthetic_suite_item_duplicate")
        expected_counts, expected_outcomes = derive_suite_counts(self.items)
        if self.counts != expected_counts or self.outcomes != expected_outcomes:
            raise ValueError("mingli_synthetic_suite_counts_invalid")
        expected_status = "COMPLETED_WITH_ERRORS" if self.counts.runner_errors else "COMPLETED"
        if self.status != expected_status:
            raise ValueError("mingli_synthetic_suite_status_invalid")
        if self.suite_run_version == "v60.mingli-synthetic-suite-run.001":
            if (self.counts.sealed > 0) != (self.candidate_identity is not None):
                raise ValueError("mingli_synthetic_suite_candidate_identity_invalid")
        elif (
            self.candidate_identity is None or self.candidate_identity.agent_reading_version is None
        ):
            raise ValueError("mingli_synthetic_suite_attempted_candidate_required")
        if _cluster_bindings(self.error_clusters) != _cluster_bindings(
            derive_error_clusters(self.items)
        ):
            raise ValueError("mingli_synthetic_suite_clusters_invalid")
        return self


def derive_suite_counts(
    items: tuple[SyntheticSuiteRunItem, ...],
) -> tuple[SyntheticSuiteCounts, SyntheticSuiteOutcomeCounts]:
    sealed = sum(item.execution_status == "SEALED" for item in items)
    outcomes = {
        outcome: sum(item.outcome == outcome for item in items)
        for outcome in (
            "PASS",
            "PRODUCT_SAFE_MODEL_FAIL",
            "MODEL_FAIL",
            "INVALID_EXPERIMENT",
        )
    }
    return (
        SyntheticSuiteCounts(
            experiments=len(items),
            sealed=sealed,
            runner_errors=len(items) - sealed,
            review_required=sum(item.review_required for item in items),
        ),
        SyntheticSuiteOutcomeCounts(**outcomes),
    )


def derive_error_clusters(
    items: tuple[SyntheticSuiteRunItem, ...],
) -> tuple[SyntheticSuiteErrorCluster, ...]:
    occurrences: dict[str, set[str]] = defaultdict(set)
    experiments: dict[str, set[str]] = defaultdict(set)
    for item in items:
        variant_reasons: set[str] = set()
        for variant_review in item.variant_reviews:
            for reason in variant_review.reason_keys:
                variant_reasons.add(reason)
                occurrences[reason].add(f"{item.experiment_ref}:{variant_review.variant}")
                experiments[reason].add(item.experiment_ref)
        for reason in item.review_reason_keys:
            if reason not in variant_reasons:
                occurrences[reason].add(f"{item.experiment_ref}:PAIR")
            experiments[reason].add(item.experiment_ref)
    return tuple(
        SyntheticSuiteErrorCluster(
            kind=_cluster_kind(reason),
            key=reason,
            label=_cluster_label(reason),
            occurrence_count=len(occurrences[reason]),
            experiment_count=len(experiments[reason]),
            experiment_refs=tuple(sorted(experiments[reason])),
            member_occurrences=tuple(sorted(occurrences[reason])),
        )
        for reason in sorted(occurrences)
    )


def _cluster_bindings(
    clusters: tuple[SyntheticSuiteErrorCluster, ...],
) -> tuple[tuple[object, ...], ...]:
    """Validate stable evidence bindings without rewriting historical UI labels."""

    return tuple(
        (
            item.kind,
            item.key,
            item.occurrence_count,
            item.experiment_count,
            item.experiment_refs,
            item.member_occurrences,
        )
        for item in clusters
    )


def _cluster_kind(reason: str) -> str:
    if reason.startswith("SERVER_REPAIR:"):
        return "SERVER_REPAIR"
    if reason.startswith(("CHECK_FAIL:EXPERIMENT_VALIDITY:", "CHECK_FAIL:MUST_HOLD:")):
        return "EXPERIMENT_INVALID"
    if reason.startswith("CHECK_FAIL:EXPECTED_CHANGE:"):
        return "EXPECTED_CHECK_FAIL"
    if reason == "REVIEW_CONTRACT:SUPERSEDED":
        return "CONTRACT_SUPERSEDED"
    return "RUNNER_ERROR"


def _cluster_label(reason: str) -> str:
    if reason == "SERVER_REPAIR:DAY_MASTER_REGIME":
        return "日主与根气裁决"
    if reason in {"SERVER_REPAIR:HYPOTHESIS_H1", "SERVER_REPAIR:HYPOTHESIS_H2"}:
        return "假设结构归槽"
    if reason.startswith("SERVER_REPAIR:"):
        return "模型判断归槽"
    if reason.startswith("CHECK_FAIL:EXPECTED_CHANGE:"):
        return "方法响应未通过"
    if reason.startswith("CHECK_FAIL:"):
        return "控制变量或实验结构漂移"
    if reason == "REVIEW_CONTRACT:SUPERSEDED":
        return "审阅口径已更新"
    return "训练运行未完成"
