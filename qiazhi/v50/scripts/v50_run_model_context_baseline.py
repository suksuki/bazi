from __future__ import annotations

import argparse
import json
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliContextCompiler, ModelPolicyRouter, compile_chart_world


ROOT = Path(__file__).resolve().parents[1]


def build_model_context_baseline(
    *,
    endpoint: str,
    available_models: list[dict[str, Any]],
    running_models: list[dict[str, Any]],
) -> dict[str, Any]:
    routes = ModelPolicyRouter.from_env().manifest()
    available_names = {str(item.get("name") or item.get("model") or "") for item in available_models}
    assigned = {str(item["model"]) for item in routes}
    missing = sorted(assigned - available_names)
    context_rows = _context_rows()
    by_stage = {}
    for stage in sorted({row["stage"] for row in context_rows}):
        rows = [row for row in context_rows if row["stage"] == stage]
        by_stage[stage] = {
            "cases": len(rows),
            "avg_payload_bytes": round(mean(row["payload_bytes"] for row in rows)),
            "max_payload_bytes": max(row["payload_bytes"] for row in rows),
            "avg_fact_count": round(mean(row["fact_count"] for row in rows), 2),
            "max_fact_count": max(row["fact_count"] for row in rows),
            "critical_omission_count": sum(row["critical_omission_count"] for row in rows),
        }
    cognitive_models = {
        route["model"]
        for route in routes
        if route["role"] in {"whole_chart", "dual_lens", "domain", "case_revision"}
    }
    role_drift = len(cognitive_models) > 1
    return {
        "version": "deepbazi.model_context_baseline.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not missing and not role_drift else "partial",
        "endpoint": endpoint,
        "model_routes": routes,
        "available_models": available_models,
        "running_models": running_models,
        "context_baseline": by_stage,
        "observed_data": {
            "assigned_models": sorted(assigned),
            "missing_assigned_models": missing,
            "cognitive_models": sorted(cognitive_models),
            "cognitive_role_drift": role_drift,
            "fixture_case_count": len({row["case_id"] for row in context_rows}),
            "critical_attention_omissions": sum(row["critical_omission_count"] for row in context_rows),
            "running_vram_bytes": sum(int(item.get("size_vram") or 0) for item in running_models),
        },
        "interpretation": (
            "Model quality is protected by keeping one cognitive authority across whole-chart and domain stages. "
            "Latency work must use transport metrics and context measurements rather than model downgrades."
        ),
        "recommendation": (
            "Collect stage-level prompt/eval metrics on a small live run. Keep Gemma in expression/Abu wording and Qwen 8B in intake only."
        ),
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "model_downgraded": False,
            "server_configuration_modified": False,
            "live_generation_performed": False,
        },
    }


def _context_rows() -> list[dict[str, Any]]:
    taxonomy = json.loads(
        (ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json").read_text(encoding="utf-8")
    )
    compiler = MingliContextCompiler()
    rows = []
    for fixture in taxonomy["cases"]:
        payload = dict(fixture["birth_input"])
        payload["birth_time"] = "12:00"
        world = compile_chart_world(
            reading_id=f"model-baseline:{fixture['case_id']}",
            birth_input=BirthInputCanonical.model_validate(payload),
            include_research_fixture_prior=False,
        )
        for stage in ("pattern", "work_path", "prediction", "career", "wealth"):
            context = compiler.compile(world=world, stage=stage)
            rows.append(
                {
                    "case_id": fixture["case_id"],
                    "stage": stage,
                    "payload_bytes": len(json.dumps(context.payload, ensure_ascii=False).encode("utf-8")),
                    "fact_count": len(context.fact_refs),
                    "knowledge_count": len(context.knowledge_refs),
                    "critical_omission_count": len(context.attention_receipt.critical_omission_refs),
                }
            )
    return rows


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310 - configured local Ollama endpoint.
        return json.loads(response.read().decode("utf-8"))


def _write(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "model_context_baseline_v1.json"
    md_path = output_dir / "model_context_baseline_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    observed = report["observed_data"]
    md_path.write_text(
        "\n".join(
            [
                "# Model and Context Baseline v1",
                "",
                f"- Status: `{report['status']}`",
                f"- Endpoint: `{report['endpoint']}`",
                f"- Cognitive models: `{observed['cognitive_models']}`",
                f"- Cognitive role drift: `{observed['cognitive_role_drift']}`",
                f"- Missing assigned models: `{observed['missing_assigned_models']}`",
                f"- Critical attention omissions: `{observed['critical_attention_omissions']}`",
                f"- Running VRAM bytes: `{observed['running_vram_bytes']}`",
                "",
                "## Context",
                "",
                "```json",
                json.dumps(report["context_baseline"], ensure_ascii=False, indent=2),
                "```",
                "",
                "## Boundaries",
                "",
                "```json",
                json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit installed Ollama models and V50 context sizes without live generation.")
    parser.add_argument("--endpoint", default=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"))
    parser.add_argument("--output-dir", default=str(ROOT / "reports/model-context-baseline/v1"))
    args = parser.parse_args()
    endpoint = args.endpoint.rstrip("/")
    tags = _get_json(f"{endpoint}/api/tags").get("models", [])
    running = _get_json(f"{endpoint}/api/ps").get("models", [])
    report = build_model_context_baseline(endpoint=endpoint, available_models=tags, running_models=running)
    paths = _write(report, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
