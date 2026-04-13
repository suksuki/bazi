"""PhysicsInferenceSkill: 物理参数读取、缓存与能量张量推断。

神煞（symbolic stars）不在本模块计算；展示层标签由 interpretation_helper 在终判 LLM 前注入 metadata。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Dict

from pydantic import BaseModel, Field
from sqlmodel import select

from app.db.models import PhysicsInteractionParam, PhysicsPositionWeight, PhysicsSeasonalMatrix
from app.db.session import session_scope
from app.services.helpers.session_consensus_query import fetch_latest_session_consensus_rows
from app.core.bazi.engine import ensure_l0_for_physics
from app.core.config.physics_settings import resolve_physics_settings
from app.schemas.bazi_metadata import BaziMetadata
from app.skills.base import AuditLog, BaseSkill
from app.skills.climate_inference import ClimateInferenceSkill
from app.plugins.classical.climate_adjuster_v1 import apply_climate_manifest_to_meta
from app.logic.physics.branch_interactions import build_branch_interactions
from app.plugins.classical.conflict_auditor_v1 import compute_conflict_topology_v1, merge_conflict_topology_into_meta
from app.skills.physics_calculations import (
    apply_climate_correction,
    build_energy_fields,
    calculate_deity_scores,
    normalize_element_vector,
    root_coupling_check,
)
from app.skills.physics_rules import (
    DEFAULT_INTERACTION_PARAMS,
    DEFAULT_POSITION_WEIGHTS,
    DEFAULT_SEASONAL_BASE,
    SOLAR_TERMS,
    TERM_TO_SEASON,
)


@dataclass
class PhysicsCache:
    position_weights: Dict[str, float]
    interaction_params: Dict[str, float]
    seasonal_matrix: Dict[str, Dict[str, float]]
    version_id: str = "bootstrap"


class PhysicsSkillOutput(BaseModel):
    vector: Dict[str, float]
    normalized: Dict[str, float]
    confidence: float
    evidence: list[str] = Field(default_factory=list)
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
    rule_version = "physics_rules.v1"

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
        merged_params = dict(DEFAULT_INTERACTION_PARAMS)
        merged_params.update(params)
        self._cache.interaction_params = merged_params
        self._cache.seasonal_matrix = terms
        self._cache.version_id = version_id

    def get_interaction_params(self) -> Dict[str, float]:
        """供 L1 流水线读取当前 DB/默认融合后的交互参数字典。"""
        return dict(self._cache.interaction_params)

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
                    for item in fetch_latest_session_consensus_rows(s, int(session_id)):
                        key = str(item.get("decision_key") or "").strip()
                        if not key:
                            continue
                        raw_v = item.get("confirmed_value")
                        if raw_v is None:
                            continue
                        consensus_overrides[key] = float(raw_v)
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
            "physics_config": context.get("physics_config") or {},
            "consensus_overrides": consensus_overrides,
            "hard_route_logs": hard_route_logs,
        }

    def produce(self, consumed: Dict[str, Any]) -> Dict[str, Any]:
        payload = self.infer(
            metadata=consumed["metadata"],
            solar_term=consumed.get("solar_term"),
            dayun=consumed.get("dayun"),
            liunian=consumed.get("liunian"),
            physics_config=consumed.get("physics_config") or {},
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
        physics_config: Dict[str, Any] | None = None,
        consensus_overrides: Dict[str, float] | None = None,
        hard_route_logs: list[str] | None = None,
    ) -> Dict[str, Any]:
        if metadata.pillars is None:
            return {"vector": {}, "by_pillar": {}, "meta": {"reason": "pillars_missing"}}

        ensure_l0_for_physics()
        params = dict(self._cache.interaction_params)
        runtime_settings = resolve_physics_settings(physics_config)
        for k, v in (consensus_overrides or {}).items():
            if k in params:
                params[k] = float(v)
        root_decay = params.get("root_decay_lambda", 0.7)
        stem_boost = params.get("through_stem_boost", 1.05)
        floating_decay = params.get("CF_FLOATING_DECAY", 0.3)
        protrusion = params.get("A_PROTRUSION", 1.0)
        conflict_count = len(metadata.conflict_matrix.points)

        day_stem = metadata.pillars.day.stem
        root_trace, root_decay_factor = root_coupling_check(metadata=metadata, floating_decay=floating_decay)
        floating_deities = {"比肩", "劫财"} if bool(root_trace.get("no_root", False)) else set()
        climate_meta_block: Dict[str, Any] = {}
        md_dump = metadata.model_dump(mode="json")
        branch_ix = build_branch_interactions(md_dump)
        climate_meta_block["branch_interactions"] = branch_ix
        topology = compute_conflict_topology_v1(
            md_dump, physics_config=runtime_settings, branch_interactions=branch_ix
        )
        conflict_factor = float(topology.get("aggregate_conflict_linear_factor") or 1.0)
        raw_el = topology.get("element_conflict_mods")
        if isinstance(raw_el, dict):
            conflict_element_mods = {
                k: float(raw_el.get(k, 1.0) or 1.0) for k in ("wood", "fire", "earth", "metal", "water")
            }
        else:
            conflict_element_mods = {k: 1.0 for k in ("wood", "fire", "earth", "metal", "water")}
        merge_conflict_topology_into_meta(climate_meta_block, topology)
        apply_climate_manifest_to_meta(climate_meta_block, md_dump)
        climate_mods = {
            k: float(climate_meta_block["climate_field_correction_v1"]["element_mods"][k])
            for k in ("wood", "fire", "earth", "metal", "water")
        }
        result_by_pillar, vector, raw_deity_energy, deity_contribution_sources = build_energy_fields(
            metadata=metadata,
            position_weights=self._cache.position_weights,
            climate_mods=climate_mods,
            day_stem=day_stem,
            stem_boost=stem_boost,
            root_decay=root_decay,
            conflict_factor=conflict_factor,
            protrusion=protrusion,
            floating_deities=floating_deities,
            root_decay_factor=root_decay_factor,
            dayun=dayun,
            liunian=liunian,
            weight_luck=runtime_settings["WEIGHT_LUCK"],
            weight_year=runtime_settings["WEIGHT_YEAR"],
            runtime_physics=runtime_settings,
            conflict_element_mods=conflict_element_mods,
        )
        neutral_mods = {k: 1.0 for k in ("wood", "fire", "earth", "metal", "water")}
        _, vector_pre_manifest, _, _ = build_energy_fields(
            metadata=metadata,
            position_weights=self._cache.position_weights,
            climate_mods=neutral_mods,
            day_stem=day_stem,
            stem_boost=stem_boost,
            root_decay=root_decay,
            conflict_factor=conflict_factor,
            protrusion=protrusion,
            floating_deities=floating_deities,
            root_decay_factor=root_decay_factor,
            dayun=dayun,
            liunian=liunian,
            weight_luck=runtime_settings["WEIGHT_LUCK"],
            weight_year=runtime_settings["WEIGHT_YEAR"],
            runtime_physics=runtime_settings,
            conflict_element_mods=conflict_element_mods,
        )
        climate_meta_block["climate_manifest_field_compare_v1"] = {
            "normalized_pre_manifest": normalize_element_vector(vector_pre_manifest),
            "normalized_post_manifest_pre_hard_climate": normalize_element_vector(dict(vector)),
        }
        pre_climate_vector = {k: float(v) for k, v in vector.items()}
        pre_climate_deity_energy = {k: float(v) for k, v in raw_deity_energy.items()}
        vector, raw_deity_energy, climate_trace = apply_climate_correction(
            metadata=metadata,
            vector=vector,
            raw_deity_energy=raw_deity_energy,
            deity_contribution_sources=deity_contribution_sources,
            climate_enabled=bool(runtime_settings.get("ENABLE_CLIMATE_HARD_FACTOR", 1.0)),
            climate_factors=ClimateInferenceSkill.infer(
                metadata=metadata,
                climate_intensity=float(runtime_settings.get("CLIMATE_INTENSITY", 1.0)),
            ).get("factors", {}),
        )
        climate_trace["vector_before"] = pre_climate_vector
        climate_trace["vector_after"] = {k: float(v) for k, v in vector.items()}
        climate_trace["deity_before"] = pre_climate_deity_energy
        climate_trace["deity_after"] = {k: float(v) for k, v in raw_deity_energy.items()}

        vector = {k: round(v, 4) for k, v in vector.items()}
        total = sum(vector.values()) or 1.0
        normalized = {k: round(v / total, 4) for k, v in vector.items()}

        deity_scores, deity_components, deity_energy_axes, deity_trace_details = calculate_deity_scores(
            raw_deity_energy=raw_deity_energy,
            interaction_params=params,
            contribution_sources=deity_contribution_sources,
            root_check=root_trace,
        )
        evidence = [
            f"solar_term={solar_term or 'derived_from_month_branch'}",
            f"conflict_count={conflict_count}",
            f"conflict_topology.aggregate={topology.get('aggregate_conflict_linear_factor')}",
            f"conflict_topology.element_mods={conflict_element_mods}",
            f"root.no_root={bool(root_trace.get('no_root', False))}",
            f"param_version={self._cache.version_id}",
            f"climate.enabled={bool(climate_trace.get('enabled', False))}",
            f"climate.factors={climate_trace.get('factors', {})}",
        ]
        confidence = 0.92
        if conflict_count >= 3:
            confidence -= 0.1
        elif conflict_count >= 1:
            confidence -= 0.05
        if bool(root_trace.get("no_root", False)):
            confidence -= 0.05
        confidence = round(max(0.5, min(0.99, confidence)), 2)
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
            rule_version=self.rule_version,
            param_version_id=routed_param_version_id,
            formula_refs=[
                "E_self_new = E_self + E_support * (EFF_PROMOTING - 1)",
                "E_self_final = E_self_new * EFF_RESTRAINING * EFF_EXHAUSTING * EFF_CONSUMING",
                "hidden_stem_energy = raw * ratio * ... * conflict_factor * conflict_element_mods[element]",
            ],
            param_snapshot={
                k: float(v)
                for k, v in params.items()
                if k.startswith("EFF_")
                or k.startswith("CF_")
                or k.startswith("OFFICER_")
                or k.startswith("POWER_")
                or k == "A_PROTRUSION"
            },
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
                "runtime_physics_config": runtime_settings,
                "climate_adjustment": climate_trace,
            },
        )
        return {
            "vector": vector,
            "normalized": normalized,
            "confidence": confidence,
            "evidence": evidence,
            "deity_scores": deity_scores,
            "deity_components": deity_components,
            "deity_energy_axes": deity_energy_axes,
            "deity_trace_details": deity_trace_details,
            "by_pillar": result_by_pillar,
            "meta": {
                **climate_meta_block,
                "solar_term": solar_term or "derived_from_month_branch",
                "conflict_count": conflict_count,
                "params": {
                    "root_decay_lambda": root_decay,
                    "through_stem_boost": stem_boost,
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
                "disturbance_weights": {
                    "luck": runtime_settings["WEIGHT_LUCK"],
                    "year": runtime_settings["WEIGHT_YEAR"],
                },
                "baseline_regression": baseline_regression,
                "runtime_physics_config": runtime_settings,
                "climate_adjustment": climate_trace,
            },
            "audit_log": audit_log.model_dump(),
        }

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
            root_trace, _ = root_coupling_check(case, self._cache.interaction_params.get("CF_FLOATING_DECAY", 0.3))
            # 基线仅做轻量一致性巡检，避免递归跑全套 infer。
            output[key] = {
                "root_check": root_trace,
                "solar_term": solar_term or "derived_from_month_branch",
            }
        return output
