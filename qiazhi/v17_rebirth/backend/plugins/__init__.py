"""V17 插件包：契约 `V17PluginSpec`；聚合 API 从 `v17_wrappers` 延迟加载。"""

from __future__ import annotations

from typing import Any, List

from v17_rebirth.backend.plugins.spec import V17Decision, V17Fact, V17PluginSpec

__all__ = [
    "V17Decision",
    "V17Fact",
    "V17PluginSpec",
    "collect_plugin_facts",
    "collect_spec_facts",
    "collect_spec_facts_and_record",
    "collect_pending_decisions_from_specs",
    "iter_v17_plugin_specs",
]


def __getattr__(name: str) -> Any:
    if name in {
        "collect_plugin_facts",
        "collect_spec_facts",
        "collect_spec_facts_and_record",
        "collect_pending_decisions_from_specs",
        "iter_v17_plugin_specs",
    }:
        from v17_rebirth.backend.plugins import v17_wrappers as w

        return getattr(w, name)
    raise AttributeError(name)


def __dir__() -> List[str]:
    return sorted(set(__all__))
