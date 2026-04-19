from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOGIC_ROOT = ROOT / "backend" / "logic"
CONFIG_ROOT = LOGIC_ROOT / "configs"


def _literal_or_none(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _collect_plugin_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(LOGIC_ROOT.rglob("*.py")):
        if path.name.startswith("_") or path.parent.name == "configs":
            continue
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except Exception:
            continue

        manifest: dict[str, Any] = {}
        params: dict[str, Any] = {}
        plugin_id = ""
        reads_config = False
        config_lookup_key = ""
        source_text = text

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "V17_SKILL_MANIFEST":
                        value = _literal_or_none(node.value)
                        if isinstance(value, dict):
                            manifest = value
                    if isinstance(target, ast.Name) and target.id == "DECLARED_PARAMS":
                        value = _literal_or_none(node.value)
                        if isinstance(value, dict):
                            params = value
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "plugin_id":
                value = _literal_or_none(node.value)
                if isinstance(value, str):
                    plugin_id = value
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "plugin_id":
                        value = _literal_or_none(node.value)
                        if isinstance(value, str):
                            plugin_id = value
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "get_plugin_config":
                reads_config = True
                if node.args:
                    value = _literal_or_none(node.args[0])
                    if isinstance(value, str):
                        config_lookup_key = value

        effective_id = str(manifest.get("id") or plugin_id or "").strip()
        if not effective_id and not params:
            continue

        cfg_key = config_lookup_key or effective_id
        cfg_path = CONFIG_ROOT / f"{cfg_key}.json"
        param_rows: list[dict[str, Any]] = []
        for param_key, default_value in sorted(params.items()):
            declared_ref = f'DECLARED_PARAMS["{param_key}"]'
            cfg_get_ref = f'cfg.get("{param_key}"'
            local_cfg_ref = f'local_cfg.get("{param_key}"'
            key_literal_ref = f'"{param_key}"'
            used_default = declared_ref in source_text
            used_cfg = cfg_get_ref in source_text or local_cfg_ref in source_text
            mentioned = key_literal_ref in source_text
            if used_default and used_cfg and cfg_path.exists():
                classification = "used_and_configurable"
            elif used_default and used_cfg:
                classification = "used_but_no_config_file"
            elif used_default:
                classification = "used_but_hardcoded"
            elif mentioned:
                classification = "mentioned_but_not_wired"
            else:
                classification = "declared_but_unused"
            param_rows.append(
                {
                    "key": param_key,
                    "default": default_value,
                    "used_default_fallback": used_default,
                    "config_hooked": used_cfg,
                    "config_file_present": cfg_path.exists(),
                    "classification": classification,
                }
            )
        rows.append(
            {
                "plugin_id": effective_id,
                "file": str(path.relative_to(ROOT)),
                "config_lookup_key": cfg_key,
                "config_exists": cfg_path.exists(),
                "config_file": str(cfg_path.relative_to(ROOT)) if cfg_path.exists() else "",
                "reads_config": reads_config,
                "param_count": len(params),
                "params": params,
                "param_audit": param_rows,
            }
        )
    return rows


def main() -> None:
    rows = _collect_plugin_rows()
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
