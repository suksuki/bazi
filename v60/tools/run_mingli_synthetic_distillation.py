from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace
from typing import Literal

from abu_v60.db import engine
from abu_v60.mingli.synthetic_distillation_runtime import (
    configured_mingli_synthetic_distillation_runtime,
)
from abu_v60.mingli.synthetic_distillation_service import (
    MingliSyntheticDistillationService,
    MingliSyntheticDistillationServiceError,
)
from abu_v60.mingli.synthetic_experiment_catalog import (
    MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
)
from abu_v60.provenance import canonical_json
from abu_v60.settings import settings

MANAGED_LOCAL_QWEN38_BASE_URL = "http://dblife.com:11888"
MANAGED_LOCAL_QWEN38_MODEL = "qwen3.8:27b"
MANAGED_LOCAL_QWEN38_MODEL_DIGEST = (
    "22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643"
)
MANAGED_LOCAL_QWEN38_PROFILE_REF = "v60.model-serving.qwen38-27b-mingli-agent.002"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the DEV-only three-pass Mingli distillation probe on a canonical "
            "synthetic experiment."
        )
    )
    parser.add_argument(
        "--experiment-ref",
        default=MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
    )
    parser.add_argument("--variant", choices=("A", "B", "both"), default="both")
    parser.add_argument(
        "--runtime-profile",
        choices=("managed-local-qwen38", "environment"),
        default="managed-local-qwen38",
    )
    args = parser.parse_args()
    runtime_settings = (
        settings
        if args.runtime_profile == "environment"
        else replace(
            settings,
            mingli_agent_enabled=True,
            mingli_agent_model=MANAGED_LOCAL_QWEN38_MODEL,
            mingli_agent_model_digest=MANAGED_LOCAL_QWEN38_MODEL_DIGEST,
            mingli_agent_profile_ref=MANAGED_LOCAL_QWEN38_PROFILE_REF,
            mingli_agent_base_url=MANAGED_LOCAL_QWEN38_BASE_URL,
            mingli_agent_timeout_seconds=240.0,
            mingli_agent_think=False,
            mingli_agent_temperature=0.0,
            mingli_agent_top_p=0.95,
            mingli_agent_top_k=20,
            mingli_agent_num_ctx=8192,
            mingli_agent_num_predict=1800,
            mingli_agent_keep_alive="30m",
        )
    )
    service = MingliSyntheticDistillationService(
        engine,
        runtime=configured_mingli_synthetic_distillation_runtime(runtime_settings),
    )
    variants: tuple[Literal["A", "B"], ...] = (
        ("A", "B") if args.variant == "both" else (args.variant,)
    )
    results = []
    for variant in variants:
        print(
            f"DISTILLATION_START variant={variant}",
            file=sys.stderr,
            flush=True,
        )
        started = time.monotonic()
        try:
            execution = service.run(
                experiment_ref=args.experiment_ref,
                variant=variant,
            )
        except MingliSyntheticDistillationServiceError as exc:
            print(
                canonical_json(
                    {
                        "status": "ERROR",
                        "experiment_ref": args.experiment_ref,
                        "variant": variant,
                        "error_code": str(exc),
                    }
                )
            )
            return 2
        run = execution.run
        print(
            (
                f"DISTILLATION_DONE variant={variant} "
                f"outcome={run.evaluation.outcome} duration_ms={run.duration_ms}"
            ),
            file=sys.stderr,
            flush=True,
        )
        results.append(
            {
                "variant": variant,
                "run_ref": run.run_ref,
                "run_hash": run.run_hash,
                "cache_hit": execution.cache_hit,
                "model_ref": run.model_ref,
                "model_digest": run.model_digest,
                "provider_profile_ref": run.provider_profile_ref,
                "provider_profile_hash": run.provider_profile_hash,
                "prompt_hash": run.prompt_hash,
                "outcome": run.evaluation.outcome,
                "model_independence": run.evaluation.model_independence,
                "issue_keys": run.evaluation.issue_keys,
                "stage_metrics": tuple(
                    {
                        "stage": item.stage,
                        "input_tokens": item.input_tokens,
                        "output_tokens": item.output_tokens,
                        "total_tokens": item.total_tokens,
                        "duration_ms": item.duration_ms,
                    }
                    for item in run.passes
                ),
                "model_certainty": run.passes[2].raw_output,
                "local_certainty": run.evaluation.certainty_assembly.model_dump(mode="json"),
                "candidate_assembly": (run.evaluation.candidate_assembly.model_dump(mode="json")),
                "input_tokens": run.input_tokens,
                "output_tokens": run.output_tokens,
                "total_tokens": run.total_tokens,
                "model_duration_ms": run.duration_ms,
                "wall_duration_ms": round((time.monotonic() - started) * 1000),
                "qualification_effect": run.evaluation.qualification_effect,
            }
        )
    print(
        canonical_json(
            {
                "status": "COMPLETED",
                "experiment_ref": args.experiment_ref,
                "results": results,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
