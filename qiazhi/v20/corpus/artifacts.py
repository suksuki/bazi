from __future__ import annotations

import json
import hashlib
import os
import sqlite3
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from v20.corpus.job_runner import full_precompute_root, read_full_precompute_status
from v20.knowledge.rule_proposal import build_first_wave_rule_proposals
from v20.storage.local_jsonl import local_jsonl_store_from_env


DEFAULT_ARTIFACT_RUN_ID = "v20_full_518k_20260501_main"


@dataclass(frozen=True)
class CorpusArtifactPaths:
    run_id: str
    run_dir: Path
    artifact_dir: Path
    snapshots_path: Path
    coverage_summary_path: Path
    flat_labels_path: Path
    sqlite_index_path: Path
    cluster_model_path: Path
    similarity_manifest_path: Path
    portrait_learning_path: Path
    portrait_training_path: Path
    rule_support_path: Path
    rule_training_path: Path
    postgres_manifest_path: Path
    parquet_manifest_path: Path
    status_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "artifact_dir": str(self.artifact_dir),
            "snapshots_path": str(self.snapshots_path),
            "coverage_summary_path": str(self.coverage_summary_path),
            "flat_labels_path": str(self.flat_labels_path),
            "sqlite_index_path": str(self.sqlite_index_path),
            "cluster_model_path": str(self.cluster_model_path),
            "similarity_manifest_path": str(self.similarity_manifest_path),
            "portrait_learning_path": str(self.portrait_learning_path),
            "portrait_training_path": str(self.portrait_training_path),
            "rule_support_path": str(self.rule_support_path),
            "rule_training_path": str(self.rule_training_path),
            "postgres_manifest_path": str(self.postgres_manifest_path),
            "parquet_manifest_path": str(self.parquet_manifest_path),
            "status_path": str(self.status_path),
        }


def corpus_artifact_paths(run_id: str = DEFAULT_ARTIFACT_RUN_ID, *, runtime_dir: Path | None = None) -> CorpusArtifactPaths:
    run_dir = full_precompute_root(runtime_dir) / run_id
    artifact_dir = run_dir / "artifacts"
    return CorpusArtifactPaths(
        run_id=run_id,
        run_dir=run_dir,
        artifact_dir=artifact_dir,
        snapshots_path=run_dir / "snapshots.jsonl",
        coverage_summary_path=artifact_dir / "coverage_summary.json",
        flat_labels_path=artifact_dir / "flat_labels.jsonl",
        sqlite_index_path=artifact_dir / "corpus_index.sqlite",
        cluster_model_path=artifact_dir / "cluster_model.json",
        similarity_manifest_path=artifact_dir / "similarity_index_manifest.json",
        portrait_learning_path=artifact_dir / "portrait_axis_learning.json",
        portrait_training_path=artifact_dir / "portrait_axis_training.json",
        rule_support_path=artifact_dir / "rule_proposal_support.json",
        rule_training_path=artifact_dir / "rule_proposal_training.json",
        postgres_manifest_path=artifact_dir / "postgres_import_manifest.json",
        parquet_manifest_path=artifact_dir / "parquet_export_manifest.json",
        status_path=artifact_dir / "artifact_status.json",
    )


def resolve_corpus_artifact_run_id(run_id: str = "", *, runtime_dir: Path | None = None) -> str:
    normalized = run_id.strip()
    if normalized:
        return normalized
    latest = read_full_precompute_status(runtime_dir=runtime_dir)
    latest_run_id = str(latest.get("run_id", "")).strip()
    return latest_run_id or DEFAULT_ARTIFACT_RUN_ID


