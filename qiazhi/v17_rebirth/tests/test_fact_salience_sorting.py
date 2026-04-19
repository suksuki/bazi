from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import infer_salience_weight, v17_fact_to_row
from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator
from v17_rebirth.infrastructure.llm_micro_client import build_v17_system_prompt


def test_infer_salience_weight_maps_core_pattern_to_tier0() -> None:
    weight = infer_salience_weight(
        plugin_id="ten_god_pattern",
        fact_text="十神格局判定：七杀主轴格。",
        causal_tier=3,
        priority=0.78,
    )
    assert weight >= 0.95


def test_v17_fact_to_row_exposes_weight() -> None:
    row = v17_fact_to_row(
        V17Fact(
            plugin_id="kong_wang",
            text="空亡波动抬升，信号空转比约 3.90。",
            causal_tier=3,
            salience_weight=0.31,
            priority=0.8,
        )
    )
    assert row["weight"] == 0.31


def test_build_fragments_orders_by_weight_and_caps_to_80() -> None:
    orch = VerdictOrchestrator()
    facts = [{"fact": f"低权重{i}", "weight": 0.1} for i in range(95)]
    facts += [{"fact": f"高权重{i}", "weight": 0.99 - i * 0.01} for i in range(15)]

    fragments = orch._build_fragments(
        {"正官": 42.0, "食神": 18.0},
        facts,
        total_energy_index=60.0,
    )

    assert "显著性（Salience）" in fragments[0]
    # [0] salience 头部, [1] energy_hint, [2] lead 概要, [3+] facts
    assert "Total Energy Index=60.00" in fragments[1]
    assert fragments[2] == "正官偏强、食神偏强，局势进入再平衡阶段"
    assert fragments[3] == "高权重0"
    assert "低权重94" not in fragments
    assert len([x for x in fragments if x.startswith("低权重") or x.startswith("高权重")]) <= 80


def test_build_v17_system_prompt_contains_salience_anchor() -> None:
    prompt = build_v17_system_prompt(
        will_proxy="stable",
        decision_anchor="",
        action_signal=False,
        physics_tensor={
            "four_pillars": {"year": "丙午", "month": "壬辰", "day": "壬戌", "hour": "甲辰"},
            "luck_pillar": "辛卯",
            "flow_pillar": "丙午",
            "flow_year": 2026,
        },
    )
    assert "显著性（Salience）降序排列" in prompt
    assert "优先回应前 10 条核心事实" in prompt
