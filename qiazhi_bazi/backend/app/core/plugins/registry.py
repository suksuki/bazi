"""Plugin registry and lifecycle hooks for Bazi OS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal

from app.plugins.blind_school.core import run_blind_school_plugin
from app.plugins.modern_wealth_risk.core import run_modern_wealth_risk_plugin
from app.plugins.wangshuai.core import run_wangshuai_plugin

HookName = Literal["on_physics_complete", "on_verdict_ready"]


@dataclass(frozen=True)
class PluginSpec:
    plugin_id: str
    category: str
    dependencies: List[str]
    priority: float
    audit_source: str
    hook: HookName
    runner: Callable[..., Dict[str, Any]]


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, PluginSpec] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            PluginSpec(
                plugin_id="classical.blind_school.v1",
                category="Functional/Classical",
                dependencies=["base.physics_l1", "base.chronos"],
                priority=0.8,
                audit_source="BLIND_SCHOOL_ENCYCLOPEDIA.md",
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
                dependencies=["base.physics_l1", "classical.blind_school.v1"],
                priority=0.55,
                audit_source="BLIND_SCHOOL_ENCYCLOPEDIA.md",
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
                dependencies=["base.physics_l1", "base.chronos"],
                priority=0.6,
                audit_source="LOGIC_CONSTITUTION.md",
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
                "category": s.category,
                "dependencies": s.dependencies,
                "priority": s.priority,
                "audit_source": s.audit_source,
                "hook": s.hook,
            }
            for s in sorted(self._plugins.values(), key=lambda x: x.priority, reverse=True)
        ]

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
            payload = spec.runner(**context)
            outputs[spec.plugin_id] = {
                "verdict": str(payload.get("verdict") or ""),
                "evidence": list(payload.get("evidence") or []),
                "confidence_score": float(payload.get("confidence_score", 0.7) or 0.7),
                "audit_source": spec.audit_source,
                "payload": payload,
            }
        return outputs

