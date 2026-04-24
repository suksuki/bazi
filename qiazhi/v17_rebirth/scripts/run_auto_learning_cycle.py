from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.testing.auto_learning_loop import run_auto_learning_cycle


def main() -> None:
    print(json.dumps(run_auto_learning_cycle(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

