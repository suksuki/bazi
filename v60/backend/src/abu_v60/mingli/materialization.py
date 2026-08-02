from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.engine import Engine

from abu_v60.mingli.calendar import BirthInput
from abu_v60.mingli.candidates import StructuralCandidateCompiler
from abu_v60.mingli.domain import MingliLifeDomainEvidenceCompiler
from abu_v60.mingli.domain_store import MingliLifeDomainVectorStore
from abu_v60.mingli.mechanism import MingliMechanismEvidenceCompiler
from abu_v60.mingli.mechanism_store import MingliMechanismVectorStore
from abu_v60.mingli.quant_store import MingliQuantVectorStore
from abu_v60.mingli.quantitative import MingliQuantFoundationCompiler
from abu_v60.mingli.reading import MingliReadingProjector
from abu_v60.mingli.reading_store import MingliReadingStore
from abu_v60.mingli.service import MingliCaseService
from abu_v60.mingli.source_review import MingliSourceCoordinateReviewCompiler
from abu_v60.mingli.source_review_store import MingliSourceReviewVectorStore
from abu_v60.mingli.timing import MingliTimingEvidenceCompiler
from abu_v60.mingli.timing_store import MingliTimingVectorStore

MINGLI_CASE_MATERIALIZATION_VERSION = "v60.mingli-case-materialization.001"


class MingliCaseMaterializationService:
    """Build the one canonical evidence and Reading chain for any admitted Case."""

    def __init__(self, engine: Engine) -> None:
        self._cases = MingliCaseService(engine)
        self._candidates = StructuralCandidateCompiler()
        self._quant_compiler = MingliQuantFoundationCompiler()
        self._quant_store = MingliQuantVectorStore(engine)
        self._source_review_compiler = MingliSourceCoordinateReviewCompiler()
        self._source_review_store = MingliSourceReviewVectorStore(engine)
        self._mechanism_compiler = MingliMechanismEvidenceCompiler()
        self._mechanism_store = MingliMechanismVectorStore(engine)
        self._timing_compiler = MingliTimingEvidenceCompiler()
        self._timing_store = MingliTimingVectorStore(engine)
        self._domain_compiler = MingliLifeDomainEvidenceCompiler()
        self._domain_store = MingliLifeDomainVectorStore(engine)
        self._reading_projector = MingliReadingProjector()
        self._reading_store = MingliReadingStore(engine)

    def materialize(
        self,
        *,
        account_ref: str,
        case_ref: str,
        subject_kind: str,
        analysis_date: date,
    ) -> dict[str, Any]:
        workspace = self._cases.workspace(account_ref=account_ref, case_ref=case_ref)
        if workspace["case"]["subject_kind"] != subject_kind:
            raise ValueError("mingli_materialization_subject_kind_mismatch")
        chart_ref = str(workspace["chart"]["chart_version_ref"])
        facts = workspace["facts"]
        candidates = self._candidates.compile(
            chart_version_ref=chart_ref,
            facts=facts,
        )
        quant = self._quant_store.ensure(
            self._quant_compiler.compile(
                case_ref=case_ref,
                chart_version_ref=chart_ref,
                pillars=workspace["chart"]["pillars"],
                facts=facts,
            )
        )
        source_review = self._source_review_store.ensure(
            self._source_review_compiler.compile(
                quant_vector=quant,
                facts=facts,
            )
        )
        mechanism = self._mechanism_store.ensure(
            self._mechanism_compiler.compile(quant_vector=quant, facts=facts)
        )
        timing = self._timing_store.ensure(
            self._timing_compiler.compile(
                case_ref=case_ref,
                chart_version_ref=chart_ref,
                life_case_revision_ref=str(
                    workspace["life_case"]["life_case_revision_ref"]
                ),
                birth_input=BirthInput.model_validate(
                    workspace["profile"]["birth_input"]
                ),
                gender=str(workspace["profile"]["gender"]),
                pillars=workspace["chart"]["pillars"],
                facts=facts,
                analysis_date=analysis_date,
                mechanism_vector=mechanism,
            )
        )
        domains = self._domain_store.ensure(
            self._domain_compiler.compile(
                mechanism_vector=mechanism,
                timing_vector=timing,
            )
        )
        reading = self._reading_store.ensure(
            self._reading_projector.project(
                case_ref=case_ref,
                chart_version_ref=chart_ref,
                life_case_revision_ref=str(
                    workspace["life_case"]["life_case_revision_ref"]
                ),
                facts=facts,
                candidates=candidates,
                quant_vector=quant,
                source_review_vector=source_review,
                mechanism_vector=mechanism,
                timing_vector=timing,
                life_domain_vector=domains,
            )
        )
        return {
            "materialization_version": MINGLI_CASE_MATERIALIZATION_VERSION,
            "case_ref": case_ref,
            "subject_kind": subject_kind,
            "chart_version_ref": chart_ref,
            "life_case_revision_ref": workspace["life_case"][
                "life_case_revision_ref"
            ],
            "quant_vector_ref": quant.vector_ref,
            "source_review_vector_ref": source_review.vector_ref,
            "mechanism_vector_ref": mechanism.vector_ref,
            "timing_vector_ref": timing.vector_ref,
            "life_domain_vector_ref": domains.vector_ref,
            "reading_ref": reading.reading_ref,
            "reading_hash": reading.reading_hash,
            "fact_count": len(facts),
            "structural_candidate_count": len(candidates),
            "mechanism_candidate_count": len(mechanism.candidates),
            "timing_coordinate_count": len(timing.coordinates),
            "source_review_required_count": source_review.review_required_count,
            "domain_signal_statuses": {
                item.domain: item.signal_status for item in domains.observations
            },
            "unresolved_dimensions": list(reading.unresolved_dimensions),
        }
