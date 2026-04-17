from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from app.core.runtime_config import get_runtime_config
from app.plugins.blind_school.core import run_blind_school_plugin
from app.plugins.blind_school.skill_prompt import format_blind_skill_registry_for_prompt
from app.core.rules.junction import sync_l1_junction_flags_to_meta
from app.prompts.final_verdict_contracts import build_final_verdict_system_message
from app.prompts.final_verdict_user_locale import FinalVerdictUserLocale
from app.prompts.physics_audit import SYSTEM_FACT_CONFLICT_ANCHOR
from app.services.helpers.tensor_adapters import collect_conflict_matrix_points_for_llm
from app.skills.final_verdict_parts.metadata_sanitize import (
    sanitize_metadata_for_verdict_llm,
    scrub_previous_verdict_sql,
    shallow_physics_for_llm_evidence,
)
from app.skills.blind_school_encyclopedia import audit_host_guest_vectors, build_blind_school_digest
from app.skills.dual_school_auditor import build_dual_school_audit
from app.skills.final_verdict_parts.context_trim import clean_context_lines
from app.skills.final_verdict_parts.core_logic_seed import format_core_logic_seed_user_block
from app.skills.final_verdict_parts.evidence import format_audit_snapshot_inline, get_logical_evidence
from app.skills.final_verdict_parts.evidence_chunking import format_plugin_evidence_chunks
from app.skills.spatial_sovereignty import audit_spatial_sovereignty
from app.services.helpers.l2_structure_bundle import build_structure_bundle_with_l2
from app.services.helpers.will_injection import UPDATE_PHYSICS_PARAM
from app.utils.semantic_firewall import strip_float_literals as _semantic_firewall_strip_float_literals
from app.semantic_translator.imagery_mapping import (
    adapt_lines_for_style,
    build_data_imagery_mapping_lines,
    build_pattern_specialized_prompt_lines,
    build_style_anchor,
    translate_to_human_terms,
)
from app.semantic_translator.aliasing import alias_fact_ids_in_text
from app.skills.prompts_registry import (
    SCENE_ARCHITECT,
    SCENE_PROPHET,
    output_purge_directive,
    prompt_user_prefix,
    prompt_user_suffix,
    scene_system_directive,
)


_DNUM = re.compile(r"\d+(?:\.\d+)?")


def _denude_numeric_tokens(s: str) -> str:
    """终判 User：弱化物理数值泄漏（保留干支等非数字 token）。"""
    t = _DNUM.sub("·", str(s or ""))
    while "··" in t:
        t = t.replace("··", "·")
    return t.strip()


def _pack_verified_facts(
    rows: List[str],
    *,
    max_items: int = 72,
) -> Tuple[List[str], int]:
    """将多源脱水行编号为 VF01…，供 LLM 在 assertions 中短引用。"""
    out: List[str] = []
    n = 0
    for raw in rows:
        s = str(raw or "").strip()
        if not s:
            continue
        s = _denude_numeric_tokens(s)
        # V13.35：User Message 禁止直注 Fact_ID，统一转语义别名。
        s = alias_fact_ids_in_text(s)
        if not s:
            continue
        n += 1
        out.append(f"VF{n:02d}: {s[:280]}")
        if n >= max_items:
            break
    return out, n


def _verdict_skeleton_confirmed_decisions_block(md_for_llm: Dict[str, Any], loc: FinalVerdictUserLocale) -> str:
    """终判 Step5：物理定论骨架 + 用户结构化意志（与 CONTRACT_MODE 配对）。"""
    va = md_for_llm.get("verdict_anchor_layer") if isinstance(md_for_llm.get("verdict_anchor_layer"), dict) else {}
    sk = str(va.get("verdict_skeleton") or "").strip()
    sk_disp = sk if sk else loc.skeleton_empty_fallback()
    cd_lines: List[str] = []
    pl = md_for_llm.get("persistence_layer") if isinstance(md_for_llm.get("persistence_layer"), dict) else {}
    cv = pl.get("confirmed_verdicts") if isinstance(pl.get("confirmed_verdicts"), list) else []
    for i, e in enumerate(cv[-16:]):
        if not isinstance(e, dict):
            continue
        kinds = e.get("kinds") or []
        if isinstance(kinds, str):
            kinds = [kinds]
        ks = ",".join(str(x) for x in kinds if str(x).strip())
        payload = e.get("payload") if isinstance(e.get("payload"), dict) else {}
        blob = ""
        if payload:
            try:
                blob = json.dumps(payload, ensure_ascii=False)[:480]
            except (TypeError, ValueError):
                blob = str(payload)[:480]
        cd_lines.append(f"persistence#{i + 1:02d} kinds=[{ks}] {blob}")
    hc = md_for_llm.get("history_context") if isinstance(md_for_llm.get("history_context"), dict) else {}
    cvr = hc.get("confirmed_verdicts") if isinstance(hc.get("confirmed_verdicts"), list) else []
    for i, e in enumerate(cvr[-12:]):
        if not isinstance(e, dict):
            continue
        dk = e.get("decision_kinds") or []
        if isinstance(dk, str):
            dk = [dk]
        if UPDATE_PHYSICS_PARAM not in [str(x).strip() for x in dk if str(x).strip()]:
            continue
        pp = e.get("physics_param_payload") if isinstance(e.get("physics_param_payload"), dict) else {}
        blob = ""
        if pp:
            try:
                blob = json.dumps(pp, ensure_ascii=False)[:480]
            except (TypeError, ValueError):
                blob = str(pp)[:480]
        excerpt = str(e.get("body_excerpt") or "").strip()[:160]
        cd_lines.append(f"history#{i + 1:02d} {blob} excerpt={excerpt}")
    cd_body = "\n".join(f"- {x}" for x in cd_lines) if cd_lines else loc.no_structured_will_items()
    return (
        loc.banner_verdict_skeleton()
        + f"{sk_disp}\n\n"
        + loc.banner_confirmed_decisions()
        + f"{cd_body}\n\n"
    )


