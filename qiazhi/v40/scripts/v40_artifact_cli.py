#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v40.artifacts import load_evaluation_cases
from v40.engines import build_native_bazi_runtime
from v40.evaluation import evaluate_cases_against_runtime
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import V40PostgresRepository
from v40.synthetic import build_evaluation_cases_from_seeds, load_synthetic_seeds


def main() -> None:
    parser = argparse.ArgumentParser(description="Qiazhi V40 artifact utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_cases = subparsers.add_parser("import-cases", help="Import EvaluationCaseSpec JSON artifact")
    import_cases.add_argument("--path", required=True)

    export_cases = subparsers.add_parser("export-cases", help="Export recent evaluation case rows")
    export_cases.add_argument("--path", required=True)
    export_cases.add_argument("--limit", type=int, default=100)

    run_batch = subparsers.add_parser("run-batch", help="Run cases against a V30 JSON export through V40 importer")
    run_batch.add_argument("--cases", required=True)
    run_batch.add_argument("--v30-export", required=True)
    run_batch.add_argument("--batch-id", required=True)
    run_batch.add_argument("--candidate-version", required=True)
    run_batch.add_argument("--no-persist", action="store_true")

    import_synthetic = subparsers.add_parser("import-synthetic-cases", help="Import synthetic seeds as EvaluationCaseSpec rows")
    import_synthetic.add_argument("--path", required=True)

    native_seed = subparsers.add_parser("run-native-seed", help="Run V40 native Bazi skeleton from a synthetic seed")
    native_seed.add_argument("--path", required=True)
    native_seed.add_argument("--seed-id", required=True)
    native_seed.add_argument("--reading-id", required=True)
    native_seed.add_argument("--no-persist", action="store_true")

    subparsers.add_parser("lab-summary", help="Print V40 lab summary")

    args = parser.parse_args()
    repository = V40PostgresRepository.from_env()

    if args.command == "import-cases":
        cases = load_evaluation_cases(args.path)
        for case in cases:
            repository.save_evaluation_case(case)
        print(json.dumps({"imported": len(cases), "path": args.path}, ensure_ascii=False))
        return

    if args.command == "export-cases":
        rows = repository.list_evaluation_cases(limit=args.limit)
        Path(args.path).write_text(json.dumps({"cases": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"exported": len(rows), "path": args.path}, ensure_ascii=False))
        return

    if args.command == "run-batch":
        cases = load_evaluation_cases(args.cases)
        export_payload = json.loads(Path(args.v30_export).read_text(encoding="utf-8"))
        runtime = build_runtime_from_v30_export(V30ExportEnvelope.model_validate(export_payload))
        runs, summary = evaluate_cases_against_runtime(
            batch_id=args.batch_id,
            cases=cases,
            runtime=runtime,
            candidate_version=args.candidate_version,
        )
        if not args.no_persist:
            for run in runs:
                repository.save_evaluation_run(run)
                if run.release_gate:
                    repository.save_release_gate(run.release_gate)
            repository.save_evaluation_batch_summary(summary)
        print(json.dumps(summary.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    if args.command == "import-synthetic-cases":
        seeds = load_synthetic_seeds(args.path)
        cases = build_evaluation_cases_from_seeds(seeds)
        for case in cases:
            repository.save_evaluation_case(case)
        print(json.dumps({"imported": len(cases), "path": args.path}, ensure_ascii=False))
        return

    if args.command == "run-native-seed":
        seeds = load_synthetic_seeds(args.path)
        seed = next((row for row in seeds if row.seed_id == args.seed_id), None)
        if seed is None:
            raise ValueError(f"seed_id not found: {args.seed_id}")
        runtime = build_native_bazi_runtime(
            request_id=f"native:{seed.seed_id}",
            reading_id=args.reading_id,
            chart=seed.chart_facts,
            user_question=seed.question,
        )
        if not args.no_persist:
            repository.save_runtime(runtime)
        print(
            json.dumps(
                {
                    "reading_id": runtime.reading_id,
                    "signal_count": len(runtime.signal_registry.signals if runtime.signal_registry else []),
                    "verdict_count": len(runtime.verdicts),
                    "advice_count": len(runtime.advice_plans),
                    "persisted": not args.no_persist,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "lab-summary":
        print(json.dumps(repository.lab_summary(), ensure_ascii=False, indent=2))
        return

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    main()
