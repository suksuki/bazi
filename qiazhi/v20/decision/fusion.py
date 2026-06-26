from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from v20.answer.measurement_policy import domain_label

DECISION_FUSION_VERSION = "v20.decision_fusion.v1"

_CONTROL_DOMAIN_BY_KEY = {
    "control.day_master_strength": "strength",
    "control.shang_guan_jian_guan": "career",
    "control.wealth_capacity": "wealth",
    "control.pattern_status": "pattern",
    "control.mainline_arbitration": "mainline",
}

_CONTROL_STATE_MAP = {
    "control.day_master_strength": {
        "偏强": "confirmed",
        "中和偏强": "chain_review",
        "中和": "mixed",
        "中和偏弱": "weak_candidate",
        "偏弱": "requires_review",
        "待复核": "requires_review",
    },
    "control.shang_guan_jian_guan": {
        "成立": "confirmed",
        "候选": "candidate",
        "被印化": "mixed",
        "被财通关": "chain_review",
        "不成立": "blocked",
        "待复核": "requires_review",
    },
    "control.wealth_capacity": {
        "可承接": "confirmed",
        "需扶身": "weak_candidate",
        "走通关": "chain_review",
        "看大运": "volatile",
        "证据不足": "requires_review",
        "待复核": "requires_review",
    },
    "control.pattern_status": {
        "成格": "confirmed",
        "破格": "mixed",
        "候选": "candidate",
        "不取格": "blocked",
        "待复核": "requires_review",
    },
    "control.mainline_arbitration": {
        "采用第一主线": "confirmed",
        "切换到次级主线": "mixed",
        "暂缓主线": "requires_review",
        "证据不足": "evidence_gap",
    },
}

_STATE_RANK = {
    "confirmed": 90,
    "chain_review": 80,
    "weak_candidate": 70,
    "candidate": 65,
    "mixed": 55,
    "volatile": 45,
    "countered": 40,
    "requires_review": 35,
    "candidate_review": 30,
    "evidence_gap": 25,
    "out_of_scope": 15,
    "blocked": 10,
}

_STATE_CONFIDENCE_BOOST = {
    "confirmed": 0.25,
    "chain_review": 0.18,
    "candidate": 0.12,
    "weak_candidate": 0.08,
    "mixed": 0.06,
    "volatile": 0.05,
    "countered": 0.02,
    "requires_review": 0.00,
    "candidate_review": 0.00,
    "evidence_gap": -0.03,
    "out_of_scope": -0.10,
    "blocked": -0.04,
}

_RISK_BY_STATE = {
    "confirmed": "low",
    "chain_review": "medium",
    "candidate": "medium",
    "weak_candidate": "medium",
    "mixed": "medium",
    "volatile": "medium-high",
    "countered": "high",
    "requires_review": "high",
    "candidate_review": "high",
    "evidence_gap": "high",
    "out_of_scope": "high",
    "blocked": "high",
}

_INTENT_BOUNDARY_BY_STATE = {
    "confirmed": "已形成可复核结构路径，不做确定事件断言。",
    "candidate": "当前偏结构候选，需要补齐强弱与时序先后。",
    "weak_candidate": "线索可见但承接和抗压仍偏弱，先看现实支撑是否足够。",
    "mixed": "结构主次并存，建议先比对主次与反向约束。",
    "chain_review": "链条成立并非一体推演，建议按关键环节顺序复核。",
    "volatile": "结构会被时运和流年牵动，先看触发窗口。",
    "countered": "存在明显反向路径，需要先处理相互牵制的部分。",
    "requires_review": "证据不足，需要补齐复核动作后再下结论。",
    "candidate_review": "处于命理师复核优先位，默认不输出硬结论。",
    "evidence_gap": "当前证据不足，先观察可观察线索。",
    "out_of_scope": "当前依据不足且外推不稳，先说明可观察范围。",
    "blocked": "当前结构受阻，建议先复核反制与优先级。",
}


