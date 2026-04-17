"""V12.94：冲突自动裁决分流（Conflict Router）与断言树静默合并算子。"""

from __future__ import annotations

import logging
import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Literal, Mapping, MutableMapping, Optional, Sequence, Set

from sqlmodel import Session, select

from app.core.plugins.registry import plugin_authority_level
from app.services.narrative.realtime_narrator import compose_realtime_narration
from app.services.narrative.pipeline import guard_narrative_payload, sanitize_frame_for_client

_LOG = logging.getLogger(__name__)

_INBOX_SQL_PATCH_OK = re.compile(
    r"^UPDATE\s+physics_interaction_params\s+SET\s+param_value\s*=\s*([0-9]*\.?[0-9]+)\s+WHERE\s+param_key\s*=\s*'([A-Za-z0-9_]+)'\s*;?$",
    re.IGNORECASE,
)


def _decision_inbox_sql_filter(sql_patch: str) -> str:
    """与 ``router_helpers.sql_filter`` 同语义，避免 decision_hub → router 的额外导入边。"""
    sql = (sql_patch or "").strip()
    if not sql or "--" in sql or "/*" in sql or sql.count(";") > 1:
        return ""
    m = _INBOX_SQL_PATCH_OK.match(sql)
    if not m:
        return ""
    try:
        value = float(m.group(1))
    except (TypeError, ValueError):
        return ""
    key = str(m.group(2) or "").strip()
    if not key or not (0.0 <= value <= 2.0):
        return ""
    return f"UPDATE physics_interaction_params SET param_value={value:.2f} WHERE param_key='{key}';"

ConflictRoute = Literal["USER", "AUTO_LLM", "AUTO_LLM_QUEUED"]


def conflict_pattern_signature(conflict: Mapping[str, Any]) -> str:
    """用于与黄金账本种子/版本指纹做弱匹配的稳定签名。"""
    kind = str(conflict.get("kind") or "").strip().lower()
    detail = str(conflict.get("detail") or "").strip().lower()
    return f"{kind}|{detail}"


def _pattern_keys_from_snapshot(snap: Any) -> Set[str]:
    keys: Set[str] = set()
    if not snap:
        return keys
    vid = str(getattr(snap, "version_id", "") or "").strip()
    if vid:
        keys.add(vid.lower())
    for s in list(getattr(snap, "seeds_matched", None) or []):
        t = str(s or "").strip().lower()
        if t:
            keys.add(t)
    payload = getattr(snap, "snapshot_payload", None) or {}
    if isinstance(payload, dict):
        extra = payload.get("arbiter_conflict_keys")
        if isinstance(extra, list):
            for x in extra:
                t = str(x or "").strip().lower()
                if t:
                    keys.add(t)
    return keys


def load_gold_arbiter_matching(session: Session, conflict: Mapping[str, Any]) -> tuple[Set[str], str]:
    """
    返回 `(全量 GOLD 模式键并集, 徽章文案)`；若当前 ``conflict`` 命中某条 GOLD 样本，则徽章带 Set 序号。
    """
    from app.db.learning_ledger import ArbiterPreferenceLedger
    from app.db.models import BrainHtnSnapshot

    union: Set[str] = set()
    badge = "GOLD ledger (pattern union)"
    try:
        rows = list(
            session.exec(
                select(ArbiterPreferenceLedger)
                .where(ArbiterPreferenceLedger.preference_tier == "GOLD")
                .order_by(ArbiterPreferenceLedger.id)
            ).all()
        )
    except Exception:
        return union, badge
    first_hit: Optional[str] = None
    for i, row in enumerate(rows or [], start=1):
        try:
            sid = int(getattr(row, "snapshot_id", 0) or 0)
        except (TypeError, ValueError):
            continue
        if sid <= 0:
            continue
        snap = session.get(BrainHtnSnapshot, sid)
        local = _pattern_keys_from_snapshot(snap)
        union |= local
        if first_hit is None and local and conflict_matches_ledger_patterns(conflict, local):
            hid = int(getattr(snap, "id", 0) or 0)
            first_hit = f"Based on GOLD Set #{i} (HTN snapshot #{hid})"
    if first_hit:
        badge = first_hit
    return union, badge


def load_gold_arbiter_pattern_keys(session: Session) -> Set[str]:
    """
    从 ``ArbiterPreferenceLedger``（GOLD）关联的 ``BrainHtnSnapshot`` 收集可匹配模式并集。
    """
    keys, _ = load_gold_arbiter_matching(session, {"kind": "", "detail": ""})
    return keys


def _normalized_conflict_blob(conflict: Mapping[str, Any]) -> str:
    return conflict_pattern_signature(conflict).replace(" ", "")


def conflict_matches_ledger_patterns(conflict: Mapping[str, Any], gold_keys: Iterable[str]) -> bool:
    """黄金账本模式与当前冲突摘要做子串/锚点弱匹配。"""
    blob = _normalized_conflict_blob(conflict)
    if not blob or blob == "|":
        return False
    for raw in gold_keys:
        g = str(raw or "").strip().lower()
        if not g:
            continue
        tail = g.split(":", 1)[-1] if ":" in g else g
        if len(tail) >= 2 and tail in blob:
            return True
        if len(g) >= 4 and g in blob:
            return True
        # version_id 形如 v12.x / pulse-xxx
        if re.match(r"^v[\d.]+$", g) and g in blob:
            return True
    return False


