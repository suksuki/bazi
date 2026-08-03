from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.agent_fact_language import (
    manifestation_claim_conflicts,
    resolution_ruling_conflicts,
)
from abu_v60.mingli.agent_method_cards import (
    FALLBACK_METHOD_CARD_REF,
    method_card_catalog,
)
from abu_v60.mingli.agent_method_distillation import (
    OUTPUT_TO_PRESSURE,
    OUTPUT_TO_WEALTH,
    cross_card_discriminator,
)
from abu_v60.mingli.agent_output_copy import MINGLI_AGENT_NORMALIZATION_ISSUE_FIELD
from abu_v60.mingli.agent_regime import (
    normalize_regime_decision,
    reconcile_day_master_state,
)

if TYPE_CHECKING:
    from abu_v60.mingli.agent_contracts import MingliAgentCasePacket

AgentMethodRulingValue = Literal[
    "SUPPORTS",
    "CONDITIONAL",
    "OPPOSES",
    "UNRESOLVED",
]
AgentMechanismAdjudication = Literal[
    "SUPPORTED",
    "CONDITIONAL",
    "BROKEN",
    "UNRESOLVED",
]

_DAY_MASTER_STATE_ALIASES = {
    "身强": "STRONG",
    "强": "STRONG",
    "身弱": "WEAK",
    "弱": "WEAK",
    "中和": "BALANCED",
    "平衡": "BALANCED",
    "从势": "FOLLOWING_TENDENCY",
    "专旺": "SPECIALIZED_TENDENCY",
    "不确定": "UNCERTAIN",
}


