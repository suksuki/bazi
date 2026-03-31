"""
FDS 2.0 LLM 判词叙事（基于物理证据 + RAG 原典 + 大运/流年/地域）
================================================================
选中档案后，结合当前大运、流年、地域与 5D 流形叠加态，构造三层嵌套 Prompt，
调用 LLM 生成判词；支持流式输出，供全息格局页打字机展示。
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Generator

from core.manifold_trace import affinity_from_d_m
from core.dynamic_engine import build_dynamic_context_for_prompt
from core.rag_canon import query_citations, format_citations_for_prompt
from core.fds_fusion import calculate_manifold_fusion_tensor, analyze_macro_indices

# 语义呼吸：遇这些标点或换行时额外停顿，模拟「推演者在命运转折点的停顿思考」
_BREATH_PUNCTUATION = frozenset("，。、；！？\n：" + ".")

# SOP V8.2：状态/参数中文化，避免 Qwen 因英文参数进入英文思维
_STATE_CN = {
    "PURE": "高度凝聚",
    "VERIFIED": "格局成立",
    "DRIFTING": "漂移不稳",
    "BROKEN": "结构坍缩",
    "formed_by_transport": "岁运成格",
    "broken_year": "岁运破格",
    "original": "原局成立",
}
_ENERGY_TIER_CN = {"high": "极高", "mid": "中等", "low": "偏低"}


def build_fds_verdict_prompt(
    pattern_id: str,
    status: str,
    d_m: float,
    affinity: float,
    overlay: List[Dict[str, Any]],
    point_5d: Dict[str, float],
    luck_pillar: str = "",
    year_pillar: str = "",
    geo_label: str = "",
    macro_indices: Optional[Dict[str, float]] = None,
    ranked_classical: Optional[List[Dict[str, Any]]] = None,
    pattern_change_trigger: Optional[List[str]] = None,
) -> str:
    """
    构造三层嵌套 Prompt（证据层 + RAG 层 + 叙事层），
    注入大运、流年、地域供 LLM 结合时空写判词。
    SOP V6.8：若提供 macro_indices（财富/事业/健康 0-100），注入合成张量宏观指数，要求判词结合量化指向。
    SOP V7.2：若提供 ranked_classical（按法理主权分排序的古典格成列表），要求判词按主次书写：主权格为主干叙事，修饰格为性情/风格，神煞格为细节注脚。
    """
    status = (status or "BROKEN").upper()
    state_map = {
        "PURE": "高度凝聚（PURE）",
        "VERIFIED": "格局成立（VERIFIED）",
        "DRIFTING": "漂移不稳（DRIFTING）",
        "BROKEN": "结构坍缩（BROKEN）",
    }
    state_cn = state_map.get(status, status)

    overlay_lines = []
    for i, item in enumerate(overlay, 1):
        pid = item.get("pattern_id", "")
        d_val = float(item.get("D_M", 0.0))
        aff = affinity_from_d_m(d_val)
        raw_status = item.get("status", "")
        status_cn = _STATE_CN.get(raw_status, raw_status) or "—"
        et = item.get("energy_tier", "mid")
        et_cn = _ENERGY_TIER_CN.get(et, et)
        overlay_lines.append(
            f"- {i}. {pid} · 匹配度≈{aff:.1f}% · 状态：{status_cn} · 能量成色：{et_cn}"
        )

    zero_vec = {k: 0.0 for k in point_5d.keys()} if point_5d else {}
    dynamic_context = build_dynamic_context_for_prompt(
        base_point=point_5d or {},
        dynamic_point=point_5d or {},
        time_delta=zero_vec,
        geo_factor=zero_vec,
        luck_gan_zhi=luck_pillar or "—",
        year_gan_zhi=year_pillar or "—",
        direction=geo_label or "—",
    )
    if luck_pillar or year_pillar or geo_label:
        dynamic_context += f"\n【当前时空】大运={luck_pillar or '—'}，流年={year_pillar or '—'}，地域={geo_label or '—'}"

    citations = query_citations(pattern_id)
    rag_block = format_citations_for_prompt(citations) if citations else ""

    if status in ("PURE", "VERIFIED"):
        tone = "整体语气偏庄重、宏大，强调格局成就感与结构稳定性，但必须保持克制与敬畏。"
    elif status == "BROKEN":
        tone = "整体语气偏警示、急促，强调结构性风险与坍缩危险，但避免恐吓与绝对化预言。"
    else:
        tone = "整体语气介于平衡与紧张之间，体现漂移与不确定性，强调选择与调整空间。"

    overlay_text = "\n".join(overlay_lines) if overlay_lines else "（无叠加态信息）"

    # SOP V8.5：中文灵魂注入 + 推理引导 — 第一反应/逻辑演进/最终批导均须中文，思考以命理术语为基点
    prompt = """#重要# 你的第一反应必须是中文，你的逻辑演进必须是中文，你的最终批导必须是中文。

