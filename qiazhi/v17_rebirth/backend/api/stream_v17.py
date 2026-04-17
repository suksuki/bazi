from __future__ import annotations

import json
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator

router = APIRouter(tags=["v17"])


def _default_payload() -> Dict[str, Any]:
    return {
        "deity_scores": {"正官": 51.34, "食神": 20.1, "比肩": 8.9, "偏印": 5.4},
        "facts": [
            "五行火旺，结构张力上扬",
            "正官牵引秩序诉求增强",
            "外部压力触发自我收束",
        ],
    }


def _safe_parse_birth_time(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        # Accept "Z" suffix for web clients.
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pillar(stems: List[str], branches: List[str], idx: int) -> str:
    return f"{stems[idx % len(stems)]}{branches[idx % len(branches)]}"


def _run_v17_physics_core(*, birth_time: datetime | None, gender: str | None) -> Dict[str, Any]:
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    dt = birth_time or datetime.utcnow()
    gender_norm = "male" if str(gender or "").lower() == "male" else "female"

    year_idx = dt.year
    month_idx = dt.year * 12 + dt.month
    day_idx = dt.toordinal()
    hour_idx = day_idx * 12 + (dt.hour // 2)
    four_pillars = {
        "year": _pillar(stems, branches, year_idx),
        "month": _pillar(stems, branches, month_idx),
        "day": _pillar(stems, branches, day_idx),
        "hour": _pillar(stems, branches, hour_idx),
    }

    base = {
        "正官": 28.0 + (dt.month % 6) * 3.2,
        "食神": 16.0 + (dt.day % 7) * 2.4,
        "比肩": 10.0 + (dt.hour % 6) * 2.1,
        "偏印": 8.0 + (dt.year % 5) * 1.8,
        "正财": 12.0 + (dt.month % 4) * 2.0,
    }
    if gender_norm == "male":
        base["正官"] += 2.2
        base["比肩"] += 1.3
    else:
        base["食神"] += 2.0
        base["正财"] += 1.1

    scores = {k: round(v, 2) for k, v in base.items()}
    ten_gods = [k for k, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:4]]
    facts = [
        f"四柱落位：年{four_pillars['year']} 月{four_pillars['month']} 日{four_pillars['day']} 时{four_pillars['hour']}",
        f"十神主轴：{'、'.join(ten_gods)}",
        "命局主线已进入 V17 叙事织造阶段",
    ]
    return {
        "deity_scores": scores,
        "facts": facts,
        "four_pillars": four_pillars,
        "ten_gods": ten_gods,
        "gender": gender_norm,
        "birth_time": dt.isoformat(),
    }


async def _stream_frames(*, will_proxy: str, payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    orchestrator = VerdictOrchestrator()
    raw_physics = payload if isinstance(payload, dict) else {}
    facts = payload.get("facts") if isinstance(payload.get("facts"), list) else []
    # Frame 0: SNAPSHOT
    snap = orchestrator.snapshot_frame(raw_physics=raw_physics)
    yield (json.dumps(snap, ensure_ascii=False) + "\n").encode("utf-8")
    # Frame 1..N: NARRATOR
    async for frame in orchestrator.narrator_frames(
        raw_physics=raw_physics,
        facts=[str(x) for x in facts if str(x).strip()],
        will_proxy=will_proxy,
    ):
        yield (json.dumps(frame, ensure_ascii=False) + "\n").encode("utf-8")


@router.get("/v17/stream")
@router.get("/api/v17/stream")
async def stream_v17(
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: str | None = Query(default=None),
    gender: str | None = Query(default="female", pattern="^(male|female)$"),
) -> StreamingResponse:
    physics_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(birth_time),
        gender=gender,
    )
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=physics_payload),
        media_type="application/x-ndjson",
    )


@router.post("/v17/stream")
@router.post("/api/v17/stream")
async def stream_v17_post(
    payload: Dict[str, Any],
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: str | None = Query(default=None),
    gender: str | None = Query(default="female", pattern="^(male|female)$"),
) -> StreamingResponse:
    merged_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(birth_time),
        gender=gender,
    )
    if isinstance(payload, dict):
        merged_payload.update(payload)
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=merged_payload if isinstance(merged_payload, dict) else _default_payload()),
        media_type="application/x-ndjson",
    )
