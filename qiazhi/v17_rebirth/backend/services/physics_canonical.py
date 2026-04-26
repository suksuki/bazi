"""
V17.20：元数据中心（SSOT）——六柱与 LLM 事实行仅允许从后端 physics_tensor 物化，
禁止依赖 HTTP Body 回传的柱位字符串。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from v17_rebirth.backend.logic.climate_field_protocol import climate_field_prompt_lines
from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import normalize_blind_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import normalize_climate_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.xiangfa_theme_core import normalize_xiangfa_theme_meta
from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import normalize_bazi_image_meta
from v17_rebirth.backend.logic.L3_modern_narrative.macro_theme_core import normalize_macro_theme_meta
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import normalize_wealth_code_meta
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import normalize_wealth_profile_meta
from v17_rebirth.backend.logic.runtime_field_protocol import runtime_field_prompt_lines
from v17_rebirth.backend.services.physics_layers import read_runtime_scores

_PHYS_DASH = "\u2014"


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _cell_ok(value: Any) -> bool:
    s = str(value or "").strip()
    return bool(s) and s not in (_PHYS_DASH, "-")


def _meta_rows(pt: Dict[str, Any]) -> Dict[str, Any]:
    meta = pt.get("meta")
    return meta if isinstance(meta, dict) else {}


def _energy_meta_rows(pt: Dict[str, Any]) -> Dict[str, Any]:
    raw = pt.get("energy_meta")
    return raw if isinstance(raw, dict) else {}


def _relation_summary_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    energy_meta = _energy_meta_rows(pt)
    meta = _meta_rows(pt)
    raw = (
        energy_meta.get("relation_formation_summary")
        if isinstance(energy_meta.get("relation_formation_summary"), list)
        else meta.get("relation_formation_summary")
    )
    if not isinstance(raw, list) or not raw:
        return []
    rows = [
        "合化解释合同：以下百分比表示成局度/效率，不是十神能量百分比；需与家族基准倍数、源气保留比例和十神绝对强度合读。"
    ]
    ranked = sorted(
        (
            row for row in raw
            if isinstance(row, dict) and str(row.get("formation_label") or "").strip()
        ),
        key=lambda row: float(row.get("formation_percent") or 0.0),
        reverse=True,
    )
    for row in ranked[:3]:
        label = str(row.get("formation_label") or "").strip()
        percent = _safe_float(row.get("formation_percent"), 0.0)
        factor = _safe_float(row.get("family_factor"), 0.0)
        status = str(row.get("status") or "").strip()
        conflict_damping = _safe_float(row.get("conflict_damping"), 1.0)
        projection_preview = row.get("projection_preview") if isinstance(row.get("projection_preview"), list) else []
        fragments = [f"{label} {percent:.1f}%"]
        if factor > 0.0:
            fragments.append(f"基准x{factor:.2f}")
        source_retention_ratio = _safe_float(row.get("source_retention_ratio"), 1.0)
        if source_retention_ratio < 0.995:
            fragments.append(f"源气保留{round(source_retention_ratio * 100):.0f}%")
        if status:
            fragments.append(status)
        if conflict_damping < 0.995:
            fragments.append(f"受扰保留{round(conflict_damping * 100):.0f}%")
        if projection_preview:
            projection_text = " / ".join(
                str(item).strip() for item in projection_preview[:2] if str(item).strip()
            )
            if projection_text:
                fragments.append(f"主投影 {projection_text}")
        rows.append("合化摘要：" + "，".join(fragments[:5]))
    return rows


def _relation_dynamics_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    energy_meta = _energy_meta_rows(pt)
    meta = _meta_rows(pt)
    raw = (
        energy_meta.get("relation_dynamics_summary")
        if isinstance(energy_meta.get("relation_dynamics_summary"), list)
        else meta.get("relation_dynamics_summary")
    )
    if not isinstance(raw, list) or not raw:
        return []
    rows = [
        "关系动力学合同：刑冲克害破与合必须分开读能量与稳定性；冲偏激发，刑偏内耗，克偏压制转移，害偏暗损，破偏解构，合偏绑定/组织化。"
    ]
    ranked = sorted(
        (row for row in raw if isinstance(row, dict) and str(row.get("label") or "").strip()),
        key=lambda row: abs(_safe_float(row.get("stability_delta_ratio"), 0.0)) + _safe_float(row.get("energy_effect_ratio"), 0.0),
        reverse=True,
    )
    for row in ranked[:4]:
        label = str(row.get("label") or "").strip()
        energy_axis = str(row.get("energy_axis") or "").strip()
        energy_ratio = _safe_float(row.get("energy_effect_ratio"), 0.0)
        stability_delta = _safe_float(row.get("stability_delta_ratio"), 0.0)
        lock_ratio = _safe_float(row.get("free_energy_lock_ratio"), 0.0)
        note = str(row.get("note") or "").strip()
        fragments = [f"{label} {energy_axis}{round(energy_ratio * 100):.0f}%"]
        if abs(stability_delta) > 1e-6:
            sign = "+" if stability_delta > 0 else ""
            fragments.append(f"稳定{sign}{round(stability_delta * 100):.0f}%")
        if lock_ratio > 0.0:
            fragments.append(f"自由能锁定{round(lock_ratio * 100):.0f}%")
        if note:
            fragments.append(note)
        rows.append("关系动力学：" + "，".join(fragments[:4]))
    return rows


def _runtime_field_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    return runtime_field_prompt_lines()


def _climate_field_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    energy_meta = _energy_meta_rows(pt)
    climate = energy_meta.get("climate_field") if isinstance(energy_meta.get("climate_field"), dict) else {}
    modifier = energy_meta.get("climate_modifier_layer") if isinstance(energy_meta.get("climate_modifier_layer"), dict) else {}
    if not climate:
        return []
    rows = list(climate_field_prompt_lines())
    state = str(climate.get("state") or "").strip()
    thermal = _safe_float(climate.get("thermal_index"), 0.0)
    moisture = _safe_float(climate.get("moisture_index"), 0.0)
    tension = _safe_float(climate.get("climate_tension"), 0.0)
    by_element = climate.get("source_by_element") if isinstance(climate.get("source_by_element"), dict) else {}
    dominant_elements = sorted(
        (
            (str(element).strip(), abs(_safe_float(raw.get("thermal"), 0.0)) + abs(_safe_float(raw.get("moisture"), 0.0)))
            for element, raw in by_element.items()
            if str(element).strip() and isinstance(raw, dict)
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    element_fragments: List[str] = []
    for element, _score in dominant_elements[:2]:
        raw = by_element.get(element) if isinstance(by_element.get(element), dict) else {}
        element_fragments.append(
            f"{element} 热{_safe_float(raw.get('thermal'), 0.0):+.2f}/湿{_safe_float(raw.get('moisture'), 0.0):+.2f}"
        )
    rows.append(
        "调候摘要："
        f"{state or '未定'}"
        f"；寒热轴{thermal:+.2f}"
        f"；燥湿轴{moisture:+.2f}"
        f"；张力{tension:.2f}"
        + (f"；主来源 {' / '.join(element_fragments)}" if element_fragments else "")
    )
    if modifier:
        priority_map = modifier.get("yongshen_priority_delta") if isinstance(modifier.get("yongshen_priority_delta"), dict) else {}
        ranked = sorted(
            (
                (str(god).strip(), _safe_float(delta, 0.0))
                for god, delta in priority_map.items()
                if str(god).strip() and abs(_safe_float(delta, 0.0)) > 1e-6
            ),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        if ranked:
            preview = "；".join(f"{god}{delta:+.2f}" for god, delta in ranked[:3])
            rows.append("调候修正层：" + preview)
    return rows


def _climate_theme_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    climate_theme = normalize_climate_theme_meta(meta.get("climate_theme"))
    if not climate_theme:
        return []
    rows = [
        "调候专题合同：调候专题是 climate field 的 L2 解释层，只输出 evidence / narrative / report，不额外回写 L0 原始十神总量，也不再叠加 bias。",
    ]
    state = str(climate_theme.get("state") or "").strip()
    digest = str(climate_theme.get("prompt_digest") or "").strip()
    favored = climate_theme.get("favored_gods") if isinstance(climate_theme.get("favored_gods"), list) else []
    strained = climate_theme.get("strained_gods") if isinstance(climate_theme.get("strained_gods"), list) else []
    pattern_rows = climate_theme.get("pattern_survival") if isinstance(climate_theme.get("pattern_survival"), list) else []
    fragments: List[str] = []
    if state:
        fragments.append(state)
    if favored:
        fragments.append("顺势 " + "/".join(str(item).strip() for item in favored[:2] if str(item).strip()))
    if strained:
        fragments.append("承压 " + "/".join(str(item).strip() for item in strained[:2] if str(item).strip()))
    if pattern_rows:
        top = pattern_rows[0] if isinstance(pattern_rows[0], dict) else {}
        label = str(top.get("label") or top.get("key") or "").strip()
        bucket = str(top.get("bucket") or "").strip()
        if label:
            fragments.append(f"{label}{bucket}")
    if digest:
        fragments.append(digest)
    if fragments:
        rows.append("调候专题摘要：" + "；".join(fragment for fragment in fragments if fragment))
    return rows


def _xiangfa_theme_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    xiangfa_theme = normalize_xiangfa_theme_meta(meta.get("xiangfa_theme"))
    if not xiangfa_theme:
        return []
    rows = [
        "象法专题合同：象法专题当前只做 semantic mapping / evidence / narrative hint / event framing，不修改能量、不写入 bias，也不覆盖 authority。",
    ]
    semantic = (
        xiangfa_theme.get("semantic_mapping")
        if isinstance(xiangfa_theme.get("semantic_mapping"), list)
        else []
    )
    evidence = (
        xiangfa_theme.get("evidence")
        if isinstance(xiangfa_theme.get("evidence"), list)
        else []
    )
    hints = (
        xiangfa_theme.get("narrative_hint")
        if isinstance(xiangfa_theme.get("narrative_hint"), list)
        else []
    )
    framing = (
        xiangfa_theme.get("event_framing")
        if isinstance(xiangfa_theme.get("event_framing"), list)
        else []
    )
    digest = str(xiangfa_theme.get("prompt_digest") or "").strip()
    topics = (
        xiangfa_theme.get("source_topics")
        if isinstance(xiangfa_theme.get("source_topics"), list)
        else []
    )
    fragments: List[str] = []
    if semantic:
        fragments.append("语义 " + " / ".join(str(item).strip() for item in semantic[:2] if str(item).strip()))
    if framing:
        fragments.append("事件 " + " / ".join(str(item).strip() for item in framing[:2] if str(item).strip()))
    if hints:
        fragments.append("叙事 " + " / ".join(str(item).strip() for item in hints[:1] if str(item).strip()))
    if topics:
        fragments.append("来源 " + "/".join(str(item).strip() for item in topics[:3] if str(item).strip()))
    if digest:
        fragments.append(digest)
    if evidence:
        rows.append("象法证据：" + "；".join(str(item).strip() for item in evidence[:3] if str(item).strip()))
    if fragments:
        rows.append("象法专题摘要：" + "；".join(fragment for fragment in fragments if fragment))
    return rows


def _macro_theme_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    macro_theme = normalize_macro_theme_meta(meta.get("macro_theme"))
    if not macro_theme:
        return []
    rows = [
        "宏观象合同：宏观象是 L3 主题层，只读十神、体用、格局、盲派、象法、调候与关系动力；不得反写物理参数，也不得把弱主题写成强定论。",
    ]
    topics = macro_theme.get("topics") if isinstance(macro_theme.get("topics"), list) else []
    ranked = sorted(
        (row for row in topics if isinstance(row, dict) and str(row.get("id") or "").strip()),
        key=lambda row: float(row.get("score") or 0.0),
        reverse=True,
    )
    fragments: List[str] = []
    for row in ranked[:4]:
        label = str(row.get("label") or row.get("id") or "").strip()
        score = _safe_float(row.get("score"), 0.0)
        confidence = _safe_float(row.get("confidence"), 0.0)
        risk = _safe_float(row.get("risk"), 0.0)
        stance = str(row.get("stance") or "").strip()
        summary = str(row.get("summary") or "").strip()
        bits = [f"{label}{round(score * 100):.0f}%"]
        if stance:
            bits.append(stance)
        bits.append(f"置信{round(confidence * 100):.0f}%")
        if risk > 0.0:
            bits.append(f"风险{round(risk * 100):.0f}%")
        if summary:
            bits.append(summary[:80])
        fragments.append("，".join(bits[:5]))
    if fragments:
        rows.append("宏观象摘要：" + "；".join(fragments))
    digest = str(macro_theme.get("prompt_digest") or "").strip()
    if digest:
        rows.append("宏观象主线：" + digest)
    return rows


def _bazi_image_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    bazi_image = normalize_bazi_image_meta(meta.get("bazi_image"))
    if not bazi_image:
        return []
    rows = [
        "八字象义合同：bazi_image 是 L0 象义事实层，只说明天干、地支、十神、宫位、藏透和库象的材质；不得据此直接生成吉凶断语、体用裁决或参数修改。",
    ]
    day_master = str(bazi_image.get("day_master_stem") or "").strip()
    digest = str(bazi_image.get("prompt_digest") or "").strip()
    if day_master or digest:
        rows.append("八字象义摘要：" + "；".join(item for item in [f"日主{day_master}" if day_master else "", digest] if item))
    facts = bazi_image.get("symbolic_facts") if isinstance(bazi_image.get("symbolic_facts"), list) else []
    fact_bits: List[str] = []
    for fact in facts[:4]:
        if not isinstance(fact, dict):
            continue
        meaning = str(fact.get("plain_meaning") or "").strip()
        if meaning:
            fact_bits.append(meaning[:90])
    if fact_bits:
        rows.append("象义事实：" + "；".join(fact_bits))
    return rows


def _wealth_profile_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    wealth_profile = normalize_wealth_profile_meta(meta.get("wealth_profile"))
    if not wealth_profile:
        return []
    rows = [
        "财富解读合同：财富画像是 L3 专题解码层，只读底层事实；面向用户时必须翻译成收入来源、赚钱方式、现金流、合作、合同和风险控制，不得自行改写来源、风险或置信度。",
    ]
    score = _safe_float(wealth_profile.get("score"), 0.0)
    confidence = _safe_float(wealth_profile.get("confidence"), 0.0)
    risk = _safe_float(wealth_profile.get("risk"), 0.0)
    stance = str(wealth_profile.get("stance") or "").strip()
    visibility = str(wealth_profile.get("visibility") or "").strip()
    usable = str(wealth_profile.get("usable_state") or "").strip()
    rows.append(
        "财富分析摘要："
        f"收入机会{round(score * 100):.0f}%"
        f"；参考度{round(confidence * 100):.0f}%"
        f"；风险{round(risk * 100):.0f}%"
        + (f"；状态{stance}" if stance else "")
        + (f"；显性{visibility}" if visibility else "")
        + (f"；可用{usable}" if usable else "")
    )
    channels = wealth_profile.get("primary_channels") if isinstance(wealth_profile.get("primary_channels"), list) else []
    channel_bits: List[str] = []
    for row in channels[:3]:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or row.get("id") or "").strip()
        channel_score = _safe_float(row.get("score"), 0.0)
        if label:
            channel_bits.append(f"{label}{round(channel_score * 100):.0f}%")
    if channel_bits:
        rows.append("主要赚钱方式：" + "；".join(channel_bits))
    risks = wealth_profile.get("risks") if isinstance(wealth_profile.get("risks"), list) else []
    bridges = wealth_profile.get("bridge_requirements") if isinstance(wealth_profile.get("bridge_requirements"), list) else []
    if risks:
        rows.append("要避开的坑：" + "；".join(str(item).strip() for item in risks[:3] if str(item).strip()))
    if bridges:
        rows.append("要先做到：" + "；".join(str(item).strip() for item in bridges[:3] if str(item).strip()))
    return rows


def _wealth_code_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    wealth_code = normalize_wealth_code_meta(meta.get("wealth_code"))
    if not wealth_code:
        return []
    rows = [
        "财富密码合同：wealth_code 是 L3 财富路径解码层，只读 bazi_image、wealth_profile 和底层证据；面向用户时只写钱从哪里来、靠什么变现、如何接住和哪里漏钱，不得承诺金额或确定发财年份。",
    ]
    primary = wealth_code.get("primary_wealth_path") if isinstance(wealth_code.get("primary_wealth_path"), dict) else {}
    source = wealth_code.get("wealth_source") if isinstance(wealth_code.get("wealth_source"), dict) else {}
    carrier = wealth_code.get("carrier") if isinstance(wealth_code.get("carrier"), dict) else {}
    if primary:
        rows.append(
            "财富主路径："
            + str(primary.get("plain_name") or primary.get("id") or "").strip()
            + (f"；{str(primary.get('plain_summary') or '').strip()[:100]}" if primary.get("plain_summary") else "")
        )
    if source:
        rows.append("财源材质：" + str(source.get("plain_source") or source.get("material") or "").strip()[:120])
    if carrier:
        requirements = carrier.get("requirements") if isinstance(carrier.get("requirements"), list) else []
        if requirements:
            rows.append("财富承接：" + "；".join(str(item).strip() for item in requirements[:3] if str(item).strip()))
    leakage = wealth_code.get("leakage_points") if isinstance(wealth_code.get("leakage_points"), list) else []
    if leakage:
        rows.append(
            "漏财风险："
            + "；".join(
                str(row.get("plain_name") or "").strip()
                for row in leakage[:3]
                if isinstance(row, dict) and str(row.get("plain_name") or "").strip()
            )
        )
    return rows


def _pattern_summary_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    claims = meta.get("plugin_claims") if isinstance(meta.get("plugin_claims"), list) else []
    if not claims:
        return []
    candidates: Dict[str, Dict[str, Any]] = {}
    for row in claims:
        if not isinstance(row, dict):
            continue
        name = str(row.get("pattern_candidate") or row.get("pattern_name") or "").strip()
        if not name:
            continue
        confidence_raw = row.get("pattern_confidence_percent")
        if confidence_raw is None:
            confidence_raw = row.get("pattern_confidence")
        if confidence_raw is None:
            confidence_raw = row.get("match_ratio")
        confidence = _safe_float(confidence_raw, 0.0)
        if confidence <= 1.0:
            confidence *= 100.0
        confidence = max(0.0, min(100.0, confidence))
        target = str(row.get("target_god") or "").strip()
        scope = str(row.get("pattern_scope_label") or row.get("pattern_scope") or "").strip()
        key = f"{name}::{target or 'na'}"
        current = candidates.get(key)
        candidate = {
            "name": name,
            "confidence": round(confidence, 1),
            "target": target,
            "scope": scope,
        }
        if current is None or float(candidate["confidence"]) > float(current.get("confidence") or 0.0):
            candidates[key] = candidate
    ranked = sorted(candidates.values(), key=lambda row: float(row.get("confidence") or 0.0), reverse=True)
    if not ranked:
        return []
    rows = ["格局解释合同：以下百分比表示格局拟合度/置信度，不直接改写十神能量；应与原局、运流和做功链条合读。"]
    fragments: List[str] = []
    for row in ranked[:3]:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        confidence = _safe_float(row.get("confidence"), 0.0)
        target = str(row.get("target") or "").strip()
        scope = str(row.get("scope") or "").strip()
        bits = [f"{name} {confidence:.1f}%"]
        if target:
            bits.append(f"主落点 {target}")
        if scope:
            bits.append(scope)
        fragments.append("，".join(bits[:3]))
    if fragments:
        rows.append("格局摘要：" + "；".join(fragments))
    return rows


def _ten_gods_prompt_contract_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    return [
        "十神解释合同：`ten_gods_base_l0/ten_gods_runtime` 为绝对物理强度，不是百分比。",
        "十神解释合同：单个十神总分应理解为显化、根气、势能、潜藏残值的合成结果，不能当作单一来源。",
        "十神解释合同：显化内部还包含柱位贴身权重；原局天干通常按月干 > 时干 > 年干，且这不属于根气。",
        "十神解释合同：根气与势能不是同一概念；根气回答“是否扎根”，势能回答“是否得势”。",
        "十神解释合同：通根只定义为“天干 <- 地支藏干”；透干只定义为“地支藏干 -> 天干显影”。",
        "十神解释合同：地支之间不谈根气，天干之间不谈透干；二者可互相增强，但必须基于冻结盘面单次结算，禁止递归放大。",
        "十神解释合同：天干五合与地支成局分开解读；五合只回看地支根气与争合/支扰，倍率明显轻于地支三合三会。",
        "十神解释合同：关系成局的大倍率主要由动态透干/显神触发；月干透出最强，日干在动态做功中有效，但不回流为静态比劫显化。",
        "十神解释合同：同五行可通根，但阴阳不纯配时应折损；本根强于异阴阳根。",
        "十神解释合同：日干是十神参照轴，不直接计入比肩/劫财等显化分。",
        "十神解释合同：只有藏干未透时通常仅作弱支撑或潜藏残值，不宜直接判为强轴。",
        "十神解释合同：例如丙见巳偏根强，丙见午偏势强；解释时必须区分“根深”与“势猛”。",
    ]


def _ten_gods_decomposition_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    raw = pt.get("ten_gods_decomposition_l0")
    if not isinstance(raw, dict) or not raw:
        return []
    ranked = sorted(
        (
            (str(god).strip(), row)
            for god, row in raw.items()
            if str(god).strip() and isinstance(row, dict)
        ),
        key=lambda item: float(item[1].get("total") or 0.0),
        reverse=True,
    )
    lines: List[str] = []
    for god, row in ranked[:3]:
        lines.append(
            "十神分解："
            f"{god} 总{float(row.get('total') or 0.0):.2f}"
            f"＝显化{float(row.get('manifest') or 0.0):.2f}"
            f"+根气{float(row.get('root') or 0.0):.2f}"
            f"+势能{float(row.get('momentum') or 0.0):.2f}"
            f"+潜藏{float(row.get('hidden') or 0.0):.2f}"
        )
        momentum_parts = [
            ("月令势", float(row.get("momentum_month_order") or 0.0)),
            ("阶段势", float(row.get("momentum_stage") or 0.0)),
            ("禄势", float(row.get("momentum_stage_lu") or 0.0)),
            ("刃势", float(row.get("momentum_stage_blade") or 0.0)),
            ("长生势", float(row.get("momentum_stage_general") or 0.0)),
            ("结构势", float(row.get("momentum_structure") or 0.0)),
            ("辅助势", float(row.get("momentum_auxiliary") or 0.0)),
            ("其他势", float(row.get("momentum_other") or 0.0)),
        ]
        visible_parts = [f"{label}{value:.2f}" for label, value in momentum_parts if value > 0.0]
        if visible_parts:
            lines.append(f"十神势能细项：{god}＝{' + '.join(visible_parts)}")
    return lines


def _core_flux_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
    flux_meta = authority.get("core_flux_meta") if isinstance(authority.get("core_flux_meta"), dict) else {}
    if not flux_meta:
        return []

    rows: List[str] = [
        "做功解释合同：方向矩阵中的 source->target 表示对目标十神/结构的净推动或净压制；回路张力区分同向放大与对冲拉扯。"
    ]

    interaction_rows = flux_meta.get("interaction_matrix") if isinstance(flux_meta.get("interaction_matrix"), list) else []
    if interaction_rows:
        positive_rows = []
        negative_rows = []
        for item in interaction_rows:
            if not isinstance(item, dict):
                continue
            source = str(item.get("source") or "").strip()
            target = str(item.get("target") or "").strip()
            if not source or not target:
                continue
            net = _safe_float(item.get("net"), 0.0)
            support_ratio = _safe_float(item.get("support_ratio"), 0.0)
            resist_ratio = _safe_float(item.get("resist_ratio"), 0.0)
            row = (
                f"{source}->{target} 净{net:+.3f}"
                f"（合{round(support_ratio * 100):.0f}%/抗{round(resist_ratio * 100):.0f}%）"
            )
            if net >= 0.0:
                positive_rows.append((abs(net), row))
            else:
                negative_rows.append((abs(net), row))
        top_fragments: List[str] = []
        if positive_rows:
            top_fragments.append(max(positive_rows, key=lambda item: item[0])[1])
        if negative_rows:
            top_fragments.append(max(negative_rows, key=lambda item: item[0])[1])
        if not top_fragments:
            raw_sorted = sorted(
                (
                    (
                        abs(_safe_float(item.get("net"), 0.0)),
                        f"{str(item.get('source') or '').strip()}->{str(item.get('target') or '').strip()} "
                        f"净{_safe_float(item.get('net'), 0.0):+.3f}"
                    )
                    for item in interaction_rows
                    if isinstance(item, dict)
                    and str(item.get("source") or "").strip()
                    and str(item.get("target") or "").strip()
                ),
                key=lambda item: item[0],
                reverse=True,
            )
            top_fragments = [label for _score, label in raw_sorted[:2]]
        if top_fragments:
            rows.append("做功方向矩阵：" + "；".join(top_fragments[:2]))

    tension_rows = flux_meta.get("tension_pairs") if isinstance(flux_meta.get("tension_pairs"), list) else []
    if tension_rows:
        top_pairs: List[str] = []
        for item in tension_rows[:2]:
            if not isinstance(item, dict):
                continue
            left = str(item.get("left") or "").strip()
            right = str(item.get("right") or "").strip()
            if not left or not right:
                continue
            mode = str(item.get("mode") or "").strip()
            score = _safe_float(item.get("score"), 0.0)
            label = "同向放大" if mode == "reinforce" else "对冲拉扯"
            top_pairs.append(f"{left}<->{right} {label}{score:.3f}")
        if top_pairs:
            rows.append("做功回路：" + "；".join(top_pairs))

    return rows


def _authority_axis_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
    effect_scores = authority.get("effect_scores") if isinstance(authority.get("effect_scores"), dict) else {}
    if not effect_scores:
        return []

    ranked = sorted(
        (
            (str(god).strip(), row)
            for god, row in effect_scores.items()
            if str(god).strip() and isinstance(row, dict)
        ),
        key=lambda item: abs(_safe_float(item[1].get("authority_use_score"), 0.0)) + abs(_safe_float(item[1].get("authority_taboo_score"), 0.0)),
        reverse=True,
    )
    rows: List[str] = [
        "体用双轴合同：authority 不只看净效，还同时看能量、稳定承接与波动；高能低稳与低能高稳必须分开解释。"
    ]
    fragments: List[str] = []
    for god, row in ranked[:3]:
        profile = str(row.get("authority_profile") or "").strip()
        if not profile:
            continue
        energy = _safe_float(row.get("authority_energy"), 0.0)
        stability = _safe_float(row.get("authority_stability"), 0.0)
        volatility = _safe_float(row.get("authority_volatility"), 0.0)
        use_score = _safe_float(row.get("authority_use_score"), 0.0)
        taboo_score = _safe_float(row.get("authority_taboo_score"), 0.0)
        fragments.append(
            f"{god} {profile}"
            f"（能量{energy:.2f}/稳{stability:.2f}/波动{volatility:.2f}"
            f"/用{use_score:+.2f}/忌{taboo_score:+.2f}）"
        )
    if fragments:
        rows.append("体用双轴摘要：" + "；".join(fragments))
    judgement_protocol = authority.get("judgement_bias_protocol") if isinstance(authority.get("judgement_bias_protocol"), dict) else {}
    blind_protocol = authority.get("blind_bias_protocol") if isinstance(authority.get("blind_bias_protocol"), dict) else {}
    stage_protocol = authority.get("stage_bias_protocol") if isinstance(authority.get("stage_bias_protocol"), dict) else {}
    layer_protocol = authority.get("authority_layer_protocol") if isinstance(authority.get("authority_layer_protocol"), dict) else {}
    judgement_summary = judgement_protocol.get("summary") if isinstance(judgement_protocol.get("summary"), dict) else {}
    blind_summary = blind_protocol.get("summary") if isinstance(blind_protocol.get("summary"), dict) else {}
    stage_summary = stage_protocol.get("summary") if isinstance(stage_protocol.get("summary"), dict) else {}
    layer_summary = layer_protocol.get("summary") if isinstance(layer_protocol.get("summary"), dict) else {}
    if layer_protocol:
        rows.append(
            "裁决分层合同：Level 1 为 ziping 主裁决硬约束，Level 2 为结构增强，Level 3 为 soft bias；"
            f"override_forbidden={'是' if bool(layer_protocol.get('override_forbidden')) else '否'}"
            f"；bias 上限{_safe_float(layer_protocol.get('max_bias_ratio'), 0.0):.2f}"
            f"；硬约束{int(layer_summary.get('hard_constraint_count') or 0)}"
            f"；结构增强{int(layer_summary.get('structure_enhancement_count') or 0)}"
            f"；软偏置{int(layer_summary.get('soft_bias_count') or 0)}"
        )
    if judgement_summary:
        line = (
            "判定偏置合同：L2 judgement 只提供 bias / evidence / narrative hint，不直接改写 L0/L1 物理结算。 "
            "判定偏置摘要："
            f"条目{int(judgement_summary.get('entry_count') or 0)}"
            f"；用侧{_safe_float(judgement_summary.get('total_use_bias'), 0.0):.2f}"
            f"；忌侧{_safe_float(judgement_summary.get('total_taboo_bias'), 0.0):.2f}"
        )
        if stage_summary:
            line += (
                "；阶段偏置摘要："
                f"条目{int(stage_summary.get('entry_count') or 0)}"
                f"；推用{_safe_float(stage_summary.get('total_use_boost'), 0.0):.2f}"
                f"；推忌{_safe_float(stage_summary.get('total_taboo_boost'), 0.0):.2f}"
                f"；稳{_safe_float(stage_summary.get('total_stability_boost'), 0.0):.2f}"
                f"；波动{_safe_float(stage_summary.get('total_volatility_boost'), 0.0):.2f}"
            )
        rows.append(line)
    elif stage_summary:
        rows.append(
            "阶段偏置摘要："
            f"条目{int(stage_summary.get('entry_count') or 0)}"
            f"；推用{_safe_float(stage_summary.get('total_use_boost'), 0.0):.2f}"
            f"；推忌{_safe_float(stage_summary.get('total_taboo_boost'), 0.0):.2f}"
            f"；稳{_safe_float(stage_summary.get('total_stability_boost'), 0.0):.2f}"
            f"；波动{_safe_float(stage_summary.get('total_volatility_boost'), 0.0):.2f}"
        )
    if blind_protocol:
        route = str(blind_protocol.get("primary_route") or "").strip()
        body_mode = str(blind_protocol.get("body_mode") or "").strip()
        line = (
            "盲派桥接合同：盲派只以 bias_only 方式并行推用/推忌，不覆盖子平 authority 主裁决。 "
            "盲派桥接摘要："
            f"{route or '主线待定'}"
            f"；体态{body_mode or '未定'}"
            f"；推用{_safe_float(blind_summary.get('use_total'), 0.0):.2f}"
            f"；推忌{_safe_float(blind_summary.get('taboo_total'), 0.0):.2f}"
            f"；换挡{int(blind_summary.get('switch_count') or 0)}"
        )
        rows.append(line)
    return rows


def _blind_theme_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    blind_theme = normalize_blind_theme_meta(meta.get("blind_theme"))
    if not blind_theme:
        return []
    rows = [
        "盲派专题合同：盲派作为可选独立专题，与子平/格局并行；只输出体用候选、家里家外、运行换挡与断事摘要，不直接覆盖最终 authority。"
    ]
    summary_parts: List[str] = []
    primary_route = str(blind_theme.get("primary_route") or "").strip()
    body_mode = str(blind_theme.get("body_mode") or "").strip()
    use_candidates = blind_theme.get("use_candidates") if isinstance(blind_theme.get("use_candidates"), list) else []
    taboo_candidates = blind_theme.get("taboo_candidates") if isinstance(blind_theme.get("taboo_candidates"), list) else []
    house_roles = blind_theme.get("house_roles") if isinstance(blind_theme.get("house_roles"), dict) else {}
    runtime_switches = blind_theme.get("runtime_switches") if isinstance(blind_theme.get("runtime_switches"), list) else []
    digest = str(blind_theme.get("prompt_digest") or "").strip()
    if primary_route:
        summary_parts.append(f"主线{primary_route}")
    if body_mode:
        summary_parts.append(f"体态{body_mode}")
    if use_candidates:
        summary_parts.append("用侧" + "/".join(str(item).strip() for item in use_candidates[:2] if str(item).strip()))
    if taboo_candidates:
        summary_parts.append("忌侧" + "/".join(str(item).strip() for item in taboo_candidates[:2] if str(item).strip()))
    inside = [god for god, role in house_roles.items() if str(role).strip() == "inside"]
    outside = [god for god, role in house_roles.items() if str(role).strip() == "outside"]
    if inside:
        summary_parts.append("家里" + "/".join(inside[:2]))
    if outside:
        summary_parts.append("家外" + "/".join(outside[:2]))
    switch_labels = [str(item).strip() for item in runtime_switches[:2] if str(item).strip()]
    if switch_labels:
        summary_parts.append("换挡" + "；".join(switch_labels))
    if digest:
        summary_parts.append("断口" + digest)
    if summary_parts:
        rows.append("盲派专题摘要：" + "；".join(summary_parts))
    return rows


def six_pillars_tensor_complete(pt: Dict[str, Any]) -> bool:
    """与 VerdictOrchestrator 物理门控一致：四柱 + 大运 + 流年。"""
    fp = pt.get("four_pillars")
    if not isinstance(fp, dict):
        return False
    for key in ("year", "month", "day", "hour"):
        if not _cell_ok(fp.get(key)):
            return False
    if not _cell_ok(pt.get("luck_pillar")):
        return False
    if not _cell_ok(pt.get("flow_pillar")):
        return False
    return True


@dataclass(frozen=True)
class SixPillarsModel:
    """只读物化模型：字段一律从 physics_tensor 读取，不从请求体独立解析。"""

    year: str
    month: str
    day: str
    hour: str
    luck_pillar: str
    flow_pillar: str
    flow_year: Optional[int]

    @classmethod
    def from_physics_tensor(cls, pt: Dict[str, Any]) -> SixPillarsModel:
        fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
        fy = pt.get("flow_year")
        try:
            fy_int = int(fy) if fy is not None else None
        except (TypeError, ValueError):
            fy_int = None
        return cls(
            year=str(fp.get("year") or "").strip(),
            month=str(fp.get("month") or "").strip(),
            day=str(fp.get("day") or "").strip(),
            hour=str(fp.get("hour") or "").strip(),
            luck_pillar=str(pt.get("luck_pillar") or "").strip(),
            flow_pillar=str(pt.get("flow_pillar") or "").strip(),
            flow_year=fy_int,
        )

    def materialize_prompt_lines(self) -> List[str]:
        """元数据中心出口：写入 LLM user 侧的硬事实行（与 Body/facts 解耦）。"""
        fy = self.flow_year if self.flow_year is not None else "?"
        return [
            f"四柱落位（元数据中心）：年{self.year} 月{self.month} 日{self.day} 时{self.hour}",
            f"大运（{fy}）：{self.luck_pillar}；流年：{self.flow_pillar}",
        ]


class PhysicsCanonicalService:
    """物理层单一事实源：供 pipeline / llm_micro_client 在装配 prompt 时调用。"""

    @staticmethod
    def sixpillars_from_tensor(pt: Dict[str, Any]) -> SixPillarsModel:
        return SixPillarsModel.from_physics_tensor(pt)

    @staticmethod
    def materialize_prompt_lines(physics_tensor: Dict[str, Any]) -> List[str]:
        rows = SixPillarsModel.from_physics_tensor(physics_tensor).materialize_prompt_lines()
        if not isinstance(physics_tensor, dict):
            return rows
        rows.extend(_core_flux_prompt_lines(physics_tensor))
        rows.extend(_runtime_field_prompt_lines(physics_tensor))
        rows.extend(_climate_field_prompt_lines(physics_tensor))
        rows.extend(_climate_theme_prompt_lines(physics_tensor))
        rows.extend(_xiangfa_theme_prompt_lines(physics_tensor))
        rows.extend(_bazi_image_prompt_lines(physics_tensor))
        rows.extend(_macro_theme_prompt_lines(physics_tensor))
        rows.extend(_wealth_profile_prompt_lines(physics_tensor))
        rows.extend(_wealth_code_prompt_lines(physics_tensor))
        rows.extend(_authority_axis_prompt_lines(physics_tensor))
        rows.extend(_blind_theme_prompt_lines(physics_tensor))
        rows.extend(_relation_summary_prompt_lines(physics_tensor))
        rows.extend(_relation_dynamics_prompt_lines(physics_tensor))
        rows.extend(_pattern_summary_prompt_lines(physics_tensor))
        rows.extend(_ten_gods_prompt_contract_lines(physics_tensor))
        rows.extend(_ten_gods_decomposition_lines(physics_tensor))
        total_energy = physics_tensor.get("total_energy_index")
        scores = read_runtime_scores(physics_tensor)
        if isinstance(scores, dict) and scores:
            ranked = sorted(
                (
                    (str(k).strip(), float(v))
                    for k, v in scores.items()
                    if str(k).strip()
                ),
                key=lambda kv: kv[1],
                reverse=True,
            )
            top_rows = [f"{name}:{value:.2f}" for name, value in ranked[:6]]
            if top_rows:
                rows.append(f"十神绝对强度（非比例）：{'，'.join(top_rows)}")
        try:
            total_value = float(total_energy)
        except (TypeError, ValueError):
            total_value = None
        if total_value is not None:
            rows.append(f"全盘总能量指标：{total_value:.2f}")
        return rows


def strip_client_pillar_echoes(rows: List[str]) -> List[str]:
    """剔除可能由前端回灌的柱位描述行，避免与元数据中心重复或冲突。"""
    out: List[str] = []
    for r in rows:
        t = str(r).strip()
        if not t:
            continue
        if t.startswith("四柱落位"):
            continue
        if "大运（" in t and ("流年" in t or "流年：" in t):
            continue
        out.append(t)
    return out


@dataclass
class V17PhysicsMetadata:
    """叙事协程启动前的因果对齐：await metadata.is_stable()。"""

    physics: Dict[str, Any]

    async def is_stable(self) -> bool:
        await asyncio.sleep(0)
        pt = self.physics if isinstance(self.physics, dict) else {}
        if not six_pillars_tensor_complete(pt):
            return False
        meta = pt.get("meta")
        if not isinstance(meta, dict):
            return False
        return bool(meta.get("v17_physics_stable"))
