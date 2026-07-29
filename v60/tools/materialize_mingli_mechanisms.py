from __future__ import annotations

from abu_v60.db import engine
from abu_v60.mingli import (
    MingliMechanismEvidenceCompiler,
    MingliMechanismVectorStore,
    MingliQuantFoundationCompiler,
    MingliQuantVectorStore,
)
from abu_v60.mingli.service import MingliCaseService
from abu_v60.provenance import canonical_json
from sqlalchemy import text


def main() -> None:
    cases = _all_cases()
    case_service = MingliCaseService(engine)
    quant_compiler = MingliQuantFoundationCompiler()
    quant_store = MingliQuantVectorStore(engine)
    mechanism_compiler = MingliMechanismEvidenceCompiler()
    mechanism_store = MingliMechanismVectorStore(engine)
    results: list[dict[str, object]] = []
    for case_ref, owner_account_ref in cases:
        workspace = case_service.workspace(
            account_ref=owner_account_ref,
            case_ref=case_ref,
        )
        chart_ref = str(workspace["chart"]["chart_version_ref"])
        quant = quant_store.ensure(
            quant_compiler.compile(
                case_ref=case_ref,
                chart_version_ref=chart_ref,
                pillars=workspace["chart"]["pillars"],
                facts=workspace["facts"],
            )
        )
        mechanism = mechanism_store.ensure(
            mechanism_compiler.compile(
                quant_vector=quant,
                facts=workspace["facts"],
            )
        )
        results.append(
            {
                "case_ref": case_ref,
                "chart_version_ref": chart_ref,
                "quant_vector_ref": quant.vector_ref,
                "mechanism_vector_ref": mechanism.vector_ref,
                "candidate_count": len(mechanism.candidates),
            }
        )
    print(canonical_json({"materialized_cases": results}))


def _all_cases() -> list[tuple[str, str]]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT case_ref, owner_account_ref
                FROM mingli.cases
                WHERE status = 'ACTIVE'
                ORDER BY case_ref
                """
            )
        ).all()
    return [(str(row[0]), str(row[1])) for row in rows]


if __name__ == "__main__":
    main()
