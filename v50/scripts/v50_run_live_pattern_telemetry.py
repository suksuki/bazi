from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliContextCompiler, compile_chart_world
from core.mingli_agent.contracts import PatternHypothesisDraft
from core.mingli_agent.reasoner import (
    _apply_scope_boundary,
    _filter_evidence_refs,
    _pattern_hypothesis_prompt,
    _pattern_stage_errors,
    _sanitize_pattern_alternatives,
    default_pattern_model,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_TYPES = ("climate_regulation_dominant", "mediation_path")


def run_live_pattern_telemetry(*, case_types: tuple[str, ...]) -> dict[str, Any]:
    taxonomy = json.loads(
        (ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json").read_text(encoding="utf-8")
    )
    by_type = {item["case_type"]: item for item in taxonomy["cases"] if item["case_id"].endswith(".01")}
    model = default_pattern_model()
    compiler = MingliContextCompiler()
    results = []
    for case_type in case_types:
        fixture = by_type[case_type]
        payload = dict(fixture["birth_input"])
        payload["birth_time"] = "12:00"
        world = compile_chart_world(
            reading_id=f"live-pattern-telemetry:{fixture['case_id']}",
            birth_input=BirthInputCanonical.model_validate(payload),
            include_research_fixture_prior=False,
        )
        context = compiler.compile(world=world, stage="pattern")
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
            results.append(
                {
                    "case_id": fixture["case_id"],
                    "case_type": case_type,
                    "status": "passed" if not errors else "review_failed",
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                    "context_hash": context.content_hash,
                    "context_payload_bytes": len(json.dumps(context.payload, ensure_ascii=False).encode("utf-8")),
                    "fact_count": len(context.fact_refs),
                    "critical_attention_omissions": context.attention_receipt.critical_omission_refs,
                    "hypothesis_count": len(draft.hypotheses),
                    "selected_hypothesis_id": draft.selected_hypothesis_id,
                    "first_look": draft.first_look,
                    "review_errors": errors,
                    "transport_metrics": model.last_metrics,
                }
            )
        except Exception as exc:  # noqa: BLE001 - telemetry records bounded model failures.
            results.append(
                {
                    "case_id": fixture["case_id"],
                    "case_type": case_type,
                    "status": "failed",
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                    "error": f"{type(exc).__name__}:{exc}",
                    "transport_metrics": model.last_metrics,
                }
            )
    passed = sum(item["status"] == "passed" for item in results)
    return {
        "version": "deepbazi.live_pattern_telemetry.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed == len(results) else "partial",
        "model": model.model,
        "endpoint": model.base_url,
        "observed_data": {
            "case_count": len(results),
            "passed_count": passed,
            "review_failed_count": sum(item["status"] == "review_failed" for item in results),
            "transport_failed_count": sum(item["status"] == "failed" for item in results),
        },
        "case_results": results,
        "interpretation": "This smoke run measures real qualified-model Pattern behavior and transport metrics; it is not an expert correctness score.",
        "boundary_status": {
            "expected_contract_visible_to_model": False,
            "training_performed": False,
            "weights_modified": False,
            "prompt_tuned_from_results": False,
            "model_downgraded": False,
        },
    }


def _write(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "live_pattern_telemetry_v1.json"
    md_path = output_dir / "live_pattern_telemetry_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Live Pattern Telemetry v1",
        "",
        f"- Status: `{report['status']}`",
        f"- Model: `{report['model']}`",
        f"- Endpoint: `{report['endpoint']}`",
        "",
    ]
    for item in report["case_results"]:
        lines.extend(
            [
                f"## {item['case_type']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Elapsed: `{item['elapsed_ms']} ms`",
                f"- Transport: `{json.dumps(item.get('transport_metrics', {}), ensure_ascii=False)}`",
                f"- First look: {item.get('first_look', '')}",
                f"- Review errors: `{item.get('review_errors', item.get('error', ''))}`",
                "",
            ]
        )
    lines.extend(["## Boundaries", "", "```json", json.dumps(report["boundary_status"], ensure_ascii=False, indent=2), "```", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run two leak-free live Pattern telemetry cases.")
    parser.add_argument("--case-types", nargs="*", default=list(DEFAULT_CASE_TYPES))
    parser.add_argument("--output-dir", default=str(ROOT / "reports/live-pattern-telemetry/v1"))
    args = parser.parse_args()
    report = run_live_pattern_telemetry(case_types=tuple(args.case_types))
    paths = _write(report, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
