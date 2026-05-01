from __future__ import annotations

import json
import sqlite3
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.corpus.job_runner import full_precompute_root
from v20.knowledge.rule_proposal import build_first_wave_rule_proposals


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
    portrait_learning_path: Path
    rule_support_path: Path
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
            "portrait_learning_path": str(self.portrait_learning_path),
            "rule_support_path": str(self.rule_support_path),
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
        portrait_learning_path=artifact_dir / "portrait_axis_learning.json",
        rule_support_path=artifact_dir / "rule_proposal_support.json",
        postgres_manifest_path=artifact_dir / "postgres_import_manifest.json",
        parquet_manifest_path=artifact_dir / "parquet_export_manifest.json",
        status_path=artifact_dir / "artifact_status.json",
    )


def build_corpus_artifacts(
    run_id: str = DEFAULT_ARTIFACT_RUN_ID,
    *,
    runtime_dir: Path | None = None,
    status_every: int = 25_000,
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
    }
    cooccurrence: Counter[str] = Counter()
    cluster_counts: Counter[str] = Counter()
    cluster_examples: dict[str, list[str]] = defaultdict(list)
    rule_support = _rule_support_seed()
    total = 0
    feature_count_sum = 0
    knowledge_ref_count_sum = 0
    portrait_axis_count_sum = 0

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
            batch.append(_sqlite_row(flat_row))
            _update_counters(counters, label)
            _update_rule_support(rule_support, label)
            _update_portrait_cooccurrence(cooccurrence, label)
            cluster_key = _cluster_key(label)
            cluster_counts[cluster_key] += 1
            if len(cluster_examples[cluster_key]) < 5:
                cluster_examples[cluster_key].append(str(label["case_id"]))
            density = label.get("evidence_density", {})
            feature_count_sum += int(density.get("feature_count", 0))
            knowledge_ref_count_sum += int(density.get("knowledge_ref_count", 0))
            portrait_axis_count_sum += int(density.get("portrait_axis_count", 0))
            total += 1
            if len(batch) >= 2_000:
                conn.executemany(SQLITE_INSERT, batch)
                conn.commit()
                batch.clear()
            if total % status_every == 0:
                _write_json(
                    paths.status_path,
                    _status_payload(paths, "running", total, started_at, time.monotonic() - started),
                )
        if batch:
            conn.executemany(SQLITE_INSERT, batch)
            conn.commit()
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
    rule_support_summary = _rule_support_summary(paths, total, rule_support)
    postgres_manifest = _postgres_import_manifest(paths, total)
    parquet_manifest = _parquet_manifest(paths, total)
    _write_json(paths.coverage_summary_path, coverage)
    _write_json(paths.portrait_learning_path, portrait_learning)
    _write_json(paths.rule_support_path, rule_support_summary)
    _write_json(paths.postgres_manifest_path, postgres_manifest)
    _write_json(paths.parquet_manifest_path, parquet_manifest)
    status = _status_payload(paths, "completed", total, started_at, time.monotonic() - started)
    status["artifact_outputs"] = {
        "coverage_summary": str(paths.coverage_summary_path),
        "sqlite_index": str(paths.sqlite_index_path),
        "flat_labels": str(paths.flat_labels_path),
        "portrait_axis_learning": str(paths.portrait_learning_path),
        "rule_proposal_support": str(paths.rule_support_path),
        "postgres_import_manifest": str(paths.postgres_manifest_path),
        "parquet_export_manifest": str(paths.parquet_manifest_path),
    }
    _write_json(paths.status_path, status)
    return status


def read_corpus_artifact_status(run_id: str = DEFAULT_ARTIFACT_RUN_ID, *, runtime_dir: Path | None = None) -> dict[str, object]:
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


