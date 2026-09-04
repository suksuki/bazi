from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MINGLI_AGENT_NORMALIZATION_RECEIPT_VERSION = "v60.mingli-agent-normalization-receipt.001"

NormalizationStage = Literal[
    "EVIDENCE_ID_NORMALIZATION",
    "PACKET_FACT_BINDING",
    "PROFESSIONAL_ADJUDICATION",
    "PROSE_EVIDENCE_REPAIR",
    "OUTPUT_FORM_REPAIR",
    "LOCAL_FIELD_REPAIR",
]

NORMALIZATION_STAGE_ORDER: tuple[NormalizationStage, ...] = (
    "EVIDENCE_ID_NORMALIZATION",
    "PACKET_FACT_BINDING",
    "PROFESSIONAL_ADJUDICATION",
    "PROSE_EVIDENCE_REPAIR",
    "OUTPUT_FORM_REPAIR",
    "LOCAL_FIELD_REPAIR",
)


class MingliAgentNormalizationDelta(BaseModel):
    """One leaf-level change between two consecutive normalization stages."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: NormalizationStage
    path: str = Field(pattern=r"^/")
    before_present: bool
    after_present: bool
    before: Any = None
    after: Any = None

    @model_validator(mode="after")
    def change_is_real(self) -> MingliAgentNormalizationDelta:
        if not self.before_present and not self.after_present:
            raise ValueError("mingli_agent_normalization_delta_empty")
        if (not self.before_present and self.before is not None) or (
            not self.after_present and self.after is not None
        ):
            raise ValueError("mingli_agent_normalization_delta_missing_value")
        if self.before_present and self.after_present and self.before == self.after:
            raise ValueError("mingli_agent_normalization_delta_unchanged")
        return self


class MingliAgentNormalizationReceipt(BaseModel):
    """Private append-only proof of model output and server normalization.

    The raw value is the structured JSON answer returned with ``think=false``.
    Hidden reasoning is neither requested nor stored.  The normalized answer is
    already bound by the enclosing Agent Reading; its hash is repeated here so
    the two artifacts cannot be silently mixed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    receipt_ref: str = Field(min_length=1)
    receipt_hash: str = Field(min_length=64, max_length=64)
    receipt_version: Literal["v60.mingli-agent-normalization-receipt.001"]
    provider_response_ref: str = Field(min_length=1)
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    agent_profile_ref: str = Field(min_length=1)
    agent_profile_hash: str = Field(min_length=64, max_length=64)
    provider_id: str = Field(min_length=1)
    model_ref: str = Field(min_length=1)
    model_digest: str = Field(min_length=64, max_length=64)
    provider_profile_ref: str = Field(min_length=1)
    provider_profile_hash: str = Field(min_length=64, max_length=64)
    prompt_ref: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=64, max_length=64)
    raw_output: dict[str, Any]
    raw_output_hash: str = Field(min_length=64, max_length=64)
    normalized_output_hash: str = Field(min_length=64, max_length=64)
    changes: tuple[MingliAgentNormalizationDelta, ...] = Field(max_length=512)
    server_issue_keys: tuple[str, ...] = Field(max_length=24)
    stored_scope: Literal["STRUCTURED_PROVIDER_OUTPUT_ONLY"]
    hidden_reasoning_stored: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_is_valid(self) -> MingliAgentNormalizationReceipt:
        if self.raw_output_hash != content_hash(self.raw_output):
            raise ValueError("mingli_agent_normalization_raw_hash_mismatch")
        delta_keys = tuple((item.stage, item.path) for item in self.changes)
        if len(delta_keys) != len(set(delta_keys)):
            raise ValueError("mingli_agent_normalization_delta_duplicate")
        replayed = _replay_normalization_deltas(self.raw_output, self.changes)
        if content_hash(replayed) != self.normalized_output_hash:
            raise ValueError("mingli_agent_normalization_delta_chain_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"receipt_ref", "receipt_hash"},
        )
        if self.receipt_hash != content_hash(identity):
            raise ValueError("mingli_agent_normalization_receipt_hash_mismatch")
        if self.receipt_ref != stable_ref(
            "v60-mingli-agent-normalization-receipt",
            identity,
        ):
            raise ValueError("mingli_agent_normalization_receipt_ref_mismatch")
        return self

    def is_bound_to_reading_payload(self, reading: Mapping[str, Any]) -> bool:
        """Verify that a receipt belongs to one serialized Agent Reading."""

        output = reading.get("output")
        if not isinstance(output, dict):
            return False
        bound_fields = (
            "provider_response_ref",
            "packet_ref",
            "packet_hash",
            "agent_profile_ref",
            "agent_profile_hash",
            "provider_id",
            "model_ref",
            "model_digest",
            "provider_profile_ref",
            "provider_profile_hash",
            "prompt_ref",
            "prompt_hash",
        )
        return (
            all(getattr(self, key) == reading.get(key) for key in bound_fields)
            and self.normalized_output_hash == content_hash(output)
            and self.server_issue_keys == tuple(output.get("server_issue_keys", ()))
        )

    @classmethod
    def issue(
        cls,
        *,
        provider_response_ref: str,
        packet_ref: str,
        packet_hash: str,
        agent_profile_ref: str,
        agent_profile_hash: str,
        provider_id: str,
        model_ref: str,
        model_digest: str,
        provider_profile_ref: str,
        provider_profile_hash: str,
        prompt_ref: str,
        prompt_hash: str,
        raw_output: dict[str, Any],
        normalized_output: dict[str, Any],
        changes: tuple[MingliAgentNormalizationDelta, ...],
        server_issue_keys: tuple[str, ...],
    ) -> MingliAgentNormalizationReceipt:
        identity = {
            "receipt_version": MINGLI_AGENT_NORMALIZATION_RECEIPT_VERSION,
            "provider_response_ref": provider_response_ref,
            "packet_ref": packet_ref,
            "packet_hash": packet_hash,
            "agent_profile_ref": agent_profile_ref,
            "agent_profile_hash": agent_profile_hash,
            "provider_id": provider_id,
            "model_ref": model_ref,
            "model_digest": model_digest,
            "provider_profile_ref": provider_profile_ref,
            "provider_profile_hash": provider_profile_hash,
            "prompt_ref": prompt_ref,
            "prompt_hash": prompt_hash,
            "raw_output": raw_output,
            "raw_output_hash": content_hash(raw_output),
            "normalized_output_hash": content_hash(normalized_output),
            "changes": tuple(item.model_dump(mode="json") for item in changes),
            "server_issue_keys": server_issue_keys,
            "stored_scope": "STRUCTURED_PROVIDER_OUTPUT_ONLY",
            "hidden_reasoning_stored": False,
            "read_only": True,
        }
        return cls(
            receipt_ref=stable_ref(
                "v60-mingli-agent-normalization-receipt",
                identity,
            ),
            receipt_hash=content_hash(identity),
            **identity,
        )


