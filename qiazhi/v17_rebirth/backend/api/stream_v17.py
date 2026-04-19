from __future__ import annotations

import json
import asyncio
import fcntl
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from v17_rebirth.paths import RUNTIME_DIR

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse

from v17_rebirth.infrastructure.stream_interrupt import ActionInterruptDuringStream
from v17_rebirth.infrastructure.state_backend import get_state_backend

from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator
from v17_rebirth.backend.infrastructure.evolution_db import evolution_storage
from v17_rebirth.backend.services.physics_layers import sync_runtime_aliases
from v17_rebirth.backend.services.target_god_resolver import resolve_target_god
from v17_rebirth.backend.services.decision_brain_protocol import DecisionBrainPlan, build_plan_claim
from v17_rebirth.backend.services.llm_prompt_contracts import build_plan_prompt_text
from v17_rebirth.backend.services.decision_batches import build_decision_batches
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER

router = APIRouter(tags=["v17"])
_WILL_IMPACT_BUFFER: List[Dict[str, Any]] = []
_ACTION_SEQ = 0
_FREEZE_FILE = RUNTIME_DIR / "v17_causal_reports.json"
# V17.23-Red：_SESSION_QUEUES 已迁移到 StateBackend.subscribe_actions/publish_action
# V17.20：六柱与流年锚点仅允许由服务端 physics core 写入，禁止 POST Body 覆盖。
_PHYS_SSOT_KEYS = frozenset({"four_pillars", "luck_pillar", "flow_pillar", "flow_year"})
_DECISION_BRAIN_KEY = "decision_brain_state"
_PLAN_QUEUE_KEY = "plan_queue"
_PLAN_MAX_QUEUE = 96
_PLAN_AUTO_APPROVE_MAX_COUNT = 8
_PLAN_AUTO_APPROVE_MAX_RATIO = 0.18
_PLAN_AUTO_APPROVE_MAX_SUM = 1.0


_log = logging.getLogger(__name__)


def _warn_if_multi_worker() -> None:
    """V17.23：进程内 Queue / PhysicsService 在 multi-worker 下无法共享，启动时告警。"""
    concurrency = str(os.getenv("WEB_CONCURRENCY", "") or "").strip()
    workers_arg = str(os.getenv("UVICORN_WORKERS", "") or "").strip()
    try:
        if (concurrency and int(concurrency) > 1) or (workers_arg and int(workers_arg) > 1):
            _log.warning(
                "[V17-CRITICAL] Multi-worker mode detected (WEB_CONCURRENCY=%s / UVICORN_WORKERS=%s). "
                "_SESSION_QUEUES and _SESSION_PHYSICS are in-process only — "
                "Action signals WILL NOT reach streams in other workers. "
                "Mitigation: set --workers 1, or migrate queues to Redis Pub/Sub.",
                concurrency, workers_arg,
            )
    except (TypeError, ValueError):
        pass


_warn_if_multi_worker()




def _v17_api_secret() -> str:
    """
    V17.23：从环境变量读取 API 密钥。
    生产环境建议设置 QIAZHI_V17_API_SECRET 为一个随机高强度字符串。
    未设置时退化为默认字符串（开发兼容）。
    """
    return str(os.getenv("QIAZHI_V17_API_SECRET", "v17_rebirth") or "v17_rebirth").strip()


def _sovereignty_v17(origin: Optional[str]) -> bool:
    """校验 v17_origin / X-V17-Origin 头是否与当前密钥匹配。"""
    return str(origin or "").strip() == _v17_api_secret()


def _default_payload() -> Dict[str, Any]:
    scores = {"正官": 51.34, "食神": 20.1, "比肩": 8.9, "偏印": 5.4}
    return {
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "deity_scores": dict(scores),
        "ten_gods_absolute_intensity": dict(scores),
        "ten_gods_absolute": dict(scores),
        "total_energy_index": 85.74,
        "facts": [
            "五行火旺，结构张力上扬",
            "正官牵引秩序诉求增强",
            "外部压力触发自我收束",
        ],
    }


def _sync_append_freeze_report(entry: Dict[str, Any]) -> str:
    """同步写入（在 asyncio.to_thread 中执行），带 fcntl 文件锁避免并发写入竞争。"""
    _FREEZE_FILE.parent.mkdir(parents=True, exist_ok=True)
    rid = f"v17r_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    with open(_FREEZE_FILE, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.seek(0)
            raw = fh.read()
            rows: List[Dict[str, Any]] = []
            if raw.strip():
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        rows = [x for x in parsed if isinstance(x, dict)]
                except Exception:
                    rows = []
            rows.append({"report_id": rid, **entry})
            rows = rows[-300:]
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps(rows, ensure_ascii=False, indent=2))
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    return rid


async def _append_freeze_report(entry: Dict[str, Any]) -> str:
    """async 包装：将同步文件 I/O 卓罴到线程池，不阻塞事件循环。"""
    return await asyncio.to_thread(_sync_append_freeze_report, entry)


def _safe_parse_birth_time(value: Optional[str]) -> Optional[datetime]:
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


def _should_rebuild_physics_core(
    *,
    current_physics: Dict[str, Any] | None,
    birth_time: Optional[str],
    gender: Optional[str],
    flow_year: Optional[int],
) -> bool:
    current = current_physics if isinstance(current_physics, dict) else {}
    if not current:
        return True

    if flow_year is not None:
        try:
            current_flow_year = int(current.get("flow_year")) if current.get("flow_year") is not None else None
        except (TypeError, ValueError):
            current_flow_year = None
        if current_flow_year != int(flow_year):
            return True

    if gender is not None:
        current_gender = str(current.get("gender") or "").strip().lower() or None
        request_gender = str(gender or "").strip().lower() or None
        if current_gender != request_gender:
            return True

    if birth_time is not None:
        current_birth = str(current.get("birth_time") or "").strip() or None
        parsed_request = _safe_parse_birth_time(birth_time)
        request_birth = parsed_request.isoformat() if parsed_request is not None else str(birth_time or "").strip() or None
        if current_birth != request_birth:
            return True

    return False


def _pillar(stems: List[str], branches: List[str], idx: int) -> str:
    return f"{stems[idx % len(stems)]}{branches[idx % len(branches)]}"


def _pillars_from_lunar(*, birth_time: datetime, gender: Optional[str], flow_year: int) -> Tuple[Dict[str, str], str, str]:
    """
    与 legacy BaziProfile 一致：使用 lunar_python 排四柱；流年用年中点规避立春边界；
    大运按 lunar 大运表匹配 flow_year（起运前空干支则顺延至首个有效大运）。
    """
    from lunar_python import Lunar, Solar

    lunar = Lunar.fromDate(birth_time)
    ec = lunar.getEightChar()
    four_pillars = {
        "year": str(ec.getYear() or ""),
        "month": str(ec.getMonth() or ""),
        "day": str(ec.getDay() or ""),
        "hour": str(ec.getTime() or ""),
    }

    gender_code = 1 if str(gender or "").lower() == "male" else 0
    yun = ec.getYun(gender_code)
    luck_pillar = "—"
    for dy in yun.getDaYun():
        sy, ey = int(dy.getStartYear()), int(dy.getEndYear())
        if sy <= flow_year <= ey:
            gz = dy.getGanZhi()
            if isinstance(gz, str) and len(gz.strip()) >= 2:
                luck_pillar = gz.strip()
                break
    if luck_pillar == "—":
        for dy in yun.getDaYun():
            gz = dy.getGanZhi()
            if not (isinstance(gz, str) and len(gz.strip()) >= 2):
                continue
            sy = int(dy.getStartYear())
            if flow_year < sy:
                luck_pillar = gz.strip()
                break

    solar = Solar.fromYmd(int(flow_year), 6, 15)
    ygz = solar.getLunar().getYearInGanZhi()
    flow_pillar = str(ygz).strip() if ygz else "—"

    return four_pillars, luck_pillar, flow_pillar


