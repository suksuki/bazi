from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.calendar import CALENDAR_ENGINE_VERSION, BirthInput, ChartPillars
from abu_v60.mingli.foundation_runtime import FoundationRuntimeMaps
from abu_v60.provenance import content_hash, stable_ref

PILLAR_SLOTS = ("year", "month", "day", "hour")


@dataclass(frozen=True, slots=True)
class CompiledCase:
    chart_version_ref: str
    chart_hash: str
    pillars: dict[str, str]
    facts: tuple[dict[str, Any], ...]
    life_case_revision_ref: str
    life_case_hash: str
    life_case_payload: dict[str, Any]
    evidence_manifest: dict[str, Any]
    scene_ref: str
    scene_hash: str
    scene_payload: dict[str, Any]


def compile_case(
    *,
    case_ref: str,
    birth_input: BirthInput,
    chart: ChartPillars,
    knowledge: KnowledgeAuthority | None = None,
) -> CompiledCase:
    foundation = FoundationRuntimeMaps.from_profile(
        (knowledge or KnowledgeAuthority()).active_foundation_profile()
    )
    pillars = dict(zip(PILLAR_SLOTS, chart.ordered(), strict=True))
    chart_payload = {
        "case_ref": case_ref,
        "version": 1,
        "birth_input_hash": birth_input.input_hash,
        "pillars": pillars,
        "algorithm_version": CALENDAR_ENGINE_VERSION,
    }
    chart_hash = content_hash(chart_payload)
    chart_ref = stable_ref("v60-chart", chart_payload)
    facts = tuple(
        _compile_facts(
            case_ref=case_ref,
            chart_ref=chart_ref,
            pillars=pillars,
            foundation=foundation,
        )
    )
    fact_refs = [fact["fact_ref"] for fact in facts]

    life_case_payload = {
        "case_ref": case_ref,
        "chart_version_ref": chart_ref,
        "revision": 1,
        "status": "BOUNDED_BASELINE",
        "day_stem": pillars["day"][0],
        "day_element": foundation.stem_elements[pillars["day"][0]],
        "fact_refs": fact_refs,
        "unresolved": [
            "strength",
            "usable_root",
            "mechanism",
            "effective_work",
            "life_outcomes",
        ],
        "professional_boundary": {
            "allowed": [
                "pillar_identity",
                "stem_element",
                "stem_polarity",
                "hidden_stem_membership",
                "six_clash_membership",
                "six_harmony_membership",
            ],
            "forbidden": list(foundation.forbidden_inferences),
        },
    }
    evidence_manifest = {
        "chart_version_ref": chart_ref,
        "fact_refs": fact_refs,
        "profile_source_ref": foundation.profile_source_ref,
        "all_conclusions_bounded": True,
    }
    life_case_hash = content_hash(
        {"payload": life_case_payload, "evidence_manifest": evidence_manifest}
    )
    life_case_ref = stable_ref("v60-lifecase", life_case_hash)

    phenotype = _tree_phenotype(
        pillars=pillars,
        foundation=foundation,
    )
    scene_payload = {
        "case_ref": case_ref,
        "life_case_revision_ref": life_case_ref,
        "scene_version": 1,
        "tree_phenotype": phenotype,
        "projection_notice": (
            "Visual metaphor derived from bounded deterministic facts; "
            "not a strength or outcome judgment."
        ),
        "evidence_refs": fact_refs,
    }
    scene_hash = content_hash(scene_payload)
    scene_ref = stable_ref("v60-scene", scene_hash)
    return CompiledCase(
        chart_version_ref=chart_ref,
        chart_hash=chart_hash,
        pillars=pillars,
        facts=facts,
        life_case_revision_ref=life_case_ref,
        life_case_hash=life_case_hash,
        life_case_payload=life_case_payload,
        evidence_manifest=evidence_manifest,
        scene_ref=scene_ref,
        scene_hash=scene_hash,
        scene_payload=scene_payload,
    )


