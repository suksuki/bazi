"""结构类意志「影子预览」：预判 VF 行与格局预警（仅 is_preview 路径，不落库）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.logic.patterns.l2_summary import sanitize_pattern_headline_zh

# V9.1：与 L2 空命中口径一致（禁止「平常局」）
_NO_SIGNIFICANT_PATTERN_LABELS = frozenset({"常规格", "常规格 (无显著格局)"})

# 与前端 `buildStructuralPreviewHintForCard` 对齐的可信 kind 白名单
STRUCTURAL_PREVIEW_KINDS = frozenset(
    {
        "L1_STRUCTURE",
        "PLUGIN_ENABLE",
        "LOGIC_OVERRIDE",
        "SEMANTIC_VERDICT",
        "PATTERN_SOVEREIGNTY",
    }
)


def normalize_structural_preview_hint(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    kind = str(raw.get("kind") or "").strip()
    if kind not in STRUCTURAL_PREVIEW_KINDS:
        return None
    card_id = str(raw.get("card_id") or "").strip()
    label = str(raw.get("label") or "").strip()
    plugin_id = str(raw.get("plugin_id") or "").strip()
    override_key = str(raw.get("override_key") or "").strip()
    if kind == "L1_STRUCTURE" and not label:
        return None
    if kind == "SEMANTIC_VERDICT" and not label and not card_id:
        return None
    if kind == "PLUGIN_ENABLE" and not plugin_id:
        return None
    if kind == "LOGIC_OVERRIDE" and not override_key:
        return None
    base_k = str(raw.get("baseline_pattern_kind") or "").strip()
    base_n = str(raw.get("baseline_pattern_name_zh") or "").strip()
    if kind == "PATTERN_SOVEREIGNTY":
        return {
            "kind": kind,
            "card_id": card_id,
            "label": label,
            "plugin_id": plugin_id,
            "override_key": override_key,
            "baseline_pattern_kind": base_k,
            "baseline_pattern_name_zh": base_n,
        }
    out = {
        "kind": kind,
        "card_id": card_id,
        "label": label,
        "plugin_id": plugin_id,
        "override_key": override_key,
        "baseline_pattern_kind": base_k,
        "baseline_pattern_name_zh": base_n,
    }
    return out


def build_structural_preview_vf_payloads(hint: Dict[str, Any]) -> List[Dict[str, Any]]:
    """SSE `vf_discovered`：中文 fallback + i18n 模板键（前端 locales）。"""
    kind = str(hint.get("kind") or "")
    label = str(hint.get("label") or "").strip()
    plugin_id = str(hint.get("plugin_id") or "").strip()
    override_key = str(hint.get("override_key") or "").strip()
    if kind == "L1_STRUCTURE":
        zh = f"[PREVIEW] 预期激活 [{label}]"
        return [{"line": zh, "i18n_template": "shadowPreview.vf.l1Activate", "i18n_params": {"label": label}}]
    if kind == "PLUGIN_ENABLE":
        zh = f"[PREVIEW] 预期启用插件 [{plugin_id}]"
        return [{"line": zh, "i18n_template": "shadowPreview.vf.pluginEnable", "i18n_params": {"plugin_id": plugin_id}}]
    if kind == "LOGIC_OVERRIDE":
        zh = f"[PREVIEW] 预期覆盖逻辑参数 [{override_key}]"
        return [{"line": zh, "i18n_template": "shadowPreview.vf.logicOverride", "i18n_params": {"override_key": override_key}}]
    if kind == "SEMANTIC_VERDICT":
        tail = label or "语义断语归档"
        zh = f"[PREVIEW] 预期归档语义意志：{tail}"
        return [{"line": zh, "i18n_template": "shadowPreview.vf.semanticVerdict", "i18n_params": {"tail": tail}}]
    if kind == "PATTERN_SOVEREIGNTY":
        tail = label or "格局主权与 L1 叙事仲裁"
        zh = f"[PREVIEW] 预期强化结构意志：{tail}"
        return [{"line": zh, "i18n_template": "shadowPreview.vf.patternSovereignty", "i18n_params": {"tail": tail}}]
    return []


_CRITICAL_COLLAPSE_ZH = "[CRITICAL] 结构性破坏：当前意志可能导致格局彻底解体。"


def _norm_pattern_name_zh(raw: Any) -> str:
    return sanitize_pattern_headline_zh(str(raw or "").strip())


def _pattern_snapshot_known(pattern_kind: Any, pattern_name_zh: Any) -> bool:
    k = str(pattern_kind or "").strip().lower()
    n = _norm_pattern_name_zh(pattern_name_zh)
    if k and k != "none":
        return True
    if n and n not in _NO_SIGNIFICANT_PATTERN_LABELS:
        return True
    return False


def _pattern_snapshot_unknown_chaotic(pattern_kind: Any, pattern_name_zh: Any) -> bool:
    k = str(pattern_kind or "").strip().lower()
    n = _norm_pattern_name_zh(pattern_name_zh)
    if k == "none":
        return (not n) or (n in _NO_SIGNIFICANT_PATTERN_LABELS)
    return False


def build_structural_preview_pattern_alert_bundle(
    hint: Dict[str, Any], physics_tensor: Dict[str, Any]
) -> Dict[str, Any]:
    """
    格局预警：fallback_zh 供兼容；i18n 为 {template, params} 供前端 STATIC_I18N。
    若 baseline 已知格且本轮退化为未定型常规态，则 CRITICAL 模板。
    """
    kind = str(hint.get("kind") or "")
    label = str(hint.get("label") or "").strip()
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    pp = meta.get("pattern_profile") if isinstance(meta.get("pattern_profile"), dict) else {}
    sovereignty = bool(pp.get("sovereignty_priority"))
    post_k = pp.get("pattern_kind")
    post_n = pp.get("pattern_name_zh")
    base_k = hint.get("baseline_pattern_kind")
    base_n = hint.get("baseline_pattern_name_zh")

    parts: List[str] = []
    if kind == "L1_STRUCTURE":
        parts.append("地支结构锁定可能抬升合局五行场强，因果路由与格局表述存在跃迁风险。")
        if label:
            parts.append(f"对象：{label}。")
    elif kind == "PLUGIN_ENABLE":
        parts.append("插件开关变更将重算入选轨迹与子域特征，平衡点与用神叙事可能整体重塑。")
    elif kind == "LOGIC_OVERRIDE":
        parts.append("逻辑参数覆盖将改变 L0–L2 交互权重，终判锚点与风险段可能发生位移。")
    elif kind == "SEMANTIC_VERDICT":
        parts.append("语义断语归档将写入记忆轨，与物理事实并行约束终判表述。")
    elif kind == "PATTERN_SOVEREIGNTY":
        parts.append("格局主权与 L1 对抗域并存时，结构意志可能触发仲裁叠加。")
    if sovereignty:
        parts.append("当前盘面已标注格局主权：请复核从格/化格叙事与结构补丁的兼容性。")
    soft = "".join(parts).strip()

    if _pattern_snapshot_known(base_k, base_n) and _pattern_snapshot_unknown_chaotic(post_k, post_n):
        prev_tag = str(base_n or base_k or "已知格").strip()
        tail = soft
        fallback = (
            f"{_CRITICAL_COLLAPSE_ZH}（相对悬停前快照「{prev_tag}」→本轮推演 meta.pattern_profile 已为未定型/混乱态。）"
            + (f" {tail}" if tail else "")
        ).strip()
        return {
            "fallback_zh": fallback,
            "i18n": {
                "template": "shadowPreview.pattern.critical",
                "params": {"prev_tag": prev_tag, "tail": tail},
            },
        }

    parts_i18n: List[Dict[str, Any]] = []
    if kind == "L1_STRUCTURE":
        parts_i18n.append({"template": "shadowPreview.pattern.l1Intro", "params": {}})
        if label:
            parts_i18n.append({"template": "shadowPreview.pattern.l1Label", "params": {"label": label}})
    elif kind == "PLUGIN_ENABLE":
        parts_i18n.append({"template": "shadowPreview.pattern.pluginEnable", "params": {}})
    elif kind == "LOGIC_OVERRIDE":
        parts_i18n.append({"template": "shadowPreview.pattern.logicOverride", "params": {}})
    elif kind == "SEMANTIC_VERDICT":
        parts_i18n.append({"template": "shadowPreview.pattern.semanticVerdict", "params": {}})
    elif kind == "PATTERN_SOVEREIGNTY":
        parts_i18n.append({"template": "shadowPreview.pattern.patternSovereignty", "params": {}})
    if sovereignty:
        parts_i18n.append({"template": "shadowPreview.pattern.sovereigntyHint", "params": {}})

    if soft and parts_i18n:
        return {"fallback_zh": soft, "i18n": {"parts": parts_i18n}}
    if soft:
        return {"fallback_zh": soft, "i18n": None}
    return {"fallback_zh": "", "i18n": None}
