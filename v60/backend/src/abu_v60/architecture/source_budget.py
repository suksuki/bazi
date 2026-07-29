from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceBudget:
    relative_root: str
    suffix: str
    maximum_lines: int


@dataclass(frozen=True, slots=True)
class SourceBudgetViolation:
    path: str
    line_count: int
    maximum_lines: int


RUNTIME_SOURCE_BUDGETS = (
    SourceBudget("backend/src/abu_v60", ".py", 850),
    SourceBudget("web/src", ".ts", 500),
    SourceBudget("web/src", ".tsx", 500),
    SourceBudget("web/src", ".css", 600),
)

EXCLUDED_PARTS = frozenset(
    {
        "__pycache__",
        "dist",
        "generated",
        "node_modules",
    }
)


def audit_runtime_source_budgets(
    repository_root: Path,
) -> tuple[SourceBudgetViolation, ...]:
    violations: list[SourceBudgetViolation] = []
    for budget in RUNTIME_SOURCE_BUDGETS:
        source_root = repository_root / budget.relative_root
        for path in source_root.rglob(f"*{budget.suffix}"):
            relative_path = path.relative_to(repository_root)
            if EXCLUDED_PARTS.intersection(relative_path.parts):
                continue
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > budget.maximum_lines:
                violations.append(
                    SourceBudgetViolation(
                        path=relative_path.as_posix(),
                        line_count=line_count,
                        maximum_lines=budget.maximum_lines,
                    )
                )
    return tuple(sorted(violations, key=lambda item: item.path))


def format_source_budget_violations(
    violations: tuple[SourceBudgetViolation, ...],
) -> str:
    if not violations:
        return "runtime source-size budgets: PASS"
    details = "\n".join(
        f"- {item.path}: {item.line_count} lines (max {item.maximum_lines})" for item in violations
    )
    return (
        "Runtime source-size budget exceeded. Split by owner and responsibility; "
        "do not add a blanket exemption.\n"
        f"{details}"
    )