def should_auto_resolve(
    conflict: Mapping[str, Any],
    *,
    conflict_weight: float,
    gold_pattern_keys: Optional[Set[str]] = None,
    entropy_cap: float = 0.3,
    physics_meta_sink: Optional[MutableMapping[str, Any]] = None,
) -> ConflictRoute:
    """
    自动裁决分流：冲突权重低于 ``entropy_cap`` 且与黄金账本模式弱匹配 → ``AUTO_LLM``，否则 ``USER``。

    V12.98：若传入 ``physics_meta_sink``（通常为 ``physics_tensor.meta``），符合 ``AUTO_LLM`` 的冲突
    会追加到 ``pending_arbitration_queue_v1``，并返回 ``AUTO_LLM_QUEUED``（由调用方统一批量 LLM），
    不再表示「可立即单条调用」语义。
    """
    cap = float(entropy_cap)
    if cap != cap or cap <= 0.0:
        cap = 0.3
    cap = max(0.05, min(0.99, cap))
    w = float(conflict_weight)
    if w != w:  # NaN
        w = 1.0
    w = max(0.0, min(1.0, w))
    if w >= cap:
        return "USER"
    keys = gold_pattern_keys or set()
    if not keys:
        return "USER"
    if not conflict_matches_ledger_patterns(conflict, keys):
        return "USER"
    if physics_meta_sink is not None:
        qraw = physics_meta_sink.get("pending_arbitration_queue_v1")
        q = list(qraw) if isinstance(qraw, list) else []
        q.append(
            {
                "conflict": {
                    "kind": str(conflict.get("kind") or ""),
                    "detail": str(conflict.get("detail") or ""),
                },
                "conflict_weight": w,
                "entropy_cap": cap,
            }
        )
        physics_meta_sink["pending_arbitration_queue_v1"] = q[-20:]
        return "AUTO_LLM_QUEUED"
    return "AUTO_LLM"


def build_arbitration_theme(conflict: Mapping[str, Any], candidate_plugins: Sequence[str]) -> str:
    """Debug 主题行：冲突名 VS 候选插件简表。"""
    left = conflict_display_name(conflict)
    cands = [str(x).strip() for x in candidate_plugins if str(x).strip()][:4]
    right = " / ".join(cands) if cands else "（无候选）"
    return f"{left} VS {right}"