def read_corpus_coverage_summary(run_id: str = DEFAULT_ARTIFACT_RUN_ID, *, runtime_dir: Path | None = None) -> dict[str, object]:
    path = corpus_artifact_paths(run_id, runtime_dir=runtime_dir).coverage_summary_path
    if not path.exists():
        return {"version": "v20.corpus_coverage_summary.v1", "status": "not_built", "runtime_mutation": False}
    return json.loads(path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def find_similar_cases(
    case_id: str,
    *,
    run_id: str = DEFAULT_ARTIFACT_RUN_ID,
    limit: int = 8,
    runtime_dir: Path | None = None,
) -> dict[str, object]:
    paths = corpus_artifact_paths(run_id, runtime_dir=runtime_dir)
    if not paths.sqlite_index_path.exists():
        return {
            "version": "v20.corpus_similar_cases.v1",
            "status": "index_not_built",
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
    candidates = conn.execute(
        """
        SELECT * FROM corpus_cases
        WHERE case_id != ?
          AND day_master_element = ?
          AND day_master_capacity = ?
        LIMIT 5000
        """,
        (case_id, query["day_master_element"], query["day_master_capacity"]),
    ).fetchall()
    conn.close()
    query_tags = _row_tags(query)
    scored = []
    for candidate in candidates:
        tags = _row_tags(candidate)
        score = len(query_tags & tags) / max(1, len(query_tags | tags))
        scored.append((score, candidate))
    matches = [
        {
            "case_id": row["case_id"],
            "input_hash": row["input_hash"],
            "pillar_displays": json.loads(row["pillar_displays"]),
            "score": round(score, 4),
            "day_master": row["day_master"],
            "day_master_capacity": row["day_master_capacity"],
            "feature_domains": _split(row["feature_domains"]),
            "portrait_domains": _split(row["portrait_domains"]),
            "relation_types": _split(row["relation_types"]),
        }
        for score, row in sorted(scored, key=lambda item: (-item[0], item[1]["case_id"]))[:limit]
    ]
    return {
        "version": "v20.corpus_similar_cases.v1",
        "status": "ready",
        "case_id": case_id,
        "query": {
            "input_hash": query["input_hash"],
            "pillar_displays": json.loads(query["pillar_displays"]),
            "day_master": query["day_master"],
            "day_master_capacity": query["day_master_capacity"],
        },
        "match_count": len(matches),
        "matches": matches,
        "runtime_mutation": False,
        "guardrails": [
            "SIMILARITY_IS_STRUCTURAL_RETRIEVAL",
            "NO_DESTINY_OUTCOME_INFERENCE",
            "NO_RULE_ACTIVATION",
        ],
    }


SQLITE_INSERT = """
INSERT INTO corpus_cases (
  line_no, case_id, input_hash, snapshot_hash, pillar_displays,
  day_master, day_master_element, day_master_capacity,
  feature_domains, macro_feature_domains, measurement_domains, portrait_domains,
  relation_types, visible_ten_gods, hidden_ten_gods, question_keys, knowledge_ids,
  useful_god_candidate_count, wealth_feature_present, feature_count, knowledge_ref_count, portrait_axis_count
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
          feature_domains TEXT NOT NULL,
          macro_feature_domains TEXT NOT NULL,
          measurement_domains TEXT NOT NULL,
          portrait_domains TEXT NOT NULL,
          relation_types TEXT NOT NULL,
          visible_ten_gods TEXT NOT NULL,
          hidden_ten_gods TEXT NOT NULL,
          question_keys TEXT NOT NULL,
          knowledge_ids TEXT NOT NULL,
          useful_god_candidate_count INTEGER NOT NULL,
          wealth_feature_present INTEGER NOT NULL,
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
        "CREATE INDEX idx_corpus_wealth ON corpus_cases(wealth_feature_present)",
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
        "feature_domains": label.get("feature_domains", ()),
        "macro_feature_domains": label.get("macro_feature_domains", ()),
        "measurement_domains": label.get("measurement_domains", ()),
        "portrait_domains": label.get("portrait_domains", ()),
        "relation_types": label.get("relation_types", ()),
        "visible_ten_gods": label.get("visible_ten_gods", ()),
        "hidden_ten_gods": label.get("hidden_ten_gods", ()),
        "question_keys": label.get("question_keys", ()),
        "knowledge_ids": label.get("knowledge_ids", ()),
        "useful_god_candidate_count": label.get("useful_god_candidate_count", 0),
        "wealth_feature_present": label.get("wealth_feature_present", False),
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
        _join(row["feature_domains"]),
        _join(row["macro_feature_domains"]),
        _join(row["measurement_domains"]),
        _join(row["portrait_domains"]),
        _join(row["relation_types"]),
        _join(row["visible_ten_gods"]),
        _join(row["hidden_ten_gods"]),
        _join(row["question_keys"]),
        _join(row["knowledge_ids"]),
        int(row["useful_god_candidate_count"]),
        1 if row["wealth_feature_present"] else 0,
        int(row["feature_count"]),
        int(row["knowledge_ref_count"]),
        int(row["portrait_axis_count"]),
    )


def _update_counters(counters: dict[str, Counter[str]], label: dict[str, object]) -> None:
    for key in ("day_master", "day_master_element", "day_master_capacity"):
        counters[key][str(label.get(key, ""))] += 1
    for key in (
        "feature_domains",
        "macro_feature_domains",
        "measurement_domains",
        "portrait_domains",
        "relation_types",
        "visible_ten_gods",
        "hidden_ten_gods",
        "question_keys",
        "knowledge_ids",
    ):
        counters[key].update(str(item) for item in label.get(key, ()))
    counters["useful_god_candidate_count"][str(label.get("useful_god_candidate_count", 0))] += 1
    counters["wealth_feature_present"]["true" if label.get("wealth_feature_present") else "false"] += 1


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
                "support_count": 0,
                "sample_case_ids": [],
            }
    return rows


def _update_rule_support(rule_support: dict[str, dict[str, object]], label: dict[str, object]) -> None:
    feature_ids = tuple(str(item) for item in label.get("feature_ids", ()))
    for row in rule_support.values():
        hooks = tuple(str(item) for item in row["emits_feature_hooks"])
        if hooks and all(any(feature_id.startswith(hook) for feature_id in feature_ids) for hook in hooks):
            row["support_count"] = int(row["support_count"]) + 1
            samples = row["sample_case_ids"]
            if isinstance(samples, list) and len(samples) < 5:
                samples.append(str(label["case_id"]))


def _update_portrait_cooccurrence(cooccurrence: Counter[str], label: dict[str, object]) -> None:
    domains = sorted(str(item) for item in label.get("portrait_domains", ()))
    for left_index, left in enumerate(domains):
        for right in domains[left_index + 1 :]:
            cooccurrence[f"{left}|{right}"] += 1


def _cluster_key(label: dict[str, object]) -> str:
    relation = "+".join(str(item) for item in label.get("relation_types", ())) or "quiet"
    wealth = "wealth" if label.get("wealth_feature_present") else "no_wealth"
    return "|".join(
        (
            str(label.get("day_master_element", "")),
            str(label.get("day_master_capacity", "")),
            relation,
            wealth,
            f"useful{label.get('useful_god_candidate_count', 0)}",
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


def _rule_support_summary(
    paths: CorpusArtifactPaths,
    total: int,
    support: dict[str, dict[str, object]],
) -> dict[str, object]:
    proposals = sorted(support.values(), key=lambda row: (-int(row["support_count"]), str(row["proposal_id"])))
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
            "shadow_rule_path_frequency",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_SUPPORT_ONLY",
            "NO_RULE_ACTIVATION",
            "NO_USER_VISIBLE_VERDICT",
        ],
    }


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


def _row_tags(row: sqlite3.Row) -> set[str]:
    tags = {
        f"day_master:{row['day_master']}",
        f"element:{row['day_master_element']}",
        f"capacity:{row['day_master_capacity']}",
        f"wealth:{row['wealth_feature_present']}",
    }
    for column in (
        "feature_domains",
        "macro_feature_domains",
        "measurement_domains",
        "portrait_domains",
        "relation_types",
        "visible_ten_gods",
        "hidden_ten_gods",
    ):
        tags.update(f"{column}:{item}" for item in _split(row[column]))
    return tags


def _join(values: object) -> str:
    return "|".join(str(item) for item in values)


def _split(value: object) -> list[str]:
    return [item for item in str(value or "").split("|") if item]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
