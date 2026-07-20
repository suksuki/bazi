from __future__ import annotations

import json
import hashlib
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Protocol, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from core.mingli_agent.contracts import (
    BirthIntakeDraft,
    CaseTurnDraft,
    ChartWorldInstance,
    DomainCausalReading,
    DomainExploration,
    DiscriminatingProbe,
    DualLensCognitionDraft,
    EpistemicReviewReceipt,
    HypothesisComparisonReceipt,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    PatternHypothesisDraft,
    PatternPreviewDraft,
    PredictionProbeDraft,
    PriorPrediction,
    ReviewIssue,
    WorkPathPortraitDraft,
    WholeChartCognitionDraft,
)
from core.life_domains import LifeDomain, domain_definition, domain_reasoning_protocol
from core.mingli_agent.context import ContextStage, MingliContextCompiler, ReasoningContextPack
from core.mingli_agent.fact_review import (
    audit_professional_facts,
    assertive_claim_text,
    deterministic_fact_conflicts,
    is_parallel_predicate_fragment,
    repair_locked_fact_assertions,
)
from core.mingli_agent.model_policy import CognitiveTask, ModelPolicyRouter
from core.mingli_agent.orchestrator import CognitiveOrchestrator
from core.mingli_agent.reliability import (
    cognition_semantic_signature,
    domain_baseline_override_reason,
    domain_request_fingerprint,
    normalize_strategy_dimensions,
)


T = TypeVar("T", bound=BaseModel)
StageCallback = Callable[[str, dict[str, Any]], None]
_MODEL_LOCKS: dict[str, threading.Lock] = {}
_MODEL_LOCKS_GUARD = threading.Lock()


class CognitiveModel(Protocol):
    model: str

    def generate(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.2,
        thinking: bool = True,
        max_tokens: int = 3200,
        on_text_chunk: Callable[[str], None] | None = None,
    ) -> T: ...


class OllamaCognitiveModel:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: int = 180,
        num_ctx: int = 32768,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.num_ctx = num_ctx
        self._local = threading.local()
        with _MODEL_LOCKS_GUARD:
            self._request_lock = _MODEL_LOCKS.setdefault(f"{self.base_url}|{self.model}", threading.Lock())

    def generate(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.2,
        thinking: bool = True,
        max_tokens: int = 3200,
        on_text_chunk: Callable[[str], None] | None = None,
    ) -> T:
        self._local.last_metrics = {}
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False, separators=(",", ":"))
        base_prompt = f"{prompt}\n\n输出必须是单个 JSON 对象，严格符合以下 JSON Schema，不要 Markdown：\n{schema_json}"
        last_error: Exception | None = None
        raw = ""
        # A second full model call is too expensive for an interactive reading. Recover
        # locally when possible and surface an unrecoverable schema error immediately.
        schema_attempts = 1
        with self._request_lock:
            for attempt in range(schema_attempts):
                attempt_prompt = base_prompt
                if attempt:
                    attempt_prompt += "\n上一次输出没有形成完整 JSON。请压缩解释长度，确保所有括号和字符串闭合，优先保证结构完整。"
                payload = {
                    "model": self.model,
                    "prompt": attempt_prompt,
                    "stream": on_text_chunk is not None,
                    "think": thinking,
                    "format": schema.model_json_schema(),
                    "options": {
                        "temperature": temperature if attempt == 0 else 0.0,
                        "top_p": 0.9 if attempt == 0 else 0.75,
                        "top_k": 30,
                        "num_ctx": self.num_ctx,
                        "num_predict": max_tokens,
                        "repeat_penalty": 1.08,
                    },
                    "keep_alive": "30m",
                }
                request = urllib.request.Request(
                    f"{self.base_url}/api/generate",
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - configured local model.
                        if on_text_chunk is None:
                            body = json.loads(response.read().decode("utf-8"))
                            raw = str(body.get("response") or body.get("thinking") or "{}").strip()
                        else:
                            body, raw = _read_streaming_ollama_response(
                                response=response,
                                on_text_chunk=on_text_chunk,
                            )
                except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
                    # Replaying an expensive cognitive request does not repair transport failure and
                    # can turn one visible timeout into several minutes of silent waiting.
                    last_error = exc
                    break
                self._local.last_metrics = _ollama_metrics(
                    body=body,
                    schema_attempts=attempt + 1,
                    response_bytes=len(raw.encode("utf-8")),
                )
                try:
                    return _validate_model_json(raw=raw, schema=schema)
                except (ValueError, TypeError) as exc:
                    last_error = exc
                    if attempt + 1 < schema_attempts:
                        time.sleep(0.5)
                        continue
                    break
        error_detail = f"{type(last_error).__name__}:{last_error}" if last_error else "unknown_model_error"
        self._local.last_metrics = {
            "schema_attempts": min(schema_attempts, attempt + 1),
            "response_bytes": len(raw.encode("utf-8")),
        }
        raise ValueError(f"model_generation_failed:{error_detail}:{raw[:1600]}") from last_error

    @property
    def last_metrics(self) -> dict[str, Any]:
        return dict(getattr(self._local, "last_metrics", {}))


def _read_streaming_ollama_response(
    *,
    response: Any,
    on_text_chunk: Callable[[str], None],
) -> tuple[dict[str, Any], str]:
    response_chunks: list[str] = []
    thinking_chunks: list[str] = []
    final_body: dict[str, Any] = {}
    for raw_line in response:
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else str(raw_line)
        if not line.strip():
            continue
        item = json.loads(line)
        final_body = item
        response_part = str(item.get("response") or "")
        thinking_part = str(item.get("thinking") or "")
        if response_part:
            response_chunks.append(response_part)
            on_text_chunk(response_part)
        elif thinking_part:
            thinking_chunks.append(thinking_part)
    raw = "".join(response_chunks) or "".join(thinking_chunks) or "{}"
    return final_body, raw.strip()


def _ollama_metrics(*, body: dict[str, Any], schema_attempts: int, response_bytes: int) -> dict[str, Any]:
    def duration_ms(key: str) -> int | None:
        value = body.get(key)
        return round(value / 1_000_000) if isinstance(value, (int, float)) else None

    return {
        "transport_total_ms": duration_ms("total_duration"),
        "load_duration_ms": duration_ms("load_duration"),
        "prompt_eval_count": body.get("prompt_eval_count") if isinstance(body.get("prompt_eval_count"), int) else None,
        "prompt_eval_duration_ms": duration_ms("prompt_eval_duration"),
        "eval_count": body.get("eval_count") if isinstance(body.get("eval_count"), int) else None,
        "eval_duration_ms": duration_ms("eval_duration"),
        "schema_attempts": schema_attempts,
        "response_bytes": response_bytes,
    }


def default_reasoning_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b"),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")),
        num_ctx=int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768")),
    )


def default_pattern_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_PATTERN_MODEL", os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "240")),
        num_ctx=int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768")),
    )


def default_work_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_WORK_MODEL", os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")),
        num_ctx=int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768")),
    )


def default_domain_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_DOMAIN_MODEL", os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")),
        num_ctx=int(os.getenv("V50_MINGLI_DOMAIN_NUM_CTX", "32768")),
    )


