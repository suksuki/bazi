from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from core.contracts import BirthInputCanonical
from core.mingli_agent import compile_chart_world
from core.mingli_agent.contracts import MingliCognitiveDraft
from core.mingli_agent.reasoner import review_cognition
from scripts.v50_run_mingli_reliability_gate import _build_report, _markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay saved Mingli drafts through the current reliability gate.")
    parser.add_argument(
        "--checkpoint",
        default="reports/mingli-reliability-gate-v1/live-stability/mingli_reliability_stability_checkpoint.jsonl",
    )
    parser.add_argument("--fixture", default="data/validation/fixtures/synthetic_chart_taxonomy_v2.json")
    parser.add_argument("--output-dir", default="reports/mingli-reliability-gate-v1/gate-replay")
    parser.add_argument("--model", default="qwen3.5:35b")
    parser.add_argument("--base-url", default="http://dblife.com:11888")
    args = parser.parse_args()

    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    by_id = {item["case_id"]: item for item in fixture["cases"]}
    rows = [json.loads(line) for line in Path(args.checkpoint).read_text(encoding="utf-8").splitlines() if line]
    worlds = {}
    replayed = []
    for row in rows:
        case_id = row["case_id"]
        if case_id not in worlds:
            birth_payload = {**by_id[case_id]["birth_input"]}
            if birth_payload.get("birth_time") == "explicit":
                birth_payload["birth_time"] = "12:00"
            worlds[case_id] = compile_chart_world(
                reading_id=f"reliability:{case_id}",
                birth_input=BirthInputCanonical.model_validate(birth_payload),
                include_research_fixture_prior=False,
            )
        updated = dict(row)
        updated["live_gate_status"] = row["status"]
        if row["status"] != "runtime_failed":
            review = review_cognition(
                draft=MingliCognitiveDraft.model_validate(row["raw_cognition"]),
                world=worlds[case_id],
                model=f"replay:{args.model}",
            )
            updated["status"] = review.disposition
            updated["commit_eligible"] = review.commit_eligible
            updated["review"] = review.model_dump(mode="json")
        replayed.append(updated)

    now = datetime.now(timezone.utc).isoformat()
    report = _build_report(
        rows=replayed,
        started_at=now,
        finished_at=now,
        base_url=args.base_url,
        model=args.model,
        repeats=max(row["repeat"] for row in replayed),
    )
    report["version"] = "deepbazi.mingli_reliability_gate_replay.v1"
    report["status_changes"] = [
        {
            "case_id": row["case_id"],
            "repeat": row["repeat"],
            "from": row["live_gate_status"],
            "to": row["status"],
        }
        for row in replayed
        if row.get("live_gate_status") != row["status"]
    ]
    report["boundary_status"]["live_llm_used"] = False
    report["boundary_status"]["saved_draft_replay_only"] = True

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "mingli_reliability_gate_replay_v1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "mingli_reliability_gate_replay_rows_v1.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in replayed), encoding="utf-8"
    )
    markdown = _markdown(report)
    if report["status_changes"]:
        markdown += "\n## Gate status changes after parser correction\n\n"
        markdown += "\n".join(
            f"- `{row['case_id']}` run {row['repeat']}: `{row['from']}` -> `{row['to']}`"
            for row in report["status_changes"]
        )
        markdown += "\n"
    path = output_dir / "mingli_reliability_gate_replay_v1.md"
    path.write_text(markdown, encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
