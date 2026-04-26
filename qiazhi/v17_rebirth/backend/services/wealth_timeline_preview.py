from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, ten_god_from_stems
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import (
    normalize_wealth_profile_meta,
    resolve_wealth_profile,
)

WEALTH_TIMELINE_PREVIEW_PROTOCOL = "v17.topic.wealth_timeline_preview.v1"
WEALTH_TIMELINE_CONTRACT = "v17.topic.wealth_timeline.v1"

_STEMS = set("甲乙丙丁戊己庚辛壬癸")
_BRANCHES = set("子丑寅卯辰巳午未申酉戌亥")
_WEALTH_GODS = {"正财", "偏财"}
_OUTPUT_GODS = {"食神", "伤官"}
_AUTHORITY_GODS = {"正官", "七杀"}
_SEAL_GODS = {"正印", "偏印"}
_PEER_GODS = {"比肩", "劫财"}

_CHANNEL_FOCUS: Dict[str, Tuple[str, ...]] = {
    "stable_income": ("正财", "正官", "正印"),
    "opportunity_income": ("偏财", "伤官", "七杀"),
    "output_to_wealth": ("食神", "伤官", "正财", "偏财"),
    "authority_income": ("正官", "七杀", "正财"),
    "knowledge_asset": ("正印", "偏印", "正财"),
    "resource_integration": ("偏财", "比肩", "劫财"),
}


