from __future__ import annotations

from pathlib import Path

from abu_v60.architecture.source_budget import (
    audit_runtime_source_budgets,
    format_source_budget_violations,
)


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    violations = audit_runtime_source_budgets(repository_root)
    print(format_source_budget_violations(violations))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
