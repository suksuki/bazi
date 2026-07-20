from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any
from uuid import uuid4

from product.agent_case_store import AgentCaseStore
from core.engines.bazi.knowledge import BRANCH_ELEMENTS, STEM_ELEMENTS, STEM_POLARITY
from core.life_case import LifeCase
from experience.compiler import canonical_hash
from experience.contracts import (
    AllowedChartFact,
    ApprovedClaim,
    ApprovedReasoningStep,
    CompetingHypothesis,
    EnvelopeFallback,
    EnvelopeSource,
    EnvelopeUncertainty,
    HiddenStemFact,
    MingliExperienceEnvelope,
    ParticipantScope,
    TopicScope,
)


TEN_GOD_LABELS = {
    "bi_jian": "比肩",
    "jie_cai": "劫财",
    "shi_shen": "食神",
    "shang_guan": "伤官",
    "pian_cai": "偏财",
    "zheng_cai": "正财",
    "qi_sha": "七杀",
    "zheng_guan": "正官",
    "pian_yin": "偏印",
    "zheng_yin": "正印",
}


class ProductExperienceEnvelopePort:
    """Application adapter that projects LifeCase into minimal experience data."""

    def __init__(self, *, case_store: AgentCaseStore) -> None:
        self.case_store = case_store

    def issue_envelope(
        self,
        *,
        participant_id: str,
        topic_id: str,
        topic_version: str,
        disclosure_level: str,
        case_id: str | None = None,
        permitted_capabilities: list[str] | None = None,
    ) -> MingliExperienceEnvelope:
        row = self.case_store.get(case_id=case_id, user_id=participant_id) if case_id else None
        if case_id and row is None:
            raise ValueError("experience_case_not_found")
        now = datetime.now(timezone.utc)
        world = row.get("world") if isinstance(row, dict) else None
        pillars = _pillar_facts(world)
        life_case = _active_life_case(row)
        requested = disclosure_level.strip().lower()

        if life_case and requested == "approved_insights":
            mode = "personal_ready"
            scope_disclosure = "approved_insights"
            reasoning_steps = _approved_reasoning_steps(life_case)
            claims = [_approved_baseline_claim(life_case, reasoning_steps=reasoning_steps)]
            hypotheses = _competing_hypotheses(life_case)
            uncertainty = EnvelopeUncertainty(
                level=life_case.baseline_insight.uncertainty.level,
                reasons=life_case.baseline_insight.uncertainty.reasons,
            )
            life_case_version = life_case.case_version
        elif pillars and requested in {"approved_insights", "chart_facts"}:
            mode = "chart_facts_only"
            scope_disclosure = "chart_facts"
            claims = []
            reasoning_steps = []
            hypotheses = []
            uncertainty = EnvelopeUncertainty(
                level="high",
                reasons=["可靠排盘已经建立，但正式整盘认知尚未写入 LifeCase。"],
            )
            life_case_version = None
        else:
            mode = "observer"
            scope_disclosure = "observer"
            pillars = []
            claims = []
            reasoning_steps = []
            hypotheses = []
            uncertainty = EnvelopeUncertainty(
                level="high",
                reasons=["当前参与者未授权任何命盘或案例认知。"],
            )
            life_case_version = None

        source_projection = {
            "participant_ref": participant_id,
            "topic_id": topic_id,
            "topic_version": topic_version,
            "chart_version": _chart_version(life_case, world),
            "life_case_version": life_case_version,
            "pillars": [item.model_dump(mode="json") for item in pillars],
            "claims": [item.model_dump(mode="json") for item in claims],
            "reasoning_steps": [item.model_dump(mode="json") for item in reasoning_steps],
            "hypotheses": [item.model_dump(mode="json") for item in hypotheses],
        }
        source_hash = canonical_hash(source_projection)
        return MingliExperienceEnvelope(
            envelope_id=f"envelope-{uuid4().hex[:20]}",
            mode=mode,
            participant_scope=ParticipantScope(
                participant_ref=participant_id,
                privacy_level="account" if not participant_id.startswith("guest-") else "anonymous",
                disclosure_level=scope_disclosure,
                language="zh-CN",
            ),
            source=EnvelopeSource(
                chart_version=_chart_version(life_case, world),
                life_case_version=life_case_version,
                case_ref=case_id if row else None,
                generated_at=now,
                expires_at=now + timedelta(hours=24),
                source_hash=source_hash,
            ),
            topic_scope=TopicScope(
                topic_id=topic_id,
                topic_version=topic_version,
                permitted_capabilities=list(dict.fromkeys([
                    "private_scene",
                    "frozen_cue",
                    "approved_reasoning_path",
                    "topic_exploration",
                    *(permitted_capabilities or []),
                ])),
                prohibited_capabilities=["modify_life_case", "read_reality_evidence", "read_draft_insight"],
            ),
            allowed_chart_facts=pillars,
            approved_claims=claims,
            approved_reasoning_steps=reasoning_steps,
            competing_hypotheses=hypotheses,
            uncertainty=uncertainty,
            must_not_say=[
                "一定会发财",
                "一定会生病",
                "命中注定",
                "保证成功",
            ],
            fallback=EnvelopeFallback(
                mode="chart_facts_only" if pillars else "observer",
                allowed_content=["four_pillars"] if pillars else ["public_program"],
            ),
        )


