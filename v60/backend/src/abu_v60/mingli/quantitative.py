from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.knowledge.quant_contracts import BaziQuantFoundationProfile
from abu_v60.mingli.foundation_runtime import FoundationRuntimeMaps
from abu_v60.mingli.quant_contracts import (
    ElementMembershipMeasurement,
    MingliQuantFoundationVector,
    PolarityMembershipMeasurement,
    SourceManifestationEvidence,
    TenGodCount,
    TenGodOccurrence,
)
from abu_v60.provenance import stable_ref

PILLAR_SLOTS = ("year", "month", "day", "hour")
ELEMENT_ORDER = ("wood", "fire", "earth", "metal", "water")
TEN_GOD_ORDER = (
    "比肩",
    "劫财",
    "食神",
    "伤官",
    "偏财",
    "正财",
    "七杀",
    "正官",
    "偏印",
    "正印",
)


def resolve_ten_god(
    *,
    day_stem: str,
    other_stem: str,
    authority: KnowledgeAuthority | None = None,
) -> str:
    knowledge = authority or KnowledgeAuthority()
    foundation = FoundationRuntimeMaps.from_profile(knowledge.active_foundation_profile())
    if day_stem not in foundation.stem_elements:
        raise ValueError("quant_day_stem_not_registered")
    if other_stem not in foundation.stem_elements:
        raise ValueError("quant_other_stem_not_registered")
    return _ten_god(
        day_stem=day_stem,
        other_stem=other_stem,
        foundation=foundation,
        quant_profile=knowledge.active_quant_foundation_profile(),
    )


