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
) -> dict[str, Any]:
    candidates = _candidates(decision_report, feature_state_model, structure_dynamics, question_intent_model, time_context)
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
        "candidate_count": len(candidates),
        "time_layer_status": str(time_context.get("status", "")),
        "runtime_mutation": False,
        "guardrails": [
            "MAINLINE_ARBITRATION_IS_EVIDENCE_WEIGHTED",
            "NO_LLM_CAN_OVERRIDE_PRIMARY_MAINLINE",
            "PORTRAIT_AND_RULES_CAN_RERANK_NOT_CREATE_FACTS",
            "OUTPUT_IS_REVIEWABLE_NOT_FINAL_VERDICT",
            "QUALITY_GATE_CAN_REQUIRE_PRACTITIONER_REVIEW",
            "PRACTITIONER_REVIEW_RERANKS_SESSION_ONLY",
        ],
    }


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
    return tuple(sorted(merged, key=lambda row: (row.score, row.source), reverse=True))


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
    chain = structure_dynamics.get("dominant_chain", {})
    nodes = _tuple(chain.get("nodes", ())) if isinstance(chain, dict) else ()
    return MainlineCandidate(
        candidate_key=str(chain.get("chain_key", "")) if isinstance(chain, dict) else "structure.empty",
        title=_title("", nodes),
        domain="structure",
        nodes=nodes,
        score=round(float(structure_dynamics.get("volatility_score", 0.0) or 0.0) + 0.34, 3),
        status=str(structure_dynamics.get("chain_state", "candidate")),
        source="structure_dynamics",
        evidence=_tuple(chain.get("evidence", ()))[:6] if isinstance(chain, dict) else (),
    )


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
        merged[key] = MainlineCandidate(
            candidate_key=previous.candidate_key if previous else row.candidate_key,
            title=previous.title if previous and previous.score >= row.score else row.title,
            domain=row.domain,
            nodes=row.nodes,
            score=round(min(1.45, score), 3),
            status=row.status,
            source=f"{previous.source}+{row.source}" if previous and row.source not in previous.source else row.source,
            evidence=evidence,
        )
    return list(merged.values())


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
    rows = [
        f"{selected.title} 在当前规则、画像和结构动态中综合权重最高。",
        f"来源：{selected.source}，置信分 {selected.score:.2f}。",
    ]
    if selected.evidence:
        rows.append(f"关键证据：{'；'.join(selected.evidence[:3])}。")
    if supporting:
        rows.append(f"次级主线保留观察：{'、'.join(row.title for row in supporting[:2])}。")
    return rows


def _why_not_selected(selected: MainlineCandidate, rejected: tuple[MainlineCandidate, ...]) -> list[str]:
    rows = []
    for row in rejected[:3]:
        rows.append(f"{row.title} 暂不作为第一主线，因为综合分 {row.score:.2f} 低于 {selected.title}。")
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
        targets.append(f"补充「{selected.title}」的明透、藏干、规则或画像证据。")
    if "single_source_bias" in risks:
        targets.append("至少需要规则、画像、结构动态中的两类来源共同支持。")
    if "close_competing_mainline" in risks and supporting:
        targets.append(f"复核「{selected.title}」与「{supporting[0].title}」谁先进入回答。")
    if any(risk.startswith("selected_status:") for risk in risks):
        targets.append(f"主线状态为 {selected.status}，需要命理师确认是否可作为第一主线。")
    if "time_layer_not_ready" in risks:
        targets.append("缺少可用岁运层时，主线只按原局和规则候选观察。")
    return targets[:5]
