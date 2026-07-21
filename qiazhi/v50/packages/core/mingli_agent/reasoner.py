from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from core.life_domains import LifeDomain, domain_reasoning_protocol
from core.mingli_agent.context import ContextStage, MingliContextCompiler, ReasoningContextPack
from core.mingli_agent.contracts import (
    BirthIntakeDraft,
    CaseTurnDraft,
    ChartWorldInstance,
    DomainCausalReading,
    DomainExploration,
    DualLensCognitionDraft,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    PatternHypothesisDraft,
    PatternPreviewDraft,
    PredictionProbeDraft,
    WholeChartCognitionDraft,
    WorkPathPortraitDraft,
)
from core.mingli_agent.fact_review import (
    assertive_claim_text,
    deterministic_fact_conflicts,
    repair_locked_fact_assertions,
)
from core.mingli_agent.model_client import (
    CognitiveModel,
    OllamaCognitiveModel,
    _ollama_metrics,
    default_domain_model,
    default_pattern_model,
    default_reasoning_model,
    default_work_model,
)
from core.mingli_agent.model_policy import CognitiveTask, ModelPolicyRouter
from core.mingli_agent.orchestrator import CognitiveOrchestrator
from core.mingli_agent.reasoning_normalization import (
    _all_citations,
    _apply_scope_boundary,
    _assemble_whole_chart,
    _baseline_cognitive_reference_ids,
    _domain_context_payload,
    _domain_evidence_refs,
    _domain_reading_citations,
    _extract_completed_json_string,
    _extract_first_completed_json_array_string,
    _filter_evidence_refs,
    _normalize_baseline_cognition,
    _normalize_domain_reading,
    _normalize_dual_probe_refs,
    _normalize_pattern_bookkeeping,
    _normalize_prediction_probe,
    _normalize_work_strategy_dimensions,
    _preview_is_fact_safe,
    _probe_needs_local_fallback,
    _repair_pattern_locally,
    _sanitize_pattern_alternatives,
    _sanitize_preview_line,
    _sanitize_work_questions,
    _soften_prediction_text,
    _whole_chart_from_record,
    sanitize_public_mingli_payload,
)
from core.mingli_agent.reasoning_prompts import (
    _baseline_cognition_prompt,
    _case_turn_prompt,
    _extended_domain_reasoning_prompt,
    _pattern_hypothesis_prompt,
    _pattern_preview_prompt,
    _pattern_repair_prompt,
    _prediction_repair_prompt,
    _prediction_stage_prompt,
    _prediction_stage_repair_prompt,
    _probe_repair_prompt,
    _single_baseline_repair_prompt,
    _single_domain_reasoning_prompt,
    _single_domain_repair_prompt,
    _structural_repair_prompt,
    _whole_chart_prompt,
    _work_path_prompt,
    _work_repair_prompt,
    _ziwei_integration_prompt,
    _ziwei_integration_repair_prompt,
    _ziwei_probe_repair_prompt,
)
from core.mingli_agent.reasoning_review import (
    _classify_review_issue,
    _cognition_has_unresolved_competition,
    _finalize_review,
    _forbidden_domain_tokens,
    _review_requires_one_repair,
    review_cognition,
    review_domain_reading,
)
from core.mingli_agent.reasoning_utils import _hypothesis_signature, _unique
from core.mingli_agent.reasoning_validation import (
    _citation_allowed,
    _contains_asserted_relation,
    _contains_role_conflict,
    _dual_lens_errors,
    _pattern_hard_errors,
    _pattern_preview_errors,
    _pattern_soft_issues,
    _pattern_stage_errors,
    _prediction_stage_errors,
    _review_hypothesis_space,
    _semantic_text_errors,
    _whole_stage_errors,
    _work_stage_errors,
)
from core.mingli_agent.reliability import (
    cognition_semantic_signature,
    domain_baseline_override_reason,
    domain_request_fingerprint,
)


T = TypeVar("T", bound=BaseModel)
StageCallback = Callable[[str, dict[str, Any]], None]


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


def _notify_stage(callback: StageCallback | None, event_type: str, payload: dict[str, Any]) -> None:
    if callback is None:
        return
    try:
        callback(event_type, payload)
    except Exception:  # noqa: BLE001 - delivery failure must not alter cognition.
        return
