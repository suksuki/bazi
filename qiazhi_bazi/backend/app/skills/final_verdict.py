"""FinalVerdictSkill: 基于物理真值生成终判与变更摘要。"""
from __future__ import annotations

import json
import re
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List

from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient


class FinalVerdictSkill:
    _instance: "FinalVerdictSkill | None" = None
    _lock = Lock()
    skill_id = "final_verdict_skill"
    skill_version = "1.0.0"

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
        deity_axes = (physics_tensor.get("deity_energy_axes", {}) if isinstance(physics_tensor, dict) else {}) or {}
        for deity in ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]:
            axis = deity_axes.get(deity) if isinstance(deity_axes, dict) else None
            if isinstance(axis, dict):
                abs_energy = float(axis.get("absolute_energy", 0.0) or 0.0)
                qualifier = FinalVerdictSkill._strength_qualifier(abs_energy)
                lines.append(f"十神.{deity}.Abs={abs_energy:.2f} [状态:{qualifier}]")
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
        system = (
            "你是 Qiazhi-Bazi 的 FinalVerdictSkill。"
            "你必须每次返回一份全量、唯一、可执行的终判，不允许追加旧内容。"
            "必须引用具体物理数值（十神绝对能量 Abs）作为依据；禁止空泛修辞。"
            "你生成的每一句命理断语，必须能在 [Physical Evidence] 里找到数值或标签支撑。"
            "若与 [User Consensus] 冲突，必须以 [User Consensus] 为准。"
            "输出严格 JSON："
            '{"verdict_body":"markdown","change_log":{"physics_diff":[],"consensus_diff":[],"text_diff_hint":""}}。'
            "change_log 仅写相对上一版的变化；若无上一版则写当前基线要点。"
            f"{lang_hint}"
        )
        user = (
            "[Physical Evidence]\n"
            + "\n".join(f"- {x}" for x in logical_evidence)
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
            + "\n"
            f"Previous_Verdict={previous_verdict or ''}\n"
            "请输出三段 markdown 小节：### 核心气象 / ### 裁决共识 / ### 行为指引。"
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

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
        return {
            "version_id": datetime.utcnow().strftime("v2.%m%d%H%M%S"),
            "verdict_body": verdict_body,
            "change_log": change_log,
            "logical_evidence": logical_evidence,
            "raw": raw,
        }

