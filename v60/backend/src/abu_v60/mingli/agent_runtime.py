from __future__ import annotations

import json
import re
import time
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from abu_v60.llm_transport import JsonTransport, LlmTransportError, default_json_transport
from abu_v60.mingli.agent_adjudication import (
    normalize_adjudication_output,
    repair_output_form,
    validate_adjudication_output,
)
from abu_v60.mingli.agent_contracts import (
    MINGLI_AGENT_PACKET_VERSION,
    MINGLI_AGENT_PROMPT_VIEW_VERSION,
    MINGLI_AGENT_READING_VERSION,
    MingliAgentCasePacket,
    MingliAgentModelOutput,
    MingliAgentReadingEnvelope,
    mingli_agent_generation_key,
)
from abu_v60.mingli.agent_fact_binding import bind_packet_fact_fields
from abu_v60.mingli.agent_method_cards import MINGLI_AGENT_ADJUDICATION_VERSION
from abu_v60.mingli.agent_method_distillation import (
    MINGLI_AGENT_METHOD_DISTILLATION_VERSION,
)
from abu_v60.mingli.agent_output_repair import (
    MINGLI_AGENT_OUTPUT_REPAIR_VERSION,
    repair_local_output_fields,
)
from abu_v60.mingli.agent_profile import (
    MINGLI_AGENT_OWNER_REVIEW_ALLOWED,
    MINGLI_AGENT_PROFESSIONAL_REVIEW_STATUS,
    MINGLI_AGENT_PROFILE_HASH,
    MINGLI_AGENT_PROFILE_REF,
    MINGLI_AGENT_PROMPT_HASH,
    MINGLI_AGENT_PROMPT_REF,
    MINGLI_AGENT_PUBLICATION_ALLOWED,
    MINGLI_AGENT_RUNTIME_VERSION,
    MINGLI_AGENT_SYSTEM_PROMPT,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref
from abu_v60.settings import Settings, settings

OLLAMA_GENERATE_PROVIDER_ID = "ollama-generate"
MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS = 18000
MINGLI_AGENT_OUTPUT_SCHEMA_MAX_CHARS = 12000


class MingliAgentRuntimeStatus(StrEnum):
    READY = "READY"
    READY_FOR_OWNER_REVIEW = "READY_FOR_OWNER_REVIEW"
    DISABLED = "DISABLED"
    MISCONFIGURED = "MISCONFIGURED"


class MingliAgentRuntimeError(RuntimeError):
    pass


class MingliAgentRuntimeUnavailable(MingliAgentRuntimeError):
    pass


class MingliAgentProviderError(MingliAgentRuntimeError):
    pass


class MingliAgentProviderResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_response_ref: str = Field(min_length=1)
    output: MingliAgentModelOutput
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    duration_ms: int = Field(ge=0)


class MingliAgentProvider(Protocol):
    provider_id: str
    model_ref: str
    model_digest: str
    provider_profile_ref: str
    provider_profile_hash: str

    def generate(self, *, packet: MingliAgentCasePacket) -> MingliAgentProviderResult: ...


class OllamaMingliAgentProvider:
    """One-call whole-chart agent over the private dblife Ollama deployment."""

    provider_id = OLLAMA_GENERATE_PROVIDER_ID

    def __init__(
        self,
        *,
        model_ref: str,
        model_digest: str,
        provider_profile_ref: str,
        base_url: str,
        timeout_seconds: float,
        think: bool,
        temperature: float,
        top_p: float,
        top_k: int,
        num_ctx: int,
        num_predict: int,
        keep_alive: str,
        transport: JsonTransport = default_json_transport,
    ) -> None:
        if not model_ref or len(model_digest) != 64 or not provider_profile_ref:
            raise ValueError("mingli_agent_provider_identity_invalid")
        self.model_ref = model_ref
        self.model_digest = model_digest
        self.provider_profile_ref = provider_profile_ref
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._think = think
        self._temperature = temperature
        self._top_p = top_p
        self._top_k = top_k
        self._num_ctx = num_ctx
        self._num_predict = num_predict
        self._keep_alive = keep_alive
        self._transport = transport
        self.provider_profile_hash = content_hash(self.provider_profile)

    @property
    def provider_profile(self) -> dict[str, Any]:
        return {
            "provider_profile_ref": self.provider_profile_ref,
            "provider_id": self.provider_id,
            "model_ref": self.model_ref,
            "model_digest": self.model_digest,
            "agent_profile_ref": MINGLI_AGENT_PROFILE_REF,
            "agent_profile_hash": MINGLI_AGENT_PROFILE_HASH,
            "prompt_ref": MINGLI_AGENT_PROMPT_REF,
            "prompt_hash": MINGLI_AGENT_PROMPT_HASH,
            "think": self._think,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "top_k": self._top_k,
            "num_ctx": self._num_ctx,
            "num_predict": self._num_predict,
            "keep_alive": self._keep_alive,
            "structured_output_mode": "json_schema",
            "prompt_view_version": MINGLI_AGENT_PROMPT_VIEW_VERSION,
            "prompt_view_max_chars": MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS,
            "output_schema_max_chars": MINGLI_AGENT_OUTPUT_SCHEMA_MAX_CHARS,
            "primary_call_count": 1,
        }

    def generate(self, *, packet: MingliAgentCasePacket) -> MingliAgentProviderResult:
        started = time.monotonic()
        try:
            response = self._transport(
                url=f"{self._base_url}/api/generate",
                headers={"Content-Type": "application/json"},
                payload=self._payload(packet=packet),
                timeout_seconds=self._timeout_seconds,
            )
        except LlmTransportError as exc:
            raise MingliAgentProviderError(str(exc)) from exc
        duration_ms = max(0, round((time.monotonic() - started) * 1000))
        output_text = response.get("response")
        if not isinstance(output_text, str) or not output_text.strip():
            raise MingliAgentProviderError("mingli_agent_provider_output_missing")
        try:
            raw_output = json.loads(output_text)
            normalized_output = _normalize_evidence_ids(
                raw_output,
                allowed=packet.allowed_evidence_ids,
            )
            normalized_output = bind_packet_fact_fields(
                normalized_output,
                packet=packet,
            )
            normalized_output = normalize_adjudication_output(
                normalized_output,
                packet=packet,
            )
            normalized_output = _strip_evidence_ids_from_prose(normalized_output)
            normalized_output = repair_output_form(normalized_output)
            normalized_output = repair_local_output_fields(
                normalized_output,
                packet=packet,
            )
            output = MingliAgentModelOutput.model_validate(normalized_output)
        except ValueError as exc:
            raise MingliAgentProviderError(f"mingli_agent_provider_output_invalid:{exc}") from exc
        input_tokens = _nonnegative_int(response.get("prompt_eval_count"))
        output_tokens = _nonnegative_int(response.get("eval_count"))
        response_ref = stable_ref(
            "v60-mingli-agent-provider-response",
            {
                "provider_id": self.provider_id,
                "model_ref": self.model_ref,
                "model_digest": self.model_digest,
                "provider_profile_hash": self.provider_profile_hash,
                "packet_ref": packet.packet_ref,
                "packet_hash": packet.packet_hash,
                "created_at": response.get("created_at"),
                "output_hash": content_hash(output.model_dump(mode="json")),
            },
        )
        return MingliAgentProviderResult(
            provider_response_ref=response_ref,
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            duration_ms=duration_ms,
        )

    def _payload(self, *, packet: MingliAgentCasePacket) -> dict[str, Any]:
        prompt = canonical_json(packet.model_prompt_view())
        output_schema = MingliAgentModelOutput.model_json_schema()
        if len(prompt) > MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS:
            raise MingliAgentProviderError("mingli_agent_prompt_view_budget_exceeded")
        if len(canonical_json(output_schema)) > MINGLI_AGENT_OUTPUT_SCHEMA_MAX_CHARS:
            raise MingliAgentProviderError("mingli_agent_output_schema_budget_exceeded")
        return {
            "model": self.model_ref,
            "system": MINGLI_AGENT_SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
            "think": self._think,
            "format": output_schema,
            "options": {
                "temperature": self._temperature,
                "top_p": self._top_p,
                "top_k": self._top_k,
                "num_ctx": self._num_ctx,
                "num_predict": self._num_predict,
            },
            "keep_alive": self._keep_alive,
        }


class MingliAgentRuntime:
    def __init__(
        self,
        *,
        provider: MingliAgentProvider | None,
        enabled: bool,
    ) -> None:
        self._provider = provider
        self._enabled = enabled

    @property
    def ready(self) -> bool:
        return self._enabled and self._provider is not None

    def generation_key(
        self,
        *,
        requester_account_ref: str,
        packet: MingliAgentCasePacket,
    ) -> str:
        provider = self._required_provider()
        return mingli_agent_generation_key(
            requester_account_ref=requester_account_ref,
            reading_ref=packet.reading_ref,
            reading_hash=packet.reading_hash,
            packet_ref=packet.packet_ref,
            packet_hash=packet.packet_hash,
            agent_profile_ref=MINGLI_AGENT_PROFILE_REF,
            agent_profile_hash=MINGLI_AGENT_PROFILE_HASH,
            provider_profile_ref=provider.provider_profile_ref,
            provider_profile_hash=provider.provider_profile_hash,
            prompt_ref=MINGLI_AGENT_PROMPT_REF,
            prompt_hash=MINGLI_AGENT_PROMPT_HASH,
        )

    def run(
        self,
        *,
        requester_account_ref: str,
        packet: MingliAgentCasePacket,
    ) -> MingliAgentReadingEnvelope:
        provider = self._required_provider()
        result = provider.generate(packet=packet)
        try:
            result.output.validate_evidence(packet.allowed_evidence_ids)
            _validate_packet_bound_reasoning(output=result.output, packet=packet)
        except ValueError as exc:
            raise MingliAgentProviderError(f"mingli_agent_provider_output_invalid:{exc}") from exc
        return MingliAgentReadingEnvelope.issue(
            generation_key=self.generation_key(
                requester_account_ref=requester_account_ref,
                packet=packet,
            ),
            requester_account_ref=requester_account_ref,
            case_ref=packet.case_ref,
            chart_version_ref=packet.chart_version_ref,
            life_case_revision_ref=packet.life_case_revision_ref,
            reading_ref=packet.reading_ref,
            reading_hash=packet.reading_hash,
            packet_ref=packet.packet_ref,
            packet_hash=packet.packet_hash,
            agent_profile_ref=MINGLI_AGENT_PROFILE_REF,
            agent_profile_hash=MINGLI_AGENT_PROFILE_HASH,
            provider_id=provider.provider_id,
            model_ref=provider.model_ref,
            model_digest=provider.model_digest,
            provider_profile_ref=provider.provider_profile_ref,
            provider_profile_hash=provider.provider_profile_hash,
            prompt_ref=MINGLI_AGENT_PROMPT_REF,
            prompt_hash=MINGLI_AGENT_PROMPT_HASH,
            provider_response_ref=result.provider_response_ref,
            output=result.output,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            duration_ms=result.duration_ms,
        )

    def _required_provider(self) -> MingliAgentProvider:
        if not self._enabled or self._provider is None:
            raise MingliAgentRuntimeUnavailable("mingli_agent_runtime_not_ready")
        return self._provider


def mingli_agent_runtime_status(
    current_settings: Settings = settings,
) -> MingliAgentRuntimeStatus:
    if not current_settings.mingli_agent_enabled:
        return MingliAgentRuntimeStatus.DISABLED
    if (
        current_settings.mingli_agent_provider != OLLAMA_GENERATE_PROVIDER_ID
        or not current_settings.mingli_agent_model
        or len(current_settings.mingli_agent_model_digest) != 64
    ):
        return MingliAgentRuntimeStatus.MISCONFIGURED
    if MINGLI_AGENT_PUBLICATION_ALLOWED:
        return MingliAgentRuntimeStatus.READY
    if MINGLI_AGENT_OWNER_REVIEW_ALLOWED:
        return MingliAgentRuntimeStatus.READY_FOR_OWNER_REVIEW
    return MingliAgentRuntimeStatus.DISABLED


def configured_mingli_agent_runtime(
    current_settings: Settings = settings,
) -> MingliAgentRuntime:
    status = mingli_agent_runtime_status(current_settings)
    provider: MingliAgentProvider | None = None
    if status in {
        MingliAgentRuntimeStatus.READY,
        MingliAgentRuntimeStatus.READY_FOR_OWNER_REVIEW,
    }:
        provider = OllamaMingliAgentProvider(
            model_ref=current_settings.mingli_agent_model,
            model_digest=current_settings.mingli_agent_model_digest,
            provider_profile_ref=current_settings.mingli_agent_profile_ref,
            base_url=current_settings.mingli_agent_base_url,
            timeout_seconds=current_settings.mingli_agent_timeout_seconds,
            think=current_settings.mingli_agent_think,
            temperature=current_settings.mingli_agent_temperature,
            top_p=current_settings.mingli_agent_top_p,
            top_k=current_settings.mingli_agent_top_k,
            num_ctx=current_settings.mingli_agent_num_ctx,
            num_predict=current_settings.mingli_agent_num_predict,
            keep_alive=current_settings.mingli_agent_keep_alive,
        )
    return MingliAgentRuntime(
        provider=provider,
        enabled=status
        in {
            MingliAgentRuntimeStatus.READY,
            MingliAgentRuntimeStatus.READY_FOR_OWNER_REVIEW,
        },
    )


def mingli_agent_runtime_manifest(
    current_settings: Settings = settings,
) -> dict[str, Any]:
    status = mingli_agent_runtime_status(current_settings)
    profile = {
        "provider_profile_ref": current_settings.mingli_agent_profile_ref,
        "provider_id": current_settings.mingli_agent_provider,
        "model_ref": current_settings.mingli_agent_model,
        "model_digest": current_settings.mingli_agent_model_digest,
        "agent_profile_ref": MINGLI_AGENT_PROFILE_REF,
        "agent_profile_hash": MINGLI_AGENT_PROFILE_HASH,
        "prompt_ref": MINGLI_AGENT_PROMPT_REF,
        "prompt_hash": MINGLI_AGENT_PROMPT_HASH,
        "think": current_settings.mingli_agent_think,
        "temperature": current_settings.mingli_agent_temperature,
        "top_p": current_settings.mingli_agent_top_p,
        "top_k": current_settings.mingli_agent_top_k,
        "num_ctx": current_settings.mingli_agent_num_ctx,
        "num_predict": current_settings.mingli_agent_num_predict,
        "keep_alive": current_settings.mingli_agent_keep_alive,
        "primary_call_count": 1,
        "structured_output_mode": "json_schema",
        "prompt_view_version": MINGLI_AGENT_PROMPT_VIEW_VERSION,
        "prompt_view_max_chars": MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS,
        "output_schema_max_chars": MINGLI_AGENT_OUTPUT_SCHEMA_MAX_CHARS,
    }
    return {
        "runtime_ref": MINGLI_AGENT_RUNTIME_VERSION,
        "packet_contract_ref": MINGLI_AGENT_PACKET_VERSION,
        "output_contract_ref": MINGLI_AGENT_READING_VERSION,
        "adjudication_contract_ref": MINGLI_AGENT_ADJUDICATION_VERSION,
        "method_distillation_ref": MINGLI_AGENT_METHOD_DISTILLATION_VERSION,
        "output_repair_contract_ref": MINGLI_AGENT_OUTPUT_REPAIR_VERSION,
        "method_adjudication": "TYPED_CHECK_RULINGS_AND_SERVER_DERIVED_AGGREGATE",
        "whole_chart_judgment_required": True,
        "status": status.value,
        "model_qualification_status": MINGLI_AGENT_PROFESSIONAL_REVIEW_STATUS,
        "reasoning_mode": "BLIND_READING",
        "owner_review_allowed": MINGLI_AGENT_OWNER_REVIEW_ALLOWED,
        "publication_allowed": MINGLI_AGENT_PUBLICATION_ALLOWED,
        "profile": {
            **profile,
            "provider_profile_hash": content_hash(profile),
        },
        "canonical_fact_write_allowed": False,
        "network_calls_enabled": status
        in {
            MingliAgentRuntimeStatus.READY,
            MingliAgentRuntimeStatus.READY_FOR_OWNER_REVIEW,
        },
    }


def _nonnegative_int(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


_EVIDENCE_LIST_FIELDS = {
    "day_master_evidence_ids",
    "evidence_ids",
    "mechanism_evidence_ids",
    "natal_evidence_ids",
    "relation_evidence_ids",
}


def _normalize_evidence_ids(
    value: Any,
    *,
    allowed: frozenset[str],
    field_name: str = "",
) -> Any:
    """Normalize E12 to E012 only when that exact catalog item exists."""

    if isinstance(value, dict):
        return {
            key: _normalize_evidence_ids(item, allowed=allowed, field_name=key)
            for key, item in value.items()
        }
    if isinstance(value, list):
        normalized = [
            _normalize_evidence_ids(item, allowed=allowed, field_name=field_name) for item in value
        ]
        if field_name in _EVIDENCE_LIST_FIELDS:
            return list(dict.fromkeys(item for item in normalized if item in allowed))
        return normalized
    if isinstance(value, str):
        match = re.fullmatch(r"E(\d{1,3})", value)
        if match is not None:
            normalized = f"E{int(match.group(1)):03d}"
            if normalized in allowed:
                return normalized
    return value


def _strip_evidence_ids_from_prose(value: Any, *, field_name: str = "") -> Any:
    """Repair presentation-only E### leakage without changing evidence fields."""

    evidence_fields = {
        "coordinate_evidence_id",
        "day_master_evidence_ids",
        "evidence_id",
        "evidence_ids",
        "mechanism_evidence_ids",
        "method_card_ref",
        "natal_evidence_ids",
        "relation_evidence_ids",
    }
    if isinstance(value, dict):
        return {
            key: _strip_evidence_ids_from_prose(item, field_name=key) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_strip_evidence_ids_from_prose(item, field_name=field_name) for item in value]
    if isinstance(value, str) and field_name not in evidence_fields:
        cleaned = re.sub(
            r"(?:证据(?:编号)?\s*)?[（(]?\s*(?<![A-Za-z0-9])E\d{1,3}(?!\d)\s*[）)]?",
            "",
            value,
        )
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\s+([，。；：、])", r"\1", cleaned)
        return cleaned.strip()
    return value


def _validate_packet_bound_reasoning(
    *,
    output: MingliAgentModelOutput,
    packet: MingliAgentCasePacket,
) -> None:
    prose_segments = _output_prose_segments(output)
    if any(re.search(r"(?<![A-Za-z0-9])E\d{1,3}(?!\d)", item) for item in prose_segments):
        raise ValueError("mingli_agent_output_evidence_id_leaked_into_prose")
    _validate_support_selection(output=output, packet=packet)
    _validate_hypothesis_evidence(output=output, packet=packet)
    validate_adjudication_output(output=output, packet=packet)
    _validate_timing_scope(output=output, packet=packet)


def _output_prose_segments(output: MingliAgentModelOutput) -> tuple[str, ...]:
    """Return user-facing prose only; typed evidence fields are intentionally absent."""

    segments: list[str] = [
        output.first_look,
        output.whole_chart_thesis,
        output.day_master_rationale,
        output.work_path.path_statement,
        output.work_path.condition,
        output.life_image.title,
        output.life_image.image,
        output.life_image.explanation,
        output.timing.natal_baseline,
        *output.timing.verification_signals,
        output.hypothesis_decision.winner.rationale,
        output.hypothesis_decision.loser.rationale,
        output.hypothesis_decision.reversal.question,
        output.hypothesis_decision.reversal.winner_signal,
        output.hypothesis_decision.reversal.loser_signal,
    ]
    for hypothesis in output.hypotheses:
        segments.extend(
            (
                hypothesis.name,
                hypothesis.thesis,
                hypothesis.failure_condition,
                *(ruling.rationale for ruling in hypothesis.method_rulings),
                *(ruling.condition_or_falsifier for ruling in hypothesis.method_rulings),
            )
        )
    for candidate in output.excluded_candidates:
        segments.extend((candidate.name, candidate.rationale))
    for _, domain in output.domains.ordered:
        segments.extend(
            (
                domain.headline,
                domain.conclusion,
                *domain.causal_chain,
                domain.condition,
            )
        )
    for timing in (output.timing.dayun, output.timing.annual):
        segments.extend((timing.conclusion, *timing.activation_chain))
    return tuple(segments)


def _validate_support_selection(
    *,
    output: MingliAgentModelOutput,
    packet: MingliAgentCasePacket,
) -> None:
    expected_roots = packet.day_master_support.same_element_hidden_support
    selection = output.support_selection
    if selection.root_status != ("PRESENT" if expected_roots else "NONE"):
        raise ValueError("mingli_agent_output_root_status_conflicts_with_packet")
    if selection.root_coordinates != expected_roots:
        raise ValueError("mingli_agent_output_root_selection_conflicts_with_packet")
    if selection.peer_coordinates != packet.day_master_support.visible_peer_support:
        raise ValueError("mingli_agent_output_peer_selection_conflicts_with_packet")
    if selection.resource_coordinates != packet.day_master_support.resource_support:
        raise ValueError("mingli_agent_output_resource_selection_conflicts_with_packet")


def _validate_hypothesis_evidence(
    *,
    output: MingliAgentModelOutput,
    packet: MingliAgentCasePacket,
) -> None:
    mechanism_ids = {item.evidence_id for item in packet.mechanism_observations}
    for item in output.hypotheses:
        if not set(item.mechanism_evidence_ids).issubset(mechanism_ids):
            raise ValueError("mingli_agent_output_unknown_mechanism")
    # A missing chart-basis citation weakens the primary hypothesis; it does not
    # erase the model's whole-chart reading.  The deterministic Claim Graph marks
    # that hypothesis NEEDS_RECONCILIATION while preserving every other claim.


def _validate_timing_scope(
    *,
    output: MingliAgentModelOutput,
    packet: MingliAgentCasePacket,
) -> None:
    coordinates = {item.layer: item.evidence_id for item in packet.timing_coordinates}
    relation_ids = {
        layer: {item.evidence_id for item in packet.timing_relations if item.left_layer == layer}
        for layer in ("DAYUN", "ANNUAL")
    }
    natal_ids = {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}
    dayun_allowed = natal_ids | {coordinates["DAYUN"]} | relation_ids["DAYUN"]
    annual_allowed = dayun_allowed | {coordinates["ANNUAL"]} | relation_ids["ANNUAL"]
    for layer, reading, allowed in (
        ("DAYUN", output.timing.dayun, dayun_allowed),
        ("ANNUAL", output.timing.annual, annual_allowed),
    ):
        if reading.coordinate_evidence_id != coordinates[layer]:
            raise ValueError("mingli_agent_output_timing_coordinate_conflict")
        if not set(reading.relation_evidence_ids).issubset(relation_ids[layer]):
            raise ValueError("mingli_agent_output_timing_relation_scope_conflict")
        if set(reading.evidence_ids) & relation_ids[layer] != set(reading.relation_evidence_ids):
            raise ValueError("mingli_agent_output_relation_evidence_field_mismatch")
        if not set(reading.evidence_ids).issubset(allowed):
            raise ValueError("mingli_agent_output_timing_evidence_scope_conflict")
    if not set(output.timing.natal_evidence_ids).issubset(natal_ids):
        raise ValueError("mingli_agent_output_natal_timing_basis_conflict")
