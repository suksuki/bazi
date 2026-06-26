from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import Any

from v20.orchestrator.schema import MainlineCandidate


MAINLINE_ARBITRATION_VERSION = "v20.mainline_arbitration.v1"

DOMAIN_NODES = {
    "wealth": ("output", "wealth", "self"),
    "career": ("output", "authority", "resource"),
    "strength": ("self", "resource"),
    "useful_god": ("resource", "self"),
    "pattern": ("authority", "resource"),
    "relationship": ("authority", "wealth"),
    "time": (),
}

RULE_NODES = {
    "output_to_wealth": ("output", "wealth"),
    "output_wealth_capacity": ("output", "wealth", "self"),
    "output_wealth_capacity_chain": ("output", "wealth", "self"),
    "wealth_capacity": ("wealth", "self"),
    "wealth_peer": ("wealth", "self"),
    "wealth.peer_competition": ("wealth", "self"),
    "resource_buffer": ("authority", "resource"),
    "output_authority_resource": ("output", "authority", "resource"),
    "output_authority_resource_chain": ("output", "authority", "resource"),
    "shang_guan_jian_guan": ("output", "authority", "resource"),
    "guan_sha_mixed": ("authority",),
}

NODE_LABELS = {
    "output": "食伤",
    "wealth": "财星",
    "authority": "官杀",
    "resource": "印星",
    "self": "比劫/承载",
}


def arbitrate_mainline(
    *,
    decision_report: dict[str, Any],
    feature_state_model: dict[str, Any],
    structure_dynamics: dict[str, Any],
    question_intent_model: dict[str, Any],
    time_context: dict[str, Any],
    practitioner_selections: tuple[dict[str, Any], ...] = (),
    evidence_items: tuple[dict[str, Any], ...] = (),
    runtime_policy_pointer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidates = _candidates(decision_report, feature_state_model, structure_dynamics, question_intent_model, time_context)
    candidates = _attach_unified_evidence(candidates, evidence_items, question_intent_model, time_context)
    candidates = _rerank_for_question_domain(candidates, question_intent_model)
    candidates, policy_effect = _apply_runtime_policy(candidates, runtime_policy_pointer or {})
    selected = candidates[0] if candidates else _fallback_candidate(structure_dynamics)
    supporting = tuple(row for row in candidates[1:4] if row.candidate_key != selected.candidate_key)
    rejected = tuple(row for row in candidates[4:8])
    selected, supporting, rejected, practitioner_review = _apply_practitioner_mainline_review(
        selected,
        supporting,
        rejected,
        practitioner_selections,
    )
    quality_gate = _quality_gate(selected, supporting, rejected, time_context)
    quality_gate = _apply_review_to_quality_gate(quality_gate, practitioner_review)
    return {
        "version": MAINLINE_ARBITRATION_VERSION,
        "status": "ready" if selected.nodes else "empty",
        "algorithm": "weighted_evidence_mainline_arbitration_phase1",
        "source": "DecisionReport+FeatureStateModel+StructureDynamics+QuestionIntent+TimeContext",
        "primary_mainline": selected.to_dict(),
        "supporting_mainlines": [row.to_dict() for row in supporting],
        "rejected_mainlines": [row.to_dict() for row in rejected],
        "why_selected": _why_selected(selected, supporting),
        "why_not_selected": _why_not_selected(selected, rejected),
        "quality_gate": quality_gate,
        "requires_review": quality_gate["requires_review"],
        "practitioner_review": practitioner_review,
        "runtime_policy_effect": policy_effect,
        "candidate_count": len(candidates),
        "evidence_count": len(evidence_items),
        "evidence_items": _visible_evidence_items(evidence_items),
        "time_layer_status": str(time_context.get("status", "")),
        "runtime_mutation": False,
        "guardrails": [
            "MAINLINE_ARBITRATION_IS_EVIDENCE_WEIGHTED",
            "NO_LLM_CAN_OVERRIDE_PRIMARY_MAINLINE",
            "PORTRAIT_AND_RULES_CAN_RERANK_NOT_CREATE_FACTS",
            "OUTPUT_IS_REVIEWABLE_NOT_FINAL_VERDICT",
            "QUALITY_GATE_CAN_REQUIRE_PRACTITIONER_REVIEW",
            "PRACTITIONER_REVIEW_RERANKS_SESSION_ONLY",
            "MAINLINE_CANDIDATES_REFERENCE_UNIFIED_EVIDENCE",
            "QUESTION_DOMAIN_CAN_BREAK_CLOSE_MAINLINE_TIES",
            "FAST_TRACK_POLICY_CAN_RERANK_MAINLINE_CANDIDATES",
        ],
    }


def _apply_runtime_policy(
    candidates: tuple[MainlineCandidate, ...],
    runtime_policy_pointer: dict[str, Any],
) -> tuple[tuple[MainlineCandidate, ...], dict[str, object]]:
    if not candidates or not runtime_policy_pointer.get("runtime_applied"):
        return candidates, _policy_effect("not_applied", runtime_policy_pointer, 0)
    payload = runtime_policy_pointer.get("policy_payload", {})
    if not isinstance(payload, dict):
        return candidates, _policy_effect("empty_payload", runtime_policy_pointer, 0)
    policies = [row for row in payload.get("mainline_arbitration_weight_policy", ()) if isinstance(row, dict)]
    applied = 0
    adjusted = []
    for candidate in candidates:
        delta, notes = _mainline_policy_delta(candidate, policies)
        if delta:
            applied += 1
            adjusted.append(
                replace(
                    candidate,
                    score=round(max(0.0, min(1.55, candidate.score + delta)), 3),
                    source=_append_source(candidate.source, "runtime_policy"),
                    evidence=tuple(dict.fromkeys((*candidate.evidence, *notes)))[:8],
                    base_score=candidate.base_score or candidate.score,
                    requires_review=candidate.requires_review or delta < 0,
                )
            )
        else:
            adjusted.append(candidate)
    return (
        tuple(sorted(adjusted, key=_candidate_sort_key, reverse=True)),
        _policy_effect("applied" if applied else "no_matching_candidate", runtime_policy_pointer, applied),
    )


def _mainline_policy_delta(candidate: MainlineCandidate, policies: list[dict[str, object]]) -> tuple[float, tuple[str, ...]]:
    delta = 0.0
    notes: list[str] = []
    for policy in policies:
        if not policy.get("runtime_allowed"):
            continue
        target = str(policy.get("primary_mainline_key", ""))
        if target and target != candidate.candidate_key:
            continue
        action = str(policy.get("suggested_action", ""))
        if action == "increase_primary_stability_weight":
            delta += 0.08
            notes.append("中枢记忆策略：提高该主线稳定权重")
        elif action == "increase_supporting_review_weight":
            delta += 0.05
            notes.append("中枢记忆策略：提高次级主线复核权重")
        elif action in {"increase_evidence_gap_penalty", "increase_review_boundary_weight"}:
            delta -= 0.06
            notes.append("中枢记忆策略：提高证据缺口复核权重")
    return delta, tuple(notes)


def _policy_effect(status: str, pointer: dict[str, Any], applied: int) -> dict[str, object]:
    return {
        "version": "v20.mainline_runtime_policy_effect.v1",
        "status": status,
        "active_policy_version": str(pointer.get("active_policy_version", "")),
        "candidate_policy_version": str(pointer.get("candidate_policy_version", "")),
        "applied_adjustment_count": applied,
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_EFFECT_RERANKS_ONLY",
            "NO_CHART_FACT_MUTATION",
            "BASELINE_ROLLBACK_POINTER_AVAILABLE",
        ],
    }


