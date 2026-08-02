from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Any

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.agent_contracts import (
    AgentDayMasterSupportContext,
    AgentEvidenceItem,
    AgentMechanismContext,
    AgentPillarContext,
    AgentRelationContext,
    AgentSourceContext,
    AgentTimingCoordinate,
    MingliAgentCasePacket,
)
from abu_v60.mingli.foundation_runtime import FoundationRuntimeMaps
from abu_v60.mingli.mechanism_contracts import MingliMechanismEvidenceVector
from abu_v60.mingli.quant_contracts import MingliQuantFoundationVector, TenGodOccurrence
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.timing_contracts import MingliTimingEvidenceVector

MINGLI_AGENT_PACKET_COMPILER_VERSION = "v60.mingli-agent-packet-compiler.002"
PILLAR_SLOTS = ("year", "month", "day", "hour")

_ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
_POLARITY_LABELS = {"yin": "阴", "yang": "阳"}
_RELATION_LABELS = {
    "same_branch_membership": "同支",
    "six_clash_membership": "六冲",
    "six_harmony_membership": "六合",
}
_TIMING_LABELS = {"DAYUN": "当前大运", "ANNUAL": "当前流年", "MONTHLY": "当前流月"}
AGENT_TIMING_LAYERS = frozenset({"DAYUN", "ANNUAL"})


class _EvidenceBuilder:
    def __init__(self) -> None:
        self._items: list[AgentEvidenceItem] = []

    @property
    def items(self) -> tuple[AgentEvidenceItem, ...]:
        return tuple(self._items)

    def add(
        self,
        *,
        kind: str,
        statement: str,
        source_refs: Sequence[str],
    ) -> str:
        evidence_id = f"E{len(self._items) + 1:03d}"
        refs = tuple(sorted({str(item) for item in source_refs if str(item)}))
        if not refs:
            raise ValueError("mingli_agent_packet_evidence_requires_source")
        self._items.append(
            AgentEvidenceItem(
                evidence_id=evidence_id,
                kind=kind,
                statement=statement,
                source_refs=refs,
            )
        )
        return evidence_id


