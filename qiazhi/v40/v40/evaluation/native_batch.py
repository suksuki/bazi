from __future__ import annotations

from v40.contracts.base import RoleKey
from v40.contracts.evaluation import EvaluationBatchSummary, EvaluationCaseSpec, EvaluationRunResult
from v40.contracts.runtime import RuntimeResult
from v40.contracts.chart import SyntheticCaseSeed
from v40.engines import build_native_bazi_runtime
from v40.evaluation.batch import build_evaluation_batch_summary
from v40.evaluation.runner import evaluate_runtime_against_case
from v40.synthetic import build_evaluation_cases_from_seeds


def evaluate_native_seeds(
    *,
    batch_id: str,
    seeds: list[SyntheticCaseSeed],
    candidate_version: str,
    role_key: RoleKey = "user",
) -> tuple[list[RuntimeResult], list[EvaluationCaseSpec], list[EvaluationRunResult], EvaluationBatchSummary]:
    cases = build_evaluation_cases_from_seeds(seeds)
    runtimes: list[RuntimeResult] = []
    runs: list[EvaluationRunResult] = []
    for seed, case in zip(seeds, cases, strict=True):
        runtime = build_native_bazi_runtime(
            request_id=f"native-batch:{batch_id}:{seed.seed_id}",
            reading_id=f"reading:{batch_id}:{seed.seed_id}",
            chart=seed.chart_facts,
            user_question=seed.question,
            topic=case.topic,
            role_key=role_key,
        )
        runtimes.append(runtime)
        runs.append(
            evaluate_runtime_against_case(
                run_id=f"{batch_id}:{case.case_id}",
                case_spec=case,
                runtime=runtime,
                candidate_version=candidate_version,
                build_release_gate=True,
            )
        )
    summary = build_evaluation_batch_summary(
        batch_id=batch_id,
        candidate_version=candidate_version,
        runs=runs,
    )
    return runtimes, cases, runs, summary
