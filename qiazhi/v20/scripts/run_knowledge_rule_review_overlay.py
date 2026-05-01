#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.decision.knowledge_bridge import build_knowledge_rule_review_overlay  # noqa: E402
from v20.learning.knowledge_rule_review_overlay import (  # noqa: E402
    read_knowledge_rule_review_overlay_artifact,
    write_knowledge_rule_review_overlay_artifact,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or write the V20 knowledge-rule review overlay artifact.")
    parser.add_argument("--write", action="store_true", help="Write a local runtime artifact.")
    parser.add_argument("--status", action="store_true", help="Read latest written local artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr.")
    args = parser.parse_args()

    progress = (lambda message: print(f"[v20-rule-overlay] {message}", file=sys.stderr, flush=True)) if args.progress else None
    if args.status:
        payload = read_knowledge_rule_review_overlay_artifact()
    elif args.write:
        payload = write_knowledge_rule_review_overlay_artifact(progress=progress)
    else:
        payload = build_knowledge_rule_review_overlay()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") not in {"fail", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
