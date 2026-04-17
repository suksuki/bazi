from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict

try:
    from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator
except ImportError:  # pragma: no cover
    from backend.services.verdict_orchestrator import VerdictOrchestrator


@dataclass
class FirstPureVerdictExperiment:
    _deprecated_note: str = "Deprecated in V17.2: use backend/services/verdict_orchestrator.py"

    async def run(self) -> Dict[str, Any]:
        # 典型“火旺 + 正官张力”样例；含工程词，验证 sanitizer。
        raw = {
            "deity_scores": {"正官": 51.34, "食神": 20.1, "比肩": 8.9},
            "facts": [
                "VF.正官主导，Abs档偏高",
                "Fact_ID=fg_001：火势持续上扬",
                "seed:官火并举，node_id=root",
            ],
        }
        orchestrator = VerdictOrchestrator()
        snapshot = orchestrator.snapshot_frame(raw_physics=raw)
        last_narrator = None
        async for frame in orchestrator.narrator_frames(
            raw_physics=raw,
            facts=[str(x) for x in (raw.get("facts") or []) if str(x).strip()],
            will_proxy="stable",
        ):
            last_narrator = frame
        frame = last_narrator or snapshot
        text = str((((frame.get("payload") or {}).get("render_text")) or "")).strip()
        if len(text) > 50:
            frame["payload"]["render_text"] = text[:50]
        return frame


async def main() -> None:
    result = await FirstPureVerdictExperiment().run()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