def _rerank_for_question_domain(
    candidates: tuple[MainlineCandidate, ...],
    question_intent_model: dict[str, Any],
) -> tuple[MainlineCandidate, ...]:
    intent_domain = _selected_intent_domain(question_intent_model)
    if not candidates or not intent_domain or candidates[0].domain == intent_domain:
        return candidates
    aligned = [row for row in candidates if row.domain == intent_domain]
    if not aligned:
        return candidates
    top = candidates[0]
    best = aligned[0]
    if best.score < top.score - 0.12:
        return candidates
    promoted = replace(
        best,
        source=_append_source(best.source, "question_domain_focus"),
        evidence=tuple(dict.fromkeys((*best.evidence, f"用户当前问题聚焦：{_domain_label(intent_domain)}"))),
        requires_review=best.requires_review or best.score < top.score,
    )
    return (promoted, *tuple(row for row in candidates if row.candidate_key != best.candidate_key))


def _attach_unified_evidence(
    candidates: tuple[MainlineCandidate, ...],
    evidence_items: tuple[dict[str, Any], ...],
    question_intent_model: dict[str, Any],
    time_context: dict[str, Any],
) -> tuple[MainlineCandidate, ...]:
    if not evidence_items:
        return candidates
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_source_key: dict[str, dict[str, Any]] = {}
    for item in evidence_items:
        if not isinstance(item, dict):
            continue
        by_domain[str(item.get("domain", ""))].append(item)
        by_source_key[str(item.get("source_key", ""))] = item
    intent_domain = _selected_intent_domain(question_intent_model)
    time_ready = str(time_context.get("status", "")) == "ready"
    enriched = []
    for candidate in candidates:
        matched = []
        source_match = by_source_key.get(candidate.candidate_key)
        if source_match:
            matched.append(source_match)
        matched.extend(by_domain.get(candidate.domain, ())[:4])
        if candidate.domain != "time":
            matched.extend(by_domain.get("structure", ())[:1])
        evidence_ids = tuple(dict.fromkeys(str(row.get("evidence_id", "")) for row in matched if row.get("evidence_id")))[:8]
        source_types = tuple(dict.fromkeys(str(row.get("source_type", "")) for row in matched if row.get("source_type")))[:6]
        question_relevance = 0.16 if intent_domain and candidate.domain == intent_domain else 0.0
        time_relevance = 0.08 if time_ready and (candidate.domain == "time" or candidate.source in {"decision_mainline", "structure_dynamics"}) else 0.0
        knowledge_relevance = _knowledge_relevance(matched)
        conflict_risk = _candidate_conflict_risk(candidate)
        evidence_notes = tuple(
            dict.fromkeys(
                str(row.get("label", ""))
                for row in matched
                if str(row.get("source_type", "")) == "knowledge_basis" and str(row.get("label", ""))
            )
        )[:2]
        enriched.append(
            replace(
                candidate,
                candidate_id=candidate.candidate_key,
                source_types=source_types,
                evidence_ids=evidence_ids,
                base_score=candidate.score,
                question_relevance=round(question_relevance, 3),
                time_relevance=round(time_relevance, 3),
                conflict_risk=round(conflict_risk, 3),
                requires_review=candidate.status in {"requires_review", "mixed", "weak_candidate"} or conflict_risk >= 0.32,
                evidence=tuple(dict.fromkeys((*candidate.evidence, *evidence_notes)))[:8],
                score=round(max(0.0, min(1.45, candidate.score + question_relevance + time_relevance + knowledge_relevance - conflict_risk)), 3),
            )
        )
    return tuple(sorted(enriched, key=_candidate_sort_key, reverse=True))


