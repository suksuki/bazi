from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
KNOWLEDGE_ROOT = PROJECT_ROOT / "docs" / "bazi_knowledge"
TAXONOMY_FILE = KNOWLEDGE_ROOT / "catalog" / "bazi_knowledge_taxonomy_master_zh_v1.md"
MANIFEST_FILE = KNOWLEDGE_ROOT / "catalog" / "knowledge_base_v2_manifest.json"
KNOWLEDGE_DRAFT_SEED_FILE = KNOWLEDGE_ROOT / "database" / "current_knowledge_draft_seeds_v1.json"
KNOWLEDGE_DRAFT_PACK_DIR = KNOWLEDGE_ROOT / "packs"

P31_ALL_KNOWLEDGE_COVERAGE_AUDIT_VERSION = "v19.p31.all_knowledge_coverage_audit.v1"
P31_GUARDRAILS = [
    "AUDIT_ONLY",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_KNOWLEDGE_REWRITE",
    "NEW_FRAMEWORK_FIT_REVIEW",
    "MISSING_TOPICS_TO_BACKLOG",
    "NO_FORTUNE",
]

STATUS_ORDER = {"已有": 0, "部分": 1, "缺失": 2, "归档": 3, "后置": 4}
HIGH_PRIORITY = {"P0", "P1"}


def run_p31_all_knowledge_coverage_audit() -> Dict[str, Any]:
    taxonomy_items = _parse_taxonomy_items()
    drafts = _load_all_knowledge_drafts()
    directory_report = _directory_coverage(taxonomy_items)
    gap_backlog = _gap_backlog(taxonomy_items, drafts)
    framework_fit = _framework_fit_summary(taxonomy_items)
    migration_batches = _migration_batches(gap_backlog)
    high_priority_gaps = [row for row in gap_backlog if row["priority"] in HIGH_PRIORITY]
    return {
        "ok": True,
        "version": P31_ALL_KNOWLEDGE_COVERAGE_AUDIT_VERSION,
        "status": "audit_ready_gaps_found" if high_priority_gaps else "audit_ready",
        "summary": {
            "taxonomy_item_count": len(taxonomy_items),
            "knowledge_draft_count": len(drafts),
            "expected_directory_count": len(directory_report["expected_directories"]),
            "existing_directory_count": len(directory_report["existing_directories"]),
            "missing_directory_count": len(directory_report["missing_directories"]),
            "gap_backlog_count": len(gap_backlog),
            "high_priority_gap_count": len(high_priority_gaps),
            "p0_gap_count": sum(1 for row in gap_backlog if row["priority"] == "P0"),
            "p1_gap_count": sum(1 for row in gap_backlog if row["priority"] == "P1"),
            "by_taxonomy_status": _count_by(taxonomy_items, "status"),
            "by_priority": _count_by(taxonomy_items, "priority"),
            "drafts_by_domain": _count_by(drafts, "domain"),
            "drafts_by_risk": _count_by(drafts, "risk_level"),
        },
        "directory_report": directory_report,
        "taxonomy_items": taxonomy_items,
        "domain_review": _domain_review(taxonomy_items, drafts),
        "gap_backlog": gap_backlog,
        "framework_fit": framework_fit,
        "migration_policy": {
            "decision": "dual_track_forward_first_then_backfill",
            "new_knowledge": "Use condition models, positive/negative eval samples, shadow gates, internal scoring, and arbitration when the topic has mechanism behavior.",
            "old_knowledge": "Do not big-bang rewrite. Backfill only when a topic is touched or before activation.",
            "r3_r4": "Keep archive-only unless a neutral structure label can be extracted.",
        },
        "migration_batches": migration_batches,
        "guardrails": P31_GUARDRAILS,
    }


def _parse_taxonomy_items() -> List[Dict[str, Any]]:
    if not TAXONOMY_FILE.exists():
        return []
    items: List[Dict[str, Any]] = []
    current_layer = ""
    for raw_line in TAXONOMY_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## L"):
            current_layer = line.lstrip("#").strip()
            continue
        if not line.startswith("|") or "---" in line or "类别" in line:
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        status = cells[2]
        priority = cells[3]
        if status not in STATUS_ORDER or not priority.startswith("P"):
            continue
        items.append(
            {
                "layer": current_layer,
                "topic": cells[0],
                "directory": cells[1],
                "status": status,
                "priority": priority,
                "note": cells[4],
                "expected_directories": _split_directories(cells[1]),
                "framework_track": _framework_track(cells[0], cells[1], status, priority, cells[4]),
            }
        )
    return items


