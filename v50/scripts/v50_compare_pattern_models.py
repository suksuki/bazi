from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliContextCompiler, compile_chart_world
from core.mingli_agent.contracts import PatternHypothesisDraft
from core.mingli_agent.reasoner import (
    OllamaCognitiveModel,
    _apply_scope_boundary,
    _filter_evidence_refs,
    _pattern_hypothesis_prompt,
    _pattern_stage_errors,
    _review_hypothesis_space,
    _sanitize_pattern_alternatives,
)


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json"
DEFAULT_CASE_IDS = ("c2.month_command_dominant.01", "c2.complete_triple_combination.01")


def compare_pattern_models(
    *,
    endpoint: str,
    models: list[str],
    case_ids: list[str],
    timeout_seconds: int,
    num_ctx: int,
) -> dict[str, Any]:
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    cases = {item["case_id"]: item for item in taxonomy["cases"]}
    missing = sorted(set(case_ids) - set(cases))
    if missing:
        raise ValueError(f"unknown_case_ids:{','.join(missing)}")

    rows: list[dict[str, Any]] = []
    for model_name in models:
        model = OllamaCognitiveModel(
            base_url=endpoint,
            model=model_name,
            timeout_seconds=timeout_seconds,
            num_ctx=num_ctx,
        )
        for case_id in case_ids:
            fixture = cases[case_id]
            birth_payload = dict(fixture["birth_input"])
            birth_payload["birth_time"] = "12:00"
            world = compile_chart_world(
                reading_id=f"pattern-model-compare:{model_name}:{case_id}",
                birth_input=BirthInputCanonical.model_validate(birth_payload),
                include_research_fixture_prior=False,
            )
            context = MingliContextCompiler().compile(world=world, stage="pattern")
            started = time.monotonic()
            try:
                draft = model.generate(
                    prompt=_pattern_hypothesis_prompt(world, context_payload=context.payload),
                    schema=PatternHypothesisDraft,
                    temperature=0.0,
                    thinking=False,
                    max_tokens=2600,
                )
                draft = _sanitize_pattern_alternatives(
                    _filter_evidence_refs(_apply_scope_boundary(draft), world=world),
                    world=world,
                )
                errors = _pattern_stage_errors(pattern=draft, world=world, context=context)
                comparison = _review_hypothesis_space(pattern=draft, context=context)
                accepted = not errors and comparison.passed
                rows.append({
                    "model": model_name,
                    "case_id": case_id,
                    "case_type": fixture["case_type"],
                    "status": "accepted" if accepted else "review_failed",
                    "elapsed_seconds": round(time.monotonic() - started, 2),
                    "first_look": draft.first_look,
                    "whole_chart_thesis": draft.whole_chart_thesis,
                    "selected_hypothesis_id": draft.selected_hypothesis_id,
                    "hypothesis_count": len(draft.hypotheses),
                    "review_errors": errors,
                    "hypothesis_review": comparison.model_dump(mode="json"),
                    "transport_metrics": model.last_metrics,
                })
            except Exception as exc:  # noqa: BLE001 - comparison records failures without repairing policy.
                rows.append({
                    "model": model_name,
                    "case_id": case_id,
                    "case_type": fixture["case_type"],
                    "status": "failed",
                    "elapsed_seconds": round(time.monotonic() - started, 2),
                    "error": f"{type(exc).__name__}:{exc}",
                    "transport_metrics": model.last_metrics,
                })

    summaries = []
    for model_name in models:
        model_rows = [row for row in rows if row["model"] == model_name]
        accepted = [row for row in model_rows if row["status"] == "accepted"]
        summaries.append({
            "model": model_name,
            "accepted_cases": len(accepted),
            "total_cases": len(model_rows),
            "acceptance_rate": round(len(accepted) / len(model_rows), 4) if model_rows else 0.0,
            "average_elapsed_seconds": round(sum(row["elapsed_seconds"] for row in model_rows) / len(model_rows), 2) if model_rows else None,
            "average_accepted_elapsed_seconds": round(sum(row["elapsed_seconds"] for row in accepted) / len(accepted), 2) if accepted else None,
        })
    return {
        "version": "deepbazi.pattern_model_comparison.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "case_ids": case_ids,
        "summaries": summaries,
        "cases": rows,
        "decision": {
            "automatic_promotion_allowed": False,
            "expert_blind_review_required": True,
            "note": "Deterministic review and latency can nominate a candidate; they cannot prove professional Mingli superiority.",
        },
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "runtime_rules_modified": False,
            "prompt_modified": False,
            "model_promoted": False,
            "pattern_only": True,
        },
    }


def _write(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "pattern_model_comparison_v1.json"
    md_path = output_dir / "pattern_model_comparison_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Pattern Model Comparison v1", "", f"Endpoint: `{report['endpoint']}`", "", "## Summary", ""]
    for item in report["summaries"]:
        lines.append(
            f"- `{item['model']}`: accepted `{item['accepted_cases']}/{item['total_cases']}`, "
            f"average `{item['average_elapsed_seconds']}s`"
        )
    lines.extend(["", "## Cases", ""])
    for item in report["cases"]:
        lines.extend([
            f"### {item['model']} / {item['case_id']}",
            "",
            f"- Status: `{item['status']}`",
            f"- Elapsed: `{item['elapsed_seconds']}s`",
            f"- First look: {item.get('first_look', '')}",
            f"- Thesis: {item.get('whole_chart_thesis', '')}",
            f"- Error: `{item.get('error', '')}`",
            "",
        ])
    lines.extend([
        "## Decision Boundary",
        "",
        "This report never promotes a model automatically. Professional blind review remains required.",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare cognitive Pattern candidates on identical sealed contexts.")
    parser.add_argument("--endpoint", default="http://dblife.com:11888")
    parser.add_argument("--models", nargs="+", default=["qwen3.5:35b", "gemma4:latest"])
    parser.add_argument("--case-ids", nargs="+", default=list(DEFAULT_CASE_IDS))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--output-dir", default=str(ROOT / "reports/pattern-model-comparison/v1"))
    args = parser.parse_args()
    report = compare_pattern_models(
        endpoint=args.endpoint.rstrip("/"),
        models=args.models,
        case_ids=args.case_ids,
        timeout_seconds=args.timeout_seconds,
        num_ctx=args.num_ctx,
    )
    paths = _write(report, Path(args.output_dir))
    print(json.dumps({"reports": [str(path) for path in paths], "summaries": report["summaries"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
