from __future__ import annotations

from pathlib import Path

from v20.testing.runner import run_tier
from v20.testing.tiers import get_tier, test_tier_manifest as build_test_tier_manifest


def test_v20_test_tiers_are_bounded_and_opt_in_for_slow_work() -> None:
    manifest = build_test_tier_manifest()
    names = [row["name"] for row in manifest["tiers"]]

    assert names == ["smoke", "fast", "targeted", "full", "services", "corpus"]
    assert get_tier("fast").budget_seconds <= 20
    assert get_tier("services").commands[0].opt_in_env == "RUN_V20_SERVICE_TESTS"
    assert get_tier("corpus").commands[0].opt_in_env == "RUN_V20_CORPUS_TESTS"
    assert "SERVICE_AND_CORPUS_TESTS_REQUIRE_OPT_IN" in manifest["guardrails"]


def test_v20_test_runner_dry_run_expands_local_commands() -> None:
    result = run_tier("smoke", dry_run=True)

    assert result["ok"] is True
    assert result["tier"] == "smoke"
    assert result["budget_ok"] is True
    compile_cmd = result["commands"][0]
    assert compile_cmd["status"] == "dry_run"
    assert "v20/api/runtime.py" in compile_cmd["argv"]


def test_v20_test_scripts_and_docs_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    scripts = {
        "smoke": root / "v20/scripts/test_smoke.sh",
        "fast": root / "v20/scripts/test_fast.sh",
        "targeted": root / "v20/scripts/test_targeted.sh",
        "full": root / "v20/scripts/test_full.sh",
        "services": root / "v20/scripts/test_services.sh",
        "corpus": root / "v20/scripts/test_corpus.sh",
    }
    for tier, path in scripts.items():
        text = path.read_text(encoding="utf-8")
        assert "v20.testing.runner" in text
        assert tier in text
    doc = (root / "docs/v20/V20_TEST_SYSTEM.md").read_text(encoding="utf-8")
    assert "V20 uses bounded test tiers" in doc
    assert "RUN_V20_SERVICE_TESTS=1" in doc
    assert "RUN_V20_CORPUS_TESTS=1" in doc