def build_corpus_artifacts(
    run_id: str = DEFAULT_ARTIFACT_RUN_ID,
    *,
    runtime_dir: Path | None = None,
    status_every: int = 25_000,
    progress: Callable[[str], None] | None = None,
    build_sqlite_cache: bool = True,
) -> dict[str, object]:
    paths = corpus_artifact_paths(run_id, runtime_dir=runtime_dir)
    if not paths.snapshots_path.exists():
        raise FileNotFoundError(f"Missing corpus snapshots: {paths.snapshots_path}")
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    counters: dict[str, Counter[str]] = {
        "day_master": Counter(),
        "day_master_element": Counter(),
        "day_master_capacity": Counter(),
        "feature_domains": Counter(),
        "salience_feature_ids": Counter(),
        "salience_domains": Counter(),
        "macro_feature_domains": Counter(),
        "measurement_domains": Counter(),
        "portrait_domains": Counter(),
        "relation_types": Counter(),
        "visible_ten_gods": Counter(),
        "hidden_ten_gods": Counter(),
        "question_keys": Counter(),
        "knowledge_ids": Counter(),
        "useful_god_candidate_count": Counter(),
        "wealth_feature_present": Counter(),
        "wealth_material_level": Counter(),
        "mainline_keys": Counter(),
        "mainline_domains": Counter(),
    }
    cooccurrence: Counter[str] = Counter()
    cluster_counts: Counter[str] = Counter()
    cluster_examples: dict[str, list[str]] = defaultdict(list)
    cluster_tag_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cluster_feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cluster_portrait_counts: dict[str, Counter[str]] = defaultdict(Counter)
    rule_support = _rule_support_seed()
    total = 0
    expected_total = _expected_snapshot_count(paths)
    feature_count_sum = 0
    knowledge_ref_count_sum = 0
    portrait_axis_count_sum = 0

    conn: sqlite3.Connection | None = None
    if build_sqlite_cache:
        if paths.sqlite_index_path.exists():
            paths.sqlite_index_path.unlink()
        conn = sqlite3.connect(paths.sqlite_index_path)
        _configure_sqlite(conn)
        _create_schema(conn)

    with paths.snapshots_path.open(encoding="utf-8") as source, paths.flat_labels_path.open("w", encoding="utf-8") as flat:
        batch = []
        for line_no, line in enumerate(source):
            if not line.strip():
                continue
            snapshot = json.loads(line)
            label = snapshot["label_snapshot"]
            flat_row = _flat_label_row(line_no, label)
            flat.write(json.dumps(flat_row, ensure_ascii=False, sort_keys=True) + "\n")
            if conn is not None:
                batch.append(_sqlite_row(flat_row))
            _update_counters(counters, label)
            _update_rule_support(rule_support, label)
            _update_portrait_cooccurrence(cooccurrence, label)
            cluster_key = _cluster_key(label)
            feature_ids = _label_feature_ids(label)
            portrait_domains = tuple(str(item) for item in label.get("portrait_domains", ()))
            label_tags = _label_tags(label)
            cluster_counts[cluster_key] += 1
            cluster_tag_counts[cluster_key].update(label_tags)
            cluster_feature_counts[cluster_key].update(feature_ids)
            cluster_portrait_counts[cluster_key].update(portrait_domains)
            if len(cluster_examples[cluster_key]) < 5:
                cluster_examples[cluster_key].append(str(label["case_id"]))
            density = label.get("evidence_density", {})
            feature_count_sum += int(density.get("feature_count", 0))
            knowledge_ref_count_sum += int(density.get("knowledge_ref_count", 0))
            portrait_axis_count_sum += int(density.get("portrait_axis_count", 0))
            total += 1
            if conn is not None and len(batch) >= 2_000:
                conn.executemany(SQLITE_INSERT, batch)
                conn.commit()
                batch.clear()
            if total % status_every == 0:
                status = _status_payload(paths, "running", total, started_at, time.monotonic() - started)
                _write_json(paths.status_path, status)
                _emit_artifact_progress(progress, status, expected_total)
        if conn is not None and batch:
            conn.executemany(SQLITE_INSERT, batch)
            conn.commit()
    status = _status_payload(paths, "indexing", total, started_at, time.monotonic() - started)
    status["sqlite_cache_enabled"] = build_sqlite_cache
    _write_json(paths.status_path, status)
    _emit_artifact_progress(progress, status, expected_total)
    if conn is not None:
        _create_indexes(conn)
        conn.close()

    coverage = _coverage_summary(
        paths=paths,
        total=total,
        counters=counters,
        cluster_counts=cluster_counts,
        cluster_examples=cluster_examples,
        feature_count_sum=feature_count_sum,
        knowledge_ref_count_sum=knowledge_ref_count_sum,
        portrait_axis_count_sum=portrait_axis_count_sum,
        elapsed_seconds=time.monotonic() - started,
    )
    portrait_learning = _portrait_learning_summary(paths, total, counters, cooccurrence, cluster_counts)
    cluster_model = _cluster_model(
        paths=paths,
        total=total,
        cluster_counts=cluster_counts,
        cluster_examples=cluster_examples,
        cluster_tag_counts=cluster_tag_counts,
        cluster_feature_counts=cluster_feature_counts,
        cluster_portrait_counts=cluster_portrait_counts,
    )
    similarity_manifest = _similarity_manifest(paths, total, cluster_counts)
    portrait_training = _portrait_training_summary(
        paths=paths,
        total=total,
        counters=counters,
        cooccurrence=cooccurrence,
        cluster_counts=cluster_counts,
        cluster_portrait_counts=cluster_portrait_counts,
        cluster_feature_counts=cluster_feature_counts,
    )
    rule_support_summary = _rule_support_summary(paths, total, rule_support)
    rule_training = _rule_training_summary(paths, total, rule_support)
    postgres_manifest = _postgres_import_manifest(paths, total)
    parquet_manifest = _parquet_manifest(paths, total)
    _write_json(paths.coverage_summary_path, coverage)
    _write_json(paths.cluster_model_path, cluster_model)
    _write_json(paths.similarity_manifest_path, similarity_manifest)
    _write_json(paths.portrait_learning_path, portrait_learning)
    _write_json(paths.portrait_training_path, portrait_training)
    _write_json(paths.rule_support_path, rule_support_summary)
    _write_json(paths.rule_training_path, rule_training)
    _write_json(paths.postgres_manifest_path, postgres_manifest)
    _write_json(paths.parquet_manifest_path, parquet_manifest)
    status = _status_payload(paths, "completed", total, started_at, time.monotonic() - started)
    status["artifact_outputs"] = {
        "coverage_summary": str(paths.coverage_summary_path),
        "flat_labels": str(paths.flat_labels_path),
        "cluster_model": str(paths.cluster_model_path),
        "similarity_manifest": str(paths.similarity_manifest_path),
        "portrait_axis_learning": str(paths.portrait_learning_path),
        "portrait_axis_training": str(paths.portrait_training_path),
        "rule_proposal_support": str(paths.rule_support_path),
        "rule_proposal_training": str(paths.rule_training_path),
        "postgres_import_manifest": str(paths.postgres_manifest_path),
        "parquet_export_manifest": str(paths.parquet_manifest_path),
    }
    status["local_sqlite_cache"] = {
        "enabled": build_sqlite_cache,
        "role": "disposable_local_similarity_cache",
        "authority": "postgres_or_versioned_jsonl_artifacts",
        "path": str(paths.sqlite_index_path) if build_sqlite_cache else "",
        "rebuildable": True,
    }
    if build_sqlite_cache:
        status["artifact_outputs"]["sqlite_cache"] = str(paths.sqlite_index_path)
    _write_json(paths.status_path, status)
    _emit_artifact_progress(progress, status, total or expected_total)
    return status


