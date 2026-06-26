#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.orchestrator_memory_training import build_orchestrator_memory_training_report  # noqa: E402
from v20.learning.orchestrator_policy_candidates import build_orchestrator_policy_candidate_report  # noqa: E402
from v20.learning.orchestrator_policy_observability_training import build_policy_observability_training_report  # noqa: E402
from v20.learning.orchestrator_policy_versioning import build_orchestrator_policy_version_candidate  # noqa: E402
from v20.learning.training_iteration import read_training_iteration_artifact  # noqa: E402
from v20.graph.question_source_graph import arbitrate_question_source_paths  # noqa: E402
from v20.learning.question_source_training import build_question_source_training_report  # noqa: E402
from v20.orchestrator.runtime_policy import build_runtime_policy_pointer  # noqa: E402
from v20.api.runtime import run_runtime_from_pillars  # noqa: E402
from v20.scripts.contract import run_and_print  # noqa: E402


def build_release_smoke_report(
    *,
    base_url: str = "http://127.0.0.1:9020",
    skip_http: bool = False,
    timeout_sec: float = 3.0,
) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    if not skip_http:
        checks.extend(_http_checks(base_url=base_url.rstrip("/"), timeout_sec=timeout_sec))
    checks.extend(_local_orchestrator_checks())
    failures = [row["check_key"] for row in checks if row.get("status") != "pass"]
    return {
        "version": "v20.release_smoke_report.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "check_count": len(checks),
        "failure_count": len(failures),
        "failures": failures,
        "checks": checks,
        "runtime_mutation": False,
        "guardrails": [
            "RELEASE_SMOKE_IS_READ_ONLY",
            "ORCHESTRATOR_POLICY_LOOP_SMOKE_COVERED",
            "NO_ROLLBACK_OR_ACTIVATE_FROM_RELEASE_SMOKE",
        ],
    }


def _http_checks(*, base_url: str, timeout_sec: float) -> list[dict[str, object]]:
    return [
        _expect_json(
            check_key="health_live",
            url=f"{base_url}/health/live",
            expected_version="v20.service_liveness.v1",
            timeout_sec=timeout_sec,
        ),
        _expect_json(
            check_key="health_ready",
            url=f"{base_url}/health/ready",
            expected_version="v20.service_readiness.v1",
            timeout_sec=timeout_sec,
        ),
        _expect_text(
            check_key="admin_static_policy_panel",
            url=f"{base_url}/v20/ui/admin.html",
            required=("Policy Observe", "policySwitchTimeline", "policyRecommendations", "questionSourceGraphPaths"),
            timeout_sec=timeout_sec,
        ),
        _expect_text(
            check_key="observe_static_policy_trend",
            url=f"{base_url}/v20/ui/workbench-observe.html",
            required=("policyTrainingTrend", "policyTrainingTimeline", "questionSourceGraphPaths", "Policy Observatory"),
            timeout_sec=timeout_sec,
        ),
    ]


