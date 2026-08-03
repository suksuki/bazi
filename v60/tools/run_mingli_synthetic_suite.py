from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from typing import Any

from abu_v60.db import engine
from abu_v60.mingli.agent_runtime import (
    MingliAgentRuntimeUnavailable,
    configured_mingli_agent_runtime,
)
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentService
from abu_v60.mingli.synthetic_suite_catalog import (
    HIDDEN_RANK_DEV_SUITE_REF,
    SYNTHETIC_SUITES,
)
from abu_v60.mingli.synthetic_suite_contracts import (
    SyntheticSuiteCandidateIdentity,
)
from abu_v60.mingli.synthetic_suite_service import (
    SyntheticSuiteService,
    SyntheticSuiteServiceError,
)
from abu_v60.provenance import canonical_json
from abu_v60.settings import settings

MANAGED_LOCAL_GEMMA_BASE_URL = "http://dblife.com:11888"


def _progress(event: str, position: int, total: int, experiment_ref: str) -> None:
    print(
        f"{event} {position}/{total} {experiment_ref}",
        file=sys.stderr,
        flush=True,
    )


def _public_result(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "suite_run_ref": run["suite_run_ref"],
        "suite_run_hash": run["suite_run_hash"],
        "suite_ref": run["suite_ref"],
        "mode": run["suite_mode"],
        "status": run["status"],
        "counts": run["counts"],
        "outcomes": run["outcomes"],
        "error_clusters": run["error_clusters"],
        "items": run["items"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--suite-ref",
        choices=[item.suite_ref for item in SYNTHETIC_SUITES],
        default=HIDDEN_RANK_DEV_SUITE_REF,
    )
    parser.add_argument(
        "--runtime-profile",
        choices=("managed-local-gemma", "environment"),
        default="managed-local-gemma",
        help=(
            "Use the managed V60 Gemma profile by default; choose environment "
            "to require explicit V60_MINGLI_AGENT_* settings."
        ),
    )
    args = parser.parse_args()
    try:
        service = _service(args.runtime_profile)
        run = service.run_suite(
            suite_ref=args.suite_ref,
            progress=_progress,
        )
    except SyntheticSuiteServiceError as exc:
        print(
            canonical_json(
                {
                    "status": "ERROR",
                    "suite_ref": args.suite_ref,
                    "error_code": str(exc),
                }
            )
        )
        return 2
    print(canonical_json(_public_result(run)))
    return 2 if run["counts"]["runner_errors"] else 0


def _service(runtime_profile: str) -> SyntheticSuiteService:
    runtime_settings = (
        settings
        if runtime_profile == "environment"
        else replace(
            settings,
            mingli_agent_enabled=True,
            mingli_agent_base_url=MANAGED_LOCAL_GEMMA_BASE_URL,
        )
    )
    runtime = configured_mingli_agent_runtime(runtime_settings)
    try:
        candidate = SyntheticSuiteCandidateIdentity.model_validate(runtime.candidate_identity())
    except (MingliAgentRuntimeUnavailable, ValueError) as exc:
        raise SyntheticSuiteServiceError(str(exc)) from exc
    experiment_service = SyntheticExperimentService(engine, runtime=runtime)
    return SyntheticSuiteService(
        engine,
        experiment_service=experiment_service,
        candidate_identity=candidate,
    )


if __name__ == "__main__":
    raise SystemExit(main())