def _load_all_knowledge_drafts() -> List[Dict[str, Any]]:
    seed_files = [KNOWLEDGE_DRAFT_SEED_FILE]
    if KNOWLEDGE_DRAFT_PACK_DIR.exists():
        seed_files.extend(sorted(KNOWLEDGE_DRAFT_PACK_DIR.glob("*_knowledge_draft_seeds_*.json")))
    rows: List[Dict[str, Any]] = []
    for seed_file in seed_files:
        rows.extend(_load_draft_seed_file(seed_file))
    return rows


def _load_draft_seed_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    pack_id = str(data.get("pack_id") or path.stem) if isinstance(data, dict) else path.stem
    rows = data.get("knowledge_drafts") if isinstance(data, dict) else []
    out = []
    for row in rows or []:
        if isinstance(row, dict):
            item = dict(row)
            item["source_pack_id"] = pack_id
            item["source_seed_file"] = str(path.relative_to(PROJECT_ROOT))
            out.append(item)
    return out


def _directory_coverage(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    expected = sorted({directory for item in items for directory in item.get("expected_directories") or []})
    existing = [directory for directory in expected if (KNOWLEDGE_ROOT / directory).exists()]
    missing = [directory for directory in expected if directory not in set(existing)]
    return {
        "expected_directories": expected,
        "existing_directories": existing,
        "missing_directories": missing,
        "expected_directory_count": len(expected),
        "existing_directory_count": len(existing),
        "missing_directory_count": len(missing),
        "missing_high_priority": _missing_high_priority_directories(items, set(existing)),
    }


def _missing_high_priority_directories(items: List[Dict[str, Any]], existing: set[str]) -> List[Dict[str, str]]:
    rows = []
    seen = set()
    for item in items:
        if item.get("priority") not in HIGH_PRIORITY:
            continue
        for directory in item.get("expected_directories") or []:
            if directory in existing or directory in seen:
                continue
            seen.add(directory)
            rows.append({"directory": directory, "first_topic": item["topic"], "priority": item["priority"], "layer": item["layer"]})
    return rows


def _gap_backlog(items: List[Dict[str, Any]], drafts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing_dirs = {path for path in _directory_coverage(items)["existing_directories"]}
    domain_counts = _count_by(drafts, "domain")
    rows = []
    for item in items:
        if item["status"] not in {"缺失", "部分"}:
            continue
        missing_dirs = [directory for directory in item.get("expected_directories") or [] if directory not in existing_dirs]
        rows.append(
            {
                "topic": item["topic"],
                "layer": item["layer"],
                "directory": item["directory"],
                "status": item["status"],
                "priority": item["priority"],
                "missing_directories": missing_dirs,
                "domain_has_drafts": _domain_has_drafts(item, domain_counts),
                "recommended_action": _recommended_action(item, missing_dirs),
                "framework_track": item["framework_track"],
            }
        )
    rows.sort(key=lambda row: (row["priority"], STATUS_ORDER.get(row["status"], 9), row["layer"], row["topic"]))
    return rows


def _domain_review(items: List[Dict[str, Any]], drafts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    domain_counts = _count_by(drafts, "domain")
    risk_by_domain: Dict[str, Dict[str, int]] = {}
    for draft in drafts:
        domain = str(draft.get("domain") or "unknown")
        risk_by_domain.setdefault(domain, {})
        risk = str(draft.get("risk_level") or "unknown")
        risk_by_domain[domain][risk] = risk_by_domain[domain].get(risk, 0) + 1
    directories = sorted({directory for item in items for directory in item.get("expected_directories") or []})
    rows = []
    for directory in directories:
        directory_items = [item for item in items if directory in (item.get("expected_directories") or [])]
        domain = directory.split("/", 1)[0]
        rows.append(
            {
                "directory": directory,
                "domain_guess": domain,
                "taxonomy_item_count": len(directory_items),
                "draft_count": int(domain_counts.get(_domain_from_directory(domain), 0) or 0),
                "by_status": _count_by(directory_items, "status"),
                "by_priority": _count_by(directory_items, "priority"),
                "risk_levels": risk_by_domain.get(_domain_from_directory(domain), {}),
                "coverage_state": _coverage_state(directory_items),
                "next_action": _domain_next_action(directory, directory_items),
            }
        )
    return rows


def _framework_fit_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for track in sorted({item["framework_track"] for item in items}):
        track_items = [item for item in items if item["framework_track"] == track]
        rows.append(
            {
                "track": track,
                "count": len(track_items),
                "p0_p1_count": sum(1 for item in track_items if item["priority"] in HIGH_PRIORITY),
                "by_status": _count_by(track_items, "status"),
            }
        )
    return {"tracks": rows, "by_track": {row["track"]: row["count"] for row in rows}}


def _migration_batches(gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    p0 = [row for row in gaps if row["priority"] == "P0"]
    p1 = [row for row in gaps if row["priority"] == "P1"]
    return [
        {
            "batch": "P31A_foundation_gap_seed_packs",
            "scope": "P0 missing/partial knowledge",
            "item_count": len(p0),
            "topics": [row["topic"] for row in p0[:20]],
            "action": "Create or expand seed packs before rule conversion.",
        },
        {
            "batch": "P31B_priority_condition_models",
            "scope": "P1 missing/partial mechanism and relation knowledge",
            "item_count": len(p1),
            "topics": [row["topic"] for row in p1[:20]],
            "action": "Add condition axes and synthetic samples after P0 directories exist.",
        },
        {
            "batch": "P31C_archive_and_later_domains",
            "scope": "P2-P4 and archive-only knowledge",
            "item_count": len([row for row in gaps if row["priority"] not in HIGH_PRIORITY]),
            "action": "Keep as backlog unless a current topic touches it.",
        },
    ]


def _framework_track(topic: str, directory: str, status: str, priority: str, note: str) -> str:
    text = f"{topic} {directory} {note}"
    if status in {"归档", "后置"} or priority in {"P3", "P4"}:
        return "archive_or_defer"
    if any(key in text for key in ["格局", "强弱", "引动", "机制", "用神", "财", "官", "杀", "印", "食", "伤", "比劫", "宫位与十神"]):
        return "condition_model_eval_gate"
    if any(key in text for key in ["出生地", "时区", "经纬度", "真太阳时", "夏令时", "地理"]):
        return "metadata_boundary_rule"
    if any(key in text for key in ["盲派", "象法", "口诀", "神煞", "纳音"]):
        return "archive_first_neutral_tags_only"
    return "metadata_seed_rule_candidate"


def _split_directories(raw: str) -> List[str]:
    cleaned = raw.replace("`", " ").replace(",", " ").replace("，", " ")
    out = []
    for part in cleaned.split():
        value = part.strip().strip("|").strip()
        if not value.endswith("/"):
            continue
        out.append(value.rstrip("/"))
    return out


def _domain_from_directory(directory: str) -> str:
    return {
        "core": "core_structure",
        "time_context": "luck_flow",
        "interaction": "interaction",
        "pattern": "pattern",
        "strength": "strength",
        "ten_god": "ten_god",
        "wealth": "wealth",
        "geo_context": "geo_context",
        "answer_expression": "answer_expression",
        "palace": "palace",
        "blind": "blind",
    }.get(directory, directory)


def _domain_has_drafts(item: Dict[str, Any], domain_counts: Dict[str, int]) -> bool:
    for directory in item.get("expected_directories") or []:
        domain = _domain_from_directory(directory.split("/", 1)[0])
        if int(domain_counts.get(domain, 0) or 0) > 0:
            return True
    return False


def _recommended_action(item: Dict[str, Any], missing_dirs: List[str]) -> str:
    if item["status"] == "缺失" and missing_dirs:
        return "create_directory_and_seed_pack"
    if item["status"] == "缺失":
        return "create_seed_pack"
    if item["framework_track"] == "condition_model_eval_gate":
        return "expand_condition_model_and_eval_samples"
    if item["framework_track"] == "archive_first_neutral_tags_only":
        return "archive_first_extract_neutral_tags"
    return "expand_existing_knowledge_units"


def _coverage_state(items: List[Dict[str, Any]]) -> str:
    statuses = {item["status"] for item in items}
    if statuses <= {"已有"}:
        return "covered"
    if "缺失" in statuses:
        return "has_missing"
    if "部分" in statuses:
        return "partial"
    if statuses & {"归档", "后置"}:
        return "archive_or_defer"
    return "unknown"


def _domain_next_action(directory: str, items: List[Dict[str, Any]]) -> str:
    if not (KNOWLEDGE_ROOT / directory).exists():
        return "create_directory"
    if any(item["status"] == "缺失" and item["priority"] in HIGH_PRIORITY for item in items):
        return "seed_high_priority_missing_topics"
    if any(item["status"] == "部分" and item["priority"] in HIGH_PRIORITY for item in items):
        return "expand_high_priority_partial_topics"
    return "maintain_or_defer"


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