你是一位精通中国传统命理与现代心理学的资深大师。请务必使用【简体中文】进行所有的分析与叙事。严禁输出任何英文正文。
请你在内部推理时，直接以中文命理术语（如「杀印相生」「财官双美」「伤官见官」）作为逻辑基点进行思考；开始你的中文思考过程，并最终输出中文判词。

"""
    prompt += f"""你同时是 FDS 2.0 时代的「量子命运物理审计师」，任务是在严格遵守物理证据的前提下，生成一段简洁、深刻的中文判词。在分析格局时，请结合古典辞章，风格需圆润博学，叙事需贴合中国人的情感逻辑与处世哲学。
【语言】你必须且仅使用简体中文书写整段判词及任何推理过程，禁止使用英文。
请务必遵守：不得编造与下述物理证据相矛盾的内容，不得给出绝对化的吉凶结论。

====================
【一、物理证据层】
- 主权格局：{pattern_id}
- 当前主权状态：{state_cn}
- 主权匹配度：{affinity:.2f}%（流形距离 D_M={d_m:.4f}）

【叠加态（前 3 格局）】
{overlay_text}

【5D 坐标与当前时空】
{dynamic_context}
"""
    if macro_indices:
        w = macro_indices.get("wealth", 0)
        c = macro_indices.get("career", 0)
        h = macro_indices.get("health", 0)
        prompt += f"""
【合成张量宏观指数（SOP V6.8）】财富 {w:.0f} 分、事业 {c:.0f} 分、健康 {h:.0f} 分。判词中需结合这些量化指标给出具体指向（例如：财高健康低时明确提示防范因应力过载导致的身体透支；事业高而健康低时提示「虽可进取，宜先固本」）。"""
    prompt += f"""

====================
【二、古典原典与判例】
以下是与该格局相关的古典原话/判例，请在判词中至少引用或转译其中 1 条，并与上述物理状态相呼应：
{rag_block}
"""
    if ranked_classical:
        sovereign = [x for x in ranked_classical if x.get("llm_role") == "sovereign"]
        modifier = [x for x in ranked_classical if x.get("llm_role") == "modifier"]
        accessory = [x for x in ranked_classical if x.get("llm_role") == "accessory"]
        lines = []
        if sovereign:
            parts = [
                f"{x.get('classical_name', '')}（能量成色：{_ENERGY_TIER_CN.get(x.get('energy_tier', 'mid'), '中')}）"
                for x in sovereign
            ]
            names = "、".join(parts)
            lines.append(f"- **第一顺位（主权）**：{names}。作为判词主干，决定事业/地位/人生底色，请以「君之命局法理以……为主权」或等价表述开门见山。")
        if modifier:
            names = "、".join(x.get("classical_name", "") for x in modifier)
            lines.append(f"- **第二/三顺位（修饰）**：{names}。作为性情与风格修饰，描述行事风骨、辅助主权格之成型，可写「兼具……之风骨」。")
        if accessory:
            names = "、".join(x.get("classical_name", "") for x in accessory)
            lines.append(f"- **末尾顺位（注脚）**：{names}。作为细节彩蛋，可于流年或细节处一笔带过，如「流年更见……入局」。")
        if lines:
            prompt += """
【古典法理主次（SOP V7.2）】以下格局已按法理主权分排序，判词须体现主次分明，不得胡子眉毛一把抓：
""" + "\n".join(lines) + "\n"
        # SOP V7.7 弹性定性：成色高可写「格成极真、富贵自天来」，成色低可写「格局虽成，然根基尚浅，需步步为营」
        if sovereign or modifier:
            prompt += "【定性描述】能量成色极高时可用「格成极真、富贵自天来」；成色偏低时须用「格局虽成，然根基尚浅，需步步为营」等弹性表述，名分在而贵贱由成色定。\n"
    prompt += f"""

