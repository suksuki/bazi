from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.admin.app import ADMIN_PREFIX, create_admin_app
from v40.api.app import API_PREFIX, create_app
from v40.project import build_mingli_depth_index, build_module_migration_status


def test_mingli_depth_index_is_separate_from_architecture_completion() -> None:
    index = build_mingli_depth_index(
        lab_summary={
            "counts": {
                "runtime_records": 4,
                "training_label_events": 8,
                "conversation_turns": 1,
                "local_overlays": 3,
                "training_examples": 3,
                "training_example_replays": 2,
                "training_replay_batches": 2,
                "global_weight_versions": 5,
                "evaluation_cases": 4,
                "evaluation_runs": 7,
                "shadow_compare_runs": 3,
            }
        }
    )

    assert index["architecture_completion_reference"] == 98
    assert 50 <= index["mingli_depth_percent"] <= 65
    assert index["status"] == "rc2_mingli_depth_migration_required"
    assert len(index["domains"]) == 6
    assert index["domains"][0]["key"] == "fact_depth"
    assert "P0: Real Case Bank / Acceptance Window" in index["priorities"]
    assert index["boundary"] == "mingli_depth_index_observes_depth_without_enabling_migrated_assets"


def test_mingli_depth_index_api_is_readonly() -> None:
    response = TestClient(create_app()).get(f"{API_PREFIX}/project/mingli-depth-index")

    assert response.status_code == 200
    body = response.json()
    assert body["index"]["version"] == "v40.mingli_depth_index.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "mingli_depth_index_reads_v40_evidence_without_migration_enablement"


def test_rc2_docs_define_migration_gate_and_depth_plan() -> None:
    plan = Path("qiazhi/v40/docs/V40_RC2_MINGLI_DEPTH_MIGRATION_PLAN.md").read_text(encoding="utf-8")
    gate = Path("qiazhi/v40/docs/V40_RC2_ASSET_MIGRATION_GATE.md").read_text(encoding="utf-8")
    module_map = Path("qiazhi/v40/docs/V40_RC2_MODULE_STATUS_AND_MIGRATION_MAP.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")

    assert "Mingli Depth Index" in plan
    assert "Bazi Fact Engine Pro" in plan
    assert "Hidden Factor Probe Engine" in plan
    assert "MigratedMingliAsset" in gate
    assert "draft → sidecar → evaluating → enabled" in gate
    assert "GET /api/v40/project/module-migration-status" in module_map
    assert "Direct V30 runtime reuse: 0" in module_map
    assert "V40-RC2: Mingli Depth Migration" in readme


def test_module_migration_status_keeps_v30_reuse_as_asset_migration_only() -> None:
    status = build_module_migration_status()

    assert status["summary"]["v30_direct_runtime_reuse_allowed"] == 0
    assert status["summary"]["new_required_groups"] >= 3
    assert status["summary"]["reusable_v30_asset_groups"] >= 10
    assert status["hard_rule"].startswith("V40 can reuse V30 mingli assets only through DTO")
    module_keys = {module["key"] for module in status["modules"]}
    assert "bazi_fact_engine_pro" in module_keys
    assert "asset_migration_gate" in module_keys
    asset_gate = next(row for row in status["modules"] if row["key"] == "asset_migration_gate")
    assert asset_gate["current_state"] == "v40_native_v1_sidecar_ready"
    assert "hidden_factor_probe_engine" in module_keys
    hidden_factor = next(row for row in status["modules"] if row["key"] == "hidden_factor_probe_engine")
    assert hidden_factor["current_state"] == "v40_native_v1_probe_signal_ready"
    assert "legacy_v30_ui_admin" in module_keys


def test_module_migration_status_api_is_readonly() -> None:
    response = TestClient(create_app()).get(f"{API_PREFIX}/project/module-migration-status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"]["version"] == "v40.module_migration_status.v1"
    assert body["status"]["summary"]["v30_direct_runtime_reuse_allowed"] == 0
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False


def test_admin_console_exposes_rc2_depth_and_module_map() -> None:
    page = TestClient(create_admin_app()).get(ADMIN_PREFIX)

    assert page.status_code == 200
    assert "Mingli Depth" in page.text
    assert "Module Map" in page.text
    assert "/admin/v40/api/mingli-depth-index" in page.text
    assert "/admin/v40/api/module-migration-status" in page.text