class MingliQuantFoundationCompiler:
    """Compile deterministic structure measurements from one pinned chart."""

    def __init__(self, authority: KnowledgeAuthority | None = None) -> None:
        self._authority = authority or KnowledgeAuthority()

    def compile(
        self,
        *,
        case_ref: str,
        chart_version_ref: str,
        pillars: Mapping[str, str],
        facts: Sequence[Mapping[str, Any]],
    ) -> MingliQuantFoundationVector:
        if set(pillars) != set(PILLAR_SLOTS):
            raise ValueError("quant_vector_requires_four_pillars")
        foundation = FoundationRuntimeMaps.from_profile(self._authority.active_foundation_profile())
        quant_profile = self._authority.active_quant_foundation_profile()
        fact_index = _FactIndex(facts)
        day_master = pillars["day"][0]

        visible_counts: Counter[str] = Counter()
        hidden_counts: Counter[str] = Counter()
        visible_polarity: Counter[str] = Counter()
        hidden_polarity: Counter[str] = Counter()
        occurrences: list[TenGodOccurrence] = []
        hidden_coordinates: list[tuple[str, str, int, str, str]] = []

        for slot in PILLAR_SLOTS:
            stem, branch = pillars[slot]
            visible_fact_refs = fact_index.visible_refs(
                slot=slot,
                stem=stem,
            )
            visible_counts[foundation.stem_elements[stem]] += 1
            visible_polarity[foundation.stem_polarity[stem]] += 1
            label = (
                "日主"
                if slot == "day"
                else _ten_god(
                    day_stem=day_master,
                    other_stem=stem,
                    foundation=foundation,
                    quant_profile=quant_profile,
                )
            )
            occurrence_identity = {
                "chart_version_ref": chart_version_ref,
                "pillar_slot": slot,
                "layer": "VISIBLE_STEM",
                "stem": stem,
                "label": label,
                "evidence_refs": visible_fact_refs,
            }
            occurrences.append(
                TenGodOccurrence(
                    occurrence_ref=stable_ref(
                        "v60-ten-god-occurrence",
                        occurrence_identity,
                    ),
                    pillar_slot=slot,
                    layer="VISIBLE_STEM",
                    stem=stem,
                    label=label,
                    evidence_refs=visible_fact_refs,
                )
            )
            for order, hidden_stem in enumerate(foundation.hidden_stems[branch]):
                hidden_ref = fact_index.hidden_ref(
                    slot=slot,
                    branch=branch,
                    hidden_stem=hidden_stem,
                    membership_order=order,
                )
                hidden_coordinates.append((slot, branch, order, hidden_stem, hidden_ref))
                hidden_counts[foundation.stem_elements[hidden_stem]] += 1
                hidden_polarity[foundation.stem_polarity[hidden_stem]] += 1
                hidden_label = _ten_god(
                    day_stem=day_master,
                    other_stem=hidden_stem,
                    foundation=foundation,
                    quant_profile=quant_profile,
                )
                hidden_identity = {
                    "chart_version_ref": chart_version_ref,
                    "pillar_slot": slot,
                    "layer": "HIDDEN_STEM",
                    "stem": hidden_stem,
                    "branch": branch,
                    "membership_order": order,
                    "label": hidden_label,
                    "evidence_refs": (hidden_ref,),
                }
                occurrences.append(
                    TenGodOccurrence(
                        occurrence_ref=stable_ref(
                            "v60-ten-god-occurrence",
                            hidden_identity,
                        ),
                        pillar_slot=slot,
                        layer="HIDDEN_STEM",
                        stem=hidden_stem,
                        branch=branch,
                        membership_order=order,
                        label=hidden_label,
                        evidence_refs=(hidden_ref,),
                    )
                )

        hidden_total = sum(hidden_counts.values())
        membership_total = 4 + hidden_total
        element_measurements = tuple(
            ElementMembershipMeasurement(
                element=element,
                visible_stem_count=visible_counts[element],
                hidden_stem_membership_count=hidden_counts[element],
                total_membership_count=visible_counts[element] + hidden_counts[element],
                total_membership_share=round(
                    (visible_counts[element] + hidden_counts[element]) / membership_total,
                    6,
                ),
            )
            for element in ELEMENT_ORDER
        )
        polarity_measurements = tuple(
            PolarityMembershipMeasurement(
                polarity=polarity,
                visible_stem_count=visible_polarity[polarity],
                hidden_stem_membership_count=hidden_polarity[polarity],
                total_membership_count=(visible_polarity[polarity] + hidden_polarity[polarity]),
            )
            for polarity in ("yang", "yin")
        )
        ten_god_counts = _ten_god_counts(occurrences)
        source_evidence = _source_manifestation_evidence(
            chart_version_ref=chart_version_ref,
            pillars=pillars,
            foundation=foundation,
            fact_index=fact_index,
            hidden_coordinates=hidden_coordinates,
        )
        return MingliQuantFoundationVector.issue(
            case_ref=case_ref,
            chart_version_ref=chart_version_ref,
            quant_profile_ref=quant_profile.source_ref,
            quant_profile_hash=quant_profile.profile_hash,
            day_master_stem=day_master,
            day_master_element=foundation.stem_elements[day_master],
            day_master_polarity=foundation.stem_polarity[day_master],
            visible_stem_total=4,
            hidden_stem_membership_total=hidden_total,
            element_measurements=element_measurements,
            polarity_measurements=polarity_measurements,
            ten_god_occurrences=tuple(occurrences),
            ten_god_counts=ten_god_counts,
            source_manifestation_evidence=source_evidence,
            measurement_semantics="DETERMINISTIC_UNWEIGHTED_STRUCTURE",
            calibration_status=quant_profile.calibration_status,
            forbidden_conclusions=quant_profile.forbidden_conclusions,
        )


class _FactIndex:
    def __init__(self, facts: Sequence[Mapping[str, Any]]) -> None:
        self._facts = tuple(facts)

    def visible_refs(self, *, slot: str, stem: str) -> tuple[str, ...]:
        subject = f"pillar:{slot}:stem:{stem}"
        refs = tuple(
            sorted(
                str(fact["fact_ref"])
                for fact in self._facts
                if fact.get("subject_ref") == subject
                and fact.get("fact_type") in {"stem_element", "stem_polarity"}
            )
        )
        if len(refs) != 2:
            raise ValueError(f"quant_visible_stem_facts_incomplete:{slot}")
        return refs

    def hidden_ref(
        self,
        *,
        slot: str,
        branch: str,
        hidden_stem: str,
        membership_order: int,
    ) -> str:
        subject = f"pillar:{slot}:branch:{branch}"
        refs = [
            str(fact["fact_ref"])
            for fact in self._facts
            if fact.get("subject_ref") == subject
            and fact.get("fact_type") == "hidden_stem_membership"
            and fact.get("fact_json", {}).get("hidden_stem") == hidden_stem
            and fact.get("fact_json", {}).get("membership_order") == membership_order
        ]
        if len(refs) != 1:
            raise ValueError(f"quant_hidden_stem_fact_incomplete:{slot}:{membership_order}")
        return refs[0]


