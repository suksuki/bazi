from __future__ import annotations

import pytest

from app.services.narrative.realtime_narrator import compose_realtime_narration


@pytest.mark.asyncio
async def test_realtime_narrator_weaves_conflict_and_interaction() -> None:
    md = {
        "conflict_matrix": {"points": [{"detail": "寅巳穿害"}]},
        "decision_impact_registry_v14_01": {
            "events": [
                {"verb": "IGNORE", "subject": "食神过旺"},
                {"verb": "PATCH", "narrative": "强调寅巳穿风险"},
            ]
        },
    }
    pt = {"meta": {"semantic_label_bundle_v1": {"verified_fact_lines": ["检测到物理冲突：寅巳穿害"]}}}
    out = await compose_realtime_narration(metadata=md, physics_tensor=pt, lang="ZH", max_chars=200)
    assert out.get("ok") is True
    text = str(out.get("text") or "")
    assert "寅巳穿害" in text
    assert ("强调" in text) or ("补丁" in text)

