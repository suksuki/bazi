#!/usr/bin/env python3
"""
SOP V6.7：LLM 判词生成实验脚本
================================
选取 3 个不同物理状态的样本（接近 PURE / 中度漂移 / 明显破格），
基于 5D 坐标 + D_M + 叠加态 + 古典 RAG 原典，构造三层嵌套 Prompt，
调用 LLM 生成判词，用于验证「物理驱动叙事」链路是否工作正常。

运行方式：
    python scripts/test_llm_verdict.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.engine import load_static_atlas
from core.manifold_trace import compute_dm_cloud, affinity_from_d_m
from core.dynamic_engine import build_dynamic_context_for_prompt
from core.rag_canon import query_citations, format_citations_for_prompt
from core.config_manager import ConfigManager


@dataclass
class SampleCase:
    name: str
    description: str
    point_5d: Dict[str, float]


def _pick_reference_pattern() -> Dict[str, Any]:
    """从 static_atlas 中选择一个带 centroid_5d 的参考格局（优先 A-47，其次首个可用格局）。"""
    atlas = load_static_atlas()
    patterns = atlas.get("patterns") or []
    chosen = None
    for p in patterns:
        if (p.get("pattern_id") or "").strip().upper() == "A-47" and p.get("centroid_5d"):
            chosen = p
            break
    if not chosen:
        for p in patterns:
            if p.get("centroid_5d"):
                chosen = p
                break
    if not chosen:
        raise RuntimeError("static_atlas 中缺少带 centroid_5d 的格局，无法构造测试样本。")
    return chosen


def _vec_add(a: List[float], b: List[float], scale: float = 1.0) -> List[float]:
    return [ai + scale * bi for ai, bi in zip(a, b)]


def _build_sample_cases() -> List[SampleCase]:
    """
    基于 atlas 质心构造三组 5D 样本：
    - case_pure: 直接取质心本身，D_M≈0，对应高匹配（接近 PURE）
    - case_mid: 在两个质心之间取中点，D_M 中等，对应 VERIFIED/DRIFTING 过渡带
    - case_far: 在质心连线方向上外推，D_M 明显偏大，对应 DRIFTING/BROKEN
    """
    atlas = load_static_atlas()
    patterns = [p for p in (atlas.get("patterns") or []) if p.get("centroid_5d")]
    if len(patterns) < 2:
        raise RuntimeError("static_atlas 中可用质心不足 2 个，无法构造对比样本。")

    p_ref = _pick_reference_pattern()
    cen_ref = [float(x) for x in p_ref["centroid_5d"]]

    # 选一个与参考格局质心差异明显的对照质心
    other = None
    best_dist = 0.0
    for p in patterns:
        if p is p_ref:
            continue
        cen = [float(x) for x in p["centroid_5d"]]
        d = math.sqrt(sum((cen[i] - cen_ref[i]) ** 2 for i in range(5)))
        if d > best_dist:
            best_dist = d
            other = cen
    if other is None:
        other = [float(x) for x in patterns[1]["centroid_5d"]]

    # 中点与外推点
    mid = [(a + b) / 2.0 for a, b in zip(cen_ref, other)]
    direction = [other[i] - cen_ref[i] for i in range(5)]
    far = _vec_add(cen_ref, direction, scale=2.0)

    def _to_dict(vec: List[float]) -> Dict[str, float]:
        from core.manifold_trace import DIM_ORDER

        return {k: float(vec[i]) for i, k in enumerate(DIM_ORDER)}

    return [
        SampleCase(
            name="PURE_like",
            description="接近格局质心的样本，用于模拟 PURE / VERIFIED 区域。",
            point_5d=_to_dict(cen_ref),
        ),
        SampleCase(
            name="MID_drift",
            description="处于两个格局质心中点的样本，用于模拟 VERIFIED → DRIFTING 过渡带。",
            point_5d=_to_dict(mid),
        ),
        SampleCase(
            name="FAR_broken",
            description="沿质心连线外推的远点，用于模拟 DRIFTING / BROKEN 区域。",
            point_5d=_to_dict(far),
        ),
    ]


def _build_llm_prompt(
    pattern_id: str,
    status: str,
    d_m: float,
    affinity: float,
    overlay: List[Dict[str, Any]],
    point_5d: Dict[str, float],
) -> str:
    """
    构造三层嵌套 Prompt：
    1）物理证据层：Top1 主权、D_M、匹配度、叠加态、5D 坐标
    2）原典 RAG 层：注入古典原话与判例
    3）叙事风格层：根据 PURE/VERIFIED/DRIFTING/BROKEN 调整语气与张力
    """
    # 物理证据层
    status = status.upper()
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

    # 动态演化文本（此处仅用静态 base/dynamic，对 time_delta/geo_factor 给出中性值）
    base_point = point_5d  # 简化：视当前点为动态点，相对“自身质心”的偏移由 D_M 体现
    dynamic_point = point_5d
    zero_vec = {k: 0.0 for k in point_5d.keys()}
    dynamic_context = build_dynamic_context_for_prompt(
        base_point=base_point,
        dynamic_point=dynamic_point,
        time_delta=zero_vec,
        geo_factor=zero_vec,
        luck_gan_zhi="",
        year_gan_zhi="",
        direction="",
    )

    # 原典 RAG 层
    citations = query_citations(pattern_id)
    rag_block = format_citations_for_prompt(citations) if citations else ""

    # 叙事风格控制
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

【5D 坐标与动态演化】
{dynamic_context}

====================
【二、古典原典与判例（RAG Layer）】
以下是与该格局相关的古典原话 / 判例，请在判词中至少引用或转译其中 1 条，并在逻辑上与上面的 5D 物理状态相呼应：
{rag_block}

====================
【三、叙事生成指令（Narrative Layer）】

1. 结构：按照「原局格局特征 → 当前时空状态 → 风险与张力 → 走向与建议」四段式展开。
2. 风格：{tone}
3. 物理约束：
   - 必须在文中显性或隐性地体现 D_M 与匹配度的含义（例如“已逼近临界半径”“仍在安全引力井内”等）。
   - 当状态为 BROKEN 时，必须描述“结构坍缩”或“引力场断裂”的含义，但不得宣称“必然灾祸”。
   - 当叠加态中存在第二主格时，可以点出“另一股引力场正在形成/干扰”，体现命运的多重可能。
4. 语言要求：
   - 只用简体中文，不要输出拼音或英文解释。
   - 语气像一位既懂物理又懂命理的冷静观察者，可以带一点诗意，但绝不煽情。
5. 长度：控制在 200～300 字之间。

现在，请基于以上所有信息，生成一段完整的判词（Markdown 段落即可，无需再重复标题或分隔线）："""
    return prompt


