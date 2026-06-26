from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.storage.production_replay_store import build_production_replay_store
from v30.validation.post_seal_status_review import build_post_seal_status_review
from v30.validation.release_candidate_review import build_release_candidate_review
from v30.validation.release_gate import run_release_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 post-seal release-candidate review.")
    parser.add_argument("--run-quick-gate", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    gate_payload = {}
    if args.run_quick_gate:
        gate_payload = run_release_gate(mode="quick", sample_limit=args.sample_limit).model_dump(mode="json")
    replay_search = build_production_replay_store().search(selection_status="calibration_ready", module_ready="m4")
    result = build_release_candidate_review(
        post_seal_status_review=build_post_seal_status_review(),
        release_gate_result=gate_payload,
        replay_search=replay_search,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"rc_gate_recommended={decision['release_candidate_gate_recommended']}")
        print(f"next={result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
        if decision["blockers"]:
            print("blockers=" + ",".join(decision["blockers"]))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