def _active_life_case(row: dict[str, Any] | None) -> LifeCase | None:
    payload = row.get("life_case") if isinstance(row, dict) else None
    if not isinstance(payload, dict):
        return None
    life_case = LifeCase.model_validate(payload)
    insight = life_case.baseline_insight
    if (
        life_case.status != "active"
        or not life_case.chart_version.active
        or insight.status != "committed"
        or insight.epistemic_state not in {"reliable", "competing"}
    ):
        return None
    return life_case


def _pillar_facts(world: Any) -> list[AllowedChartFact]:
    if not isinstance(world, dict):
        return []
    pillars = _world_pillars(world)
    if not isinstance(pillars, list) or len(pillars) != 4:
        return []
    labels = ("年柱", "月柱", "日柱", "时柱")
    slots = ("year", "month", "day", "hour")
    hidden_rows = _hidden_stem_rows(world)
    visible_ten_gods = _visible_ten_gods(world)
    return [
        AllowedChartFact(
            fact_ref=f"chart.pillar.{index}",
            fact_type="pillar",
            display_value=f"{labels[index]} {str(value)}",
            visual_anchor=f"baseline-pillar-{index}",
            pillar_slot=slots[index],
            pillar_label=labels[index],
            stem=str(value)[0] if len(str(value)) >= 1 else "",
            branch=str(value)[1] if len(str(value)) >= 2 else "",
            stem_element=STEM_ELEMENTS.get(str(value)[:1], ""),
            stem_polarity=STEM_POLARITY.get(str(value)[:1], ""),
            branch_element=BRANCH_ELEMENTS.get(str(value)[1:2], ""),
            branch_polarity=_branch_polarity(str(value)[1:2]),
            visible_ten_god=(
                "日主"
                if index == 2
                else _ten_god_label(visible_ten_gods.get(slots[index], ""))
            ),
            hidden_stems=[
                HiddenStemFact(
                    stem=str(stem),
                    ten_god=_ten_god_label(
                        (hidden_rows.get(slots[index], {}).get("ten_gods") or {}).get(str(stem), "")
                    ),
                    element=STEM_ELEMENTS.get(str(stem), ""),
                    polarity=STEM_POLARITY.get(str(stem), ""),
                )
                for stem in hidden_rows.get(slots[index], {}).get("stems", [])
            ],
        )
        for index, value in enumerate(pillars)
    ]


def _world_pillars(world: dict[str, Any]) -> list[str]:
    direct = world.get("pillars")
    if isinstance(direct, list) and len(direct) == 4:
        return [str(item) for item in direct]
    for fact in world.get("facts") or []:
        if not isinstance(fact, dict):
            continue
        payload = fact.get("payload") or {}
        values = payload.get("pillars") if isinstance(payload, dict) else None
        if isinstance(values, dict):
            ordered = [values.get(slot) for slot in ("year", "month", "day", "hour")]
            if all(ordered):
                return [str(item) for item in ordered]
        if isinstance(values, list) and len(values) == 4:
            return [str(item) for item in values]
    return []


