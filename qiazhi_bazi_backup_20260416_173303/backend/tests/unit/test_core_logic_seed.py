from __future__ import annotations

from app.skills.final_verdict_parts.core_logic_seed import format_core_logic_seed_user_block


def test_core_logic_seed_contains_l1_and_conflict() -> None:
    md = {"conflict_matrix": {"points": [{"kind": "harm", "detail": "寅巳穿（害）"}]}}
    pt: dict = {}
    bw: dict = {"morphing_hints": []}
    l1 = {"SHANG_GUAN_JIAN_GUAN": True}
    fd = {"primary_structure": "伤官配印", "stability_risk": "中"}
    sa: dict = {}
    out = format_core_logic_seed_user_block(
        metadata=md,
        physics_tensor=pt,
        blind_work=bw,
        l1_flags=l1,
        final_decision_v0=fd,
        school_audit=sa,
    )
    assert "[Core Logic Seed]" in out
    assert "伤官" in out or "正官" in out
    assert "寅巳" in out or "穿" in out


def test_core_logic_seed_skips_polluted_top_anomaly() -> None:
    md = {"conflict_matrix": {"points": []}}
    pt = {"top_anomaly": "未拿到结构化审计结论"}
    out = format_core_logic_seed_user_block(
        metadata=md,
        physics_tensor=pt,
        blind_work={},
        l1_flags={},
        final_decision_v0={},
        school_audit={},
    )
    assert "未拿到" not in out
