from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.agent_adjudication import AgentMechanismAdjudication
from abu_v60.mingli.agent_regime_contracts import AgentRegimeDecision
from abu_v60.provenance import content_hash, stable_ref

MINGLI_SYNTHETIC_DISTILLATION_RUNTIME_VERSION = "v60.mingli-synthetic-distillation-runtime.001"
MINGLI_SYNTHETIC_DISTILLATION_PROMPT_VERSION = "v60.prompt.mingli-synthetic-distillation.001"
MINGLI_SYNTHETIC_DISTILLATION_PASS_VERSION = "v60.mingli-synthetic-distillation-pass.001"
MINGLI_SYNTHETIC_DISTILLATION_EVALUATOR_VERSION = "v60.mingli-synthetic-distillation-evaluator.001"
MINGLI_SYNTHETIC_DISTILLATION_RUN_VERSION = "v60.mingli-synthetic-distillation-run.001"

SyntheticDistillationStage = Literal[
    "REGIME",
    "CANDIDATE_COMPARISON",
    "CERTAINTY",
]
SYNTHETIC_DISTILLATION_STAGE_ORDER: tuple[SyntheticDistillationStage, ...] = (
    "REGIME",
    "CANDIDATE_COMPARISON",
    "CERTAINTY",
)
SyntheticDistillationJudgment = Literal[
    "SUPPORTED",
    "WORKS_IF",
    "PARTIAL",
    "BLOCKED",
    "COMPETING",
]


class DistillationRegimeOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    regime_decision: AgentRegimeDecision
    day_master_state: Literal[
        "STRONG",
        "WEAK",
        "BALANCED",
        "FOLLOWING_TENDENCY",
        "SPECIALIZED_TENDENCY",
        "UNCERTAIN",
    ]
    rationale: str = Field(min_length=16, max_length=220)


