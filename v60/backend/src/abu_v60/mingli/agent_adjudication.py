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

if TYPE_CHECKING:
    from abu_v60.mingli.agent_contracts import (
        MingliAgentCasePacket,
        MingliAgentModelOutput,
    )

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
    cards = method_card_catalog(packet.mechanism_observations)
    candidate_refs = [item.evidence_id for item in packet.mechanism_observations]
    available_refs = [*candidate_refs, FALLBACK_METHOD_CARD_REF]
    forced_refs = (
        [FALLBACK_METHOD_CARD_REF, FALLBACK_METHOD_CARD_REF]
        if not candidate_refs
        else [candidate_refs[0], FALLBACK_METHOD_CARD_REF]
        if len(candidate_refs) == 1
        else candidate_refs
        if len(candidate_refs) == 2
        else None
    )
    natal_ids = {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}
    normalized: list[Any] = []
    used_refs: set[str] = set()
    for index, hypothesis in enumerate(hypotheses[:2]):
        if not isinstance(hypothesis, dict):
            normalized.append(hypothesis)
            continue
        hypothesis = dict(hypothesis)
        card_ref = (
            forced_refs[index] if forced_refs is not None else hypothesis.get("method_card_ref")
        )
        if card_ref not in cards or (card_ref in used_refs and len(candidate_refs) >= 2):
            card_ref = next(
                (item for item in available_refs if item not in used_refs),
                FALLBACK_METHOD_CARD_REF,
            )
        used_refs.add(str(card_ref))
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
        raw_rulings = raw_rulings if isinstance(raw_rulings, list) else []
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
                rationale = "显藏或柱位事实不支持原判断；本项仍未决。"
            if resolution_ruling_conflicts(
                check_code=check_code,
                ruling=ruling,
                rationale=rationale,
            ):
                ruling = "UNRESOLVED"
                rationale = "原回答描述了阻断，却没有说明阻断如何解除；本项仍未决。"
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
        parsed = tuple(AgentMethodRuling.model_validate(item) for item in ordered)
        hypothesis["adjudication"] = aggregate_method_rulings(
            rulings=parsed,
            blocking_checks=tuple(card["blocking_checks"]),
        )
        normalized.append(hypothesis)
    if len(normalized) != 2 or not all(isinstance(item, dict) for item in normalized):
        value["hypotheses"] = normalized
        return value
    _normalize_hypothesis_roles(normalized=normalized, cards=cards, packet=packet)
    value["hypotheses"] = normalized
    value["excluded_candidates"] = _normalize_excluded_candidates(
        value.get("excluded_candidates"),
        normalized=normalized,
        packet=packet,
        cards=cards,
        natal_ids=natal_ids,
    )
    value["hypothesis_decision"] = _normalize_decision(
        value.get("hypothesis_decision"),
        normalized=normalized,
    )
    primary = next(item for item in normalized if item["role"] == "PRIMARY")
    work_path = value.get("work_path")
    if isinstance(work_path, dict) and work_path.get("closure") == "CLOSED":
        work_path["closure"] = {
            "CONDITIONAL": "CONDITIONAL",
            "UNRESOLVED": "UNCERTAIN",
            "BROKEN": "BROKEN",
        }.get(primary["adjudication"], "CLOSED")
    return value


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
) -> None:
    rank = {"BROKEN": 0, "UNRESOLVED": 1, "CONDITIONAL": 2, "SUPPORTED": 3}
    ruling_score = {"OPPOSES": 0, "UNRESOLVED": 1, "CONDITIONAL": 2, "SUPPORTS": 3}

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
        return (
            float(rank[item["adjudication"]]),
            sum(blocker_values) / max(1, len(blocker_values)),
            sum(all_values) / max(1, len(all_values)),
            float(-index),
        )

    selected = max(range(2), key=selection_key)
    if all(item["adjudication"] == "BROKEN" for item in normalized):
        selected = 0
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
    if normalized[0].get("name") == normalized[1].get("name"):
        normalized[1]["name"] = f"{normalized[1]['name']}的替代解释"


def _normalize_decision(
    value: Any,
    *,
    normalized: list[dict[str, Any]],
) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    primary = next(item for item in normalized if item["role"] == "PRIMARY")
    alternative = next(item for item in normalized if item["role"] == "ALTERNATIVE")

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
    winner_signal = reversal.get("winner_signal")
    if not isinstance(winner_signal, str) or len(winner_signal.strip()) < 8:
        winner_signal = f"若更符合{primary.get('name', '主解释')}，维持当前判断。"
    elif primary.get("name") not in winner_signal:
        winner_signal = f"更符合{primary['name']}：{winner_signal}"
    loser_signal = reversal.get("loser_signal")
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
    }


