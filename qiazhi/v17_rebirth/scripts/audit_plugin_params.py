from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
from collections import OrderedDict
import ast
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOGIC_ROOT = ROOT / "backend" / "logic"
CONFIG_ROOT = LOGIC_ROOT / "configs"
DOC_PATH = ROOT / "docs" / "V17_PLUGIN_PARAMETER_AUDIT_AUTO_REPORT.md"


def _literal(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _string(node: ast.AST | None) -> str | None:
    value = _literal(node)
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _classify_default_risk(default_value: Any, key: str) -> str:
    if isinstance(default_value, str):
        default_text = default_value.strip()
        if default_text.startswith("ref(global.") and default_text.endswith(")"):
            return ""
    v = _safe_float(default_value)
    if v is None:
        return "非数值默认值，建议补充类型边界校验"
    upper = key.upper()

    if "PRIORITY" in upper:
        if not (0.0 <= v <= 1.0):
            return "优先级通常应在[0,1]，当前越界"
        return ""
    if "IMPACT_RATIO" in upper:
        if not (-2.0 <= v <= 2.0):
            return "冲击比例建议优先在[-2,2]范围，当前可疑"
        if v == 0.0:
            return "比例/权重为0会导致插件失活"
        return ""
    if "RATIO" in upper or "WEIGHT" in upper:
        if not (0.0 <= v <= 2.0):
            return "比例/权重建议优先在[0,2]，当前越界"
        if v == 0.0:
            return "比例/权重为0会导致插件失活"
        return ""
    if "MULT" in upper or "COEFF" in upper or "BOOST" in upper or "GAIN" in upper:
        if v < 0.0 or v > 8.0:
            return "放大类参数建议控制在[0,8]范围"
        return ""
    if "LIMIT" in upper or "CAP" in upper:
        if not (0.0 <= v <= 1.0):
            return "上限参数建议优先在[0,1]，当前可疑"
        return ""
    if "THRESH" in upper or upper.startswith("MIN_") or upper.startswith("MAX_"):
        if v < 0.0:
            return "阈值参数不能为负"
        return ""
    if "EFFICIENCY" in upper:
        if not (0.0 <= v <= 1.0):
            return "效率参数建议在[0,1]，当前可疑"
        return ""
    if "DAMP" in upper:
        if v < 0.0 or v > 1.0:
            return "阻尼建议在[0,1]"
        return ""
    if v < 0.0:
        return "参数为负值，请确认是否为故意设计"
    return ""


def _collect_manifest_id(tree: ast.AST) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "V17_SKILL_MANIFEST":
                continue
            data = _literal(node.value)
            if not isinstance(data, dict):
                continue
            manifest_id = data.get("id")
            if isinstance(manifest_id, str):
                manifest_id = manifest_id.strip()
                if manifest_id:
                    return manifest_id
    return ""


def _collect_class_plugin_ids(tree: ast.AST) -> set[str]:
    plugin_ids: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == "plugin_id":
                value = _string(item.value)
                if value:
                    plugin_ids.add(value)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "plugin_id":
                        value = _string(item.value)
                        if value:
                            plugin_ids.add(value)
                        break
    return plugin_ids


def _collect_declared_defaults(tree: ast.AST) -> dict[str, Any]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DECLARED_PARAMS":
                    data = _literal(node.value)
                    return data if isinstance(data, dict) else {}
    return {}


def _collect_default_buckets(tree: ast.AST) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    declared = _collect_declared_defaults(tree)
    defaults: dict[str, dict[str, Any]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if not name.endswith("_DEFAULTS"):
                continue
            data = _literal(node.value)
            if not isinstance(data, dict):
                continue
            for plugin_id, plugin_defaults in data.items():
                if not isinstance(plugin_id, str) or not isinstance(plugin_defaults, dict):
                    continue
                defaults.setdefault(plugin_id.strip(), {}).update(plugin_defaults)
    return declared, defaults


def _collect_config_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Name) or call.func.id != "get_plugin_config":
            continue
        plugin_id = _string(call.args[0]) if call.args else None
        if plugin_id:
            aliases[target.id] = plugin_id
    return aliases


def _extract_declared_param_refs(tree: ast.AST) -> set[str]:
    declared_keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        if not isinstance(node.value, ast.Name):
            continue
        if node.value.id != "DECLARED_PARAMS":
            continue
        key = _string(node.slice)
        if key:
            declared_keys.add(key)
    return declared_keys


def _extract_callable_signatures(tree: ast.AST) -> dict[str, list[str]]:
    signatures: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params: list[str] = []
        for arg in list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs):
            params.append(arg.arg)
        signatures[node.name] = params
    return signatures