def _knowledge_relevance(matched: list[dict[str, Any]]) -> float:
    weights = [
        float(row.get("weight", 0.0) or 0.0)
        for row in matched
        if isinstance(row, dict) and str(row.get("source_type", "")) == "knowledge_basis"
    ]
    if not weights:
        return 0.0
    return round(min(0.07, max(weights) * 0.06), 3)


def _candidate_conflict_risk(candidate: MainlineCandidate) -> float:
    if candidate.status in {"requires_review", "mixed"}:
        return 0.18
    if candidate.status in {"weak_candidate", "candidate"}:
        return 0.08
    if candidate.status in {"volatile", "chain_review"}:
        return 0.12
    return 0.0


def _visible_evidence_items(evidence_items: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    rows = []
    for item in evidence_items[:24]:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "evidence_id": item.get("evidence_id", ""),
                "source_type": item.get("source_type", ""),
                "source_key": item.get("source_key", ""),
                "domain": item.get("domain", ""),
                "label": item.get("label", ""),
                "summary": item.get("summary", ""),
                "confidence": item.get("confidence", 0),
                "weight": item.get("weight", 0),
                "boundary": item.get("boundary", ""),
                "role_visibility": item.get("role_visibility", []),
            }
        )
    return rows


def _candidates(
    decision_report: dict[str, Any],
    feature_state_model: dict[str, Any],
    structure_dynamics: dict[str, Any],
    question_intent_model: dict[str, Any],
    time_context: dict[str, Any],
) -> tuple[MainlineCandidate, ...]:
    rows: list[MainlineCandidate] = []
    rows.extend(_mainline_candidates(decision_report))
    rows.extend(_decision_candidates(decision_report))
    rows.extend(_portrait_candidates(decision_report))
    rows.extend(_feature_state_candidates(feature_state_model))
    rows.append(_structure_candidate(structure_dynamics))

    intent_domain = _selected_intent_domain(question_intent_model)
    time_ready = str(time_context.get("status", "")) == "ready"
    merged = _merge_candidates(rows, intent_domain=intent_domain, time_ready=time_ready)
    merged = _align_candidates_to_structure_dynamics(merged, structure_dynamics, intent_domain=intent_domain)
    return tuple(sorted(merged, key=_candidate_sort_key, reverse=True))


def _candidate_sort_key(row: MainlineCandidate) -> tuple[float, int, str]:
    return (row.score, _candidate_sort_priority(row), row.source)


