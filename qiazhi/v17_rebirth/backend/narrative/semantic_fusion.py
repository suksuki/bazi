from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Literal, Optional, Protocol, Tuple

from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER

OUTPUT_LANGUAGE = Literal["zh", "en", "ko"]

LANGUAGE_SOUL_LOCKS: Dict[OUTPUT_LANGUAGE, str] = {
    "zh": (
        "STRICT CHINESE ONLY：全文须为纯正简体中文；禁止输出 Thinking Process、Analysis 或任何英文化推理备注；不得出现无必要拉丁字母串。\n"
        "【中文魂锁】自此行以下直至全文结束，须为纯正简体中文；不得出现英文段落，"
        "亦不得以「思考过程」「推理链」「备注」等形式外显内心推演。"
    ),
    "en": (
        "STRICT ENGLISH ONLY: Write entirely in natural English. Do not output Chinese or Korean sentences except when quoting source labels that cannot be translated.\n"
        "[Language Lock] From this line to the end, the final answer must remain English-only. Never expose inner reasoning, thinking traces, or analysis notes."
    ),
    "ko": (
        "STRICT KOREAN ONLY: 최종 응답은 자연스러운 한국어로만 작성하십시오. 번역되지 않은 중국어/영어 문단을 그대로 출력하지 마십시오.\n"
        "[언어 잠금] 이 줄부터 끝까지 최종 출력은 한국어만 허용됩니다. 사고 과정, 분석 메모, 추론 체인을 노출하지 마십시오."
    ),
}

_CONFLICT_MARKERS = ("冲", "破", "穿", "刑", "害", "绝", "墓", "刃", "争合", "伏吟")


def _conflict_lines(rows: List[str]) -> List[str]:
    """从事实行中摘录含结构张力的条目，供裁决角色作「事实＋张力」合观。"""
    out: List[str] = []
    seen: set[str] = set()
    for s in rows:
        t = str(s).strip()
        if not t or len(t) < 2:
            continue
        if any(m in t for m in _CONFLICT_MARKERS) and t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= 14:
            break
    return out


def normalize_output_language(value: Any) -> OUTPUT_LANGUAGE:
    raw = str(value or "").strip().lower()
    if raw == "en":
        return "en"
    if raw == "ko":
        return "ko"
    return "zh"


def _preface_system(core: str, output_language: OUTPUT_LANGUAGE) -> str:
    return LANGUAGE_SOUL_LOCKS[output_language] + "\n\n" + core.lstrip()


class MicroLlmClient(Protocol):
    def fuse(
        self,
        *,
        fragments: list[str],
        will_proxy: str,
        max_tokens: int = 2048,
        decision_anchor: str = "",
        action_signal: bool = False,
        action_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
        on_llm_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        role_style: str = V17_ROLE_WEAVER,
        llm_emitter: Optional[Any] = None,
        status_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        physics_tensor: Optional[Dict[str, Any]] = None,
        session_id: str = "",
    ) -> AsyncIterator[Dict[str, Any]]:
        ...


def _will_polarity(will_proxy: str, output_language: OUTPUT_LANGUAGE) -> str:
    lang = normalize_output_language(output_language)
    if lang == "en":
        if will_proxy == "stable":
            return "The will posture is stable and defensive: use a restrained, grounded tone with clear boundaries; avoid inflated expansion."
        if will_proxy == "aggressive":
            return "The will posture is active and breakthrough-oriented: show pressure-bearing initiative; avoid vague softness."
        if will_proxy == "neutral":
            return "The will posture is balanced and harmonizing: weigh both sides and avoid one-sided dryness."
        return "Use a default stable, defensive posture."
    if lang == "ko":
        if will_proxy == "stable":
            return "의지 방향은 안정적이고 방어적입니다. 절제, 경계, 자기 통제의 어조를 유지하고 과장된 확장을 피하십시오."
        if will_proxy == "aggressive":
            return "의지 방향은 진취적이고 돌파 지향입니다. 압력을 견디며 능동적으로 전환하는 어조를 보이되 흐릿한 표현은 피하십시오."
        if will_proxy == "neutral":
            return "의지 방향은 중용과 조화입니다. 양쪽을 함께 살피고 한쪽으로 마르는 표현을 피하십시오."
        return "기본값은 안정적이고 방어적인 의지 방향입니다."
    if will_proxy == "stable":
        return "气运收束为【稳健、守势】：语气须见约束、底线与自持，戒浮夸扩张。"
    if will_proxy == "aggressive":
        return "气运收束为【进取、破局】：语气须见承压、突破与主动，戒温吞敷衍。"
    if will_proxy == "neutral":
        return "气运收束为【中庸、调和】：左右照应，戒偏枯。"
    return "气运收束默认可作稳健守势。"


