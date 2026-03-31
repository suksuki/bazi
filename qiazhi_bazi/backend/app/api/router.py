"""API：健康检查、示例 BaziMetadata、LLM、决策链写入。"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.scanner import Scanner
from app.core.physics import calculate_clash_loss
from app.core.runtime_config import get_runtime_config
from app.db.session import session_scope
from app.db.models import Consultation, DecisionStep
from app.llm.client import QwenClient, build_first_observation_messages
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


@router.post("/decision-steps", response_model=dict)
def create_decision_step(body: DecisionStepCreate) -> dict:
    with session_scope() as s:
        step = DecisionStep(
            consultation_id=body.consultation_id,
            step_type=body.step_type,
            raw_data=body.raw_data,
            human_choice=body.human_choice,
        )
        s.add(step)
        s.flush()
        s.refresh(step)
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


class AnalyzeSeedRequest(BaseModel):
    date: str
    time: str = "12:00"
    calendar: str = "solar"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lang: str = "ZH"


class TranslateRequest(BaseModel):
    texts: List[str]
    target_lang: str = "ZH"


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
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    try:
        llm_text = await client.chat(
            build_first_observation_messages(metadata_obj.model_dump(), location_hint=location_hint, lang=body.lang),
            temperature=0.3,
            max_tokens=512,
            stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
        )
    except Exception:
        observed = [p.detail for p in metadata_obj.conflict_matrix.points]
        if not observed:
            llm_text = "我暂未观察到明显的冲合。我们是否继续做下一层扫描？"
        else:
            llm_text = (
                "我先汇报观察到的物理点：" + "、".join(observed) + "。"
                "我发现局部正在对撞/耦合，我们是否需要深入分析这个局部？"
            )

    return {
        "metadata": metadata_obj.model_dump(),
        "llm_prompt": llm_text,
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
        )
    )
    metadata = result["metadata"]
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
            "payload": {"pillars": metadata.get("pillars"), "conflicts": points},
        },
        {
            "step": "03",
            "role": "Auditor",
            "action": "基于物理冲突，生成初级判词与诱导问句。",
            "relay_to": "Arbiter",
            "timestamp": _now_iso(),
            "payload": {"llm_prompt": result["llm_prompt"]},
        },
    ]
    result["audit_summary"] = trail
    result["timeline"] = timeline
    return result