def _get_ollama_client_and_model():
    """根据系统配置获取 ollama Client 与模型名称。"""
    from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer

    synth = LLMSemanticSynthesizer()
    if not getattr(synth, "use_llm", False):
        return None, None
    client = getattr(synth, "_llm_client", None)
    model = getattr(synth, "model_name", None)
    return client, model


def run_experiment() -> None:
    """运行三组样本的 LLM 判词实验，将物理证据与判词结果一并打印到控制台。"""
    cases = _build_sample_cases()
    client, model = _get_ollama_client_and_model()
    if not client or not model:
        print("⚠️ LLM 客户端不可用或未配置模型，将仅打印物理证据与 Prompt 片段，跳过实际调用。")

    print("=== FDS 2.0 LLM 判词生成实验（SOP V6.7） ===\n")
    for idx, case in enumerate(cases, 1):
        print(f"\n==============================")
        print(f"【样本 {idx}: {case.name}】 {case.description}")
        print("==============================")

        trace = compute_dm_cloud(case.point_5d, top_k=3)
        overlay = trace.get("overlay") or []
        if not overlay:
            print("❌ compute_dm_cloud 未返回 overlay，跳过该样本。")
            continue
        top = overlay[0]
        pattern_id = top.get("pattern_id", "")
        status = top.get("status", "UNKNOWN")
        d_m = float(top.get("D_M", 0.0))
        affinity = affinity_from_d_m(d_m)

        print(f"- Top1 格局: {pattern_id}")
        print(f"- 状态 status: {status}")
        print(f"- D_M: {d_m:.4f}")
        print(f"- 匹配度 Affinity: {affinity:.2f}%")

        prompt = _build_llm_prompt(
            pattern_id=pattern_id,
            status=status,
            d_m=d_m,
            affinity=affinity,
            overlay=overlay,
            point_5d=trace.get("point_5d") or case.point_5d,
        )

        # 为调试方便，仅打印前若干行 Prompt
        print("\n--- Prompt 预览（前 40 行）---")
        preview_lines = prompt.splitlines()[:40]
        for line in preview_lines:
            print(line)

        if client and model:
            try:
                print("\n--- LLM 判词输出 ---")
                resp = client.generate(
                    model=model,
                    prompt=prompt,
                    stream=False,
                    options={"temperature": 0.7, "top_p": 0.9, "num_predict": 600},
                )
                if isinstance(resp, dict):
                    text = resp.get("response") or resp.get("text") or resp.get("content") or ""
                else:
                    text = str(resp)
                print(text.strip())
            except Exception as e:
                print(f"⚠️ LLM 调用失败: {e}")
        else:
            print("\n（LLM 未启用，仅完成物理证据与 Prompt 构造。）")


if __name__ == "__main__":
    run_experiment()

