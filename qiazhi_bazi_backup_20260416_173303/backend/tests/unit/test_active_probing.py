from __future__ import annotations

from app.logic.brain.active_probing import evaluate_active_probing
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


def test_active_probing_pending_when_high_tension() -> None:
    pt = {
        "meta": {
            "decision_inbox_v1": {
                "match_scores": [
                    {"plugin_id": "classical.blind_school.v1", "score": 0.91},
                    {"plugin_id": "classical.wangshuai.v1", "score": 0.62},
                ]
            }
        }
    }
    po = {"classical.blind_school.v1": {}, "classical.wangshuai.v1": {}}
    out = evaluate_active_probing(physics_tensor=pt, plugin_outputs=po)
    assert out.should_probe is True
    assert out.block_mode is True
    assert out.interrupt is not None
    assert out.interrupt.state == "pending"


def test_active_probing_advisory_when_multi_plugin_but_not_hot() -> None:
    pt = {
        "meta": {
            "decision_inbox_v1": {
                "match_scores": [
                    {"plugin_id": "classical.blind_school.v1", "score": 0.65},
                ]
            }
        }
    }
    po = {"classical.blind_school.v1": {}, "classical.wangshuai.v1": {}}
    out = evaluate_active_probing(physics_tensor=pt, plugin_outputs=po)
    assert out.should_probe is True
    assert out.block_mode is False
    assert out.reason_code == "M3_ADVISORY_PROBE"


def test_active_probing_on_1990_sample_can_emit_pending() -> None:
    sample = _sample_bundle_1990_06_14_zhengguan()
    md = dict(sample["metadata"])
    # 日支子午冲会先触发婚姻宫位追问；此处显式写入婚姻偏置以覆盖 Decision Inbox 高压路径
    pl = dict(md.get("persistence_layer") or {})
    pl["marriage_palace_bias"] = {"ack": True, "source": "unit_test"}
    md["persistence_layer"] = pl
    pt = sample["physics_tensor"]
    pt.setdefault("meta", {})
    pt["meta"]["decision_inbox_v1"] = {
        "match_scores": [
            {"plugin_id": "classical.blind_school.v1", "score": 0.9},
            {"plugin_id": "classical.pattern_detector.v2", "score": 0.81},
        ]
    }
    po = {
        "classical.blind_school.v1": {"payload": {}},
        "classical.pattern_detector.v2": {"payload": {}},
    }
    out = evaluate_active_probing(physics_tensor=pt, plugin_outputs=po, metadata=md)
    assert out.should_probe is True
    assert out.interrupt is not None


def test_active_probing_zi_wu_marriage_palace_when_bias_missing() -> None:
    sample = _sample_bundle_1990_06_14_zhengguan()
    md = sample["metadata"]
    pt = sample["physics_tensor"]
    po = {"classical.pattern_detector.v2": {"payload": {}}}
    out = evaluate_active_probing(physics_tensor=pt, plugin_outputs=po, metadata=md)
    assert out.should_probe is True
    assert out.block_mode is True
    assert out.interrupt is not None
    assert out.reason_code == "M3_ZI_WU_MARRIAGE_PALACE_PROBE"
    assert out.interrupt.reason_code == "M3_ZI_WU_MARRIAGE_PALACE_PROBE"


def test_active_probing_blocks_on_l1_logic_conflict() -> None:
    sample = _sample_bundle_1990_06_14_zhengguan()
    pt = sample["physics_tensor"]
    pt.setdefault("meta", {})
    # V13.01：仅 FATAL（或极性+极小分差+CRITICAL）触发 L1 强阻断
    pt["meta"]["l1_junction_flags"] = {"sgjg_severity": "FATAL"}
    out = evaluate_active_probing(physics_tensor=pt, plugin_outputs={"sys.core.physics": {}}, metadata=sample["metadata"])
    assert out.should_probe is True
    assert out.block_mode is True
    assert out.interrupt is not None
    assert out.reason_code == "M3_L1_LOGIC_CONFLICT_PENDING"


def test_active_probing_critical_without_polarity_does_not_block_l1() -> None:
    sample = _sample_bundle_1990_06_14_zhengguan()
    pt = sample["physics_tensor"]
    pt.setdefault("meta", {})
    pt["meta"]["l1_junction_flags"] = {"sgjg_severity": "CRITICAL"}
    pt["meta"]["decision_signal_to_noise"] = {"has_critical_marker": True}
    out = evaluate_active_probing(physics_tensor=pt, plugin_outputs={"sys.core.physics": {}}, metadata=sample["metadata"])
    assert out.reason_code != "M3_L1_LOGIC_CONFLICT_PENDING"


def test_active_probing_unblocks_after_resume_ack() -> None:
    sample = _sample_bundle_1990_06_14_zhengguan()
    md = dict(sample["metadata"])
    pl = dict(md.get("persistence_layer") or {})
    pl["interrupt_request"] = {"state": "resumed", "reason_code": "M3_L1_LOGIC_CONFLICT_PENDING"}
    pl["resume_feedback_history"] = [{"feedback": {"answer": "确认冲突"}}]
    md["persistence_layer"] = pl
    pt = sample["physics_tensor"]
    pt.setdefault("meta", {})
    pt["meta"]["l1_junction_flags"] = {"sgjg_severity": "FATAL"}
    pt["meta"]["decision_signal_to_noise"] = {"has_critical_marker": True}
    out = evaluate_active_probing(physics_tensor=pt, plugin_outputs={"sys.core.physics": {}}, metadata=md)
    assert out.should_probe is True
    assert out.block_mode is False
    assert out.interrupt is None
    assert out.reason_code == "M3_L1_LOGIC_CONFLICT_ACKED"
