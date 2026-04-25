"""
V17.11–V17.12：递归扫描 L0–L3；支持 `PLUGIN` / `PLUGINS`；合并 L1 manifest 动态算子。
- 执行序：同帧内按 causal_tier（高先）再按 registry_priority（高先）稳定排序。
- conflict_level（dict 行）→ meta.physics_tension ∈ [0,1]（假定旧标度 0–5）。
"""
from __future__ import annotations

import logging
import importlib
import inspect
import pkgutil
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from v17_rebirth.backend.plugins.spec import V17Decision, V17Fact, V17PluginSpec
from v17_rebirth.backend.services.decision_compiler import infer_decision_hint
from v17_rebirth.backend.services.pattern_confidence import derive_pattern_confidence
from v17_rebirth.backend.services.evidence_bundle import compact_fact_meta
from v17_rebirth.backend.services.plugin_display import plugin_display_profile
from v17_rebirth.backend.services.plugin_governance import classify_plugin_governance
from v17_rebirth.backend.services.physics_layers import read_runtime_scores

_LOGIC_ROOT = Path(__file__).resolve().parent
_log = logging.getLogger(__name__)

LAYER_DIRS: Sequence[Tuple[str, str, int]] = (
    ("L0_physics_fields", "L0", 5),
    ("L1_atomic_ops", "L1", 4),
    ("L2_structure_patterns", "L2", 3),
    ("L3_modern_narrative", "L3", 2),
    ("L4_strategic_narrative", "L4", 1),
)


def infer_salience_weight(
    *,
    plugin_id: str,
    fact_text: str,
    causal_tier: int,
    priority: float,
) -> float:
    """
    V17.26：按显著性阶梯为 Fact 注入权重。

    Tier 0: 格局 / 三合六冲 / 月令主气 / 调候
    Tier 1: 十神偏枯 / 五行强度 / 强力神煞
    Tier 2: 一般结构关系
    Tier 3: 纳音 / 空亡 / 琐碎信息
    """
    text = str(fact_text or "").strip()
    pid = str(plugin_id or "").strip()
    pr = max(0.0, min(1.0, float(priority or 0.0)))

    tier0_hits = ("格局", "建禄格", "从儿格", "月令", "调候", "三合", "六冲")
    tier1_hits = ("十神", "偏强", "偏枯", "五行", "强度", "天医", "将星", "神煞")
    tier3_hits = ("纳音", "空亡")

    if any(k in text for k in tier0_hits) or pid in {"ten_god_pattern", "three_harmony", "l1.physics.op_branch_liuchong"}:
        return round(max(0.95, 0.95 + pr * 0.04), 4)
    if any(k in text for k in tier3_hits) or pid in {"kong_wang"}:
        return round(min(0.39, 0.18 + pr * 0.18), 4)
    if any(k in text for k in tier1_hits) or pid in {"shensha", "chang_sheng_12"}:
        return round(min(0.9, max(0.7, 0.7 + pr * 0.18)), 4)

    base = 0.42 + max(0, min(5, int(causal_tier))) * 0.045
    return round(min(0.69, max(0.4, base + pr * 0.12)), 4)


def deity_scores_from_tensor(physics_tensor: Dict[str, Any]) -> Dict[str, float]:
    return read_runtime_scores(physics_tensor)


def _conflict_level_to_tension(row: Dict[str, Any]) -> float:
    cl = row.get("conflict_level")
    if cl is None:
        return 0.0
    try:
        v = float(cl)
        return max(0.0, min(1.0, v / 5.0))
    except (TypeError, ValueError):
        return 0.0


