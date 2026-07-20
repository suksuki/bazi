from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any
from uuid import uuid4

from core.engines.bazi.knowledge import BRANCH_ELEMENTS, STEM_ELEMENTS, STEM_POLARITY
from core.life_case import FormalInsight, LifeCase
from core.mingli_agent.contracts import ChartWorldInstance
from experience.canonical_scene import (
    CanonicalProjectionEnvelope,
    CanonicalProjectionKind,
    CanonicalScene,
    CanonicalSceneBundle,
    CanonicalSceneRole,
    CanonicalSceneSource,
    CanonicalTemporalState,
    compile_canonical_projection,
    compile_canonical_scene,
    compile_canonical_scene_bundle,
)
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
from product.agent_case_store import AgentCaseStore


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
MUST_NOT_SAY = [
    "一定会发财",
    "一定会生病",
    "命中注定",
    "保证成功",
]


class CanonicalSceneUnavailable(ValueError):
    pass


class CanonicalSceneOwner:
    """The sole application owner of formal case-to-scene compilation."""

    def __init__(self, *, case_store: AgentCaseStore) -> None:
        self.case_store = case_store

    def issue(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
    ) -> CanonicalSceneBundle:
        scene = self.issue_scene(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        return compile_canonical_scene_bundle(scene)

    def issue_scene(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
    ) -> CanonicalScene:
        row = self.case_store.get(case_id=case_id, user_id=participant_id)
        if row is None:
            raise CanonicalSceneUnavailable("canonical_scene_case_not_found")
        source = canonical_scene_source_from_case_row(case_id=case_id, row=row)
        return compile_canonical_scene(source=source, role=canonical_scene_role(account_role))

    def issue_projection(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        projection_kind: CanonicalProjectionKind,
    ) -> CanonicalProjectionEnvelope:
        scene = self.issue_scene(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        return compile_canonical_projection(scene=scene, kind=projection_kind)

    def issue_experience_envelope(
        self,
        *,
        participant_id: str,
        topic_id: str,
        topic_version: str,
        disclosure_level: str,
        case_id: str | None = None,
        permitted_capabilities: list[str] | None = None,
        account_role: str = "member",
    ) -> MingliExperienceEnvelope:
        """Compatibility projection for the existing Theater runtime contract."""

        row = self.case_store.get(case_id=case_id, user_id=participant_id) if case_id else None
        if case_id and row is None:
            raise ValueError("experience_case_not_found")
        requested = disclosure_level.strip().lower()
        now = datetime.now(timezone.utc)
        facts = pillar_facts_from_world(
            row.get("world") if isinstance(row, dict) else None,
            chart_version_id=_chart_version_from_row(row),
        )
        scene = None
        if row is not None and requested == "approved_insights":
            try:
                source = canonical_scene_source_from_case_row(case_id=str(case_id), row=row)
                scene = compile_canonical_scene(
                    source=source,
                    role=canonical_scene_role(account_role),
                )
            except CanonicalSceneUnavailable:
                scene = None

        if scene is not None:
            mode = "personal_ready"
            scope_disclosure = "approved_insights"
            facts = list(scene.chart_facts)
            claims = list(scene.approved_claims)
            reasoning_steps = list(scene.approved_reasoning_steps)
            hypotheses = list(scene.competing_hypotheses)
            uncertainty = scene.uncertainty
            life_case_version = scene.identity.life_case_version
            chart_version = scene.identity.chart_version_id
            source_hash = scene.identity.source_hash
        elif facts and requested in {"approved_insights", "chart_facts"}:
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
            chart_version = _chart_version_from_row(row)
            source_hash = canonical_hash({
                "case_ref": case_id,
                "chart_version": chart_version,
                "facts": [item.model_dump(mode="json") for item in facts],
            })
        else:
            mode = "observer"
            scope_disclosure = "observer"
            facts = []
            claims = []
            reasoning_steps = []
            hypotheses = []
            uncertainty = EnvelopeUncertainty(
                level="high",
                reasons=["当前参与者未授权任何命盘或案例认知。"],
            )
            life_case_version = None
            chart_version = "observer-no-chart"
            source_hash = canonical_hash({
                "participant_ref": participant_id,
                "topic_id": topic_id,
                "topic_version": topic_version,
                "mode": mode,
            })

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
                chart_version=chart_version,
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
                prohibited_capabilities=[
                    "modify_life_case",
                    "read_reality_evidence",
                    "read_draft_insight",
                    "override_canonical_scene",
                ],
            ),
            allowed_chart_facts=facts,
            approved_claims=claims,
            approved_reasoning_steps=reasoning_steps,
            competing_hypotheses=hypotheses,
            uncertainty=uncertainty,
            must_not_say=MUST_NOT_SAY,
            fallback=EnvelopeFallback(
                mode="chart_facts_only" if facts else "observer",
                allowed_content=["four_pillars"] if facts else ["public_program"],
            ),
        )


