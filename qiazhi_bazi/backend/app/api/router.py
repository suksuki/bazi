"""API：健康检查、示例 BaziMetadata、LLM、决策链写入。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.admin_auth import admin_token_guard
from app.api.contracts import (
    AnalyzeClashRequest,
    AnalyzeSeedRequest,
    AuditPhysicsWithLlmRequest,
    ChatRequest,
    ConfirmStructureRequest,
    ConsultationCreate,
    DecisionRollbackRequest,
    DecisionStepCreate,
    EvolutionAdmissionRequest,
    EvolutionBatchRunRequest,
    FinalVerdictRequest,
    PhysicsSettingsPersistRequest,
    ResolveConflictRequest,
    SkillFeedbackRequest,
    StressTestRequest,
    TranslateRequest,
)
from app.api.router_helpers import now_iso
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
    run_stress_test,
    resolve_consensus_history,
    translate_text_items,
)
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
from app.services.llm_service import run_chat_completion, stream_chat_events
from app.core.physics.settings_manager import list_physics_registry_rows, persist_physics_registry_updates_from_body

router = APIRouter(tags=["qiazhi-bazi"])


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


@router.post("/consultations", response_model=dict)
def create_consultation(body: ConsultationCreate) -> dict:
    with session_scope() as s:
        return create_consultation_record(s, body)


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


@router.post("/decision-steps", response_model=dict)
def create_decision_step(body: DecisionStepCreate) -> dict:
    with session_scope() as s:
        return create_decision_step_record(s, body)


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


@router.post("/v1/analyze-seed", response_model=dict)
async def analyze_seed(body: AnalyzeSeedRequest) -> dict:
    """
    输入生日（日期+时刻） -> 基础排盘 -> 冲合扫描 -> 首轮引导文案。
    """
    from app.services.bazi_engine import get_bazi, get_timeline_snapshot

    try:
        return await analyze_seed_flow(body, get_bazi, get_timeline_snapshot, now_iso())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {e}") from e


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
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