def _user_will_priority_block(md_for_llm: Dict[str, Any], loc: FinalVerdictUserLocale) -> str:
    """Step 5 终审：已存意志（persistence_layer）置于 User 消息最前，作为最高权重叙事约束。"""
    pl = md_for_llm.get("persistence_layer") if isinstance(md_for_llm.get("persistence_layer"), dict) else {}
    svs = pl.get("semantic_verdicts") if isinstance(pl.get("semantic_verdicts"), list) else []
    rows: List[str] = []
    for i, e in enumerate(svs[-28:]):
        if not isinstance(e, dict):
            continue
        txt = str(e.get("text") or "").strip()
        if txt:
            rows.append(f"UW-{i + 1:02d}: {txt[:520]}")
    if not rows:
        return (
            loc.banner_user_will()
            + f"{loc.user_will_empty_bullet()}\n\n"
        )
    return (
        loc.banner_user_will()
        + f"{loc.user_will_intro()}"
        + "\n".join(f"- {x}" for x in rows)
        + "\n\n"
    )


def _user_decision_lines(_md_for_llm: Dict[str, Any], selected_cards: List[Dict[str, Any]]) -> List[str]:
    """本回合 Inbox 勾选；已归档意志仅在 _user_will_priority_block 出现，避免重复。"""
    rows: List[str] = []
    for c in selected_cards or []:
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id") or "").strip() or "card"
        title = str(c.get("title") or "").strip()
        dt = str(c.get("displayText") or "").strip()
        blob = " / ".join(x for x in (title, dt) if x)
        if blob:
            rows.append(f"UD-{cid}: {blob[:420]}")
    return rows


def _qualitative_blind_lines(
    blind_work: Dict[str, Any],
    *,
    lock_warning: str | None = None,
    loc: FinalVerdictUserLocale,
) -> List[str]:
    out: List[str] = []
    for idx, vector in enumerate(blind_work.get("work_vectors", []) or []):
        if not isinstance(vector, dict):
            continue
        t = str(vector.get("type") or "—")
        d = str(vector.get("direction") or "—")
        out.append(loc.blind_work_vector(idx + 1, t, d))
    out.append(loc.blind_net_effect(str(blind_work.get("net_effect") or "neutral")))
    morph = blind_work.get("morphing_hints") or []
    if morph:
        out.append(loc.blind_morph_hints("、".join(str(x) for x in morph[:6] if x)))
    if blind_work.get("llm_hint"):
        out.append(loc.blind_llm_hint(str(blind_work.get("llm_hint"))))
    lw = (lock_warning or "").strip()
    if lw:
        out.append(loc.blind_spatial_gate(lw[:180]))
    return out


def _tone_weight_qualitative(*, blind_ratio: float, wangshuai_ratio: float, loc: FinalVerdictUserLocale) -> str:
    if blind_ratio >= 0.65:
        return loc.tone_blind_dominant()
    if wangshuai_ratio >= 0.65:
        return loc.tone_wangshuai_dominant()
    return loc.tone_balanced()


