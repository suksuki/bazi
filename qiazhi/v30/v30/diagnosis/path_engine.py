from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.contracts import StructureState
from v30.diagnosis.contracts import DiagnosisDomain, DiagnosisPath


PATH_ENGINE_VERSION = "v30.real_bazi_diagnosis.path_engine.v1"

FAMILY_LABELS = {
    "self": "比劫",
    "output": "食伤",
    "wealth": "财星",
    "authority": "官杀",
    "resource": "印星",
    "day_master": "日主",
}

RESOLUTION_LABELS = {
    "reaches_day_master": "回到日主",
    "resource_support_path": "印星承接",
    "tongguan_resource_mediator": "印星通关",
    "tongguan_output_wealth_bridge": "食伤生财桥",
    "zhihua_wealth_authority_resource": "财官印制化",
    "zhihua_output_authority": "食伤制官杀",
    "zhihua_output_authority_resource": "食伤制官转印",
    "zhihua_control_to_generation": "克转生的制化",
    "generate_control_sequence": "生克连续",
    "control_pressure": "克制压力",
    "resource_support_path": "印星承接",
}


def translate_dynamic_paths(
    structure_state: StructureState,
    *,
    timing_context: Mapping[str, Any] | None = None,
    limit: int | None = None,
) -> list[DiagnosisPath]:
    rows = [
        node for node in structure_state.graph_nodes
        if isinstance(node, dict) and node.get("kind") == "dynamic_path"
    ]
    rows.sort(key=lambda row: float(row.get("score", 0.0) or 0.0), reverse=True)
    paths: list[DiagnosisPath] = []
    for row in rows:
        path = _translate_path(row, timing_context=timing_context or {})
        if path is None:
            continue
        paths.append(path)
        paths.extend(_supplemental_paths(row, primary=path, timing_context=timing_context or {}))
    paths.sort(key=lambda row: row.score, reverse=True)
    if limit is not None:
        return paths[:limit]
    return paths


def summarize_diagnosis_paths(paths: Sequence[DiagnosisPath]) -> dict[str, Any]:
    by_domain: dict[str, int] = {}
    by_mechanism: dict[str, int] = {}
    for path in paths:
        for domain in path.domain_targets:
            by_domain[domain] = by_domain.get(domain, 0) + 1
        by_mechanism[path.mechanism] = by_mechanism.get(path.mechanism, 0) + 1
    return {
        "version": PATH_ENGINE_VERSION,
        "path_count": len(paths),
        "domain_counts": dict(sorted(by_domain.items())),
        "mechanism_counts": dict(sorted(by_mechanism.items())),
        "top_path_ids": [path.path_id for path in list(paths)[:8]],
        "high_confidence_path_count": sum(1 for path in paths if path.score >= 0.68),
        "boundary": "diagnosis_path_summary_is_module_trace_not_public_verdict",
    }


def _translate_path(row: Mapping[str, Any], *, timing_context: Mapping[str, Any]) -> DiagnosisPath | None:
    family_chain = _string_list(row.get("family_chain"))
    resolution = _string_list(row.get("resolution_families"))
    if len(family_chain) < 2:
        return None
    score = float(row.get("score", 0.0) or 0.0)
    conflicts = _string_list(row.get("conflict_families"))
    mechanism = _mechanism(family_chain, resolution, conflicts, score_reasons=_string_list(row.get("score_reasons")))
    domain_targets = _domain_targets(family_chain, resolution, conflicts)
    evidence_ids = _evidence_ids(row)
    return _build_path(
        path_id=str(row.get("node_id") or ""),
        family_chain=family_chain,
        mechanism=mechanism,
        resolution=resolution,
        conflicts=conflicts,
        timing_context=timing_context,
        score=score,
        evidence_ids=evidence_ids,
        counter_evidence_ids=_counter_evidence_ids(row),
    )


def _supplemental_paths(
    row: Mapping[str, Any],
    *,
    primary: DiagnosisPath,
    timing_context: Mapping[str, Any],
) -> list[DiagnosisPath]:
    family_chain = _string_list(row.get("family_chain"))
    chain_set = set(family_chain)
    conflicts = _string_list(row.get("conflict_families"))
    if not ({"output", "wealth"} <= chain_set and conflicts):
        return []
    mechanism = "食伤制官杀" if primary.mechanism != "食伤制官杀" else "食伤生财"
    return [
        _build_path(
            path_id=f"{row.get('node_id')}.supplemental.{mechanism}",
            family_chain=family_chain,
            mechanism=mechanism,
            resolution=_string_list(row.get("resolution_families")),
            conflicts=conflicts,
            timing_context=timing_context,
            score=max(0.01, float(row.get("score", 0.0) or 0.0) - 0.01),
            evidence_ids=_evidence_ids(row),
            counter_evidence_ids=_counter_evidence_ids(row),
        )
    ]