def _run_v17_physics_core(
    *,
    birth_time: Optional[datetime],
    gender: Optional[str],
    flow_year: Optional[int] = None,
) -> Dict[str, Any]:
    from datetime import timezone as _tz
    from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores

    _stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    _branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    dt = birth_time or datetime(1977, 5, 8, 18, 0, 0)
    gender_norm = "male" if str(gender or "").lower() == "male" else "female"
    fy = int(flow_year) if flow_year is not None else datetime.now().year

    luck_pillar = "—"
    flow_pillar = "—"
    try:
        four_pillars, luck_pillar, flow_pillar = _pillars_from_lunar(birth_time=dt, gender=gender, flow_year=fy)
    except Exception:
        year_idx = dt.year
        month_idx = dt.year * 12 + dt.month
        day_idx = dt.toordinal()
        hour_idx = day_idx * 12 + (dt.hour // 2)
        four_pillars = {
            "year": _pillar(_stems, _branches, year_idx),
            "month": _pillar(_stems, _branches, month_idx),
            "day": _pillar(_stems, _branches, day_idx),
            "hour": _pillar(_stems, _branches, hour_idx),
        }

    # 真实十神分值：基于日主干支阴阳五行生克关系（L0 层 ten_gods_engine）
    scores, ten_gods, total_energy_index, energy_meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        gender=gender_norm,
        birth_time=dt,
    )
    facts = [
        {
            "fact": f"四柱落位：年{four_pillars['year']} 月{four_pillars['month']} 日{four_pillars['day']} 时{four_pillars['hour']}",
            "weight": 0.98,
            "tier": 0,
        },
        {
            "fact": f"大运（{fy}）：{luck_pillar}；流年：{flow_pillar}",
            "weight": 0.96,
            "tier": 0,
        },
        {
            "fact": f"十神主轴：{'、'.join(ten_gods)}",
            "weight": 0.82,
            "tier": 1,
        },
        {
            "fact": "命局主线已进入 V17 叙事织造阶段",
            "weight": 0.52,
            "tier": 2,
        },
    ]
    # V17.32: 序列化 Evolution Ledger（从 EvolutionLedger 对象转为 JSON-safe dict）
    from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
    raw_ledger = energy_meta.pop("ledger", None)
    ten_gods_ledger = raw_ledger.to_dict() if isinstance(raw_ledger, EvolutionLedger) else {}

    payload = {
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "total_energy_index": total_energy_index,
        "energy_meta": energy_meta,
        "ten_gods_ledger": ten_gods_ledger,
        "facts": facts,
        "four_pillars": four_pillars,
        "luck_pillar": luck_pillar,
        "flow_pillar": flow_pillar,
        "flow_year": fy,
        "ten_gods": ten_gods,
        "gender": gender_norm,
        "birth_time": dt.isoformat(),
    }
    sync_runtime_aliases(payload, scores)
    return payload


def _safe_plan_ids(raw_ids: Any) -> List[str]:
    if isinstance(raw_ids, str):
        raw_ids = [raw_ids]
    if not isinstance(raw_ids, list):
        return []
    out: List[str] = []
    for item in raw_ids:
        sid = str(item or "").strip()
        if sid and sid not in out:
            out.append(sid)
    return out


def _is_plan_terminal(status: str) -> bool:
    normalized = str(status or "").strip().upper()
    return normalized in {"COMMITTED", "REJECTED", "FAILED", "DONE"}


def _are_decisions_settled(rows: List[Dict[str, Any]]) -> bool:
    if not rows:
        return False
    terminal_states = {"APPROVED", "REJECTED", "COMMITTED", "FAILED", "DONE"}
    for row in rows:
        if str(row.get("status") or "").strip().upper() not in terminal_states:
            return False
    return True


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _build_plan_claim(*, routing: str, routing_reason: str, routing_features: Dict[str, Any]) -> Dict[str, Any]:
    claim = build_plan_claim(
        routing=routing,
        routing_reason=routing_reason,
        routing_features={
            "decision_count": int(routing_features.get("decision_count") or 0),
            "conflict_pairs": int(routing_features.get("conflict_pairs") or 0),
            "duplicate_events": int(routing_features.get("duplicate_events") or 0),
            "max_abs_ratio": _safe_float(routing_features.get("max_abs_ratio"), 0.0),
            "total_abs_ratio": _safe_float(routing_features.get("total_abs_ratio"), 0.0),
        },
    )
    claim["routing_reason"] = routing_reason
    return claim


