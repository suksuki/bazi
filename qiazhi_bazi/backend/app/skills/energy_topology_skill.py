"""Energy topology skill: path discovery + impedance calculation."""
from __future__ import annotations

from typing import Any, Dict, List

from app.core.config.physics_settings import resolve_physics_settings
from app.skills.base import AuditLog, BaseSkill


from app.skills.relation_nodes import RelationNodeFactory

RELATION_GAIN = {
    "冲": 1.0,
    "合": 0.85,
    "刑": 0.8,
    "穿": 0.95,
    "害": 0.7,
    "破": 0.65,
    "生": 0.75,
    "克": 0.9,
}

_BRANCH_CHARS = frozenset("子丑寅卯辰巳午未申酉戌亥")


class EnergyTopologySkill(BaseSkill):
    skill_id = "energy_topology_skill"
    skill_version = "0.1.0"
    rule_version = "etrm_rules.v1"

    def consume(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "metadata": context.get("metadata") or {},
            "physics_tensor": context.get("physics_tensor") or {},
        }

    def produce(self, consumed: Dict[str, Any]) -> Dict[str, Any]:
        return self.build_topology(
            metadata=consumed["metadata"],
            physics_tensor=consumed["physics_tensor"],
        )

    def audit(self, consumed: Dict[str, Any], produced: Dict[str, Any]) -> AuditLog:
        return AuditLog(
            skill_id=self.skill_id,
            skill_version=self.skill_version,
            rule_version=self.rule_version,
            param_version_id=str((((consumed.get("physics_tensor") or {}).get("audit_log") or {}).get("param_version_id") or "unknown")),
            formula_refs=[
                "effective_energy = raw_energy * resonance_boost * relation_gain * distance_decay",
                "distance_decay = max(0.1, 1 - decay_per_column * distance)",
            ],
            trace={"edge_count": len((produced.get("edges") or []))},
        )



    @classmethod
    def build_topology(cls, *, metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
        pillars = (metadata or {}).get("pillars") or {}
        conflicts = (((metadata or {}).get("conflict_matrix") or {}).get("points") or [])
        deity_axes = ((physics_tensor or {}).get("deity_energy_axes") or {})
        runtime_cfg = (((physics_tensor or {}).get("meta") or {}).get("runtime_physics_config") or {})
        settings = resolve_physics_settings(runtime_cfg)
        boost = float(settings.get("STEM_RESONANCE_BOOST", 1.5))
        decay = float(settings.get("TRANSFER_DISTANCE_DECAY", 0.1))
        threshold = float(settings.get("WORK_MIN_THRESHOLD", 0.5))
        climate_intensity = float(settings.get("CLIMATE_INTENSITY", 1.0))

        # 12-node simplified ring from visible stems/branches.
        nodes: List[Dict[str, Any]] = []
        for key in ("year", "month", "day", "hour"):
            p = pillars.get(key) or {}
            stem = str(p.get("stem", ""))
            branch = str(p.get("branch", ""))
            nodes.append({"id": f"{key}_stem", "label": stem, "kind": "stem", "abs_final": 0.0})
            nodes.append({"id": f"{key}_branch", "label": branch, "kind": "branch", "abs_final": 0.0})

        # Use total Abs mean as base potential for now.
        abs_values = [float((v or {}).get("absolute_energy", 0.0) or 0.0) for v in deity_axes.values() if isinstance(v, dict)]
        base_abs = (sum(abs_values) / len(abs_values)) if abs_values else 1.0
        for node in nodes:
            # V1: branch nodes hold stronger manifested potential than stem nodes.
            if node.get("kind") == "branch":
                node["abs_final"] = round(base_abs * 1.1, 4)
            else:
                node["abs_final"] = round(base_abs * 0.9, 4)

        edges: List[Dict[str, Any]] = []
        topology_audit: List[Dict[str, Any]] = []
        for point in conflicts:
            if not isinstance(point, dict):
                continue
            detail = str(point.get("detail") or "")
            rule_node = RelationNodeFactory.get_rule_from_detail(detail)
            relation = rule_node.relation_key
            raw_energy = base_abs * RELATION_GAIN.get(relation, 0.8)
            distance = 1.0

            topology_result = rule_node.apply_topology(
                raw_energy=raw_energy,
                boost_setting=boost,
                decay_setting=decay,
                distance=distance
            )
            resonance_boost = topology_result.get("resonance_boost", 1.0)
            distance_decay = topology_result.get("distance_decay", 1.0)
            final_work = topology_result.get("final_work", raw_energy)

            if final_work < threshold:
                continue
            efficiency = max(0.0, min(1.0, (resonance_boost * distance_decay) / max(boost, 0.0001)))
            edge = {
                "from": "month_branch",
                "to": "day_branch",
                "relation": relation,
                "relation_type": rule_node.relation_type,
                "stem_resonance": topology_result.get("stem_resonance", False),
                "flow_direction": "month_branch->day_branch",
                "raw_energy": round(raw_energy, 4),
                "resonance_boost": resonance_boost,
                "resonance_multiplier": round(resonance_boost * distance_decay, 4),
                "distance_decay": distance_decay,
                "efficiency_score": round(efficiency, 4),
                "clash_vibration_flag": topology_result.get("clash_vibration_flag", False),
                "final_work": final_work,
                "detail": detail,
            }
            edges.append(edge)
            topology_audit.append(
                {
                    "detail": detail,
                    "Raw_Energy": round(raw_energy, 4),
                    "Resonance_Boost": round(resonance_boost, 4),
                    "Decay": round(distance_decay, 4),
                    "Final_Work": round(final_work, 4),
                }
            )

        sanhe_edges, sanhe_audit = cls._sanhe_cluster_edges(
            physics_tensor=physics_tensor or {},
            base_abs=base_abs,
            threshold=threshold,
            boost=boost,
            decay=decay,
        )
        edges.extend(sanhe_edges)
        topology_audit.extend(sanhe_audit)

        return {
            "nodes": nodes,
            "edges": edges,
            "topology_audit": topology_audit,
            "threshold": threshold,
            "params": {
                "STEM_RESONANCE_BOOST": boost,
                "TRANSFER_DISTANCE_DECAY": decay,
                "WORK_MIN_THRESHOLD": threshold,
                "CLIMATE_INTENSITY": climate_intensity,
            },
        }

    @staticmethod
    def _sanhe_cluster_edges(
        *,
        physics_tensor: Dict[str, Any],
        base_abs: float,
        threshold: float,
        boost: float,
        decay: float,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """将 composite_field_impact.sanhe_clusters 转为拓扑边（relation_type=sanhe_cluster，供前端金色渲染）。"""
        comp = (physics_tensor or {}).get("composite_field_impact")
        if not isinstance(comp, dict):
            return [], []
        raw = comp.get("sanhe_clusters")
        if not isinstance(raw, list):
            return [], []
        extra_edges: List[Dict[str, Any]] = []
        extra_audit: List[Dict[str, Any]] = []
        floor_work = max(float(threshold) + 0.12, 1.05)

        for idx, cl in enumerate(raw):
            if not isinstance(cl, dict):
                continue
            labels: List[str] = []
            nodes = cl.get("nodes") or []
            if isinstance(nodes, list):
                for n in nodes:
                    if not isinstance(n, dict):
                        continue
                    br = str(n.get("branch") or "").strip()
                    if len(br) == 1 and br in _BRANCH_CHARS:
                        labels.append(br)
            uniq: List[str] = []
            seen: set[str] = set()
            for b in labels:
                if b not in seen:
                    seen.add(b)
                    uniq.append(b)
            if len(uniq) < 2:
                brs = cl.get("branches") or []
                if isinstance(brs, list):
                    for x in brs:
                        b = str(x).strip()
                        if len(b) == 1 and b in _BRANCH_CHARS and b not in seen:
                            seen.add(b)
                            uniq.append(b)
            if len(uniq) < 2:
                continue
            bureau = "·".join(uniq)
            cluster_abs = float(cl.get("cluster_abs") or 0.0)
            for i in range(len(uniq)):
                a, b = uniq[i], uniq[(i + 1) % len(uniq)]
                if a == b:
                    continue
                work = max(floor_work, min(2.4, cluster_abs * 0.12 + 0.92))
                raw_energy = base_abs * RELATION_GAIN.get("合", 0.85)
                edge = {
                    "from": a,
                    "to": b,
                    "relation": "三合",
                    "relation_type": "sanhe_cluster",
                    "stem_resonance": False,
                    "flow_direction": f"{a}->{b}",
                    "raw_energy": round(raw_energy, 4),
                    "resonance_boost": boost,
                    "distance_decay": decay,
                    "resonance_multiplier": round(boost * decay, 4),
                    "efficiency_score": 0.92,
                    "clash_vibration_flag": False,
                    "final_work": round(work, 4),
                    "detail": f"合成场·三合局 [{bureau}]",
                }
                extra_edges.append(edge)
                extra_audit.append(
                    {
                        "detail": edge["detail"],
                        "kind": "sanhe_cluster",
                        "cluster_index": idx,
                        "Final_Work": round(work, 4),
                    }
                )
        return extra_edges, extra_audit
