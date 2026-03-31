"""Qiazhi-Bazi API：MVP 路由（协议 + 墓库 + LLM 连通）。"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from qiazhi_core.bridge.legacy_adapter import get_vault_params_snapshot, legacy_config_version
from qiazhi_core.llm.client import QwenClient
from qiazhi_core.plugins.storehouse import (
    ArbiterChoice,
    StorehouseEvaluation,
    StorehousePhase,
    evaluate_storehouse,
    map_arbiter_to_phase,
    record_arbiter_decision,
)
from qiazhi_core.schemas.protocol import BaziMetadata, SemanticFeature

router = APIRouter(tags=["qiazhi-bazi"])


class StorehouseEvaluateIn(BaseModel):
    energy_storage: float = Field(..., description="储能标量，与 config.vault.threshold 比较")
    branch_has_clash: bool = False
    branch_has_effective_punishment: bool = False
    earth_branch_code: str = ""


class StorehouseEvaluateOut(BaseModel):
    system_phase: str
    needs_arbitration: bool
    narrative_zh: str
    semantic_features: List[Dict[str, Any]]
    vault_config_snapshot: Dict[str, Any]


@router.post("/storehouse/evaluate", response_model=StorehouseEvaluateOut)
def post_storehouse_evaluate(body: StorehouseEvaluateIn) -> StorehouseEvaluateOut:
    ev: StorehouseEvaluation = evaluate_storehouse(
        energy_storage=body.energy_storage,
        branch_has_clash=body.branch_has_clash,
        branch_has_effective_punishment=body.branch_has_effective_punishment,
        earth_branch_code=body.earth_branch_code,
    )
    return StorehouseEvaluateOut(
        system_phase=ev.system_phase.value,
        needs_arbitration=ev.needs_arbitration,
        narrative_zh=ev.narrative_zh,
        semantic_features=ev.semantic_features,
        vault_config_snapshot=get_vault_params_snapshot(),
    )


class StorehouseDecisionIn(BaseModel):
    session_id: str
    system_suggested: str
    arbiter_choice: str = Field(..., description="sealed | open | collapse")
    note: str = ""


class StorehouseDecisionOut(BaseModel):
    recorded: Dict[str, Any]
    resolved_phase: str


@router.post("/storehouse/decision", response_model=StorehouseDecisionOut)
def post_storehouse_decision(body: StorehouseDecisionIn) -> StorehouseDecisionOut:
    suggested = StorehousePhase(body.system_suggested)
    choice = ArbiterChoice(body.arbiter_choice)
    row = record_arbiter_decision(
        session_id=body.session_id,
        system_suggested=suggested,
        arbiter_choice=choice,
        note=body.note,
    )
    resolved = map_arbiter_to_phase(choice)
    return StorehouseDecisionOut(recorded=row, resolved_phase=resolved.value)


class MetadataSampleOut(BaseModel):
    metadata: BaziMetadata


@router.get("/demo/metadata", response_model=MetadataSampleOut)
def get_demo_metadata() -> MetadataSampleOut:
    ev = evaluate_storehouse(
        energy_storage=25.0,
        branch_has_clash=True,
        branch_has_effective_punishment=False,
        earth_branch_code="辰",
    )
    feats = [
        SemanticFeature(
            code=f["code"],
            title=f["title"],
            narrative=f["narrative"],
            level=f["level"],
            meta=f.get("meta") or {},
        )
        for f in ev.semantic_features
    ]
    meta = BaziMetadata(
        basic_info={"pillars": {}, "gender": None, "longitude": None, "latitude": None},
        energy_profile={"labels": {}, "raw_scores": {}},
        clash_combinations=[],
        features=feats,
        semantic_refs=[ev.vault_config_ref],
        engine_trace={"legacy_config_version": legacy_config_version()},
    )
    return MetadataSampleOut(metadata=meta)


class ChatIn(BaseModel):
    messages: List[Dict[str, str]]


@router.post("/llm/chat")
async def llm_chat(body: ChatIn) -> Dict[str, Any]:
    client = QwenClient()
    content = await client.chat(body.messages)
    return {"content": content}


@router.post("/llm/stream")
async def llm_stream(body: ChatIn):
    client = QwenClient()

    async def _event_stream():
        async for token in client.stream_chat(body.messages):
            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@router.get("/health")
def qiazhi_health() -> Dict[str, Any]:
    return {
        "service": "Qiazhi-Bazi",
        "legacy_config": legacy_config_version(),
        "vault": get_vault_params_snapshot(),
    }