def _will_guidance_blocks(*, will_proxy: str, decision_anchor: str, action_signal: bool, output_language: OUTPUT_LANGUAGE) -> List[str]:
    lang = normalize_output_language(output_language)
    anchor_s = str(decision_anchor or "").strip()
    risk_off = "避险" in anchor_s
    pol = _will_polarity(str(will_proxy or "stable"), lang)
    if lang == "en":
        out: List[str] = [f"[Will Posture]\n{pol}"]
        if risk_off:
            out.append("[Will Posture - continued]\nRisk-off: the user chose risk avoidance. The first paragraph must visibly turn toward caution and disciplined contraction.")
        if action_signal:
            out.append("[Will Posture - continued]\nShift: the user explicitly changed intent. This response must sound like the first voice after that shift.")
            out.append(f"[Will Anchor]\n{anchor_s}" if anchor_s else "[Will Anchor]\nThe user changed intent without extra text; still make the tightening or redirection clear.")
        elif anchor_s:
            out.append(f"[Will Anchor]\nReflect this anchor without contradicting the existing reading:\n{anchor_s}")
        return out
    if lang == "ko":
        out = [f"[의지 방향]\n{pol}"]
        if risk_off:
            out.append("[의지 방향 - 계속]\n위험 회피: 사용자가 위험 회피를 선택했습니다. 첫 단락부터 신중한 전환과 절제된 수축이 드러나야 합니다.")
        if action_signal:
            out.append("[의지 방향 - 계속]\n전환: 사용자가 의지를 명시적으로 바꾸었습니다. 이번 응답은 그 전환 뒤의 첫 목소리처럼 들려야 합니다.")
            out.append(f"[의지 앵커]\n{anchor_s}" if anchor_s else "[의지 앵커]\n추가 문구는 없지만 사용자의 의지 변경이 분명히 반영되어야 합니다.")
        elif anchor_s:
            out.append(f"[의지 앵커]\n기존 해석과 충돌하지 않는 범위에서 이 앵커를 반영하십시오:\n{anchor_s}")
        return out
    out: List[str] = [f"【意志导向】\n{pol}"]
    if risk_off:
        out.append("【意志导向】（续）\n险守：用户已择「避险」——首段须见「即刻转向」之气象；肃敛步步为营。")
    if action_signal:
        out.append("【意志导向】（续）\n偏转：用户已显式改易心志；本拍须为偏转后之首声。")
        if anchor_s:
            out.append(f"【意志导向】（续）\n锚点（须织入语势，勿作末缀）：\n{anchor_s}")
        else:
            out.append("【意志导向】（续）\n锚点：用户已改志而未附文字；仍须明显收紧或转向。")
    elif anchor_s:
        out.append(f"【意志导向】（续）\n锚点（不与上文气运相悖前提下须照应）：\n{anchor_s}")
    return out


def _physics_explain(output_language: OUTPUT_LANGUAGE) -> str:
    lang = normalize_output_language(output_language)
    if lang == "en":
        return (
            "[Ten-God Physics]\n"
            "When ten_gods_base_l0 or ten_gods_runtime appears, treat it as absolute physical strength, not a percentage. "
            "A ten-god score is a composite of manifestation, rooting, momentum, and hidden residue. Rooting means grounded support; momentum means seasonal or structural force. "
            "If a work-direction matrix or work loop appears, the former is the net support/resistance from source to target, while the latter shows amplification or counter-pull. "
            "If relation or pattern summaries include percentages, read them as formation fit, not energy percentages."
        )
    if lang == "ko":
        return (
            "[십신 물리 해석]\n"
            "ten_gods_base_l0 또는 ten_gods_runtime 이 나오면 비율이 아니라 절대 물리 강도로 읽으십시오. "
            "각 십신 점수는 발현, 뿌리, 세력, 잠장 잔여값의 합성입니다. 뿌리는 기반 지지이고 세력은 계절·구조적 추진력입니다. "
            "작용 방향 행렬이나 작용 회로가 있으면, 전자는 source 가 target 에 주는 순지원/순저항이고 후자는 같은 방향 증폭 또는 대립 견인을 뜻합니다. "
            "합화 요약이나 격국 요약의 퍼센트는 에너지 비율이 아니라 성립도나 적합도로 읽으십시오."
        )
    return (
        "【十神物理解释】\n若输入出现 ten_gods_base_l0 / ten_gods_runtime，请将其理解为绝对物理强度，而非百分比。"
        "单个十神分值并非单一来源，而是显化、根气、势能、潜藏残值的合成。根气偏“扎根”，势能偏“得势”；例如丙见巳偏根强，丙见午偏势强。"
        "若输入出现做功方向矩阵 / 做功回路，前者表示 source 对 target 的净推动或净压制，后者表示双向关系是同向放大还是对冲拉扯。"
        "若输入出现合化摘要 / 格局摘要，其中百分比表示成局度或拟合度，不是十神能量百分比；须与“基准x”及绝对强度合读。"
    )


