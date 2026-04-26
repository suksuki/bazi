from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import (
    normalize_bazi_image_meta,
    resolve_bazi_image,
)
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import (
    normalize_wealth_profile_meta,
    resolve_wealth_profile,
)
from v17_rebirth.backend.services.physics_layers import read_runtime_scores


WEALTH_CODE_CONTRACT = "v17.topic.wealth_code.v1"
WEALTH_PATH_KNOWLEDGE_ID = "v17.knowledge.wealth_path_templates.v1"

FINAL_WEALTH_CODE_KEYS: List[str] = [
    "contract",
    "topic",
    "is_l3_topic_decoder",
    "knowledge_base",
    "score",
    "confidence",
    "risk",
    "primary_wealth_path",
    "secondary_paths",
    "wealth_source",
    "monetization_engine",
    "carrier",
    "wealth_vault",
    "leakage_points",
    "decade_path_trends",
    "flow_year_watchlist",
    "evidence_graph",
    "evidence",
    "llm_boundary",
    "learning_hooks",
    "guardrails",
]

_WEALTH_GODS = ("正财", "偏财")
_OUTPUT_GODS = ("食神", "伤官")
_AUTHORITY_GODS = ("正官", "七杀")
_SEAL_GODS = ("正印", "偏印")
_PEER_GODS = ("比肩", "劫财")

_PATH_KEYWORDS: Dict[str, tuple[str, ...]] = {
    "direct_wealth": ("正财格", "偏财格", "财星直取", "从财"),
    "output_to_wealth": ("食伤生财", "伤官生财", "输出换财"),
    "output_controls_pressure": ("食伤制杀", "食神制杀", "伤官制杀", "制杀", "shishen_zhisha"),
    "wealth_officer_platform": ("财官", "财官相生", "财官协同", "平台收入"),
    "wealth_seal_asset": ("财印", "财印路径", "财印相战", "财破印"),
    "resource_integration": ("合财", "资源整合", "合伙", "从财"),
    "wealth_vault": ("财库", "墓库", "开库", "库"),
    "leakage_risk": ("比劫夺财", "劫财夺财", "分财", "争财"),
}


WEALTH_PATH_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "direct_wealth": {
        "classic_label": "财星直取",
        "plain_name": "直接收入/明确客户",
        "plain_summary": "钱更容易来自明确客户、固定收入、直接资源或可被管理的现金流。",
        "driver": "wealth",
        "carrier_type": "contract",
        "threshold": 0.36,
        "risk_hint": "直接机会越明显，越要注意预算、账期和收入稳定性。",
    },
    "output_to_wealth": {
        "classic_label": "食伤生财",
        "plain_name": "技能、产品或表达变现",
        "plain_summary": "钱更容易从专业能力、内容、产品、服务、销售表达中转出来。",
        "driver": "output",
        "carrier_type": "self_capacity",
        "threshold": 0.36,
        "risk_hint": "能力强不等于马上有钱，需要产品化、定价和复购路径。",
    },
    "output_controls_pressure": {
        "classic_label": "食伤制杀",
        "plain_name": "靠解决难题赚钱",
        "plain_summary": "钱更容易来自复杂任务、高压项目、竞争场景和别人解决不了的问题。",
        "driver": "output_authority",
        "carrier_type": "method_and_contract",
        "threshold": 0.34,
        "risk_hint": "机会常带压力，必须管理合同、交付成本和规则边界。",
    },
    "wealth_officer_platform": {
        "classic_label": "财官路径",
        "plain_name": "平台、职位或规则收入",
        "plain_summary": "钱更容易通过平台、职位、组织授权、合同规则和责任边界兑现。",
        "driver": "authority",
        "carrier_type": "platform",
        "threshold": 0.34,
        "risk_hint": "收入依赖平台和规则，不能只看机会，还要看授权与合规。",
    },
    "wealth_seal_asset": {
        "classic_label": "财印路径",
        "plain_name": "专业资产/知识信用变现",
        "plain_summary": "钱更容易从知识、证书、方法论、信用、IP 或长期专业资产中沉淀。",
        "driver": "seal",
        "carrier_type": "knowledge",
        "threshold": 0.32,
        "risk_hint": "短期变现不能牺牲长期口碑、资质和专业壁垒。",
    },
    "resource_integration": {
        "classic_label": "比劫合财",
        "plain_name": "合作资源整合",
        "plain_summary": "钱更容易从团队、人脉、合伙项目、资源撮合和共同经营中出现。",
        "driver": "peer",
        "carrier_type": "team",
        "threshold": 0.32,
        "risk_hint": "合作能带来钱，也容易卡在权责、分账和退出机制。",
    },
    "wealth_vault": {
        "classic_label": "财库路径",
        "plain_name": "资产沉淀/资金蓄水",
        "plain_summary": "财富更像被收藏在项目、资产、库存、回款或资金结构里，等待条件引动。",
        "driver": "vault",
        "carrier_type": "asset",
        "threshold": 0.28,
        "risk_hint": "开库不等于必进财，也可能是投入、回款、资产转换或现金流波动。",
    },
    "leakage_risk": {
        "classic_label": "比劫夺财/漏财风险",
        "plain_name": "合作分账与现金流泄漏",
        "plain_summary": "钱容易被合作、竞争、分账、成本或现金流节奏分走。",
        "driver": "risk",
        "carrier_type": "boundary",
        "threshold": 0.28,
        "risk_hint": "先定义边界、分配、账期和退出条件，再谈放大。",
    },
}


