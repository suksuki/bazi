"""
FDS AI Engine - 流形语义生成 (Manifold-to-Text)
===============================================
对接本地 Ollama/vLLM，将 5D 物理偏移转化为「物理逻辑一致」的深度判词。

- 输入：命例在 5D 空间的 point、相对质心的 offset、十神分布、矩阵版本
- 输出：Qwen-32B 生成的语义解读（性格/倾向微调，非二元结论）

Compliance: 公理三（量子概率性）、零硬编码（参数从 config 读取）
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 5D 轴语义（与 hkb_params 一致，仅作 Prompt 说明用，不写死阈值）
AXIS_SEMANTICS = {
    "E": "能量轴 (Energy)：身强/身弱、生命力能级",
    "O": "秩序轴 (Order)：社会地位、克制力、法律边界",
    "M": "财富轴 (Material)：资源拥有度、物质丰盈度",
    "S": "压力轴 (Stress)：环境应力、危机感",
    "R": "关系轴 (Relation)：逻辑深度、精神高度",
}

SYSTEM_PROMPT_5D = """你是一位精通命理学与物理建模的「流形解读师」。你的任务是根据命例在 5D 命运流形上的**物理坐标与偏移向量**，给出简洁、有逻辑的语义解读。

## 五轴含义（必须严格按此理解）
- **E (能量轴)**：身强/身弱、生命力能级。正值越大表示日主根基越稳、抗压能力越强。
- **O (秩序轴)**：社会地位、克制力、法律边界。与官星、纪律、管理能力相关。
- **M (财富轴)**：资源拥有度、物质丰盈度。与财星、资产、执行力相关。
- **S (压力轴)**：环境应力、危机感。压力大时需看是否有印比化解。
- **R (关系轴)**：逻辑深度、精神高度、人际与悟性。

## 输入说明
你会收到：
1. **5D 坐标** (point)：命例在当前矩阵下的 E/O/M/S/R 取值。
2. **偏移向量** (offset)：命例相对「最近质心」在各轴上的偏移（正=向该轴正向偏，负=向负向偏）。
3. **最近质心** (best_subpattern)：如 A-01-S1（身强任官）或 A-01-S2（财官双美）。
4. **矩阵版本**：物理校准矩阵版本号。