class AgentMethodRuling(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    method_card_ref: str = Field(min_length=4, max_length=48)
    check_code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    ruling: AgentMethodRulingValue
    rationale: str = Field(min_length=12, max_length=220)
    condition_or_falsifier: str = Field(min_length=8, max_length=180)
    evidence_ids: tuple[str, ...] = Field(max_length=8)

    @model_validator(mode="after")
    def evidence_is_unique(self) -> AgentMethodRuling:
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("mingli_agent_method_ruling_evidence_not_unique")
        return self


class AgentHypothesis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    hypothesis_id: Literal["H1", "H2"]
    role: Literal["PRIMARY", "ALTERNATIVE"]
    name: str = Field(min_length=2, max_length=48)
    judgment: Literal["SUPPORTED", "WORKS_IF", "PARTIAL", "BLOCKED", "COMPETING"]
    mechanism_evidence_ids: tuple[str, ...] = Field(max_length=4)
    method_card_ref: str = Field(min_length=4, max_length=48)
    method_rulings: tuple[AgentMethodRuling, ...] = Field(min_length=5, max_length=6)
    adjudication: AgentMechanismAdjudication
    thesis: str = Field(min_length=12, max_length=300)
    failure_condition: str = Field(min_length=6, max_length=140)
    evidence_ids: tuple[str, ...] = Field(max_length=10)
    confidence: Literal["LOW", "MEDIUM", "HIGH"]


class AgentExcludedCandidate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    method_card_ref: str = Field(min_length=4, max_length=48)
    name: str = Field(min_length=2, max_length=80)
    status: Literal["EXCLUDED", "UNRESOLVED"]
    decisive_check: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    rationale: str = Field(min_length=12, max_length=240)
    evidence_ids: tuple[str, ...] = Field(max_length=8)


class AgentDecisionSide(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rationale: str = Field(min_length=16, max_length=260)
    decisive_checks: tuple[str, ...] = Field(min_length=1, max_length=4)


class AgentReversalTest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    question: str = Field(min_length=12, max_length=180)
    winner_signal: str = Field(min_length=8, max_length=160)
    loser_signal: str = Field(min_length=8, max_length=160)

    @model_validator(mode="after")
    def signals_are_distinct(self) -> AgentReversalTest:
        if not self.question.rstrip().endswith(("？", "?")):
            raise ValueError("mingli_agent_reversal_question_missing_mark")
        if self.winner_signal.strip() == self.loser_signal.strip():
            raise ValueError("mingli_agent_reversal_signals_not_distinct")
        return self


class AgentHypothesisDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    winner_id: Literal["H1", "H2"]
    loser_id: Literal["H1", "H2"]
    winner: AgentDecisionSide
    loser: AgentDecisionSide
    reversal: AgentReversalTest

    @model_validator(mode="after")
    def ids_are_distinct(self) -> AgentHypothesisDecision:
        if self.winner_id == self.loser_id:
            raise ValueError("mingli_agent_decision_ids_not_distinct")
        return self


def aggregate_method_rulings(
    *,
    rulings: tuple[AgentMethodRuling, ...],
    blocking_checks: tuple[str, ...],
) -> AgentMechanismAdjudication:
    by_code = {item.check_code: item.ruling for item in rulings}
    blocking_values = tuple(by_code[item] for item in blocking_checks)
    if "OPPOSES" in blocking_values:
        return "BROKEN"
    if "UNRESOLVED" in blocking_values:
        return "UNRESOLVED"
    all_values = tuple(item.ruling for item in rulings)
    if "UNRESOLVED" in all_values or "CONDITIONAL" in all_values or "OPPOSES" in all_values:
        return "CONDITIONAL"
    return "SUPPORTED"


def normalize_adjudication_output(
    value: Any,
    *,
    packet: MingliAgentCasePacket,
) -> Any:
    """Repair model form and derive all adjudication fields server-side."""

    if not isinstance(value, dict):
        return value
    value = dict(value)
    hypotheses = value.get("hypotheses")
    if not isinstance(hypotheses, list):
        return value
    raw_primary_slots = [
        index
        for index, item in enumerate(hypotheses[:2])
        if isinstance(item, dict) and item.get("role") == "PRIMARY"
    ]
    raw_primary_slot = raw_primary_slots[0] if len(raw_primary_slots) == 1 else None
    raw_primary_method_ref = (
        hypotheses[raw_primary_slot].get("method_card_ref")
        if raw_primary_slot is not None
        and isinstance(hypotheses[raw_primary_slot], dict)
        else None
    )
    # Every newly generated Reading uses the current contract. Historical
    # envelopes are replayed without entering this normalizer, so a missing
    # binding here is a current-model defect to repair and receipt, not a
    # reason to fall back to the legacy count-based selector.
    binding_mode = True
    cards = method_card_catalog(packet.mechanism_observations)
    candidate_refs = [item.evidence_id for item in packet.mechanism_observations]
    assigned_refs, identity_repaired = _assign_method_card_refs(
        hypotheses=hypotheses[:2],
        candidate_refs=candidate_refs,
    )
    natal_ids = {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}
    normalized: list[Any] = []
    normalization_issues: set[str] = set()
    value.pop(MINGLI_AGENT_NORMALIZATION_ISSUE_FIELD, None)
    raw_day_master_state = value.get("day_master_state")
    if raw_day_master_state not in {
        "STRONG",
        "WEAK",
        "BALANCED",
        "FOLLOWING_TENDENCY",
        "SPECIALIZED_TENDENCY",
        "UNCERTAIN",
    }:
        value["day_master_state"] = _DAY_MASTER_STATE_ALIASES.get(
            str(raw_day_master_state).strip(),
            "UNCERTAIN",
        )
        normalization_issues.add("DAY_MASTER")
    regime_decision = normalize_regime_decision(
        value.get("regime_decision"),
        packet=packet,
        day_master_state=value["day_master_state"],
        normalization_issues=normalization_issues,
    )
    value["regime_decision"] = regime_decision
    reconcile_day_master_state(
        value,
        classification=str(regime_decision["classification"]),
        packet=packet,
        normalization_issues=normalization_issues,
    )
    for index, hypothesis in enumerate(hypotheses[:2]):
        if not isinstance(hypothesis, dict):
            normalized.append(hypothesis)
            continue
        hypothesis = dict(hypothesis)
        card_ref = assigned_refs[index]
        if hypothesis.get("hypothesis_id") != f"H{index + 1}":
            normalization_issues.add(f"HYPOTHESIS_H{index + 1}")
        hypothesis["hypothesis_id"] = f"H{index + 1}"
        hypothesis["method_card_ref"] = card_ref
        hypothesis["mechanism_evidence_ids"] = (
            [] if card_ref == FALLBACK_METHOD_CARD_REF else [card_ref]
        )
        card = cards.get(card_ref)
        raw_rulings = hypothesis.get("method_rulings")
        if card is None:
            normalized.append(hypothesis)
            continue
        if index in identity_repaired:
            _neutralize_rebound_hypothesis(
                hypothesis=hypothesis,
                card_ref=card_ref,
                card=card,
            )
            raw_rulings = []
            normalization_issues.add(f"HYPOTHESIS_H{index + 1}")
        raw_rulings = raw_rulings if isinstance(raw_rulings, list) else []
        expected_ruling_identity = [
            (card_ref, check_code) for check_code in card["required_checks"]
        ]
        raw_ruling_identity = [
            (item.get("method_card_ref"), item.get("check_code"))
            for item in raw_rulings
            if isinstance(item, dict)
        ]
        if raw_ruling_identity != expected_ruling_identity:
            normalization_issues.add(f"HYPOTHESIS_H{index + 1}")
        existing = {
            item.get("check_code"): item
            for item in raw_rulings
            if isinstance(item, dict) and item.get("check_code") in set(card["required_checks"])
        }
        ordered: list[dict[str, Any]] = []
        for check_code in card["required_checks"]:
            raw = existing.get(check_code, {})
            ruling = raw.get("ruling")
            if ruling not in {"SUPPORTS", "CONDITIONAL", "OPPOSES", "UNRESOLVED"}:
                ruling = "UNRESOLVED"
            rationale = raw.get("rationale")
            if not isinstance(rationale, str) or len(rationale.strip()) < 12:
                rationale = "这一项尚未形成足以改变整盘主次的明确判断。"
            falsifier = raw.get("condition_or_falsifier")
            if (
                not isinstance(falsifier, str)
                or len(falsifier.strip()) < 8
                or re.fullmatch(r"[A-Z_]+", falsifier.strip())
                or not any(
                    term in falsifier for term in ("若", "如果", "当", "只有", "除非", "反之")
                )
            ):
                falsifier = "若现实反馈与此相反，就重排两种解释。"
            if manifestation_claim_conflicts(
                f"{rationale}\n{falsifier}",
                pillars=packet.pillars,
            ):
                ruling = "UNRESOLVED"
                rationale = "显藏或柱位事实与这项判断冲突；因此仍需复核。"
            if resolution_ruling_conflicts(
                check_code=check_code,
                ruling=ruling,
                rationale=rationale,
            ):
                ruling = "UNRESOLVED"
                rationale = "当前命盘里，这项阻断尚未找到清楚的解除路径；因此仍需复核。"
            if (
                check_code == "DAY_MASTER_CAPACITY"
                and ruling == "SUPPORTS"
                and value.get("day_master_state") in {"WEAK", "UNCERTAIN"}
                and regime_decision["effective_root_status"] != "PRESENT"
                and regime_decision["rooted_visible_support_status"] != "PRESENT"
            ):
                ruling = "CONDITIONAL"
                rationale = "日主无根，浮比与藏印能否持续承载仍需整盘比较。"
                falsifier = "若获得有效根或从势条件闭合，再重判承载。"
                normalization_issues.add(f"DAY_MASTER_CAPACITY_H{index + 1}")
            raw_evidence = raw.get("evidence_ids")
            evidence = raw_evidence if isinstance(raw_evidence, list) else []
            evidence = list(dict.fromkeys(item for item in evidence if item in natal_ids))
            ordered.append(
                {
                    "method_card_ref": card_ref,
                    "check_code": check_code,
                    "ruling": ruling,
                    "rationale": rationale.strip(),
                    "condition_or_falsifier": falsifier.strip(),
                    "evidence_ids": evidence[:8],
                }
            )
        hypothesis["method_rulings"] = ordered
        if ordered != raw_rulings:
            normalization_issues.add(f"HYPOTHESIS_H{index + 1}")
        parsed = tuple(AgentMethodRuling.model_validate(item) for item in ordered)
        hypothesis["adjudication"] = aggregate_method_rulings(
            rulings=parsed,
            blocking_checks=tuple(card["blocking_checks"]),
        )
        normalized.append(hypothesis)
    if len(normalized) != 2 or not all(isinstance(item, dict) for item in normalized):
        value["hypotheses"] = normalized
        return value
    selection_repaired = _normalize_hypothesis_roles(
        normalized=normalized,
        cards=cards,
        packet=packet,
        identity_repaired=identity_repaired,
        raw_primary_slot=raw_primary_slot,
        normalization_issues=normalization_issues,
    )
    if binding_mode and selection_repaired:
        normalization_issues.update({"PRIMARY_SELECTION", "WORK_PATH"})
    value["hypotheses"] = normalized
    raw_excluded = value.get("excluded_candidates")
    value["excluded_candidates"] = _normalize_excluded_candidates(
        raw_excluded,
        normalized=normalized,
        packet=packet,
        cards=cards,
        natal_ids=natal_ids,
    )
    if binding_mode and value["excluded_candidates"] != raw_excluded:
        normalization_issues.add("CANDIDATE_COVERAGE")
    decision_identity_repaired = set(identity_repaired)
    if selection_repaired:
        decision_identity_repaired.update(range(2))
    decision, decision_repaired = _normalize_decision(
        value.get("hypothesis_decision"),
        normalized=normalized,
        identity_repaired=decision_identity_repaired,
        preserve_valid=binding_mode,
    )
    value["hypothesis_decision"] = decision
    if decision_repaired:
        normalization_issues.add("HYPOTHESIS_DECISION")
    primary = next(item for item in normalized if item["role"] == "PRIMARY")
    if (
        raw_primary_method_ref is not None
        and raw_primary_method_ref != primary["method_card_ref"]
    ):
        normalization_issues.add("WORK_PATH")
    work_path = value.get("work_path")
    if binding_mode and isinstance(work_path, dict):
        expected_binding = (
            primary["hypothesis_id"],
            primary["method_card_ref"],
        )
        actual_binding = (
            work_path.get("selected_hypothesis_id"),
            work_path.get("method_card_ref"),
        )
        if selection_repaired or actual_binding != expected_binding:
            work_path = {
                "selected_hypothesis_id": expected_binding[0],
                "method_card_ref": expected_binding[1],
                "path_statement": "主解释与工作路径绑定不一致，本次暂不展示专业转化路径。",
                "transformation_codes": ["CHANNELS"],
                "closure": "UNCERTAIN",
                "condition": "模型重新提交与主解释一致的路径后再判断",
                "evidence_ids": [],
            }
            value["work_path"] = work_path
            normalization_issues.add("WORK_PATH")
    if isinstance(work_path, dict) and work_path.get("closure") == "CLOSED":
        repaired_closure = {
            "CONDITIONAL": "CONDITIONAL",
            "UNRESOLVED": "UNCERTAIN",
            "BROKEN": "BROKEN",
        }.get(primary["adjudication"], "CLOSED")
        if repaired_closure != work_path["closure"]:
            work_path["closure"] = repaired_closure
            normalization_issues.add("WORK_PATH")
    if normalization_issues:
        value[MINGLI_AGENT_NORMALIZATION_ISSUE_FIELD] = sorted(normalization_issues)
    return value


def _assign_method_card_refs(
    *,
    hypotheses: list[Any],
    candidate_refs: list[str],
) -> tuple[tuple[str, str], set[int]]:
    """Preserve valid semantic identities before repairing missing or duplicate refs."""

    raw_refs = [
        item.get("method_card_ref") if isinstance(item, dict) else None
        for item in hypotheses
    ]
    raw_refs.extend([None] * (2 - len(raw_refs)))
    raw_refs = raw_refs[:2]
    if not candidate_refs:
        assigned = (FALLBACK_METHOD_CARD_REF, FALLBACK_METHOD_CARD_REF)
        repaired = {
            index for index, raw_ref in enumerate(raw_refs) if raw_ref != assigned[index]
        }
        return assigned, repaired

    available_refs = (
        [candidate_refs[0], FALLBACK_METHOD_CARD_REF]
        if len(candidate_refs) == 1
        else list(candidate_refs)
    )
    counts = {
        card_ref: sum(raw_ref == card_ref for raw_ref in raw_refs)
        for card_ref in available_refs
    }
    assigned: list[str | None] = [None, None]
    used_refs: set[str] = set()

    # First reserve every valid identity that occurs exactly once. This prevents
    # an invalid earlier slot from taking the later slot's legitimate card.
    for index, raw_ref in enumerate(raw_refs):
        if raw_ref in counts and counts[raw_ref] == 1 and raw_ref not in used_refs:
            assigned[index] = raw_ref
            used_refs.add(raw_ref)

    for index, card_ref in enumerate(assigned):
        if card_ref is not None:
            continue
        assigned[index] = next(item for item in available_refs if item not in used_refs)
        used_refs.add(str(assigned[index]))

    resolved = (str(assigned[0]), str(assigned[1]))
    duplicate_indices = {
        index
        for index, raw_ref in enumerate(raw_refs)
        if raw_ref in counts and counts[raw_ref] > 1
    }
    repaired = {
        index for index, raw_ref in enumerate(raw_refs) if raw_ref != resolved[index]
    } | duplicate_indices
    return resolved, repaired


def _neutralize_rebound_hypothesis(
    *,
    hypothesis: dict[str, Any],
    card_ref: str,
    card: dict[str, object],
) -> None:
    label = str(card.get("label") or "月令与整盘主线解释")
    name = label.removesuffix("候选")[:48]
    hypothesis.update(
        {
            "name": name,
            "thesis": (
                f"{name}需要重新完成全部条件比较，当前只保留为低置信度工作解释。"
            )[:300],
            "failure_condition": "关键来源、目标、承载或阻断条件不成立时不采用",
            "evidence_ids": [] if card_ref == FALLBACK_METHOD_CARD_REF else [card_ref],
            "confidence": "LOW",
        }
    )


def _normalize_excluded_candidates(
    value: Any,
    *,
    normalized: list[dict[str, Any]],
    packet: MingliAgentCasePacket,
    cards: dict[str, dict[str, object]],
    natal_ids: set[str],
) -> list[dict[str, Any]]:
    selected = {
        item["method_card_ref"]
        for item in normalized
        if item["method_card_ref"] != FALLBACK_METHOD_CARD_REF
    }
    expected = [
        item.evidence_id
        for item in packet.mechanism_observations
        if item.evidence_id not in selected
    ]
    raw_items = value if isinstance(value, list) else []
    raw_by_ref = {item.get("method_card_ref"): item for item in raw_items if isinstance(item, dict)}
    labels = {item.evidence_id: item.label for item in packet.mechanism_observations}
    result: list[dict[str, Any]] = []
    for card_ref in expected:
        raw = raw_by_ref.get(card_ref, {})
        card = cards[card_ref]
        decisive_check = raw.get("decisive_check")
        if decisive_check not in set(card["required_checks"]):
            decisive_check = card["blocking_checks"][0]
        status = raw.get("status")
        if status not in {"EXCLUDED", "UNRESOLVED"}:
            status = "UNRESOLVED"
        rationale = raw.get("rationale")
        if not isinstance(rationale, str) or len(rationale.strip()) < 12:
            rationale = "此候选未进入前两条解释，现保留为待比较结构。"
        raw_evidence = raw.get("evidence_ids")
        evidence = raw_evidence if isinstance(raw_evidence, list) else []
        evidence = list(dict.fromkeys(item for item in evidence if item in natal_ids))
        result.append(
            {
                "method_card_ref": card_ref,
                "name": labels[card_ref],
                "status": status,
                "decisive_check": decisive_check,
                "rationale": rationale.strip(),
                "evidence_ids": (evidence or [card_ref])[:8],
            }
        )
    return result


def _normalize_hypothesis_roles(
    *,
    normalized: list[dict[str, Any]],
    cards: dict[str, dict[str, object]],
    packet: MingliAgentCasePacket,
    identity_repaired: set[int],
    raw_primary_slot: int | None,
    normalization_issues: set[str],
) -> bool:
    rank = {"BROKEN": 0, "UNRESOLVED": 1, "CONDITIONAL": 2, "SUPPORTED": 3}
    ruling_score = {"OPPOSES": 0, "UNRESOLVED": 1, "CONDITIONAL": 2, "SUPPORTS": 3}
    pattern_by_card = {
        item.evidence_id: item.pattern_ref for item in packet.mechanism_observations
    }
    discriminator = cross_card_discriminator()
    decisive_by_pattern = {
        OUTPUT_TO_PRESSURE: tuple(discriminator["pressure_decisive_checks"]),
        OUTPUT_TO_WEALTH: tuple(discriminator["wealth_decisive_checks"]),
    }

    def selection_key(index: int) -> tuple[float, ...]:
        item = normalized[index]
        card = cards[item["method_card_ref"]]
        blocking = set(card["blocking_checks"])
        blocker_values = [
            ruling_score[ruling["ruling"]]
            for ruling in item["method_rulings"]
            if ruling["check_code"] in blocking
        ]
        all_values = [ruling_score[ruling["ruling"]] for ruling in item["method_rulings"]]
        decisive_checks = set(
            decisive_by_pattern.get(
                pattern_by_card.get(item["method_card_ref"], ""),
                tuple(blocking),
            )
        )
        decisive_values = [
            ruling_score[ruling["ruling"]]
            for ruling in item["method_rulings"]
            if ruling["check_code"] in decisive_checks
        ]
        return (
            float(rank[item["adjudication"]]),
            float(min(decisive_values, default=0)),
            sum(decisive_values) / max(1, len(decisive_values)),
            sum(blocker_values) / max(1, len(blocker_values)),
            sum(all_values) / max(1, len(all_values)),
            float(index not in identity_repaired),
            float(-index),
        )

    raw_primary_index = (
        raw_primary_slot
        if raw_primary_slot is not None and raw_primary_slot not in identity_repaired
        else None
    )
    selected = (
        raw_primary_index
        if raw_primary_index is not None
        and normalized[raw_primary_index]["adjudication"] != "BROKEN"
        else max(range(2), key=selection_key)
    )
    if all(item["adjudication"] == "BROKEN" for item in normalized):
        selected = 0
        fallback_repaired = True
        normalization_issues.add(f"HYPOTHESIS_H{selected + 1}")
        fallback = cards[FALLBACK_METHOD_CARD_REF]
        normalized[selected]["method_card_ref"] = FALLBACK_METHOD_CARD_REF
        normalized[selected]["mechanism_evidence_ids"] = []
        normalized[selected]["name"] = "月令与整盘主线解释"
        normalized[selected]["method_rulings"] = [
            {
                "method_card_ref": FALLBACK_METHOD_CARD_REF,
                "check_code": check,
                "ruling": "UNRESOLVED",
                "rationale": "命名机制均受阻，先回到月令与整盘力量次序继续判断。",
                "condition_or_falsifier": "若现实反馈支持一条完整路径，再恢复对应机制解释。",
                "evidence_ids": [],
            }
            for check in fallback["required_checks"]
        ]
        normalized[selected]["adjudication"] = "UNRESOLVED"
    else:
        fallback_repaired = False
    for index, item in enumerate(normalized):
        item["role"] = "PRIMARY" if index == selected else "ALTERNATIVE"
        aggregate = item["adjudication"]
        item["judgment"] = {
            "SUPPORTED": "SUPPORTED",
            "CONDITIONAL": "WORKS_IF" if index == selected else "PARTIAL",
            "BROKEN": "BLOCKED",
            "UNRESOLVED": "COMPETING",
        }[aggregate]
        if aggregate in {"BROKEN", "UNRESOLVED"}:
            item["confidence"] = "LOW"
        elif item.get("confidence") not in {"LOW", "MEDIUM"}:
            item["confidence"] = "MEDIUM"
    alternative_index = 1 - selected
    if rank[normalized[selected]["adjudication"]] < rank[
        normalized[alternative_index]["adjudication"]
    ]:
        normalized[selected]["confidence"] = "LOW"
    if normalized[0].get("name") == normalized[1].get("name"):
        normalized[1]["name"] = f"{normalized[1]['name']}的替代解释"
    return fallback_repaired or raw_primary_index is None or selected != raw_primary_index


def _normalize_decision(
    value: Any,
    *,
    normalized: list[dict[str, Any]],
    identity_repaired: set[int],
    preserve_valid: bool,
) -> tuple[dict[str, Any], bool]:
    raw = value if isinstance(value, dict) else {}
    primary = next(item for item in normalized if item["role"] == "PRIMARY")
    alternative = next(item for item in normalized if item["role"] == "ALTERNATIVE")

    if preserve_valid and not identity_repaired and _decision_matches_hypotheses(
        raw,
        primary=primary,
        alternative=alternative,
    ):
        return dict(raw), False

    def side(item: dict[str, Any], label: str) -> dict[str, Any]:
        preferred = (
            ("SUPPORTS", "CONDITIONAL", "UNRESOLVED", "OPPOSES")
            if label == "主解释"
            else ("OPPOSES", "UNRESOLVED", "CONDITIONAL", "SUPPORTS")
        )
        selected = list(
            dict.fromkeys(
                ruling["check_code"]
                for status in preferred
                for ruling in item["method_rulings"]
                if ruling["ruling"] == status
            )
        )[:2]
        decisive = next(
            ruling for ruling in item["method_rulings"] if ruling["check_code"] == selected[0]
        )
        counts = {
            status: sum(ruling["ruling"] == status for ruling in item["method_rulings"])
            for status in ("SUPPORTS", "CONDITIONAL", "UNRESOLVED", "OPPOSES")
        }
        rationale = (
            f"{item.get('name', label)}"
            f"{'暂列主线' if label == '主解释' else '暂不列主线'}："
            f"{counts['SUPPORTS']}项支持、{counts['CONDITIONAL']}项有条件、"
            f"{counts['UNRESOLVED']}项未决、{counts['OPPOSES']}项反对；"
            f"{decisive['rationale']}"
        )[:260]
        return {"rationale": rationale, "decisive_checks": selected[:4]}

    reversal = raw.get("reversal")
    reversal = reversal if isinstance(reversal, dict) else {}
    question = reversal.get("question")
    if not isinstance(question, str) or len(question.strip()) < 12:
        question = "现实中更常先出现成果转化，还是先出现责任压力？"
    if not question.rstrip().endswith(("？", "?")):
        question = f"{question.rstrip('。！!')}？"
    raw_winner_id = raw.get("winner_id")
    raw_loser_id = raw.get("loser_id")
    signal_by_hypothesis: dict[str, Any] = {}
    if (
        raw_winner_id in {"H1", "H2"}
        and raw_loser_id in {"H1", "H2"}
        and raw_winner_id != raw_loser_id
    ):
        signal_by_hypothesis = {
            str(raw_winner_id): reversal.get("winner_signal"),
            str(raw_loser_id): reversal.get("loser_signal"),
        }
    repaired_ids = {f"H{index + 1}" for index in identity_repaired}
    winner_signal = (
        None
        if primary["hypothesis_id"] in repaired_ids
        else signal_by_hypothesis.get(primary["hypothesis_id"])
    )
    if not isinstance(winner_signal, str) or len(winner_signal.strip()) < 8:
        winner_signal = f"若更符合{primary.get('name', '主解释')}，维持当前判断。"
    elif primary.get("name") not in winner_signal:
        winner_signal = f"更符合{primary['name']}：{winner_signal}"
    loser_signal = (
        None
        if alternative["hypothesis_id"] in repaired_ids
        else signal_by_hypothesis.get(alternative["hypothesis_id"])
    )
    if not isinstance(loser_signal, str) or len(loser_signal.strip()) < 8:
        loser_signal = f"若更符合{alternative.get('name', '替代解释')}，就翻转主次。"
    elif alternative.get("name") not in loser_signal:
        loser_signal = f"更符合{alternative['name']}：{loser_signal}"
    return {
        "winner_id": primary["hypothesis_id"],
        "loser_id": alternative["hypothesis_id"],
        "winner": side(primary, "主解释"),
        "loser": side(alternative, "替代解释"),
        "reversal": {
            "question": question,
            "winner_signal": winner_signal[:160],
            "loser_signal": loser_signal[:160],
        },
    }, preserve_valid


def _decision_matches_hypotheses(
    raw: dict[str, Any],
    *,
    primary: dict[str, Any],
    alternative: dict[str, Any],
) -> bool:
    try:
        decision = AgentHypothesisDecision.model_validate(raw)
    except ValueError:
        return False
    if (
        decision.winner_id != primary["hypothesis_id"]
        or decision.loser_id != alternative["hypothesis_id"]
    ):
        return False
    for side, hypothesis in (
        (decision.winner, primary),
        (decision.loser, alternative),
    ):
        allowed = {item["check_code"] for item in hypothesis["method_rulings"]}
        if not set(side.decisive_checks).issubset(allowed):
            return False
    return True
