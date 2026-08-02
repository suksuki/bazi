from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path
from typing import Any

from abu_v60.mingli import (
    MingliMechanismEvidenceCompiler,
    MingliQuantFoundationCompiler,
)
from abu_v60.mingli.calendar import ChartPillars
from abu_v60.mingli.compiler import compile_research_case
from abu_v60.provenance import canonical_json, content_hash
from sqlalchemy import create_engine, text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only mechanism evidence audit over every V50 profile."
    )
    parser.add_argument(
        "--output",
        default="artifacts/audits/v60-mingli-mechanism-dataset-v2.json",
    )
    args = parser.parse_args()
    source_url = os.getenv(
        "V50_SOURCE_DATABASE_URL",
        "postgresql+psycopg:///qiazhi_v50?host=/tmp",
    )
    source = create_engine(source_url, pool_pre_ping=True)
    rows = _read_profiles(source)
    records = [_compile_row(row) for row in rows]
    payload = _report(records)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    print(
        canonical_json(
            {
                "output": str(output.resolve()),
                "report_hash": content_hash(payload),
                "profiles": payload["profile_count"],
                "unique_charts": payload["unique_chart_count"],
                "candidate_distribution": payload["candidate_distribution"],
            }
        )
    )


def _read_profiles(engine: Any) -> list[dict[str, Any]]:
    with engine.begin() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        rows = (
            connection.execute(
                text(
                    """
                    SELECT profile_id, profile_fingerprint, calendar_type,
                           birth_date, birth_time, timezone, pillars, profile_json
                    FROM v50_bazi_profiles
                    WHERE deleted = false
                    ORDER BY profile_id
                    """
                )
            )
            .mappings()
            .all()
        )
    return [dict(row) for row in rows]


def _compile_row(row: dict[str, Any]) -> dict[str, Any]:
    ordered = tuple(str(item) for item in row["pillars"])
    chart = ChartPillars(
        year=ordered[0],
        month=ordered[1],
        day=ordered[2],
        hour=ordered[3],
    )
    case_ref = f"v50-read-only-audit:{row['profile_id']}"
    compiled = compile_research_case(
        case_ref=case_ref,
        chart=chart,
    )
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    compiler = MingliMechanismEvidenceCompiler()
    vector = compiler.compile(quant_vector=quant, facts=compiled.facts)
    replay = compiler.compile(
        quant_vector=quant,
        facts=tuple(reversed(compiled.facts)),
    )
    if replay.vector_hash != vector.vector_hash:
        raise RuntimeError(f"mechanism_replay_hash_mismatch:{row['profile_id']}")
    return {
        "source_profile_ref": f"v50.profile:{row['profile_id']}",
        "source_profile_fingerprint": str(row["profile_fingerprint"]),
        "chart_hash": compiled.chart_hash,
        "quant_vector_hash": quant.vector_hash,
        "mechanism_vector_hash": vector.vector_hash,
        "candidate_count": len(vector.candidates),
        "pattern_refs": sorted(item.pattern_ref for item in vector.candidates),
        "comparison_status": vector.comparison_status,
        "professional_verdict_allowed": vector.professional_verdict_allowed,
    }


def _report(records: list[dict[str, Any]]) -> dict[str, Any]:
    distribution = Counter(record["candidate_count"] for record in records)
    patterns = Counter(pattern for record in records for pattern in record["pattern_refs"])
    return {
        "report_version": "v60.mingli-mechanism-dataset-audit.002",
        "source_database": "qiazhi_v50",
        "source_access": "READ_ONLY",
        "runtime_dependency_created": False,
        "profile_count": len(records),
        "unique_chart_count": len({record["chart_hash"] for record in records}),
        "candidate_distribution": {
            str(count): frequency for count, frequency in sorted(distribution.items())
        },
        "pattern_coverage": dict(sorted(patterns.items())),
        "all_replay_hashes_stable": True,
        "all_professional_verdicts_denied": all(
            record["professional_verdict_allowed"] is False for record in records
        ),
        "records": records,
    }


if __name__ == "__main__":
    main()