def _ten_god(
    *,
    day_stem: str,
    other_stem: str,
    foundation: FoundationRuntimeMaps,
    quant_profile: BaziQuantFoundationProfile,
) -> str:
    day_element = foundation.stem_elements[day_stem]
    other_element = foundation.stem_elements[other_stem]
    generates = {item.element: item.generates for item in quant_profile.element_cycles}
    controls = {item.element: item.controls for item in quant_profile.element_cycles}
    if other_element == day_element:
        relationship = "same_element"
    elif generates[day_element] == other_element:
        relationship = "day_master_generates"
    elif controls[day_element] == other_element:
        relationship = "day_master_controls"
    elif controls[other_element] == day_element:
        relationship = "other_controls_day_master"
    else:
        relationship = "other_generates_day_master"
    same_polarity = foundation.stem_polarity[day_stem] == foundation.stem_polarity[other_stem]
    lookup = {
        (item.relationship, item.same_polarity): item.label
        for item in quant_profile.ten_god_definitions
    }
    return lookup[(relationship, same_polarity)]


def _ten_god_counts(
    occurrences: Sequence[TenGodOccurrence],
) -> tuple[TenGodCount, ...]:
    visible = Counter(
        item.label for item in occurrences if item.layer == "VISIBLE_STEM" and item.label != "日主"
    )
    hidden = Counter(item.label for item in occurrences if item.layer == "HIDDEN_STEM")
    return tuple(
        TenGodCount(
            label=label,
            visible_count=visible[label],
            hidden_membership_count=hidden[label],
        )
        for label in TEN_GOD_ORDER
    )


def _source_manifestation_evidence(
    *,
    chart_version_ref: str,
    pillars: Mapping[str, str],
    foundation: FoundationRuntimeMaps,
    fact_index: _FactIndex,
    hidden_coordinates: Sequence[tuple[str, str, int, str, str]],
) -> tuple[SourceManifestationEvidence, ...]:
    evidence: list[SourceManifestationEvidence] = []
    for visible_slot in PILLAR_SLOTS:
        visible_stem = pillars[visible_slot][0]
        visible_refs = fact_index.visible_refs(
            slot=visible_slot,
            stem=visible_stem,
        )
        visible_element = foundation.stem_elements[visible_stem]
        for source_slot, source_branch, _, hidden_stem, hidden_ref in hidden_coordinates:
            hidden_element = foundation.stem_elements[hidden_stem]
            if hidden_stem == visible_stem:
                match_kind = "EXACT_IDENTITY"
                match_state = "EXACT_IDENTITY_CROSS_LAYER_PRESENT"
            elif hidden_element == visible_element:
                match_kind = "SAME_ELEMENT_DIFFERENT_IDENTITY"
                match_state = "ELEMENTAL_AFFINITY_CROSS_LAYER_PRESENT"
            else:
                continue
            states = [
                "HIDDEN_STEM_MEMBER",
                "SOURCE_COORDINATE_PRESENT",
                "STEM_LAYER_PRESENT",
                match_state,
            ]
            if visible_slot == source_slot:
                states.append("SAME_PILLAR_SOURCE_COORDINATE")
            if source_slot == "month":
                states.append("MONTH_BRANCH_SOURCE_COORDINATE")
            states.append("EFFECT_UNRESOLVED")
            evidence_refs = tuple(sorted((*visible_refs, hidden_ref)))
            identity = {
                "chart_version_ref": chart_version_ref,
                "visible_slot": visible_slot,
                "visible_stem": visible_stem,
                "source_slot": source_slot,
                "source_branch": source_branch,
                "hidden_stem": hidden_stem,
                "source_match_kind": match_kind,
                "evidence_states": states,
                "evidence_refs": evidence_refs,
                "effect_status": "EFFECT_UNRESOLVED",
            }
            evidence.append(
                SourceManifestationEvidence(
                    evidence_ref=stable_ref(
                        "v60-source-manifestation-evidence",
                        identity,
                    ),
                    visible_slot=visible_slot,
                    visible_stem=visible_stem,
                    source_slot=source_slot,
                    source_branch=source_branch,
                    hidden_stem=hidden_stem,
                    source_match_kind=match_kind,
                    evidence_states=tuple(states),
                    evidence_refs=evidence_refs,
                    effect_status="EFFECT_UNRESOLVED",
                )
            )
    return tuple(evidence)
