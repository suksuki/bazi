"""Plugin registry and lifecycle hooks for Bazi OS."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Dict, List, Literal

from app.plugins.blind_school.core import run_blind_school_plugin
from app.plugins.modern_wealth_risk.core import run_modern_wealth_risk_plugin
from app.plugins.wangshuai.core import run_wangshuai_plugin

HookName = Literal["on_physics_complete", "on_verdict_ready"]


@dataclass(frozen=True)
class PluginSpec:
    plugin_id: str
    category: str
    layer_id: Literal["L1", "L2", "L3", "L4"]
    label: str
    dependencies: List[str]
    priority: float
    audit_source: str
    hook: HookName
    runner: Callable[..., Dict[str, Any]]


_PLUGIN_STATS: Dict[str, Dict[str, Any]] = {}


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, PluginSpec] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
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
                ),
            )
        )
        self.register(
            PluginSpec(
                plugin_id="modern.wealth_risk.v1",
                category="Functional/Modern",
                layer_id="L3",
                label="现代财富风险画像",
                dependencies=["base.physics_l1", "classical.blind_school.v1"],
                priority=0.55,
                audit_source="knowledge_base/BLIND_SCHOOL_ENCYCLOPEDIA.md",
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
                layer_id="L2",
                label="旺衰平衡解析引擎",
                dependencies=["base.physics_l1", "base.chronos"],
                priority=0.6,
                audit_source="engine/LOGIC_CONSTITUTION.md",
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

    def get_manifest(self, enabled_plugins: List[str] | None = None) -> Dict[str, Any]:
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
            plugins.append(
                {
                    "id": spec.plugin_id,
                    "layer": spec.layer_id,
                    "category": spec.category,
                    "status": status,
                    "dependencies": list(spec.dependencies),
                    "metadata": {
                        "label": spec.label,
                        "doc_path": f"/docs/{doc_slug}",
                        "priority": spec.priority,
                        "hook": spec.hook,
                    },
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

        tension = 0.0
        if perf_rows:
            peak = max(perf_rows)
            tension = min(1.0, peak / 400.0)
        return {
            "plugins": plugins,
            "dependency_links": dependency_links,
            "performance_snapshot": {
                "plugin_count": len(plugins),
                "max_last_latency_ms": round(max(perf_rows), 3) if perf_rows else None,
            },
            "global_conflict_tension": round(float(tension), 4),
            "refreshed_at": time.time(),
        }

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
            if selected and spec.plugin_id not in selected:
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

