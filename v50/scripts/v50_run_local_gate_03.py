from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliAgent, MingliContextCompiler, compile_chart_world
from core.mingli_agent.model_client import OllamaCognitiveModel
from product.agent_case_store import MemoryAgentCaseStore
from product.agent_command_service import BaselineCaseCommand, BaselineCaseCommandService


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "validation" / "fixtures"
CASE_PACK = FIXTURE_DIR / "local_gate_03_case_pack_v1.json"
TAXONOMY = FIXTURE_DIR / "synthetic_chart_taxonomy_v2.json"


class CountingCaseStore(MemoryAgentCaseStore):
    def __init__(self) -> None:
        super().__init__()
        self.reads = 0
        self.writes = 0
        self.lists = 0

    def save(self, **kwargs: Any) -> None:
        self.writes += 1
        super().save(**kwargs)

    def get(self, **kwargs: Any) -> dict[str, Any] | None:
        self.reads += 1
        return super().get(**kwargs)

    def list_for_user(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.lists += 1
        return super().list_for_user(**kwargs)


def run_local_gate(
    *,
    run_id: str,
    endpoint: str,
    model_name: str,
    timeout_seconds: int,
    output_root: Path,
) -> dict[str, Any]:
    pack = _load(CASE_PACK)
    taxonomy = _load(TAXONOMY)
    taxonomy_by_id = {item["case_id"]: item for item in taxonomy["cases"]}
    target = output_root / run_id
    target.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for selection in pack["cases"]:
        fixture = taxonomy_by_id[selection["case_id"]]
        print(json.dumps({"case_id": fixture["case_id"], "status": "running"}, ensure_ascii=False), flush=True)
        result = _run_case(
            fixture=fixture,
            selection=selection,
            endpoint=endpoint,
            model_name=model_name,
            timeout_seconds=timeout_seconds,
            target=target,
        )
        results.append(result)
        print(
            json.dumps(
                {
                    "case_id": fixture["case_id"],
                    "status": result["run_status"],
                    "elapsed_seconds": result["metrics"]["wall_elapsed_seconds"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    differentiation = _differentiation(results)
    summary = {
        "version": "deepbazi.local_gate_03_report.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "mac_local_real_model_isolated_case_store",
        "model": model_name,
        "endpoint": endpoint,
        "policy": {
            "max_output_tokens": 3200,
            "knowledge_material_limit": 5,
            "status": "provisional_local_baseline",
            "prompt_modified_during_run": False,
            "model_policy_modified_during_run": False,
        },
        "case_pack": pack,
        "summary": {
            "requested": len(results),
            "completed": sum(item["run_status"] == "completed" for item in results),
            "committed": sum(item["formal_insight_status"] == "committed" for item in results),
            "partial": sum(item["formal_insight_status"] == "partial" for item in results),
            "failed": sum(item["formal_insight_status"] == "failed" for item in results),
            "truncation_suspected": sum(item["metrics"]["truncation_suspected"] for item in results),
            "total_input_tokens": sum(item["metrics"]["input_tokens"] for item in results),
            "total_output_tokens": sum(item["metrics"]["output_tokens"] for item in results),
            "total_wall_seconds": round(sum(item["metrics"]["wall_elapsed_seconds"] for item in results), 2),
            "slowest_case_seconds": max((item["metrics"]["wall_elapsed_seconds"] for item in results), default=0),
        },
        "differentiation": differentiation,
        "cases": [
            {
                key: item[key]
                for key in (
                    "case_id",
                    "audit_role",
                    "pillars",
                    "day_master",
                    "run_status",
                    "formal_insight_status",
                    "first_look",
                    "whole_chart_thesis",
                    "primary_path",
                    "selected_hypothesis",
                    "metrics",
                    "case_directory",
                )
            }
            for item in results
        ],
        "boundaries": {
            "professional_mingli_quality_evaluated": False,
            "synthetic_cases_are_professional_gold": False,
            "domain_generation_performed": False,
            "tts_generation_performed": False,
            "production_database_modified": False,
            "remote_sync_performed": False,
        },
    }
    summary_path = target / "local_gate_03_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = target / "LOCAL_GATE_03_FIVE_CHART_RUN.md"
    markdown_path.write_text(_markdown(summary), encoding="utf-8")
    manifest = _manifest(target)
    manifest_path = target / "manifest.sha256.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary["artifacts"] = {
        "directory": str(target),
        "summary": str(summary_path),
        "markdown": str(markdown_path),
        "manifest": str(manifest_path),
    }
    return summary


def _run_case(
    *,
    fixture: dict[str, Any],
    selection: dict[str, Any],
    endpoint: str,
    model_name: str,
    timeout_seconds: int,
    target: Path,
) -> dict[str, Any]:
    case_id = str(fixture["case_id"])
    case_dir = target / case_id.replace(".", "_")
    case_dir.mkdir(parents=True, exist_ok=True)
    birth_payload = dict(fixture["birth_input"])
    birth_payload["birth_time"] = "12:00"
    birth = BirthInputCanonical.model_validate(birth_payload)
    world = compile_chart_world(
        reading_id=f"local-gate-03:{case_id}",
        birth_input=birth,
        include_research_fixture_prior=False,
    )
    context = MingliContextCompiler().compile(world=world, stage="baseline")
    model = OllamaCognitiveModel(
        base_url=endpoint,
        model=model_name,
        timeout_seconds=timeout_seconds,
        num_ctx=int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768")),
    )
    store = CountingCaseStore()
    agent = MingliAgent(model=model)
    command_service = BaselineCaseCommandService(agent=agent, case_store=store)
    events: list[dict[str, Any]] = []
    started = time.monotonic()
    error = ""
    result = None
    try:
        result = command_service.execute(
            BaselineCaseCommand(
                case_id=case_id,
                reading_id=world.reading_id,
                birth_input=birth,
                profile_id=f"audit-profile:{case_id}",
                user_id="local-gate-03",
                active_mode="research",
                world=world,
            ),
            on_event=lambda event_type, payload: events.append({"event_type": event_type, "payload": payload}),
        )
    except Exception as exc:  # noqa: BLE001 - the audit records every failed case without repair.
        error = f"{type(exc).__name__}:{exc}"
    elapsed = round(time.monotonic() - started, 2)
    stored = store.get(case_id=case_id, user_id="local-gate-03")
    raw = model.last_raw_response
    if raw:
        (case_dir / "raw_model_output.json").write_text(raw.rstrip() + "\n", encoding="utf-8")
    else:
        (case_dir / "raw_model_output.txt").write_text(error + "\n", encoding="utf-8")
    (case_dir / "selected_context.json").write_text(
        json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (case_dir / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if stored is not None:
        (case_dir / "stored_case.json").write_text(json.dumps(stored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result is None:
        case_result = {
            "case_id": case_id,
            "audit_role": selection["audit_role"],
            "selection_reason": selection["selection_reason"],
            "pillars": list(world.pillars),
            "day_master": world.pillars[2][0],
            "run_status": "failed",
            "formal_insight_status": "failed",
            "first_look": "",
            "whole_chart_thesis": "",
            "primary_path": "",
            "selected_hypothesis": "",
            "error": error,
            "metrics": {
                "wall_elapsed_seconds": elapsed,
                "input_tokens": 0,
                "output_tokens": 0,
                "knowledge_retrieval_count": len(context.knowledge_refs),
                "store_reads": store.reads,
                "store_writes": store.writes,
                "truncation_suspected": False,
            },
            "case_directory": str(case_dir),
        }
    else:
        cognition = result.record.cognition
        receipt = (result.record.stage_receipts or [{}])[-1]
        output_tokens = int(receipt.get("eval_count") or 0)
        route_limit = max((int(item.get("max_tokens") or 0) for item in result.record.model_routes), default=3200)
        case_result = {
            "case_id": case_id,
            "audit_role": selection["audit_role"],
            "selection_reason": selection["selection_reason"],
            "pillars": list(world.pillars),
            "day_master": world.pillars[2][0],
            "run_status": "completed",
            "formal_insight_status": "committed" if result.committed else "partial",
            "first_look": cognition.first_look,
            "whole_chart_thesis": cognition.whole_chart_thesis,
            "primary_path": cognition.work_path.path_statement,
            "selected_hypothesis": cognition.selected_hypothesis_id,
            "hypotheses": [item.model_dump(mode="json") for item in cognition.hypotheses],
            "conditions": list(cognition.work_path.success_conditions),
            "uncertainties": list(cognition.unresolved_questions),
            "review": result.record.review.model_dump(mode="json"),
            "assertion_gate": result.record.assertion_gate.model_dump(mode="json"),
            "validation": result.validation.model_dump(mode="json"),
            "metrics": {
                "wall_elapsed_seconds": elapsed,
                "input_tokens": int(receipt.get("prompt_eval_count") or 0),
                "output_tokens": output_tokens,
                "max_output_tokens": route_limit,
                "output_budget_utilization": round(output_tokens / route_limit, 4) if route_limit else 0,
                "knowledge_retrieval_count": len(context.knowledge_refs),
                "selected_fact_count": len(context.fact_refs),
                "excluded_knowledge_count": context.excluded_knowledge_count,
                "store_reads": store.reads,
                "store_writes": store.writes,
                "domain_generations": len(result.record.domain_explorations),
                "truncation_suspected": bool(output_tokens and route_limit and output_tokens >= route_limit - 8),
            },
            "case_directory": str(case_dir),
        }
        (case_dir / "structured_result.json").write_text(
            json.dumps(case_result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return case_result


def _differentiation(results: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [item for item in results if item["run_status"] == "completed"]
    pairs = []
    for left, right in combinations(completed, 2):
        pairs.append({
            "left": left["case_id"],
            "right": right["case_id"],
            "first_look_bigram_similarity": _bigram_similarity(left["first_look"], right["first_look"]),
            "thesis_bigram_similarity": _bigram_similarity(left["whole_chart_thesis"], right["whole_chart_thesis"]),
            "path_bigram_similarity": _bigram_similarity(left["primary_path"], right["primary_path"]),
        })
    return {
        "unique_selected_hypotheses": len({item["selected_hypothesis"] for item in completed}),
        "max_first_look_similarity": max((item["first_look_bigram_similarity"] for item in pairs), default=0),
        "max_thesis_similarity": max((item["thesis_bigram_similarity"] for item in pairs), default=0),
        "max_path_similarity": max((item["path_bigram_similarity"] for item in pairs), default=0),
        "pairwise": pairs,
        "machine_boundary": "Similarity is a template-risk signal, not a professional correctness score.",
    }


def _bigram_similarity(left: str, right: str) -> float:
    def grams(value: str) -> set[str]:
        compact = "".join(value.split())
        return {compact[index:index + 2] for index in range(max(0, len(compact) - 1))}

    a, b = grams(left), grams(right)
    return round(len(a & b) / len(a | b), 4) if a and b else 0.0


def _manifest(root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "manifest.sha256.json"):
        files.append({
            "path": str(path.relative_to(root)),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return {"version": "deepbazi.local_gate_03_manifest.v1", "files": files}


def _markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# LOCAL-GATE-03 Five-chart Real-model Run",
        "",
        f"- Run: `{report['run_id']}`",
        f"- Model: `{report['model']}`",
        f"- Completed: `{summary['completed']}/{summary['requested']}`",
        f"- Committed / partial / failed: `{summary['committed']} / {summary['partial']} / {summary['failed']}`",
        f"- Input / output tokens: `{summary['total_input_tokens']} / {summary['total_output_tokens']}`",
        f"- Total / slowest: `{summary['total_wall_seconds']}s / {summary['slowest_case_seconds']}s`",
        f"- Suspected truncations: `{summary['truncation_suspected']}`",
        "",
        "## Cases",
        "",
    ]
    for item in report["cases"]:
        lines.extend([
            f"### {item['audit_role']} — {' '.join(item['pillars'])}",
            "",
            f"- Status: `{item['formal_insight_status']}`",
            f"- First look: {item['first_look'] or '(none)' }",
            f"- Thesis: {item['whole_chart_thesis'] or '(none)' }",
            f"- Path: {item['primary_path'] or '(none)' }",
            f"- Selected hypothesis: `{item['selected_hypothesis'] or '(none)'}`",
            "",
        ])
    lines.extend([
        "## Differentiation signal",
        "",
        f"- Unique selected hypotheses: `{report['differentiation']['unique_selected_hypotheses']}`",
        f"- Max first-look similarity: `{report['differentiation']['max_first_look_similarity']}`",
        f"- Max thesis similarity: `{report['differentiation']['max_thesis_similarity']}`",
        f"- Max path similarity: `{report['differentiation']['max_path_similarity']}`",
        "",
        "This run is local product and epistemic evidence. It is not a professional Mingli approval.",
        "",
    ])
    return "\n".join(lines)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LOCAL-GATE-03 against five anonymous charts.")
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--endpoint", default=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"))
    parser.add_argument("--model", default=os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b"))
    parser.add_argument("--timeout-seconds", type=int, default=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")))
    parser.add_argument("--output-root", type=Path, default=ROOT / "reports" / "local-gate-03")
    args = parser.parse_args()
    report = run_local_gate(
        run_id=args.run_id,
        endpoint=args.endpoint,
        model_name=args.model,
        timeout_seconds=args.timeout_seconds,
        output_root=args.output_root,
    )
    print(json.dumps({"status": report["summary"], "artifacts": report["artifacts"]}, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["completed"] == report["summary"]["requested"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
