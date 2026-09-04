from __future__ import annotations

import json
import time
from typing import Any, Protocol, TypeVar, cast

from pydantic import BaseModel

from abu_v60.llm_transport import JsonTransport, LlmTransportError, default_json_transport
from abu_v60.mingli.agent_contracts import MingliAgentCasePacket
from abu_v60.mingli.synthetic_distillation_contracts import (
    MINGLI_SYNTHETIC_DISTILLATION_PROMPT_VERSION,
    MINGLI_SYNTHETIC_DISTILLATION_RUNTIME_VERSION,
    DistillationCandidateOutput,
    DistillationCertaintyOutput,
    DistillationRegimeOutput,
    SyntheticDistillationPass,
    SyntheticDistillationStage,
)
from abu_v60.mingli.synthetic_distillation_logic import (
    assemble_candidate_output,
    distillation_candidate_context,
    distillation_certainty_context,
    distillation_regime_context,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref
from abu_v60.settings import Settings, settings

MINGLI_SYNTHETIC_DISTILLATION_PROVIDER_PROFILE_REF = (
    "v60.model-serving.qwen38-27b-mingli-distillation.001"
)
MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_VERSION = "v60.mingli-synthetic-distillation-context.001"
MINGLI_SYNTHETIC_DISTILLATION_NUM_CTX = 8192
MINGLI_SYNTHETIC_DISTILLATION_SEED = 42
MINGLI_SYNTHETIC_DISTILLATION_TEMPERATURE = 0.0
MINGLI_SYNTHETIC_DISTILLATION_TOP_P = 0.95
MINGLI_SYNTHETIC_DISTILLATION_TOP_K = 20
MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_MAX_CHARS = {
    "REGIME": 12000,
    "CANDIDATE_COMPARISON": 18000,
    "CERTAINTY": 5000,
}
MINGLI_SYNTHETIC_DISTILLATION_NUM_PREDICT = {
    "REGIME": 500,
    "CANDIDATE_COMPARISON": 1800,
    "CERTAINTY": 320,
}

_STAGE_OUTPUT_TYPES: dict[SyntheticDistillationStage, type[BaseModel]] = {
    "REGIME": DistillationRegimeOutput,
    "CANDIDATE_COMPARISON": DistillationCandidateOutput,
    "CERTAINTY": DistillationCertaintyOutput,
}

_STAGE_SYSTEM_PROMPTS: dict[SyntheticDistillationStage, str] = {
    "REGIME": (
        "你只做八字原局的身弱／从势判型。命盘事实与允许出口由系统给出，不重算四柱，"
        "不谈候选机制、人生领域或岁运。选择一个合法出口，引用现有证据编号，按 JSON "
        "Schema 返回。"
    ),
    "CANDIDATE_COMPARISON": (
        "你只比较系统列出的原局机制候选。必须选择两个不同候选，逐项按给定 check_code "
        "原顺序裁决，并精确列出剩余排除集合；不重做判型，不谈人生领域或岁运，按 JSON "
        "Schema 返回。为提高本地速度，只写裁决所需最短文字：每项 rationale 8—18 字，"
        "summary 12—24 字，comparison_rationale 16—40 字，reversal_condition 12—30 字；"
        "不要复述命盘或展开同义解释。"
    ),
    "CERTAINTY": (
        "你只做结论强度映射。系统已经重算 PRIMARY 与 ALTERNATIVE 的 adjudication；"
        "逐字按映射表填写 judgment、work_path_closure 与不超过上限的 confidence，不重新推盘，"
        "按 JSON Schema 返回。"
    ),
}


def _stage_schema(stage: SyntheticDistillationStage) -> dict[str, Any]:
    return _STAGE_OUTPUT_TYPES[stage].model_json_schema()


MINGLI_SYNTHETIC_DISTILLATION_STAGE_PROMPT_HASHES = {
    stage: content_hash(
        {
            "prompt_version": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_VERSION,
            "context_version": MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_VERSION,
            "stage": stage,
            "system": _STAGE_SYSTEM_PROMPTS[stage],
            "schema": _stage_schema(stage),
        }
    )
    for stage in _STAGE_SYSTEM_PROMPTS
}
MINGLI_SYNTHETIC_DISTILLATION_PROMPT_HASH = content_hash(
    {
        "prompt_version": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_VERSION,
        "context_version": MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_VERSION,
        "stage_prompt_hashes": MINGLI_SYNTHETIC_DISTILLATION_STAGE_PROMPT_HASHES,
        "call_order": ("REGIME", "CANDIDATE_COMPARISON", "CERTAINTY"),
    }
)


class MingliSyntheticDistillationRuntimeError(RuntimeError):
    pass


class MingliSyntheticDistillationRuntimeUnavailable(MingliSyntheticDistillationRuntimeError):
    pass


class MingliSyntheticDistillationProvider(Protocol):
    provider_id: str
    model_ref: str
    model_digest: str
    provider_profile_ref: str
    provider_profile_hash: str

    def generate_stage(
        self,
        *,
        stage: SyntheticDistillationStage,
        context: dict[str, Any],
    ) -> SyntheticDistillationPass: ...


OutputModel = TypeVar("OutputModel", bound=BaseModel)


class OllamaSyntheticDistillationProvider:
    """Three small strict calls for DEV method training, never publication."""

    provider_id = "ollama-generate"

    def __init__(
        self,
        *,
        model_ref: str,
        model_digest: str,
        base_url: str,
        timeout_seconds: float,
        temperature: float,
        top_p: float,
        top_k: int,
        keep_alive: str,
        transport: JsonTransport = default_json_transport,
    ) -> None:
        if not model_ref or len(model_digest) != 64:
            raise ValueError("mingli_distillation_provider_identity_invalid")
        self.model_ref = model_ref
        self.model_digest = model_digest
        self.provider_profile_ref = MINGLI_SYNTHETIC_DISTILLATION_PROVIDER_PROFILE_REF
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = min(timeout_seconds, 240.0)
        self._temperature = temperature
        self._top_p = top_p
        self._top_k = top_k
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
            "runtime_ref": MINGLI_SYNTHETIC_DISTILLATION_RUNTIME_VERSION,
            "prompt_version": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_VERSION,
            "prompt_hash": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_HASH,
            "call_order": ("REGIME", "CANDIDATE_COMPARISON", "CERTAINTY"),
            "call_count": 3,
            "structured_output_mode": "stage_json_schema",
            "think": False,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "top_k": self._top_k,
            "seed": MINGLI_SYNTHETIC_DISTILLATION_SEED,
            "num_ctx": MINGLI_SYNTHETIC_DISTILLATION_NUM_CTX,
            "num_predict_by_stage": MINGLI_SYNTHETIC_DISTILLATION_NUM_PREDICT,
            "context_max_chars_by_stage": (MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_MAX_CHARS),
            "keep_alive": self._keep_alive,
            "publication_allowed": False,
            "qualification_effect": "DEV_TRAINING_ONLY_NOT_QUALIFICATION",
        }

    def generate_stage(
        self,
        *,
        stage: SyntheticDistillationStage,
        context: dict[str, Any],
    ) -> SyntheticDistillationPass:
        context_json = canonical_json(context)
        if len(context_json) > MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_MAX_CHARS[stage]:
            raise MingliSyntheticDistillationRuntimeError(
                f"mingli_distillation_context_budget_exceeded:{stage}"
            )
        started = time.monotonic()
        try:
            response = self._transport(
                url=f"{self._base_url}/api/generate",
                headers={"Content-Type": "application/json"},
                payload=self._payload(stage=stage, context_json=context_json),
                timeout_seconds=self._timeout_seconds,
            )
        except LlmTransportError as exc:
            raise MingliSyntheticDistillationRuntimeError(
                f"mingli_distillation_provider_failed:{stage}:{exc}"
            ) from exc
        duration_ms = max(0, round((time.monotonic() - started) * 1000))
        response_text = response.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            raise MingliSyntheticDistillationRuntimeError(
                f"mingli_distillation_provider_output_missing:{stage}"
            )
        try:
            raw_output = json.loads(response_text)
            if not isinstance(raw_output, dict):
                raise TypeError("mingli_distillation_output_not_object")
            output = _STAGE_OUTPUT_TYPES[stage].model_validate(raw_output)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MingliSyntheticDistillationRuntimeError(
                f"mingli_distillation_provider_output_invalid:{stage}:{exc}"
            ) from exc
        context_hash = content_hash(context)
        provider_response_ref = stable_ref(
            "v60-mingli-distillation-provider-response",
            {
                "provider_id": self.provider_id,
                "model_ref": self.model_ref,
                "model_digest": self.model_digest,
                "provider_profile_hash": self.provider_profile_hash,
                "stage": stage,
                "context_hash": context_hash,
                "raw_output_hash": content_hash(raw_output),
                "created_at": response.get("created_at"),
            },
        )
        input_tokens = _nonnegative_int(response.get("prompt_eval_count"))
        output_tokens = _nonnegative_int(response.get("eval_count"))
        return SyntheticDistillationPass.issue(
            stage=stage,
            context_hash=context_hash,
            stage_prompt_hash=MINGLI_SYNTHETIC_DISTILLATION_STAGE_PROMPT_HASHES[stage],
            provider_response_ref=provider_response_ref,
            raw_output=raw_output,
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            duration_ms=duration_ms,
        )

    def _payload(
        self,
        *,
        stage: SyntheticDistillationStage,
        context_json: str,
    ) -> dict[str, Any]:
        return {
            "model": self.model_ref,
            "system": _STAGE_SYSTEM_PROMPTS[stage],
            "prompt": context_json,
            "stream": False,
            "think": False,
            "format": _stage_schema(stage),
            "options": {
                "temperature": self._temperature,
                "top_p": self._top_p,
                "top_k": self._top_k,
                "seed": MINGLI_SYNTHETIC_DISTILLATION_SEED,
                "num_ctx": MINGLI_SYNTHETIC_DISTILLATION_NUM_CTX,
                "num_predict": MINGLI_SYNTHETIC_DISTILLATION_NUM_PREDICT[stage],
            },
            "keep_alive": self._keep_alive,
        }


