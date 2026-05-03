#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.knowledge.rule_library import (  # noqa: E402
    build_knowledge_rule_library,
    validate_knowledge_rule_library,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the V20 knowledge-authored active rule library.")
    parser.add_argument("--domain", default="", help="Optional domain filter, such as strength, wealth, career.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--validate", action="store_true", help="Run validation instead of printing the library.")
    parser.add_argument("--summary", action="store_true", help="Print a compact summary for human review.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.validate:
            payload = validate_knowledge_rule_library(args.domain, limit=args.limit)
            return payload | {"status": payload.get("status", "pass")}
        payload = build_knowledge_rule_library(args.domain, limit=args.limit)
        return _summary(payload) if args.summary else payload

    return run_and_print(
        _run,
        command="run_knowledge_rule_library.py",
        args=args,
        runtime_mutation=False,
    )


def _summary(library: dict[str, object]) -> dict[str, object]:
    definitions = [row for row in library.get("definitions", ()) if isinstance(row, dict)]
    return {
        "version": "v20.knowledge_rule_library_summary.v1",
        "status": library.get("status", ""),
        "domain": library.get("domain", ""),
        "definition_count": library.get("definition_count", 0),
        "atom_count": library.get("atom_count", 0),
        "portrait_output_count": library.get("portrait_output_count", 0),
        "question_output_count": library.get("question_output_count", 0),
        "runtime_allowed_count": library.get("runtime_allowed_count", 0),
        "rules": [
            {
                "rule_key": row.get("rule_key", ""),
                "domain": row.get("domain", ""),
                "source_knowledge_id": row.get("source_knowledge_id", ""),
                "atoms": len(row.get("condition_atoms", ())),
                "portrait": _first_title(row.get("portrait_outputs", ()), "label"),
                "question": _first_title(row.get("question_outputs", ()), "title"),
                "validation_state": row.get("validation_state", ""),
                "activation_status": row.get("activation_status", ""),
            }
            for row in definitions
        ],
        "runtime_mutation": False,
    }


def _first_title(rows: object, key: str) -> str:
    if not isinstance(rows, (list, tuple)) or not rows:
        return ""
    first = rows[0]
    if not isinstance(first, dict):
        return ""
    return str(first.get(key, ""))


if __name__ == "__main__":
    raise SystemExit(main())