_MISSING = object()


def _replay_normalization_deltas(
    raw_output: dict[str, Any],
    changes: tuple[MingliAgentNormalizationDelta, ...],
) -> dict[str, Any]:
    replayed: Any = deepcopy(raw_output)
    stage_index = {stage: index for index, stage in enumerate(NORMALIZATION_STAGE_ORDER)}
    prior_stage = -1
    for delta in changes:
        current_stage = stage_index[delta.stage]
        if current_stage < prior_stage:
            raise ValueError("mingli_agent_normalization_stage_order_invalid")
        prior_stage = current_stage
        present, current = _read_pointer(replayed, delta.path)
        if present != delta.before_present or (present and current != delta.before):
            raise ValueError("mingli_agent_normalization_delta_before_mismatch")
        replayed = _apply_pointer_delta(replayed, delta)
    if not isinstance(replayed, dict):
        raise TypeError("mingli_agent_normalization_replay_not_object")
    return replayed


def _read_pointer(document: Any, path: str) -> tuple[bool, Any]:
    if path == "/":
        return True, document
    current = document
    for token in _pointer_tokens(path):
        if not isinstance(current, dict) or token not in current:
            return False, None
        current = current[token]
    return True, current


def _apply_pointer_delta(
    document: Any,
    delta: MingliAgentNormalizationDelta,
) -> Any:
    if delta.path == "/":
        if not delta.after_present:
            raise ValueError("mingli_agent_normalization_root_removal_forbidden")
        return deepcopy(delta.after)
    tokens = _pointer_tokens(delta.path)
    parent = document
    for token in tokens[:-1]:
        if not isinstance(parent, dict) or token not in parent:
            raise ValueError("mingli_agent_normalization_delta_parent_missing")
        parent = parent[token]
    if not isinstance(parent, dict):
        raise TypeError("mingli_agent_normalization_delta_parent_invalid")
    key = tokens[-1]
    if delta.after_present:
        parent[key] = deepcopy(delta.after)
    else:
        parent.pop(key, None)
    return document


def _pointer_tokens(path: str) -> tuple[str, ...]:
    if not path.startswith("/") or path == "/":
        raise ValueError("mingli_agent_normalization_pointer_invalid")
    return tuple(token.replace("~1", "/").replace("~0", "~") for token in path[1:].split("/"))


def normalization_deltas(
    before: Any,
    after: Any,
    *,
    stage: NormalizationStage,
) -> tuple[MingliAgentNormalizationDelta, ...]:
    """Return deterministic JSON-pointer leaf changes for one repair stage."""

    changes: list[MingliAgentNormalizationDelta] = []
    _collect_deltas(
        before,
        after,
        stage=stage,
        path="",
        changes=changes,
    )
    return tuple(changes)


def _collect_deltas(
    before: Any,
    after: Any,
    *,
    stage: NormalizationStage,
    path: str,
    changes: list[MingliAgentNormalizationDelta],
) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            _collect_deltas(
                before.get(key, _MISSING),
                after.get(key, _MISSING),
                stage=stage,
                path=f"{path}/{_escape_pointer(str(key))}",
                changes=changes,
            )
        return
    if before is not _MISSING and after is not _MISSING and before == after:
        return
    changes.append(
        MingliAgentNormalizationDelta(
            stage=stage,
            path=path or "/",
            before_present=before is not _MISSING,
            after_present=after is not _MISSING,
            before=None if before is _MISSING else before,
            after=None if after is _MISSING else after,
        )
    )


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")