def _clean_label(value: Any, *, limit: int = 160) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _clean_str_list(values: Sequence[Any] | None, *, limit: int = 8) -> List[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    rows: List[str] = []
    seen: set[str] = set()
    for value in values:
        label = _clean_label(value)
        if not label or label in seen:
            continue
        seen.add(label)
        rows.append(label)
        if len(rows) >= limit:
            break
    return rows


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        next_value = float(value)
    except (TypeError, ValueError):
        return fallback
    if next_value != next_value:
        return fallback
    return next_value


def _safe_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _parse_gz(value: Any) -> Tuple[str, str]:
    text = str(value or "").strip()
    stem = ""
    branch = ""
    for char in text:
        if not stem and char in _STEMS:
            stem = char
            continue
        if not branch and char in _BRANCHES:
            branch = char
        if stem and branch:
            break
    return stem, branch


def _parse_birth_datetime(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _profile_from_inputs(
    *,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> Tuple[Dict[str, Any], str]:
    if isinstance(wealth_profile, dict) and wealth_profile:
        return normalize_wealth_profile_meta(wealth_profile), "payload.wealth_profile"
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    if isinstance(meta.get("wealth_profile"), dict) and meta.get("wealth_profile"):
        return normalize_wealth_profile_meta(meta.get("wealth_profile")), "physics.meta.wealth_profile"
    if pt:
        resolved = resolve_wealth_profile(pt).get("wealth_profile")
        return normalize_wealth_profile_meta(resolved), "computed.from_server_physics"
    return {}, "missing"


def _day_master_from_tensor(pt: Mapping[str, Any]) -> str:
    four = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), Mapping) else {}
    day_stem, _ = _parse_gz(four.get("day") if isinstance(four, Mapping) else "")
    if day_stem:
        return day_stem
    dt = _parse_birth_datetime(pt.get("birth_time_solar") or pt.get("birth_time") or pt.get("birth_time_input"))
    if dt is None:
        return ""
    try:
        from lunar_python import Lunar

        day_gz = Lunar.fromDate(dt).getEightChar().getDay()
        day_stem, _ = _parse_gz(day_gz)
        return day_stem
    except Exception:
        return ""


def _branch_main_god(branch: str, day_master: str) -> str:
    hidden = BRANCH_HIDDEN.get(str(branch or "").strip(), [])
    if not hidden or not day_master:
        return ""
    return ten_god_from_stems(day_master, hidden[0][0])


def _pillar_gods(gz: Any, day_master: str) -> Tuple[str, str, str, str]:
    stem, branch = _parse_gz(gz)
    stem_god = ten_god_from_stems(day_master, stem) if stem and day_master else ""
    branch_god = _branch_main_god(branch, day_master) if branch and day_master else ""
    return stem, branch, stem_god, branch_god


def _flow_pillar_for_year(year: int) -> str:
    try:
        from lunar_python import Solar

        ygz = Solar.fromYmd(int(year), 6, 15).getLunar().getYearInGanZhi()
        return str(ygz or "").strip() or "—"
    except Exception:
        return "—"


def _derive_luck_window(pt: Mapping[str, Any], current_year: int) -> Dict[str, Any]:
    fallback_pillar = _clean_label(pt.get("luck_pillar")) or "—"
    fallback = {
        "luck_pillar": fallback_pillar,
        "start_year": int(current_year),
        "end_year": int(current_year) + 9,
        "start_age": None,
        "end_age": None,
        "index": None,
        "source": "physics_snapshot_fallback",
    }
    dt = _parse_birth_datetime(pt.get("birth_time_solar") or pt.get("birth_time") or pt.get("birth_time_input"))
    if dt is None:
        return fallback
    try:
        from lunar_python import Lunar

        gender_code = 1 if str(pt.get("gender") or "").strip().lower() == "male" else 0
        yun = Lunar.fromDate(dt).getEightChar().getYun(gender_code)
        first_future: Dict[str, Any] | None = None
        same_pillar: Dict[str, Any] | None = None
        for dy in yun.getDaYun():
            gz = _clean_label(dy.getGanZhi())
            if len(gz) < 2:
                continue
            row = {
                "luck_pillar": gz,
                "start_year": _safe_int(dy.getStartYear(), current_year),
                "end_year": _safe_int(dy.getEndYear(), current_year + 9),
                "start_age": _safe_int(dy.getStartAge(), 0),
                "end_age": _safe_int(dy.getEndAge(), 0),
                "index": _safe_int(dy.getIndex(), 0),
                "source": "lunar_python.dayun",
            }
            if row["start_year"] <= int(current_year) <= row["end_year"]:
                return row
            if fallback_pillar != "—" and gz == fallback_pillar:
                same_pillar = row
            if first_future is None and int(current_year) < row["start_year"]:
                first_future = row
        return same_pillar or first_future or fallback
    except Exception:
        return fallback


def _channel_id(profile: Mapping[str, Any]) -> str:
    channels = profile.get("primary_channels") if isinstance(profile.get("primary_channels"), list) else []
    if not channels:
        return ""
    first = channels[0]
    return _clean_label(first.get("id") if isinstance(first, Mapping) else "")


def _god_signal(god: str, *, top_channel: str, usable_state: str) -> Dict[str, Any]:
    score_delta = 0.0
    risk_delta = 0.0
    tags: List[str] = []
    reasons: List[str] = []
    actions: List[str] = []
    focus_gods = set(_CHANNEL_FOCUS.get(top_channel, ()))

    if god in _WEALTH_GODS:
        score_delta += 0.14
        tags.append("财星触发")
        reasons.append(f"{god}临运年，财富主题容易被推到台前")
        actions.append("优先看现金流、合同回款和资源承接")
        if usable_state == "wealth_as_use":
            score_delta += 0.06
            reasons.append("wealth_profile 判定财星在顺侧，可作为机会窗口观察")
        elif usable_state == "wealth_as_taboo":
            risk_delta += 0.13
            reasons.append("wealth_profile 判定财星在忌侧，财动同时带压力和牵扯")
    elif god in _OUTPUT_GODS:
        score_delta += 0.1 if top_channel == "output_to_wealth" or god in focus_gods else 0.07
        tags.append("输出变现")
        reasons.append(f"{god}临运年，利于把技能、产品、表达转成收入线索")
        actions.append("把交付、定价和复购路径先做清楚")
    elif god in _AUTHORITY_GODS:
        score_delta += 0.08 if top_channel in {"authority_income", "stable_income"} or god in focus_gods else 0.05
        risk_delta += 0.035
        tags.append("平台规则")
        reasons.append(f"{god}临运年，平台、职位、合同和规则承接变重要")
        actions.append("用合规、合同、角色边界承接机会")
    elif god in _SEAL_GODS:
        score_delta += 0.06 if top_channel == "knowledge_asset" or god in focus_gods else 0.035
        tags.append("资质沉淀")
        reasons.append(f"{god}临运年，更适合用资质、方法论或专业壁垒蓄财")
        actions.append("沉淀可复用资产，避免只追短期交易")
    elif god in _PEER_GODS:
        risk_delta += 0.11
        tags.append("竞争分利")
        reasons.append(f"{god}临运年，合伙、竞争、分账和同辈资源会放大")
        actions.append("先定分账、退出和责任边界")
        if top_channel == "resource_integration":
            score_delta += 0.055
            risk_delta += 0.035
            reasons.append("主通道偏资源整合，机会和分利风险会同时抬升")
    return {
        "score_delta": score_delta,
        "risk_delta": risk_delta,
        "tags": tags,
        "reasons": reasons,
        "actions": actions,
    }


def _merge_signal(*signals: Dict[str, Any]) -> Dict[str, Any]:
    tags: List[str] = []
    reasons: List[str] = []
    actions: List[str] = []
    score_delta = 0.0
    risk_delta = 0.0
    for signal in signals:
        score_delta += _safe_float(signal.get("score_delta"), 0.0)
        risk_delta += _safe_float(signal.get("risk_delta"), 0.0)
        tags.extend(_clean_str_list(signal.get("tags"), limit=6))
        reasons.extend(_clean_str_list(signal.get("reasons"), limit=6))
        actions.extend(_clean_str_list(signal.get("actions"), limit=6))
    return {
        "score_delta": score_delta,
        "risk_delta": risk_delta,
        "tags": list(dict.fromkeys(tags))[:5],
        "reasons": list(dict.fromkeys(reasons))[:5],
        "actions": list(dict.fromkeys(actions))[:4],
    }


def _attention_type(score: float, risk: float) -> str:
    if score >= 0.62 and risk >= 0.43:
        return "opportunity_with_risk"
    if score >= 0.62:
        return "opportunity"
    if risk >= 0.5:
        return "risk_watch"
    if score >= 0.52:
        return "conversion_watch"
    return "steady_watch"


def _attention_level(score: float, risk: float, salience: float) -> str:
    if score >= 0.68 or risk >= 0.58 or salience >= 0.65:
        return "high"
    if score >= 0.56 or risk >= 0.45 or salience >= 0.54:
        return "medium"
    return "steady"


def _focus_label(attention_type: str, tags: Sequence[str]) -> str:
    if attention_type == "opportunity_with_risk":
        return "机会与风控同看"
    if attention_type == "opportunity":
        return "财富机会窗口"
    if attention_type == "risk_watch":
        return "现金流与分利风险"
    if "输出变现" in tags:
        return "输出转化窗口"
    if "平台规则" in tags:
        return "平台/合同承接"
    return "稳态观察"


def _year_row(
    *,
    year: int,
    flow_pillar: str,
    luck_pillar: str,
    day_master: str,
    profile: Mapping[str, Any],
    current_year: int,
) -> Dict[str, Any]:
    top_channel = _channel_id(profile)
    usable_state = _clean_label(profile.get("usable_state")) or "unclear"
    profile_score = _safe_float(profile.get("score"), 0.0)
    profile_risk = _safe_float(profile.get("risk"), 0.0)
    _, _, luck_stem_god, luck_branch_god = _pillar_gods(luck_pillar, day_master)
    _, _, flow_stem_god, flow_branch_god = _pillar_gods(flow_pillar, day_master)

    luck_signal = _merge_signal(
        _god_signal(luck_stem_god, top_channel=top_channel, usable_state=usable_state),
        _god_signal(luck_branch_god, top_channel=top_channel, usable_state=usable_state),
    )
    flow_signal = _merge_signal(
        _god_signal(flow_stem_god, top_channel=top_channel, usable_state=usable_state),
        _god_signal(flow_branch_god, top_channel=top_channel, usable_state=usable_state),
    )

    score = _clamp(0.18 + profile_score * 0.45 + luck_signal["score_delta"] * 0.55 + flow_signal["score_delta"], high=0.96)
    risk = _clamp(0.08 + profile_risk * 0.52 + luck_signal["risk_delta"] * 0.5 + flow_signal["risk_delta"], high=0.88)
    if usable_state == "wealth_needs_bridge" and not set(flow_signal["tags"]) & {"输出变现", "平台规则", "资质沉淀"}:
        score = _clamp(score - 0.035, high=0.96)
        flow_signal["reasons"].append("财富画像提示需要桥接，本年若无桥接神，机会更宜保守承接")
    if usable_state == "wealth_as_taboo" and score >= 0.58:
        risk = _clamp(risk + 0.06, high=0.88)
    salience = _clamp(score * 0.58 + risk * 0.42 + (0.04 if int(year) == int(current_year) else 0.0))
    attention_type = _attention_type(score, risk)
    tags = list(dict.fromkeys([*flow_signal["tags"], *luck_signal["tags"]]))[:5]
    reasons = list(dict.fromkeys([*flow_signal["reasons"], *luck_signal["reasons"]]))[:5]
    actions = list(dict.fromkeys([*flow_signal["actions"], *luck_signal["actions"]]))[:4]
    if not reasons:
        reasons = ["流年未形成强财富触发，宜按财富画像的主通道稳态观察"]
    if not actions:
        actions = ["保持预算、现金流和机会筛选纪律"]
    return {
        "year": int(year),
        "flow_pillar": _clean_label(flow_pillar) or "—",
        "luck_pillar": _clean_label(luck_pillar) or "—",
        "flow_ten_gods": {
            "stem": _clean_label(flow_stem_god),
            "branch": _clean_label(flow_branch_god),
        },
        "score": round(score, 3),
        "risk": round(risk, 3),
        "salience": round(salience, 3),
        "attention_level": _attention_level(score, risk, salience),
        "attention_type": attention_type,
        "focus": _focus_label(attention_type, tags),
        "tags": tags,
        "reasons": _clean_str_list(reasons, limit=5),
        "suggested_actions": _clean_str_list(actions, limit=4),
    }


def _luck_summary(
    *,
    luck_window: Mapping[str, Any],
    profile: Mapping[str, Any],
    day_master: str,
) -> Dict[str, Any]:
    luck_pillar = _clean_label(luck_window.get("luck_pillar")) or "—"
    top_channel = _channel_id(profile)
    usable_state = _clean_label(profile.get("usable_state")) or "unclear"
    _, _, luck_stem_god, luck_branch_god = _pillar_gods(luck_pillar, day_master)
    signal = _merge_signal(
        _god_signal(luck_stem_god, top_channel=top_channel, usable_state=usable_state),
        _god_signal(luck_branch_god, top_channel=top_channel, usable_state=usable_state),
    )
    base_score = _safe_float(profile.get("score"), 0.0)
    base_risk = _safe_float(profile.get("risk"), 0.0)
    score = _clamp(0.2 + base_score * 0.52 + signal["score_delta"] * 0.72, high=0.94)
    risk = _clamp(0.08 + base_risk * 0.58 + signal["risk_delta"] * 0.72, high=0.86)
    if score >= 0.62 and risk >= 0.42:
        stance = "opportunity_with_pressure"
        summary = "本步大运能把财富主题推到前台，但必须同看承接、风控和分利边界。"
    elif score >= 0.62:
        stance = "opportunity_period"
        summary = "本步大运偏财富机会窗口，适合围绕主财富通道做持续承接。"
    elif risk >= 0.48:
        stance = "pressure_period"
        summary = "本步大运财富压力大于显性机会，现金流、合伙和判断纪律要先行。"
    elif set(signal["tags"]) & {"输出变现", "平台规则", "资质沉淀"}:
        stance = "conversion_period"
        summary = "本步大运更像财富转化期，先做桥接条件，再谈放大机会。"
    else:
        stance = "steady_observation"
        summary = "本步大运财富信号偏稳，适合按画像主通道做观察和小步验证。"
    return {
        "luck_pillar": luck_pillar,
        "start_year": _safe_int(luck_window.get("start_year"), 0),
        "end_year": _safe_int(luck_window.get("end_year"), 0),
        "start_age": luck_window.get("start_age"),
        "end_age": luck_window.get("end_age"),
        "score": round(score, 3),
        "risk": round(risk, 3),
        "stance": stance,
        "summary": summary,
        "tags": _clean_str_list(signal.get("tags"), limit=5),
        "reasons": _clean_str_list(signal.get("reasons"), limit=5),
        "source": _clean_label(luck_window.get("source")),
    }


def build_wealth_timeline_preview(
    *,
    physics_tensor: Dict[str, Any] | None = None,
    wealth_profile: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    profile, profile_source = _profile_from_inputs(wealth_profile=wealth_profile, physics_tensor=pt)
    current_year = _safe_int(pt.get("flow_year"), datetime.now().year)
    day_master = _day_master_from_tensor(pt)
    luck_window = _derive_luck_window(pt, current_year)
    luck_summary = _luck_summary(luck_window=luck_window, profile=profile, day_master=day_master) if profile else {}
    years = list(range(_safe_int(luck_window.get("start_year"), current_year), _safe_int(luck_window.get("end_year"), current_year + 9) + 1))
    if len(years) > 10:
        years = years[:10]
    if not years:
        years = list(range(current_year, current_year + 10))

    decade_rows: List[Dict[str, Any]] = []
    if profile and day_master:
        for year in years:
            flow_pillar = _flow_pillar_for_year(year)
            decade_rows.append(
                _year_row(
                    year=year,
                    flow_pillar=flow_pillar,
                    luck_pillar=_clean_label(luck_window.get("luck_pillar")) or _clean_label(pt.get("luck_pillar")),
                    day_master=day_master,
                    profile=profile,
                    current_year=current_year,
                )
            )
    current_flow = next((row for row in decade_rows if int(row.get("year") or 0) == int(current_year)), {})
    ranked = sorted(
        [row for row in decade_rows if row.get("attention_level") in {"high", "medium"}],
        key=lambda row: (_safe_float(row.get("salience"), 0.0), _safe_float(row.get("score"), 0.0), _safe_float(row.get("risk"), 0.0)),
        reverse=True,
    )
    if len(ranked) < 3:
        ranked = sorted(
            decade_rows,
            key=lambda row: (_safe_float(row.get("salience"), 0.0), _safe_float(row.get("score"), 0.0), _safe_float(row.get("risk"), 0.0)),
            reverse=True,
        )
    top_attention = [dict(row, rank=index + 1) for index, row in enumerate(ranked[:4])]
    return {
        "protocol": WEALTH_TIMELINE_PREVIEW_PROTOCOL,
        "contract": WEALTH_TIMELINE_CONTRACT,
        "mode": "backstage_preview",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "topic": "wealth",
        "profile_source": profile_source,
        "profile_present": bool(profile),
        "timeline_ready": bool(profile and day_master and decade_rows),
        "safety": {
            "raw_chart_access_for_llm": False,
            "llm_input_scope": "wealth_profile_and_wealth_timeline_only",
            "physics_mutation": False,
            "parameter_mutation": False,
            "body_use_mutation": False,
        },
        "guardrails": [
            "财富时间窗只表示机会、承接与风险的关注窗口，不承诺确定金额、确定发财年份或破产年份。",
            "推演只读服务端物理快照与 wealth_profile，不回写参数、体用裁决或格局裁决。",
            "任何面向 LLM 的后续财富时间断语，只能消费 wealth_profile 与 wealth_timeline，不能自由读取原始八字。",
        ],
        "wealth_profile_summary": {
            "score": round(_safe_float(profile.get("score"), 0.0), 3) if profile else 0.0,
            "confidence": round(_safe_float(profile.get("confidence"), 0.0), 3) if profile else 0.0,
            "risk": round(_safe_float(profile.get("risk"), 0.0), 3) if profile else 0.0,
            "usable_state": _clean_label(profile.get("usable_state")) if profile else "",
            "top_channel": _channel_id(profile) if profile else "",
        },
        "luck_window": luck_summary,
        "current_flow": current_flow,
        "decade_years": decade_rows,
        "top_attention_years": top_attention,
        "llm_boundaries": {
            "allowed_inputs": ["wealth_profile", "wealth_timeline"],
            "forbidden_inputs": ["raw_four_pillars", "raw_birth_time", "free_chart_reinterpretation"],
            "must_avoid": ["必发财", "无财", "破产", "确定金额", "确定发财年份"],
        },
    }


def attach_wealth_timeline_preview_meta(meta: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(meta or {})
    out["wealth_timeline_preview"] = dict(preview or {})
    audits = out.get("topic_prediction_audits") if isinstance(out.get("topic_prediction_audits"), list) else []
    luck_window = preview.get("luck_window") if isinstance(preview.get("luck_window"), Mapping) else {}
    top_years = preview.get("top_attention_years") if isinstance(preview.get("top_attention_years"), list) else []
    compact = {
        "protocol": WEALTH_TIMELINE_PREVIEW_PROTOCOL,
        "contract": WEALTH_TIMELINE_CONTRACT,
        "created_at": str(preview.get("created_at") or ""),
        "topic": "wealth",
        "kind": "timeline_preview",
        "profile_present": bool(preview.get("profile_present")),
        "timeline_ready": bool(preview.get("timeline_ready")),
        "profile_source": str(preview.get("profile_source") or ""),
        "luck_pillar": str(luck_window.get("luck_pillar") or ""),
        "start_year": luck_window.get("start_year"),
        "end_year": luck_window.get("end_year"),
        "top_attention_years": [row.get("year") for row in top_years[:4] if isinstance(row, Mapping)],
    }
    out["topic_prediction_audits"] = [compact, *audits[:9]]
    return out


def summarize_wealth_timeline_preview(preview: Dict[str, Any], *, include_rows: bool = True) -> Dict[str, Any]:
    if not isinstance(preview, dict) or not preview:
        return {"preview_present": False}
    out = {
        "preview_present": True,
        "protocol": str(preview.get("protocol") or ""),
        "contract": str(preview.get("contract") or ""),
        "created_at": str(preview.get("created_at") or ""),
        "profile_present": bool(preview.get("profile_present")),
        "timeline_ready": bool(preview.get("timeline_ready")),
        "wealth_profile_summary": preview.get("wealth_profile_summary") if isinstance(preview.get("wealth_profile_summary"), dict) else {},
        "luck_window": preview.get("luck_window") if isinstance(preview.get("luck_window"), dict) else {},
        "current_flow": preview.get("current_flow") if isinstance(preview.get("current_flow"), dict) else {},
        "top_attention_years": preview.get("top_attention_years") if isinstance(preview.get("top_attention_years"), list) else [],
        "guardrails": preview.get("guardrails") if isinstance(preview.get("guardrails"), list) else [],
    }
    if include_rows:
        out["decade_years"] = preview.get("decade_years") if isinstance(preview.get("decade_years"), list) else []
    return out