class MingliSyntheticDistillationRuntime:
    def __init__(
        self,
        *,
        provider: MingliSyntheticDistillationProvider | None,
        enabled: bool,
    ) -> None:
        self._provider = provider
        self._enabled = enabled

    @property
    def ready(self) -> bool:
        return self._enabled and self._provider is not None

    def candidate_identity(self) -> dict[str, str]:
        provider = self._required_provider()
        return {
            "runtime_ref": MINGLI_SYNTHETIC_DISTILLATION_RUNTIME_VERSION,
            "provider_id": provider.provider_id,
            "model_ref": provider.model_ref,
            "model_digest": provider.model_digest,
            "provider_profile_ref": provider.provider_profile_ref,
            "provider_profile_hash": provider.provider_profile_hash,
            "prompt_version": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_VERSION,
            "prompt_hash": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_HASH,
        }

    def generation_key(
        self,
        *,
        experiment_ref: str,
        definition_hash: str,
        variant: str,
        packet: MingliAgentCasePacket,
    ) -> str:
        return content_hash(
            {
                "experiment_ref": experiment_ref,
                "definition_hash": definition_hash,
                "variant": variant,
                "packet_ref": packet.packet_ref,
                "packet_hash": packet.packet_hash,
                "candidate_identity": self.candidate_identity(),
            }
        )

    def run(
        self,
        *,
        packet: MingliAgentCasePacket,
    ) -> tuple[SyntheticDistillationPass, ...]:
        provider = self._required_provider()
        regime_pass = provider.generate_stage(
            stage="REGIME",
            context=distillation_regime_context(packet),
        )
        regime_output = cast(DistillationRegimeOutput, regime_pass.output)
        candidate_pass = provider.generate_stage(
            stage="CANDIDATE_COMPARISON",
            context=distillation_candidate_context(
                packet,
                regime_output=regime_output,
            ),
        )
        candidate_output = cast(
            DistillationCandidateOutput,
            candidate_pass.output,
        )
        assembly = assemble_candidate_output(packet, candidate_output)
        certainty_pass = provider.generate_stage(
            stage="CERTAINTY",
            context=distillation_certainty_context(assembly=assembly),
        )
        return regime_pass, candidate_pass, certainty_pass

    def _required_provider(self) -> MingliSyntheticDistillationProvider:
        if not self._enabled or self._provider is None:
            raise MingliSyntheticDistillationRuntimeUnavailable(
                "mingli_distillation_runtime_not_ready"
            )
        return self._provider


