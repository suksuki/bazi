from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_llm_live_smoke


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 bounded LLM live smoke.")
    parser.add_argument("--reading-id", default="v30-llm-live-smoke")
    parser.add_argument("--no-artifact", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_llm_live_smoke(
        reading_id=args.reading_id,
        write_artifact=not args.no_artifact,
    )
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(
            f"{result.run_id}: {result.status} "
            f"smoke_status={result.summary.get('smoke_status', '')} "
            f"call_status={result.summary.get('call_status', '')} "
            f"executed={result.summary.get('executed', False)}"
        )
        if result.artifact_uri:
            print(f"artifact={result.artifact_uri}")
        for failure in result.failures:
            print(f"- {failure}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