def _mandatory_synthesis_body_without_firewall(
    md_for_llm: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    loc: FinalVerdictUserLocale,
) -> str:
    """供 _build_mandatory_final_synthesis_block 拼装后再统一过防火墙。"""
    pillars = md_for_llm.get("pillars") if isinstance(md_for_llm.get("pillars"), dict) else {}
    points = collect_conflict_matrix_points_for_llm(
        md_for_llm,
        physics_tensor if isinstance(physics_tensor, dict) else {},
    )
    pl = md_for_llm.get("persistence_layer") if isinstance(md_for_llm.get("persistence_layer"), dict) else {}
    svs = pl.get("semantic_verdicts") if isinstance(pl.get("semantic_verdicts"), list) else []
    diag_lines: List[str] = []
    for p in points[:28]:
        if not isinstance(p, dict):
            continue
        kind = str(p.get("kind") or "")
        detail = str(p.get("detail") or "")
        if detail or kind:
            diag_lines.append(f"- [{kind}] {detail}")
    verdict_lines: List[str] = []
    for e in svs[:36]:
        if not isinstance(e, dict):
            continue
        txt = str(e.get("text") or "").strip()
        if txt:
            verdict_lines.append(f"- {txt}")
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    audit_diag = str(pt.get("top_anomaly") or "").strip()
    audit_causal = str(pt.get("causal_reasoning") or "").strip()
    pillar_blob = _trim_prompt_blob(pillars, 1400)
    role = loc.mandatory_synthesis_role()
    return (
        "\n\n======== MANDATORY_FINAL_SYNTHESIS ========\n"
        f"{role}\n"
        f"{loc.mandatory_pillars_title()}{pillar_blob}\n"
        f"{loc.mandatory_conflict_title()}"
        + ("\n".join(diag_lines) if diag_lines else loc.mandatory_conflict_empty())
        + loc.mandatory_semantic_verdicts_title()
        + ("\n".join(verdict_lines) if verdict_lines else loc.mandatory_semantic_verdicts_empty())
        + loc.mandatory_physics_audit_title()
        + f"- top_anomaly: {audit_diag or '—'}\n"
        + f"- causal_reasoning: {audit_causal or '—'}\n"
        + "======== END_MANDATORY_FINAL_SYNTHESIS ========\n\n"
    )


def _build_mandatory_final_synthesis_block(
    md_for_llm: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    loc: FinalVerdictUserLocale,
) -> str:
    """终审语义整合：经语义防火墙剔除浮点字面量后再交给 LLM。"""
    return _semantic_firewall_strip_float_literals(
        _mandatory_synthesis_body_without_firewall(md_for_llm, physics_tensor, loc)
    )


def _trim_prompt_blob(val: Any, max_len: int) -> str:
    """压缩盲派/结构块中非核心 JSON，避免挤占 [Physical Evidence] 注意力预算。"""
    try:
        s = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
    except (TypeError, ValueError):
        s = str(val)
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _incremental_context_v14_block(md_for_llm: Dict[str, Any]) -> str:
    ic = md_for_llm.get("incremental_context_v14") if isinstance(md_for_llm.get("incremental_context_v14"), dict) else {}
    patches = ic.get("logical_patches") if isinstance(ic.get("logical_patches"), list) else []
    if not patches:
        return ""
    lines: List[str] = [
        "[Incremental Context · V14 · Decision_Inbox_Feedback]",
        "",
    ]
    for i, p in enumerate(patches[-24:], start=1):
        if not isinstance(p, dict):
            continue
        try:
            blob = json.dumps(p, ensure_ascii=False)[:900]
        except (TypeError, ValueError):
            blob = str(p)[:900]
        lines.append(f"- Patch#{i}: {blob}")
    lines.extend(
        [
            "- 以上为用户在 Inbox 中的逐步操作所累积的逻辑补丁，本轮终判须与之对齐（因果与措辞）。",
            "",
        ]
    )
    return "\n".join(lines)


def _interaction_log_v14_01_block(md_for_llm: Dict[str, Any]) -> str:
    """Inbox ACK/IGNORE/PATCH → User 末尾 [INTERACTION_LOG]，引导模型调整断言重心。"""
    reg = md_for_llm.get("decision_impact_registry_v14_01") if isinstance(md_for_llm.get("decision_impact_registry_v14_01"), dict) else {}
    events = [e for e in (reg.get("events") or []) if isinstance(e, dict)]
    if not events:
        return ""
    lines: List[str] = ["[INTERACTION_LOG]", ""]
    ignored: List[str] = []
    acked: List[str] = []
    emphasized: List[str] = []
    for e in events[-16:]:
        verb = str(e.get("verb") or "").upper()
        subj = str(e.get("subject") or "").strip()
        note = str(e.get("note") or "").strip()
        nar = str(e.get("narrative") or "").strip()
        if verb == "IGNORE" and subj:
            ignored.append(subj)
            lines.append(f"- IGNORE：已降权或忽略「{subj[:120]}」" + (f"（{note[:160]}）" if note else ""))
        elif verb == "ACK" and subj:
            acked.append(subj)
            lines.append(f"- ACK：已确认「{subj[:120]}」" + (f"（{note[:160]}）" if note else ""))
        elif verb == "PATCH":
            if nar:
                emphasized.append(nar)
            patch_note = note or nar
            if patch_note:
                lines.append(f"- PATCH：{patch_note[:280]}")
            if e.get("sql_patch"):
                lines.append("  （物理 interaction 参数已排队并在终判前静默合并，请以最新物理证据为准。）")
    summary_bits: List[str] = []
    if ignored:
        summary_bits.append(f"对「{' / '.join(ignored[:4])}」相关提醒采取了忽略或降权")
    if emphasized:
        summary_bits.append(f"重点强调：{'；'.join(emphasized[:3])}")
    elif acked:
        summary_bits.append(f"保留确认项：{' / '.join(acked[:4])}")
    if summary_bits:
        lines.append("")
        lines.append(
            "【交互摘要】裁决者"
            + "，".join(summary_bits)
            + "。请据此调整断言重心、风险措辞与证据引用优先级。"
        )
    lines.append("")
    return "\n".join(lines)


