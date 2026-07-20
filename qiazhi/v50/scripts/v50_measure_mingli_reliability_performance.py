from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.life_domains import LifeDomain
from core.mingli_agent import MingliAgent, compile_chart_world
from core.mingli_agent.contracts import MingliCognitiveDraft, MingliCognitiveRecord
from core.mingli_agent.reasoner import review_cognition
from core.mingli_agent.reliability import cognition_semantic_signature


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure real baseline reuse, domain preview, and exact cache latency.")
    parser.add_argument(
        "--checkpoint",
        default="reports/mingli-reliability-gate-v1/live-stability-v2/mingli_reliability_stability_checkpoint.jsonl",
    )
    parser.add_argument("--fixture", default="data/validation/fixtures/synthetic_chart_taxonomy_v2.json")
    parser.add_argument("--case-id", default="c2.complete_triple_combination.01")
    parser.add_argument("--domain", choices=[item.value for item in LifeDomain if item is not LifeDomain.WHOLE_CHART], default="career")
    parser.add_argument("--question", default="这张盘的职业价值主要通过什么路径形成？")
    parser.add_argument("--base-url", default=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"))
    parser.add_argument("--model", default=os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b"))
    parser.add_argument("--output-dir", default="reports/mingli-reliability-gate-v1/live-performance")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["V50_MINGLI_AGENT_BASE_URL"] = args.base_url
    os.environ["V50_MINGLI_AGENT_MODEL"] = args.model
    os.environ["V50_MINGLI_DOMAIN_MODEL"] = args.model
    source = _fixture_case(Path(args.fixture), args.case_id)
    birth_payload = dict(source["birth_input"])
    if birth_payload.get("birth_time") == "explicit":
        birth_payload["birth_time"] = "12:00"
    birth = BirthInputCanonical.model_validate(birth_payload)
    world = compile_chart_world(
        reading_id=f"reliability-performance:{args.case_id}",
        birth_input=birth,
        include_research_fixture_prior=False,
    )
    saved = _checkpoint_row(Path(args.checkpoint), args.case_id)
    cognition = MingliCognitiveDraft.model_validate(saved["raw_cognition"])
    review = review_cognition(draft=cognition, world=world, model=f"baseline:{args.model}")
    if not review.commit_eligible:
        raise SystemExit(f"selected_baseline_not_reliable:{review.disposition}")
    signature = cognition_semantic_signature(cognition)
    record = MingliCognitiveRecord(
        record_id=f"performance-{signature}",
        case_id=f"performance:{args.case_id}",
        world_id=world.world_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        model=f"baseline:{args.model}",
        cognition=cognition,
        review=review,
        reliability_disposition=review.disposition,
        reliability_signature=signature,
    )
    agent = MingliAgent()
    domain = LifeDomain(args.domain)
    stage_times: dict[str, float] = {}
    stage_payloads: dict[str, dict[str, Any]] = {}
    started = time.perf_counter()

    def on_stage(event_type: str, payload: dict[str, Any]) -> None:
        stage_times.setdefault(event_type, round(time.perf_counter() - started, 3))
        stage_payloads[event_type] = payload

    exploration = agent.explore_domain(
        world=world,
        record=record,
        domain=domain,
        user_question=args.question,
        baseline_insight_id="baseline-performance-v1",
        baseline_case_version="v1",
        on_stage=on_stage,
    )
    completed = round(time.perf_counter() - started, 3)
    cache_events: list[str] = []
    cache_seconds: float | None = None
    cache_same_generated_at = False
    if exploration.review.commit_eligible and not exploration.case_revision_candidate:
        cached_record = record.model_copy(update={
            "domain_explorations": {domain: exploration},
        })
        cache_started = time.perf_counter()
        cached = agent.explore_domain(
            world=world,
            record=cached_record,
            domain=domain,
            user_question=args.question,
            baseline_insight_id="baseline-performance-v1",
            baseline_case_version="v1",
            on_stage=lambda event_type, _payload: cache_events.append(event_type),
        )
        cache_seconds = round(time.perf_counter() - cache_started, 6)
        cache_same_generated_at = cached.generated_at == exploration.generated_at
    report = {
        "version": "deepbazi.mingli_reliability_performance.v1",
        "case_id": args.case_id,
        "pillars": world.pillars,
        "domain": domain.value,
        "question": args.question,
        "model": args.model,
        "baseline": {
            "record_id": record.record_id,
            "semantic_signature": signature,
            "disposition": review.disposition,
        },
        "observed": {
            "baseline_reuse_visible_seconds": stage_times.get("domain_baseline_reused"),
            "domain_first_meaningful_preview_seconds": stage_times.get("domain_preview_ready"),
            "domain_complete_seconds": completed,
            "domain_disposition": exploration.review.disposition,
            "domain_commit_eligible": exploration.review.commit_eligible,
            "domain_review": exploration.review.model_dump(mode="json"),
            "domain_reading": exploration.reading.model_dump(mode="json"),
            "semantic_repair_attempted": bool(exploration.context_manifest.get("semantic_repair_attempted")),
            "domain_preview_line": (stage_payloads.get("domain_preview_ready") or {}).get("preview_line"),
            "exact_cache_reuse_seconds": cache_seconds,
            "exact_cache_event": cache_events,
            "exact_cache_reused": "domain_cache_reused" in cache_events,
            "exact_cache_same_generated_at": cache_same_generated_at,
            "model_metrics": getattr(agent.domain_model, "last_metrics", {}),
        },
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "live_llm_used": True,
            "performance_measurement_only": True,
        },
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "mingli_reliability_performance_v1.json"
    md_path = output_dir / "mingli_reliability_performance_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(md_path)
    return 0


def _fixture_case(path: Path, case_id: str) -> dict[str, Any]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return next(item for item in fixture["cases"] if item["case_id"] == case_id)


def _checkpoint_row(path: Path, case_id: str) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return next(item for item in rows if item.get("case_id") == case_id and item.get("status") == "reliable")


def _markdown(report: dict[str, Any]) -> str:
    observed = report["observed"]
    return "\n".join([
        "# Mingli Reliability Gate v1 — Live Performance",
        "",
        f"- Chart: `{report['case_id']}` / `{' · '.join(report['pillars'])}`",
        f"- Domain: `{report['domain']}`",
        f"- Baseline disposition: `{report['baseline']['disposition']}`",
        f"- Baseline reuse visible: `{observed['baseline_reuse_visible_seconds']}s`",
        f"- Domain first meaningful preview: `{observed['domain_first_meaningful_preview_seconds']}s`",
        f"- Domain complete: `{observed['domain_complete_seconds']}s`",
        f"- Exact cache reuse: `{observed['exact_cache_reuse_seconds']}s` (`{observed['exact_cache_reused']}`)",
        f"- Domain disposition: `{observed['domain_disposition']}`",
        "",
        "## Preview",
        "",
        observed["domain_preview_line"] or "No fact-safe streamed preview was emitted.",
        "",
        "## Interpretation boundary",
        "",
        "This is a transport and gate measurement. It does not establish that the domain interpretation is professionally correct.",
        "",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
