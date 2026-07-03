from __future__ import annotations

from collections import defaultdict
from typing import Any

from v30.brain.contracts import (
    DecisionCandidate,
    DecisionConflict,
    DecisionEngineResult,
    DecisionInputBundle,
    DecisionVerdict,
)
from v30.brain.conflict_resolver import (
    DECISION_CONFLICT_RESOLVER_VERSION,
    resolve_decision_conflicts,
)
from v30.production.candidate_builder import (
    SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION,
    build_signal_candidate_support,
)


DECISION_ENGINE_VERSION = "v30.decision_engine.v1"


def build_decision_result(
    *,
    reading_id: str,
    active_stage_id: str,
    diagnosis: dict[str, object],
    claim_scores: list[dict[str, object]],
    central_feedback_overlay: dict[str, object] | None = None,
    signal_registry: dict[str, object] | None = None,
    candidate_builder_mode: str = "compatibility",
) -> dict[str, object]:
    claims = _claims_by_id(diagnosis)
    candidate_signal_support = build_signal_candidate_support(
        claim_scores=claim_scores,
        claims=claims,
        signal_registry=signal_registry or {},
        mode=candidate_builder_mode,
    )
    candidates = _decision_candidates(
        claim_scores,
        claims,
        signal_support_by_claim=_dict(candidate_signal_support.get("support_by_claim_id")),
        candidate_builder_mode=candidate_builder_mode,
    )
    conflict_resolution = resolve_decision_conflicts(candidates)
    conflicts = [
        DecisionConflict.model_validate(row)
        for row in _list(conflict_resolution.get("conflicts"))
        if isinstance(row, dict)
    ]
    conflict_audit_by_domain = _conflict_audit_by_domain(conflict_resolution.get("audit"))
    verdicts = _decision_verdicts(
        candidates,
        conflicts,
        conflict_audit_by_domain=conflict_audit_by_domain,
    )
    feedback_recalculation_summary = _feedback_recalculation_summary(
        candidates,
        verdicts,
        central_feedback_overlay or {},
    )
    bundle = DecisionInputBundle(
        bundle_id=f"{reading_id}:{active_stage_id or 'reading'}:decision-input",
        reading_id=reading_id,
        active_stage_id=active_stage_id,
        candidates=candidates,
        conflicts=conflicts,
        feedback_overlay=central_feedback_overlay or {},
        practitioner_selection_count=int(_float((central_feedback_overlay or {}).get("practitioner_selection_count"), 0.0)),
    )
    result = DecisionEngineResult(
        engine_version=DECISION_ENGINE_VERSION,
        reading_id=reading_id,
        active_stage_id=active_stage_id,
        decision_input_bundle=bundle,
        verdicts=verdicts,
        candidate_builder_summary=_candidate_builder_public_summary(candidate_signal_support),
        conflict_resolver_summary=_dict(conflict_resolution.get("summary")),
        conflict_resolver_audit=[
            row for row in _list(conflict_resolution.get("audit")) if isinstance(row, dict)
        ],
        feedback_recalculation_summary=feedback_recalculation_summary,
        blocked_verdict_count=sum(1 for verdict in verdicts if verdict.assertion_level == "blocked"),
        llm_expression_contract={
            "version": "v30.decision_llm_expression_contract.v1",
            "llm_can_rewrite_expression_only": True,
            "llm_can_create_chart_facts": False,
            "llm_can_override_verdict": False,
            "must_stay_within_allowed_assertions": True,
            "must_respect_forbidden_assertions": True,
            "boundary": "llm_consumes_decision_verdicts_for_expression_not_final_authority",
        },
        training_signal={
            "version": "v30.training_signal.decision_engine.v1",
            "trainable": True,
            "targets": [
                "decision_candidate_weight",
                "decision_assertion_level_threshold",
                "decision_conflict_resolution_policy",
                "decision_conflict_resolver_explanation_quality",
                "decision_next_question_slot_policy",
                "decision_feedback_recalculation_quality",
                "llm_expression_boundary_verifier",
                "signal_to_candidate_binding_quality",
            ],
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "raw_rule_match",
                "llm_fact_injection",
            ],
            "conflict_resolver_version": DECISION_CONFLICT_RESOLVER_VERSION,
        },
    )
    return result.model_dump(mode="json")