class MingliAgentCasePacketCompiler:
    """Compile one chart into the compact dossier used by the Mingli Agent."""

    def __init__(self, authority: KnowledgeAuthority | None = None) -> None:
        self._authority = authority or KnowledgeAuthority()

    def compile(
        self,
        *,
        workspace: Mapping[str, Any],
        reading: MingliReadingEnvelope,
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> MingliAgentCasePacket:
        self._validate_lineage(
            workspace=workspace,
            reading=reading,
            quant_vector=quant_vector,
            mechanism_vector=mechanism_vector,
            timing_vector=timing_vector,
        )
        foundation = FoundationRuntimeMaps.from_profile(
            self._authority.active_foundation_profile()
        )
        builder = _EvidenceBuilder()
        pillars = self._pillars(
            pillar_values=workspace["chart"]["pillars"],
            occurrences=quant_vector.ten_god_occurrences,
            foundation=foundation,
            builder=builder,
        )
        day_master_support = self._day_master_support(
            occurrences=quant_vector.ten_god_occurrences,
            foundation=foundation,
            day_master_stem=quant_vector.day_master_stem,
            day_master_element=quant_vector.day_master_element,
            builder=builder,
        )
        natal_relations = self._natal_relations(
            pillar_values=workspace["chart"]["pillars"],
            chart_version_ref=str(workspace["chart"]["chart_version_ref"]),
            facts=workspace["facts"],
            builder=builder,
        )
        sources = self._sources(
            quant_vector=quant_vector,
            builder=builder,
        )
        mechanisms = self._mechanisms(
            mechanism_vector=mechanism_vector,
            builder=builder,
        )
        timing_coordinates = self._timing_coordinates(
            timing_vector=timing_vector,
            builder=builder,
        )
        timing_relations = self._timing_relations(
            timing_vector=timing_vector,
            builder=builder,
        )
        quant_profile = self._authority.active_quant_foundation_profile()
        element_cycles = tuple(
            (
                f"{_ELEMENT_LABELS[item.element]}生{_ELEMENT_LABELS[item.generates]}，"
                f"{_ELEMENT_LABELS[item.element]}克{_ELEMENT_LABELS[item.controls]}"
            )
            for item in quant_profile.element_cycles
        )
        return MingliAgentCasePacket.issue(
            case_ref=str(workspace["case"]["case_ref"]),
            chart_version_ref=str(workspace["chart"]["chart_version_ref"]),
            life_case_revision_ref=str(
                workspace["life_case"]["life_case_revision_ref"]
            ),
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            subject_kind=str(workspace["case"]["subject_kind"]),
            gender=str(workspace["profile"]["gender"]),
            birth_timezone=str(workspace["profile"]["timezone"]),
            day_master_stem=quant_vector.day_master_stem,
            day_master_element=quant_vector.day_master_element,
            month_command_branch=pillars[1].branch,
            pillars=pillars,
            day_master_support=day_master_support,
            natal_relations=natal_relations,
            source_contexts=sources,
            mechanism_observations=mechanisms,
            timing_analysis_date=timing_vector.analysis_date.isoformat(),
            timing_coordinates=timing_coordinates,
            timing_relations=timing_relations,
            element_cycles=element_cycles,
            evidence_catalog=builder.items,
            interpretation_tasks=(
                "先形成整盘总纲和主要矛盾，不按五行数量直接断旺衰",
                "判断日主状态并说明月令、根位、透藏和全盘配合",
                "比较二至三个格局或机制解释并选定主解释",
                "给出条件化的调候、扶抑、格局、制化或做功取舍",
                "形成有源端、转化、目标、成立和失效条件的主路径",
                "推演性格、事业、财富、关系和家庭的个案化应事",
                "以原局为基线解释当前大运和流年的激活链",
                "形成一幅由本盘结构推出的生命意象",
            ),
        )

    @staticmethod
    def _validate_lineage(
        *,
        workspace: Mapping[str, Any],
        reading: MingliReadingEnvelope,
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> None:
        expected = (
            str(workspace["case"]["case_ref"]),
            str(workspace["chart"]["chart_version_ref"]),
            str(workspace["life_case"]["life_case_revision_ref"]),
        )
        if (
            reading.case_ref,
            reading.chart_version_ref,
            reading.life_case_revision_ref,
        ) != expected:
            raise ValueError("mingli_agent_packet_reading_lineage_mismatch")
        if (quant_vector.case_ref, quant_vector.chart_version_ref) != expected[:2]:
            raise ValueError("mingli_agent_packet_quant_lineage_mismatch")
        if (
            mechanism_vector.case_ref,
            mechanism_vector.chart_version_ref,
            mechanism_vector.quant_vector_ref,
        ) != (*expected[:2], quant_vector.vector_ref):
            raise ValueError("mingli_agent_packet_mechanism_lineage_mismatch")
        if (
            timing_vector.case_ref,
            timing_vector.chart_version_ref,
            timing_vector.life_case_revision_ref,
        ) != expected:
            raise ValueError("mingli_agent_packet_timing_lineage_mismatch")
        if (
            reading.quant_vector_ref,
            reading.mechanism_vector_ref,
            reading.timing_vector_ref,
        ) != (quant_vector.vector_ref, mechanism_vector.vector_ref, timing_vector.vector_ref):
            raise ValueError("mingli_agent_packet_reading_vector_mismatch")

    @staticmethod
    def _pillars(
        *,
        pillar_values: Mapping[str, str],
        occurrences: Sequence[TenGodOccurrence],
        foundation: FoundationRuntimeMaps,
        builder: _EvidenceBuilder,
    ) -> tuple[AgentPillarContext, ...]:
        visible_by_slot = {
            item.pillar_slot: item
            for item in occurrences
            if item.layer == "VISIBLE_STEM"
        }
        hidden_by_slot = {
            slot: tuple(
                sorted(
                    (
                        item
                        for item in occurrences
                        if item.layer == "HIDDEN_STEM" and item.pillar_slot == slot
                    ),
                    key=lambda item: (
                        item.membership_order if item.membership_order is not None else 99
                    ),
                )
            )
            for slot in PILLAR_SLOTS
        }
        result: list[AgentPillarContext] = []
        for slot in PILLAR_SLOTS:
            pillar = str(pillar_values[slot])
            stem, branch = pillar
            visible = visible_by_slot[slot]
            hidden = hidden_by_slot[slot]
            hidden_labels = tuple(item.label for item in hidden)
            hidden_stems = tuple(item.stem for item in hidden)
            evidence_id = builder.add(
                kind="PILLAR",
                statement=(
                    f"{slot}柱{pillar}：明干{stem}为{visible.label}，"
                    f"{_POLARITY_LABELS[foundation.stem_polarity[stem]]}"
                    f"{_ELEMENT_LABELS[foundation.stem_elements[stem]]}；"
                    f"{branch}藏"
                    + "、".join(
                        f"{item.stem}({item.label})" for item in hidden
                    )
                    + "。"
                ),
                source_refs=(
                    visible.occurrence_ref,
                    *visible.evidence_refs,
                    *(item.occurrence_ref for item in hidden),
                    *(ref for item in hidden for ref in item.evidence_refs),
                ),
            )
            result.append(
                AgentPillarContext(
                    slot=slot,
                    pillar=pillar,
                    stem=stem,
                    branch=branch,
                    stem_element=foundation.stem_elements[stem],
                    stem_polarity=foundation.stem_polarity[stem],
                    visible_ten_god=visible.label,
                    hidden_stems=hidden_stems,
                    hidden_ten_gods=hidden_labels,
                    evidence_id=evidence_id,
                )
            )
        return tuple(result)

    @staticmethod
    def _day_master_support(
        *,
        occurrences: Sequence[TenGodOccurrence],
        foundation: FoundationRuntimeMaps,
        day_master_stem: str,
        day_master_element: str,
        builder: _EvidenceBuilder,
    ) -> AgentDayMasterSupportContext:
        hidden = tuple(item for item in occurrences if item.layer == "HIDDEN_STEM")
        same_identity = tuple(
            f"{item.pillar_slot}支藏{item.stem}"
            for item in hidden
            if item.stem == day_master_stem
        )
        same_element = tuple(
            f"{item.pillar_slot}支藏{item.stem}"
            for item in hidden
            if foundation.stem_elements[item.stem] == day_master_element
        )
        visible_peers = tuple(
            f"{item.pillar_slot}干{item.stem}({item.label})"
            for item in occurrences
            if item.layer == "VISIBLE_STEM"
            and item.pillar_slot != "day"
            and item.label in {"比肩", "劫财"}
        )
        resources = tuple(
            f"{item.pillar_slot}{'干' if item.layer == 'VISIBLE_STEM' else '支藏'}"
            f"{item.stem}({item.label})"
            for item in occurrences
            if item.label in {"正印", "偏印"}
        )
        source_refs = tuple(item.occurrence_ref for item in occurrences)
        evidence_id = builder.add(
            kind="SUPPORT",
            statement=(
                f"日主{day_master_stem}的地支同五行藏干支持为"
                f"{('、'.join(same_element) if same_element else '无')}；"
                f"同字藏干为{('、'.join(same_identity) if same_identity else '无')}；"
                f"明干同类为{('、'.join(visible_peers) if visible_peers else '无')}；"
                f"印星生扶为{('、'.join(resources) if resources else '无')}。"
                "印星可生扶日主，但不能称为日主之根。"
            ),
            source_refs=source_refs,
        )
        return AgentDayMasterSupportContext(
            same_identity_hidden_support=same_identity,
            same_element_hidden_support=same_element,
            visible_peer_support=visible_peers,
            resource_support=resources,
            root_language_policy=(
                "ONLY_SAME_ELEMENT_HIDDEN_STEMS_ARE_ROOT_CANDIDATES"
            ),
            evidence_id=evidence_id,
        )

    @staticmethod
    def _natal_relations(
        *,
        pillar_values: Mapping[str, str],
        chart_version_ref: str,
        facts: Sequence[Mapping[str, Any]],
        builder: _EvidenceBuilder,
    ) -> tuple[AgentRelationContext, ...]:
        result: list[AgentRelationContext] = []
        for (left_slot, left_pillar), (right_slot, right_pillar) in combinations(
            ((slot, str(pillar_values[slot])) for slot in PILLAR_SLOTS),
            2,
        ):
            if left_pillar[1] != right_pillar[1]:
                continue
            branch = left_pillar[1]
            evidence_id = builder.add(
                kind="RELATION",
                statement=(
                    f"原局{left_slot}支与{right_slot}支同为{branch}，"
                    "这是同支重复，不自动等于合化或关系作用。"
                ),
                source_refs=(chart_version_ref,),
            )
            result.append(
                AgentRelationContext(
                    relation_type="same_branch_membership",
                    left_layer="NATAL",
                    left_slot=left_slot,
                    left_branch=branch,
                    right_layer="NATAL",
                    right_slot=right_slot,
                    right_branch=branch,
                    evidence_id=evidence_id,
                )
            )
        relation_facts = sorted(
            (
                item
                for item in facts
                if item["fact_type"] in {
                    "six_clash_membership",
                    "six_harmony_membership",
                }
            ),
            key=lambda item: str(item["fact_ref"]),
        )
        for item in relation_facts:
            payload = item["fact_json"]
            relation_type = str(item["fact_type"])
            left_slot = str(payload["left_slot"])
            right_slot = str(payload["right_slot"])
            left_branch = str(payload["left_branch"])
            right_branch = str(payload["right_branch"])
            evidence_id = builder.add(
                kind="RELATION",
                statement=(
                    f"原局{left_slot}支{left_branch}与{right_slot}支{right_branch}"
                    f"构成{_RELATION_LABELS[relation_type]}成员关系。"
                ),
                source_refs=(str(item["fact_ref"]),),
            )
            result.append(
                AgentRelationContext(
                    relation_type=relation_type,
                    left_layer="NATAL",
                    left_slot=left_slot,
                    left_branch=left_branch,
                    right_layer="NATAL",
                    right_slot=right_slot,
                    right_branch=right_branch,
                    evidence_id=evidence_id,
                )
            )
        return tuple(result)

    @staticmethod
    def _sources(
        *,
        quant_vector: MingliQuantFoundationVector,
        builder: _EvidenceBuilder,
    ) -> tuple[AgentSourceContext, ...]:
        result: list[AgentSourceContext] = []
        for item in sorted(
            quant_vector.source_manifestation_evidence,
            key=lambda value: value.evidence_ref,
        ):
            evidence_id = builder.add(
                kind="SOURCE",
                statement=(
                    f"{item.visible_slot}干{item.visible_stem}与"
                    f"{item.source_slot}支{item.source_branch}所藏{item.hidden_stem}"
                    f"形成{item.source_match_kind}来源坐标。"
                ),
                source_refs=(item.evidence_ref, *item.evidence_refs),
            )
            result.append(
                AgentSourceContext(
                    visible_slot=item.visible_slot,
                    visible_stem=item.visible_stem,
                    source_slot=item.source_slot,
                    source_branch=item.source_branch,
                    hidden_stem=item.hidden_stem,
                    match_kind=item.source_match_kind,
                    evidence_id=evidence_id,
                )
            )
        return tuple(result)

    @staticmethod
    def _mechanisms(
        *,
        mechanism_vector: MingliMechanismEvidenceVector,
        builder: _EvidenceBuilder,
    ) -> tuple[AgentMechanismContext, ...]:
        result: list[AgentMechanismContext] = []
        for item in mechanism_vector.candidates:
            roles = tuple(
                (
                    f"{role.role_id}：{','.join(role.occurrence_labels)}，"
                    f"位置{','.join(role.participant_slots)}，"
                    f"明干{role.visible_occurrence_count}/藏干{role.hidden_occurrence_count}"
                )
                for role in item.roles
            )
            evidence_id = builder.add(
                kind="MECHANISM_CANDIDATE",
                statement=(
                    f"系统识别到{item.pattern_label}的结构成员："
                    f"{item.structural_statement}；这只是候选观察，需整盘比较。"
                ),
                source_refs=(
                    item.candidate_ref,
                    *item.support_evidence_refs,
                    *item.context_evidence_refs,
                    *item.counter_evidence_refs,
                ),
            )
            result.append(
                AgentMechanismContext(
                    candidate_ref=item.candidate_ref,
                    pattern_ref=item.pattern_ref,
                    label=item.pattern_label,
                    structural_statement=item.structural_statement,
                    role_summary=roles,
                    blocker_codes=item.blocker_codes,
                    evidence_id=evidence_id,
                )
            )
        return tuple(result)

    @staticmethod
    def _timing_coordinates(
        *,
        timing_vector: MingliTimingEvidenceVector,
        builder: _EvidenceBuilder,
    ) -> tuple[AgentTimingCoordinate, ...]:
        result: list[AgentTimingCoordinate] = []
        for item in timing_vector.coordinates:
            if item.layer not in AGENT_TIMING_LAYERS:
                continue
            bounds = (
                f"，范围{item.start_year}-{item.end_year}"
                if item.start_year is not None and item.end_year is not None
                else ""
            )
            evidence_id = builder.add(
                kind="TIMING",
                statement=(
                    f"{_TIMING_LABELS[item.layer]}为{item.pillar}，"
                    f"天干相对日主为{item.ten_god_label}{bounds}。"
                ),
                source_refs=(item.coordinate_ref, timing_vector.vector_ref),
            )
            result.append(
                AgentTimingCoordinate(
                    layer=item.layer,
                    pillar=item.pillar,
                    ten_god_label=item.ten_god_label,
                    start_year=item.start_year,
                    end_year=item.end_year,
                    evidence_id=evidence_id,
                )
            )
        return tuple(result)

    @staticmethod
    def _timing_relations(
        *,
        timing_vector: MingliTimingEvidenceVector,
        builder: _EvidenceBuilder,
    ) -> tuple[AgentRelationContext, ...]:
        result: list[AgentRelationContext] = []
        for item in sorted(
            timing_vector.relation_evidence,
            key=lambda value: value.evidence_ref,
        ):
            if item.timing_layer not in AGENT_TIMING_LAYERS:
                continue
            evidence_id = builder.add(
                kind="TIMING",
                statement=(
                    f"{_TIMING_LABELS[item.timing_layer]}支{item.timing_branch}与"
                    f"原局{item.natal_slot}支{item.natal_branch}形成"
                    f"{_RELATION_LABELS[item.relation_type]}成员关系。"
                ),
                source_refs=(item.evidence_ref, *item.evidence_refs),
            )
            result.append(
                AgentRelationContext(
                    relation_type=item.relation_type,
                    left_layer=item.timing_layer,
                    left_slot=item.timing_layer.lower(),
                    left_branch=item.timing_branch,
                    right_layer="NATAL",
                    right_slot=item.natal_slot,
                    right_branch=item.natal_branch,
                    evidence_id=evidence_id,
                )
            )
        return tuple(result)
