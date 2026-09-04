from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MINGLI_FOCUSED_READING_VERSION = "v60.mingli-focused-reading.001"
MINGLI_FOCUSED_PASS_VERSION = "v60.mingli-focused-pass.001"
MINGLI_FOCUSED_PASS_RECORD_VERSION = "v60.mingli-focused-pass-record.001"
MINGLI_FOCUSED_RUNTIME_VERSION = "v60.mingli-focused-runtime.001"
MINGLI_FOCUSED_PROMPT_VERSION = "v60.prompt.mingli-focused-reading.001"

MingliFocus = Literal[
    "STRUCTURE",
    "LIFE_IMAGE_PERSONALITY",
    "CAREER_WEALTH",
    "RELATIONSHIP_FAMILY",
    "TIMING",
]

MINGLI_FOCUS_ORDER: tuple[MingliFocus, ...] = (
    "STRUCTURE",
    "LIFE_IMAGE_PERSONALITY",
    "CAREER_WEALTH",
    "RELATIONSHIP_FAMILY",
    "TIMING",
)


class MingliFocusedPassResult(BaseModel):
    """One short model answer plus deterministic presentation normalization."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pass_ref: str = Field(min_length=1)
    pass_hash: str = Field(min_length=64, max_length=64)
    pass_version: Literal["v60.mingli-focused-pass.001"]
    focus: MingliFocus
    question: str = Field(min_length=1, max_length=500)
    context_hash: str = Field(min_length=64, max_length=64)
    provider_response_ref: str = Field(min_length=1)
    raw_text: str = Field(min_length=1, max_length=6000)
    normalized_text: str = Field(min_length=1, max_length=3000)
    normalization_codes: tuple[str, ...] = Field(max_length=16)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    duration_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliFocusedPassResult:
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("mingli_focused_pass_token_total_mismatch")
        if self.normalization_codes != tuple(sorted(set(self.normalization_codes))):
            raise ValueError("mingli_focused_pass_codes_not_sorted_unique")
        identity = self.model_dump(mode="json", exclude={"pass_ref", "pass_hash"})
        if self.pass_hash != content_hash(identity):
            raise ValueError("mingli_focused_pass_hash_mismatch")
        if self.pass_ref != stable_ref("v60-mingli-focused-pass", identity):
            raise ValueError("mingli_focused_pass_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliFocusedPassResult:
        identity = {
            "pass_version": MINGLI_FOCUSED_PASS_VERSION,
            **values,
            "normalization_codes": tuple(sorted(set(values.get("normalization_codes", ())))),
        }
        return cls(
            pass_ref=stable_ref("v60-mingli-focused-pass", identity),
            pass_hash=content_hash(identity),
            **identity,
        )


class MingliFocusedReadingEnvelope(BaseModel):
    """Private multi-pass prose reading; it never owns chart facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    focused_reading_ref: str = Field(min_length=1)
    focused_reading_hash: str = Field(min_length=64, max_length=64)
    focused_reading_version: Literal["v60.mingli-focused-reading.001"]
    generation_key: str = Field(min_length=64, max_length=64)
    requester_account_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    runtime_ref: Literal["v60.mingli-focused-runtime.001"]
    provider_id: str = Field(min_length=1)
    model_ref: str = Field(min_length=1)
    model_digest: str = Field(min_length=64, max_length=64)
    provider_profile_ref: str = Field(min_length=1)
    provider_profile_hash: str = Field(min_length=64, max_length=64)
    prompt_version: Literal["v60.prompt.mingli-focused-reading.001"]
    prompt_hash: str = Field(min_length=64, max_length=64)
    passes: tuple[MingliFocusedPassResult, ...] = Field(min_length=5, max_length=5)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    interpretation_status: Literal["FOCUSED_AGENT_INTERPRETATION"]
    owner_review_status: Literal["NOT_REVIEWED"]
    publication_allowed: Literal[False]
    canonical_fact_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliFocusedReadingEnvelope:
        if tuple(item.focus for item in self.passes) != MINGLI_FOCUS_ORDER:
            raise ValueError("mingli_focused_reading_pass_order_invalid")
        if self.input_tokens != sum(item.input_tokens for item in self.passes):
            raise ValueError("mingli_focused_reading_input_tokens_mismatch")
        if self.output_tokens != sum(item.output_tokens for item in self.passes):
            raise ValueError("mingli_focused_reading_output_tokens_mismatch")
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("mingli_focused_reading_total_tokens_mismatch")
        if self.duration_ms != sum(item.duration_ms for item in self.passes):
            raise ValueError("mingli_focused_reading_duration_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"focused_reading_ref", "focused_reading_hash"},
        )
        if self.focused_reading_hash != content_hash(identity):
            raise ValueError("mingli_focused_reading_hash_mismatch")
        if self.focused_reading_ref != stable_ref("v60-mingli-focused-reading", identity):
            raise ValueError("mingli_focused_reading_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliFocusedReadingEnvelope:
        passes = tuple(values["passes"])
        identity = {
            **values,
            "focused_reading_version": MINGLI_FOCUSED_READING_VERSION,
            "runtime_ref": MINGLI_FOCUSED_RUNTIME_VERSION,
            "prompt_version": MINGLI_FOCUSED_PROMPT_VERSION,
            "passes": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in passes
            ),
            "input_tokens": sum(item.input_tokens for item in passes),
            "output_tokens": sum(item.output_tokens for item in passes),
            "total_tokens": sum(item.total_tokens for item in passes),
            "duration_ms": sum(item.duration_ms for item in passes),
            "interpretation_status": "FOCUSED_AGENT_INTERPRETATION",
            "owner_review_status": "NOT_REVIEWED",
            "publication_allowed": False,
            "canonical_fact_write_allowed": False,
            "read_only": True,
        }
        return cls(
            focused_reading_ref=stable_ref("v60-mingli-focused-reading", identity),
            focused_reading_hash=content_hash(identity),
            **identity,
        )

    def pass_for(self, focus: MingliFocus) -> MingliFocusedPassResult:
        return next(item for item in self.passes if item.focus == focus)


