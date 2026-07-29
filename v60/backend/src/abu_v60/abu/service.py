from __future__ import annotations

from typing import Any

from abu_v60.context import ExperienceContextEnvelope, ExperienceUnit


class AbuSaysProjector:
    """Project bounded guidance without creating facts or decisions."""

    def project(self, *, context: ExperienceContextEnvelope) -> dict[str, Any]:
        return {
            "context_ref": context.context_ref,
            "disclosure": context.disclosure_for(ExperienceUnit.ABU).model_dump(mode="json"),
            "speaker": "ABU",
            "line": context.story.abu_line,
            "authority": "GUIDE_ONLY",
            "fact_creation": False,
            "decision_creation": False,
            "content_key": f"{context.story.content_key}.abu",
        }
