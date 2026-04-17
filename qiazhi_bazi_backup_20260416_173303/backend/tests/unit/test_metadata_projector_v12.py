"""V12 M1：三色投影器单测（1990-06-14 正官格 mock，无 LLM）。"""

from __future__ import annotations

import copy

from app.services.helpers.metadata_projector_v12 import MetadataProjectorV12


def _sample_bundle_1990_06_14_zhengguan() -> dict:
    """阳历 1990-06-14 样例：四柱 + 物理基准 + L2 正官格严格行（mock）。"""
    metadata = {
        "version": "1.0",
        "memory_schema_version": "2.0",
        "pillars": {
            "year": {"stem": "庚", "branch": "午", "energy_value": 100},
            "month": {"stem": "壬", "branch": "午", "energy_value": 100},
            "day": {"stem": "庚", "branch": "子", "energy_value": 100},
            "hour": {"stem": "丙", "branch": "子", "energy_value": 100},
        },
        "temporal_context": {"dayun": "甲申", "reference_year": 1990},
        "conflict_matrix": {"points": []},
        "persistence_layer": {
            "persistence_protocol": "persistence_layer.v1",
            "semantic_verdicts": [],
            "confirmed_verdicts": [],
        },
        "history_context": {},
        "active_verdict_skeleton": {"protocol": "active_verdict_skeleton.v1", "engine_bullets": [], "user_will_lines": []},
    }

    baseline_deity_scores = {
        "比肩": 3.2,
        "劫财": 2.1,
        "食神": 4.0,
        "伤官": 1.5,
        "偏财": 2.8,
        "正财": 5.0,
        "七杀": 2.4,
        "正官": 8.6,
        "偏印": 3.0,
        "正印": 3.5,
    }
    baseline_abs_nodes = {"庚": 2.0, "壬": 1.2, "丙": 0.9, "子": 1.5, "午": 1.8}
    baseline_normalized = {"wood": 0.12, "fire": 0.28, "earth": 0.18, "metal": 0.32, "water": 0.10}

    pattern_row = {
        "pattern_id": "GOV_PATTERN",
        "name": "正官格",
        "primary_axis": "Gov_Axis",
        "progress": 0.92,
        "affinity_score": 0.92,
        "exclusion_hit": False,
        "engine_v": "MANIFEST_V5.8_STRICT",
        "trace_logic": ["[GATING_CHECK] GOV_PATTERN: Axis=0.42 Req=0.28 Result=PASS"],
    }

    meta = {
        "params": {"WORK_MIN_THRESHOLD": 0.5},
        "climate_field_correction_v1": {"enabled": True, "opposing_element": "fire", "factors": {"fire": 0.95}},
        "pattern_thresholds": [pattern_row],
        "pattern_thresholds_engine": "universal_manifest_v1",
        "pattern_thresholds_status": "OK",
        "l2_pattern_result_summary_v1": "正官格",
        "hit_pattern_name": "正官格",
        "l2_pattern_engine": "MANIFEST_V5.8_STRICT",
        "intention_context": {"version": "will_proxy_v1", "active_intention": "seek_stability"},
        "semantic_label_bundle_v1": {"protocol": "semantic_label_bundle.v1", "labels": []},
    }

    physics_tensor = {
        "deity_scores": copy.deepcopy(baseline_deity_scores),
        "abs_nodes": copy.deepcopy(baseline_abs_nodes),
        "normalized": copy.deepcopy(baseline_normalized),
        "confidence": 0.91,
        "audit_log": {"param_version_id": "pv-mock-19900614", "skill_id": "physics_inference"},
        "meta": meta,
        "plugin_outputs": {"classical.pattern_detector.v2": {"payload": {}, "evidence": []}},
    }

    return {
        "metadata": metadata,
        "physics_tensor": physics_tensor,
        "user_intention": "seek_stability",
    }


def test_projector_static_baseline_matches_physics_exactly() -> None:
    bundle = _sample_bundle_1990_06_14_zhengguan()
    original_scores = copy.deepcopy(bundle["physics_tensor"]["deity_scores"])
    original_abs = copy.deepcopy(bundle["physics_tensor"]["abs_nodes"])
    original_norm = copy.deepcopy(bundle["physics_tensor"]["normalized"])

    tri = MetadataProjectorV12().project(bundle)

    assert tri.static_fact.baseline_tensor["deity_scores"] == original_scores
    assert tri.static_fact.baseline_tensor["abs_nodes"] == original_abs
    assert tri.static_fact.baseline_tensor["normalized"] == original_norm
    assert tri.static_fact.baseline_tensor["confidence"] == 0.91
    assert tri.static_fact.physics_param_version_id == "pv-mock-19900614"


def test_projector_pillars_and_temporal_unchanged() -> None:
    bundle = _sample_bundle_1990_06_14_zhengguan()
    tri = MetadataProjectorV12().project(bundle)

    assert tri.static_fact.pillars == bundle["metadata"]["pillars"]
    assert tri.static_fact.temporal_anchors == bundle["metadata"]["temporal_context"]
    assert tri.static_fact.climate_baseline == bundle["physics_tensor"]["meta"]["climate_field_correction_v1"]


def test_projector_l2_rows_and_intention_context() -> None:
    bundle = _sample_bundle_1990_06_14_zhengguan()
    tri = MetadataProjectorV12().project(bundle)

    assert len(tri.dynamic_inference.l2_pattern_rows) == 1
    row = tri.dynamic_inference.l2_pattern_rows[0]
    assert row.get("pattern_id") == "GOV_PATTERN"
    assert row.get("name") == "正官格"
    assert tri.dynamic_inference.will_intention_context.get("active_intention") == "seek_stability"
    assert tri.dynamic_inference.l2_engine_provenance.get("pattern_thresholds_engine") == "universal_manifest_v1"


def test_projector_arbiter_bias_user_intention_from_bundle() -> None:
    bundle = _sample_bundle_1990_06_14_zhengguan()
    tri = MetadataProjectorV12().project(bundle)
    assert tri.arbiter_bias.user_intention_id == "seek_stability"
    assert tri.arbiter_bias.persistence_layer.get("persistence_protocol") == "persistence_layer.v1"
