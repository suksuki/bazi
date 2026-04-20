from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.services import decision_intel


def test_build_auto_decisions_dedupe_and_bucket() -> None:
    auto_resolutions = [
        {"id": "a", "source": "p1", "label": "冲突", "target_god": "伤官"},
        {"id": "a", "source": "p1", "label": "冲突", "target_god": "伤官"},
        {"id": "b", "source": "p2", "label": "合化", "target_god": "正官"},
    ]
    llm_ctx = [
        {"id": "a", "source": "p1", "label": "冲突", "target_god": "伤官", "status": "pending"},
    ]

    rows = decision_intel.build_auto_decisions(
        auto_resolutions=auto_resolutions,
        llm_arbitration_context=llm_ctx,
    )

    assert len(rows) == 2
    assert rows[0]["auto_bucket"] == "system"
    assert rows[1]["auto_bucket"] == "system"


def test_build_claim_conflict_graph() -> None:
    raw_physics = {
        "meta": {
            "plugin_claims": [
                {"claim_id": "c1", "plugin_id": "p1", "claim_text": "伤官见官", "target_god": "伤官", "logic_level": "L1", "priority": 0.9},
                {"claim_id": "c2", "plugin_id": "p2", "claim_text": "偏印夺食", "target_god": "偏印", "logic_level": "L2", "priority": 0.8},
            ],
            "plugin_conflicts": [
                {
                    "conflict_id": "x1",
                    "conflict_type": "opposite_signal",
                    "severity": "P2",
                    "claims": ["c1", "c2"],
                }
            ],
            "plugin_conflict_resolutions": [
                {"conflict_id": "x1", "status": "approved", "resolved_by": "system"},
            ],
        }
    }

    graph = decision_intel.build_claim_conflict_graph(raw_physics=raw_physics)
    assert graph["summary"]["conflict_count"] == 1
    assert graph["summary"]["resolved_conflict_count"] == 1
    assert graph["summary"]["open_conflict_count"] == 0


def test_build_decision_arbitration_sanitizes(monkeypatch) -> None:
    facts = [
        V17Fact(
            plugin_id="p1",
            text="测试事实",
            causal_tier=1,
            salience_weight=0.7,
            priority=0.6,
            decision_hint="",
            meta={},
        )
    ]
    raw_pending = [
        {"title": "老标题", "label": "<x>", "hint": "<y>"},
    ]

    def fake_compile(*, facts, spec_decisions, existing_rows, physics_tensor):
        assert existing_rows == raw_pending
        return {
            "manual_decisions": [{"title": "未清洗", "label": "<y>", "hint": "<x>"}],
            "auto_resolutions": [],
            "llm_arbitration_context": [],
            "pending_decisions": [],
        }

    def fake_apply(*, arbitration, meta):
        assert meta == {}
        return arbitration

    monkeypatch.setattr(
        "v17_rebirth.backend.services.decision_intel.logic_pd.collect_all_spec_facts_and_record",
        lambda raw: facts,
    )
    monkeypatch.setattr("v17_rebirth.backend.services.decision_intel.compile_decision_arbitration", fake_compile)
    monkeypatch.setattr("v17_rebirth.backend.services.decision_intel.apply_brain_action_queue", fake_apply)
    monkeypatch.setattr(
        "v17_rebirth.backend.services.decision_intel.collect_pending_decisions_from_specs",
        lambda f: [("x",)],
    )

    arbitration = decision_intel.build_decision_arbitration(
        raw_physics={"pending_decisions": raw_pending},
        spec_facts=facts,
    )
    assert arbitration["manual_decisions"][0]["title"] == "未清洗"
    assert arbitration["manual_decisions"][0]["label"] == "<y>"