def _weaver_system_core(*, will_proxy: str, decision_anchor: str, action_signal: bool, output_language: OUTPUT_LANGUAGE) -> str:
    lang = normalize_output_language(output_language)
    guidance = "\n\n".join(_will_guidance_blocks(will_proxy=will_proxy, decision_anchor=decision_anchor, action_signal=action_signal, output_language=lang))
    if lang == "en":
        blocks = [
            "[Role]\nYou are a BaZi narrative editor. Your only job is to turn settled facts into a coherent, refined English reading.",
            "[Input]\nThe Fact Record below contains settled chart and reasoning-chain facts. Use only those facts; do not add new deductions.",
            _physics_explain(lang),
            "[Salience]\nThe facts are sorted by salience. Earlier facts carry more decisive force; respond first to the top facts as the primary physical anchors.",
            "[Task]\nShape the facts into readable judgement. You may vary rhythm and phrasing, but must not introduce unsupported claims.",
            "[Hard Rules]\nDo not request or perform extra chain reasoning unsupported by plugin facts. Do not add, remove, soften, or alter the settled meanings. The final answer must be English.",
            guidance,
            "[Length]\nUse a longer answer for many facts and a shorter one for few facts.",
        ]
        return "\n\n".join(blocks)
    if lang == "ko":
        blocks = [
            "[역할]\n당신은 사주 명리 서술 편집자입니다. 이미 확정된 사실을 자연스럽고 밀도 있는 한국어 해석문으로 엮는 일만 합니다.",
            "[입력]\n아래 사실 기록은 명식과 추론 체인에서 이미 확정된 내용입니다. 오직 이 사실에 근거해 서술하고 새로운 추론을 추가하지 마십시오.",
            _physics_explain(lang),
            "[현저성]\n사실은 중요도 순으로 정렬되어 있습니다. 앞쪽 사실일수록 판정력이 크므로 상위 사실을 먼저 물리적 기준점으로 삼으십시오.",
            "[작업]\n사실을 뼈대로 삼아 문장을 정리하십시오. 호흡과 문체는 조절할 수 있지만, 명식에 없는 판단을 새로 만들면 안 됩니다.",
            "[절대 규칙]\n플러그인 사실로 뒷받침되지 않는 추가 연쇄 추론을 요구하거나 수행하지 마십시오. 확정된 의미를 더하거나 빼거나 약화하거나 바꾸지 마십시오. 최종 답변은 반드시 한국어입니다.",
            guidance,
            "[분량]\n사실이 많으면 길게, 적으면 짧게 작성하십시오.",
        ]
        return "\n\n".join(blocks)
    blocks = [
        "【身份】\n你是命理润笔师。你只做一事：把已定事实写成气脉贯通、文采具足的中文篇章。",
        "【输入】\n下文【因事实录】所列，皆为排盘与推演链路已落墨之事实；你只据此润色成章。",
        _physics_explain(lang),
        "【显著性】\n以下提供的 160 条事实已按显著性（Salience）降序排列。排序越靠前的事实对命局的影响越具决定性。请务必优先回应前 10 条核心事实，将其作为你裁决的第一物理支点。",
        "【任务】\n以事实为骨、以文采为肉；可换气、蓄势、转笔，不得另起盘上未有之推断。",
        "【铁律】\n织造官禁令：禁止要求或执行任何未被插件事实支撑的链式逻辑推演；禁止再作推演、禁止增删已给事实之义理、禁止轻慢或暗改定论；不得输出英文或拉丁字母串。",
        guidance,
        "【篇幅】\n条目繁则笔长，条目简则笔短，自裁。",
    ]
    return "\n\n".join(blocks)