def _feedback_recalculation_summary(
    candidates: list[DecisionCandidate],
    verdicts: list[DecisionVerdict],
    overlay: dict[str, object],
) -> dict[str, object]:
    domain_deltas = _dict(overlay.get("domain_deltas"))
    claim_deltas = _dict(overlay.get("claim_deltas"))
    topic_deltas = _dict(overlay.get("topic_deltas"))
    score_adjustments = []
    for candidate in candidates:
        delta = _float(candidate.score_components.get("central_feedback_overlay"), 0.0)
        if not delta and candidate.domain not in domain_deltas and candidate.claim_id not in claim_deltas:
            continue
        score_adjustments.append(
            {
                "candidate_id": candidate.candidate_id,
                "claim_id": candidate.claim_id,
                "domain": candidate.domain,
                "score_delta": round(delta, 3),
                "confidence_after_feedback": candidate.confidence,
            }
        )
    affected_candidate_ids = [str(row["candidate_id"]) for row in score_adjustments[:12]]
    affected_claim_ids = _sorted_unique(str(row["claim_id"]) for row in score_adjustments if row.get("claim_id"))
    affected_domains = _sorted_unique(
        [
            *[str(row.get("domain") or "") for row in score_adjustments],
            *[str(key) for key, value in domain_deltas.items() if _float(value, 0.0)],
            *[str(key) for key, value in topic_deltas.items() if _float(value, 0.0)],
        ]
    )
    affected_verdict_ids = [
        verdict.verdict_id
        for verdict in verdicts
        if verdict.domain in affected_domains
        or verdict.primary_branch_id in affected_candidate_ids
    ][:12]
    return {
        "version": "v30.decision_feedback_recalculation_summary.v1",
        "feedback_applied": int(_float(overlay.get("effect_count"), 0.0)) > 0,
        "effect_count": int(_float(overlay.get("effect_count"), 0.0)),
        "question_outcome_count": int(_float(overlay.get("question_outcome_count"), 0.0)),
        "practitioner_selection_count": int(_float(overlay.get("practitioner_selection_count"), 0.0)),
        "domain_deltas": domain_deltas,
        "claim_deltas": claim_deltas,
        "topic_deltas": topic_deltas,
        "requires_question_topics": [str(row) for row in _list(overlay.get("requires_question_topics"))[:8]],
        "score_adjustments": score_adjustments[:12],
        "affected_candidate_ids": affected_candidate_ids,
        "affected_claim_ids": affected_claim_ids[:12],
        "affected_domains": affected_domains[:12],
        "affected_verdict_ids": affected_verdict_ids,
        "admin_training_projection": {
            "version": "v30.decision_feedback_admin_training_projection.v1",
            "trainable": True,
            "targets": [
                "feedback_to_decision_candidate_weight",
                "practitioner_selection_to_verdict_branch_weight",
                "question_outcome_to_verdict_recalculation",
                "decision_feedback_quality_diff",
            ],
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "raw_rule_truth",
            ],
            "boundary": "admin_training_projection_tracks_feedback_effects_without_promoting_policy_or_mutating_chart_facts",
        },
        "chart_fact_mutation_allowed": False,
        "recompute_policy": "feedback_changes_candidate_weight_then_decision_engine_rebuilds_verdicts",
        "boundary": "decision_feedback_recalculation_summary_is_weight_trace_not_chart_fact",
    }


