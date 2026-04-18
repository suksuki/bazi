from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _derive_day_master_stem(physics_tensor: Dict[str, Any]) -> str:
    stem = str(physics_tensor.get("day_master_stem") or "").strip()
    if stem:
        return stem
    pillars = physics_tensor.get("four_pillars")
    if isinstance(pillars, dict):
        day = str(pillars.get("day") or "").strip()
        if day:
            return day[:1]
    return "壬"


class NarrativeMappingEngine:
    """将 L1.5 物理流转摘要转译为可注入 L2 Prompt 的事实断言。"""

    FLOW_STEPS = {"L1.5_FLOW_SETTLEMENT", "SRC_FLOW"}

    @classmethod
    def _element_lead_gods(cls, physics_tensor: Dict[str, Any]) -> Dict[str, str]:
        try:
            from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map
        except Exception:
            return {}

        scores_raw = (
            physics_tensor.get("ten_gods_absolute")
            or physics_tensor.get("ten_gods_absolute_intensity")
            or physics_tensor.get("deity_scores")
            or {}
        )
        scores = scores_raw if isinstance(scores_raw, dict) else {}
        g2e = _get_god_to_element_map(_derive_day_master_stem(physics_tensor))
        best: Dict[str, Tuple[str, float]] = {}
        for god, element in g2e.items():
            if not str(element).strip():
                continue
            score = _safe_float(scores.get(god))
            prev = best.get(element)
            if prev is None or score > prev[1]:
                best[element] = (str(god), score)
        return {element: god for element, (god, _score) in best.items()}

    @classmethod
    def _flow_ledger_assertions(cls, physics_tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
        ledger = physics_tensor.get("ten_gods_ledger")
        if not isinstance(ledger, dict):
            return []
        out: List[Dict[str, Any]] = []
        for god, entries in ledger.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                step = str(entry.get("step") or "").strip()
                source = str(entry.get("source") or "").strip()
                is_flow = step in cls.FLOW_STEPS or "FLOW" in step or source == "SRC_FLOW"
                if not is_flow:
                    continue
                val = _safe_float(entry.get("val"))
                delta = _safe_float(entry.get("delta"))
                prev_val = val - delta
                ratio = abs(delta) / max(abs(prev_val), 1.0)
                if ratio > 0.10:
                    out.append(
                        {
                            "god": str(god),
                            "delta": delta,
                            "ratio": ratio,
                            "step": step or "SRC_FLOW",
                            "source": source or "SRC_FLOW",
                            "highlight_type": str(entry.get("highlight_type") or "").strip() or "cyan",
                        }
                    )
        out.sort(key=lambda item: (item["ratio"], abs(item["delta"])), reverse=True)
        return out[:6]

    @classmethod
    def _conductive_paths(cls, physics_tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
        topology = physics_tensor.get("flow_topology")
        if not isinstance(topology, list):
            return []
        lead_gods = cls._element_lead_gods(physics_tensor)
        out: List[Dict[str, Any]] = []
        for row in topology:
            if not isinstance(row, dict):
                continue
            resistance = _safe_float(row.get("resistance"), default=999.0)
            if resistance >= 1.0:
                continue
            from_el = str(row.get("from_el") or "").strip()
            to_el = str(row.get("to_el") or "").strip()
            out.append(
                {
                    "from_el": from_el,
                    "to_el": to_el,
                    "from_god": lead_gods.get(from_el, from_el),
                    "to_god": lead_gods.get(to_el, to_el),
                    "current": _safe_float(row.get("current")),
                    "resistance": resistance,
                    "stress": _safe_float(row.get("stress")),
                    "rel": str(row.get("rel") or "").strip() or "流转",
                }
            )
        out.sort(key=lambda item: abs(item["current"]), reverse=True)
        return out[:6]

    @classmethod
    def build_physics_report_lines(cls, physics_tensor: Dict[str, Any]) -> List[str]:
        if not isinstance(physics_tensor, dict) or not physics_tensor:
            return []

        lines: List[str] = []
        for item in cls._flow_ledger_assertions(physics_tensor):
            lines.append(
                "Report: Node[{god}] ΔQ={delta:+.2f} ({ratio_pct:.1f}%) via [{source}]；判定=核心动能点。".format(
                    god=item["god"],
                    delta=item["delta"],
                    ratio_pct=item["ratio"] * 100.0,
                    source=item["source"],
                )
            )

        for path in cls._conductive_paths(physics_tensor):
            lines.append(
                "Report: Source[{from_god}] -> Outlet[{to_god}] 经由 {rel} 路导通；I={current:.2f}，R={resistance:.2f}，Stress[F={stress:.2f}]；判定=因果导通路径。".format(
                    from_god=path["from_god"],
                    to_god=path["to_god"],
                    rel=path["rel"],
                    current=path["current"],
                    resistance=path["resistance"],
                    stress=path["stress"],
                )
            )

        deduped: List[str] = []
        seen: set[str] = set()
        for line in lines:
            if line in seen:
                continue
            seen.add(line)
            deduped.append(line)
        return deduped[:8]
