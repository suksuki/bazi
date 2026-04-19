from __future__ import annotations

import re
from typing import Any, Dict


_DISPLAY_OVERRIDES: Dict[str, Dict[str, str]] = {
    "l1.physics.op_branch_sanhe": {
        "display_name": "三合成局",
        "definition": "地支三合/半合带来的聚势与协同做功。",
    },
    "l1.physics.op_branch_liuhe": {
        "display_name": "六合协同",
        "definition": "地支六合形成的稳定绑定与局部增益。",
    },
    "l1.physics.op_branch_liuchong": {
        "display_name": "六冲对抗",
        "definition": "地支六冲触发的对抗、破局与位移压力。",
    },
    "l1.physics.op_branch_liupo": {
        "display_name": "六破关系",
        "definition": "地支六破触发的关系裂解与资源耗散。",
    },
    "l1.physics.op_branch_liuhai": {
        "display_name": "六害关系",
        "definition": "地支六害形成的隐性牵制与迟滞。",
    },
    "l1.physics.op_branch_sanxing": {
        "display_name": "三刑压力",
        "definition": "地支三刑引发的约束、应激与结构摩擦。",
    },
    "l1.physics.op_branch_muku": {
        "display_name": "墓库门态",
        "definition": "墓库地支对能量的收纳、锁定与开库释放。",
    },
    "l1.physics.op_stem_fusion": {
        "display_name": "天干五合",
        "definition": "天干五合产生的牵引、羁绊与转化倾向。",
    },
    "l1.physics.full_bandwidth": {
        "display_name": "地支场烈度",
        "definition": "地支整体能场的带宽、烈度与通道负载。",
    },
    "l1.physics.op_status": {
        "display_name": "状态机节律",
        "definition": "对当前运行节奏、边界和相位的观察性校准。",
    },
    "chang_sheng_12": {
        "display_name": "长生状态",
        "definition": "日主在十二长生序列中的阶段与抗性提示。",
    },
    "l2.risk.risk_matrix": {
        "display_name": "官伤风险矩阵",
        "definition": "围绕羊刃、枭神、官伤等高阶风险结构的检测与提示。",
    },
    "narrative_clip": {
        "display_name": "叙事剪辑",
        "definition": "将物理事实翻译为现代执行建议的叙事插件。",
    },
    "modern.will_proxy.v1": {
        "display_name": "意图代理",
        "definition": "将用户意图映射到叙事偏置层的现代代理插件。",
    },
    "modern.wealth_risk.v1": {
        "display_name": "财富风险代理",
        "definition": "对现代财富风险叙事做兼容映射的代理插件。",
    },
    "classical.wangshuai.v1": {
        "display_name": "旺衰框架",
        "definition": "经典旺衰评估框架的兼容占位插件。",
    },
}


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _trim_sentence(text: str) -> str:
    text = _clean_text(text)
    if not text:
        return ""
    text = re.sub(r"[。；;:：]+$", "", text)
    return text


def _first_phrase(text: str) -> str:
    text = _trim_sentence(text)
    if not text:
        return ""
    parts = re.split(r"[。；;:：,，]", text, maxsplit=1)
    return parts[0].strip()


def _derive_name_from_text(text: str) -> str:
    phrase = _first_phrase(text)
    if not phrase:
        return ""
    phrase = re.sub(r"^(检测到|高阶|现代|基于|用于|围绕)", "", phrase).strip()
    phrase = re.sub(r"(通用)?(协同)?(性)?算法$", "", phrase).strip()
    phrase = re.sub(r"(结构)?检测矩阵$", "风险矩阵", phrase).strip()
    phrase = re.sub(r"插件$", "", phrase).strip()
    return phrase[:24].strip()


def plugin_display_profile(
    *,
    plugin_id: Any,
    manifest: Dict[str, Any] | None = None,
    summary: Any = "",
    rationale: Any = "",
    module_doc: Any = "",
    spec_doc: Any = "",
) -> Dict[str, str]:
    pid = str(plugin_id or "").strip()
    manifest = manifest if isinstance(manifest, dict) else {}
    summary_text = _trim_sentence(
        manifest.get("Description")
        or manifest.get("summary")
        or manifest.get("display_definition")
        or summary
    )
    rationale_text = _trim_sentence(
        manifest.get("Rationale")
        or manifest.get("rationale")
        or manifest.get("display_description")
        or rationale
    )
    module_text = _trim_sentence(module_doc)
    spec_text = _trim_sentence(spec_doc)
    override = _DISPLAY_OVERRIDES.get(pid, {})

    display_name = _trim_sentence(
        override.get("display_name")
        or manifest.get("DisplayName")
        or manifest.get("display_name")
        or manifest.get("Name")
        or manifest.get("name")
        or _derive_name_from_text(summary_text)
        or _derive_name_from_text(module_text)
        or pid
    )
    display_definition = _trim_sentence(
        override.get("definition")
        or summary_text
        or module_text
        or spec_text
        or "该插件已接入 V17 推理链路，但尚未补齐定义说明"
    )
    display_description = _trim_sentence(
        rationale_text
        or summary_text
        or module_text
        or spec_text
        or "暂无补充说明"
    )
    technical_label = pid or "unknown_plugin"
    family = technical_label.split(".")[-1] if technical_label else ""
    return {
        "display_name": display_name,
        "display_definition": display_definition,
        "display_description": display_description,
        "technical_label": technical_label,
        "family_label": family,
    }


def plugin_source_label(source: Any, *, fallback: Any = "") -> str:
    raw = str(source or "").strip()
    if not raw:
        return _trim_sentence(fallback) or "未知规则"
    override = _DISPLAY_OVERRIDES.get(raw, {})
    if override.get("display_name"):
        return str(override["display_name"]).strip()
    text_fallback = _trim_sentence(fallback)
    if text_fallback:
        derived = _derive_name_from_text(text_fallback)
        if derived:
            return derived
    if raw.startswith("l2."):
        tail = raw.split(".")[-1]
        return _derive_name_from_text(tail.replace("_", " ")) or raw.replace("l2.", "L2:", 1)
    if raw.startswith("l1."):
        tail = raw.split(".")[-1]
        return _derive_name_from_text(tail.replace("_", " ")) or raw.replace("l1.", "L1:", 1)
    return raw