def rows_dict_to_v17_facts(
    rows: List[Dict[str, Any]],
    *,
    causal_tier: int,
    default_plugin_id: str,
) -> List[V17Fact]:
    """将脱水 dict 行转为 V17Fact（供各标准 Spec 插件复用）。"""
    facts: List[V17Fact] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = str(row.get("fact", "")).strip()
        if not text:
            continue
        tension = _conflict_level_to_tension(row)
        
        # V17.99: 必须保留插件原生的 meta (如 target_god, impact_ratio 等)
        original_meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        meta: Dict[str, Any] = {**original_meta}
        meta = derive_pattern_confidence(
            plugin_id=str(row.get("plugin", default_plugin_id)),
            meta=meta,
            priority=float(row.get("priority", 0.5) or 0.5),
            salience_weight=infer_salience_weight(
                plugin_id=str(row.get("plugin", default_plugin_id)),
                fact_text=text,
                causal_tier=int(causal_tier),
                priority=float(row.get("priority", 0.5) or 0.5),
            ),
        )
        
        if tension > 0.0:
            meta["physics_tension"] = tension
        salience_weight = infer_salience_weight(
            plugin_id=str(row.get("plugin", default_plugin_id)),
            fact_text=text,
            causal_tier=int(causal_tier),
            priority=float(row.get("priority", 0.5) or 0.5),
        )
        decision_hint = str(
            row.get("decision_hint")
            or row.get("label")
            or infer_decision_hint(
                plugin_id=str(row.get("plugin", default_plugin_id)),
                fact_text=text,
                meta=meta,
            )
            or ""
        ).strip()
        facts.append(
            V17Fact(
                plugin_id=str(row.get("plugin", default_plugin_id)),
                text=text,
                causal_tier=int(causal_tier),
                salience_weight=salience_weight,
                priority=float(row.get("priority", 0.5) or 0.5),
                decision_hint=decision_hint,
                meta=meta,
            )
        )
    return facts
def spec_execution_sort_key(s: V17PluginSpec) -> Tuple[int, float, str]:
    """与运行时 `collect_all_spec_facts*` 遍历顺序一致。"""
    rp = float(getattr(s, "registry_priority", 0.5))
    return (-int(s.causal_tier), -rp, str(s.plugin_id))


def _plugins_from_module(mod: Any) -> List[V17PluginSpec]:
    out: List[V17PluginSpec] = []
    
    # 动态检查：只要具备 collect_v17_facts 且有 plugin_id，我们就视其为 V17 插件
    # 这可以规避由于模块重载导致的 isinstance 失败问题
    def _is_v17_spec(p: Any) -> bool:
        return hasattr(p, "collect_v17_facts") and hasattr(p, "plugin_id")

    multi = getattr(mod, "PLUGINS", None)
    if isinstance(multi, list):
        for p in multi:
            if _is_v17_spec(p):
                out.append(p)
    
    plug = getattr(mod, "PLUGIN", None)
    if _is_v17_spec(plug):
        out.append(plug)
        
    return out


_MANIFEST_SPECS_CACHE: Optional[List[V17PluginSpec]] = None


def warm_manifest_operators() -> None:
    """由 AutoScanner 调用：仅预热 manifest，避免在 collect 内递归 iter。"""
    global _MANIFEST_SPECS_CACHE
    if _MANIFEST_SPECS_CACHE is not None:
        return
    from v17_rebirth.backend.logic.L1_atomic_ops.dynamic_manifest_plugins import build_manifest_operator_specs

    _MANIFEST_SPECS_CACHE = build_manifest_operator_specs()


def _manifest_specs_cached() -> List[V17PluginSpec]:
    global _MANIFEST_SPECS_CACHE
    if _MANIFEST_SPECS_CACHE is None:
        warm_manifest_operators()
    return list(_MANIFEST_SPECS_CACHE or [])


def _gather_specs_unsorted() -> List[V17PluginSpec]:
    specs: List[V17PluginSpec] = []
    for _subdir, _tag, _tier, mod in iter_logic_modules():
        specs.extend(_plugins_from_module(mod))
    seen = {s.plugin_id for s in specs}
    for m in _manifest_specs_cached():
        if m.plugin_id in seen:
            continue
        specs.append(m)
        seen.add(m.plugin_id)
    return specs


_MODULE_CACHE: Optional[List[Tuple[str, str, int, Any]]] = None


def clear_logic_module_cache() -> None:
    """测试或热重载时清空 discovery 缓存。"""
    global _MODULE_CACHE, _MANIFEST_SPECS_CACHE
    _MODULE_CACHE = None
    _MANIFEST_SPECS_CACHE = None
    try:
        from v17_rebirth.backend.services.auto_scanner import AutoScanner

        AutoScanner.reset()
    except Exception:
        pass