def _build_path(
    *,
    path_id: str,
    family_chain: Sequence[str],
    mechanism: str,
    resolution: Sequence[str],
    conflicts: Sequence[str],
    timing_context: Mapping[str, Any],
    score: float,
    evidence_ids: Sequence[str],
    counter_evidence_ids: Sequence[str],
) -> DiagnosisPath:
    domain_targets = _domain_targets(family_chain, resolution, conflicts)
    return DiagnosisPath(
        path_id=path_id,
        family_chain=family_chain,
        mechanism=mechanism,
        domain_targets=domain_targets,
        diagnosis_statement=_diagnosis_statement(family_chain, mechanism, resolution, conflicts),
        risk_statement=_risk_statement(family_chain, mechanism, conflicts),
        timing_trigger=_timing_trigger(timing_context),
        score=round(max(0.01, min(1.0, score)), 3),
        evidence_ids=list(evidence_ids),
        counter_evidence_ids=list(counter_evidence_ids),
        blocked_overclaim=_blocked_overclaims(domain_targets, conflicts),
    )


def _mechanism(
    family_chain: Sequence[str],
    resolution: Sequence[str],
    conflicts: Sequence[str],
    *,
    score_reasons: Sequence[str] = (),
) -> str:
    chain = tuple(family_chain)
    chain_set = set(chain)
    resolution_set = set(resolution)
    competition_rank = _competition_rank(score_reasons)
    if "output" in chain_set and "wealth" in chain_set and conflicts and competition_rank >= 2:
        return "食伤制官杀"
    if chain[:2] == ("output", "wealth") or "tongguan_output_wealth_bridge" in resolution_set:
        return "食伤生财"
    if (
        {"wealth", "authority", "resource"} <= chain_set
        or "zhihua_wealth_authority_resource" in resolution_set
        or ("wealth" in chain_set and "resource" in chain_set and conflicts and "resource_support_path" in resolution_set)
    ):
        return "财官印制化"
    if chain[:2] == ("authority", "resource") or {"authority", "resource"} <= chain_set:
        return "官印相生"
    if {"output", "authority"} <= chain_set:
        return "食伤制官杀"
    if {"self", "wealth"} <= chain_set:
        return "比劫争财"
    if "tongguan_resource_mediator" in resolution_set:
        return "印星通关"
    if chain == ("resource",) and "resource_support_path" in resolution_set:
        return "印星承接"
    if resolution_set & {"zhihua_control_to_generation", "zhihua_output_authority_resource"}:
        return "制化转生"
    if conflicts:
        return "冲突压力路径"
    return "结构流通路径"


def _domain_targets(
    family_chain: Sequence[str],
    resolution: Sequence[str],
    conflicts: Sequence[str],
) -> list[DiagnosisDomain]:
    domains: list[DiagnosisDomain] = ["structure"]
    chain = set(family_chain)
    if "wealth" in chain:
        domains.append("wealth")
    if "wealth" in chain and "resource" in chain and conflicts:
        domains.append("career")
    if "authority" in chain:
        domains.append("career")
        domains.append("relationship")
    if "resource" in chain:
        domains.append("useful_god")
    if "output" in chain and "wealth" in chain:
        domains.append("wealth")
    if conflicts:
        domains.extend(["relationship", "health"])
    if set(resolution) & {"tongguan_resource_mediator", "zhihua_wealth_authority_resource", "resource_support_path"}:
        domains.append("useful_god")
    return _dedupe_domains(domains)


def _diagnosis_statement(
    family_chain: Sequence[str],
    mechanism: str,
    resolution: Sequence[str],
    conflicts: Sequence[str],
) -> str:
    chain_text = " → ".join(_family_label(item) for item in family_chain)
    resolution_text = "、".join(_resolution_label(item) for item in resolution[:3])
    if mechanism == "财官印制化":
        return f"{chain_text}形成财官印路径，财星不是单独成财，而是先牵动责任与压力，再由印星承接回到日主。"
    if mechanism == "官印相生":
        return f"{chain_text}形成官印相生路径，压力、规则或职责需要通过印星转成资质、凭证、学习或平台承接。"
    if mechanism == "食伤生财":
        return f"{chain_text}形成食伤生财路径，财源更依赖输出、技术、表达、方案或流量转化。"
    if mechanism == "食伤制官杀":
        return f"{chain_text}形成食伤制官杀路径，表达和行动力会直接触碰规则、压力或权责边界。"
    if mechanism == "比劫争财":
        return f"{chain_text}形成比劫争财路径，资源分配、合伙分账、同辈竞争或现金流消耗需要重点看。"
    if mechanism == "印星通关":
        return f"{chain_text}出现印星通关，冲突或压力更适合经由学习、规则、资质、长辈/平台资源来承接。"
    if mechanism == "印星承接":
        return f"{chain_text}形成印星承接路径，重点看学习、资质、平台、长辈资源或规则体系如何回生日主。"
    if mechanism == "制化转生":
        return f"{chain_text}有制化转生线索，原本的克制压力可以转成新的承接路径，但仍要看反证和时运触发。"
    if conflicts:
        conflict_text = "、".join(_resolution_label(item) for item in conflicts[:2])
        return f"{chain_text}存在{conflict_text}，这条路径更像压力触发线，不宜直接当成吉凶结论。"
    if resolution_text:
        return f"{chain_text}作为结构流通路径，当前可见{resolution_text}，可用于后续断语承接。"
    return f"{chain_text}作为结构流通路径，可用于复核格局、用神与领域断语。"