def read_corpus_artifact_status(run_id: str = "", *, runtime_dir: Path | None = None) -> dict[str, object]:
    run_id = resolve_corpus_artifact_run_id(run_id, runtime_dir=runtime_dir)
    paths = corpus_artifact_paths(run_id, runtime_dir=runtime_dir)
    if not paths.status_path.exists():
        return {
            "version": "v20.corpus_artifact_status.v1",
            "run_id": run_id,
            "status": "not_built",
            "paths": paths.to_dict(),
            "runtime_mutation": False,
            "guardrails": ["ARTIFACT_STATUS_READ_ONLY"],
        }
    return json.loads(paths.status_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def read_corpus_coverage_summary(run_id: str = "", *, runtime_dir: Path | None = None) -> dict[str, object]:
    run_id = resolve_corpus_artifact_run_id(run_id, runtime_dir=runtime_dir)
    path = corpus_artifact_paths(run_id, runtime_dir=runtime_dir).coverage_summary_path
    if not path.exists():
        return {
            "version": "v20.corpus_coverage_summary.v1",
            "run_id": run_id,
            "status": "not_built",
            "runtime_mutation": False,
        }
    return json.loads(path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def read_corpus_cluster_model(run_id: str = "", *, runtime_dir: Path | None = None) -> dict[str, object]:
    run_id = resolve_corpus_artifact_run_id(run_id, runtime_dir=runtime_dir)
    path = corpus_artifact_paths(run_id, runtime_dir=runtime_dir).cluster_model_path
    if not path.exists():
        return {
            "version": "v20.corpus_cluster_model.v1",
            "run_id": run_id,
            "status": "not_built",
            "runtime_mutation": False,
        }
    return json.loads(path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def read_corpus_training_artifacts(run_id: str = "", *, runtime_dir: Path | None = None) -> dict[str, object]:
    run_id = resolve_corpus_artifact_run_id(run_id, runtime_dir=runtime_dir)
    paths = corpus_artifact_paths(run_id, runtime_dir=runtime_dir)
    return {
        "version": "v20.corpus_training_artifacts.v1",
        "run_id": run_id,
        "status": "ready"
        if paths.portrait_training_path.exists() and paths.rule_training_path.exists()
        else "not_built",
        "portrait_axis_training": _read_json_if_exists(paths.portrait_training_path),
        "rule_proposal_training": _read_json_if_exists(paths.rule_training_path),
        "similarity_manifest": _read_json_if_exists(paths.similarity_manifest_path),
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_ARTIFACTS_ARE_OFFLINE_SIGNALS",
            "NO_RULE_ACTIVATION",
            "NO_USER_VISIBLE_VERDICT",
        ],
    }


def find_similar_cases(
    case_id: str,
    *,
    run_id: str = "",
    limit: int = 8,
    runtime_dir: Path | None = None,
) -> dict[str, object]:
    run_id = resolve_corpus_artifact_run_id(run_id, runtime_dir=runtime_dir)
    postgres_result = _find_similar_cases_postgres(case_id, limit=limit)
    if postgres_result["status"] in {"ready", "case_not_found"}:
        return postgres_result

    paths = corpus_artifact_paths(run_id, runtime_dir=runtime_dir)
    if not paths.sqlite_index_path.exists():
        return {
            "version": "v20.corpus_similar_cases.v1",
            "status": "index_not_built",
            "backend": "sqlite",
            "postgres_status": postgres_result["status"],
            "case_id": case_id,
            "matches": [],
            "runtime_mutation": False,
        }
    conn = sqlite3.connect(paths.sqlite_index_path)
    conn.row_factory = sqlite3.Row
    query = conn.execute("SELECT * FROM corpus_cases WHERE case_id = ?", (case_id,)).fetchone()
    if query is None:
        conn.close()
        return {
            "version": "v20.corpus_similar_cases.v1",
            "status": "case_not_found",
            "case_id": case_id,
            "matches": [],
            "runtime_mutation": False,
        }
    candidates = _similarity_candidates(conn, query)
    conn.close()
    query_tags = _row_tags(query)
    scored = []
    for candidate in candidates:
        tags = _row_tags(candidate)
        shared_tags = tuple(sorted(query_tags & tags))
        score = _similarity_score(query_tags, tags)
        scored.append((score, shared_tags, candidate))
    matches = [
        {
            "case_id": row["case_id"],
            "input_hash": row["input_hash"],
            "pillar_displays": json.loads(row["pillar_displays"]),
            "score": round(score, 4),
            "day_master": row["day_master"],
            "day_master_capacity": row["day_master_capacity"],
            "cluster_key": row["cluster_key"],
            "feature_domains": _split(row["feature_domains"]),
            "feature_ids": _split(row["feature_ids"]),
            "portrait_domains": _split(row["portrait_domains"]),
            "relation_types": _split(row["relation_types"]),
            "wealth_material_level": row["wealth_material_level"] if "wealth_material_level" in row.keys() else "",
            "mainline_domains": _split(row["mainline_domains"]) if "mainline_domains" in row.keys() else [],
            "shared_tag_count": len(shared_tags),
            "shared_tags": list(shared_tags[:12]),
        }
        for score, shared_tags, row in sorted(scored, key=lambda item: (-item[0], item[2]["case_id"]))[:limit]
    ]
    return {
        "version": "v20.corpus_similar_cases.v1",
        "status": "ready",
        "backend": "sqlite",
        "postgres_status": postgres_result["status"],
        "case_id": case_id,
        "query": {
            "input_hash": query["input_hash"],
            "pillar_displays": json.loads(query["pillar_displays"]),
            "day_master": query["day_master"],
            "day_master_capacity": query["day_master_capacity"],
            "cluster_key": query["cluster_key"],
            "wealth_material_level": query["wealth_material_level"] if "wealth_material_level" in query.keys() else "",
            "mainline_domains": _split(query["mainline_domains"]) if "mainline_domains" in query.keys() else [],
        },
        "match_count": len(matches),
        "candidate_count": len(candidates),
        "matches": matches,
        "runtime_mutation": False,
        "guardrails": [
            "SIMILARITY_IS_STRUCTURAL_RETRIEVAL",
            "NO_DESTINY_OUTCOME_INFERENCE",
            "NO_RULE_ACTIVATION",
        ],
    }


def _find_similar_cases_postgres(case_id: str, *, limit: int) -> dict[str, object]:
    url = os.getenv("V20_DATABASE_URL", "")
    if not url:
        return {
            "version": "v20.corpus_similar_cases.v1",
            "status": "postgres_not_configured",
            "backend": "postgres",
            "case_id": case_id,
            "matches": [],
            "runtime_mutation": False,
        }
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except Exception as exc:
        return _postgres_similarity_blocked(case_id, "postgres_driver_missing", str(exc))
    try:
        with psycopg2.connect(url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT payload FROM v20_corpus_snapshots WHERE snapshot_id = %s", (case_id,))
                query_row = cur.fetchone()
                if query_row is None:
                    return {
                        "version": "v20.corpus_similar_cases.v1",
                        "status": "case_not_found",
                        "backend": "postgres",
                        "case_id": case_id,
                        "matches": [],
                        "runtime_mutation": False,
                    }
                query = query_row["payload"]
                candidates = _postgres_similarity_candidates(cur, query)
    except Exception as exc:
        return _postgres_similarity_blocked(case_id, "postgres_query_error", str(exc))
    query_tags = _row_tags(query)
    scored = []
    for candidate in candidates:
        tags = _row_tags(candidate)
        shared_tags = tuple(sorted(query_tags & tags))
        score = _similarity_score(query_tags, tags)
        scored.append((score, shared_tags, candidate))
    matches = [
        {
            "case_id": row["case_id"],
            "input_hash": row["input_hash"],
            "pillar_displays": _split(row["pillar_displays"]),
            "score": round(score, 4),
            "day_master": row["day_master"],
            "day_master_capacity": row["day_master_capacity"],
            "cluster_key": row["cluster_key"],
            "feature_domains": _split(row["feature_domains"]),
            "feature_ids": _split(row["feature_ids"]),
            "portrait_domains": _split(row["portrait_domains"]),
            "relation_types": _split(row["relation_types"]),
            "wealth_material_level": row.get("wealth_material_level", ""),
            "mainline_domains": _split(row.get("mainline_domains", ())),
            "shared_tag_count": len(shared_tags),
            "shared_tags": list(shared_tags[:12]),
        }
        for score, shared_tags, row in sorted(scored, key=lambda item: (-item[0], item[2]["case_id"]))[:limit]
    ]
    return {
        "version": "v20.corpus_similar_cases.v1",
        "status": "ready",
        "backend": "postgres",
        "case_id": case_id,
        "query": {
            "input_hash": query["input_hash"],
            "pillar_displays": _split(query["pillar_displays"]),
            "day_master": query["day_master"],
            "day_master_capacity": query["day_master_capacity"],
            "cluster_key": query["cluster_key"],
            "wealth_material_level": query.get("wealth_material_level", ""),
            "mainline_domains": _split(query.get("mainline_domains", ())),
        },
        "match_count": len(matches),
        "candidate_count": len(candidates),
        "matches": matches,
        "runtime_mutation": False,
        "guardrails": [
            "SIMILARITY_IS_STRUCTURAL_RETRIEVAL",
            "POSTGRES_AUTHORITATIVE_CORPUS_QUERY",
            "NO_DESTINY_OUTCOME_INFERENCE",
            "NO_RULE_ACTIVATION",
        ],
    }


def _postgres_similarity_blocked(case_id: str, status: str, error: str) -> dict[str, object]:
    return {
        "version": "v20.corpus_similar_cases.v1",
        "status": status,
        "backend": "postgres",
        "case_id": case_id,
        "matches": [],
        "error": error,
        "runtime_mutation": False,
    }


SQLITE_INSERT = """
INSERT INTO corpus_cases (
  line_no, case_id, input_hash, snapshot_hash, pillar_displays,
  day_master, day_master_element, day_master_capacity,
  feature_ids, salience_feature_ids, salience_domains,
  feature_domains, macro_feature_domains, measurement_domains, portrait_domains,
  relation_types, visible_ten_gods, hidden_ten_gods, question_keys, knowledge_ids,
  mainline_keys, mainline_domains, useful_god_candidate_count,
  wealth_feature_present, wealth_material_level, cluster_key, tag_signature,
  feature_count, knowledge_ref_count, portrait_axis_count
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _configure_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=MEMORY")


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE corpus_cases (
          line_no INTEGER PRIMARY KEY,
          case_id TEXT UNIQUE NOT NULL,
          input_hash TEXT NOT NULL,
          snapshot_hash TEXT NOT NULL,
          pillar_displays TEXT NOT NULL,
          day_master TEXT NOT NULL,
          day_master_element TEXT NOT NULL,
          day_master_capacity TEXT NOT NULL,
          feature_ids TEXT NOT NULL,
          salience_feature_ids TEXT NOT NULL,
          salience_domains TEXT NOT NULL,
          feature_domains TEXT NOT NULL,
          macro_feature_domains TEXT NOT NULL,
          measurement_domains TEXT NOT NULL,
          portrait_domains TEXT NOT NULL,
          relation_types TEXT NOT NULL,
          visible_ten_gods TEXT NOT NULL,
          hidden_ten_gods TEXT NOT NULL,
          question_keys TEXT NOT NULL,
          knowledge_ids TEXT NOT NULL,
          mainline_keys TEXT NOT NULL,
          mainline_domains TEXT NOT NULL,
          useful_god_candidate_count INTEGER NOT NULL,
          wealth_feature_present INTEGER NOT NULL,
          wealth_material_level TEXT NOT NULL,
          cluster_key TEXT NOT NULL,
          tag_signature TEXT NOT NULL,
          feature_count INTEGER NOT NULL,
          knowledge_ref_count INTEGER NOT NULL,
          portrait_axis_count INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def _create_indexes(conn: sqlite3.Connection) -> None:
    for sql in (
        "CREATE INDEX idx_corpus_case_id ON corpus_cases(case_id)",
        "CREATE INDEX idx_corpus_hash ON corpus_cases(input_hash)",
        "CREATE INDEX idx_corpus_day_master ON corpus_cases(day_master)",
        "CREATE INDEX idx_corpus_element_capacity ON corpus_cases(day_master_element, day_master_capacity)",
        "CREATE INDEX idx_corpus_cluster_key ON corpus_cases(cluster_key)",
        "CREATE INDEX idx_corpus_wealth ON corpus_cases(wealth_feature_present)",
        "CREATE INDEX idx_corpus_wealth_level ON corpus_cases(wealth_material_level)",
        "CREATE INDEX idx_corpus_mainline_domains ON corpus_cases(mainline_domains)",
    ):
        conn.execute(sql)
    conn.commit()


def _flat_label_row(line_no: int, label: dict[str, object]) -> dict[str, object]:
    density = label.get("evidence_density", {})
    return {
        "line_no": line_no,
        "case_id": label["case_id"],
        "input_hash": label["input_hash"],
        "snapshot_hash": label["snapshot_hash"],
        "pillar_displays": label["pillar_displays"],
        "day_master": label["day_master"],
        "day_master_element": label["day_master_element"],
        "day_master_capacity": label["day_master_capacity"],
        "feature_ids": _label_feature_ids(label),
        "salience_feature_ids": _label_salience_feature_ids(label),
        "salience_domains": label.get("salience_domains", ()),
        "feature_domains": label.get("feature_domains", ()),
        "macro_feature_domains": label.get("macro_feature_domains", ()),
        "measurement_domains": label.get("measurement_domains", ()),
        "portrait_domains": label.get("portrait_domains", ()),
        "relation_types": label.get("relation_types", ()),
        "visible_ten_gods": label.get("visible_ten_gods", ()),
        "hidden_ten_gods": label.get("hidden_ten_gods", ()),
        "question_keys": label.get("question_keys", ()),
        "knowledge_ids": label.get("knowledge_ids", ()),
        "mainline_keys": label.get("mainline_keys", ()),
        "mainline_domains": label.get("mainline_domains", ()),
        "useful_god_candidate_count": label.get("useful_god_candidate_count", 0),
        "wealth_feature_present": label.get("wealth_feature_present", False),
        "wealth_material_level": label.get("wealth_material_level", "unknown"),
        "cluster_key": _cluster_key(label),
        "tag_signature": tuple(sorted(_label_tags(label))),
        "feature_count": density.get("feature_count", 0),
        "knowledge_ref_count": density.get("knowledge_ref_count", 0),
        "portrait_axis_count": density.get("portrait_axis_count", 0),
    }


def _sqlite_row(row: dict[str, object]) -> tuple[object, ...]:
    return (
        row["line_no"],
        row["case_id"],
        row["input_hash"],
        row["snapshot_hash"],
        json.dumps(row["pillar_displays"], ensure_ascii=False),
        row["day_master"],
        row["day_master_element"],
        row["day_master_capacity"],
        _join(row["feature_ids"]),
        _join(row["salience_feature_ids"]),
        _join(row["salience_domains"]),
        _join(row["feature_domains"]),
        _join(row["macro_feature_domains"]),
        _join(row["measurement_domains"]),
        _join(row["portrait_domains"]),
        _join(row["relation_types"]),
        _join(row["visible_ten_gods"]),
        _join(row["hidden_ten_gods"]),
        _join(row["question_keys"]),
        _join(row["knowledge_ids"]),
        _join(row["mainline_keys"]),
        _join(row["mainline_domains"]),
        int(row["useful_god_candidate_count"]),
        1 if row["wealth_feature_present"] else 0,
        str(row["wealth_material_level"]),
        row["cluster_key"],
        _join(row["tag_signature"]),
        int(row["feature_count"]),
        int(row["knowledge_ref_count"]),
        int(row["portrait_axis_count"]),
    )


def _update_counters(counters: dict[str, Counter[str]], label: dict[str, object]) -> None:
    for key in ("day_master", "day_master_element", "day_master_capacity"):
        counters[key][str(label.get(key, ""))] += 1
    for key in (
        "feature_domains",
        "salience_feature_ids",
        "salience_domains",
        "macro_feature_domains",
        "measurement_domains",
        "portrait_domains",
        "relation_types",
        "visible_ten_gods",
        "hidden_ten_gods",
        "question_keys",
        "knowledge_ids",
        "mainline_keys",
        "mainline_domains",
    ):
        counters[key].update(str(item) for item in label.get(key, ()))
    counters["useful_god_candidate_count"][str(label.get("useful_god_candidate_count", 0))] += 1
    counters["wealth_feature_present"]["true" if label.get("wealth_feature_present") else "false"] += 1
    counters["wealth_material_level"][str(label.get("wealth_material_level", "unknown"))] += 1


def _label_feature_ids(label: dict[str, object]) -> tuple[str, ...]:
    return tuple(str(item) for item in label.get("feature_ids", ()) if str(item))


def _label_salience_feature_ids(label: dict[str, object]) -> tuple[str, ...]:
    explicit = tuple(str(item) for item in label.get("salience_feature_ids", ()) if str(item))
    if explicit:
        return explicit
    return tuple(feature_id for feature_id in _label_feature_ids(label) if _is_salience_feature_id(feature_id))


def _label_tags(label: dict[str, object]) -> set[str]:
    tags = {
        f"day_master:{label.get('day_master', '')}",
        f"element:{label.get('day_master_element', '')}",
        f"capacity:{label.get('day_master_capacity', '')}",
        f"wealth:{label.get('wealth_material_level', 'unknown')}",
        f"useful_god_candidate_count:{label.get('useful_god_candidate_count', 0)}",
    }
    for feature_id in _label_feature_ids(label):
        tags.add(f"feature_id:{feature_id}")
    for feature_id in _label_salience_feature_ids(label):
        tags.add(f"salience_feature_id:{feature_id}")
    for key in (
        "feature_domains",
        "salience_domains",
        "macro_feature_domains",
        "measurement_domains",
        "portrait_domains",
        "relation_types",
        "visible_ten_gods",
        "hidden_ten_gods",
        "question_keys",
        "knowledge_ids",
        "mainline_keys",
        "mainline_domains",
    ):
        tags.update(f"{key}:{item}" for item in label.get(key, ()))
    return {tag for tag in tags if not tag.endswith(":")}


def _rule_support_seed() -> dict[str, dict[str, object]]:
    proposals = build_first_wave_rule_proposals(limit_per_domain=10)
    rows = {}
    for report in proposals["reports"]:
        for proposal in report["proposals"]:
            rows[str(proposal["proposal_id"])] = {
                "proposal_id": proposal["proposal_id"],
                "domain": proposal["domain"],
                "source_knowledge_id": proposal["source_knowledge_id"],
                "emits_feature_hooks": proposal["emits_feature_hooks"],
                "supports_question_hooks": proposal["supports_question_hooks"],
                "condition_model": proposal["condition_model"],
                "support_count": 0,
                "sample_case_ids": [],
                "exact_signature_counts": Counter(),
                "cluster_counts": Counter(),
                "day_master_capacity_counts": Counter(),
                "feature_counts": Counter(),
                "salience_feature_counts": Counter(),
                "salience_signature_counts": Counter(),
            }
    return rows


def _update_rule_support(rule_support: dict[str, dict[str, object]], label: dict[str, object]) -> None:
    feature_ids = _label_feature_ids(label)
    salience_feature_ids = set(_label_salience_feature_ids(label))
    cluster_key = _cluster_key(label)
    for row in rule_support.values():
        hooks = tuple(str(item) for item in row["emits_feature_hooks"])
        matched_features = tuple(
            feature_id for feature_id in feature_ids if any(feature_id.startswith(hook) for hook in hooks)
        )
        matched_salience_features = tuple(feature_id for feature_id in matched_features if feature_id in salience_feature_ids)
        if hooks and all(any(feature_id.startswith(hook) for feature_id in feature_ids) for hook in hooks):
            row["support_count"] = int(row["support_count"]) + 1
            samples = row["sample_case_ids"]
            if isinstance(samples, list) and len(samples) < 5:
                samples.append(str(label["case_id"]))
            exact_counter = row["exact_signature_counts"]
            cluster_counter = row["cluster_counts"]
            capacity_counter = row["day_master_capacity_counts"]
            feature_counter = row["feature_counts"]
            salience_counter = row["salience_feature_counts"]
            salience_signature_counter = row["salience_signature_counts"]
            if isinstance(exact_counter, Counter):
                exact_counter[_join(matched_features)] += 1
            if isinstance(cluster_counter, Counter):
                cluster_counter[cluster_key] += 1
            if isinstance(capacity_counter, Counter):
                capacity_counter[str(label.get("day_master_capacity", ""))] += 1
            if isinstance(feature_counter, Counter):
                feature_counter.update(matched_features)
            if isinstance(salience_counter, Counter):
                salience_counter.update(matched_salience_features)
            if isinstance(salience_signature_counter, Counter) and matched_salience_features:
                salience_signature_counter[_join(matched_salience_features)] += 1


def _update_portrait_cooccurrence(cooccurrence: Counter[str], label: dict[str, object]) -> None:
    domains = sorted(str(item) for item in label.get("portrait_domains", ()))
    for left_index, left in enumerate(domains):
        for right in domains[left_index + 1 :]:
            cooccurrence[f"{left}|{right}"] += 1


def _cluster_key(label: dict[str, object]) -> str:
    relation = "+".join(str(item) for item in label.get("relation_types", ())) or "quiet"
    wealth = str(label.get("wealth_material_level", "")) or ("visible_wealth" if label.get("wealth_feature_present") else "no_wealth")
    mainline = "+".join(str(item) for item in label.get("mainline_domains", ())[:3]) or "no_mainline"
    return "|".join(
        (
            str(label.get("day_master_element", "")),
            str(label.get("day_master_capacity", "")),
            relation,
            wealth,
            f"useful{label.get('useful_god_candidate_count', 0)}",
            mainline,
        )
    )


def _coverage_summary(
    *,
    paths: CorpusArtifactPaths,
    total: int,
    counters: dict[str, Counter[str]],
    cluster_counts: Counter[str],
    cluster_examples: dict[str, list[str]],
    feature_count_sum: int,
    knowledge_ref_count_sum: int,
    portrait_axis_count_sum: int,
    elapsed_seconds: float,
) -> dict[str, object]:
    return {
        "version": "v20.corpus_coverage_summary.v1",
        "status": "ready",
        "run_id": paths.run_id,
        "case_count": total,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "cases_per_second": round(total / elapsed_seconds, 3) if elapsed_seconds else 0,
        "distributions": {key: dict(counter.most_common()) for key, counter in counters.items()},
        "averages": {
            "feature_count": round(feature_count_sum / total, 4) if total else 0,
            "knowledge_ref_count": round(knowledge_ref_count_sum / total, 4) if total else 0,
            "portrait_axis_count": round(portrait_axis_count_sum / total, 4) if total else 0,
        },
        "cluster_count": len(cluster_counts),
        "top_clusters": [
            {"cluster_key": key, "count": count, "sample_case_ids": cluster_examples.get(key, [])}
            for key, count in cluster_counts.most_common(20)
        ],
        "runtime_mutation": False,
        "guardrails": [
            "SUMMARY_ONLY",
            "NO_DESTINY_TRUTH_LABEL",
            "NO_EVENT_OUTCOME_LABEL",
        ],
    }


def _portrait_learning_summary(
    paths: CorpusArtifactPaths,
    total: int,
    counters: dict[str, Counter[str]],
    cooccurrence: Counter[str],
    cluster_counts: Counter[str],
) -> dict[str, object]:
    return {
        "version": "v20.portrait_axis_learning_summary.v1",
        "status": "ready",
        "run_id": paths.run_id,
        "case_count": total,
        "axis_counts": dict(counters["portrait_domains"].most_common()),
        "axis_cooccurrence_top": [
            {"pair": key.split("|"), "count": count}
            for key, count in cooccurrence.most_common(50)
        ],
        "cluster_count": len(cluster_counts),
        "learning_scope": [
            "axis_frequency_prior",
            "axis_cooccurrence_prior",
            "coverage_gap_detection",
            "calibration_candidate_grouping",
        ],
        "forbidden_scope": [
            "personality_verdict_generation",
            "fortune_outcome_labeling",
            "question_bias_activation",
        ],
        "runtime_mutation": False,
    }


def _cluster_model(
    *,
    paths: CorpusArtifactPaths,
    total: int,
    cluster_counts: Counter[str],
    cluster_examples: dict[str, list[str]],
    cluster_tag_counts: dict[str, Counter[str]],
    cluster_feature_counts: dict[str, Counter[str]],
    cluster_portrait_counts: dict[str, Counter[str]],
) -> dict[str, object]:
    clusters = []
    rare_clusters = []
    for key, count in cluster_counts.most_common():
        share = count / total if total else 0
        if count <= 12 or share < 0.001:
            rare_clusters.append(key)
        clusters.append(
            {
                "cluster_id": _stable_id("cluster", key),
                "cluster_key": key,
                "count": count,
                "share": round(share, 6),
                "centroid_tags": _counter_top_with_weight(cluster_tag_counts[key], count, limit=24),
                "top_feature_ids": _counter_top_with_weight(cluster_feature_counts[key], count, limit=16),
                "top_portrait_axes": _counter_top_with_weight(cluster_portrait_counts[key], count, limit=10),
                "sample_case_ids": cluster_examples.get(key, []),
                "training_use": [
                    "similar_case_candidate_pool",
                    "coverage_gap_prior",
                    "portrait_axis_calibration_group",
                    "rule_proposal_active_support_group",
                ],
            }
        )
    return {
        "version": "v20.corpus_cluster_model.v1",
        "status": "ready",
        "run_id": paths.run_id,
        "case_count": total,
        "cluster_count": len(cluster_counts),
        "clustering_method": "deterministic_structural_signature",
        "signature_dimensions": [
            "day_master_element",
            "day_master_capacity",
            "relation_types",
            "wealth_feature_present",
            "wealth_material_level",
            "useful_god_candidate_count",
            "mainline_domains",
        ],
        "clusters": clusters,
        "coverage_gaps": {
            "rare_cluster_count": len(rare_clusters),
            "rare_cluster_keys": rare_clusters[:80],
        },
        "runtime_mutation": False,
        "guardrails": [
            "CLUSTERS_ARE_STRUCTURAL_GROUPS",
            "NO_DESTINY_OUTCOME_LABEL",
            "NO_RULE_ACTIVATION",
        ],
    }


def _similarity_manifest(paths: CorpusArtifactPaths, total: int, cluster_counts: Counter[str]) -> dict[str, object]:
    return {
        "version": "v20.corpus_similarity_index_manifest.v1",
        "status": "ready",
        "run_id": paths.run_id,
        "case_count": total,
        "sqlite_index": str(paths.sqlite_index_path),
        "candidate_strategy": [
            "same_cluster_key_first",
            "same_day_master_element_and_capacity_fallback",
            "bounded_candidate_pool",
        ],
        "scoring": "weighted_jaccard_over_structural_tags",
        "tag_sources": [
            "feature_ids",
            "feature_domains",
            "portrait_domains",
            "relation_types",
            "ten_god_labels",
            "question_keys",
            "knowledge_ids",
            "wealth_material_level",
            "mainline_domains",
        ],
        "cluster_count": len(cluster_counts),
        "runtime_mutation": False,
        "guardrails": [
            "SIMILARITY_IS_RETRIEVAL_ONLY",
            "NO_PERSON_OUTCOME_TRANSFER",
            "NO_EVENT_PREDICTION_BY_NEIGHBOR",
        ],
    }


def _portrait_training_summary(
    *,
    paths: CorpusArtifactPaths,
    total: int,
    counters: dict[str, Counter[str]],
    cooccurrence: Counter[str],
    cluster_counts: Counter[str],
    cluster_portrait_counts: dict[str, Counter[str]],
    cluster_feature_counts: dict[str, Counter[str]],
) -> dict[str, object]:
    axis_rows = []
    for axis, count in counters["portrait_domains"].most_common():
        ratio = count / total if total else 0
        cluster_lift = []
        for cluster_key, cluster_count in cluster_counts.items():
            axis_count = cluster_portrait_counts[cluster_key][axis]
            if not axis_count:
                continue
            local_ratio = axis_count / cluster_count
            lift = local_ratio / ratio if ratio else 0
            if lift >= 1.05 or local_ratio >= 0.95:
                cluster_lift.append(
                    {
                        "cluster_id": _stable_id("cluster", cluster_key),
                        "cluster_key": cluster_key,
                        "cluster_count": cluster_count,
                        "axis_ratio": round(local_ratio, 6),
                        "lift": round(lift, 4),
                    }
                )
        axis_rows.append(
            {
                "axis": axis,
                "count": count,
                "global_ratio": round(ratio, 6),
                "top_clusters": sorted(
                    cluster_lift,
                    key=lambda row: (-float(row["lift"]), -int(row["cluster_count"]), str(row["cluster_key"])),
                )[:16],
                "top_feature_ids": _counter_top_with_weight(
                    _feature_counts_for_axis(axis, cluster_portrait_counts, cluster_feature_counts),
                    count,
                    limit=16,
                ),
                "diagnostic": "flat_axis_needs_sub_axis_modeling" if ratio > 0.95 else "selective_axis",
            }
        )
    return {
        "version": "v20.portrait_axis_training.v1",
        "status": "ready",
        "run_id": paths.run_id,
        "case_count": total,
        "axis_models": axis_rows,
        "axis_cooccurrence_top": [
            {"pair": key.split("|"), "count": count}
            for key, count in cooccurrence.most_common(50)
        ],
        "training_targets": [
            "portrait_axis_prior",
            "portrait_sub_axis_split_proposal",
            "feedback_calibration_weight",
            "domain_language_boundary_selection",
        ],
        "known_limitations": [
            "Phase-1 portrait domains are often always present; sub-axis labels must be learned from feature ids and feedback.",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "PORTRAIT_TRAINING_IS_CALIBRATION_ONLY",
            "NO_PERSONALITY_VERDICT",
            "NO_QUESTION_BIAS_ACTIVATION",
        ],
    }


def _rule_support_summary(
    paths: CorpusArtifactPaths,
    total: int,
    support: dict[str, dict[str, object]],
) -> dict[str, object]:
    proposals = sorted(
        (_rule_support_public_row(row, total) for row in support.values()),
        key=lambda row: (-int(row["support_count"]), str(row["proposal_id"])),
    )
    return {
        "version": "v20.rule_proposal_support_summary.v1",
        "status": "ready",
        "run_id": paths.run_id,
        "case_count": total,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "training_scope": [
            "proposal_priority",
            "coverage_weight",
            "active_rule_path_frequency",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_SUPPORT_ONLY",
            "NO_RULE_ACTIVATION",
            "NO_USER_VISIBLE_VERDICT",
        ],
    }


def _rule_training_summary(
    paths: CorpusArtifactPaths,
    total: int,
    support: dict[str, dict[str, object]],
) -> dict[str, object]:
    proposals = sorted(
        (_rule_training_public_row(row, total) for row in support.values()),
        key=lambda row: (-float(row["selectivity_score"]), -int(row["support_count"]), str(row["proposal_id"])),
    )
    return {
        "version": "v20.rule_proposal_training.v1",
        "status": "ready",
        "run_id": paths.run_id,
        "case_count": total,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "training_targets": [
            "proposal_selectivity",
            "exact_feature_signature_support",
            "cluster_condition_prior",
            "active_rule_path_priority",
            "synthetic_case_gap_proposal",
        ],
        "release_policy": {
            "active_training_allowed": True,
            "user_visible_runtime_allowed": True,
            "iteration_requires": [
                "synthetic_validation",
                "runtime_replay_report",
                "forbidden_output_scan",
                "decision_registry_iteration_record",
            ],
        },
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_ONLY",
            "NO_RULE_ACTIVATION",
            "NO_USER_VISIBLE_VERDICT",
        ],
    }


def _counter_top_with_weight(counter: Counter[str], denominator: int, *, limit: int) -> list[dict[str, object]]:
    return [
        {
            "value": value,
            "count": count,
            "weight": round(count / denominator, 6) if denominator else 0,
        }
        for value, count in counter.most_common(limit)
    ]


def _feature_counts_for_axis(
    axis: str,
    cluster_portrait_counts: dict[str, Counter[str]],
    cluster_feature_counts: dict[str, Counter[str]],
) -> Counter[str]:
    rows: Counter[str] = Counter()
    for cluster_key, portrait_counts in cluster_portrait_counts.items():
        if portrait_counts[axis]:
            rows.update(cluster_feature_counts[cluster_key])
    return rows


def _rule_support_public_row(row: dict[str, object], total: int) -> dict[str, object]:
    support_count = int(row["support_count"])
    return {
        "proposal_id": row["proposal_id"],
        "domain": row["domain"],
        "source_knowledge_id": row["source_knowledge_id"],
        "emits_feature_hooks": row["emits_feature_hooks"],
        "supports_question_hooks": row["supports_question_hooks"],
        "support_count": support_count,
        "support_ratio": round(support_count / total, 6) if total else 0,
        "support_quality": _support_quality(support_count, total),
        "sample_case_ids": row["sample_case_ids"],
        "truth_scope": "coverage_prior_only_not_rule_truth",
    }


def _rule_training_public_row(row: dict[str, object], total: int) -> dict[str, object]:
    support_count = int(row["support_count"])
    exact_signatures = row.get("exact_signature_counts")
    cluster_counts = row.get("cluster_counts")
    capacity_counts = row.get("day_master_capacity_counts")
    feature_counts = row.get("feature_counts")
    salience_feature_counts = row.get("salience_feature_counts")
    salience_signature_counts = row.get("salience_signature_counts")
    if not isinstance(exact_signatures, Counter):
        exact_signatures = Counter()
    if not isinstance(cluster_counts, Counter):
        cluster_counts = Counter()
    if not isinstance(capacity_counts, Counter):
        capacity_counts = Counter()
    if not isinstance(feature_counts, Counter):
        feature_counts = Counter()
    if not isinstance(salience_feature_counts, Counter):
        salience_feature_counts = Counter()
    if not isinstance(salience_signature_counts, Counter):
        salience_signature_counts = Counter()
    support_ratio = support_count / total if total else 0
    return {
        "proposal_id": row["proposal_id"],
        "domain": row["domain"],
        "source_knowledge_id": row["source_knowledge_id"],
        "condition_model": row["condition_model"],
        "emits_feature_hooks": row["emits_feature_hooks"],
        "supports_question_hooks": row["supports_question_hooks"],
        "support_count": support_count,
        "support_ratio": round(support_ratio, 6),
        "support_quality": _support_quality(support_count, total),
        "selectivity_score": _selectivity_score(support_count, total),
        "top_exact_feature_signatures": _counter_top_with_weight(exact_signatures, support_count, limit=16),
        "top_clusters": [
            {
                "cluster_id": _stable_id("cluster", key),
                "cluster_key": key,
                "count": count,
                "weight": round(count / support_count, 6) if support_count else 0,
            }
            for key, count in cluster_counts.most_common(16)
        ],
        "day_master_capacity_distribution": dict(capacity_counts.most_common()),
        "top_matched_feature_ids": _counter_top_with_weight(feature_counts, support_count, limit=16),
        "top_matched_salience_feature_ids": _counter_top_with_weight(salience_feature_counts, support_count, limit=16),
        "top_salience_feature_signatures": _counter_top_with_weight(salience_signature_counts, support_count, limit=16),
        "sample_case_ids": row["sample_case_ids"],
        "next_training_action": _next_training_action(support_count, total),
        "truth_scope": "coverage_prior_only_not_rule_truth",
    }


def _support_quality(support_count: int, total: int) -> str:
    if total <= 0 or support_count <= 0:
        return "no_support"
    ratio = support_count / total
    if ratio >= 0.95:
        return "too_broad_needs_subconditions"
    if ratio <= 0.001:
        return "too_sparse_needs_more_evidence"
    return "usable_active_signal"


def _selectivity_score(support_count: int, total: int) -> float:
    quality = _support_quality(support_count, total)
    if quality == "usable_active_signal":
        ratio = support_count / total
        return round(1 - abs(0.2 - ratio), 6)
    if quality == "too_broad_needs_subconditions":
        return 0.2
    if quality == "too_sparse_needs_more_evidence":
        return 0.1
    return 0


def _next_training_action(support_count: int, total: int) -> str:
    quality = _support_quality(support_count, total)
    if quality == "too_broad_needs_subconditions":
        return "split_by_exact_feature_signature_and_cluster"
    if quality == "too_sparse_needs_more_evidence":
        return "generate_synthetic_edge_cases_and_review_hooks"
    if quality == "no_support":
        return "review_knowledge_hook_mapping"
    return "rank_in_active_training"


def _postgres_import_manifest(paths: CorpusArtifactPaths, total: int) -> dict[str, object]:
    return {
        "version": "v20.corpus_postgres_import_manifest.v1",
        "status": "ready_for_explicit_import",
        "run_id": paths.run_id,
        "case_count": total,
        "target_table": "v20_corpus_snapshots",
        "source_flat_labels_jsonl": str(paths.flat_labels_path),
        "source_snapshots_jsonl": str(paths.snapshots_path),
        "suggested_copy_strategy": "COPY staging table from flat_labels_jsonl, then insert payload into v20_corpus_snapshots.",
        "runtime_mutation": False,
        "guardrails": [
            "MANIFEST_ONLY",
            "POSTGRES_IMPORT_REQUIRES_EXPLICIT_COMMAND",
            "BACKUP_REQUIRED_BEFORE_REMOTE_IMPORT",
        ],
    }


def _parquet_manifest(paths: CorpusArtifactPaths, total: int) -> dict[str, object]:
    try:
        import pyarrow  # type: ignore  # pragma: no cover

        pyarrow_status = f"available:{pyarrow.__version__}"
    except Exception:
        pyarrow_status = "missing_pyarrow"
    return {
        "version": "v20.corpus_parquet_export_manifest.v1",
        "status": "ready_for_conversion" if pyarrow_status.startswith("available") else "blocked_missing_dependency",
        "run_id": paths.run_id,
        "case_count": total,
        "source_flat_labels_jsonl": str(paths.flat_labels_path),
        "target_parquet": str(paths.artifact_dir / "flat_labels.parquet"),
        "dependency_status": pyarrow_status,
        "runtime_mutation": False,
        "guardrails": [
            "PARQUET_EXPORT_MANIFEST_ONLY",
            "NO_DATA_LOSS_CONVERSION_REQUIRED",
            "FLAT_JSONL_IS_AUTHORITATIVE_EXPORT_SOURCE",
        ],
    }


def _status_payload(
    paths: CorpusArtifactPaths,
    status: str,
    processed: int,
    started_at: str,
    elapsed_seconds: float,
) -> dict[str, object]:
    return {
        "version": "v20.corpus_artifact_status.v1",
        "run_id": paths.run_id,
        "status": status,
        "processed": processed,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "cases_per_second": round(processed / elapsed_seconds, 3) if elapsed_seconds else 0,
        "started_at": started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "paths": paths.to_dict(),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_ARTIFACT_BUILD",
            "NO_POSTGRES_WRITE",
            "NO_RULE_ACTIVATION",
        ],
    }


def _expected_snapshot_count(paths: CorpusArtifactPaths) -> int:
    progress_path = paths.run_dir / "progress.json"
    if progress_path.exists():
        try:
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            target = int(progress.get("target_count", 0))
            if target > 0:
                return target
        except Exception:
            pass
    return _count_lines(paths.snapshots_path) if paths.snapshots_path.exists() else 0


def _count_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as source:
        for _line in source:
            count += 1
    return count


def _emit_artifact_progress(
    progress: Callable[[str], None] | None,
    status: dict[str, object],
    expected_total: int,
) -> None:
    if progress is None:
        return
    processed = int(status.get("processed", 0))
    elapsed = float(status.get("elapsed_seconds", 0.0))
    ratio = (processed / expected_total) if expected_total else 0.0
    width = 24
    filled = max(0, min(width, round(width * ratio)))
    bar = "#" * filled + "-" * (width - filled)
    remaining = max(0, expected_total - processed)
    rate = processed / elapsed if elapsed > 0 else 0.0
    eta = remaining / rate if rate > 0 else None
    eta_text = "unknown" if eta is None else f"{round(eta, 1)}s"
    progress(
        f"[{bar}] {ratio * 100:6.2f}% "
        f"processed={processed}/{expected_total or '?'} "
        f"status={status.get('status', '')} "
        f"rate={round(rate, 2)} rows/s eta={eta_text}"
    )


def _similarity_candidates(conn: sqlite3.Connection, query: sqlite3.Row) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT * FROM corpus_cases
        WHERE case_id != ?
          AND cluster_key = ?
        LIMIT 4000
        """,
        (query["case_id"], query["cluster_key"]),
    ).fetchall()
    seen = {row["case_id"] for row in rows}
    if len(rows) < 4000:
        fallback = conn.execute(
            """
            SELECT * FROM corpus_cases
            WHERE case_id != ?
              AND day_master_element = ?
              AND day_master_capacity = ?
            LIMIT 4000
            """,
            (query["case_id"], query["day_master_element"], query["day_master_capacity"]),
        ).fetchall()
        for row in fallback:
            if row["case_id"] not in seen:
                rows.append(row)
                seen.add(row["case_id"])
            if len(rows) >= 5000:
                break
    return rows


def _postgres_similarity_candidates(cur, query: dict[str, object]) -> list[dict[str, object]]:
    cur.execute(
        """
        SELECT payload FROM v20_corpus_snapshots
        WHERE snapshot_id != %s
          AND payload->>'cluster_key' = %s
        ORDER BY snapshot_id
        LIMIT 4000
        """,
        (query["case_id"], query["cluster_key"]),
    )
    rows = [dict(row["payload"]) for row in cur.fetchall()]
    seen = {row["case_id"] for row in rows}
    if len(rows) < 4000:
        cur.execute(
            """
            SELECT payload FROM v20_corpus_snapshots
            WHERE snapshot_id != %s
              AND payload->>'day_master_element' = %s
              AND payload->>'day_master_capacity' = %s
            ORDER BY snapshot_id
            LIMIT 4000
            """,
            (query["case_id"], query["day_master_element"], query["day_master_capacity"]),
        )
        for result in cur.fetchall():
            row = dict(result["payload"])
            if row["case_id"] not in seen:
                rows.append(row)
                seen.add(row["case_id"])
            if len(rows) >= 5000:
                break
    return rows


def _similarity_score(query_tags: set[str], candidate_tags: set[str]) -> float:
    if not query_tags and not candidate_tags:
        return 0
    weights = {
        "feature_id": 3.0,
        "salience_feature_id": 3.4,
        "relation_types": 2.0,
        "visible_ten_gods": 1.5,
        "hidden_ten_gods": 1.5,
        "question_keys": 1.25,
        "knowledge_ids": 1.25,
    }
    weights.update(_active_similarity_weight_overrides())
    union = query_tags | candidate_tags
    intersection = query_tags & candidate_tags
    numerator = sum(_tag_weight(tag, weights) for tag in intersection)
    denominator = sum(_tag_weight(tag, weights) for tag in union)
    return numerator / denominator if denominator else 0


def _active_similarity_weight_overrides() -> dict[str, float]:
    path = local_jsonl_store_from_env().runtime_dir / "training" / "corpus_policy_versions" / "active_pointer.json"
    if not path.exists():
        return {}
    try:
        pointer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if pointer.get("version") != "v20.corpus_runtime_active_pointer.v1" or pointer.get("status") != "candidate_active":
        return {}
    payload = pointer.get("policy_payload", {})
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("similarity_tag_weight_policy", ())
    if not isinstance(rows, list):
        return {}
    mapping = {
        "feature_ids": "feature_id",
        "salience_feature_ids": "salience_feature_id",
        "relation_types": "relation_types",
        "visible_ten_gods": "visible_ten_gods",
        "hidden_ten_gods": "hidden_ten_gods",
        "question_keys": "question_keys",
        "knowledge_ids": "knowledge_ids",
        "mainline_domains": "mainline_domains",
        "portrait_domains": "portrait_domains",
    }
    overrides: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        prefix = mapping.get(str(row.get("tag_prefix", "")))
        if not prefix:
            continue
        try:
            overrides[prefix] = max(0.1, 1.0 + float(row.get("weight_delta", 0.0) or 0.0))
        except (TypeError, ValueError):
            continue
    return overrides


def _tag_weight(tag: str, weights: dict[str, float]) -> float:
    key = tag.split(":", 1)[0]
    return weights.get(key, 1.0)


def _row_tags(row: sqlite3.Row) -> set[str]:
    if "tag_signature" in row.keys() and row["tag_signature"]:
        return set(_split(row["tag_signature"]))
    wealth_material = (
        row["wealth_material_level"]
        if "wealth_material_level" in row.keys()
        else ("visible" if row["wealth_feature_present"] else "not_visible")
    )
    tags = {
        f"day_master:{row['day_master']}",
        f"element:{row['day_master_element']}",
        f"capacity:{row['day_master_capacity']}",
        f"wealth:{wealth_material}",
    }
    if "feature_ids" in row.keys():
        tags.update(f"feature_id:{item}" for item in _split(row["feature_ids"]))
    if "salience_feature_ids" in row.keys():
        tags.update(f"salience_feature_id:{item}" for item in _split(row["salience_feature_ids"]))
    for column in (
        "feature_domains",
        "salience_domains",
        "macro_feature_domains",
        "measurement_domains",
        "portrait_domains",
        "relation_types",
        "visible_ten_gods",
        "hidden_ten_gods",
        "mainline_keys",
        "mainline_domains",
    ):
        if column in row.keys():
            tags.update(f"{column}:{item}" for item in _split(row[column]))
    return tags


def _join(values: object) -> str:
    return "|".join(str(item) for item in values)


def _split(value: object) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    return [item for item in str(value or "").split("|") if item]


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"v20.{prefix}.{digest}"


def _is_salience_feature_id(feature_id: str) -> bool:
    return str(feature_id).startswith(
        (
            "feature.ten_god.focus.",
            "feature.element.prominent.",
            "feature.element.weak.",
            "feature.branch.relation_type.",
            "feature.time.relation_type.",
            "feature.time.ten_god.",
        )
    )


def _read_json_if_exists(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "not_built", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
