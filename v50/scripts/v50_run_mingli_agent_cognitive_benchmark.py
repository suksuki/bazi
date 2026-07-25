from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.life_domains import LifeDomain
from core.mingli_agent import MingliAgent, compile_chart_world


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v1.json"
DEFAULT_CASE_TYPES = (
    "month_command_dominant",
    "bridge_node_dominant",
    "converter_dominant",
    "hidden_stem_dark_line",
)
BRANCH_TIME = {
    "子时": "00:30", "丑时": "02:30", "寅时": "04:30", "卯时": "06:30",
    "辰时": "08:30", "巳时": "10:30", "午时": "12:30", "未时": "14:30",
    "申时": "16:30", "酉时": "18:30", "戌时": "20:30", "亥时": "22:30",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run chart-specific Mingli Agent cognitive benchmarks.")
    parser.add_argument("--case-types", nargs="*", default=list(DEFAULT_CASE_TYPES))
    parser.add_argument("--output-dir", default=str(ROOT / "reports" / "mingli_agent"))
    args = parser.parse_args()

    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    by_type = {item["case_type"]: item for item in taxonomy["cases"]}
    agent = MingliAgent()
    results: list[dict[str, Any]] = []
    for case_type in args.case_types:
        fixture = by_type[case_type]
        started = time.time()
        try:
            birth = _birth_input(fixture["birth_input"])
            world = compile_chart_world(
                reading_id=f"benchmark:{fixture['case_id']}",
                birth_input=birth,
                analysis_year=datetime.now().year,
                include_research_fixture_prior=False,
            )
            record = agent.first_reading(case_id=fixture["case_id"], world=world)
            cognition = record.cognition
            career = agent.explore_domain(world=world, record=record, domain=LifeDomain.CAREER)
            wealth = agent.explore_domain(world=world, record=record, domain=LifeDomain.WEALTH)
            results.append({
                "case_id": fixture["case_id"],
                "case_type": case_type,
                "chart": fixture["chart"],
                "status": "passed" if record.review.passed else "review_failed",
                "elapsed_seconds": round(time.time() - started, 1),
                "first_look": cognition.first_look,
                "whole_chart_thesis": cognition.whole_chart_thesis,
                "selected_hypothesis": next(
                    (item.name for item in cognition.hypotheses if item.hypothesis_id == cognition.selected_hypothesis_id),
                    cognition.selected_hypothesis_id,
                ),
                "work_path": cognition.work_path.path_statement,
                "probe": cognition.next_probe.question,
                "career_assertions": [item.claim for item in career.reading.assertions],
                "wealth_assertions": [item.claim for item in wealth.reading.assertions],
                "review": record.review.model_dump(mode="json"),
                "stage_receipts": record.stage_receipts,
                "context_manifest": record.context_manifest,
            })
        except Exception as exc:  # noqa: BLE001 - benchmark must continue across cases.
            results.append({
                "case_id": fixture["case_id"],
                "case_type": case_type,
                "chart": fixture["chart"],
                "status": "failed",
                "elapsed_seconds": round(time.time() - started, 1),
                "error": repr(exc),
            })
        print(json.dumps({"case_type": case_type, "status": results[-1]["status"]}, ensure_ascii=False), flush=True)

    passed = [item for item in results if item["status"] == "passed"]
    similarities = [
        {
            "left": left["case_type"],
            "right": right["case_type"],
            "thesis_bigram_similarity": round(_bigram_similarity(left["whole_chart_thesis"], right["whole_chart_thesis"]), 3),
        }
        for left, right in combinations(passed, 2)
    ]
    max_similarity = max((item["thesis_bigram_similarity"] for item in similarities), default=0.0)
    unique_hypotheses = len({item["selected_hypothesis"] for item in passed})
    required_passes = len(results) if len(results) <= 3 else 3
    diversity_ok = len(results) == 1 or (max_similarity < 0.72 and unique_hypotheses >= 2)
    report = {
        "run_id": f"mingli-agent-benchmark-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "model": os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b"),
        "pattern_model": os.getenv("V50_MINGLI_PATTERN_MODEL", "qwen3.6:27b"),
        "domain_model": os.getenv("V50_MINGLI_DOMAIN_MODEL", "gemma4:latest"),
        "status": "passed" if len(passed) >= required_passes and diversity_ok else "partial",
        "boundary": {
            "training_performed": False,
            "weights_modified": False,
            "deterministic_brain_used": False,
            "template_fallback_used": False,
        },
        "summary": {
            "cases_requested": len(results),
            "cases_passed": len(passed),
            "unique_selected_hypotheses": unique_hypotheses,
            "max_thesis_bigram_similarity": max_similarity,
        },
        "pairwise_similarity": similarities,
        "cases": results,
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "mingli_agent_cognitive_benchmark_v1.json"
    md_path = output_dir / "mingli_agent_cognitive_benchmark_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"report": str(md_path), "status": report["status"]}, ensure_ascii=False), flush=True)
    return 0 if report["status"] == "passed" else 2


def _birth_input(payload: dict[str, Any]) -> BirthInputCanonical:
    payload = dict(payload)
    payload["birth_time"] = BRANCH_TIME.get(str(payload.get("birth_time")), payload.get("birth_time") or "12:00")
    return BirthInputCanonical(**payload)


def _bigram_similarity(left: str, right: str) -> float:
    def grams(value: str) -> set[str]:
        compact = "".join(value.split())
        return {compact[index:index + 2] for index in range(max(0, len(compact) - 1))}

    a, b = grams(left), grams(right)
    return 0.0 if not a or not b else len(a & b) / len(a | b)


def _markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Mingli Agent Cognitive Benchmark v1",
        "",
        f"- Status: `{report['status']}`",
        f"- Model: `{report['model']}`",
        f"- Pattern/work model: `{report['pattern_model']}`",
        f"- Domain model: `{report['domain_model']}`",
        f"- Cases passed: `{summary['cases_passed']}/{summary['cases_requested']}`",
        f"- Unique primary hypotheses: `{summary['unique_selected_hypotheses']}`",
        f"- Max thesis similarity: `{summary['max_thesis_bigram_similarity']}`",
        "",
        "## Case Results",
        "",
    ]
    for item in report["cases"]:
        lines.extend([
            f"### {item['case_type']} — {item['chart']}",
            "",
            f"- Status: `{item['status']}`",
            f"- Elapsed: `{item['elapsed_seconds']}s`",
        ])
        if item["status"] == "passed":
            lines.extend([
                f"- First look: {item['first_look']}",
                f"- Thesis: {item['whole_chart_thesis']}",
                f"- Primary hypothesis: {item['selected_hypothesis']}",
                f"- Work path: {item['work_path']}",
                f"- Probe: {item['probe']}",
            ])
        else:
            lines.append(f"- Error: `{item.get('error', 'review_failed')}`")
        lines.append("")
    lines.extend([
        "## Boundary",
        "",
        "This run did not train models, modify weights, invoke the retired deterministic Brain, or use a template reading fallback.",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