def _compile_facts(
    *,
    case_ref: str,
    chart_ref: str,
    pillars: dict[str, str],
    foundation: FoundationRuntimeMaps,
) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for slot, pillar in pillars.items():
        stem, branch = pillar
        facts.append(
            _fact(
                case_ref,
                chart_ref,
                "pillar_identity",
                f"pillar:{slot}",
                None,
                {"slot": slot, "pillar": pillar, "stem": stem, "branch": branch},
                foundation,
            )
        )
        facts.append(
            _fact(
                case_ref,
                chart_ref,
                "stem_element",
                f"pillar:{slot}:stem:{stem}",
                f"element:{foundation.stem_elements[stem]}",
                {"stem": stem, "element": foundation.stem_elements[stem]},
                foundation,
            )
        )
        facts.append(
            _fact(
                case_ref,
                chart_ref,
                "stem_polarity",
                f"pillar:{slot}:stem:{stem}",
                f"polarity:{foundation.stem_polarity[stem]}",
                {"stem": stem, "polarity": foundation.stem_polarity[stem]},
                foundation,
            )
        )
        for index, hidden_stem in enumerate(foundation.hidden_stems[branch]):
            facts.append(
                _fact(
                    case_ref,
                    chart_ref,
                    "hidden_stem_membership",
                    f"pillar:{slot}:branch:{branch}",
                    f"hidden-stem:{hidden_stem}",
                    {
                        "branch": branch,
                        "hidden_stem": hidden_stem,
                        "membership_order": index,
                        "effect_not_inferred": True,
                    },
                    foundation,
                )
            )

    branch_slots = [(slot, pillar[1]) for slot, pillar in pillars.items()]
    for (left_slot, left), (right_slot, right) in combinations(branch_slots, 2):
        pair = frozenset((left, right))
        relation_type = (
            "six_clash_membership"
            if pair in foundation.six_clash
            else "six_harmony_membership"
            if pair in foundation.six_harmony
            else None
        )
        if relation_type is None:
            continue
        facts.append(
            _fact(
                case_ref,
                chart_ref,
                relation_type,
                f"pillar:{left_slot}:branch:{left}",
                f"pillar:{right_slot}:branch:{right}",
                {
                    "left_branch": left,
                    "right_branch": right,
                    "left_slot": left_slot,
                    "right_slot": right_slot,
                    "membership_only": True,
                    "effect_not_inferred": True,
                },
                foundation,
            )
        )
    return facts


def _fact(
    case_ref: str,
    chart_ref: str,
    fact_type: str,
    subject_ref: str,
    object_ref: str | None,
    payload: dict[str, Any],
    foundation: FoundationRuntimeMaps,
) -> dict[str, Any]:
    identity = {
        "case_ref": case_ref,
        "chart_version_ref": chart_ref,
        "fact_type": fact_type,
        "subject_ref": subject_ref,
        "object_ref": object_ref,
        "payload": payload,
        "source_ref": foundation.profile_source_ref,
    }
    return {
        "fact_ref": stable_ref("v60-fact", identity),
        "fact_type": fact_type,
        "subject_ref": subject_ref,
        "object_ref": object_ref,
        "authority": "SYSTEM_DETERMINISTIC_BOUNDED",
        "fact_json": payload,
        "source_ref": foundation.profile_source_ref,
        "fact_hash": content_hash(identity),
    }


def _tree_phenotype(
    *,
    pillars: dict[str, str],
    foundation: FoundationRuntimeMaps,
) -> dict[str, Any]:
    counts = {element: 0 for element in ("wood", "fire", "earth", "metal", "water")}
    for pillar in pillars.values():
        counts[foundation.stem_elements[pillar[0]]] += 2
        for hidden_stem in foundation.hidden_stems[pillar[1]]:
            counts[foundation.stem_elements[hidden_stem]] += 1
    total = sum(counts.values())
    normalized = {key: round(value / total, 4) for key, value in counts.items()}
    return {
        "profile_version": "v60.life-tree-phenotype.bounded-facts.v1",
        "fact_basis": "visible_stems_plus_unweighted_hidden_stem_membership",
        "element_membership_ratios": normalized,
        "crown_spread": round(0.88 + normalized["wood"] * 0.36, 4),
        "branch_lift": round(0.84 + normalized["fire"] * 0.42, 4),
        "root_spread": round(0.86 + normalized["earth"] * 0.38, 4),
        "bark_definition": round(0.82 + normalized["metal"] * 0.44, 4),
        "surface_moisture": round(0.8 + normalized["water"] * 0.46, 4),
        "semantic_status": "VISUAL_METAPHOR_ONLY",
    }