def _decision_candidates(
    claim_scores: list[dict[str, object]],
    claims: dict[str, dict[str, object]],
    *,
    signal_support_by_claim: dict[str, object] | None = None,
    candidate_builder_mode: str = "compatibility",
) -> list[DecisionCandidate]:
    candidates: list[DecisionCandidate] = []
    signal_support_by_claim = signal_support_by_claim or {}
    for score in claim_scores:
        if not isinstance(score, dict):
            continue
        claim_id = str(score.get("claim_id") or "")
        if not claim_id:
            continue
        claim = claims.get(claim_id, {})
        claim_text = _clean_text(str(claim.get("claim_text") or ""))
        domain = str(score.get("domain") or claim.get("domain") or "overview")
        if not claim_text:
            claim_text = f"{_domain_label(domain)}候选判断需要结合证据链裁决"
        components = {
            key: _float(value, 0.0)
            for key, value in _dict(score.get("components")).items()
            if isinstance(key, str) and isinstance(value, (int, float))
        }
        confidence = _float(score.get("score"), 0.0)
        signal_support = _dict(signal_support_by_claim.get(claim_id))
        candidates.append(
            DecisionCandidate(
                candidate_id=f"candidate:{claim_id}",
                candidate_type=_candidate_type(score, claim),
                claim_id=claim_id,
                domain=domain,
                claim_text=claim_text,
                source_module=_source_module(score, claim),
                evidence_refs=_evidence_refs(claim, score, fallback=claim_id),
                counter_evidence_refs=_counter_evidence_refs(score),
                confidence=confidence,
                score_components=components,
                requires_calibration=bool(score.get("requires_question")),
                role_visibility=_role_visibility(score),
                source_signal_ids=[str(row) for row in _list(signal_support.get("source_signal_ids")) if str(row)],
                signal_source_summary=_signal_source_summary(signal_support),
                candidate_builder={
                    "version": SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION,
                    "mode": candidate_builder_mode,
                    "score_mutation_allowed": False,
                    "score_mutated": False,
                    "confidence_source": "claim_scores",
                    "source_signal_count": int(_float(signal_support.get("signal_count"), 0.0)),
                    "direct_claim_signal_id": str(signal_support.get("direct_claim_signal_id") or ""),
                    "boundary": "decision_candidate_uses_signal_registry_for_binding_without_score_mutation",
                },
            )
        )
    return sorted(candidates, key=lambda row: (-row.confidence, row.domain, row.candidate_id))