def _judge_system_core(*, will_proxy: str, decision_anchor: str, action_signal: bool, output_language: OUTPUT_LANGUAGE) -> str:
    lang = normalize_output_language(output_language)
    guidance = "\n\n".join(_will_guidance_blocks(will_proxy=will_proxy, decision_anchor=decision_anchor, action_signal=action_signal, output_language=lang))
    if lang == "en":
        blocks = [
            "[Role]\nYou are a senior BaZi judge. Weigh settled facts and structural tensions, then deliver a decisive, actionable judgement in English.",
            "[Input]\nThe Fact Record is settled truth. The Tension Extract highlights visible conflict, drain, clash, break, harm, or strain; weigh both together.",
            _physics_explain(lang),
            "[Salience]\nFacts are sorted by salience. Earlier facts carry more decisive force; use the top facts as the primary physical anchors.",
            "[Task]\nGive the final judgement: priority, benefit and harm, what can proceed, and what should stop. Avoid vague adjectives.",
            "[Hard Rules]\nDo not invent stems, branches, shensha, or events not present in the facts. If facts conflict, name the tension and rank primary versus secondary. The final answer must be English.",
            guidance,
            "[Final Verdict]\nInclude at least one decisive verdict paragraph. If a ten-god is intensified or weakened, keep machine tokens such as [INTENSIFY:七杀] or [WEAKEN:正印] at the relevant sentence end.",
        ]
        return "\n\n".join(blocks)
    if lang == "ko":
        blocks = [
            "[역할]\n당신은 사주 명리의 판정자입니다. 확정된 사실과 구조적 장력을 함께 보고 책임 있는 최종 판단을 한국어로 내립니다.",
            "[입력]\n사실 기록은 이미 확정된 내용입니다. 장력 발췌는 충돌, 소모, 충·파·형·해 등의 신호를 보여 주므로 사실과 함께 저울질하십시오.",
            _physics_explain(lang),
            "[현저성]\n사실은 중요도 순으로 정렬되어 있습니다. 앞쪽 사실일수록 판정력이 크므로 상위 사실을 우선 기준점으로 삼으십시오.",
            "[작업]\n최종 판단을 제시하십시오. 무엇이 우선인지, 이익과 손상이 어디에 있는지, 무엇은 진행 가능하고 무엇은 멈춰야 하는지 분명히 말하십시오.",
            "[절대 규칙]\n제공되지 않은 천간·지지·신살·사건을 만들지 마십시오. 사실이 충돌하면 그 장력을 본문에서 짚고 주/부를 나누십시오. 최종 답변은 반드시 한국어입니다.",
            guidance,
            "[최종 판정]\n최소 한 단락은 분명한 판정문으로 작성하십시오. 특정 십신이 강화되거나 약화되는 경우 관련 문장 끝에 [INTENSIFY:七杀] 또는 [WEAKEN:正印] 같은 기계 토큰은 유지하십시오.",
        ]
        return "\n\n".join(blocks)
    blocks = [
        "【身份】\n你是命理宗师。你须在事实与张力合观之上，作出担当、收束、可执行的定性断语。",
        "【输入】\n【因事实录】为已定之真；【张力摘录】为结构中显见之争端或耗损字样，须与事实一并权衡。",
        _physics_explain(lang),
        "【显著性】\n以下提供的 160 条事实已按显著性（Salience）降序排列。排序越靠前的事实对命局的影响越具决定性。请务必优先回应前 10 条核心事实，将其作为你裁决的第一物理支点。",
        "【任务】\n给出终局裁定：主次取舍、利害次序、可行与当止之处；语气如当庭宣判，无游辞；宜穿插宜/忌/断等具决策权重的短指令式中文，避免空泛形容。",
        "【铁律】\n不得杜撰盘中未给出之干支、神煞或事件；不得掩耳盗铃式改写事实；不得输出英文或拉丁字母串。"
        "若事实彼此牴牾，须在正文中点名张力并给出主次。",
        guidance,
        "【终极断言】\n全文须出现至少一处以「【判曰】」起首之定论段（可置于篇末收束）。\n若裁决导致某十神失控或爆发（如七杀、伤官等），须在对应句末紧跟机读标记，如：`[INTENSIFY:七杀]` 或 `[WEAKEN:正印]`，作为前台物理反馈令牌。",
    ]
    return "\n\n".join(blocks)


