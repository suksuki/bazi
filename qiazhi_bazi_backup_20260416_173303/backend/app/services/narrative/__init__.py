"""V16.2 narrative package: single source of realtime narration."""
from app.services.narrative.pipeline import RealtimeNarrativePipeline
from app.services.narrative.realtime_narrator import compose_realtime_narration, rewrite_fragments_tone_v15
from app.services.narrative.sanitizer import sanitize_fragment_text
from app.services.narrative.pipeline import guard_narrative_payload

__all__ = [
    "RealtimeNarrativePipeline",
    "compose_realtime_narration",
    "rewrite_fragments_tone_v15",
    "sanitize_fragment_text",
    "guard_narrative_payload",
]

