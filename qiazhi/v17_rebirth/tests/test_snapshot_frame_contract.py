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
        "ten_gods_absolute_intensity": {"食神": 45.0, "正官": 25.0},
        "total_energy_index": 70.0,
    }
    orch = VerdictOrchestrator(repo_root=str(bazi_repo_root))
    snap = orch.snapshot_frame(raw_physics=raw)
    assert snap.get("layer") == "SNAPSHOT"
    inner = snap.get("payload") or {}
    assert inner.get("snapshot_contract") == "v17.21_full_physics"
    assert isinstance(inner.get("plugins"), dict)
    assert "hits" in (inner.get("plugins") or {})
    assert isinstance((inner.get("plugins") or {}).get("statuses"), list)
    assert isinstance((inner.get("plugins") or {}).get("claims"), list)
    assert isinstance((inner.get("plugins") or {}).get("conflicts"), list)
    assert isinstance((inner.get("plugins") or {}).get("conflict_resolutions"), list)
    assert isinstance((inner.get("plugins") or {}).get("knowledge_snapshot"), dict)
    assert isinstance((inner.get("plugins") or {}).get("brain_action_queue"), list)
    assert "食神" in inner.get("ten_gods_base_l0", {})
    assert "食神" in inner.get("ten_gods_runtime", {})
    assert "食神" in inner.get("ten_gods_narrative", {})
    assert "食神" in inner.get("ten_gods_absolute_intensity", {})
    assert "total_energy_index" in inner
    pillars = inner.get("pillars") or {}
    assert isinstance(pillars.get("four_pillars"), dict)
    dbg = inner.get("debug_trace") or {}
    assert isinstance(dbg.get("hits"), list)
    assert isinstance(dbg.get("facts"), list)
    assert isinstance(inner.get("fact_rows"), list)
    assert isinstance(inner.get("manual_decisions"), list)
    assert isinstance(inner.get("auto_resolutions"), list)
    assert isinstance(inner.get("llm_arbitration_context"), list)
    assert isinstance(inner.get("decision_batches"), list)
    assert isinstance(inner.get("decision_prompt_batches"), list)
    if inner.get("manual_decisions"):
        assert "arbitration_trace" in inner["manual_decisions"][0]
