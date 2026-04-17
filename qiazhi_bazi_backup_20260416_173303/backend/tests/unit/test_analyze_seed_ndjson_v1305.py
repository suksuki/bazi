from __future__ import annotations

import json

import pytest

from app.api.contracts import AnalyzeSeedRequest
from app.services import analysis_service as m


@pytest.mark.asyncio
async def test_iter_analyze_seed_ndjson_phase_then_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_flow(
        body: AnalyzeSeedRequest,
        _gb: object,
        _gt: object,
        _now: str,
        *,
        update_orchestrator_status=None,
    ):
        if update_orchestrator_status:
            await update_orchestrator_status("PHASE_PHYSICS", "解析天干地支能量场...")
        return {
            "metadata": {"pillars": {}, "gender": body.gender},
            "llm_prompt": "",
            "physics_tensor": {},
            "timeline": {},
        }

    monkeypatch.setattr(m, "analyze_seed_flow", fake_flow)
    body = AnalyzeSeedRequest(date="1990-01-15", time="12:00", calendar="solar", gender="male", reference_year=2024)
    lines: list[str] = []
    async for chunk in m.iter_analyze_seed_ndjson(body, lambda *_a, **_k: None, lambda *_a, **_k: {}, "iso"):
        lines.append(chunk.decode("utf-8"))

    parsed = [json.loads(x) for x in "".join(lines).strip().split("\n") if x.strip()]
    assert any(p.get("type") == "phase" and p.get("phase") == "PHASE_PHYSICS" for p in parsed)
    assert any(p.get("type") == "complete" and isinstance(p.get("data"), dict) for p in parsed)