def _candidate_sort_priority(row: MainlineCandidate) -> int:
    node_set = set(row.nodes)
    if "structure_dynamics" in row.source and {"output", "authority"}.issubset(node_set):
        return 50
    if {"output", "authority", "resource"}.issubset(node_set):
        return 42
    if {"output", "authority"}.issubset(node_set):
        return 36
    if row.domain == "career":
        return 24
    if row.domain == "wealth":
        return 18
    return 10


def _mainline_candidates(decision_report: dict[str, Any]) -> list[MainlineCandidate]:
    rows = []
    for index, row in enumerate(decision_report.get("mainlines", ())):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain", ""))
        key = str(row.get("mainline_key", "")) or f"mainline.{index}"
        nodes = _nodes_for_key(key) or DOMAIN_NODES.get(domain, ())
        rows.append(
            MainlineCandidate(
                candidate_key=key,
                title=str(row.get("title", "")) or _title(domain, nodes),
                domain=domain,
                nodes=nodes,
                score=round(float(row.get("score", 0.0) or 0.0) + 0.32, 3),
                status=str(row.get("status", "candidate")),
                source="decision_mainline",
                evidence=_tuple(row.get("support", ()))[:5],
            )
        )
    return rows


def _decision_candidates(decision_report: dict[str, Any]) -> list[MainlineCandidate]:
    rows = []
    for row in decision_report.get("decisions", ()):
        if not isinstance(row, dict):
            continue
        role = str(row.get("role", ""))
        if role not in {"mainline_candidate", "supporting_path", "time_context"}:
            continue
        key = str(row.get("decision_key", "") or row.get("rule_key", ""))
        domain = str(row.get("domain", ""))
        nodes = _nodes_for_key(key) or _nodes_for_text(str(row.get("label", "")), _tuple(row.get("support", ()))) or DOMAIN_NODES.get(domain, ())
        rows.append(
            MainlineCandidate(
                candidate_key=key,
                title=str(row.get("label", "")) or _title(domain, nodes),
                domain=domain,
                nodes=nodes,
                score=round(float(row.get("score", 0.0) or 0.0) + 0.18, 3),
                status=str(row.get("status", "candidate")),
                source="decision_candidate",
                evidence=_tuple(row.get("support", ()))[:5],
            )
        )
    return rows


def _portrait_candidates(decision_report: dict[str, Any]) -> list[MainlineCandidate]:
    portrait = decision_report.get("portrait_projection", {})
    axes = portrait.get("axes", ()) if isinstance(portrait, dict) else ()
    rows = []
    for axis in axes:
        if not isinstance(axis, dict):
            continue
        domain = str(axis.get("domain", ""))
        nodes = DOMAIN_NODES.get(domain, ())
        if not nodes:
            continue
        rows.append(
            MainlineCandidate(
                candidate_key=str(axis.get("axis_id", "")) or f"portrait.axis.{domain}",
                title=str(axis.get("structural_anchor", "") or axis.get("label", "")) or _title(domain, nodes),
                domain=domain,
                nodes=nodes,
                score=round(float(axis.get("peak_confidence", 0.0) or 0.0) + 0.1, 3),
                status=str(axis.get("axis_state", "candidate")),
                source="portrait_axis",
                evidence=_tuple(axis.get("evidence_boundaries", ()))[:4],
            )
        )
    return rows


def _feature_state_candidates(feature_state_model: dict[str, Any]) -> list[MainlineCandidate]:
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in feature_state_model.get("priority_features", ()):
        if isinstance(row, dict):
            by_domain[str(row.get("domain", ""))].append(row)
    rows = []
    for domain, states in by_domain.items():
        nodes = DOMAIN_NODES.get(domain, ())
        if not nodes:
            continue
        score = max(float(row.get("priority", 0.0) or 0.0) for row in states)
        rows.append(
            MainlineCandidate(
                candidate_key=f"feature_state.{domain}",
                title=_title(domain, nodes),
                domain=domain,
                nodes=nodes,
                score=round(score + 0.08, 3),
                status="active",
                source="feature_state",
                evidence=tuple(str(row.get("title", "")) for row in states[:4] if row.get("title")),
            )
        )
    return rows


