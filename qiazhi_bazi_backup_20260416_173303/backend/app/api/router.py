"""API：健康检查、示例 BaziMetadata、LLM、决策链写入。"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from app.core.v12_error_protocol import build_v12_error

from app.api.admin_auth import admin_token_guard
from app.api.contracts import (
    AssertionFrameBacktraceRequest,
    AnalyzeClashRequest,
    AnalyzeSeedRequest,
    ArbitrationOverruleRequest,
    AuditPhysicsWithLlmRequest,
    BlindSchoolFeatureFlags,
    ChatRequest,
    ConfirmStructureRequest,
    ConsultationCreate,
    DecisionRollbackRequest,
    DecisionStepCreate,
    EvolutionAdmissionRequest,
    EvolutionBatchRunRequest,
    FinalVerdictRequest,
    HotReloadPhysicsRequest,
    OrchestratorInternalLoopRequest,
    PhysicsSettingsPersistRequest,
    ResumeCalculationRequest,
    RealtimeNarratorRequest,
    ResolveConflictRequest,
    SkillFeedbackRequest,
    StressTestRequest,
    StandardSeedRequest,
    TranslateRequest,
)
from app.api.router_helpers import now_iso
from sqlmodel import select
from sqlalchemy import desc, func
from app.db.session import session_scope
from app.schemas.bazi_metadata import (
    BaziMetadata,
    ConflictMatrix,
    ConflictPoint,
    FlowState,
    FourPillars,
    StemBranchPair,
)
from app.services.analysis_service import (
    analyze_clash_flow,
    analyze_seed_flow,
    generate_final_verdict,
    hot_reload_physics_context,
    iter_analyze_seed_ndjson,
    iter_final_verdict_ndjson,
    run_stress_test,
    resolve_consensus_history,
    translate_text_items,
)
from app.core.errors import V12SchemaViolationError
from app.logic.brain.decision_hub import (
    DecisionEvolutionFrameProtocol,
    apply_arbitration_overrule_to_client_bundle,
    persist_arbitration_log_to_snapshot,
)
from app.logic.brain.seeds import SEED_SHORT_CODE_MAP
from app.db.learning_ledger import ArbiterPreferenceLedger
from app.db.models import BrainDissentLedger, BrainHtnSnapshot, ResumePulseHistory
from app.services.orchestrator_service import OrchestratorService, run_full_cycle
from app.core.evolution.combination_space import TOTAL_BAZI_COMBINATION_SPACE
from app.core.evolution.dna_registry import (
    gene_maturity_heatmap,
    is_evolution_admitted_to_mainnet,
    load_rule_genes,
    set_evolution_admission,
)
from app.core.evolution.worker import EvolutionaryBatchRunner
from app.core.plugins.registry import PluginRegistry
from app.services.decision_service import resolve_conflict
from app.services.evolution_feedback_service import append_skill_feedback
from app.services.audit_service import audit_physics_with_llm_flow
from app.services.consultation_service import (
    confirm_structure_for_consultation,
    create_consultation_record,
    create_decision_step_record,
    list_history_items,
    rollback_decision_step_record,
)
from app.services.narrative.realtime_narrator import compose_realtime_narration
from app.services.llm_service import run_chat_completion, stream_chat_events
from app.services.recommendation_service import get_top_recommendations
from app.core.physics.settings_manager import list_physics_registry_rows, persist_physics_registry_updates_from_body

router = APIRouter(tags=["qiazhi-bazi"])
_LOG = logging.getLogger(__name__)


def require_db_initialized(request: Request) -> None:
    """init_db 失败时禁止写库，避免裸 500；与 GET /ready 对齐。"""
    if not getattr(request.app.state, "db_init_ok", False):
        err = build_v12_error(
            code="DB_ENV_PATH_NOT_READY",
            user_message="数据库未就绪：当前环境的数据库路径不可达。",
            diagnosis=str(getattr(request.app.state, "db_init_error", "") or ""),
            hints=[
                "检查 DATABASE_URL 主机是否为当前运行环境可达地址（容器内请避免 127.0.0.1 指向误解）。",
                "可先访问 GET /ready，查看 checks.db_init.error 详情。",
            ],
        )
        raise HTTPException(
            status_code=503,
            detail=err,
        )


@router.get("/demo/metadata")
def demo_metadata() -> BaziMetadata:
    """返回一份占位 BaziMetadata，供前端联调。"""
    return BaziMetadata(
        pillars=FourPillars(
            year=StemBranchPair(stem="甲", branch="子"),
            month=StemBranchPair(stem="丙", branch="寅"),
            day=StemBranchPair(stem="戊", branch="午"),
            hour=StemBranchPair(stem="庚", branch="申"),
        ),
        conflict_matrix=ConflictMatrix(
            points=[
                ConflictPoint(kind="clash", positions=["month_branch", "hour_branch"], detail="寅申冲（示例）"),
            ]
        ),
        flow_state=FlowState.UNKNOWN,
        notes="demo",
    )


@router.post("/consultations", response_model=dict, dependencies=[Depends(require_db_initialized)])
def create_consultation(body: ConsultationCreate) -> dict:
    try:
        with session_scope() as s:
            return create_consultation_record(s, body)
    except SQLAlchemyError:
        _LOG.exception("create_consultation: database error")
        err = build_v12_error(
            code="DB_WRITE_PATH_FAILED",
            user_message="数据库写入失败：更可能是环境路径/连通性问题，不是前端参数问题。",
            hints=[
                "确认 PostgreSQL 已监听且应用所在环境可达。",
                "确认 consultation 表已创建并迁移完成。",
            ],
        )
        raise HTTPException(
            status_code=503,
            detail=err,
        ) from None


@router.post("/confirm-structure", response_model=dict)
def confirm_structure(body: ConfirmStructureRequest) -> dict:
    """
    L2 会把“格局认领”结果写进当前 consultation 的 input_meta，
    从而在后续 decision_step 的写入链路里复用（避免改数据库 schema）。
    """
    with session_scope() as s:
        try:
            return confirm_structure_for_consultation(s, body)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/decision-steps", response_model=dict)
def create_decision_step(body: DecisionStepCreate) -> dict:
    with session_scope() as s:
        try:
            return create_decision_step_record(s, body)
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/decision-steps/rollback", response_model=dict)
def rollback_decision_step(body: DecisionRollbackRequest) -> dict:
    with session_scope() as s:
        try:
            return rollback_decision_step_record(s, body)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc




@router.post("/llm/chat")
async def llm_chat(body: ChatRequest) -> dict:
    try:
        return await run_chat_completion(body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.post("/llm/stream")
async def llm_stream(body: ChatRequest):
    return StreamingResponse(stream_chat_events(body), media_type="text/event-stream")


@router.get("/history")
def history() -> dict:
    with session_scope() as s:
        return list_history_items(s, now_iso())


@router.post("/i18n/translate", response_model=dict)
async def i18n_translate(body: TranslateRequest) -> dict:
    return await translate_text_items(body)


@router.post("/v1/analyze_clash", response_model=dict)
async def analyze_clash(body: AnalyzeClashRequest) -> dict:
    return await analyze_clash_flow(body)


@router.post("/v1/hot-reload-physics", response_model=dict)
async def hot_reload_physics_v14(body: HotReloadPhysicsRequest) -> dict:
    """V14：参数/插件变更后重跑物理合成（等同 analyze_clash 全栈），并合并会话态 metadata。"""
    return await hot_reload_physics_context(body)


@router.post("/v1/orchestrator/internal-loop", response_model=dict)
async def orchestrator_internal_loop(body: OrchestratorInternalLoopRequest) -> dict:
    """
    Inbox 勾选等触发的静默物理重算：仅 Orchestrator 内部环，不调 LLM。
    返回 metadata（含 verdict_skeleton）、physics_tensor、VF 摘要等。
    """
    blind_flags = (
        body.blind_school_features.model_dump()
        if body.blind_school_features
        else BlindSchoolFeatureFlags().model_dump()
    )
    physics_cfg = body.physics_config.model_dump(exclude_none=True) if body.physics_config else {}
    sp = body.structural_preview.model_dump(exclude_none=True) if body.structural_preview else None
    out = OrchestratorService.run_internal_loop(
        metadata_obj=body.metadata,
        enabled_plugins=list(body.enabled_plugins or []),
        blind_school_features=blind_flags,
        physics_config=physics_cfg,
        session_id=body.session_id,
        dayun=body.dayun,
        liunian=body.liunian,
        is_preview=bool(body.is_preview),
        structural_preview=sp,
    )
    md = out["metadata"]
    ret: dict = {
        "metadata": md.model_dump(),
        "physics_tensor": out["physics_tensor"],
        "plugin_outputs": out.get("plugin_outputs") or {},
        "semantic_label_bundle_v1": out.get("semantic_label_bundle_v1") or {},
        "verified_fact_lines": out.get("verified_fact_lines") or [],
        "verdict_skeleton": out.get("verdict_skeleton") or "",
        "requires_narrative_refresh": bool(out.get("requires_narrative_refresh")),
        "pre_injection_deity_display": out.get("pre_injection_deity_display") or {},
        "is_preview": bool(body.is_preview),
        "active_probing": out.get("active_probing") or {},
        "interrupt_request": out.get("interrupt_request") or {},
    }
    if body.is_preview:
        ret["preview_pattern_alert"] = str(out.get("preview_pattern_alert") or "")
        _pam = out.get("preview_pattern_alert_meta")
        if isinstance(_pam, dict) and _pam:
            ret["preview_pattern_alert_meta"] = _pam
    return ret


@router.post("/v1/orchestrator/full-cycle/stream")
async def orchestrator_full_cycle_stream(body: OrchestratorInternalLoopRequest):
    """
    中枢全链路 SSE：physics_update / vf_discovered / audit_pulse 增量，末帧 `complete` 与 POST internal-loop JSON 同构。
    """
    blind_flags = (
        body.blind_school_features.model_dump()
        if body.blind_school_features
        else BlindSchoolFeatureFlags().model_dump()
    )
    physics_cfg = body.physics_config.model_dump(exclude_none=True) if body.physics_config else {}
    sp = body.structural_preview.model_dump(exclude_none=True) if body.structural_preview else None

    async def event_gen():
        async for item in run_full_cycle(
            metadata_obj=body.metadata,
            enabled_plugins=list(body.enabled_plugins or []),
            blind_school_features=blind_flags,
            physics_config=physics_cfg,
            session_id=body.session_id,
            dayun=body.dayun,
            liunian=body.liunian,
            is_preview=bool(body.is_preview),
            structural_preview=sp,
        ):
            ev = str(item.get("event") or "message")
            raw = item.get("data")
            data_obj: Any = raw if isinstance(raw, dict) else {}
            yield f"event: {ev}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post("/v1/orchestrator/resume", response_model=dict, dependencies=[Depends(require_db_initialized)])
async def orchestrator_resume(body: ResumeCalculationRequest) -> dict:
    """中断恢复事务流：先落库确认，再从断点局部重算。"""
    blind_flags = (
        body.blind_school_features.model_dump()
        if body.blind_school_features
        else BlindSchoolFeatureFlags().model_dump()
    )
    physics_cfg = body.physics_config.model_dump(exclude_none=True) if body.physics_config else {}
    try:
        return OrchestratorService.resume_calculation(
            session_id=body.session_id,
            user_feedback=dict(body.user_feedback or {}),
            metadata=body.metadata,
            enabled_plugins=list(body.enabled_plugins or []),
            blind_school_features=blind_flags,
            physics_config=physics_cfg,
            dayun=body.dayun,
            liunian=body.liunian,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SQLAlchemyError:
        _LOG.exception("orchestrator_resume: database error")
        err = build_v12_error(
            code="DB_RESUME_TX_FAILED",
            user_message="中断恢复事务提交失败，请先检查数据库连通性。",
            hints=["确认 consultation 可写。", "确认会话未被其他异常事务占用。"],
        )
        raise HTTPException(status_code=503, detail=err) from None


@router.post("/v1/analyze-seed", response_model=dict)
async def analyze_seed(body: StandardSeedRequest, request: Request) -> dict:
    """
    输入生日（日期+时刻） -> 基础排盘 -> 冲合扫描 -> 首轮引导文案。
    """
    from app.services.bazi_engine import get_bazi, get_timeline_snapshot
    req_id = (
        str(request.headers.get("x-request-id") or "").strip()
        or str(getattr(body, "request_id", "") or "").strip()
        or str(uuid.uuid4())
    )
    body.request_id = req_id

    flow_hint = str(body.flow_state or "").strip().lower()
    if flow_hint in {"idle", "synthesis"}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ANALYZE_SEED_FLOW_STATE_CONFLICT",
                "message": f"flow_state={flow_hint} 不允许进入 analyze-seed。",
                "expected": {"flow_state": "probe_waiting"},
            },
        )
    raw_seed = str(body.seed_short or "").strip()
    if raw_seed:
        short_values = {str(v).strip() for v in SEED_SHORT_CODE_MAP.values()}
        legacy_values = set(SEED_SHORT_CODE_MAP.keys())
        if raw_seed in legacy_values:
            body.seed_short = str(SEED_SHORT_CODE_MAP.get(raw_seed) or "")
        elif raw_seed not in short_values:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ANALYZE_SEED_INVALID_SHORT_CODE",
                    "message": f"seed_short={raw_seed} 非法。",
                    "expected": {"seed_short": sorted(short_values)},
                },
            )
    if isinstance(body.user_feedback, str):
        body.user_feedback = body.user_feedback[:300]
    try:
        return await analyze_seed_flow(body, get_bazi, get_timeline_snapshot, now_iso())
    except V12SchemaViolationError as exc:
        err = build_v12_error(
            code="V12_SCHEMA_VIOLATION_ERROR",
            user_message="analyze-seed 触发 V12 结构锁，请修复节点链后重试。",
            diagnosis=str(exc),
            hints=["检查 AssertionTree 是否完整。", "检查首观 Node_Chain_Execution 是否产出节点。"],
            extra={"pulse_id": exc.pulse_id},
        )
        raise HTTPException(status_code=422, detail=err) from exc
    except ValueError as e:
        _LOG.warning(
            "analyze_seed bad request request_id=%s: %s | body=%s",
            req_id,
            str(e),
            body.model_dump(exclude_none=True),
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ANALYZE_SEED_INVALID_INPUT",
                "message": str(e),
                "expected": {"date": "YYYY-MM-DD", "time": "HH:MM"},
            },
        ) from e


@router.post("/v1/analyze-seed/stream")
async def analyze_seed_stream(body: StandardSeedRequest, request: Request) -> StreamingResponse:
    """V13.05：与 ``/v1/analyze-seed`` 同参同语义，以 NDJSON 推送计算阶段心跳。"""
    from app.services.bazi_engine import get_bazi, get_timeline_snapshot

    req_id = (
        str(request.headers.get("x-request-id") or "").strip()
        or str(getattr(body, "request_id", "") or "").strip()
        or str(uuid.uuid4())
    )
    body.request_id = req_id

    flow_hint = str(body.flow_state or "").strip().lower()
    if flow_hint in {"idle", "synthesis"}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ANALYZE_SEED_FLOW_STATE_CONFLICT",
                "message": f"flow_state={flow_hint} 不允许进入 analyze-seed。",
                "expected": {"flow_state": "probe_waiting"},
            },
        )
    raw_seed = str(body.seed_short or "").strip()
    if raw_seed:
        short_values = {str(v).strip() for v in SEED_SHORT_CODE_MAP.values()}
        legacy_values = set(SEED_SHORT_CODE_MAP.keys())
        if raw_seed in legacy_values:
            body.seed_short = str(SEED_SHORT_CODE_MAP.get(raw_seed) or "")
        elif raw_seed not in short_values:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ANALYZE_SEED_INVALID_SHORT_CODE",
                    "message": f"seed_short={raw_seed} 非法。",
                    "expected": {"seed_short": sorted(short_values)},
                },
            )
    if isinstance(body.user_feedback, str):
        body.user_feedback = body.user_feedback[:300]

    async def gen():
        async for chunk in iter_analyze_seed_ndjson(body, get_bazi, get_timeline_snapshot, now_iso()):
            yield chunk

    return StreamingResponse(
        gen(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/v1/brain/m5-gold-stats", response_model=dict)
def m5_gold_stats() -> dict:
    fallback = {
        "ok": True,
        "degraded": True,
        "gold_total": 0,
        "current_entropy_reduction": 0.12,
        "seed_hit_distribution": {},
        "top3_assimilated_seeds": [],
        "recent_sync_time": now_iso(),
        "updated_at": now_iso(),
        "silent_arbiter_audit_events": 0,
        "silent_arbiter_overrule_events": 0,
        "auto_arbitration_success_rate": None,
        "arbitration_user_overrule_rate": None,
        "logic_school_axis_distribution_v1306": {},
        "authority_scope_peak_distribution_v1306": {},
    }
    try:
        with session_scope() as s:
            gold_rows = s.exec(
                select(ArbiterPreferenceLedger).where(ArbiterPreferenceLedger.preference_tier == "GOLD")
            ).all()
            snapshots = s.exec(select(BrainHtnSnapshot)).all()
    except Exception:
        _LOG.warning("m5_gold_stats degraded: db unavailable or schema not ready", exc_info=True)
        return fallback
    by_snapshot = {int(r.snapshot_id): r for r in gold_rows if r.snapshot_id is not None}
    seed_hits: Dict[str, int] = {}
    latest_entropy = 0.12
    latest_ts = ""
    for snap in snapshots:
        sid = int(getattr(snap, "id", 0) or 0)
        if sid not in by_snapshot:
            continue
        for code in list(getattr(snap, "seeds_matched", []) or []):
            key = str(code or "").strip()
            if not key:
                continue
            seed_hits[key] = int(seed_hits.get(key, 0)) + 1
        ts = str(getattr(snap, "created_at", "") or "")
        if ts and ts >= latest_ts:
            latest_ts = ts
            payload = getattr(snap, "snapshot_payload", {}) if isinstance(getattr(snap, "snapshot_payload", {}), dict) else {}
            bh = payload.get("brain_hub") if isinstance(payload.get("brain_hub"), dict) else {}
            ent = bh.get("entropy_reduction")
            if isinstance(ent, (int, float)):
                latest_entropy = float(ent)
    top3 = sorted(seed_hits.items(), key=lambda x: (-int(x[1]), str(x[0])))[:3]
    n_audit = 0
    n_over = 0
    for snap in snapshots:
        raw_logs = getattr(snap, "arbitration_logs", None)
        logs = list(raw_logs) if isinstance(raw_logs, list) else []
        for log in logs:
            if not isinstance(log, dict):
                continue
            proto = str(log.get("protocol") or "")
            if proto == "arbitration_audit.v1":
                n_audit += 1
            elif proto == "arbitration_overrule.v1":
                n_over += 1
    succ_rate: Optional[float] = None
    over_rate: Optional[float] = None
    if n_audit > 0:
        succ_rate = round(max(0, n_audit - n_over) / n_audit, 4)
        over_rate = round(n_over / n_audit, 4)
    school_axis_counts: Dict[str, int] = {}
    authority_peak_counts: Dict[str, int] = {}
    for r in gold_rows:
        ax = str(getattr(r, "logic_school_axis", "") or "").strip() or "UNKNOWN"
        school_axis_counts[ax] = int(school_axis_counts.get(ax, 0)) + 1
        pk = getattr(r, "authority_scope_peak", None)
        pk_key = str(int(pk)) if isinstance(pk, (int, float)) and not isinstance(pk, bool) else "none"
        authority_peak_counts[pk_key] = int(authority_peak_counts.get(pk_key, 0)) + 1
    return {
        "ok": True,
        "degraded": False,
        "gold_total": len(gold_rows),
        "current_entropy_reduction": round(float(latest_entropy), 4),
        "seed_hit_distribution": seed_hits,
        "top3_assimilated_seeds": [str(k) for k, _ in top3],
        "recent_sync_time": latest_ts or now_iso(),
        "updated_at": latest_ts or now_iso(),
        "silent_arbiter_audit_events": n_audit,
        "silent_arbiter_overrule_events": n_over,
        "auto_arbitration_success_rate": succ_rate,
        "arbitration_user_overrule_rate": over_rate,
        "logic_school_axis_distribution_v1306": school_axis_counts,
        "authority_scope_peak_distribution_v1306": authority_peak_counts,
    }


@router.post("/v1/brain/arbitration-overrule", response_model=dict)
def arbitration_overrule(body: ArbitrationOverruleRequest) -> dict:
    """撤销静默 LAW、回滚 flow_state，并恢复 persistence_layer.interrupt_request（pending）。"""
    try:
        patch = apply_arbitration_overrule_to_client_bundle(
            audit_id=body.audit_id,
            assertion_tree=body.assertion_tree,
            metadata=body.metadata,
            arbitration_audit_feed=body.arbitration_audit_feed,
            physics_meta=body.physics_meta or {},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    cid = int(body.consultation_id or 0)
    if cid > 0:
        try:
            entry = {
                "protocol": "arbitration_overrule.v1",
                "audit_id": str(body.audit_id).strip(),
                "at": now_iso(),
            }
            with session_scope() as s:
                persist_arbitration_log_to_snapshot(s, consultation_id=cid, entry=entry)
        except Exception:
            _LOG.warning("arbitration_overrule persist skipped consultation_id=%s", cid, exc_info=True)
    return patch


@router.post("/v1/seed-preview", response_model=dict)
async def seed_preview(body: AnalyzeSeedRequest) -> dict:
    """
    轻量排盘：仅四柱 + 大运/流年（按 reference_year），无 LLM、无物理张量。
    供前端在正式「测算八字」前展示六柱预览。
    """
    from app.services.bazi_engine import get_bazi, get_timeline_snapshot

    try:
        pillars = get_bazi(body.date, body.time, body.calendar)
        timeline = get_timeline_snapshot(
            body.date,
            body.time,
            body.calendar,
            1 if body.gender == "male" else 0,
            body.reference_year,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {e}") from e
    timeline_out = dict(timeline) if isinstance(timeline, dict) else {}
    eo = body.external_overrides if isinstance(getattr(body, "external_overrides", None), dict) else {}
    if eo.get("liunian_ganzhi"):
        timeline_out["liunian"] = str(eo["liunian_ganzhi"]).strip()
    if eo.get("dayun_ganzhi"):
        timeline_out["dayun"] = str(eo["dayun_ganzhi"]).strip()
    return {
        "pillars": pillars.model_dump(),
        "timeline": timeline_out,
    }


@router.post("/v1/audit-physics-with-llm", response_model=dict)
async def audit_physics_with_llm(body: AuditPhysicsWithLlmRequest) -> dict:
    return await audit_physics_with_llm_flow(body)


@router.post("/v1/final-verdict", response_model=dict)
async def final_verdict(body: FinalVerdictRequest) -> dict:
    consensus_history = resolve_consensus_history(
        explicit_history=body.consensus_history,
        consultation_id=body.consultation_id,
        session_scope=session_scope,
    )
    try:
        return await generate_final_verdict(body, consensus_history)
    except PermissionError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "FINAL_VERDICT_FLOW_STATE_CONFLICT",
                "message": str(exc),
                "expected": {"flow_state": "ready"},
            },
        ) from exc
    except V12SchemaViolationError as exc:
        err = build_v12_error(
            code="V12_SCHEMA_VIOLATION_ERROR",
            user_message="终判结构缺失 assertion_tree，已阻断回退。",
            diagnosis=str(exc),
            hints=["检查 assertion_tree.nodes 是否为空。", "检查终判路由是否被旧协议覆盖。"],
            extra={"pulse_id": exc.pulse_id},
        )
        raise HTTPException(status_code=422, detail=err) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/v1/final-verdict/stream")
async def final_verdict_stream(body: FinalVerdictRequest) -> StreamingResponse:
    """NDJSON 流式终判：token 行为 LLM 增量，末帧 complete 与 POST /final-verdict JSON 同构。"""
    consensus_history = resolve_consensus_history(
        explicit_history=body.consensus_history,
        consultation_id=body.consultation_id,
        session_scope=session_scope,
    )
    return StreamingResponse(
        iter_final_verdict_ndjson(body, consensus_history),
        media_type="application/x-ndjson",
    )


@router.post("/v1/assertion-frames/backtrace", response_model=dict)
async def assertion_frames_backtrace(body: AssertionFrameBacktraceRequest) -> dict:
    md = body.metadata if isinstance(body.metadata, dict) else {}
    return {
        "ok": True,
        "protocol": "assertion_frame_backtrace.v14",
        "items": DecisionEvolutionFrameProtocol.backtrace(md, max_items=int(body.max_items or 80)),
        "priority_overwrite": DecisionEvolutionFrameProtocol.priority_overwrite_view(md),
    }


@router.post("/v1/realtime-narrator", response_model=dict)
async def realtime_narrator(body: RealtimeNarratorRequest) -> dict:
    return await compose_realtime_narration(
        metadata=body.metadata if isinstance(body.metadata, dict) else {},
        physics_tensor=body.physics_tensor if isinstance(body.physics_tensor, dict) else {},
        lang=body.lang,
        max_chars=int(body.max_chars or 220),
    )


@router.get("/v1/orchestrator/resume-pulse-history/{session_id}", response_model=None)
def get_resume_pulse_history(session_id: int) -> dict | JSONResponse:
    """M5 调试：按 session 拉取 resume 脉冲历史。库表缺失或查询失败时返回 503+空列表，避免裸 500。"""
    if session_id <= 0:
        raise HTTPException(status_code=422, detail="session_id must be positive")
    try:
        with session_scope() as s:
            rows = s.exec(
                select(ResumePulseHistory)
                .where(ResumePulseHistory.session_id == session_id)
                .order_by(ResumePulseHistory.resume_timestamp.asc())
            ).all()
    except SQLAlchemyError:
        _LOG.exception("resume_pulse_history query failed session_id=%s", session_id)
        return JSONResponse(
            status_code=503,
            content={"ok": False, "items": [], "error": "database_error"},
        )

    items: List[Dict[str, Any]] = []
    for r in rows:
        try:
            ts = getattr(r, "resume_timestamp", None)
            ts_str = ts.isoformat() if ts is not None and hasattr(ts, "isoformat") else ""
            pl_raw = getattr(r, "user_feedback_payload", None)
            pl: Dict[str, Any] = pl_raw if isinstance(pl_raw, dict) else {}
            items.append(
                {
                    "session_id": int(getattr(r, "session_id", 0) or 0),
                    "interrupted_node_id": str(getattr(r, "interrupted_node_id", "") or ""),
                    "resume_timestamp": ts_str,
                    "user_feedback_payload": pl,
                }
            )
        except Exception:
            _LOG.warning("resume_pulse_history row skipped session_id=%s", session_id, exc_info=True)

    return {"ok": True, "items": items}


@router.get("/v1/brain/learning-insights", response_model=dict)
def brain_learning_insights(top_n: int = 5) -> dict:
    limit_n = max(1, min(int(top_n or 5), 20))
    with session_scope() as s:
        rows = s.exec(
            select(
                BrainDissentLedger.reason_code,
                func.count(BrainDissentLedger.id).label("count"),
            )
            .group_by(BrainDissentLedger.reason_code)
            .order_by(desc("count"))
            .limit(limit_n)
        ).all()
    rank = [{"reason_code": str(r[0] or "UNKNOWN"), "count": int(r[1] or 0)} for r in rows]
    hints: list[str] = []
    for item in rank:
        rc = item["reason_code"]
        if "LIG_AXIS_POS_MISMATCH" in rc:
            hints.append("提高 PSV 语义门控阈值，压制与负向轴冲突的正向措辞。")
        elif "WEALTH" in rc:
            hints.append("下调财轴正向词模板权重，并提高比劫穿透比的拒稿惩罚。")
        elif "OFFICER" in rc:
            hints.append("增强官杀轴与 user_intention 的一致性约束，减少越轴叙事。")
        else:
            hints.append(f"为 {rc} 补充规则特征，纳入 RLHF-C 参数校准候选。")
    return {"ok": True, "top_reject_dimensions": rank, "parameter_hints": hints[:limit_n]}


@router.post("/v1/analyze/stress-test", response_model=dict)
async def stress_test(body: StressTestRequest) -> dict:
    return await run_stress_test(body)


@router.get("/v1/admin/settings", response_model=dict)
def admin_physics_settings_list(_: None = Depends(admin_token_guard)) -> dict:
    return {"ok": True, "settings": list_physics_registry_rows()}


@router.post("/v1/admin/settings", response_model=dict)
def admin_physics_settings_persist(
    body: PhysicsSettingsPersistRequest,
    _: None = Depends(admin_token_guard),
) -> dict:
    raw = [i.model_dump() for i in body.items]
    changed = persist_physics_registry_updates_from_body(raw)
    return {"ok": True, "changed": changed}


@router.get("/v1/plugins/conflict-hotspots", response_model=dict)
def plugins_conflict_hotspots(top_n: int = 24) -> dict:
    """Decision Inbox 门控遥测：Skill/插件签名与 eligible vs gated 频次。"""
    registry = PluginRegistry()
    return registry.get_conflict_hotspots(top_n=top_n)


@router.post("/v1/evolution/skill-feedback", response_model=dict)
def evolution_skill_feedback(body: SkillFeedbackRequest) -> dict:
    path = append_skill_feedback(body.model_dump())
    return {"ok": True, "path": str(path)}


@router.get("/v1/evolution/state", response_model=dict)
def evolution_state() -> dict:
    genes = load_rule_genes()
    return {
        "combination_space_total": TOTAL_BAZI_COMBINATION_SPACE,
        "admission": is_evolution_admitted_to_mainnet(),
        "heatmap": gene_maturity_heatmap(genes),
        "genes": [g.to_json() for g in genes],
    }


@router.put("/v1/evolution/admission", response_model=dict)
def evolution_admission(body: EvolutionAdmissionRequest) -> dict:
    set_evolution_admission(bool(body.admit_evolved_to_mainnet))
    return {"ok": True, "admission": is_evolution_admitted_to_mainnet()}


@router.post("/v1/evolution/run-batch", response_model=dict)
def evolution_run_batch(body: EvolutionBatchRunRequest) -> dict:
    runner = EvolutionaryBatchRunner()
    result = runner.run_once(n_seeds=int(body.n_seeds))
    return {"ok": True, "summary": result.summary, "sample_count": len(result.samples)}


@router.post("/v1/decision/resolve-conflict", response_model=dict)
def decision_resolve_conflict(body: ResolveConflictRequest) -> dict:
    return resolve_conflict(
        consultation_id=body.consultation_id,
        skill_id=body.skill_id,
        abs_delta=float(body.abs_delta),
        processing_preference=body.processing_preference,
        extra=body.extra,
    )


@router.post("/v1/recommendations/top-decisions", response_model=dict)
def recommendations_top_decisions(body: Dict[str, Any]) -> dict:
    """
    V6.1：并行插件 dry-run + 内置配置补丁预览，返回因果评分最高的决策与 ``reason_templates`` 填充文案。
    """
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="expected_json_object")
    pt = body.get("physics_tensor") if isinstance(body.get("physics_tensor"), dict) else {}
    md = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
    bf = body.get("blind_school_features") if isinstance(body.get("blind_school_features"), dict) else {}
    ep = body.get("enabled_plugins") if isinstance(body.get("enabled_plugins"), list) else []
    cards = body.get("inbox_cards") if isinstance(body.get("inbox_cards"), list) else None
    top_n = body.get("top_n")
    tn = int(top_n) if isinstance(top_n, (int, float)) and not isinstance(top_n, bool) else 3
    return get_top_recommendations(
        physics_tensor=pt,
        metadata=md,
        blind_school_features=bf,
        enabled_plugins=[str(x) for x in ep],
        inbox_cards=[c for c in (cards or []) if isinstance(c, dict)],
        top_n=max(1, min(12, tn)),
    )


@router.get("/v1/plugins/manifest", response_model=dict)
def plugins_manifest(enabled_plugins: Optional[str] = None, plugin_id: Optional[str] = None) -> dict:
    """
    插件清单单一事实源（SSOT）：
    - plugins: 元数据 + 层级 + 状态 + 性能快照
    - dependency_links: 依赖连线（供拓扑图绘制）
    - plugin_id: 若提供则仅返回该插件切片（含 blueprint_markdown），供逻辑蓝图 Modal
    """
    parsed: List[str] = []
    if enabled_plugins:
        parsed = [item.strip() for item in enabled_plugins.split(",") if item.strip()]
    registry = PluginRegistry()
    pid = plugin_id.strip() if isinstance(plugin_id, str) and plugin_id.strip() else None
    payload = registry.get_manifest(enabled_plugins=parsed or None, plugin_id=pid)
    if pid and payload.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"unknown plugin_id={pid}")
    return payload
