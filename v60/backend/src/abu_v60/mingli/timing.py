from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from lunar_python import Solar

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.calendar import BirthInput, resolve_eight_char
from abu_v60.mingli.mechanism_contracts import MingliMechanismEvidenceVector
from abu_v60.mingli.quantitative import PILLAR_SLOTS, resolve_ten_god
from abu_v60.mingli.timing_contracts import (
    MingliTimingEvidenceVector,
    TimingCandidateOverlap,
    TimingCoordinate,
    TimingRelationEvidence,
)
from abu_v60.provenance import stable_ref


class MingliTimingEvidenceCompiler:
    """Compile one immutable as-of timing vector without inferring effects."""

    def __init__(self, authority: KnowledgeAuthority | None = None) -> None:
        self._authority = authority or KnowledgeAuthority()

    def compile(
        self,
        *,
        case_ref: str,
        chart_version_ref: str,
        life_case_revision_ref: str,
        birth_input: BirthInput,
        gender: str,
        pillars: Mapping[str, str],
        facts: Sequence[Mapping[str, Any]],
        analysis_date: date,
        mechanism_vector: MingliMechanismEvidenceVector | None = None,
    ) -> MingliTimingEvidenceVector:
        if set(pillars) != set(PILLAR_SLOTS):
            raise ValueError("timing_vector_requires_four_pillars")
        if mechanism_vector is not None and (
            mechanism_vector.case_ref != case_ref
            or mechanism_vector.chart_version_ref != chart_version_ref
        ):
            raise ValueError("timing_vector_mechanism_lineage_mismatch")

        timing_profile = self._authority.active_timing_evidence_profile()
        foundation_profile = self._authority.active_foundation_profile()
        gender_codes = {
            item.gender: item.lunar_python_code
            for item in timing_profile.yun_gender_codes
        }
        if gender not in gender_codes:
            raise ValueError("timing_vector_gender_not_supported")

        eight_char = resolve_eight_char(birth_input)
        yun = eight_char.getYun(gender_codes[gender])
        current_dayun = next(
            (
                item
                for item in yun.getDaYun()
                if item.getStartYear() <= analysis_date.year <= item.getEndYear()
            ),
            None,
        )
        if current_dayun is None:
            raise ValueError("timing_vector_current_dayun_not_found")

        current_eight_char = Solar.fromYmdHms(
            analysis_date.year,
            analysis_date.month,
            analysis_date.day,
            12,
            0,
            0,
        ).getLunar().getEightChar()
        current_eight_char.setSect(2)
        raw_coordinates = (
            (
                "DAYUN",
                current_dayun.getGanZhi(),
                current_dayun.getStartYear(),
                current_dayun.getEndYear(),
            ),
            ("ANNUAL", current_eight_char.getYear(), None, None),
            ("MONTHLY", current_eight_char.getMonth(), None, None),
        )
        day_master = pillars["day"][0]
        coordinates = tuple(
            self._coordinate(
                case_ref=case_ref,
                chart_version_ref=chart_version_ref,
                life_case_revision_ref=life_case_revision_ref,
                analysis_date=analysis_date,
                day_master=day_master,
                layer=layer,
                pillar=pillar,
                start_year=start_year,
                end_year=end_year,
            )
            for layer, pillar, start_year, end_year in raw_coordinates
        )
        relations = self._relations(
            chart_version_ref=chart_version_ref,
            coordinates=coordinates,
            pillars=pillars,
            facts=facts,
            foundation_profile=foundation_profile,
        )
        overlaps = self._candidate_overlaps(
            coordinates=coordinates,
            mechanism_vector=mechanism_vector,
        )
        return MingliTimingEvidenceVector.issue(
            case_ref=case_ref,
            chart_version_ref=chart_version_ref,
            life_case_revision_ref=life_case_revision_ref,
            birth_input_hash=birth_input.input_hash,
            timing_profile_ref=timing_profile.source_ref,
            timing_profile_hash=timing_profile.profile_hash,
            foundation_profile_ref=foundation_profile.source_ref,
            foundation_profile_hash=foundation_profile.profile_hash,
            calendar_engine_version=timing_profile.calendar_engine_version,
            analysis_date=analysis_date,
            timezone=birth_input.timezone,
            day_master_stem=day_master,
            coordinates=coordinates,
            relation_evidence=relations,
            candidate_overlaps=overlaps,
            timing_semantics="COORDINATE_AND_MEMBERSHIP_ONLY",
            activation_status="UNRESOLVED",
            effect_status="UNRESOLVED",
            calibration_status="NOT_CALIBRATED",
            forbidden_conclusions=timing_profile.forbidden_conclusions,
        )

    def _coordinate(
        self,
        *,
        case_ref: str,
        chart_version_ref: str,
        life_case_revision_ref: str,
        analysis_date: date,
        day_master: str,
        layer: str,
        pillar: str,
        start_year: int | None,
        end_year: int | None,
    ) -> TimingCoordinate:
        identity = {
            "case_ref": case_ref,
            "chart_version_ref": chart_version_ref,
            "life_case_revision_ref": life_case_revision_ref,
            "analysis_date": analysis_date.isoformat(),
            "layer": layer,
            "pillar": pillar,
        }
        return TimingCoordinate(
            coordinate_ref=stable_ref("v60-mingli-timing-coordinate", identity),
            layer=layer,
            pillar=pillar,
            stem=pillar[0],
            branch=pillar[1],
            ten_god_label=resolve_ten_god(
                day_stem=day_master,
                other_stem=pillar[0],
                authority=self._authority,
            ),
            start_year=start_year,
            end_year=end_year,
            calculation_status="DETERMINISTIC_COORDINATE",
        )

    @staticmethod
    def _relations(
        *,
        chart_version_ref: str,
        coordinates: tuple[TimingCoordinate, ...],
        pillars: Mapping[str, str],
        facts: Sequence[Mapping[str, Any]],
        foundation_profile: Any,
    ) -> tuple[TimingRelationEvidence, ...]:
        relation_lookup = {
            frozenset((item.left_branch, item.right_branch)): item.relation_type
            for item in foundation_profile.relations
        }
        fact_refs_by_branch = {
            slot: tuple(
                sorted(
                    str(fact["fact_ref"])
                    for fact in facts
                    if fact.get("subject_ref") == f"pillar:{slot}:branch:{pillar[1]}"
                    and fact.get("fact_type") == "hidden_stem_membership"
                )
            )
            for slot, pillar in pillars.items()
        }
        evidence: list[TimingRelationEvidence] = []
        for coordinate in coordinates:
            for slot in PILLAR_SLOTS:
                natal_branch = pillars[slot][1]
                relation_type = (
                    "same_branch_membership"
                    if coordinate.branch == natal_branch
                    else relation_lookup.get(frozenset((coordinate.branch, natal_branch)))
                )
                if relation_type is None:
                    continue
                natal_refs = fact_refs_by_branch[slot]
                if not natal_refs:
                    raise ValueError(f"timing_natal_branch_facts_incomplete:{slot}")
                identity = {
                    "chart_version_ref": chart_version_ref,
                    "timing_coordinate_ref": coordinate.coordinate_ref,
                    "natal_slot": slot,
                    "natal_branch": natal_branch,
                    "relation_type": relation_type,
                }
                evidence.append(
                    TimingRelationEvidence(
                        evidence_ref=stable_ref("v60-mingli-timing-relation", identity),
                        timing_coordinate_ref=coordinate.coordinate_ref,
                        timing_layer=coordinate.layer,
                        timing_branch=coordinate.branch,
                        natal_slot=slot,
                        natal_branch=natal_branch,
                        relation_type=relation_type,
                        evidence_refs=(coordinate.coordinate_ref, *natal_refs),
                        rule_ref=foundation_profile.source_ref,
                        relation_status="MEMBERSHIP_PRESENT",
                        effect_status="UNRESOLVED",
                    )
                )
        return tuple(
            sorted(
                evidence,
                key=lambda item: (
                    ("DAYUN", "ANNUAL", "MONTHLY").index(item.timing_layer),
                    PILLAR_SLOTS.index(item.natal_slot),
                    item.relation_type,
                ),
            )
        )

    @staticmethod
    def _candidate_overlaps(
        *,
        coordinates: tuple[TimingCoordinate, ...],
        mechanism_vector: MingliMechanismEvidenceVector | None,
    ) -> tuple[TimingCandidateOverlap, ...]:
        if mechanism_vector is None:
            return ()
        overlaps: list[TimingCandidateOverlap] = []
        for coordinate in coordinates:
            for candidate in mechanism_vector.candidates:
                role_ids = tuple(
                    sorted(
                        role.role_id
                        for role in candidate.roles
                        if coordinate.ten_god_label in role.accepted_labels
                    )
                )
                if not role_ids:
                    continue
                identity = {
                    "timing_coordinate_ref": coordinate.coordinate_ref,
                    "candidate_ref": candidate.candidate_ref,
                    "matching_role_ids": role_ids,
                }
                overlaps.append(
                    TimingCandidateOverlap(
                        overlap_ref=stable_ref("v60-mingli-timing-overlap", identity),
                        timing_coordinate_ref=coordinate.coordinate_ref,
                        timing_layer=coordinate.layer,
                        timing_ten_god_label=coordinate.ten_god_label,
                        candidate_ref=candidate.candidate_ref,
                        matching_role_ids=role_ids,
                        overlap_status="LABEL_OVERLAP_ONLY",
                        activation_status="UNRESOLVED",
                        effect_status="UNRESOLVED",
                    )
                )
        return tuple(
            sorted(
                overlaps,
                key=lambda item: (
                    ("DAYUN", "ANNUAL", "MONTHLY").index(item.timing_layer),
                    item.candidate_ref,
                ),
            )
        )
