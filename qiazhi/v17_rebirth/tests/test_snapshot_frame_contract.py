"""集成级（进程内）：snapshot_frame 契约（插件链 + pillars，无 LLM）。"""
from __future__ import annotations

from pathlib import Path

from v17_rebirth.backend.logic import plugin_discovery as pd
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator


def test_snapshot_frame_v17_21_contract(bazi_repo_root: Path) -> None:
    pd.clear_logic_module_cache()
    raw = {
        "four_pillars": {"year": "丙寅", "month": "癸巳", "day": "戊申", "hour": "甲寅"},
        "luck_pillar": "庚午",
        "flow_pillar": "甲辰",
        "deity_scores": {"食神": 45.0, "正官": 25.0},
    }
    orch = VerdictOrchestrator(repo_root=str(bazi_repo_root))
    snap = orch.snapshot_frame(raw_physics=raw)
    assert snap.get("layer") == "SNAPSHOT"
    inner = snap.get("payload") or {}
    assert inner.get("snapshot_contract") == "v17.21_full_physics"
    assert isinstance(inner.get("plugins"), dict)
    assert "hits" in (inner.get("plugins") or {})
    pillars = inner.get("pillars") or {}
    assert isinstance(pillars.get("four_pillars"), dict)
    dbg = inner.get("debug_trace") or {}
    assert isinstance(dbg.get("hits"), list)
    assert isinstance(dbg.get("facts"), list)