def canonical_scene_source_from_case_row(
    *,
    case_id: str,
    row: dict[str, Any],
) -> CanonicalSceneSource:
    world_payload = row.get("world")
    life_case_payload = row.get("life_case")
    if not isinstance(world_payload, dict):
        raise CanonicalSceneUnavailable("canonical_scene_chart_world_required")
    if not isinstance(life_case_payload, dict):
        raise CanonicalSceneUnavailable("canonical_scene_life_case_required")

    try:
        world = ChartWorldInstance.model_validate(world_payload)
        life_case = LifeCase.model_validate(life_case_payload)
    except Exception as exc:  # noqa: BLE001 - boundary converts invalid stored state.
        raise CanonicalSceneUnavailable("canonical_scene_source_invalid") from exc
    baseline = life_case.baseline_insight
    if (
        life_case.case_id != case_id
        or baseline.case_id != case_id
        or baseline.case_version != life_case.case_version
        or life_case.status != "active"
        or not life_case.chart_version.active
        or baseline.status != "committed"
        or baseline.epistemic_state not in {"reliable", "competing"}
    ):
        raise CanonicalSceneUnavailable("canonical_scene_formal_life_case_unavailable")
    if world.world_id != life_case.chart_version.world_id:
        raise CanonicalSceneUnavailable("canonical_scene_world_version_mismatch")

    facts = pillar_facts_from_world(
        world.model_dump(mode="json"),
        chart_version_id=life_case.chart_version.version_id,
    )
    if len(facts) != 4:
        raise CanonicalSceneUnavailable("canonical_scene_four_pillars_required")
    claims = [_approved_claim(baseline, category="baseline")]
    reasoning = _approved_reasoning_steps(baseline)
    for domain in sorted(life_case.domain_insights):
        committed = next(
            (item for item in reversed(life_case.domain_insights[domain]) if item.status == "committed"),
            None,
        )
        if committed is None:
            continue
        claims.append(_approved_claim(committed, category=f"domain:{domain}"))
        reasoning.extend(_approved_reasoning_steps(committed))

    active_snapshots = [item for item in life_case.temporal_snapshots if item.status == "active"]
    timing = world.timing_context
    temporal_refs = [item.snapshot_id for item in active_snapshots]
    source_refs = list(dict.fromkeys([
        f"world:{world.world_id}",
        f"chart-version:{life_case.chart_version.version_id}",
        f"life-case:{life_case.life_case_id}:{life_case.case_version}",
        baseline.insight_id,
        *(item.claim_ref for item in claims[1:]),
        *temporal_refs,
    ]))
    selected_snapshot = active_snapshots[-1] if active_snapshots else None
    return CanonicalSceneSource(
        case_ref=case_id,
        chart_version_id=life_case.chart_version.version_id,
        chart_hash=life_case.chart_version.chart_hash,
        world_id=world.world_id,
        life_case_id=life_case.life_case_id,
        life_case_version=life_case.case_version,
        source_updated_at=_parse_datetime(life_case.updated_at),
        chart_facts=facts,
        approved_claims=claims,
        approved_reasoning_steps=reasoning,
        competing_hypotheses=_competing_hypotheses(baseline),
        temporal_state=CanonicalTemporalState(
            temporal_snapshot_refs=temporal_refs,
            selected_period=selected_snapshot.period_key if selected_snapshot else "",
            luck_pillar=str(timing.get("luck_pillar") or ""),
            luck_year_range=[
                int(item)
                for item in (timing.get("luck_year_range") or [])[:2]
                if isinstance(item, int) or str(item).isdigit()
            ],
            annual_pillar=str(timing.get("annual_pillar") or ""),
            analysis_year=(
                int(timing["analysis_year"])
                if timing.get("analysis_year") is not None
                and str(timing.get("analysis_year")).isdigit()
                else None
            ),
            validation_status=str(timing.get("validation_status") or "unavailable"),
            publicly_supported=bool(timing.get("publicly_supported")),
            source_refs=list(dict.fromkeys([
                *(str(item) for item in timing.get("calculation_refs") or []),
                *temporal_refs,
            ])),
        ),
        uncertainty=EnvelopeUncertainty(
            level=baseline.uncertainty.level,
            reasons=baseline.uncertainty.reasons,
        ),
        must_not_say=MUST_NOT_SAY,
        source_refs=source_refs,
    )


