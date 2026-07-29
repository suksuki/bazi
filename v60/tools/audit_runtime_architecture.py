from __future__ import annotations

import json

from abu_v60.db import engine
from abu_v60.observability import RuntimeIntegrityService


def main() -> None:
    print(
        json.dumps(
            RuntimeIntegrityService().inspect(engine),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