def _structure_candidate(structure_dynamics: dict[str, Any]) -> MainlineCandidate:
    chain = structure_dynamics.get("primary_dynamic_chain", {})
    if not isinstance(chain, dict) or not chain.get("nodes"):
        chain = structure_dynamics.get("dominant_chain_v2", {})
    if not isinstance(chain, dict) or not chain.get("nodes"):
        chain = structure_dynamics.get("legacy_dynamic_chain", {})
    nodes = _tuple(chain.get("nodes", ())) if isinstance(chain, dict) else ()
    domain = _structure_domain(chain, nodes) if isinstance(chain, dict) else "structure"
    return MainlineCandidate(
        candidate_key=str(chain.get("chain_key", "")) if isinstance(chain, dict) else "structure.empty",
        title=str(chain.get("pattern_label") or chain.get("label") or _title("", nodes)) if isinstance(chain, dict) else _title("", nodes),
        domain=domain,
        nodes=nodes,
        score=round(float(chain.get("confidence", structure_dynamics.get("volatility_score", 0.0)) or 0.0) + 0.34, 3) if isinstance(chain, dict) else 0.34,
        status=str(chain.get("state") or structure_dynamics.get("chain_state", "candidate")) if isinstance(chain, dict) else "candidate",
        source="structure_dynamics",
        evidence=_tuple(chain.get("evidence", ()))[:6] if isinstance(chain, dict) else (),
    )


def _structure_domain(chain: dict[str, Any], nodes: tuple[str, ...]) -> str:
    label = str(chain.get("pattern_label", "") or chain.get("label", ""))
    key = str(chain.get("pattern_key", ""))
    node_set = set(nodes)
    if "官杀" in label or "制杀" in label or "authority" in key or "authority" in node_set:
        return "career"
    if "财" in label or "wealth" in key or "wealth" in node_set:
        return "wealth"
    if "印" in label or "resource" in key:
        return "strength"
    return "structure"


def _align_candidates_to_structure_dynamics(
    rows: list[MainlineCandidate],
    structure_dynamics: dict[str, Any],
    *,
    intent_domain: str,
) -> list[MainlineCandidate]:
    chain = structure_dynamics.get("primary_dynamic_chain", {})
    if not isinstance(chain, dict) or not chain.get("nodes"):
        chain = structure_dynamics.get("dominant_chain_v2", {})
    if not isinstance(chain, dict):
        return rows
    structure_nodes = _tuple(chain.get("nodes", ()))
    structure_set = set(structure_nodes)
    pattern_label = str(chain.get("pattern_label", "") or chain.get("label", ""))
    if not structure_set:
        return rows
    has_output_authority = {"output", "authority"}.issubset(structure_set) or any(term in pattern_label for term in ("制官杀", "制杀", "伤官见官"))
    has_output_wealth = {"output", "wealth"}.issubset(structure_set) or "食伤生财" in pattern_label
    if not (has_output_authority or has_output_wealth):
        return rows

    aligned: list[MainlineCandidate] = []
    for row in rows:
        node_set = set(row.nodes)
        delta = 0.0
        notes: list[str] = []
        requires_review = row.requires_review
        if has_output_authority:
            if {"output", "authority"}.issubset(node_set) or row.domain == "career":
                delta += 0.14
                notes.append("结构动态主链指向食伤与官杀，优先按官杀压力与制化链路组织。")
            if {"output", "wealth"}.issubset(node_set) and "authority" not in node_set:
                delta -= 0.22
                requires_review = True
                notes.append("结构动态未把财星作为主链，不默认升为食伤生财。")
        if has_output_wealth and {"output", "wealth"}.issubset(node_set):
            delta += 0.08
            notes.append("结构动态主链支持食伤接财。")
        if delta:
            aligned.append(
                replace(
                    row,
                    score=round(max(0.0, min(1.45, row.score + delta)), 3),
                    source=_append_source(row.source, "structure_dynamic_alignment"),
                    evidence=tuple(dict.fromkeys((*row.evidence, *notes)))[:8],
                    requires_review=requires_review,
                )
            )
        else:
            aligned.append(row)
    return aligned


def _fallback_candidate(structure_dynamics: dict[str, Any]) -> MainlineCandidate:
    return _structure_candidate(structure_dynamics)


def _merge_candidates(
    rows: list[MainlineCandidate],
    *,
    intent_domain: str,
    time_ready: bool,
) -> list[MainlineCandidate]:
    merged: dict[tuple[str, tuple[str, ...]], MainlineCandidate] = {}
    for row in rows:
        if not row.nodes:
            continue
        key = (row.domain, row.nodes)
        bonus = 0.0
        if intent_domain and row.domain == intent_domain:
            bonus += 0.16
        if time_ready and row.source in {"decision_mainline", "structure_dynamics"}:
            bonus += 0.06
        previous = merged.get(key)
        evidence = row.evidence
        score = row.score + bonus
        if previous:
            evidence = tuple(dict.fromkeys((*previous.evidence, *row.evidence)))[:8]
            score = max(previous.score, score) + min(0.22, row.score * 0.08)
        title_source = row if _should_structure_candidate_name_merged_mainline(previous, row) else previous
        merged[key] = MainlineCandidate(
            candidate_key=title_source.candidate_key if title_source else row.candidate_key,
            title=title_source.title if title_source else row.title,
            domain=row.domain,
            nodes=row.nodes,
            score=round(min(1.45, score), 3),
            status=title_source.status if title_source else row.status,
            source=f"{previous.source}+{row.source}" if previous and row.source not in previous.source else row.source,
            evidence=evidence,
        )
    return list(merged.values())


