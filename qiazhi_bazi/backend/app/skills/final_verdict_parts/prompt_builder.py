from __future__ import annotations

import json
from typing import Any, Dict, List

from app.plugins.blind_school.core import run_blind_school_plugin
from app.plugins.blind_school.skill_prompt import format_blind_skill_registry_for_prompt
from app.core.rules.junction import sync_l1_junction_flags_to_meta
from app.skills.blind_school_encyclopedia import audit_host_guest_vectors, build_blind_school_digest
from app.skills.dual_school_auditor import build_dual_school_audit
from app.skills.final_verdict_parts.context_trim import clean_context_lines
from app.skills.final_verdict_parts.evidence import get_logical_evidence
from app.skills.spatial_sovereignty import audit_spatial_sovereignty
from app.skills.structure_final_decision import build_structure_final_decision_v0
from app.skills.structure_resolver_v0 import resolve_structure_candidates_v0


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
    """构建终判 LLM 的 system/user 消息列表（原 FinalVerdictSkill._build_prompt）。"""
    lang_hint = "请仅使用中文输出。"
    if (lang or "ZH").upper() == "EN":
        lang_hint = "Please output strictly in English."
    elif (lang or "ZH").upper() == "KO":
        lang_hint = "최종 출력은 반드시 한국어로만 작성하세요."
    logical_evidence = get_logical_evidence(
        metadata=metadata,
        physics_tensor=physics_tensor,
        selected_cards=selected_cards,
        consensus_history=consensus_history,
    )
    l1_flags = sync_l1_junction_flags_to_meta(metadata=metadata, physics_tensor=physics_tensor)
    blind_work = run_blind_school_plugin(physics_tensor=physics_tensor, metadata=metadata)
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
    work_lines = []
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
    work_lines.append(f"解锁.options={strike_options}")
    work_lines.append(f"墓库.locked={blind_work.get('potential_energy_locked', 0.0)}")
    work_lines.append(f"墓库.released={blind_work.get('released_energy', 0.0)}")
    work_lines.append(f"做功.gain={blind_work.get('unlock_gain', 0.0)}")
    work_lines.append(f"做功.risk={blind_work.get('backfire_risk', 0.0)}")
    work_lines.append(f"做功.risk_ratio={blind_work.get('risk_ratio', 0.0)}")
    work_lines.append(f"做功.net_effect={blind_work.get('net_effect', 'neutral')}")
    work_lines.append(f"做功.morphing_hints={','.join(blind_work.get('morphing_hints', []) or [])}")
    work_lines.append(f"做功.body_damage={blind_work.get('body_damage_estimation', {})}")
    work_lines.append(f"做功.hint={blind_work.get('llm_hint', '劳而无功')}")
    structure_v0 = resolve_structure_candidates_v0(
        physics_tensor=physics_tensor,
        work_vector=blind_work,
    )
    self_abs = float(structure_v0.get("self_abs", 0.0) or 0.0)
    work_net = float(blind_work.get("work_expectation", 0.0) or 0.0)
    structure_lines = [
        f"structure.self_abs={structure_v0.get('self_abs', 0.0)}",
        f"structure.root_score={structure_v0.get('root_score', 0.0)}",
        f"structure.hud={structure_v0.get('hud', {})}",
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
    knowledge_lines.extend([f"知识.百科.{i + 1}={x}" for i, x in enumerate(blind_digest)])
    system = (
        "你是 Qiazhi-Bazi 的 FinalVerdictSkill。"
        "你必须每次返回一份全量、唯一、可执行的终判，不允许追加旧内容。"
        "必须引用具体物理数值（十神绝对能量 Abs）作为依据；禁止空泛修辞。"
        "你生成的每一句命理断语，必须能在 [Physical Evidence] 里找到数值或标签支撑。"
        "若与 [User Consensus] 冲突，必须以 [User Consensus] 为准。"
        "输出严格 JSON："
        '{"verdict_body":"markdown","change_log":{"physics_diff":[],"consensus_diff":[],"text_diff_hint":""}}。'
        "change_log 仅写相对上一版的变化；若无上一版则写当前基线要点。"
        "请根据 [盲派硬核证据] 评估日主获取能量效率：做功值为负偏向“劳而无功”，为正偏向“取财有道”。"
        "必须引用 net_effect 做辩证分析；当 backfire_risk 超过 unlock_gain 的50%时，严禁只给单边褒义结论，必须说明代价与震荡。"
        "当出现 [BROKEN_LINK] 时，禁止讨论“库中之物已兑现”，只能讨论“能量淤积/怀才不遇”。"
        "请分析 [Structure Candidates V0]。若出现 QuantumLeap，必须讨论岁运态射风险。"
        "第一段必须先报告 Self_Abs 与 Tomb_State，再进入叙事。"
        "如果 [PHYSICS_CONSTRAINT] 出现，则不得出现“补印比/生扶日主”等建议。"
        "如果 [BLIND_WORK_CONSTRAINT] 出现，则不得给出单边乐观结论。"
        "如果 [BODY_DAMAGE_CONSTRAINT] 出现，必须明确指出体阵营受损节点及其代价，不得轻描淡写。"
        "若出现 [LOGIC_CONFLICT_WARNING]，必须在“裁决共识”段显式写出两派冲突与折中路径。"
        "你必须严格遵循 [Plugin Weight Guidance] 的语气和叙述重心。"
        "严禁跳过 L1_Junction 直接下‘伤官见官’结论；必须先引用 [L1 Junction Flags]。"
        f"{lang_hint}"
    )
    blind_skill_block = format_blind_skill_registry_for_prompt(physics_tensor)
    if blind_skill_block:
        system = f"{system}\n{blind_skill_block}"
    logical_evidence = clean_context_lines(logical_evidence)
    work_lines = clean_context_lines(work_lines)
    structure_lines = clean_context_lines(structure_lines)

    user = (
        "[Physical Evidence]\n"
        + "\n".join(f"- {x}" for x in logical_evidence)
        + "\n[盲派硬核证据]\n"
        + "\n".join(f"- {x}" for x in work_lines)
        + "\n[Structure Candidates V0]\n"
        + "\n".join(f"- {x}" for x in structure_lines)
        + "\n[Knowledge Base Digest]\n"
        + "\n".join(f"- {x}" for x in knowledge_lines)
        + "\n[User Consensus]\n"
        + "\n".join(
            f"- {x}"
            for x in get_logical_evidence(
                metadata={},
                physics_tensor={},
                selected_cards=[],
                consensus_history=consensus_history,
            )
        )
        + "\n[Selected Decisions]\n"
        + "\n".join(
            f"- {x}"
            for x in get_logical_evidence(
                metadata={},
                physics_tensor={},
                selected_cards=selected_cards,
                consensus_history=[],
            )
        )
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
        + "\n"
        f"Previous_Verdict={previous_verdict or ''}\n"
        "请输出三段 markdown 小节：### 核心气象 / ### 裁决共识 / ### 行为指引。"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