def bind_packet_fact_fields(
    value: Any,
    *,
    packet: MingliAgentCasePacket,
) -> Any:
    """Replace model-copied facts with packet-owned coordinates and scope."""

    if not isinstance(value, dict):
        return value
    value = dict(value)
    roots = packet.day_master_support.same_element_hidden_support
    value["support_selection"] = {
        "root_status": "PRESENT" if roots else "NONE",
        "root_coordinates": list(roots),
        "peer_coordinates": list(packet.day_master_support.visible_peer_support),
        "resource_coordinates": list(packet.day_master_support.resource_support),
    }
    _bind_life_image(value=value, packet=packet)
    _bind_timing_fact_fields(value=value, packet=packet)
    return value


_IMAGE_SUBJECTS = {
    "甲": "挺直乔木",
    "乙": "柔韧藤木",
    "丙": "高悬日火",
    "丁": "守夜灯火",
    "戊": "厚重山岭",
    "己": "细作田畴",
    "庚": "待炼矿铁",
    "辛": "经琢珠玉",
    "壬": "奔行江水",
    "癸": "润物雨露",
}
_SEASON_SCENES = {
    **{branch: "早春原野" for branch in "寅卯辰"},
    **{branch: "盛夏旷野" for branch in "巳午未"},
    **{branch: "清秋庭野" for branch in "申酉戌"},
    **{branch: "寒冬山野" for branch in "亥子丑"},
}
_ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
_NON_IMAGE_TERMS = (
    "知识分子",
    "知识工作者",
    "专业技术",
    "艺术家",
    "思考者",
    "技能变现",
    "模型",
    "框架",
    "工坊",
    "身强",
    "身弱",
    "用神",
    "忌神",
    "格局",
)


def _bind_life_image(*, value: dict[str, Any], packet: MingliAgentCasePacket) -> None:
    life_image = value.get("life_image")
    life_image = life_image if isinstance(life_image, dict) else {}
    corpus = "\n".join(str(life_image.get(key, "")) for key in ("title", "image", "explanation"))
    valid_shape = (
        isinstance(life_image.get("title"), str)
        and len(life_image["title"].strip()) >= 2
        and isinstance(life_image.get("image"), str)
        and len(life_image["image"].strip()) >= 8
        and isinstance(life_image.get("explanation"), str)
        and len(life_image["explanation"].strip()) >= 16
    )
    if valid_shape and not any(term in corpus for term in _NON_IMAGE_TERMS):
        return
    scene = _SEASON_SCENES[packet.month_command_branch]
    subject = _IMAGE_SUBJECTS[packet.day_master_stem]
    roots = len(packet.day_master_support.same_element_hidden_support)
    peers = len(packet.day_master_support.visible_peer_support)
    resources = len(packet.day_master_support.resource_support)
    root_image = "脚下已有同类根系可依" if roots else "脚下没有同类根系可依"
    peer_image = f"近旁有{peers}处同类彼此呼应" if peers else "近旁少见同类呼应"
    resource_image = f"暗处仍有{resources}处生扶维持气息" if resources else "暗处也少见生扶接续"
    life_image.update(
        {
            "title": f"{scene}里的{subject}"[:24],
            "image": f"{scene}里，{subject}迎着时令展开；{root_image}，{peer_image}，{resource_image}。",
            "explanation": (
                f"日主为{packet.day_master_stem}{_ELEMENT_LABELS[packet.day_master_element]}，"
                f"生在{packet.month_command_branch}月；地支同类根{roots}处，"
                f"明干同类{peers}处，印星生扶{resources}处。"
                "因此画面强调的是它如何承载、借力并继续生长。"
            ),
            "evidence_ids": [
                packet.pillars[1].evidence_id,
                packet.day_master_support.evidence_id,
            ],
        }
    )
    value["life_image"] = life_image


def _bind_timing_fact_fields(
    *,
    value: dict[str, Any],
    packet: MingliAgentCasePacket,
) -> None:
    timing = value.get("timing")
    if not isinstance(timing, dict):
        return
    timing = dict(timing)
    coordinates = {item.layer: item.evidence_id for item in packet.timing_coordinates}
    relations = {
        layer: {item.evidence_id for item in packet.timing_relations if item.left_layer == layer}
        for layer in ("DAYUN", "ANNUAL")
    }
    natal = {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}
    dayun_allowed = natal | {coordinates["DAYUN"]} | relations["DAYUN"]
    allowed_by_layer = {
        "DAYUN": dayun_allowed,
        "ANNUAL": dayun_allowed | {coordinates["ANNUAL"]} | relations["ANNUAL"],
    }
    for key, layer in (("dayun", "DAYUN"), ("annual", "ANNUAL")):
        reading = timing.get(key)
        if not isinstance(reading, dict):
            continue
        reading = dict(reading)
        raw_evidence = reading.get("evidence_ids")
        evidence = raw_evidence if isinstance(raw_evidence, list) else []
        raw_relations = reading.get("relation_evidence_ids")
        relation_values = raw_relations if isinstance(raw_relations, list) else []
        selected_relations = list(
            dict.fromkeys(
                item for item in (*relation_values, *evidence) if item in relations[layer]
            )
        )
        filtered = [item for item in evidence if item in allowed_by_layer[layer]]
        reading["coordinate_evidence_id"] = coordinates[layer]
        reading["relation_evidence_ids"] = selected_relations
        reading["evidence_ids"] = list(
            dict.fromkeys((*filtered, coordinates[layer], *selected_relations))
        )[:8]
        timing[key] = reading
    value["timing"] = timing