def _should_structure_candidate_name_merged_mainline(
    previous: MainlineCandidate | None,
    row: MainlineCandidate,
) -> bool:
    if previous is None:
        return True
    if row.source != "structure_dynamics":
        return previous.score < row.score
    if row.status not in {"closed", "active", "confirmed"}:
        return previous.score < row.score
    if row.title in {"结构主线", "食伤 → 官杀 → 印星", "食伤 → 财星 → 比劫/承载"}:
        return previous.score < row.score
    return True


def _selected_intent_domain(question_intent_model: dict[str, Any]) -> str:
    selected = question_intent_model.get("selected_question_intent", {})
    return str(selected.get("domain", "")) if isinstance(selected, dict) else ""


def _apply_practitioner_mainline_review(
    selected: MainlineCandidate,
    supporting: tuple[MainlineCandidate, ...],
    rejected: tuple[MainlineCandidate, ...],
    practitioner_selections: tuple[dict[str, Any], ...],
) -> tuple[MainlineCandidate, tuple[MainlineCandidate, ...], tuple[MainlineCandidate, ...], dict[str, Any]]:
    option = _latest_mainline_review_option(practitioner_selections)
    if not option:
        return selected, supporting, rejected, _empty_practitioner_review()

    if option == "采用第一主线":
        reviewed = replace(
            selected,
            status="confirmed",
            source=_append_source(selected.source, "practitioner_review"),
            evidence=tuple(dict.fromkeys((*selected.evidence, "命理师确认采用第一主线"))),
        )
        return reviewed, supporting, rejected, _practitioner_review(option, "accepted_primary", reviewed, selected)

    if option == "切换到次级主线":
        if supporting:
            promoted = replace(
                supporting[0],
                status="mixed",
                source=_append_source(supporting[0].source, "practitioner_review"),
                evidence=tuple(dict.fromkeys((*supporting[0].evidence, "命理师切换到次级主线"))),
            )
            demoted = replace(
                selected,
                status="requires_review",
                source=_append_source(selected.source, "practitioner_review_demoted"),
            )
            new_supporting = (demoted, *supporting[1:])
            return promoted, new_supporting, rejected, _practitioner_review(option, "promoted_supporting", promoted, selected)
        deferred = replace(
            selected,
            status="requires_review",
            source=_append_source(selected.source, "practitioner_review_no_supporting"),
            evidence=tuple(dict.fromkeys((*selected.evidence, "命理师要求切换，但暂无可提升次级主线"))),
        )
        return deferred, supporting, rejected, _practitioner_review(option, "no_supporting_candidate", deferred, selected)

    if option == "暂缓主线":
        deferred = replace(
            selected,
            status="requires_review",
            source=_append_source(selected.source, "practitioner_review_deferred"),
            evidence=tuple(dict.fromkeys((*selected.evidence, "命理师暂缓主线结论"))),
        )
        return deferred, supporting, rejected, _practitioner_review(option, "deferred_primary", deferred, selected)

    if option == "证据不足":
        gap = replace(
            selected,
            status="evidence_gap",
            source=_append_source(selected.source, "practitioner_review_evidence_gap"),
            evidence=tuple(dict.fromkeys((*selected.evidence, "命理师标记主线证据不足"))),
        )
        return gap, supporting, rejected, _practitioner_review(option, "evidence_gap", gap, selected)

    return selected, supporting, rejected, _empty_practitioner_review()


def _latest_mainline_review_option(practitioner_selections: tuple[dict[str, Any], ...]) -> str:
    for selection in reversed(practitioner_selections):
        if not isinstance(selection, dict):
            continue
        if str(selection.get("control_key", "")) == "control.mainline_arbitration":
            return str(selection.get("option", "")).strip()
    return ""


def _empty_practitioner_review() -> dict[str, Any]:
    return {
        "status": "not_applied",
        "option": "",
        "action": "",
        "runtime_mutation": False,
    }


