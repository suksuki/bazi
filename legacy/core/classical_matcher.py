# core/classical_matcher.py
"""
SOP V7.0：古典格局判定引擎（法理分析器）
========================================
将 L1 古典扫描逻辑封装为统一接口 get_classical_patterns(chart, context)，
与 5D 全息观测并列，构成双模态观测。
输入对齐：八字、大运、流年、地域。匹配度 = Conditions_Met/Conditions_Total * α（α 含地域/岁运加成）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 项目根与 scripts 加入 path，供 pattern_scanner_* 导入链使用
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SCRIPTS = _ROOT / "scripts"
if _SCRIPTS.exists() and str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def _load_classical_registry() -> Dict[str, Any]:
    """从 config/classical_registry.json 加载古典格局索引与 α 系数。"""
    path = _ROOT / "config" / "classical_registry.json"
    if not path.exists():
        return {"patterns": {}, "alpha": {"base": 1.0, "geo_bonus": 0.05, "annual_bonus": 0.03}, "verdicts": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _chart_to_bazi(chart: List[str]) -> Dict[str, str]:
    """四柱列表 -> case['bazi'] 格式。"""
    if not chart or len(chart) < 4:
        return {}
    return {
        "year": chart[0] if len(chart) > 0 else "",
        "month": chart[1] if len(chart) > 1 else "",
        "day": chart[2] if len(chart) > 2 else "",
        "hour": chart[3] if len(chart) > 3 else "",
    }


# SOP V7.5：合成能量场（原局+大运+流年）— 三合/三会、十神并入
_SAN_HE = {"火": {"寅", "午", "戌"}, "水": {"申", "子", "辰"}, "木": {"亥", "卯", "未"}, "金": {"巳", "酉", "丑"}}
_SAN_HUI = {"木": {"寅", "卯", "辰"}, "火": {"巳", "午", "未"}, "金": {"申", "酉", "戌"}, "水": {"亥", "子", "丑"}}


def _compute_composite_branches(
    chart: List[str],
    luck_pillar: str = "",
    annual_pillar: str = "",
) -> List[str]:
    """原局四柱地支 + 大运支 + 流年支（共 6 支），用于三合/三会检测。"""
    branches = []
    for p in (chart or [])[:4]:
        if isinstance(p, str) and len(p) >= 2:
            branches.append(p[1])
        else:
            branches.append("")
    if isinstance(luck_pillar, str) and len(luck_pillar) >= 2:
        branches.append(luck_pillar[1])
    if isinstance(annual_pillar, str) and len(annual_pillar) >= 2:
        branches.append(annual_pillar[1])
    return [b for b in branches if b]


def _detect_san_he_san_hui(branches: List[str]) -> Dict[str, float]:
    """检测三合/三会，返回五行权重增量（用于合成能量）。"""
    s = set(branches)
    out = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    for wuxing, he in _SAN_HE.items():
        if he <= s:
            out[wuxing] = out.get(wuxing, 0) + 1.0
    for wuxing, hui in _SAN_HUI.items():
        if hui <= s:
            out[wuxing] = out.get(wuxing, 0) + 0.8
    return out


def _merge_ten_gods_with_transport(
    ten_gods: Dict[str, float],
    day_master: str,
    luck_pillar: str = "",
    annual_pillar: str = "",
    transport_weight: float = 0.8,
) -> Dict[str, float]:
    """
    SOP V7.5：将大运、流年天干对日主的十神并入 ten_gods，使从格/化气能感知岁运。
    大运/流年干按 transport_weight 加权加入对应十神，便于 L1 在「合成场」下重跑。
    """
    if not day_master:
        return dict(ten_gods) if ten_gods else {}
    try:
        from core.classical_tougan import get_ten_god_code
    except Exception:
        return dict(ten_gods) if ten_gods else {}
    out = dict(ten_gods) if ten_gods else {}
    for pillar_name, pillar in [("大运", luck_pillar), ("流年", annual_pillar)]:
        if not isinstance(pillar, str) or len(pillar) < 1:
            continue
        stem = pillar[0].strip()
        code = get_ten_god_code(day_master.strip(), stem)
        if code:
            out[code] = out.get(code, 0.0) + transport_weight
    return out


def _build_ten_gods(chart: List[str], day_master: str) -> Dict[str, float]:
    """从四柱与日主计算十神能量向量（ZG, PG, ...），供 L1 从格等判定使用。"""
    try:
        from core.physics_engine import compute_energy_flux
    except Exception:
        return {}
    en_to_code = {
        "bi_jian": "ZB", "jie_cai": "PB", "shi_shen": "ZS", "shang_guan": "PS",
        "zheng_cai": "ZR", "pian_cai": "PR", "zheng_guan": "ZG", "qi_sha": "PG",
        "zheng_yin": "ZC", "pian_yin": "PC",
    }
    en_to_cn = {
        "bi_jian": "比肩", "jie_cai": "劫财", "shi_shen": "食神", "shang_guan": "伤官",
        "zheng_cai": "正财", "pian_cai": "偏财", "zheng_guan": "正官", "qi_sha": "七杀",
        "zheng_yin": "正印", "pian_yin": "偏印",
    }
    out = {}
    for en, code in en_to_code.items():
        cn = en_to_cn.get(en, "")
        if cn:
            try:
                out[code] = float(compute_energy_flux(chart, day_master, cn))
            except Exception:
                out[code] = 0.0
    return out


def _run_l1_scanners(case: Dict[str, Any]) -> List[str]:
    """对 case 运行各梯队 L1 扫描，返回命中的 pattern_id 列表（去重）。"""
    seen: set = set()
    out: List[str] = []

    try:
        from pattern_scanner_v57 import l1_match_all_v57
        for pid in l1_match_all_v57(case):
            if pid and pid not in seen:
                seen.add(pid)
                out.append(pid)
    except Exception:
        pass

    try:
        from pattern_scanner_v58 import l1_match_a31_through_a35
        for pid in l1_match_a31_through_a35(case):
            if pid and pid not in seen:
                seen.add(pid)
                out.append(pid)
    except Exception:
        pass

    try:
        from pattern_scanner_v59 import l1_match_a36_through_a40
        for pid in l1_match_a36_through_a40(case):
            if pid and pid not in seen:
                seen.add(pid)
                out.append(pid)
    except Exception:
        pass

    try:
        from pattern_scanner_v60 import l1_match_a41_through_a50
        for pid in l1_match_a41_through_a50(case):
            if pid and pid not in seen:
                seen.add(pid)
                out.append(pid)
    except Exception:
        pass

    try:
        from pattern_scanner_v62 import l1_match_a46_through_a60
        for pid in l1_match_a46_through_a60(case):
            if pid and pid not in seen:
                seen.add(pid)
                out.append(pid)
    except Exception:
        pass

    return out


# SOP V7.3 / V7.6：古典原典硬规则后置过滤；V7.6 神煞加严（将星能量/冲、驿马马头、天乙空亡冲）
# 将星：寅午戌→午，申子辰→子，巳酉丑→酉，亥卯未→卯
_JIANG_XING = {
    "寅": "午", "午": "午", "戌": "午", "申": "子", "子": "子", "辰": "子",
    "巳": "酉", "酉": "酉", "丑": "酉", "亥": "卯", "卯": "卯", "未": "卯",
}
# 地支六冲
_BRANCH_CHONG = {
    "子": "午", "午": "子", "丑": "未", "未": "丑",
    "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}
# 地支本气五行（用于将星能量占比）
_BRANCH_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}
# 驿马：年支/日支 → 驿马支（马头带财/官/印 用）
_YIMA = {
    "寅": "申", "午": "申", "戌": "申", "申": "寅", "子": "寅", "辰": "寅",
    "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳",
}
# 天乙贵人：日干 → 贵人地支列表
_TIANYI = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["午", "寅"],
}
# 马头带财/官/印 的十神名
_MA_TOU_ALLOWED = {"正财", "偏财", "正官", "七杀", "正印", "偏印"}


def _get_void_branches(day_pillar: str) -> List[str]:
    """日柱旬空两支，与 BaziProfile.get_void_branches 逻辑一致。"""
    if not day_pillar or len(day_pillar) < 2:
        return []
    gan_list, zhi_list = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
    try:
        g_idx = gan_list.index(day_pillar[0])
        z_idx = zhi_list.index(day_pillar[1])
        xun_start = (z_idx - g_idx) % 12
        return [zhi_list[(xun_start + 10) % 12], zhi_list[(xun_start + 11) % 12]]
    except Exception:
        return []


def _stem_ten_god_cn(day_master: str, stem: str) -> str:
    """日干对某天干的十神中文名。"""
    if not day_master or not stem:
        return ""
    try:
        from core.classical_tougan import get_ten_god_code
        code = get_ten_god_code(day_master.strip(), stem.strip())
        return _TEN_GOD_CODE_TO_CN.get(code, "")
    except Exception:
        return ""


def _classical_hard_rule_filter(
    chart: List[str],
    matched_ids: List[str],
    day_master: Optional[str] = None,
    registry: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    SOP V7.3：对 L1 命中结果做古典原典硬规则二次校验，仅保留 100% 符合者。
    SOP V7.6：神煞加严——将星须能量占比且不被冲；驿马须马头带财/官/印；天乙须贵人不空亡不冲。
    地域与岁运不参与是否命中，仅影响后续 rank_classical_patterns 的 Final_Score。
    """
    if not chart or len(chart) < 4:
        return []
    stems = []
    branches = []
    for p in chart:
        if isinstance(p, str) and len(p) >= 2:
            stems.append(p[0])
            branches.append(p[1])
        else:
            stems.append("")
            branches.append("")
    year_branch = branches[0] if len(branches) > 0 else ""
    day_branch = branches[2] if len(branches) > 2 else ""
    branch_set = set(b for b in branches if b)
    tier3 = (registry or {}).get("tier3_hardening") or {}
    day_pillar = chart[2] if len(chart) > 2 else ""
    void_branches = set(_get_void_branches(day_pillar))
    dm = (day_master or "").strip()

    out = []
    for pid in matched_ids:
        if pid == "A-57":
            # 将星格（V7.6）：将星在柱、不被冲、且将星支五行在四柱中占比 >= min_energy_share
            jx = None
            for trigger in [year_branch, day_branch]:
                if trigger:
                    jx = _JIANG_XING.get(trigger)
                    if jx and jx in branch_set:
                        break
            if not jx or jx not in branch_set:
                continue
            chong = _BRANCH_CHONG.get(jx)
            if chong and chong in branch_set:
                continue
            wx = _BRANCH_WUXING.get(jx)
            if wx:
                same_count = sum(1 for b in branches if b and _BRANCH_WUXING.get(b) == wx)
                min_share = float(tier3.get("A-57_jiangxing_min_energy_share", 0.15))
                if same_count / 4.0 < min_share:
                    continue
        elif pid == "A-54":
            # 驿马格（V7.6）：见马星且马头带财/官/印（驿马所在柱天干十神为财/官/印）
            if not tier3.get("A-54_require_ma_tou_cai_guan_yin", True):
                out.append(pid)
                continue
            yima_branch = None
            for trigger in [year_branch, day_branch]:
                if trigger:
                    ym = _YIMA.get(trigger)
                    if ym and ym in branch_set:
                        yima_branch = ym
                        break
            if not yima_branch:
                continue
            # 马头：驿马支所在柱的天干十神
            ma_tou_ok = False
            for i, b in enumerate(branches):
                if b == yima_branch and i < len(stems) and dm:
                    shi = _stem_ten_god_cn(dm, stems[i])
                    if shi in _MA_TOU_ALLOWED:
                        ma_tou_ok = True
                        break
            if not ma_tou_ok:
                continue
        elif pid == "A-55":
            # 天乙格（V7.6）：贵人支在柱且不入空亡、不被冲
            if not tier3.get("A-55_require_no_void_no_chong", True):
                out.append(pid)
                continue
            targets = _TIANYI.get(dm, [])
            has_ok = False
            for t in targets:
                if t not in branch_set:
                    continue
                if t in void_branches:
                    continue
                if _BRANCH_CHONG.get(t) in branch_set:
                    continue
                has_ok = True
                break
            if not has_ok:
                continue
        out.append(pid)
    return out


