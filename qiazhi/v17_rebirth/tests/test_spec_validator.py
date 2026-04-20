from __future__ import annotations

from pathlib import Path

from v17_rebirth.backend.logic.spec_validator import SpecValidator


def test_spec_validator_flags_missing_config_file(tmp_path: Path) -> None:
    plugin_file = tmp_path / "sample_plugin.py"
    plugin_file.write_text(
        """
V17_SKILL_MANIFEST = {
    "id": "demo.plugin",
    "Description": "demo",
}

DECLARED_PARAMS = {
    "ALPHA": 1.0,
}

class DemoPlugin:
    plugin_id: str = "demo.plugin"

    def collect_v17_facts(self, physics_tensor):
        return []
""",
        encoding="utf-8",
    )

    result = SpecValidator.validate_plugin_file(plugin_file)

    assert result["valid"] is True
    assert result["config_required"] is True
    assert result["config_exists"] is False
    assert "Missing plugin config file" in result["policy_errors"]
    assert result["policy_valid"] is False


def test_spec_validator_flags_plugin_output_id_mismatch(tmp_path: Path) -> None:
    plugin_file = tmp_path / "bad_output_plugin.py"
    plugin_file.write_text(
        """
V17_SKILL_MANIFEST = {
    "id": "demo.good",
    "Description": "demo",
}

class DemoPlugin:
    plugin_id: str = "demo.good"

    def collect_v17_facts(self, physics_tensor):
        return [
            {
                "plugin": "demo.bad",
                "fact": "x",
            }
        ]
""",
        encoding="utf-8",
    )

    result = SpecValidator.validate_plugin_file(plugin_file)

    assert result["valid"] is True
    assert result["plugin_output_ids"] == ["demo.bad"]
    assert result["class_plugin_ids"] == ["demo.good"]
    assert result["policy_valid"] is False
    assert any("Plugin output id mismatch" in msg for msg in result["policy_errors"])


def test_core_plugins_remain_policy_valid() -> None:
    core_plugin_ids = {
        "l2.risk.risk_matrix",
        "l1.physics.op_branch_sanhe",
        "l1.physics.op_branch_muku",
        "l1.physics.op_branch_liuchong",
        "l1.physics.op_branch_liuhe",
        "l1.physics.op_branch_liupo",
        "l1.physics.op_branch_liuhai",
        "l1.physics.op_status",
        "ten_god_pattern",
        "shensha",
        "kong_wang",
    }

    results = SpecValidator.scan_all_plugins()
    by_id = {
        str(row.get("id") or "").strip(): row
        for row in results
        if str(row.get("id") or "").strip()
    }

    missing = sorted(core_plugin_ids - set(by_id.keys()))
    assert not missing, f"missing core plugins in scan: {missing}"

    invalid = {
        plugin_id: by_id[plugin_id].get("policy_errors") or by_id[plugin_id].get("errors") or []
        for plugin_id in sorted(core_plugin_ids)
        if not bool(by_id[plugin_id].get("policy_valid"))
    }
    assert not invalid, f"core plugin policy violations: {invalid}"
