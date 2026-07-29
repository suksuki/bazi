from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.mingli.mechanism_contracts import (
    MechanismCandidateEvidence,
    MechanismRoleEvidence,
    MingliMechanismEvidenceVector,
)
from abu_v60.mingli.mechanism_depth_contracts import (
    MECHANISM_EVIDENCE_CHANNEL_ORDER,
    MECHANISM_UNRESOLVED_DIMENSIONS,
    CandidateMechanismEvidenceDepth,
    MechanismRoleEvidenceDepth,
    MechanismSharedParticipantDepth,
    MechanismTimingOverlapDepth,
    MechanismTimingRelationDepth,
    MingliMechanismEvidenceDepthEnvelope,
)
from abu_v60.mingli.quant_contracts import (
    MingliQuantFoundationVector,
    SourceManifestationEvidence,
    TenGodOccurrence,
)
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.timing_contracts import MingliTimingEvidenceVector


class MingliMechanismEvidenceDepthProjector:
    """Organize existing evidence without inferring strength, effect, or rank."""

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
        mechanism_comparison: Mapping[str, Any],
    ) -> MingliMechanismEvidenceDepthEnvelope:
        self._validate_lineage(
            reading=reading,
            quant_vector=quant_vector,
            mechanism_vector=mechanism_vector,
            timing_vector=timing_vector,
        )
        selected_ref = mechanism_comparison.get("selected_candidate_ref")
        if selected_ref is not None:
            selected_ref = str(selected_ref)
            if selected_ref not in {item.candidate_ref for item in mechanism_vector.candidates}:
                raise ValueError("mechanism_depth_selected_candidate_not_in_vector")
        occurrence_index = {item.occurrence_ref: item for item in quant_vector.ten_god_occurrences}
        source_index = {
            item.evidence_ref: item for item in quant_vector.source_manifestation_evidence
        }
        candidate_index = {item.candidate_ref: item for item in mechanism_vector.candidates}
        selected_competitors = (
            set(candidate_index[selected_ref].competing_candidate_refs)
            if selected_ref is not None
            else set()
        )
        candidates = tuple(
            self._candidate(
                candidate=candidate,
                attention_status=(
                    "PRIMARY_ATTENTION"
                    if candidate.candidate_ref == selected_ref
                    else "DIRECT_COMPETITOR"
                    if candidate.candidate_ref in selected_competitors
                    else "UNRANKED"
                ),
                occurrence_index=occurrence_index,
                source_index=source_index,
                candidate_index=candidate_index,
                timing_vector=timing_vector,
            )
            for candidate in mechanism_vector.candidates
        )
        return MingliMechanismEvidenceDepthEnvelope.issue(
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            case_ref=reading.case_ref,
            chart_version_ref=reading.chart_version_ref,
            quant_vector_ref=quant_vector.vector_ref,
            quant_vector_hash=quant_vector.vector_hash,
            mechanism_vector_ref=mechanism_vector.vector_ref,
            mechanism_vector_hash=mechanism_vector.vector_hash,
            timing_vector_ref=timing_vector.vector_ref,
            timing_vector_hash=timing_vector.vector_hash,
            selected_attention_candidate_ref=selected_ref,
            candidates=tuple(sorted(candidates, key=lambda item: item.candidate_ref)),
        )

    @staticmethod
    def _validate_lineage(
        *,
        reading: MingliReadingEnvelope,
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> None:
        if (
            len(
                {
                    reading.case_ref,
                    quant_vector.case_ref,
                    mechanism_vector.case_ref,
                    timing_vector.case_ref,
                }
            )
            != 1
        ):
            raise ValueError("mechanism_depth_case_lineage_mismatch")
        if (
            len(
                {
                    reading.chart_version_ref,
                    quant_vector.chart_version_ref,
                    mechanism_vector.chart_version_ref,
                    timing_vector.chart_version_ref,
                }
            )
            != 1
        ):
            raise ValueError("mechanism_depth_chart_lineage_mismatch")
        expected = (
            (reading.quant_vector_ref, quant_vector.vector_ref),
            (reading.quant_vector_hash, quant_vector.vector_hash),
            (reading.mechanism_vector_ref, mechanism_vector.vector_ref),
            (reading.mechanism_vector_hash, mechanism_vector.vector_hash),
            (reading.timing_vector_ref, timing_vector.vector_ref),
            (reading.timing_vector_hash, timing_vector.vector_hash),
        )
        if any(left != right for left, right in expected):
            raise ValueError("mechanism_depth_vector_lineage_mismatch")

    def _candidate(
        self,
        *,
        candidate: MechanismCandidateEvidence,
        attention_status: str,
        occurrence_index: Mapping[str, TenGodOccurrence],
        source_index: Mapping[str, SourceManifestationEvidence],
        candidate_index: Mapping[str, MechanismCandidateEvidence],
        timing_vector: MingliTimingEvidenceVector,
    ) -> CandidateMechanismEvidenceDepth:
        roles = tuple(
            self._role(
                role=role,
                occurrence_index=occurrence_index,
                source_index=source_index,
            )
            for role in candidate.roles
        )
        overlaps = tuple(
            MechanismTimingOverlapDepth(
                overlap_ref=item.overlap_ref,
                timing_coordinate_ref=item.timing_coordinate_ref,
                timing_layer=item.timing_layer,
                timing_ten_god_label=item.timing_ten_god_label,
                matching_role_ids=item.matching_role_ids,
                activation_status="UNRESOLVED",
            )
            for item in timing_vector.candidate_overlaps
            if item.candidate_ref == candidate.candidate_ref
        )
        timing_relations = tuple(
            relation
            for item in timing_vector.relation_evidence
            if (
                relation := self._timing_relation(
                    relation=item,
                    candidate=candidate,
                )
            )
            is not None
        )
        shared_participants = tuple(
            self._shared_participants(
                candidate=candidate,
                competitor=candidate_index[competitor_ref],
                occurrence_index=occurrence_index,
            )
            for competitor_ref in candidate.competing_candidate_refs
        )
        channels = {"STRUCTURAL_ROLES"}
        if any(role.visible_occurrence_refs for role in roles):
            channels.add("VISIBLE_CARRIERS")
        if any(role.hidden_occurrence_refs for role in roles):
            channels.add("HIDDEN_MEMBERS")
        if any(
            role.exact_source_evidence_refs or role.elemental_source_evidence_refs for role in roles
        ):
            channels.add("SOURCE_MANIFESTATION")
        if any(
            role.month_branch_occurrence_refs or role.month_branch_source_evidence_refs
            for role in roles
        ):
            channels.add("MONTH_BRANCH_CONTEXT")
        if overlaps:
            channels.add("TIMING_ROLE_OVERLAP")
        if timing_relations:
            channels.add("TIMING_RELATION_CONTEXT")
        if shared_participants:
            channels.add("SHARED_PARTICIPANT_COMPETITION")
        return CandidateMechanismEvidenceDepth(
            candidate_ref=candidate.candidate_ref,
            pattern_ref=candidate.pattern_ref,
            pattern_label=candidate.pattern_label,
            attention_status=attention_status,
            roles=roles,
            timing_overlaps=overlaps,
            timing_relations=timing_relations,
            shared_participants=shared_participants,
            evidence_channels=tuple(
                item for item in MECHANISM_EVIDENCE_CHANNEL_ORDER if item in channels
            ),
            unresolved_dimensions=MECHANISM_UNRESOLVED_DIMENSIONS,
            evidence_score_status="NOT_COMPUTED",
            professional_admission=False,
        )

    @staticmethod
    def _role(
        *,
        role: MechanismRoleEvidence,
        occurrence_index: Mapping[str, TenGodOccurrence],
        source_index: Mapping[str, SourceManifestationEvidence],
    ) -> MechanismRoleEvidenceDepth:
        try:
            occurrences = tuple(occurrence_index[item] for item in role.occurrence_refs)
            source_evidence = tuple(source_index[item] for item in role.manifestation_evidence_refs)
        except KeyError as exc:
            raise ValueError("mechanism_depth_evidence_ref_not_found") from exc
        visible = tuple(item for item in occurrences if item.layer == "VISIBLE_STEM")
        hidden = tuple(item for item in occurrences if item.layer == "HIDDEN_STEM")
        carrier_state = (
            "VISIBLE_AND_HIDDEN"
            if visible and hidden
            else "VISIBLE_ONLY"
            if visible
            else "HIDDEN_ONLY"
        )
        return MechanismRoleEvidenceDepth(
            role_id=role.role_id,
            accepted_labels=role.accepted_labels,
            visible_labels=tuple(sorted({item.label for item in visible})),
            hidden_labels=tuple(sorted({item.label for item in hidden})),
            carrier_state=carrier_state,
            visible_occurrence_refs=tuple(sorted(item.occurrence_ref for item in visible)),
            hidden_occurrence_refs=tuple(sorted(item.occurrence_ref for item in hidden)),
            month_branch_occurrence_refs=tuple(
                sorted(item.occurrence_ref for item in hidden if item.pillar_slot == "month")
            ),
            exact_source_evidence_refs=tuple(
                sorted(
                    item.evidence_ref
                    for item in source_evidence
                    if item.source_match_kind == "EXACT_IDENTITY"
                )
            ),
            elemental_source_evidence_refs=tuple(
                sorted(
                    item.evidence_ref
                    for item in source_evidence
                    if item.source_match_kind == "SAME_ELEMENT_DIFFERENT_IDENTITY"
                )
            ),
            same_pillar_source_evidence_refs=tuple(
                sorted(
                    item.evidence_ref
                    for item in source_evidence
                    if "SAME_PILLAR_SOURCE_COORDINATE" in item.evidence_states
                )
            ),
            month_branch_source_evidence_refs=tuple(
                sorted(
                    item.evidence_ref
                    for item in source_evidence
                    if "MONTH_BRANCH_SOURCE_COORDINATE" in item.evidence_states
                )
            ),
            direct_evidence_refs=role.direct_evidence_refs,
            source_effect_status="UNRESOLVED",
        )

    @staticmethod
    def _timing_relation(
        *,
        relation: Any,
        candidate: MechanismCandidateEvidence,
    ) -> MechanismTimingRelationDepth | None:
        matching_role_ids = tuple(
            sorted(
                role.role_id
                for role in candidate.roles
                if relation.natal_slot in role.participant_slots
            )
        )
        if not matching_role_ids:
            return None
        return MechanismTimingRelationDepth(
            evidence_ref=relation.evidence_ref,
            timing_coordinate_ref=relation.timing_coordinate_ref,
            timing_layer=relation.timing_layer,
            natal_slot=relation.natal_slot,
            relation_type=relation.relation_type,
            matching_role_ids=matching_role_ids,
            rule_ref=relation.rule_ref,
            effect_status="UNRESOLVED",
        )

    @staticmethod
    def _shared_participants(
        *,
        candidate: MechanismCandidateEvidence,
        competitor: MechanismCandidateEvidence,
        occurrence_index: Mapping[str, TenGodOccurrence],
    ) -> MechanismSharedParticipantDepth:
        candidate_refs = {ref for role in candidate.roles for ref in role.occurrence_refs}
        competitor_refs = {ref for role in competitor.roles for ref in role.occurrence_refs}
        shared_refs = tuple(sorted(candidate_refs & competitor_refs))
        if not shared_refs:
            raise ValueError("mechanism_depth_competitor_has_no_shared_participant")
        return MechanismSharedParticipantDepth(
            competing_candidate_ref=competitor.candidate_ref,
            shared_occurrence_refs=shared_refs,
            shared_labels=tuple(sorted({occurrence_index[item].label for item in shared_refs})),
        )