@dataclass(frozen=True)
class PractitionerRevision:
    revision_id: str
    control_key: str
    domain: str
    option: str
    resolved_state: str
    target_decision_keys: tuple[str, ...]
    source_decision_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeDomainDecision:
    domain: str
    decision_key: str
    structural_state: str
    user_facing_decision: str
    user_facing_boundary: str
    confidence: float
    risk_level: str
    evidence_summary: tuple[str, ...]
    counter_evidence: tuple[str, ...]
    feature_ids: tuple[str, ...]
    source_decision_key: str
    source_rule_key: str
    source_support: tuple[str, ...]
    score: float
    confidence_delta: float
    revision_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_runtime_decision_fusion(
    decision_report: dict[str, object],
    practitioner_selections: tuple[dict[str, object], ...] = (),
) -> dict[str, object]:
    """Build a deterministic, domain-level structural view of current decision state.

    The fusion layer never mutates rule/fact truth; it only annotates and reorders
    runtime signals for downstream recommendation, portrait and answer modules.
    """

    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    by_domain = _group_by_domain(decisions)
    revisions_by_domain = _build_practitioner_revisions(decisions, practitioner_selections)
    runtime_decisions: list[RuntimeDomainDecision] = []
    revision_items: list[PractitionerRevision] = []

    for domain, selected_rows in sorted(by_domain.items()):
        primary, priority_state = _pick_primary_decision(selected_rows)
        revision = _pick_domain_revision(domain, primary, revisions_by_domain)
        applied_state = revision["resolved_state"] if revision else _normalize_state(str(primary.get("status", "")))
        confidence = _fused_confidence(primary, applied_state, revision is not None)
        support_summary = _collect_support(primary)
        counter_summary = _collect_counter_evidence(primary)
        source_decision_key = str(primary.get("decision_key", ""))
        source_rule_key = str(primary.get("rule_key", ""))
        decision_key = f"runtime.{domain}.fused"
        if revision:
            revision_items.append(PractitionerRevision(
                revision_id=f"revision.{revision['control_key']}.{domain}.{source_decision_key or 'all'}",
                control_key=revision["control_key"],
                domain=domain,
                option=revision["option"],
                resolved_state=applied_state,
                target_decision_keys=tuple(revision["target_decision_keys"]),
                source_decision_keys=tuple(revision["source_decision_keys"]),
            ))
        decision_key = decision_key if not source_decision_key else f"{decision_key}.{source_decision_key}"
        runtime_decisions.append(RuntimeDomainDecision(
            domain=domain,
            decision_key=decision_key,
            structural_state=applied_state,
            user_facing_decision=_build_user_facing_decision(domain, applied_state, source=primary, priority_state=priority_state),
            user_facing_boundary=_INTENT_BOUNDARY_BY_STATE.get(applied_state, "先做结构复核后再下结论。"),
            confidence=confidence,
            risk_level=_RISK_BY_STATE.get(applied_state, "high"),
            evidence_summary=tuple(support_summary[:3]),
            counter_evidence=tuple(counter_summary[:3]),
            feature_ids=tuple(str(row) for row in primary.get("feature_ids", ()) if str(row)),
            source_decision_key=source_decision_key,
            source_rule_key=source_rule_key,
            source_support=tuple(primary.get("support", ())[:3]),
            score=float(primary.get("score", 0.0) or 0.0),
            confidence_delta=0.06 if revision else 0.0,
            revision_id=f"revision.{revision['control_key']}.{domain}" if revision else "",
        ))

    fused_payload = {
        "version": DECISION_FUSION_VERSION,
        "status": "ready" if runtime_decisions else "empty",
        "runtime_mutation": False,
        "decision_count": len(runtime_decisions),
        "decision_domains": tuple(decision.domain for decision in runtime_decisions),
        "decisions": tuple(decision.to_dict() for decision in runtime_decisions),
        "revisions": tuple(revision.to_dict() for revision in revision_items),
        "revision_count": len(revision_items),
        "decision_summary": _decision_summary(runtime_decisions),
        "guardrails": (
            "DECISION_FUSION_AGGREGATES_BY_DOMAIN",
            "RUNTIME_DECISIONS_REWRITE_PRACTITIONER_INPUT_NOT_FACTS",
            "PRATITIONER_REVISION_ONLY_AFFECTS_SESSION_RANKING_AND_PRESENTATION",
            "NO_RUNTIME_RULE_TRUTH_MUTATION",
        ),
    }
    return fused_payload