def merge_silent_arbiter_into_assertion_tree(
    tree: Mapping[str, Any],
    *,
    plugin_id: str,
    reason: str,
    conflict_signature: str,
    audit_bundle: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    将静默裁决结果写入断言树：追加 LAW 节点、边，以及 ``silent_arbiter_history_v1`` 历史项。
    ``audit_bundle`` 写入历史：完整 Prompt、候选、原始回复与回滚快照（供一票否决）。
    """
    out: Dict[str, Any] = dict(tree) if isinstance(tree, dict) else {}
    nodes: List[Any] = list(out.get("nodes") or []) if isinstance(out.get("nodes"), list) else []
    edges: List[Any] = list(out.get("edges") or []) if isinstance(out.get("edges"), list) else []

    node_id = f"law-arbiter-{uuid.uuid4().hex[:12]}"
    law_text = f"SILENT_ARBITER plugin={plugin_id} | {reason[:280]}"
    nodes.append(
        {
            "node_id": node_id,
            "node_type": "LAW",
            "text": law_text,
            "evidence_refs": [
                f"decision_hub.v12_94.silent_merge:{conflict_signature[:120]}",
                f"silent_arbiter.law_node_id={node_id}",
            ],
        }
    )
    edges.append({"from": "root", "to": node_id, "label": "silent_arbiter"})

    hist = list(out.get("silent_arbiter_history_v1") or []) if isinstance(out.get("silent_arbiter_history_v1"), list) else []

    row: Dict[str, Any] = {
        "protocol": "silent_arbiter_history.v1",
        "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "route": "AUTO_LLM",
        "decision": str(plugin_id or "").strip(),
        "reason": str(reason or "").strip()[:400],
        "conflict_signature": str(conflict_signature or "").strip()[:240],
        "law_node_id": node_id,
    }
    if audit_bundle and isinstance(audit_bundle, dict):
        for k, v in audit_bundle.items():
            if v is not None:
                row[str(k)] = v
    hist.append(row)
    out["nodes"] = nodes
    out["edges"] = edges
    out["silent_arbiter_history_v1"] = hist[-50:]
    return out


def append_silent_arbiter_meta(
    physics_meta: MutableMapping[str, Any],
    entry: Mapping[str, Any],
) -> None:
    """在 ``physics_tensor.meta`` 侧挂载一份可观测历史（供 Debug 看板无需解析 assertion_tree）。"""
    cur = physics_meta.get("silent_arbiter_history_v1")
    hist = list(cur) if isinstance(cur, list) else []
    hist.append(dict(entry))
    physics_meta["silent_arbiter_history_v1"] = hist[-50:]


def conflict_display_name(conflict: Mapping[str, Any]) -> str:
    """人读冲突标题（Debug / 审计）。"""
    detail = str(conflict.get("detail") or "").strip()
    kind = str(conflict.get("kind") or "").strip().lower()
    blob = f"{detail}"
    if "伤官" in blob and ("官" in blob or "正官" in blob or "七杀" in blob):
        return "伤官见官逻辑冲突"
    if "子午" in blob or ("子" in blob and "午" in blob):
        return "子午对冲结构张力"
    if "寅" in blob and "巳" in blob:
        return "寅巳穿害结构张力"
    if "辰" in blob and "戌" in blob:
        return "辰戌冲结构张力"
    if kind == "clash" and detail:
        return f"地支冲合：{detail[:40]}"
    if detail:
        return f"盘面冲突：{detail[:48]}"
    return "多插件高分张力（择优）"


def build_arbitration_physics_context(
    *,
    metadata: Mapping[str, Any],
    physics_tensor: Mapping[str, Any],
    conflict: Mapping[str, Any],
    routing_note: str,
) -> Dict[str, Any]:
    """供 LLM 与审计回放：结构化物理证据摘录（非全量 physics_tensor）。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    bundle = meta.get("semantic_label_bundle_v1") if isinstance(meta.get("semantic_label_bundle_v1"), dict) else {}
    vf = bundle.get("verified_fact_lines") if isinstance(bundle.get("verified_fact_lines"), list) else []
    vf_out = [str(x).strip() for x in vf[:12] if str(x).strip()]
    inbox = meta.get("decision_inbox_v1") if isinstance(meta.get("decision_inbox_v1"), dict) else {}
    scores = inbox.get("match_scores") if isinstance(inbox.get("match_scores"), list) else []
    score_excerpt: List[Dict[str, Any]] = []
    for x in scores[:8]:
        if isinstance(x, dict):
            score_excerpt.append(
                {
                    "plugin_id": str(x.get("plugin_id") or ""),
                    "score": x.get("score"),
                }
            )
    pillars = metadata.get("pillars") if isinstance(metadata.get("pillars"), dict) else {}
    scores_ds = physics_tensor.get("deity_scores") if isinstance(physics_tensor.get("deity_scores"), dict) else {}
    deity_excerpt: Dict[str, float] = {}
    for k, v in list(scores_ds.items())[:10]:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            deity_excerpt[str(k)] = float(v)
    return {
        "protocol": "arbitration_conflict_context.v1",
        "conflict_point": dict(conflict),
        # V13.42：前端 Hook 需稳定数组结构，避免 undefined 分支触发残留断言噪音。
        "temporal_events": [],
        "global_entropy": meta.get("global_entropy"),
        "decision_inbox_match_scores_excerpt": score_excerpt,
        "verified_fact_lines_excerpt": vf_out,
        "pillars_brief": pillars,
        "deity_scores_excerpt": deity_excerpt,
        "routing_note": str(routing_note or "")[:800],
    }


def build_arbitration_audit_entry(
    *,
    conflict_name: str,
    conflict_context: Mapping[str, Any],
    messages: List[Dict[str, str]],
    raw_response: str,
    decision_plugin_id: str,
    reason: str,
    gold_badge: str,
    arbitration_theme: str = "",
    candidate_plugins: Optional[Sequence[str]] = None,
    law_node_id: str = "",
    rollback_interrupt: Optional[Mapping[str, Any]] = None,
    rollback_flow_state: str = "",
    entry_id: Optional[str] = None,
    batch_id: str = "",
    batch_index: int = -1,
    batch_total: int = 0,
) -> Dict[str, Any]:
    """V12.95：单条裁决审计记录（写入 ``BrainHtnSnapshot.arbitration_logs`` 与 meta feed）。"""
    cands = [str(x).strip() for x in (candidate_plugins or []) if str(x).strip()]
    rid = str(entry_id or "").strip() or f"arb-{uuid.uuid4().hex[:16]}"
    out_e: Dict[str, Any] = {
        "protocol": "arbitration_audit.v1",
        "id": rid,
        "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "arbitration_theme": str(arbitration_theme or "").strip()[:300],
        "conflict_name": str(conflict_name or "").strip()[:200],
        "gold_badge": str(gold_badge or "").strip()[:240],
        "conflict_context": dict(conflict_context),
        "prompt_messages": [{"role": str(m.get("role") or ""), "content": str(m.get("content") or "")} for m in messages],
        "candidate_plugins": cands,
        "raw_response": str(raw_response or "")[:8000],
        "raw_llm_reason": str(reason or "").strip()[:800],
        "decision_plugin_id": str(decision_plugin_id or "").strip(),
        "reason": str(reason or "").strip()[:400],
        "law_node_id": str(law_node_id or "").strip(),
        "rollback_interrupt": dict(rollback_interrupt or {}),
        "rollback_flow_state": str(rollback_flow_state or "").strip()[:64],
        "overruled": False,
    }
    bid = str(batch_id or "").strip()
    if bid:
        out_e["batch_id"] = bid[:64]
        if batch_index >= 0:
            out_e["batch_index"] = int(batch_index)
        if batch_total > 0:
            out_e["batch_total"] = int(batch_total)
    return out_e


def append_arbitration_audit_feed(physics_meta: MutableMapping[str, Any], entry: Mapping[str, Any]) -> None:
    cur = physics_meta.get("arbitration_audit_feed_v1")
    hist = list(cur) if isinstance(cur, list) else []
    hist.append(dict(entry))
    physics_meta["arbitration_audit_feed_v1"] = hist[-30:]


def append_physics_autonomy_log(physics_meta: MutableMapping[str, Any], entry: Mapping[str, Any]) -> None:
    """V13.03：物理自治审计（静默毙稿、权力否决、二段跳闭合），供 Debug 面板展示。"""
    cur = physics_meta.get("physics_autonomy_log_v1")
    hist = list(cur) if isinstance(cur, list) else []
    row = dict(entry)
    row.setdefault("at", datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    hist.append(row)
    physics_meta["physics_autonomy_log_v1"] = hist[-80:]


def _polarity_anchor_from_physics(physics_tensor: Mapping[str, Any]) -> float:
    """[-1,1] 粗锚：优先 deity_energy_axes 极性；否则退化到 deity_scores 张力。"""
    axes = physics_tensor.get("deity_energy_axes") if isinstance(physics_tensor.get("deity_energy_axes"), dict) else {}
    pos_w = 0.0
    neg_w = 0.0
    for _k, ax in axes.items():
        if not isinstance(ax, dict):
            continue
        ae = float(ax.get("absolute_energy") or 0.0)
        if ae <= 0.0:
            continue
        pol = str(ax.get("polarity") or ax.get("polarity_label") or "").upper()
        if "NEG" in pol or pol in ("YIN", "阴"):
            neg_w += ae
        elif "POS" in pol or pol in ("YANG", "阳"):
            pos_w += ae
    tot = pos_w + neg_w
    if tot > 1e-6:
        return max(-1.0, min(1.0, (pos_w - neg_w) / tot))
    ds = physics_tensor.get("deity_scores") if isinstance(physics_tensor.get("deity_scores"), dict) else {}
    vals = [float(v) for v in ds.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(vals) < 2:
        return 0.0
    rng = max(vals) - min(vals)
    top = max(vals) + 1e-9
    return max(-1.0, min(1.0, math.tanh((rng / top) * 1.5) * 0.85))


_PLUGIN_POLE_HINT: Dict[str, float] = {
    "classical.blind_school.v1": 0.42,
    "classical.wangshuai.v1": -0.38,
    "base.chronos": 0.05,
    "modern.wealth_risk.v1": 0.22,
    "classical.pattern_detector.v2": -0.12,
    "classical.climate_adjuster.v1": 0.08,
    "classical.conflict_auditor.v1": -0.05,
    "modern.will_proxy.v1": 0.0,
}


def _plugin_polarity_hint(plugin_id: str) -> float:
    return float(_PLUGIN_POLE_HINT.get(str(plugin_id or "").strip(), 0.0))


def apply_physical_sanity_check(
    conflicts: Sequence[Mapping[str, Any]],
    *,
    physics_tensor: Mapping[str, Any],
    match_scores: List[Dict[str, Any]],
    physics_meta_sink: Optional[MutableMapping[str, Any]] = None,
    deviation_threshold: float = 0.4,
) -> List[Dict[str, Any]]:
    """
    V13.03 物理真值锚点：对比 ``physics_tensor`` 能量极性锚与插件极性先验；
    偏差超过阈值则 ``SILENT_REJECT``，不进入 Inbox match_scores。
    ``conflicts`` 用于审计签名（可为空序列）。
    """
    thr = float(deviation_threshold)
    if thr != thr or thr <= 0.0:
        thr = 0.4
    thr = max(0.05, min(0.95, thr))
    anchor = _polarity_anchor_from_physics(physics_tensor)
    sig = ""
    if conflicts:
        try:
            sig = conflict_pattern_signature(conflicts[0]) if isinstance(conflicts[0], Mapping) else ""
        except Exception:
            sig = ""
    kept: List[Dict[str, Any]] = []
    for row in list(match_scores or []):
        if not isinstance(row, dict):
            continue
        pid = str(row.get("plugin_id") or "").strip()
        sc = float(row.get("score") or 0.0)
        hint = _plugin_polarity_hint(pid) + (sc - 0.5) * 0.18
        dev = abs(anchor - hint)
        if dev > thr:
            if physics_meta_sink is not None:
                append_physics_autonomy_log(
                    physics_meta_sink,
                    {
                        "kind": "SILENT_REJECT",
                        "reason": "physical_anchor_deviation",
                        "plugin_id": pid,
                        "conflict_signature": sig[:200],
                        "anchor": round(anchor, 5),
                        "hint_effective": round(hint, 5),
                        "deviation": round(dev, 5),
                        "threshold": thr,
                    },
                )
            continue
        kept.append(row)
    return kept


def apply_plugin_authority_tiers(
    match_scores: List[Dict[str, Any]],
    *,
    physics_meta_sink: Optional[MutableMapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """仅保留最高 ``authority_level`` 的插件分；低等级一律 SILENT_REJECT（一票否决）。"""
    rows = [r for r in (match_scores or []) if isinstance(r, dict)]
    if not rows:
        return rows
    levels = [int(r.get("authority_level") or plugin_authority_level(str(r.get("plugin_id") or ""))) for r in rows]
    mx = max(levels) if levels else 1
    kept: List[Dict[str, Any]] = []
    for r in rows:
        lv = int(r.get("authority_level") or plugin_authority_level(str(r.get("plugin_id") or "")))
        if lv == mx:
            kept.append(r)
            continue
        if physics_meta_sink is not None:
            append_physics_autonomy_log(
                physics_meta_sink,
                {
                    "kind": "SILENT_REJECT",
                    "reason": "plugin_authority_veto",
                    "plugin_id": str(r.get("plugin_id") or ""),
                    "authority_level": lv,
                    "max_authority_level": mx,
                },
            )
    return kept


def maybe_two_stage_fact_closure(
    *,
    metadata: Optional[Mapping[str, Any]],
    physics_tensor: MutableMapping[str, Any],
    match_scores: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    V13.03：同一 Fact（冲突签名）下高分插件僵持两轮仍无果时，
    强制采纳当前最高分插件、``global_conflict_tension`` 抹零并写自治日志。
    """
    meta = physics_tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return match_scores
    rows = [r for r in (match_scores or []) if isinstance(r, dict)]
    if len(rows) < 2:
        return rows
    md0 = metadata if isinstance(metadata, Mapping) else {}
    cm = md0.get("conflict_matrix") if isinstance(md0.get("conflict_matrix"), dict) else {}
    pts = cm.get("points") if isinstance(cm.get("points"), list) else []
    if pts and isinstance(pts[0], dict):
        sig = conflict_pattern_signature(
            {"kind": str((pts[0] or {}).get("kind") or ""), "detail": str((pts[0] or {}).get("detail") or "")}
        )
    else:
        sig = "_no_conflict_point_"
    cycles_raw = meta.get("v1303_fact_stalemate_cycles")
    cycles: Dict[str, int] = {str(k): int(v) for k, v in dict(cycles_raw).items()} if isinstance(cycles_raw, dict) else {}
    sc_vals = sorted([float(r.get("score") or 0.0) for r in rows], reverse=True)
    top2 = sc_vals[:2]
    stalemate = len(top2) >= 2 and top2[0] >= 0.52 and (top2[0] - top2[1]) <= 0.12
    if stalemate:
        cycles[sig] = int(cycles.get(sig, 0)) + 1
    else:
        cycles[sig] = 0
    meta["v1303_fact_stalemate_cycles"] = cycles
    n = int(cycles.get(sig, 0))
    if stalemate and n >= 2:
        winner = sorted(rows, key=lambda r: float(r.get("score") or 0.0), reverse=True)[:1]
        meta["global_conflict_tension"] = 0.0
        meta["v1303_two_stage_auto_closure_v1"] = True
        append_physics_autonomy_log(
            meta,
            {
                "kind": "TWO_STAGE_FORCE",
                "reason": "fact_stalemate_exhausted",
                "fact_signature": sig[:220],
                "cycles": n,
                "winner_plugin_id": str(winner[0].get("plugin_id") or "") if winner else "",
            },
        )
        cycles[sig] = 0
        meta["v1303_fact_stalemate_cycles"] = cycles
        return winner
    return rows


def persist_arbitration_log_to_snapshot(session: Session, *, consultation_id: int, entry: Mapping[str, Any]) -> Optional[int]:
    """将审计条目追加到该会话最近一条 ``BrainHtnSnapshot``；若无则创建占位快照。"""
    from app.db.models import BrainHtnSnapshot

    cid = int(consultation_id)
    if cid <= 0:
        return None
    payload = dict(entry)
    try:
        stmt = (
            select(BrainHtnSnapshot)
            .where(BrainHtnSnapshot.session_id == cid)
            .order_by(BrainHtnSnapshot.id.desc())  # type: ignore[union-attr]
        )
        row = session.exec(stmt).first()
        if row is not None:
            logs = list(getattr(row, "arbitration_logs", None) or [])
            logs.append(payload)
            row.arbitration_logs = logs[-100:]
            session.add(row)
            session.flush()
            return int(row.id or 0) or None
        nrow = BrainHtnSnapshot(
            session_id=cid,
            version_id=f"v12.95-audit-{uuid.uuid4().hex[:10]}",
            lineage="HTN_DRIVEN",
            assimilated=False,
            full_path=["arbitration_audit_ephemeral"],
            seeds_matched=[],
            snapshot_payload={"source": "v12.95_arbitration_audit"},
            arbitration_logs=[payload],
        )
        session.add(nrow)
        session.flush()
        return int(nrow.id or 0) or None
    except Exception:
        _LOG.warning("persist_arbitration_log_to_snapshot failed consultation_id=%s", cid, exc_info=True)
        return None


def apply_arbitration_overrule_to_client_bundle(
    *,
    audit_id: str,
    assertion_tree: Mapping[str, Any],
    metadata: Mapping[str, Any],
    arbitration_audit_feed: Sequence[Mapping[str, Any]],
    physics_meta: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    一票否决：移除对应 LAW 节点与静默历史项，恢复 ``rollback_interrupt`` 为 pending，``flow_state`` → probe_waiting。
    返回供前端 ``mergeSnapshot`` 的补丁（metadata / assertion_tree / physics_tensor.meta）。
    """
    aid = str(audit_id or "").strip()
    if not aid:
        raise ValueError("audit_id required")

    audit: Optional[Dict[str, Any]] = None
    for row in arbitration_audit_feed or []:
        if isinstance(row, dict) and str(row.get("id") or "").strip() == aid:
            audit = dict(row)
            break
    if not audit:
        raise LookupError(f"arbitration audit not found: {aid}")

    law_id = str(audit.get("law_node_id") or "").strip()
    tree = dict(assertion_tree) if isinstance(assertion_tree, dict) else {}
    nodes = [n for n in (tree.get("nodes") or []) if isinstance(n, dict)]
    edges = [e for e in (tree.get("edges") or []) if isinstance(e, dict)]

    def _node_matches(nb: Mapping[str, Any]) -> bool:
        nid = str(nb.get("node_id") or "").strip()
        if law_id and nid == law_id:
            return True
        refs = nb.get("evidence_refs") if isinstance(nb.get("evidence_refs"), list) else []
        for r in refs:
            if aid in str(r):
                return True
        return False

    drop_ids = {str(n.get("node_id")) for n in nodes if _node_matches(n)}
    nodes2 = [n for n in nodes if str(n.get("node_id")) not in drop_ids]
    edges2 = [
        e
        for e in edges
        if str(e.get("to") or "") not in drop_ids and str(e.get("from") or "") not in drop_ids
    ]
    tree["nodes"] = nodes2
    tree["edges"] = edges2
    sh = list(tree.get("silent_arbiter_history_v1") or []) if isinstance(tree.get("silent_arbiter_history_v1"), list) else []
    tree["silent_arbiter_history_v1"] = [
        x
        for x in sh
        if not (isinstance(x, dict) and (str(x.get("arbitration_audit_id") or "") == aid or str(x.get("law_node_id") or "") == law_id))
    ][-50:]

    new_feed: List[Dict[str, Any]] = []
    for row in arbitration_audit_feed or []:
        if not isinstance(row, dict):
            continue
        r = dict(row)
        if str(r.get("id") or "").strip() == aid:
            r["overruled"] = True
        new_feed.append(r)

    rb = dict(audit.get("rollback_interrupt") or {})
    if rb:
        rb["state"] = "pending"
    md = dict(metadata) if isinstance(metadata, dict) else {}
    md["flow_state"] = "probe_waiting"
    pl_raw = md.get("persistence_layer")
    pl: Dict[str, Any] = dict(pl_raw) if isinstance(pl_raw, dict) else {}
    if rb:
        pl["interrupt_request"] = rb
    md["persistence_layer"] = pl

    meta_patch: Dict[str, Any] = {}
    pm = dict(physics_meta) if isinstance(physics_meta, dict) else {}
    pm["arbitration_audit_feed_v1"] = new_feed[-30:]
    pm["silent_arbiter_history_v1"] = list(pm.get("silent_arbiter_history_v1") or []) if isinstance(pm.get("silent_arbiter_history_v1"), list) else []
    pm["silent_arbiter_history_v1"] = [
        x
        for x in (pm["silent_arbiter_history_v1"] or [])
        if not (
            isinstance(x, dict)
            and (str(x.get("arbitration_audit_id") or "") == aid or (law_id and str(x.get("law_node_id") or "") == law_id))
        )
    ][-50:]
    meta_patch = pm

    return {
        "ok": True,
        "audit_id": aid,
        "assertion_tree": tree,
        "metadata": md,
        "physics_meta_patch": meta_patch,
    }


class DecisionInboxFeedbackCollector:
    """V14.00：Inbox 逐步操作 → Logical_Patch 累积，供下一轮终判 Prompt 注入。"""

    PROTO = "logical_patch.v14"

    @staticmethod
    def append_logical_patch(meta: MutableMapping[str, Any], patch: Mapping[str, Any]) -> Dict[str, Any]:
        ic = meta.setdefault("incremental_context_v14", {})
        if not isinstance(ic, dict):
            ic = {}
            meta["incremental_context_v14"] = ic
        lp = list(ic.get("logical_patches") or [])
        row: Dict[str, Any] = {
            "protocol": DecisionInboxFeedbackCollector.PROTO,
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            **dict(patch),
        }
        lp.append(row)
        ic["logical_patches"] = lp[-64:]
        DecisionEvolutionFrameProtocol.append_frame(
            meta,
            source_id="decision_inbox",
            content_delta=f"logical_patch:{str(patch.get('action') or patch.get('kind') or 'update')}",
            layer="PLUGIN",
            payload={
                "render_text": f"策略补丁已记录：{str(patch.get('action') or patch.get('kind') or 'update')}",
                "protocol": "decision_inbox_patch.v16_2",
            },
        )
        return row

    @staticmethod
    def record_inbox_step(
        meta: MutableMapping[str, Any],
        *,
        action: str,
        payload: Mapping[str, Any],
        conflict_signature: str = "",
    ) -> Dict[str, Any]:
        patch = {
            "kind": "decision_inbox",
            "action": str(action),
            "payload": dict(payload),
            "conflict_signature": str(conflict_signature)[:200],
        }
        return DecisionInboxFeedbackCollector.append_logical_patch(meta, patch)

    @staticmethod
    def apply_checkbox_to_m5_will(
        meta: MutableMapping[str, Any],
        *,
        plugin_id: str,
        checked: bool,
        delta: float = 0.15,
    ) -> None:
        """Inbox 勾选 → M5 意志微调：写入 plugin_weight_deltas，与终判 plugin_weights 合并。"""
        w = meta.setdefault("m5_will_anchor_v14", {})
        if not isinstance(w, dict):
            w = {}
            meta["m5_will_anchor_v14"] = w
        deltas = dict(w.get("plugin_weight_deltas") or {})
        pid = str(plugin_id).strip()
        if not pid:
            return
        try:
            d = float(delta)
        except (TypeError, ValueError):
            d = 0.15
        cur = float(deltas.get(pid, 0.0))
        if checked:
            deltas[pid] = cur + d
        else:
            deltas[pid] = max(0.0, cur - d)
        w["plugin_weight_deltas"] = deltas
        w["last_inbox_plugin_id"] = pid
        w["last_inbox_checked"] = bool(checked)


class DecisionImpactContext:
    """V14.01 决策影响因子 Registry：收集 Inbox 的 ACK / IGNORE / PATCH，驱动 Prompt 与物理二次刷新。"""

    REGISTRY_KEY = "decision_impact_registry_v14_01"
    PROTO = "decision_impact.v14_01"

    @staticmethod
    def _reg(meta: MutableMapping[str, Any]) -> Dict[str, Any]:
        r = meta.setdefault(DecisionImpactContext.REGISTRY_KEY, {})
        if not isinstance(r, dict):
            r = {}
            meta[DecisionImpactContext.REGISTRY_KEY] = r
        r.setdefault("events", [])
        r.setdefault("pending_sql_patches", [])
        return r

    @staticmethod
    def record_ack(
        meta: MutableMapping[str, Any],
        *,
        subject: str,
        note: str = "",
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        reg = DecisionImpactContext._reg(meta)
        ev: Dict[str, Any] = {
            "protocol": DecisionImpactContext.PROTO,
            "verb": "ACK",
            "subject": str(subject)[:240],
            "note": str(note)[:480],
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        if extra:
            ev["extra"] = dict(extra)
        reg["events"] = (list(reg.get("events") or []) + [ev])[-96:]
        DecisionEvolutionFrameProtocol.append_frame(
            meta,
            source_id="user_will.ack",
            content_delta=str(subject)[:160],
            layer="ACTION_TAKEN",
            payload={
                "note": note,
                "extra": dict(extra or {}),
                "render_text": f"已采纳「{str(subject)[:80]}」，正在按意志重构判词。",
            },
        )
        return ev

    @staticmethod
    def record_ignore(
        meta: MutableMapping[str, Any],
        *,
        subject: str,
        note: str = "",
        conflict_signature: str = "",
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        reg = DecisionImpactContext._reg(meta)
        ev: Dict[str, Any] = {
            "protocol": DecisionImpactContext.PROTO,
            "verb": "IGNORE",
            "subject": str(subject)[:240],
            "note": str(note)[:480],
            "conflict_signature": str(conflict_signature)[:200],
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        if extra:
            ev["extra"] = dict(extra)
        reg["events"] = (list(reg.get("events") or []) + [ev])[-96:]
        DecisionEvolutionFrameProtocol.append_frame(
            meta,
            source_id="user_will.ignore",
            content_delta=str(subject)[:160],
            layer="ACTION_TAKEN",
            payload={
                "note": note,
                "conflict_signature": conflict_signature,
                "extra": dict(extra or {}),
                "render_text": f"已忽略「{str(subject)[:80]}」，正在按意志改写结论。",
            },
        )
        return ev

    @staticmethod
    def record_patch(
        meta: MutableMapping[str, Any],
        *,
        sql_patch: str = "",
        narrative: str = "",
        note: str = "",
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """PATCH：可携带 physics_interaction_params 的 sql_patch；将进入 pending，终判前由 audit_helpers 静默合并并重算 L1。"""
        reg = DecisionImpactContext._reg(meta)
        ev: Dict[str, Any] = {
            "protocol": DecisionImpactContext.PROTO,
            "verb": "PATCH",
            "narrative": str(narrative)[:520],
            "note": str(note)[:480],
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        if extra:
            ev["extra"] = dict(extra)
        sp = _decision_inbox_sql_filter(str(sql_patch or "").strip())
        if sp:
            ev["sql_patch"] = sp
            pend = list(reg.get("pending_sql_patches") or [])
            pend.append(sp)
            reg["pending_sql_patches"] = pend[-16:]
        reg["events"] = (list(reg.get("events") or []) + [ev])[-96:]
        DecisionEvolutionFrameProtocol.append_frame(
            meta,
            source_id="user_will.patch",
            content_delta=str(narrative or note or sp or "patch")[:160],
            layer="ACTION_TAKEN",
            payload={
                "sql_patch": sp,
                "note": note,
                "extra": dict(extra or {}),
                "render_text": "参数补丁已提交，正在依据最新意志进行实时裁断。",
            },
        )
        return ev


# 规格文档中的命名（下划线式），便于检索
Decision_Impact_Context = DecisionImpactContext


class DecisionEvolutionFrameProtocol:
    """V14 帧协议：记录断言演化帧，并支持帧回溯。"""

    FRAMES_KEY = "assertion_evolution_frames_v14"

    @staticmethod
    def append_frame(
        meta: MutableMapping[str, Any],
        *,
        source_id: str,
        content_delta: str,
        layer: str = "PLUGIN",
        payload: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        frames = list(meta.get(DecisionEvolutionFrameProtocol.FRAMES_KEY) or [])
        row: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "source_id": str(source_id or "unknown")[:120],
            "content_delta": str(content_delta or "")[:2000],
            "layer": str(layer or "PLUGIN").upper(),
        }
        if payload:
            safe_payload = guard_narrative_payload(payload, layer=str(layer or "PLUGIN").upper())
            if safe_payload:
                row["payload"] = safe_payload
        frames.append(row)
        meta[DecisionEvolutionFrameProtocol.FRAMES_KEY] = frames[-240:]
        return row

    @staticmethod
    def backtrace(meta: Mapping[str, Any], *, max_items: int = 80) -> List[Dict[str, Any]]:
        rows = [x for x in (meta.get(DecisionEvolutionFrameProtocol.FRAMES_KEY) or []) if isinstance(x, dict)]
        n = max(1, min(int(max_items or 80), 240))
        return [sanitize_frame_for_client(x) for x in rows[-n:]]

    @staticmethod
    def priority_overwrite_view(meta: Mapping[str, Any]) -> Dict[str, Any]:
        """优先级覆盖：Physics 底噪 + Plugin 补丁 + User Will 蒙版。"""
        reg = meta.get(DecisionImpactContext.REGISTRY_KEY) if isinstance(meta.get(DecisionImpactContext.REGISTRY_KEY), dict) else {}
        events = [e for e in (reg.get("events") or []) if isinstance(e, dict)]
        return {
            "physics_base_noise": "always_on",
            "plugin_patch_strength": len([f for f in (meta.get(DecisionEvolutionFrameProtocol.FRAMES_KEY) or []) if isinstance(f, dict) and str(f.get("layer") or "").upper() == "PLUGIN"]),
            "user_will_mask_strength": len([e for e in events if str(e.get("verb") or "").upper() in {"ACK", "IGNORE", "PATCH"}]),
            "protocol": "priority_overwrite.v14",
        }


class NarrativeFragmentCollector:
    """V14.30：从插件事实中收集 narrative_fragment，并立即落为 PLUGIN 帧。"""

    @staticmethod
    def _coerce_fragment_from_fact(fact: Mapping[str, Any]) -> str:
        raw = str(fact.get("narrative_fragment") or "").strip()
        if raw:
            return raw
        txt = str(fact.get("text") or fact.get("detail") or fact.get("fact") or "").strip()
        if txt:
            return f"事实推断：{txt[:160]}"
        return "事实推断：插件返回了有效 Fact。"

    @staticmethod
    def _collect_plugin_fact_rows(physics_tensor: MutableMapping[str, Any]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        po = physics_tensor.get("plugin_outputs") if isinstance(physics_tensor.get("plugin_outputs"), dict) else {}
        for pid, row in po.items():
            if not isinstance(row, dict):
                continue
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            facts = payload.get("facts")
            if isinstance(facts, list):
                for idx, f in enumerate(facts):
                    if not isinstance(f, dict):
                        continue
                    frag = NarrativeFragmentCollector._coerce_fragment_from_fact(f)
                    # V15.0：强制插件 Fact 携带 narrative_fragment（最小约束写回）
                    if not str(f.get("narrative_fragment") or "").strip():
                        f["narrative_fragment"] = frag
                        facts[idx] = f
                    out.append(
                        {
                            "source_id": f"plugin:{str(pid)}",
                            "narrative_fragment": frag,
                            "fact": dict(f),
                        }
                    )
            # 兼容 evidence 列表
            evidence = payload.get("evidence")
            if isinstance(evidence, list):
                for ev in evidence[:6]:
                    s = str(ev or "").strip()
                    if not s:
                        continue
                    out.append(
                        {
                            "source_id": f"plugin:{str(pid)}",
                            "narrative_fragment": f"证据片段：{s[:160]}",
                            "fact": {"text": s},
                        }
                    )
        return out

    @staticmethod
    async def collect_and_emit(meta: MutableMapping[str, Any], physics_tensor: MutableMapping[str, Any]) -> List[Dict[str, Any]]:
        rows = NarrativeFragmentCollector._collect_plugin_fact_rows(physics_tensor)
        if not rows:
            return []
        buf = list(meta.get("narrative_fragments_v14") or [])
        for r in rows:
            frag = str(r.get("narrative_fragment") or "").strip()
            if not frag:
                continue
            item = {
                "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "source_id": str(r.get("source_id") or "plugin:unknown"),
                "narrative_fragment": frag,
            }
            buf.append(item)
            # V16.1: 所有上屏句子必须经过叙事管线（sanitize + micro llm + polarization）。
            rt = await compose_realtime_narration(
                metadata=dict(meta),
                physics_tensor=dict(physics_tensor) if isinstance(physics_tensor, dict) else {},
                lang="ZH",
                max_chars=220,
            )
            rt_text = str(rt.get("text") or "").strip()
            if rt_text:
                DecisionEvolutionFrameProtocol.append_frame(
                    meta,
                    source_id=str(item["source_id"]),
                    content_delta=rt_text,
                    layer="PLUGIN",
                    payload={
                        "protocol": "narrative_fragment.v16_1",
                        "render_text": rt_text,
                    },
                )
                DecisionEvolutionFrameProtocol.append_frame(
                    meta,
                    source_id="realtime_narrator:v15",
                    content_delta=rt_text,
                    layer="NARRATOR",
                    payload={
                        "protocol": str(rt.get("protocol") or "realtime_narrator.v16_1"),
                        "will_proxy": str(rt.get("will_proxy") or ""),
                        "trigger": "fact_ingest_sync",
                        "render_text": rt_text,
                    },
                )
        meta["narrative_fragments_v14"] = buf[-240:]
        return [x for x in buf[-len(rows):] if isinstance(x, dict)]


__all__ = [
    "NarrativeFragmentCollector",
    "DecisionEvolutionFrameProtocol",
    "DecisionImpactContext",
    "DecisionInboxFeedbackCollector",
    "Decision_Impact_Context",
    "append_arbitration_audit_feed",
    "append_physics_autonomy_log",
    "append_silent_arbiter_meta",
    "apply_arbitration_overrule_to_client_bundle",
    "apply_physical_sanity_check",
    "apply_plugin_authority_tiers",
    "build_arbitration_audit_entry",
    "build_arbitration_physics_context",
    "build_arbitration_theme",
    "conflict_display_name",
    "conflict_matches_ledger_patterns",
    "conflict_pattern_signature",
    "load_gold_arbiter_matching",
    "load_gold_arbiter_pattern_keys",
    "merge_silent_arbiter_into_assertion_tree",
    "maybe_two_stage_fact_closure",
    "persist_arbitration_log_to_snapshot",
    "should_auto_resolve",
]
