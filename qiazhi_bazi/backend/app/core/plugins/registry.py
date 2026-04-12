"""Plugin registry and lifecycle hooks for Bazi OS."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Dict, List, Literal, Set, Tuple

from app.plugins.blind_school.core import run_blind_school_plugin
from app.plugins.blind_school.skill_manifest_loader import list_blind_skills
from app.plugins.modern_wealth_risk.core import run_modern_wealth_risk_plugin
from app.plugins.modern_wealth_risk.skill_manifest_loader import list_modern_wealth_skills
from app.plugins.base_physics.manifest_loader import load_l1_physics_manifest
from app.plugins.base_physics.skill_manifest_loader import list_base_physics_skills, load_base_physics_skill_manifest
from app.plugins.chronos.core import run_chronos_plugin
from app.plugins.chronos.skill_manifest_loader import list_chronos_skills
from app.plugins.wangshuai.core import run_wangshuai_plugin
from app.plugins.wangshuai.skill_manifest_loader import list_wangshuai_skills

from app.core.config.physics_settings import resolve_physics_settings
from app.core.plugins.plugin_metadata_loader import merge_plugin_manifest_into_metadata, plugin_manifest_for_operator_card
from app.plugins.base_physics.core_operators.op_stem_fusion import judgment_protocol_dynamic_lines_for_stem_fusion
from app.plugins.base_physics.core_operators.op_sub_branch_interaction import (
    judgment_protocol_dynamic_lines_for_sub_branch_operator,
)

HookName = Literal["on_physics_complete", "on_verdict_ready"]

PluginLayer = Literal["L0", "L1", "L2", "L3", "L4"]


def _run_sys_core_physics_bundle_lazy(**ctx: Any) -> Dict[str, Any]:
    """延迟导入，避免 registry ↔ services 包循环依赖。"""
    from app.services.helpers.sys_core_physics_plugin import run_sys_core_physics_bundle_plugin

    return run_sys_core_physics_bundle_plugin(**ctx)

# 与 enabled_plugins 无关：每次 on_physics_complete 必跑（显式名单 ∪ 全部 L0）
_ALWAYS_ON_PHYSICS_COMPLETE: frozenset[str] = frozenset({"sys.core.physics"})


def _chronos_registry_runner(**ctx: Any) -> Dict[str, Any]:
    """L1 流水线已写入时跳过；仅跑 physics 而无 pipeline 时在此补写 meta 与审计行。"""
    pt = ctx.get("physics_tensor") or {}
    if not isinstance(pt, dict):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}
    meta = pt.get("meta")
    if isinstance(meta, dict) and meta.get("chronos_v1"):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}
    md = ctx.get("metadata") or {}
    rc = meta.get("runtime_physics_config") if isinstance(meta, dict) else None
    out = run_chronos_plugin(
        physics_tensor=pt,
        metadata=md,
        physics_config=rc if isinstance(rc, dict) else None,
    )
    ch = list(out.get("audit_items") or [])
    if ch:
        audit = pt.setdefault("audit_log", {})
        if isinstance(audit, dict):
            l1 = list(audit.get("l1_operator_audit_items") or [])
            if not any((x.get("id") == "chronos-mp-command") for x in l1):
                audit["l1_operator_audit_items"] = l1 + ch
            audit["chronos_audit_items"] = ch
    return {"verdict": "", "evidence": [], "confidence_score": 1.0}


@dataclass(frozen=True)
class PluginSpec:
    plugin_id: str
    category: str
    layer_id: PluginLayer
    label: str
    dependencies: List[str]
    priority: float
    audit_source: str
    hook: HookName
    runner: Callable[..., Dict[str, Any]]


_PLUGIN_STATS: Dict[str, Dict[str, Any]] = {}

# 预留：互斥插件对（同开时写入 manifest 警告，供前端/LLM 提高警觉）
_PLUGIN_MUTEX_PAIRS: Tuple[Tuple[str, str, str], ...] = (
    # ("plugin_a", "plugin_b", "同开时推理前提可能冲突，建议提高 backfire_risk 权重"),
)


def _l0_atomic_manifest_rows() -> List[Dict[str, Any]]:
    """Admin「L0 原子层」三卡：与 `DEFAULT_PHYSICS_SETTINGS` 中 L0_* 键及 DB l0_* 表对齐。"""
    perf_empty: Dict[str, Any] = {
        "last_latency_ms": None,
        "p50_ms": None,
        "p95_ms": None,
        "error_rate": 0.0,
        "last_run_at": None,
    }

    def one(pid: str, title: str, key: str, sid: str, desc: str, use_case: str) -> Dict[str, Any]:
        return {
            "id": pid,
            "layer": "L0",
            "category": "L0/Atom",
            "status": "HEALTHY",
            "dependencies": [],
            "metadata": {
                "label": title,
                "display_name": title,
                "doc_path": "/docs/causal-pulse/l0_atom_layer.md",
                "priority": 0.99,
                "hook": "on_physics_complete",
                "description_tags": ["L0", "Atom", "l0_domain"],
                "use_case": use_case,
                "detailed_description": desc,
                "physical_impact": "影响 `build_energy_fields` / `get_root_resonance` 与 DB `l0_*` 表。",
                "skills": [
                    {
                        "id": sid,
                        "name": title,
                        "description": desc,
                        "impact_factor": "L0",
                        "physics_setting_key": key,
                        "assertion_template": "",
                        "physics_weight": 0.0,
                        "description_tags": ["l0_atom", "aux_slider"],
                    }
                ],
            },
            "performance_snapshot": perf_empty,
        }

    return [
        one(
            "l0.hidden_schema",
            "L0 藏干分发",
            "L0_HIDDEN_ENERGY_SCALE",
            "l0_skill_hidden_scale",
            "整体缩放四柱与岁运通道中的藏干支能量（藏干比例由 DB `l0_branch_hidden_schema` 维护）。",
            "调节地支人元诸干对标能量的总标度。",
        ),
        one(
            "l0.root_resonance",
            "L0 通根强度",
            "L0_ROOT_BOOST_FACTOR",
            "l0_skill_root_boost",
            "通根共振总乘子：叠在 `get_root_resonance` 上，调节天干从地支藏干获得的反哺。",
            "调节干透根伏的 Abs 反哺强度。",
        ),
        one(
            "l0.pillar_time",
            "L0 时柱加权",
            "L0_YM_DH_WEIGHT_RATIO",
            "l0_skill_ym_dh",
            "年月相对日时柱位权重比：>1 增强年、月柱 position_weight，<1 则偏强日、时，再归一化。",
            "调节四柱宫位势能主轴与时间纵深。",
        ),
    ]


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, PluginSpec] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            PluginSpec(
                plugin_id="base.chronos",
                category="Base/Chronos",
                layer_id="L0",
                label="时空权重（司令 / 余气）",
                dependencies=[],
                priority=0.95,
                audit_source="plugins/chronos/readme.md",
                hook="on_physics_complete",
                runner=_chronos_registry_runner,
            )
        )
        self.register(
            PluginSpec(
                plugin_id="sys.core.physics",
                category="Base/L0Engine",
                layer_id="L0",
                label="L0 物理引擎（原生 · 合成场 / 流水线 / physics_trace）",
                dependencies=["base.physics_l1"],
                priority=0.996,
                audit_source="docs/causal-pulse/sys_core_physics.md",
                hook="on_physics_complete",
                runner=_run_sys_core_physics_bundle_lazy,
            )
        )
        self.register(
            PluginSpec(
                plugin_id="classical.blind_school.v1",
                category="Functional/Classical",
                layer_id="L2",
                label="盲派核心做功引擎",
                dependencies=["base.physics_l1", "base.chronos"],
                priority=0.8,
                audit_source="knowledge_base/BLIND_SCHOOL_ENCYCLOPEDIA.md",
                hook="on_physics_complete",
                runner=lambda **ctx: run_blind_school_plugin(
                    physics_tensor=ctx.get("physics_tensor") or {},
                    metadata=ctx.get("metadata") or {},
                    feature_flags=ctx.get("blind_school_features"),
                ),
            )
        )
        self.register(
            PluginSpec(
                plugin_id="modern.wealth_risk.v1",
                category="Functional/Modern",
                layer_id="L4",
                label="现代财富风险画像",
                dependencies=["base.physics_l1", "classical.blind_school.v1"],
                priority=0.55,
                audit_source="plugins/modern_wealth_risk/readme.md",
                hook="on_verdict_ready",
                runner=lambda **ctx: run_modern_wealth_risk_plugin(
                    work_vector=ctx.get("work_vector") or {},
                    structure_final_decision=ctx.get("structure_final_decision") or {},
                    metadata=ctx.get("metadata") or {},
                ),
            )
        )
        self.register(
            PluginSpec(
                plugin_id="classical.wangshuai.v1",
                category="Functional/Classical",
                layer_id="L1",
                label="旺衰平衡解析引擎",
                dependencies=["base.physics_l1", "base.chronos"],
                priority=0.6,
                audit_source="plugins/wangshuai/readme.md",
                hook="on_physics_complete",
                runner=lambda **ctx: run_wangshuai_plugin(
                    physics_tensor=ctx.get("physics_tensor") or {},
                    metadata=ctx.get("metadata") or {},
                ),
            )
        )

    def register(self, spec: PluginSpec) -> None:
        self._plugins[spec.plugin_id] = spec

    def list_specs(self) -> List[Dict[str, Any]]:
        return [
            {
                "plugin_id": s.plugin_id,
                "label": s.label,
                "category": s.category,
                "layer_id": s.layer_id,
                "layer": s.layer_id,
                "dependencies": s.dependencies,
                "priority": s.priority,
                "audit_source": s.audit_source,
                "hook": s.hook,
            }
            for s in sorted(self._plugins.values(), key=lambda x: x.priority, reverse=True)
        ]

    def _record_stat(self, plugin_id: str, latency_ms: float, ok: bool) -> None:
        stat = _PLUGIN_STATS.get(plugin_id) or {
            "samples": [],
            "ok_count": 0,
            "err_count": 0,
            "last_latency_ms": None,
            "last_run_at": None,
        }
        samples = list(stat.get("samples") or [])
        samples.append(float(latency_ms))
        if len(samples) > 120:
            samples = samples[-120:]
        stat["samples"] = samples
        if ok:
            stat["ok_count"] = int(stat.get("ok_count", 0)) + 1
        else:
            stat["err_count"] = int(stat.get("err_count", 0)) + 1
        stat["last_latency_ms"] = round(float(latency_ms), 3)
        stat["last_run_at"] = time.time()
        _PLUGIN_STATS[plugin_id] = stat

    @staticmethod
    def _quantile(samples: List[float], q: float) -> float:
        if not samples:
            return 0.0
        ordered = sorted(samples)
        idx = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * q))))
        return float(ordered[idx])

    @staticmethod
    def collect_mutex_warnings(enabled_ids: Set[str]) -> List[str]:
        """若启用集合同时命中某互斥对，返回人可读警告（当前默认无对，仅保留扩展点）。"""
        warnings: List[str] = []
        for a, b, msg in _PLUGIN_MUTEX_PAIRS:
            if a in enabled_ids and b in enabled_ids:
                warnings.append(f"{a} + {b}: {msg}")
        return warnings

    def get_manifest(self, enabled_plugins: List[str] | None = None, plugin_id: str | None = None) -> Dict[str, Any]:
        selected = set(enabled_plugins or [])
        specs = sorted(self._plugins.values(), key=lambda x: x.priority, reverse=True)
        active_ids = {s.plugin_id for s in specs if (not selected or s.plugin_id in selected)}

        plugins: List[Dict[str, Any]] = []
        dependency_links: List[Dict[str, str]] = []
        perf_rows: List[float] = []
        for spec in specs:
            deps_ok = all(dep.startswith("base.") or dep in active_ids for dep in spec.dependencies)
            enabled = (not selected) or (spec.plugin_id in selected)
            stat = _PLUGIN_STATS.get(spec.plugin_id) or {}
            samples = [float(x) for x in list(stat.get("samples") or []) if isinstance(x, (int, float))]
            p50 = round(self._quantile(samples, 0.5), 3) if samples else None
            p95 = round(self._quantile(samples, 0.95), 3) if samples else None
            last_latency = stat.get("last_latency_ms")
            if isinstance(last_latency, (int, float)):
                perf_rows.append(float(last_latency))
            ok_count = int(stat.get("ok_count", 0) or 0)
            err_count = int(stat.get("err_count", 0) or 0)
            total = max(1, ok_count + err_count)
            error_rate = round(err_count / total, 4)
            status = "HEALTHY" if enabled and deps_ok and error_rate < 0.2 else ("IDLE" if not enabled else "ERROR")
            doc_slug = spec.audit_source.replace(".md", "")
            meta: Dict[str, Any] = {
                "label": spec.label,
                "doc_path": f"/docs/{doc_slug}",
                "priority": spec.priority,
                "hook": spec.hook,
                "description_tags": [str(spec.layer_id), spec.category],
            }
            if spec.plugin_id == "classical.blind_school.v1":
                meta["skills"] = list_blind_skills()
            if spec.plugin_id == "base.chronos":
                meta["skills"] = list_chronos_skills()
            if spec.plugin_id == "classical.wangshuai.v1":
                meta["skills"] = list_wangshuai_skills()
            if spec.plugin_id == "modern.wealth_risk.v1":
                meta["skills"] = list_modern_wealth_skills()
            merge_plugin_manifest_into_metadata(meta, spec.plugin_id)
            plugins.append(
                {
                    "id": spec.plugin_id,
                    "layer": spec.layer_id,
                    "category": spec.category,
                    "status": status,
                    "dependencies": list(spec.dependencies),
                    "metadata": meta,
                    "performance_snapshot": {
                        "last_latency_ms": round(float(last_latency), 3) if isinstance(last_latency, (int, float)) else None,
                        "p50_ms": p50,
                        "p95_ms": p95,
                        "error_rate": error_rate,
                        "last_run_at": stat.get("last_run_at"),
                    },
                }
            )
            for dep in spec.dependencies:
                dependency_links.append({"from": dep, "to": spec.plugin_id})

        plugins = _l0_atomic_manifest_rows() + plugins

        tension = 0.0
        if perf_rows:
            peak = max(perf_rows)
            tension = min(1.0, peak / 400.0)
        mutex_warnings = self.collect_mutex_warnings(active_ids)

        l1_physics_manifest = load_l1_physics_manifest()
        l1_eff_settings = resolve_physics_settings(None)
        op_to_skill = load_base_physics_skill_manifest().get("operator_to_skill")
        if not isinstance(op_to_skill, dict):
            op_to_skill = {}
        skill_rows = [s for s in list_base_physics_skills() if isinstance(s, dict) and s.get("id")]
        skill_index = {str(s["id"]): s for s in skill_rows}

        overlays = l1_physics_manifest.get("registry_overlays") or {}
        for p in plugins:
            oid = str(p.get("id") or "")
            if oid and oid in overlays and isinstance(p.get("metadata"), dict):
                ov = overlays[oid]
                if isinstance(ov, dict) and ov.get("markdown"):
                    p["metadata"]["blueprint_markdown"] = str(ov["markdown"])

        for op in l1_physics_manifest.get("operators", []) or []:
            oid = str(op.get("id") or "")
            if not oid:
                continue
            op_id_str = str(op.get("op_id") or "")
            extra_sids = op.get("skill_ids")
            if isinstance(extra_sids, list) and extra_sids:
                op_skills = [skill_index[str(sid)] for sid in extra_sids if str(sid) in skill_index]
            else:
                sid = op_to_skill.get(op_id_str)
                op_skills = [skill_index[sid]] if sid and sid in skill_index else []
            op_card = plugin_manifest_for_operator_card(oid)
            base_desc_tags = ["L1", "Atomic", op_id_str or oid]
            op_manifest_tags = op.get("description_tags")
            if isinstance(op_manifest_tags, list):
                merged_tags = list(base_desc_tags)
                for t in op_manifest_tags:
                    ts = str(t).strip()
                    if ts and ts not in merged_tags:
                        merged_tags.append(ts)
                desc_tags_out = merged_tags
            else:
                desc_tags_out = base_desc_tags
            entry_meta: Dict[str, Any] = {
                "label": str(op.get("title") or oid),
                "doc_path": "/docs/causal-pulse/v0.13_interdimensional_protocol.md",
                "priority": float(op.get("manifest_priority") or 0.42),
                "hook": "on_physics_complete",
                "l1_physics_operator": True,
                "op_id": op.get("op_id"),
                "blueprint_markdown": str(op.get("blueprint_markdown") or ""),
                "description_tags": desc_tags_out,
                "skills": op_skills,
            }
            jp = op.get("judgment_protocol")
            base_jp: List[str] = []
            if isinstance(jp, list):
                base_jp = [str(x).strip() for x in jp if str(x).strip()]
            elif isinstance(jp, str) and jp.strip():
                base_jp = [jp.strip()]
            dyn_jp: List[str] = []
            if oid.startswith("base.physics.op_branch_"):
                dyn_jp = judgment_protocol_dynamic_lines_for_sub_branch_operator(oid, l1_eff_settings)
            elif oid.startswith("base.physics.op_stem_fusion"):
                dyn_jp = judgment_protocol_dynamic_lines_for_stem_fusion(oid, l1_eff_settings)
            if base_jp or dyn_jp:
                entry_meta["judgment_protocol"] = base_jp + dyn_jp
            for _k in ("display_name", "use_case", "detailed_description", "physical_impact", "governance_notes"):
                if _k in op_card:
                    entry_meta[_k] = op_card[_k]
            if "display_name" not in entry_meta:
                entry_meta["display_name"] = str(op.get("title") or oid)
            plugins.append(
                {
                    "id": oid,
                    "layer": "L1",
                    "category": str(op.get("category") or "Base/Atomic"),
                    "status": "HEALTHY",
                    "dependencies": [],
                    "metadata": entry_meta,
                    "performance_snapshot": {
                        "last_latency_ms": None,
                        "p50_ms": None,
                        "p95_ms": None,
                        "error_rate": 0.0,
                        "last_run_at": None,
                    },
                }
            )

        result: Dict[str, Any] = {
            "plugins": plugins,
            "dependency_links": dependency_links,
            "performance_snapshot": {
                "plugin_count": len(plugins),
                "max_last_latency_ms": round(max(perf_rows), 3) if perf_rows else None,
            },
            "global_conflict_tension": round(float(tension), 4),
            "plugin_mutex_warnings": mutex_warnings,
            "l1_physics_manifest": l1_physics_manifest,
            "base_physics_skills": skill_rows,
            "default_physics_settings": {k: float(v) for k, v in l1_eff_settings.items()},
            "refreshed_at": time.time(),
        }
        if plugin_id:
            pid = str(plugin_id).strip()
            for p in result["plugins"]:
                if str(p.get("id")) == pid:
                    meta = p.get("metadata") if isinstance(p.get("metadata"), dict) else {}
                    skills = meta.get("skills") if isinstance(meta.get("skills"), list) else []
                    return {
                        "plugin": p,
                        "blueprint_markdown": str(meta.get("blueprint_markdown") or ""),
                        "skills": list(skills),
                        "base_physics_skills": list(result.get("base_physics_skills") or []),
                        "default_physics_settings": dict(result.get("default_physics_settings") or {}),
                        "refreshed_at": result["refreshed_at"],
                    }
            return {
                "plugin": None,
                "blueprint_markdown": "",
                "skills": [],
                "base_physics_skills": list(result.get("base_physics_skills") or []),
                "default_physics_settings": dict(result.get("default_physics_settings") or {}),
                "error": "not_found",
                "refreshed_at": result["refreshed_at"],
            }
        return result

    def run_hook(
        self,
        *,
        hook: HookName,
        enabled_plugins: List[str] | None,
        context: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        selected = set(enabled_plugins or [])
        outputs: Dict[str, Dict[str, Any]] = {}
        for spec in sorted(self._plugins.values(), key=lambda x: x.priority, reverse=True):
            if spec.hook != hook:
                continue
            if (
                selected
                and spec.plugin_id not in selected
                and not (
                    hook == "on_physics_complete"
                    and (spec.plugin_id in _ALWAYS_ON_PHYSICS_COMPLETE or spec.layer_id == "L0")
                )
            ):
                continue
            started = time.perf_counter()
            ok = True
            try:
                payload = spec.runner(**context)
            except Exception as exc:
                ok = False
                payload = {"verdict": "", "evidence": [f"plugin_error={exc}"], "confidence_score": 0.0, "error": str(exc)}
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            self._record_stat(spec.plugin_id, elapsed_ms, ok=ok)
            outputs[spec.plugin_id] = {
                "verdict": str(payload.get("verdict") or ""),
                "evidence": list(payload.get("evidence") or []),
                "confidence_score": float(payload.get("confidence_score", 0.7) or 0.7),
                "audit_source": spec.audit_source,
                "payload": payload,
                "latency_ms": round(float(elapsed_ms), 3),
                "ok": ok,
            }
        return outputs

    def get_conflict_hotspots(self, top_n: int = 24) -> Dict[str, Any]:
        """聚合 Decision Inbox 门控遥测：哪些插件/开关签名最常伴随 eligible / gated。"""
        from app.core.plugins.conflict_telemetry import get_conflict_hotspot_rows

        return {
            "hotspots": get_conflict_hotspot_rows(top_n=max(1, min(200, int(top_n)))),
            "refreshed_at": time.time(),
        }

