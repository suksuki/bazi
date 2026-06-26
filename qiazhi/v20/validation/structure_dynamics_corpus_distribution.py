from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from v20.api.runtime import run_runtime_from_pillars
from v20.corpus.enumerator import FULL_CORPUS_CASE_COUNT, canonical_case_at
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.structure_dynamics_knowledge_coverage import build_structure_dynamics_knowledge_coverage_report


STRUCTURE_DYNAMICS_CORPUS_DISTRIBUTION_VERSION = "v20.structure_dynamics_corpus_distribution.v1"


def build_structure_dynamics_corpus_distribution(
    *,
    start: int = 0,
    limit: int = 64,
    run_id: str = "",
    write: bool = False,
    runtime_dir: Path | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if start < 0 or start >= FULL_CORPUS_CASE_COUNT:
        raise ValueError(f"start out of range: {start}")
    if limit <= 0:
        raise ValueError("limit must be positive")
    safe_limit = min(limit, FULL_CORPUS_CASE_COUNT - start)
    safe_run_id = _safe_run_id(run_id) or _default_run_id()
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    labels: Counter[str] = Counter()
    semantic_labels: Counter[str] = Counter()
    states: Counter[str] = Counter()
    chain_keys: Counter[str] = Counter()
    day_masters: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []
    examples: dict[str, list[dict[str, Any]]] = {}

    for offset in range(safe_limit):
        index = start + offset
        case = canonical_case_at(index)
        try:
            result = run_runtime_from_pillars(
                *case.pillar_displays,
                input_id=case.case_id,
                flow_year_pillar=case.time_pillars.get("flow_year", ""),
                luck_pillar=case.time_pillars.get("luck", ""),
                flow_month_pillar=case.time_pillars.get("flow_month", ""),
            )
            chart = result.get("chart_facts", {}) if isinstance(result.get("chart_facts"), dict) else {}
            structure = result.get("structure_dynamics", {}) if isinstance(result.get("structure_dynamics"), dict) else {}
            row = _structure_row(index=index, case_id=case.case_id, pillars=case.pillar_displays, structure=structure)
            label = str(row.get("label", ""))
            if label:
                labels[label] += 1
                examples.setdefault(label, [])
                if len(examples[label]) < 3:
                    examples[label].append(row)
            else:
                failures.append({"index": index, "case_id": case.case_id, "failure": "missing_structure_label"})
            state = str(row.get("state", ""))
            if state:
                states[state] += 1
            chain_key = str(row.get("chain_key", ""))
            if chain_key:
                chain_keys[chain_key] += 1
            day_master = str(chart.get("day_master", ""))
            if day_master:
                day_masters[day_master] += 1
            for semantic in row.get("semantic_labels", ()):
                semantic_labels[str(semantic)] += 1
        except Exception as exc:  # pragma: no cover - defensive long-run resilience
            failures.append({"index": index, "case_id": case.case_id, "failure": str(exc)})
        if progress and ((offset + 1) == safe_limit or (offset + 1) % max(1, min(50, safe_limit)) == 0):
            progress(f"structure corpus distribution {offset + 1}/{safe_limit}")

    path_distribution = {
        "version": "v20.structure_dynamics_corpus_path_distribution.v1",
        "status": "ready" if not failures else "partial_ready",
        "case_count": safe_limit,
        "pass_rate": round((safe_limit - len(failures)) / max(1, safe_limit), 4),
        "label_distribution": _counter_rows(labels),
        "semantic_distribution": _counter_rows(semantic_labels),
        "state_distribution": _counter_rows(states),
        "runtime_mutation": False,
    }
    knowledge_coverage = build_structure_dynamics_knowledge_coverage_report(path_distribution=path_distribution)
    payload = {
        "version": STRUCTURE_DYNAMICS_CORPUS_DISTRIBUTION_VERSION,
        "status": "completed" if not failures else "completed_with_findings",
        "run_id": safe_run_id,
        "start": start,
        "limit": safe_limit,
        "target_count": FULL_CORPUS_CASE_COUNT,
        "coverage_ratio": round(safe_limit / FULL_CORPUS_CASE_COUNT, 6),
        "label_distribution": _counter_rows(labels),
        "semantic_distribution": _counter_rows(semantic_labels),
        "state_distribution": _counter_rows(states),
        "chain_distribution": _counter_rows(chain_keys),
        "day_master_distribution": _counter_rows(day_masters),
        "knowledge_coverage": knowledge_coverage,
        "unsupported_label_count": int(knowledge_coverage.get("unsupported_count", 0) or 0),
        "unsupported_labels": knowledge_coverage.get("unsupported_labels", []),
        "example_cases_by_label": examples,
        "failure_count": len(failures),
        "failures": failures[:20],
        "artifact_path": str(_artifact_root(runtime_dir) / f"{safe_run_id}.json"),
        "run_path": str(_artifact_root(runtime_dir) / f"{safe_run_id}.json"),
        "latest_path": str(_artifact_root(runtime_dir) / "latest.json"),
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "runtime_mutation": write,
        "guardrails": [
            "CORPUS_DISTRIBUTION_IS_DETERMINISTIC_REPLAY",
            "NO_DESTINY_TRUTH_LABEL",
            "NO_RUNTIME_POINTER_MUTATION",
            "KNOWLEDGE_COVERAGE_REQUIRED_FOR_OBSERVED_LABELS",
        ],
    }
    if write:
        _write_report(payload, runtime_dir=runtime_dir)
    return payload


def read_latest_structure_dynamics_corpus_distribution(*, runtime_dir: Path | None = None) -> dict[str, Any]:
    path = _artifact_root(runtime_dir) / "latest.json"
    if not path.exists():
        return {
            "version": "v20.structure_dynamics_corpus_distribution.not_built.v1",
            "status": "not_built",
            "run_id": "",
            "case_count": 0,
            "target_count": FULL_CORPUS_CASE_COUNT,
            "coverage_ratio": 0.0,
            "runtime_mutation": False,
            "guardrails": ["STATUS_READ_ONLY", "NO_CORPUS_REPLAY_ON_ADMIN_READ"],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["runtime_mutation"] = False
    payload["guardrails"] = list(payload.get("guardrails", ())) + ["STATUS_READ_ONLY", "NO_CORPUS_REPLAY_ON_ADMIN_READ"]
    return payload


def _structure_row(*, index: int, case_id: str, pillars: tuple[str, str, str, str], structure: dict[str, Any]) -> dict[str, Any]:
    chain = structure.get("dominant_chain_v2", {}) if isinstance(structure.get("dominant_chain_v2"), dict) else {}
    path = structure.get("dominant_path", {}) if isinstance(structure.get("dominant_path"), dict) else {}
    semantics = structure.get("semantic_candidates", ()) if isinstance(structure.get("semantic_candidates"), list) else ()
    return {
        "index": index,
        "case_id": case_id,
        "pillar_displays": list(pillars),
        "label": str(chain.get("pattern_label", "")),
        "semantic_key": str(chain.get("pattern_key", "")),
        "chain_key": str(chain.get("chain_key", "")),
        "state": str(chain.get("state", "")),
        "confidence": float(chain.get("confidence", 0.0) or 0.0),
        "path_score": float(chain.get("path_score", path.get("score", 0.0)) or 0.0),
        "family_chain": list(path.get("family_chain", chain.get("nodes", ())) or ()),
        "node_labels": list(chain.get("node_labels", path.get("node_labels", ())) or ()),
        "semantic_labels": [
            str(row.get("label", ""))
            for row in semantics
            if isinstance(row, dict) and row.get("label")
        ],
    }


def _counter_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    total = sum(counter.values())
    return [
        {"key": key, "count": count, "ratio": round(count / max(1, total), 4)}
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _write_report(payload: dict[str, Any], *, runtime_dir: Path | None = None) -> None:
    root = _artifact_root(runtime_dir)
    root.mkdir(parents=True, exist_ok=True)
    run_path = root / f"{payload['run_id']}.json"
    latest_path = root / "latest.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    run_path.write_text(text, encoding="utf-8")
    latest_path.write_text(text, encoding="utf-8")


def _artifact_root(runtime_dir: Path | None = None) -> Path:
    base = runtime_dir or local_jsonl_store_from_env().runtime_dir
    return base / "training" / "structure_dynamics_corpus_distribution"


def _safe_run_id(run_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in run_id.strip())[:120]


def _default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"structure_dynamics_corpus_{stamp}"
