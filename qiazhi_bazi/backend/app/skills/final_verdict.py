"""FinalVerdictSkill: 基于物理真值生成终判与变更摘要（编排层；Prompt/LLM/解析见 final_verdict_parts）。"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from threading import Lock
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.plugins.conflict_evaluator import evaluate_plugin_conflict
from app.core.runtime_config import get_runtime_config
from app.core.plugins.registry import PluginRegistry
from app.core.rules.junction import sync_l1_junction_flags_to_meta
from app.plugins.blind_school.core import run_blind_school_plugin
from app.skills.base import AuditLog, BaseSkill
from app.skills.blind_school_encyclopedia import audit_host_guest_vectors
from app.skills.dual_school_auditor import build_dual_school_audit
from app.skills.energy_topology_skill import EnergyTopologySkill
from app.skills.final_verdict_parts.constants import (
    IMMUTABLE_WILL_TAGS,
    PRIMARY_WILL_TAGS,
    WILL_PRESERVATION_WINDOW,
)
from app.skills.final_verdict_parts.context_trim import clean_context_lines
from app.skills.final_verdict_parts.evidence import get_logical_evidence as get_logical_evidence_fn
from app.skills.final_verdict_parts.json_extract import (
    coerce_verdict_body_display,
    extract_json_from_llm_text,
    extract_verdict_body_relaxed,
)
from app.skills.final_verdict_parts.narrative_anchors import build_verdict_narrative_chunks
from app.skills.final_verdict_parts.llm_client import run_final_verdict_chat, run_final_verdict_chat_stream
from app.skills.final_verdict_parts.narrative_guard import (
    extract_reasoning_feedback_loop,
    weak_mode_requires_physics_fallback,
)
from app.skills.final_verdict_parts.physics_fallback import build_minimal_verdict_json_from_core_physics
from app.skills.final_verdict_parts.prompt_builder import build_final_verdict_messages
from app.skills.final_verdict_parts.verdict_fingerprint import append_verdict_fingerprint_html_comment
from app.skills.final_verdict_parts.verdict_parse import parse_verdict_anchor_layer, parse_verdict_body_and_changelog
from app.skills.spatial_sovereignty import audit_spatial_sovereignty
from app.logic.brain.hub import BrainHub
from app.logic.brain.semantic_auditor import AuditResult
from app.logic.brain.assertion_tree import build_assertion_tree
from app.logic.patterns.l2_summary import sanitize_pattern_headline_zh
from app.services.helpers.l2_structure_bundle import build_structure_bundle_with_l2

_LOG = logging.getLogger(__name__)


def _json_hint(val: Any, max_len: int = 200) -> str:
    try:
        s = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
    except (TypeError, ValueError):
        s = str(val)
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


__all__ = [
    "IMMUTABLE_WILL_TAGS",
    "PRIMARY_WILL_TAGS",
    "WILL_PRESERVATION_WINDOW",
    "FinalVerdictSkill",
]


class FinalVerdictSkill(BaseSkill):
    _instance: "FinalVerdictSkill | None" = None
    _lock = Lock()
    skill_id = "final_verdict_skill"
    skill_version = "1.0.0"
    rule_version = "final_verdict_rules.v1"

    @classmethod
    def instance(cls) -> "FinalVerdictSkill":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @staticmethod
    def get_logical_evidence(
        *,
        metadata: Dict[str, Any],
        physics_tensor: Dict[str, Any],
        selected_cards: List[Dict[str, Any]],
        consensus_history: List[Dict[str, Any]],
    ) -> List[str]:
        return get_logical_evidence_fn(
            metadata=metadata,
            physics_tensor=physics_tensor,
            selected_cards=selected_cards,
            consensus_history=consensus_history,
        )

    @staticmethod
    def _extract_json(raw: str) -> Dict[str, Any]:
        return extract_json_from_llm_text(raw)

    @staticmethod
    def _build_prompt(
        *,
        metadata: Dict[str, Any],
        physics_tensor: Dict[str, Any],
        selected_cards: List[Dict[str, Any]],
        consensus_history: List[Dict[str, Any]],
        previous_verdict: str,
        lang: str,
        plugin_weights: Dict[str, float] | None = None,
    ) -> List[Dict[str, str]]:
        return build_final_verdict_messages(
            metadata=metadata,
            physics_tensor=physics_tensor,
            selected_cards=selected_cards,
            consensus_history=consensus_history,
            previous_verdict=previous_verdict,
            lang=lang,
            plugin_weights=plugin_weights,
            mandatory_final_synthesis=False,
        )

    @staticmethod
    def _clean_context_lines(lines: List[str], max_tokens: int = 4000) -> List[str]:
        return clean_context_lines(lines, max_tokens=max_tokens)

    @staticmethod
    def _narrow_prompt_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """V12.2 Nano-Prompting：终判提示词只传节点级窄带上下文。"""
        md = metadata if isinstance(metadata, dict) else {}
        points = (((md.get("conflict_matrix") or {}).get("points") or []) if isinstance(md.get("conflict_matrix"), dict) else [])
        first_point = points[0] if isinstance(points, list) and points else {}
        node_line = str((first_point or {}).get("detail") or "局部冲合待复核").strip()
        return {
            "node_context_lines": [f"FACT_NODE:{node_line[:80]}"],
            "conflict_matrix": {"points": [first_point] if isinstance(first_point, dict) else []},
            "verdict_anchor_layer": {"verdict_skeleton": ""},
        }

    def consume(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "metadata": context.get("metadata") or {},
            "physics_tensor": context.get("physics_tensor") or {},
            "selected_cards": list(context.get("selected_cards") or []),
            "consensus_history": list(context.get("consensus_history") or []),
            "previous_verdict": str(context.get("previous_verdict") or ""),
            "previous_logical_evidence": list(context.get("previous_logical_evidence") or []),
            "lang": str(context.get("lang") or "ZH"),
        }

    def produce(self, consumed: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "version_id": "",
            "verdict_body": "",
            "change_log": {"physics_diff": [], "consensus_diff": [], "text_diff_hint": ""},
            "logical_evidence": self.get_logical_evidence(
                metadata=consumed.get("metadata") or {},
                physics_tensor=consumed.get("physics_tensor") or {},
                selected_cards=consumed.get("selected_cards") or [],
                consensus_history=consumed.get("consensus_history") or [],
            ),
        }

    def audit(self, consumed: Dict[str, Any], produced: Dict[str, Any]) -> AuditLog:
        return AuditLog(
            skill_id=self.skill_id,
            skill_version=self.skill_version,
            rule_version=self.rule_version,
            param_version_id=str(
                (((consumed.get("physics_tensor") or {}).get("audit_log") or {}).get("param_version_id") or "unknown")
            ),
            formula_refs=["final_verdict.prompt_json_contract", "final_verdict.logical_evidence_diff"],
            trace={
                "lang": consumed.get("lang", "ZH"),
                "selected_cards_count": len(consumed.get("selected_cards") or []),
                "consensus_count": len(consumed.get("consensus_history") or []),
                "has_previous_verdict": bool(str(consumed.get("previous_verdict") or "").strip()),
                "generated_version_id": produced.get("version_id"),
            },
        )

    async def generate(
        self,
        *,
        metadata: Dict[str, Any],
        physics_tensor: Dict[str, Any],
        selected_cards: List[Dict[str, Any]],
        consensus_history: List[Dict[str, Any]],
        previous_verdict: str = "",
        previous_logical_evidence: List[str] | None = None,
        lang: str = "ZH",
        plugin_weights: Dict[str, float] | None = None,
        regeneration_context: Dict[str, Any] | None = None,
        mandatory_final_synthesis: bool = False,
        stream_tokens: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        _cfg = get_runtime_config().get("llm", {})
        narrative_strategy = (
            str(_cfg.get("narrative_strategy") or "assertion_tree").strip().lower()
            if isinstance(_cfg, dict)
            else "assertion_tree"
        )
        metadata_for_prompt = self._narrow_prompt_metadata(metadata if isinstance(metadata, dict) else {})
        if narrative_strategy == "assertion_tree":
            va = metadata_for_prompt.get("verdict_anchor_layer")
            if isinstance(va, dict) and str(va.get("verdict_skeleton") or "").strip():
                va_new = dict(va)
                va_new["verdict_skeleton"] = ""
                metadata_for_prompt = dict(metadata_for_prompt)
                metadata_for_prompt["verdict_anchor_layer"] = va_new
        messages = build_final_verdict_messages(
            metadata=metadata_for_prompt,
            physics_tensor=physics_tensor,
            selected_cards=selected_cards,
            consensus_history=consensus_history,
            previous_verdict=previous_verdict,
            lang=lang,
            plugin_weights=plugin_weights,
            mandatory_final_synthesis=bool(mandatory_final_synthesis),
        )
        if bool(mandatory_final_synthesis):
            _ps = "final_verdict_mandatory_synthesis"
        elif regeneration_context:
            _ps = "final_verdict_regeneration"
        else:
            _ps = "final_verdict_decision"
        llm_meta: Dict[str, Any] = {"model_name": str(_cfg.get("model") or "LLM"), "prompt_scenario": _ps}
        hub = BrainHub()
        ctx = hub.build_context(
            metadata=metadata if isinstance(metadata, dict) else {},
            physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else {},
            user_intention=str((metadata or {}).get("user_intention") or ""),
        )
        node_state = str((metadata or {}).get("node_state") or (metadata or {}).get("flow_state") or "").strip()
        local_fact_block = hub.build_local_fact_block(metadata if isinstance(metadata, dict) else {})
        vf_tags = list((metadata or {}).get("vf_tags") or []) if isinstance((metadata or {}).get("vf_tags"), list) else []
        bh = (((metadata or {}).get("persistence_layer") or {}).get("brain_hub") or {}) if isinstance((metadata or {}).get("persistence_layer"), dict) else {}
        seeds_matched = [str(x).strip() for x in ((bh or {}).get("seeds_matched") or []) if str(x).strip()]
        sacred_refs = [str(x).strip() for x in ((bh.get("sacred_evidence_refs") or []) if isinstance(bh, dict) else []) if str(x).strip()]
        confirmed_fact_rows = [x for x in ((bh.get("confirmed_facts") or []) if isinstance(bh, dict) else []) if isinstance(x, dict)]
        confirmed_facts = [str((x or {}).get("text") or "").strip() for x in confirmed_fact_rows]
        if confirmed_facts and not any(cf and cf in local_fact_block for cf in confirmed_facts):
            local_fact_block = f"{local_fact_block} | CONFIRMED_FACT:{confirmed_facts[0][:120]}".strip()
        assimilated = len(confirmed_fact_rows) > 0
        lineage_payload = hub.export_lineage(
            seed_short=seeds_matched[0] if seeds_matched else "",
            htn_plan=dict((bh or {}).get("htn_plan") or {}) if isinstance((bh or {}).get("htn_plan"), dict) else {},
        )
        lineage = str(lineage_payload.get("lineage") or "HTN_DRIVEN")
        htn_plan = lineage_payload.get("htn_plan") if isinstance(lineage_payload.get("htn_plan"), dict) else {}
        seeds_matched = [str(x).strip() for x in (lineage_payload.get("seeds_matched") or []) if str(x).strip()]
        bounded_messages = hub.enforce_prompt_boundary(
            local_fact_block=local_fact_block,
            target_node_id="node:final_synthesis",
            vf_tags=[str(x) for x in (vf_tags + sacred_refs)][:3],
        )
        blackboard_refs = hub.build_blackboard_refs(
            local_fact_block=local_fact_block,
            psv_list=ctx.psv_list,
            logical_evidence=sacred_refs + confirmed_facts,
        )
        hub_retry_count = 0
        hub_last_retry_prompt = ""
        hub_audit: Dict[str, Any] = {}
        hub_dissent: Dict[str, Any] | None = None
        raw = ""
        tel: Dict[str, Any] = {}
        if not hub.llm_decision_allowed(node_state):
            llm_meta["gate"] = "LLM_DISABLED_BY_NODE_STATE"
            llm_meta["node_state"] = node_state or "UNKNOWN"
            raw = build_minimal_verdict_json_from_core_physics(physics_tensor, lang=lang)
            hub_audit = {
                "is_passed": True,
                "reason_code": "LIG_NODE_STATE_LOCKED",
                "audit_state": "PASS",
                "feedback_for_llm": "节点非模糊态，LLM 决策已禁用。",
                "matched_rules": ["node_state.lock"],
                "conflict_excerpt": "",
            }
            tel = {}
        elif stream_tokens is not None:
            try:
                pieces: List[str] = []
                async for _piece in run_final_verdict_chat_stream(bounded_messages):
                    pieces.append(_piece)
                    await stream_tokens(_piece)
                raw = "".join(pieces)
            except Exception as exc:
                _LOG.warning("final_verdict_llm_chat_stream_failed: %s", exc)
                raw = ""
                llm_meta["repair_mode"] = "physics_fallback_llm_exception"
        else:
            working_messages = list(bounded_messages)
            for pass_index in range(hub.max_auto_retry + 1):
                try:
                    raw, tel = await run_final_verdict_chat(working_messages)
                except Exception as exc:
                    _LOG.warning("final_verdict_llm_chat_failed: %s", exc)
                    raw = ""
                    tel = {}
                    llm_meta["repair_mode"] = "physics_fallback_llm_exception"
                candidate_obj = extract_json_from_llm_text(raw)
                candidate_body, _candidate_changelog = parse_verdict_body_and_changelog(candidate_obj)
                if not str(candidate_body or "").strip():
                    candidate_body = extract_verdict_body_relaxed(str(raw or ""))
                candidate_refs = hub.extract_candidate_evidence_refs(candidate_obj if isinstance(candidate_obj, dict) else {})
                if confirmed_facts and not any(cf and cf in local_fact_block for cf in confirmed_facts):
                    audit = AuditResult(
                        is_passed=False,
                        reason_code="LIG_FAKE_EVIDENCE_CHAIN",
                        feedback_for_llm="CONFIRMED_FACT 丢失，要求同步神圣证据并重试。",
                        audit_state="REJECT",
                        matched_rules=["blackboard.confirmed_fact_miss"],
                        conflict_excerpt="confirmed_facts_missing_in_local_fact_block",
                    )
                    hub_retry_count = pass_index
                    hub_audit = audit.model_dump()
                    if pass_index >= hub.max_auto_retry:
                        break
                    hub_last_retry_prompt = hub.build_micro_user_message(
                        target_node_id="node:final_synthesis",
                        key_pairs={"reason_code": "LIG_FAKE_EVIDENCE_CHAIN", "feedback": "同步 CONFIRMED_FACT 后重试"},
                    )
                    working_messages = hub.append_auto_retry_prompt(
                        messages,
                        hub_last_retry_prompt,
                        target_node_id="node:final_synthesis",
                    )
                    continue
                ok_chain, missing_refs = hub.verify_evidence_chain(candidate_refs=candidate_refs, blackboard_refs=blackboard_refs)
                if not ok_chain:
                    audit = AuditResult(
                        is_passed=False,
                        reason_code="LIG_FAKE_EVIDENCE_CHAIN",
                        feedback_for_llm=f"证据链不在黑板中：{','.join(missing_refs)}",
                        audit_state="REJECT",
                        matched_rules=["blackboard.evidence_miss"],
                        conflict_excerpt=",".join(missing_refs),
                    )
                else:
                    audit = hub.audit(str(candidate_body or ""), ctx.psv_list)
                hub_retry_count = pass_index
                hub_audit = audit.model_dump()
                if audit.audit_state != "REJECT":
                    break
                if pass_index >= hub.max_auto_retry:
                    settled = hub.conclude(audit=audit, retry_count=pass_index, auto_retry_prompt=hub_last_retry_prompt)
                    hub_audit = settled.audit.model_dump()
                    hub_dissent = settled.dissent_block.model_dump() if settled.dissent_block is not None else None
                    break
                target_node_id = "node:final_synthesis"
                hub_last_retry_prompt = hub.build_micro_user_message(
                    target_node_id=target_node_id,
                    key_pairs={
                        "reason_code": audit.reason_code,
                        "feedback": audit.feedback_for_llm,
                    },
                )
                working_messages = hub.append_auto_retry_prompt(
                    messages,
                    hub_last_retry_prompt,
                    target_node_id=target_node_id,
                )
            if hub_retry_count > 0:
                llm_meta["auto_retry_count"] = hub_retry_count
            if hub_last_retry_prompt:
                llm_meta["last_auto_retry_prompt"] = hub_last_retry_prompt
        if not isinstance(tel, dict):
            tel = {}
        if isinstance(tel, dict):
            if tel.get("elapsed_ms") is not None:
                llm_meta["elapsed_ms"] = tel.get("elapsed_ms")
            if tel.get("approx_tokens") is not None:
                llm_meta["approx_tokens"] = tel.get("approx_tokens")
            usage = tel.get("usage")
            if isinstance(usage, dict) and usage:
                llm_meta["usage"] = usage
        resolved_model_id = (
            str(llm_meta.get("model_name") or "").strip() or str(_cfg.get("model") or "").strip() or "unknown"
        )
        raw_llm_snapshot = str(raw or "")
        if not str(raw or "").strip():
            raw = build_minimal_verdict_json_from_core_physics(physics_tensor, lang=lang)
            llm_meta["repair_mode"] = llm_meta.get("repair_mode") or "physics_fallback_empty_response"
        obj = extract_json_from_llm_text(raw)
        verdict_body, change_log = parse_verdict_body_and_changelog(obj)
        if not str(verdict_body or "").strip():
            recovered = extract_verdict_body_relaxed(str(raw or ""))
            if str(recovered or "").strip():
                verdict_body = recovered.strip()
                llm_meta["repair_mode"] = llm_meta.get("repair_mode") or "regex_verdict_body_recovery"
        if not str(verdict_body or "").strip():
            raw = build_minimal_verdict_json_from_core_physics(physics_tensor, lang=lang)
            obj = extract_json_from_llm_text(raw)
            verdict_body, change_log = parse_verdict_body_and_changelog(obj)
            llm_meta["repair_mode"] = "physics_fallback_empty_verdict_body"

        logical_evidence = self.get_logical_evidence(
            metadata=metadata,
            physics_tensor=physics_tensor,
            selected_cards=selected_cards,
            consensus_history=consensus_history,
        )
        if confirmed_facts:
            logical_evidence.insert(0, f"神圣证据.CONFIRMED_FACT={' | '.join([x for x in confirmed_facts if x][:3])}")
        l1_flags = sync_l1_junction_flags_to_meta(metadata=metadata, physics_tensor=physics_tensor)
        blind_work = run_blind_school_plugin(physics_tensor=physics_tensor, metadata=metadata)
        enc_audit = audit_host_guest_vectors(work_vector=blind_work)
        blind_work["encyclopedia_audit"] = enc_audit
        spatial_audit = audit_spatial_sovereignty(work_vector=blind_work)
        blind_work["spatial_audit"] = spatial_audit
        unlock_advice = (blind_work.get("unlock_advice", {}) if isinstance(blind_work, dict) else {}) or {}
        strike_options = list(unlock_advice.get("strategic_strike_options", []) or [])
        topology = EnergyTopologySkill().produce({"metadata": metadata, "physics_tensor": physics_tensor})
        structure_v0, final_decision_v0 = build_structure_bundle_with_l2(
            physics_tensor=physics_tensor,
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
        enabled_plugins = list((((physics_tensor or {}).get("meta") or {}).get("enabled_plugins") or []))
        registry = PluginRegistry()
        verdict_plugin_outputs = registry.run_hook(
            hook="on_verdict_ready",
            enabled_plugins=enabled_plugins,
            context={
                "metadata": metadata,
                "work_vector": blind_work,
                "structure_final_decision": final_decision_v0,
            },
        )
        conflict_report = evaluate_plugin_conflict(
            plugin_outputs=verdict_plugin_outputs,
            plugin_weights=plugin_weights or {},
        )
        final_decision_v0["plugin_conflict_report"] = conflict_report
        if verdict_plugin_outputs:
            logical_evidence.append(f"插件.verdict_ready={list(verdict_plugin_outputs.keys())}")
        logical_evidence.append(f"插件.conflict_zone={conflict_report.get('zone', 'BLUE')}")
        logical_evidence.append(f"插件.tension_level={conflict_report.get('tension_level', 0.0)}")
        logical_evidence.append(f"L1_Junction.SHANG_GUAN_JIAN_GUAN={bool(l1_flags.get('SHANG_GUAN_JIAN_GUAN', False))}")
        logical_evidence.append(f"L1_Junction.control_energy={l1_flags.get('control_energy', 0.0)}")
        climate_trace = (
            (((physics_tensor.get("meta", {}) or {}).get("climate_adjustment", {})) if isinstance(physics_tensor, dict) else {})
            or {}
        )
        logical_evidence.extend(
            [
                f"[Tomb State: {'Released' if float(blind_work.get('released_energy', 0.0) or 0.0) > 0 else 'Locked'}] Abs_Locked: {blind_work.get('potential_energy_locked', 0.0)}",
                f"[Tomb State: Released] Unlock_Gain: +{blind_work.get('unlock_gain', 0.0)} | Risk: -{blind_work.get('backfire_risk', 0.0)} | Net: {blind_work.get('work_expectation', 0.0)}",
                f"Climate.enabled={climate_trace.get('enabled', False)}",
                f"Climate.opposing={climate_trace.get('opposing_element', 'unknown')} factor={((climate_trace.get('factors', {}) or {}).get(climate_trace.get('opposing_element', ''), 1.0))}",
                f"做功.total={blind_work.get('work_expectation', 0.0)}",
                f"做功.morphing_hints={','.join(blind_work.get('morphing_hints', []) or [])}",
                f"做功.body_damage={_json_hint(blind_work.get('body_damage_estimation', {}), 200)}",
                f"做功.hint={blind_work.get('llm_hint', '劳而无功')}",
                f"格局L2.hud={_json_hint(structure_v0.get('hud', {}), 200)}",
                f"Topology.edges={len(topology.get('edges', []))}",
                f"格局终审L2.primary={final_decision_v0.get('primary_structure')}",
                f"格局终审L2.risk={final_decision_v0.get('stability_risk')}",
                f"空间.gain_paths={spatial_audit.get('gain_path_count', 0)}",
                f"空间.loss_paths={spatial_audit.get('loss_path_count', 0)}",
                f"百科.gain_vectors={enc_audit.get('gain_vector_count', 0)}",
                f"解锁.options={_json_hint(strike_options, 220)}",
                school_audit.get("balance_line", "[BALANCE_SCHOOL] 未提供"),
                school_audit.get("work_line", "[WORK_SCHOOL] 未提供"),
            ]
        )
        if bool(enc_audit.get("anti_subjugation", False)):
            logical_evidence.append("百科.[ANTI_SUBJUGATION]=HOST_ABS明显低于GUEST_ABS，存在反被制风险。")
        if spatial_audit.get("lock_warning"):
            logical_evidence.append(f"空间.lock_warning={spatial_audit.get('lock_warning')}")
        if school_audit.get("has_conflict"):
            logical_evidence.append(school_audit.get("logic_conflict_warning", "[LOGIC_CONFLICT_WARNING]"))
        conflict_points = (((metadata or {}).get("conflict_matrix") or {}).get("points") or [])
        if any("子午冲" in str((p or {}).get("detail", "")) for p in conflict_points if isinstance(p, dict)):
            logical_evidence.append("子午冲审计=因大运子水克流年午火，导致[食神做功链路]物理断裂，身强无依内耗风险升高。")
        prev_evidence = [str(x).strip() for x in (previous_logical_evidence or []) if str(x).strip()]
        prev_map: Dict[str, str] = {}
        curr_map: Dict[str, str] = {}
        for line in prev_evidence:
            if "=" in line:
                k, v = line.split("=", 1)
                prev_map[k.strip()] = v.strip()
        for line in logical_evidence:
            if "=" in line:
                k, v = line.split("=", 1)
                curr_map[k.strip()] = v.strip()
        physics_diff: List[str] = []
        consensus_diff: List[str] = []
        for k, v in curr_map.items():
            old = prev_map.get(k)
            if old is None:
                continue
            if old != v and (k.startswith("十神.") or k.startswith("根气.")):
                physics_diff.append(f"{k}: {old} -> {v}")
            if old != v and k.startswith("共识."):
                consensus_diff.append(f"{k}: {old} -> {v}")
        for k, v in curr_map.items():
            if k.startswith("共识.") and k not in prev_map:
                consensus_diff.append(f"新增 {k}: {v}")

        if not change_log.get("physics_diff"):
            change_log["physics_diff"] = physics_diff[:6]
        if not change_log.get("consensus_diff"):
            change_log["consensus_diff"] = consensus_diff[:6]
        if not change_log.get("text_diff_hint"):
            if previous_verdict.strip():
                change_log["text_diff_hint"] = "本版断言已全量重写，并按最新物理证据与共识重新对齐。"
            else:
                change_log["text_diff_hint"] = "首版断言生成完成，后续将基于证据差分持续收敛。"
        if not verdict_body:
            verdict_body = (
                "### 核心气象\n"
                "当前断言已按最新物理张量重写。\n\n"
                "### 裁决共识\n"
                "系统仅基于已确认共识与最新十神数值生成本版结论。\n\n"
                "### 行为指引\n"
                "优先执行结构修正，再推进节奏性动作。"
            )
        if not change_log.get("physics_diff") and not change_log.get("consensus_diff"):
            change_log["text_diff_hint"] = change_log.get("text_diff_hint") or "已生成全量重写终判（非追加模式）。"
        verdict_body = coerce_verdict_body_display(str(verdict_body or ""))
        reasoning_fb = extract_reasoning_feedback_loop(obj)
        version_id = datetime.utcnow().strftime("v2.%m%d%H%M%S")
        md_for_anchors = metadata if isinstance(metadata, dict) else {}
        narrative_chunks = build_verdict_narrative_chunks(verdict_body, md_for_anchors)
        anchor_layer_dict = parse_verdict_anchor_layer(
            obj,
            verdict_body=verdict_body,
            version_id=version_id,
            metadata=md_for_anchors,
        )
        high_reasoning = bool(isinstance(_cfg, dict) and _cfg.get("is_high_reasoning_mode"))
        if weak_mode_requires_physics_fallback(
            {"assertions": anchor_layer_dict.get("assertions")},
            high_reasoning=high_reasoning,
        ):
            raw = build_minimal_verdict_json_from_core_physics(physics_tensor, lang=lang)
            obj = extract_json_from_llm_text(raw)
            verdict_body, change_log = parse_verdict_body_and_changelog(obj)
            if not str(verdict_body or "").strip():
                raw = build_minimal_verdict_json_from_core_physics(physics_tensor, lang=lang)
                obj = extract_json_from_llm_text(raw)
                verdict_body, change_log = parse_verdict_body_and_changelog(obj)
            if not str(verdict_body or "").strip():
                recovered_wm = extract_verdict_body_relaxed(raw_llm_snapshot)
                if str(recovered_wm or "").strip():
                    verdict_body = recovered_wm.strip()
                    llm_meta["repair_mode"] = llm_meta.get("repair_mode") or "regex_verdict_body_recovery"
            verdict_body = coerce_verdict_body_display(str(verdict_body or ""))
            narrative_chunks = build_verdict_narrative_chunks(verdict_body, md_for_anchors)
            anchor_layer_dict = parse_verdict_anchor_layer(
                obj,
                verdict_body=verdict_body,
                version_id=version_id,
                metadata=md_for_anchors,
            )
            llm_meta["repair_mode"] = llm_meta.get("repair_mode") or "physics_fallback_narrative_guard"
        fv_from_json = ""
        if isinstance(obj, dict) and obj.get("final_verdict") is not None:
            fv_from_json = coerce_verdict_body_display(str(obj.get("final_verdict") or ""))
        clean_body_for_meta = coerce_verdict_body_display(str(verdict_body or "").strip())
        if isinstance(anchor_layer_dict, dict):
            anchor_layer_dict["final_verdict"] = (fv_from_json or clean_body_for_meta)[:12000]
            if narrative_strategy == "assertion_tree":
                base_assertions = anchor_layer_dict.get("assertions") if isinstance(anchor_layer_dict.get("assertions"), list) else []
                sacred_assertions = [
                    {
                        "assertion_id": f"sacred-{i}",
                        "text": str((row or {}).get("text") or "用户确认事实").strip(),
                        "evidence_refs": ["brain_hub.confirmed_fact", "arbiter_bias.user_intention_id"],
                    }
                    for i, row in enumerate(confirmed_fact_rows)
                ]
                anchor_layer_dict["assertion_tree"] = build_assertion_tree(
                    version_id=version_id,
                    assertions=sacred_assertions + base_assertions,
                    psv_list=ctx.psv_list,
                    user_intention_id=str(ctx.tri.arbiter_bias.user_intention_id or ""),
                )
        assertions_for_fp = (
            anchor_layer_dict.get("assertions") if isinstance(anchor_layer_dict.get("assertions"), list) else None
        )
        verdict_body = append_verdict_fingerprint_html_comment(
            verdict_body,
            physics_tensor=physics_tensor,
            metadata=md_for_anchors,
            assertions=assertions_for_fp,
        )
        reg_in = regeneration_context if isinstance(regeneration_context, dict) else {}
        reason = str(reg_in.get("reason") or "").strip()
        trigger = str(reg_in.get("trigger") or "").strip()
        prev_vid = str(reg_in.get("previous_version_id") or "").strip()
        history_context_patch: Dict[str, Any] = {
            "verdict_model_stamps": [
                {
                    "occurred_at": datetime.utcnow().isoformat(),
                    "model_id": resolved_model_id,
                    "version_id": version_id,
                }
            ]
        }
        if (reason or trigger) and prev_vid:
            history_context_patch["regeneration_events"] = [
                {
                    "occurred_at": datetime.utcnow().isoformat(),
                    "reason": reason or "未说明",
                    "trigger": trigger or "unspecified",
                    "model_id": resolved_model_id,
                    "version_id": version_id,
                    "previous_version_id": prev_vid,
                }
            ]
        if (reason or trigger) and (prev_vid or str(previous_verdict or "").strip()):
            prev_anchor = md_for_anchors.get("verdict_anchor_layer") if isinstance(md_for_anchors.get("verdict_anchor_layer"), dict) else {}
            prev_rows = prev_anchor.get("assertions") if isinstance(prev_anchor.get("assertions"), list) else []
            prev_ids = [str((x or {}).get("assertion_id") or "") for x in prev_rows if isinstance(x, dict)][:48]
            new_rows = anchor_layer_dict.get("assertions") if isinstance(anchor_layer_dict.get("assertions"), list) else []
            new_ids = [str((x or {}).get("assertion_id") or "") for x in new_rows if isinstance(x, dict)][:48]
            history_context_patch["learning_annotation"] = {
                "schema": "learning_annotation.v1",
                "entries": [
                    {
                        "occurred_at": datetime.utcnow().isoformat(),
                        "kind": "regenerate_or_revision",
                        "version_id": version_id,
                        "model_id": resolved_model_id,
                        "previous_version_id": prev_vid,
                        "reason": reason or "",
                        "trigger": trigger or "",
                        "diff": {
                            "previous_verdict_excerpt": str(previous_verdict or "")[:1600],
                            "new_verdict_excerpt": str(verdict_body or "")[:1600],
                            "previous_assertion_ids": prev_ids,
                            "new_assertion_ids": new_ids,
                        },
                    }
                ],
            }
        metadata_memory_patch: Dict[str, Any] = {
            "verdict_anchor_layer": anchor_layer_dict,
            "memory_schema_version": "2.0",
            "history_context": history_context_patch,
        }
        if reasoning_fb is not None:
            metadata_memory_patch["reasoning_feedback_loop"] = reasoning_fb
        confirmed_decisions = [
            {
                "id": str((c or {}).get("id") or ""),
                "label": str((c or {}).get("displayText") or (c or {}).get("title") or ""),
                "is_confirmed": True,
                "confirmed_at": datetime.utcnow().isoformat(),
            }
            for c in (selected_cards or [])
            if isinstance(c, dict)
        ]
        consumed = self.consume(
            {
                "metadata": metadata,
                "physics_tensor": physics_tensor,
                "selected_cards": selected_cards,
                "consensus_history": consensus_history,
                "previous_verdict": previous_verdict,
                "previous_logical_evidence": previous_logical_evidence or [],
                "lang": lang,
            }
        )
        _pmeta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
        _hit = str(_pmeta.get("hit_pattern_name") or _pmeta.get("l2_pattern_result_summary_v1") or "").strip()
        hit_pattern_name = sanitize_pattern_headline_zh(_hit if _hit else "常规格")
        produced = {
            "version_id": version_id,
            "verdict_body": verdict_body,
            "change_log": change_log,
            "logical_evidence": logical_evidence,
            "work_vector": blind_work,
            "topology_graph_v1": topology,
            "hit_pattern_name": hit_pattern_name,
            "structure_candidates_v0": structure_v0,
            "structure_final_decision_v0": final_decision_v0,
            "plugin_outputs_verdict_ready": verdict_plugin_outputs,
            "plugin_conflict_report": conflict_report,
            "l1_junction_flags": l1_flags,
            "narrative_chunks": narrative_chunks,
            "metadata_memory_patch": metadata_memory_patch,
            "brain_hub": {
                "psv": [s.model_dump() for s in ctx.psv_list],
                "audit": hub_audit or {"reason_code": "PASS", "audit_state": "PASS", "is_passed": True},
                "retry_count": hub_retry_count,
                "dissent_block": hub_dissent,
                "lineage": lineage,
                "seeds_matched": seeds_matched,
                "htn_plan": htn_plan,
                "assimilated": assimilated,
            },
            "narrative_strategy": narrative_strategy,
            "assertion_tree": anchor_layer_dict.get("assertion_tree") if isinstance(anchor_layer_dict, dict) else {},
        }
        audit_log = self.audit(consumed, produced).model_dump()
        safe_messages = [
            {"role": str((m or {}).get("role") or ""), "content": str((m or {}).get("content") or "")[:300]}
            for m in bounded_messages
        ]
        return {
            "version_id": version_id,
            "verdict_body": verdict_body,
            "change_log": change_log,
            "logical_evidence": logical_evidence,
            "work_vector": blind_work,
            "topology_graph_v1": topology,
            "hit_pattern_name": hit_pattern_name,
            "structure_candidates_v0": structure_v0,
            "structure_final_decision_v0": final_decision_v0,
            "plugin_outputs_verdict_ready": verdict_plugin_outputs,
            "plugin_conflict_report": conflict_report,
            "l1_junction_flags": l1_flags,
            "audit_log": audit_log,
            "confirmed_decisions": confirmed_decisions,
            "raw": raw,
            "llm_request_messages": safe_messages,
            "llm_raw_response": raw,
            "llm_meta": llm_meta,
            "narrative_chunks": narrative_chunks,
            "metadata_memory_patch": metadata_memory_patch,
            "brain_hub": produced.get("brain_hub"),
            "narrative_strategy": narrative_strategy,
            "assertion_tree": produced.get("assertion_tree") or {},
        }
