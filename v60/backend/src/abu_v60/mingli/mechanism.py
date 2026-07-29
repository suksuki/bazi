from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.knowledge.mechanism_contracts import MechanismPatternDefinition
from abu_v60.mingli.mechanism_contracts import (
    MechanismCandidateEvidence,
    MechanismRoleEvidence,
    MingliMechanismEvidenceVector,
)
from abu_v60.mingli.quant_contracts import (
    MingliQuantFoundationVector,
    TenGodOccurrence,
)
from abu_v60.provenance import stable_ref

MECHANISM_EVIDENCE_COMPILER_VERSION = "v60.mechanism-evidence-compiler.001"
_RELATION_FACT_TYPES = {"six_clash_membership", "six_harmony_membership"}


class MingliMechanismEvidenceCompiler:
    """Compile role-complete candidates while preserving every unknown."""

    def __init__(self, authority: KnowledgeAuthority | None = None) -> None:
        self._authority = authority or KnowledgeAuthority()

    def compile(
        self,
        *,
        quant_vector: MingliQuantFoundationVector,
        facts: Sequence[Mapping[str, Any]],
    ) -> MingliMechanismEvidenceVector:
        profile = self._authority.active_mechanism_evidence_profile()
        candidates = [
            candidate
            for pattern in profile.patterns
            if (
                candidate := self._compile_pattern(
                    pattern=pattern,
                    profile_ref=profile.source_ref,
                    profile_hash=profile.profile_hash,
                    quant_vector=quant_vector,
                    facts=facts,
                    required_blockers=profile.required_blockers,
                )
            )
            is not None
        ]
        candidates = self._bind_competition(candidates)
        evidence_refs = tuple(
            sorted(
                {
                    ref
                    for candidate in candidates
                    for ref in (
                        *candidate.support_evidence_refs,
                        *candidate.context_evidence_refs,
                        *candidate.counter_evidence_refs,
                    )
                }
            )
        )
        return MingliMechanismEvidenceVector.issue(
            case_ref=quant_vector.case_ref,
            chart_version_ref=quant_vector.chart_version_ref,
            quant_vector_ref=quant_vector.vector_ref,
            quant_vector_hash=quant_vector.vector_hash,
            mechanism_profile_ref=profile.source_ref,
            mechanism_profile_hash=profile.profile_hash,
            candidates=tuple(sorted(candidates, key=lambda item: item.candidate_ref)),
            evidence_refs=evidence_refs,
            comparison_status=(
                "NO_CANDIDATE"
                if not candidates
                else "ONE_CANDIDATE"
                if len(candidates) == 1
                else "MULTIPLE_CANDIDATES"
            ),
            interpretation_authority="BOUNDED_REASONER_ATTENTION_ONLY",
        )

    def _compile_pattern(
        self,
        *,
        pattern: MechanismPatternDefinition,
        profile_ref: str,
        profile_hash: str,
        quant_vector: MingliQuantFoundationVector,
        facts: Sequence[Mapping[str, Any]],
        required_blockers: tuple[str, ...],
    ) -> MechanismCandidateEvidence | None:
        roles: list[MechanismRoleEvidence] = []
        for role in pattern.roles:
            occurrences = tuple(
                occurrence
                for occurrence in quant_vector.ten_god_occurrences
                if occurrence.label in set(role.accepted_ten_god_labels)
            )
            if not occurrences:
                return None
            roles.append(
                self._role_evidence(
                    role_id=role.role_id,
                    accepted_labels=role.accepted_ten_god_labels,
                    occurrences=occurrences,
                    quant_vector=quant_vector,
                )
            )

        if not any(
            role.visible_occurrence_count > 0 and role.role_id != "TARGET" for role in roles
        ):
            return None
        support_refs = tuple(sorted({ref for role in roles for ref in role.direct_evidence_refs}))
        participant_slots = {slot for role in roles for slot in role.participant_slots}
        context_refs = {ref for role in roles for ref in role.manifestation_evidence_refs}
        context_refs.update(self._relation_context_refs(facts=facts, slots=participant_slots))
        blockers = set(required_blockers)
        for role in roles:
            if role.visible_occurrence_count == 0:
                blockers.add(f"VISIBLE_CARRIER_ABSENT:{role.role_id}")
        if roles[0].manifestation_evidence_refs:
            blockers.add("SOURCE_MANIFESTATION_EFFECT_UNRESOLVED")
        else:
            blockers.add("SOURCE_MANIFESTATION_EVIDENCE_ABSENT")
        identity = {
            "compiler_version": MECHANISM_EVIDENCE_COMPILER_VERSION,
            "chart_version_ref": quant_vector.chart_version_ref,
            "quant_vector_ref": quant_vector.vector_ref,
            "mechanism_profile_ref": profile_ref,
            "mechanism_profile_hash": profile_hash,
            "pattern_ref": pattern.pattern_ref,
            "roles": [role.model_dump(mode="json") for role in roles],
            "support_evidence_refs": support_refs,
            "context_evidence_refs": sorted(context_refs),
        }
        return MechanismCandidateEvidence(
            candidate_ref=stable_ref("v60-mechanism-candidate", identity),
            pattern_ref=pattern.pattern_ref,
            pattern_label=pattern.label,
            structural_statement=pattern.structural_statement,
            forbidden_shortcut=pattern.forbidden_shortcut,
            roles=tuple(roles),
            support_evidence_refs=support_refs,
            context_evidence_refs=tuple(sorted(context_refs)),
            counter_evidence_refs=(),
            blocker_codes=tuple(sorted(blockers)),
            competing_candidate_refs=(),
            structural_presence="PRESENT",
            effect_status="UNRESOLVED",
            capacity_status="UNRESOLVED",
            usability_status="UNRESOLVED",
            timing_activation_status="UNRESOLVED",
            counter_evidence_status="NOT_ADMITTED",
            professional_admission_status="UNRESOLVED",
            comparison_eligible=True,
            professional_selection_qualified=False,
            support_score_status="NOT_COMPUTED_NO_ADMITTED_WEIGHTS",
        )

    @staticmethod
    def _role_evidence(
        *,
        role_id: str,
        accepted_labels: tuple[str, ...],
        occurrences: tuple[TenGodOccurrence, ...],
        quant_vector: MingliQuantFoundationVector,
    ) -> MechanismRoleEvidence:
        visible = tuple(item for item in occurrences if item.layer == "VISIBLE_STEM")
        manifestation_refs = tuple(
            sorted(
                evidence.evidence_ref
                for evidence in quant_vector.source_manifestation_evidence
                if any(
                    occurrence.pillar_slot == evidence.visible_slot
                    and occurrence.stem == evidence.visible_stem
                    for occurrence in visible
                )
            )
        )
        return MechanismRoleEvidence(
            role_id=role_id,
            accepted_labels=accepted_labels,
            occurrence_refs=tuple(sorted(item.occurrence_ref for item in occurrences)),
            occurrence_labels=tuple(sorted(item.label for item in occurrences)),
            participant_slots=tuple(sorted({item.pillar_slot for item in occurrences})),
            direct_evidence_refs=tuple(
                sorted({ref for item in occurrences for ref in item.evidence_refs})
            ),
            manifestation_evidence_refs=manifestation_refs,
            visible_occurrence_count=len(visible),
            hidden_occurrence_count=len(occurrences) - len(visible),
        )

    @staticmethod
    def _relation_context_refs(
        *,
        facts: Sequence[Mapping[str, Any]],
        slots: set[str],
    ) -> set[str]:
        refs: set[str] = set()
        for fact in facts:
            payload = fact.get("fact_json")
            if fact.get("fact_type") not in _RELATION_FACT_TYPES or not isinstance(
                payload, Mapping
            ):
                continue
            if {payload.get("left_slot"), payload.get("right_slot")} & slots:
                fact_ref = fact.get("fact_ref")
                if isinstance(fact_ref, str) and fact_ref:
                    refs.add(fact_ref)
        return refs

    @staticmethod
    def _bind_competition(
        candidates: list[MechanismCandidateEvidence],
    ) -> list[MechanismCandidateEvidence]:
        participants = {
            candidate.candidate_ref: {
                ref for role in candidate.roles for ref in role.occurrence_refs
            }
            for candidate in candidates
        }
        bound: list[MechanismCandidateEvidence] = []
        for candidate in candidates:
            competing = tuple(
                sorted(
                    other.candidate_ref
                    for other in candidates
                    if other.candidate_ref != candidate.candidate_ref
                    and participants[candidate.candidate_ref] & participants[other.candidate_ref]
                )
            )
            blockers = set(candidate.blocker_codes)
            if competing:
                blockers.add("COMPETING_PATH_SHARED_PARTICIPANTS")
            bound.append(
                candidate.model_copy(
                    update={
                        "competing_candidate_refs": competing,
                        "blocker_codes": tuple(sorted(blockers)),
                    }
                )
            )
        return bound
