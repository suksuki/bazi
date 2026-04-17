#!/usr/bin/env python3
"""Redline scanner: block forbidden hardcoded business constants in skills."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "app" / "skills"

FORBIDDEN_VALUES = {
    1.2,
    0.8,
    0.6,
    0.9,
}


class SkillConstantVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.violations: list[tuple[int, float]] = []
        self.allowed_ranges: list[tuple[int, int]] = []

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        # 允许种子字典内使用业务常数
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in {"DEFAULT_INTERACTION_PARAMS", "DEFAULT_SEASONAL_BASE"}:
                self.allowed_ranges.append((node.lineno, getattr(node, "end_lineno", node.lineno)))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
        target = node.target
        if isinstance(target, ast.Name) and target.id in {"DEFAULT_INTERACTION_PARAMS", "DEFAULT_SEASONAL_BASE"}:
            self.allowed_ranges.append((node.lineno, getattr(node, "end_lineno", node.lineno)))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:  # noqa: N802
        if isinstance(node.value, (float, int)):
            value = float(node.value)
            if value in FORBIDDEN_VALUES and not self._is_allowed_line(node.lineno):
                self.violations.append((node.lineno, value))
        self.generic_visit(node)

    def _is_allowed_line(self, lineno: int) -> bool:
        return any(start <= lineno <= end for start, end in self.allowed_ranges)


def main() -> int:
    failed = False
    py_files = sorted(p for p in SKILLS_DIR.rglob("*.py") if p.name != "__init__.py")
    for path in py_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = SkillConstantVisitor(path)
        visitor.visit(tree)
        for lineno, value in visitor.violations:
            failed = True
            rel = path.relative_to(ROOT)
            print(f"[HARD-CODED] {rel}:{lineno} contains forbidden literal {value}")
    if failed:
        print("Redline violated: move business constants into DB params.")
        return 1
    print("Skill hardcode scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