def _clean_label(value: Any, *, limit: int = 180) -> str:
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


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _score_sum(scores: Mapping[str, Any], gods: Sequence[str]) -> float:
    return sum(max(0.0, _safe_float(scores.get(god), 0.0)) for god in gods)


def _share(scores: Mapping[str, Any], gods: Sequence[str], total: float) -> float:
    return _score_sum(scores, gods) / max(total, 1.0)


def _signal_label(value: float) -> str:
    if value >= 0.26:
        return "偏强"
    if value >= 0.16:
        return "中等"
    if value > 0:
        return "偏弱"
    return "未显"


def _facts_text(physics_tensor: Mapping[str, Any], meta: Mapping[str, Any]) -> str:
    fragments: List[str] = []
    for row in physics_tensor.get("facts") or []:
        if not isinstance(row, Mapping):
            fragments.append(_clean_label(row, limit=220))
            continue
        plugin_id = _clean_label(row.get("plugin") or row.get("plugin_id"))
        fact_meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
        claim_type = _clean_label(fact_meta.get("claim_type"))
        if plugin_id.startswith(("modern.macro.", "modern.topic.")) or claim_type in {
            "macro_theme_observation",
            "topic_profile_observation",
            "topic_code_observation",
        }:
            continue
        fragments.append(_clean_label(row.get("fact"), limit=220))
    for row in meta.get("plugin_claims") or []:
        if not isinstance(row, Mapping):
            continue
        plugin_id = _clean_label(row.get("plugin_id") or row.get("plugin"))
        claim_type = _clean_label(row.get("claim_type"))
        if plugin_id.startswith(("modern.macro.", "modern.topic.")) or claim_type in {
            "macro_theme_observation",
            "topic_profile_observation",
            "topic_code_observation",
        }:
            continue
        fragments.extend(
            _clean_label(row.get(key), limit=120)
            for key in ("claim_text", "pattern_candidate", "pattern_name", "source_event", "plugin_id")
        )
    return " ".join(fragment for fragment in fragments if fragment)


def _keyword_hits(text: str, path_id: str) -> List[str]:
    return [word for word in _PATH_KEYWORDS.get(path_id, ()) if word and word in text][:6]


def _profile_from_tensor(pt: Mapping[str, Any], meta: Mapping[str, Any]) -> Dict[str, Any]:
    profile = normalize_wealth_profile_meta(meta.get("wealth_profile"))
    if profile:
        return profile
    return normalize_wealth_profile_meta(resolve_wealth_profile(dict(pt)).get("wealth_profile"))


def _bazi_image_from_tensor(pt: Mapping[str, Any], meta: Mapping[str, Any]) -> Dict[str, Any]:
    image = normalize_bazi_image_meta(meta.get("bazi_image"))
    if image:
        return image
    return normalize_bazi_image_meta(resolve_bazi_image(dict(pt)).get("bazi_image"))


def _top_channel_id(profile: Mapping[str, Any]) -> str:
    channels = profile.get("primary_channels") if isinstance(profile.get("primary_channels"), list) else []
    if not channels or not isinstance(channels[0], Mapping):
        return ""
    return _clean_label(channels[0].get("id"))


def _channel_score(profile: Mapping[str, Any], channel_id: str) -> float:
    channels = profile.get("primary_channels") if isinstance(profile.get("primary_channels"), list) else []
    for row in channels:
        if isinstance(row, Mapping) and row.get("id") == channel_id:
            return _safe_float(row.get("score"), 0.0)
    return 0.0


def _symbolic_facts(bazi_image: Mapping[str, Any], *, fact_type: str | None = None, topic_hint: str | None = None) -> List[Dict[str, Any]]:
    rows = bazi_image.get("symbolic_facts") if isinstance(bazi_image.get("symbolic_facts"), list) else []
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if fact_type and _clean_label(row.get("fact_type")) != fact_type:
            continue
        if topic_hint and _clean_label(row.get("topic_hint")) != topic_hint:
            continue
        out.append(dict(row))
    return out


def _wealth_material_rows(bazi_image: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        row
        for row in _symbolic_facts(bazi_image, topic_hint="wealth")
        if _clean_label(row.get("fact_type")) in {"wealth_material", "hidden_wealth_material"}
    ]


def _symbolic_fact_rows(bazi_image: Mapping[str, Any], *, fact_type: str) -> List[Dict[str, Any]]:
    return [row for row in _symbolic_facts(bazi_image) if _clean_label(row.get("fact_type")) == fact_type]


