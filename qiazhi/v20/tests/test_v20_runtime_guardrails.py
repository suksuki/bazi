from __future__ import annotations

import ast

from v20.corpus.canonical_case import CanonicalCase
from v20.corpus.precompute_runner import precompute_case
from v20.tests.support_paths import v20_path


def test_v20_corpus_precompute_is_dry_run_only() -> None:
    case = CanonicalCase("v20.case.sample", ("甲子", "戊辰", "甲午", "辛酉"))
    snapshot = precompute_case(case)

    assert snapshot["case"]["input_hash"]
    assert snapshot["runtime_mutation"] is False
    assert snapshot["feature_count"] >= 5
    assert "PRECOMPUTE_DRY_RUN_ONLY" in snapshot["guardrails"]


def test_v20_package_does_not_import_v19() -> None:
    for path in v20_path().rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(name == "v19" or name.startswith("v19.") for name in names), path
