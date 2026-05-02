#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate V20 knowledge-authored active rules against synthetic coverage and corpus priors.")
    parser.add_argument("--domain", default="", help="Optional domain filter.")
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--summary", action="store_true", help="Print a compact review summary.")
    args = parser.parse_args()

    payload = build_knowledge_rule_validation_report(args.domain, limit=args.limit)
    if args.summary:
        payload = _summary(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _summary(report: dict[str, object]) -> dict[str, object]:
    rows = [row for row in report.get("definitions", ()) if isinstance(row, dict)]
    return {
        "version": "v20.knowledge_rule_validation_summary.v1",
        "status": report.get("status", ""),
        "ok": report.get("ok", False),
        "domain": report.get("domain", ""),
        "definition_count": report.get("definition_count", 0),
        "synthetic_covered_count": report.get("synthetic_covered_count", 0),
        "missing_synthetic_count": report.get("missing_synthetic_count", 0),
        "corpus_signal_count": report.get("corpus_signal_count", 0),
        "state_counts": report.get("state_counts", {}),
        "review_actions": report.get("review_actions", {}),
        "rules": [
            {
                "source_knowledge_id": row.get("source_knowledge_id", ""),
                "domain": row.get("domain", ""),
                "portrait": row.get("portrait", ""),
                "question": row.get("question", ""),
                "validation_state": row.get("validation_state", ""),
                "next_review_action": row.get("next_review_action", ""),
                "support_quality": row.get("support_quality", ""),
            }
            for row in rows
        ],
        "runtime_mutation": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