def _hidden_ten_god_count(bazi_image: Mapping[str, Any], gods: Sequence[str]) -> int:
    branches = bazi_image.get("branches") if isinstance(bazi_image.get("branches"), list) else []
    count = 0
    for branch in branches:
        if not isinstance(branch, Mapping):
            continue
        for hidden in branch.get("hidden_stems") if isinstance(branch.get("hidden_stems"), list) else []:
            if isinstance(hidden, Mapping) and _clean_label(hidden.get("ten_god")) in gods:
                count += 1
    return count


def _has_output_wealth_nesting(bazi_image: Mapping[str, Any]) -> bool:
    output_branches = {"巳", "午", "未", "戌"}
    branches = bazi_image.get("branches") if isinstance(bazi_image.get("branches"), list) else []
    for branch in branches:
        if not isinstance(branch, Mapping) or _clean_label(branch.get("branch")) not in output_branches:
            continue
        hidden = branch.get("hidden_stems") if isinstance(branch.get("hidden_stems"), list) else []
        has_wealth = any(isinstance(row, Mapping) and _clean_label(row.get("ten_god")) in _WEALTH_GODS for row in hidden)
        has_output = any(isinstance(row, Mapping) and _clean_label(row.get("ten_god")) in _OUTPUT_GODS for row in hidden)
        if has_wealth and has_output:
            return True
    return False


