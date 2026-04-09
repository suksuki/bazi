"""FinalVerdictSkill: 基于物理真值生成终判与变更摘要。"""
from __future__ import annotations

import json
import re
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List

from app.plugins.blind_school.core import run_blind_school_plugin
from app.core.plugins.conflict_evaluator import evaluate_plugin_conflict
from app.core.plugins.registry import PluginRegistry
from app.core.rules.junction import detect_universal_flags
from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient
from app.skills.base import AuditLog, BaseSkill
from app.skills.blind_school_encyclopedia import audit_host_guest_vectors, build_blind_school_digest
from app.skills.dual_school_auditor import build_dual_school_audit
from app.skills.energy_topology_skill import EnergyTopologySkill
from app.skills.spatial_sovereignty import audit_spatial_sovereignty
from app.skills.structure_final_decision import build_structure_final_decision_v0
from app.skills.structure_resolver_v0 import resolve_structure_candidates_v0

PRIMARY_WILL_TAGS = ("[CONFIRMED_DECISION]", "confirmed_decisions")
WILL_PRESERVATION_WINDOW = 48
IMMUTABLE_WILL_TAGS = ("IMMUTABLE_WILL", '"is_confirmed": true', "is_confirmed: true")


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
    def _strength_qualifier(abs_energy: float) -> str:
        if abs_energy < 0.5:
            return "熄灭/虚存"
        if abs_energy < 2.0:
            return "衰微/无力"
        if abs_energy < 5.0:
            return "中和/可用"
        return "强旺/执拗"

    @staticmethod
    def get_logical_evidence(
        *,
        metadata: Dict[str, Any],
        physics_tensor: Dict[str, Any],
        selected_cards: List[Dict[str, Any]],
        consensus_history: List[Dict[str, Any]],
    ) -> List[str]:
        """
        元数据投影：把复杂 JSON 脱水为 Key-Value 证据行，便于 LLM 读取。
        """
        lines: List[str] = []
        pillars = ((metadata or {}).get("pillars", {}) if isinstance(metadata, dict) else {}) or {}
        if pillars:
            y = pillars.get("year", {})
            m = pillars.get("month", {})
            d = pillars.get("day", {})
            h = pillars.get("hour", {})
            lines.append(f"四柱={y.get('stem','?')}{y.get('branch','?')}/{m.get('stem','?')}{m.get('branch','?')}/{d.get('stem','?')}{d.get('branch','?')}/{h.get('stem','?')}{h.get('branch','?')}")
        if isinstance(metadata, dict) and metadata.get("gender"):
            lines.append(f"性别={metadata.get('gender')}")
        deity_axes = (physics_tensor.get("deity_energy_axes", {}) if isinstance(physics_tensor, dict) else {}) or {}
        climate_trace = (((physics_tensor.get("meta", {}) or {}).get("climate_adjustment", {})) if isinstance(physics_tensor, dict) else {}) or {}
        deity_before = (climate_trace.get("deity_before", {}) if isinstance(climate_trace, dict) else {}) or {}
        deity_after = (climate_trace.get("deity_after", {}) if isinstance(climate_trace, dict) else {}) or {}
        for deity in ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]:
            axis = deity_axes.get(deity) if isinstance(deity_axes, dict) else None
            if isinstance(axis, dict):
                abs_energy = float(axis.get("absolute_energy", 0.0) or 0.0)
                qualifier = FinalVerdictSkill._strength_qualifier(abs_energy)
                before = float(deity_before.get(deity, 0.0) or 0.0)
                after = float(deity_after.get(deity, abs_energy) or abs_energy)
                factor = (after / before) if before > 0 else 1.0
                lines.append(
                    f"十神.{deity}.Abs={abs_energy:.2f} "
                    f"(Before:{before:.2f}, Climate_Factor:{factor:.2f}) [状态:{qualifier}]"
                )
        root_check = (((physics_tensor.get("audit_log", {}) or {}).get("trace", {}) or {}).get("root_check", {}) if isinstance(physics_tensor, dict) else {}) or {}
        if isinstance(root_check, dict):
            lines.append(f"根气.no_root={bool(root_check.get('no_root', False))}")
            lines.append(f"根气.decay_factor={root_check.get('decay_factor', 'N/A')}")
            lines.append(f"根气.record={str(root_check.get('record', ''))[:180]}")
        for i, c in enumerate(consensus_history or []):
            if isinstance(c, dict):
                lines.append(
                    f"共识.{i+1}={c.get('decision_key','')}:{c.get('confirmed_value','?')}|{str(c.get('reasoning',''))[:80]}"
                )
        for i, s in enumerate(selected_cards or []):
            if isinstance(s, dict):
                lines.append(f"裁决项.{i+1}={s.get('cardType','conflict')}|{s.get('displayText') or s.get('title') or ''}")
        return lines

    @staticmethod
    def _extract_json(raw: str) -> Dict[str, Any]:
        text = (raw or "").strip()
        if not text:
            return {}
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return {}
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}

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
        lang_hint = "请仅使用中文输出。"
        if (lang or "ZH").upper() == "EN":
            lang_hint = "Please output strictly in English."
        elif (lang or "ZH").upper() == "KO":
            lang_hint = "최종 출력은 반드시 한국어로만 작성하세요."
        logical_evidence = FinalVerdictSkill.get_logical_evidence(
            metadata=metadata,
            physics_tensor=physics_tensor,
            selected_cards=selected_cards,
            consensus_history=consensus_history,
        )
        l1_flags = detect_universal_flags(metadata=metadata, physics_tensor=physics_tensor)
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
                f"做功.{idx+1}={vector.get('type')}|{vector.get('direction')}|eta={vector.get('eta')}|gain={vector.get('unlock_gain')}|risk={vector.get('backfire_risk')}|E={vector.get('expected_work')}"
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
                    f"structure.candidate.{i+1}={c.get('name')}|{c.get('state')}|score={c.get('match_score')}"
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
            f"final_decision.primary={final_decision_v0.get('primary_structure')}|confidence={final_decision_v0.get('decision_confidence')}"
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
        damage_nodes = ((blind_work.get("body_damage_estimation", {}) or {}).get("nodes", []) if isinstance(blind_work, dict) else [])
        if any(bool((x or {}).get("critical_stress", False)) for x in damage_nodes if isinstance(x, dict)):
            structure_lines.append("[BODY_DAMAGE_CONSTRAINT] 存在CRITICAL_STRESS节点，必须说明“贪财坏印/禄神受损”的物理代价")
        knowledge_lines = [
            "知识.主宾=年/月为宾，日/时为主",
            "知识.体用=BODY(比劫印) USE(食伤财官)",
            "知识.虚浮阈值=Self_Abs<1.0且无根 -> 虚浮",
        ]
        knowledge_lines.extend([f"知识.百科.{i+1}={x}" for i, x in enumerate(blind_digest)])
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
        logical_evidence = FinalVerdictSkill._clean_context_lines(logical_evidence)
        work_lines = FinalVerdictSkill._clean_context_lines(work_lines)
        structure_lines = FinalVerdictSkill._clean_context_lines(structure_lines)

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
            + "\n".join(f"- {x}" for x in FinalVerdictSkill.get_logical_evidence(
                metadata={},
                physics_tensor={},
                selected_cards=[],
                consensus_history=consensus_history,
            ))
            + "\n[Selected Decisions]\n"
            + "\n".join(f"- {x}" for x in FinalVerdictSkill.get_logical_evidence(
                metadata={},
                physics_tensor={},
                selected_cards=selected_cards,
                consensus_history=[],
            ))
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

    @staticmethod
    def _clean_context_lines(lines: List[str], max_tokens: int = 4000) -> List[str]:
        """
        ContextCleaner:
        - 避免逻辑证据无限膨胀导致断言中断
        - 超阈值后仅保留核心 L1/L2 旗标 + 最近片段
        """
        cleaned = [str(x).strip() for x in (lines or []) if str(x).strip()]
        ranked: List[tuple[int, str]] = []
        for x in cleaned:
            priority = 0
            if any(tag in x for tag in PRIMARY_WILL_TAGS):
                priority = 2_147_483_647
            if any(tag in x for tag in IMMUTABLE_WILL_TAGS):
                priority = 2_147_483_647
            elif (
                "L1_Junction" in x
                or "SHANG_GUAN_JIAN_GUAN" in x
                or "插件.conflict_zone" in x
                or "插件.tension_level" in x
                or "四柱=" in x
            ):
                priority = 200
            ranked.append((priority, x))
        primary_will_lines = [x for p, x in ranked if p == 2_147_483_647]
        if len(primary_will_lines) > WILL_PRESERVATION_WINDOW:
            primary_will_lines = primary_will_lines[-WILL_PRESERVATION_WINDOW:]
        approx_tokens = sum(max(1, len(x) // 2) for x in cleaned)
        if approx_tokens <= max_tokens:
            merged_full: List[str] = []
            seen_full = set()
            for item in [*primary_will_lines, *cleaned]:
                if item in seen_full:
                    continue
                seen_full.add(item)
                merged_full.append(item)
            return merged_full
        keep_prefix = [x for p, x in ranked if p >= 200 and p < 2_147_483_647][:18]
        tail = cleaned[-60:]
        merged: List[str] = []
        seen = set()
        for item in [*primary_will_lines, *keep_prefix, *tail]:
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
        return merged

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
        # 非流式协议适配：保持与 generate 一致的返回骨架。
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
    ) -> Dict[str, Any]:
        cfg = get_runtime_config().get("llm", {})
        client = QwenClient(
            base_url=cfg.get("base_url"),
            api_key=cfg.get("api_key"),
            model=cfg.get("model") or None,
        )
        prompt = self._build_prompt(
            metadata=metadata,
            physics_tensor=physics_tensor,
            selected_cards=selected_cards,
            consensus_history=consensus_history,
            previous_verdict=previous_verdict,
            lang=lang,
            plugin_weights=plugin_weights,
        )
        raw = await client.chat(prompt, temperature=0.2, max_tokens=900, stop=None)
        obj = self._extract_json(raw)
        verdict_body = str(obj.get("verdict_body") or "").strip()
        raw_change_log = obj.get("change_log")
        if isinstance(raw_change_log, dict):
            change_log = {
                "physics_diff": [str(x).strip() for x in (raw_change_log.get("physics_diff") or []) if str(x).strip()],
                "consensus_diff": [str(x).strip() for x in (raw_change_log.get("consensus_diff") or []) if str(x).strip()],
                "text_diff_hint": str(raw_change_log.get("text_diff_hint") or "").strip(),
            }
        else:
            legacy = raw_change_log if isinstance(raw_change_log, list) else []
            change_log = {
                "physics_diff": [],
                "consensus_diff": [],
                "text_diff_hint": "；".join([str(x).strip() for x in legacy if str(x).strip()][:2]),
            }

        logical_evidence = self.get_logical_evidence(
            metadata=metadata,
            physics_tensor=physics_tensor,
            selected_cards=selected_cards,
            consensus_history=consensus_history,
        )
        l1_flags = detect_universal_flags(metadata=metadata, physics_tensor=physics_tensor)
        blind_work = run_blind_school_plugin(physics_tensor=physics_tensor, metadata=metadata)
        enc_audit = audit_host_guest_vectors(work_vector=blind_work)
        blind_work["encyclopedia_audit"] = enc_audit
        spatial_audit = audit_spatial_sovereignty(work_vector=blind_work)
        blind_work["spatial_audit"] = spatial_audit
        unlock_advice = (blind_work.get("unlock_advice", {}) if isinstance(blind_work, dict) else {}) or {}
        strike_options = list(unlock_advice.get("strategic_strike_options", []) or [])
        topology = EnergyTopologySkill().produce({"metadata": metadata, "physics_tensor": physics_tensor})
        structure_v0 = resolve_structure_candidates_v0(
            physics_tensor=physics_tensor,
            work_vector=blind_work,
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
        logical_evidence.append(f"插件.conflict_zone={conflict_report.get('zone','BLUE')}")
        logical_evidence.append(f"插件.tension_level={conflict_report.get('tension_level',0.0)}")
        logical_evidence.append(f"L1_Junction.SHANG_GUAN_JIAN_GUAN={bool(l1_flags.get('SHANG_GUAN_JIAN_GUAN', False))}")
        logical_evidence.append(f"L1_Junction.control_energy={l1_flags.get('control_energy', 0.0)}")
        climate_trace = (((physics_tensor.get("meta", {}) or {}).get("climate_adjustment", {})) if isinstance(physics_tensor, dict) else {}) or {}
        logical_evidence.extend(
            [
                f"[Tomb State: {'Released' if float(blind_work.get('released_energy', 0.0) or 0.0) > 0 else 'Locked'}] Abs_Locked: {blind_work.get('potential_energy_locked', 0.0)}",
                f"[Tomb State: Released] Unlock_Gain: +{blind_work.get('unlock_gain', 0.0)} | Risk: -{blind_work.get('backfire_risk', 0.0)} | Net: {blind_work.get('work_expectation', 0.0)}",
                f"Climate.enabled={climate_trace.get('enabled', False)}",
                f"Climate.opposing={climate_trace.get('opposing_element', 'unknown')} factor={((climate_trace.get('factors', {}) or {}).get(climate_trace.get('opposing_element', ''), 1.0))}",
                f"做功.total={blind_work.get('work_expectation', 0.0)}",
                f"做功.morphing_hints={','.join(blind_work.get('morphing_hints', []) or [])}",
                f"做功.body_damage={blind_work.get('body_damage_estimation', {})}",
                f"做功.hint={blind_work.get('llm_hint', '劳而无功')}",
                f"格局V0.hud={structure_v0.get('hud', {})}",
                f"Topology.edges={len(topology.get('edges', []))}",
                f"格局终审V0.primary={final_decision_v0.get('primary_structure')}",
                f"格局终审V0.risk={final_decision_v0.get('stability_risk')}",
                f"空间.gain_paths={spatial_audit.get('gain_path_count', 0)}",
                f"空间.loss_paths={spatial_audit.get('loss_path_count', 0)}",
                f"百科.gain_vectors={enc_audit.get('gain_vector_count', 0)}",
                f"解锁.options={strike_options}",
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
        conflict_points = ((((metadata or {}).get("conflict_matrix") or {}).get("points") or []))
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
        version_id = datetime.utcnow().strftime("v2.%m%d%H%M%S")
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
        produced = {
            "version_id": version_id,
            "verdict_body": verdict_body,
            "change_log": change_log,
            "logical_evidence": logical_evidence,
            "work_vector": blind_work,
            "topology_graph_v1": topology,
            "structure_candidates_v0": structure_v0,
            "structure_final_decision_v0": final_decision_v0,
            "plugin_outputs_verdict_ready": verdict_plugin_outputs,
            "plugin_conflict_report": conflict_report,
            "l1_junction_flags": l1_flags,
        }
        audit_log = self.audit(consumed, produced).model_dump()
        return {
            "version_id": version_id,
            "verdict_body": verdict_body,
            "change_log": change_log,
            "logical_evidence": logical_evidence,
            "work_vector": blind_work,
            "topology_graph_v1": topology,
            "structure_candidates_v0": structure_v0,
            "structure_final_decision_v0": final_decision_v0,
            "plugin_outputs_verdict_ready": verdict_plugin_outputs,
            "plugin_conflict_report": conflict_report,
            "l1_junction_flags": l1_flags,
            "audit_log": audit_log,
            "confirmed_decisions": confirmed_decisions,
            "raw": raw,
        }