def _group_by_domain(decisions: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in decisions:
        domain = str(row.get("domain", "")).strip()
        if not domain:
            continue
        rows[domain].append(row)
    return rows


def _pick_primary_decision(rows: list[dict[str, object]]) -> tuple[dict[str, object], str]:
    normalized = [
        (
            float(row.get("score", 0.0) or 0.0)
            + _state_rank(_normalize_state(str(row.get("status", "")))) * 0.0008
            + (0.05 if str(row.get("role", "")) in {"mainline_candidate", "foundation_context"} else 0.0),
            row,
        )
        for row in rows
    ]
    if not normalized:
        fallback: dict[str, object] = {"status": "requires_review", "score": 0.0, "feature_ids": (), "support": (), "decision_key": "runtime.empty"}
        return fallback, "requires_review"
    normalized.sort(key=lambda item: item[0], reverse=True)
    top = normalized[0][1]
    return top, _normalize_state(str(top.get("status", "")))


def _pick_domain_revision(
    domain: str,
    primary: dict[str, object],
    revisions: dict[str, list[dict[str, object]]],
) -> dict[str, object] | None:
    candidates = revisions.get(domain, [])
    if not candidates:
        return None
    # Prefer explicit hit to primary decision, otherwise fallback to first domain revision.
    primary_key = str(primary.get("decision_key", ""))
    for item in candidates:
        target = item["target_decision_keys"]
        if not target:
            return item
        if primary_key and primary_key in target:
            return item
    return candidates[0]


def _build_practitioner_revisions(
    decisions: list[dict[str, object]],
    selections: tuple[dict[str, object], ...],
) -> dict[str, list[dict[str, object]]]:
    revisions_by_domain: dict[str, list[dict[str, object]]] = defaultdict(list)
    if not selections:
        return revisions_by_domain

    for selection in selections:
        control_key = str((selection or {}).get("control_key", "")).strip()
        option = str((selection or {}).get("option", "")).strip()
        if not control_key or not option:
            continue
        domain = _CONTROL_DOMAIN_BY_KEY.get(control_key)
        if not domain:
            continue
        decision_key_candidates = tuple(
            str(row)
            for row in (selection or {}).get("source_decision_keys", ())
            if str(row)
        )
        if not decision_key_candidates:
            decision_key_candidates = _decision_candidates_by_control(decisions, control_key)
            control_state = _CONTROL_STATE_MAP.get(control_key, {})
            if not control_state:
                continue
        resolved = _CONTROL_STATE_MAP.get(control_key, {}).get(option)
        if not resolved:
            continue
        revisions_by_domain[domain].append(
            {
                "control_key": control_key,
                "option": option,
                "resolved_state": resolved,
                "target_decision_keys": tuple(_decision_candidates_by_control(decisions, control_key)) if not decision_key_candidates else decision_key_candidates,
                "source_decision_keys": decision_key_candidates,
            }
        )
    return revisions_by_domain


def _decision_candidates_by_control(
    decisions: list[dict[str, object]],
    control_key: str,
) -> tuple[str, ...]:
    rows: list[str] = []
    for row in decisions:
        controls = tuple(
            str(item)
            for item in row.get("practitioner_control_keys", ())
            if str(item)
        )
        if control_key in controls:
            decision_key = str(row.get("decision_key", ""))
            if decision_key:
                rows.append(decision_key)
    return tuple(rows)


def _normalize_state(raw_state: str) -> str:
    state = str(raw_state or "").strip()
    if not state:
        return "requires_review"
    if state in _STATE_RANK:
        return state
    if state == "supports":
        return "candidate"
    if state in {"support", "ready", "active"}:
        return "candidate"
    if state == "evidence_gap":
        return "evidence_gap"
    return "requires_review"


def _state_rank(state: str) -> int:
    return int(_STATE_RANK.get(_normalize_state(state), 20))


def _fused_confidence(row: dict[str, object], state: str, revised: bool) -> float:
    base = float(row.get("score", 0.0) or 0.0)
    state_boost = _STATE_CONFIDENCE_BOOST.get(state, 0.0)
    support_count = len(tuple(str(item) for item in row.get("support", ()) if str(item)))
    support_boost = min(0.07, support_count * 0.016)
    confidence = min(0.98, max(0.18, base + state_boost + support_boost + (0.03 if revised else 0.0)))
    return round(confidence, 3)


def _collect_support(row: dict[str, object]) -> list[str]:
    support: list[str] = []
    for item in tuple(row.get("support", ())):
        text = _public_support_text(str(item))
        if not text:
            continue
        if text not in support:
            support.append(text)
    if not support:
        support.append(_public_support_text(str(row.get("label", ""))) or f"{domain_label(str(row.get('domain', '')))}主线有结构性材料")
    return support


def _collect_counter_evidence(row: dict[str, object]) -> list[str]:
    rows: list[str] = []
    for item in tuple(row.get("counter_evidence", ())):
        text = _public_support_text(str(item))
        if text and text not in rows:
            rows.append(text)
    return rows


def _public_support_text(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if text.startswith("support:"):
        return text.split(":", 1)[1]
    if text.startswith("release:"):
        return text.split(":", 1)[1]
    if text.startswith("constraint:"):
        return text.split(":", 1)[1]
    if text.startswith("channel:"):
        return text.split(":", 1)[1]
    return text


def _build_user_facing_decision(domain: str, state: str, source: dict[str, object], priority_state: str) -> str:
    topic = domain_label(domain)
    label = str(source.get("label", "")).strip() or f"{topic}结构"
    if state == "confirmed":
        return f"{topic}方向形成结构主线：{label}，可作为本次测算优先观察线。"
    if state == "candidate":
        return f"{topic}方向是候选结构：{label}，先观察支持链是否成形。"
    if state == "weak_candidate":
        return f"{topic}方向有线索，但承接、时序和先后仍偏弱。"
    if state == "chain_review":
        return f"{topic}方向更像链式结构：{label}，先复核各环节的先后。"
    if state == "mixed":
        return f"{topic}方向与反向约束并存：{label}，先分主次再下结论。"
    if state == "volatile":
        return f"{topic}方向被时间层牵引明显：{label}，先看触发窗口。"
    if state == "requires_review":
        return f"{topic}方向暂不下稳定结论：{label}，先补齐证据缺口。"
    if state == "evidence_gap":
        return f"{topic}方向材料偏弱：{label}，当前以缺口复核为先。"
    if state == "blocked":
        return f"{topic}方向出现拦截线索：{label}，先处理阻断项。"
    if state == "countered":
        return f"{topic}方向有反向证据：{label}，先看相互牵制的部分。"
    _ = priority_state
    return f"{topic}方向处于{state}状态，{label}。"


def _decision_summary(runtime_decisions: list[RuntimeDomainDecision]) -> dict[str, object]:
    return {
        "ready_domain_count": len(runtime_decisions),
        "high_confidence_domains": tuple(
            decision.domain
            for decision in runtime_decisions
            if decision.confidence >= 0.76
        ),
        "needs_review_domains": tuple(
            decision.domain
            for decision in runtime_decisions
            if decision.structural_state in {"requires_review", "evidence_gap"}
        ),
        "volatile_domains": tuple(
            decision.domain
            for decision in runtime_decisions
            if decision.structural_state == "volatile"
        ),
    }