def _priority_overwrite_v14_block(md_for_llm: Dict[str, Any]) -> str:
    """V14 统一优先级叙事：Physics 底噪、Plugin 补丁、User Will 蒙版。"""
    po = md_for_llm.get("priority_overwrite_v14") if isinstance(md_for_llm.get("priority_overwrite_v14"), dict) else {}
    pps = po.get("plugin_patch_strength")
    uws = po.get("user_will_mask_strength")
    pps_disp = str(pps) if pps is not None else "auto"
    uws_disp = str(uws) if uws is not None else "auto"
    return (
        "[PRIORITY_OVERWRITE]\n"
        "- Physics：作为底噪恒常存在（不可删除，仅可重加权）。\n"
        f"- Plugin：作为逻辑补丁叠加底噪（当前强度={pps_disp}）。\n"
        f"- User Will：作为全局蒙版决定最终语感与取舍（当前强度={uws_disp}）。\n\n"
    )


def _m5_will_anchor_v14_block(md_for_llm: Dict[str, Any]) -> str:
    m5 = md_for_llm.get("m5_will_anchor_v14") if isinstance(md_for_llm.get("m5_will_anchor_v14"), dict) else {}
    deltas = m5.get("plugin_weight_deltas") if isinstance(m5.get("plugin_weight_deltas"), dict) else {}
    if not deltas:
        return ""
    try:
        blob = json.dumps(deltas, ensure_ascii=False)[:1200]
    except (TypeError, ValueError):
        blob = str(deltas)[:1200]
    last_pid = str(m5.get("last_inbox_plugin_id") or "").strip()
    chk = m5.get("last_inbox_checked")
    tail = f" last_checkbox_plugin={last_pid} checked={chk}" if last_pid else ""
    return f"[M5 Will Anchor · V14 · Inbox]\n- plugin_weight_deltas={blob}{tail}\n\n"


def _iterative_verdict_v14_block(round_n: int, _loc: FinalVerdictUserLocale) -> str:
    if round_n <= 0 or round_n > 3:
        return ""
    if round_n == 1:
        return (
            "[Iterative Verdict · V14 · Round 1]\n"
            "本轮仅输出**结构定性**：格局/体用/风险边界；不写具体岁运应期，不列行动清单。\n\n"
        )
    if round_n == 2:
        return (
            "[Iterative Verdict · V14 · Round 2]\n"
            "本轮输出**因果分析**：必须引用上文 [Incremental Context] 与 [Verified Facts]，"
            "说明冲突→十神→体用之传导；仍避免操作流程式清单。\n\n"
        )
    return (
        "[Iterative Verdict · V14 · Round 3]\n"
        "本轮输出**行动指令**：用「可行 / 禁忌」句式给出明确建议（行/禁），并与 Round1 结构、Round2 因果自洽。\n\n"
    )


