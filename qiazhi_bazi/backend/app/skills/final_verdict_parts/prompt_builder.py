from __future__ import annotations

import json
from typing import Any, Dict, List

from app.core.runtime_config import get_runtime_config
from app.plugins.blind_school.core import run_blind_school_plugin
from app.plugins.blind_school.skill_prompt import format_blind_skill_registry_for_prompt
from app.core.rules.junction import sync_l1_junction_flags_to_meta
from app.prompts.final_verdict_contracts import (
    build_final_verdict_system_message,
    evidence_user_block_heading,
)
from app.skills.final_verdict_parts.metadata_sanitize import (
    sanitize_metadata_for_verdict_llm,
    scrub_previous_verdict_sql,
    shallow_physics_for_llm_evidence,
)
from app.skills.blind_school_encyclopedia import audit_host_guest_vectors, build_blind_school_digest
from app.skills.dual_school_auditor import build_dual_school_audit
from app.skills.final_verdict_parts.context_trim import clean_context_lines
from app.skills.final_verdict_parts.evidence import format_audit_snapshot_inline, get_logical_evidence
from app.skills.final_verdict_parts.evidence_chunking import format_plugin_evidence_chunks
from app.skills.spatial_sovereignty import audit_spatial_sovereignty
from app.skills.structure_final_decision import build_structure_final_decision_v0
from app.skills.structure_resolver_v0 import resolve_structure_candidates_v0


