__all__ = ["RealtimeNarrativePipeline", "NarrativeSanitizer", "SemanticFusion"]


def __getattr__(name: str):
    if name == "RealtimeNarrativePipeline":
        from .pipeline import RealtimeNarrativePipeline

        return RealtimeNarrativePipeline
    if name == "NarrativeSanitizer":
        from .sanitizer import NarrativeSanitizer

        return NarrativeSanitizer
    if name == "SemanticFusion":
        from .semantic_fusion import SemanticFusion

        return SemanticFusion
    raise AttributeError(name)