def repair_output_form(value: Any) -> Any:
    """Remove schema labels from copy while retaining typed enum fields."""

    if not isinstance(value, dict):
        return value
    value = dict(value)
    first_look = value.get("first_look")
    if isinstance(first_look, str):
        value["first_look"] = re.sub(
            r"^(?:PRIMARY|ALTERNATIVE|H1|H2)\s*[:：·-]\s*",
            "",
            first_look,
            flags=re.IGNORECASE,
        )
    hypotheses = value.get("hypotheses")
    names: dict[str, str] = {}
    if isinstance(hypotheses, list):
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                continue
            name = hypothesis.get("name")
            if isinstance(name, str):
                repaired = re.sub(
                    r"\s*[（(](?:PRIMARY|ALTERNATIVE|H1|H2)[）)]\s*$",
                    "",
                    name,
                    flags=re.IGNORECASE,
                ).strip()
                hypothesis["name"] = repaired
                hypothesis_id = hypothesis.get("hypothesis_id")
                if isinstance(hypothesis_id, str):
                    names[hypothesis_id] = repaired
    decision = value.get("hypothesis_decision")
    if isinstance(decision, dict):
        for key in ("winner", "loser"):
            side = decision.get(key)
            if isinstance(side, dict) and isinstance(side.get("rationale"), str):
                side["rationale"] = _repair_decision_copy(side["rationale"], names)
        reversal = decision.get("reversal")
        if isinstance(reversal, dict):
            for key in ("question", "winner_signal", "loser_signal"):
                if isinstance(reversal.get(key), str):
                    reversal[key] = _repair_decision_copy(reversal[key], names)
    return _repair_nested_copy(value, names=names)


def _repair_decision_copy(value: str, names: dict[str, str]) -> str:
    for hypothesis_id, name in names.items():
        value = re.sub(
            rf"(?<![A-Za-z0-9]){hypothesis_id}(?![A-Za-z0-9])",
            name,
            value,
        )
    value = re.sub(
        r"(?:SUPPORTS|CONDITIONAL|OPPOSES|UNRESOLVED)\s*[:：]\s*",
        "",
        value,
    )
    return (
        value.replace("UNRESOLVED", "尚需校准")
        .replace("BLOCKED", "路径受阻")
        .replace("PRIMARY", "主解释")
        .replace("ALTERNATIVE", "替代解释")
    )


_NON_PROSE_FIELDS = {
    "adjudication",
    "check_code",
    "closure",
    "confidence",
    "coordinate_evidence_id",
    "day_master_state",
    "evidence_ids",
    "hypothesis_id",
    "judgment",
    "loser_id",
    "mechanism_evidence_ids",
    "method_card_ref",
    "natal_evidence_ids",
    "relation_evidence_ids",
    "role",
    "root_status",
    "ruling",
    "transformation_codes",
    "winner_id",
}


def _repair_nested_copy(value: Any, *, names: dict[str, str], field: str = "") -> Any:
    if isinstance(value, dict):
        return {
            key: _repair_nested_copy(item, names=names, field=key) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_repair_nested_copy(item, names=names, field=field) for item in value]
    if isinstance(value, str) and field not in _NON_PROSE_FIELDS:
        return _repair_decision_copy(value, names)
    return value