def _trim_prompt_blob(val: Any, max_len: int) -> str:
    """压缩盲派/结构块中非核心 JSON，避免挤占 [Physical Evidence] 注意力预算。"""
    try:
        s = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
    except (TypeError, ValueError):
        s = str(val)
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def build_final_verdict_messages(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    selected_cards: List[Dict[str, Any]],
    consensus_history: List[Dict[str, Any]],
    previous_verdict: str,
    lang: str,
    plugin_weights: Dict[str, float] | None = None,
) -> List[Dict[str, str]]:
    """构建终判 LLM 的 system/user 消息列表。"""
    from app.services.helpers.interpretation_helper import merge_interpretation_metadata_for_llm

    _cfg = get_runtime_config()
    _cfg_llm = _cfg.get("llm") if isinstance(_cfg.get("llm"), dict) else {}
    high_reasoning = bool(_cfg_llm.get("is_high_reasoning_mode"))

    prev_scrubbed = scrub_previous_verdict_sql(previous_verdict or "")
    md_for_llm = merge_interpretation_metadata_for_llm(sanitize_metadata_for_verdict_llm(dict(metadata)))
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
    if blind_ratio >= 0.65:
        tone_style = "语气风格=冷酷、利己、注重成败与资源捕获。"
    elif wangshuai_ratio >= 0.65:
        tone_style = "语气风格=平和、关怀、注重健康与系统平衡。"
    else:
        tone_style = "语气风格=仲裁式，兼顾收益与代价，强调冲突折中。"
    enc_audit = audit_host_guest_vectors(work_vector=blind_work)
    blind_digest = build_blind_school_digest()
    blind_work["encyclopedia_audit"] = enc_audit
    spatial_audit = audit_spatial_sovereignty(work_vector=blind_work)
    blind_work["spatial_audit"] = spatial_audit
    unlock_advice = (blind_work.get("unlock_advice", {}) if isinstance(blind_work, dict) else {}) or {}
    strike_options = list(unlock_advice.get("strategic_strike_options", []) or [])
    work_lines: List[str] = []
    for idx, vector in enumerate(blind_work.get("work_vectors", [])):
        work_lines.append(
            f"做功.{idx + 1}={vector.get('type')}|{vector.get('direction')}|eta={vector.get('eta')}|"
            f"gain={vector.get('unlock_gain')}|risk={vector.get('backfire_risk')}|E={vector.get('expected_work')}"
        )
    work_lines.append(f"做功.total={blind_work.get('work_expectation', 0.0)}")
    work_lines.append(f"百科.gain_vectors={enc_audit.get('gain_vector_count', 0)}")
    if bool(enc_audit.get("anti_subjugation", False)):
        work_lines.append("百科.[ANTI_SUBJUGATION]=HOST_ABS明显低于GUEST_ABS，存在反被制风险")
    work_lines.append(f"空间.gain_paths={spatial_audit.get('gain_path_count', 0)}")
    work_lines.append(f"空间.loss_paths={spatial_audit.get('loss_path_count', 0)}")
    if spatial_audit.get("lock_warning"):
        work_lines.append(f"空间.lock_warning={spatial_audit.get('lock_warning')}")
    work_lines.append(f"解锁.options={_trim_prompt_blob(strike_options, 220)}")
    work_lines.append(f"墓库.locked={blind_work.get('potential_energy_locked', 0.0)}")
    work_lines.append(f"墓库.released={blind_work.get('released_energy', 0.0)}")
    work_lines.append(f"做功.gain={blind_work.get('unlock_gain', 0.0)}")
    work_lines.append(f"做功.risk={blind_work.get('backfire_risk', 0.0)}")
    work_lines.append(f"做功.risk_ratio={blind_work.get('risk_ratio', 0.0)}")
    work_lines.append(f"做功.net_effect={blind_work.get('net_effect', 'neutral')}")
    work_lines.append(f"做功.morphing_hints={','.join(blind_work.get('morphing_hints', []) or [])}")
    work_lines.append(
        f"做功.body_damage={_trim_prompt_blob(blind_work.get('body_damage_estimation', {}), 220)}"
    )
    work_lines.append(f"做功.hint={blind_work.get('llm_hint', '劳而无功')}")
    structure_v0 = resolve_structure_candidates_v0(
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
            "structure.self_abs=(叙事工厂·Self_Abs数值已省略；档位见[Physical Evidence])",
            "structure.root_score=(叙事工厂·数值已省略)",
            f"structure.hud={_trim_prompt_blob(structure_v0.get('hud', {}), 160)}",
        ]
    for i, c in enumerate(structure_v0.get("candidates", [])):
        if isinstance(c, dict):
            structure_lines.append(
                f"structure.candidate.{i + 1}={c.get('name')}|{c.get('state')}|score={c.get('match_score')}"
            )
    final_decision_v0 = build_structure_final_decision_v0(
        structure_candidates_v0=structure_v0,
        work_vector=blind_work,
    )
    final_decision_v0["strategic_strike_options"] = strike_options
    if bool(unlock_advice.get("is_exit_locked", False)) and strike_options:
        first_action = str((strike_options[0] or {}).get("action") or "")
        strategic = dict(final_decision_v0.get("strategic_advice", {}) or {})
        old_rec = str(strategic.get("recommendation") or "")
        strategic["recommendation"] = f"先破局：{first_action}" + (f" 然后：{old_rec}" if old_rec else "")
        final_decision_v0["strategic_advice"] = strategic
    school_audit = build_dual_school_audit(final_decision=final_decision_v0, work_vector=blind_work)
    structure_lines.append(
        f"final_decision.primary={final_decision_v0.get('primary_structure')}|"
        f"confidence={final_decision_v0.get('decision_confidence')}"
    )
    structure_lines.append(f"final_decision.stability_risk={final_decision_v0.get('stability_risk')}")
    structure_lines.append(school_audit.get("balance_line", "[BALANCE_SCHOOL] 未提供"))
    structure_lines.append(school_audit.get("work_line", "[WORK_SCHOOL] 未提供"))
    if school_audit.get("has_conflict"):
        structure_lines.append(school_audit.get("logic_conflict_warning", "[LOGIC_CONFLICT_WARNING]"))
    if self_abs > 10.0:
        structure_lines.append("[PHYSICS_CONSTRAINT] 必须推荐泄耗（克/泄），严禁推荐生扶（印比）")
    if work_net < 1.0 and self_abs > 10.0:
        structure_lines.append("[BLIND_WORK_CONSTRAINT] 必须判定做功效率低下，强调内耗风险与开库/冲动机会")
    damage_nodes = (
        (blind_work.get("body_damage_estimation", {}) or {}).get("nodes", []) if isinstance(blind_work, dict) else []
    )
    if any(bool((x or {}).get("critical_stress", False)) for x in damage_nodes if isinstance(x, dict)):
        structure_lines.append(
            "[BODY_DAMAGE_CONSTRAINT] 存在CRITICAL_STRESS节点，必须说明“贪财坏印/禄神受损”的物理代价"
        )
    knowledge_lines = [
        "知识.主宾=年/月为宾，日/时为主",
        "知识.体用=BODY(比劫印) USE(食伤财官)",
        "知识.虚浮阈值=Self_Abs<1.0且无根 -> 虚浮",
    ]
    knowledge_lines.extend(
        [f"知识.百科.{i + 1}={_trim_prompt_blob(x, 100)}" for i, x in enumerate(blind_digest)]
    )

    system = build_final_verdict_system_message(high_reasoning=high_reasoning, lang=lang)
    blind_skill_block = format_blind_skill_registry_for_prompt(physics_tensor)
    if blind_skill_block:
        system = f"{system}\n{blind_skill_block}"

    logical_evidence = clean_context_lines(logical_evidence)
    work_lines = clean_context_lines(work_lines)
    structure_lines = clean_context_lines(structure_lines)

    shen_block_lines: List[str] = []
    interp = md_for_llm.get("interpretation") if isinstance(md_for_llm.get("interpretation"), dict) else {}
    shen = interp.get("shensha") if isinstance(interp.get("shensha"), dict) else {}
    for tag in shen.get("active_tags") or []:
        if isinstance(tag, dict):
            shen_block_lines.append(f"{tag.get('name')} @支{tag.get('branch')}")
    shen_section = (
        "\n[神煞标签·展示层]\n"
        + (
            "（仅供叙事参考，未参与物理能量计算）\n" + "\n".join(f"- {x}" for x in shen_block_lines)
            if shen_block_lines
            else "- （无）\n"
        )
    )
    flow_audit = (physics_tensor.get("meta") or {}).get("energy_flow_audit") if isinstance(physics_tensor.get("meta"), dict) else None
    flow_lines: List[str] = []
    if isinstance(flow_audit, dict):
        for seg in flow_audit.get("segments") or []:
            if not isinstance(seg, dict):
                continue
            st = str(seg.get("state") or "")
            arrow = "→" if st == "FLOWING" else "✗"
            if high_reasoning:
                flow_lines.append(
                    f"- {seg.get('from')} 生 {seg.get('to')} : {st} {arrow} "
                    f"(from_abs={seg.get('from_abs')}, to_abs={seg.get('to_abs')}, thr={seg.get('threshold')})"
                )
            else:
                flow_lines.append(f"- {seg.get('from')} 生 {seg.get('to')} : {st} {arrow} (能级Abs数值已省略)")
    flow_section = "\n[因果流通链·五行相生]\n" + ("\n".join(flow_lines) if flow_lines else "- （无审计数据）\n")

    trace_section = ""
    if high_reasoning:
        it = md_for_llm.get("inference_trace") if isinstance(md_for_llm.get("inference_trace"), dict) else {}
        steps = it.get("steps") if isinstance(it.get("steps"), list) else []
        if steps:
            try:
                payload = {"version": it.get("version", "1.0"), "steps": steps[:160]}
                blob = json.dumps(payload, ensure_ascii=False)
            except (TypeError, ValueError):
                blob = "{}"
            if len(blob) > 14000:
                blob = blob[:14000] + "…"
            trace_section = f"\n[InferenceTrace·全量]\n{blob}\n"

    audit_snap = format_audit_snapshot_inline(
        md_for_llm,
        pt_evidence,
        redact_ten_god_abs=not high_reasoning,
    )
    plugin_out = physics_tensor.get("plugin_outputs") if isinstance(physics_tensor.get("plugin_outputs"), dict) else {}
    evidence_chunks = format_plugin_evidence_chunks(plugin_out, high_reasoning=high_reasoning)
    evidence_heading = evidence_user_block_heading(high_reasoning=high_reasoning)
    evidence_block = f"\n[{evidence_heading}]\n"
    if evidence_chunks:
        evidence_block += "\n".join(f"- {x}" for x in evidence_chunks) + "\n"
    else:
        evidence_block += "- （各插件暂无结构化 evidence 列表；可忽略本段）\n"

    # EvidenceDedup：物理/共识/裁决项已由单次 get_logical_evidence 合入 [Physical Evidence]，不再重复列出 UserConsensus/Selected 区段。
    user = (
        "[八字元数据快照·全卷锚点]\n"
        + f"- {audit_snap}\n"
        + "[Physical Evidence]\n"
        + "\n".join(f"- {x}" for x in logical_evidence)
        + "\n[EvidenceDedup]\n"
        + "- 共识.* 与 裁决项.* 已包含于上方 [Physical Evidence]；请勿假设存在第二份独立共识列表。\n"
        + evidence_block
        + "\n[盲派硬核证据]\n"
        + "\n".join(f"- {x}" for x in work_lines)
        + "\n[Structure Candidates V0]\n"
        + "\n".join(f"- {x}" for x in structure_lines)
        + "\n[Knowledge Base Digest]\n"
        + "\n".join(f"- {x}" for x in knowledge_lines)
        + shen_section
        + flow_section
        + trace_section
        + "\n[CONFIRMED_DECISION]\n"
        + (
            "confirmed_decisions="
            + json.dumps(
                [
                    {
                        "id": str((c or {}).get("id") or ""),
                        "title": str((c or {}).get("title") or ""),
                        "displayText": str((c or {}).get("displayText") or ""),
                        "is_confirmed": True,
                    }
                    for c in (selected_cards or [])
                    if isinstance(c, dict)
                ],
                ensure_ascii=False,
            )
        )
        + "\n[IMMUTABLE_WILL]\n"
        + (
            "confirmed_decisions="
            + json.dumps(
                [
                    {
                        "id": str((c or {}).get("id") or ""),
                        "is_confirmed": True,
                    }
                    for c in (selected_cards or [])
                    if isinstance(c, dict)
                ],
                ensure_ascii=False,
            )
        )
        + "\n[Plugin Weight Guidance]\n"
        + f"- classical.blind_school.v1={weight_blind:.2f}\n"
        + f"- classical.wangshuai.v1={weight_wangshuai:.2f}\n"
        + f"- blind_ratio={blind_ratio:.2f}\n"
        + f"- wangshuai_ratio={wangshuai_ratio:.2f}\n"
        + f"- {tone_style}\n"
        + "\n[L1 Junction Flags]\n"
        + f"- SHANG_GUAN_JIAN_GUAN={bool(l1_flags.get('SHANG_GUAN_JIAN_GUAN', False))}\n"
        + f"- control_energy={l1_flags.get('control_energy', 0.0)}\n"
        + f"- source={l1_flags.get('source', 'L1_Junction')}\n"
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
            pattern_lines.append(f"- 喜忌反转: {line.strip()}")
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
        lr_hint = "高推理下可更积极对齐历史取向，但仍禁止与插件证据矛盾。" if high_reasoning else "弱模型下仅允许影响语气与折中表述，事实仍以 Evidence 与 plugin.* 为准。"
        learning_section = (
            f"\n[LearningAnnotation·裁决者修正上下文]\n{la_blob}\n"
            f"（{lr_hint}）\n"
        )

    user = (
        user
        + "\n[格局路由 PatternRouter]\n"
        + "\n".join(f"- {x}" for x in pattern_lines)
        + "\n[格局断言关键词]\n"
        + ("\n".join(f"- {k}" for k in pk) if pk else "- （无）\n")
        + learning_section
        + "\n"
        + f"Previous_Verdict={prev_scrubbed}\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