def _hidden_stem_rows(world: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for fact in world.get("facts") or []:
        if not isinstance(fact, dict) or fact.get("category") != "hidden_stems":
            continue
        payload = fact.get("payload") or {}
        for row in payload.get("rows") or []:
            if not isinstance(row, dict) or not row.get("slot"):
                continue
            stems = [str(item) for item in row.get("hidden_stems") or []]
            gods = [str(item) for item in row.get("hidden_ten_gods") or []]
            output[str(row["slot"])] = {
                "stems": stems,
                "ten_gods": dict(zip(stems, gods, strict=False)),
            }
    return output


def _visible_ten_gods(world: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    for fact in world.get("facts") or []:
        if not isinstance(fact, dict) or fact.get("category") != "visible":
            continue
        payload = fact.get("payload") or {}
        for row in payload.get("visible_ten_gods") or []:
            if isinstance(row, dict) and row.get("slot"):
                output[str(row["slot"])] = str(row.get("ten_god") or "")
    return output


def _branch_polarity(branch: str) -> str:
    return {
        "子": "yang", "丑": "yin", "寅": "yang", "卯": "yin",
        "辰": "yang", "巳": "yin", "午": "yang", "未": "yin",
        "申": "yang", "酉": "yin", "戌": "yang", "亥": "yin",
    }.get(branch, "")


def _ten_god_label(value: str) -> str:
    return TEN_GOD_LABELS.get(value, value)


def _approved_baseline_claim(
    life_case: LifeCase,
    *,
    reasoning_steps: list[ApprovedReasoningStep],
) -> ApprovedClaim:
    insight = life_case.baseline_insight
    certainty = {"low": "high", "medium": "medium", "high": "low"}[insight.uncertainty.level]
    return ApprovedClaim(
        claim_ref=insight.insight_id,
        category="baseline",
        approved_meaning=insight.claim,
        spoken_summary=insight.claim,
        subtitle_summary=insight.claim,
        certainty=certainty,
        conditions=insight.conditions,
        counter_signals=insight.counter_signals,
        temporal_scope=str(insight.scope.get("temporal_scope") or "natal"),
        evidence_refs=[
            *insight.basis.chart_fact_refs,
            *insight.basis.holistic_belief_refs,
            *insight.basis.temporal_activation_refs,
        ],
        visual_anchors=[item.visual_anchor for item in reasoning_steps],
    )


def _approved_reasoning_steps(life_case: LifeCase) -> list[ApprovedReasoningStep]:
    insight = life_case.baseline_insight
    return [
        ApprovedReasoningStep(
            step_ref=f"{insight.insight_id}.reasoning.{index}",
            premise=_public_reasoning_text(step.premise),
            conclusion=_public_reasoning_text(step.conclusion),
            source_refs=step.source_refs,
            visual_anchor=f"reasoning-step-{index}",
        )
        for index, step in enumerate(insight.reasoning_path[:6])
    ]


def _public_reasoning_text(value: str) -> str:
    """Remove internal evidence IDs without rewriting the approved meaning."""

    text = re.sub(r"[（(]\s*(?:[FO]\d{3}\s*[,，、]?\s*)+[）)]", "", value)
    parts = [part.strip() for part in text.split("→")]
    parts = [part for part in parts if part and not re.fullmatch(r"[FO]\d{3}", part)]
    text = " → ".join(parts)
    text = re.sub(r"\s+([，。；：])", r"\1", text)
    return " ".join(text.split()).strip(" →")


def _competing_hypotheses(life_case: LifeCase) -> list[CompetingHypothesis]:
    insight = life_case.baseline_insight
    return [
        CompetingHypothesis(
            hypothesis_ref=f"{insight.insight_id}.alternative.{index}",
            approved_meaning=text,
            supporting_refs=insight.basis.holistic_belief_refs,
            unresolved_reason="仍需现实反馈区分主解释与竞争解释。",
        )
        for index, text in enumerate(insight.uncertainty.competing_hypotheses[:3])
        if text.strip()
    ]


def _chart_version(life_case: LifeCase | None, world: Any) -> str:
    if life_case:
        return life_case.chart_version.version_id
    if isinstance(world, dict):
        return str(world.get("world_id") or "chart-facts-unversioned")
    return "observer-no-chart"