====================
【三、叙事生成指令】
1. 结构：按「原局格局特征 → 当前时空状态（大运/流年/地域）→ 风险与张力 → 走向与建议」四段式展开。
2. 风格：{tone}
3. 物理约束：必须在文中体现匹配度与格局状态的含义；状态为结构坍缩时须描述风险，不得宣称必然灾祸。
4. 语言：整段判词及你的任何内部推理、思考过程必须全部使用简体中文，禁止使用英文。语气冷静、可带诗意，不煽情。长度 200～300 字。
5. 输出格式：请按以下中文小节输出，便于阅读：
【格局定性】：（开门见山，君之命局法理以……为主）
【气象分析】：（当前大运、流年、地域下的气象与张力）
【岁运建议】：（走向与建议，一两句收束）
"""
    if ranked_classical:
        prompt += "6. 法理主次：若有上述「古典法理主次」列表，判词须按主权→修饰→注脚的顺序组织古典格局表述，使叙事有血有肉、层次分明。\n"
    if pattern_change_trigger:
        prompt += "\n【格局岁运迁移（SOP V7.5）】以下为岁运成格/岁运破格提示，判词中须有所体现：\n"
        for t in pattern_change_trigger:
            prompt += f"- {t}\n"
    prompt += """
请直接按上述【格局定性】【气象分析】【岁运建议】格式输出判词正文（Markdown 段落即可）。
【语言锚点】再次强调：#重要# 你的第一反应必须是中文，逻辑演进必须是中文，最终批导必须是中文。严禁使用英文进行推理或书写。"""
    return prompt