def _risk_statement(family_chain: Sequence[str], mechanism: str, conflicts: Sequence[str]) -> str:
    if mechanism in {"财官印制化", "食伤生财"}:
        return "不能把财星路径直接说成收入结果，需要结合大运流年和实际行业/资源形态。"
    if mechanism in {"官印相生", "食伤制官杀"}:
        return "不能把官杀路径直接说成职位结果，需要看印星承接、反证和时运触发。"
    if mechanism == "比劫争财":
        return "不能直接断破财结果，应先看资源分配、合作模式和时运触发。"
    if conflicts:
        return "冲突路径只能作为压力线索，不能直接转成事件预测。"
    return "该路径是诊断证据，不是单点吉凶定论。"


def _timing_trigger(timing_context: Mapping[str, Any]) -> dict[str, Any]:
    layered = _layered_time_pillars(timing_context)
    return {
        "luck_pillar": str(timing_context.get("luck_pillar") or layered.get("luck") or ""),
        "flow_year_pillar": str(timing_context.get("flow_year_pillar") or layered.get("flow_year") or ""),
        "flow_month_pillar": str(timing_context.get("flow_month_pillar") or layered.get("flow_month") or ""),
        "status": str(timing_context.get("status") or ""),
    }


def _layered_time_pillars(timing_context: Mapping[str, Any]) -> dict[str, str]:
    layers = timing_context.get("layers")
    if not isinstance(layers, list):
        return {}
    out: dict[str, str] = {}
    for layer in layers:
        if not isinstance(layer, Mapping):
            continue
        key = str(layer.get("layer_key") or "")
        pillar = layer.get("pillar")
        if not key or not isinstance(pillar, Mapping):
            continue
        stem = str(pillar.get("stem") or "")
        branch = str(pillar.get("branch") or "")
        if stem and branch:
            out[key] = f"{stem}{branch}"
    return out


def _evidence_ids(row: Mapping[str, Any]) -> list[str]:
    ids = _string_list(row.get("evidence_ids"))
    if ids:
        return ids
    return [str(row.get("node_id") or "dynamic_path_evidence")]


def _counter_evidence_ids(row: Mapping[str, Any]) -> list[str]:
    reasons = _string_list(row.get("score_reasons"))
    return sorted(reason for reason in reasons if "counter" in reason or "conflict" in reason or "blockage" in reason)


def _blocked_overclaims(domain_targets: Sequence[DiagnosisDomain], conflicts: Sequence[str]) -> list[str]:
    blocked = {"fixed_bazi_verdict", "fixed_event_prediction"}
    if "wealth" in domain_targets:
        blocked.add("fixed_wealth_outcome_claim")
    if "career" in domain_targets:
        blocked.add("fixed_career_outcome_claim")
    if "relationship" in domain_targets:
        blocked.add("fixed_relationship_outcome_claim")
    if "health" in domain_targets:
        blocked.update({"fixed_health_outcome_claim", "medical_diagnosis", "disease_prediction"})
    if conflicts:
        blocked.add("single_factor_reading")
    return sorted(blocked)


def _family_label(value: str) -> str:
    return FAMILY_LABELS.get(value, value)


def _resolution_label(value: str) -> str:
    return RESOLUTION_LABELS.get(value, value)


def _dedupe_domains(domains: Sequence[DiagnosisDomain]) -> list[DiagnosisDomain]:
    rows: list[DiagnosisDomain] = []
    for domain in domains:
        if domain not in rows:
            rows.append(domain)
    return rows


def _string_list(value: Any) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _competition_rank(score_reasons: Sequence[str]) -> int:
    for reason in score_reasons:
        if not reason.startswith("competition_rank:"):
            continue
        try:
            return int(reason.split(":", 1)[1])
        except ValueError:
            return 1
    return 1
