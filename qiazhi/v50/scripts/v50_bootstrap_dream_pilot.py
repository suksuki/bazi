from __future__ import annotations

import json

from product.agent_case_store import build_agent_case_store
from product.dream_pilot import DreamCanonicalNpcBootstrapService
from product.dream_store import build_dream_store


def main() -> None:
    service = DreamCanonicalNpcBootstrapService(
        case_store=build_agent_case_store(),
        dream_store=build_dream_store(),
    )
    print(json.dumps(
        [item.__dict__ for item in service.ensure()],
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