def canonical_scene_role(account_role: str) -> CanonicalSceneRole:
    return {
        "admin": "admin",
        "research_master": "research",
        "research": "research",
        "practitioner": "practitioner",
        "member": "member",
    }.get(str(account_role).strip().lower(), "guest")  # type: ignore[return-value]


def pillar_facts_from_world(
    world: Any,
    *,
    chart_version_id: str,
) -> list[AllowedChartFact]:
    if not isinstance(world, dict):
        return []
    pillars = _world_pillars(world)
    if len(pillars) != 4:
        return []
    labels = ("年柱", "月柱", "日柱", "时柱")
    slots = ("year", "month", "day", "hour")
    hidden_rows = _hidden_stem_rows(world)
    visible_ten_gods = _visible_ten_gods(world)
    return [
        AllowedChartFact(
            fact_ref=f"chart:{chart_version_id}:pillar:{slots[index]}",
            fact_type="pillar",
            display_value=f"{labels[index]} {value}",
            visual_anchor=f"baseline-pillar-{index}",
            pillar_slot=slots[index],
            pillar_label=labels[index],
            stem=value[0],
            branch=value[1],
            stem_element=STEM_ELEMENTS.get(value[0], ""),
            stem_polarity=STEM_POLARITY.get(value[0], ""),
            branch_element=BRANCH_ELEMENTS.get(value[1], ""),
            branch_polarity=_branch_polarity(value[1]),
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


def _approved_claim(insight: FormalInsight, *, category: str) -> ApprovedClaim:
    certainty = {"low": "high", "medium": "medium", "high": "low"}[
        insight.uncertainty.level
    ]
    return ApprovedClaim(
        claim_ref=insight.insight_id,
        category=category,
        approved_meaning=insight.claim,
        spoken_summary=insight.claim,
        subtitle_summary=insight.claim,
        certainty=certainty,
        conditions=insight.conditions,
        counter_signals=insight.counter_signals,
        temporal_scope=str(
            insight.scope.get("temporal_scope")
            or insight.scope.get("temporal_activation")
            or "natal"
        ),
        evidence_refs=list(dict.fromkeys([
            *insight.basis.chart_fact_refs,
            *insight.basis.holistic_belief_refs,
            *insight.basis.temporal_activation_refs,
        ])),
        visual_anchors=[
            f"{insight.insight_id}.reasoning.{index}"
            for index, _ in enumerate(insight.reasoning_path[:6])
        ],
    )


def _approved_reasoning_steps(insight: FormalInsight) -> list[ApprovedReasoningStep]:
    return [
        ApprovedReasoningStep(
            step_ref=f"{insight.insight_id}.reasoning.{index}",
            premise=_public_reasoning_text(step.premise),
            conclusion=_public_reasoning_text(step.conclusion),
            source_refs=step.source_refs,
            visual_anchor=f"{insight.insight_id}.reasoning.{index}",
        )
        for index, step in enumerate(insight.reasoning_path[:6])
    ]


def _competing_hypotheses(insight: FormalInsight) -> list[CompetingHypothesis]:
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


def _public_reasoning_text(value: str) -> str:
    text = re.sub(r"[（(]\s*(?:[FO]\d{3}\s*[,，、]?\s*)+[）)]", "", value)
    parts = [part.strip() for part in text.split("→")]
    parts = [part for part in parts if part and not re.fullmatch(r"[FO]\d{3}", part)]
    text = " → ".join(parts)
    text = re.sub(r"\s+([，。；：])", r"\1", text)
    return " ".join(text.split()).strip(" →")


def _world_pillars(world: dict[str, Any]) -> list[str]:
    direct = world.get("pillars")
    if isinstance(direct, list) and len(direct) == 4:
        return [str(item) for item in direct if len(str(item)) >= 2]
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


def _chart_version_from_row(row: dict[str, Any] | None) -> str:
    life_case = row.get("life_case") if isinstance(row, dict) else None
    if isinstance(life_case, dict):
        chart_version = life_case.get("chart_version")
        if isinstance(chart_version, dict) and chart_version.get("version_id"):
            return str(chart_version["version_id"])
    world = row.get("world") if isinstance(row, dict) else None
    return str(world.get("world_id") or "chart-facts-unversioned") if isinstance(world, dict) else "observer-no-chart"


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CanonicalSceneUnavailable("canonical_scene_timestamp_invalid") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
