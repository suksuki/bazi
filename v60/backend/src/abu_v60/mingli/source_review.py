from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.quant_contracts import MingliQuantFoundationVector
from abu_v60.mingli.source_review_contracts import (
    MingliSourceCoordinateReviewVector,
    SourceCoordinateReviewEvidence,
    SourceRelationIntersection,
)
from abu_v60.provenance import stable_ref

RELATION_FACT_TYPES = frozenset(
    {
        "six_clash_membership",
        "six_harmony_membership",
    }
)


class MingliSourceCoordinateReviewCompiler:
    """Compile review triggers from admitted relation membership facts."""

    def __init__(self, authority: KnowledgeAuthority | None = None) -> None:
        self._authority = authority or KnowledgeAuthority()

    def compile(
        self,
        *,
        quant_vector: MingliQuantFoundationVector,
        facts: Sequence[Mapping[str, Any]],
    ) -> MingliSourceCoordinateReviewVector:
        profile = self._authority.active_source_review_profile()
        rules = {rule.admitted_fact_type: rule for rule in profile.rules}
        fact_index = {str(item["fact_ref"]): item for item in facts}
        if len(fact_index) != len(facts):
            raise ValueError("source_review_fact_identity_not_unique")
        if any(
            (item.get("case_ref") is not None and item.get("case_ref") != quant_vector.case_ref)
            or (
                item.get("chart_version_ref") is not None
                and item.get("chart_version_ref") != quant_vector.chart_version_ref
            )
            for item in facts
        ):
            raise ValueError("source_review_fact_lineage_mismatch")
        relation_facts = tuple(
            item for item in facts if item.get("fact_type") in RELATION_FACT_TYPES
        )
        reviews = tuple(
            sorted(
                (
                    self._review(
                        source=item,
                        fact_index=fact_index,
                        relation_facts=relation_facts,
                        rules=rules,
                    )
                    for item in quant_vector.source_manifestation_evidence
                ),
                key=lambda item: item.review_ref,
            )
        )
        return MingliSourceCoordinateReviewVector.issue(
            case_ref=quant_vector.case_ref,
            chart_version_ref=quant_vector.chart_version_ref,
            quant_vector_ref=quant_vector.vector_ref,
            quant_vector_hash=quant_vector.vector_hash,
            source_review_profile_ref=profile.source_ref,
            source_review_profile_hash=profile.profile_hash,
            reviews=reviews,
            source_evidence_count=len(reviews),
            exact_identity_count=sum(
                item.source_match_kind == "EXACT_IDENTITY" for item in reviews
            ),
            elemental_affinity_count=sum(
                item.source_match_kind == "SAME_ELEMENT_DIFFERENT_IDENTITY" for item in reviews
            ),
            clear_coordinate_count=sum(not item.relation_intersections for item in reviews),
            review_required_count=sum(bool(item.relation_intersections) for item in reviews),
            six_clash_intersection_count=sum(
                item.relation_type == "six_clash_membership"
                for review in reviews
                for item in review.relation_intersections
            ),
            six_harmony_intersection_count=sum(
                item.relation_type == "six_harmony_membership"
                for review in reviews
                for item in review.relation_intersections
            ),
            unresolved_dimensions=profile.unresolved_dimensions,
            forbidden_conclusions=profile.forbidden_conclusions,
        )

    @staticmethod
    def _review(
        *,
        source: Any,
        fact_index: Mapping[str, Mapping[str, Any]],
        relation_facts: Sequence[Mapping[str, Any]],
        rules: Mapping[str, Any],
    ) -> SourceCoordinateReviewEvidence:
        missing_refs = set(source.evidence_refs) - set(fact_index)
        if missing_refs:
            raise ValueError("source_review_source_evidence_ref_not_found")
        coordinate_ref = f"pillar:{source.source_slot}:branch:{source.source_branch}"
        intersections = tuple(
            sorted(
                (
                    MingliSourceCoordinateReviewCompiler._intersection(
                        source=source,
                        coordinate_ref=coordinate_ref,
                        fact=fact,
                        rule=rules[str(fact["fact_type"])],
                    )
                    for fact in relation_facts
                    if coordinate_ref
                    in {
                        str(fact.get("subject_ref")),
                        str(fact.get("object_ref")),
                    }
                ),
                key=lambda item: item.intersection_ref,
            )
        )
        states = (
            tuple(
                state
                for state in (
                    "SIX_CLASH_COORDINATE_REVIEW_REQUIRED",
                    "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED",
                )
                if state in {item.review_state for item in intersections}
            )
            if intersections
            else ("NO_ADMITTED_RELATION_INTERSECTION",)
        )
        evidence_refs = tuple(
            sorted(
                {
                    *source.evidence_refs,
                    *(item.relation_fact_ref for item in intersections),
                }
            )
        )
        identity = {
            "source_evidence_ref": source.evidence_ref,
            "relation_intersection_refs": tuple(item.intersection_ref for item in intersections),
            "review_states": states,
            "evidence_refs": evidence_refs,
        }
        return SourceCoordinateReviewEvidence(
            review_ref=stable_ref("v60-source-coordinate-review", identity),
            source_evidence_ref=source.evidence_ref,
            visible_slot=source.visible_slot,
            visible_stem=source.visible_stem,
            source_slot=source.source_slot,
            source_branch=source.source_branch,
            hidden_stem=source.hidden_stem,
            source_match_kind=source.source_match_kind,
            relation_intersections=intersections,
            review_states=states,
            evidence_refs=evidence_refs,
            relation_effect_status="UNRESOLVED",
            root_usability_status="UNRESOLVED",
        )

    @staticmethod
    def _intersection(
        *,
        source: Any,
        coordinate_ref: str,
        fact: Mapping[str, Any],
        rule: Any,
    ) -> SourceRelationIntersection:
        payload = fact.get("fact_json")
        if not isinstance(payload, Mapping):
            raise TypeError("source_review_relation_payload_missing")
        if fact.get("authority") != rule.required_authority:
            raise ValueError("source_review_relation_authority_not_admitted")
        if not all(payload.get(claim) is True for claim in rule.required_boolean_claims):
            raise ValueError("source_review_relation_claims_not_admitted")
        left_slot = str(payload.get("left_slot"))
        left_branch = str(payload.get("left_branch"))
        right_slot = str(payload.get("right_slot"))
        right_branch = str(payload.get("right_branch"))
        left_ref = str(fact.get("subject_ref"))
        right_ref = str(fact.get("object_ref"))
        if (
            left_ref != f"pillar:{left_slot}:branch:{left_branch}"
            or right_ref != f"pillar:{right_slot}:branch:{right_branch}"
        ):
            raise ValueError("source_review_relation_coordinate_claim_mismatch")
        if coordinate_ref == left_ref:
            peer_slot = right_slot
            peer_branch = right_branch
        elif coordinate_ref == right_ref:
            peer_slot = left_slot
            peer_branch = left_branch
        else:
            raise ValueError("source_review_relation_coordinate_mismatch")
        identity = {
            "source_evidence_ref": source.evidence_ref,
            "relation_fact_ref": str(fact["fact_ref"]),
            "source_slot": source.source_slot,
            "peer_slot": peer_slot,
            "rule_ref": rule.rule_ref,
        }
        return SourceRelationIntersection(
            intersection_ref=stable_ref(
                "v60-source-relation-intersection",
                identity,
            ),
            relation_fact_ref=str(fact["fact_ref"]),
            relation_type=str(fact["fact_type"]),
            source_slot=source.source_slot,
            source_branch=source.source_branch,
            peer_slot=peer_slot,
            peer_branch=peer_branch,
            rule_ref=rule.rule_ref,
            review_state=rule.review_state,
            effect_status="UNRESOLVED",
        )
