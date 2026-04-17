from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List

from v17_rebirth.backend.adapters.physics_adapter import PhysicsAdapter
from v17_rebirth.backend.narrative.pipeline import RealtimeNarrativePipeline
from v17_rebirth.backend.narrative.sanitizer import NarrativeSanitizer
from v17_rebirth.backend.narrative.semantic_fusion import SemanticFusion
from v17_rebirth.infrastructure.llm_bridge import V17LlmBridge, get_runtime_revision
from v17_rebirth.infrastructure.llm_micro_client import V17MicroLlmClient

_PIPELINE_EPOCH = 0
_PIPELINE_CACHE: RealtimeNarrativePipeline | None = None
_PIPELINE_CACHE_KEY: tuple[int, int] | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def restart_realtime_pipeline() -> dict[str, int]:
    global _PIPELINE_EPOCH, _PIPELINE_CACHE, _PIPELINE_CACHE_KEY
    _PIPELINE_EPOCH += 1
    _PIPELINE_CACHE = None
    _PIPELINE_CACHE_KEY = None
    return {"pipeline_epoch": _PIPELINE_EPOCH}


def _get_pipeline() -> RealtimeNarrativePipeline:
    global _PIPELINE_CACHE, _PIPELINE_CACHE_KEY
    key = (_PIPELINE_EPOCH, get_runtime_revision())
    if _PIPELINE_CACHE is None or _PIPELINE_CACHE_KEY != key:
        _PIPELINE_CACHE = RealtimeNarrativePipeline(
            sanitizer=NarrativeSanitizer(),
            fusion=SemanticFusion(llm_client=V17MicroLlmClient(bridge=V17LlmBridge())),
        )
        _PIPELINE_CACHE_KEY = key
    return _PIPELINE_CACHE


@dataclass
class VerdictOrchestrator:
    repo_root: str = "/home/hlsystem/bazi"

    def _resolve_pattern(self, deity_scores: Dict[str, float]) -> str:
        if not deity_scores:
            return "未定格"
        top = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
        name, score = top[0]
        if name == "正官" and score >= 40:
            return "正官格势强"
        if name in {"食神", "伤官"} and score >= 35:
            return "食伤外放格"
        if name in {"偏财", "正财"} and score >= 35:
            return "财星主导格"
        return f"{name}主轴格"

    def _build_fragments(self, deity_scores: Dict[str, float], facts: List[str], pattern: str) -> List[str]:
        ranked = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
        lead = [f"{k}偏强" for k, _ in ranked[:2]]
        return [
            f"当前格局：{pattern}",
            ("、".join(lead) + "，局势进入再平衡阶段") if lead else "当前能量分布尚在收敛",
            *[str(x) for x in facts[:4]],
        ]

    def snapshot_frame(self, *, raw_physics: Dict[str, Any]) -> Dict[str, Any]:
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        tension = (max(scores.values()) - min(scores.values())) if scores else 0.0
        return {
            "timestamp": _now_iso(),
            "layer": "SNAPSHOT",
            "payload": {
                "render_text": f"格局快照已同步：{pattern}",
                "pattern": pattern,
                "four_pillars": raw_physics.get("four_pillars", {}),
                "ten_gods": raw_physics.get("ten_gods", []),
                "deity_scores": scores,
                "physics_tension": tension,
                "god_rings": {
                    "god_of_use": god_of_use,
                    "god_of_taboo": god_of_taboo,
                },
            },
        }

    async def narrator_frames(
        self,
        *,
        raw_physics: Dict[str, Any],
        facts: List[str],
        will_proxy: str,
    ) -> AsyncIterator[Dict[str, Any]]:
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        fragments = self._build_fragments(scores, facts, pattern)
        pipeline = _get_pipeline()
        frame = await pipeline.run(
            fact_fragments=fragments,
            will_proxy=will_proxy,
            god_of_use=god_of_use,
            god_of_taboo=god_of_taboo,
        )
        text = str((((frame.get("payload") or {}).get("render_text")) or "")).strip()
        if not text:
            return
        # WebStream-style incremental reveal: one frame per sentence chunk.
        step = max(6, min(14, len(text) // 4 if len(text) > 24 else 8))
        for i in range(step, len(text) + step, step):
            yield {
                "timestamp": _now_iso(),
                "layer": "NARRATOR",
                "payload": {
                    "render_text": text[: min(i, len(text))],
                    "will_proxy": str(will_proxy or "stable"),
                    "god_rings": {
                        "god_of_use": god_of_use,
                        "god_of_taboo": god_of_taboo,
                    },
                },
            }
