#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from v17_rebirth.backend.services.v18_1_predictive_engine import predictive_service


def _source_digest(path: Path) -> str:
    try:
        import hashlib

        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Bazi KB-to-rule inflation audit for Wealth Knowledge Units.")
    parser.add_argument("--source", default="docs/bazi_knowledge/wealth/wealth_units_v1.md")
    parser.add_argument("--knowledge-id", default="")
    parser.add_argument("--all-wealth", action="store_true")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()

    source_path = Path(args.source)
    source_meta: dict[str, Any] = {
        "path": str(source_path),
        "exists": source_path.exists(),
        "sha256": _source_digest(source_path),
    }
    payload: dict[str, Any] = {
        "base_url": args.base_url,
        "model": args.model,
        "local_only": args.local_only,
        "source_markdown": source_meta,
    }
    results = []
    if args.knowledge_id:
        targets = [args.knowledge_id]
    else:
        units = predictive_service.list_bazi_knowledge_units(domain="wealth", limit=200)["items"]
        targets = [str(item["knowledge_id"]) for item in units] if args.all_wealth else ["wealth.019_combination_changes_stability"]
    for knowledge_id in targets:
        results.append(
            predictive_service.dry_run_bazi_knowledge_audit(
                knowledge_id,
                payload,
                actor_role="audit_script",
                actor_user_id=0,
            )
        )
    print(
        json.dumps(
            {
                "ok": True,
                "source": source_meta,
                "target_count": len(targets),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
