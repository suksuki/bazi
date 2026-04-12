"""physics_tensor 字段兼容：旧 deity_energy_axes / 新 abs_nodes 与三合 cluster 有效 Abs。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def sanhe_clusters_from_physics_tensor(physics_tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
    """仅从 `plugin_outputs.sys.core.physics.payload` 读取三合簇（禁止 tensor 顶栏回退）。"""
    po = physics_tensor.get("plugin_outputs")
    if not isinstance(po, dict):
        return []
    row = po.get("sys.core.physics")
    if not isinstance(row, dict):
        return []
    pl = row.get("payload")
    if not isinstance(pl, dict):
        return []
    raw = pl.get("sanhe_clusters")
    if isinstance(raw, list) and raw:
        return [c for c in raw if isinstance(c, dict)]
    comp = pl.get("composite_field_impact")
    if isinstance(comp, dict):
        raw2 = comp.get("sanhe_clusters")
        if isinstance(raw2, list):
            return [c for c in raw2 if isinstance(c, dict)]
    return []


def _sanhe_detail_from_cluster(cluster: Dict[str, Any]) -> str:
    brs = [str(x) for x in (cluster.get("branches") or []) if x is not None]
    if not brs:
        return "三合簇"
    ev = str(cluster.get("energy_vault_status") or "").strip()
    core = f"三合局·支池[{'、'.join(brs)}]"
    return f"{core}·{ev}".strip("·") if ev else core


def collect_conflict_matrix_points_for_llm(
    metadata: Any,
    physics_tensor: Optional[Dict[str, Any]],
    *,
    limit: int = 48,
) -> List[Dict[str, Any]]:
    """供物理审计/终判提示词使用：优先 metadata.conflict_matrix；若为空则从 physics_tensor 插件载荷回补三合等，避免与 UI 脱节。"""
    out: List[Dict[str, Any]] = []
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}

    raw_pts: List[Any] = []
    cm = getattr(metadata, "conflict_matrix", None) if metadata is not None else None
    if cm is not None and hasattr(cm, "points"):
        raw_pts = list(cm.points or [])
    elif isinstance(metadata, dict):
        raw_pts = list(((metadata.get("conflict_matrix") or {}).get("points")) or [])

    for p in raw_pts:
        if hasattr(p, "model_dump"):
            dumped = p.model_dump(exclude_none=True)
            if isinstance(dumped, dict):
                out.append(dumped)
        elif isinstance(p, dict):
            out.append(dict(p))

    if out:
        return out[:limit]

    for i, cl in enumerate(sanhe_clusters_from_physics_tensor(pt)):
        if not isinstance(cl, dict):
            continue
        out.append(
            {
                "id": f"sanhe_physics_sync_{i}",
                "kind": "sanhe",
                "positions": [],
                "detail": _sanhe_detail_from_cluster(cl),
                "source": "physics_tensor_sync",
            }
        )
    return out[:limit]


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
    由 deity_energy_axes 与 `plugin_outputs.sys.core.physics` 中的三合簇生成 abs_nodes 映射。
    调用方负责在写入前检查 physics_tensor 是否已有 abs_nodes。
    """
    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict) or not axes:
        raise ValueError("physics_tensor.deity_energy_axes 缺失或为空，无法镜像 abs_nodes")
    clusters = sanhe_clusters_from_physics_tensor(physics_tensor)
    composite_for_deity: Dict[str, Any] | None = {"sanhe_clusters": clusters} if clusters else None
    mirrored: Dict[str, float] = {}
    for k, v in axes.items():
        raw_abs = float(((v or {}).get("absolute_energy", 0.0) if isinstance(v, dict) else 0.0) or 0.0)
        effective = cluster_effective_abs_for_deity(
            composite=composite_for_deity,
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
