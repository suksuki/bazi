"""全局枢纽（用神）与 L1 负面事件监测，供 LLM 与 StreamBoard 断言标签。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Set

from app.skills.physics_rules import TEN_DEITIES as _TEN_DEITIES_LIST

_BODY_PARTY = frozenset({"比肩", "劫财", "正印", "偏印"})
_USE_PARTY = frozenset({"食神", "伤官", "正财", "偏财", "正官", "七杀"})


def _pivot_pool(self_abs: float, threshold: float) -> Set[str]:
    return set(_BODY_PARTY) if self_abs < threshold else set(_USE_PARTY)


def _pivot_scores(
    axes: Mapping[str, Any],
    per_deity: Mapping[str, Any],
) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for name in _TEN_DEITIES_LIST:
        blk = axes.get(name)
        if not isinstance(blk, dict):
            continue
        abs_e = float(blk.get("absolute_energy") or 0.0)
        row = per_deity.get(name)
        eff = float((row or {}).get("work_efficiency") or 1.0) if isinstance(row, dict) else 1.0
        out[name] = abs_e * max(0.05, eff)
    return out


def _collect_l1_threats_against_pivot(
    pivot: str,
    meta: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    threats: List[Dict[str, Any]] = []
    jf = meta.get("l1_junction_flags")
    if isinstance(jf, dict) and jf.get("SHANG_GUAN_JIAN_GUAN") and pivot in {"正官", "七杀"}:
        threats.append({"code": "L1_SGJG", "detail": "伤官见官结构对官杀枢纽施压", "severity": 0.85})
    if meta.get("l1_owl_food_v1") and pivot == "食神":
        threats.append({"code": "L1_OWL_FOOD", "detail": "枭神夺食阻尼作用于食神枢纽", "severity": 0.8})
    if (
        isinstance(jf, dict)
        and jf.get("XIAO_SHEN_DUO_SHI")
        and pivot in {"正官", "七杀"}
        and meta.get("l1_owl_food_v1")
    ):
        threats.append(
            {
                "code": "L1_XSDS_OFFICER_PIVOT",
                "detail": "枭神夺食削弱食伤根气，与官杀枢纽同局叠加承压",
                "severity": 0.42,
            }
        )
    ws = meta.get("l1_wealth_seal_v1")
    if isinstance(ws, dict) and pivot in {"正印", "偏印"}:
        touched = ws.get("deities_scaled")
        if isinstance(touched, list) and pivot in [str(x) for x in touched]:
            threats.append({"code": "L1_WEALTH_SEAL", "detail": "财星破印触及印星枢纽", "severity": 0.75})
    if meta.get("l1_robber_wealth_v1") and pivot == "正财":
        threats.append({"code": "L1_ROBBER_WEALTH", "detail": "劫财见财分配损耗作用于正财枢纽", "severity": 0.7})
    if meta.get("l1_gov_kill_mix_v1") and pivot in {"正官", "七杀"}:
        threats.append({"code": "L1_GOV_KILL_MIX", "detail": "官杀混杂降低决策效率", "severity": 0.65})
    if meta.get("l1_blade_clash_v1"):
        threats.append({"code": "L1_BLADE_CLASH", "detail": "羊刃逢冲抬升全局熵（泛威胁）", "severity": 0.4})
    return threats


def compute_pivot_defense(
    *,
    physics_tensor: MutableMapping[str, Any],
    self_abs: float,
    settings: Mapping[str, float],
) -> Dict[str, Any]:
    meta_raw = physics_tensor.get("meta")
    meta = meta_raw if isinstance(meta_raw, dict) else {}
    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict) or not axes:
        return {
            "target_pivot": "",
            "pivot_score": 0.0,
            "threats": [],
            "pivot_crisis": False,
            "llm_assertion_tags": ["PIVOT_UNKNOWN"],
            "defense_semantic": "枢纽数据不足",
        }

    l1s = meta.get("l1_status_v1")
    per_deity = (l1s or {}).get("per_deity") if isinstance(l1s, dict) else {}
    if not isinstance(per_deity, dict):
        per_deity = {}

    thr = float(settings.get("WS_PIVOT_SELF_WEAK_THRESHOLD", 5.0))
    pool = _pivot_pool(float(self_abs), thr)
    scores = _pivot_scores(axes, per_deity)
    pivot = max(pool, key=lambda n: scores.get(n, 0.0)) if pool else ""
    pivot_score = round(float(scores.get(pivot, 0.0)), 4) if pivot else 0.0

    threats = _collect_l1_threats_against_pivot(pivot, meta) if pivot else []
    sev_sum = sum(float(t.get("severity") or 0.0) for t in threats)
    crisis = bool(pivot) and (sev_sum >= 1.2 or any(float(t.get("severity") or 0) >= 0.8 for t in threats))

    if crisis:
        tags = ["PIVOT_CRISIS", "命脉受损"]
        defense_semantic = "枢纽受 L1 负面结构夹击，命脉受损风险升高"
    elif pivot and threats:
        tags = ["PIVOT_STRESSED", "枢纽承压"]
        defense_semantic = "枢纽仍在，但存在可解释的 L1 摩擦项"
    elif pivot:
        tags = ["PIVOT_STABLE", "枢纽稳固"]
        defense_semantic = "用神/枢纽在当前 L1 快照下相对稳固"
    else:
        tags = ["PIVOT_UNKNOWN"]
        defense_semantic = "未能标定枢纽十神"

    out = {
        "target_pivot": pivot,
        "pivot_score": pivot_score,
        "pivot_pool": "body_party" if self_abs < thr else "use_party",
        "self_abs_ref": round(float(self_abs), 4),
        "threats": threats,
        "pivot_crisis": crisis,
        "threat_severity_sum": round(sev_sum, 4),
        "llm_assertion_tags": tags,
        "defense_semantic": defense_semantic,
    }
    meta_mut = physics_tensor.setdefault("meta", {})
    if isinstance(meta_mut, dict):
        meta_mut["pivot_defense_v1"] = out
    return out
