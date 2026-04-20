from __future__ import annotations

import json
from pathlib import Path

import v17_rebirth.scripts.audit_plugin_params as audit


def _write_plugin_samples(root: Path) -> None:
    logic_root = root / "backend" / "logic"
    config_root = logic_root / "configs"
    logic_root.mkdir(parents=True, exist_ok=True)
    config_root.mkdir(parents=True, exist_ok=True)

    (logic_root / "__init__.py").write_text("")
    plugin_file = logic_root / "plugin_audit_fixture.py"
    plugin_file.write_text(
        """
from v17_rebirth.backend.logic.configs.manager import get_plugin_config

PATTERN_DEFAULTS = {
    "classical.pattern.axis.v1": {
        "AXIS_MATCH_BASE": 0.42,
        "CANDIDATE_FOLLOWER_RATIO": 2.0,
    },
}


def _pattern_cfg(plugin_id: str, key: str, fallback: float) -> float:
    cfg = get_plugin_config(plugin_id)
    return float(cfg.get(key, PATTERN_DEFAULTS[plugin_id].get(key, fallback)))


class DemoAxis:
    plugin_id = "classical.pattern.axis.v1"
    DECLARED_PARAMS = {"AXIS_MATCH_BASE": 0.42, "UNUSED_AXIS": 0.33}

    def run(self) -> float:
        cfg = get_plugin_config(self.plugin_id)
        a = float(cfg.get("AXIS_MATCH_BASE", 0.42))
        b = _pattern_cfg(self.plugin_id, "CANDIDATE_FOLLOWER_RATIO", 2.0)
        return a + b
""".lstrip()
    )

    (config_root / "classical.pattern.axis.v1.json").write_text(
        json.dumps({"AXIS_MATCH_BASE": 0.5, "CANDIDATE_FOLLOWER_RATIO": 2.2}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_scoped_self_plugin_id_helper_and_get_reads(monkeypatch, tmp_path):
    _write_plugin_samples(tmp_path)
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LOGIC_ROOT", tmp_path / "backend" / "logic")
    monkeypatch.setattr(audit, "CONFIG_ROOT", tmp_path / "backend" / "logic" / "configs")

    rows = audit._collect_plugin_rows()
    target = next(row for row in rows if row["plugin_id"] == "classical.pattern.axis.v1")
    by_key = {item["key"]: item for item in target["param_audit"]}

    assert target["config_exists"] is True
    assert by_key["AXIS_MATCH_BASE"]["classification"] == "used_and_configurable"
    assert by_key["CANDIDATE_FOLLOWER_RATIO"]["classification"] == "used_and_configurable"
    assert by_key["CANDIDATE_FOLLOWER_RATIO"]["config_hooked"] is True


def test_json_report_can_emit(monkeypatch, tmp_path):
    _write_plugin_samples(tmp_path)
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LOGIC_ROOT", tmp_path / "backend" / "logic")
    monkeypatch.setattr(audit, "CONFIG_ROOT", tmp_path / "backend" / "logic" / "configs")

    payload = audit._collect_plugin_rows()
    assert payload
    assert any(row["plugin_id"] == "classical.pattern.axis.v1" for row in payload)


def test_module_function_config_reads_are_audited(monkeypatch, tmp_path):
    logic_root = tmp_path / "backend" / "logic"
    config_root = logic_root / "configs"
    logic_root.mkdir(parents=True, exist_ok=True)
    config_root.mkdir(parents=True, exist_ok=True)

    (logic_root / "__init__.py").write_text("")
    (logic_root / "plugin_module_scope_sample.py").write_text(
        """
from v17_rebirth.backend.logic.configs.manager import get_plugin_config

V17_SKILL_MANIFEST = {"id": "module.scope.v1"}
DECLARED_PARAMS = {
    "MODULE_RATIO": 0.35,
    "MODULE_BOOST": 1.1,
}


def _collect_rows() -> dict:
    cfg = get_plugin_config("module.scope.v1")
    ratio = cfg.get("MODULE_RATIO", DECLARED_PARAMS["MODULE_RATIO"])
    boost = cfg.get("MODULE_BOOST", DECLARED_PARAMS["MODULE_BOOST"])
    return {"ratio": ratio, "boost": boost}

def run_module_scope() -> dict:
    return _collect_rows()
""".lstrip()
    )
    (config_root / "module.scope.v1.json").write_text(
        json.dumps({"MODULE_RATIO": 0.5, "MODULE_BOOST": 1.2}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LOGIC_ROOT", tmp_path / "backend" / "logic")
    monkeypatch.setattr(audit, "CONFIG_ROOT", tmp_path / "backend" / "logic" / "configs")

    rows = audit._collect_plugin_rows()
    target = next(row for row in rows if row["plugin_id"] == "module.scope.v1")
    by_key = {item["key"]: item for item in target["param_audit"]}

    assert by_key["MODULE_RATIO"]["classification"] == "used_and_configurable"
    assert by_key["MODULE_BOOST"]["classification"] == "used_and_configurable"
    assert target["reads_config"] is True


def test_callsite_template_plugin_id_is_audited(monkeypatch, tmp_path):
    logic_root = tmp_path / "backend" / "logic"
    config_root = logic_root / "configs"
    logic_root.mkdir(parents=True, exist_ok=True)
    config_root.mkdir(parents=True, exist_ok=True)

    (logic_root / "__init__.py").write_text("")
    (logic_root / "plugin_template_sample.py").write_text(
        """
def _pattern_cfg(plugin_id: str, key: str, fallback: float) -> float:
    return float(fallback)


def _specialized_pattern_row(*, plugin_id: str) -> float:
    return _pattern_cfg(plugin_id, "SPECIALIZED_MIN_SCORE", 26.0) + _pattern_cfg(
        plugin_id,
        "SPECIALIZED_MAX_OTHER",
        14.0,
    ) + _pattern_cfg(plugin_id, "SPECIALIZED_MATCH_BASE", 0.76)


class DemoPattern:
    plugin_id = "classical.pattern.quzhi.v1"
    DECLARED_PARAMS = {
        "SPECIALIZED_MIN_SCORE": 26.0,
        "SPECIALIZED_MAX_OTHER": 14.0,
        "SPECIALIZED_MATCH_BASE": 0.76,
    }

    def collect_v17_facts(self):
        return _specialized_pattern_row(plugin_id=self.plugin_id)
""".lstrip()
    )

    # keep config file available to make classification deterministic
    (config_root / "classical.pattern.quzhi.v1.json").write_text(
        json.dumps(
            {
                "SPECIALIZED_MIN_SCORE": 26.0,
                "SPECIALIZED_MAX_OTHER": 14.0,
                "SPECIALIZED_MATCH_BASE": 0.76,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LOGIC_ROOT", tmp_path / "backend" / "logic")
    monkeypatch.setattr(audit, "CONFIG_ROOT", tmp_path / "backend" / "logic" / "configs")

    rows = audit._collect_plugin_rows()
    target = next(row for row in rows if row["plugin_id"] == "classical.pattern.quzhi.v1")
    by_key = {item["key"]: item for item in target["param_audit"]}

    assert by_key["SPECIALIZED_MIN_SCORE"]["classification"] == "used_and_configurable"
    assert by_key["SPECIALIZED_MAX_OTHER"]["classification"] == "used_and_configurable"
    assert by_key["SPECIALIZED_MATCH_BASE"]["classification"] == "used_and_configurable"


def test_cfg_object_passed_to_helper_is_audited(monkeypatch, tmp_path):
    logic_root = tmp_path / "backend" / "logic"
    config_root = logic_root / "configs"
    logic_root.mkdir(parents=True, exist_ok=True)
    config_root.mkdir(parents=True, exist_ok=True)

    (logic_root / "__init__.py").write_text("")
    (logic_root / "plugin_cfg_pass_sample.py").write_text(
        """
from v17_rebirth.backend.logic.configs.manager import get_plugin_config

V17_SKILL_MANIFEST = {"id": "cfg.pass.v1"}
DECLARED_PARAMS = {
    "FLOW_RATIO": 0.6,
    "FLOW_BOOST": 1.2,
}


def _collect_rows(values: dict, cfg: dict) -> float:
    ratio = float(cfg.get("FLOW_RATIO", DECLARED_PARAMS["FLOW_RATIO"]))
    boost = float(cfg.get("FLOW_BOOST", DECLARED_PARAMS["FLOW_BOOST"]))
    return ratio * boost


def analyze(values: dict, cfg: dict) -> float:
    return _collect_rows(values, cfg)


class DemoCfgPlugin:
    plugin_id = "cfg.pass.v1"

    def collect_v17_facts(self, physics_tensor):
        cfg = get_plugin_config(self.plugin_id)
        return analyze({}, cfg)
""".lstrip()
    )
    (config_root / "cfg.pass.v1.json").write_text(
        json.dumps({"FLOW_RATIO": 0.55, "FLOW_BOOST": 1.15}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LOGIC_ROOT", tmp_path / "backend" / "logic")
    monkeypatch.setattr(audit, "CONFIG_ROOT", tmp_path / "backend" / "logic" / "configs")

    rows = audit._collect_plugin_rows()
    target = next(row for row in rows if row["plugin_id"] == "cfg.pass.v1")
    by_key = {item["key"]: item for item in target["param_audit"]}

    assert by_key["FLOW_RATIO"]["classification"] == "used_and_configurable"
    assert by_key["FLOW_BOOST"]["classification"] == "used_and_configurable"
    assert target["reads_config"] is True


def test_workspace_audit_has_no_declared_unused_params():
    rows = audit._collect_plugin_rows()
    summary = audit._build_summary(rows)

    assert summary["declared_but_unused"] == []
