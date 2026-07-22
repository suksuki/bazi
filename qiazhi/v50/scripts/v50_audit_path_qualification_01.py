from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from core.mingli_agent.contracts import ChartWorldInstance, WorkPathReasoning
from core.mingli_agent.path_bridge import bind_structured_path_candidate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"
DEFAULT_OUTPUT = ROOT / ".runtime" / "path-qualification-01"
RUN_VERSION = "deepbazi.path_qualification_01.v1"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def classify_case_payload(payload: dict[str, Any]) -> dict[str, Any]:
    life_case = payload.get("life_case") if isinstance(payload.get("life_case"), dict) else {}
    record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
    cognition = record.get("cognition") if isinstance(record.get("cognition"), dict) else {}
    work_path = cognition.get("work_path") if isinstance(cognition.get("work_path"), dict) else None
    assertions = [
        item
        for item in life_case.get("path_assertions") or []
        if isinstance(item, dict)
    ]
    statuses = {str(item.get("status") or "") for item in assertions}
    if "committed" in statuses:
        return _result("committed", ["path_assertion.committed"])
    if "legacy_unresolved" in statuses:
        reasons = [
            str(item.get("unresolved_reason") or "legacy_unresolved.reason_unknown")
            for item in assertions
            if item.get("status") == "legacy_unresolved"
        ]
        return _result("legacy_unresolved", reasons)
    if work_path is None:
        return _result("never_evaluated", ["work_path.not_evaluated"])

    try:
        work = WorkPathReasoning.model_validate(work_path)
        world = ChartWorldInstance.model_validate(payload.get("world"))
        _, receipt = bind_structured_path_candidate(work_path=work, world=world)
    except Exception as exc:  # noqa: BLE001 - classification must preserve invalid historical rows.
        return _result(
            "persistence_or_version_failure",
            [f"qualification_input_invalid:{type(exc).__name__}"],
        )

    if receipt.accepted_segment_count > 0:
        return _result(
            "persistence_or_version_failure",
            [
                "validated_segments_not_persisted",
                *receipt.reason_codes,
            ],
        )
    if work.structured_candidate is not None or work.candidate_path_refs or receipt.rejected_refs:
        return _result("segment_rejected", list(receipt.reason_codes))
    return _result("no_candidate", ["work_path.natural_language_without_candidate"])


def run_audit(*, database_url: str, output_dir: Path) -> dict[str, Any]:
    import psycopg

    with psycopg.connect(database_url) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        with conn.cursor() as cur:
            cur.execute(
                "SELECT version, boundary FROM v50_schema_version WHERE id = %s",
                ("v50.schema",),
            )
            schema_row = cur.fetchone()
            cur.execute(
                "SELECT case_id, case_json FROM v50_mingli_agent_cases ORDER BY case_id"
            )
            rows = cur.fetchall()

    source_digest = canonical_hash([payload for _, payload in rows])
    categories: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    work_path_text_count = 0
    path_assertion_count = 0
    relation_assertion_count = 0

    for case_id, payload in rows:
        result = classify_case_payload(payload)
        categories[result["category"]] += 1
        reasons.update(result["reason_codes"])
        record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
        cognition = record.get("cognition") if isinstance(record.get("cognition"), dict) else {}
        work_path = cognition.get("work_path") if isinstance(cognition.get("work_path"), dict) else {}
        if str(work_path.get("path_statement") or "").strip():
            work_path_text_count += 1
        life_case = payload.get("life_case") if isinstance(payload.get("life_case"), dict) else {}
        path_assertion_count += len(life_case.get("path_assertions") or [])
        relation_assertion_count += len(life_case.get("relation_assertions") or [])
        records.append({
            "qualification_ref": hashlib.sha256(
                f"path-qualification-01|{case_id}".encode("utf-8")
            ).hexdigest()[:20],
            "category": result["category"],
            "reason_codes": result["reason_codes"],
        })

    expected_categories = {
        "never_evaluated",
        "no_candidate",
        "segment_rejected",
        "persistence_or_version_failure",
        "legacy_unresolved",
        "committed",
    }
    for category in expected_categories:
        categories.setdefault(category, 0)
    total = len(rows)
    accounted = sum(categories.values())
    committed = categories["committed"]
    summary = {
        "version": RUN_VERSION,
        "status": "PASS" if committed > 0 else "BLOCKED",
        "gate": "PATH-QUALIFICATION-01",
        "database_schema": {
            "version": str(schema_row[0]) if schema_row else "missing",
            "boundary": str(schema_row[1]) if schema_row else "missing",
        },
        "case_count": total,
        "accounted_case_count": accounted,
        "source_case_payload_hash": source_digest,
        "work_path_text_count": work_path_text_count,
        "path_assertion_count": path_assertion_count,
        "relation_assertion_count": relation_assertion_count,
        "categories": dict(sorted(categories.items())),
        "reason_distribution": dict(sorted(reasons.items())),
        "local_gate_04": "NOT_PASSED" if committed == 0 else "REQUIRES_REVIEW",
        "work_path_state": "unavailable_unconfirmed" if committed == 0 else "mixed",
        "llm_used": False,
        "writes_performed": False,
        "case_identifiers_disclosed": False,
        "records": records,
    }
    if accounted != total:
        raise RuntimeError(f"path_qualification_total_mismatch:{accounted}:{total}")

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "path_qualification_01_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "version": "deepbazi.path_qualification_01_manifest.v1",
        "command": (
            "PYTHONPATH=packages:apps python scripts/"
            "v50_audit_path_qualification_01.py"
        ),
        "summary_file": summary_path.name,
        "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        "source_case_payload_hash": source_digest,
        "writes_performed": False,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _result(category: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "category": category,
        "reason_codes": sorted(set(reasons or [f"{category}.reason_unknown"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only diagnosis of Cognitive to PathAssertion qualification."
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("V50_DATABASE_URL", DEFAULT_DATABASE_URL),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = run_audit(database_url=args.database_url, output_dir=args.output_dir)
    print(json.dumps({
        "status": summary["status"],
        "case_count": summary["case_count"],
        "categories": summary["categories"],
        "output_dir": str(args.output_dir),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
