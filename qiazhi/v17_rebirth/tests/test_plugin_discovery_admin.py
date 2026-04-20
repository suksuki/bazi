from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import registry_rows_for_admin


def test_manifest_backed_l1_operator_is_exposed_as_standard_skill() -> None:
    rows = registry_rows_for_admin()
    by_id = {
        str(row.get("plugin_id") or "").strip(): row
        for row in rows
        if str(row.get("plugin_id") or "").strip()
    }

    geography = by_id["l1.physics.op_geography"]
    assert geography["kind"] == "manifest_row"
    assert geography["is_standard_skill"] is True
    assert geography["policy_valid"] is True
    assert geography["skill_manifest"]["Skill_Type"] == "ManifestBacked"
    assert geography["skill_manifest"]["Layer"] == "L1"


def test_liuchong_plugin_is_now_a_policy_valid_skill() -> None:
    rows = registry_rows_for_admin()
    by_id = {
        str(row.get("plugin_id") or "").strip(): row
        for row in rows
        if str(row.get("plugin_id") or "").strip()
    }

    liuchong = by_id["l1.physics.op_branch_liuchong"]
    assert liuchong["kind"] == "spec"
    assert liuchong["is_standard_skill"] is True
    assert liuchong["policy_valid"] is True
    assert liuchong["config_required"] is True
    assert liuchong["config_exists"] is True


def test_l2_spec_backed_plugin_is_exposed_as_standard_skill() -> None:
    rows = registry_rows_for_admin()
    by_id = {
        str(row.get("plugin_id") or "").strip(): row
        for row in rows
        if str(row.get("plugin_id") or "").strip()
    }

    ziping = by_id["classical.ziping.month_command.v1"]
    assert ziping["kind"] == "spec"
    assert ziping["is_standard_skill"] is True
    assert ziping["policy_valid"] is True
    assert ziping["skill_manifest"]["Skill_Type"] == "SpecBacked"
    assert ziping["skill_manifest"]["Layer"] == "L2"

    blind = by_id["classical.blind.work_axis.v1"]
    assert blind["is_standard_skill"] is True
    assert blind["skill_manifest"]["Skill_Type"] == "SpecBacked"