def _wealth_source(
    bazi_image: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    primary_path: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    path = primary_path if isinstance(primary_path, Mapping) else {}
    driver = _clean_label(path.get("driver"))
    output_facts = _symbolic_fact_rows(bazi_image, fact_type="output_material")
    output_wealth_nested = _has_output_wealth_nesting(bazi_image)
    stems = bazi_image.get("stems") if isinstance(bazi_image.get("stems"), list) else []
    for row in stems:
        if not isinstance(row, Mapping):
            continue
        god = _clean_label(row.get("ten_god"))
        if god not in _WEALTH_GODS:
            continue
        projection = row.get("domain_projection") if isinstance(row.get("domain_projection"), Mapping) else {}
        wealth_projection = _clean_str_list(projection.get("wealth"), limit=4)
        return {
            "material": f"{row.get('stem')}{row.get('element')}",
            "ten_god": god,
            "plain_source": "、".join(wealth_projection) or "明确财富资源",
            "visibility": _clean_label(row.get("visibility")) or "exposed",
            "location": _clean_label(row.get("pillar")),
            "evidence": list(row.get("evidence") or []),
        }
    material_rows = _wealth_material_rows(bazi_image)
    if material_rows:
        row = material_rows[0]
        terms = row.get("classic_terms") if isinstance(row.get("classic_terms"), list) else []
        plain_source = _clean_label(row.get("plain_meaning"), limit=120)
        if driver in {"output", "output_authority"} and (output_facts or output_wealth_nested):
            plain_source = (
                "钱更像藏在专业输出、内容表达、方案交付和复杂项目里；"
                "先把能力做成服务、产品、合同和回款，财才容易出来。"
            )
        return {
            "material": _clean_label(terms[1] if len(terms) > 1 else ""),
            "ten_god": _clean_label(terms[0] if terms else ""),
            "plain_source": plain_source,
            "visibility": "hidden",
            "location": "hidden_stem",
            "evidence": list(row.get("evidence") or []),
        }
    top_channel = _top_channel_id(profile)
    return {
        "material": "",
        "ten_god": "",
        "plain_source": {
            "stable_income": "稳定收入与固定现金流",
            "opportunity_income": "项目机会与市场资源",
            "output_to_wealth": "技能、产品或表达变现",
            "authority_income": "平台、职位或合同收入",
            "knowledge_asset": "专业资产与知识信用",
            "resource_integration": "合作资源与项目撮合",
        }.get(top_channel, "财富来源需要继续观察"),
        "visibility": _clean_label(profile.get("visibility")) or "unclear",
        "location": "wealth_profile",
        "evidence": _clean_str_list(profile.get("evidence"), limit=3),
    }


def _wealth_vault(bazi_image: Mapping[str, Any]) -> Dict[str, Any]:
    branches = bazi_image.get("branches") if isinstance(bazi_image.get("branches"), list) else []
    vaults: List[Dict[str, Any]] = []
    for row in branches:
        if not isinstance(row, Mapping):
            continue
        storage = row.get("storage_context") if isinstance(row.get("storage_context"), Mapping) else {}
        if not storage.get("has_vault_signal"):
            continue
        hidden = row.get("hidden_stems") if isinstance(row.get("hidden_stems"), list) else []
        hidden_wealth = [
            item
            for item in hidden
            if isinstance(item, Mapping) and _clean_label(item.get("ten_god")) in _WEALTH_GODS
        ]
        movement = row.get("movement_context") if isinstance(row.get("movement_context"), Mapping) else {}
        relation_tags = _clean_str_list(movement.get("relation_tags"), limit=4)
        state = "activated" if relation_tags else "static"
        activation_type = "cashflow_volatility" if relation_tags else "asset_storage"
        if hidden_wealth and relation_tags:
            activation_type = "asset_conversion"
        vaults.append(
            {
                "branch": _clean_label(row.get("branch")),
                "location": _clean_label(row.get("pillar")),
                "vault_element": _clean_label(storage.get("vault_element")),
                "plain_material": _clean_label(storage.get("plain_material")),
                "hidden_wealth": [
                    {
                        "stem": _clean_label(item.get("stem")),
                        "ten_god": _clean_label(item.get("ten_god")),
                    }
                    for item in hidden_wealth
                ],
                "state": state,
                "activation_type": activation_type,
                "relation_tags": relation_tags,
                "evidence": list(row.get("evidence") or []),
            }
        )
    if not vaults:
        return {
            "has_vault_signal": False,
            "vault_state": "none",
            "activation_type": "none",
            "plain_summary": "未见明确财库象，先按收入路径和现金流承接判断。",
            "items": [],
        }
    primary = vaults[0]
    summary = (
        f"{primary['branch']}带库象，偏向{primary['plain_material']}。"
        "开库不直接等于进财，需要结合岁运触发、回款、投入和现金流状态看。"
    )
    return {
        "has_vault_signal": True,
        "vault_state": primary["state"],
        "activation_type": primary["activation_type"],
        "plain_summary": summary,
        "items": vaults[:4],
    }


def _path_evidence(
    *,
    path_id: str,
    hits: Sequence[str],
    score_parts: Sequence[str],
    bazi_facts: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
) -> List[str]:
    evidence = list(score_parts)
    evidence.extend(f"经典路径线索：{hit}" for hit in hits[:3])
    evidence.extend(_clean_label(row.get("plain_meaning"), limit=120) for row in bazi_facts[:3])
    if path_id == "output_to_wealth" and _channel_score(profile, "output_to_wealth") > 0:
        evidence.append("财富画像主通道支持技能/产品/表达变现")
    if path_id == "wealth_officer_platform" and _channel_score(profile, "authority_income") > 0:
        evidence.append("财富画像支持平台、职位或合同收入")
    if path_id == "wealth_seal_asset" and _channel_score(profile, "knowledge_asset") > 0:
        evidence.append("财富画像支持专业资产或知识信用变现")
    return _clean_str_list(evidence, limit=8)


def _path_row(
    *,
    path_id: str,
    score: float,
    risk: float,
    hits: Sequence[str],
    score_parts: Sequence[str],
    bazi_facts: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
) -> Dict[str, Any]:
    template = WEALTH_PATH_TEMPLATES[path_id]
    evidence = _path_evidence(
        path_id=path_id,
        hits=hits,
        score_parts=score_parts,
        bazi_facts=bazi_facts,
        profile=profile,
    )
    confidence = _clamp(0.36 + len(evidence) * 0.055 + score * 0.16 - risk * 0.04, 0.28, 0.9)
    return {
        "id": path_id,
        "classic_label": template["classic_label"],
        "plain_name": template["plain_name"],
        "plain_summary": template["plain_summary"],
        "score": round(_clamp(score), 3),
        "confidence": round(confidence, 3),
        "risk": round(_clamp(risk), 3),
        "driver": template["driver"],
        "carrier_type": template["carrier_type"],
        "risk_hint": template["risk_hint"],
        "evidence": evidence,
    }


def _score_paths(
    *,
    scores: Mapping[str, Any],
    profile: Mapping[str, Any],
    bazi_image: Mapping[str, Any],
    text: str,
) -> List[Dict[str, Any]]:
    total = sum(max(0.0, _safe_float(value, 0.0)) for value in scores.values()) or 1.0
    wealth = _share(scores, _WEALTH_GODS, total)
    output = _share(scores, _OUTPUT_GODS, total)
    authority = _share(scores, _AUTHORITY_GODS, total)
    seal = _share(scores, _SEAL_GODS, total)
    peer = _share(scores, _PEER_GODS, total)
    profile_score = _safe_float(profile.get("score"), 0.0)
    profile_risk = _safe_float(profile.get("risk"), 0.0)
    usable_state = _clean_label(profile.get("usable_state"))
    top_channel = _top_channel_id(profile)
    wealth_materials = _wealth_material_rows(bazi_image)
    output_symbol_bonus = min(0.2, len(_symbolic_fact_rows(bazi_image, fact_type="output_material")) * 0.08)
    hidden_wealth_bonus = min(0.14, len(wealth_materials) * 0.035)
    hidden_authority_bonus = min(0.16, _hidden_ten_god_count(bazi_image, _AUTHORITY_GODS) * 0.035)
    output_wealth_nested_bonus = 0.12 if _has_output_wealth_nesting(bazi_image) else 0.0
    vault = _wealth_vault(bazi_image)
    vault_bonus = 0.1 if vault.get("has_vault_signal") else 0.0

    raw: Dict[str, tuple[float, float, List[str], List[Mapping[str, Any]]]] = {}
    for path_id in WEALTH_PATH_TEMPLATES:
        hits = _keyword_hits(text, path_id)
        hit_bonus = min(0.18, len(hits) * 0.07)
        channel_bonus = 0.0
        score_parts: List[str] = []
        if path_id == "direct_wealth":
            channel_bonus = max(_channel_score(profile, "stable_income"), _channel_score(profile, "opportunity_income")) * 0.2
            score = 0.12 + wealth * 1.65 + profile_score * 0.18 + hit_bonus + channel_bonus
            risk = 0.12 + profile_risk * 0.42 + peer * 0.22
            score_parts = [f"直接收入信号{_signal_label(wealth)}", f"画像支持{_signal_label(channel_bonus)}"]
        elif path_id == "output_to_wealth":
            channel_bonus = _channel_score(profile, "output_to_wealth") * 0.24
            score = 0.1 + output * 1.05 + wealth * 0.72 + hit_bonus + channel_bonus + output_symbol_bonus + hidden_wealth_bonus + output_wealth_nested_bonus
            risk = 0.14 + profile_risk * 0.36 + (0.08 if wealth < 0.12 else 0.0)
            score_parts = [f"技能/表达信号{_signal_label(output)}", f"财富资源信号{_signal_label(wealth)}", *(["输出场景中藏财"] if output_wealth_nested_bonus else [])]
        elif path_id == "output_controls_pressure":
            score = 0.08 + output * 0.92 + authority * 0.88 + hit_bonus + min(0.08, _channel_score(profile, "output_to_wealth") * 0.12) + output_symbol_bonus + hidden_authority_bonus
            risk = 0.22 + authority * 0.42 + profile_risk * 0.34
            score_parts = [f"技能输出{_signal_label(output)}", f"高压/规则{_signal_label(authority)}", *(["支中见规则/压力材料"] if hidden_authority_bonus else [])]
        elif path_id == "wealth_officer_platform":
            channel_bonus = _channel_score(profile, "authority_income") * 0.26
            score = 0.09 + wealth * 0.82 + authority * 0.96 + hit_bonus + channel_bonus
            risk = 0.17 + profile_risk * 0.32 + authority * 0.16
            score_parts = [f"财富资源{_signal_label(wealth)}", f"平台/规则{_signal_label(authority)}"]
        elif path_id == "wealth_seal_asset":
            channel_bonus = _channel_score(profile, "knowledge_asset") * 0.26
            score = 0.08 + wealth * 0.74 + seal * 0.98 + hit_bonus + channel_bonus
            risk = 0.16 + profile_risk * 0.3 + (0.14 if "财破印" in hits or "财印相战" in text else 0.0)
            score_parts = [f"财富资源{_signal_label(wealth)}", f"专业/信用{_signal_label(seal)}"]
        elif path_id == "resource_integration":
            channel_bonus = _channel_score(profile, "resource_integration") * 0.28
            score = 0.08 + wealth * 0.66 + peer * 0.82 + hit_bonus + channel_bonus
            risk = 0.26 + peer * 0.46 + profile_risk * 0.3
            score_parts = [f"合作/竞争{_signal_label(peer)}", f"财富资源{_signal_label(wealth)}"]
        elif path_id == "wealth_vault":
            score = 0.08 + vault_bonus + wealth * 0.34 + hit_bonus + (0.06 if wealth_materials else 0.0)
            risk = 0.2 + profile_risk * 0.28 + (0.14 if vault.get("vault_state") == "activated" else 0.04)
            score_parts = ["已见库象" if vault.get("has_vault_signal") else "未见明确库象"]
        else:
            score = 0.06 + peer * 1.05 + wealth * 0.42 + hit_bonus + (0.1 if usable_state == "wealth_as_taboo" else 0.0)
            risk = 0.34 + peer * 0.58 + profile_risk * 0.38 + (0.08 if top_channel == "resource_integration" else 0.0)
            score_parts = [f"合作/竞争{_signal_label(peer)}", f"画像风险{_signal_label(profile_risk)}"]
        raw[path_id] = (score, risk, score_parts, wealth_materials)

    rows: List[Dict[str, Any]] = []
    for path_id, (score, risk, score_parts, bazi_facts) in raw.items():
        threshold = _safe_float(WEALTH_PATH_TEMPLATES[path_id].get("threshold"), 0.3)
        if score < threshold and path_id not in {"wealth_vault", "leakage_risk"}:
            continue
        if path_id == "wealth_vault" and not vault.get("has_vault_signal") and score < 0.35:
            continue
        if path_id == "leakage_risk" and risk < 0.42 and score < 0.34:
            continue
        rows.append(
            _path_row(
                path_id=path_id,
                score=score,
                risk=risk,
                hits=_keyword_hits(text, path_id),
                score_parts=score_parts,
                bazi_facts=bazi_facts,
                profile=profile,
            )
        )
    return sorted(rows, key=lambda row: (_safe_float(row.get("score"), 0.0), -_safe_float(row.get("risk"), 0.0)), reverse=True)


def _merge_output_work_path(primary: Mapping[str, Any], secondary: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    out = dict(primary)
    secondary_by_id = {str(row.get("id") or ""): row for row in secondary if isinstance(row, Mapping)}
    primary_id = _clean_label(out.get("id"))
    pair_id = ""
    if primary_id == "output_controls_pressure" and "output_to_wealth" in secondary_by_id:
        pair_id = "output_to_wealth"
    elif primary_id == "output_to_wealth" and "output_controls_pressure" in secondary_by_id:
        pair_id = "output_controls_pressure"
    if not pair_id:
        return out
    pair = secondary_by_id[pair_id]
    out["id"] = "output_work_to_money"
    out["classic_label"] = "食伤制杀 + 食伤生财"
    out["plain_name"] = "用专业输出解决难题并变现"
    out["plain_summary"] = (
        "主线不是单纯靠职位吃工资，而是先用技术、表达、方案或产品处理复杂问题、规则压力和竞争场景，"
        "再把解决方案转成项目收入、服务收入、产品收入或更高议价。"
    )
    out["driver"] = "output_authority"
    out["carrier_type"] = "method_and_contract"
    out["risk_hint"] = "这类钱来自做功后的转化，必须把交付边界、定价、回款和合规先写清。"
    evidence = ["组合路径：专业输出先处理压力，再把成果转成收入"]
    evidence.extend(item for item in out.get("evidence") or [] if item not in evidence)
    evidence.extend(item for item in pair.get("evidence") or [] if item not in evidence)
    out["evidence"] = _clean_str_list(evidence, limit=10)
    out["score"] = round(_clamp(max(_safe_float(out.get("score"), 0.0), _safe_float(pair.get("score"), 0.0))), 3)
    out["risk"] = round(_clamp(max(_safe_float(out.get("risk"), 0.0), _safe_float(pair.get("risk"), 0.0))), 3)
    out["confidence"] = round(_clamp(max(_safe_float(out.get("confidence"), 0.0), _safe_float(pair.get("confidence"), 0.0)) + 0.04), 3)
    return out


def _carrier(primary_path: Mapping[str, Any], profile: Mapping[str, Any]) -> Dict[str, Any]:
    carrier_type = _clean_label(primary_path.get("carrier_type")) or "mixed"
    requirements = _clean_str_list(profile.get("bridge_requirements"), limit=4)
    if not requirements:
        requirements = {
            "self_capacity": ["把技能、产品和交付做成可复用的变现方式"],
            "method_and_contract": ["把方法、合同、交付边界和成本控制先建好"],
            "platform": ["用平台授权、职位职责和合同规则承接机会"],
            "knowledge": ["沉淀证书、方法论、IP 或专业信用"],
            "team": ["先写清合伙权责、分账和退出机制"],
            "asset": ["把现金流、库存、回款和资产转换节奏管理好"],
            "contract": ["把客户、账期、预算和回款规则先写清楚"],
            "boundary": ["先守住分账、成本、账期和合作边界"],
        }.get(carrier_type, ["先明确收入来源、承接条件和风险边界"])
    score = _clamp(_safe_float(primary_path.get("score"), 0.0) - _safe_float(primary_path.get("risk"), 0.0) * 0.22 + 0.18)
    return {
        "type": carrier_type,
        "plain_type": {
            "self_capacity": "个人能力与产品化交付",
            "method_and_contract": "方法论、合同与交付边界",
            "platform": "平台、职位与规则授权",
            "knowledge": "知识、资质与专业信用",
            "team": "团队、合伙与资源边界",
            "asset": "资产、库存、回款与现金流",
            "contract": "客户、合同与稳定现金流",
            "boundary": "合作边界与现金流纪律",
        }.get(carrier_type, "综合承接能力"),
        "score": round(score, 3),
        "requirements": requirements,
    }


def _monetization_engine(primary_path: Mapping[str, Any]) -> Dict[str, Any]:
    driver = _clean_label(primary_path.get("driver")) or "mixed"
    score = _safe_float(primary_path.get("score"), 0.0)
    risk = _safe_float(primary_path.get("risk"), 0.0)
    return {
        "driver": driver,
        "plain_driver": {
            "wealth": "直接收入与客户资源",
            "output": "技能、产品、内容或表达",
            "output_authority": "解决高压复杂问题",
            "authority": "平台、职位、合同和规则",
            "seal": "知识、资质、方法论和信用",
            "peer": "合作资源、人脉和团队",
            "vault": "资产沉淀、回款和资金结构",
            "risk": "风险控制与边界管理",
        }.get(driver, "混合变现链路"),
        "chain_integrity": round(_clamp(score * 0.72 + (1.0 - risk) * 0.28), 3),
    }


def _leakage_points(paths: Sequence[Mapping[str, Any]], profile: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        if path.get("id") != "leakage_risk":
            continue
        rows.append(
            {
                "id": "peer_split",
                "plain_name": "合作分账与现金流泄漏",
                "risk": round(_safe_float(path.get("risk"), 0.0), 3),
                "evidence": _clean_str_list(path.get("evidence"), limit=5),
            }
        )
    for risk_text in _clean_str_list(profile.get("risks"), limit=4):
        if any(word in risk_text for word in ("合作", "分账", "现金流", "成本", "承诺")):
            rows.append(
                {
                    "id": f"profile_risk_{len(rows) + 1}",
                    "plain_name": risk_text,
                    "risk": round(max(0.32, _safe_float(profile.get("risk"), 0.0)), 3),
                    "evidence": ["来自财富画像风险"],
                }
            )
    return rows[:5]


def _timeline_rows(meta: Mapping[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    preview = meta.get("wealth_timeline_preview") if isinstance(meta.get("wealth_timeline_preview"), Mapping) else {}
    if not preview:
        return [], []
    luck_window = preview.get("luck_window") if isinstance(preview.get("luck_window"), Mapping) else {}
    trends = []
    if luck_window:
        trends.append(
            {
                "luck_pillar": _clean_label(luck_window.get("luck_pillar")),
                "start_year": luck_window.get("start_year"),
                "end_year": luck_window.get("end_year"),
                "summary": _clean_label(luck_window.get("summary"), limit=160),
                "score": round(_safe_float(luck_window.get("score"), 0.0), 3),
                "risk": round(_safe_float(luck_window.get("risk"), 0.0), 3),
            }
        )
    watchlist = []
    for row in preview.get("top_attention_years") if isinstance(preview.get("top_attention_years"), list) else []:
        if not isinstance(row, Mapping):
            continue
        watchlist.append(
            {
                "year": row.get("year"),
                "focus": _clean_label(row.get("focus")),
                "attention_type": _clean_label(row.get("attention_type")),
                "score": round(_safe_float(row.get("score"), 0.0), 3),
                "risk": round(_safe_float(row.get("risk"), 0.0), 3),
                "triggered_components": _clean_str_list(row.get("tags"), limit=5),
            }
        )
    return trends[:2], watchlist[:5]


def _evidence_graph(
    *,
    primary_path: Mapping[str, Any],
    secondary_paths: Sequence[Mapping[str, Any]],
    wealth_source: Mapping[str, Any],
    wealth_vault: Mapping[str, Any],
    leakage_points: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = [
        {"id": "wealth_source", "type": "source", "label": _clean_label(wealth_source.get("plain_source"))},
        {"id": str(primary_path.get("id") or "primary_path"), "type": "path", "label": _clean_label(primary_path.get("plain_name"))},
    ]
    edges: List[Dict[str, Any]] = [{"from": "wealth_source", "to": str(primary_path.get("id") or "primary_path"), "relation": "feeds"}]
    for path in secondary_paths[:3]:
        pid = _clean_label(path.get("id"))
        nodes.append({"id": pid, "type": "secondary_path", "label": _clean_label(path.get("plain_name"))})
        edges.append({"from": pid, "to": str(primary_path.get("id") or "primary_path"), "relation": "supports_or_competes"})
    if wealth_vault.get("has_vault_signal"):
        nodes.append({"id": "wealth_vault", "type": "vault", "label": _clean_label(wealth_vault.get("plain_summary"), limit=80)})
        edges.append({"from": "wealth_vault", "to": str(primary_path.get("id") or "primary_path"), "relation": "stores_or_releases"})
    for index, row in enumerate(leakage_points[:3], start=1):
        rid = f"leakage_{index}"
        nodes.append({"id": rid, "type": "risk", "label": _clean_label(row.get("plain_name"), limit=80)})
        edges.append({"from": rid, "to": str(primary_path.get("id") or "primary_path"), "relation": "leaks"})
    return {"nodes": nodes, "edges": edges}


def build_wealth_code_contract() -> Dict[str, Any]:
    return {
        "contract": WEALTH_CODE_CONTRACT,
        "is_l3_topic_decoder": True,
        "topic": "wealth",
        "knowledge_base": WEALTH_PATH_KNOWLEDGE_ID,
        "path_templates": list(WEALTH_PATH_TEMPLATES.keys()),
        "final_meta_keys": list(FINAL_WEALTH_CODE_KEYS),
        "read_only_sources": [
            "bazi_image",
            "wealth_profile",
            "ten_gods_runtime",
            "god_ring_authority",
            "plugin_claims",
            "wealth_timeline_preview",
        ],
        "constraints": [
            "财富密码只读 L0-L3 已有事实，不回写体用、格局、十神能量或参数。",
            "财富路径评分只表示路径闭合度和关注方向，不承诺金额、必发财或确定年份。",
            "LLM 只能消费 wealth_code 合同，不得自由读取原始八字重新推断。",
        ],
    }


def normalize_wealth_code_meta(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping) or not value:
        return {}
    out = {key: value.get(key) for key in FINAL_WEALTH_CODE_KEYS if key in value}
    out["contract"] = _clean_label(out.get("contract")) or WEALTH_CODE_CONTRACT
    out["topic"] = _clean_label(out.get("topic")) or "wealth"
    out["is_l3_topic_decoder"] = bool(out.get("is_l3_topic_decoder", True))
    out["knowledge_base"] = dict(out.get("knowledge_base")) if isinstance(out.get("knowledge_base"), Mapping) else {
        "id": WEALTH_PATH_KNOWLEDGE_ID,
        "mode": "curated_rule_templates",
    }
    for key in (
        "secondary_paths",
        "leakage_points",
        "decade_path_trends",
        "flow_year_watchlist",
        "evidence",
        "learning_hooks",
        "guardrails",
    ):
        raw = out.get(key)
        out[key] = list(raw) if isinstance(raw, list) else []
    for key in ("primary_wealth_path", "wealth_source", "monetization_engine", "carrier", "wealth_vault", "evidence_graph", "llm_boundary"):
        raw = out.get(key)
        out[key] = dict(raw) if isinstance(raw, Mapping) else {}
    out["score"] = round(_clamp(_safe_float(out.get("score"), 0.0)), 3)
    out["confidence"] = round(_clamp(_safe_float(out.get("confidence"), 0.0)), 3)
    out["risk"] = round(_clamp(_safe_float(out.get("risk"), 0.0)), 3)
    return out


def resolve_wealth_code(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    profile = _profile_from_tensor(pt, meta)
    bazi_image = _bazi_image_from_tensor(pt, meta)
    scores = read_runtime_scores(pt)
    if not scores:
        scores = pt.get("deity_scores") if isinstance(pt.get("deity_scores"), dict) else {}
    text = _facts_text(pt, meta)
    if not profile and not bazi_image and not scores:
        return {"wealth_code": {}, "confidence": 0.0}

    paths = _score_paths(scores=scores, profile=profile, bazi_image=bazi_image, text=text)
    if not paths:
        return {"wealth_code": {}, "confidence": 0.0}

    opportunity_paths = [row for row in paths if row.get("id") != "leakage_risk"]
    raw_primary = opportunity_paths[0] if opportunity_paths else paths[0]
    raw_secondary = [row for row in paths if row.get("id") != raw_primary.get("id")][:5]
    primary = _merge_output_work_path(raw_primary, raw_secondary)
    secondary = [row for row in paths if row.get("id") != raw_primary.get("id") and row.get("id") != primary.get("id")][:5]
    wealth_source = _wealth_source(bazi_image, profile, primary_path=primary)
    wealth_vault = _wealth_vault(bazi_image)
    leakage = _leakage_points(paths, profile)
    decade_trends, year_watchlist = _timeline_rows(meta)
    risk = _clamp(max(_safe_float(primary.get("risk"), 0.0), _safe_float(profile.get("risk"), 0.0), max((_safe_float(row.get("risk"), 0.0) for row in leakage), default=0.0) * 0.88))
    score = _clamp(max(_safe_float(primary.get("score"), 0.0), _safe_float(profile.get("score"), 0.0) * 0.86))
    confidence = _clamp(
        0.34
        + _safe_float(primary.get("confidence"), 0.0) * 0.34
        + _safe_float(profile.get("confidence"), 0.0) * 0.18
        + (0.08 if bazi_image else 0.0)
        + min(0.08, len(secondary) * 0.018),
        0.35,
        0.92,
    )
    evidence = list(primary.get("evidence") or [])
    evidence.extend(_clean_str_list(profile.get("evidence"), limit=4))
    if wealth_source.get("plain_source"):
        evidence.append("财源材质：" + _clean_label(wealth_source.get("plain_source"), limit=120))
    if wealth_vault.get("has_vault_signal"):
        evidence.append("财库观察：" + _clean_label(wealth_vault.get("plain_summary"), limit=140))

    code = {
        "contract": WEALTH_CODE_CONTRACT,
        "topic": "wealth",
        "is_l3_topic_decoder": True,
        "knowledge_base": {
            "id": WEALTH_PATH_KNOWLEDGE_ID,
            "mode": "curated_rule_templates",
            "version": "2026-04-26",
            "template_count": len(WEALTH_PATH_TEMPLATES),
        },
        "score": round(score, 3),
        "confidence": round(confidence, 3),
        "risk": round(risk, 3),
        "primary_wealth_path": primary,
        "secondary_paths": secondary,
        "wealth_source": wealth_source,
        "monetization_engine": _monetization_engine(primary),
        "carrier": _carrier(primary, profile),
        "wealth_vault": wealth_vault,
        "leakage_points": leakage,
        "decade_path_trends": decade_trends,
        "flow_year_watchlist": year_watchlist,
        "evidence_graph": _evidence_graph(
            primary_path=primary,
            secondary_paths=secondary,
            wealth_source=wealth_source,
            wealth_vault=wealth_vault,
            leakage_points=leakage,
        ),
        "evidence": _clean_str_list(evidence, limit=12),
        "llm_boundary": {
            "allowed_inputs": ["wealth_code", "wealth_profile", "wealth_timeline"],
            "forbidden_inputs": ["raw_bazi_free_read", "raw_birth_time", "free_chart_reinterpretation"],
            "must_avoid": ["必发财", "无财", "破产", "确定金额", "确定发财年份", "把财星强弱直接等同财富成败"],
        },
        "learning_hooks": [
            "topic.wealth_code.path.calibration",
            "topic.wealth_code.vault.calibration",
            "topic.wealth_code.leakage.calibration",
        ],
        "guardrails": build_wealth_code_contract()["constraints"],
    }
    normalized = normalize_wealth_code_meta(code)
    return {"contract": normalized["contract"], "confidence": normalized["confidence"], "wealth_code": normalized}