def _resolve_call_arg(call: ast.Call, arg_name: str, params: list[str]) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == arg_name:
            return kw.value
    if arg_name in params:
        index = params.index(arg_name)
        if index < len(call.args):
            return call.args[index]
    return None


def _extract_function_defs(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _looks_like_cfg_name(name: str) -> bool:
    lowered = name.lower()
    if lowered == "cfg" or lowered == "config":
        return True
    return (
        lowered.startswith("cfg_")
        or lowered.endswith("_cfg")
        or lowered.startswith("config_")
        or lowered.endswith("_config")
        or "_config_" in lowered
    )


def _collect_helper_access_templates(
    tree: ast.AST,
    helper_names: set[str],
) -> dict[str, dict[str, dict[str, Any]]]:
    templates: dict[str, dict[str, dict[str, Any]]] = {}
    signatures = _extract_callable_signatures(tree)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = signatures.get(node.name, [])
        if not params:
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            func_name = call.func.id if isinstance(call.func, ast.Name) else ""
            if func_name not in helper_names or len(call.args) < 2:
                continue
            plugin_expr = call.args[0]
            if not isinstance(plugin_expr, ast.Name) or plugin_expr.id not in params:
                continue
            key = _string(call.args[1])
            if not key:
                continue
            fallback = _literal(call.args[2]) if len(call.args) >= 3 else None
            templates.setdefault(node.name, {}).setdefault(plugin_expr.id, {})[key] = fallback
    return templates


def _resolve_plugin_id(
    expr: ast.AST | None,
    class_plugin_ids: set[str],
    local_aliases: dict[str, set[str]],
) -> str | None:
    direct = _string(expr)
    if direct:
        if direct in local_aliases:
            values = local_aliases[direct]
            return next(iter(values)) if len(values) == 1 else None
        return direct

    if isinstance(expr, ast.Name) and expr.id in local_aliases:
        values = local_aliases[expr.id]
        return next(iter(values)) if len(values) == 1 else None

    if (
        isinstance(expr, ast.Attribute)
        and isinstance(expr.value, ast.Name)
        and expr.value.id == "self"
        and expr.attr == "plugin_id"
        and len(class_plugin_ids) == 1
    ):
        return next(iter(class_plugin_ids))

    if isinstance(expr, ast.Name) and expr.id == "plugin_id" and len(class_plugin_ids) == 1:
        return next(iter(class_plugin_ids))

    return None


def _collect_scoped_accesses(
    scope_node: ast.AST,
    class_plugin_ids: set[str],
    helper_call_templates: dict[str, dict[str, dict[str, Any]]] | None = None,
    callable_signatures: dict[str, list[str]] | None = None,
    callable_defs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] | None = None,
    seed_aliases: dict[str, set[str]] | None = None,
    call_depth: int = 0,
    max_call_depth: int = 3,
) -> tuple[dict[str, str], dict[str, dict[str, Any]], dict[str, set[str]], dict[tuple[str, str], Any]]:
    cfg_aliases: dict[str, str] = {}
    helper_calls: dict[str, dict[str, Any]] = {}
    cfg_accesses: dict[str, set[str]] = {}
    cfg_fallbacks: dict[tuple[str, str], Any] = {}
    helper_call_templates = helper_call_templates or {}
    callable_signatures = callable_signatures or {}
    callable_defs = callable_defs or {}
    local_seed_aliases = {key: set(values) for key, values in (seed_aliases or {}).items()}

    helper_names = {"_pattern_cfg", "_ziping_cfg", "_plugin_match_cfg"}

    if isinstance(scope_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        callable_nodes = [scope_node]
    elif isinstance(scope_node, ast.ClassDef):
        callable_nodes = [n for n in scope_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    else:
        callable_nodes = [
            n for n in ast.walk(scope_node)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    for method in callable_nodes:
        local_aliases: dict[str, set[str]] = {key: set(values) for key, values in local_seed_aliases.items()}
        if class_plugin_ids:
            for pid in class_plugin_ids:
                local_aliases.setdefault("plugin_id", set()).add(pid)

        for node in ast.walk(method):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    target_name = target.id

                    if isinstance(node.value, ast.Call):
                        call = node.value
                        if isinstance(call.func, ast.Name) and call.func.id == "get_plugin_config":
                            plugin_id = _resolve_plugin_id(call.args[0] if call.args else None, class_plugin_ids, local_aliases)
                            if plugin_id:
                                cfg_aliases[target_name] = plugin_id
                                local_aliases.setdefault(target_name, set()).add(plugin_id)
                            continue

                    if target_name == "plugin_id":
                        value = _string(node.value)
                        if value:
                            local_aliases.setdefault("plugin_id", set()).add(value)
                        continue
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                value = _string(node.value)
                if value:
                    local_aliases.setdefault(node.target.id, set()).add(value)

        for node in ast.walk(method):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
                key = _string(node.args[0])
                obj = node.func.value
                if not key or not isinstance(obj, ast.Name):
                    continue
                pid_set = local_aliases.get(obj.id)
                if not pid_set or len(pid_set) != 1:
                    continue
                plugin_id = next(iter(pid_set))
                cfg_accesses.setdefault(plugin_id, set()).add(key)
                if len(node.args) >= 2:
                    cfg_fallbacks[(plugin_id, key)] = _literal(node.args[1])
                continue

            if isinstance(node.func, ast.Name) and node.func.id in helper_names and len(node.args) >= 2:
                plugin_id = _resolve_plugin_id(node.args[0], class_plugin_ids, local_aliases)
                key = _string(node.args[1])
                if not plugin_id or not key:
                    continue
                fallback = _literal(node.args[2]) if len(node.args) >= 3 else None
                helper_calls.setdefault(plugin_id, {})[key] = fallback
                continue

            if isinstance(node.func, ast.Name):
                template = helper_call_templates.get(node.func.id, {})
                if not template:
                    if call_depth >= max_call_depth:
                        continue
                    call_name = node.func.id
                    callee = callable_defs.get(call_name)
                    callee_signature = callable_signatures.get(call_name, [])
                    if callee is None or not callee_signature:
                        continue
                    merged_aliases: dict[str, set[str]] = {
                        key: set(values) for key, values in local_aliases.items()
                    }
                    injected_cfg = False
                    for arg_name in callee_signature:
                        if not _looks_like_cfg_name(arg_name):
                            continue
                        arg_expr = _resolve_call_arg(node, arg_name, callee_signature)
                        plugin_id = _resolve_plugin_id(arg_expr, class_plugin_ids, local_aliases)
                        if not plugin_id:
                            continue
                        merged_aliases.setdefault(arg_name, set()).add(plugin_id)
                        injected_cfg = True

                    if injected_cfg:
                        nested_cfg_aliases, nested_helper_calls, nested_cfg_accesses, nested_cfg_fallbacks = _collect_scoped_accesses(
                            callee,
                            class_plugin_ids,
                            helper_call_templates=helper_call_templates,
                            callable_signatures=callable_signatures,
                            callable_defs=callable_defs,
                            seed_aliases=merged_aliases,
                            call_depth=call_depth + 1,
                            max_call_depth=max_call_depth,
                        )
                        cfg_aliases.update(nested_cfg_aliases)
                        for key, value in nested_helper_calls.items():
                            helper_calls.setdefault(key, {}).update(value)
                        for key, values in nested_cfg_accesses.items():
                            cfg_accesses.setdefault(key, set()).update(values)
                        cfg_fallbacks.update(nested_cfg_fallbacks)
                    continue
                params = callable_signatures.get(node.func.id, [])
                for param_name, accesses in template.items():
                    arg_expr = _resolve_call_arg(node, param_name, params)
                    plugin_id = _resolve_plugin_id(arg_expr, class_plugin_ids, local_aliases)
                    if not plugin_id:
                        continue
                    for key, fallback in accesses.items():
                        helper_calls.setdefault(plugin_id, {})[key] = fallback

    return cfg_aliases, helper_calls, cfg_accesses, cfg_fallbacks


def _extract_helper_calls(tree: ast.AST) -> dict[str, dict[str, Any]]:
    helper_calls: dict[str, dict[str, Any]] = {}
    helper_names = {"_pattern_cfg", "_ziping_cfg", "_plugin_match_cfg"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = node.func.id if isinstance(node.func, ast.Name) else ""
        if func_name not in helper_names:
            continue
        if len(node.args) < 2:
            continue
        plugin_id = _string(node.args[0])
        key = _string(node.args[1])
        if not plugin_id or not key:
            continue
        fallback = _literal(node.args[2]) if len(node.args) >= 3 else None
        helper_calls.setdefault(plugin_id, {})[key] = fallback
    return helper_calls


def _collect_plugin_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for path in sorted(LOGIC_ROOT.rglob("*.py")):
        if path.name.startswith("_") or path.parent.name == "configs":
            continue

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            continue

        manifest_id = _collect_manifest_id(tree)
        class_ids = _collect_class_plugin_ids(tree)
        discovered_plugin_ids: set[str] = set(class_ids)
        if manifest_id:
            discovered_plugin_ids.add(manifest_id)

        declared_params, defaults_buckets = _collect_default_buckets(tree)
        cfg_aliases = _collect_config_aliases(tree)
        callable_defs = _extract_function_defs(tree)
        cfg_accesses: dict[str, set[str]] = {}
        cfg_fallbacks: dict[tuple[str, str], Any] = {}
        declared_keys = _extract_declared_param_refs(tree)
        helper_calls = _extract_helper_calls(tree)
        helper_call_templates = _collect_helper_access_templates(tree, {"_pattern_cfg", "_ziping_cfg", "_plugin_match_cfg"})
        callable_signatures = _extract_callable_signatures(tree)

        for class_node in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            node_plugin_ids = set()
            for item in class_node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == "plugin_id":
                    value = _string(item.value)
                    if value:
                        node_plugin_ids.add(value)
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "plugin_id":
                            value = _string(item.value)
                            if value:
                                node_plugin_ids.add(value)
                            break

            scoped_aliases, scoped_helper_calls, scoped_accesses, scoped_fallbacks = _collect_scoped_accesses(
                class_node,
                node_plugin_ids,
                helper_call_templates=helper_call_templates,
                callable_signatures=callable_signatures,
                callable_defs=callable_defs,
            )
            cfg_aliases.update(scoped_aliases)
            for key, value in scoped_helper_calls.items():
                helper_calls.setdefault(key, {}).update(value)
            for key, values in scoped_accesses.items():
                cfg_accesses.setdefault(key, set()).update(values)
            cfg_fallbacks.update(scoped_fallbacks)

            discovered_plugin_ids.update(node_plugin_ids)

        for fn_node in [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            scoped_aliases, scoped_helper_calls, scoped_accesses, scoped_fallbacks = _collect_scoped_accesses(
                fn_node,
                set(discovered_plugin_ids),
                helper_call_templates=helper_call_templates,
                callable_signatures=callable_signatures,
                callable_defs=callable_defs,
            )
            cfg_aliases.update(scoped_aliases)
            for key, value in scoped_helper_calls.items():
                helper_calls.setdefault(key, {}).update(value)
            for key, values in scoped_accesses.items():
                cfg_accesses.setdefault(key, set()).update(values)
            cfg_fallbacks.update(scoped_fallbacks)

        if declared_params:
            target_plugin = ""
            if manifest_id:
                target_plugin = manifest_id
            elif len(discovered_plugin_ids) == 1:
                target_plugin = next(iter(discovered_plugin_ids))
            if target_plugin:
                defaults_buckets.setdefault(target_plugin, {}).update(declared_params)

        plugin_ids = set(discovered_plugin_ids) | set(cfg_aliases.values()) | set(helper_calls.keys()) | set(cfg_accesses.keys())
        if not plugin_ids:
            continue

        for plugin_id in sorted(plugin_ids):
            cfg_path = CONFIG_ROOT / f"{plugin_id}.json"
            cfg_exists = cfg_path.exists()
            plugin_defaults = defaults_buckets.get(plugin_id, {})
            plugin_helper_defaults = helper_calls.get(plugin_id, {})
            accessed_keys = cfg_accesses.get(plugin_id, set())
            used_keys = set(accessed_keys) | set(plugin_helper_defaults)
            all_keys = set(plugin_defaults) | set(plugin_helper_defaults) | used_keys
            if not all_keys:
                continue

            param_rows: list[dict[str, Any]] = []
            for key in sorted(all_keys):
                plugin_declared_default = plugin_defaults.get(key)
                default_source = "未声明"
                if key in plugin_defaults:
                    default_value = plugin_declared_default
                    if key in declared_keys:
                        default_source = "DECLARED_PARAMS"
                    else:
                        default_source = "pattern_defaults"
                elif key in plugin_helper_defaults:
                    default_value = plugin_helper_defaults.get(key)
                    if default_value is not None:
                        default_source = "helper_default"
                else:
                    default_value = cfg_fallbacks.get((plugin_id, key))
                    if default_value is None:
                        default_value = "-"

                config_hooked = key in used_keys
                used_default_fallback = (
                    key in plugin_defaults
                    or key in plugin_helper_defaults
                    or (plugin_id, key) in cfg_fallbacks
                )
                if config_hooked and used_default_fallback:
                    classification = "used_and_configurable" if cfg_exists else "used_but_no_config_file"
                elif config_hooked:
                    classification = "hardcoded_or_missing_default"
                elif key in plugin_defaults:
                    classification = "declared_but_unused"
                else:
                    classification = "mentioned_only"

                param_rows.append(
                    {
                        "key": key,
                        "default": default_value,
                        "source": default_source,
                        "used_default_fallback": bool(used_default_fallback),
                        "config_hooked": config_hooked,
                        "config_file_present": cfg_exists,
                        "classification": classification,
                        "value_risk": _classify_default_risk(default_value, key),
                    }
                )

            rows.append(
                {
                    "plugin_id": plugin_id,
                    "file": str(path.relative_to(ROOT)),
                    "config_lookup_key": plugin_id,
                    "config_exists": cfg_exists,
                    "config_file": str(cfg_path.relative_to(ROOT)) if cfg_exists else "",
                    "reads_config": bool(
                        plugin_id in cfg_accesses
                        or plugin_id in helper_calls
                        or any(access_key[0] == plugin_id for access_key in cfg_fallbacks.keys())
                    ),
                    "param_count": len(param_rows),
                    "param_audit": sorted(param_rows, key=lambda row: str(row["key"])),
                }
            )

    rows.sort(key=lambda row: str(row["plugin_id"]))
    return rows


def _write_missing_config_files(rows: list[dict[str, Any]]) -> int:
    """将有可回收默认值的插件缺省配置写入配置目录，返回写入文件数。"""
    written = 0
    for row in rows:
        plugin_id = str(row.get("plugin_id") or "").strip()
        if not plugin_id:
            continue
        if row.get("config_file"):
            continue
        cfg_path = Path(row.get("file", ""))
        if not cfg_path.parts:
            continue
        config_values: OrderedDict[str, Any] = OrderedDict()
        for item in row.get("param_audit", []):
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "")
            source = str(item.get("source") or "")
            default = item.get("default")
            if not key or source == "未声明" or source == "helper_default":
                continue
            if str(default) == "-":
                continue
            config_values[key] = default

        if not config_values:
            continue

        abs_cfg = CONFIG_ROOT / f"{plugin_id}.json"
        abs_cfg.parent.mkdir(parents=True, exist_ok=True)
        with abs_cfg.open("w", encoding="utf-8") as f:
            json.dump(config_values, f, ensure_ascii=False, indent=2, sort_keys=True)
        written += 1
    return written


def _build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_params = sum(row.get("param_count", 0) for row in rows)
    missing_cfg = [
        row["plugin_id"] for row in rows if row.get("param_count", 0) > 0 and not row.get("config_exists")
    ]
    declared_unused = [
        f'{row["plugin_id"]}:{item["key"]}'
        for row in rows
        for item in row.get("param_audit", [])
        if item.get("classification") == "declared_but_unused"
    ]
    high_risk = [
        f'{row["plugin_id"]}:{item["key"]}:{item["value_risk"]}'
        for row in rows
        for item in row.get("param_audit", [])
        if isinstance(item.get("value_risk"), str) and item.get("value_risk")
    ]

    return {
        "total_plugins": len(rows),
        "total_params": total_params,
        "plugins_with_missing_config": sorted(missing_cfg),
        "declared_but_unused": declared_unused,
        "high_risk_default_params": high_risk,
    }


def _markdown_report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# V17 插件参数来源与默认值审计（自动版）")
    lines.append("")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 总览")
    lines.append(f"- 插件数：{summary['total_plugins']}")
    lines.append(f"- 参数项数：{summary['total_params']}")
    lines.append(f"- 配置文件缺失：{len(summary['plugins_with_missing_config'])}")

    lines.append("")
    lines.append("## 风险清单")
    lines.append("- 未落地参数（声明未接线）：")
    if summary["declared_but_unused"]:
        for item in summary["declared_but_unused"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - 无")

    lines.append("- 高风险默认值：")
    if summary["high_risk_default_params"]:
        for item in summary["high_risk_default_params"]:
            lines.append(f"  - {item}")
    else:
        lines.append("  - 无")

    if summary["plugins_with_missing_config"]:
        lines.append("")
        lines.append("## 配置缺失")
        lines.append("| 插件 ID | 说明 |")
        lines.append("| --- | --- |")
        for plugin_id in summary["plugins_with_missing_config"]:
            lines.append(f"| {plugin_id} | 缺失 backend/logic/configs/{plugin_id}.json |")

    lines.append("")
    lines.append("## 明细（Top 400）")
    lines.append("| 插件 | 参数 | 默认值 | 来源 | 分类 | 风险 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    shown = 0
    for row in rows:
        plugin_id = str(row.get("plugin_id") or "")
        for item in row.get("param_audit", []):
            if shown >= 400:
                break
            key = str(item.get("key"))
            default = json.dumps(item.get("default"), ensure_ascii=False)
            source = str(item.get("source"))
            classification = str(item.get("classification"))
            risk = str(item.get("value_risk") or "-")
            lines.append(f"| {plugin_id} | {key} | {default} | {source} | {classification} | {risk} |")
            shown += 1
    if shown >= 400:
        lines.append("")
        lines.append("说明：明细超过 400 行时截断展示。")

    lines.append("")
    lines.append("## 下一步建议")
    lines.append("- 按清单处理 `declared_but_unused`，优先确认是否确为历史冗余参数。")
    lines.append("- 对 `used_but_no_config_file` 类项立即补齐配置文件，避免回退到硬编码。")
    lines.append("- 优先把关键风险项纳入 `V17_PLUGIN_DEFAULT_VALUE_AUDIT`，并设置变更审计。")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="V17 插件参数来源与默认值审计")
    parser.add_argument("--emit-json", action="store_true", help="输出 JSON + summary")
    parser.add_argument("--markdown", default=str(DOC_PATH), help="Markdown 报告输出路径")
    parser.add_argument("--skip-markdown", action="store_true", help="不生成 Markdown 报告")
    parser.add_argument("--seed-missing-configs", action="store_true", help="为缺失配置文件写入可用默认值")
    args = parser.parse_args(argv)

    rows = _collect_plugin_rows()
    summary = _build_summary(rows)
    if args.seed_missing_configs and summary["plugins_with_missing_config"]:
        wrote_count = _write_missing_config_files(rows)
        if wrote_count:
            # 变更后需要刷新一次视图
            rows = _collect_plugin_rows()
            summary = _build_summary(rows)

    if not args.skip_markdown:
        report_path = Path(args.markdown)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_markdown_report(rows, summary), encoding="utf-8")

    payload = {"summary": summary, "plugins": rows} if args.emit_json else rows
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
