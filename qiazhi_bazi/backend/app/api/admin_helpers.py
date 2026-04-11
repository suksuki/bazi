"""Helper functions for admin endpoints."""
from __future__ import annotations

import ipaddress
import logging
import os
import re
from typing import Any, Dict, List
from urllib.parse import urlparse, urlunparse

from fastapi import HTTPException

from app.skills.physics_rules import DEFAULT_INTERACTION_PARAMS

logger = logging.getLogger(__name__)

_ALLOWED_PHYSICS_PARAM_KEYS = frozenset(DEFAULT_INTERACTION_PARAMS.keys())


def strip_reasoning(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        logger.warning("strip_reasoning empty_input")
        return ""
    anchors = [
        "Final Answer:",
        "Answer:",
        "최종 결론:",
        "최종 답변:",
        "결론:",
        "판정:",
        "요약:",
        "最终回答：",
        "最终结论：",
        "结论：",
    ]
    for anchor in anchors:
        index = text.rfind(anchor)
        if index >= 0:
            return text[index + len(anchor):].strip()
    lower = text.lower()
    if (
        text.startswith("Thinking Process:")
        or text.startswith("思考过程")
        or "thinking process" in lower
        or "reasoning" in lower
        or "사고 과정" in text
    ):
        logger.warning("strip_reasoning blocked_reasoning_keywords")
        return ""
    if "thinking" not in lower and "reasoning" not in lower and len(text) < 200:
        return text
    cleaned = re.sub(r"^Thinking Process:\s*", "", text, flags=re.IGNORECASE)
    compact = cleaned.strip()
    if not compact:
        logger.warning("strip_reasoning empty_after_cleanup")
    return compact


def hard_compact_conclusion(text: str, max_len: int = 120) -> str:
    compact = (text or "").strip()
    if not compact:
        return ""
    lines = [line.strip() for line in compact.splitlines() if line.strip() and not line.strip().startswith("#")]
    plain = " ".join(lines)
    for separator in ["。", "！", "?", "？", "."]:
        index = plain.find(separator)
        if 0 < index < max_len:
            return plain[: index + 1]
    return plain[:max_len]


def allowed_hosts() -> set[str]:
    raw = os.getenv("QIAZHI_ALLOWED_HOSTS", "127.0.0.1,localhost,192.168.0.10")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def validate_target_url(raw_url: str, scheme_allow: set[str]) -> None:
    parsed = urlparse(raw_url)
    if parsed.scheme not in scheme_allow:
        raise HTTPException(status_code=400, detail=f"不允许的 URL 协议: {parsed.scheme}")
    if parsed.scheme == "sqlite":
        raise HTTPException(status_code=400, detail="禁止 SQLite。仅允许 PostgreSQL。")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL 缺少主机名")
    host = parsed.hostname.lower()
    allowed = allowed_hosts()
    if host in allowed:
        return
    try:
        ip = ipaddress.ip_address(host)
        if str(ip) in allowed:
            return
    except ValueError:
        pass
    raise HTTPException(status_code=403, detail=f"目标主机未在白名单内: {host}")


def masked_db_url(raw_url: str) -> str:
    try:
        parsed = urlparse(raw_url)
        if parsed.password:
            netloc = parsed.netloc.replace(parsed.password, "***")
            return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    except Exception:
        pass
    return raw_url


def parse_allowed_param_update(sql_patch: str) -> tuple[str, float]:
    raw = (sql_patch or "").strip().rstrip(";")
    pattern = re.compile(
        r"^UPDATE\s+physics_interaction_params\s+SET\s+param_value\s*=\s*([0-9]*\.?[0-9]+)\s+WHERE\s+param_key\s*=\s*'([A-Za-z0-9_]+)'$",
        re.IGNORECASE,
    )
    match = pattern.match(raw)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="仅允许格式：UPDATE physics_interaction_params SET param_value=<number> WHERE param_key='<KEY>';",
        )
    value = float(match.group(1))
    key = match.group(2)
    if key not in _ALLOWED_PHYSICS_PARAM_KEYS:
        raise HTTPException(status_code=400, detail=f"不允许更新参数: {key}")
    if not (0.0 <= value <= 2.0):
        raise HTTPException(status_code=400, detail=f"参数值越界: {value}（允许范围 0.0~2.0）")
    return key, value


def jsonb_check_payload(*, latency_ms: float, url: str, counts: Dict[str, Any], recent_raw_data: List[Any], jsonb_columns: List[str]) -> Dict[str, Any]:
    return {
        "ok": True,
        "db_url": masked_db_url(url),
        "latency_ms": latency_ms,
        "counts": counts,
        "recent_raw_data": recent_raw_data,
        "jsonb_check": {
            "decision_step_jsonb_columns": jsonb_columns,
            "ok": set(jsonb_columns) == {"raw_data", "human_choice"},
        },
    }
