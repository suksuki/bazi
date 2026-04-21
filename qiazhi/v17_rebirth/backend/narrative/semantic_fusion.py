from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Protocol, Tuple

from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER

# 全角色 System 首行：圣殿宪法 — STRICT CHINESE ONLY + 中文魂锁
CHINESE_SOUL_LOCK = (
    "STRICT CHINESE ONLY：全文须为纯正简体中文；禁止输出 Thinking Process、Analysis 或任何英文化推理备注；不得出现无必要拉丁字母串。\n"
    "【中文魂锁】自此行以下直至全文结束，须为纯正简体中文；不得出现英文段落，"
    "亦不得以「思考过程」「推理链」「备注」等形式外显内心推演。"
)

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


def _preface_system(core: str) -> str:
    return CHINESE_SOUL_LOCK + "\n\n" + core.lstrip()


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


def _will_polarity_cn(will_proxy: str) -> str:
    if will_proxy == "stable":
        return "气运收束为【稳健、守势】：语气须见约束、底线与自持，戒浮夸扩张。"
    if will_proxy == "aggressive":
        return "气运收束为【进取、破局】：语气须见承压、突破与主动，戒温吞敷衍。"
    if will_proxy == "neutral":
        return "气运收束为【中庸、调和】：左右照应，戒偏枯。"
    return "气运收束默认可作稳健守势。"


def _will_guidance_blocks(*, will_proxy: str, decision_anchor: str, action_signal: bool) -> List[str]:
    anchor_s = str(decision_anchor or "").strip()
    risk_off = "避险" in anchor_s
    pol = _will_polarity_cn(str(will_proxy or "stable"))
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


def _weaver_system_core(*, will_proxy: str, decision_anchor: str, action_signal: bool) -> str:
    guidance = "\n\n".join(_will_guidance_blocks(will_proxy=will_proxy, decision_anchor=decision_anchor, action_signal=action_signal))
    blocks = [
        "【身份】\n你是命理润笔师。你只做一事：把已定事实写成气脉贯通、文采具足的中文篇章。",
        "【输入】\n下文【因事实录】所列，皆为排盘与推演链路已落墨之事实；你只据此润色成章。",
        "【十神物理解释】\n若输入出现 ten_gods_base_l0 / ten_gods_runtime，请将其理解为绝对物理强度，而非百分比。单个十神分值并非单一来源，而是显化、根气、势能、潜藏残值的合成。根气偏“扎根”，势能偏“得势”；例如丙见巳偏根强，丙见午偏势强。",
        "【显著性】\n以下提供的 160 条事实已按显著性（Salience）降序排列。排序越靠前的事实对命局的影响越具决定性。请务必优先回应前 10 条核心事实，将其作为你裁决的第一物理支点。",
        "【任务】\n以事实为骨、以文采为肉；可换气、蓄势、转笔，不得另起盘上未有之推断。",
        "【铁律】\n织造官禁令：禁止要求或执行任何未被插件事实支撑的链式逻辑推演；禁止再作推演、禁止增删已给事实之义理、禁止轻慢或暗改定论；不得输出英文或拉丁字母串。",
        guidance,
        "【篇幅】\n条目繁则笔长，条目简则笔短，自裁。",
    ]
    return "\n\n".join(blocks)


def _judge_system_core(*, will_proxy: str, decision_anchor: str, action_signal: bool) -> str:
    guidance = "\n\n".join(_will_guidance_blocks(will_proxy=will_proxy, decision_anchor=decision_anchor, action_signal=action_signal))
    blocks = [
        "【身份】\n你是命理宗师。你须在事实与张力合观之上，作出担当、收束、可执行的定性断语。",
        "【输入】\n【因事实录】为已定之真；【张力摘录】为结构中显见之争端或耗损字样，须与事实一并权衡。",
        "【十神物理解释】\n若输入出现 ten_gods_base_l0 / ten_gods_runtime，请将其理解为绝对物理强度，而非百分比。单个十神分值并非单一来源，而是显化、根气、势能、潜藏残值的合成。根气回答“是否扎根”，势能回答“是否得势”，两者不可混为一谈。",
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
) -> str:
    """按 role_id 物理隔离 System 模板；首行统一中文魂锁。"""
    rid = str(role_id or "").strip().upper() or V17_ROLE_WEAVER
    if rid == V17_ROLE_JUDGE:
        return _preface_system(_judge_system_core(will_proxy=will_proxy, decision_anchor=decision_anchor, action_signal=action_signal))
    return _preface_system(_weaver_system_core(will_proxy=will_proxy, decision_anchor=decision_anchor, action_signal=action_signal))


def build_v17_master_system_prompt(
    *,
    will_proxy: str,
    decision_anchor: str,
    action_signal: bool,
) -> str:
    """兼容旧名：织造。"""
    return build_v17_role_system_prompt(
        role_id=V17_ROLE_WEAVER,
        will_proxy=will_proxy,
        decision_anchor=decision_anchor,
        action_signal=action_signal,
    )


def build_role_user_prompt(
    fact_rows: List[str],
    *,
    role_id: str,
    decision_anchor: str,
    list_cap: int = 16,
    will_proxy: str = "stable",
) -> str:
    """按 role_id 物理隔离 User：织造唯事实；裁决为事实＋张力摘录。"""
    rows = [str(x).strip() for x in fact_rows if str(x).strip()]
    capped = rows[: max(1, list_cap)]
    joined = "\n".join(f"{idx + 1}. {row}" for idx, row in enumerate(capped))
    rid = str(role_id or "").strip().upper() or V17_ROLE_WEAVER
    anchor = str(decision_anchor or "").strip()
    if rid == V17_ROLE_JUDGE:
        conflicts = _conflict_lines(rows)
        cj = (
            "\n".join(f"{idx + 1}. {row}" for idx, row in enumerate(conflicts))
            if conflicts
            else "（当前字面未显敏感刑冲字样；仍须据实录作全盘权衡。）"
        )
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
        parts.extend(
            [
                "",
                "【终极断言】",
                "终文须含以「【判曰】」起首之定论段。",
            ]
        )
        return "\n".join(parts)
    parts_w: List[str] = [
        "【因事实录】",
        "下列为已定事实条目，你只负责润色成章，勿增删义理、勿另作推演：",
        joined,
    ]
    if anchor:
        parts_w.extend(["", "【意志导向】", "用户意志锚点（全文语势须与之呼应）：", anchor])
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
