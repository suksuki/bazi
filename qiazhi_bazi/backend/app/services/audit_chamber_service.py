"""逻辑检察院：物理张量 vs 叙事层（终判）一致性审计（原型）。"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from app.api.contracts import AuditDiagnoseRequest, BlindSchoolFeatureFlags
from app.core.evolution.dna_registry import append_routing_audit_item
from app.core.plugins.registry import PluginRegistry
from app.core.routing.causal_router import CausalRouter, load_routing_config
from app.core.scanner import Scanner
from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FlowState
from app.services.decision_inbox_plugin_service import apply_decision_inbox_pipeline
from app.services.helpers.interaction_pipeline import evaluate_interactions
from app.services.helpers.sys_core_physics_plugin import SYS_CORE_PHYSICS_BUNDLE_SRC_KEY
from app.services.helpers.tensor_adapters import ensure_abs_nodes_on_physics_tensor
from app.skills.final_verdict_parts.evidence import get_logical_evidence
from app.skills.physics_engine import PhysicsInferenceSkill
from app.plugins.blind_school.mangpai_engine import scan_six_harm_points


def _strip_md(s: str) -> str:
    t = re.sub(r"```[\s\S]*?```", " ", s or "")
    t = re.sub(r"[#*_`>\[\]()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _keywords_for_evidence_line(line: str) -> List[str]:
    out: List[str] = []
    if "地支.三合." in line:
        out.extend(["三合", "合局"])
        m = re.search(r"=(寅午戌|申子辰|亥卯未|巳酉丑)", line)
        if m:
            out.append(m.group(1))
        for et in ("金局", "木局", "水局", "火局"):
            if et in line:
                out.append(et)
    if line.startswith("根气."):
        out.append("根气")
    if "十神." in line:
        parts = line.split(".")
        if len(parts) > 1:
            out.append(parts[1])
    dedup: List[str] = []
    for k in out:
        k = k.strip()
        if k and k not in dedup:
            dedup.append(k)
    return dedup


def _line_covered_by_verdict(line: str, verdict_norm: str) -> bool:
    if not verdict_norm:
        return False
    keys = _keywords_for_evidence_line(line)
    if not keys:
        return any(ch in verdict_norm for ch in line if ord(ch) > 127) and line[:24] in verdict_norm
    hits = sum(1 for k in keys if k and k in verdict_norm)
    return hits >= max(1, (len(keys) + 1) // 2)


def _gap_attribution(
    *,
    line: str,
    gate: Dict[str, Any],
    meta: Dict[str, Any],
) -> str:
    reasons: List[str] = []
    if not gate.get("inbox_conflict_cards_eligible", True):
        reasons.append(
            f"Decision Inbox 信噪门控：abs_estimate={gate.get('abs_estimate')} 低于阈值 "
            f"{gate.get('threshold')} 且无 CRITICAL 旁路 → 判词观察项被抑制（叙事可能更「干净」）。"
        )
    if "地支.三合." in line and not gate.get("has_critical_marker", False):
        ae = gate.get("abs_estimate")
        if ae is not None and float(ae) < float(gate.get("threshold") or 5.0):
            reasons.append("低冲战损耗 + 无 CRITICAL 标记时，模型更易忽略次要物理标签（含三合脱水行）。")
    pp = meta.get("pattern_profile") if isinstance(meta.get("pattern_profile"), dict) else {}
    if pp.get("sovereignty_priority"):
        reasons.append("格局主权（pattern_profile.sovereignty_priority）可能改写 L1 对抗叙事权重。")
    if not reasons:
        reasons.append("更可能是 LLM 采样/篇幅裁剪未引用该证据行，而非 η 门控单独导致。")
    return " ".join(reasons)


def _build_markdown_report(
    *,
    pillars_summary: str,
    logical_evidence: List[str],
    narrative_diff: Dict[str, Any],
    gate: Dict[str, Any],
    sanhe_n: int,
    steps_n: int,
    l1_flags: Dict[str, Any],
) -> str:
    lines = [
        "## 逻辑检察院 · 审计报告（原型）",
        "",
        f"**四柱摘要**：{pillars_summary}",
        "",
        "### 1. 物理层已检出结构",
        f"- L1 原子流步数：`{steps_n}`",
        f"- 三合聚能簇数量：`{sanhe_n}`",
        f"- L1 Junction：`SHANG_GUAN_JIAN_GUAN={bool(l1_flags.get('SHANG_GUAN_JIAN_GUAN'))}`，"
        f"`sgjg_severity={l1_flags.get('sgjg_severity', '—')}`",
        "",
        "### 2. 叙事层（终判）覆盖",
    ]
    miss = narrative_diff.get("missing_evidence_lines") or []
    if miss:
        lines.append("以下 `logical_evidence` 行在终判正文中未检出足够关键词重合：")
        for item in miss:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('line','')}` → {item.get('attribution','')}")
            else:
                lines.append(f"- `{item}`")
    else:
        lines.append("- 未提供终判文本，或抽样关键词均命中。")
    lines.extend(
        [
            "",
            "### 3. Decision Inbox 门控快照",
            f"- `inbox_conflict_cards_eligible`：**{gate.get('inbox_conflict_cards_eligible')}**",
            f"- `abs_estimate`：{gate.get('abs_estimate')}，阈值：{gate.get('threshold')}",
            f"- `has_critical_marker`：{gate.get('has_critical_marker')}",
            "",
            "> 本报告为规则启发式生成，不等价于完整因果证明。",
        ]
    )
    return "\n".join(lines)


def _confront_draft_answer(question: str, ctx: Dict[str, Any]) -> str:
    q = (question or "").strip()
    if not q:
        return ""
    gate = ctx.get("decision_signal_to_noise") or {}
    sanhe = ctx.get("sanhe_cluster_count", 0)
    low = f"当前门控：`eligible={gate.get('inbox_conflict_cards_eligible')}`，`abs_estimate={gate.get('abs_estimate')}`。"
    if "三合" in q or "合局" in q:
        if sanhe == 0:
            return f"插件 `plugin_outputs.sys.core.physics.payload.sanhe_clusters` 为空（未凑齐三支或未触发登记）。{low}"
        return f"物理层已登记 **{sanhe}** 组三合簇；若终判未写，多为叙事裁剪或未强制引用证据行。{low}"
    if "门控" in q or "η" in q or "eta" in q.lower():
        return (
            f"Inbox 门控由 `GLOBAL_DECISION_ABS_THRESHOLD`（默认 5.0）与 "
            f"`has_critical_marker` 共同决定：{gate}。"
        )
    if "伤官" in q and "官" in q:
        jf = ctx.get("l1_junction_flags") or {}
        return f"L1 伤官见官标志：`{jf}`。若与格局主权并存，路由层可能下调对抗叙事优先级。"
    return f"（原型）请结合左侧物理瀑布与 `logical_evidence` 对照阅读。{low}"


def run_audit_diagnose(body: AuditDiagnoseRequest) -> Dict[str, Any]:
    blind_flags = (
        body.blind_school_features.model_dump()
        if body.blind_school_features
        else BlindSchoolFeatureFlags().model_dump()
    )
    matrix = Scanner().scan(body.pillars)
    points = list(matrix.points)
    if blind_flags.get("enable_pierce_harm", True) and "classical.blind_school.v1" in (body.enabled_plugins or []):
        points.extend(scan_six_harm_points(body.pillars))
    metadata_obj = BaziMetadata(
        pillars=body.pillars,
        conflict_matrix=ConflictMatrix(points=points),
        flow_state=FlowState.UNKNOWN,
        notes="audit_chamber.diagnose",
        temporal_context=body.temporal_context,
    )
    physics_skill = PhysicsInferenceSkill.instance()
    consumed = physics_skill.consume(
        {
            "metadata": metadata_obj,
            "session_id": body.session_id,
            "dayun": body.dayun,
            "liunian": body.liunian,
            "physics_config": body.physics_config.model_dump(exclude_none=True) if body.physics_config else {},
        }
    )
    physics_tensor = physics_skill.produce(consumed)
    evaluate_interactions(
        physics_tensor=physics_tensor,
        metadata=metadata_obj,
        interaction_params=physics_skill.get_interaction_params(),
        physics_config=body.physics_config.model_dump(exclude_none=True) if body.physics_config else {},
    )
    ensure_abs_nodes_on_physics_tensor(physics_tensor)
    registry = PluginRegistry()
    plugin_outputs = registry.run_hook(
        hook="on_physics_complete",
        enabled_plugins=body.enabled_plugins,
        context={
            "physics_tensor": physics_tensor,
            "metadata": metadata_obj.model_dump(),
            "blind_school_features": blind_flags,
        },
    )
    physics_tensor.setdefault("meta", {})
    if isinstance(physics_tensor.get("meta"), dict):
        physics_tensor["meta"]["enabled_plugins"] = list(body.enabled_plugins or [])
    try:
        negotiated = CausalRouter(routing_config=load_routing_config()).negotiate_impact(
            plugin_outputs,
            physics_tensor=physics_tensor,
        )
        meta = physics_tensor.get("meta")
        if isinstance(meta, dict):
            meta["causal_routing"] = negotiated
        append_routing_audit_item(physics_tensor, negotiated)
    except Exception:
        pass
    physics_tensor["plugin_outputs"] = plugin_outputs
    try:
        apply_decision_inbox_pipeline(physics_tensor=physics_tensor, plugin_outputs=plugin_outputs, registry=registry)
    except Exception:
        pass
    if isinstance(physics_tensor, dict):
        physics_tensor.pop(SYS_CORE_PHYSICS_BUNDLE_SRC_KEY, None)

    md = metadata_obj.model_dump()
    logical_evidence = get_logical_evidence(
        metadata=md,
        physics_tensor=physics_tensor,
        selected_cards=[],
        consensus_history=[],
    )
    verdict = body.final_verdict_markdown or ""
    verdict_norm = _strip_md(verdict)
    missing: List[Dict[str, Any]] = []
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    gate = meta.get("decision_signal_to_noise") if isinstance(meta.get("decision_signal_to_noise"), dict) else {}
    for line in logical_evidence:
        if line.startswith("四柱=") or line.startswith("性别="):
            continue
        if verdict_norm and not _line_covered_by_verdict(line, verdict_norm):
            missing.append({"line": line, "attribution": _gap_attribution(line=line, gate=gate, meta=meta)})

    po = physics_tensor.get("plugin_outputs") or {}
    core_row = po.get("sys.core.physics") if isinstance(po, dict) else None
    core_pl = (core_row or {}).get("payload") if isinstance(core_row, dict) else None
    core_pl = core_pl if isinstance(core_pl, dict) else {}
    pipe = core_pl.get("l1_atomic_pipeline") if isinstance(core_pl.get("l1_atomic_pipeline"), dict) else {}
    sn_clusters = core_pl.get("sanhe_clusters") if isinstance(core_pl.get("sanhe_clusters"), list) else []
    if not sn_clusters and isinstance(core_pl.get("composite_field_impact"), dict):
        sn_clusters = (core_pl["composite_field_impact"].get("sanhe_clusters") or [])
    sanhe_n = len(sn_clusters) if isinstance(sn_clusters, list) else 0
    steps = pipe.get("steps") if isinstance(pipe, dict) else []
    steps_n = len(steps) if isinstance(steps, list) else 0
    l1_flags = meta.get("l1_junction_flags") if isinstance(meta.get("l1_junction_flags"), dict) else {}

    pillars_summary = str(md.get("pillars", {}))
    narrative_diff = {
        "verdict_provided": bool(verdict.strip()),
        "missing_evidence_lines": missing,
    }
    out: Dict[str, Any] = {
        "ok": True,
        "metadata": md,
        "logical_evidence": logical_evidence,
        "sys_core_physics": {
            "plugin_id": "sys.core.physics",
            "l1_atomic_pipeline": pipe,
            "composite_field_impact": core_pl.get("composite_field_impact")
            if isinstance(core_pl.get("composite_field_impact"), dict)
            else {},
            "sanhe_clusters": sn_clusters if isinstance(sn_clusters, list) else [],
        },
        "decision_inbox_gate": gate,
        "l1_junction_flags": l1_flags,
        "narrative_diff": narrative_diff,
    }
    if body.return_physics_tensor:
        out["physics_tensor"] = physics_tensor

    ctx = {
        "decision_signal_to_noise": gate,
        "sanhe_cluster_count": sanhe_n,
        "l1_junction_flags": l1_flags,
    }
    if body.user_question:
        out["confront_answer_markdown"] = _confront_draft_answer(body.user_question, ctx)

    if body.generate_report:
        out["audit_report_markdown"] = _build_markdown_report(
            pillars_summary=pillars_summary,
            logical_evidence=logical_evidence,
            narrative_diff=narrative_diff,
            gate=gate,
            sanhe_n=sanhe_n,
            steps_n=steps_n,
            l1_flags=l1_flags,
        )
    return out