class MingliFocusedPassRecord(BaseModel):
    """One independently generated product pass with exact packet lineage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_ref: str = Field(min_length=1)
    record_hash: str = Field(min_length=64, max_length=64)
    record_version: Literal["v60.mingli-focused-pass-record.001"]
    generation_key: str = Field(min_length=64, max_length=64)
    requester_account_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    runtime_ref: Literal["v60.mingli-focused-runtime.001"]
    provider_id: str = Field(min_length=1)
    model_ref: str = Field(min_length=1)
    model_digest: str = Field(min_length=64, max_length=64)
    provider_profile_ref: str = Field(min_length=1)
    provider_profile_hash: str = Field(min_length=64, max_length=64)
    prompt_version: Literal["v60.prompt.mingli-focused-reading.001"]
    prompt_hash: str = Field(min_length=64, max_length=64)
    focus: MingliFocus
    structure_pass_hash: str | None = Field(default=None, min_length=64, max_length=64)
    pass_result: MingliFocusedPassResult
    interpretation_status: Literal["FOCUSED_AGENT_INTERPRETATION"]
    owner_review_status: Literal["NOT_REVIEWED"]
    publication_allowed: Literal[False]
    canonical_fact_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliFocusedPassRecord:
        if self.focus != self.pass_result.focus:
            raise ValueError("mingli_focused_pass_record_focus_mismatch")
        if (self.focus == "STRUCTURE") != (self.structure_pass_hash is None):
            raise ValueError("mingli_focused_pass_record_structure_lineage_invalid")
        identity = self.model_dump(mode="json", exclude={"record_ref", "record_hash"})
        if self.record_hash != content_hash(identity):
            raise ValueError("mingli_focused_pass_record_hash_mismatch")
        if self.record_ref != stable_ref("v60-mingli-focused-pass-record", identity):
            raise ValueError("mingli_focused_pass_record_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliFocusedPassRecord:
        pass_result = values["pass_result"]
        identity = {
            **values,
            "record_version": MINGLI_FOCUSED_PASS_RECORD_VERSION,
            "runtime_ref": MINGLI_FOCUSED_RUNTIME_VERSION,
            "prompt_version": MINGLI_FOCUSED_PROMPT_VERSION,
            "pass_result": (
                pass_result.model_dump(mode="json")
                if isinstance(pass_result, BaseModel)
                else pass_result
            ),
            "interpretation_status": "FOCUSED_AGENT_INTERPRETATION",
            "owner_review_status": "NOT_REVIEWED",
            "publication_allowed": False,
            "canonical_fact_write_allowed": False,
            "read_only": True,
        }
        return cls(
            record_ref=stable_ref("v60-mingli-focused-pass-record", identity),
            record_hash=content_hash(identity),
            **identity,
        )
