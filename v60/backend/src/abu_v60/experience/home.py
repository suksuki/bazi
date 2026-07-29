from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.engine import Engine

from abu_v60.abu import MingliAbuExpressionProjector
from abu_v60.mingli import (
    MingliExplanationProjector,
    MingliLifeDomainEvidenceCompiler,
    MingliLifeDomainVectorStore,
    MingliMechanismComparisonService,
    MingliMechanismEvidenceCompiler,
    MingliMechanismQualificationProjector,
    MingliMechanismVectorStore,
    MingliQuantFoundationCompiler,
    MingliQuantVectorStore,
    MingliReadingProjector,
    MingliReadingStore,
    MingliTimingEvidenceCompiler,
    MingliTimingVectorStore,
    StructuralCandidateCompiler,
)
from abu_v60.mingli.brief import MingliReadingBriefProjector
from abu_v60.mingli.calendar import BirthInput
from abu_v60.mingli.service import MingliCaseService
from abu_v60.provenance import content_hash, stable_ref


class HomeExperienceUnavailableError(ValueError):
    pass


class HomeExperienceService:
    """Build the signed-in viewer's private, read-only life-tree projection."""

    def __init__(
        self,
        engine: Engine,
        *,
        cases: MingliCaseService | None = None,
        candidates: StructuralCandidateCompiler | None = None,
        readings: MingliReadingProjector | None = None,
        reading_store: MingliReadingStore | None = None,
        quant_compiler: MingliQuantFoundationCompiler | None = None,
        quant_store: MingliQuantVectorStore | None = None,
        mechanism_compiler: MingliMechanismEvidenceCompiler | None = None,
        mechanism_store: MingliMechanismVectorStore | None = None,
        mechanism_comparison: MingliMechanismComparisonService | None = None,
        timing_compiler: MingliTimingEvidenceCompiler | None = None,
        timing_store: MingliTimingVectorStore | None = None,
        life_domain_compiler: MingliLifeDomainEvidenceCompiler | None = None,
        life_domain_store: MingliLifeDomainVectorStore | None = None,
        explanations: MingliExplanationProjector | None = None,
        mechanism_qualifications: MingliMechanismQualificationProjector | None = None,
        analysis_date_provider: Callable[[str], date] | None = None,
        abu: MingliAbuExpressionProjector | None = None,
    ) -> None:
        self._cases = cases or MingliCaseService(engine)
        self._candidates = candidates or StructuralCandidateCompiler()
        self._readings = readings or MingliReadingProjector()
        self._reading_store = reading_store or MingliReadingStore(engine)
        self._quant_compiler = quant_compiler or MingliQuantFoundationCompiler()
        self._quant_store = quant_store or MingliQuantVectorStore(engine)
        self._mechanism_compiler = mechanism_compiler or MingliMechanismEvidenceCompiler()
        self._mechanism_store = mechanism_store or MingliMechanismVectorStore(engine)
        self._mechanism_comparison = mechanism_comparison or MingliMechanismComparisonService(
            engine
        )
        self._reading_brief = MingliReadingBriefProjector()
        self._timing_compiler = timing_compiler or MingliTimingEvidenceCompiler()
        self._timing_store = timing_store or MingliTimingVectorStore(engine)
        self._life_domain_compiler = life_domain_compiler or MingliLifeDomainEvidenceCompiler()
        self._life_domain_store = life_domain_store or MingliLifeDomainVectorStore(engine)
        self._explanations = explanations or MingliExplanationProjector()
        self._mechanism_qualifications = (
            mechanism_qualifications or MingliMechanismQualificationProjector()
        )
        self._analysis_date_provider = analysis_date_provider or (
            lambda timezone: datetime.now(ZoneInfo(timezone)).date()
        )
        self._abu = abu or MingliAbuExpressionProjector()

    def snapshot(self, *, account_ref: str) -> dict[str, Any]:
        owner_cases = [
            item
            for item in self._cases.list_cases(account_ref=account_ref)
            if item["subject_kind"] == "HUMAN_OWNER"
        ]
        home_cases = [item for item in owner_cases if item["status"] == "ACTIVE"]
        if not home_cases:
            raise HomeExperienceUnavailableError("home_case_not_found")
        if len(home_cases) != 1:
            raise HomeExperienceUnavailableError("home_case_selection_required")

        workspace = self._cases.workspace(
            account_ref=account_ref,
            case_ref=str(home_cases[0]["case_ref"]),
        )
        facts = workspace["facts"]
        chart_ref = str(workspace["chart"]["chart_version_ref"])
        candidate_paths = self._candidates.compile(
            chart_version_ref=chart_ref,
            facts=facts,
        )
        quant_vector = self._quant_store.ensure(
            self._quant_compiler.compile(
                case_ref=str(workspace["case"]["case_ref"]),
                chart_version_ref=chart_ref,
                pillars=workspace["chart"]["pillars"],
                facts=facts,
            )
        )
        mechanism_vector = self._mechanism_store.ensure(
            self._mechanism_compiler.compile(
                quant_vector=quant_vector,
                facts=facts,
            )
        )
        mechanism_comparison = self._mechanism_comparison.current_state(
            vector=mechanism_vector,
        )
        birth_input = BirthInput.model_validate(workspace["profile"]["birth_input"])
        timing_vector = self._timing_store.ensure(
            self._timing_compiler.compile(
                case_ref=str(workspace["case"]["case_ref"]),
                chart_version_ref=chart_ref,
                life_case_revision_ref=str(workspace["life_case"]["life_case_revision_ref"]),
                birth_input=birth_input,
                gender=str(workspace["profile"]["gender"]),
                pillars=workspace["chart"]["pillars"],
                facts=facts,
                analysis_date=self._analysis_date_provider(birth_input.timezone),
                mechanism_vector=mechanism_vector,
            )
        )
        life_domain_vector = self._life_domain_store.ensure(
            self._life_domain_compiler.compile(
                mechanism_vector=mechanism_vector,
                timing_vector=timing_vector,
            )
        )
        reading = self._reading_store.ensure(
            self._readings.project(
                case_ref=str(workspace["case"]["case_ref"]),
                chart_version_ref=chart_ref,
                life_case_revision_ref=str(workspace["life_case"]["life_case_revision_ref"]),
                facts=facts,
                candidates=candidate_paths,
                quant_vector=quant_vector,
                mechanism_vector=mechanism_vector,
                timing_vector=timing_vector,
                life_domain_vector=life_domain_vector,
                decision_refs=(
                    (str(mechanism_comparison["decision_ref"]),)
                    if mechanism_comparison["decision_ref"] is not None
                    else ()
                ),
            )
        )
        explanation = self._explanations.project(
            reading=reading,
            facts=facts,
            quant_vector=quant_vector,
            mechanism_vector=mechanism_vector,
            timing_vector=timing_vector,
            life_domain_vector=life_domain_vector,
            mechanism_comparison=mechanism_comparison,
        )
        mechanism_qualification = self._mechanism_qualifications.project(
            reading=reading,
            quant_vector=quant_vector,
            mechanism_vector=mechanism_vector,
            timing_vector=timing_vector,
        )
        abu_expression = self._abu.project(
            reading=reading,
            explanation=explanation,
            qualification=mechanism_qualification,
        )
        reading_brief = self._reading_brief.project(
            reading=reading,
            pillars=workspace["chart"]["pillars"],
            fact_count=len(facts),
            quant_vector=quant_vector,
            mechanism_vector=mechanism_vector,
            timing_vector=timing_vector,
            life_domain_vector=life_domain_vector,
            mechanism_comparison=mechanism_comparison,
        )
        lineage = {
            "case_ref": workspace["case"]["case_ref"],
            "life_case_revision_ref": workspace["life_case"]["life_case_revision_ref"],
            "chart_version_ref": chart_ref,
            "scene_ref": workspace["scene"]["scene_ref"],
            "fact_refs": sorted(str(item["fact_ref"]) for item in facts),
        }
        tree_identity = {
            "projection_kind": "PRIVATE_HOME_LIFE_TREE",
            **lineage,
        }
        context_identity = {
            "scope": "HOME_CASE",
            "profile_ref": workspace["profile"]["profile_ref"],
            **lineage,
        }
        context_ref = stable_ref("v60-home-experience", context_identity)
        return {
            "scope": "HOME_CASE",
            "context_ref": context_ref,
            "context_hash": content_hash(context_identity),
            "profile": {
                "profile_ref": workspace["profile"]["profile_ref"],
                "display_name": workspace["profile"]["display_name"],
            },
            "case": workspace["case"],
            "case_options": [
                {
                    "case_ref": item["case_ref"],
                    "profile_ref": item["profile_ref"],
                    "display_name": item["display_name"],
                    "status": item["status"],
                    "pillars": item["pillars_json"],
                    "active": item["case_ref"] == workspace["case"]["case_ref"],
                }
                for item in owner_cases
            ],
            "chart": {
                "chart_version_ref": chart_ref,
                "version": workspace["chart"]["version"],
                "pillars": workspace["chart"]["pillars"],
                "chart_hash": workspace["chart"]["chart_hash"],
            },
            "life_case": {
                "life_case_revision_ref": workspace["life_case"]["life_case_revision_ref"],
                "revision": workspace["life_case"]["revision"],
                "status": workspace["life_case"]["status"],
                "revision_hash": workspace["life_case"]["revision_hash"],
            },
            "tree": {
                "tree_ref": stable_ref("v60-private-home-tree", tree_identity),
                "projection_version": workspace["scene"]["version"],
                "scene_ref": workspace["scene"]["scene_ref"],
                "phenotype": workspace["scene"]["payload"]["tree_phenotype"],
                "read_only": True,
                "source_kind": "CANONICAL_SCENE_PROJECTION",
            },
            "mingli": {
                "authority": "MINGLI_FACT_AUTHORITY",
                "pillars": workspace["chart"]["pillars"],
                "facts": facts,
                "reading": reading.model_dump(mode="json"),
                "quant_foundation": quant_vector.model_dump(mode="json"),
                "mechanism_evidence": mechanism_vector.model_dump(mode="json"),
                "timing_evidence": timing_vector.model_dump(mode="json"),
                "life_domains": life_domain_vector.model_dump(mode="json"),
                "reading_brief": reading_brief,
                "explanation": explanation.model_dump(mode="json"),
                "mechanism_qualification": mechanism_qualification.model_dump(mode="json"),
                "abu_expression": abu_expression.model_dump(mode="json"),
                "read_only": True,
            },
            "lab": {
                "reading_ref": reading.reading_ref,
                "reading_hash": reading.reading_hash,
                "explanation_ref": explanation.explanation_ref,
                "explanation_hash": explanation.explanation_hash,
                "mechanism_qualification_ref": (
                    mechanism_qualification.qualification_ref
                ),
                "mechanism_qualification_hash": (
                    mechanism_qualification.qualification_hash
                ),
                "mechanism_qualification_candidates": [
                    item.model_dump(mode="json")
                    for item in mechanism_qualification.candidates
                ],
                "profile_bindings": {
                    "foundation": reading.foundation_profile.model_dump(mode="json"),
                    "candidate_rules": reading.candidate_rule_profile.model_dump(mode="json"),
                    "quant_foundation": (
                        reading.quant_foundation_profile.model_dump(mode="json")
                        if reading.quant_foundation_profile is not None
                        else None
                    ),
                    "mechanism_evidence": (
                        reading.mechanism_evidence_profile.model_dump(mode="json")
                        if reading.mechanism_evidence_profile is not None
                        else None
                    ),
                    "timing_evidence": (
                        reading.timing_evidence_profile.model_dump(mode="json")
                        if reading.timing_evidence_profile is not None
                        else None
                    ),
                },
                "quant_vector_ref": quant_vector.vector_ref,
                "quant_vector_hash": quant_vector.vector_hash,
                "candidate_paths": [
                    candidate.model_dump(mode="json") for candidate in candidate_paths
                ],
                "mechanism_vector_ref": mechanism_vector.vector_ref,
                "mechanism_vector_hash": mechanism_vector.vector_hash,
                "timing_vector_ref": timing_vector.vector_ref,
                "timing_vector_hash": timing_vector.vector_hash,
                "life_domain_vector_ref": life_domain_vector.vector_ref,
                "life_domain_vector_hash": life_domain_vector.vector_hash,
                "life_domain_observations": [
                    item.model_dump(mode="json") for item in life_domain_vector.observations
                ],
                "timing_coordinates": [
                    coordinate.model_dump(mode="json") for coordinate in timing_vector.coordinates
                ],
                "timing_relations": [
                    item.model_dump(mode="json") for item in timing_vector.relation_evidence
                ],
                "timing_candidate_overlaps": [
                    item.model_dump(mode="json") for item in timing_vector.candidate_overlaps
                ],
                "mechanism_candidates": [
                    candidate.model_dump(mode="json") for candidate in mechanism_vector.candidates
                ],
                "mechanism_comparison": mechanism_comparison,
                "interpretation_status": "BOUNDED_ATTENTION_COMPARISON",
                "research_admission_status": "PROFILE_ADMISSION_REQUIRED",
                "canonical_write_allowed": False,
            },
            "units": {
                "dream": {
                    "status": "THRESHOLD_AVAILABLE",
                    "line": "阿布仍守着通往梦境的雾径。",
                },
                "abu": {
                    "status": "MINGLI_BOUND_EXPRESSION",
                    "reading_ref": reading.reading_ref,
                    "line": abu_expression.summary,
                },
                "theater": {
                    "status": "NO_ADMITTED_HOME_SCENE",
                    "line": "你的正式生命片段尚未进入小剧场。",
                },
            },
            "lineage": lineage,
            "boundaries": {
                "private_to_account": True,
                "dream_encounter_subject": False,
                "canonical_write_allowed": False,
                "visual_semantics": "VISUAL_METAPHOR_ONLY",
            },
        }

    def compare_mechanisms(self, *, account_ref: str) -> dict[str, Any]:
        snapshot = self.snapshot(account_ref=account_ref)
        vector = self._mechanism_store.get(vector_ref=str(snapshot["lab"]["mechanism_vector_ref"]))
        return self._mechanism_comparison.compare(vector=vector)
