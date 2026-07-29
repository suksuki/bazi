from __future__ import annotations

from typing import Any

from abu_v60.context import ExperienceContextEnvelope, ExperienceUnit


class MingliWorkspaceProjector:
    """Project formal chart facts separately from Lab candidates."""

    def project(
        self,
        *,
        context: ExperienceContextEnvelope,
    ) -> dict[str, Any]:
        return {
            "context_ref": context.context_ref,
            "disclosure": context.disclosure_for(ExperienceUnit.MINGLI).model_dump(mode="json"),
            "chart_version_ref": context.lineage.chart_version_ref,
            "life_case_revision_ref": context.lineage.life_case_revision_ref,
            "pillars": dict(context.pillars),
            "facts": [fact.model_dump(mode="json") for fact in context.facts],
            "authority": "MINGLI_FACT_AUTHORITY",
            "read_only": True,
        }