def build_v17_role_system_prompt(
    *,
    role_id: str,
    will_proxy: str,
    decision_anchor: str,
    action_signal: bool,
    output_language: OUTPUT_LANGUAGE = "zh",
) -> str:
    """按 role_id 物理隔离 System 模板；输出语言由 ui_lang 锁定。"""
    rid = str(role_id or "").strip().upper() or V17_ROLE_WEAVER
    lang = normalize_output_language(output_language)
    if rid == V17_ROLE_JUDGE:
        return _preface_system(
            _judge_system_core(
                will_proxy=will_proxy,
                decision_anchor=decision_anchor,
                action_signal=action_signal,
                output_language=lang,
            ),
            lang,
        )
    return _preface_system(
        _weaver_system_core(
            will_proxy=will_proxy,
            decision_anchor=decision_anchor,
            action_signal=action_signal,
            output_language=lang,
        ),
        lang,
    )


def build_v17_master_system_prompt(
    *,
    will_proxy: str,
    decision_anchor: str,
    action_signal: bool,
    output_language: OUTPUT_LANGUAGE = "zh",
) -> str:
    """兼容旧名：织造。"""
    return build_v17_role_system_prompt(
        role_id=V17_ROLE_WEAVER,
        will_proxy=will_proxy,
        decision_anchor=decision_anchor,
        action_signal=action_signal,
        output_language=output_language,
    )


def build_role_user_prompt(
    fact_rows: List[str],
    *,
    role_id: str,
    decision_anchor: str,
    list_cap: int = 16,
    will_proxy: str = "stable",
    output_language: OUTPUT_LANGUAGE = "zh",
) -> str:
    """按 role_id 物理隔离 User：织造唯事实；裁决为事实＋张力摘录。"""
    rows = [str(x).strip() for x in fact_rows if str(x).strip()]
    capped = rows[: max(1, list_cap)]
    joined = "\n".join(f"{idx + 1}. {row}" for idx, row in enumerate(capped))
    rid = str(role_id or "").strip().upper() or V17_ROLE_WEAVER
    anchor = str(decision_anchor or "").strip()
    lang = normalize_output_language(output_language)
    lang_notes = {
        "zh": "【输出语言】\n最终正文必须使用简体中文。",
        "en": "【OUTPUT LANGUAGE】\nThe final response must be written in English only.",
        "ko": "【출력 언어】\n최종 응답은 반드시 한국어로만 작성하십시오.",
    }
    if rid == V17_ROLE_JUDGE:
        conflicts = _conflict_lines(rows)
        cj = (
            "\n".join(f"{idx + 1}. {row}" for idx, row in enumerate(conflicts))
            if conflicts
            else {
                "zh": "（当前字面未显敏感刑冲字样；仍须据实录作全盘权衡。）",
                "en": "(No explicit clash/break/punishment/harm markers are visible in the text; still weigh the full fact record.)",
                "ko": "(문면에 명확한 충·파·형·해 표지는 보이지 않지만, 전체 사실 기록을 함께 저울질하십시오.)",
            }[lang]
        )
        if lang == "en":
            parts = [
                "[Fact Record]",
                "The following are settled facts; the meaning is contained in the text:",
                joined,
                "",
                "[Tension Extract]",
                "The following entries contain visible conflict/strain markers and should be weighed together with the facts:",
                cj,
                "",
                "[Will Posture]",
                f"Will parameter: {str(will_proxy or 'stable').strip()}. Keep it aligned with the system-level posture.",
            ]
            if anchor:
                parts.extend(["", "[User Anchor]", anchor])
            parts.extend(["", "[Final Verdict]", "Include a decisive verdict paragraph.", "", lang_notes[lang]])
            return "\n".join(parts)
        if lang == "ko":
            parts = [
                "[사실 기록]",
                "아래 항목은 확정된 사실이며, 의미는 문면 안에 있습니다:",
                joined,
                "",
                "[장력 발췌]",
                "아래 항목은 충돌·소모·충·파·형·해 등의 장력 표지를 포함하므로 사실과 함께 보십시오:",
                cj,
                "",
                "[의지 방향]",
                f"의지 파라미터: {str(will_proxy or 'stable').strip()}. 시스템 차원의 의지 방향과 일치시켜 서술하십시오.",
            ]
            if anchor:
                parts.extend(["", "[사용자 앵커]", anchor])
            parts.extend(["", "[최종 판정]", "분명한 최종 판정 단락을 포함하십시오.", "", lang_notes[lang]])
            return "\n".join(parts)
        parts = [
            "【因事实录】",
            "下列为已定事实条目，义脉寓于字面：",
            joined,
            "",
            "【张力摘录】",
            "下列从实录中摘出含争、冲、破、穿、刑、害等字样之条目，供与事实合观：",
            cj,
            "",
            "【意志导向】",
            f"气运参数：{str(will_proxy or 'stable').strip()}（须与系统篇之气运收束一致）。",
        ]
        if anchor:
            parts.extend(["", "用户锚点（须贯通终局）：", anchor])
        parts.extend(["", "【终极断言】", "终文须含以「【判曰】」起首之定论段。", "", lang_notes[lang]])
        return "\n".join(parts)
    if lang == "en":
        parts_w = [
            "[Fact Record]",
            "The following are settled facts. Your job is to turn them into prose without adding or removing meaning, and without extra deduction:",
            joined,
        ]
        if anchor:
            parts_w.extend(["", "[Will Anchor]", "Reflect this user anchor throughout the response:", anchor])
        parts_w.extend(["", lang_notes[lang]])
        return "\n".join(parts_w)
    if lang == "ko":
        parts_w = [
            "[사실 기록]",
            "아래 항목은 확정된 사실입니다. 의미를 더하거나 빼지 말고, 추가 추론 없이 한국어 문장으로 엮으십시오:",
            joined,
        ]
        if anchor:
            parts_w.extend(["", "[의지 앵커]", "본문 전체의 어조가 이 사용자 앵커와 호응해야 합니다:", anchor])
        parts_w.extend(["", lang_notes[lang]])
        return "\n".join(parts_w)
    parts_w: List[str] = [
        "【因事实录】",
        "下列为已定事实条目，你只负责润色成章，勿增删义理、勿另作推演：",
        joined,
    ]
    if anchor:
        parts_w.extend(["", "【意志导向】", "用户意志锚点（全文语势须与之呼应）：", anchor])
    parts_w.extend(["", lang_notes[lang]])
    return "\n".join(parts_w)