def _compute_alpha(context: Optional[Dict[str, Any]], registry: Dict[str, Any]) -> float:
    """地域、流年加成：α = base + geo_bonus + annual_bonus（若提供）。"""
    return _compute_alpha_for_pattern(None, context, registry)


def _compute_alpha_for_pattern(
    pattern_id: Optional[str],
    context: Optional[Dict[str, Any]],
    registry: Dict[str, Any],
) -> float:
    """
    按格局计算 α：若 pattern_id 在 annual_sensitivity.pattern_ids 且 context 含岁运，
    使用 annual_bonus_override 提高岁运灵敏度（岁运引发格局变幻）。
    """
    alpha_cfg = registry.get("alpha") or {}
    base = float(alpha_cfg.get("base", 1.0))
    geo_bonus = float(alpha_cfg.get("geo_bonus", 0.05))
    annual_bonus = float(alpha_cfg.get("annual_bonus", 0.03))

    sens = registry.get("annual_sensitivity") or {}
    sensitive_ids = sens.get("pattern_ids") or []
    annual_override = float(sens.get("annual_bonus_override", 0.10))

    has_annual = bool(context and (context.get("annual_pillar") or context.get("luck_pillar")))
    use_override = pattern_id and pattern_id in sensitive_ids and has_annual
    annual_add = annual_override if use_override else (annual_bonus if has_annual and context else 0.0)

    alpha = base
    if context and (context.get("geo_city") or context.get("geo_region")):
        alpha += geo_bonus
    alpha += annual_add
    return min(1.2, alpha)