def _decision_route_reason(payload: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    explicit = str(payload.get("routing") or payload.get("route") or payload.get("routing_hint") or "").strip().lower()
    if explicit in {"system", "llm", "user"}:
        routing_reason = "payload routing_hint has explicit route"
        routing_features = {}
        return {
            "routing": explicit,
            "routing_reason": routing_reason,
            "routing_policy": "explicit_payload_routing",
            "routing_features": routing_features,
            "routing_claim": _build_plan_claim(
                routing=explicit,
                routing_reason=routing_reason,
                routing_features=routing_features,
            ),
        }

    total_abs = 0.0
    max_abs = 0.0
    conflict_pairs = 0
    duplicate_events = 0
    target_by_sign: Dict[str, set[float]] = {}
    exclusivity_count: Dict[str, int] = {}
    decision_count = len(rows)

    for row in rows:
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        ratio = _safe_float(impact.get("impact_ratio", 0.0), 0.0)
        abs_ratio = abs(ratio)
        total_abs += abs_ratio
        max_abs = max(max_abs, abs_ratio)

        target = str(row.get("target_god") or impact.get("target_god") or "").strip() or "untargeted"
        target_by_sign.setdefault(target, set()).add(-1.0 if ratio < 0 else 1.0 if ratio > 0 else 0.0)

        event_key = str(row.get("exclusivity_key") or row.get("source_event") or "").strip()
        if event_key:
            exclusivity_count[event_key] = exclusivity_count.get(event_key, 0) + 1

        text = str(row.get("label") or row.get("title") or row.get("hint") or "").strip()
        if any(keyword in text for keyword in ("格局", "坍塌", "翻盘", "断裂", "冲", "刑", "害", "破", "夺", "离", "转化")):
            total_abs += 0.03

    for value in target_by_sign.values():
        signs = {item for item in value if item != 0.0}
        if len(signs) >= 2:
            conflict_pairs += 1

    duplicate_events = sum(1 for count in exclusivity_count.values() if count > 1)
    conflict_signal = conflict_pairs > 0 or duplicate_events > 0
    ratio_sum = _safe_float(sum(_safe_float((row.get("physical_impact") or {}).get("impact_ratio", 0.0), 0.0) for row in rows), 0.0)

    if not conflict_signal and decision_count <= _PLAN_AUTO_APPROVE_MAX_COUNT and max_abs <= _PLAN_AUTO_APPROVE_MAX_RATIO and abs(ratio_sum) <= _PLAN_AUTO_APPROVE_MAX_SUM:
        routing = "system"
        reason = "low risk and低冲突批次，系统可自动执行"
    elif not conflict_signal and max_abs <= max(_PLAN_AUTO_APPROVE_MAX_RATIO * 1.8, 0.25):
        routing = "llm"
        reason = "中等风险批次，先交由模型进行价值校验"
    else:
        routing = "user"
        reason = "高风险/冲突批次，建议人工裁定"

    routing_features = {
        "decision_count": decision_count,
        "conflict_pairs": conflict_pairs,
        "duplicate_events": duplicate_events,
        "max_abs_ratio": round(max_abs, 4),
        "total_abs_ratio": round(total_abs, 4),
        "net_ratio": round(ratio_sum, 4),
    }

    return {
        "routing": routing,
        "routing_reason": reason,
        "routing_policy": "local_batch_heuristic",
        "routing_features": routing_features,
        "routing_claim": _build_plan_claim(
            routing=routing,
            routing_reason=reason,
            routing_features=routing_features,
        ),
    }


def _build_llm_plan_prompt(*, rows: List[Dict[str, Any]], action: str, anchor: str) -> str:
    if not rows:
        return "未检测到可执行候选，无法生成批量提示词。"
    return build_plan_prompt_text(rows=rows, action=action, anchor=anchor, max_rows=16)


def _safe_decision_label(row: Dict[str, Any]) -> str:
    return str(row.get("label") or row.get("title") or row.get("hint") or row.get("id") or "").strip()


def _safe_decision_trace(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build compact evidence bundles so plan 结算过程可追溯，不依赖 LLM 回答文本。"""
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        label = _safe_decision_label(row)
        if not label and not str(row.get("id") or "").strip():
            continue
        target = str(
            row.get("target_god")
            or (row.get("physical_impact") or {}).get("target_god")
            or ""
        ).strip()
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        try:
            impact_ratio = float(impact.get("impact_ratio", 0.0) or 0.0)
        except (TypeError, ValueError):
            impact_ratio = 0.0
        try:
            priority = float(row.get("priority", 0.0) or 0.0)
        except (TypeError, ValueError):
            priority = 0.0
        out.append(
            {
                "trace_index": idx,
                "decision_id": str(row.get("id") or f"row_{idx}").strip(),
                "label": label,
                "source": str(row.get("source") or row.get("plugin_id") or "unknown").strip(),
                "target_god": target,
                "impact_ratio": round(impact_ratio, 6),
                "priority": round(priority, 6),
                "exclusivity_key": str(row.get("exclusivity_key") or "").strip(),
                "routing_hint": str(row.get("arbiter_type") or "user").strip(),
                "source_event": str(row.get("source_event") or "").strip(),
            }
        )
    return out


def _boolish(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    raw = str(value).strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _build_physics_sync_payload(pt: Dict[str, Any]) -> Dict[str, Any]:
    auto_resolutions = [dict(x) for x in pt.get("auto_resolutions", []) if isinstance(x, dict)]
    llm_arbitration_context = [dict(x) for x in pt.get("llm_arbitration_context", []) if isinstance(x, dict)]
    auto_decisions = [dict(x) for x in pt.get("auto_decisions", []) if isinstance(x, dict)]
    if not auto_decisions:
        auto_decisions = [*auto_resolutions, *llm_arbitration_context]
    payload: Dict[str, Any] = {
        "type": "PHYSICS_SYNC",
        "decision_inbox_contract": str(pt.get("decision_inbox_contract") or "v17.decision.inbox.v2"),
        "pending_decisions": [dict(x) for x in pt.get("pending_decisions", []) if isinstance(x, dict)],
        "manual_decisions": [dict(x) for x in pt.get("manual_decisions", []) if isinstance(x, dict)],
        "manual_inbox": [dict(x) for x in pt.get("manual_decisions", []) if isinstance(x, dict)],
        "auto_decisions": auto_decisions,
        "auto_resolutions": auto_resolutions,
        "llm_arbitration_context": llm_arbitration_context,
        "decision_brain_state": dict(pt.get("decision_brain_state") or {}),
        "decision_batches": [dict(x) for x in pt.get("decision_batches_cache", []) if isinstance(x, dict)],
    }
    return payload


def _event_for_publish(event: Dict[str, Any], *, physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(event)
    request_verdict = _boolish(out.get("request_verdict"), default=True)
    if request_verdict:
        return out
    out["signal"] = "PHYSICS_SYNC"
    out["payload"] = _build_physics_sync_payload(physics_tensor)
    return out


def _read_plan_state(pt: Dict[str, Any]) -> Dict[str, Any]:
    raw = pt.get(_DECISION_BRAIN_KEY)
    if isinstance(raw, dict):
        plans = raw.get(_PLAN_QUEUE_KEY)
        if isinstance(plans, list):
            return {_PLAN_QUEUE_KEY: [dict(x) for x in plans if isinstance(x, dict)]}
    return {_PLAN_QUEUE_KEY: []}


def _find_plan_by_id(pt: Dict[str, Any], plan_id: str) -> Optional[Dict[str, Any]]:
    normalized = str(plan_id or "").strip()
    if not normalized:
        return None
    state = _read_plan_state(pt)
    rows = state.get(_PLAN_QUEUE_KEY)
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("plan_id") or "").strip() == normalized:
            return row
    return None


def _write_plan_state(pt: Dict[str, Any], *, plan: DecisionBrainPlan) -> None:
    state = _read_plan_state(pt)
    plans = state.get(_PLAN_QUEUE_KEY)
    if not isinstance(plans, list):
        plans = []
    replaced = False
    for idx, row in enumerate(plans):
        if str(row.get("plan_id") or "").strip() == str(plan.plan_id):
            plans[idx] = plan.to_dict()
            replaced = True
            break
    if not replaced:
        plans.insert(0, plan.to_dict())
    if len(plans) > _PLAN_MAX_QUEUE:
        plans = plans[:_PLAN_MAX_QUEUE]
    pt[_DECISION_BRAIN_KEY] = {_PLAN_QUEUE_KEY: plans}


def _pick_pending_decisions(pt: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = pt.get("pending_decisions")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    manual = pt.get("manual_decisions")
    if isinstance(manual, list):
        return [row for row in manual if isinstance(row, dict)]
    return []


def _index_pending_decisions(pt: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    rows = _pick_pending_decisions(pt)
    by_id: Dict[str, Dict[str, Dict[str, Any]]] = {}
    by_label: Dict[str, Dict[str, Dict[str, Any]]] = {}
    by_title: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in rows:
        rid = str(row.get("id") or "").strip()
        label = str(row.get("label") or row.get("title") or "").strip()
        title = str(row.get("title") or "").strip()
        if rid:
            by_id[rid] = row
        if label:
            by_label[label] = row
        if title:
            by_title[title] = row
    return {"id": by_id, "label": by_label, "title": by_title}


def _collect_matched_decisions(
    pt: Dict[str, Any],
    *,
    decision_ids: List[str] | None = None,
    decision_labels: List[str] | None = None,
) -> List[Dict[str, Any]]:
    ids = _safe_plan_ids(decision_ids or [])
    labels = _safe_plan_ids(decision_labels or [])
    if not ids and not labels:
        return []
    index = _index_pending_decisions(pt)
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _append(row: Dict[str, Any]) -> None:
        rid = str(row.get("id") or row.get("label") or row.get("title") or "").strip()
        if not rid or rid in seen:
            return
        seen.add(rid)
        out.append(row)

    for sid in ids:
        candidate = index["id"].get(sid)
        if candidate:
            _append(candidate)
        candidate = index["label"].get(sid)
        if candidate:
            _append(candidate)
        candidate = index["title"].get(sid)
        if candidate:
            _append(candidate)

    for lab in labels:
        candidate = index["label"].get(lab)
        if candidate:
            _append(candidate)
            continue
        candidate = index["title"].get(lab)
        if candidate:
            _append(candidate)
    return out


def _resolve_batch_decisions(pt: Dict[str, Any], batch_ids: List[str]) -> List[Dict[str, Any]]:
    if not batch_ids:
        return []
    cache = pt.get("decision_batches_cache")
    if not isinstance(cache, list):
        return []
    rows = []
    for item in cache:
        if not isinstance(item, dict):
            continue
        batch_id = str(item.get("batch_id") or "").strip()
        if batch_id not in batch_ids:
            continue
        rows.extend(_safe_plan_ids(item.get("decision_ids")))
    return _collect_matched_decisions(pt, decision_ids=rows)


def _impact_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, float] = {}
    for row in rows:
        impact = row.get("physical_impact")
        if not isinstance(impact, dict):
            impact = {}
        ratio = float(impact.get("impact_ratio", 0.0) or 0.0)
        target = str(row.get("target_god") or impact.get("target_god") or "untargeted").strip()
        out[target] = out.get(target, 0.0) + ratio
    return {key: round(value, 6) for key, value in out.items()}


def _seed_plan_from_payload(
    payload: Dict[str, Any],
    *,
    session_id: str,
    rows: List[Dict[str, Any]],
    signal: str,
) -> DecisionBrainPlan:
    route = _decision_route_reason(payload, rows) if signal == "PLAN_SUBMIT" else {}
    effective_routing = str(
        route.get("routing") or payload.get("routing") or payload.get("route") or "system"
    ).strip().lower()
    if effective_routing not in {"system", "llm", "user"}:
        effective_routing = "system"
    if signal in {"PLAN_APPROVE", "PLAN_REJECT", "PLAN_ESCALATE", "PLAN_WITHDRAW"} and effective_routing == "system":
        # 人工确认的 plan 按执行路径处理时，明确标记为 system，避免被后续策略误判成非执行。
        effective_routing = "system"
    action = str(payload.get("action") or "").strip()
    if not action and rows:
        action = str(rows[0].get("label") or rows[0].get("title") or "").strip()
    anchor = str(payload.get("anchor") or "").strip()
    if not anchor and rows:
        anchor = str(rows[0].get("exclusivity_key") or rows[0].get("source_event") or rows[0].get("source") or "").strip()
    if not anchor:
        anchor = str(payload.get("source") or "manual").strip() or "manual"
    decision_ids = _safe_plan_ids(payload.get("decision_ids"))
    if not decision_ids:
        decision_id = str(payload.get("decision_id") or "").strip()
        if decision_id:
            decision_ids.append(decision_id)
    if not decision_ids:
        decision_ids = [str(r.get("id") or r.get("label") or r.get("title") or "").strip() for r in rows if str(r.get("id") or r.get("label") or r.get("title") or "").strip()]
    status = "DRAFT"
    if signal == "PLAN_APPROVE":
        status = "APPROVED"
    elif signal == "PLAN_REJECT":
        status = "REJECTED"
    elif signal in {"PLAN_ESCALATE", "PLAN_WITHDRAW"}:
        status = "AWAIT_REVIEW"
    elif signal == "PLAN_SUBMIT":
        status = "AWAIT_REVIEW"
    return DecisionBrainPlan.from_dict(
        {
            "plan_id": str(payload.get("plan_id") or f"plan_{int(datetime.now(timezone.utc).timestamp() * 1000)}"),
            "anchor": anchor,
            "batch_ids": _safe_plan_ids(payload.get("batch_ids") or payload.get("batch_id")),
            "routing": effective_routing,
            "creator": str(payload.get("creator") or "user").strip() or "user",
            "status": status,
            "impact_summary": _impact_summary(rows),
            "residual_estimate": float(payload.get("residual_estimate") or 0.0),
            "meta": {
                "signal": signal,
                "action": action,
                "source": str(payload.get("source") or "oracle"),
                "rows": len(rows),
                "decision_ids": decision_ids,
                "routing_reason": route.get("routing_reason"),
                "routing_policy": route.get("routing_policy"),
                "routing_features": route.get("routing_features"),
                "routing_claim": route.get("routing_claim"),
                "decision_trace": _safe_decision_trace(rows),
                "decision_trace_contract": "v17.decision.trace.v1",
                "decision_count": len(rows),
            },
            "session_id": session_id,
        },
        session_id=session_id,
    )


def _mark_plan_decisions(
    pt: Dict[str, Any],
    rows: List[Dict[str, Any]],
    *,
    status: str,
    plan_id: str,
) -> None:
    row_ids = {str(r.get("id") or "").strip() for r in rows if str(r.get("id") or "").strip()}
    if not row_ids:
        return
    for name in ("pending_decisions", "manual_decisions"):
        section = pt.get(name)
        if not isinstance(section, list):
            continue
        for row in section:
            rid = str(row.get("id") or "").strip()
            if rid and rid in row_ids:
                row["status"] = status
                row["plan_id"] = plan_id


def _emit_decision_batch_cache(pt: Dict[str, Any]) -> None:
    arbitration = {
        "manual_decisions": [dict(x) for x in _pick_pending_decisions(pt)],
        "auto_resolutions": [dict(x) for x in pt.get("auto_resolutions", []) if isinstance(x, dict)],
        "llm_arbitration_context": [dict(x) for x in pt.get("llm_arbitration_context", []) if isinstance(x, dict)],
    }
    pt["decision_batches_cache"] = build_decision_batches(arbitration=arbitration).get("all", [])


def _normalize_plan_signal(payload_signal: str, status: str) -> str:
    direct = str(payload_signal or "").strip().upper()
    if direct in {"PLAN_SUBMIT", "PLAN_APPROVE", "PLAN_REJECT", "PLAN_ESCALATE", "PLAN_WITHDRAW"}:
        return direct
    if direct == "ACTION_TAKEN":
        if str(status or "").strip().upper() == "REJECTED":
            return "PLAN_REJECT"
        return "PLAN_APPROVE"
    return "PLAN_SUBMIT"

def _physical_void_stop_frame() -> Dict[str, Any]:
    """物理门控失败时唯一出帧：禁止 physics 快照与 LLM 抢跑。"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "layer": "SNAPSHOT",
        "payload": {
            "snapshot_kind": "physical_void",
            "render_text": "[圣殿警告] 物理因果缺失，叙事引擎已强行熄火。",
            "llm_meta": {
                "ok": False,
                "engine_state": "physical_void",
                "physics_guard": True,
            },
        },
    }


def _system_init_failure_stop_frame() -> Dict[str, Any]:
    """元数据未稳定（DataSovereigntyError）：禁止任何 NARRATOR 抢跑。"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "layer": "SNAPSHOT",
        "payload": {
            "snapshot_kind": "system_init_failure",
            "render_text": "系统初始化失败",
            "llm_meta": {
                "ok": False,
                "engine_state": "physics_metadata_unstable",
                "visibility_lock": True,
                "data_sovereignty": True,
            },
        },
    }


def _narrator_runtime_failure_frame(*, err: Exception, step_cursor: str = "") -> Dict[str, Any]:
    err_name = type(err).__name__
    err_text = str(err).strip()
    detail = f"{err_name}: {err_text}" if err_text else err_name
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "layer": "NARRATOR",
        "payload": {
            "render_text": f"[叙事协程异常中止] {detail}",
            "llm_meta": {
                "ok": False,
                "engine_state": "orchestrator_runtime_error",
                "error": detail,
                "step_position": str(step_cursor or "").strip(),
            },
        },
    }


def _is_terminal_narrator_frame(frame: Dict[str, Any]) -> bool:
    if str(frame.get("layer") or "").strip().upper() != "NARRATOR":
        return False
    payload = frame.get("payload") if isinstance(frame.get("payload"), dict) else {}
    llm_meta = payload.get("llm_meta") if isinstance(payload.get("llm_meta"), dict) else {}
    if llm_meta.get("ok") is False:
        return True
    try:
        return llm_meta.get("elapsed_ms") is not None and not bool(llm_meta.get("stream_partial"))
    except Exception:
        return False


async def _hydrate_physics_atomically(pl: Dict[str, Any]) -> None:
    """在发出任何 SNAPSHOT(physics) 之前，于线程中完成 meta 张量注水，与 HTTP 响应流解耦。"""

    def _sync() -> None:
        hydrate_v17_physics_tensor(pl)

    await asyncio.to_thread(_sync)


async def _self_heal_physics_if_missing(session_id: str, pl: Dict[str, Any]) -> bool:
    """
    Redis/StateBackend 读空时，现场同步重算一遍 physics core 并重新绑定，
    尽量吸收前端请求快于后端持久化的竞态。
    """
    backend = get_state_backend()
    current = await backend.get_physics(session_id)
    if isinstance(current, dict) and current:
        return False

    _log.warning(
        "[V17-HEAL] Session %s physics tensor missing in backend; forcing synchronous physics core rebuild",
        session_id,
    )
    raw_flow_year = pl.get("flow_year")
    try:
        healed_flow_year = int(raw_flow_year) if raw_flow_year is not None else None
    except (TypeError, ValueError):
        healed_flow_year = None
    healed_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(str(pl.get("birth_time") or "").strip() or None),
        gender=str(pl.get("gender") or "").strip() or None,
        flow_year=healed_flow_year,
    )
    pl.update(healed_payload)
    PhysicsService.prime_local_tensor(session_id, pl)
    await _hydrate_physics_atomically(pl)
    VerdictOrchestrator().assert_six_pillars_physics(pl)
    await PhysicsService.abind_session_tensor(session_id, pl)
    await PhysicsService.ensure_stability(session_id, local_physics=pl)
    return True


def _sse_heartbeat_sec() -> float:
    """编排协程超过该间隔未 yield 则下发 HEARTBEAT；默认 2s；可用 QIAZHI_V17_SSE_HEARTBEAT_SEC 覆盖。"""
    try:
        v = float(str(os.getenv("QIAZHI_V17_SSE_HEARTBEAT_SEC", "2.0") or "2.0").strip())
        return max(1.0, min(120.0, v))
    except (TypeError, ValueError):
        return 2.0


def _frame_step_cursor(frame: Dict[str, Any]) -> str:
    """从 NDJSON 帧推断当前步进标签，供 HEARTBEAT 携带。"""
    layer = str(frame.get("layer") or "")
    pl = frame.get("payload") if isinstance(frame.get("payload"), dict) else {}
    if layer == "SNAPSHOT":
        sk = str(pl.get("snapshot_kind") or "").strip()
        if sk == "system_init_failure":
            return "SNAPSHOT:system_init_failure"
        if sk == "physical_void":
            return "SNAPSHOT:physical_void"
        return f"SNAPSHOT:{sk}" if sk else "SNAPSHOT"
    if layer == "WILL_FLASH":
        return "WILL_FLASH:ACTION_TAKEN"
    if layer == "NARRATOR":
        lm = pl.get("llm_meta") if isinstance(pl.get("llm_meta"), dict) else {}
        beat = str(lm.get("叙事节拍") or lm.get("engine_state") or "").strip()
        if beat:
            return f"NARRATOR:{beat}"
        if lm.get("stream_partial") or lm.get("audit_preview"):
            return "NARRATOR:streaming_partial"
        return "NARRATOR:body"
    if layer == "HEARTBEAT":
        return str(pl.get("step_position") or "HEARTBEAT")
    return layer or "unknown"


def _heartbeat_status_frame(*, step_cursor: str, idle_sec: float, idle_beats: int) -> Dict[str, Any] | None:
    """长时间无正文时，补发一条可审计的 NARRATOR 状态帧，避免前端只能盲等 HEARTBEAT。"""
    step = str(step_cursor or "START").strip() or "START"
    if step.startswith("SNAPSHOT:llm_audit_preview") or step.startswith("NARRATOR:已联通"):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": "",
                "llm_meta": {
                    "stream_partial": True,
                    "engine_state": "awaiting_first_token",
                    "heartbeat_step": step,
                    "idle_sec": idle_sec,
                    "idle_beats": idle_beats,
                },
                "source_facts": [],
            },
        }
    if step.startswith("NARRATOR:streaming_partial"):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": "",
                "llm_meta": {
                    "stream_partial": True,
                    "engine_state": "stream_stalled",
                    "heartbeat_step": step,
                    "idle_sec": idle_sec,
                    "idle_beats": idle_beats,
                },
                "source_facts": [],
            },
        }
    return None


def _should_retry_premature_close(step_cursor: str, retry_count: int) -> bool:
    step = str(step_cursor or "").strip()
    if retry_count >= 1:
        return False
    return (
        step == "START"
        or step.startswith("SNAPSHOT:llm_audit_dispatch")
        or step.startswith("SNAPSHOT:llm_audit_preview")
        or step.startswith("NARRATOR:已联通")
    )


async def _narrator_with_heartbeat(
    agen: AsyncIterator[Dict[str, Any]],
) -> AsyncIterator[Dict[str, Any]]:
    """在 async for 迭代上包一层：超过间隔无帧则下发 HEARTBEAT（含步进位置），避免 SSE 被代理/浏览器静默掐断。"""
    sec = _sse_heartbeat_sec()
    it = agen.__aiter__()
    step_cursor = "START"
    idle_beats = 0
    next_task: asyncio.Task[Dict[str, Any]] | None = None
    while True:
        try:
            if next_task is None:
                next_task = asyncio.create_task(it.__anext__())
            done, _ = await asyncio.wait({next_task}, timeout=sec, return_when=asyncio.FIRST_COMPLETED)
            if not done:
                raise asyncio.TimeoutError()
            frame = next_task.result()
            next_task = None
        except StopAsyncIteration:
            next_task = None
            break
        except asyncio.TimeoutError:
            idle_beats += 1
            yield {
                "timestamp": datetime.utcnow().isoformat(),
                "layer": "HEARTBEAT",
                "payload": {"signal": "sse_tick", "idle_sec": sec, "step_position": step_cursor},
            }
            if idle_beats >= 2:
                status_frame = _heartbeat_status_frame(
                    step_cursor=step_cursor,
                    idle_sec=sec,
                    idle_beats=idle_beats,
                )
                if status_frame is not None:
                    yield status_frame
            continue
        step_cursor = _frame_step_cursor(frame)
        idle_beats = 0
        yield frame
    if next_task is not None:
        next_task.cancel()
        try:
            await next_task
        except Exception:
            pass


async def _stream_frames(*, will_proxy: str, payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    orchestrator = VerdictOrchestrator()
    pl = payload if isinstance(payload, dict) else {}
    session_id = str(pl.get("session_id", "")).strip() or "default"
    print(f"[V17-TRACE] Stream Request In: {session_id}", flush=True)

    # V17.24：Redis 活性探针——如果配置了 Redis 但连接失败，拒绝 SSE 启动（避免异常写入导致一系列下游报错）
    backend = get_state_backend()
    from v17_rebirth.infrastructure.state_backend import RedisStateBackend
    if isinstance(backend, RedisStateBackend):
        try:
            redis_ok = await backend.ping()
        except Exception:  # noqa: BLE001
            redis_ok = False
        if not redis_ok:
            _log.error("[V17-FATAL] Redis backend unreachable for session=%s — refusing SSE stream", session_id)
            yield (json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "layer": "SNAPSHOT",
                "payload": {
                    "snapshot_kind": "system_init_failure",
                    "render_text": "[V17-FATAL] Redis 连接丢失，请查看后端 8017 日志。",
                    "llm_meta": {"ok": False, "engine_state": "redis_unreachable"},
                },
            }, ensure_ascii=False) + "\n").encode("utf-8")
            await asyncio.sleep(0)
            return

    await _hydrate_physics_atomically(pl)
    PhysicsService.prime_local_tensor(session_id, pl)
    try:
        orchestrator.assert_six_pillars_physics(pl)
    except DataSovereigntyError:
        # V17.24：因果残影——找出当前张量内容（帮助判断是数据未写入还是写错了地方）
        _log.error(
            "[V17-FATAL] Session %s assert_six_pillars_physics FAILED. "
            "Current pl keys: %s  |  four_pillars: %s  |  luck_pillar: %s  |  flow_pillar: %s",
            session_id,
            list(pl.keys()),
            pl.get("four_pillars"),
            pl.get("luck_pillar"),
            pl.get("flow_pillar"),
        )
        yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    raw_physics = pl
    try:
        snap = orchestrator.snapshot_frame(
            raw_physics=raw_physics,
            session_id=session_id,
            causal_anchor="local_memory",
        )
    except DataSovereigntyError:
        yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    _log.warning("[Local-Snapshot] session=%s causal_anchor=local_memory", session_id)
    yield (json.dumps(snap, ensure_ascii=False) + "\n").encode("utf-8")
    await asyncio.sleep(0)
    # 第二动：Redis 锁定确认；未确认即视为主权失败
    try:
        await PhysicsService.abind_session_tensor(session_id, raw_physics)
    except DataSovereigntyError:
        _log.error("[V17-FATAL] Session %s Redis bind confirmation failed", session_id)
        yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
        await asyncio.sleep(0)
        return
    _log.warning("[Redis-Bind-Success] session=%s", session_id)
    try:
        await PhysicsService.ensure_stability(session_id, local_physics=raw_physics)
    except DataSovereigntyError:
        try:
            healed = await _self_heal_physics_if_missing(session_id, raw_physics)
        except DataSovereigntyError:
            healed = False
        if healed:
            _log.warning("[V17-HEAL] Session %s recovered after backend MISS", session_id)
        else:
            # V17.24：因果残影——展示 Redis 里实际存的 key
            try:
                tensor_keys = await PhysicsService.get_physics_keys(session_id)
            except Exception:  # noqa: BLE001
                tensor_keys = ["<failed to query>"]
            _log.error(
                "[V17-FATAL] Session %s tensor keys in backend: %s",
                session_id, tensor_keys,
            )
            yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
            await asyncio.sleep(0)
            return

    if _boolish(pl.get("suppress_narrator"), default=False):
        # Sync-only mode: emit physics snapshot and stop. Used by Decision Inbox
        # to refresh tensor/queue state without invoking LLM narration.
        _log.info("[V17-SYNC-ONLY] session=%s suppress_narrator=true", session_id)
        return

    facts = pl.get("facts") if isinstance(pl.get("facts"), list) else []
    # V17.99：从物理张量中提取全量案卷（跨 L1-L4）
    dec_raw = pl.get("pending_decisions") if isinstance(pl.get("pending_decisions"), list) else []
    if not dec_raw:
        dec_raw = pl.get("decisions") if isinstance(pl.get("decisions"), list) else []
    
    decisions_rows: List[Dict[str, Any]] = []
    for x in dec_raw:
        if not isinstance(x, dict):
            continue
        lab = str(x.get("label") or x.get("title") or "").strip()
        if lab:
            decisions_rows.append({"id": str(x.get("id") or "").strip(), "label": lab, "title": str(x.get("title") or "").strip()})
    narrative_role = V17_ROLE_JUDGE if decisions_rows else V17_ROLE_WEAVER
    # V17.23-Red：由 StateBackend 订阅事件（内存模式向后兼容，Redis 模式跨 worker）
    async with get_state_backend().subscribe_actions(session_id) as queue:
        _log.warning("[Narrator-Start] session=%s causal_anchor=redis_sync", session_id)
        # Frame 1..N: NARRATOR — LLM 真流式 + ActionQueue 内联 cancel，异常即 WILL_FLASH 重启
        current_user_message = str(pl.get("user_message", "")).strip()
        current_action_signal = bool(current_user_message)
        current_proxy = str(will_proxy or "stable")
        decision_anchor = current_user_message
        last_step_cursor = "START"
        premature_close_retry_count = 0
        while True:
            restarted = False
            saw_terminal_narrator = False
            try:
                async for frame in _narrator_with_heartbeat(
                    orchestrator.narrator_frames(
                        raw_physics=raw_physics,
                        facts=[x for x in facts if str(x).strip()],
                        will_proxy=current_proxy,
                        user_message=current_user_message,
                        action_signal=current_action_signal,
                        decision_anchor=decision_anchor,
                        action_queue=queue,
                        role_style=narrative_role,
                        decisions=decisions_rows,
                        session_id=session_id,
                        causal_anchor="redis_sync",
                        stability_checked=True,
                    )
                ):
                    if isinstance(frame, dict):
                        last_step_cursor = _frame_step_cursor(frame)
                        if _is_terminal_narrator_frame(frame):
                            saw_terminal_narrator = True
                    yield (json.dumps(frame, ensure_ascii=False) + "\n").encode("utf-8")
                    await asyncio.sleep(0)
                if not restarted and not saw_terminal_narrator:
                    if _should_retry_premature_close(last_step_cursor, premature_close_retry_count):
                        premature_close_retry_count += 1
                        _log.warning(
                            "[V17-NARRATOR-SOFT-RETRY] session=%s step=%s retry=%s",
                            session_id,
                            last_step_cursor,
                            premature_close_retry_count,
                        )
                        restarted = True
                    else:
                        _log.error(
                            "[V17-NARRATOR-PREMATURE-CLOSE] session=%s step=%s",
                            session_id,
                            last_step_cursor,
                        )
                        yield (
                            json.dumps(
                                _narrator_runtime_failure_frame(
                                    err=RuntimeError("narrator_stream_closed_without_terminal_frame"),
                                    step_cursor=last_step_cursor,
                                ),
                                ensure_ascii=False,
                            )
                            + "\n"
                        ).encode("utf-8")
                        await asyncio.sleep(0)
            except DataSovereigntyError as _dse:
                if str(_dse).strip() == "physics_metadata_unstable":
                    yield (json.dumps(_system_init_failure_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
                else:
                    yield (json.dumps(_physical_void_stop_frame(), ensure_ascii=False) + "\n").encode("utf-8")
                await asyncio.sleep(0)
                break
            except ActionInterruptDuringStream as exc:
                action_pl = exc.payload if isinstance(exc.payload, dict) else {}
                current_user_message = str(action_pl.get("action", "")).strip()
                decision_anchor = current_user_message
                current_action_signal = True
                if any(k in current_user_message for k in ["进", "冲", "突破", "加码"]):
                    current_proxy = "aggressive"
                elif any(k in current_user_message for k in ["稳", "守", "风控", "谨慎", "避险"]):
                    current_proxy = "stable"
                will_flash = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "layer": "WILL_FLASH",
                    "payload": {
                        "signal": "ACTION_TAKEN",
                        "action": current_user_message,
                        "will_proxy": current_proxy,
                        "will_flash": True,
                    },
                }
                yield (json.dumps(will_flash, ensure_ascii=False) + "\n").encode("utf-8")
                await asyncio.sleep(0)
                restarted = True
            except Exception as exc:  # noqa: BLE001
                _log.exception("[V17-NARRATOR-CRASH] session=%s step=%s", session_id, last_step_cursor)
                yield (
                    json.dumps(
                        _narrator_runtime_failure_frame(err=exc, step_cursor=last_step_cursor),
                        ensure_ascii=False,
                    )
                    + "\n"
                ).encode("utf-8")
                await asyncio.sleep(0)
                break
            if restarted:
                continue
            break



@router.get("/v17/stream", response_model=None)
@router.get("/api/v17/stream", response_model=None)
async def stream_v17(
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default="male", pattern="^(male|female)$"),
    flow_year: Optional[int] = Query(default=None, ge=1800, le=2200),
    v17_origin: Optional[str] = Query(default=None),
) -> Union[StreamingResponse, JSONResponse]:
    if not _sovereignty_v17(v17_origin):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    physics_payload = _run_v17_physics_core(
        birth_time=_safe_parse_birth_time(birth_time),
        gender=gender,
        flow_year=flow_year,
    )
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=physics_payload),
        media_type="application/x-ndjson",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
        },
    )


@router.post("/v17/stream", response_model=None)
@router.post("/api/v17/stream", response_model=None)
async def stream_v17_post(
    payload: Dict[str, Any],
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default="male", pattern="^(male|female)$"),
    flow_year: Optional[int] = Query(default=None, ge=1800, le=2200),
) -> Union[StreamingResponse, JSONResponse]:
    session_id = str((payload or {}).get("session_id", "")).strip() or "default"
    current_physics = await get_state_backend().get_physics(session_id)
    if _should_rebuild_physics_core(
        current_physics=current_physics if isinstance(current_physics, dict) else None,
        birth_time=birth_time,
        gender=gender,
        flow_year=flow_year,
    ):
        merged_payload = _run_v17_physics_core(
            birth_time=_safe_parse_birth_time(birth_time),
            gender=gender,
            flow_year=flow_year,
        )
    else:
        merged_payload = dict(current_physics) if isinstance(current_physics, dict) and current_physics else _run_v17_physics_core(
            birth_time=_safe_parse_birth_time(birth_time),
            gender=gender,
            flow_year=flow_year,
        )
    if isinstance(payload, dict):
        for _k, _v in payload.items():
            if _k in _PHYS_SSOT_KEYS:
                continue
            merged_payload[_k] = _v
    if not _sovereignty_v17(str(merged_payload.get("v17_origin", "")) if isinstance(merged_payload, dict) else None):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    if _WILL_IMPACT_BUFFER:
        last = _WILL_IMPACT_BUFFER[-1]
        if str(last.get("signal", "")).upper() == "ACTION_TAKEN":
            merged_payload["user_message"] = str(last.get("action", "")).strip()
            merged_payload["_action_seq"] = int(last.get("seq", 0) or 0)
    return StreamingResponse(
        _stream_frames(will_proxy=will_proxy, payload=merged_payload if isinstance(merged_payload, dict) else _default_payload()),
        media_type="application/x-ndjson",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
        },
    )


@router.post("/v17/action")
@router.post("/api/v17/action")
async def v17_action(payload: Dict[str, Any], v17_origin: Optional[str] = Header(default=None, alias="v17_origin")) -> JSONResponse:
    global _ACTION_SEQ
    body_origin = str(payload.get("v17_origin", "")).strip()
    header_origin = str(v17_origin or "").strip()
    if not _sovereignty_v17(body_origin) and not _sovereignty_v17(header_origin):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    signal = str(payload.get("signal", "")).strip().upper()
    action = str(payload.get("action", "")).strip()
    raw_status = str(payload.get("status", "APPROVED")).strip().upper()
    if signal in {"", "INJECT_PATCH"}:
        signal = "PLAN_SUBMIT"
    plan_signal = _normalize_plan_signal(signal, raw_status)
    if plan_signal not in {"PLAN_SUBMIT", "PLAN_APPROVE", "PLAN_REJECT", "PLAN_ESCALATE", "PLAN_WITHDRAW"}:
        return JSONResponse({"ok": False, "detail": "invalid action signal"}, status_code=400)
    _ACTION_SEQ += 1
    session_id = str(payload.get("session_id", "")).strip() or "default"
    decision_id = str(payload.get("decision_id", "")).strip()
    plan_id = str(payload.get("plan_id", "")).strip()
    event = {
        "signal": signal,
        "plan_signal": plan_signal,
        "action": action,
        "plan_id": plan_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "seq": _ACTION_SEQ,
        "session_id": session_id,
    }
    request_verdict = _boolish(payload.get("request_verdict"), default=True)
    event["request_verdict"] = request_verdict
    kernel_dispatch_ok = True
    kernel_dispatch_detail = ""
    # V17.45: 全域因果调度 (SRC_MANUAL)
    if plan_signal:
        from v17_rebirth.backend.logic.L1_atomic_ops.physics_kernel import PhysicsKernel
        try:
            current_physics = await get_state_backend().get_physics(session_id)
            if not isinstance(current_physics, dict):
                current_physics = {}
            resolved_plan = _find_plan_by_id(current_physics, plan_id) if plan_id else None
            anchor = str(payload.get("anchor", "")).strip()
            if not anchor:
                anchor = str(resolved_plan.get("anchor") or "") if isinstance(resolved_plan, dict) else ""
            batch_ids = _safe_plan_ids(payload.get("batch_ids") or payload.get("batch_id"))
            decision_ids = _safe_plan_ids(payload.get("decision_ids"))
            if (not batch_ids and not decision_ids) and resolved_plan:
                resolved_plan_rows = _safe_plan_ids(resolved_plan.get("batch_ids"))
                if resolved_plan_rows:
                    batch_ids = resolved_plan_rows
                else:
                    decision_ids = _safe_plan_ids((resolved_plan.get("meta") or {}).get("decision_ids"))
            if not decision_ids and decision_id:
                decision_ids.append(decision_id)

            matched_decisions = _resolve_batch_decisions(current_physics, batch_ids)
            if not matched_decisions:
                if not decision_ids:
                    # 兼容旧行为：ACTION_TAKEN 时如果只用 action 文案命中
                    matched_decisions = _collect_matched_decisions(
                        current_physics,
                        decision_labels=[action] if action else [],
                    )
                else:
                    matched_decisions = _collect_matched_decisions(current_physics, decision_ids=decision_ids)

            if not action and matched_decisions:
                sample = matched_decisions[0]
                action = str(sample.get("label") or sample.get("title") or "").strip()

            if not action:
                if isinstance(resolved_plan, dict):
                    action = str(
                        ((resolved_plan.get("meta") or {}).get("action") or resolved_plan.get("anchor") or "").strip()
                    ) or action
                action = action or f"PLAN-{plan_signal}"
            if _are_decisions_settled(matched_decisions) and plan_signal in {"PLAN_APPROVE", "PLAN_SUBMIT"}:
                event["decision_count"] = 0
                event["plan_status"] = (
                    str((resolved_plan or {}).get("status") or "APPROVED") if resolved_plan else "APPROVED"
                )
                event["note"] = "decision set already settled; skip duplicate dispatch"
                await get_state_backend().set_physics(session_id, current_physics)
                await get_state_backend().publish_action(
                    session_id,
                    _event_for_publish(event, physics_tensor=current_physics),
                )
                return JSONResponse({"ok": True, "signal": "VOTE_IGNORED", "action": action, "detail": event["note"]})
            if resolved_plan:
                resolved_status = str((resolved_plan or {}).get("status", "")).strip().upper()
                if _is_plan_terminal(resolved_status) and plan_signal in {
                    "PLAN_APPROVE",
                    "PLAN_REJECT",
                    "PLAN_ESCALATE",
                    "PLAN_WITHDRAW",
                    "PLAN_SUBMIT",
                }:
                    event["plan_status"] = resolved_status
                    event["note"] = "plan already terminal; duplicate ignored"
                    await get_state_backend().set_physics(session_id, current_physics)
                    await get_state_backend().publish_action(
                        session_id,
                        _event_for_publish(event, physics_tensor=current_physics),
                    )
                    return JSONResponse(
                        {
                            "ok": True,
                            "signal": "VOTE_IGNORED",
                            "action": action,
                            "plan_id": str(plan_id),
                            "detail": event["note"],
                        }
                    )
            if not matched_decisions:
                # 兼容旧流程：无匹配决策时直观触发叙事，不下发到物理层。
                event["error"] = "decision_not_found"
                await get_state_backend().set_physics(session_id, current_physics)
                await get_state_backend().publish_action(
                    session_id,
                    _event_for_publish(event, physics_tensor=current_physics),
                )
                return JSONResponse({"ok": True, "signal": "NARRATIVE_TRIGGER", "action": action})

            for each in matched_decisions:
                each.setdefault("id", str(each.get("label") or each.get("title") or action).strip())

            plan = _seed_plan_from_payload(
                payload={**payload, "action": action, "anchor": anchor},
                session_id=session_id,
                rows=matched_decisions,
                signal=plan_signal,
            )
            if plan_signal == "PLAN_SUBMIT" and str(plan.routing or "").strip().lower() == "llm":
                plan.meta["llm_review_prompt"] = _build_llm_plan_prompt(
                    rows=matched_decisions,
                    action=action,
                    anchor=anchor,
                )
                event["llm_review_prompt"] = plan.meta.get("llm_review_prompt")
            execute_as_plan_approve = plan_signal == "PLAN_SUBMIT" and str(plan.routing or "user").strip() == "system"
            execution_signal = "PLAN_APPROVE" if execute_as_plan_approve else plan_signal
            if execute_as_plan_approve:
                event["auto_approved"] = True
                event["routing"] = plan.routing
                event["routing_reason"] = str(plan.meta.get("routing_reason") or "").strip() or None
            decision_status = {
                "PLAN_APPROVE": "APPROVED",
                "PLAN_REJECT": "REJECTED",
                "PLAN_ESCALATE": "AWAIT_REVIEW",
                "PLAN_WITHDRAW": "REJECTED",
                "PLAN_SUBMIT": "AWAIT_REVIEW" if not execute_as_plan_approve else "APPROVED",
            }.get(plan_signal, "DRAFT")

            applied_ids: list[str] = []
            if execution_signal == "PLAN_APPROVE":
                # 逐条执行，避免单次事件失败污染全体。
                for idx, matched_decision in enumerate(matched_decisions):
                    row_payload = dict(payload)
                    matched_label = str(matched_decision.get("label", "")).strip()
                    matched_title = str(matched_decision.get("title", "")).strip()
                    row_payload["action"] = matched_label or matched_title or action
                    row_payload.pop("decision_ids", None)
                    row_payload["decision_ids"] = [str(matched_decision.get("id", "")).strip()] if str(
                        matched_decision.get("id", "")
                    ).strip() else []

                    if isinstance(matched_decision.get("physical_impact"), dict):
                        row_payload["physical_impact"] = dict(matched_decision.get("physical_impact"))
                    elif isinstance(payload.get("physical_impact"), dict):
                        row_payload["physical_impact"] = dict(payload.get("physical_impact"))
                    else:
                        row_payload["physical_impact"] = {}

                    final_target = str(row_payload.get("target_god", "")).strip()
                    if not final_target and isinstance(row_payload.get("physical_impact"), dict):
                        final_target = str(row_payload["physical_impact"].get("target_god", "")).strip()
                        if final_target:
                            row_payload["target_god"] = final_target
                    if not final_target:
                        final_target = resolve_target_god(
                            row_target=row_payload.get("target_god"),
                            impact=row_payload.get("physical_impact") if isinstance(row_payload.get("physical_impact"), dict) else {},
                            title=row_payload.get("title") or row_payload.get("action"),
                            label=matched_label,
                            plugin_id=matched_decision.get("plugin_id") if isinstance(matched_decision, dict) else "",
                            physics_tensor=current_physics if isinstance(current_physics, dict) else {},
                        )
                        if final_target:
                            row_payload["target_god"] = final_target

                    if not final_target:
                        _log.warning("[V17-ACTION] decision no target_god, degrade to context_only: %s", matched_label)
                        matched_decision["status"] = "CONSUMED_CONTEXT"
                        matched_decision["applied"] = False
                        matched_decision["llm_resolution_type"] = "context_only"
                        matched_decision["llm_resolution_state"] = "pending_context"
                        matched_decision["llm_terminal_state"] = "consume_context"
                        continue

                    matched_decision["status"] = "APPROVED"
                    matched_decision["applied"] = True
                    decision_id_val = str(matched_decision.get("id", "")).strip() or f"{action}_{idx}"
                    applied_ids.append(decision_id_val)
                    row_payload["decision_id"] = decision_id_val
                    ok = await PhysicsKernel.dispatch_perturbation(
                        session_id=session_id,
                        source="SRC_MANUAL",
                        payload={**row_payload, "reason": f"手动激活动作: {action}"},
                        causality_id=f"plan_{plan.plan_id}_{_ACTION_SEQ}_{idx}_{decision_id_val}",
                    )
                    if not ok:
                        kernel_dispatch_ok = False
                        kernel_dispatch_detail = f"physics kernel rejected perturbation at index {idx}"
                        matched_decision["status"] = "FAILED"
                        _log.error(
                            "[V17-ACTION-REJECTED] session=%s action=%s detail=%s",
                            session_id,
                            action,
                            kernel_dispatch_detail,
                        )
                        break
            else:
                # 仅状态裁决，不触发物理扰动
                for matched_decision in matched_decisions:
                    matched_decision["status"] = decision_status

            if execution_signal != "PLAN_APPROVE":
                event["decision_count"] = len(matched_decisions)
                _mark_plan_decisions(current_physics, matched_decisions, status=decision_status, plan_id=plan.plan_id)
                if plan_signal == "PLAN_REJECT":
                    for matched in matched_decisions:
                        evolution_storage.log_feedback(
                            session_id=session_id,
                            decision_id=str(matched.get("id") or "").strip(),
                            action=action,
                            status="REJECTED",
                            meta={"trigger": "user_manual_reject", "plan_id": plan.plan_id},
                        )
                    plan.transition("REJECTED")
                    _write_plan_state(current_physics, plan=plan)
                    _emit_decision_batch_cache(current_physics)
                    await get_state_backend().set_physics(session_id, current_physics)
                    await get_state_backend().publish_action(
                        session_id,
                        _event_for_publish(event, physics_tensor=current_physics),
                    )
                    return JSONResponse(
                        {
                            "ok": True,
                            "signal": "VOTE_REJECTED",
                            "action": action,
                            "plan_id": plan.plan_id,
                            "decision_count": len(matched_decisions),
                        }
                    )
                if plan_signal == "PLAN_WITHDRAW":
                    for matched in matched_decisions:
                        evolution_storage.log_feedback(
                            session_id=session_id,
                            decision_id=str(matched.get("id") or "").strip(),
                            action=action,
                            status="REJECTED",
                            meta={"trigger": "user_plan_withdraw", "plan_id": plan.plan_id},
                        )
                    plan.transition("REJECTED")
                    _write_plan_state(current_physics, plan=plan)
                    _emit_decision_batch_cache(current_physics)
                    await get_state_backend().set_physics(session_id, current_physics)
                    await get_state_backend().publish_action(
                        session_id,
                        _event_for_publish(event, physics_tensor=current_physics),
                    )
                    return JSONResponse(
                        {
                            "ok": True,
                            "signal": "VOTE_WITHDRAWN",
                            "action": action,
                            "plan_id": plan.plan_id,
                            "decision_count": len(matched_decisions),
                        }
                    )
                if plan_signal in {"PLAN_SUBMIT", "PLAN_ESCALATE"}:
                    plan.transition("AWAIT_REVIEW")
                    if str(plan.routing or "").strip().lower() == "llm":
                        event["llm_review_prompt"] = plan.meta.get("llm_review_prompt")
                    _write_plan_state(current_physics, plan=plan)
                    _emit_decision_batch_cache(current_physics)
                    await get_state_backend().set_physics(session_id, current_physics)
                    await get_state_backend().publish_action(
                        session_id,
                        _event_for_publish(event, physics_tensor=current_physics),
                    )
                    return JSONResponse(
                        {
                            "ok": True,
                            "plan_id": plan.plan_id,
                            "signal": signal if signal == "PLAN_SUBMIT" else plan_signal,
                            "action": action,
                            "decision_count": len(matched_decisions),
                            "llm_review_prompt": event.get("llm_review_prompt"),
                        }
                    )

            if execution_signal == "PLAN_APPROVE" and not applied_ids:
                no_target_only = all(
                    str(item.get("status") or "").strip().upper() == "CONSUMED_CONTEXT"
                    for item in matched_decisions
                )
                event["decision_count"] = len(matched_decisions)
                if no_target_only:
                    plan.transition("COMMITTED")
                    event["signal"] = "CONTEXT_CONSUMED"
                else:
                    event["error"] = "no_physics_apply"
                    plan.transition("FAILED")
                _write_plan_state(current_physics, plan=plan)
                _emit_decision_batch_cache(current_physics)
                await get_state_backend().set_physics(session_id, current_physics)
                await get_state_backend().publish_action(
                    session_id,
                    _event_for_publish(event, physics_tensor=current_physics),
                )
                if no_target_only:
                    return JSONResponse({"ok": True, "signal": "CONTEXT_CONSUMED", "action": action, "decision_count": len(matched_decisions)})
                return JSONResponse({"ok": True, "signal": "NARRATIVE_TRIGGER", "action": action, "decision_count": 0})

            if execution_signal == "PLAN_APPROVE":
                latest_physics = await get_state_backend().get_physics(session_id)
                if isinstance(latest_physics, dict) and latest_physics:
                    current_physics = latest_physics
                _mark_plan_decisions(
                    current_physics,
                    matched_decisions,
                    status="APPROVED" if kernel_dispatch_ok else "FAILED",
                    plan_id=plan.plan_id,
                )
                if kernel_dispatch_ok:
                    plan.transition("COMMITTED")
                    event["decision_count"] = len(applied_ids)
                else:
                    plan.transition("FAILED")
                    event["error"] = "physics kernel dispatch failed"
                    event["detail"] = kernel_dispatch_detail or "physics kernel dispatch failed"
                    event["decision_count"] = len(matched_decisions)

                _write_plan_state(current_physics, plan=plan)
                _emit_decision_batch_cache(current_physics)
                await get_state_backend().set_physics(session_id, current_physics)
                await get_state_backend().publish_action(
                    session_id,
                    _event_for_publish(event, physics_tensor=current_physics),
                )
                if not kernel_dispatch_ok:
                    return JSONResponse(
                        {"ok": False, "detail": kernel_dispatch_detail or "physics kernel dispatch failed", "signal": signal},
                        status_code=500,
                    )
        except Exception as e:
            kernel_dispatch_ok = False
            kernel_dispatch_detail = str(e)
            _log.error(f"[V17-KERNEL-DISPATCH-FAIL] {e}")
            return JSONResponse(
                {"ok": False, "detail": kernel_dispatch_detail or "physics action failed", "signal": signal},
                status_code=500,
            )

    if not kernel_dispatch_ok:
        return JSONResponse(
            {
                "ok": False,
                "detail": kernel_dispatch_detail or "physics kernel dispatch failed",
                "signal": signal,
            },
            status_code=500,
        )
    
    # V17.99: 记录正反馈并捕获残差 (The Cerebrum)
    if locals().get("execution_signal") == "PLAN_APPROVE" and kernel_dispatch_ok:
        try:
            residual = float(payload.get("residual", 0.0))
            decision_ids = payload.get("decision_ids")
            id_lookup = {str(dec.get("id", "")).strip(): dec for dec in locals().get("matched_decisions", []) if isinstance(dec, dict)}
            if isinstance(decision_ids, list) and decision_ids:
                for each_id in decision_ids:
                    each_sid = str(each_id or "").strip()
                    if not each_sid:
                        continue
                    matched = id_lookup.get(each_sid, {})
                    meta = {
                        "impact_ratio": (
                            matched.get("physical_impact", {}).get("impact_ratio")
                            if isinstance(matched.get("physical_impact"), dict)
                            else payload.get("physical_impact", {}).get("impact_ratio") if isinstance(payload.get("physical_impact"), dict) else None
                        ),
                        "target_god": (
                            str(
                                matched.get("target_god", "")
                                or (
                                    matched.get("physical_impact", {}).get("target_god")
                                    if isinstance(matched.get("physical_impact"), dict)
                                    else ""
                                )
                            ).strip()
                            or payload.get("target_god")
                        ),
                    }
                    evolution_storage.log_feedback(
                        session_id=session_id,
                        decision_id=each_sid,
                        action=action,
                        status="APPROVED",
                        residual=residual,
                        meta=meta,
                    )
            else:
                evolution_storage.log_feedback(
                    session_id=session_id,
                    decision_id=decision_id or action,
                    action=action,
                    status="APPROVED",
                    residual=residual,
                    meta={
                        "impact_ratio": payload.get("physical_impact", {}).get("impact_ratio"),
                        "target_god": payload.get("target_god")
                    }
                )
        except Exception as e:
            _log.error(f"[V17-EVOLUTION-LOG-FAIL] {e}")

    return JSONResponse(
        {
            "ok": True,
            "signal": signal if signal != "PLAN_WITHDRAW" else plan_signal,
            "plan_id": plan.plan_id if "plan" in locals() else None,
            "plan_signal": plan_signal,
            "will_proxy_delta": "aggressive" if any(k in action for k in ["进", "冲", "加码"]) else "stable",
        }
    )


@router.post("/v17/freeze-report")
@router.post("/api/v17/freeze-report")
async def freeze_report(
    payload: Dict[str, Any],
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> JSONResponse:
    origin = str(payload.get("v17_origin", "")).strip() or str(v17_origin_header or "").strip()
    if not _sovereignty_v17(origin):
        return JSONResponse({"ok": False, "detail": "v17_origin validation failed"}, status_code=403)
    render_text = str(payload.get("render_text", "")).strip()
    decisions = payload.get("decisions")
    if not render_text:
        return JSONResponse({"ok": False, "detail": "render_text is required"}, status_code=400)
    rows = decisions if isinstance(decisions, list) else []
    sanitized_rows = [{"id": str((x or {}).get("id", "")).strip(), "label": str((x or {}).get("label", "")).strip()} for x in rows if isinstance(x, dict)]
    rid = _append_freeze_report(
        {
            "v17_origin": "v17_rebirth",
            "timestamp": datetime.utcnow().isoformat(),
            "render_text": render_text,
            "decisions": [x for x in sanitized_rows if x["label"]],
        }
    )
    return JSONResponse({"ok": True, "report_id": rid})