def _practitioner_review(
    option: str,
    action: str,
    selected: MainlineCandidate,
    original: MainlineCandidate,
) -> dict[str, Any]:
    return {
        "status": "applied",
        "option": option,
        "action": action,
        "selected_candidate_key": selected.candidate_key,
        "original_candidate_key": original.candidate_key,
        "runtime_mutation": False,
        "guardrails": [
            "SESSION_REVIEW_ONLY",
            "NO_RULE_FACT_MUTATION",
            "BATCH_PROMOTION_REQUIRED_FOR_MODEL_CHANGE",
        ],
    }


def _append_source(source: str, suffix: str) -> str:
    if suffix in source:
        return source
    return f"{source}+{suffix}" if source else suffix


def _apply_review_to_quality_gate(quality_gate: dict[str, Any], practitioner_review: dict[str, Any]) -> dict[str, Any]:
    if practitioner_review.get("status") != "applied":
        return quality_gate
    gate = dict(quality_gate)
    risks = list(gate.get("risk_flags", ()))
    action = str(practitioner_review.get("action", ""))
    if action == "accepted_primary":
        gate["status"] = "pass_with_practitioner_review"
        gate["requires_review"] = False
        risks = [risk for risk in risks if not risk.startswith("selected_status:")]
        risks.append("practitioner_confirmed_primary")
        gate["review_targets"] = ["命理师已确认第一主线，本轮回答按该主线展开。"]
    elif action == "promoted_supporting":
        gate["status"] = "review_recommended_after_practitioner_switch"
        gate["requires_review"] = True
        risks.append("practitioner_switched_mainline")
    elif action in {"deferred_primary", "evidence_gap", "no_supporting_candidate"}:
        gate["status"] = "review_required_by_practitioner"
        gate["requires_review"] = True
        risks.append(f"practitioner_{action}")
    gate["risk_flags"] = list(dict.fromkeys(risks))
    gate["practitioner_review"] = practitioner_review
    return gate


def _nodes_for_key(key: str) -> tuple[str, ...]:
    normalized = key.replace("decision.", "").replace("rule.", "").replace("mainline.", "")
    for token, nodes in RULE_NODES.items():
        if token in normalized:
            return nodes
    return ()


def _nodes_for_text(label: str, support: tuple[str, ...]) -> tuple[str, ...]:
    text = " ".join((label, *support))
    nodes = []
    if "食神" in text or "伤官" in text or "食伤" in text:
        nodes.append("output")
    if "财" in text:
        nodes.append("wealth")
    if "官" in text or "杀" in text:
        nodes.append("authority")
    if "印" in text:
        nodes.append("resource")
    if "比肩" in text or "劫财" in text or "比劫" in text or "日主" in text or "承载" in text:
        nodes.append("self")
    return tuple(dict.fromkeys(nodes))[:3]


def _title(domain: str, nodes: tuple[str, ...]) -> str:
    labels = [NODE_LABELS.get(node, node) for node in nodes]
    if labels:
        return " → ".join(labels)
    return f"{domain or '结构'}主线"


def _tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return tuple(str(row) for row in value if str(row))
    if isinstance(value, list):
        return tuple(str(row) for row in value if str(row))
    return ()


def _why_selected(selected: MainlineCandidate, supporting: tuple[MainlineCandidate, ...]) -> list[str]:
    title = _public_title(selected.title)
    rows = [f"中枢本轮先以「{title}」组织解读。"]
    if "question_domain_focus" in selected.source or selected.question_relevance > 0:
        rows.append(f"当前问题落在「{_domain_label(selected.domain)}」，所以优先让这条主线进入回答。")
    else:
        rows.append(f"这条主线同时得到{_source_label(selected.source)}支持。")
    evidence = _public_evidence_lines(selected.evidence, 3)
    if evidence:
        rows.append(f"关键依据：{'；'.join(evidence)}。")
    if supporting:
        rows.append(f"次级主线保留复核：{'、'.join(_public_title(row.title) for row in supporting[:2])}。")
    return rows


def _why_not_selected(selected: MainlineCandidate, rejected: tuple[MainlineCandidate, ...]) -> list[str]:
    rows = []
    selected_title = _public_title(selected.title)
    for row in rejected[:3]:
        title = _public_title(row.title)
        if title == selected_title:
            continue
        rows.append(f"{title} 暂列次级观察，先让「{selected_title}」回答当前问题。")
    return rows


