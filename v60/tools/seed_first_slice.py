from __future__ import annotations

from abu_v60.db import engine
from abu_v60.dream.seed import seed_first_slice
from abu_v60.provenance import canonical_json


def main() -> None:
    print(canonical_json(seed_first_slice(engine)))


if __name__ == "__main__":
    main()
