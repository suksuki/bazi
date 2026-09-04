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
MANAGED_LOCAL_QWEN38_BASE_URL = "http://dblife.com:11888"
MANAGED_LOCAL_QWEN38_MODEL = "qwen3.8:27b"
MANAGED_LOCAL_QWEN38_MODEL_DIGEST = (
    "22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643"
)
MANAGED_LOCAL_QWEN38_PROFILE_REF = "v60.model-serving.qwen38-27b-mingli-agent.002"


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
        choices=("managed-local-gemma", "managed-local-qwen38", "environment"),
        default="managed-local-gemma",
        help=(
            "Use the managed V60 Gemma profile by default; choose Qwen3.8 or environment "
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
    if runtime_profile == "environment":
        runtime_settings = settings
    elif runtime_profile == "managed-local-qwen38":
        runtime_settings = replace(
            settings,
            mingli_agent_enabled=True,
            mingli_agent_model=MANAGED_LOCAL_QWEN38_MODEL,
            mingli_agent_model_digest=MANAGED_LOCAL_QWEN38_MODEL_DIGEST,
            mingli_agent_profile_ref=MANAGED_LOCAL_QWEN38_PROFILE_REF,
            mingli_agent_base_url=MANAGED_LOCAL_QWEN38_BASE_URL,
            mingli_agent_timeout_seconds=600.0,
            mingli_agent_think=False,
            mingli_agent_temperature=0.0,
            mingli_agent_top_p=0.95,
            mingli_agent_top_k=20,
            mingli_agent_num_ctx=24576,
            mingli_agent_num_predict=6000,
            mingli_agent_keep_alive="30m",
        )
    else:
        runtime_settings = replace(
            settings,
            mingli_agent_enabled=True,
            mingli_agent_base_url=MANAGED_LOCAL_GEMMA_BASE_URL,
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
