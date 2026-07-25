from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from experience.contracts import CompiledTopic, SceneNode, TopicPackage


class TopicCompileError(ValueError):
    pass


class FrozenDict(dict[str, Any]):
    """A JSON-serializable mapping that rejects runtime mutation."""

    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("compiled_topic_mapping_is_immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _canonical_value(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def load_topic_package(path: str | Path) -> TopicPackage:
    return TopicPackage.model_validate_json(Path(path).read_text(encoding="utf-8"))


def compile_topic(package: TopicPackage) -> CompiledTopic:
    nodes = _unique_by_id(package.scene_nodes, "node_id", "duplicate_scene_node")
    cues = _unique_by_id(package.cue_templates, "template_id", "duplicate_cue_template")
    assets = _unique_by_id(package.asset_manifest.assets, "asset_id", "duplicate_asset")

    if package.entry_node not in nodes:
        raise TopicCompileError(f"missing_entry_node:{package.entry_node}")
    for mode, node_id in package.fallback_entry_nodes.items():
        if node_id not in nodes:
            raise TopicCompileError(f"missing_fallback_entry:{mode}:{node_id}")

    _validate_node_references(nodes=nodes, cues=cues)
    _validate_cue_references(cues=cues, assets=assets)
    _validate_graph(nodes=nodes, entry_nodes={package.entry_node, *package.fallback_entry_nodes.values()})

    source_hash = canonical_hash(package)
    content = {
        "topic": package.topic.model_dump(mode="json"),
        "entry_node": package.entry_node,
        "fallback_entry_nodes": package.fallback_entry_nodes,
        "scene_nodes": {key: value.model_dump(mode="json") for key, value in nodes.items()},
        "cue_templates": {key: value.model_dump(mode="json") for key, value in cues.items()},
        "assets": {key: value.model_dump(mode="json") for key, value in assets.items()},
        "policies": package.policies.model_dump(mode="json"),
        "source_hash": source_hash,
    }
    compiled = CompiledTopic(
        topic=package.topic,
        entry_node=package.entry_node,
        fallback_entry_nodes=package.fallback_entry_nodes,
        scene_nodes=nodes,
        cue_templates=cues,
        assets=assets,
        policies=package.policies,
        source_hash=source_hash,
        content_hash=canonical_hash(content),
        compiled_at=datetime.now(timezone.utc),
    )
    object.__setattr__(compiled, "scene_nodes", FrozenDict(compiled.scene_nodes))
    object.__setattr__(compiled, "cue_templates", FrozenDict(compiled.cue_templates))
    object.__setattr__(compiled, "assets", FrozenDict(compiled.assets))
    object.__setattr__(compiled, "fallback_entry_nodes", FrozenDict(compiled.fallback_entry_nodes))
    return compiled


def _unique_by_id(rows: list[Any], field: str, error: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows:
        key = str(getattr(row, field))
        if key in result:
            raise TopicCompileError(f"{error}:{key}")
        result[key] = row
    return result


def _validate_node_references(*, nodes: dict[str, SceneNode], cues: dict[str, Any]) -> None:
    for node in nodes.values():
        for cue_id in node.cue_template_ids:
            if cue_id not in cues:
                raise TopicCompileError(f"missing_cue:{node.node_id}:{cue_id}")
            if cues[cue_id].visibility != node.visibility:
                raise TopicCompileError(f"cue_visibility_mismatch:{node.node_id}:{cue_id}")
        for transition in node.transitions:
            if transition.target not in nodes:
                raise TopicCompileError(f"missing_transition_target:{node.node_id}:{transition.target}")
        if node.fallback_node and node.fallback_node not in nodes:
            raise TopicCompileError(f"missing_fallback_node:{node.node_id}:{node.fallback_node}")
        if node.visibility == "public" and any(binding.startswith("envelope.") for binding in node.data_bindings):
            raise TopicCompileError(f"public_node_reads_envelope:{node.node_id}")
        if node.visibility == "participant_private":
            if not node.rejoin_node or node.rejoin_node not in nodes:
                raise TopicCompileError(f"private_node_missing_rejoin:{node.node_id}")
            if nodes[node.rejoin_node].visibility != "public":
                raise TopicCompileError(f"private_node_rejoins_private:{node.node_id}")


def _validate_cue_references(*, cues: dict[str, Any], assets: dict[str, Any]) -> None:
    for cue in cues.values():
        if cue.dialogue_template and not cue.subtitle_template:
            raise TopicCompileError(f"dialogue_without_subtitle:{cue.template_id}")
        if cue.fallback_template_id and cue.fallback_template_id not in cues:
            raise TopicCompileError(f"missing_fallback_cue:{cue.template_id}:{cue.fallback_template_id}")
        referenced = [cue.actor.motion_asset, cue.voice.audio_asset]
        referenced.extend(command.asset_ref for command in cue.stage)
        for asset_id in (item for item in referenced if item):
            if asset_id not in assets:
                raise TopicCompileError(f"missing_asset:{cue.template_id}:{asset_id}")


def _validate_graph(*, nodes: dict[str, SceneNode], entry_nodes: set[str]) -> None:
    reachable: set[str] = set()
    stack = list(entry_nodes)
    while stack:
        node_id = stack.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        node = nodes[node_id]
        stack.extend(item.target for item in node.transitions)
        if node.fallback_node:
            stack.append(node.fallback_node)
        if node.rejoin_node:
            stack.append(node.rejoin_node)
    unreachable = sorted(set(nodes) - reachable)
    if unreachable:
        raise TopicCompileError(f"unreachable_nodes:{','.join(unreachable)}")

    reverse: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    terminals: set[str] = set()
    for node in nodes.values():
        targets = {item.target for item in node.transitions}
        if node.fallback_node:
            targets.add(node.fallback_node)
        if node.rejoin_node:
            targets.add(node.rejoin_node)
        if not targets:
            terminals.add(node.node_id)
        for target in targets:
            reverse[target].add(node.node_id)
    can_finish = set(terminals)
    stack = list(terminals)
    while stack:
        target = stack.pop()
        for source in reverse[target]:
            if source not in can_finish:
                can_finish.add(source)
                stack.append(source)
    trapped = sorted(reachable - can_finish)
    if trapped:
        raise TopicCompileError(f"exitless_cycle_or_path:{','.join(trapped)}")