# SOP V7.5 地域对 integrity 的微调：得地加成、失地损耗（系数来自 config/classical_registry.json integrity_geo）
_ELEMENT_EN_TO_ZH = {"Fire": "火", "Water": "水", "Wood": "木", "Metal": "金", "Earth": "土"}
_WUXING_KE = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}  # 克：key 克 value（地域克格局即 geo 克 pattern）


def _get_geo_wuxing(geo_city: Optional[str]) -> Optional[str]:
    """从 context.geo_city（GEO_CITY_MAP 的 key）解析地域主气五行。"""
    if not geo_city or geo_city == "None":
        return None
    try:
        from core.data.geo_cities import GEO_CITY_MAP
    except Exception:
        return None
    raw = GEO_CITY_MAP.get(geo_city)
    if not raw or not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return None
    elem = (raw[1] or "").strip().split("/")[0].strip()  # "Fire/Earth" -> "Fire"
    return _ELEMENT_EN_TO_ZH.get(elem)


def _integrity_geo_adjust(
    integrity: float,
    pattern_wuxing: Optional[str],
    geo_wuxing: Optional[str],
    registry: Dict[str, Any],
) -> float:
    """
    得地：格局五行与地域五行一致 → integrity += de_di_bonus（封顶 integrity_cap）。
    失地：地域五行克格局五行 → integrity -= shi_di_penalty。
    系数从 registry.integrity_geo 读取，零硬编码。
    """
    if not pattern_wuxing or not geo_wuxing:
        return integrity
    cfg = (registry.get("integrity_geo") or {})
    cap = float(cfg.get("integrity_cap", 1.0))
    bonus = float(cfg.get("de_di_bonus", 0.05))
    penalty = float(cfg.get("shi_di_penalty", 0.10))
    out = integrity
    if pattern_wuxing == geo_wuxing:
        out = min(cap, out + bonus)
    if _WUXING_KE.get(geo_wuxing) == pattern_wuxing:
        out = max(0.0, out - penalty)
    return out


