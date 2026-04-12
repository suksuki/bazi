from __future__ import annotations

import json
import re

from app.skills.final_verdict_parts.evidence import (
    format_audit_snapshot_inline,
    format_deity_abs_semantic_slices,
    get_logical_evidence,
)
from app.skills.final_verdict_parts.metadata_sanitize import (
    sanitize_metadata_for_verdict_llm,
    scrub_previous_verdict_sql,
    shallow_physics_for_llm_evidence,
)
from app.skills.final_verdict_parts.narrative_guard import (
    filter_logical_evidence_for_narrative_factory,
    inject_label_only_semantic_slices,
)
from app.skills.final_verdict_parts.physics_fallback import build_minimal_verdict_json_from_core_physics


def test_sanitize_metadata_strips_audit_keys() -> None:
    meta = {
        "pillars": {"year": {"stem": "甲", "branch": "子"}},
        "audit": {"logic_proposal": {"sql_patch": "x"}, "sql_patch": "UPDATE physics_interaction_params SET x"},
        "physics_interaction_params": {"CF_FLOATING_DECAY": 0.2},
    }
    out = sanitize_metadata_for_verdict_llm(meta)
    assert "pillars" in out
    assert "logic_proposal" not in str(out)
    assert "physics_interaction_params" not in out


def test_scrub_previous_verdict_sql() -> None:
    t = "正常行\nUPDATE physics_interaction_params SET param_value=1 WHERE param_key='X';\n尾行"
    s = scrub_previous_verdict_sql(t)
    assert "UPDATE physics_interaction" not in s
    assert "正常行" in s
    assert "尾行" in s


def test_shallow_physics_drops_runtime_config() -> None:
    pt = {"meta": {"runtime_physics_config": {"A": 1}, "solar_term": "立春"}, "abs_nodes": {"比肩": 1.0}}
    s = shallow_physics_for_llm_evidence(pt)
    assert "runtime_physics_config" not in (s.get("meta") or {})
    assert s["meta"]["solar_term"] == "立春"
    assert s["abs_nodes"]["比肩"] == 1.0


def test_format_deity_abs_semantic_slices() -> None:
    pt = {
        "deity_energy_axes": {
            "比肩": {"absolute_energy": 0.05},
            "劫财": {"absolute_energy": 3.0},
        }
    }
    lines = format_deity_abs_semantic_slices(pt)
    assert any("语义.十神.比肩" in x and "全无" in x for x in lines)
    assert any("劫财" in x and "中庸" in x for x in lines)


def test_format_deity_abs_semantic_slices_label_only_hides_abs_numeric() -> None:
    pt = {"deity_energy_axes": {"比肩": {"absolute_energy": 8.0}}}
    lines = format_deity_abs_semantic_slices(pt, label_only=True)
    blob = "\n".join(lines)
    assert "Abs≈" not in blob
    assert "8.0" not in blob
    assert any("偏强" in x for x in lines)


def test_format_audit_snapshot_redacts_ten_god_abs() -> None:
    meta = {"pillars": {"year": {"stem": "甲", "branch": "子"}}}
    pt = {"deity_energy_axes": {"比肩": {"absolute_energy": 9.9}}, "abs_nodes": {}}
    full = format_audit_snapshot_inline(meta, pt, redact_ten_god_abs=False)
    red = format_audit_snapshot_inline(meta, pt, redact_ten_god_abs=True)
    assert "9.900" in full or "9.9" in full
    assert "9.9" not in red and "9.900" not in red
    assert "叙事工厂已省略数值" in red


def test_get_logical_evidence_redact_drops_ten_god_abs_lines() -> None:
    pt = shallow_physics_for_llm_evidence(
        {
            "deity_energy_axes": {"正印": {"absolute_energy": 0.2}},
            "meta": {},
        }
    )
    lines = get_logical_evidence(
        metadata={},
        physics_tensor=pt,
        selected_cards=[],
        consensus_history=[],
        redact_audit_snapshot_abs=True,
    )
    lines = filter_logical_evidence_for_narrative_factory(lines, high_reasoning=False)
    lines = inject_label_only_semantic_slices(lines, physics_tensor=pt, enabled=True)
    blob = "\n".join(lines)
    assert not re.search(r"十神\.[^.]+\.Abs=", blob)
    assert "语义.十神" in blob


def test_get_logical_evidence_includes_semantic_header() -> None:
    pt = shallow_physics_for_llm_evidence(
        {
            "deity_energy_axes": {"正印": {"absolute_energy": 0.2}},
            "meta": {},
        }
    )
    lines = get_logical_evidence(metadata={}, physics_tensor=pt, selected_cards=[], consensus_history=[])
    assert any("语义.十神" in x for x in lines)


def test_physics_fallback_json_parseable() -> None:
    pt = {
        "plugin_outputs": {
            "sys.core.physics": {
                "verdict": "三合火局已登记，做功门偏泄。",
                "evidence": ["l1_step:sanhe_scan", "sys.core.physics=ok"],
            }
        }
    }
    raw = build_minimal_verdict_json_from_core_physics(pt, lang="ZH")
    obj = json.loads(raw)
    assert "核心气象" in obj["verdict_body"]
    assert obj["assertions"][0]["evidence_refs"] == ["plugin.sys.core.physics"]
