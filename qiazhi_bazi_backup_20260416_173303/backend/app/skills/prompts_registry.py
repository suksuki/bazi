from __future__ import annotations

from typing import Any, Dict, List, Tuple

SCENE_ARBITER = "SCENE_ARBITER"
SCENE_ARCHITECT = "SCENE_ARCHITECT"
SCENE_PROPHET = "SCENE_PROPHET"

_PROBE_QUERY_STRUCTURAL_GATING = "VF.structural_tags 为空，请先完成格局定性（例如：财格/官格/从格/常规格）并给出依据。"
_OUTPUT_PURGE_DIRECTIVE = "禁止输出任何关于系统状态、流程说明、免责声明或对照提示的文字。仅输出命理断言内容。"
_NO_PROCESS_DIRECTIVE = "DO NOT talk about your process. Output the result directly in the specified format."
_PROMPT_USER_PREFIX = (
    "[命理核心数据包·即时裁决]\n"
    "首句必须从【格局】入手直接定性（如“此命财官双美...”或“寅巳穿害损局严重...”），禁止任何开场白。\n\n"
)
_PROMPT_USER_SUFFIX = "\n输出指令：仅输出四段式命理断言正文。禁止输出思考过程。"


def _as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _extract_structural_tags(metadata: Dict[str, Any]) -> List[str]:
    md = _as_dict(metadata)
    out: List[str] = []
    va = _as_dict(md.get("verdict_anchor_layer"))
    for k in ("structural_tags", "structure_tags"):
        raw = va.get(k)
        if isinstance(raw, list):
            out.extend([str(x).strip() for x in raw if str(x).strip()])
    li = _as_dict(md.get("logic_introspection"))
    vf = _as_dict(li.get("vf"))
    raw2 = vf.get("structural_tags")
    if isinstance(raw2, list):
        out.extend([str(x).strip() for x in raw2 if str(x).strip()])
    pp = _as_dict(_as_dict(md.get("history_context")).get("pattern_profile"))
    pk = str(pp.get("pattern_kind") or "").strip()
    if pk:
        out.append(pk)
    return list(dict.fromkeys(out))


def route_final_verdict_scene(metadata: Dict[str, Any]) -> Dict[str, Any]:
    md = _as_dict(metadata)
    flow_state = str(md.get("flow_state") or "").strip().lower()
    has_pending_probe = False
    pl = _as_dict(md.get("persistence_layer"))
    ir = _as_dict(pl.get("interrupt_request"))
    if str(ir.get("state") or "").strip().lower() == "pending":
        has_pending_probe = True
    if str(ir.get("probe_query") or "").strip():
        has_pending_probe = True
    points = _as_dict(md.get("conflict_matrix")).get("points")
    conflict_count = len(points) if isinstance(points, list) else 0

    structural_tags = _extract_structural_tags(md)
    no_structure = len(structural_tags) == 0

    # V13.60 Prophet Protocol: if conflict points exist, force Prophet.
    if conflict_count > 0:
        return {
            "scene": SCENE_PROPHET,
            "routing_reason": "conflict_forced_prophet",
            "structural_tags": structural_tags,
            "requires_internal_probe": False,
            "internal_probe_query": "",
        }
    if flow_state == "probe_waiting" or has_pending_probe:
        return {
            "scene": SCENE_ARBITER,
            "routing_reason": "flow_or_conflict_pending",
            "structural_tags": structural_tags,
            "requires_internal_probe": False,
            "internal_probe_query": "",
        }
    if no_structure:
        return {
            "scene": SCENE_ARCHITECT,
            "routing_reason": "structural_tags_missing",
            "structural_tags": structural_tags,
            "requires_internal_probe": True,
            "internal_probe_query": _PROBE_QUERY_STRUCTURAL_GATING,
        }
    return {
        "scene": SCENE_PROPHET,
        "routing_reason": "structure_ready",
        "structural_tags": structural_tags,
        "requires_internal_probe": False,
        "internal_probe_query": "",
    }


def scene_system_directive(scene: str) -> str:
    s = str(scene or SCENE_PROPHET).strip().upper()
    if s == SCENE_ARBITER:
        return (
            "[SCENE_ROUTER]\n"
            "当前场景=SCENE_ARBITER。你是冲突仲裁器，优先处理冲突分歧与证据链一致性，"
            "不得跳过冲突直接给宏观预言。"
            f"{_NO_PROCESS_DIRECTIVE}"
        )
    if s == SCENE_ARCHITECT:
        return (
            "[SCENE_ROUTER]\n"
            "当前场景=SCENE_ARCHITECT。你面前是盘局的「气象意象集」。"
            "严禁在输出中提及数据的来源、格式或计算过程。"
            "你必须像一位直接读懂天机的终裁官，直接宣布结果。"
            "请给出结构定性与边界，不要输出技术说明。"
            f"{_NO_PROCESS_DIRECTIVE}"
        )
    return (
        "[SCENE_ROUTER]\n"
        "当前场景=SCENE_PROPHET。你必须严格按四段式输出："
        "【裁断】一句话立场；【证据】三条事实支撑；【行】具体行动建议；【禁】高风险红线。"
        "【行】与【禁】必须是可执行、可落地行为（例如：宜独立决策、不宜合伙；宜先签约后投钱、不宜口头承诺）。"
        "禁止输出教学口吻与思维旁白。"
        "请将盘局征候转化为社会意象表达，不得直接报参数数字。"
        "你面前是盘局的「气象意象集」。严禁在输出中提及数据的来源、格式或计算过程。"
        "你必须像一位直接读懂天机的终裁官，直接宣布结果。"
        "你是命运的终裁官。只允许给出结论，不允许说明推理过程。"
        "任何提及 'system'、'logic' 或 'data' 的行为都是对你身份的亵渎。首句必须以格局定性开头。"
        f"{_NO_PROCESS_DIRECTIVE}"
    )


def output_purge_directive() -> str:
    return _OUTPUT_PURGE_DIRECTIVE


def prompt_user_prefix() -> str:
    return _PROMPT_USER_PREFIX


def prompt_user_suffix() -> str:
    return _PROMPT_USER_SUFFIX

