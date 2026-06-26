from __future__ import annotations

from v30.knowledge import build_knowledge_rule_portrait_signals
from v30.runtime import create_smoke_runtime


def test_seed_registry_builds_bound_knowledge_rule_portrait_signals() -> None:
    runtime = create_smoke_runtime("krp-runtime")
    signals = build_knowledge_rule_portrait_signals(runtime.feature_evidence)
    types = {signal.signal_type for signal in signals}
    assert {"knowledge", "rule", "portrait"} <= types
    assert all(signal.evidence_ids for signal in signals)
    assert all(signal.source_id.startswith("v30.") for signal in signals)
    assert all("v20" not in signal.source_id for signal in signals)


def test_runtime_trace_contains_knowledge_rule_portrait_signals() -> None:
    runtime = create_smoke_runtime("krp-trace")
    signals = runtime.question_plan.knowledge_rule_portrait_signals
    assert len(signals) >= 3
    assert {signal["signal_type"] for signal in signals} >= {"knowledge", "rule", "portrait"}
    assert any(signal["boundary"] == "rule_blocks_fixed_useful_god_without_review" for signal in signals)
