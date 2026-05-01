from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v20.server import app
from v20.testing.matrix import build_test_coverage_matrix
from v20.testing.runner import main as runner_main, run_tier
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


def test_v20_test_runner_cli_accepts_flags_after_tier(capsys) -> None:
    code = runner_main(["smoke", "--dry-run", "--json"])

    output = capsys.readouterr().out
    assert code == 0
    assert '"tier": "smoke"' in output
    assert '"status": "dry_run"' in output


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


def test_v20_test_coverage_matrix_tracks_mainline_areas() -> None:
    matrix = build_test_coverage_matrix()
    areas = {row["area"] for row in matrix["areas"]}

    assert matrix["runtime_mutation"] is False
    assert {
        "runtime_feature_spine",
        "explicit_time_layer",
        "knowledge_llm_i18n",
        "access_roles",
        "ops_storage_redis",
        "corpus_learning_validation",
        "ui_static_shell",
    } <= areas


def test_v20_testing_matrix_endpoint_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/testing/matrix")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert data["default_tier"] == "fast"