def _quality_gate(
    selected: MainlineCandidate,
    supporting: tuple[MainlineCandidate, ...],
    rejected: tuple[MainlineCandidate, ...],
    time_context: dict[str, Any],
) -> dict[str, Any]:
    evidence_count = len(selected.evidence)
    source_parts = {part for part in selected.source.split("+") if part}
    source_count = len(source_parts)
    runner_up = supporting[0] if supporting else None
    margin = round(selected.score - runner_up.score, 3) if runner_up else selected.score
    risks: list[str] = []
    if evidence_count < 2:
        risks.append("evidence_thin")
    if source_count < 2:
        risks.append("single_source_bias")
    if runner_up and margin < 0.12:
        risks.append("close_competing_mainline")
    if selected.status in {"requires_review", "review_required", "chain_review", "mixed", "volatile", "candidate_review"}:
        risks.append(f"selected_status:{selected.status}")
    if str(time_context.get("status", "")) != "ready":
        risks.append("time_layer_not_ready")
    if rejected and rejected[0].score >= selected.score * 0.88:
        risks.append("high_score_rejected_candidate")

    evidence_coverage = round(min(1.0, evidence_count / 4) * 0.42 + min(1.0, source_count / 3) * 0.38 + min(1.0, max(margin, 0.0) / 0.28) * 0.2, 3)
    requires_review = bool(risks) or evidence_coverage < 0.66
    if evidence_coverage >= 0.82 and not any(risk in {"evidence_thin", "single_source_bias"} for risk in risks):
        gate_status = "pass_with_review_notes" if requires_review else "pass"
    elif evidence_coverage >= 0.58:
        gate_status = "review_recommended"
    else:
        gate_status = "review_required"
    return {
        "version": "v20.mainline_quality_gate.v1",
        "status": gate_status,
        "evidence_coverage": evidence_coverage,
        "evidence_count": evidence_count,
        "source_count": source_count,
        "score_margin": margin,
        "requires_review": requires_review,
        "risk_flags": risks,
        "review_targets": _review_targets(selected, supporting, risks),
        "runtime_mutation": False,
        "guardrails": [
            "QUALITY_GATE_IS_DIAGNOSTIC_NOT_VERDICT",
            "LOW_COVERAGE_REQUIRES_PRACTITIONER_REVIEW",
            "REJECTED_MAINLINES_REMAIN_AUDITABLE",
        ],
    }


def _review_targets(
    selected: MainlineCandidate,
    supporting: tuple[MainlineCandidate, ...],
    risks: list[str],
) -> list[str]:
    targets = []
    if "evidence_thin" in risks:
        targets.append(f"补充「{_public_title(selected.title)}」的明透、藏干或画像依据。")
    if "single_source_bias" in risks:
        targets.append("至少需要规则、画像、结构动态中的两类来源共同支持。")
    if "close_competing_mainline" in risks and supporting:
        targets.append(f"复核「{_public_title(selected.title)}」与「{_public_title(supporting[0].title)}」谁先进入回答。")
    if any(risk.startswith("selected_status:") for risk in risks):
        targets.append(f"主线状态为 {selected.status}，需要命理师确认是否可作为第一主线。")
    if "time_layer_not_ready" in risks:
        targets.append("缺少可用岁运层时，主线只按原局、画像和结构依据观察。")
    return targets[:5]


def _source_label(source: str) -> str:
    labels = {
        "decision_mainline": "规则主线",
        "decision_candidate": "规则候选",
        "portrait_axis": "画像轴",
        "feature_state": "特征状态",
        "structure_dynamics": "结构动态",
        "question_domain_focus": "当前问题",
        "practitioner_review": "命理师复核",
    }
    parts = [labels.get(part, part) for part in source.split("+") if part]
    return "、".join(dict.fromkeys(parts)) or "结构证据"


def _public_evidence_lines(evidence: tuple[str, ...], limit: int) -> list[str]:
    rows = []
    for item in evidence:
        text = _public_text(item)
        if not text:
            continue
        rows.append(text)
        if len(rows) >= limit:
            break
    return rows


def _public_title(value: object) -> str:
    return _public_text(value) or "结构主线"


def _public_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "evidence." in text or text.startswith("证据 "):
        return ""
    text = text.replace("规则：明确成立", "")
    text = text.replace("：明确成立", "")
    text = text.replace("规则", "")
    text = text.replace("3/3 条件成立", "条件已形成")
    text = text.replace("2/2 条件成立", "条件已形成")
    text = text.replace("decision_candidate", "规则候选")
    return " ".join(text.split()).strip(" 。；")


def _domain_label(domain: object) -> str:
    labels = {
        "career": "事业结构",
        "wealth": "财运结构",
        "strength": "日主承载",
        "useful_god": "用神候选",
        "pattern": "格局结构",
        "relationship": "关系结构",
        "time": "岁运时间",
        "branch": "地支互动",
        "element": "五行分布",
        "ten_god": "十神结构",
    }
    return labels.get(str(domain or ""), str(domain or ""))
