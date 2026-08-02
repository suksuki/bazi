from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.materialization import MingliCaseMaterializationService
from abu_v60.mingli.service import MingliCaseService
from abu_v60.provenance import canonical_json, content_hash, stable_ref

CORPUS_QUALIFICATION_VERSION = "v60.mingli-corpus-qualification.002"
QUALIFIED_SUBJECT_KINDS = frozenset({"HUMAN_OWNER", "HUMAN_REFERENCE"})


class MingliCorpusQualificationError(ValueError):
    pass


class MingliCorpusQualificationService:
    """Materialize and record bounded coverage across an authorized private corpus."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._cases = MingliCaseService(engine)
        self._materializer = MingliCaseMaterializationService(engine)

    def qualify(
        self,
        *,
        account_ref: str,
        analysis_date: date,
    ) -> dict[str, Any]:
        cases = tuple(
            item
            for item in self._cases.list_cases(account_ref=account_ref)
            if item["status"] == "ACTIVE" and item["subject_kind"] in QUALIFIED_SUBJECT_KINDS
        )
        if not cases:
            raise MingliCorpusQualificationError("mingli_corpus_has_no_qualified_cases")

        results = tuple(
            self._materializer.materialize(
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
            "cases_with_source_relation_review": sum(
                item["source_review_required_count"] > 0 for item in results
            ),
            "domain_signal_counts": {
                domain: {
                    status: sum(
                        item["domain_signal_statuses"][domain] == status for item in results
                    )
                    for status in sorted(
                        {item["domain_signal_statuses"][domain] for item in results}
                    )
                }
                for domain in domains
            },
            "unresolved_dimensions": sorted(
                {dimension for item in results for dimension in item["unresolved_dimensions"]}
            ),
            "professional_verdicts_emitted": 0,
            "probabilities_emitted": 0,
        }
