"""API：健康检查、示例 BaziMetadata、LLM、决策链写入。"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.scanner import Scanner
from app.core.physics import calculate_clash_loss
from app.core.runtime_config import get_runtime_config
from app.db.session import session_scope
from app.db.models import Consultation, DecisionStep, SessionConsensus
from app.llm.client import QwenClient, build_first_observation_messages
from app.skills.physics_engine import PhysicsInferenceSkill
from app.skills.final_verdict import FinalVerdictSkill
from app.schemas.bazi_metadata import (
    BaziMetadata,
    ConflictMatrix,
    ConflictPoint,
    FlowState,
    FourPillars,
    StemBranchPair,
    detect_clashes,
)
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["qiazhi-bazi"])


class ConsultationCreate(BaseModel):
    subject_ref: Optional[str] = None
    input_meta: Dict[str, Any] = Field(default_factory=dict)


class DecisionStepCreate(BaseModel):
    consultation_id: int
    step_type: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    human_choice: Optional[Dict[str, Any]] = None


class DecisionRollbackRequest(BaseModel):
    target_step_id: int
    reason: Optional[str] = None


class ConfirmStructureRequest(BaseModel):
    consultation_id: int
    structure_name: str
    confidence: Optional[float] = None
    evidence: Optional[str] = None


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
        c = Consultation(subject_ref=body.subject_ref, input_meta=body.input_meta)
        s.add(c)
        s.flush()
        s.refresh(c)
        return {"id": c.id}


@router.post("/confirm-structure", response_model=dict)
def confirm_structure(body: ConfirmStructureRequest) -> dict:
    """
    L2 会把“格局认领”结果写进当前 consultation 的 input_meta，
    从而在后续 decision_step 的写入链路里复用（避免改数据库 schema）。
    """
    with session_scope() as s:
        c = s.get(Consultation, body.consultation_id)
        if not c:
            raise HTTPException(status_code=404, detail="consultation not found")
        meta = dict(c.input_meta or {})
        meta["confirmed_structure"] = {
            "name": body.structure_name,
            "confidence": body.confidence,
            "evidence": body.evidence,
            "confirmed_at": datetime.utcnow().isoformat(),
        }
        c.input_meta = meta
        s.add(c)
        return {"ok": True, "confirmed_structure": meta["confirmed_structure"]}


@router.post("/decision-steps", response_model=dict)
def create_decision_step(body: DecisionStepCreate) -> dict:
    with session_scope() as s:
        c = s.get(Consultation, body.consultation_id)
        confirmed_structure = None
        if c:
            meta = c.input_meta or {}
            confirmed_structure = meta.get("confirmed_structure")

        step = DecisionStep(
            consultation_id=body.consultation_id,
            step_type=body.step_type,
            raw_data={**(body.raw_data or {}), **({} if confirmed_structure is None else {"confirmed_structure": confirmed_structure})},
            human_choice=body.human_choice,
        )
        s.add(step)
        s.flush()
        s.refresh(step)
        # ConsensusTracker: 把本次执行中确认的原子提案写入 session_consensus
        choice = body.human_choice or {}
        action = str(choice.get("action") or "")
        selected_proposals = choice.get("selected_proposals") or []
        if action == "execute" and isinstance(selected_proposals, list):
            for p in selected_proposals:
                if not isinstance(p, dict):
                    continue
                key = str(p.get("param_key") or "").strip()
                if not key:
                    continue
                val_raw = p.get("suggested_value")
                try:
                    val = float(val_raw) if val_raw is not None else None
                except Exception:
                    val = None
                reasoning = str(p.get("reason") or p.get("expected_impact") or "")
                s.add(
                    SessionConsensus(
                        session_id=body.consultation_id,
                        decision_key=key,
                        confirmed_value=val,
                        reasoning=reasoning,
                    )
                )
        return {"id": step.id}


@router.post("/decision-steps/rollback", response_model=dict)
def rollback_decision_step(body: DecisionRollbackRequest) -> dict:
    with session_scope() as s:
        target = s.get(DecisionStep, body.target_step_id)
        if not target:
            raise HTTPException(status_code=404, detail="target decision step not found")
        event = DecisionStep(
            consultation_id=target.consultation_id,
            step_type="rollback_event",
            raw_data={
                "target_step_id": target.id,
                "target_step_type": target.step_type,
            },
            human_choice={
                "action": "rollback",
                "reason": body.reason or "manual rollback",
            },
        )
        s.add(event)
        s.flush()
        s.refresh(event)
        return {"id": event.id, "target_step_id": target.id, "consultation_id": target.consultation_id}


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    temperature: float = 0.4
    max_tokens: int = 2048
    lang: str = "ZH"


class AnalyzeClashRequest(BaseModel):
    pillars: FourPillars
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lang: str = "ZH"
    session_id: Optional[int] = None
    dayun: Optional[str] = None
    liunian: Optional[str] = None


class AnalyzeSeedRequest(BaseModel):
    date: str
    time: str = "12:00"
    calendar: str = "solar"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lang: str = "ZH"
    session_id: Optional[int] = None


class AuditPhysicsWithLlmRequest(BaseModel):
    metadata: BaziMetadata
    physics_tensor: Optional[Dict[str, Any]] = None
    solar_term: Optional[str] = None
    lang: str = "ZH"
    consensus_history: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: Optional[int] = None


class AuditLlmStructuredResponse(BaseModel):
    diagnosis: str = ""
    # 若 LLM JSON 缺失 alignment_score，则落到 0.0，后续交由语义修补器补齐
    alignment_score: float = 0.0
    top_anomaly: str = ""
    causal_reasoning: str = ""
    tuning_suggestions: List[str] = Field(default_factory=list)
    sql_patch: str = ""
    refresh_hint: str = ""
    logic_proposal: Dict[str, Any] = Field(default_factory=dict)


class TranslateRequest(BaseModel):
    texts: List[str]
    target_lang: str = "ZH"


class FinalVerdictRequest(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    physics_tensor: Dict[str, Any] = Field(default_factory=dict)
    selected_cards: List[Dict[str, Any]] = Field(default_factory=list)
    consensus_history: List[Dict[str, Any]] = Field(default_factory=list)
    previous_verdict: str = ""
    previous_logical_evidence: List[str] = Field(default_factory=list)
    consultation_id: Optional[int] = None
    lang: str = "ZH"


def _guess_text_lang(text: str) -> str:
    if not text:
        return "UNKNOWN"
    if any("\uac00" <= ch <= "\ud7a3" for ch in text):
        return "KO"
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "ZH"
    if text.isascii():
        return "EN"
    return "UNKNOWN"


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _lang_output_instruction(lang: str) -> str:
    upper = (lang or "ZH").upper()
    if upper == "EN":
        return (
            "请基于中文命理逻辑推演，但最终只用英文输出。"
            "若术语无直接对等词，使用标准学术拼音并保留术语一致性。"
        )
    if upper == "KO":
        return "请基于中文命理逻辑推演，但最终只用韩语输出，并使用韩语术语。请务必以“최종 결론:”开头。"
    return "请基于中文命理逻辑推演，并只用中文输出。"


def _build_physics_audit_prompt(
    *,
    deity_scores: Dict[str, float],
    root_check: Dict[str, Any],
    seasonal_factors: Dict[str, Any],
    consensus_history: List[Dict[str, Any]],
    lang: str,
) -> List[Dict[str, str]]:
    lang_hint = _lang_output_instruction(lang)
    system_text = (
        "你是 0.13 实验室的首席物理命理审计官。只输出严格 JSON，不输出任何非 JSON 文本。"
        "字段固定（字段名/层级必须一致）："
        '{"diagnosis":"","alignment_score":0,"top_anomaly":"","causal_reasoning":"","tuning_suggestions":[""],"sql_patch":"","refresh_hint":"","logic_proposal":{"title":"","param_key":"","suggested_value":0,"reason":"","expected_impact":"","sql_patch":"","source_role":"LLM"}}'
        "若 top_anomaly 非空，则 alignment_score 必须 < 60。"
    )
    user_text = (
        f"Input. 十神分值={json.dumps(deity_scores, ensure_ascii=False)}；"
        f"根气汇总={json.dumps(root_check, ensure_ascii=False)}；"
        f"季节系数={json.dumps(seasonal_factors, ensure_ascii=False)}。\n"
        f"## 已达成逻辑共识\n{json.dumps(consensus_history or [], ensure_ascii=False)}\n"
        "Mandatory: "
        "1) top_anomaly: 最核心不匹配；"
        "2) causal_reasoning: 解释其违背的能量规律；"
        "3) sql_patch: 仅允许 UPDATE physics_interaction_params SET param_value=<float> WHERE param_key='<KEY>';"
        "4) logic_proposal: 必须含 title/param_key/suggested_value/reason/expected_impact/sql_patch/source_role；"
        "5) 对于已达成逻辑共识中的参数，不得重复质疑其已确认值，应在其基础上分析尚未共识的矛盾；"
        f"{lang_hint}"
    )
    return [{"role": "system", "content": system_text}, {"role": "user", "content": user_text}]


def _extract_first_json_object(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("json object not found")
    return m.group(0)


def _coerce_alignment_score(score: float, top_anomaly: str) -> float:
    val = max(1.0, min(100.0, float(score)))
    if top_anomaly.strip() and val >= 60.0:
        return 59.0
    return val


def _patch_audit_json_from_text(raw_text: str, draft: AuditLlmStructuredResponse) -> tuple[AuditLlmStructuredResponse, bool]:
    text = (raw_text or "").strip()
    changed = False
    out = draft.model_copy(deep=True)
    sentinel_missing = "未拿到结构化审计结论" in (out.top_anomaly or "")
    if not out.top_anomaly or sentinel_missing:
        # 兼容 JSON key： "top_anomaly":"..."
        m = re.search(r"\"top_anomaly\"\s*[:：]\s*\"([^\"]+)\"", text, flags=re.IGNORECASE)
        if not m:
            m = re.search(r"(?:anomaly|异常|预警)[:：]\s*([^\n]+)", text, flags=re.IGNORECASE)
        if m:
            out.top_anomaly = m.group(1).strip()
            changed = True
    if (out.alignment_score is None) or float(out.alignment_score) <= 0 or (sentinel_missing and float(out.alignment_score) == 35.0):
        # 支持：alignment_score: 12 / alignment score = 12 / score 12分 等
        m = re.search(
            r"(?:alignment[_\s-]*score|对齐分|alignment|对齐)[：:\s]*([0-9]{1,3}(?:\.[0-9]+)?)",
            text,
            flags=re.IGNORECASE,
        )
        if not m:
            m = re.search(r"score[:：\s]*([0-9]{1,3}(?:\.[0-9]+)?)", text, flags=re.IGNORECASE)
        if not m:
            m = re.search(r"([0-9]{1,3}(?:\.[0-9]+)?)\s*分", text)
        if m:
            out.alignment_score = float(m.group(1))
            changed = True
    if not out.sql_patch or (sentinel_missing and "param_value=0.20" in (out.sql_patch or "")):
        m = re.search(
            r"(UPDATE\s+physics_interaction_params\s+SET\s+param_value\s*=\s*[0-9]*\.?[0-9]+\s+WHERE\s+param_key\s*=\s*'[A-Za-z0-9_]+'\s*;?)",
            text,
            flags=re.IGNORECASE,
        )
        if m:
            out.sql_patch = m.group(1).strip()
            changed = True
        # 仅出现“CF_FLOATING_DECAY=0.15”但未给 UPDATE 语句时：补全生成 sql_patch
        if not out.sql_patch:
            kv = re.search(r"(CF_FLOATING_DECAY|A_PROTRUSION)\s*[:：=]\s*([0-9]*\.?[0-9]+)", text, flags=re.IGNORECASE)
            if kv:
                key = kv.group(1)
                val = float(kv.group(2))
                if 0.0 <= val <= 2.0:
                    out.sql_patch = f"UPDATE physics_interaction_params SET param_value={val:.2f} WHERE param_key='{key}';"
                    changed = True
    # Healer 3.0：如果正文里给了“十神应降到/应升到某数值”，把它映射到 tuning_suggestions
    existing_suggestions = [str(s).strip() for s in (out.tuning_suggestions or []) if str(s).strip()]
    if not existing_suggestions:
        ten_gods = r"(比肩|劫财|食神|伤官|正财|偏财|正官|七杀|正印|偏印|官杀)"
        down_pat = re.compile(rf"{ten_gods}(?:\s*(?:应该|应当|应))?\s*(降到|降为)\s*([0-9]{{1,3}}(?:\.[0-9]+)?)", flags=re.IGNORECASE)
        up_pat = re.compile(rf"{ten_gods}(?:\s*(?:应该|应当|应))?\s*(升到|升为|提高到)\s*([0-9]{{1,3}}(?:\.[0-9]+)?)", flags=re.IGNORECASE)
        extracted: list[str] = []
        for m in down_pat.finditer(text):
            god = m.group(1)
            op = m.group(2)
            val = m.group(3)
            extracted.append(f"正文提取：{god} 目标{op}{val}（用于对齐物理现实）")
        for m in up_pat.finditer(text):
            god = m.group(1)
            op = m.group(2)
            val = m.group(3)
            extracted.append(f"正文提取：{god} 目标{op}{val}（用于对齐物理现实）")
        if extracted:
            out.tuning_suggestions = extracted[:5]
            changed = True
    if not out.diagnosis:
        out.diagnosis = "语义修补：由正文提取关键字段后完成结构化补全。"
        changed = True
    return out, changed


def _sql_filter(sql_patch: str) -> str:
    sql = (sql_patch or "").strip()
    if not sql:
        return ""
    # 禁止注入痕迹和多语句
    if "--" in sql or "/*" in sql or "*/" in sql:
        return ""
    if sql.count(";") > 1:
        return ""
    pattern = re.compile(
        r"^UPDATE\s+physics_interaction_params\s+SET\s+param_value\s*=\s*([0-9]*\.?[0-9]+)\s+WHERE\s+param_key\s*=\s*'([A-Za-z0-9_]+)'\s*;?$",
        re.IGNORECASE,
    )
    m = pattern.match(sql)
    if not m:
        return ""
    val = float(m.group(1))
    key = m.group(2)
    if not (0.0 <= val <= 2.0):
        return ""
    return f"UPDATE physics_interaction_params SET param_value={val:.2f} WHERE param_key='{key}';"


def _physics_snapshot(physics_tensor: Dict[str, Any]) -> str:
    deity = (physics_tensor.get("deity_scores", {}) if isinstance(physics_tensor, dict) else {}) or {}
    audit_log = (physics_tensor.get("audit_log", {}) if isinstance(physics_tensor, dict) else {}) or {}
    trace = (audit_log.get("trace", {}) if isinstance(audit_log, dict) else {}) or {}
    root_check = trace.get("root_check", {}) if isinstance(trace, dict) else {}
    meta = (physics_tensor.get("meta", {}) if isinstance(physics_tensor, dict) else {}) or {}
    self_score = float(deity.get("比肩", 0.0)) + float(deity.get("劫财", 0.0))
    root_state = "None" if bool(root_check.get("no_root")) else "Linked"
    season = str(meta.get("solar_term") or "derived")
    return f"[Self: {self_score:.1f} | Root: {root_state} | Season: {season}]"


def _apply_energy_preview(metadata: BaziMetadata) -> None:
    """
    v1.2 预览：基于已识别冲突给四柱地支能量做静态扣减。
    """
    if not metadata.pillars:
        return
    pillars_map = {
        "year_branch": metadata.pillars.year,
        "month_branch": metadata.pillars.month,
        "day_branch": metadata.pillars.day,
        "hour_branch": metadata.pillars.hour,
    }
    month_branch = metadata.pillars.month.branch
    for p in metadata.conflict_matrix.points:
        if p.kind != "clash" or len(p.positions) != 2:
            continue
        a_pos, b_pos = p.positions
        a = pillars_map.get(a_pos)
        b = pillars_map.get(b_pos)
        if not a or not b:
            continue
        loss = calculate_clash_loss(a.branch, b.branch, month_branch=month_branch)
        a.energy_value = max(0, int(a.energy_value) - int(loss.get(a.branch, 0)))
        b.energy_value = max(0, int(b.energy_value) - int(loss.get(b.branch, 0)))


@router.post("/llm/chat")
async def llm_chat(body: ChatRequest) -> dict:
    cfg = get_runtime_config().get("llm", {})
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    messages = [
        {"role": "system", "content": "你是严谨命理分析助手，必须基于中文术语体系进行推演。"},
        *body.messages,
        {"role": "user", "content": _lang_output_instruction(body.lang)},
    ]
    stop_words = ["Thinking Process:", "Reasoning:", "思考过程", "推理过程"]
    try:
        text = await client.chat(messages, temperature=body.temperature, max_tokens=body.max_tokens, stop=stop_words)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return {"content": text}


@router.post("/llm/stream")
async def llm_stream(body: ChatRequest):
    cfg = get_runtime_config().get("llm", {})
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )

    messages = [
        {"role": "system", "content": "你是严谨命理分析助手，必须基于中文术语体系进行推演。"},
        *body.messages,
        {"role": "user", "content": _lang_output_instruction(body.lang)},
    ]
    stop_words = ["Thinking Process:", "Reasoning:", "思考过程", "推理过程"]
    async def gen():
        try:
            async for chunk in client.stream_chat(
                messages, temperature=body.temperature, max_tokens=body.max_tokens, stop=stop_words
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/history")
def history() -> dict:
    with session_scope() as s:
        rows = s.query(DecisionStep).order_by(DecisionStep.id.desc()).limit(50).all()
        items = [
            {
                "id": f"db-{r.id}",
                "title": r.step_type,
                "answer": (r.human_choice or {}).get("action") if isinstance(r.human_choice, dict) else None,
                "createdAt": r.created_at.isoformat() if getattr(r, "created_at", None) else _now_iso(),
            }
            for r in rows
        ]
    return {"items": items}


@router.post("/i18n/translate", response_model=dict)
async def i18n_translate(body: TranslateRequest) -> dict:
    texts = [x for x in body.texts if isinstance(x, str) and x.strip()]
    if not texts:
        return {"items": []}
    if body.target_lang.upper() == "ZH":
        return {"items": texts}
    target = body.target_lang.upper()
    if all(_guess_text_lang(t) in {target, "UNKNOWN"} for t in texts):
        return {"items": texts}
    cfg = get_runtime_config().get("llm", {})
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    lang_name = {"EN": "English", "KO": "Korean", "ZH": "Chinese"}.get(body.target_lang.upper(), "English")
    raw = await client.chat(
        [
            {
                "role": "system",
                "content": (
                    "You are a translation engine. Return STRICT JSON only: "
                    '{"items":["..."]}. Keep same count and order, no explanation.'
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"target": lang_name, "items": texts}, ensure_ascii=False),
            },
        ],
        temperature=0.1,
        max_tokens=1500,
        stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
    )
    try:
        parsed = json.loads(raw)
        items = parsed.get("items", [])
        if isinstance(items, list) and len(items) == len(texts):
            return {"items": [str(x) for x in items]}
    except Exception:
        pass
    return {"items": texts}


@router.post("/v1/analyze_clash", response_model=dict)
async def analyze_clash(body: AnalyzeClashRequest) -> dict:
    """
    输入四柱，识别地支六冲，并调用 LLM 生成给裁决人的判定提示语。
    """
    matrix = Scanner().scan(body.pillars)
    metadata_obj = BaziMetadata(
        pillars=body.pillars,
        conflict_matrix=matrix,
        flow_state=FlowState.UNKNOWN,
        notes="已完成原子探测（六冲+六合）",
    )
    _apply_energy_preview(metadata_obj)
    location_hint = ""
    if body.latitude is not None and body.longitude is not None:
        location_hint = f" 当前地理参考为纬度{body.latitude}、经度{body.longitude}。"
    cfg = get_runtime_config().get("llm", {})
    model_name = str(cfg.get("model") or "LLM")
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    llm_elapsed_ms = 0.0
    llm_approx_tokens = 0.0
    t0 = time.perf_counter()
    try:
        llm_text = await client.chat(
            build_first_observation_messages(metadata_obj.model_dump(), location_hint=location_hint, lang=body.lang),
            temperature=0.3,
            max_tokens=512,
            stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
        )
        llm_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        llm_approx_tokens = round(len(llm_text) / 1.8, 2)
    except Exception:
        llm_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        observed = [p.detail for p in metadata_obj.conflict_matrix.points]
        if not observed:
            llm_text = "我暂未观察到明显的冲合。我们是否继续做下一层扫描？"
        else:
            llm_text = (
                "我先汇报观察到的物理点：" + "、".join(observed) + "。"
                "我发现局部正在对撞/耦合，我们是否需要深入分析这个局部？"
            )

    physics_skill = PhysicsInferenceSkill.instance()
    consumed = physics_skill.consume(
        {
            "metadata": metadata_obj,
            "session_id": body.session_id,
            "dayun": body.dayun,
            "liunian": body.liunian,
        }
    )
    physics_tensor = physics_skill.produce(consumed)
    return {
        "metadata": metadata_obj.model_dump(),
        "llm_prompt": llm_text,
        "llm_meta": {
            "model_name": model_name,
            "elapsed_ms": llm_elapsed_ms,
            "approx_tokens": llm_approx_tokens,
        },
        "physics_tensor": physics_tensor,
    }


@router.post("/v1/analyze-seed", response_model=dict)
async def analyze_seed(body: AnalyzeSeedRequest) -> dict:
    """
    输入生日（日期+时刻） -> 基础排盘 -> 冲合扫描 -> 首轮引导文案。
    """
    from app.services.bazi_engine import get_bazi, get_timeline_snapshot

    try:
        pillars = get_bazi(body.date, body.time, body.calendar)
        timeline = get_timeline_snapshot(body.date, body.time, body.calendar)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {e}") from e
    result = await analyze_clash(
        AnalyzeClashRequest(
            pillars=pillars,
            latitude=body.latitude,
            longitude=body.longitude,
            lang=body.lang,
            session_id=body.session_id,
            dayun=(timeline or {}).get("dayun"),
            liunian=(timeline or {}).get("liunian"),
        )
    )
    metadata = result["metadata"]
    llm_meta = result.get("llm_meta", {})
    model_name = str(llm_meta.get("model_name") or "LLM")
    llm_elapsed_ms = float(llm_meta.get("elapsed_ms") or 0.0)
    llm_approx_tokens = float(llm_meta.get("approx_tokens") or 0.0)
    param_version_id = str((result.get("physics_tensor", {}) or {}).get("audit_log", {}).get("param_version_id", "--"))
    snapshot_summary = _physics_snapshot(result.get("physics_tensor", {}) or {})
    hard_route_logs = (
        ((result.get("physics_tensor", {}) or {}).get("audit_log", {}) or {})
        .get("trace", {})
        .get("hard_route_logs", [])
    )
    root_check = (((result.get("physics_tensor", {}) or {}).get("audit_log", {}) or {}).get("trace", {}).get("root_check", {}) or {})
    local_decay_applied = bool(root_check.get("no_root", False))
    points = metadata.get("conflict_matrix", {}).get("points", [])
    point_labels = [p.get("detail", "") for p in points]
    trail = [
        {
            "step": "01",
            "role": "Arbiter",
            "action": f"提交生辰 {body.date} {body.time}，请求物理建模。",
            "relay_to": "Core",
            "timestamp": _now_iso(),
            "payload": {"date": body.date, "time": body.time, "calendar": body.calendar},
        },
        {
            "step": "02",
            "role": "Core",
            "action": (
                f"完成排盘 [{metadata['pillars']['year']['stem']}{metadata['pillars']['year']['branch']}/"
                f"{metadata['pillars']['month']['stem']}{metadata['pillars']['month']['branch']}/"
                f"{metadata['pillars']['day']['stem']}{metadata['pillars']['day']['branch']}/"
                f"{metadata['pillars']['hour']['stem']}{metadata['pillars']['hour']['branch']}] "
                f"及物理探测 [{('、'.join(point_labels) if point_labels else '未见明显冲合')}]。"
                "数据已移交审计员。"
            ),
            "relay_to": "Auditor",
            "timestamp": _now_iso(),
            "payload": {
                "pillars": metadata.get("pillars"),
                "conflicts": points,
                "snapshot_summary": snapshot_summary,
                "hard_route_logs": hard_route_logs,
                "local_decay_applied": local_decay_applied,
                "self_deity_only": True,
            },
        },
        {
            "step": "03",
            "role": "Auditor",
            "action": "基于物理冲突，生成初级判词与诱导问句。",
            "relay_to": "Arbiter",
            "timestamp": _now_iso(),
            "payload": {
                "llm_prompt": result["llm_prompt"],
                "model_name": model_name,
                "llm_elapsed_ms": llm_elapsed_ms,
                "llm_approx_tokens": llm_approx_tokens,
                "param_version_id": param_version_id,
                "snapshot_summary": snapshot_summary,
            },
        },
    ]
    result["audit_summary"] = trail
    result["timeline"] = timeline
    return result


@router.post("/v1/audit-physics-with-llm", response_model=dict)
async def audit_physics_with_llm(body: AuditPhysicsWithLlmRequest) -> dict:
    physics_skill = PhysicsInferenceSkill.instance()
    physics_tensor = body.physics_tensor
    if not physics_tensor:
        consumed = physics_skill.consume({"metadata": body.metadata, "solar_term": body.solar_term, "session_id": body.session_id})
        physics_tensor = physics_skill.produce(consumed)

    deity_scores = (physics_tensor or {}).get("deity_scores", {}) or {}
    audit_log = (physics_tensor or {}).get("audit_log", {}) or {}
    trace = (audit_log.get("trace", {}) if isinstance(audit_log, dict) else {}) or {}
    root_check = trace.get("root_check", {}) if isinstance(trace, dict) else {}
    seasonal_factors = {
        "solar_term": (physics_tensor or {}).get("meta", {}).get("solar_term", "derived_from_month_branch"),
        "params": (physics_tensor or {}).get("meta", {}).get("params", {}),
    }

    cfg = get_runtime_config().get("llm", {})
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    prompt = _build_physics_audit_prompt(
        deity_scores=deity_scores,
        root_check=root_check if isinstance(root_check, dict) else {},
        seasonal_factors=seasonal_factors,
        consensus_history=body.consensus_history or [],
        lang=body.lang,
    )
    raw = ""
    parsed: AuditLlmStructuredResponse | None = None
    structured_hit = False
    repair_mode = "fallback"
    llm_elapsed_ms = 0.0
    llm_approx_tokens = 0.0
    try:
        t0 = time.perf_counter()
        raw = await client.chat(
            prompt,
            temperature=0.2,
            max_tokens=700,
            # 不使用 stop：避免在 JSON 中途触发截断导致结构化解析失败
            stop=None,
        )
        llm_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        llm_approx_tokens = round(len(raw) / 1.8, 2)
        parsed = AuditLlmStructuredResponse.model_validate(json.loads(_extract_first_json_object(raw)))
        structured_hit = True
        repair_mode = "strict_json"
    except Exception:
        try:
            retry_prompt = [
                {"role": "system", "content": "Only output strict JSON object. No prose."},
                {"role": "user", "content": f"基于上一轮分析，输出JSON：{raw[:1800]}"},
            ]
            t1 = time.perf_counter()
            retry_raw = await client.chat(
                retry_prompt,
                temperature=0.0,
                max_tokens=180,
                # 同理：去掉 stop，保证 JSON 对象完整落地再解析
                stop=None,
            )
            llm_elapsed_ms = round((llm_elapsed_ms or 0.0) + (time.perf_counter() - t1) * 1000, 2)
            llm_approx_tokens = round((llm_approx_tokens or 0.0) + len(retry_raw) / 1.8, 2)
            raw = retry_raw
            parsed = AuditLlmStructuredResponse.model_validate(json.loads(_extract_first_json_object(retry_raw)))
            structured_hit = True
            repair_mode = "retry_json"
        except Exception:
            parsed = None

    parsed_obj = parsed or AuditLlmStructuredResponse(
        diagnosis="结构化审计回退：LLM 未返回可解析 JSON，已启用默认评分策略。",
        alignment_score=35.0,
        top_anomaly="未拿到结构化审计结论，请检查 LLM 返回格式。",
        causal_reasoning="建议检查根气与季节系数是否同步进入模型。",
        tuning_suggestions=[
            "UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key='CF_FLOATING_DECAY';",
        ],
        sql_patch="UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key='CF_FLOATING_DECAY';",
        refresh_hint="POST /api/admin/refresh-physics",
        logic_proposal={
            "title": "[系统逻辑校准] 抑制比肩虚浮能量",
            "param_key": "CF_FLOATING_DECAY",
            "suggested_value": 0.20,
            "reason": "乙木无根且比肩偏高，需要增强虚浮衰减。",
            "expected_impact": "比肩分值下降并与根气现实对齐。",
            "sql_patch": "UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key='CF_FLOATING_DECAY';",
            "source_role": "LLM",
        },
    )
    needs_semantic_heal = (
        (not structured_hit)
        or float(getattr(parsed_obj, "alignment_score", 0.0) or 0.0) <= 0.0
        or not (parsed_obj.sql_patch or "").strip()
        or not (isinstance(parsed_obj.logic_proposal, dict) and parsed_obj.logic_proposal.get("sql_patch"))
    )
    if needs_semantic_heal:
        patched_obj, patched = _patch_audit_json_from_text(raw, parsed_obj)
        parsed_obj = patched_obj
        if patched:
            structured_hit = True
            repair_mode = "semantic_patch"

    top_anomaly = parsed_obj.top_anomaly.strip()
    diagnosis = parsed_obj.diagnosis.strip()
    alignment_score = _coerce_alignment_score(parsed_obj.alignment_score, top_anomaly)
    causal_reasoning = parsed_obj.causal_reasoning.strip()
    tuning_suggestions = [str(x) for x in (parsed_obj.tuning_suggestions or []) if str(x).strip()]
    sql_patch = _sql_filter(parsed_obj.sql_patch.strip())
    if not sql_patch and tuning_suggestions:
        sql_patch = _sql_filter(str(tuning_suggestions[0]))
    if not sql_patch:
        sql_patch = "UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key='CF_FLOATING_DECAY';"
    logic_proposal = parsed_obj.logic_proposal if isinstance(parsed_obj.logic_proposal, dict) else {}
    if not logic_proposal:
        logic_proposal = {
            "title": "[系统逻辑校准] 抑制比肩虚浮能量",
            "param_key": "CF_FLOATING_DECAY",
            "suggested_value": 0.20,
            "reason": "结构化回退场景，建议先收敛虚浮系数。",
            "expected_impact": "重算后比肩下降，结构稳定性提升。",
            "sql_patch": sql_patch,
            "source_role": "LLM",
        }
    logic_proposal["sql_patch"] = _sql_filter(str(logic_proposal.get("sql_patch", ""))) or sql_patch
    logic_proposal["source_role"] = str(logic_proposal.get("source_role") or "LLM")
    refresh_hint = parsed_obj.refresh_hint.strip()

    return {
        "ok": True,
        "diagnosis": diagnosis,
        "alignment_score": alignment_score,
        "top_anomaly": top_anomaly,
        "causal_reasoning": causal_reasoning,
        "tuning_suggestions": tuning_suggestions,
        "sql_patch": sql_patch,
        "refresh_hint": refresh_hint,
        "structured_hit": structured_hit,
        "repair_mode": repair_mode,
        "logic_proposal": logic_proposal,
        "llm_meta": {
            "elapsed_ms": llm_elapsed_ms,
            "approx_tokens": llm_approx_tokens,
        },
        "llm_raw": raw,
        "prompt": prompt,
        "physics_tensor": physics_tensor,
    }


@router.post("/v1/final-verdict", response_model=dict)
async def final_verdict(body: FinalVerdictRequest) -> dict:
    consensus_history = list(body.consensus_history or [])
    if body.consultation_id and not consensus_history:
        try:
            with session_scope() as s:
                rows = s.exec(select(SessionConsensus).where(SessionConsensus.session_id == body.consultation_id)).all()
                consensus_history = [
                    {
                        "decision_key": str(r.decision_key or ""),
                        "confirmed_value": float(r.confirmed_value) if r.confirmed_value is not None else None,
                        "reasoning": str(r.reasoning or ""),
                    }
                    for r in rows
                ]
        except Exception:
            consensus_history = []

    skill = FinalVerdictSkill.instance()
    out = await skill.generate(
        metadata=body.metadata or {},
        physics_tensor=body.physics_tensor or {},
        selected_cards=body.selected_cards or [],
        consensus_history=consensus_history,
        previous_verdict=body.previous_verdict or "",
        previous_logical_evidence=body.previous_logical_evidence or [],
        lang=body.lang,
    )
    return {
        "ok": True,
        "version_id": out.get("version_id"),
        "verdict_body": out.get("verdict_body"),
        "change_log": out.get("change_log", []),
        "logical_evidence": out.get("logical_evidence", []),
    }