def iter_logic_modules() -> List[Tuple[str, str, int, Any]]:
    """(layer_dir, layer_tag, default_tier, imported_module)"""
    global _MODULE_CACHE
    if _MODULE_CACHE is not None:
        return _MODULE_CACHE
    found: List[Tuple[str, str, int, Any]] = []
    for subdir, tag, tier in LAYER_DIRS:
        base = _LOGIC_ROOT / subdir
        if not base.is_dir():
            continue
        for mod in pkgutil.iter_modules([str(base)]):
            if mod.ispkg or mod.name.startswith("_"):
                continue
            fq = f"v17_rebirth.backend.logic.{subdir}.{mod.name}"
            try:
                m = importlib.import_module(fq)
            except Exception as exc:
                _log.warning("[plugin_discovery] import module %s failed: %s", fq, exc)
                continue
            found.append((subdir, tag, tier, m))
    _MODULE_CACHE = found
    return found


def iter_all_plugin_specs() -> List[V17PluginSpec]:
    return sorted(_gather_specs_unsorted(), key=spec_execution_sort_key)


def plugin_execution_order_map() -> Dict[str, int]:
    return {s.plugin_id: i + 1 for i, s in enumerate(iter_all_plugin_specs())}


def collect_all_spec_facts(physics_tensor: Dict[str, Any]) -> List[V17Fact]:
    rows: List[V17Fact] = []
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    for spec in iter_all_plugin_specs():
        rows.extend(spec.collect_v17_facts(pt))
    return rows


def collect_all_spec_facts_and_record(physics_tensor: Dict[str, Any]) -> List[V17Fact]:
    """与 `collect_all_spec_facts` 相同，但按插件写入运行时 telemetry（最近 Facts）。"""
    from v17_rebirth.backend.services.auto_scanner import AutoScanner
    from v17_rebirth.backend.services.plugin_runtime_state import record_plugin_run

    AutoScanner.ensure_loaded()
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    rows: List[V17Fact] = []
    for spec in iter_all_plugin_specs():
        fs = spec.collect_v17_facts(pt)
        record_plugin_run(
            plugin_id=spec.plugin_id,
            causal_tier=int(spec.causal_tier),
            fact_texts=[f.text for f in fs],
        )
        rows.extend(fs)
    return rows


def collect_pending_decisions_from_specs(facts: List[V17Fact]) -> List[V17Decision]:
    out: List[V17Decision] = []
    for spec in iter_all_plugin_specs():
        out.extend(spec.get_pending_decisions(facts))
    return sorted(out, key=lambda d: -d.priority)


def v17_fact_to_row(f: V17Fact) -> Dict[str, Any]:
    meta = dict(f.meta or {}) if isinstance(f.meta, dict) else {}
    return {
        "plugin": f.plugin_id,
        "plugin_id": f.plugin_id,
        "fact": f.text,
        "label": f.decision_hint or f.text,
        "weight": float(f.salience_weight or 0.0),
        "priority": float(f.priority or 0.0),
        **compact_fact_meta(meta),
    }


def v17_decision_to_row(d: V17Decision) -> Dict[str, Any]:
    return {
        "id": d.id,
        "title": d.title,
        "label": d.label,
        "source": d.source,
        "priority": d.priority,
        "target_god": d.target_god,
        "physical_impact": dict(d.physical_impact or {}),
    }


