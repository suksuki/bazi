#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.knowledge.rule_extraction import (  # noqa: E402
    build_llm_rule_extraction_report,
    validate_llm_rule_extraction_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 bounded LLM rule extraction drafts.")
    parser.add_argument("--domain", default="")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.validate:
        payload = validate_llm_rule_extraction_report(args.domain, limit=args.limit)
    else:
        payload = build_llm_rule_extraction_report(args.domain, limit=args.limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") in {"ready", "empty", "pass"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
