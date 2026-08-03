from __future__ import annotations

import argparse

from abu_v60.db import engine
from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    SYNTHETIC_EXPERIMENTS,
)
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentService
from abu_v60.provenance import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--experiment-ref",
        choices=[item.experiment_ref for item in SYNTHETIC_EXPERIMENTS],
        default=FIRST_SYNTHETIC_EXPERIMENT_REF,
    )
    args = parser.parse_args()
    run = SyntheticExperimentService(engine).run_experiment(
        experiment_ref=args.experiment_ref,
    )
    print(
        canonical_json(
            {
                "run_ref": run["run_ref"],
                "run_hash": run["run_hash"],
                "outcome": run["outcome"],
                "evaluation": run["evaluation_json"],
            }
        )
    )


if __name__ == "__main__":
    main()
