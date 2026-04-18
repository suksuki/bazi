from __future__ import annotations

from v17_rebirth.backend.narrative.NarrativeMappingEngine import NarrativeMappingEngine
from v17_rebirth.infrastructure.llm_micro_client import build_v17_system_prompt


def _tensor() -> dict:
    return {
        "day_master_stem": "壬",
        "four_pillars": {"year": "丙午", "month": "壬辰", "day": "壬戌", "hour": "丁未"},
        "luck_pillar": "辛卯",
        "flow_pillar": "丙午",
        "flow_year": 2026,
        "ten_gods_absolute_intensity": {
            "比肩": 120.0,
            "食神": 82.0,
            "正财": 30.0,
            "正官": 24.0,
            "正印": 18.0,
        },
        "total_energy_index": 274.0,
        "ten_gods_ledger": {
            "食神": [
                {"step": "L0_BASE", "val": 60.0, "reason": "基线"},
                {
                    "step": "L1.5_FLOW_SETTLEMENT",
                    "val": 82.0,
                    "delta": 22.0,
                    "reason": "五行内生系统平衡流转",
                    "source": "SRC_FLOW",
                    "highlight_type": "cyan",
                },
            ]
        },
        "flow_topology": [
            {"from_el": "水", "to_el": "木", "current": 35.0, "rel": "生", "resistance": 0.62, "stress": 4.2},
            {"from_el": "木", "to_el": "火", "current": 12.5, "rel": "生", "resistance": 0.71, "stress": 3.4},
        ],
        "meta": {"v17_physics_stable": True},
    }


def test_narrative_mapping_engine_extracts_overload_source_and_outlet() -> None:
    lines = NarrativeMappingEngine.build_physics_report_lines(_tensor())
    joined = "\n".join(lines)

    assert "Node[食神]" in joined
    assert "核心动能点" in joined
    assert "Source[比肩] -> Outlet[食神]" in joined
    assert "因果导通路径" in joined
    assert "R=0.62" in joined
    assert "Stress[F=4.20]" in joined


def test_build_v17_system_prompt_includes_physics_report_block() -> None:
    prompt = build_v17_system_prompt(
        will_proxy="stable",
        decision_anchor="六冲",
        action_signal=True,
        session_id="l2-bridge-case",
        physics_tensor=_tensor(),
    )

    assert "[PHYSICS_REPORT]" in prompt
    assert "Node[食神]" in prompt
    assert "Source[比肩] -> Outlet[食神]" in prompt