def _decision_verdicts(
    candidates: list[DecisionCandidate],
    conflicts: list[DecisionConflict],
    *,
    conflict_audit_by_domain: dict[str, dict[str, object]] | None = None,
) -> list[DecisionVerdict]:
    conflict_audit_by_domain = conflict_audit_by_domain or {}
    conflicts_by_domain: dict[str, list[DecisionConflict]] = defaultdict(list)
    for conflict in conflicts:
        conflicts_by_domain[conflict.domain].append(conflict)
    by_domain: dict[str, list[DecisionCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_domain[candidate.domain].append(candidate)
    verdicts: list[DecisionVerdict] = []
    for domain, rows in sorted(by_domain.items(), key=lambda item: _domain_priority(item[0])):
        rows = sorted(rows, key=lambda row: (-row.confidence, row.candidate_id))
        if not rows:
            continue
        primary = rows[0]
        domain_conflicts = conflicts_by_domain.get(domain, [])
        level = _assertion_level(primary, domain_conflicts)
        evidence_refs = primary.evidence_refs[:8]
        counter_refs = _sorted_unique([*primary.counter_evidence_refs, *[ref for conflict in domain_conflicts for ref in conflict.evidence_for_b]])[:8]
        verdicts.append(
            DecisionVerdict(
                verdict_id=f"verdict:{domain}:{primary.claim_id or primary.candidate_id}",
                domain=domain,
                headline=_headline(primary, level),
                assertion_level=level,
                confidence=primary.confidence,
                primary_branch_id=primary.candidate_id,
                alternative_branch_ids=[row.candidate_id for row in rows[1:4]],
                evidence_refs=evidence_refs,
                counter_evidence_refs=counter_refs,
                allowed_assertions=_allowed_assertions(primary, level),
                forbidden_assertions=_forbidden_assertions(primary, level, bool(domain_conflicts)),
                advice_points=_advice_points(domain, primary, level),
                next_question_slots=_next_question_slots(domain, primary, domain_conflicts),
                trace={
                    "version": "v30.decision_verdict_trace.v1",
                    "source_candidate_id": primary.candidate_id,
                    "source_claim_id": primary.claim_id,
                    "candidate_confidence": primary.confidence,
                    "conflict_count": len(domain_conflicts),
                    "score_components": primary.score_components,
                    "source_signal_ids": primary.source_signal_ids[:12],
                    "signal_source_summary": primary.signal_source_summary,
                    "candidate_builder": primary.candidate_builder,
                    "conflict_resolver": conflict_audit_by_domain.get(domain, {}),
                    "llm_text_as_fact_used": False,
                    "chart_fact_mutation_allowed": False,
                    "boundary": "decision_trace_explains_verdict_from_clean_candidates",
                },
            )
        )
    return sorted(verdicts, key=lambda row: (-_assertion_rank(row.assertion_level), -row.confidence, _domain_priority(row.domain)))


def _assertion_level(candidate: DecisionCandidate, conflicts: list[DecisionConflict]) -> str:
    if candidate.confidence < 0.2:
        return "blocked"
    if any(conflict.conflict_type == "close_branch_probability" for conflict in conflicts):
        return "mixed"
    counter = _float(candidate.score_components.get("counter_evidence"), 0.0)
    missing = _float(candidate.score_components.get("missing_context_penalty"), 0.0)
    overclaim = _float(candidate.score_components.get("overclaim_risk"), 0.0)
    path = _float(candidate.score_components.get("path_coherence"), 0.0)
    if candidate.requires_calibration and candidate.confidence < 0.72:
        return "weak_candidate"
    if counter >= 0.38 or missing >= 0.42 or overclaim >= 0.45:
        return "weak_candidate"
    if candidate.confidence >= 0.82 and counter < 0.2 and missing < 0.2:
        return "confirmed"
    if candidate.confidence >= 0.62 and path >= 0.28:
        return "supported"
    return "weak_candidate"


def _headline(candidate: DecisionCandidate, level: str) -> str:
    text = candidate.claim_text.strip(" 。")
    if level == "confirmed":
        return text
    if level == "supported":
        return text
    if level == "mixed":
        return f"{text}，但当前仍保留相近分支"
    if level == "blocked":
        return f"{_domain_label(candidate.domain)}证据不足，暂不形成断语"
    return f"{text}，目前只能作为候选判断"


def _allowed_assertions(candidate: DecisionCandidate, level: str) -> list[str]:
    domain_label = _domain_label(candidate.domain)
    text = candidate.claim_text.strip(" 。")
    if level == "blocked":
        return [f"{domain_label}暂不下结论，需要先补关键证据。"]
    if level == "mixed":
        return [f"{domain_label}存在分支：当前主分支是{text}，但需要保留备选。"]
    if level == "weak_candidate":
        return [f"{domain_label}可先按候选看：{text}。"]
    return [f"{domain_label}当前主判断是{text}。"]


def _forbidden_assertions(candidate: DecisionCandidate, level: str, has_conflict: bool) -> list[str]:
    forbidden = [
        "不能新增未在命盘事实、规则、路径或画像里出现的事件。",
        "不能把 LLM 表达当成命盘事实来源。",
    ]
    if level in {"mixed", "weak_candidate", "blocked"} or has_conflict:
        forbidden.append("不能把候选分支说成已经完全定死。")
    if candidate.requires_calibration:
        forbidden.append("不能在用户或命理师未校准前扩大断语范围。")
    if candidate.counter_evidence_refs:
        forbidden.append("不能忽略反证或冲突证据。")
    return forbidden


def _advice_points(domain: str, candidate: DecisionCandidate, level: str) -> list[str]:
    if level == "blocked":
        return [f"先补充{_domain_label(domain)}相关关键背景，再继续判断。"]
    defaults = {
        "career": ["先把职责压力拆成资质、规则、平台和可交付成果。", "转型前先确认承接路径，不要只看冲动机会。"],
        "wealth": ["先区分主动争取、合作分配和保守积累三种财务动作。", "先设风险边界，再谈收益节奏。"],
        "relationship": ["先确认互动模式和反复矛盾触发点。", "提前立住表达、距离和承诺边界。"],
        "health": ["先把压力来源、作息节律和身体反馈分开记录。", "先调整最消耗精力的一项习惯。"],
        "timing": ["先把时运触发点对应到具体选择。", "不要把单一年份直接当最终定论。"],
        "structure": ["先复核强弱、十神显隐和用神候选。", "若反证增强，及时降权当前候选。"],
        "useful_god": ["先把用神候选按承接、通关、泄秀和制化分层。", "用后续规则和现实反馈复核取用方向。"],
        "hidden_factor": ["只用低成本问题确认隐藏线索。", "未确认前不把隐藏线索写成事实。"],
    }
    return defaults.get(domain, ["先抓住当前最强证据链。", "保留一个可校准的反馈点。"])[:2]


def _next_question_slots(domain: str, candidate: DecisionCandidate, conflicts: list[DecisionConflict]) -> list[dict[str, Any]]:
    if not (candidate.requires_calibration or conflicts):
        return []
    return [
        {
            "version": "v30.decision_next_question_slot.v1",
            "domain": domain,
            "target_candidate_id": candidate.candidate_id,
            "question": _question_for_domain(domain),
            "reason": "reduce_branch_conflict_or_missing_context",
            "answer_shape": "choice",
            "boundary": "question_slot_is_needed_context_not_dialogue_step",
        }
    ]


def _claims_by_id(diagnosis: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("claim_id") or ""): row
        for row in _list(diagnosis.get("claims"))
        if isinstance(row, dict) and str(row.get("claim_id") or "")
    }


def _candidate_builder_public_summary(payload: dict[str, object]) -> dict[str, object]:
    return {
        "version": str(payload.get("version") or SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION),
        "mode": str(payload.get("mode") or "compatibility"),
        "registry_id": str(payload.get("registry_id") or ""),
        "registry_signal_count": int(_float(payload.get("registry_signal_count"), 0.0)),
        "claim_support_count": int(_float(payload.get("claim_support_count"), 0.0)),
        "claims_with_direct_signal_count": int(_float(payload.get("claims_with_direct_signal_count"), 0.0)),
        "claims_with_any_signal_count": int(_float(payload.get("claims_with_any_signal_count"), 0.0)),
        "source_type_counts": _dict(payload.get("source_type_counts")),
        "source_module_counts": _dict(payload.get("source_module_counts")),
        "score_mutation_allowed": False,
        "score_mutated": False,
        "boundary": "decision_candidate_builder_summary_is_signal_binding_compatibility_trace",
    }


def _signal_source_summary(signal_support: dict[str, object]) -> dict[str, object]:
    if not signal_support:
        return {
            "version": SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION,
            "mode": "compatibility",
            "signal_count": 0,
            "source_type_counts": {},
            "source_module_counts": {},
            "score_mutation_allowed": False,
            "boundary": "no_signal_support_bound_to_candidate",
        }
    return {
        "version": str(signal_support.get("version") or SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION),
        "mode": str(signal_support.get("mode") or "compatibility"),
        "signal_count": int(_float(signal_support.get("signal_count"), 0.0)),
        "direct_claim_signal_id": str(signal_support.get("direct_claim_signal_id") or ""),
        "source_type_counts": _dict(signal_support.get("source_type_counts")),
        "source_module_counts": _dict(signal_support.get("source_module_counts")),
        "evidence_bound_signal_count": int(_float(signal_support.get("evidence_bound_signal_count"), 0.0)),
        "score_mutation_allowed": False,
        "score_mutated": False,
        "boundary": "signal_source_summary_binds_registry_signals_without_changing_candidate_score",
    }


def _conflict_audit_by_domain(value: object) -> dict[str, dict[str, object]]:
    audits: dict[str, dict[str, object]] = {}
    for row in _list(value):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain") or "")
        if domain:
            audits[domain] = row
    return audits


def _candidate_type(score: dict[str, object], claim: dict[str, object]) -> str:
    domain = str(score.get("domain") or claim.get("domain") or "")
    level = str(score.get("claim_level") or claim.get("claim_level") or "")
    if domain in {"useful_god"}:
        return "useful_god"
    if domain in {"timing"}:
        return "timing"
    if level in {"rule"}:
        return "rule"
    if level in {"portrait"}:
        return "portrait"
    if level in {"path"}:
        return "path"
    if level in {"domain"}:
        return "domain"
    return "claim"


def _source_module(score: dict[str, object], claim: dict[str, object]) -> str:
    candidate_type = _candidate_type(score, claim)
    return {
        "rule": "rule_matcher",
        "path": "path_engine",
        "portrait": "portrait_engine",
        "feature": "feature_engine",
        "useful_god": "useful_god_engine",
        "timing": "timing_engine",
        "domain": "domain_synthesis_material",
    }.get(candidate_type, "diagnosis_claim")


def _evidence_refs(claim: dict[str, object], score: dict[str, object], *, fallback: str) -> list[str]:
    refs = [
        *[str(row) for row in _list(claim.get("evidence_ids"))],
        *[str(row) for row in _list(claim.get("rule_ids"))],
        *[str(row) for row in _list(claim.get("path_ids"))],
        *[str(row) for row in _list(claim.get("portrait_ids"))],
    ]
    graph = _dict(score.get("graph_metrics"))
    if graph:
        refs.extend([f"graph_support:{int(_float(graph.get('support_edge_count'), 0.0))}"])
    return _sorted_unique(row for row in refs if row) or [fallback]


def _counter_evidence_refs(score: dict[str, object]) -> list[str]:
    components = _dict(score.get("components"))
    refs: list[str] = []
    if _float(components.get("counter_evidence"), 0.0) > 0:
        refs.append("counter:evidence")
    if _float(components.get("missing_context_penalty"), 0.0) > 0:
        refs.append("missing:context")
    if _float(components.get("overclaim_risk"), 0.0) > 0.2:
        refs.append("risk:overclaim")
    if bool(score.get("requires_question")):
        refs.append("requires:calibration")
    return refs


def _role_visibility(score: dict[str, object]) -> list[str]:
    if bool(score.get("requires_question")):
        return ["user", "practitioner", "admin"]
    return ["user", "practitioner", "admin"]


def _domain_priority(domain: str) -> tuple[int, str]:
    order = {
        "overview": 0,
        "structure": 1,
        "useful_god": 2,
        "career": 3,
        "wealth": 4,
        "relationship": 5,
        "health": 6,
        "timing": 7,
        "hidden_factor": 8,
    }
    return (order.get(domain, 50), domain)


def _assertion_rank(level: str) -> int:
    return {
        "confirmed": 5,
        "supported": 4,
        "mixed": 3,
        "weak_candidate": 2,
        "blocked": 1,
    }.get(level, 0)


def _question_for_domain(domain: str) -> str:
    return {
        "career": "事业更像稳定承接职责，还是已经出现转型触发？",
        "wealth": "当前财务更需要主动争取、合作分配，还是保守积累？",
        "relationship": "关系里最反复的是表达冲突、距离边界，还是承诺节奏？",
        "health": "最近更明显的是压力消耗、作息紊乱，还是身体反馈？",
        "timing": "哪一年或哪段时间的变化最明显？",
        "structure": "当前更能印证身强、身弱，还是中和待复核？",
        "useful_god": "现实反馈更支持承接扶助，还是疏通泄化？",
        "hidden_factor": "是否有反复出现但命盘表层不容易直接解释的经历？",
    }.get(domain, "这个判断最需要补充哪个现实背景？")


def _domain_label(domain: str) -> str:
    return {
        "career": "事业",
        "wealth": "财运",
        "relationship": "关系",
        "health": "健康",
        "timing": "时运",
        "structure": "结构",
        "overview": "整体",
        "useful_god": "用神",
        "hidden_factor": "隐藏线索",
    }.get(domain, domain or "整体")


def _clean_text(text: str) -> str:
    blocked = [
        "不作为固定人生结论",
        "不作为具体人生结果断语",
        "只作为结构路径说明",
        "只作为规则投影",
        "不能独立制造事件结论",
    ]
    pieces: list[str] = []
    for raw in text.replace("；", "。").split("。"):
        sentence = raw.strip()
        if not sentence or any(fragment in sentence for fragment in blocked):
            continue
        pieces.append(sentence)
    return "。".join(pieces).strip(" 。")


def _sorted_unique(values: list[str] | object) -> list[str]:
    if isinstance(values, list):
        iterable = values
    else:
        iterable = list(values) if values is not None else []
    return sorted({str(row) for row in iterable if str(row)})


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _float(value: object, default: float) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default
