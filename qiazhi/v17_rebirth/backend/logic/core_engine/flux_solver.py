from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, ten_god_from_stems
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import SixPillarGraph
from v17_rebirth.backend.logic.core_engine.work_path_engine import WorkPath


_GOD_GROUP: Dict[str, str] = {
    "比肩": "peer",
    "劫财": "peer",
    "食神": "output",
    "伤官": "output",
    "正财": "wealth",
    "偏财": "wealth",
    "正官": "officer",
    "七杀": "officer",
    "正印": "seal",
    "偏印": "seal",
}

_GENERATE_CHAIN: Dict[str, str] = {
    "peer": "output",
    "output": "wealth",
    "wealth": "officer",
    "officer": "seal",
    "seal": "peer",
}

_CONTROL_CHAIN: Dict[str, str] = {
    "peer": "wealth",
    "output": "officer",
    "wealth": "seal",
    "officer": "peer",
    "seal": "output",
}


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _clean_gods(values: Any) -> List[str]:
    if values is None:
        return []
    if isinstance(values, str):
        value = values.strip()
        return [value] if value else []
    if not isinstance(values, list):
        return []
    out: List[str] = []
    seen: set[str] = set()
    for item in values:
        god = str(item or "").strip()
        if not god or god in seen:
            continue
        seen.add(god)
        out.append(god)
    return out


def _path_sign(path: WorkPath) -> int:
    role = str(path.path_role or "").strip().lower()
    net = _safe_float(path.net_effect, 0.0)
    if role in {"restrain", "intercept"}:
        return -1
    if role in {"promote", "bridge"}:
        return 1
    if net > 0.0:
        return 1
    if net < 0.0:
        return -1
    return 1


def _path_efficiency(path: WorkPath) -> float:
    activation = _safe_float(path.activation, 0.0)
    transmission = _safe_float(path.transmission, 0.0)
    stability = _safe_float(path.stability, 0.0)
    loss = _safe_float(path.loss, 0.0)
    magnitude = abs(_safe_float(path.net_effect, 0.0))
    raw = (
        magnitude * 0.34
        + activation * 0.18
        + transmission * 0.30
        + stability * 0.24
    )
    raw *= 1.0 - min(0.62, max(0.0, loss) * 0.58)
    return _clamp(raw, 0.05, 0.95)


def _source_gods_from_path(path: WorkPath) -> List[str]:
    evidence = path.evidence if isinstance(path.evidence, dict) else {}
    target = str(path.target_god or "").strip()
    candidates = (
        _clean_gods(evidence.get("counterpart_gods"))
        or _clean_gods(evidence.get("actor_gods"))
        or _clean_gods(evidence.get("receiver_gods"))
        or _clean_gods(evidence.get("targets"))
    )
    out: List[str] = []
    for god in candidates:
        if god and god != target and god not in out:
            out.append(god)
    if out:
        return out
    return [target] if target else []


def _collect_all_gods(
    *,
    paths: Sequence[WorkPath],
    deity_scores: Dict[str, float],
    effect_scores: Dict[str, Dict[str, float]],
) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for god in deity_scores.keys():
        name = str(god or "").strip()
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    for god in effect_scores.keys():
        name = str(god or "").strip()
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    for path in paths:
        target = str(path.target_god or "").strip()
        if target and target not in seen:
            seen.add(target)
            out.append(target)
        for source in _source_gods_from_path(path):
            if source and source not in seen:
                seen.add(source)
                out.append(source)
    return out


def _day_master_from_graph(graph: SixPillarGraph | None) -> str:
    if graph is None:
        return ""
    for node in graph.nodes:
        if node.node_id == "day_stem":
            return str(node.symbol or "").strip()
    for node in graph.nodes:
        if node.pillar == "day" and node.kind == "stem":
            return str(node.symbol or "").strip()
    return ""


