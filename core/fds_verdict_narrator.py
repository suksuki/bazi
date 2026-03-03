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
        overlay_lines.append(
            f"- {i}. {pid} · D_M={d_val:.4f} · 匹配度≈{aff:.1f}% · 状态={item.get('status', '')}"
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

    prompt = f"""你是一名 FDS 2.0 时代的「量子命运物理审计师」，任务是在严格遵守物理证据的前提下，生成一段简洁、深刻的中文判词。
请务必遵守：不得编造与下述物理证据相矛盾的内容，不得给出绝对化的吉凶结论。

====================
【一、物理证据层（Evidence Layer）】
- 主权格局: {pattern_id}
- 当前主权状态: {state_cn}
- 主权 D_M: {d_m:.4f}
- 主权匹配度 (Affinity): {affinity:.2f}%

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
【二、古典原典与判例（RAG Layer）】
以下是与该格局相关的古典原话/判例，请在判词中至少引用或转译其中 1 条，并与上述 5D 物理状态相呼应：
{rag_block}
"""
    if ranked_classical:
        sovereign = [x for x in ranked_classical if x.get("llm_role") == "sovereign"]
        modifier = [x for x in ranked_classical if x.get("llm_role") == "modifier"]
        accessory = [x for x in ranked_classical if x.get("llm_role") == "accessory"]
        lines = []
        _et_cn = {"high": "高", "mid": "中", "low": "低"}
        if sovereign:
            parts = [f"{x.get('classical_name', '')}（成色：{_et_cn.get(x.get('energy_tier', 'mid'), '中')}）" for x in sovereign]
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
            prompt += "【定性描述（SOP V7.7）】成色 high 时可用「格成极真、富贵自天来」；成色 low 时须用「格局虽成，然根基尚浅，需步步为营」等弹性表述，名分在而贵贱由成色定。\n"
    prompt += f"""

====================
【三、叙事生成指令（Narrative Layer）】
1. 结构：按「原局格局特征 → 当前时空状态（大运/流年/地域）→ 风险与张力 → 走向与建议」四段式展开。
2. 风格：{tone}
3. 物理约束：必须在文中体现 D_M 与匹配度的含义；状态为 BROKEN 时须描述结构坍缩/引力场断裂，不得宣称必然灾祸。
4. 语言：仅用简体中文，语气冷静、可带诗意，不煽情。长度 200～300 字。
"""
    if ranked_classical:
        prompt += "5. 法理主次：若有上述「古典法理主次」列表，判词须按主权→修饰→注脚的顺序组织古典格局表述，使叙事有血有肉、层次分明。\n"
    if pattern_change_trigger:
        prompt += "\n【格局岁运迁移（SOP V7.5）】以下为岁运成格/岁运破格提示，判词中须有所体现：\n"
        for t in pattern_change_trigger:
            prompt += f"- {t}\n"
    prompt += """
请直接输出判词正文（Markdown 段落即可，无需重复标题）："""
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

    try:
        stream = client.generate(
            model=model,
            prompt=prompt,
            stream=True,
            options={"temperature": 0.7, "top_p": 0.9, "num_predict": 600},
        )
        for chunk in stream:
            text = ""
            if isinstance(chunk, dict):
                text = chunk.get("response", "") or chunk.get("text", "")
            elif hasattr(chunk, "response"):
                text = chunk.response or ""
            else:
                text = str(chunk)
            for char in text:
                yield char
                if typing_delay > 0:
                    time.sleep(typing_delay)
                if char in _BREATH_PUNCTUATION and breath_pause > 0:
                    time.sleep(breath_pause)
    except Exception as e:
        yield f"\n\n⚠️ 生成中断：{e}"