def _detect_structural_rescue(
    pid: str,
    ten_gods: Dict[str, float],
) -> bool:
    """
    SOP V7.7：古典成败救应——结构完整度。有救应则 Final_Score 可加权。
    逻辑关系成立即算，不设能量阈值。ten_gods 可为原局或合成场。
    """
    if not ten_gods:
        return False
    has = lambda *codes: any(ten_gods.get(c, 0) > 0 for c in codes)
    # 正官格：见财星（财生官）
    if pid == "A-01":
        return has("ZR", "PR")
    # 七杀格：见印或食伤（制化）
    if pid == "A-02":
        return has("ZC", "PC", "ZS", "PS")
    # 伤官格：见财或印（伤官生财 / 配印）
    if pid == "A-05":
        return has("ZR", "PR", "ZC", "PC")
    # 偏财格：见官或食伤
    if pid == "A-03":
        return has("ZG", "PG", "ZS", "PS")
    return False


def _energy_tier(integrity: float, registry: Optional[Dict[str, Any]] = None) -> str:
    """SOP V7.7：能量成色分级，供判词定性描述。不参与是否格成。阈值从 config 读取。"""
    cfg = (registry or {}).get("sop_v77_qualitative") or {}
    high_thr = float(cfg.get("energy_tier_high_threshold", 0.9))
    low_thr = float(cfg.get("energy_tier_low_threshold", 0.7))
    if integrity >= high_thr:
        return "high"
    if integrity < low_thr:
        return "low"
    return "mid"