def validate_adjudication_output(
    *,
    output: MingliAgentModelOutput,
    packet: MingliAgentCasePacket,
) -> None:
    cards = method_card_catalog(packet.mechanism_observations)
    natal_ids = {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}
    by_id = {item.hypothesis_id: item for item in output.hypotheses}
    if (
        len(packet.mechanism_observations) >= 2
        and len({item.method_card_ref for item in output.hypotheses}) != 2
    ):
        raise ValueError("mingli_agent_hypothesis_cards_not_competing")
    for hypothesis in output.hypotheses:
        card = cards.get(hypothesis.method_card_ref)
        if card is None:
            raise ValueError("mingli_agent_unknown_method_card")
        expected = tuple(card["required_checks"])
        actual = tuple(item.check_code for item in hypothesis.method_rulings)
        if actual != expected:
            raise ValueError("mingli_agent_method_checks_not_exact_order")
        if any(
            item.method_card_ref != hypothesis.method_card_ref for item in hypothesis.method_rulings
        ):
            raise ValueError("mingli_agent_method_ruling_card_mismatch")
        if any(
            not set(item.evidence_ids).issubset(natal_ids) for item in hypothesis.method_rulings
        ):
            raise ValueError("mingli_agent_method_ruling_uses_non_natal_evidence")
        if hypothesis.method_card_ref == FALLBACK_METHOD_CARD_REF:
            if hypothesis.mechanism_evidence_ids:
                raise ValueError("mingli_agent_fallback_card_has_mechanism_evidence")
        elif hypothesis.mechanism_evidence_ids != (hypothesis.method_card_ref,):
            raise ValueError("mingli_agent_method_card_mechanism_mismatch")
        expected_aggregate = aggregate_method_rulings(
            rulings=hypothesis.method_rulings,
            blocking_checks=tuple(card["blocking_checks"]),
        )
        if hypothesis.adjudication != expected_aggregate:
            raise ValueError("mingli_agent_method_aggregate_mismatch")
        if expected_aggregate == "BROKEN" and hypothesis.judgment != "BLOCKED":
            raise ValueError("mingli_agent_broken_method_not_blocked")
        if expected_aggregate == "SUPPORTED" and hypothesis.judgment != "SUPPORTED":
            raise ValueError("mingli_agent_supported_method_not_supported")
        if expected_aggregate == "CONDITIONAL" and hypothesis.judgment not in {
            "WORKS_IF",
            "PARTIAL",
        }:
            raise ValueError("mingli_agent_conditional_method_judgment_conflict")
        if expected_aggregate == "UNRESOLVED" and hypothesis.judgment != "COMPETING":
            raise ValueError("mingli_agent_unresolved_method_not_competing")
        if hypothesis.confidence == "HIGH":
            raise ValueError("mingli_agent_hypothesis_confidence_exceeds_adjudication")
        if expected_aggregate in {"BROKEN", "UNRESOLVED"} and hypothesis.confidence != "LOW":
            raise ValueError("mingli_agent_unresolved_method_confidence_too_high")

    selected_cards = {
        item.method_card_ref
        for item in output.hypotheses
        if item.method_card_ref != FALLBACK_METHOD_CARD_REF
    }
    expected_excluded = tuple(
        item.evidence_id
        for item in packet.mechanism_observations
        if item.evidence_id not in selected_cards
    )
    if tuple(item.method_card_ref for item in output.excluded_candidates) != expected_excluded:
        raise ValueError("mingli_agent_candidate_coverage_incomplete")
    for item in output.excluded_candidates:
        card = cards[item.method_card_ref]
        if item.decisive_check not in set(card["required_checks"]):
            raise ValueError("mingli_agent_excluded_candidate_check_invalid")
        if not set(item.evidence_ids).issubset(natal_ids):
            raise ValueError("mingli_agent_excluded_candidate_uses_non_natal_evidence")
    candidate_count = len(packet.mechanism_observations)
    expected_selected = min(candidate_count, 2)
    if len(selected_cards) != expected_selected and not (
        candidate_count >= 1
        and any(item.adjudication == "BROKEN" for item in output.hypotheses)
        and FALLBACK_METHOD_CARD_REF in {item.method_card_ref for item in output.hypotheses}
    ):
        raise ValueError("mingli_agent_candidate_selection_count_invalid")

    decision = output.hypothesis_decision
    primary = next(item for item in output.hypotheses if item.role == "PRIMARY")
    alternative = next(item for item in output.hypotheses if item.role == "ALTERNATIVE")
    if (decision.winner_id, decision.loser_id) != (
        primary.hypothesis_id,
        alternative.hypothesis_id,
    ):
        raise ValueError("mingli_agent_decision_role_conflict")
    for side, hypothesis in (
        (decision.winner, by_id[decision.winner_id]),
        (decision.loser, by_id[decision.loser_id]),
    ):
        allowed_checks = {item.check_code for item in hypothesis.method_rulings}
        if not set(side.decisive_checks).issubset(allowed_checks):
            raise ValueError("mingli_agent_decisive_check_not_in_method_card")
    rank = {"BROKEN": 0, "UNRESOLVED": 1, "CONDITIONAL": 2, "SUPPORTED": 3}
    if rank[primary.adjudication] < rank[alternative.adjudication]:
        raise ValueError("mingli_agent_winner_weaker_than_loser")
    if primary.adjudication == "BROKEN":
        raise ValueError("mingli_agent_broken_primary")
    if primary.adjudication != "SUPPORTED" and output.work_path.closure == "CLOSED":
        raise ValueError("mingli_agent_work_path_closed_without_supported_method")
    if primary.adjudication == "UNRESOLVED" and primary.confidence != "LOW":
        raise ValueError("mingli_agent_working_primary_must_be_low_confidence")
