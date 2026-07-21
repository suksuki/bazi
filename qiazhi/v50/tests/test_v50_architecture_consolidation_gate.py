from __future__ import annotations

from scripts.v50_run_architecture_gate import run_architecture_gate


def test_architecture_consolidation_gate_passes_all_authority_checks() -> None:
    result = run_architecture_gate()

    assert result["status"] == "PASS", result
    assert len(result["checks"]) == 17
    assert all(item["passed"] for item in result["checks"])
    assert result["r1_locked_assets"] == 20
    assert result["llm_used"] is False
    assert result["production_migration_performed"] is False


def test_architecture_gate_is_deterministic_for_the_same_source_tree() -> None:
    assert run_architecture_gate() == run_architecture_gate()
