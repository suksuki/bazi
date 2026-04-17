from app.core.rules.decision_inbox_gate import apply_decision_inbox_signal_gate


def test_gate_blocks_low_abs_without_critical():
    meta: dict = {"l1_junction_flags": {"sgjg_severity": "MINOR_INTERFERENCE"}}
    settings = {"GLOBAL_DECISION_ABS_THRESHOLD": 5.0}
    out = apply_decision_inbox_signal_gate(meta=meta, settings=settings, clash_abs_loss_total=1.0)
    assert out["inbox_conflict_cards_eligible"] is False
    assert meta["decision_signal_to_noise"]["has_critical_marker"] is False


def test_gate_passes_when_critical_despite_low_abs():
    meta: dict = {"l1_junction_flags": {"sgjg_severity": "CRITICAL"}}
    settings = {"GLOBAL_DECISION_ABS_THRESHOLD": 5.0}
    out = apply_decision_inbox_signal_gate(meta=meta, settings=settings, clash_abs_loss_total=0.5)
    assert out["inbox_conflict_cards_eligible"] is True


def test_gate_passes_high_abs_without_critical():
    meta: dict = {"l1_junction_flags": {"sgjg_severity": "NONE"}}
    settings = {"GLOBAL_DECISION_ABS_THRESHOLD": 5.0}
    out = apply_decision_inbox_signal_gate(meta=meta, settings=settings, clash_abs_loss_total=12.0)
    assert out["inbox_conflict_cards_eligible"] is True


def test_gate_permissive_when_clash_metric_missing():
    meta: dict = {"l1_junction_flags": {"sgjg_severity": "NONE"}}
    settings = {"GLOBAL_DECISION_ABS_THRESHOLD": 5.0}
    out = apply_decision_inbox_signal_gate(meta=meta, settings=settings, clash_abs_loss_total=None)
    assert out["inbox_conflict_cards_eligible"] is True


def test_gate_passes_when_sanhe_cluster_bypasses_low_abs():
    meta: dict = {"l1_junction_flags": {"sgjg_severity": "MINOR_INTERFERENCE"}}
    settings = {"GLOBAL_DECISION_ABS_THRESHOLD": 5.0}
    out = apply_decision_inbox_signal_gate(
        meta=meta, settings=settings, clash_abs_loss_total=0.5, has_sanhe_cluster=True
    )
    assert out["inbox_conflict_cards_eligible"] is True
    assert out["sanhe_inbox_bypass"] is True
    assert out["has_critical_marker"] is False


def test_gate_passes_when_l1_inbox_signal_bypass_surface_other_than_sgjg():
    meta: dict = {
        "l1_junction_flags": {
            "sgjg_severity": "MINOR_INTERFERENCE",
            "l1_inbox_signal_bypass": True,
        }
    }
    settings = {"GLOBAL_DECISION_ABS_THRESHOLD": 5.0}
    out = apply_decision_inbox_signal_gate(meta=meta, settings=settings, clash_abs_loss_total=0.5)
    assert out["inbox_conflict_cards_eligible"] is True
