from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict

try:
    from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
    from v17_rebirth.backend.services.physics_service import PhysicsService
    from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator
except ImportError:  # pragma: no cover
    from backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor  # type: ignore
    from backend.services.physics_service import PhysicsService  # type: ignore
    from backend.services.verdict_orchestrator import VerdictOrchestrator


@dataclass
class FirstPureVerdictExperiment:
    _deprecated_note: str = "Deprecated in V17.2: use backend/services/verdict_orchestrator.py"

    async def run(self) -> Dict[str, Any]:
        # 典型“火旺 + 正官张力”样例；含工程词，验证 sanitizer。
        raw = {
            "four_pillars": {"year": "丙寅", "month": "甲午", "day": "戊子", "hour": "壬子"},
            "luck_pillar": "癸卯",
            "flow_pillar": "甲辰",
            "deity_scores": {"正官": 51.34, "食神": 20.1, "比肩": 8.9},
            "facts": [
                "VF.正官主导，Abs档偏高",
                "Fact_ID=fg_001：火势持续上扬",
                "seed:官火并举，node_id=root",
            ],
        }
        orchestrator = VerdictOrchestrator()
        hydrate_v17_physics_tensor(raw)
        PhysicsService.bind_session_tensor("default", raw)
        snapshot = orchestrator.snapshot_frame(raw_physics=raw)
        last_narrator = None
        async for frame in orchestrator.narrator_frames(
            raw_physics=raw,
            facts=[str(x) for x in (raw.get("facts") or []) if str(x).strip()],
            will_proxy="stable",
            session_id="default",
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