def _node_to_god_weights(graph: SixPillarGraph | None, day_master: str) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    if graph is None or not day_master:
        return out
    for node in graph.nodes:
        if node.kind == "stem":
            god = ten_god_from_stems(day_master, node.symbol)
            if god:
                out[node.node_id] = {god: 1.0}
            continue
        if node.kind != "branch":
            continue
        row: Dict[str, float] = {}
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(node.symbol, []):
            god = ten_god_from_stems(day_master, hidden_stem)
            row[god] = row.get(god, 0.0) + float(hidden_weight)
        total = sum(row.values()) or 1.0
        out[node.node_id] = {god: weight / total for god, weight in row.items() if weight > 0.0}
    return out


def _top_node_god(node_id: str, node_gods: Dict[str, Dict[str, float]]) -> str:
    row = node_gods.get(node_id) if isinstance(node_gods.get(node_id), dict) else {}
    if not row:
        return ""
    return max(row.items(), key=lambda item: float(item[1]))[0]


def _graph_edge_weights(graph: SixPillarGraph | None) -> Dict[Tuple[str, str], float]:
    out: Dict[Tuple[str, str], float] = {}
    if graph is None:
        return out
    for edge in graph.edges:
        out[(edge.source, edge.target)] = float(edge.weight)
    return out