def _local_orchestrator_checks() -> list[dict[str, object]]:
    pointer = build_runtime_policy_pointer(brain_memory_signal={})
    policy_report = build_policy_observability_training_report()
    iteration = read_training_iteration_artifact()
    memory_report = build_orchestrator_memory_training_report()
    policy_candidates = build_orchestrator_policy_candidate_report(
        memory_training_report=memory_report,
        policy_observability_report=policy_report,
    )
    policy_version = build_orchestrator_policy_version_candidate(candidate_report=policy_candidates)
    question_source_graph = arbitrate_question_source_paths(quality_signal=policy_candidates)
    runtime = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="release.smoke.question_source")
    question_source_report = runtime.get("question_source_ranking_report", {})
    question_source_training = build_question_source_training_report(reports=(question_source_report,))
    return [
        _pass_or_fail(
            "active_policy_pointer",
            bool(pointer.get("active_policy_version")) and pointer.get("version") == "v20.orchestrator_runtime_policy_pointer.v1",
            {
                "active_policy_version": pointer.get("active_policy_version", ""),
                "candidate_policy_version": pointer.get("candidate_policy_version", ""),
                "rollback_policy_version": pointer.get("rollback_policy_version", ""),
            },
        ),
        _pass_or_fail(
            "policy_observability_training",
            policy_report.get("version") == "v20.orchestrator_policy_observability_training_report.v1"
            and "trend_summary" in policy_report
            and "version_switch_timeline" in policy_report,
            {
                "status": policy_report.get("status", ""),
                "observation_count": policy_report.get("observation_count", 0),
                "recommendation_count": len(policy_report.get("strategy_recommendations", ())),
            },
        ),
        _pass_or_fail(
            "training_iteration_summary",
            iteration.get("version")
            in {"v20.training_iteration_report.v1", "v20.training_iteration_artifact_status.v1"},
            {
                "status": iteration.get("status", ""),
                "quality_status": iteration.get("quality_status", ""),
                "policy_learning_status": iteration.get("orchestrator_policy_learning_summary", {}).get("status", ""),
                "latest_path": iteration.get("latest_path", ""),
            },
        ),
        _pass_or_fail(
            "policy_candidate_traceability",
            isinstance(policy_candidates, dict)
            and "policy_observability_input_summary" in policy_candidates
            and "candidate_quality_summary" in policy_candidates
            and isinstance(policy_version, dict)
            and "source_policy_observability_input_summary" in policy_version
            and "source_candidate_quality_summary" in policy_version
            and "source_quality_scoring_policy" in policy_version,
            {
                "candidate_status": policy_candidates.get("status", ""),
                "version_status": policy_version.get("status", ""),
                "candidate_count": policy_candidates.get("candidate_count", 0),
                "top_quality_score": policy_candidates.get("candidate_quality_summary", {}).get("top_quality_score", 0),
                "quality_policy_version": policy_candidates.get("quality_scoring_policy", {}).get("version", ""),
            },
        ),
        _pass_or_fail(
            "question_source_graph_observability",
            question_source_graph.get("version") == "v20.question_source_graph.v1"
            and bool(question_source_graph.get("selected_paths"))
            and "QUALITY_SIGNALS_RERANK_ONLY" in question_source_graph.get("guardrails", ()),
            {
                "status": question_source_graph.get("status", ""),
                "path_count": question_source_graph.get("path_count", 0),
                "quality_summary_count": len(question_source_graph.get("quality_summary", ())),
            },
        ),
        _pass_or_fail(
            "runtime_question_source_ranking_report",
            isinstance(question_source_report, dict)
            and question_source_report.get("version") == "v20.question_source_ranking_report.v1"
            and question_source_report.get("question_count") == len(runtime.get("questions", ()))
            and "NO_QUESTION_ORDER_MUTATION" in question_source_report.get("guardrails", ()),
            {
                "status": question_source_report.get("status", ""),
                "question_count": question_source_report.get("question_count", 0),
                "source_path_count": question_source_report.get("source_path_count", 0),
            },
        ),
        _pass_or_fail(
            "question_source_training_report",
            question_source_training.get("version") == "v20.question_source_training_report.v1"
            and question_source_training.get("compiled_source_row_count", 0) > 0
            and "NO_RUNTIME_QUESTION_ORDER_MUTATION" in question_source_training.get("guardrails", ()),
            {
                "status": question_source_training.get("status", ""),
                "report_count": question_source_training.get("report_count", 0),
                "proposal_count": len(question_source_training.get("training_proposals", ())),
            },
        ),
    ]


def _expect_json(*, check_key: str, url: str, expected_version: str, timeout_sec: float) -> dict[str, object]:
    try:
        payload = json.loads(_fetch(url, timeout_sec=timeout_sec))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return _fail(check_key, {"url": url, "error": str(exc)})
    return _pass_or_fail(
        check_key,
        payload.get("version") == expected_version,
        {"url": url, "version": payload.get("version", ""), "status": payload.get("status", "")},
    )


def _expect_text(*, check_key: str, url: str, required: tuple[str, ...], timeout_sec: float) -> dict[str, object]:
    try:
        text = _fetch(url, timeout_sec=timeout_sec)
    except (HTTPError, URLError, TimeoutError) as exc:
        return _fail(check_key, {"url": url, "error": str(exc)})
    missing = [item for item in required if item not in text]
    return _pass_or_fail(check_key, not missing, {"url": url, "missing": missing})


def _fetch(url: str, *, timeout_sec: float) -> str:
    request = Request(url, headers={"Accept": "application/json,text/html"})
    with urlopen(request, timeout=timeout_sec) as response:
        return response.read().decode("utf-8")


def _pass_or_fail(check_key: str, ok: bool, details: dict[str, object]) -> dict[str, object]:
    return {
        "check_key": check_key,
        "status": "pass" if ok else "fail",
        "details": details,
        "runtime_mutation": False,
    }


def _fail(check_key: str, details: dict[str, object]) -> dict[str, object]:
    return _pass_or_fail(check_key, False, details)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 release smoke checks for the orchestrator policy loop.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9020", help="Running V20 service base URL.")
    parser.add_argument("--skip-http", action="store_true", help="Skip live HTTP checks and run local orchestrator checks only.")
    parser.add_argument("--timeout-sec", type=float, default=3.0, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    return run_and_print(
        lambda: build_release_smoke_report(
            base_url=args.base_url,
            skip_http=args.skip_http,
            timeout_sec=max(0.2, args.timeout_sec),
        ),
        command="release_smoke.py",
        args=args,
        runtime_mutation=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
