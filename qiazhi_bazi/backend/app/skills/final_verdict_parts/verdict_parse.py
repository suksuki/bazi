from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.skills.final_verdict_parts.json_extract import coerce_verdict_body_display
from app.skills.final_verdict_parts.narrative_guard import evidence_ref_allowed_for_verdict_parse

_EARTHLY: Set[str] = set("子丑寅卯辰巳午未申酉戌亥")
_PILLAR_KEYS = ("year", "month", "day", "hour")


def _heuristic_evidence_refs(text: str, metadata: Dict[str, Any]) -> List[str]:
    """LLM Markdown/JSON 不标准时，用关键词与柱支共现补全 evidence_refs。"""
    refs: List[str] = []
    if not text or not isinstance(metadata, dict):
        return refs
    pillars = metadata.get("pillars")
    if isinstance(pillars, dict):
        for pk in _PILLAR_KEYS:
            col = pillars.get(pk)
            if not isinstance(col, dict):
                continue
            br = str(col.get("branch") or "").strip()
            st = str(col.get("stem") or "").strip()
            if br and br in text:
                refs.extend((f"{pk}.branch", f"branch.{br}", f"{pk}.pillar"))
            if st and st in text:
                refs.append(f"{pk}.stem")
                if br:
                    refs.append(f"{pk}.pillar")
    for ch in text:
        if ch in _EARTHLY:
            refs.append(f"branch.{ch}")
    cm = (metadata.get("conflict_matrix") or {}).get("points") or []
    if isinstance(cm, list):
        for p in cm:
            if not isinstance(p, dict):
                continue
            pid = str(p.get("id") or "").strip()
            detail = str(p.get("detail") or "")
            if not pid:
                continue
            if detail and detail in text:
                refs.append(f"conflict_matrix.{pid}")
                continue
            if detail and len(detail) >= 2:
                for i in range(len(detail) - 1):
                    if detail[i : i + 2] in text:
                        refs.append(f"conflict_matrix.{pid}")
                        break
    low = text.lower()
    if "盲派" in text or "blind" in low or "mangpai" in low:
        refs.append("plugin.classical.blind_school.v1")
    if "旺衰" in text or "wangshuai" in low:
        refs.append("plugin.classical.wangshuai.v1")
    if "财" in text and ("风险" in text or "现金流" in text or "wealth" in low):
        refs.append("plugin.modern.wealth_risk.v1")
    if "伤官" in text or "正官" in text or "junction" in low or "l1" in low:
        refs.append("plugin.sys.core.physics")
    # 显式锚点串（弱模型偶发写在正文里）
    for m in re.finditer(
        r"(?:conflict_matrix\.[\w.-]+|(?:year|month|day|hour)\.(?:branch|stem|pillar)|plugin\.[\w.]+\.v\d+)",
        text,
    ):
        refs.append(m.group(0))
    for m in re.finditer(r"\bVF\d+\b", text, flags=re.IGNORECASE):
        refs.append(m.group(0).upper())
    return sorted(set(refs))[:48]


def _merge_evidence_refs_into_row(row: Dict[str, Any], metadata: Dict[str, Any]) -> None:
    base = [str(x).strip() for x in (row.get("evidence_refs") or []) if str(x).strip()]
    extra = _heuristic_evidence_refs(str(row.get("text") or ""), metadata)
    merged = sorted(set(base) | set(extra))[:48]
    allowed = [r for r in merged if evidence_ref_allowed_for_verdict_parse(r)]
    row["evidence_refs"] = allowed if allowed else merged[:48]


def _normalize_assertion_row(raw: Dict[str, Any], idx: int) -> Optional[Dict[str, Any]]:
    text = coerce_verdict_body_display(str(raw.get("text") or raw.get("assertion") or "").strip())
    if not text:
        return None
    aid = str(raw.get("assertion_id") or raw.get("id") or f"a{idx}").strip() or f"a{idx}"
    refs_raw = raw.get("evidence_refs") or raw.get("refs") or raw.get("anchors") or []
    refs = [str(x).strip() for x in (refs_raw if isinstance(refs_raw, list) else []) if str(x).strip()]
    return {"assertion_id": aid, "text": text[:8000], "evidence_refs": refs[:48]}


def parse_verdict_anchor_layer(
    obj: Dict[str, Any],
    *,
    verdict_body: str,
    version_id: str,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """解析 LLM JSON 的 assertions[]；缺省或非标准时用语义块 + 启发式补全 evidence_refs。"""
    md = metadata if isinstance(metadata, dict) else {}
    raw_list = obj.get("assertions")
    rows: List[Dict[str, Any]] = []
    if isinstance(raw_list, list):
        for i, item in enumerate(raw_list):
            if not isinstance(item, dict):
                if isinstance(item, str) and item.strip():
                    st = coerce_verdict_body_display(str(item).strip())
                    if st:
                        rows.append(
                            {
                                "assertion_id": f"a{i}",
                                "text": st[:8000],
                                "evidence_refs": [],
                            }
                        )
                continue
            row = _normalize_assertion_row(item, i)
            if row:
                rows.append(row)
    if not rows and verdict_body.strip():
        from app.skills.final_verdict_parts.narrative_anchors import build_verdict_narrative_chunks

        for i, ch in enumerate(build_verdict_narrative_chunks(verdict_body, md)):
            refs: List[str] = []
            for pk in ch.get("pillar_keys") or []:
                refs.append(f"{pk}.pillar")
            for cid in ch.get("conflict_point_ids") or []:
                refs.append(f"conflict_matrix.{cid}")
            for br in ch.get("branch_chars") or []:
                if br:
                    refs.append(f"branch.{br}")
            rows.append(
                {
                    "assertion_id": str(ch.get("chunk_id") or f"h{i}"),
                    "text": str(ch.get("text") or "")[:8000],
                    "evidence_refs": sorted(set(refs))[:48],
                }
            )
    for row in rows:
        _merge_evidence_refs_into_row(row, md)
    return {"narrative_version_id": str(version_id or ""), "assertions": rows}


def parse_verdict_body_and_changelog(obj: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """从 LLM JSON 对象解析 verdict_body 与规范化 change_log。"""
    verdict_body = str(obj.get("verdict_body") or "").strip()
    raw_change_log = obj.get("change_log")
    if isinstance(raw_change_log, dict):
        change_log: Dict[str, Any] = {
            "physics_diff": [str(x).strip() for x in (raw_change_log.get("physics_diff") or []) if str(x).strip()],
            "consensus_diff": [str(x).strip() for x in (raw_change_log.get("consensus_diff") or []) if str(x).strip()],
            "text_diff_hint": str(raw_change_log.get("text_diff_hint") or "").strip(),
        }
    else:
        legacy: List[Any] = raw_change_log if isinstance(raw_change_log, list) else []
        change_log = {
            "physics_diff": [],
            "consensus_diff": [],
            "text_diff_hint": "；".join([str(x).strip() for x in legacy if str(x).strip()][:2]),
        }
    return verdict_body, change_log
