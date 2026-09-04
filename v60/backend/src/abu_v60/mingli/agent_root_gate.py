from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from abu_v60.mingli.agent_contracts import MingliAgentCasePacket

MINGLI_EFFECTIVE_ROOT_METHOD_VERSION = "v60.mingli-effective-root-method.001"

_RELATION_COMPETITION_TYPES = {
    "six_clash_membership",
    "six_harmony_membership",
}


def root_candidate_assessments(
    *,
    day_master_stem: str,
    pillars: Sequence[Any],
    same_element_candidates: Sequence[str],
    same_identity_candidates: Sequence[str],
    natal_relations: Sequence[Any],
) -> tuple[dict[str, object], ...]:
    """Describe root candidates without turning all candidates into effective roots.

    Only the narrow, high-certainty anti-follow gate is deterministic: an exact
    day-master identity in the first hidden-stem position, with no admitted natal
    clash/harmony membership on that branch, is enough to block a direct follow
    classification.  It says nothing about overall strength, useful deity, path
    availability, or auspiciousness.
    """

    identity_candidates = set(same_identity_candidates)
    assessments: list[dict[str, object]] = []
    for coordinate in same_element_candidates:
        located = _locate_candidate(coordinate=coordinate, pillars=pillars)
        if located is None:
            assessments.append(
                {
                    "coordinate": coordinate,
                    "identity_match": "UNRESOLVED",
                    "hidden_order": None,
                    "hidden_rank": "UNRESOLVED",
                    "branch": None,
                    "relation_competition_evidence_ids": (),
                    "minimum_anti_follow_gate": "NOT_DETERMINED",
                    "gate_reason": "候选坐标未能回到四柱藏干顺序，必须保留未决。",
                }
            )
            continue
        slot, branch, stem, hidden_order = located
        relation_ids = _relation_competition_evidence_ids(
            slot=slot,
            natal_relations=natal_relations,
        )
        exact_identity = coordinate in identity_candidates and stem == day_master_stem
        gate_present = exact_identity and hidden_order == 1 and not relation_ids
        assessments.append(
            {
                "coordinate": coordinate,
                "identity_match": (
                    "EXACT_DAY_MASTER" if exact_identity else "SAME_ELEMENT_DIFFERENT_STEM"
                ),
                "hidden_order": hidden_order,
                "hidden_rank": (
                    "PRIMARY_QI"
                    if hidden_order == 1
                    else "SECONDARY_QI"
                    if hidden_order == 2
                    else "TERTIARY_QI"
                ),
                "branch": branch,
                "relation_competition_evidence_ids": relation_ids,
                "minimum_anti_follow_gate": ("PRESENT" if gate_present else "NOT_DETERMINED"),
                "gate_reason": (
                    "日主同字位于该支第一藏干，且该支没有准入的原局冲合成员关系；"
                    "仅在阻断直接从势的窄范围内，最低有效根成立。"
                    if gate_present
                    else "未同时满足同字、第一藏干与无原局冲合竞争三项，交由整盘裁决。"
                ),
            }
        )
    return tuple(assessments)


def packet_root_candidate_assessments(
    packet: MingliAgentCasePacket,
) -> tuple[dict[str, object], ...]:
    support = packet.day_master_support
    return root_candidate_assessments(
        day_master_stem=packet.day_master_stem,
        pillars=packet.pillars,
        same_element_candidates=support.same_element_hidden_support,
        same_identity_candidates=support.same_identity_hidden_support,
        natal_relations=packet.natal_relations,
    )


def minimum_anti_follow_root_coordinates(
    packet: MingliAgentCasePacket,
) -> tuple[str, ...]:
    return tuple(
        str(item["coordinate"])
        for item in packet_root_candidate_assessments(packet)
        if item["minimum_anti_follow_gate"] == "PRESENT"
    )


def _locate_candidate(
    *,
    coordinate: str,
    pillars: Sequence[Any],
) -> tuple[str, str, str, int] | None:
    for pillar in pillars:
        slot = str(_read(pillar, "slot"))
        branch = str(_read(pillar, "branch"))
        hidden_stems = tuple(str(item) for item in _read(pillar, "hidden_stems"))
        for index, stem in enumerate(hidden_stems, start=1):
            if coordinate == f"{slot}支藏{stem}":
                return slot, branch, stem, index
    return None


def _relation_competition_evidence_ids(
    *,
    slot: str,
    natal_relations: Sequence[Any],
) -> tuple[str, ...]:
    result = {
        str(_read(relation, "evidence_id"))
        for relation in natal_relations
        if str(_read(relation, "relation_type")) in _RELATION_COMPETITION_TYPES
        and slot
        in {
            str(_read(relation, "left_slot")),
            str(_read(relation, "right_slot")),
        }
    }
    return tuple(sorted(result))


def _read(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value[key]
    return getattr(value, key)