def collect_legacy_dict_rows(deity_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """兼容旧调用方：等价于当前 Spec 路径的 dict 行。"""
    pt: Dict[str, Any] = {"deity_scores": deity_scores if isinstance(deity_scores, dict) else {}}
    return [v17_fact_to_row(f) for f in collect_all_spec_facts(pt)]


def registry_rows_for_admin() -> List[Dict[str, Any]]:
    from v17_rebirth.backend.logic.spec_validator import SpecValidator
    
    # 扫描全量 Skill 规范
    skills = {s["id"] or s["file_rel"]: s for s in SpecValidator.scan_all_plugins()}
    
    order = plugin_execution_order_map()
    id_meta: Dict[str, Tuple[str, str, str]] = {}
    id_mod: Dict[str, Any] = {}
    for subdir, tag, tier, mod in iter_logic_modules():
        name = getattr(mod, "__name__", "")
        stem = str(name).split(".")[-1]
        for plug in _plugins_from_module(mod):
            id_meta[plug.plugin_id] = (tag, subdir, stem)
            id_mod[plug.plugin_id] = mod

    rows: List[Dict[str, Any]] = []
    for spec in iter_all_plugin_specs():
        pid = spec.plugin_id
        mod = id_mod.get(pid)
        tag, subdir, stem = id_meta.get(pid, ("L1", "L1_atomic_ops", "manifest"))
        
        # 寻找对应的 Skill 规范
        skill = skills.get(pid)
        if not skill:
            # 尝试通过模块名匹配
            skill = skills.get(f"{subdir}/{stem}.py")

        summary = str(getattr(spec, "manifest_summary", "") or "").strip()
        rationale = str(getattr(spec, "manifest_rationale", "") or "").strip()
        
        if skill and skill.get("manifest"):
            m = skill["manifest"]
            summary = m.get("Description") or m.get("summary") or summary
            rationale = m.get("Rationale") or m.get("rationale") or rationale

        if not summary:
            summary = str(getattr(spec, "doc_summary", "") or "").strip()
        if not rationale:
            rationale = str(getattr(spec, "doc_rationale", "") or "").strip()
            
        if mod is not None:
            summary = summary or str(getattr(mod, "PLUGIN_SUMMARY", "") or getattr(mod, "PLUGIN_DESCRIPTION", "") or "").strip()
            rationale = rationale or str(getattr(mod, "PLUGIN_RATIONALE", "") or getattr(mod, "PLUGIN_DESIGN_RATIONALE", "") or "").strip()

        config_path = Path(__file__).resolve().parent / "configs" / f"{pid}.json"
        config_exists = config_path.exists()
        config_file = f"backend/logic/configs/{pid}.json"

        if (not skill or not bool(skill.get("valid"))) and mod is None and summary:
            skill = {
                "valid": True,
                "id": pid,
                "manifest": {
                    "id": pid,
                    "Layer": tag,
                    "Skill_Type": "ManifestBacked",
                    "Domain": "Physics",
                    "Description": summary,
                    "Rationale": rationale or summary,
                },
                "params": {},
                "policy_errors": [],
                "config_required": False,
                "config_file": config_file if config_exists else "",
                "config_exists": config_exists,
                "policy_valid": True,
            }

        synthetic_summary = summary or str(getattr(spec, "plugin_id", "")).strip() or "V17 插件"
        synthetic_rationale = rationale or synthetic_summary

        if (
            (not skill or not bool(skill.get("valid")))
            and mod is not None
            and (config_exists or pid.startswith("classical.") or pid.startswith("l1.physics.op_") or pid.startswith("l0.foundation."))
        ):
            skill = {
                "valid": True,
                "id": pid,
                "manifest": {
                    "id": pid,
                    "Layer": tag,
                    "Skill_Type": "SpecBacked",
                    "Domain": "Physics" if tag in {"L0", "L1"} else "Patterns",
                    "Description": synthetic_summary,
                    "Rationale": synthetic_rationale,
                },
                "params": {},
                "policy_errors": [],
                "config_required": bool(config_exists),
                "config_file": config_file if config_exists else "",
                "config_exists": config_exists,
                "policy_valid": True,
            }
        
        module_doc = _compact_admin_text(inspect.getdoc(mod) if mod is not None else "")
        spec_doc = _compact_admin_text(inspect.getdoc(spec.__class__) or "")
        display_profile = plugin_display_profile(
            plugin_id=pid,
            manifest=skill.get("manifest", {}) if skill else {},
            summary=summary,
            rationale=rationale,
            module_doc=module_doc,
            spec_doc=spec_doc,
        )
        definition_text = display_profile["display_definition"]
        trigger_condition_text = _plugin_trigger_condition_text(mod, fallback=module_doc or summary or spec_doc)
        detail_description = display_profile["display_description"]
        kind = "manifest_row" if mod is None else "spec"
        governance_profile = classify_plugin_governance(
            plugin_id=pid,
            layer=tag,
            causal_tier=int(spec.causal_tier),
            manifest=skill.get("manifest", {}) if skill else {},
        )
        
        rows.append(
            {
                "layer": tag,
                "layer_dir": subdir,
                "module": stem,
                "plugin_id": pid,
                "causal_tier": int(spec.causal_tier),
                "registry_priority": float(getattr(spec, "registry_priority", 0.5)),
                "execution_order": int(order.get(pid, 0)),
                "kind": kind,
                "function_summary": summary,
                "design_rationale": rationale,
                "module_doc": module_doc,
                "spec_doc": spec_doc,
                "display_name": display_profile["display_name"],
                "display_definition": display_profile["display_definition"],
                "display_description": display_profile["display_description"],
                "technical_label": display_profile["technical_label"],
                "family_label": display_profile["family_label"],
                "definition_text": definition_text,
                "trigger_condition_text": trigger_condition_text,
                "detail_description": detail_description,
                "declared_params": skill.get("params", {}) if skill else {},
                "skill_manifest": skill.get("manifest", {}) if skill else {},
                "is_standard_skill": bool(skill and skill.get("valid")),
                "policy_valid": bool(skill.get("policy_valid", False)) if skill else False,
                "policy_errors": list(skill.get("policy_errors", [])) if skill else [],
                "config_required": bool(skill.get("config_required", False)) if skill else False,
                "config_exists": bool(skill.get("config_exists", False)) if skill else False,
                "config_file": str(skill.get("config_file", "") or "") if skill else "",
                "governance_profile": governance_profile,
                "governance_class": str(governance_profile.get("governance_class") or ""),
                "authority_level": str(governance_profile.get("authority_level") or ""),
                "output_contract": str(governance_profile.get("output_contract") or ""),
                "learning_family": str(governance_profile.get("learning_family") or ""),
            }
        )
    return sorted(rows, key=lambda r: (int(r.get("execution_order", 999)), str(r.get("plugin_id", ""))))


def annotate_causal_trace(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """为每行补充上游执行链说明（就地更新 dict）。"""
    ordered = sorted(rows, key=lambda r: (int(r.get("execution_order", 999)), str(r.get("plugin_id", ""))))
    before_ids: List[str] = []
    for r in ordered:
        pid = str(r.get("plugin_id", "")).strip()
        prev = list(before_ids)
        r["executed_before_plugin_ids"] = prev
        if not prev:
            r["causal_trace_text"] = "执行流第一站：此前无上游插件输出，本插件为场数据提供初始锚点。"
        else:
            tail = "、".join(prev[-4:])
            r["causal_trace_text"] = (
                f"上游已执行 {len(prev)} 支插件（序末含 {tail}），"
                f"推理场已递进至 {r.get('layer', '?')}；本插件在其事实叠加之后裁决。"
            )
        if pid:
            before_ids.append(pid)
        # V17.14b：本期测算是否对该插件产出了事实（与 merge_registry_with_runtime 的 activated 对齐）
        facts_row = r.get("last_facts") if isinstance(r.get("last_facts"), list) else []
        r["causal_active_path"] = bool(r.get("activated")) and bool([t for t in facts_row if str(t).strip()])
        if r["causal_active_path"]:
            r["causal_trace_text"] = (
                str(r.get("causal_trace_text") or "").rstrip("。")
                + "；〔本期活跃路径〕本插件已输出事实碎屑，因果链在此节点发生实质做功。"
            )
    return rows


def _compact_admin_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return re.sub(r"\s+", " ", text)


def _plugin_trigger_condition_text(mod: Any, *, fallback: str = "") -> str:
    if mod is None:
        return _compact_admin_text(fallback) or "该插件由清单动态挂载，触发条件取决于对应物理命中项。"
    doc = _compact_admin_text(inspect.getdoc(mod) or "")
    if any(k in doc for k in ("触发", "判定", "检测", "超阈", "达到", "命中")):
        return doc

    fn = getattr(mod, "_collect_rows", None)
    lines = _source_trigger_lines(fn)
    if lines:
        return "；".join(lines)

    method = getattr(type(getattr(mod, "PLUGIN", None)), "collect_v17_facts", None)
    lines = _source_trigger_lines(method)
    if lines:
        return "；".join(lines)
    return _compact_admin_text(fallback) or "当前插件未显式声明触发条件。"


def _source_trigger_lines(fn: Any) -> List[str]:
    if fn is None:
        return []
    try:
        source = inspect.getsource(fn)
    except Exception:
        return []
    out: List[str] = []
    for raw in source.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("def ") or line.startswith("@"):
            continue
        if line in {"return []", "return rows"}:
            continue
        if (
            " if " in f" {line} "
            or line.startswith("if ")
            or any(token in line for token in (">=", "<=", ">", "<", "==", "!="))
        ):
            out.append(_compact_admin_text(line))
        elif any(token in line for token in ("ratio =", "locked =", "pattern =", "score =", "priority =", "intensity =")):
            out.append(_compact_admin_text(line))
        if len(out) >= 4:
            break
    return out
