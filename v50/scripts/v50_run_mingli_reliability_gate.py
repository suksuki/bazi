from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliAgent, compile_chart_world


DEFAULT_CASE_IDS = (
    "c2.output_controls_pressure.01",
    "c2.climate_regulation_dominant.01",
    "c2.complete_triple_combination.01",
    "c2.output_to_wealth.01",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Mingli Reliability Gate stability audit.")
    parser.add_argument("--fixture", default="data/validation/fixtures/synthetic_chart_taxonomy_v2.json")
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--base-url", default=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"))
    parser.add_argument("--model", default=os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b"))
    parser.add_argument("--output-dir", default="reports/mingli-reliability-gate-v1/live-stability")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["V50_MINGLI_AGENT_BASE_URL"] = args.base_url
    os.environ["V50_MINGLI_AGENT_MODEL"] = args.model
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    by_id = {item["case_id"]: item for item in fixture["cases"]}
    case_ids = tuple(args.case_ids or DEFAULT_CASE_IDS)
    missing = [case_id for case_id in case_ids if case_id not in by_id]
    if missing:
        raise SystemExit(f"unknown_case_ids:{','.join(missing)}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "mingli_reliability_stability_checkpoint.jsonl"
    rows: list[dict[str, Any]] = []
    started_at = datetime.now(timezone.utc).isoformat()
    checkpoint_path.write_text("", encoding="utf-8")

    for case_id in case_ids:
        source = by_id[case_id]
        birth_payload = {**source["birth_input"]}
        if birth_payload.get("birth_time") == "explicit":
            birth_payload["birth_time"] = "12:00"
        birth = BirthInputCanonical.model_validate(birth_payload)
        world = compile_chart_world(
            reading_id=f"reliability:{case_id}",
            birth_input=birth,
            include_research_fixture_prior=False,
        )
        for repeat in range(1, args.repeats + 1):
            started = time.perf_counter()
            stage_elapsed: dict[str, float] = {}

            def on_stage(event_type: str, _payload: dict[str, Any]) -> None:
                stage_elapsed.setdefault(event_type, round(time.perf_counter() - started, 3))

            try:
                record = MingliAgent().first_baseline_reading(
                    case_id=f"reliability:{case_id}:run-{repeat}",
                    world=world,
                    on_stage=on_stage,
                )
                elapsed = time.perf_counter() - started
                row = _record_row(
                    case_id=case_id,
                    repeat=repeat,
                    pillars=[birth.year_pillar, birth.month_pillar, birth.day_pillar, birth.hour_pillar],
                    elapsed=elapsed,
                    record=record,
                    stage_elapsed=stage_elapsed,
                )
            except Exception as exc:  # noqa: BLE001 - audit must preserve failures and continue.
                row = {
                    "case_id": case_id,
                    "repeat": repeat,
                    "pillars": [birth.year_pillar, birth.month_pillar, birth.day_pillar, birth.hour_pillar],
                    "status": "runtime_failed",
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "error": f"{type(exc).__name__}:{exc}",
                }
            rows.append(row)
            with checkpoint_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(
                f"[{len(rows)}/{len(case_ids) * args.repeats}] {case_id} run {repeat}: "
                f"{row['status']} {row['elapsed_seconds']}s",
                flush=True,
            )

    report = _build_report(
        rows=rows,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc).isoformat(),
        base_url=args.base_url,
        model=args.model,
        repeats=args.repeats,
    )
    json_path = output_dir / "mingli_reliability_stability_audit_v1.json"
    markdown_path = output_dir / "mingli_reliability_stability_audit_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    print(markdown_path)
    return 0


def _record_row(
    *,
    case_id: str,
    repeat: int,
    pillars: list[str],
    elapsed: float,
    record,
    stage_elapsed: dict[str, float],
) -> dict[str, Any]:
    cognition = record.cognition
    selected = next(
        (item for item in cognition.hypotheses if item.hypothesis_id == cognition.selected_hypothesis_id),
        cognition.hypotheses[0],
    )
    alternatives = [item for item in cognition.hypotheses if item.hypothesis_id != selected.hypothesis_id]
    stage_metrics = [
        {
            key: receipt.get(key)
            for key in (
                "stage",
                "duration_ms",
                "transport_total_ms",
                "prompt_eval_count",
                "prompt_eval_duration_ms",
                "eval_count",
                "eval_duration_ms",
                "response_bytes",
            )
        }
        for receipt in record.stage_receipts
    ]
    return {
        "case_id": case_id,
        "repeat": repeat,
        "pillars": pillars,
        "status": record.review.disposition,
        "commit_eligible": record.review.commit_eligible,
        "elapsed_seconds": round(elapsed, 3),
        "first_meaningful_preview_seconds": stage_elapsed.get("baseline_preview_ready"),
        "draft_ready_seconds": stage_elapsed.get("baseline_draft_ready"),
        "semantic_signature": record.reliability_signature,
        "core_claims": {
            "center_of_gravity": cognition.whole_chart_thesis,
            "primary_hypothesis": selected.name,
            "primary_thesis": selected.thesis,
            "primary_confidence": selected.confidence,
            "work_path": cognition.work_path.path_statement,
            "success_conditions": cognition.work_path.success_conditions,
            "failure_conditions": cognition.work_path.failure_conditions,
            "strategy_dimensions": [
                {
                    "lens": item.lens,
                    "scope": item.scope,
                    "question": item.question_answered,
                    "candidate": item.candidate,
                    "role": item.role,
                    "confidence": item.confidence,
                }
                for item in cognition.useful_god_reasoning
            ],
            "competing_hypotheses": [
                {"name": item.name, "thesis": item.thesis, "confidence": item.confidence}
                for item in alternatives
            ],
            "uncertainty": cognition.unresolved_questions,
        },
        "review": record.review.model_dump(mode="json"),
        "stage_metrics": stage_metrics,
        "raw_cognition": cognition.model_dump(mode="json"),
    }


def _build_report(
    *,
    rows: list[dict[str, Any]],
    started_at: str,
    finished_at: str,
    base_url: str,
    model: str,
    repeats: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_id"]].append(row)
    elapsed = [row["elapsed_seconds"] for row in rows if row["status"] != "runtime_failed"]
    previews = [
        row["first_meaningful_preview_seconds"]
        for row in rows
        if row.get("first_meaningful_preview_seconds") is not None
    ]
    cases = []
    for case_id, case_rows in grouped.items():
        valid = [row for row in case_rows if row["status"] != "runtime_failed"]
        primary_names = [row["core_claims"]["primary_hypothesis"] for row in valid]
        statuses = [row["status"] for row in valid]
        strategy_by_lens: dict[str, list[str]] = defaultdict(list)
        for row in valid:
            for item in row["core_claims"]["strategy_dimensions"]:
                strategy_by_lens[item["lens"]].append(f"{item['candidate']} · {item['role']}")
        cases.append({
            "case_id": case_id,
            "pillars": case_rows[0]["pillars"],
            "runs": case_rows,
            "observed": {
                "status_values": statuses,
                "status_consistent": len(set(statuses)) <= 1,
                "primary_hypothesis_values": primary_names,
                "primary_label_consistent": len(set(primary_names)) <= 1,
                "strategy_values_by_lens": dict(strategy_by_lens),
                "exact_semantic_signature_count": len({row["semantic_signature"] for row in valid}),
            },
        })
    return {
        "version": "deepbazi.mingli_reliability_stability_audit.v1",
        "started_at": started_at,
        "finished_at": finished_at,
        "model": model,
        "base_url": base_url,
        "repeats_per_case": repeats,
        "case_count": len(cases),
        "run_count": len(rows),
        "status_counts": _counts(row["status"] for row in rows),
        "performance": {
            "first_meaningful_preview_median_seconds": round(statistics.median(previews), 3) if previews else None,
            "first_meaningful_preview_p95_seconds": round(_percentile(previews, 0.95), 3) if previews else None,
            "median_seconds": round(statistics.median(elapsed), 3) if elapsed else None,
            "p95_seconds": round(_percentile(elapsed, 0.95), 3) if elapsed else None,
            "min_seconds": min(elapsed) if elapsed else None,
            "max_seconds": max(elapsed) if elapsed else None,
        },
        "cases": cases,
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "global_policy_promoted": False,
            "live_llm_used": True,
            "stability_audit_only": True,
        },
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Mingli Reliability Gate v1 — Live Stability Audit",
        "",
        f"- Model: `{report['model']}`",
        f"- Runs: `{report['run_count']}` ({report['case_count']} charts x {report['repeats_per_case']})",
        f"- Status counts: `{json.dumps(report['status_counts'], ensure_ascii=False)}`",
        f"- Median / p95: `{report['performance']['median_seconds']}s / {report['performance']['p95_seconds']}s`",
        "- First meaningful preview median / p95: "
        f"`{_seconds(report['performance']['first_meaningful_preview_median_seconds'])} / "
        f"{_seconds(report['performance']['first_meaningful_preview_p95_seconds'])}`",
        "",
        "> This report records observed model output. It is not a professional expert verdict and does not convert synthetic charts into real-world gold.",
        "",
    ]
    for case in report["cases"]:
        lines.extend([
            f"## {case['case_id']}",
            "",
            f"Pillars: `{' · '.join(case['pillars'])}`",
            "",
            "| Core judgment | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Machine observation |",
            "|---|---|---|---|---|---|---|",
        ])
        runs = case["runs"]
        lines.append(_table_row("Gate state", [row["status"] for row in runs], case["observed"]["status_consistent"]))
        lines.append(_table_row("Primary hypothesis", [_short(row.get("core_claims", {}).get("primary_hypothesis", "runtime failure"), 36) for row in runs], case["observed"]["primary_label_consistent"]))
        lines.append(_table_row("Work path", [_short(row.get("core_claims", {}).get("work_path", row.get("error", "")), 72) for row in runs], None))
        lines.append(_table_row("Success condition", [_short((row.get("core_claims", {}).get("success_conditions") or [""])[0], 54) for row in runs], None))
        lines.append(_table_row("Failure condition", [_short((row.get("core_claims", {}).get("failure_conditions") or [""])[0], 54) for row in runs], None))
        lines.append(_table_row("Strategy dimensions", [_short("；".join(f"{item['lens']}={item['candidate']}" for item in row.get("core_claims", {}).get("strategy_dimensions", [])), 72) for row in runs], None))
        lines.append(_table_row("Main alternative", [_short(((row.get("core_claims", {}).get("competing_hypotheses") or [{}])[0]).get("name", ""), 36) for row in runs], None))
        lines.append(_table_row("Uncertainty", [_short((row.get("core_claims", {}).get("uncertainty") or [""])[0], 54) for row in runs], None))
        lines.extend(["", f"Exact semantic signatures: `{case['observed']['exact_semantic_signature_count']}`", ""])
    return "\n".join(lines)


def _table_row(label: str, values: list[str], consistent: bool | None) -> str:
    padded = [*values[:5], *([""] * max(0, 5 - len(values)))]
    observation = "consistent" if consistent is True else "drift detected" if consistent is False else "requires professional comparison"
    cells = [label, *(_escape_table(value) for value in padded), observation]
    return "| " + " | ".join(cells) + " |"


def _short(value: str, limit: int) -> str:
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _seconds(value: float | None) -> str:
    return "not measured" if value is None else f"{value}s"


def _escape_table(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _counts(values) -> dict[str, int]:
    output: dict[str, int] = defaultdict(int)
    for value in values:
        output[str(value)] += 1
    return dict(output)


def _percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * ratio)))
    return ordered[index]


if __name__ == "__main__":
    raise SystemExit(main())
