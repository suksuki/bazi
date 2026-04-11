"""physics_tensor 字段兼容：旧 deity_energy_axes / 新 abs_nodes 与三合 cluster 有效 Abs。"""
from __future__ import annotations

from typing import Any, Dict


def cluster_effective_abs_for_deity(
    *,
    composite: Dict[str, Any] | None,
    deity_name: str,
    raw_abs: float,
) -> float | None:
    """若该十神落在 AGGREGATED 合局内，优先取 cluster 上的 effective 值；否则返回 None。"""
    if not isinstance(composite, dict):
        return None
    sanhe_clusters = composite.get("sanhe_clusters")
    if not isinstance(sanhe_clusters, list):
        return None
    for cluster in sanhe_clusters:
        if not isinstance(cluster, dict):
            continue
        for map_key in ("effective_abs_nodes", "abs_nodes", "node_effective_abs"):
            m = cluster.get(map_key)
            if isinstance(m, dict) and isinstance(m.get(deity_name), (int, float)):
                return float(m.get(deity_name))
        nodes = cluster.get("nodes")
        if isinstance(nodes, list):
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                node_name = str(node.get("name") or node.get("node") or node.get("deity") or "")
                if node_name != deity_name:
                    continue
                for val_key in ("effective_abs", "effective_energy", "effective_field_abs"):
                    if isinstance(node.get(val_key), (int, float)):
                        return float(node.get(val_key))
                if isinstance(node.get("raw_energy"), (int, float)):
                    unlocked = bool(cluster.get("cluster_phi_unlock", False))
                    return float(node.get("raw_energy")) if unlocked else 0.0
        if bool(cluster.get("cluster_phi_unlock", False)) is False and (
            isinstance(cluster.get("energy_vault_status"), str)
            and str(cluster.get("energy_vault_status")).upper() == "AGGREGATED"
        ):
            if isinstance(cluster.get("deities"), list) and deity_name in [str(x) for x in cluster.get("deities")]:
                return max(0.0, raw_abs * 0.0)
    return None


def mirror_abs_nodes_from_deity_axes(physics_tensor: Dict[str, Any]) -> Dict[str, float]:
    """
    由 deity_energy_axes 与 composite_field_impact 生成 abs_nodes 映射。
    调用方负责在写入前检查 physics_tensor 是否已有 abs_nodes。
    """
    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict) or not axes:
        raise ValueError("physics_tensor.deity_energy_axes 缺失或为空，无法镜像 abs_nodes")
    composite = physics_tensor.get("composite_field_impact")
    mirrored: Dict[str, float] = {}
    for k, v in axes.items():
        raw_abs = float(((v or {}).get("absolute_energy", 0.0) if isinstance(v, dict) else 0.0) or 0.0)
        effective = cluster_effective_abs_for_deity(
            composite=composite if isinstance(composite, dict) else None,
            deity_name=str(k),
            raw_abs=raw_abs,
        )
        mirrored[str(k)] = float(effective if effective is not None else raw_abs)
    return mirrored


def ensure_abs_nodes_on_physics_tensor(physics_tensor: Dict[str, Any]) -> None:
    """原地补全 abs_nodes；已有则跳过。"""
    if "abs_nodes" in physics_tensor and isinstance(physics_tensor.get("abs_nodes"), dict):
        return
    physics_tensor["abs_nodes"] = mirror_abs_nodes_from_deity_axes(physics_tensor)
