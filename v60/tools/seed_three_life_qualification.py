from __future__ import annotations

from abu_v60.db import engine
from abu_v60.dream.qualification_seed import seed_three_life_qualification
from abu_v60.provenance import canonical_json


def main() -> None:
    print(canonical_json(seed_three_life_qualification(engine)))


if __name__ == "__main__":
    main()