def _quantitative_context_v15_system_block(metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> str:
    deity_scores = physics_tensor.get("deity_scores") if isinstance(physics_tensor.get("deity_scores"), dict) else {}
    deity_lines: List[str] = []
    for k, v in sorted(deity_scores.items(), key=lambda kv: float(kv[1] or 0.0), reverse=True)[:6]:
        try:
            fv = float(v or 0.0)
        except (TypeError, ValueError):
            fv = 0.0
        if fv >= 45:
            st = "极度过热/高压"
        elif fv >= 30:
            st = "偏热"
        elif fv <= 8:
            st = "低活性"
        else:
            st = "中性"
        deity_lines.append(f"- {k}: {fv:.2f} (状态: {st})")
    if not deity_lines:
        deity_lines.append("- 未提供 deity_scores")

    meta_pt = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    pp = meta_pt.get("pattern_profile") if isinstance(meta_pt.get("pattern_profile"), dict) else {}
    primary_name = str(pp.get("pattern_name_zh") or pp.get("pattern_kind") or "未定")
    primary_pct = float(pp.get("confidence") or pp.get("primary_ratio") or 0.0)
    alt = pp.get("candidates") if isinstance(pp.get("candidates"), list) else []
    comp_name = "未定"
    comp_pct = 0.0
    if alt and isinstance(alt[0], dict):
        comp_name = str(alt[0].get("name") or "未定")
        try:
            comp_pct = float(alt[0].get("match_score") or 0.0)
        except (TypeError, ValueError):
            comp_pct = 0.0
    pattern_line = f"- 主导格局: {primary_name} [{primary_pct:.0f}%], 竞争格局: {comp_name} [{comp_pct:.0f}%]"

    conflict_points = collect_conflict_matrix_points_for_llm(metadata, physics_tensor)
    penalty = float(meta_pt.get("global_conflict_tension") or 0.0)
    efficiency = max(0.0, min(100.0, (1.0 - penalty) * 100.0))
    sample_conflict = ""
    if conflict_points and isinstance(conflict_points[0], dict):
        sample_conflict = str(conflict_points[0].get("detail") or conflict_points[0].get("kind") or "")
    if sample_conflict:
        physics_line = f"- 由于{sample_conflict}，当前能量传输效率约为 {efficiency:.0f}%"
    else:
        physics_line = f"- 当前能量传输效率约为 {efficiency:.0f}%（由冲突惩罚系数折算）"

    return (
        "[Deity_Absolute_Power]\n"
        + "\n".join(deity_lines)
        + "\n\n[Pattern_Quantization]\n"
        + pattern_line
        + "\n\n[Physics_Formula]\n"
        + physics_line
        + "\n"
    )


def _shadow_buffer_v15_user_block(metadata: Dict[str, Any]) -> str:
    ss = metadata.get("Verdict_Shadow_State") if isinstance(metadata.get("Verdict_Shadow_State"), dict) else {}
    if not ss:
        return ""
    lines = ["[Shadow_Buffer · V15]"]
    ante = str(ss.get("antecedent_v0_5") or "").strip()
    if ante:
        lines.append(f"- shadow_antecedent={ante[:600]}")
    for i, row in enumerate(ss.get("new_fragments") or [], start=1):
        if not isinstance(row, dict):
            continue
        lines.append(f"- New_Fragment#{i}: {str(row.get('fragment') or '')[:180]}")
    lines.append("- 本轮以 (Shadow_State + New_Fragments) 进行语义合并，不重复解析全量历史。")
    lines.append("")
    return "\n".join(lines)


def build_final_verdict_messages(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    selected_cards: List[Dict[str, Any]],
    consensus_history: List[Dict[str, Any]],
    previous_verdict: str,
    lang: str,
    plugin_weights: Dict[str, float] | None = None,
    mandatory_final_synthesis: bool = False,
    prompt_scene: str = SCENE_PROPHET,
    internal_probe_query: str = "",
    iterative_verdict_round: int = 0,
) -> List[Dict[str, str]]:
    """构建终判 LLM 的 system/user 消息列表。"""
    from app.services.helpers.interpretation_helper import merge_interpretation_metadata_for_llm

    _cfg = get_runtime_config()
    _cfg_llm = _cfg.get("llm") if isinstance(_cfg.get("llm"), dict) else {}
    high_reasoning = bool(_cfg_llm.get("is_high_reasoning_mode"))

    prev_scrubbed = scrub_previous_verdict_sql(previous_verdict or "")
    md_for_llm = merge_interpretation_metadata_for_llm(sanitize_metadata_for_verdict_llm(dict(metadata)))
    loc = FinalVerdictUserLocale(lang)
    pt_evidence = shallow_physics_for_llm_evidence(physics_tensor if isinstance(physics_tensor, dict) else {})
    logical_evidence = get_logical_evidence(
        metadata=md_for_llm,
        physics_tensor=pt_evidence,
        selected_cards=selected_cards,
        consensus_history=consensus_history,
        redact_audit_snapshot_abs=not high_reasoning,
    )
    from app.skills.final_verdict_parts.narrative_guard import (
        filter_logical_evidence_for_narrative_factory,
        inject_label_only_semantic_slices,
    )

    logical_evidence = filter_logical_evidence_for_narrative_factory(
        logical_evidence,
        high_reasoning=high_reasoning,
    )
    logical_evidence = inject_label_only_semantic_slices(
        logical_evidence,
        physics_tensor=pt_evidence,
        enabled=not high_reasoning,
    )
    l1_flags = sync_l1_junction_flags_to_meta(metadata=md_for_llm, physics_tensor=physics_tensor)
    blind_work = run_blind_school_plugin(physics_tensor=physics_tensor, metadata=md_for_llm)
    weight_blind = float((plugin_weights or {}).get("classical.blind_school.v1", 0.0) or 0.0)
    weight_wangshuai = float((plugin_weights or {}).get("classical.wangshuai.v1", 0.0) or 0.0)
    total_weight = max(0.0001, weight_blind + weight_wangshuai)
    blind_ratio = weight_blind / total_weight
    wangshuai_ratio = weight_wangshuai / total_weight
    enc_audit = audit_host_guest_vectors(work_vector=blind_work)
    blind_digest = build_blind_school_digest()
    blind_work["encyclopedia_audit"] = enc_audit
    spatial_audit = audit_spatial_sovereignty(work_vector=blind_work)
    blind_work["spatial_audit"] = spatial_audit
    unlock_advice = (blind_work.get("unlock_advice", {}) if isinstance(blind_work, dict) else {}) or {}
    strike_options = list(unlock_advice.get("strategic_strike_options", []) or [])
    structure_v0, final_decision_v0 = build_structure_bundle_with_l2(
        physics_tensor=physics_tensor,
        work_vector=blind_work,
    )
    self_abs = float(structure_v0.get("self_abs", 0.0) or 0.0)
    work_net = float(blind_work.get("work_expectation", 0.0) or 0.0)
    if high_reasoning:
        structure_lines = [
            f"structure.self_abs={structure_v0.get('self_abs', 0.0)}",
            f"structure.root_score={structure_v0.get('root_score', 0.0)}",
            f"structure.hud={_trim_prompt_blob(structure_v0.get('hud', {}), 160)}",
        ]
    else:
        structure_lines = [
            loc.structure_self_abs_redacted(),
            loc.structure_root_redacted(),
            f"structure.hud={_trim_prompt_blob(structure_v0.get('hud', {}), 160)}",
        ]
    for i, c in enumerate(structure_v0.get("candidates", [])):
        if isinstance(c, dict):
            structure_lines.append(
                f"structure.candidate.{i + 1}={c.get('name')}|{c.get('state')}|score={c.get('match_score')}"
            )
    final_decision_v0["strategic_strike_options"] = strike_options
    if bool(unlock_advice.get("is_exit_locked", False)) and strike_options:
        first_action = str((strike_options[0] or {}).get("action") or "")
        strategic = dict(final_decision_v0.get("strategic_advice", {}) or {})
        old_rec = str(strategic.get("recommendation") or "")
        strategic["recommendation"] = loc.strategic_breakthrough_recommendation(first_action, old_rec)
        final_decision_v0["strategic_advice"] = strategic
    school_audit = build_dual_school_audit(final_decision=final_decision_v0, work_vector=blind_work)
    structure_lines.append(
        f"final_decision.primary={final_decision_v0.get('primary_structure')}|"
        f"confidence={final_decision_v0.get('decision_confidence')}"
    )
    structure_lines.append(f"final_decision.stability_risk={final_decision_v0.get('stability_risk')}")
    structure_lines.append(school_audit.get("balance_line", loc.school_balance_fallback()))
    structure_lines.append(school_audit.get("work_line", loc.school_work_fallback()))
    if school_audit.get("has_conflict"):
        structure_lines.append(school_audit.get("logic_conflict_warning", loc.school_logic_conflict_fallback()))
    if self_abs > 10.0:
        structure_lines.append(loc.structure_physics_constraint())
    if work_net < 1.0 and self_abs > 10.0:
        structure_lines.append(loc.structure_blind_work_constraint())
    damage_nodes = (
        (blind_work.get("body_damage_estimation", {}) or {}).get("nodes", []) if isinstance(blind_work, dict) else []
    )
    if any(bool((x or {}).get("critical_stress", False)) for x in damage_nodes if isinstance(x, dict)):
        structure_lines.append(loc.structure_body_damage_constraint())
    knowledge_lines = [
        loc.knowledge_line_host_guest(),
        loc.knowledge_line_body_use(),
        loc.knowledge_line_xufu(),
    ]
    knowledge_lines.extend(
        [f"{loc.knowledge_encyclopedia_prefix(i)}{_trim_prompt_blob(x, 100)}" for i, x in enumerate(blind_digest)]
    )

    system = build_final_verdict_system_message(
        high_reasoning=high_reasoning,
        lang=lang,
        contract_polish_mode=bool(mandatory_final_synthesis),
    )
    scene = str(prompt_scene or SCENE_PROPHET).strip().upper()
    system = f"{system}\n\n{scene_system_directive(scene)}\n{output_purge_directive()}"
    style_mode, style_anchor = build_style_anchor(
        physics_tensor if isinstance(physics_tensor, dict) else {},
        md_for_llm if isinstance(md_for_llm, dict) else {},
    )
    system = f"{system}\n[STYLE_MODE]={style_mode}\n{style_anchor}"
    system = f"{system}\n{_quantitative_context_v15_system_block(md_for_llm, physics_tensor)}"
    blind_skill_block = format_blind_skill_registry_for_prompt(physics_tensor)
    if blind_skill_block:
        system = f"{system}\n{blind_skill_block}"

    logical_evidence = clean_context_lines(logical_evidence)
    structure_lines = clean_context_lines(structure_lines)

    shen_block_lines: List[str] = []
    interp = md_for_llm.get("interpretation") if isinstance(md_for_llm.get("interpretation"), dict) else {}
    shen = interp.get("shensha") if isinstance(interp.get("shensha"), dict) else {}
    for tag in shen.get("active_tags") or []:
        if isinstance(tag, dict):
            shen_block_lines.append(
                loc.shensha_row(str(tag.get("name") or ""), str(tag.get("branch") or "")),
            )
    flow_audit = (physics_tensor.get("meta") or {}).get("energy_flow_audit") if isinstance(physics_tensor.get("meta"), dict) else None
    flow_lines: List[str] = []
    if isinstance(flow_audit, dict):
        for seg in flow_audit.get("segments") or []:
            if not isinstance(seg, dict):
                continue
            st = str(seg.get("state") or "")
            arrow = "→" if st == "FLOWING" else "✗"
            flow_lines.append(
                f"- {seg.get('from')}{loc.causal_segment_generation()}{seg.get('to')} : {st} {arrow}",
            )

    trace_blob = ""
    if high_reasoning:
        it = md_for_llm.get("inference_trace") if isinstance(md_for_llm.get("inference_trace"), dict) else {}
        steps = it.get("steps") if isinstance(it.get("steps"), list) else []
        if steps:
            try:
                payload = {"version": it.get("version", "1.0"), "steps": steps[:160]}
                trace_blob = json.dumps(payload, ensure_ascii=False)
            except (TypeError, ValueError):
                trace_blob = "{}"
            if len(trace_blob) > 14000:
                trace_blob = trace_blob[:14000] + "…"

    snap_for_vf = format_audit_snapshot_inline(
        md_for_llm,
        pt_evidence,
        redact_ten_god_abs=True,
    )
    plugin_out = physics_tensor.get("plugin_outputs") if isinstance(physics_tensor.get("plugin_outputs"), dict) else {}
    evidence_chunks = format_plugin_evidence_chunks(plugin_out, high_reasoning=high_reasoning)

    le_for_vf = filter_logical_evidence_for_narrative_factory(logical_evidence, high_reasoning=False)
    pts_for_vf = collect_conflict_matrix_points_for_llm(
        md_for_llm,
        physics_tensor if isinstance(physics_tensor, dict) else {},
    )
    cm_rows: List[str] = []
    for p in pts_for_vf[:24]:
        if not isinstance(p, dict):
            continue
        kind = str(p.get("kind") or "")
        detail = str(p.get("detail") or "")
        if detail or kind:
            cm_rows.append(loc.chip_conflict_row(kind, detail))

    raw_vf_rows: List[str] = []
    if cm_rows:
        raw_vf_rows.extend(cm_rows)
        raw_vf_rows.append(SYSTEM_FACT_CONFLICT_ANCHOR)
    raw_vf_rows.append(f"{loc.pillar_snapshot_label()}{snap_for_vf}")
    raw_vf_rows.extend(le_for_vf)
    if evidence_chunks:
        raw_vf_rows.extend([f"{loc.plugin_slice_prefix()}{x}" for x in evidence_chunks])
    raw_vf_rows.extend(
        _qualitative_blind_lines(
            blind_work,
            lock_warning=str(spatial_audit.get("lock_warning") or "").strip() or None,
            loc=loc,
        )
    )
    raw_vf_rows.extend(structure_lines)
    raw_vf_rows.extend(knowledge_lines)
    for x in shen_block_lines:
        raw_vf_rows.append(f"{loc.shensha_prefix()}{x}")
    if flow_lines:
        raw_vf_rows.extend(
            [loc.causal_flow_prefix() + _denude_numeric_tokens(x[2:].strip()) for x in flow_lines],
        )
    else:
        raw_vf_rows.append(loc.causal_flow_prefix() + loc.causal_flow_empty())

    vf_numbered, _vf_n = _pack_verified_facts(raw_vf_rows)
    core_seed_block = format_core_logic_seed_user_block(
        metadata=md_for_llm,
        physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else {},
        blind_work=blind_work if isinstance(blind_work, dict) else {},
        l1_flags=l1_flags if isinstance(l1_flags, dict) else {},
        final_decision_v0=final_decision_v0 if isinstance(final_decision_v0, dict) else {},
        school_audit=school_audit if isinstance(school_audit, dict) else {},
    )
    ud_numbered = _user_decision_lines(md_for_llm, selected_cards)

    trace_section = ""
    if trace_blob:
        tb = _denude_numeric_tokens(trace_blob)
        if len(tb) > 9000:
            tb = tb[:9000] + "…"
        trace_section = f"{loc.banner_auxiliary_trace()}{tb}\n"

    will_head = _user_will_priority_block(md_for_llm, loc)
    skeleton_cd = _verdict_skeleton_confirmed_decisions_block(md_for_llm, loc)
    inc_v14 = _incremental_context_v14_block(md_for_llm)
    m5_v14 = _m5_will_anchor_v14_block(md_for_llm)
    iter_v14 = _iterative_verdict_v14_block(int(iterative_verdict_round or 0), loc)
    shadow_v15 = _shadow_buffer_v15_user_block(md_for_llm)
    vf_narrative_rules = loc.vf_narrative_rules(contract_polish=bool(mandatory_final_synthesis))
    user_payload = (
        will_head
        + skeleton_cd
        + inc_v14
        + m5_v14
        + iter_v14
        + shadow_v15
        + vf_narrative_rules
        + "[Verified Facts]\n"
        + ("\n".join(f"- {x}" for x in vf_numbered) if vf_numbered else loc.verified_facts_empty())
        + "\n"
        + core_seed_block
        + trace_section
        + "[User Decisions]\n"
        + ("\n".join(f"- {x}" for x in ud_numbered) if ud_numbered else loc.user_decisions_empty())
        + loc.banner_l1_gate()
        + f"- SHANG_GUAN_JIAN_GUAN={bool(l1_flags.get('SHANG_GUAN_JIAN_GUAN', False))}\n"
        + f"- source={l1_flags.get('source', 'L1_Junction')}\n"
        + loc.banner_narrative_weight()
        + f"- {_tone_weight_qualitative(blind_ratio=blind_ratio, wangshuai_ratio=wangshuai_ratio, loc=loc)}\n"
    )
    meta_pt = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    pp_raw = meta_pt.get("pattern_profile") if isinstance(meta_pt, dict) else None
    pp = pp_raw if isinstance(pp_raw, dict) else {}
    cr_raw = meta_pt.get("causal_routing") if isinstance(meta_pt, dict) else None
    cr = cr_raw if isinstance(cr_raw, dict) else {}
    pk = [str(x) for x in (cr.get("pattern_assertion_keywords") or []) if x]
    pattern_lines = [
        f"- pattern_name_zh={pp.get('pattern_name_zh', '')}",
        f"- sovereignty_priority={bool(pp.get('sovereignty_priority'))}",
        f"- pattern_kind={pp.get('pattern_kind', 'none')}",
    ]
    for line in pp.get("xi_ji_reversal_lines") or []:
        if isinstance(line, str) and line.strip():
            pattern_lines.append(loc.pattern_xiji_line(line))
    imagery_lines = build_data_imagery_mapping_lines(
        physics_tensor if isinstance(physics_tensor, dict) else {},
        md_for_llm if isinstance(md_for_llm, dict) else {},
    )
    semantic_buffer_lines = translate_to_human_terms(meta_pt if isinstance(meta_pt, dict) else {})
    specialized_pattern_lines = build_pattern_specialized_prompt_lines(
        physics_tensor if isinstance(physics_tensor, dict) else {}
    )
    mandatory_stance_lines = [x for x in imagery_lines if str(x).startswith("CRITICAL_WILL_OVERRIDE=")]
    imagery_lines = [x for x in imagery_lines if not str(x).startswith("CRITICAL_WILL_OVERRIDE=")]
    imagery_lines = adapt_lines_for_style(imagery_lines, style_mode)
    semantic_buffer_lines = adapt_lines_for_style(semantic_buffer_lines, style_mode)
    specialized_pattern_lines = adapt_lines_for_style(specialized_pattern_lines, style_mode)
    if mandatory_stance_lines:
        system = (
            f"{system}\n[MANDATORY_STANCE]\n"
            + "\n".join(f"- {str(x)}" for x in mandatory_stance_lines)
            + "\n- 以上意志主权高优先级，必须在【裁断】首句显式体现。"
        )
    learning_section = ""
    hc_llm = md_for_llm.get("history_context") if isinstance(md_for_llm.get("history_context"), dict) else {}
    la_raw = hc_llm.get("learning_annotation") if isinstance(hc_llm.get("learning_annotation"), dict) else {}
    la_entries = la_raw.get("entries") if isinstance(la_raw.get("entries"), list) else []
    if la_entries:
        try:
            la_blob = json.dumps(
                {
                    "schema": la_raw.get("schema"),
                    "last_entries": la_entries[-5:],
                },
                ensure_ascii=False,
            )
        except (TypeError, ValueError):
            la_blob = "{}"
        if len(la_blob) > 3200:
            la_blob = la_blob[:3200] + "…"
        lr_hint = loc.learning_hint(high_reasoning=high_reasoning)
        learning_section = (
            f"{loc.banner_learning_annotation()}{la_blob}\n"
            f"（{lr_hint}）\n"
        )

    synthesis_block = (
        _build_mandatory_final_synthesis_block(md_for_llm, physics_tensor, loc) if mandatory_final_synthesis else ""
    )
    route_probe_block = ""
    if scene == SCENE_ARCHITECT and str(internal_probe_query or "").strip():
        route_probe_block = (
            "\n[INTERNAL_PROBE]\n"
            f"- {str(internal_probe_query).strip()}\n"
            "- 在给出终判前，必须先完成上述结构定性。\n"
        )
    user_payload = (
        user_payload
        + synthesis_block
        + route_probe_block
        + _priority_overwrite_v14_block(md_for_llm)
        + loc.banner_pattern_router()
        + "\n".join(f"- {x}" for x in pattern_lines)
        + loc.banner_pattern_keywords()
        + ("\n".join(f"- {k}" for k in pk) if pk else loc.pattern_keywords_empty())
        + "\n[语义翻译层]\n"
        + ("\n".join(f"- {x}" for x in imagery_lines) if imagery_lines else "- 无显著意象偏置，按中和叙事。")
        + "\n[语义缓冲区]\n"
        + ("\n".join(f"- {x}" for x in semantic_buffer_lines) if semantic_buffer_lines else "- 无显式气场冲突描述。")
        + "\n[格局专项提示词]\n"
        + (
            "\n".join(f"- {x}" for x in specialized_pattern_lines)
            if specialized_pattern_lines
            else "- 当前格局按通用四段式叙事，不做专项偏置。"
        )
        + learning_section
        + "\n"
        + _interaction_log_v14_01_block(md_for_llm)
        + f"Previous_Verdict={prev_scrubbed}\n"
    )
    user = prompt_user_prefix() + user_payload + prompt_user_suffix()
    user = _semantic_firewall_strip_float_literals(user)
    system = _semantic_firewall_strip_float_literals(system)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