class DistillationMethodRuling(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    check_code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    ruling: Literal["SUPPORTS", "CONDITIONAL", "OPPOSES", "UNRESOLVED"]
    rationale: str = Field(min_length=8, max_length=140)
    evidence_ids: tuple[str, ...] = Field(max_length=4)

    @model_validator(mode="after")
    def evidence_is_unique(self) -> DistillationMethodRuling:
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("mingli_distillation_ruling_evidence_not_unique")
        return self


class DistillationCandidateAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    method_card_ref: str = Field(min_length=4, max_length=48)
    rulings: tuple[DistillationMethodRuling, ...] = Field(min_length=1, max_length=6)
    summary: str = Field(min_length=12, max_length=180)

    @model_validator(mode="after")
    def ruling_codes_are_unique(self) -> DistillationCandidateAssessment:
        codes = tuple(item.check_code for item in self.rulings)
        if len(codes) != len(set(codes)):
            raise ValueError("mingli_distillation_ruling_codes_not_unique")
        return self


class DistillationCandidateOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    primary_method_card_ref: str = Field(min_length=4, max_length=48)
    alternative_method_card_ref: str = Field(min_length=4, max_length=48)
    assessments: tuple[DistillationCandidateAssessment, ...] = Field(
        min_length=2,
        max_length=2,
    )
    excluded_method_card_refs: tuple[str, ...] = Field(max_length=8)
    comparison_rationale: str = Field(min_length=16, max_length=220)
    reversal_condition: str = Field(min_length=12, max_length=180)

    @model_validator(mode="after")
    def candidate_lists_are_unique(self) -> DistillationCandidateOutput:
        assessment_refs = tuple(item.method_card_ref for item in self.assessments)
        if len(assessment_refs) != len(set(assessment_refs)):
            raise ValueError("mingli_distillation_assessment_refs_not_unique")
        if len(self.excluded_method_card_refs) != len(set(self.excluded_method_card_refs)):
            raise ValueError("mingli_distillation_excluded_refs_not_unique")
        return self


class DistillationCertaintyOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    primary_judgment: SyntheticDistillationJudgment
    alternative_judgment: SyntheticDistillationJudgment
    work_path_closure: Literal["CLOSED", "CONDITIONAL", "BROKEN", "UNCERTAIN"]
    confidence: Literal["LOW", "MEDIUM"]
    rationale: str = Field(min_length=12, max_length=180)


DistillationStageOutput = (
    DistillationRegimeOutput | DistillationCandidateOutput | DistillationCertaintyOutput
)


class SyntheticDistillationPass(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    pass_version: Literal["v60.mingli-synthetic-distillation-pass.001"]
    pass_ref: str = Field(min_length=1)
    pass_hash: str = Field(min_length=64, max_length=64)
    stage: SyntheticDistillationStage
    context_hash: str = Field(min_length=64, max_length=64)
    stage_prompt_hash: str = Field(min_length=64, max_length=64)
    provider_response_ref: str = Field(min_length=1)
    raw_output: dict[str, Any]
    output: DistillationStageOutput
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    duration_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def identity_and_stage_are_valid(self) -> SyntheticDistillationPass:
        expected_type = {
            "REGIME": DistillationRegimeOutput,
            "CANDIDATE_COMPARISON": DistillationCandidateOutput,
            "CERTAINTY": DistillationCertaintyOutput,
        }[self.stage]
        if not isinstance(self.output, expected_type):
            raise TypeError("mingli_distillation_pass_stage_output_mismatch")
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("mingli_distillation_pass_token_total_mismatch")
        identity = self.model_dump(mode="json", exclude={"pass_ref", "pass_hash"})
        if self.pass_hash != content_hash(identity):
            raise ValueError("mingli_distillation_pass_hash_mismatch")
        if self.pass_ref != stable_ref("v60-mingli-distillation-pass", identity):
            raise ValueError("mingli_distillation_pass_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> SyntheticDistillationPass:
        identity = {
            "pass_version": MINGLI_SYNTHETIC_DISTILLATION_PASS_VERSION,
            **values,
        }
        if isinstance(identity["output"], BaseModel):
            identity["output"] = identity["output"].model_dump(mode="json")
        return cls(
            **identity,
            pass_ref=stable_ref("v60-mingli-distillation-pass", identity),
            pass_hash=content_hash(identity),
        )


class DistillationCandidateAssembly(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    universe: tuple[str, ...]
    primary_method_card_ref: str
    alternative_method_card_ref: str
    excluded_method_card_refs: tuple[str, ...]
    primary_adjudication: AgentMechanismAdjudication
    alternative_adjudication: AgentMechanismAdjudication
    issue_keys: tuple[str, ...]

    @model_validator(mode="after")
    def issues_are_canonical(self) -> DistillationCandidateAssembly:
        if self.issue_keys != tuple(sorted(set(self.issue_keys))):
            raise ValueError("mingli_distillation_assembly_issues_not_canonical")
        return self


class DistillationCertaintyAssembly(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    primary_judgment: SyntheticDistillationJudgment
    alternative_judgment: SyntheticDistillationJudgment
    work_path_closure: Literal["CLOSED", "CONDITIONAL", "BROKEN", "UNCERTAIN"]
    confidence_ceiling: Literal["LOW", "MEDIUM"]


class DistillationEvaluationCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    check_ref: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,79}$")
    status: Literal["PASS", "FAIL"]
    statement: str = Field(min_length=8, max_length=240)
    details: dict[str, Any]


class SyntheticDistillationEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_version: Literal["v60.mingli-synthetic-distillation-evaluator.001"]
    checks: tuple[DistillationEvaluationCheck, ...]
    candidate_assembly: DistillationCandidateAssembly
    certainty_assembly: DistillationCertaintyAssembly
    outcome: Literal["DEV_PASS", "DEV_REVIEW_REQUIRED"]
    model_independence: Literal["PASS", "FAIL"]
    issue_keys: tuple[str, ...]
    qualification_effect: Literal["DEV_TRAINING_ONLY_NOT_QUALIFICATION"]

    @model_validator(mode="after")
    def evaluation_is_coherent(self) -> SyntheticDistillationEvaluation:
        expected_issues = tuple(
            sorted(item.check_ref for item in self.checks if item.status == "FAIL")
        )
        if self.issue_keys != expected_issues:
            raise ValueError("mingli_distillation_evaluation_issues_invalid")
        passed = not self.issue_keys
        if passed != (self.outcome == "DEV_PASS") or passed != (self.model_independence == "PASS"):
            raise ValueError("mingli_distillation_evaluation_outcome_invalid")
        return self


class SyntheticDistillationRun(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_version: Literal["v60.mingli-synthetic-distillation-run.001"]
    run_ref: str = Field(min_length=1)
    run_hash: str = Field(min_length=64, max_length=64)
    generation_key: str = Field(min_length=64, max_length=64)
    research_account_ref: Literal["v60-mingli-synthetic-research"]
    experiment_ref: str = Field(min_length=1)
    definition_hash: str = Field(min_length=64, max_length=64)
    variant: Literal["A", "B"]
    case_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    runtime_ref: Literal["v60.mingli-synthetic-distillation-runtime.001"]
    provider_id: str = Field(min_length=1)
    model_ref: str = Field(min_length=1)
    model_digest: str = Field(min_length=64, max_length=64)
    provider_profile_ref: str = Field(min_length=1)
    provider_profile_hash: str = Field(min_length=64, max_length=64)
    prompt_version: Literal["v60.prompt.mingli-synthetic-distillation.001"]
    prompt_hash: str = Field(min_length=64, max_length=64)
    passes: tuple[SyntheticDistillationPass, ...] = Field(min_length=3, max_length=3)
    evaluation: SyntheticDistillationEvaluation
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    publication_allowed: Literal[False]
    canonical_fact_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def run_identity_is_valid(self) -> SyntheticDistillationRun:
        if tuple(item.stage for item in self.passes) != SYNTHETIC_DISTILLATION_STAGE_ORDER:
            raise ValueError("mingli_distillation_stage_order_invalid")
        if self.input_tokens != sum(item.input_tokens for item in self.passes):
            raise ValueError("mingli_distillation_input_tokens_invalid")
        if self.output_tokens != sum(item.output_tokens for item in self.passes):
            raise ValueError("mingli_distillation_output_tokens_invalid")
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("mingli_distillation_total_tokens_invalid")
        if self.duration_ms != sum(item.duration_ms for item in self.passes):
            raise ValueError("mingli_distillation_duration_invalid")
        identity = self.model_dump(mode="json", exclude={"run_ref", "run_hash"})
        if self.run_hash != content_hash(identity):
            raise ValueError("mingli_distillation_run_hash_mismatch")
        if self.run_ref != stable_ref("v60-mingli-distillation-run", identity):
            raise ValueError("mingli_distillation_run_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> SyntheticDistillationRun:
        identity = {
            "run_version": MINGLI_SYNTHETIC_DISTILLATION_RUN_VERSION,
            **values,
            "publication_allowed": False,
            "canonical_fact_write_allowed": False,
            "read_only": True,
        }
        for key in ("passes",):
            identity[key] = tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in identity[key]
            )
        if isinstance(identity["evaluation"], BaseModel):
            identity["evaluation"] = identity["evaluation"].model_dump(mode="json")
        return cls(
            **identity,
            run_ref=stable_ref("v60-mingli-distillation-run", identity),
            run_hash=content_hash(identity),
        )
