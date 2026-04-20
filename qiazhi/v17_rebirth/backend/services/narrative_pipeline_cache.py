from __future__ import annotations

from v17_rebirth.backend.narrative.pipeline import RealtimeNarrativePipeline
from v17_rebirth.backend.narrative.sanitizer import NarrativeSanitizer
from v17_rebirth.backend.narrative.semantic_fusion import SemanticFusion
from v17_rebirth.infrastructure.llm_bridge import V17LlmBridge, get_runtime_revision
from v17_rebirth.infrastructure.llm_micro_client import V17MicroLlmClient


_PIPELINE_EPOCH = 0
_PIPELINE_CACHE: RealtimeNarrativePipeline | None = None
_PIPELINE_CACHE_KEY: tuple[int, int] | None = None


def restart_pipeline_cache() -> dict[str, int]:
    """重置叙事流水线实例，返回当前版本号，用于运维与审计追踪。"""
    global _PIPELINE_EPOCH, _PIPELINE_CACHE, _PIPELINE_CACHE_KEY
    _PIPELINE_EPOCH += 1
    _PIPELINE_CACHE = None
    _PIPELINE_CACHE_KEY = None
    return {"pipeline_epoch": _PIPELINE_EPOCH}


def get_realtime_pipeline() -> RealtimeNarrativePipeline:
    """获取带 Revision 约束的共享叙事流水线单例。"""
    global _PIPELINE_CACHE, _PIPELINE_CACHE_KEY
    from v17_rebirth.backend.narrative.pipeline import DialogueLayer

    key = (_PIPELINE_EPOCH, get_runtime_revision())
    if _PIPELINE_CACHE is None or _PIPELINE_CACHE_KEY != key:
        _PIPELINE_CACHE = RealtimeNarrativePipeline(
            sanitizer=NarrativeSanitizer(),
            fusion=SemanticFusion(llm_client=V17MicroLlmClient(bridge=V17LlmBridge())),
            dialogue=DialogueLayer(sanitizer=NarrativeSanitizer()),
        )
        _PIPELINE_CACHE_KEY = key
    return _PIPELINE_CACHE
