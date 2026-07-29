from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
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
from abu_v60.mingli.timing import MingliTimingEvidenceCompiler
from abu_v60.mingli.timing_store import MingliTimingVectorStore
from abu_v60.provenance import canonical_json, content_hash, stable_ref

CORPUS_QUALIFICATION_VERSION = "v60.mingli-corpus-qualification.001"
QUALIFIED_SUBJECT_KINDS = frozenset({"HUMAN_OWNER", "HUMAN_REFERENCE"})


class MingliCorpusQualificationError(ValueError):
    pass


class MingliCorpusQualificationService:
    """Materialize and record bounded coverage across an authorized private corpus."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._cases = MingliCaseService(engine)
        self._candidates = StructuralCandidateCompiler()
        self._quant_compiler = MingliQuantFoundationCompiler()
        self._quant_store = MingliQuantVectorStore(engine)
        self._mechanism_compiler = MingliMechanismEvidenceCompiler()
        self._mechanism_store = MingliMechanismVectorStore(engine)
        self._timing_compiler = MingliTimingEvidenceCompiler()
        self._timing_store = MingliTimingVectorStore(engine)
        self._domain_compiler = MingliLifeDomainEvidenceCompiler()
        self._domain_store = MingliLifeDomainVectorStore(engine)
        self._reading_projector = MingliReadingProjector()
        self._reading_store = MingliReadingStore(engine)

    def qualify(
        self,
        *,
        account_ref: str,
        analysis_date: date,
    ) -> dict[str, Any]:
        cases = tuple(
            item
            for item in self._cases.list_cases(account_ref=account_ref)
            if item["status"] == "ACTIVE"
            and item["subject_kind"] in QUALIFIED_SUBJECT_KINDS
        )
        if not cases:
            raise MingliCorpusQualificationError("mingli_corpus_has_no_qualified_cases")

        results = tuple(
            self._materialize_case(
                account_ref=account_ref,
                case_ref=str(item["case_ref"]),
                subject_kind=str(item["subject_kind"]),
                analysis_date=analysis_date,
            )
            for item in cases
        )
        coverage = self._coverage(results)
        identity = {
            "run_version": CORPUS_QUALIFICATION_VERSION,
            "account_ref": account_ref,
            "analysis_date": analysis_date.isoformat(),
            "case_results": results,
            "coverage": coverage,
        }
        run_ref = stable_ref("v60-mingli-corpus-qualification", identity)
        run_hash = content_hash(identity)
        owner_case_count = sum(item["subject_kind"] == "HUMAN_OWNER" for item in results)
        reference_case_count = len(results) - owner_case_count
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.corpus_qualification_runs
                        (run_ref, run_version, account_ref, analysis_date,
                         case_count, owner_case_count, reference_case_count,
                         case_results_json, coverage_json, run_hash)
                    VALUES
                        (:run_ref, :run_version, :account_ref, :analysis_date,
                         :case_count, :owner_case_count, :reference_case_count,
                         CAST(:case_results AS jsonb), CAST(:coverage AS jsonb),
                         :run_hash)
                    ON CONFLICT (run_ref) DO NOTHING
                    """
                ),
                {
                    "run_ref": run_ref,
                    "run_version": CORPUS_QUALIFICATION_VERSION,
                    "account_ref": account_ref,
                    "analysis_date": analysis_date,
                    "case_count": len(results),
                    "owner_case_count": owner_case_count,
                    "reference_case_count": reference_case_count,
                    "case_results": canonical_json(results),
                    "coverage": canonical_json(coverage),
                    "run_hash": run_hash,
                },
            )
            persisted = (
                connection.execute(
                    text(
                        """
                        SELECT run_version, account_ref, analysis_date,
                               case_count, owner_case_count, reference_case_count,
                               case_results_json, coverage_json, run_hash
                        FROM mingli.corpus_qualification_runs
                        WHERE run_ref = :run_ref
                        """
                    ),
                    {"run_ref": run_ref},
                )
                .mappings()
                .one()
            )
        expected = {
            "run_version": CORPUS_QUALIFICATION_VERSION,
            "account_ref": account_ref,
            "analysis_date": analysis_date,
            "case_count": len(results),
            "owner_case_count": owner_case_count,
            "reference_case_count": reference_case_count,
            "case_results_json": list(results),
            "coverage_json": coverage,
            "run_hash": run_hash,
        }
        if dict(persisted) != expected:
            raise MingliCorpusQualificationError("mingli_corpus_run_identity_conflict")
        return {
            "run_ref": run_ref,
            "run_hash": run_hash,
            "analysis_date": analysis_date.isoformat(),
            "case_count": len(results),
            "owner_case_count": owner_case_count,
            "reference_case_count": reference_case_count,
            "coverage": coverage,
            "cases": list(results),
            "probability_claim": None,
            "accuracy_claim": None,
        }

    def _materialize_case(
        self,
        *,
        account_ref: str,
        case_ref: str,
        subject_kind: str,
        analysis_date: date,
    ) -> dict[str, Any]:
        workspace = self._cases.workspace(
            account_ref=account_ref,
            case_ref=case_ref,
        )
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
        mechanism = self._mechanism_store.ensure(
            self._mechanism_compiler.compile(
                quant_vector=quant,
                facts=facts,
            )
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
                mechanism_vector=mechanism,
                timing_vector=timing,
                life_domain_vector=domains,
            )
        )
        return {
            "case_ref": case_ref,
            "subject_kind": subject_kind,
            "chart_version_ref": chart_ref,
            "life_case_revision_ref": workspace["life_case"][
                "life_case_revision_ref"
            ],
            "quant_vector_ref": quant.vector_ref,
            "mechanism_vector_ref": mechanism.vector_ref,
            "timing_vector_ref": timing.vector_ref,
            "life_domain_vector_ref": domains.vector_ref,
            "reading_ref": reading.reading_ref,
            "fact_count": len(facts),
            "structural_candidate_count": len(candidates),
            "mechanism_candidate_count": len(mechanism.candidates),
            "timing_coordinate_count": len(timing.coordinates),
            "domain_signal_statuses": {
                item.domain: item.signal_status for item in domains.observations
            },
            "unresolved_dimensions": list(reading.unresolved_dimensions),
        }

    @staticmethod
    def _coverage(results: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        domains = ("career", "wealth", "relationship")
        return {
            "cases_with_structural_candidates": sum(
                item["structural_candidate_count"] > 0 for item in results
            ),
            "cases_with_mechanism_candidates": sum(
                item["mechanism_candidate_count"] > 0 for item in results
            ),
            "cases_with_timing_coordinates": sum(
                item["timing_coordinate_count"] > 0 for item in results
            ),
            "domain_signal_counts": {
                domain: {
                    status: sum(
                        item["domain_signal_statuses"][domain] == status
                        for item in results
                    )
                    for status in sorted(
                        {
                            item["domain_signal_statuses"][domain]
                            for item in results
                        }
                    )
                }
                for domain in domains
            },
            "unresolved_dimensions": sorted(
                {
                    dimension
                    for item in results
                    for dimension in item["unresolved_dimensions"]
                }
            ),
            "professional_verdicts_emitted": 0,
            "probabilities_emitted": 0,
        }
