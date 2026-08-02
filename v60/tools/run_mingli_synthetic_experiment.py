from __future__ import annotations

from abu_v60.db import engine
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentService
from abu_v60.provenance import canonical_json


def main() -> None:
    run = SyntheticExperimentService(engine).run_first_experiment()
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