## 输出要求
1. **物理逻辑优先**：先根据偏移方向与幅度，说明「相对标准质心」在哪些轴上发生了何种方向的微调（例如：向 E 轴正向偏移 0.5 单位 → 能量略强于该子格局典型值）。
2. **性格/倾向**：用 1～3 句中文，概括这种偏移在现实中可能体现的性格或命运倾向微调，避免绝对化结论（如「一定」「必然」）。
3. **禁止**：不输出纯表格、不输出 JSON、不输出「仅供参考」等免责句。直接给出一段连贯的解读段落，控制在 150 字以内。
"""

# 默认 HKB 路径（A-01 语义核心从该文件注入）
_DEFAULT_HKB_PATH = Path(__file__).resolve().parent.parent / "config" / "hkb" / "hkb_params.json"


def _get_system_prompt_with_a01_semantic() -> str:
    """在基础 Prompt 后追加 A-01 正官格语义核心（立法），从 hkb_params 读取。"""
    base = SYSTEM_PROMPT_5D
    try:
        with open(_DEFAULT_HKB_PATH, "r", encoding="utf-8") as f:
            hkb = json.load(f)
        core = (hkb.get("hkb") or {}).get("a01_semantic_core")
        if not isinstance(core, dict):
            return base
        lines = [
            "",
            "## A-01 正官格语义核心（立法，必须遵循）",
        ]
        for key in ("dimension_a_order_rigidity", "dimension_b_energy_carrier", "dimension_c_wealth_coupling"):
            d = core.get(key)
            if not isinstance(d, dict):
                continue
            name = d.get("name", key)
            definition = d.get("definition", "")
            mapping = d.get("physical_mapping", "")
            axis = d.get("axis") or ", ".join(d.get("axes") or [])
            lines.append(f"- **{name}**（轴：{axis}）定义：{definition} 物理映射：{mapping}")
        if len(lines) > 2:
            base = base + "\n".join(lines)
        base += "\n\n## 动态演化（若输入中提供）\n若输入中包含【动态 5D 坐标】与【时间增量】，请对比原局与动态点的位移，给出**动态趋势分析**与**风险提示**（例如：S 轴突增、O 轴坍缩时，建议收缩扩张、稳固秩序）；结合古典「伤官见官」「财能生官」等法理，用 1～3 句概括该时段格局健康度与趋吉避凶要点。"
    except Exception as e:
        logger.debug("加载 A-01 语义核心失败，使用基础 Prompt: %s", e)
    return base


def _get_ollama_client():
    """从配置读取 ollama_host 并返回 Ollama 客户端（懒加载）。"""
    try:
        import ollama
    except ImportError:
        logger.warning("ollama 未安装，AI 判词不可用")
        return None
    cm = ConfigManager()
    host = cm.get("ollama_host") or "http://localhost:11434"
    if host and host != "http://localhost:11434":
        return ollama.Client(host=host)
    return ollama.Client()


def _build_user_prompt(
    point: Dict[str, float],
    offset: Dict[str, float],
    best_subpattern: str,
    matrix_version: str,
    ten_gods_summary: Optional[str] = None,
    dynamic_context: Optional[str] = None,
) -> str:
    """构建发给大模型的用户 Prompt（含物理数据、十神摘要与可选动态演化）。"""
    lines = [
        "请根据以下物理数据给出流形语义解读：",
        "",
        "【5D 坐标 point】",
        json.dumps(point, ensure_ascii=False, indent=2),
        "",
        "【相对质心的偏移向量 offset】",
        json.dumps(offset, ensure_ascii=False, indent=2),
        "",
        f"【最近质心子格局】{best_subpattern}",
        f"【矩阵版本】{matrix_version}",
    ]
    if ten_gods_summary:
        lines.append("")
        lines.append("【十神分布摘要】")
        lines.append(ten_gods_summary)
    if dynamic_context:
        lines.append("")
        lines.append("【动态演化】")
        lines.append(dynamic_context)
    return "\n".join(lines)


def generate_manifold_interpretation(
    point: Dict[str, float],
    offset: Dict[str, float],
    best_subpattern: str,
    matrix_version: str,
    ten_gods: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    timeout_sec: int = 60,
    dynamic_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    根据 5D 坐标与偏移向量，调用本地大模型生成「物理偏移感应式」判词。

    Args:
        point: 5D 坐标 {"E": float, "O": float, ...}
        offset: 相对质心偏移 {"E": float, ...}
        best_subpattern: 最近质心 ID，如 A-01-S1
        matrix_version: 矩阵版本号
        ten_gods: 十神向量（可选），用于生成摘要
        model: 模型名，默认从配置读取或 qwen2.5:32b
        timeout_sec: 请求超时秒数

    Returns:
        {
            "success": bool,
            "text": str,           # 生成的判词正文
            "model": str,
            "error": str | None,
        }
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    client = _get_ollama_client()
    if not client:
        result["error"] = "Ollama 未安装或不可用"
        return result

    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None)
    if not model_name:
        model_name = "qwen2.5:32b"

    ten_gods_summary = None
    if ten_gods:
        # 只取非零或主要几项，避免 prompt 过长
        parts = [f"{k}={v}" for k, v in sorted(ten_gods.items(), key=lambda x: -abs(x[1] if isinstance(x[1], (int, float)) else 0))[:6]]
        ten_gods_summary = ", ".join(parts)

    user_prompt = _build_user_prompt(
        point=point,
        offset=offset,
        best_subpattern=best_subpattern,
        matrix_version=matrix_version,
        ten_gods_summary=ten_gods_summary,
        dynamic_context=dynamic_context,
    )

    system_prompt = _get_system_prompt_with_a01_semantic()
    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"num_predict": 400},
        )
        # Ollama 返回格式: { "message": { "content": "..." } }
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("AI 判词调用失败")
        result["error"] = str(e)
    return result


def stream_manifold_interpretation(
    point: Dict[str, float],
    offset: Dict[str, float],
    best_subpattern: str,
    matrix_version: str,
    ten_gods: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    dynamic_context: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    流式生成判词，逐 chunk 产出，供 UI 打字机展示。
    成功时 yield 内容片段；失败时抛出异常。
    """
    client = _get_ollama_client()
    if not client:
        raise RuntimeError("Ollama 未安装或不可用")
    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"
    ten_gods_summary = None
    if ten_gods:
        parts = [f"{k}={v}" for k, v in sorted(ten_gods.items(), key=lambda x: -abs(x[1] if isinstance(x[1], (int, float)) else 0))[:6]]
        ten_gods_summary = ", ".join(parts)
    user_prompt = _build_user_prompt(point=point, offset=offset, best_subpattern=best_subpattern, matrix_version=matrix_version, ten_gods_summary=ten_gods_summary, dynamic_context=dynamic_context)
    system_prompt = _get_system_prompt_with_a01_semantic()
    stream = client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
        options={"num_predict": 400},
    )
    for chunk in stream:
        content = ""
        if isinstance(chunk, dict):
            content = (chunk.get("message") or {}).get("content", "") or ""
        elif hasattr(chunk, "message"):
            content = getattr(getattr(chunk, "message", None), "content", "") or ""
        if isinstance(content, str) and content:
            yield content


def is_ai_engine_available() -> bool:
    """检测本地 AI 引擎（Ollama）是否可用。"""
    client = _get_ollama_client()
    if not client:
        return False
    try:
        client.list()  # 简单列出模型即可验证连通
        return True
    except Exception:
        return False


__all__ = [
    "generate_manifold_interpretation",
    "stream_manifold_interpretation",
    "is_ai_engine_available",
    "AXIS_SEMANTICS",
    "SYSTEM_PROMPT_5D",
]
