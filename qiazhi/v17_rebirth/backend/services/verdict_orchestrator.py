from __future__ import annotations

from dataclasses import dataclass
import asyncio
import importlib
import pkgutil
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List

from v17_rebirth.backend.adapters.physics_adapter import PhysicsAdapter
from v17_rebirth.backend.narrative.pipeline import DialogueLayer, RealtimeNarrativePipeline
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
            dialogue=DialogueLayer(sanitizer=NarrativeSanitizer()),
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

    def _pending_decisions(self, deity_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        sanitizer = NarrativeSanitizer()
        rows = self._collect_plugin_facts(deity_scores)
        out: List[Dict[str, Any]] = []
        for idx, row in enumerate(sorted(rows, key=lambda x: float(x.get("priority", 0.0)), reverse=True)[:4]):
            label = sanitizer.sanitize(row.get("label", "") or row.get("fact", ""))
            title = sanitizer.sanitize(row.get("fact", ""))
            if not label:
                continue
            out.append(
                {
                    "id": f"{row.get('plugin','plugin')}_{idx}",
                    "title": title or "建议动作",
                    "label": label,
                    "source": row.get("plugin", "plugin"),
                    "priority": float(row.get("priority", 0.0)),
                }
            )
        return out

    def _collect_plugin_facts(self, deity_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        try:
            import v17_rebirth.backend.logic as logic_pkg
        except Exception:
            return rows
        for mod in pkgutil.iter_modules(logic_pkg.__path__):
            if mod.name.startswith("_"):
                continue
            try:
                m = importlib.import_module(f"v17_rebirth.backend.logic.{mod.name}")
                fn = getattr(m, "collect_v17_facts", None)
                if callable(fn):
                    result = fn(deity_scores)
                    if isinstance(result, list):
                        rows.extend([x for x in result if isinstance(x, dict)])
            except Exception:
                continue
        return rows

    def snapshot_frame(self, *, raw_physics: Dict[str, Any]) -> Dict[str, Any]:
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        tension = (max(scores.values()) - min(scores.values())) if scores else 0.0
        plugin_rows = self._collect_plugin_facts(scores)
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        plugin_hits = sorted({str(x.get("plugin", "")).strip() for x in plugin_rows if str(x.get("plugin", "")).strip()})
        decisions = self._pending_decisions(scores)
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
                "pending_decisions": decisions,
                "debug_trace": {
                    "hits": plugin_hits,
                    "facts": plugin_facts[:10],
                },
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
        user_message: str = "",
        action_signal: bool = False,
        decision_anchor: str = "",
    ) -> AsyncIterator[Dict[str, Any]]:
        adapter = PhysicsAdapter(root=__import__("pathlib").Path(self.repo_root))
        scores = adapter.read_deity_scores(raw_physics)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        god_of_use = [x[0] for x in ranked[:2]]
        god_of_taboo = [x[0] for x in ranked[-2:]] if len(ranked) >= 2 else []
        pattern = self._resolve_pattern(scores)
        plugin_rows = await asyncio.to_thread(self._collect_plugin_facts, scores)
        plugin_facts = [str(x.get("fact", "")).strip() for x in plugin_rows if str(x.get("fact", "")).strip()]
        fragments = self._build_fragments(scores, [*facts, *plugin_facts], pattern)
        pipeline = _get_pipeline()
        frame = await pipeline.run(
            fact_fragments=fragments,
            will_proxy=will_proxy,
            user_message=user_message,
            action_signal=action_signal,
            decision_anchor=decision_anchor,
            god_of_use=god_of_use,
            god_of_taboo=god_of_taboo,
        )
        text = str((((frame.get("payload") or {}).get("render_text")) or "")).strip()
        llm_meta = (frame.get("payload") or {}).get("llm_meta", {})
        source_facts = (frame.get("payload") or {}).get("source_facts", [])
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
                    "llm_meta": llm_meta if isinstance(llm_meta, dict) else {},
                    "source_facts": source_facts if isinstance(source_facts, list) else [],
                    "god_rings": {
                        "god_of_use": god_of_use,
                        "god_of_taboo": god_of_taboo,
                    },
                },
            }
