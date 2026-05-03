#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.knowledge.rule_extraction import (  # noqa: E402
    build_llm_rule_extraction_report,
    validate_llm_rule_extraction_report,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 bounded LLM rule extraction drafts.")
    parser.add_argument("--domain", default="")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--persist-local", action="store_true", help="Write report.json and drafts.jsonl under V20 runtime.")
    parser.add_argument("--apply-postgres", action="store_true", help="Upsert accepted/fallback LLM artifacts into Postgres.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.validate:
            payload = validate_llm_rule_extraction_report(args.domain, limit=args.limit)
        else:
            payload = build_llm_rule_extraction_report(args.domain, limit=args.limit)
        if args.persist_local:
            payload["local_persistence"] = _persist_local(payload, args.run_id or _default_run_id(args.domain))
        if args.apply_postgres:
            payload["postgres_persistence"] = _persist_postgres(payload, args.run_id or _default_run_id(args.domain))
        return payload

    return run_and_print(
        _run,
        command="extract_rules_llm.py",
        args=args,
        runtime_mutation=args.persist_local or args.apply_postgres,
    )


def _default_run_id(domain: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = domain.strip() or "all"
    return f"v20_llm_rule_extraction_{suffix}_{stamp}"


def _persist_local(payload: dict[str, object], run_id: str) -> dict[str, object]:
    output_dir = ROOT / "v20" / ".runtime" / "local" / "llm" / "rule_extraction" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.json"
    drafts_path = output_dir / "drafts.jsonl"
    status_path = output_dir / "status.json"
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    drafts = _draft_rows(payload)
    with drafts_path.open("w", encoding="utf-8") as handle:
        for row in drafts:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    status = {
        "version": "v20.llm_rule_extraction_local_persistence.v1",
        "status": "persisted",
        "run_id": run_id,
        "report_path": str(report_path),
        "drafts_path": str(drafts_path),
        "candidate_count": payload.get("candidate_count", 0),
        "accepted_count": payload.get("accepted_count", 0),
        "fallback_count": payload.get("fallback_count", 0),
        "runtime_mutation": True,
        "guardrails": ["LOCAL_ARTIFACT_ONLY", "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE"],
    }
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return status


def _persist_postgres(payload: dict[str, object], run_id: str) -> dict[str, object]:
    url = os.getenv("V20_DATABASE_URL", "")
    result = {
        "version": "v20.llm_rule_extraction_postgres_persistence.v1",
        "run_id": run_id,
        "database_url_present": bool(url),
        "runtime_mutation": True,
        "guardrails": [
            "EXPLICIT_APPLY_POSTGRES_REQUIRED",
            "NO_SECRET_VALUES_RENDERED",
            "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE",
        ],
    }
    if not url:
        return result | {"status": "blocked_missing_V20_DATABASE_URL", "upserted": 0}
    try:
        import psycopg2
        from psycopg2.extras import Json
    except Exception as exc:
        return result | {"status": "blocked_missing_psycopg2", "error": str(exc), "upserted": 0}
    drafts = _draft_rows(payload)
    rows = []
    for row in drafts:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_knowledge_id", "unknown"))
        draft_result = row.get("draft_result", {})
        validation_status = str(draft_result.get("status", "unknown")) if isinstance(draft_result, dict) else "unknown"
        artifact_id = _artifact_id(run_id, source_id, row)
        rows.append((artifact_id, "rule_extraction_draft", validation_status, Json(row)))
    try:
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS v20_llm_artifacts (
                      artifact_id text PRIMARY KEY,
                      task_name text NOT NULL,
                      validation_status text NOT NULL,
                      created_at timestamptz NOT NULL DEFAULT now(),
                      updated_at timestamptz NOT NULL DEFAULT now(),
                      payload jsonb NOT NULL
                    )
                    """
                )
                for row in rows:
                    cur.execute(
                        """
                        INSERT INTO v20_llm_artifacts (artifact_id, task_name, validation_status, payload)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (artifact_id) DO UPDATE SET
                          task_name = EXCLUDED.task_name,
                          validation_status = EXCLUDED.validation_status,
                          payload = EXCLUDED.payload,
                          updated_at = now()
                        """,
                        row,
                    )
            conn.commit()
    except Exception as exc:
        return result | {"status": "blocked_postgres_error", "error": str(exc), "upserted": 0}
    return result | {"status": "persisted", "upserted": len(rows), "table": "v20_llm_artifacts"}


def _artifact_id(run_id: str, source_id: str, payload: dict[str, object]) -> str:
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return f"v20.llm.rule_extraction.{run_id}.{source_id}.{digest}"


def _draft_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    drafts = payload.get("drafts", ())
    return [row for row in drafts if isinstance(row, dict)] if isinstance(drafts, (list, tuple)) else []


if __name__ == "__main__":
    raise SystemExit(main())