class MingliAgent:
    def __init__(
        self,
        model: CognitiveModel | None = None,
        domain_model: CognitiveModel | None = None,
        *,
        pattern_model: CognitiveModel | None = None,
        work_model: CognitiveModel | None = None,
        model_policy: ModelPolicyRouter | None = None,
        context_compiler: MingliContextCompiler | None = None,
        orchestrator: CognitiveOrchestrator | None = None,
        p0_audit_only: bool = False,
    ) -> None:
        self.model = model or default_reasoning_model()
        self.pattern_model = pattern_model or (self.model if model is not None else default_pattern_model())
        self.work_model = work_model or (self.model if model is not None else default_work_model())
        self.domain_model = domain_model or (self.model if model is not None else default_domain_model())
        self.model_policy = model_policy or ModelPolicyRouter.from_env()
        self.context_compiler = context_compiler or MingliContextCompiler()
        self.orchestrator = orchestrator or CognitiveOrchestrator()
        # Phase-0 benchmarks must preserve the model's semantic output exactly as
        # produced. Product delivery keeps its existing repair behavior by default.
        self.p0_audit_only = p0_audit_only
        self._context_packs: list[ReasoningContextPack] = []
        self._used_routes: list[dict[str, Any]] = []

    def _compile_context(
        self,
        *,
        world: ChartWorldInstance,
        stage: ContextStage,
        cognitive_state: dict[str, Any] | None = None,
    ) -> ReasoningContextPack:
        pack = self.context_compiler.compile(world=world, stage=stage, cognitive_state=cognitive_state)
        self._context_packs.append(pack)
        return pack

    def _generate_stage(
        self,
        *,
        task: CognitiveTask,
        stage: str,
        context: ReasoningContextPack,
        model: CognitiveModel,
        prompt: str,
        schema: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        thinking: bool | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
    ) -> T:
        route = self.model_policy.route(task).model_copy(update={"model": model.model})
        self._used_routes.append(route.model_dump(mode="json"))
        try:
            def generate() -> T:
                kwargs = {
                    "prompt": prompt,
                    "schema": schema,
                    "temperature": route.temperature if temperature is None else temperature,
                    "thinking": route.thinking if thinking is None else thinking,
                    "max_tokens": route.max_tokens if max_tokens is None else max_tokens,
                }
                if on_text_chunk is not None and isinstance(model, OllamaCognitiveModel):
                    return model.generate(**kwargs, on_text_chunk=on_text_chunk)
                return model.generate(**kwargs)

            return self.orchestrator.execute(
                stage=stage,
                route=route,
                context=context,
                artifact_type=schema.__name__,
                operation=generate,
            )
        finally:
            self.orchestrator.annotate_last(stage=stage, metrics=getattr(model, "last_metrics", None))

    def first_reading(
        self,
        *,
        case_id: str,
        world: ChartWorldInstance,
        on_stage: StageCallback | None = None,
    ) -> MingliCognitiveRecord:
        self.orchestrator.reset()
        self._context_packs = []
        self._used_routes = []
        pattern_context = self._compile_context(world=world, stage="pattern")
        preview = self._generate_stage(
            task="pattern_preview",
            stage="pattern_preview",
            context=pattern_context,
            model=self.pattern_model,
            prompt=_pattern_preview_prompt(world, context_payload=pattern_context.payload),
            schema=PatternPreviewDraft,
        )
        if not self.p0_audit_only:
            preview = _filter_evidence_refs(_apply_scope_boundary(preview), world=world)
            preview = preview.model_copy(update={"preview_line": _sanitize_preview_line(preview.preview_line)})
        preview_emitted = not _pattern_preview_errors(preview=preview, world=world, context=pattern_context)
        if preview_emitted:
            _notify_stage(
                on_stage,
                "pattern_preview_ready",
                {
                    "preview_line": preview.preview_line,
                    "review_status": "fact_safe",
                    "focus_refs": preview.focus_refs,
                },
            )
        pattern = self._generate_stage(
            task="pattern_hypothesis",
            stage="pattern_hypothesis",
            context=pattern_context,
            model=self.pattern_model,
            prompt=_pattern_hypothesis_prompt(world, context_payload=pattern_context.payload),
            schema=PatternHypothesisDraft,
        )
        if not self.p0_audit_only:
            pattern = _normalize_pattern_bookkeeping(
                _filter_evidence_refs(_apply_scope_boundary(pattern), world=world)
            )
        pre_repair_errors = _pattern_hard_errors(pattern=pattern, world=world, context=pattern_context)
        deterministic_pre_repair = [
            item
            for item in deterministic_fact_conflicts(
                text=assertive_claim_text(pattern.model_dump(mode="json")),
                world=world,
            )
            if not item.startswith("地支关系未建模:")
        ]
        if deterministic_pre_repair and not self.p0_audit_only:
            pattern = _normalize_pattern_bookkeeping(
                _repair_pattern_locally(pattern, world=world)
            )
        hard_errors = _pattern_hard_errors(pattern=pattern, world=world, context=pattern_context)
        soft_issues = _unique([
            *hard_errors,
            *_pattern_soft_issues(pattern=pattern, world=world, context=pattern_context),
            *[
                f"{'待人工审阅' if self.p0_audit_only else '本地事实修复'}:{item}"
                for item in deterministic_pre_repair
                if item not in hard_errors
            ],
        ])
        if not preview_emitted:
            _notify_stage(
                on_stage,
                "pattern_preview_ready",
                {
                    "preview_line": pattern.first_look,
                    "whole_chart_thesis": pattern.whole_chart_thesis,
                    "review_status": "fact_safe",
                    "focus_refs": pattern.evidence_refs[:4],
                },
            )
        hypothesis_comparison = _review_hypothesis_space(pattern=pattern, context=pattern_context)
        _notify_stage(
            on_stage,
            "pattern_candidates_ready",
            {
                **pattern.model_dump(mode="json"),
                "soft_review": {
                    "status": "complete" if not soft_issues else "needs_enrichment",
                    "issue_count": len(soft_issues),
                },
            },
        )

        work_context = self._compile_context(
            world=world,
            stage="work_path",
            cognitive_state={"pattern": pattern.model_dump(mode="json")},
        )
        work = self._generate_stage(
            task="work_path_portrait",
            stage="work_path_portrait",
            context=work_context,
            model=self.work_model,
            prompt=_work_path_prompt(world=world, pattern=pattern, context_payload=work_context.payload),
            schema=WorkPathPortraitDraft,
        )
        if not self.p0_audit_only:
            work = _sanitize_work_questions(
                _filter_evidence_refs(_apply_scope_boundary(work), world=world),
                world=world,
            )
        work = _normalize_work_strategy_dimensions(work)
        work_errors = _work_stage_errors(work=work, world=world)
        _notify_stage(
            on_stage,
            "work_path_ready",
            {
                **work.model_dump(mode="json"),
                "soft_review": {"issues": work_errors},
            },
        )

        dual_lens: DualLensCognitionDraft | None = None
        if world.ziwei_profile.get("reasoning_ready"):
            ziwei_context = self._compile_context(
                world=world,
                stage="ziwei_integration",
                cognitive_state={
                    "bazi_pattern": pattern.model_dump(mode="json"),
                    "bazi_work": work.model_dump(mode="json"),
                },
            )
            dual_lens = self._generate_stage(
                task="ziwei_integration",
                stage="ziwei_integration",
                context=ziwei_context,
                model=self.model,
                prompt=_ziwei_integration_prompt(
                    world=world,
                    pattern=pattern,
                    work=work,
                    context_payload=ziwei_context.payload,
                ),
                schema=DualLensCognitionDraft,
            )
            if not self.p0_audit_only:
                dual_lens = _normalize_dual_probe_refs(
                    _filter_evidence_refs(_apply_scope_boundary(dual_lens), world=world),
                    pattern=pattern,
                )
            dual_errors = _dual_lens_errors(dual_lens=dual_lens, world=world)
            _notify_stage(
                on_stage,
                "ziwei_lens_ready",
                {
                    **dual_lens.model_dump(mode="json"),
                    "soft_review": {"issues": dual_errors},
                },
            )
        else:
            _notify_stage(on_stage, "ziwei_unavailable", dict(world.ziwei_profile))

        prediction_context = self._compile_context(
            world=world,
            stage="prediction",
            cognitive_state={
                "pattern": pattern.model_dump(mode="json"),
                "work": work.model_dump(mode="json"),
                "dual_lens": dual_lens.model_dump(mode="json") if dual_lens else None,
            },
        )
        predictions = self._generate_stage(
            task="prediction_probe",
            stage="prediction_probe",
            context=prediction_context,
            model=self.model,
            prompt=_prediction_stage_prompt(
                world=world,
                pattern=pattern,
                work=work,
                dual_lens=dual_lens,
                context_payload=prediction_context.payload,
            ),
            schema=PredictionProbeDraft,
        )
        if not self.p0_audit_only:
            predictions = _normalize_prediction_probe(
                _filter_evidence_refs(_apply_scope_boundary(predictions), world=world),
                pattern=pattern,
                work=work,
                world=world,
            )
        prediction_issues = _prediction_stage_errors(predictions=predictions, world=world)
        _notify_stage(
            on_stage,
            "prior_probe_ready",
            {
                **predictions.model_dump(mode="json"),
                "soft_review": {
                    "status": "complete" if not prediction_issues else "locally_repaired",
                    "issues": prediction_issues,
                },
            },
        )

        whole = _assemble_whole_chart(pattern=pattern, work=work, predictions=predictions, dual_lens=dual_lens)
        if self.p0_audit_only:
            repaired_payload = whole.model_dump(mode="json")
            locked_fact_repairs: list[str] = []
        else:
            repaired_payload, locked_fact_repairs = repair_locked_fact_assertions(
                payload=whole.model_dump(mode="json"),
                world=world,
            )
        draft = MingliCognitiveDraft(**repaired_payload)
        model_identity = f"pattern:{self.pattern_model.model}|whole:{self.model.model}"
        receipt = review_cognition(
            draft=draft,
            world=world,
            model=model_identity,
            repaired=bool(locked_fact_repairs),
        )
        reliability_signature = cognition_semantic_signature(draft)
        _notify_stage(
            on_stage,
            "whole_chart_ready",
            {
                "first_look": draft.first_look,
                "whole_chart_thesis": draft.whole_chart_thesis,
                "selected_hypothesis_id": draft.selected_hypothesis_id,
                "locked_fact_repairs": locked_fact_repairs,
                "review": receipt.model_dump(mode="json"),
            },
        )
        return MingliCognitiveRecord(
            record_id=f"cognition-{uuid4().hex[:20]}",
            case_id=case_id,
            world_id=world.world_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            model=model_identity,
            cognition=draft,
            review=receipt,
            hypothesis_comparison=hypothesis_comparison,
            stage_receipts=[item.model_dump(mode="json") for item in self.orchestrator.receipt().stage_receipts],
            context_manifest=[
                {
                    "stage": item.stage,
                    "content_hash": item.content_hash,
                    "fact_count": len(item.fact_refs),
                    "knowledge_count": len(item.knowledge_refs),
                    "excluded_fact_count": item.excluded_fact_count,
                    "excluded_knowledge_count": item.excluded_knowledge_count,
                    "attention_selected_refs": item.attention_receipt.selected_fact_refs,
                    "attention_critical_omissions": item.attention_receipt.critical_omission_refs,
                    "reasoning_phase": item.reasoning_phase,
                    "experimental_tool_refs": item.experimental_tool_refs,
                }
                for item in self._context_packs
            ],
            model_routes=list(self._used_routes),
            domain_explorations={},
            reliability_disposition=receipt.disposition,
            reliability_signature=reliability_signature,
        )

    def first_baseline_reading(
        self,
        *,
        case_id: str,
        world: ChartWorldInstance,
        on_stage: StageCallback | None = None,
    ) -> MingliCognitiveRecord:
        """Create the production whole-chart baseline with one cognitive model call.

        The older staged protocol remains available to offline experiments. Public
        first-run uses this method so domains are not precomputed and the user is
        blocked by exactly one professional cognition call.
        """

        self.orchestrator.reset()
        self._context_packs = []
        self._used_routes = []
        context = self._compile_context(world=world, stage="baseline")
        partial_json = ""
        preview_emitted = False
        baseline_started = time.perf_counter()

        def on_text_chunk(chunk: str) -> None:
            nonlocal partial_json, preview_emitted
            if preview_emitted:
                return
            partial_json = (partial_json + chunk)[-120_000:]
            first_look = _extract_completed_json_string(partial_json, key="first_look")
            if not first_look:
                return
            first_look = _sanitize_preview_line(first_look)
            if not first_look or not _preview_is_fact_safe(text=first_look, world=world):
                return
            preview_emitted = True
            _notify_stage(
                on_stage,
                "baseline_preview_ready",
                {
                    "preview_line": first_look,
                    "status": "provisional",
                    "persisted": False,
                    "elapsed_seconds": round(time.perf_counter() - baseline_started, 3),
                },
            )

        whole = self._generate_stage(
            task="baseline_cognition",
            stage="baseline_cognition",
            context=context,
            model=self.model,
            prompt=_baseline_cognition_prompt(world=world, context_payload=context.payload),
            schema=WholeChartCognitionDraft,
            on_text_chunk=on_text_chunk,
        )
        draft, pattern, locked_fact_repairs = _normalize_baseline_cognition(whole=whole, world=world)
        model_identity = f"baseline:{self.model.model}"
        comparison = _review_hypothesis_space(pattern=pattern, context=context)
        receipt = review_cognition(
            draft=draft,
            world=world,
            model=model_identity,
            repaired=bool(locked_fact_repairs),
        )
        if _review_requires_one_repair(receipt):
            repaired_whole = self._generate_stage(
                task="baseline_cognition",
                stage="baseline_repair",
                context=context,
                model=self.model,
                prompt=_single_baseline_repair_prompt(
                    world=world,
                    draft=draft,
                    receipt=receipt,
                    context_payload=context.payload,
                ),
                schema=WholeChartCognitionDraft,
                temperature=0.0,
            )
            draft, pattern, second_locked_repairs = _normalize_baseline_cognition(
                whole=repaired_whole,
                world=world,
            )
            locked_fact_repairs = [*locked_fact_repairs, *second_locked_repairs]
            comparison = _review_hypothesis_space(pattern=pattern, context=context)
            receipt = review_cognition(
                draft=draft,
                world=world,
                model=model_identity,
                repaired=True,
            )
        reliability_signature = cognition_semantic_signature(draft)
        _notify_stage(
            on_stage,
            "baseline_draft_ready",
            {
                "status": "draft",
                "first_look": draft.first_look,
                "whole_chart_thesis": draft.whole_chart_thesis,
                "primary_path": draft.work_path.path_statement,
                "key_condition": (draft.work_path.success_conditions or [""])[0],
                "uncertainty": (draft.unresolved_questions or [""])[0],
            },
        )
        return MingliCognitiveRecord(
            record_id=f"cognition-{uuid4().hex[:20]}",
            case_id=case_id,
            world_id=world.world_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            model=model_identity,
            cognition=draft,
            review=receipt,
            hypothesis_comparison=comparison,
            stage_receipts=[item.model_dump(mode="json") for item in self.orchestrator.receipt().stage_receipts],
            context_manifest=[
                {
                    "stage": item.stage,
                    "content_hash": item.content_hash,
                    "fact_count": len(item.fact_refs),
                    "knowledge_count": len(item.knowledge_refs),
                    "excluded_fact_count": item.excluded_fact_count,
                    "excluded_knowledge_count": item.excluded_knowledge_count,
                    "attention_selected_refs": item.attention_receipt.selected_fact_refs,
                    "attention_critical_omissions": item.attention_receipt.critical_omission_refs,
                    "reasoning_phase": item.reasoning_phase,
                    "experimental_tool_refs": item.experimental_tool_refs,
                }
                for item in self._context_packs
            ],
            model_routes=list(self._used_routes),
            domain_explorations={},
            reliability_disposition=receipt.disposition,
            reliability_signature=reliability_signature,
        )

    def explore_domain(
        self,
        *,
        world: ChartWorldInstance,
        record: MingliCognitiveRecord,
        domain: LifeDomain,
        user_question: str = "",
        baseline_insight_id: str = "",
        baseline_case_version: str = "v1",
        chart_version_id: str = "",
        temporal_scope: str = "current",
        on_stage: StageCallback | None = None,
    ) -> DomainExploration:
        if domain is LifeDomain.WHOLE_CHART:
            raise ValueError("whole_chart_already_available")
        existing = record.domain_explorations.get(domain)
        route = self.model_policy.route("domain_reasoning")
        implementation_versions = {
            "reasoner_id": "deepbazi.mingli_agent.domain",
            "reasoner_version": "on-demand-domain-v1",
            "prompt_hash": hashlib.sha256(b"extended-domain-reasoning-v1").hexdigest()[:16],
            "model_version": route.model,
            "knowledge_version": "deepbazi-world-v1",
            "gate_version": "mingli_reliability_gate_v1",
            "context_compiler_version": "mingli-context-v1",
        }
        input_context_hash = hashlib.sha256(
            json.dumps(
                {
                    "world_id": world.world_id,
                    "baseline_signature": record.reliability_signature or cognition_semantic_signature(record.cognition),
                    "selected_hypothesis_id": record.cognition.selected_hypothesis_id,
                    "domain": domain.value,
                    "question": " ".join(user_question.strip().split()),
                    "baseline_context_hashes": [item.get("content_hash") for item in record.context_manifest],
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:24]
        request_fingerprint = domain_request_fingerprint(
            record=record,
            world_id=world.world_id,
            domain=domain,
            user_question=user_question,
            case_version=baseline_case_version,
            chart_version_id=chart_version_id,
            temporal_scope=temporal_scope,
            implementation_versions=implementation_versions,
            input_context_hash=input_context_hash,
        )
        current_cache_review = (
            review_domain_reading(
                reading=existing.reading,
                world=world,
                model=existing.review.model,
                baseline_record=record,
                expected_domain=domain,
            )
            if existing
            else None
        )
        cache_ready = bool(
            existing
            and current_cache_review
            and current_cache_review.commit_eligible
            and existing.request_fingerprint == request_fingerprint
            and existing.baseline_record_id == record.record_id
            and existing.baseline_insight_id == baseline_insight_id
            and existing.baseline_case_version == baseline_case_version
            and existing.implementation_versions == implementation_versions
            and existing.input_context_hash == input_context_hash
            and existing.temporal_scope == temporal_scope
            and existing.baseline_semantic_signature == (
                record.reliability_signature or cognition_semantic_signature(record.cognition)
            )
        )
        if cache_ready:
            _notify_stage(
                on_stage,
                "domain_cache_reused",
                {
                    "domain": domain.value,
                    "baseline_record_id": record.record_id,
                    "request_fingerprint": request_fingerprint,
                },
            )
            return existing.model_copy(update={
                "review": current_cache_review,
                "reliability_disposition": current_cache_review.disposition,
            })
        whole = _whole_chart_from_record(record)
        _notify_stage(
            on_stage,
            "domain_baseline_reused",
            {
                "domain": domain.value,
                "baseline_record_id": record.record_id,
                "baseline_insight_id": baseline_insight_id,
                "baseline_semantic_signature": (
                    record.reliability_signature or cognition_semantic_signature(record.cognition)
                ),
                "preview_line": whole.first_look,
            },
        )
        protocol = domain_reasoning_protocol(domain)
        context = self.context_compiler.compile(
            world=world,
            stage="domain",
            cognitive_state={
                "whole": whole.model_dump(mode="json"),
                "domain": domain.value,
                "user_question": user_question,
            },
        )
        domain_context_payload = _domain_context_payload(
            context.payload,
            relevant_palaces=protocol.relevant_ziwei_palaces,
        )
        partial_json = ""
        preview_emitted = False
        domain_started = time.perf_counter()

        def on_text_chunk(chunk: str) -> None:
            nonlocal partial_json, preview_emitted
            if preview_emitted:
                return
            partial_json = (partial_json + chunk)[-120_000:]
            direction = _extract_first_completed_json_array_string(partial_json, key="causal_chain")
            if not direction:
                return
            direction = _sanitize_preview_line(direction)
            if not direction or not _preview_is_fact_safe(text=direction, world=world):
                return
            preview_emitted = True
            _notify_stage(
                on_stage,
                "domain_preview_ready",
                {
                    "domain": domain.value,
                    "preview_line": direction,
                    "status": "provisional",
                    "persisted": False,
                    "elapsed_seconds": round(time.perf_counter() - domain_started, 3),
                },
            )

        generation_kwargs = {
            "prompt": _extended_domain_reasoning_prompt(
                world=world,
                whole=whole,
                domain=domain,
                user_question=user_question,
                context_payload=domain_context_payload,
            ),
            "schema": DomainCausalReading,
            "temperature": route.temperature,
            "thinking": route.thinking,
            "max_tokens": route.max_tokens,
        }
        if isinstance(self.domain_model, OllamaCognitiveModel):
            reading = self.domain_model.generate(**generation_kwargs, on_text_chunk=on_text_chunk)
        else:
            reading = self.domain_model.generate(**generation_kwargs)
        reading = _normalize_domain_reading(reading, domain=domain)
        locked_fact_repairs: list[str] = []
        review = review_domain_reading(
            reading=reading,
            world=world,
            model=self.domain_model.model,
            repaired=bool(locked_fact_repairs),
            baseline_record=record,
            expected_domain=domain,
        )
        repair_attempted = False
        if _review_requires_one_repair(review):
            repair_attempted = True
            reading = self.domain_model.generate(
                prompt=_single_domain_repair_prompt(
                    world=world,
                    whole=whole,
                    domain_reading=reading,
                    receipt=review,
                    context_payload=domain_context_payload,
                ),
                schema=DomainCausalReading,
                temperature=0.0,
                thinking=route.thinking,
                max_tokens=route.max_tokens,
            )
            reading = _normalize_domain_reading(
                reading,
                domain=domain,
            )
            review = review_domain_reading(
                reading=reading,
                world=world,
                model=self.domain_model.model,
                repaired=True,
                baseline_record=record,
                expected_domain=domain,
            )
        override_reason = domain_baseline_override_reason(reading=reading, record=record)
        revision_candidate = (
            {
                "kind": "case_revision_candidate",
                "reason": override_reason,
                "baseline_record_id": record.record_id,
                "baseline_insight_id": baseline_insight_id,
                "domain": domain.value,
            }
            if override_reason
            else None
        )
        return DomainExploration(
            domain=domain,
            reading=reading,
            review=review,
            reasoning_protocol=protocol.model_dump(mode="json"),
            context_manifest={
                "stage": context.stage,
                "content_hash": context.content_hash,
                "fact_refs": context.fact_refs,
                "knowledge_refs": context.knowledge_refs,
                "excluded_fact_count": context.excluded_fact_count,
                "excluded_knowledge_count": context.excluded_knowledge_count,
                "attention_selected_refs": context.attention_receipt.selected_fact_refs,
                "attention_critical_omissions": context.attention_receipt.critical_omission_refs,
                "relevant_ziwei_palaces": protocol.relevant_ziwei_palaces,
                "included_ziwei_palaces": list((domain_context_payload.get("ziwei_profile") or {}).get("palaces", {})),
                "model_route": route.model_dump(mode="json"),
                "locked_fact_repairs": locked_fact_repairs,
                "semantic_repair_attempted": repair_attempted,
            },
            generated_at=datetime.now(timezone.utc).isoformat(),
            reliability_disposition=review.disposition,
            baseline_record_id=record.record_id,
            baseline_insight_id=baseline_insight_id,
            baseline_case_version=baseline_case_version,
            baseline_semantic_signature=record.reliability_signature or cognition_semantic_signature(record.cognition),
            request_fingerprint=request_fingerprint,
            implementation_versions=implementation_versions,
            input_context_hash=input_context_hash,
            temporal_scope=temporal_scope,
            case_revision_candidate=revision_candidate,
        )

    def continue_case(
        self,
        *,
        world: ChartWorldInstance,
        record: MingliCognitiveRecord,
        user_message: str,
    ) -> CaseTurnDraft:
        turn = self.model.generate(
            prompt=_case_turn_prompt(world=world, record=record, user_message=user_message),
            schema=CaseTurnDraft,
            temperature=0.24,
            thinking=False,
            max_tokens=1800,
        )
        return _filter_evidence_refs(_apply_scope_boundary(turn), world=world)

    def parse_birth_intake(self, *, message: str, current: BirthIntakeDraft | None = None) -> BirthIntakeDraft:
        prompt = f"""
你是 Abu 的出生信息整理器。只提取用户明确说出的信息，不推测未说出的出生地、日期或性别。
把相对口语时间转换为 24 小时 HH:MM；无法确定时保留 unknown 并提出一个最关键的澄清问题。
公历/阳历映射 solar，农历/阴历映射 lunar。中国大陆默认时区 Asia/Shanghai，韩国默认 Asia/Seoul。
必须在姓名、性别、历法、出生日期、出生时间、出生地点齐全后才 ready_for_confirmation=true。

已有草稿：
{json.dumps(current.model_dump(mode='json') if current else {}, ensure_ascii=False)}

用户本轮：{message}
""".strip()
        return self.model.generate(
            prompt=prompt,
            schema=BirthIntakeDraft,
            temperature=0.0,
            thinking=False,
            max_tokens=700,
        )


def review_cognition(
    *,
    draft: MingliCognitiveDraft,
    world: ChartWorldInstance,
    model: str,
    repaired: bool = False,
) -> EpistemicReviewReceipt:
    issues: list[ReviewIssue] = []
    allowed = set(world.allowed_evidence_refs)
    cited = _all_citations(draft)
    unknown = sorted(ref for ref in cited if not _citation_allowed(ref=ref, allowed=allowed))
    if unknown:
        issues.append(ReviewIssue(code="unknown_evidence_refs", severity="error", message=", ".join(unknown[:12])))
    if len(draft.hypotheses) < 2:
        issues.append(ReviewIssue(code="insufficient_competing_hypotheses", severity="warning", message="本轮只保留一个事实安全的命局假设"))
    hypothesis_ids = {item.hypothesis_id for item in draft.hypotheses}
    if draft.selected_hypothesis_id not in hypothesis_ids:
        issues.append(ReviewIssue(code="selected_hypothesis_missing", severity="error", message=draft.selected_hypothesis_id))
    if not any(item.status == "primary" and item.hypothesis_id == draft.selected_hypothesis_id for item in draft.hypotheses):
        issues.append(ReviewIssue(code="primary_status_mismatch", severity="error", message="主假设标记不一致"))
    if not draft.prior_predictions:
        issues.append(ReviewIssue(code="missing_prior_predictions", severity="warning", message="本轮没有保留可安全展示的先验判断"))
    if len({item.claim for item in draft.prior_predictions}) != len(draft.prior_predictions):
        issues.append(ReviewIssue(code="repeated_prior_predictions", severity="error", message="先验预测重复"))
    generated_domains = [item for item in (draft.career, draft.wealth) if item is not None]
    if any(len(item.causal_chain) < 2 for item in generated_domains):
        issues.append(ReviewIssue(code="thin_domain_causal_chain", severity="error", message="已生成领域需要完整因果链"))
    if not draft.work_path.failure_conditions:
        issues.append(ReviewIssue(code="work_path_without_failure_conditions", severity="warning", message="主做功尚未补充失效条件"))
    if not any(item.rejection_reason for item in draft.hypotheses if item.status == "alternative"):
        issues.append(ReviewIssue(code="alternatives_not_compared", severity="warning", message="替代假设缺少放弃原因"))
    if any(item.lens == "mixed" for item in draft.useful_god_reasoning):
        issues.append(ReviewIssue(
            code="ambiguous_strategy_dimension",
            severity="error",
            message="调候、扶抑、结构、制化、做功与时序不能压缩成 mixed 用神结论",
        ))
    for item in draft.useful_god_reasoning:
        if not item.question_answered.strip():
            issues.append(ReviewIssue(
                code="strategy_question_missing",
                severity="error",
                message=f"{item.candidate}:{item.lens} 没有说明正在回答哪一个命理问题",
            ))
        if not item.applicable_conditions or not item.invalidating_conditions:
            issues.append(ReviewIssue(
                code="strategy_conditions_missing",
                severity="error",
                message=f"{item.candidate}:{item.lens} 缺少成立或失效条件",
            ))
    generic = ("有机会也有挑战", "保持积极心态", "平衡工作与生活", "相信自己", "顺其自然")
    draft_payload = draft.model_dump(mode="json")
    corpus = json.dumps(draft_payload, ensure_ascii=False)
    assertive_text = assertive_claim_text(draft_payload)
    for phrase in generic:
        if phrase in corpus:
            issues.append(ReviewIssue(code="generic_advice", severity="warning", message=phrase))
    for error in _semantic_text_errors(text=assertive_text, world=world, include_deterministic=False):
        issues.append(ReviewIssue(code="mingli_fact_conflict", severity="error", message=error))
    for fact_issue in audit_professional_facts(text=assertive_text, world=world, claim_ref="whole_chart_cognition"):
        issues.append(
            ReviewIssue(
                code=f"professional_fact:{fact_issue.issue_type}",
                severity="error" if fact_issue.severity in {"hard", "major"} else "warning",
                message=(
                    f"{fact_issue.original_text} | {fact_issue.canonical_fact_ref} | "
                    f"{fact_issue.modality} | {fact_issue.disposition}"
                ),
            )
        )
    traceability = 1.0 if not cited else round(sum(_citation_allowed(ref=ref, allowed=allowed) for ref in cited) / len(cited), 3)
    return _finalize_review(
        issues=issues,
        fact_traceability_rate=traceability,
        model=model,
        repaired=repaired,
        competing=_cognition_has_unresolved_competition(draft),
    )


def review_domain_reading(
    *,
    reading: DomainCausalReading,
    world: ChartWorldInstance,
    model: str,
    repaired: bool = False,
    baseline_record: MingliCognitiveRecord | None = None,
    expected_domain: LifeDomain | None = None,
) -> EpistemicReviewReceipt:
    issues: list[ReviewIssue] = []
    allowed = set(world.allowed_evidence_refs)
    if baseline_record is not None:
        allowed.update(_baseline_cognitive_reference_ids(baseline_record))
    cited = _domain_reading_citations(reading)
    unknown = sorted(ref for ref in cited if not _citation_allowed(ref=ref, allowed=allowed))
    if unknown:
        issues.append(ReviewIssue(code="unknown_evidence_refs", severity="error", message=", ".join(unknown[:12])))
    if not 2 <= len(reading.causal_chain) <= 6:
        issues.append(ReviewIssue(code="invalid_causal_chain", severity="error", message="领域因果链需要保持可理解的完整路径"))
    if not reading.assertions:
        issues.append(ReviewIssue(code="thin_domain_assertions", severity="error", message="领域至少需要一条可证伪断言"))
    if any(item.domain != reading.domain for item in reading.assertions):
        issues.append(ReviewIssue(code="domain_scope_leakage", severity="error", message="领域断言越界"))
    if expected_domain is not None and reading.domain != expected_domain:
        issues.append(ReviewIssue(
            code="domain_scope_leakage",
            severity="error",
            message=f"请求领域为 {expected_domain.value}，模型却返回 {reading.domain.value}",
        ))
    if reading.next_probe is not None and len(reading.next_probe.options) < 2:
        issues.append(ReviewIssue(code="invalid_domain_probe", severity="error", message="已经提出的问题需要提供可区分的回答方式"))
    elif reading.next_probe is not None and len(reading.next_probe.distinguishes_hypothesis_refs) < 2:
        issues.append(ReviewIssue(code="thin_domain_probe_targets", severity="warning", message="当前问题尚未充分区分两条断言"))
    elif reading.next_probe is not None:
        probe_targets = set(reading.next_probe.distinguishes_hypothesis_refs)
        known_targets = {item.assertion_id for item in reading.assertions}
        if baseline_record is not None:
            known_targets.update(item.hypothesis_id for item in baseline_record.cognition.hypotheses)
        unknown_targets = sorted(probe_targets - known_targets)
        if unknown_targets:
            issues.append(ReviewIssue(
                code="invalid_domain_probe",
                severity="error",
                message=f"Probe 引用了不存在的专题断言或整盘假设：{', '.join(unknown_targets)}",
            ))
    reading_payload = reading.model_dump(mode="json")
    corpus = json.dumps(reading_payload, ensure_ascii=False)
    assertive_text = assertive_claim_text(reading_payload)
    for phrase in ("有机会也有挑战", "保持积极心态", "顺其自然", "因人而异"):
        if phrase in corpus:
            issues.append(ReviewIssue(code="generic_domain_advice", severity="error", message=phrase))
    protocol = domain_reasoning_protocol(reading.domain)
    for forbidden in protocol.forbidden_claims:
        if forbidden in corpus:
            issues.append(ReviewIssue(code="forbidden_domain_claim", severity="error", message=forbidden))
    for forbidden in _forbidden_domain_tokens(reading.domain):
        if forbidden in corpus:
            issues.append(ReviewIssue(code="high_risk_domain_claim", severity="error", message=forbidden))
    for error in _semantic_text_errors(text=assertive_text, world=world, include_deterministic=False):
        issues.append(ReviewIssue(code="mingli_fact_conflict", severity="error", message=error))
    for fact_issue in audit_professional_facts(
        text=assertive_text,
        world=world,
        claim_ref=f"domain:{reading.domain.value}",
    ):
        issues.append(
            ReviewIssue(
                code=f"professional_fact:{fact_issue.issue_type}",
                severity="error" if fact_issue.severity in {"hard", "major"} else "warning",
                message=(
                    f"{fact_issue.original_text} | {fact_issue.canonical_fact_ref} | "
                    f"{fact_issue.modality} | {fact_issue.disposition}"
                ),
            )
        )
    if baseline_record is not None:
        override_reason = domain_baseline_override_reason(reading=reading, record=baseline_record)
        if override_reason:
            issues.append(ReviewIssue(
                code="baseline_override_attempt",
                severity="error",
                message=override_reason,
            ))
    traceability = 1.0 if not cited else round(sum(_citation_allowed(ref=ref, allowed=allowed) for ref in cited) / len(cited), 3)
    competing = bool(reading.assertions) and not any(
        item.epistemic_status == "supported" for item in reading.assertions
    )
    return _finalize_review(
        issues=issues,
        fact_traceability_rate=traceability,
        model=model,
        repaired=repaired,
        competing=competing,
    )


def _finalize_review(
    *,
    issues: list[ReviewIssue],
    fact_traceability_rate: float,
    model: str,
    repaired: bool,
    competing: bool,
) -> EpistemicReviewReceipt:
    classified = [_classify_review_issue(item) for item in issues]
    hard_failures = [item.code for item in classified if item.blocks_commit]
    repairable = [item.code for item in classified if item.repairable]
    disposition = "blocked" if hard_failures else "competing" if competing else "reliable"
    return EpistemicReviewReceipt(
        passed=not hard_failures,
        issues=classified,
        fact_traceability_rate=fact_traceability_rate,
        model=model,
        repaired=repaired,
        disposition=disposition,
        commit_eligible=disposition == "reliable",
        hard_failure_codes=_unique(hard_failures),
        repairable_issue_codes=_unique(repairable),
        gate_version="mingli_reliability_gate_v1",
    )


def _classify_review_issue(issue: ReviewIssue) -> ReviewIssue:
    code = issue.code
    if code == "mingli_fact_conflict" or code.startswith("professional_fact:"):
        category = "chart_fact"
        repairable = False
    elif code == "unknown_evidence_refs":
        category = "evidence"
        repairable = True
    elif code in {
        "selected_hypothesis_missing",
        "primary_status_mismatch",
        "repeated_prior_predictions",
        "ambiguous_strategy_dimension",
        "strategy_question_missing",
        "strategy_conditions_missing",
        "baseline_override_attempt",
    }:
        category = "semantic_consistency"
        repairable = code not in {"baseline_override_attempt"}
    elif code in {"forbidden_domain_claim", "high_risk_domain_claim", "domain_scope_leakage"}:
        category = "safety"
        repairable = True
    elif code in {
        "thin_domain_causal_chain",
        "invalid_causal_chain",
        "thin_domain_assertions",
        "invalid_domain_probe",
    }:
        category = "completeness"
        repairable = True
    elif "hypothes" in code or code in {"alternatives_not_compared", "thin_domain_probe_targets"}:
        category = "hypothesis_competition"
        repairable = issue.severity == "error"
    else:
        category = "quality"
        repairable = issue.severity == "error"
    return issue.model_copy(update={
        "category": category,
        "blocks_commit": issue.severity == "error",
        "repairable": repairable,
    })


def _cognition_has_unresolved_competition(draft: MingliCognitiveDraft) -> bool:
    selected = next(
        (item for item in draft.hypotheses if item.hypothesis_id == draft.selected_hypothesis_id),
        None,
    )
    if selected is None or selected.confidence == "low":
        return True
    confidence_rank = {"low": 1, "medium": 2, "high": 3}
    for item in draft.hypotheses:
        if item.hypothesis_id == draft.selected_hypothesis_id:
            continue
        if not item.rejection_reason.strip():
            return True
        if item.status == "unresolved" and confidence_rank[item.confidence] >= confidence_rank[selected.confidence]:
            return True
        if (
            confidence_rank[item.confidence] >= confidence_rank[selected.confidence]
            and not item.rejection_reason.strip()
        ):
            return True
    return False


def _normalize_work_strategy_dimensions(work: WorkPathPortraitDraft) -> WorkPathPortraitDraft:
    return work.model_copy(update={
        "useful_god_reasoning": normalize_strategy_dimensions(work.useful_god_reasoning),
    })


def _normalize_baseline_cognition(
    *,
    whole: WholeChartCognitionDraft,
    world: ChartWorldInstance,
) -> tuple[MingliCognitiveDraft, PatternHypothesisDraft, list[str]]:
    pattern = PatternHypothesisDraft(
        first_look=whole.first_look,
        whole_chart_thesis=whole.whole_chart_thesis,
        salient_phenomena=whole.salient_phenomena,
        hypotheses=whole.hypotheses,
        selected_hypothesis_id=whole.selected_hypothesis_id,
        evidence_refs=whole.evidence_refs,
    )
    work = _normalize_work_strategy_dimensions(
        WorkPathPortraitDraft(
            work_path=whole.work_path,
            useful_god_reasoning=whole.useful_god_reasoning,
            portrait=whole.portrait,
            unresolved_questions=whole.unresolved_questions,
            evidence_refs=whole.evidence_refs,
        )
    )
    predictions = PredictionProbeDraft(
        prior_predictions=whole.prior_predictions,
        next_probe=whole.next_probe,
    )
    dual_lens = whole.dual_lens if world.ziwei_profile.get("reasoning_ready") else None
    assembled = _assemble_whole_chart(
        pattern=pattern,
        work=work,
        predictions=predictions,
        dual_lens=dual_lens,
    )
    return MingliCognitiveDraft(**assembled.model_dump(mode="json")), pattern, []


def _review_requires_one_repair(receipt: EpistemicReviewReceipt) -> bool:
    blocking = [item for item in receipt.issues if item.blocks_commit]
    return bool(blocking) and all(item.repairable for item in blocking)


def _forbidden_domain_tokens(domain: LifeDomain) -> tuple[str, ...]:
    return {
        LifeDomain.RELATIONSHIP: ("一定结婚", "必然结婚", "一定离婚", "必然离婚", "婚期就在"),
        LifeDomain.CHILDREN_LEGACY: ("一定生育", "必然生育", "生几个", "生男", "生女"),
        LifeDomain.HEALTH_VITALITY: ("诊断为", "患有", "癌症", "肿瘤", "心脏病", "肝病", "寿命", "死亡时间"),
        LifeDomain.LIFE_TIMING: ("一定会发生", "必然发生", "保证在", "灾祸日期", "发财年份"),
    }.get(domain, ())


def _notify_stage(callback: StageCallback | None, event_type: str, payload: dict[str, Any]) -> None:
    if callback is None:
        return
    try:
        callback(event_type, payload)
    except Exception:  # noqa: BLE001 - delivery failure must not alter cognition.
        return


def _pattern_hypothesis_prompt(
    world: ChartWorldInstance,
    *,
    context_payload: dict[str, Any] | None = None,
) -> str:
    payload = context_payload or _reasoning_world_payload(world)
    return f"""
你是 DeepBazi 的整盘模式识别者。此轮只完成“第一眼、盘面重心、竞争假设”，不写做功细节、用神、领域和 Probe。

规则：
- 先找全局力量集中在哪里、哪个节点连接或改变全局，再谈旺衰。
- 这是独立第一眼阶段。上下文不会提供 Graph/Path/Role/敏感度排名；不得假设系统已经替你选好重心。
- 至少 2 个、最多 3 个竞争假设，只选 1 个 primary；每个假设必须写 failure_conditions，替代假设必须写 rejection_reason。
- 从格与主动食伤做功不能混为一个假设。日主弱不自动从格。
- immutable_chart_ledger 是十神与五行事实权威。
- 在写任何格局名或“财、官杀、印、食伤”之前，先按 element_role_ledger 核对日主对应关系；模型记忆与账本冲突时必须服从账本。
- 控制关系只服从 element_cycles。不得因为某元素数量多就反转生克方向，也不得把财富压力误写成官杀压力。
- visible_ten_gods 已排除日干本人；统计比肩数量时不得把日主自己再算进去。
- salient_phenomena 最多 3 条；每条必须引用存在的短 evidence id。
- 每条 salient_phenomena 的 evidence_refs 必须至少出现在一个假设的 supporting_evidence_refs 或 counter_evidence_refs 中，表示该重心已被假设空间解释。
- 只有一个 primary，selected_hypothesis_id 必须指向它；替代假设必须是不同的因果解释，不得换词重复主假设。
- attention 中 critical/high 项是本轮优先检查对象；最终假设空间必须引用并解释至少一条高优先注意力事实。
- transformation 表示生、克、合、冲等作用关系，不表示一种元素物理变成另一种元素；不同机制不能用斜线拼成一个万能解释。
- 每个候选假设都必须从本轮不可变事实或中性关系独立推出。不得假设存在外部标准答案或研究标签。
- 不写人生建议、职业、财富、事件或年份。

最小命理世界：
{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}
    """.strip()


def _pattern_preview_prompt(
    world: ChartWorldInstance,
    *,
    context_payload: dict[str, Any] | None = None,
) -> str:
    payload = context_payload or _reasoning_world_payload(world)
    return f"""
你是 DeepBazi 的整盘观察者。现在只返回一条可以立即给用户看的“第一眼”，完整假设稍后再做。

硬规则：
- preview_line 只写一句中文，40 到 90 字，指出全局力量重心、关键连接或核心矛盾。
- 不写职业、财富、健康、事件、年份、建议或吉凶。
- 不下最终格局结论，不使用“必然、纯从、破格、灾祸”等确定词。
- 不把一种五行写成转化为另一种五行；生克合冲必须服从账本。
- 连续因果必须逐段写清，例如“食伤生财、财再生杀”；禁止用“生财化杀”省略或混合中间关系。
- focus_refs 提供 1 到 4 个真正支持这句话的短 evidence id。
- 不输出解释过程。

最小命理世界：
{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _pattern_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    errors: list[str],
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
整盘模式识别存在事实或假设错误。只重写 PatternHypothesisDraft，不扩展到做功、领域或事件。

必须修复：{json.dumps(errors, ensure_ascii=False)}
命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

从格和主动输出做功必须分开比较；所有元素与十神服从账本。
每个假设都必须列出可证伪的 failure_conditions；每个 alternative 都必须解释本盘为何暂不采用。
逐条核对 salient_phenomena.evidence_refs，确保每个引用至少进入一个假设的 supporting_evidence_refs 或 counter_evidence_refs。
修复时不得引入命理世界中不存在的结构标签；只比较能由当前事实和工具观察支持的候选。
""".strip()


def _work_path_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
整盘模式与主假设已经冻结。此轮只形成主做功、体用、条件用神、整盘画像和未决问题。

规则：
- 此轮可以读取 experimental_tool_observation 作为 Challenge Pack，但它们不是答案，也不具备裁决权。
- 比较系统枚举候选、知识检索候选和你基于事实组合的路径；工具没有表达的路径可以保留为 llm_composed，但每一步必须映射回事实。
- 主做功必须写清 source -> transformation -> target；每个元素和十神角色唯一。
- 五行只允许木生火、火生土、土生金、金生水、水生木；木克土、土克水、水克火、火克金、金克木。
- 用神是让主路径成立的角色，不是缺什么补什么；最多 2 个候选。
- 用神、忌神、通关与桥接必须说明 lens、正在回答的问题、成立条件和失效条件，不能写成脱离主路径的永久标签。
- lens 只能在 climate、support_balance、structure、transformation、work_path、timing、domain 中选择；禁止 mixed。
- 原局结构与当前岁运策略必须分别写，不能因为当前阶段过旺而反向改写原局需要。
- portrait 只写 2 条可证伪整盘断言，不写职业清单或具体事件。
- portrait.claim 必须是普通用户能直接理解的现实倾向，不出现 AST、node、converter、英文内部标签或吉凶绝对化语言；技术依据只写在 rationale。
- 不重新选择主假设，不引入新格局。
- transformation 表示作用关系，不表示元素变成另一元素；例如丁火只能制约酉金，不能“转化为酉金”。

命理世界：
{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

冻结的模式假设：
{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _work_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    errors: list[str],
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
主做功与画像存在事实错误。保持冻结的主假设，只重写 WorkPathPortraitDraft。

必须修复：{json.dumps(errors, ensure_ascii=False)}
命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
冻结假设：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

不得混用五行生克，不得更换 target 的十神角色，不得用“或”拼接互斥路径。
""".strip()


def _prediction_stage_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    dual_lens: DualLensCognitionDraft | None,
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
根据冻结的整盘假设与主做功，生成少量可被现实明确否定的高信息量先验判断；只有确实能区分解释时才提出行为问题。

规则：
- 优先覆盖整盘行为方式、事业价值形成、财富形成/承载；不为凑数量重复表达。
- claim 使用普通人能理解的现实语言，禁止“必然、一定、绝对、只要就”等过度确定表达。
- 每条写出 disconfirming_answer，不能用“有机会也有挑战”。
- 本轮 Probe 优先询问用户面对某类现实压力通常怎么处理；不追问灾难、健康或确定事件。
- Probe 选项必须对应不同处理机制，distinguishes_hypothesis_refs 至少包含主假设和一个替代假设。
- 若存在双镜头认知，Probe 可以优先验证八字长期结构与紫微当前舞台之间的张力，但仍必须问现实行为而非玄学术语。

命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
冻结假设：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
冻结做功：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
双镜头认知：{json.dumps(dual_lens.model_dump(mode='json') if dual_lens else None, ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _prediction_stage_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    dual_lens: DualLensCognitionDraft | None,
    predictions: PredictionProbeDraft,
    errors: list[str],
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
先验与 Probe 没有满足可证伪和行为区分要求。只重写 PredictionProbeDraft。

必须修复：{json.dumps(errors, ensure_ascii=False)}
假设：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
做功：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
双镜头认知：{json.dumps(dual_lens.model_dump(mode='json') if dual_lens else None, ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(predictions.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
允许引用：{json.dumps(world.allowed_evidence_refs, ensure_ascii=False)}
最小命理世界：{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _ziwei_integration_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    context_payload: dict[str, Any],
) -> str:
    return f"""
你是 DeepBazi 的双镜头命理认知主体。八字整盘模式与主做功已经冻结；此轮只做紫微第一眼，并与八字比较。

职责边界：
- 八字负责长期结构、力量流向和做功；紫微负责人生舞台、宫位主题、角色分布与当前时序窗口。
- 不得用紫微改写四柱、十神或八字主假设；不得把八字术语硬套到星曜。
- 不得罗列十二宫和全部星曜。只挑 2 至 4 个真正改变理解的宫位观察，至少覆盖 identity、career、wealth 中的两个领域。
- 每个观察必须引用当前上下文中真实存在的 ziwei fact id，并写出反面成立条件。
- agreements 写两套系统互相支持的内容；tensions 写它们关注点不同或尚未一致的内容。没有张力可以为空，不能制造冲突。
- integrated_thesis 必须说明“长期结构如何在具体人生舞台中表现”，不是把两段摘要拼起来。
- current_stage_note 只能条件性解释当前大限/流年所激活的舞台，不预测确定事件。
- cross_lens_probe 只问一个现实行为问题，用于区分长期倾向与当前阶段；不得问用户懂不懂星曜。
- 不足的出生时间、空宫借宫、弱证据和时序不确定性必须写入 uncertainties。

紫微事实与不可变账本：
{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}

冻结的八字模式：
{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

冻结的八字主做功：
{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _ziwei_integration_repair_prompt(
    *,
    world: ChartWorldInstance,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    dual_lens: DualLensCognitionDraft,
    errors: list[str],
    context_payload: dict[str, Any],
) -> str:
    return f"""
双镜头认知没有满足事实引用、角色分工或可证伪要求。只重写 DualLensCognitionDraft。

必须修复：{json.dumps(errors, ensure_ascii=False)}
允许引用：{json.dumps(world.allowed_evidence_refs, ensure_ascii=False)}
紫微事实与不可变账本：{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}
冻结八字模式：{json.dumps(pattern.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
冻结八字主做功：{json.dumps(work.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
原结果：{json.dumps(dual_lens.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

不得增加不存在的星曜、宫位、四化或时序；不得把候选写成确定事件；Probe 必须是普通用户能回答的现实行为问题。
""".strip()


def _ziwei_probe_repair_prompt(
    *,
    pattern: PatternHypothesisDraft,
    dual_lens: DualLensCognitionDraft,
    errors: list[str],
) -> str:
    return f"""
双镜头认知本身已经保留，只修正其中的现实鉴别问题。不要重写紫微观察、整合结论或八字假设。

必须修复：{json.dumps(errors, ensure_ascii=False)}
竞争假设：{json.dumps([{"hypothesis_id": item.hypothesis_id, "name": item.name, "thesis": item.thesis} for item in pattern.hypotheses], ensure_ascii=False, separators=(',', ':'))}
当前双镜头结论：{json.dumps({"integrated_thesis": dual_lens.integrated_thesis, "agreements": dual_lens.agreements, "tensions": dual_lens.tensions}, ensure_ascii=False, separators=(',', ':'))}
原问题：{json.dumps(dual_lens.cross_lens_probe.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

输出一个普通用户能凭现实经历回答的问题：
- 不出现星曜、宫位、命宫、四化、大限等术语；
- 不要求用户判断命理理论；
- 必须提供至少两个清晰选项；
- 必须区分至少两个给定的假设 id；
- 只写 DiscriminatingProbe。
""".strip()


def _whole_chart_prompt(world: ChartWorldInstance) -> str:
    world_payload = _reasoning_world_payload(world)
    return f"""
你是 DeepBazi 的命理认知主体，一位擅长子平、格局、体用、做功、象法与反事实比较的资深命理师。

你的任务不是扩写字段，而是独立理解这张完整八字。系统只提供事实、工具观察和相关知识；路径分数、节点分数和机制提示都不是答案。你必须批判地使用它们。

DeepBazi 看盘纲领：
- 先看全局力量如何做功、流向哪里、在哪里闭合或失败，再谈旺衰和格局名称。
- 日主弱不自动等于从格；必须检查透干同类、输出节点、制化路径和反事实消融。
- 三合成局说明气势与连接，不自动等于命主顺从该五行，也不直接等于吉凶。
- 财、官杀、印、食伤必须严格服从不可变十神账本；不得按生活语义混称。
- 用神是让主做功成立或修复失败条件的角色，不是“缺什么补什么”。
- 从格与“食神制杀/输出制压”是竞争解释，不能混成“假从食伤制杀格”。如果输出节点仍主动做功，从格只能作为替代假设。
- 一个主假设只保留一条主导因果链。不要把食伤生财、食神制杀、从儿、从杀堆成一个万能格局名。
- 主做功中的 source、transformation、target 必须角色唯一；不能把同一个金局一会儿写官杀、一会儿写财星，也不能用“或”逃避选择。
- 五行只允许木生火、火生土、土生金、金生水、水生木；只允许木克土、土克水、水克火、火克金、金克木。禁止写“火生金”等错误关系。
- 不要用生活语义偷换命理关系；所有生克与十神角色必须从当前命盘账本推出。
- 同一日主下，同阴阳同五行才是比肩，异阴阳才是劫财。不得因为同类多就把具体天干含混写成“比劫夺财”。
- 本轮不开放健康和具体事件预测，先验不得断疾病、失业、破财或必然年份。

认知要求：
1. 第一眼先指出盘面真正的重心，必须具体到此盘的干支、位置或结构关系。
2. 形成至少两个竞争命局假设，比较支持、反证和失败条件，再选择主假设。
3. 明确主做功、体用关系、结构闭合与破坏条件。
4. 用神只能条件化解释：它在何种结构中有用，何时反而有害。
5. 在不知道现实职业、收入和性格的前提下，给出整盘画像、事业和财富的先验判断。
6. 先验判断必须可被用户回答推翻；不为凑数量重复判断，Probe 只在能区分竞争假设时提出。
7. 重要结论必须引用下方存在的 fact_id / observation id / knowledge_id；不得编造引用。
8. 十神账本是不可修改的权威事实。禁止凭模型记忆重新计算十神，禁止把官杀说成财星、把食神说成伤官。
9. Timing 标记为研究候选，只能条件性表达，禁止确定事件和精确发财升职年份。
10. 不要说“有机会也有挑战”“保持平衡”等可适用于任何人的话。

命理世界实例：
{json.dumps(world_payload, ensure_ascii=False, separators=(',', ':'))}

请直接返回符合 JSON Schema 的中文认知结果。所有 id 使用简短 ASCII，例如 h1、a-career-1、probe-1。
""".strip()


def _single_domain_reasoning_prompt(
    *,
    world: ChartWorldInstance,
    whole: WholeChartCognitionDraft,
    domain: str,
    context_payload: dict[str, Any] | None = None,
) -> str:
    domain_instruction = (
        "事业必须回答价值如何形成、适合处理什么问题、什么组织环境有利或消耗。"
        if domain == "career"
        else "财富必须回答财富如何形成、承载、保留和流失，财在做功中是目标、工具、结果还是压力。"
    )
    return f"""
你是 DeepBazi 的命理认知主体。整盘假设竞争已经完成，现在只推演 `{domain}` 一个领域。

要求：
1. 领域判断必须继承整盘主假设、主做功和失败条件，不能重新套十神模板。
2. 写出完整而自然的因果链：命局结构 -> 能力/行为方式 -> 环境互动 -> 条件性结果；按本盘需要控制在 2 至 6 步，不凑固定步数。
3. {domain_instruction}
4. 方向只能作为可证伪先验，不得根据用户现实经历倒推。
5. 每条重要断言引用允许的事实、观察或知识 id。十神账本不可修改。
6. 不要输出通用人生建议，不要制造确定事件。
7. 不得把元素生克方向写反；尤其禁止“土克火”“火生金”等错误关系。
8. Timing 只允许引用 timing_context 已给出的当前候选，不得擅自扩写连续年份区间。
9. 风险必须写成结构条件与可观察行为，禁止戏剧化事件。
10. 返回对象的 domain 必须是 `{domain}`，不要生成另一个领域。
11. 信息预算：只保留改变判断的内容；各列表通常 1 至 3 条，允许更少，不为满足数量重复表达。
12. 每条尽量在 80 个汉字内，直接写因果，不重复整盘结论。

最小命理世界：
{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

整盘认知：
{json.dumps(whole.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _baseline_cognition_prompt(
    *,
    world: ChartWorldInstance,
    context_payload: dict[str, Any],
) -> str:
    ziwei_ready = bool(world.ziwei_profile.get("reasoning_ready"))
    return f"""
你是 DeepBazi 的专业命理认知主体。请用一次完整推理形成这张命盘的整盘基线认知。

这不是事业、财富、关系或健康报告。只回答四件事：
1. 整盘最核心的结构重心是什么；
2. 命局主要通过哪条路径运行，并比较至少一个竞争解释；
3. 哪些条件会使主路径增强、受阻或转向；
4. 当前有哪些不确定性，以及什么现实表现可以区分竞争假设。

认知要求：
- 先整体识别 Pattern，再比较 Hypothesis；不要把单一旺衰、十神标签或候选工具路径直接当结论。
- 每个 alternative hypothesis 必须填写 rejection_reason，明确它为什么暂时不是主解释；如果证据不足以排除，标记为 unresolved，并把主假设 confidence 降到 medium 或 low。
- Graph、Path、Role、Ablation 都只是候选观察，LLM 必须综合命盘事实和知识后判断。
- work_path 写命理解释链，不包装成现代科学因果。
- useful_god_reasoning 必须是条件性的，并分别说明它在调候、扶抑、格局、制化、做功或当前岁运中回答什么问题；说明何时有用、何时反而有害。
- useful_god_reasoning.lens 只能使用 climate、support_balance、structure、transformation、work_path、timing、domain；禁止 mixed，原局与当前阶段不得写成同一个结论。
- prior_predictions 只保留 1 至 3 条可被现实反驳的整盘先验，不进入具体人生领域。
- next_probe 只问一个真正能区分两个命局假设的现实问题。
- 不写通用心理话术，不写“有机会也有挑战”“保持平衡”等任何盘都适用的话。
- 每个重要判断引用当前上下文中存在的 evidence id；不知道时保留 unknown，不得补猜。
- 紫微可用：{str(ziwei_ready).lower()}。只有可用时才填写 dual_lens，并只用它复核人生舞台，不覆盖八字主线。
- 不预计算任何 domain，不输出具体疾病、投资收益、婚期或其他确定事件。

最小充分命理世界：
{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _extended_domain_reasoning_prompt(
    *,
    world: ChartWorldInstance,
    whole: WholeChartCognitionDraft,
    domain: LifeDomain,
    user_question: str,
    context_payload: dict[str, Any],
) -> str:
    definition = domain_definition(domain)
    protocol = domain_reasoning_protocol(domain)
    return f"""
你是 DeepBazi 的命理认知主体。整盘认知已经冻结，现在只推演“{definition.name_zh}”。

这不是栏目模板。你必须从本盘主假设、主做功、失败条件、八字事实和相关紫微宫位推导这个领域。

领域协议：
{json.dumps(protocol.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

公开边界：{definition.boundary or '只给条件性、可证伪的命理理解，不制造必然事件。'}
用户当前问题：{user_question or '尚未给出更具体的问题，先形成领域先验。'}

要求：
1. domain 必须是 `{domain.value}`，所有 assertions 也必须属于同一领域。
2. causal_chain 按本盘需要保留 2 至 6 步：命局结构 -> 心理/能力或互动方式 -> 环境作用 -> 条件性结果。
3. 不得改变整盘主假设、主做功、分层用神逻辑或命盘事实；若专题证据真的要求修正，只能明确写成“需要修正整盘基线”的候选，不得在专题里悄悄替换。
4. 只选择真正相关的紫微宫位，不得罗列十二宫。
5. 只保留有区分力的可证伪断言，并引用存在的 evidence id；一条强断言好于多条重复断言。
6. 风险写成结构条件和可观察行为，不写戏剧化事件。
7. 时机只引用 timing_context 的候选状态，不擅自发明年份。
8. 严格遵守 forbidden_claims；健康只谈精力、压力和生活节奏，不诊断。
9. 不写“有机会也有挑战”“保持平衡”等任何盘都适用的话。
10. 各列表只保留改变判断的 1 至 3 条内容，允许更少，不凑固定数量。
11. 只有存在真正未决分歧时才提供 next_probe；若提供，至少有 2 个自然语言选项，distinguishes_hypothesis_refs 引用本领域 assertions 的 assertion_id。

最小领域世界：
{json.dumps(context_payload, ensure_ascii=False, separators=(',', ':'))}

冻结整盘认知：
{json.dumps(whole.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _whole_chart_from_record(record: MingliCognitiveRecord) -> WholeChartCognitionDraft:
    payload = {
        field: getattr(record.cognition, field)
        for field in WholeChartCognitionDraft.model_fields
    }
    whole = WholeChartCognitionDraft.model_validate(payload)
    return WholeChartCognitionDraft.model_validate(sanitize_public_mingli_payload(whole.model_dump(mode="json")))


def sanitize_public_mingli_payload(value: Any, *, _preserve_machine_value: bool = False) -> Any:
    if _preserve_machine_value:
        return value
    if isinstance(value, dict):
        return {
            key: sanitize_public_mingli_payload(
                child,
                _preserve_machine_value=_is_machine_contract_key(key),
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [sanitize_public_mingli_payload(child) for child in value]
    if not isinstance(value, str):
        return value
    text = value
    text = re.sub(r"未记录（仅凭\s*V\d+\s*导入）", "资料未完整记录", text, flags=re.IGNORECASE)
    text = re.sub(r"未记录（\s*V\d+\s*导入）", "资料未完整记录", text, flags=re.IGNORECASE)
    text = re.sub(r"V\d+\s*导入", "历史档案", text, flags=re.IGNORECASE)
    text = re.sub(r"V\d+", "历史版本", text, flags=re.IGNORECASE)
    text = re.sub(r"admin_profile|fixture|runtime|schema", "内部资料", text, flags=re.IGNORECASE)
    return text.replace("会彻底改变", "需要重新评估").replace("彻底改变", "需要重新评估").replace("结构性崩塌", "原有路径可能失效")


def _is_machine_contract_key(key: str) -> bool:
    normalized = key.lower()
    return (
        normalized in {"version", "case_version", "from_case_version", "to_case_version"}
        or normalized.endswith(("_id", "_ids", "_ref", "_refs", "_hash", "_key", "_version", "_versions", "_fingerprint"))
    )


def _domain_context_payload(payload: dict[str, Any], *, relevant_palaces: list[str]) -> dict[str, Any]:
    output = json.loads(json.dumps(payload, ensure_ascii=False))
    profile = output.get("ziwei_profile") or {}
    palaces = profile.get("palaces") or {}
    requested = {
        name.replace("大限", "").replace("流年", "")
        for name in relevant_palaces
    }
    profile["palaces"] = {
        name: value
        for name, value in palaces.items()
        if name in requested
    }
    output["ziwei_profile"] = profile
    return output


def _normalize_domain_reading(reading: DomainCausalReading, *, domain: LifeDomain) -> DomainCausalReading:
    causal_chain = list(reading.causal_chain)
    if len(causal_chain) == 1:
        lines = [item.strip(" -\t") for item in re.split(r"\n+", causal_chain[0]) if item.strip(" -\t")]
        if 2 <= len(lines) <= 6:
            causal_chain = lines
    del domain
    return reading.model_copy(update={"causal_chain": causal_chain})


def _domain_reading_citations(reading: DomainCausalReading) -> set[str]:
    return {
        ref
        for assertion in reading.assertions
        for ref in [*assertion.evidence_refs, *assertion.counter_evidence_refs]
        if ref
    }


def _baseline_cognitive_reference_ids(record: MingliCognitiveRecord) -> set[str]:
    cognition = record.cognition
    refs = {record.record_id}
    refs.update(item.phenomenon_id for item in cognition.salient_phenomena)
    refs.update(item.hypothesis_id for item in cognition.hypotheses)
    refs.update(item.assertion_id for item in cognition.portrait)
    refs.update(item.prediction_id for item in cognition.prior_predictions)
    if cognition.dual_lens is not None:
        refs.update(item.observation_id for item in cognition.dual_lens.palace_observations)
    return {ref for ref in refs if ref}


def _structural_repair_prompt(*, world: ChartWorldInstance, whole: WholeChartCognitionDraft, errors: list[str]) -> str:
    structural = whole.model_dump(mode="json")
    structural.pop("prior_predictions", None)
    structural.pop("next_probe", None)
    return f"""
你刚才的整盘结构认知存在事实或假设混合错误。只重写整盘结构，不生成先验预测或 Probe。
必须保留具体盘面重心、竞争假设、主做功和条件用神，不得用空话回避。

必须修复：{json.dumps(errors, ensure_ascii=False)}

事实与结构先验：
{json.dumps(_reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

原认知：
{json.dumps(structural, ensure_ascii=False, separators=(',', ':'))}

特别注意：十神和五行生克只服从 immutable_chart_ledger、element_role_ledger 和 element_cycles。
从格与主动食伤制杀必须作为不同假设，不能混进同一个主假设名称。每个元素和十神角色必须唯一。
""".strip()


def _prediction_repair_prompt(*, world: ChartWorldInstance, whole: WholeChartCognitionDraft) -> str:
    safe_whole = whole.model_dump(mode="json")
    safe_whole.pop("prior_predictions", None)
    safe_whole.pop("next_probe", None)
    return f"""
根据已经形成的整盘认知，只重新生成三条可证伪的先验画像/事业/财富预测和一个区分性问题。

硬边界：
- 不预测疾病、健康、失业、破财、死亡、婚姻事件或灾祸。
- 不写确定年份和必然事件。
- 不给通用建议。
- 每条预测都必须能被用户回答明确否定，并引用存在的短 evidence id。
- Probe 必须区分当前主假设与至少一个替代假设。

命理世界：
{json.dumps(_reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

整盘认知：
{json.dumps(safe_whole, ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _probe_repair_prompt(*, world: ChartWorldInstance, whole: WholeChartCognitionDraft) -> str:
    hypotheses = [
        {
            "hypothesis_id": item.hypothesis_id,
            "name": item.name,
            "thesis": item.thesis,
            "status": item.status,
        }
        for item in whole.hypotheses
    ]
    return f"""
只生成一个能区分主假设与替代假设的现实行为问题。

硬规则：
- 询问用户在某类现实压力下通常怎样处理，不问某年发生了什么。
- 禁止年份、大运、疾病、灾难、失败、破财和重大事件。
- 选项必须对应两种不同处理机制；不能只是“是/不是”。
- purpose 要说明每个答案会增强哪个 hypothesis_id。
- distinguishes_hypothesis_refs 至少包含主假设和一个替代假设。

竞争假设：
{json.dumps(hypotheses, ensure_ascii=False, separators=(',', ':'))}

盘面主做功：
{json.dumps(whole.work_path.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _single_domain_repair_prompt(
    *,
    world: ChartWorldInstance,
    whole: WholeChartCognitionDraft,
    domain_reading: DomainCausalReading,
    receipt: EpistemicReviewReceipt,
    context_payload: dict[str, Any] | None = None,
) -> str:
    return f"""
整盘认知已经冻结，不允许重写。`{domain_reading.domain}` 领域推演中出现了事实、引用或边界问题。
请只重写这个 DomainCausalReading，保留具体因果判断，不得改成套话，也不得生成另一个领域。

评审问题：
{json.dumps(receipt.model_dump(mode='json'), ensure_ascii=False)}

命理世界与不可变账本：
{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

冻结的整盘认知：
{json.dumps(whole.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

原领域推演：
{json.dumps(domain_reading.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

修复引用、因果链和可证伪性。所有五行关系、十神关系和 timing 范围必须逐句回到账本；
风险改写成结构条件与可观察行为，不写戏剧化事件。不得添加冻结整盘认知之外的新格局。
""".strip()


def _single_baseline_repair_prompt(
    *,
    world: ChartWorldInstance,
    draft: MingliCognitiveDraft,
    receipt: EpistemicReviewReceipt,
    context_payload: dict[str, Any],
) -> str:
    return f"""
这是一份整盘认知草稿的唯一一次完整性修复。不得更换命局主线，不得掩盖竞争假设，
不得把事实冲突改写成听起来合理的文字。只修复评审指出的引用、条件、因果链、
可证伪性或字段完整性问题，并返回完整 WholeChartCognitionDraft。

如果原草稿缺少足够依据，不要编造依据；应降低 hypothesis confidence、保留 unresolved_questions，
或把相关假设标为 unresolved。调候、扶抑、格局、制化、做功与当前时序必须分开表达，
每条 UsefulGodReasoning 必须说明它回答的问题、适用范围、成立条件和失效条件。

评审问题：
{json.dumps(receipt.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

命理世界与不可变事实：
{json.dumps(context_payload or _reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

原整盘草稿：
{json.dumps(draft.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}
""".strip()


def _case_turn_prompt(*, world: ChartWorldInstance, record: MingliCognitiveRecord, user_message: str) -> str:
    return f"""
你是 Abu 背后的 DeepBazi 命理认知 Agent。用户正在围绕一个已经建立的命理案例继续交流。

规则：
- 判断来自命盘认知，不要根据用户答案倒推第一份命理结论。
- 如果用户是在验证先验预测，明确哪些假设增强、减弱或保持不变。
- 如果用户提出事业或财富问题，沿已有整盘认知继续做因果推演。
- 如果用户问“为什么”，解释关键现象、竞争假设与反证，不要暴露内部逐字思维链。
- 一次回复聚焦一个问题；必要时只提出一个高信息增益 Probe。
- 不得修改命盘事实，不得把一次用户反馈写成全局理论。

命理世界：
    {json.dumps(_reasoning_world_payload(world), ensure_ascii=False, separators=(',', ':'))}

当前案例认知：
{json.dumps(record.model_dump(mode='json'), ensure_ascii=False, separators=(',', ':'))}

用户：{user_message}
""".strip()


def _all_citations(draft: MingliCognitiveDraft) -> set[str]:
    refs = set(draft.evidence_refs)
    refs.update(ref for item in draft.salient_phenomena for ref in item.evidence_refs)
    refs.update(ref for item in draft.hypotheses for ref in item.supporting_evidence_refs)
    refs.update(ref for item in draft.hypotheses for ref in item.counter_evidence_refs)
    refs.update(draft.work_path.evidence_refs)
    refs.update(ref for item in draft.useful_god_reasoning for ref in item.evidence_refs)
    refs.update(ref for item in draft.portrait for ref in item.evidence_refs)
    for domain in (draft.career, draft.wealth):
        if domain is not None:
            refs.update(ref for item in domain.assertions for ref in item.evidence_refs)
    refs.update(ref for item in draft.prior_predictions for ref in item.evidence_refs)
    return {ref for ref in refs if ref}


def _domain_evidence_refs(*domains: DomainCausalReading) -> list[str]:
    return _unique([
        ref
        for domain in domains
        for assertion in domain.assertions
        for ref in [*assertion.evidence_refs, *assertion.counter_evidence_refs]
    ])


def _normalize_json_object(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key).strip(): _normalize_json_object(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_normalize_json_object(item) for item in value]
    return value


def _validate_model_json(*, raw: str, schema: type[T]) -> T:
    try:
        return schema.model_validate(_normalize_json_object(json.loads(raw)))
    except Exception as first_error:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise ValueError(f"model_json_missing:{raw[:1200]}") from first_error
        try:
            return schema.model_validate(_normalize_json_object(json.loads(match.group(0))))
        except Exception as second_error:
            raise ValueError(f"model_json_invalid:{raw[:1600]}") from second_error


def _citation_allowed(*, ref: str, allowed: set[str]) -> bool:
    if ref in allowed:
        return True
    match = re.fullmatch(r"([FOK])(\d{3})\s*[-–—]\s*\1?(\d{3})", ref)
    if not match:
        return False
    prefix, start_text, end_text = match.groups()
    start, end = int(start_text), int(end_text)
    if end < start or end - start > 120:
        return False
    return f"{prefix}{start:03d}" in allowed and f"{prefix}{end:03d}" in allowed


def _apply_scope_boundary(value: T) -> T:
    """Remove unsupported event drama without rewriting the Mingli reasoning."""

    replacements = {
        "资金链断裂": "资源承载明显失衡",
        "重大健康危机": "未开放领域的外部因素",
        "健康危机": "未开放领域的外部因素",
        "健康受损": "未开放领域的外部因素",
        "筋骨疼痛": "未开放领域的外部因素",
        "肝胆": "未开放领域",
        "疾病": "未开放领域因素",
        "失业": "职业连续性中断",
        "重大挫折": "路径明显受阻",
        "重大变故": "外部条件显著变化",
        "必然破财": "资源风险显著上升",
        "招灾": "风险显著上升",
        "死亡": "极端外部因素",
    }

    def rewrite(item: Any) -> Any:
        if isinstance(item, str):
            for source, target in replacements.items():
                item = item.replace(source, target)
            item = re.sub(r"20\d{2}\s*(?:-|—|–|至|到)\s*20\d{2}\s*年?", "相关行运阶段", item)
            return item
        if isinstance(item, list):
            return [rewrite(child) for child in item]
        if isinstance(item, dict):
            return {key: rewrite(child) for key, child in item.items()}
        return item

    return type(value).model_validate(rewrite(value.model_dump(mode="json")))


def _filter_evidence_refs(value: T, *, world: ChartWorldInstance) -> T:
    """Keep LLM cognition intact while dropping references that do not exist."""

    allowed = set(world.allowed_evidence_refs)

    def rewrite(item: Any, key: str = "") -> Any:
        if isinstance(item, list):
            if key.endswith("evidence_refs"):
                return [ref for ref in item if isinstance(ref, str) and _citation_allowed(ref=ref, allowed=allowed)]
            return [rewrite(child) for child in item]
        if isinstance(item, dict):
            return {child_key: rewrite(child, child_key) for child_key, child in item.items()}
        return item

    return type(value).model_validate(rewrite(value.model_dump(mode="json")))


def _sanitize_work_questions(work: WorkPathPortraitDraft, *, world: ChartWorldInstance) -> WorkPathPortraitDraft:
    questions: list[str] = []
    for question in work.unresolved_questions:
        # A question is not an asserted natal fact, but its premise can still be
        # unusable. Convert only the interrogative wrapper for this product-only
        # sanitation check; Phase-0 raw review never calls this function.
        asserted_premise = re.sub(r"^(?:请确认|请判断)?(?:是否|能否|会否)(?:存在|构成|形成)?", "命局存在", question)
        asserted_premise = asserted_premise.rstrip("？?")
        errors = _semantic_text_errors(text=question, world=world, include_deterministic=False)
        errors.extend(deterministic_fact_conflicts(text=asserted_premise, world=world))
        if not errors:
            questions.append(question)
    return work.model_copy(update={"unresolved_questions": questions})


def _soften_prediction_text(text: str) -> str:
    replacements = {
        "绝对阈值": "明显界限",
        "吉凶判定": "阶段判断",
        "瞬间转为凶险": "短期内明显承压",
        "立即崩塌": "较快失去支撑",
        "结构性崩塌": "结构明显失衡",
        "彻底改变": "明显调整",
        "一定会": "更可能",
        "注定": "更可能",
    }
    softened = text
    for source, target in replacements.items():
        softened = softened.replace(source, target)
    softened = re.sub(r"(?<![不非])必然", "更可能", softened)
    return softened


def _sanitize_preview_line(text: str) -> str:
    cleaned = re.sub(r"[（(\[]\s*(?:F|O|K)\d{3}(?:\s*[,，、]\s*(?:F|O|K)\d{3})*\s*[）)\]]", "", text)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _extract_completed_json_string(text: str, *, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*', text)
    if not match or match.end() >= len(text) or text[match.end()] != '"':
        return None
    start = match.end()
    escaped = False
    for index in range(start + 1, len(text)):
        character = text[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == '"':
            try:
                value = json.loads(text[start : index + 1])
            except json.JSONDecodeError:
                return None
            return value if isinstance(value, str) else None
    return None


def _extract_first_completed_json_array_string(text: str, *, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*\[\s*', text)
    if not match or match.end() >= len(text) or text[match.end()] != '"':
        return None
    synthetic = '{"value":' + text[match.end() :]
    return _extract_completed_json_string(synthetic, key="value")


def _preview_is_fact_safe(*, text: str, world: ChartWorldInstance) -> bool:
    if deterministic_fact_conflicts(text=text, world=world):
        return False
    return not any(
        item.severity in {"hard", "major"}
        for item in audit_professional_facts(
            text=text,
            world=world,
            claim_ref="baseline_stream_preview",
        )
    )


def _normalize_prediction_probe(
    predictions: PredictionProbeDraft,
    *,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    world: ChartWorldInstance,
) -> PredictionProbeDraft:
    """Repair presentation bookkeeping locally without asking the model to rethink the chart."""

    safe_predictions: list[PriorPrediction] = []
    seen_claims: set[str] = set()
    for item in predictions.prior_predictions:
        candidate = item.model_copy(update={
            "claim": _soften_prediction_text(item.claim),
            "why_predicted": _soften_prediction_text(item.why_predicted),
            "disconfirming_answer": _soften_prediction_text(item.disconfirming_answer),
        })
        signature = re.sub(r"\s+", "", candidate.claim)
        if not signature or signature in seen_claims:
            continue
        seen_claims.add(signature)
        safe_predictions.append(candidate)
        if len(safe_predictions) == 3:
            break

    selected_ref = pattern.selected_hypothesis_id
    for assertion in work.portrait:
        if len(safe_predictions) == 3:
            break
        claim = _soften_prediction_text(assertion.claim)
        signature = re.sub(r"\s+", "", claim)
        if not signature or signature in seen_claims:
            continue
        candidate = PriorPrediction(
            prediction_id=f"portrait-{assertion.assertion_id}",
            claim=claim,
            why_predicted=_soften_prediction_text(assertion.rationale),
            target_hypothesis_ref=selected_ref,
            evidence_refs=list(assertion.evidence_refs),
            disconfirming_answer=(
                _soften_prediction_text(assertion.falsifiers[0])
                if assertion.falsifiers
                else "如果长期现实表现与这条倾向相反，应降低这条判断的权重。"
            ),
        )
        seen_claims.add(signature)
        safe_predictions.append(candidate)

    probe = predictions.next_probe
    probe_updates = {key: _soften_prediction_text(value) for key, value in probe.expected_updates.items()}
    probe = probe.model_copy(update={
        "question": _soften_prediction_text(probe.question),
        "purpose": _soften_prediction_text(probe.purpose),
        "options": [_soften_prediction_text(item) for item in probe.options],
        "expected_updates": probe_updates,
    })
    hypothesis_refs = [item.hypothesis_id for item in pattern.hypotheses]
    probe_refs = _unique([*probe.distinguishes_hypothesis_refs, *hypothesis_refs])[:2]
    if len(probe_refs) < 2 or len(probe.options) < 2:
        probe_refs = _unique([selected_ref, *hypothesis_refs])[:2]
        options = probe.options[:2] if len(probe.options) >= 2 else [
            "先形成自己的方案，在行动中根据反馈调整",
            "先弄清规则和边界，条件明确后再行动",
        ]
        probe = DiscriminatingProbe(
            probe_id=probe.probe_id or "probe-local-safe",
            question="面对一项既需要独立判断、又有明确规则约束的任务时，你通常更接近哪种做法？",
            purpose="用现实中的处理方式区分当前保留的两个命局解释。",
            distinguishes_hypothesis_refs=probe_refs,
            options=options,
            expected_updates={
                options[0]: f"增强 {probe_refs[0]}" if probe_refs else "增强主动处理解释",
                options[1]: f"增强 {probe_refs[1]}" if len(probe_refs) > 1 else "增强环境约束解释",
            },
        )
    else:
        probe = probe.model_copy(update={"distinguishes_hypothesis_refs": probe_refs})

    return predictions.model_copy(update={
        "prior_predictions": safe_predictions,
        "next_probe": probe,
    })


def _probe_needs_local_fallback(*, probe: DiscriminatingProbe, world: ChartWorldInstance) -> bool:
    del world
    return len(probe.options) < 2 or len(probe.distinguishes_hypothesis_refs) < 2


def _sanitize_pattern_alternatives(pattern: PatternHypothesisDraft, *, world: ChartWorldInstance) -> PatternHypothesisDraft:
    hypotheses: list[CognitiveHypothesis] = []
    for hypothesis in pattern.hypotheses:
        name = hypothesis.name
        if hypothesis.hypothesis_id == pattern.selected_hypothesis_id and "从" in name and ("制杀" in name or "食伤" in name):
            base_name = re.split(r"[（(]", name, maxsplit=1)[0].strip()
            if base_name and "从" not in base_name and ("制杀" in base_name or "食伤" in base_name):
                name = base_name
        cleaned = hypothesis.model_copy(update={
            "name": name,
            "success_conditions": [item for item in hypothesis.success_conditions if not _semantic_text_errors(text=item, world=world)],
            "failure_conditions": [item for item in hypothesis.failure_conditions if not _semantic_text_errors(text=item, world=world)],
        })
        core_text = f"{cleaned.name} {cleaned.thesis} {cleaned.rejection_reason}"
        if cleaned.hypothesis_id != pattern.selected_hypothesis_id and _semantic_text_errors(text=core_text, world=world):
            continue
        hypotheses.append(cleaned)

    selected = next((item for item in hypotheses if item.hypothesis_id == pattern.selected_hypothesis_id), None)
    safe_selected_thesis = selected.thesis if selected and not _semantic_text_errors(text=selected.thesis, world=world) else ""
    first_look = pattern.first_look
    if _semantic_text_errors(text=first_look, world=world) and safe_selected_thesis:
        first_look = safe_selected_thesis
    whole_chart_thesis = pattern.whole_chart_thesis
    if _semantic_text_errors(text=whole_chart_thesis, world=world) and safe_selected_thesis:
        whole_chart_thesis = safe_selected_thesis
    salient = [
        item
        for item in pattern.salient_phenomena
        if not _semantic_text_errors(text=f"{item.observation} {item.why_it_matters}", world=world)
    ]
    return pattern.model_copy(update={
        "first_look": first_look,
        "whole_chart_thesis": whole_chart_thesis,
        "salient_phenomena": salient,
        "hypotheses": hypotheses,
    })


def _repair_pattern_locally(pattern: PatternHypothesisDraft, *, world: ChartWorldInstance) -> PatternHypothesisDraft:
    safe: list[CognitiveHypothesis] = []
    seen_ids: set[str] = set()
    seen_signatures: set[str] = set()
    for hypothesis in sorted(pattern.hypotheses, key=lambda item: item.rank):
        core_text = f"{hypothesis.name} {hypothesis.thesis} {hypothesis.rejection_reason}"
        signature = _hypothesis_signature(hypothesis)
        fact_conflicts = [
            item
            for item in deterministic_fact_conflicts(text=core_text, world=world)
            if not item.startswith("地支关系未建模:")
        ]
        if (
            fact_conflicts
            or hypothesis.hypothesis_id in seen_ids
            or signature in seen_signatures
        ):
            continue
        seen_ids.add(hypothesis.hypothesis_id)
        seen_signatures.add(signature)
        safe.append(hypothesis)

    if not safe:
        return pattern
    selected_id = pattern.selected_hypothesis_id
    if selected_id not in {item.hypothesis_id for item in safe}:
        selected_id = safe[0].hypothesis_id
    normalized = [
        item.model_copy(update={
            "rank": index,
            "status": "primary" if item.hypothesis_id == selected_id else "alternative",
        })
        for index, item in enumerate(safe, start=1)
    ]
    selected = next(item for item in normalized if item.hypothesis_id == selected_id)
    first_look = pattern.first_look
    if any(not item.startswith("地支关系未建模:") for item in deterministic_fact_conflicts(text=first_look, world=world)):
        first_look = selected.thesis
    whole_chart_thesis = pattern.whole_chart_thesis
    if any(not item.startswith("地支关系未建模:") for item in deterministic_fact_conflicts(text=whole_chart_thesis, world=world)):
        whole_chart_thesis = selected.thesis
    return pattern.model_copy(update={
        "first_look": first_look,
        "whole_chart_thesis": whole_chart_thesis,
        "hypotheses": normalized,
        "selected_hypothesis_id": selected_id,
    })


def _normalize_dual_probe_refs(
    dual_lens: DualLensCognitionDraft,
    *,
    pattern: PatternHypothesisDraft,
) -> DualLensCognitionDraft:
    probe = dual_lens.cross_lens_probe
    if len(probe.distinguishes_hypothesis_refs) >= 2:
        return dual_lens
    refs = _unique([*probe.distinguishes_hypothesis_refs, pattern.selected_hypothesis_id, "ziwei:current_stage"])
    return dual_lens.model_copy(update={
        "cross_lens_probe": probe.model_copy(update={"distinguishes_hypothesis_refs": refs}),
    })


def _reasoning_world_payload(world: ChartWorldInstance) -> dict[str, Any]:
    return MingliContextCompiler().compile(world=world, stage="pattern").payload


def _element_role_ledger(ledger: dict[str, Any]) -> dict[str, str]:
    day_master = ledger.get("day_master") or {}
    day_element = str(day_master.get("day_element") or day_master.get("element") or "")
    if not day_element:
        return {}
    generates = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
    controls = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}
    generated_by = next((source for source, target in generates.items() if target == day_element), "")
    controlled_by = next((source for source, target in controls.items() if target == day_element), "")
    return {
        day_element: "比劫/同类",
        generates.get(day_element, ""): "食伤/输出",
        controls.get(day_element, ""): "财星/资源结果",
        controlled_by: "官杀/规则压力",
        generated_by: "印星/支持输入",
    }


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output


def _assemble_whole_chart(
    *,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    predictions: PredictionProbeDraft,
    dual_lens: DualLensCognitionDraft | None,
) -> WholeChartCognitionDraft:
    pattern_payload = pattern.model_dump(mode="json")
    pattern_payload.pop("evidence_refs", None)
    return WholeChartCognitionDraft(
        **pattern_payload,
        work_path=work.work_path,
        useful_god_reasoning=work.useful_god_reasoning,
        portrait=work.portrait,
        prior_predictions=predictions.prior_predictions,
        next_probe=predictions.next_probe,
        dual_lens=dual_lens,
        unresolved_questions=work.unresolved_questions,
        evidence_refs=_unique([
            *pattern.evidence_refs,
            *work.evidence_refs,
            *(dual_lens.evidence_refs if dual_lens else []),
        ]),
    )


def _pattern_stage_errors(
    *,
    pattern: PatternHypothesisDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack | None = None,
) -> list[str]:
    return _unique([
        *_pattern_hard_errors(pattern=pattern, world=world, context=context),
        *_pattern_soft_issues(pattern=pattern, world=world, context=context),
    ])


def _pattern_preview_errors(
    *,
    preview: PatternPreviewDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack,
) -> list[str]:
    errors = _semantic_text_errors(text=preview.preview_line, world=world)
    if not preview.preview_line.strip():
        errors.append("第一眼预览为空")
    if not preview.focus_refs:
        errors.append("第一眼预览缺少事实引用")
    allowed = set(context.fact_refs)
    missing = [ref for ref in preview.focus_refs if ref not in allowed]
    if missing:
        errors.append(f"第一眼预览引用不存在:{','.join(missing)}")
    return _unique(errors)


def _pattern_hard_errors(
    *,
    pattern: PatternHypothesisDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack | None = None,
) -> list[str]:
    errors: list[str] = []
    selected = next((item for item in pattern.hypotheses if item.hypothesis_id == pattern.selected_hypothesis_id), None)
    if selected is None:
        errors.append("selected_hypothesis_id 不存在")
    elif "从" in selected.name and ("制杀" in selected.name or "食伤" in selected.name):
        errors.append("从格与主动食伤做功不能混入同一主假设")
    text = json.dumps(pattern.model_dump(mode="json"), ensure_ascii=False)
    errors.extend(_semantic_text_errors(text=text, world=world, include_deterministic=False))
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(pattern.model_dump(mode="json")), world=world))
    comparison = _review_hypothesis_space(
        pattern=pattern,
        context=context or MingliContextCompiler().compile(world=world, stage="pattern"),
    )
    hard_prefixes = (
        "竞争假设 id 重复",
        "竞争假设 rank 重复",
        "竞争假设必须且只能有一个 primary",
        "selected_hypothesis_id 必须指向唯一 primary",
    )
    errors.extend(issue for issue in comparison.issues if issue.startswith(hard_prefixes))
    return _unique(errors)


def _pattern_soft_issues(
    *,
    pattern: PatternHypothesisDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack | None = None,
) -> list[str]:
    issues: list[str] = []
    if not 2 <= len(pattern.hypotheses) <= 3:
        issues.append("竞争假设必须为2到3个")
    if len(pattern.salient_phenomena) > 3:
        issues.append("盘面重心最多3个")
    for hypothesis in pattern.hypotheses:
        if not hypothesis.failure_conditions:
            issues.append(f"假设缺少失败条件:{hypothesis.hypothesis_id}")
        if hypothesis.status == "alternative" and not hypothesis.rejection_reason:
            issues.append(f"替代假设缺少放弃理由:{hypothesis.hypothesis_id}")
    comparison = _review_hypothesis_space(
        pattern=pattern,
        context=context or MingliContextCompiler().compile(world=world, stage="pattern"),
    )
    hard_prefixes = (
        "竞争假设 id 重复",
        "竞争假设 rank 重复",
        "竞争假设必须且只能有一个 primary",
        "selected_hypothesis_id 必须指向唯一 primary",
    )
    issues.extend(issue for issue in comparison.issues if not issue.startswith(hard_prefixes))
    return _unique(issues)


def _normalize_pattern_bookkeeping(pattern: PatternHypothesisDraft) -> PatternHypothesisDraft:
    salient = list(pattern.salient_phenomena[:3])
    refs = _unique([
        *pattern.evidence_refs,
        *(ref for item in salient for ref in item.evidence_refs),
        *(ref for item in pattern.hypotheses for ref in item.supporting_evidence_refs),
        *(ref for item in pattern.hypotheses for ref in item.counter_evidence_refs),
    ])
    return pattern.model_copy(update={"salient_phenomena": salient, "evidence_refs": refs})


def _review_hypothesis_space(
    *,
    pattern: PatternHypothesisDraft,
    context: ReasoningContextPack,
) -> HypothesisComparisonReceipt:
    issues: list[str] = []
    ids = [item.hypothesis_id for item in pattern.hypotheses]
    ranks = [item.rank for item in pattern.hypotheses]
    primary_ids = [item.hypothesis_id for item in pattern.hypotheses if item.status == "primary"]
    alternative_ids = [item.hypothesis_id for item in pattern.hypotheses if item.status in {"alternative", "unresolved"}]
    signatures = [_hypothesis_signature(item) for item in pattern.hypotheses]
    if len(ids) != len(set(ids)):
        issues.append("竞争假设 id 重复")
    if len(ranks) != len(set(ranks)):
        issues.append("竞争假设 rank 重复")
    if len(primary_ids) != 1:
        issues.append("竞争假设必须且只能有一个 primary")
    if primary_ids and pattern.selected_hypothesis_id != primary_ids[0]:
        issues.append("selected_hypothesis_id 必须指向唯一 primary")
    if len(signatures) != len(set(signatures)):
        issues.append("竞争假设因果签名重复")
    for hypothesis in pattern.hypotheses:
        if not hypothesis.supporting_evidence_refs:
            issues.append(f"假设缺少支持证据:{hypothesis.hypothesis_id}")

    salient_refs = _unique([
        ref
        for phenomenon in pattern.salient_phenomena
        for ref in phenomenon.evidence_refs
    ])
    explained_refs = set(
        ref
        for hypothesis in pattern.hypotheses
        for ref in [*hypothesis.supporting_evidence_refs, *hypothesis.counter_evidence_refs]
    )
    uncovered = [ref for ref in salient_refs if ref not in explained_refs]
    if uncovered:
        issues.append(f"盘面重心证据未进入假设比较:{','.join(uncovered)}")

    high_attention_refs = {
        item.fact_ref
        for item in context.attention_receipt.items
        if item.selected and item.priority in {"critical", "high"}
    }
    cited_refs = {
        *pattern.evidence_refs,
        *salient_refs,
        *explained_refs,
    }
    attention_used = sorted(high_attention_refs & cited_refs)
    if high_attention_refs and not attention_used:
        issues.append("假设空间未引用任何 critical/high 注意力事实")

    coverage = 1.0 if not salient_refs else round((len(salient_refs) - len(uncovered)) / len(salient_refs), 4)
    return HypothesisComparisonReceipt(
        passed=not issues,
        selected_hypothesis_id=pattern.selected_hypothesis_id,
        primary_hypothesis_ids=primary_ids,
        alternative_hypothesis_ids=alternative_ids,
        distinct_signature_count=len(set(signatures)),
        salient_evidence_coverage_rate=coverage,
        uncovered_salient_refs=uncovered,
        attention_evidence_used=attention_used,
        issues=_unique(issues),
    )


def _hypothesis_signature(hypothesis: CognitiveHypothesis) -> str:
    text = f"{hypothesis.name} {hypothesis.thesis}".lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", text)


def _work_stage_errors(*, work: WorkPathPortraitDraft, world: ChartWorldInstance) -> list[str]:
    payload = work.model_dump(mode="json")
    errors = _semantic_text_errors(text=json.dumps(payload, ensure_ascii=False), world=world, include_deterministic=False)
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(payload), world=world))
    return _unique(errors)


def _prediction_stage_errors(*, predictions: PredictionProbeDraft, world: ChartWorldInstance) -> list[str]:
    errors: list[str] = []
    if not predictions.prior_predictions:
        errors.append("本轮没有保留可安全展示的先验判断")
    text = json.dumps(predictions.model_dump(mode="json"), ensure_ascii=False)
    errors.extend(_semantic_text_errors(text=text, world=world, include_deterministic=False))
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(predictions.model_dump(mode="json")), world=world))
    if len(predictions.next_probe.distinguishes_hypothesis_refs) < 2:
        errors.append("Probe 尚未区分两个假设")
    return _unique(errors)


def _dual_lens_errors(*, dual_lens: DualLensCognitionDraft, world: ChartWorldInstance) -> list[str]:
    errors: list[str] = []
    if not 2 <= len(dual_lens.palace_observations) <= 4:
        errors.append("紫微第一眼必须保留2到4个关键宫位观察")
    covered_domains = {item.domain for item in dual_lens.palace_observations}
    if len(covered_domains & {"identity", "career", "wealth"}) < 2:
        errors.append("紫微观察至少覆盖身份、事业、财富中的两个领域")
    if not dual_lens.agreements:
        errors.append("双镜头必须列出至少一个一致处")
    probe = dual_lens.cross_lens_probe
    if len(probe.distinguishes_hypothesis_refs) < 2:
        errors.append("双镜头 Probe 必须区分至少两个解释")
    if len(probe.options) < 2:
        errors.append("双镜头 Probe 至少需要两个可区分选项")
    probe_text = f"{probe.question} {probe.purpose}"
    if any(token in probe_text for token in ("星曜", "宫位", "命宫", "四化", "大限")):
        errors.append("双镜头 Probe 必须询问现实行为，不能要求用户理解紫微术语")
    dual_payload = dual_lens.model_dump(mode="json")
    text = json.dumps(dual_payload, ensure_ascii=False)
    for phrase in ("必然", "一定会", "注定"):
        for match in re.finditer(phrase, text):
            prefix = text[max(0, match.start() - 10):match.start()]
            if any(token in prefix for token in ("不", "非", "不能", "并不", "不代表", "避免", "不得")):
                continue
            errors.append("紫微时序不得写成确定事件")
            break
    allowed = set(world.allowed_evidence_refs)
    ziwei_allowed = {
        ref
        for fact in world.facts
        if fact.category.startswith("ziwei_")
        for ref in [fact.fact_id, *fact.source_refs]
    }
    cited = {
        ref
        for item in dual_lens.palace_observations
        for ref in item.evidence_refs
    }
    cited.update(dual_lens.evidence_refs)
    if not any(ref in ziwei_allowed and _citation_allowed(ref=ref, allowed=allowed) for ref in cited):
        errors.append("紫微观察缺少可追溯的紫微事实引用")
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(dual_payload), world=world))
    return _unique(errors)


def _whole_stage_errors(*, whole: WholeChartCognitionDraft, world: ChartWorldInstance) -> list[str]:
    errors: list[str] = []
    structural_payload = whole.model_dump(mode="json")
    predictions_payload = {
        "prior_predictions": structural_payload.pop("prior_predictions", []),
        "next_probe": structural_payload.pop("next_probe", {}),
    }
    structural_text = json.dumps(structural_payload, ensure_ascii=False)
    prediction_text = json.dumps(predictions_payload, ensure_ascii=False)
    if len(whole.hypotheses) < 2:
        errors.append("结构:至少比较两个命局假设")
    if whole.selected_hypothesis_id not in {item.hypothesis_id for item in whole.hypotheses}:
        errors.append("结构:selected_hypothesis_id 不存在")
    if not whole.prior_predictions:
        errors.append("先验:本轮没有保留可安全展示的先验判断")
    selected = next((item for item in whole.hypotheses if item.hypothesis_id == whole.selected_hypothesis_id), None)
    if selected and "从" in selected.name and ("制杀" in selected.name or "食伤" in selected.name):
        errors.append("结构:主假设混合互斥解释:从格与主动食伤做功必须分开比较")
    probe_text = f"{whole.next_probe.question} {whole.next_probe.purpose}"
    if re.search(r"20\d{2}", probe_text) or any(token in probe_text for token in ("年份", "大运", "计划受阻", "决策失误", "健康", "外部因素")):
        errors.append("Probe 失焦:必须用可观察行为区分假设而非追问灾难或年份")
    errors.extend(f"结构:{item}" for item in _semantic_text_errors(text=structural_text, world=world, include_deterministic=False))
    errors.extend(f"先验:{item}" for item in _semantic_text_errors(text=prediction_text, world=world, include_deterministic=False))
    errors.extend(f"事实:{item}" for item in deterministic_fact_conflicts(text=assertive_claim_text(whole.model_dump(mode="json")), world=world))
    return _unique(errors)


def _semantic_text_errors(*, text: str, world: ChartWorldInstance, include_deterministic: bool = True) -> list[str]:
    errors: list[str] = list(deterministic_fact_conflicts(text=text, world=world)) if include_deterministic else []
    invalid_relations = (
        "木生土", "木生金", "木生水",
        "火生金", "火生水", "火生木",
        "土生木", "土生水", "土生火",
        "金生木", "金生火", "金生土",
        "水生土", "水生火", "水生金",
        "木克金", "木克水", "木克火",
        "火克木", "火克水", "火克土",
        "土克木", "土克火", "土克金",
        "金克火", "金克土", "金克水",
        "水克木", "水克金", "水克土",
    )
    for invalid in invalid_relations:
        if _contains_asserted_relation(text=text, relation=invalid):
            errors.append(f"错误五行关系:{invalid}")
    if "火化土" in text:
        errors.append("错误五行表述:火与土必须写生而不是化")
    if re.search(r"(?:食神|食伤)制杀\s*[/／]\s*化印", text):
        errors.append("机制拼接冲突:制杀与化印不能用斜线合并为同一做功")
    if re.search(r"(?:食神|食伤)生财(?:而|并|再)?化杀", text):
        errors.append("因果链压缩:食伤生财与财生杀必须逐段表达")
    for match in re.finditer(r"(?:丁火|丙火|火气|火)[^。；]{0,36}(?:(?:转化为|变成)\s*(?:酉金|金局|金气|金)|导向[^。；]{0,12}(?:酉金|金局|金气|金))", text):
        segment = match.group(0)
        if not any(token in segment for token in ("制", "克", "约束", "作用于")):
            errors.append(f"五行转化偷换:{segment[:48]}")
    for pattern in (
        r"(?:丁火|丙火)[^。；]{0,48}(?:引动|生出|化成)[^。；]{0,12}(?:酉金|金局|金气)",
        r"(?:丁火|丙火)[^。；]{0,10}(?:转化为|变成)\s*(?:食伤|食神|伤官)",
        r"(?:火气|火势|火)\s*(?:欲去生|生)\s*(?:水/金|水|金)",
    ):
        for match in re.finditer(pattern, text):
            segment = match.group(0)
            prefix = text[max(0, match.start() - 10):match.start()]
            if any(token in prefix for token in ("不", "不能", "并非", "不得", "避免", "误写")):
                continue
            if is_parallel_predicate_fragment(text=text, start=match.start(), end=match.end()):
                continue
            errors.append(f"五行转化偷换:{segment[:48]}")

    forbidden_events = (
        "失业", "疾病", "肝胆", "筋骨疼痛", "健康受损", "健康危机",
        "必然破财", "资金链断裂", "重大挫折", "重大变故", "招灾", "死亡",
    )
    for forbidden in forbidden_events:
        if forbidden in text:
            errors.append(f"越界先验:{forbidden}")
    overconfident_phrases = ("必然", "绝对阈值", "吉凶判定", "瞬间转为凶险", "立即崩塌", "结构性崩塌", "彻底改变")
    for phrase in overconfident_phrases:
        for match in re.finditer(phrase, text):
            prefix = text[max(0, match.start() - 12):match.start()]
            if any(token in prefix for token in ("不", "非", "不能", "并不", "不代表", "避免", "不得", "不等于")):
                continue
            excerpt = text[max(0, match.start() - 36):match.end() + 36]
            errors.append(f"过度确定断言:{phrase}:{excerpt}")
            break

    internal_match = re.search(r"V(?:20|30|40|50|60)|admin_profile|fixture|runtime|schema", text, flags=re.IGNORECASE)
    if internal_match:
        errors.append(f"内部工程信息泄漏:{internal_match.group(0)}")

    if re.search(r"20\d{2}\s*(?:-|—|–|至|到)\s*20\d{2}", text):
        errors.append("Timing 越权:擅自扩写连续年份区间")
    if re.search(r"(?:水|壬|癸|亥|子)[^。；]{0,28}伤官见官|伤官见官[^。；]{0,28}(?:水|壬|癸|亥|子)", text):
        errors.append("十神因果冲突:水不能被机械写成伤官见官")

    ledger = _reasoning_world_payload(world)["immutable_chart_ledger"]
    day_master = str((ledger.get("day_master") or {}).get("stem") or "")
    if day_master and f"{day_master}（比劫）" in text:
        errors.append(f"十神精度不足:{day_master}必须按账本写具体比肩/劫财")

    visible = (ledger.get("visible") or {}).get("visible_ten_gods", [])
    labels = {
        "bi_jian": "比肩", "jie_cai": "劫财", "shi_shen": "食神", "shang_guan": "伤官",
        "pian_cai": "偏财", "zheng_cai": "正财", "qi_sha": "七杀", "zheng_guan": "正官",
        "pian_yin": "偏印", "zheng_yin": "正印",
    }
    all_labels = set(labels.values())
    visible_bi_jian_count = sum(str(row.get("ten_god") or "") == "bi_jian" for row in visible)
    chinese_counts = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4}
    for chinese, count in chinese_counts.items():
        if re.search(rf"(?:透出|可见|天干[^。；]{{0,8}}|全局[^。；]{{0,8}}){chinese}(?:见|个)?比肩", text) and count != visible_bi_jian_count:
            errors.append(f"比肩数量冲突:账本可见比肩为{visible_bi_jian_count}不是{count}")

    month_branch = world.pillars[1][1] if len(world.pillars) > 1 and len(world.pillars[1]) >= 2 else ""
    for match in re.finditer(r"([子丑寅卯辰巳午未申酉戌亥])(?:木|火|土|金|水)?[^。；，]{0,8}当令", text):
        branch = match.group(1)
        if month_branch and branch != month_branch:
            errors.append(f"月令位置冲突:{branch}不在月支，不能写作当令")
    for row in visible:
        stem = str(row.get("stem") or "")
        correct = labels.get(str(row.get("ten_god") or ""), "")
        for wrong in all_labels - {correct}:
            if stem and (f"{stem}火{wrong}" in text or f"{stem}{wrong}" in text):
                errors.append(f"十神账本冲突:{stem}应为{correct}不是{wrong}")
                break

    role_ledger = _reasoning_world_payload(world)["element_role_ledger"]
    cn = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    for element, role in role_ledger.items():
        symbol = cn.get(element, "")
        if not symbol:
            continue
        role_name = role.split("/")[0]
        for wrong in {"财星", "官杀", "印星", "食伤", "比劫"} - {role_name}:
            if (
                f"{symbol}为{wrong}" in text
                or f"{symbol}是{wrong}" in text
                or re.search(rf"{re.escape(symbol)}(?:属性|气|局|势|的)?{re.escape(wrong)}", text)
                or f"{wrong}（{symbol}）" in text
                or f"{wrong}({symbol})" in text
                or _contains_role_conflict(text=text, symbol=symbol, wrong=wrong)
            ):
                errors.append(f"元素十神冲突:{symbol}应属{role}不是{wrong}")
        if role_name != "官杀" and re.search(rf"{re.escape(symbol)}[^。；]{{0,8}}(?:直克|克制|压制|攻克)(?:日主|命主)", text):
            errors.append(f"五行作用方向冲突:{symbol}不是克制日主的官杀元素")
    return _unique(errors)


def _contains_asserted_relation(*, text: str, relation: str) -> bool:
    for match in re.finditer(re.escape(relation), text):
        prefix = text[max(0, match.start() - 10):match.start()]
        if any(token in prefix for token in ("不是", "并非", "非", "不能", "禁止", "不得", "避免", "误写为")):
            continue
        if is_parallel_predicate_fragment(text=text, start=match.start(), end=match.end()):
            continue
        return True
    return False


def _contains_role_conflict(*, text: str, symbol: str, wrong: str) -> bool:
    patterns = (
        rf"{re.escape(symbol)}[^。；]{{0,10}}(?:为|是|作为|属于|或){re.escape(wrong)}",
        rf"{re.escape(wrong)}[^。；]{{0,8}}(?:为|是|作为|属于){re.escape(symbol)}",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            segment = match.group(0)
            if any(token in segment for token in ("不是", "并非", "非财", "非官", "非印", "非食", "非比")):
                continue
            return True
    return False