def stream_fds_verdict(
    projection: Dict[str, float],
    overlay: List[Dict[str, Any]],
    luck_pillar: str = "",
    year_pillar: str = "",
    geo_label: str = "",
    typing_delay: float = 0.03,
    breath_pause: float = 0.5,
    macro_indices: Optional[Dict[str, float]] = None,
    ranked_classical: Optional[List[Dict[str, Any]]] = None,
    pattern_change_trigger: Optional[List[str]] = None,
) -> Generator[str, None, None]:
    """
    根据当前 5D 投影与叠加态，结合大运、流年、地域，流式生成 LLM 判词；
    逐字符 yield，便于前端打字机展示。
    遇逗号、句号、段落换行等「语义呼吸点」时额外停顿 breath_pause 秒，增强命运转折点的停顿感。
    SOP V6.8：若未传入 macro_indices，则根据 overlay 计算合成张量宏观指数并注入判词。
    """
    if not overlay:
        yield "暂无叠加态数据，无法生成判词。"
        return

    top = overlay[0]
    pattern_id = top.get("pattern_id", "")
    status = top.get("status", "BROKEN")
    d_m = float(top.get("D_M", 0.0))
    affinity = affinity_from_d_m(d_m)

    if macro_indices is None:
        p_final = calculate_manifold_fusion_tensor(overlay)
        macro_indices = analyze_macro_indices(p_final)
    prompt = build_fds_verdict_prompt(
        pattern_id=pattern_id,
        status=status,
        d_m=d_m,
        affinity=affinity,
        overlay=overlay,
        point_5d=projection,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar,
        geo_label=geo_label,
        macro_indices=macro_indices,
        ranked_classical=ranked_classical,
        pattern_change_trigger=pattern_change_trigger,
    )

    try:
        from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer
        synth = LLMSemanticSynthesizer()
        if not getattr(synth, "use_llm", False):
            yield "LLM 未启用或不可用，请在系统配置中设置模型并启动 Ollama。"
            return
        client = getattr(synth, "_llm_client", None)
        model = getattr(synth, "model_name", "Qwen2.5")
        if not client:
            yield "LLM 客户端未就绪。"
            return
    except Exception as e:
        yield f"判词引擎初始化失败：{e}"
        return

    def _to_dict(obj):
        """Pydantic v1/v2 或普通 dict 转 dict，便于统一取 message.content。"""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            try:
                return obj.model_dump()
            except Exception:
                pass
        if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
            try:
                return obj.dict()
            except Exception:
                pass
        return None

    # SOP V8.3：判词只展示正文，不展示思考过程。thinking/reasoning_content 仅用于模型内部，不得进入 UI。
    _CONTENT_KEYS = ("content", "text", "body")
    _REASONING_KEYS = ("reasoning_content", "thinking")  # 仅作调试用，不参与判词展示

    def _normalize_text(val):
        if val is None:
            return ""
        if isinstance(val, str) and val.strip():
            return val.strip()
        return ""

    def _deep_search_content(obj, depth=0, max_depth=5, content_only=True):
        """递归扫描取正文。content_only=True 时只取 content/text/body，不取 thinking/reasoning（避免思考过程进判词）。"""
        if depth > max_depth or obj is None:
            return ""
        keys = _CONTENT_KEYS if content_only else _CONTENT_KEYS + _REASONING_KEYS
        if isinstance(obj, dict):
            for k in keys:
                v = obj.get(k)
                t = _normalize_text(v)
                if t:
                    return t
            for v in obj.values():
                t = _deep_search_content(v, depth + 1, max_depth, content_only)
                if t:
                    return t
            return ""
        if hasattr(obj, "__dict__"):
            for k in keys:
                t = _normalize_text(getattr(obj, k, None))
                if t:
                    return t
        d = _to_dict(obj)
        if isinstance(d, dict):
            return _deep_search_content(d, depth + 1, max_depth, content_only)
        return ""

    def _extract_chunk_text(chunk):
        """
        判词流式解析 - SOP V8.5 状态机优先级：
        IF chunk.content (或 text/body) NOT EMPTY -> 视为判词正文，Display as Verdict；
        IF chunk.reasoning_content / thinking NOT EMPTY -> 不进入判词框（可重定向调试/Expert Analysis）。
        仅提取 content/text/body，确保 thinking 结束并转入 content 后的中文正文被正确展示。
        """
        if chunk is None:
            return ""
        try:
            # 1) OpenAI 风格：chunk.choices[0].delta，仅正文
            if hasattr(chunk, "choices") and getattr(chunk, "choices", None) and len(chunk.choices) > 0:
                delta = getattr(chunk.choices[0], "delta", None)
                if delta is not None:
                    for field in _CONTENT_KEYS + ("message",):
                        val = getattr(delta, field, None)
                        t = _normalize_text(val)
                        if t:
                            return t
                    if hasattr(delta, "__dict__"):
                        for k in _CONTENT_KEYS:
                            t = _normalize_text(getattr(delta, k, None))
                            if t:
                                return t

            # 2) Ollama/聚合器：chunk.message，仅 content/text/body，不取 thinking
            if hasattr(chunk, "message") and chunk.message is not None:
                m = chunk.message
                for field in _CONTENT_KEYS:
                    val = getattr(m, field, None)
                    t = _normalize_text(val)
                    if t:
                        return t
                if hasattr(m, "get") and callable(getattr(m, "get")):
                    for k in _CONTENT_KEYS:
                        t = _normalize_text(m.get(k))
                        if t:
                            return t
                if hasattr(m, "__dict__"):
                    for k in _CONTENT_KEYS:
                        v = getattr(m, k, None)
                        t = _normalize_text(v) if isinstance(v, str) else ""
                        if t:
                            return t

            # 3) 顶层 response / text
            for k in ("response", "text") + _CONTENT_KEYS:
                val = getattr(chunk, k, None) if hasattr(chunk, k) else None
                t = _normalize_text(val)
                if t:
                    return t

            # 4) 兜底：深度扫描时仅取正文（默认 content_only=True）
            d = _to_dict(chunk)
            if d is not None:
                t = _deep_search_content(d)
                if t:
                    return t
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug("Qwen 解析 chunk 异常: %s", e)
        return ""

    def _extract_full_message(resp, content_only=True):
        """从非流式 chat 响应提取正文。content_only=True 时只取 content/text/body。"""
        if resp is None:
            return ""
        d = _to_dict(resp)
        if d is not None:
            t = _deep_search_content(d, content_only=content_only)
            if t:
                return t
        if hasattr(resp, "message") and resp.message is not None:
            m = resp.message
            keys = _CONTENT_KEYS if content_only else _CONTENT_KEYS + _REASONING_KEYS
            for k in keys:
                t = _normalize_text(getattr(m, k, None))
                if t:
                    return t
            md = _to_dict(resp.message)
            if isinstance(md, dict):
                t = _deep_search_content(md, content_only=content_only)
                if t:
                    return t
        if hasattr(resp, "response") and resp.response:
            return resp.response if isinstance(resp.response, str) else str(resp.response)
        return ""

    def _extract_thinking(resp):
        """从非流式响应中仅提取 thinking/reasoning_content（当 content 为空时兜底用）。"""
        if resp is None:
            return ""
        d = _to_dict(resp)
        if d is not None:
            msg = d.get("message")
            msg_d = _to_dict(msg) if msg is not None else None
            if isinstance(msg_d, dict):
                for k in _REASONING_KEYS:
                    t = _normalize_text(msg_d.get(k))
                    if t:
                        return t
        if hasattr(resp, "message") and resp.message is not None:
            m = resp.message
            for k in _REASONING_KEYS:
                t = _normalize_text(getattr(m, k, None))
                if t:
                    return t
        return ""

    # SOP V8.6：Qwen 3.5 等思考模型 — 尝试 think=False 关闭 thinking 流；流式消费必须在 try 外执行
    first_chunk_debug = None
    _opts = {"temperature": 0.7, "top_p": 0.9, "num_predict": 800, "repeat_penalty": 1.1}
    _chat_kw = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True, "options": _opts}
    try:
        try:
            stream = client.chat(**{**_chat_kw, "think": False})
        except TypeError:
            stream = client.chat(**_chat_kw)
    except Exception as e:
        yield f"\n\n⚠️ 生成中断：{e}"
        return

    emitted = False
    _log = __import__("logging").getLogger(__name__)
    for chunk in stream:
        if first_chunk_debug is None:
            first_chunk_debug = chunk
        text = _extract_chunk_text(chunk)
        if not text and hasattr(chunk, "message") and getattr(chunk.message, "thinking", None):
            _log.debug("判词流: 收到 thinking 块，跳过展示，等待 content。")
        if text:
            for char in text:
                emitted = True
                yield char
                if typing_delay > 0:
                    time.sleep(typing_delay)
                if char in _BREATH_PUNCTUATION and breath_pause > 0:
                    time.sleep(breath_pause)

    try:
        if not emitted:
            try:
                _fallback_kw = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False, "options": _opts}
                try:
                    resp = client.chat(**{**_fallback_kw, "think": False})
                except TypeError:
                    resp = client.chat(**_fallback_kw)
                full = _extract_full_message(resp, content_only=True)
                # Qwen 3.5 等有时只填 message.thinking、message.content 为空，用 thinking 兜底并加说明
                if not full:
                    thinking = _extract_thinking(resp)
                    if thinking:
                        full = (
                            "【说明】当前模型未单独返回判词正文，以下为模型思考过程（含推理与结论），供参考。"
                            "若思考过程为英文，系模型默认推理语言；已在 prompt 中要求其使用简体中文，可重试一次。\n\n"
                            + thinking
                        )
                if full:
                    for char in full:
                        yield char
                        if typing_delay > 0:
                            time.sleep(typing_delay)
                        if char in _BREATH_PUNCTUATION and breath_pause > 0:
                            time.sleep(breath_pause)
                    return
            except Exception:
                pass
            debug_parts = []
            if first_chunk_debug is not None:
                debug_parts.append(f"首 chunk: {type(first_chunk_debug).__name__}")
                d = _to_dict(first_chunk_debug)
                if d is not None:
                    debug_parts.append(f"d_keys={list(d.keys())}")
                    msg = d.get("message")
                    if msg is not None:
                        msg_d = _to_dict(msg)
                        if isinstance(msg_d, dict):
                            debug_parts.append(f"message_keys={list(msg_d.keys())}")
                            for k in ("content", "text", "thinking", "role"):
                                v = msg_d.get(k)
                                if v is not None:
                                    s = str(v)[:80] + ("..." if len(str(v)) > 80 else "")
                                    debug_parts.append(f"message.{k}={s!r}")
                        else:
                            debug_parts.append(f"message_type={type(msg).__name__}")
                    if hasattr(first_chunk_debug, "message") and first_chunk_debug.message is not None:
                        m = first_chunk_debug.message
                        # SOP V8.1：确认 Qwen 是否把内容放在 reasoning_content / thinking
                        for k in ("content", "text", "thinking", "reasoning_content", "body"):
                            v = getattr(m, k, None)
                            if v is not None:
                                s = str(v)[:80] + ("..." if len(str(v)) > 80 else "")
                                debug_parts.append(f"msg.{k}={s!r}")
                        # 检查 message.__dict__ 是否被 Pydantic 私有字段拦截
                        if hasattr(m, "__dict__"):
                            pub = [x for x in getattr(m, "__dict__", {}).keys() if not str(x).startswith("_")]
                            if pub:
                                debug_parts.append(f"msg.__dict__ keys={pub[:15]}")
                else:
                    attrs = [x for x in dir(first_chunk_debug) if not x.startswith("_")][:12]
                    debug_parts.append(f"属性={attrs}")
            yield f"\n\n⚠️ 模型 `{model}` 未返回可见文本。 " + " | ".join(debug_parts)
    except Exception as e:
        yield f"\n\n⚠️ 生成中断：{e}"
