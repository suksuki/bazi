from __future__ import annotations

from pathlib import Path

from abu_v60.architecture.source_budget import (
    audit_runtime_source_budgets,
    format_source_budget_violations,
)


def test_runtime_source_files_respect_maintainability_budget() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    violations = audit_runtime_source_budgets(repository_root)

    assert not violations, format_source_budget_violations(violations)