def _clean_node_ids(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    seen: set[str] = set()
    for item in values:
        nid = str(item or "").strip()
        if not nid or nid in seen:
            continue
        seen.add(nid)
        out.append(nid)
    return out


def _node_ids_for_god(
    *,
    graph: SixPillarGraph,
    node_gods: Dict[str, Dict[str, float]],
    god: str,
    limit: int = 4,
) -> List[str]:
    target = str(god or "").strip()
    if not target:
        return []
    pos_by_node = {node.node_id: float(node.position_weight) for node in graph.nodes}
    scored: List[Tuple[str, float]] = []
    for node_id, row in node_gods.items():
        weight = float(row.get(target, 0.0) or 0.0)
        if weight <= 0.0:
            continue
        scored.append((node_id, weight * (0.72 + pos_by_node.get(node_id, 0.6) * 0.28)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [node_id for node_id, _ in scored[:limit]]


def _build_node_flux_edges(
    *,
    paths: Sequence[WorkPath],
    graph: SixPillarGraph | None,
    node_gods: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    if graph is None:
        return []
    edge_weights = _graph_edge_weights(graph)
    edge_bucket: Dict[Tuple[str, str], Dict[str, Any]] = {}
    valid_nodes = {node.node_id for node in graph.nodes}
    for path in paths:
        if str(path.path_type or "").strip().lower() == "static_basis":
            continue
        evidence = path.evidence if isinstance(path.evidence, dict) else {}
        actor_nodes = [node for node in _clean_node_ids(evidence.get("actor_nodes")) if node in valid_nodes]
        receiver_nodes = [node for node in _clean_node_ids(evidence.get("receiver_nodes")) if node in valid_nodes]
        member_nodes = [node for node in _clean_node_ids(evidence.get("member_nodes")) if node in valid_nodes]
        if not actor_nodes:
            source_gods = _source_gods_from_path(path)
            for source_god in source_gods:
                actor_nodes.extend(_node_ids_for_god(graph=graph, node_gods=node_gods, god=source_god, limit=3))
            actor_nodes = [node for node in actor_nodes if node in valid_nodes]
        actor_nodes = list(dict.fromkeys(actor_nodes))
        if not receiver_nodes:
            receiver_nodes.extend(_node_ids_for_god(graph=graph, node_gods=node_gods, god=str(path.target_god or ""), limit=4))
            receiver_nodes = [node for node in receiver_nodes if node in valid_nodes]
        receiver_nodes = list(dict.fromkeys(receiver_nodes))
        sources = actor_nodes or member_nodes
        targets = receiver_nodes or member_nodes
        if not sources or not targets:
            continue
        sign = _path_sign(path)
        base_eta = _path_efficiency(path)
        role = str(path.path_role or "").strip().lower() or "unknown"
        family = str(path.path_family or "").strip().lower() or "dynamic_work"
        kind = f"{family}:{role}"
        directional = _safe_float(evidence.get("directional_factor"), 1.0)
        directed_hint = _safe_float(evidence.get("directed_edge_weight"), 0.0)
        role_factor = 1.0
        if role == "bridge":
            role_factor = 1.07
        elif role in {"restrain", "intercept"}:
            role_factor = 0.98
        for source in sources:
            for target in targets:
                if source == target:
                    continue
                edge_w = _safe_float(edge_weights.get((source, target)), 0.0)
                if edge_w <= 0.0:
                    edge_w = directed_hint if directed_hint > 0.0 else 0.58
                eta = _clamp(
                    base_eta
                    * (0.64 + edge_w * 0.36)
                    * (0.88 + min(1.4, max(0.6, directional)) * 0.12)
                    * role_factor,
                    0.03,
                    0.98,
                )
                signed = float(sign) * eta
                _add_signed_edge(
                    edge_bucket,
                    source=source,
                    target=target,
                    signed_value=signed,
                    edge_kind=kind,
                    path_id=str(path.path_id or ""),
                )
    edges: List[Dict[str, Any]] = []
    for (source, target), row in edge_bucket.items():
        signed = _safe_float(row.get("signed"), 0.0)
        if abs(signed) < 0.02:
            continue
        sign = 1 if signed > 0.0 else -1
        eta = _clamp(abs(signed), 0.04, 0.96)
        kinds = row.get("kinds")
        kind_list = sorted(list(kinds)) if isinstance(kinds, set) else []
        path_ids = row.get("path_ids") if isinstance(row.get("path_ids"), list) else []
        edges.append(
            {
                "source": source,
                "target": target,
                "sign": sign,
                "eta": round(eta, 4),
                "signed": round(sign * eta, 4),
                "count": int(row.get("count") or 0),
                "kinds": kind_list[:4],
                "path_ids": path_ids[:5],
                "source_god": _top_node_god(source, node_gods),
                "target_god": _top_node_god(target, node_gods),
            }
        )
    return edges


def _seed_node_strengths(
    *,
    graph: SixPillarGraph | None,
    node_gods: Dict[str, Dict[str, float]],
    deity_scores: Dict[str, float],
) -> Dict[str, float]:
    if graph is None:
        return {}
    max_score = max([_safe_float(value, 0.0) for value in deity_scores.values()] or [1.0])
    out: Dict[str, float] = {}
    for node in graph.nodes:
        gw = node_gods.get(node.node_id) if isinstance(node_gods.get(node.node_id), dict) else {}
        if not gw:
            continue
        score = 0.0
        for god, weight in gw.items():
            score += max(0.0, _safe_float(deity_scores.get(god), 0.0)) * float(weight)
        norm = score / max(max_score, 1.0)
        strength = norm * (0.72 + float(node.position_weight) * 0.28)
        if strength >= 0.05:
            out[node.node_id] = round(strength, 4)
    return out


def _project_node_chains_to_god_chains(
    *,
    node_chains: Sequence[Dict[str, Any]],
    node_gods: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in node_chains:
        source_node = str(row.get("source") or "").strip()
        target_node = str(row.get("target") or "").strip()
        flux = _safe_float(row.get("flux"), 0.0)
        if not source_node or not target_node or abs(flux) <= 1e-9:
            continue
        src_map = node_gods.get(source_node) if isinstance(node_gods.get(source_node), dict) else {}
        tgt_map = node_gods.get(target_node) if isinstance(node_gods.get(target_node), dict) else {}
        if not tgt_map:
            continue
        if not src_map:
            src_map = {source_node: 1.0}
        for source_god, sw in src_map.items():
            for target_god, tw in tgt_map.items():
                part_flux = flux * float(sw) * float(tw)
                if abs(part_flux) <= 1e-9:
                    continue
                out.append(
                    {
                        "source": str(source_god or "").strip(),
                        "target": str(target_god or "").strip(),
                        "nodes": list(row.get("nodes") or []),
                        "node_source": source_node,
                        "node_target": target_node,
                        "depth": int(row.get("depth") or 0),
                        "seed": _safe_float(row.get("seed"), 0.0),
                        "eta_product": _safe_float(row.get("eta_product"), 0.0),
                        "sign": int(1 if part_flux >= 0.0 else -1),
                        "flux": round(part_flux, 4),
                        "trace": list(row.get("trace") or []),
                    }
                )
    out.sort(key=lambda item: abs(_safe_float(item.get("flux"), 0.0)), reverse=True)
    return out


def _merge_sink_summaries(
    *,
    base_summary: Dict[str, Dict[str, Any]],
    node_summary: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    gods = set(base_summary.keys()) | set(node_summary.keys())
    for god in gods:
        base = base_summary.get(god) if isinstance(base_summary.get(god), dict) else {}
        node = node_summary.get(god) if isinstance(node_summary.get(god), dict) else {}
        benefit = _safe_float(base.get("benefit"), 0.0) + _safe_float(node.get("benefit"), 0.0)
        harm = _safe_float(base.get("harm"), 0.0) + _safe_float(node.get("harm"), 0.0)
        net = _safe_float(base.get("net"), 0.0) + _safe_float(node.get("net"), 0.0)
        chain_count = int(base.get("chain_count") or 0) + int(node.get("chain_count") or 0)
        causes = []
        causes.extend(list(base.get("top_causes") or []))
        causes.extend(list(node.get("top_causes") or []))
        causes = sorted(causes, key=lambda row: abs(_safe_float(row.get("flux"), 0.0)), reverse=True)[:6]
        out[god] = {
            "benefit": round(benefit, 4),
            "harm": round(harm, 4),
            "net": round(net, 4),
            "chain_count": chain_count,
            "top_causes": causes[:5],
        }
    return out


def _add_signed_edge(
    edge_bucket: Dict[Tuple[str, str], Dict[str, Any]],
    *,
    source: str,
    target: str,
    signed_value: float,
    edge_kind: str,
    path_id: str = "",
) -> None:
    if not source or not target or source == target:
        return
    if abs(signed_value) <= 1e-9:
        return
    key = (source, target)
    entry = edge_bucket.setdefault(
        key,
        {"signed": 0.0, "abs_total": 0.0, "count": 0, "kinds": set(), "path_ids": []},
    )
    entry["signed"] = float(entry["signed"]) + float(signed_value)
    entry["abs_total"] = float(entry["abs_total"]) + abs(float(signed_value))
    entry["count"] = int(entry["count"]) + 1
    kinds = entry["kinds"]
    if isinstance(kinds, set):
        kinds.add(str(edge_kind or "").strip() or "unknown")
    path_ids = entry["path_ids"]
    if isinstance(path_ids, list):
        pid = str(path_id or "").strip()
        if pid and pid not in path_ids:
            path_ids.append(pid)


def _build_god_flux_edges(
    *,
    paths: Sequence[WorkPath],
    gods: Sequence[str],
) -> List[Dict[str, Any]]:
    edge_bucket: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for path in paths:
        target = str(path.target_god or "").strip()
        if not target:
            continue
        sign = _path_sign(path)
        eta = _path_efficiency(path)
        role = str(path.path_role or "").strip().lower() or "unknown"
        family = str(path.path_family or "").strip().lower() or "dynamic_work"
        kind = f"{family}:{role}"
        source_gods = _source_gods_from_path(path)
        if not source_gods:
            source_gods = [target]
        for source in source_gods:
            if source == target:
                continue
            factor = 1.0
            if role == "bridge":
                factor = 1.06
            elif role in {"restrain", "intercept"}:
                factor = 0.98
            signed = sign * eta * factor
            _add_signed_edge(
                edge_bucket,
                source=source,
                target=target,
                signed_value=signed,
                edge_kind=kind,
                path_id=str(path.path_id or ""),
            )

    # 五行关系先验边：用于补齐“无显式 counterpart 的潜在链条”
    all_gods = [str(g).strip() for g in gods if str(g).strip()]
    for source in all_gods:
        src_group = _GOD_GROUP.get(source, "")
        if not src_group:
            continue
        gen_group = _GENERATE_CHAIN.get(src_group, "")
        ctrl_group = _CONTROL_CHAIN.get(src_group, "")
        for target in all_gods:
            if source == target:
                continue
            tgt_group = _GOD_GROUP.get(target, "")
            if not tgt_group:
                continue
            if tgt_group == gen_group:
                _add_signed_edge(
                    edge_bucket,
                    source=source,
                    target=target,
                    signed_value=0.09,
                    edge_kind="prior:generate",
                )
            if tgt_group == ctrl_group:
                _add_signed_edge(
                    edge_bucket,
                    source=source,
                    target=target,
                    signed_value=-0.08,
                    edge_kind="prior:control",
                )

    edges: List[Dict[str, Any]] = []
    for (source, target), row in edge_bucket.items():
        signed = _safe_float(row.get("signed"), 0.0)
        if abs(signed) < 0.02:
            continue
        sign = 1 if signed > 0.0 else -1
        eta = _clamp(abs(signed), 0.04, 0.96)
        kinds = row.get("kinds")
        kind_list = sorted(list(kinds)) if isinstance(kinds, set) else []
        path_ids = row.get("path_ids") if isinstance(row.get("path_ids"), list) else []
        edges.append(
            {
                "source": source,
                "target": target,
                "sign": sign,
                "eta": round(eta, 4),
                "signed": round(sign * eta, 4),
                "count": int(row.get("count") or 0),
                "kinds": kind_list[:4],
                "path_ids": path_ids[:5],
            }
        )
    return edges


def _seed_strengths(gods: Sequence[str], deity_scores: Dict[str, float]) -> Dict[str, float]:
    max_score = max([_safe_float(value, 0.0) for value in deity_scores.values()] or [1.0])
    out: Dict[str, float] = {}
    for god in gods:
        score = max(0.0, _safe_float(deity_scores.get(god), 0.0))
        strength = score / max(max_score, 1.0)
        if strength >= 0.06:
            out[str(god)] = round(strength, 4)
    return out


def _adjacency(edges: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for edge in edges:
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if not source or not target or source == target:
            continue
        out.setdefault(source, []).append(edge)
    for edge_list in out.values():
        edge_list.sort(key=lambda item: abs(_safe_float(item.get("signed"), 0.0)), reverse=True)
    return out


def _enumerate_flux_chains(
    *,
    edges: Sequence[Dict[str, Any]],
    seeds: Dict[str, float],
    max_depth: int = 3,
    per_source_limit: int = 18,
) -> List[Dict[str, Any]]:
    graph = _adjacency(edges)
    chains: List[Dict[str, Any]] = []
    if not graph or not seeds:
        return chains

    for source, seed_strength in sorted(seeds.items(), key=lambda item: item[1], reverse=True):
        candidates = graph.get(source) or []
        if not candidates:
            continue
        local_count = 0

        def dfs(
            *,
            origin: str,
            current: str,
            depth: int,
            sign_product: int,
            eta_product: float,
            nodes: List[str],
            edge_trace: List[Dict[str, Any]],
        ) -> None:
            nonlocal local_count
            if depth > 0:
                flux = float(seed_strength) * float(eta_product) * float(sign_product)
                if abs(flux) >= 0.015:
                    chains.append(
                        {
                            "source": origin,
                            "target": current,
                            "nodes": list(nodes),
                            "depth": depth,
                            "seed": round(float(seed_strength), 4),
                            "eta_product": round(float(eta_product), 4),
                            "sign": int(1 if sign_product >= 0 else -1),
                            "flux": round(flux, 4),
                            "trace": [
                                {
                                    "source": str(e.get("source") or ""),
                                    "target": str(e.get("target") or ""),
                                    "eta": round(_safe_float(e.get("eta"), 0.0), 4),
                                    "sign": int(1 if _safe_float(e.get("signed"), 0.0) >= 0 else -1),
                                    "kinds": list(e.get("kinds") or []),
                                }
                                for e in edge_trace
                            ],
                        }
                    )
                    local_count += 1
            if depth >= max_depth or local_count >= per_source_limit:
                return
            for edge in graph.get(current) or []:
                nxt = str(edge.get("target") or "").strip()
                if not nxt or nxt in nodes:
                    continue
                edge_sign = 1 if _safe_float(edge.get("signed"), 0.0) >= 0 else -1
                edge_eta = _safe_float(edge.get("eta"), 0.0)
                if edge_eta <= 0.0:
                    continue
                dfs(
                    origin=origin,
                    current=nxt,
                    depth=depth + 1,
                    sign_product=sign_product * edge_sign,
                    eta_product=eta_product * edge_eta * (0.92 if depth >= 1 else 1.0),
                    nodes=nodes + [nxt],
                    edge_trace=edge_trace + [edge],
                )

        dfs(
            origin=source,
            current=source,
            depth=0,
            sign_product=1,
            eta_product=1.0,
            nodes=[source],
            edge_trace=[],
        )

    chains.sort(key=lambda row: abs(_safe_float(row.get("flux"), 0.0)), reverse=True)
    return chains[:120]


def _summarize_sink_chains(chains: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    sink_map: Dict[str, List[Dict[str, Any]]] = {}
    for chain in chains:
        target = str(chain.get("target") or "").strip()
        if not target:
            continue
        sink_map.setdefault(target, []).append(chain)

    out: Dict[str, Dict[str, Any]] = {}
    for sink, rows in sink_map.items():
        benefit = sum(max(0.0, _safe_float(row.get("flux"), 0.0)) for row in rows)
        harm = sum(max(0.0, -_safe_float(row.get("flux"), 0.0)) for row in rows)
        total_abs = sum(abs(_safe_float(row.get("flux"), 0.0)) for row in rows) or 1.0
        sorted_rows = sorted(rows, key=lambda row: abs(_safe_float(row.get("flux"), 0.0)), reverse=True)
        top_causes: List[Dict[str, Any]] = []
        for row in sorted_rows[:5]:
            flux = _safe_float(row.get("flux"), 0.0)
            top_causes.append(
                {
                    "source": str(row.get("source") or ""),
                    "depth": int(row.get("depth") or 0),
                    "flux": round(flux, 4),
                    "ratio": round(abs(flux) / total_abs, 4),
                    "nodes": list(row.get("nodes") or []),
                }
            )
        out[sink] = {
            "benefit": round(benefit, 4),
            "harm": round(harm, 4),
            "net": round(benefit - harm, 4),
            "chain_count": len(rows),
            "top_causes": top_causes,
        }
    return out


def _summarize_interaction_matrix(
    *,
    chains: Sequence[Dict[str, Any]],
    limit: int = 120,
) -> List[Dict[str, Any]]:
    bucket: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for chain in chains:
        source = str(chain.get("source") or "").strip()
        target = str(chain.get("target") or "").strip()
        flux = _safe_float(chain.get("flux"), 0.0)
        if not source or not target or source == target or abs(flux) <= 1e-9:
            continue
        key = (source, target)
        row = bucket.setdefault(
            key,
            {"benefit": 0.0, "harm": 0.0, "net": 0.0, "abs_total": 0.0, "count": 0, "depth_sum": 0.0},
        )
        if flux >= 0.0:
            row["benefit"] = float(row["benefit"]) + flux
        else:
            row["harm"] = float(row["harm"]) + (-flux)
        row["net"] = float(row["net"]) + flux
        row["abs_total"] = float(row["abs_total"]) + abs(flux)
        row["count"] = int(row["count"]) + 1
        row["depth_sum"] = float(row["depth_sum"]) + _safe_float(chain.get("depth"), 0.0)

    rows: List[Dict[str, Any]] = []
    for (source, target), row in bucket.items():
        abs_total = max(1e-9, _safe_float(row.get("abs_total"), 0.0))
        benefit = _safe_float(row.get("benefit"), 0.0)
        harm = _safe_float(row.get("harm"), 0.0)
        net = _safe_float(row.get("net"), 0.0)
        count = max(1, int(row.get("count") or 0))
        dominance = abs(net) / abs_total
        if benefit > 0.0 and harm > 0.0:
            polarity = "mixed"
        elif net >= 0.0:
            polarity = "support"
        else:
            polarity = "resist"
        rows.append(
            {
                "source": source,
                "target": target,
                "benefit": round(benefit, 4),
                "harm": round(harm, 4),
                "net": round(net, 4),
                "count": count,
                "avg_depth": round(_safe_float(row.get("depth_sum"), 0.0) / count, 4),
                "support_ratio": round(benefit / abs_total, 4),
                "resist_ratio": round(harm / abs_total, 4),
                "dominance": round(dominance, 4),
                "polarity": polarity,
            }
        )
    rows.sort(
        key=lambda item: (
            abs(_safe_float(item.get("net"), 0.0)),
            _safe_float(item.get("benefit"), 0.0) + _safe_float(item.get("harm"), 0.0),
            int(item.get("count") or 0),
        ),
        reverse=True,
    )
    return rows[: max(0, int(limit))]


def _summarize_tension_pairs(
    *,
    interaction_rows: Sequence[Dict[str, Any]],
    limit: int = 24,
) -> List[Dict[str, Any]]:
    net_map: Dict[Tuple[str, str], float] = {}
    count_map: Dict[Tuple[str, str], int] = {}
    for row in interaction_rows:
        source = str(row.get("source") or "").strip()
        target = str(row.get("target") or "").strip()
        if not source or not target or source == target:
            continue
        key = (source, target)
        net_map[key] = _safe_float(row.get("net"), 0.0)
        count_map[key] = int(row.get("count") or 0)

    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()
    for source, target in net_map.keys():
        pair = tuple(sorted((source, target)))
        if pair in seen:
            continue
        seen.add(pair)
        left, right = pair
        left_to_right = _safe_float(net_map.get((left, right)), 0.0)
        right_to_left = _safe_float(net_map.get((right, left)), 0.0)
        if abs(left_to_right) <= 0.02 or abs(right_to_left) <= 0.02:
            continue
        same_direction = left_to_right * right_to_left > 0.0
        reinforce = min(abs(left_to_right), abs(right_to_left)) if same_direction else 0.0
        tension = min(abs(left_to_right), abs(right_to_left)) if not same_direction else 0.0
        mode = "reinforce" if same_direction else "tension"
        score = reinforce if same_direction else tension
        out.append(
            {
                "left": left,
                "right": right,
                "left_to_right": round(left_to_right, 4),
                "right_to_left": round(right_to_left, 4),
                "mode": mode,
                "score": round(score, 4),
                "reinforce": round(reinforce, 4),
                "tension": round(tension, 4),
                "dominant": round(max(abs(left_to_right), abs(right_to_left)), 4),
                "left_to_right_count": int(count_map.get((left, right), 0)),
                "right_to_left_count": int(count_map.get((right, left), 0)),
            }
        )
    out.sort(
        key=lambda item: (
            _safe_float(item.get("score"), 0.0),
            _safe_float(item.get("dominant"), 0.0),
        ),
        reverse=True,
    )
    return out[: max(0, int(limit))]


def _attach_flux_to_effect_scores(
    *,
    effect_scores: Dict[str, Dict[str, float]],
    sink_summary: Dict[str, Dict[str, Any]],
) -> None:
    for god, row in effect_scores.items():
        if not isinstance(row, dict):
            continue
        flux = sink_summary.get(god) if isinstance(sink_summary.get(god), dict) else {}
        benefit = _safe_float(flux.get("benefit"), 0.0)
        harm = _safe_float(flux.get("harm"), 0.0)
        net = _safe_float(flux.get("net"), 0.0)
        base_resolved = _safe_float(row.get("resolved_utility", row.get("net_utility", 0.0)), 0.0)
        row["flux_benefit"] = round(benefit, 4)
        row["flux_harm"] = round(harm, 4)
        row["flux_net"] = round(net, 4)
        row["flux_chain_count"] = int(flux.get("chain_count") or 0)
        row["flux_top_causes"] = list(flux.get("top_causes") or [])[:3]
        row["resolved_utility_base"] = round(base_resolved, 4)
        row["resolved_utility_flux"] = round(base_resolved + net * 0.42, 4)


def solve_dynamic_flux(
    *,
    paths: Sequence[WorkPath],
    deity_scores: Dict[str, float],
    effect_scores: Dict[str, Dict[str, float]],
    graph: SixPillarGraph | None = None,
    max_depth: int = 3,
) -> Dict[str, Any]:
    gods = _collect_all_gods(paths=paths, deity_scores=deity_scores, effect_scores=effect_scores)
    god_edges = _build_god_flux_edges(paths=paths, gods=gods)
    god_seeds = _seed_strengths(gods, deity_scores)
    god_chains = _enumerate_flux_chains(edges=god_edges, seeds=god_seeds, max_depth=max_depth)
    god_sink_summary = _summarize_sink_chains(god_chains)

    day_master = _day_master_from_graph(graph)
    node_gods = _node_to_god_weights(graph, day_master)
    node_edges = _build_node_flux_edges(paths=paths, graph=graph, node_gods=node_gods)
    node_seeds = _seed_node_strengths(graph=graph, node_gods=node_gods, deity_scores=deity_scores)
    node_chains = _enumerate_flux_chains(edges=node_edges, seeds=node_seeds, max_depth=max_depth + 1, per_source_limit=22)
    node_sink_summary = _summarize_sink_chains(node_chains)
    projected_node_chains = _project_node_chains_to_god_chains(node_chains=node_chains, node_gods=node_gods)
    node_projected_sink_summary = _summarize_sink_chains(projected_node_chains)
    interaction_rows = _summarize_interaction_matrix(
        chains=[*god_chains, *projected_node_chains],
        limit=140,
    )
    tension_pairs = _summarize_tension_pairs(
        interaction_rows=interaction_rows,
        limit=24,
    )

    sink_summary = _merge_sink_summaries(
        base_summary=god_sink_summary,
        node_summary=node_projected_sink_summary,
    )
    _attach_flux_to_effect_scores(effect_scores=effect_scores, sink_summary=sink_summary)
    return {
        "enabled": True,
        "max_depth": int(max_depth),
        "god_count": len(gods),
        "edge_count": len(god_edges),
        "seed_count": len(god_seeds),
        "chain_count": len(god_chains),
        "edges": god_edges[:28],
        "seeds": {god: round(score, 4) for god, score in sorted(god_seeds.items(), key=lambda item: item[1], reverse=True)},
        "top_chains": god_chains[:12],
        "sink_summary_god_edges": god_sink_summary,
        "node_edge_count": len(node_edges),
        "node_seed_count": len(node_seeds),
        "node_chain_count": len(node_chains),
        "node_edges": node_edges[:28],
        "node_seeds": {node: round(score, 4) for node, score in sorted(node_seeds.items(), key=lambda item: item[1], reverse=True)},
        "node_top_chains": node_chains[:14],
        "node_sink_summary": node_sink_summary,
        "projected_chain_count": len(projected_node_chains),
        "projected_top_chains": projected_node_chains[:12],
        "projected_sink_summary": node_projected_sink_summary,
        "interaction_count": len(interaction_rows),
        "interaction_matrix": interaction_rows[:30],
        "tension_pair_count": len(tension_pairs),
        "tension_pairs": tension_pairs[:12],
        "sink_summary": sink_summary,
    }