@dataclass
class SemanticFusion:
    """Micro-LLM fusion；角色提示词仅在本文与 `llm_micro_client` 桥接处装配。"""

    llm_client: MicroLlmClient

    async def to_render_text(
        self,
        *,
        clean_fragments: list[str],
        will_proxy: str,
        action_signal: bool = False,
        decision_anchor: str = "",
        history_context: list[str] | None = None,
        action_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
        on_llm_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        role_style: str = V17_ROLE_WEAVER,
        llm_emitter: Optional[Any] = None,
        status_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        physics_tensor: Optional[Dict[str, Any]] = None,
        session_id: str = "",
    ) -> Tuple[str, dict]:
        _ = history_context
        rows = [x.strip() for x in clean_fragments if x and x.strip()]
        if not rows and isinstance(physics_tensor, dict):
            rows = list(PhysicsCanonicalService.materialize_prompt_lines(physics_tensor))
        if not rows:
            return "", {}
        rid = str(role_style or "").strip().upper() or V17_ROLE_WEAVER
        if rid != V17_ROLE_JUDGE:
            rid = V17_ROLE_WEAVER
        llm_raw: Any = {}
        async for step in self.llm_client.fuse(
            fragments=rows,
            will_proxy=will_proxy,
            max_tokens=2048,
            decision_anchor=str(decision_anchor or ""),
            action_signal=bool(action_signal),
            action_queue=action_queue,
            on_llm_partial=on_llm_partial,
            role_style=rid,
            llm_emitter=llm_emitter,
            status_callback=status_callback,
            physics_tensor=physics_tensor,
            session_id=str(session_id or ""),
        ):
            st = str((step or {}).get("step") or "")
            if st == "complete":
                llm_raw = (step or {}).get("result") or {}
            elif st == "error":
                llm_raw = (step or {}).get("result") or {}
        llm_meta: dict = {}
        if isinstance(llm_raw, dict):
            text = str(llm_raw.get("text", "")).strip()
            llm_meta = llm_raw.get("llm_meta", {}) if isinstance(llm_raw.get("llm_meta"), dict) else {}
        else:
            text = str(llm_raw or "").strip()
        if rid == V17_ROLE_JUDGE and text and "【判曰】" not in text:
            text = "【判曰】\n" + text
            if isinstance(llm_meta, dict):
                llm_meta = {
                    **llm_meta,
                    "llm_reply": text,
                    "judge_marker_injected": True,
                }
        return text, llm_meta