def get_classical_patterns(
    chart: List[str],
    day_master: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    古典格局判定：SOP V7.7 弹性定性——结构优先，逻辑成立即格成，匹配度统一 100%。
    能量（integrity）仅表成色/清浊，不决定是否成格。
    第一步：原局 L1 + 硬规则后置 → matched_original。
    第二步（有大运/流年时）：合成场 L1 + 硬规则 → matched_composite（时空补齐）。
    第三步：合并两路，标注 state、integrity、verdict_type、qualitative_match、energy_tier、structural_rescue。
    """
    registry = _load_classical_registry()
    patterns_cfg = registry.get("patterns") or {}
    verdicts_cfg = registry.get("verdicts") or {}
    verdict_ok = verdicts_cfg.get("格成", "古典法理成立，与命局结构相符。")
    verdict_fail = verdicts_cfg.get("破格", "古典法理未达或结构有破，可参 5D 流形。")
    auth = registry.get("authority_tiers") or {}
    cong_ge_ids = set(auth.get("cong_ge_ids") or [])
    pattern_tier = auth.get("pattern_tier") or {}

    bazi = _chart_to_bazi(chart)
    if not bazi or not day_master:
        by_pattern_id = {
            pid: {
                "classical_name": (patterns_cfg.get(pid) or {}).get("classical_name", pid),
                "affinity": 0.0,
                "status": "破格",
                "verdict_snippet": verdict_fail,
            }
            for pid in patterns_cfg
        }
        return {"items": [], "by_pattern_id": by_pattern_id}

    luck = (context or {}).get("luck_pillar") or ""
    annual = (context or {}).get("annual_pillar") or ""

    case_orig: Dict[str, Any] = {"bazi": bazi}
    ten_gods = _build_ten_gods(chart, day_master)
    if ten_gods:
        case_orig["ten_gods"] = ten_gods
    raw_orig = _run_l1_scanners(case_orig)
    matched_original = _classical_hard_rule_filter(chart, raw_orig, day_master=day_master, registry=registry)

    matched_composite: List[str] = []
    if luck or annual:
        ten_composite = _merge_ten_gods_with_transport(ten_gods or {}, day_master, luck, annual)
        case_comp: Dict[str, Any] = {"bazi": bazi, "ten_gods": ten_composite}
        raw_comp = _run_l1_scanners(case_comp)
        matched_composite = _classical_hard_rule_filter(chart, raw_comp, day_master=day_master, registry=registry)

    set_orig = set(matched_original)
    set_comp = set(matched_composite)
    all_matched = set_orig | set_comp
    # 合成场十神（用于成败救应：岁运补齐的也算结构完整）
    ten_for_rescue = _merge_ten_gods_with_transport(ten_gods or {}, day_master, luck, annual) if (luck or annual) else (ten_gods or {})

    items: List[Dict[str, Any]] = []
    by_pattern_id: Dict[str, Dict[str, Any]] = {}

    for pid, meta in patterns_cfg.items():
        classical_name = meta.get("classical_name") or pid
        tier = pattern_tier.get(pid, 3)
        if pid not in all_matched:
            by_pattern_id[pid] = {"classical_name": classical_name, "affinity": 0.0, "status": "破格", "verdict_snippet": verdict_fail, "tier": tier}
            continue
        aff = 100.0
        status = "格成"
        in_orig = pid in set_orig
        in_comp = pid in set_comp
        if in_orig and in_comp:
            state = "original"
            integrity = 1.0
            verdict_type = "成格"
            snippet = verdict_ok
        elif in_comp and not in_orig:
            state = "formed_by_transport"
            integrity = 0.95
            verdict_type = "岁运成格"
            snippet = "此岁运交汇，格局由岁运催化成立，宜结合流年大运论成败。"
        elif in_orig and not in_comp and pid in cong_ge_ids:
            state = "broken_year"
            integrity = 0.65
            verdict_type = "岁运破格"
            snippet = "原局格成，然当前岁运引动破格（如从格见比劫），宜慎防逆势。"
        else:
            state = "original"
            integrity = 1.0
            verdict_type = "成格"
            snippet = verdict_ok

        # SOP V7.5 地域对 integrity 的微调：得地加成、失地损耗
        pattern_wuxing = meta.get("wuxing")
        geo_wuxing = _get_geo_wuxing((context or {}).get("geo_city"))
        integrity = _integrity_geo_adjust(integrity, pattern_wuxing, geo_wuxing, registry)

        # SOP V7.7 弹性定性：逻辑成即格成，统一 100%；能量仅表成色
        qualitative_match = True
        ephemeral = state == "formed_by_transport"
        energy_tier = _energy_tier(integrity, registry)
        structural_rescue = _detect_structural_rescue(pid, ten_for_rescue)

        item = {
            "pattern_id": pid,
            "classical_name": classical_name,
            "affinity": aff,
            "status": status,
            "verdict_snippet": snippet,
            "state": state,
            "integrity": integrity,
            "verdict_type": verdict_type,
            "tier": pattern_tier.get(pid, 3),
            "qualitative_match": qualitative_match,
            "ephemeral": ephemeral,
            "energy_tier": energy_tier,
            "structural_rescue": structural_rescue,
        }
        items.append(item)
        by_pattern_id[pid] = dict(item)

    items.sort(key=lambda x: (-x.get("integrity", 0), -x.get("affinity", 0), x.get("pattern_id", "")))

    triggers: List[str] = []
    for it in items:
        vt = it.get("verdict_type", "")
        name = it.get("classical_name", it.get("pattern_id", ""))
        if vt == "岁运成格":
            triggers.append(f"格局【{name}】由岁运催化成立，判词可写「此岁运交汇，化气成象」或等价表述。")
        elif vt == "岁运破格":
            triggers.append(f"格局【{name}】原局成格但当前岁运破格，判词须提示逆势与慎防。")

    return {
        "items": items,
        "by_pattern_id": by_pattern_id,
        "pattern_change_trigger": triggers,
    }


# 十神代码 -> 中文名（用于透干引动判定）
_TEN_GOD_CODE_TO_CN = {
    "ZG": "正官", "PG": "七杀", "ZR": "正财", "PR": "偏财",
    "ZS": "食神", "PS": "伤官", "ZC": "正印", "PC": "偏印",
    "ZB": "比肩", "PB": "劫财",
}


def _stem_to_ten_god_cn(day_master: str, stem: str) -> str:
    """日干对某天干的十神中文名。"""
    if not day_master or not stem:
        return ""
    try:
        from core.classical_tougan import get_ten_god_code
        code = get_ten_god_code(day_master.strip(), stem.strip())
        return _TEN_GOD_CODE_TO_CN.get(code, "")
    except Exception:
        return ""


def rank_classical_patterns(
    classical_items: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
    projection: Optional[Dict[str, float]] = None,
    day_master: str = "",
) -> List[Dict[str, Any]]:
    """
    SOP V7.2：按法理主权分排序古典格成格局，并分配 LLM 角色（sovereign / modifier / accessory）。
    Final_Score = W_tier × (1 + W_active) × W_energy，降序排列。
    仅处理 status=格成 的项；未命中或破格项不参与排序。
    """
    registry = _load_classical_registry()
    auth = registry.get("authority_tiers") or {}
    tier_weights = auth.get("tier_weights") or {"1": 1.0, "2": 0.75, "3": 0.4}
    pattern_tier = auth.get("pattern_tier") or {}
    trigger_keyword = auth.get("trigger_keyword") or {}
    needs_order = set(auth.get("needs_order") or [])
    cong_ge_ids = set(auth.get("cong_ge_ids") or [])
    active_w = auth.get("active_weights") or {}
    trans_bonus = float(active_w.get("transparent_bonus", 0.2))
    div_penalty = float(active_w.get("divergence_penalty", 0.3))
    order_bonus = float(auth.get("energy_order_bonus", 0.1))
    order_threshold = float(auth.get("energy_order_threshold", 0.5))
    structure_mult = float(auth.get("structural_rescue_multiplier", 2.0))

    # 仅格成
    items = [x for x in classical_items if (x.get("status") or "") == "格成"]
    if not items:
        return []

    annual = (context or {}).get("annual_pillar") or ""
    luck = (context or {}).get("luck_pillar") or ""
    year_gan = annual[0] if len(annual) >= 1 else ""
    luck_gan = luck[0] if len(luck) >= 1 else ""
    year_shi = _stem_to_ten_god_cn(day_master, year_gan)
    luck_shi = _stem_to_ten_god_cn(day_master, luck_gan)

    # 从格岁运背离：大运/流年天干为比劫（与日主同五行）则扣分
    def is_bijie_stem(dm: str, stem: str) -> bool:
        if not dm or not stem:
            return False
        cn = _stem_to_ten_god_cn(dm, stem)
        return cn in ("比肩", "劫财")

    O_val = float(projection.get("O", 0.0)) if projection else 0.0

    ranked: List[Dict[str, Any]] = []
    for item in items:
        pid = item.get("pattern_id", "")
        w_tier = float(tier_weights.get(str(pattern_tier.get(pid, 2)), 0.75))
        w_active = 0.0
        if context and day_master:
            kw = trigger_keyword.get(pid)
            if kw and (year_shi == kw or luck_shi == kw):
                w_active += trans_bonus
            if pid in cong_ge_ids and (is_bijie_stem(day_master, year_gan) or is_bijie_stem(day_master, luck_gan)):
                w_active -= div_penalty
        w_energy = 1.0
        if pid in needs_order and O_val >= order_threshold:
            w_energy += order_bonus
        final_score = w_tier * (1.0 + w_active) * w_energy
        # SOP V7.7 结构完整度加成：成败救应得分加倍
        if item.get("structural_rescue"):
            final_score *= structure_mult
        ranked.append({
            **item,
            "final_score": round(final_score, 4),
            "w_tier": w_tier,
            "w_active": w_active,
            "w_energy": w_energy,
        })
    ranked.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    # 分配 LLM 角色：第一顺位 sovereign，第二/三 modifier，其余 accessory
    for i, r in enumerate(ranked):
        if i == 0:
            r["llm_role"] = "sovereign"
        elif i <= 2:
            r["llm_role"] = "modifier"
        else:
            r["llm_role"] = "accessory"
    return ranked