def configured_mingli_synthetic_distillation_runtime(
    current_settings: Settings = settings,
) -> MingliSyntheticDistillationRuntime:
    provider: MingliSyntheticDistillationProvider | None = None
    enabled = bool(current_settings.mingli_agent_enabled)
    if enabled:
        provider = OllamaSyntheticDistillationProvider(
            model_ref=current_settings.mingli_agent_model,
            model_digest=current_settings.mingli_agent_model_digest,
            base_url=current_settings.mingli_agent_base_url,
            timeout_seconds=current_settings.mingli_agent_timeout_seconds,
            temperature=MINGLI_SYNTHETIC_DISTILLATION_TEMPERATURE,
            top_p=MINGLI_SYNTHETIC_DISTILLATION_TOP_P,
            top_k=MINGLI_SYNTHETIC_DISTILLATION_TOP_K,
            keep_alive=current_settings.mingli_agent_keep_alive,
        )
    return MingliSyntheticDistillationRuntime(provider=provider, enabled=enabled)


def mingli_synthetic_distillation_runtime_manifest(
    current_settings: Settings = settings,
) -> dict[str, Any]:
    runtime = configured_mingli_synthetic_distillation_runtime(current_settings)
    profile = None
    profile_hash = None
    if runtime.ready:
        provider = runtime._required_provider()
        if isinstance(provider, OllamaSyntheticDistillationProvider):
            profile = provider.provider_profile
            profile_hash = provider.provider_profile_hash
    return {
        "runtime_ref": MINGLI_SYNTHETIC_DISTILLATION_RUNTIME_VERSION,
        "status": "READY_FOR_DEV" if runtime.ready else "DISABLED",
        "prompt_version": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_VERSION,
        "prompt_hash": MINGLI_SYNTHETIC_DISTILLATION_PROMPT_HASH,
        "provider_profile": profile,
        "provider_profile_hash": profile_hash,
        "runtime_role": "DEV_METHOD_TRAINING_ONLY",
        "network_calls_enabled": runtime.ready,
        "call_count": 3,
        "gold_in_model_context": False,
        "candidate_assembly_authority": "LOCAL_SYSTEM",
        "certainty_ceiling_authority": "LOCAL_SYSTEM",
        "strict_whole_chart_replacement_allowed": False,
        "publication_allowed": False,
        "canonical_fact_write_allowed": False,
        "qualification_effect": "DEV_TRAINING_ONLY_NOT_QUALIFICATION",
    }


def _nonnegative_int(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0
