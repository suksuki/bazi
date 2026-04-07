"""PhysicsInferenceSkill: 物理参数读取、缓存与能量张量推断。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from threading import Lock
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field
from sqlmodel import select

from app.db.models import PhysicsInteractionParam, PhysicsPositionWeight, PhysicsSeasonalMatrix, SessionConsensus
from app.db.session import session_scope
from app.schemas.bazi_metadata import BaziMetadata
from app.skills.base import AuditLog, BaseSkill

DEFAULT_POSITION_WEIGHTS: Dict[str, float] = {
    "year": 0.20,
    "month": 0.45,
    "day": 0.25,
    "hour": 0.10,
}

DEFAULT_INTERACTION_PARAMS: Dict[str, float] = {
    "root_decay_lambda": 0.7,
    "through_stem_boost": 1.05,
    "conflict_penalty_gamma": 0.12,
    "EFF_PROMOTING": 1.2,
    "EFF_PROMOTING_SAME": 1.2,
    "EFF_PROMOTING_DIFF": 1.2,
    "EFF_EXHAUSTING": 0.8,
    "EFF_EXHAUSTING_SAME": 0.8,
    "EFF_EXHAUSTING_DIFF": 0.8,
    "EFF_RESTRAINING": 0.6,
    "EFF_RESTRAINING_SAME": 0.6,
    "EFF_RESTRAINING_DIFF": 0.6,
    "EFF_CONSUMING": 0.9,
    "EFF_CONSUMING_SAME": 0.9,
    "EFF_CONSUMING_DIFF": 0.9,
    "CF_FLOATING_DECAY": 0.1,
    "A_PROTRUSION": 1.0,
}
WEIGHT_LUCK = 0.4
WEIGHT_YEAR = 0.2

SOLAR_TERMS = [
    "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]

DEFAULT_SEASONAL_BASE: Dict[str, Dict[str, float]] = {
    "default": {"wood": 1.0, "fire": 1.0, "earth": 1.0, "metal": 1.0, "water": 1.0},
    "spring": {"wood": 1.2, "fire": 1.05, "earth": 0.95, "metal": 0.85, "water": 0.95},
    "summer": {"wood": 1.0, "fire": 1.2, "earth": 1.05, "metal": 0.85, "water": 0.85},
    "autumn": {"wood": 0.85, "fire": 0.9, "earth": 1.0, "metal": 1.2, "water": 1.05},
    "winter": {"wood": 0.9, "fire": 0.8, "earth": 0.95, "metal": 1.05, "water": 1.2},
}

TERM_TO_SEASON = {
    **{k: "spring" for k in SOLAR_TERMS[0:6]},
    **{k: "summer" for k in SOLAR_TERMS[6:12]},
    **{k: "autumn" for k in SOLAR_TERMS[12:18]},
    **{k: "winter" for k in SOLAR_TERMS[18:24]},
}

STEM_TO_ELEMENT = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 天干阴阳：奇数为阳（甲丙戊庚壬），偶数为阴（乙丁己辛癸）
STEM_YIN_YANG = {
    "甲": "yang",
    "乙": "yin",
    "丙": "yang",
    "丁": "yin",
    "戊": "yang",
    "己": "yin",
    "庚": "yang",
    "辛": "yin",
    "壬": "yang",
    "癸": "yin",
}

# 地支藏干比例（v1 静态表：本气/中气/余气的近似比例，和 SOP 可再校准）
BRANCH_HIDDEN_STEMS: Dict[str, Dict[str, float]] = {
    "子": {"癸": 100.0},
    "丑": {"己": 60.0, "癸": 30.0, "辛": 10.0},
    "寅": {"甲": 60.0, "丙": 30.0, "戊": 10.0},
    "卯": {"乙": 100.0},
    "辰": {"戊": 60.0, "乙": 20.0, "癸": 20.0},
    "巳": {"丙": 60.0, "戊": 20.0, "庚": 20.0},
    "午": {"丁": 80.0, "己": 20.0},
    "未": {"己": 60.0, "丁": 20.0, "乙": 20.0},
    "申": {"庚": 60.0, "壬": 30.0, "戊": 10.0},
    "酉": {"辛": 100.0},
    "戌": {"戊": 60.0, "辛": 20.0, "丁": 20.0},
    "亥": {"壬": 60.0, "甲": 20.0, "戊": 20.0},
}

TEN_DEITIES = [
    "比肩",
    "劫财",
    "食神",
    "伤官",
    "正财",
    "偏财",
    "正官",
    "七杀",
    "正印",
    "偏印",
]

MONTH_BRANCH_TO_SEASON = {
    # 寅卯辰：春；巳午未：夏；申酉戌：秋；亥子丑：冬
    "寅": "spring",
    "卯": "spring",
    "辰": "spring",
    "巳": "summer",
    "午": "summer",
    "未": "summer",
    "申": "autumn",
    "酉": "autumn",
    "戌": "autumn",
    "亥": "winter",
    "子": "winter",
    "丑": "winter",
}


def _stem_polarity(stem: str) -> str:
    return STEM_YIN_YANG.get(stem, "yang")


def _deity_from_self_and_target_stem(*, day_stem: str, target_stem: str) -> str:
    """
    十神映射（v1）：
    - 比肩/劫财：同类
    - 食神/伤官：自生
    - 正财/偏财：自克
    - 正官/七杀：被克
    - 正印/偏印：生我
    正/偏：当“正”=阴阳相反（财官印），输出/同类“正”=阴阳相同（食神/比肩）。
    """
    self_element = STEM_TO_ELEMENT.get(day_stem, "earth")
    target_element = STEM_TO_ELEMENT.get(target_stem, "earth")
    day_pol = _stem_polarity(day_stem)
    tar_pol = _stem_polarity(target_stem)

    if target_element == self_element:
        return "比肩" if tar_pol == day_pol else "劫财"

    # 自生：食伤
    if ELEMENT_GENERATES.get(self_element) == target_element:
        return "食神" if tar_pol == day_pol else "伤官"

    # 自克：财
    if ELEMENT_CONTROLS.get(self_element) == target_element:
        return "偏财" if tar_pol == day_pol else "正财"

    # 被克：官杀（target 克 self）
    if ELEMENT_CONTROLS.get(target_element) == self_element:
        return "七杀" if tar_pol == day_pol else "正官"

    # 生我：印（target 生 self）
    if ELEMENT_GENERATES.get(target_element) == self_element:
        return "偏印" if tar_pol == day_pol else "正印"

    return "比肩"

ELEMENT_GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

ELEMENT_CONTROLS = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}


def _controlled_by(element: str) -> str:
    for src, dst in ELEMENT_CONTROLS.items():
        if dst == element:
            return src
    return "earth"


def _generated_by(element: str) -> str:
    for src, dst in ELEMENT_GENERATES.items():
        if dst == element:
            return src
    return "earth"


def _deity_element_map(self_element: str) -> Dict[str, str]:
    output = ELEMENT_GENERATES[self_element]
    wealth = ELEMENT_CONTROLS[self_element]
    power = _controlled_by(self_element)
    support = _generated_by(self_element)
    return {
        "比劫": self_element,
        "食伤": output,
        "财星": wealth,
        "官杀": power,
        "印星": support,
    }


@dataclass
class PhysicsCache:
    position_weights: Dict[str, float]
    interaction_params: Dict[str, float]
    seasonal_matrix: Dict[str, Dict[str, float]]
    version_id: str = "bootstrap"


class PhysicsSkillOutput(BaseModel):
    vector: Dict[str, float]
    normalized: Dict[str, float]
    deity_scores: Dict[str, float]
    deity_components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    deity_energy_axes: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    deity_trace_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    by_pillar: Dict[str, Dict[str, Any]]
    meta: Dict[str, Any]
    audit_log: AuditLog


def seed_physics_defaults() -> None:
    """若物理参数表为空，则写入默认种子。"""
    with session_scope() as s:
        has_positions = s.exec(select(PhysicsPositionWeight)).first() is not None
        if not has_positions:
            for pillar, weight in DEFAULT_POSITION_WEIGHTS.items():
                s.add(PhysicsPositionWeight(pillar_type=pillar, weight=weight))

        existing_params = {
            p.param_key: p
            for p in s.exec(select(PhysicsInteractionParam)).all()
        }
        for k, v in DEFAULT_INTERACTION_PARAMS.items():
            if k not in existing_params:
                s.add(PhysicsInteractionParam(param_key=k, param_value=v))

        has_terms = s.exec(select(PhysicsSeasonalMatrix)).first() is not None
        if not has_terms:
            for term in SOLAR_TERMS:
                base = DEFAULT_SEASONAL_BASE[TERM_TO_SEASON.get(term, "default")]
                s.add(
                    PhysicsSeasonalMatrix(
                        solar_term=term,
                        element_wood=base["wood"],
                        element_fire=base["fire"],
                        element_earth=base["earth"],
                        element_metal=base["metal"],
                        element_water=base["water"],
                    )
                )


class PhysicsInferenceSkill(BaseSkill):
    _instance: "PhysicsInferenceSkill | None" = None
    _lock = Lock()
    skill_id = "physics_inference_skill"
    skill_version = "1.2.0"

    def __init__(self) -> None:
        self._cache = PhysicsCache(
            position_weights=dict(DEFAULT_POSITION_WEIGHTS),
            interaction_params=dict(DEFAULT_INTERACTION_PARAMS),
            seasonal_matrix={},
            version_id="bootstrap",
        )
        self.refresh_cache()

    @classmethod
    def instance(cls) -> "PhysicsInferenceSkill":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def refresh_cache(self) -> None:
        try:
            with session_scope() as s:
                position_rows = s.exec(select(PhysicsPositionWeight)).all()
                param_rows = s.exec(select(PhysicsInteractionParam)).all()
                term_rows = s.exec(select(PhysicsSeasonalMatrix)).all()
                positions = {p.pillar_type: float(p.weight) for p in position_rows}
                params = {p.param_key: float(p.param_value) for p in param_rows}
                terms = {
                    t.solar_term: {
                        "wood": float(t.element_wood),
                        "fire": float(t.element_fire),
                        "earth": float(t.element_earth),
                        "metal": float(t.element_metal),
                        "water": float(t.element_water),
                    }
                    for t in term_rows
                }
                updated_marks: list[str] = []
                updated_marks.extend(
                    [p.updated_at.isoformat() for p in position_rows if getattr(p, "updated_at", None)]
                )
                updated_marks.extend(
                    [p.updated_at.isoformat() for p in param_rows if getattr(p, "updated_at", None)]
                )
                updated_marks.extend(
                    [p.updated_at.isoformat() for p in term_rows if getattr(p, "updated_at", None)]
                )
                version_id = max(updated_marks) if updated_marks else datetime.utcnow().isoformat()
        except Exception:
            positions = {}
            params = {}
            terms = {}
            version_id = datetime.utcnow().isoformat()

        self._cache.position_weights = positions or dict(DEFAULT_POSITION_WEIGHTS)
        self._cache.interaction_params = params or dict(DEFAULT_INTERACTION_PARAMS)
        self._cache.seasonal_matrix = terms
        self._cache.version_id = version_id

    def refresh_and_recalculate(self) -> None:
        """
        兼容“系统反馈闭环”的语义接口。
        物理引擎的“重算”依赖后续的 `analyze-seed`/`analyze-clash` 请求入参，
        因此这里仅保证缓存/版本号与最新 DB 参数一致（refresh_cache）。
        """
        self.refresh_cache()

    def consume(self, context: Dict[str, Any]) -> Dict[str, Any]:
        metadata = context.get("metadata")
        if metadata is None:
            raise ValueError("physics skill dependency missing: metadata")
        session_id = context.get("session_id")
        consensus_overrides: Dict[str, float] = {}
        hard_route_logs: list[str] = []
        if isinstance(session_id, int) and session_id > 0:
            try:
                with session_scope() as s:
                    rows = s.exec(select(SessionConsensus).where(SessionConsensus.session_id == session_id)).all()
                    for row in rows:
                        key = str(row.decision_key or "").strip()
                        if not key:
                            continue
                        if row.confirmed_value is None:
                            continue
                        val = float(row.confirmed_value)
                        consensus_overrides[key] = val
                for k, v in consensus_overrides.items():
                    hard_route_logs.append(
                        f"[HARD_ROUTE] Param '{k}' overridden by user consensus session#{session_id} => {v:.2f}."
                    )
            except Exception:
                # 不阻断主链路：共识读取失败时回退到缓存参数
                consensus_overrides = {}
                hard_route_logs = []
        return {
            "metadata": metadata,
            "solar_term": context.get("solar_term"),
            "session_id": session_id,
            "dayun": context.get("dayun"),
            "liunian": context.get("liunian"),
            "consensus_overrides": consensus_overrides,
            "hard_route_logs": hard_route_logs,
        }

    def produce(self, consumed: Dict[str, Any]) -> Dict[str, Any]:
        payload = self.infer(
            metadata=consumed["metadata"],
            solar_term=consumed.get("solar_term"),
            dayun=consumed.get("dayun"),
            liunian=consumed.get("liunian"),
            consensus_overrides=consumed.get("consensus_overrides") or {},
            hard_route_logs=consumed.get("hard_route_logs") or [],
        )
        PhysicsSkillOutput.model_validate(payload)
        return payload

    def audit(self, consumed: Dict[str, Any], produced: Dict[str, Any]) -> AuditLog:
        return produced["audit_log"]

    def infer(
        self,
        metadata: BaziMetadata,
        solar_term: str | None = None,
        dayun: str | None = None,
        liunian: str | None = None,
        consensus_overrides: Dict[str, float] | None = None,
        hard_route_logs: list[str] | None = None,
    ) -> Dict[str, Any]:
        if metadata.pillars is None:
            return {"vector": {}, "by_pillar": {}, "meta": {"reason": "pillars_missing"}}

        params = dict(self._cache.interaction_params)
        for k, v in (consensus_overrides or {}).items():
            if k in params:
                params[k] = float(v)
        root_decay = params.get("root_decay_lambda", 0.7)
        stem_boost = params.get("through_stem_boost", 1.05)
        conflict_gamma = params.get("conflict_penalty_gamma", 0.12)
        floating_decay = params.get("CF_FLOATING_DECAY", 0.3)
        protrusion = params.get("A_PROTRUSION", 1.0)
        conflict_count = len(metadata.conflict_matrix.points)
        conflict_factor = max(0.5, 1.0 - conflict_count * conflict_gamma)

        day_stem = metadata.pillars.day.stem
        root_trace, root_decay_factor = self._root_coupling_check(metadata=metadata, floating_decay=floating_decay)
        floating_deities = {"比肩", "劫财"} if bool(root_trace.get("no_root", False)) else set()
        # 季节修正：优先太阳节气（如果传入且存在于表），否则从月令推导季节桶
        if solar_term and solar_term in self._cache.seasonal_matrix:
            seasonal_factor = self._cache.seasonal_matrix.get(solar_term, DEFAULT_SEASONAL_BASE["default"])
        else:
            month_branch = metadata.pillars.month.branch
            derived_season = MONTH_BRANCH_TO_SEASON.get(month_branch, "spring")
            # 若表内有对应季节的节气行，则取均值；否则回退到默认桶
            terms = [t for t, s in TERM_TO_SEASON.items() if s == derived_season]
            if self._cache.seasonal_matrix and terms:
                acc = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
                cnt = 0
                for t in terms:
                    v = self._cache.seasonal_matrix.get(t)
                    if not v:
                        continue
                    for k in acc.keys():
                        acc[k] += float(v.get(k, 1.0))
                    cnt += 1
                seasonal_factor = {k: (acc[k] / cnt if cnt else DEFAULT_SEASONAL_BASE[derived_season][k]) for k in acc.keys()}
            else:
                seasonal_factor = DEFAULT_SEASONAL_BASE[derived_season]

        # 目标输出
        result_by_pillar: Dict[str, Dict[str, float]] = {}
        vector = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
        raw_deity_energy: Dict[str, float] = {k: 0.0 for k in TEN_DEITIES}
        deity_contribution_sources: Dict[str, List[Dict[str, Any]]] = {k: [] for k in TEN_DEITIES}

        for pillar in ("year", "month", "day", "hour"):
            pair = getattr(metadata.pillars, pillar)
            pos_weight = self._cache.position_weights.get(pillar, DEFAULT_POSITION_WEIGHTS[pillar])

            # 可见天干：先作为“骨架能量”
            stem_char = pair.stem
            stem_element = STEM_TO_ELEMENT.get(stem_char, "earth")
            seasonal_el = float(seasonal_factor.get(stem_element, 1.0))
            raw = float(pair.energy_value)
            stem_energy = raw * pos_weight * seasonal_el * stem_boost * root_decay * conflict_factor * protrusion

            vector[stem_element] += stem_energy
            deity_stem = _deity_from_self_and_target_stem(day_stem=day_stem, target_stem=stem_char)
            # 规则：日干本体不参与十神计分（仅作为参照原点）
            if not (pillar == "day" and stem_char == day_stem):
                if deity_stem in floating_deities:
                    stem_energy *= root_decay_factor
                raw_deity_energy[deity_stem] += stem_energy
                deity_contribution_sources[deity_stem].append(
                    {
                        "source": f"{pillar}.stem:{stem_char}",
                        "raw_energy": round(raw, 4),
                        "position_weight": round(pos_weight, 4),
                        "seasonal_factor": round(seasonal_el, 4),
                        "hidden_ratio": 1.0,
                        "contribution_energy": round(stem_energy, 4),
                    }
                )

            # 地支藏干：以“容器拆解”方式展开，并进入同一十神能量合流
            branch_char = pair.branch
            hidden = BRANCH_HIDDEN_STEMS.get(branch_char, {})
            for hidden_stem, ratio in hidden.items():
                hidden_element = STEM_TO_ELEMENT.get(hidden_stem, "earth")
                seasonal_h = float(seasonal_factor.get(hidden_element, 1.0))
                hidden_energy = (
                    raw
                    * (float(ratio) / 100.0)
                    * pos_weight
                    * seasonal_h
                    * stem_boost
                    * root_decay
                    * conflict_factor
                    * protrusion
                )
                vector[hidden_element] += hidden_energy
                deity_hidden = _deity_from_self_and_target_stem(day_stem=day_stem, target_stem=hidden_stem)
                if deity_hidden in floating_deities:
                    hidden_energy *= root_decay_factor
                raw_deity_energy[deity_hidden] += hidden_energy
                deity_contribution_sources[deity_hidden].append(
                    {
                        "source": f"{pillar}.branch:{branch_char}.hidden:{hidden_stem}",
                        "raw_energy": round(raw, 4),
                        "position_weight": round(pos_weight, 4),
                        "seasonal_factor": round(seasonal_h, 4),
                        "hidden_ratio": round(float(ratio) / 100.0, 4),
                        "contribution_energy": round(hidden_energy, 4),
                    }
                )

            result_by_pillar[pillar] = {
                "element": stem_element,
                "raw_energy": raw,
                "weight": pos_weight,
                "seasonal_factor": round(seasonal_el, 4),
                "stem_energy": round(stem_energy, 4),
            }

        # 岁运扰动场：大运(0.4) + 流年(0.2) 注入原始十神能量
        def _inject_disturbance(ganzhi: str | None, weight: float, tag: str) -> None:
            if not ganzhi or len(str(ganzhi)) < 2:
                return
            stem_char = str(ganzhi)[0]
            branch_char = str(ganzhi)[1]
            s_el = STEM_TO_ELEMENT.get(stem_char, "earth")
            s_seasonal = float(seasonal_factor.get(s_el, 1.0))
            s_energy = 100.0 * weight * s_seasonal * stem_boost * root_decay * conflict_factor * protrusion
            s_deity = _deity_from_self_and_target_stem(day_stem=day_stem, target_stem=stem_char)
            if s_deity in floating_deities:
                s_energy *= root_decay_factor
            vector[s_el] += s_energy
            raw_deity_energy[s_deity] += s_energy
            deity_contribution_sources[s_deity].append(
                {
                    "source": f"{tag}.stem:{stem_char}",
                    "raw_energy": 100.0,
                    "position_weight": round(weight, 4),
                    "seasonal_factor": round(s_seasonal, 4),
                    "hidden_ratio": 1.0,
                    "contribution_energy": round(s_energy, 4),
                }
            )
            hidden = BRANCH_HIDDEN_STEMS.get(branch_char, {})
            for hidden_stem, ratio in hidden.items():
                h_el = STEM_TO_ELEMENT.get(hidden_stem, "earth")
                h_seasonal = float(seasonal_factor.get(h_el, 1.0))
                h_energy = (
                    100.0
                    * weight
                    * (float(ratio) / 100.0)
                    * h_seasonal
                    * stem_boost
                    * root_decay
                    * conflict_factor
                    * protrusion
                )
                h_deity = _deity_from_self_and_target_stem(day_stem=day_stem, target_stem=hidden_stem)
                if h_deity in floating_deities:
                    h_energy *= root_decay_factor
                vector[h_el] += h_energy
                raw_deity_energy[h_deity] += h_energy
                deity_contribution_sources[h_deity].append(
                    {
                        "source": f"{tag}.branch:{branch_char}.hidden:{hidden_stem}",
                        "raw_energy": 100.0,
                        "position_weight": round(weight, 4),
                        "seasonal_factor": round(h_seasonal, 4),
                        "hidden_ratio": round(float(ratio) / 100.0, 4),
                        "contribution_energy": round(h_energy, 4),
                    }
                )

        _inject_disturbance(dayun, WEIGHT_LUCK, "luck")
        _inject_disturbance(liunian, WEIGHT_YEAR, "year")

        vector = {k: round(v, 4) for k, v in vector.items()}
        total = sum(vector.values()) or 1.0
        normalized = {k: round(v / total, 4) for k, v in vector.items()}

        deity_scores, deity_components, deity_energy_axes, deity_trace_details = self._calculate_deity_scores(
            metadata=metadata,
            raw_deity_energy=raw_deity_energy,
            interaction_params=params,
            contribution_sources=deity_contribution_sources,
            root_check=root_trace,
        )
        baseline_regression = self._run_baseline_regression(solar_term=solar_term)
        hard_route_keys = sorted((consensus_overrides or {}).keys())
        routed_param_version_id = (
            f"{self._cache.version_id}|hr:{','.join(hard_route_keys)}"
            if hard_route_keys
            else self._cache.version_id
        )
        audit_log = AuditLog(
            skill_id=self.skill_id,
            skill_version=self.skill_version,
            param_version_id=routed_param_version_id,
            formula_refs=[
                "E_self_new = E_self + E_support * (EFF_PROMOTING - 1)",
                "E_self_final = E_self_new * EFF_RESTRAINING * EFF_EXHAUSTING * EFF_CONSUMING",
                "hidden_stem_energy = raw * ratio * position_weight * seasonal * through_stem_boost * root_decay * conflict_factor",
            ],
            param_snapshot={k: float(v) for k, v in params.items() if k.startswith("EFF_") or k.startswith("CF_") or k == "A_PROTRUSION"},
            trace={
                "day_stem": metadata.pillars.day.stem,
                "conflict_count": conflict_count,
                "solar_term": solar_term or "derived_from_month_branch",
                "hard_route_logs": hard_route_logs or [],
                "root_check": root_trace,
                "vector": vector,
                "deity_scores": deity_scores,
                "deity_components": deity_components,
                "deity_energy_axes": deity_energy_axes,
                "deity_trace_details": deity_trace_details,
                "baseline_regression": baseline_regression,
            },
        )
        return {
            "vector": vector,
            "normalized": normalized,
            "deity_scores": deity_scores,
            "deity_components": deity_components,
            "deity_energy_axes": deity_energy_axes,
            "deity_trace_details": deity_trace_details,
            "by_pillar": result_by_pillar,
            "meta": {
                "solar_term": solar_term or "derived_from_month_branch",
                "conflict_count": conflict_count,
                "params": {
                    "root_decay_lambda": root_decay,
                    "through_stem_boost": stem_boost,
                    "conflict_penalty_gamma": conflict_gamma,
                    "CF_FLOATING_DECAY": floating_decay,
                    "A_PROTRUSION": protrusion,
                },
                "root_check": root_trace,
                "root_details": {
                    "by_deity": {
                        k: {
                            "root_sources": v.get("root_sources", []),
                            "is_floating": bool(root_trace.get("no_root", False)),
                        }
                        for k, v in deity_components.items()
                    },
                },
                "hard_route_logs": hard_route_logs or [],
                "deity_trace_details": deity_trace_details,
                "disturbance_weights": {"luck": WEIGHT_LUCK, "year": WEIGHT_YEAR},
                "baseline_regression": baseline_regression,
            },
            "audit_log": audit_log.model_dump(),
        }

    def _root_coupling_check(self, metadata: BaziMetadata, floating_decay: float) -> tuple[Dict[str, Any], float]:
        day_stem = metadata.pillars.day.stem
        day_element = STEM_TO_ELEMENT.get(day_stem, "")
        branches = [
            metadata.pillars.year.branch,
            metadata.pillars.month.branch,
            metadata.pillars.day.branch,
            metadata.pillars.hour.branch,
        ]
        root_map: Dict[str, set[str]] = {
            "甲": {"寅", "卯", "辰", "未", "亥"},
            "乙": {"寅", "卯", "辰", "未"},
            "丙": {"巳", "午", "寅", "未"},
            "丁": {"巳", "午", "未", "戌"},
            "戊": {"辰", "戌", "丑", "未", "巳", "午"},
            "己": {"辰", "戌", "丑", "未", "午"},
            "庚": {"申", "酉", "戌", "丑"},
            "辛": {"申", "酉", "戌", "丑"},
            "壬": {"亥", "子", "申", "辰"},
            "癸": {"亥", "子", "丑", "辰"},
        }
        roots = root_map.get(day_stem, set())
        matched = [b for b in branches if b in roots]
        no_root = len(matched) == 0
        decay_factor = max(0.0, 1.0 - float(floating_decay)) if no_root and day_element == "wood" else 1.0
        record = (
            f"[ROOT_CHECK] Target: {day_stem}木, Result: NULL, Action: CF_FLOATING_DECAY({floating_decay}) applied."
            if no_root and day_stem == "乙"
            else (
                f"[ROOT_CHECK] Target: {day_stem}, Result: NULL, Action: CF_FLOATING_DECAY({floating_decay}) applied."
                if no_root
                else f"[ROOT_CHECK] Target: {day_stem}, Result: ROOT_FOUND({','.join(matched)}), Action: no_decay."
            )
        )
        return {
            "target_stem": day_stem,
            "branches": branches,
            "matched_roots": matched,
            "no_root": no_root,
            "decay_factor": round(decay_factor, 4),
            "record": record,
        }, decay_factor

    def _run_baseline_regression(self, solar_term: str | None) -> Dict[str, Any]:
        baselines = {
            "baseline_1990": BaziMetadata(
                pillars={
                    "year": {"stem": "庚", "branch": "午", "energy_value": 100},
                    "month": {"stem": "壬", "branch": "午", "energy_value": 100},
                    "day": {"stem": "甲", "branch": "子", "energy_value": 100},
                    "hour": {"stem": "乙", "branch": "酉", "energy_value": 100},
                }
            ),
            "baseline_dingsi_yisi": BaziMetadata(
                pillars={
                    "year": {"stem": "丁", "branch": "巳", "energy_value": 100},
                    "month": {"stem": "乙", "branch": "巳", "energy_value": 100},
                    "day": {"stem": "乙", "branch": "酉", "energy_value": 100},
                    "hour": {"stem": "辛", "branch": "丑", "energy_value": 100},
                }
            ),
        }
        output: Dict[str, Any] = {}
        for key, case in baselines.items():
            root_trace, _ = self._root_coupling_check(case, self._cache.interaction_params.get("CF_FLOATING_DECAY", 0.3))
            # 基线仅做轻量一致性巡检，避免递归跑全套 infer。
            output[key] = {
                "root_check": root_trace,
                "solar_term": solar_term or "derived_from_month_branch",
            }
        return output

    def _calculate_deity_scores(
        self,
        metadata: BaziMetadata,
        raw_deity_energy: Dict[str, float],
        interaction_params: Dict[str, float] | None = None,
        contribution_sources: Dict[str, List[Dict[str, Any]]] | None = None,
        root_check: Dict[str, Any] | None = None,
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], Dict[str, Dict[str, float]], Dict[str, Dict[str, Any]]]:
        params = interaction_params or self._cache.interaction_params
        raw_deity_energy = {k: float(raw_deity_energy.get(k, 0.0)) for k in TEN_DEITIES}

        # 十神聚合维度
        raw_self = raw_deity_energy["比肩"] + raw_deity_energy["劫财"]
        raw_output = raw_deity_energy["食神"] + raw_deity_energy["伤官"]
        raw_wealth = raw_deity_energy["正财"] + raw_deity_energy["偏财"]
        raw_power = raw_deity_energy["正官"] + raw_deity_energy["七杀"]
        raw_support = raw_deity_energy["正印"] + raw_deity_energy["偏印"]

        # 同性/异性拆分（由十神正/偏类型间接映射到阴阳同/异）
        support_same = raw_deity_energy["偏印"]
        support_diff = raw_deity_energy["正印"]
        output_same = raw_deity_energy["食神"]
        output_diff = raw_deity_energy["伤官"]
        wealth_same = raw_deity_energy["偏财"]
        wealth_diff = raw_deity_energy["正财"]
        power_same = raw_deity_energy["七杀"]
        power_diff = raw_deity_energy["正官"]

        eff_promoting_same = params.get("EFF_PROMOTING_SAME", params.get("EFF_PROMOTING", 1.0))
        eff_promoting_diff = params.get("EFF_PROMOTING_DIFF", params.get("EFF_PROMOTING", 1.0))
        eff_exhausting_same = params.get("EFF_EXHAUSTING_SAME", params.get("EFF_EXHAUSTING", 1.0))
        eff_exhausting_diff = params.get("EFF_EXHAUSTING_DIFF", params.get("EFF_EXHAUSTING", 1.0))
        eff_restraining_same = params.get("EFF_RESTRAINING_SAME", params.get("EFF_RESTRAINING", 1.0))
        eff_restraining_diff = params.get("EFF_RESTRAINING_DIFF", params.get("EFF_RESTRAINING", 1.0))
        eff_consuming_same = params.get("EFF_CONSUMING_SAME", params.get("EFF_CONSUMING", 1.0))
        eff_consuming_diff = params.get("EFF_CONSUMING_DIFF", params.get("EFF_CONSUMING", 1.0))

        def _weighted_eff(same_energy: float, diff_energy: float, eff_same: float, eff_diff: float, base: float) -> float:
            total = same_energy + diff_energy
            if total <= 0:
                return base
            return (same_energy * eff_same + diff_energy * eff_diff) / total

        eff_promoting = _weighted_eff(
            support_same,
            support_diff,
            eff_promoting_same,
            eff_promoting_diff,
            params.get("EFF_PROMOTING", 1.0),
        )
        eff_exhausting = _weighted_eff(
            output_same,
            output_diff,
            eff_exhausting_same,
            eff_exhausting_diff,
            params.get("EFF_EXHAUSTING", 1.0),
        )
        eff_restraining = _weighted_eff(
            power_same,
            power_diff,
            eff_restraining_same,
            eff_restraining_diff,
            params.get("EFF_RESTRAINING", 1.0),
        )
        eff_consuming = _weighted_eff(
            wealth_same,
            wealth_diff,
            eff_consuming_same,
            eff_consuming_diff,
            params.get("EFF_CONSUMING", 1.0),
        )

        # 物理循环：按你给的“印生身/官杀克身/食伤泄身/财星耗身”顺序
        e_self_new = raw_self + raw_support * (eff_promoting - 1.0)
        e_self_final = e_self_new * eff_restraining * eff_exhausting * eff_consuming

        self_change = max(0.0, raw_self - e_self_final)
        e_output_final = raw_output + self_change * (1.0 - eff_exhausting)
        e_wealth_final = raw_wealth + self_change * (1.0 - eff_consuming)
        e_power_final = raw_power + self_change * (1.0 - eff_restraining)
        e_support_final = raw_support * eff_promoting

        # 归还到 10 个独立十神
        final = {k: 0.0 for k in TEN_DEITIES}
        if raw_self > 0:
            final["比肩"] = e_self_final * (raw_deity_energy["比肩"] / raw_self)
            final["劫财"] = e_self_final * (raw_deity_energy["劫财"] / raw_self)
        if raw_output > 0:
            final["食神"] = e_output_final * (raw_deity_energy["食神"] / raw_output)
            final["伤官"] = e_output_final * (raw_deity_energy["伤官"] / raw_output)
        if raw_wealth > 0:
            final["正财"] = e_wealth_final * (raw_deity_energy["正财"] / raw_wealth)
            final["偏财"] = e_wealth_final * (raw_deity_energy["偏财"] / raw_wealth)
        if raw_power > 0:
            final["正官"] = e_power_final * (raw_deity_energy["正官"] / raw_power)
            final["七杀"] = e_power_final * (raw_deity_energy["七杀"] / raw_power)
        if raw_support > 0:
            final["正印"] = e_support_final * (raw_deity_energy["正印"] / raw_support)
            final["偏印"] = e_support_final * (raw_deity_energy["偏印"] / raw_support)

        total = sum(final.values()) or 1.0
        pct = {k: (Decimal(str(v)) / Decimal(str(total)) * Decimal("100")) for k, v in final.items()}
        quantized = {k: v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for k, v in pct.items()}
        expected = Decimal("100.00")
        diff = expected - sum(quantized.values())
        if diff != Decimal("0.00"):
            anchor = max(quantized.keys(), key=lambda k: quantized[k])
            quantized[anchor] = (quantized[anchor] + diff).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        final_scores = {k: float(v) for k, v in quantized.items()}
        deity_components: Dict[str, Dict[str, Any]] = {}
        deity_energy_axes: Dict[str, Dict[str, float]] = {}
        trace_details: Dict[str, Dict[str, Any]] = {}
        sum_final = sum(final.values()) or 1.0
        intervention_params = {
            "EFF_PROMOTING": round(float(eff_promoting), 4),
            "EFF_EXHAUSTING": round(float(eff_exhausting), 4),
            "EFF_RESTRAINING": round(float(eff_restraining), 4),
            "EFF_CONSUMING": round(float(eff_consuming), 4),
            "EFF_PROMOTING_SAME": round(float(eff_promoting_same), 4),
            "EFF_PROMOTING_DIFF": round(float(eff_promoting_diff), 4),
            "EFF_EXHAUSTING_SAME": round(float(eff_exhausting_same), 4),
            "EFF_EXHAUSTING_DIFF": round(float(eff_exhausting_diff), 4),
            "EFF_RESTRAINING_SAME": round(float(eff_restraining_same), 4),
            "EFF_RESTRAINING_DIFF": round(float(eff_restraining_diff), 4),
            "EFF_CONSUMING_SAME": round(float(eff_consuming_same), 4),
            "EFF_CONSUMING_DIFF": round(float(eff_consuming_diff), 4),
            "CF_FLOATING_DECAY": round(float(params.get("CF_FLOATING_DECAY", 0.0)), 4),
            "A_PROTRUSION": round(float(params.get("A_PROTRUSION", 1.0)), 4),
        }
        for deity in TEN_DEITIES:
            contribution = list((contribution_sources or {}).get(deity, []))
            final_energy = float(final.get(deity, 0.0))
            raw_total = float(raw_deity_energy.get(deity, 0.0))
            raw_stem = sum(float(x.get("contribution_energy", 0.0)) for x in contribution if ".stem:" in str(x.get("source", "")))
            raw_root = max(0.0, raw_total - raw_stem)
            stem_final_energy = (final_energy * raw_stem / raw_total) if raw_total > 0 else 0.0
            root_final_energy = (final_energy * raw_root / raw_total) if raw_total > 0 else 0.0
            stem_score = round((stem_final_energy / sum_final) * 100.0, 2) if sum_final > 0 else 0.0
            root_score = round((root_final_energy / sum_final) * 100.0, 2) if sum_final > 0 else 0.0
            total_score = round(float(final_scores.get(deity, 0.0)), 2)
            # 保证 total_score = stem_score + root_score（四舍五入后锚定）
            root_score = round(total_score - stem_score, 2)
            root_sources = sorted({
                f"{src.split('.branch:', 1)[0]}_branch"
                for src in [str(x.get("source", "")) for x in contribution]
                if ".branch:" in src
            })
            stem_sources = sorted({
                f"{src.split('.stem:', 1)[0]}_stem"
                for src in [str(x.get("source", "")) for x in contribution]
                if ".stem:" in src
            })
            deity_components[deity] = {
                "total_score": total_score,
                "stem_score": stem_score,
                "root_score": root_score,
                "root_sources": root_sources,
                "stem_sources": stem_sources,
                "is_floating": bool((root_check or {}).get("no_root", False)),
            }
            deity_energy_axes[deity] = {
                "absolute_energy": round(final_energy, 4),
                "relative_percentage": total_score,
            }
            trace_details[deity] = {
                "base_energy": {
                    "raw_deity_energy": round(float(raw_deity_energy.get(deity, 0.0)), 4),
                    "contribution_sources": contribution,
                },
                "root_strength": deity_components[deity],
                "interventions": {
                    "applied_params": intervention_params,
                    "self_pipeline": {
                        "raw_self": round(raw_self, 4),
                        "e_self_new": round(e_self_new, 4),
                        "e_self_final": round(e_self_final, 4),
                        "self_change": round(self_change, 4),
                    },
                },
                "normalization": {
                    "final_energy_before_pct": round(final_energy, 4),
                    "all_deities_final_energy_sum": round(sum_final, 4),
                    "final_percent": round(final_scores.get(deity, 0.0), 2),
                    "formula": f"{round(final_energy, 4)} / {round(sum_final, 4)} * 100",
                },
            }
        return final_scores, deity_components, deity_energy_axes, trace_details
