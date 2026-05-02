from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.corpus.artifacts import read_corpus_training_artifacts
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report

ProgressCallback = Callable[[str], None]


def build_rule_subcondition_split_report(
    domain: str = "",
    *,
    limit: int = 64,
    per_rule: int = 5,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    validation = build_knowledge_rule_validation_report(domain, limit=limit)
    corpus = read_corpus_training_artifacts()
    corpus_by_source = _corpus_proposals_by_source(corpus)
    definitions = [
        row
        for row in validation.get("definitions", ())
        if isinstance(row, dict) and row.get("validation_state") == "synthetic_passed_needs_subconditions"
    ]
    packets = []
    for index, definition in enumerate(definitions, start=1):
        _emit(progress, f"[{index}/{len(definitions)}] split {definition.get('domain', '')}")
        packets.append(
            _split_packet(
                definition,
                corpus_by_source.get(str(definition.get("source_knowledge_id", "")), {}),
                per_rule=max(1, per_rule),
            )
        )
    missing_corpus = [
        str(packet["source_knowledge_id"])
        for packet in packets
        if packet["corpus_state"] == "missing_corpus_training"
    ]
    return {
        "version": "v20.rule_subcondition_split_report.v1",
        "status": "ready" if packets else "empty",
        "domain": domain.strip(),
        "packet_count": len(packets),
        "subcondition_count": sum(len(packet["subconditions"]) for packet in packets),
        "counterexample_candidate_count": sum(len(packet["counterexample_candidates"]) for packet in packets),
        "missing_corpus_count": len(missing_corpus),
        "quality_status": "needs_corpus" if missing_corpus else "active_ready",
        "packets": packets,
        "upstream": {
            "validation_status": validation.get("status", ""),
            "validation_state_counts": validation.get("state_counts", {}),
            "corpus_training_status": corpus.get("status", ""),
            "corpus_training_run_id": corpus.get("run_id", ""),
        },
        "runtime_mutation": False,
        "guardrails": [
            "SUBCONDITION_SPLIT_IS_OFFLINE_REVIEW_SIGNAL",
            "FULL_CORPUS_PROVIDES_PRIOR_AND_COVERAGE_NOT_TRUTH",
            "ACTIVE_RULE_ITERATION",
            "DECISION_REGISTRY_REQUIRED_BEFORE_PROMOTION",
        ],
    }


def write_rule_subcondition_split_artifact(
    *,
    domain: str = "",
    limit: int = 64,
    per_rule: int = 5,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = build_rule_subcondition_split_report(domain, limit=limit, per_rule=per_rule, progress=progress)
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "rule_subcondition_split"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{_safe(domain)}" if domain.strip() else ""
    run_path = directory / f"rule_subcondition_split{suffix}_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.rule_subcondition_split_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "quality_status": report["quality_status"],
        "packet_count": report["packet_count"],
        "subcondition_count": report["subcondition_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "ACTIVE_RULE_ITERATION",
        ],
    }


def read_rule_subcondition_split_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "rule_subcondition_split") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.rule_subcondition_split_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _split_packet(definition: dict[str, object], corpus_row: dict[str, object], *, per_rule: int) -> dict[str, object]:
    source_id = str(definition.get("source_knowledge_id", ""))
    broad_features = _broad_feature_ids(corpus_row)
    signatures = [
        row
        for row in corpus_row.get("top_exact_feature_signatures", ())[:per_rule]
        if isinstance(row, dict) and row.get("value")
    ]
    subconditions = tuple(
        _subcondition(definition, signature, broad_features, index)
        for index, signature in enumerate(signatures, start=1)
    )
    return {
        "version": "v20.rule_subcondition_split_packet.v1",
        "packet_id": f"v20.rule_subcondition_split.{_hash(source_id, str(definition.get('rule_key', '')))}",
        "rule_key": definition.get("rule_key", ""),
        "source_knowledge_id": source_id,
        "domain": definition.get("domain", ""),
        "portrait": definition.get("portrait", ""),
        "question": definition.get("question", ""),
        "corpus_state": "ready" if corpus_row else "missing_corpus_training",
        "support_count": int(corpus_row.get("support_count", 0) or 0),
        "support_ratio": float(corpus_row.get("support_ratio", 0.0) or 0.0),
        "support_quality": str(corpus_row.get("support_quality", "")),
        "broad_feature_ids": broad_features,
        "subconditions": subconditions,
        "counterexample_candidates": _counterexample_candidates(corpus_row, broad_features, per_rule=per_rule),
        "recommended_review_action": "review_subconditions_and_add_counterexamples",
        "runtime_allowed": True,
        "guardrails": [
            "PACKET_IS_REVIEW_OBJECT",
            "SUBCONDITIONS_ARE_CANDIDATES_ONLY",
            "HUMAN_OR_ADMIN_DECISION_REQUIRED",
        ],
    }


def _subcondition(
    definition: dict[str, object],
    signature: dict[str, object],
    broad_features: tuple[str, ...],
    index: int,
) -> dict[str, object]:
    feature_ids = _signature_feature_ids(str(signature.get("value", "")))
    discriminator_ids = tuple(row for row in feature_ids if row not in broad_features)[:6] or feature_ids[:6]
    domain = str(definition.get("domain", ""))
    return {
        "subcondition_key": f"v20.subcondition.{_hash(str(definition.get('rule_key', '')), str(index), '|'.join(discriminator_ids))}",
        "rank": index,
        "domain": domain,
        "support_count": int(signature.get("count", 0) or 0),
        "support_weight": float(signature.get("weight", 0.0) or 0.0),
        "feature_ids": feature_ids,
        "discriminator_feature_ids": discriminator_ids,
        "condition_model": {
            "type": "all_of_feature_ids",
            "all_of": [{"feature_id": feature_id} for feature_id in discriminator_ids],
            "source": "full_corpus_exact_feature_signature",
        },
        "review_prompt": _review_prompt(domain, discriminator_ids),
        "runtime_allowed": True,
    }


def _counterexample_candidates(
    corpus_row: dict[str, object],
    broad_features: tuple[str, ...],
    *,
    per_rule: int,
) -> tuple[dict[str, object], ...]:
    rows = []
    for index, cluster in enumerate(corpus_row.get("top_clusters", ())[: max(2, per_rule)], start=1):
        if not isinstance(cluster, dict):
            continue
        rows.append(
            {
                "counterexample_key": f"v20.counterexample.{_hash(str(cluster.get('cluster_id', '')), str(index))}",
                "cluster_id": cluster.get("cluster_id", ""),
                "cluster_key": cluster.get("cluster_key", ""),
                "support_count": int(cluster.get("count", 0) or 0),
                "support_weight": float(cluster.get("weight", 0.0) or 0.0),
                "contrast_against_broad_features": broad_features[:6],
                "review_question": "这类聚类是否应该排除、降权，或单独拆成另一条子规则？",
                "runtime_allowed": True,
            }
        )
    return tuple(rows[:per_rule])


def _corpus_proposals_by_source(corpus: dict[str, object]) -> dict[str, dict[str, object]]:
    training = corpus.get("rule_proposal_training", {})
    if not isinstance(training, dict):
        return {}
    return {
        str(row["source_knowledge_id"]): row
        for row in training.get("proposals", ())
        if isinstance(row, dict) and row.get("source_knowledge_id")
    }


def _broad_feature_ids(corpus_row: dict[str, object]) -> tuple[str, ...]:
    case_count = int(corpus_row.get("support_count", 0) or 0)
    rows = []
    for item in corpus_row.get("top_matched_feature_ids", ()):
        if not isinstance(item, dict):
            continue
        weight = float(item.get("weight", 0.0) or 0.0)
        count = int(item.get("count", 0) or 0)
        value = str(item.get("value", ""))
        if value and (weight >= 0.9 or (case_count and count == case_count)):
            rows.append(value)
    return tuple(dict.fromkeys(rows))


def _signature_feature_ids(value: str) -> tuple[str, ...]:
    return tuple(row for row in value.split("|") if row.startswith("feature."))


def _review_prompt(domain: str, feature_ids: tuple[str, ...]) -> str:
    material = "、".join(_feature_label(row) for row in feature_ids[:4]) or "当前特征组合"
    prompts = {
        "career": f"这条事业规则是否只在「{material}」同时出现时成立？",
        "relationship": f"这条关系投影是否只在「{material}」同时出现时成立？",
        "health": f"这条健康边界是否只用于「{material}」这类五行压力组合？",
        "wealth": f"这条财运规则是否只在「{material}」同时出现时成立？",
        "strength": f"这条强弱裁决是否需要用「{material}」作为子条件？",
    }
    return prompts.get(domain, f"这条规则是否需要用「{material}」作为子条件？")


def _feature_label(feature_id: str) -> str:
    exact = {
        "feature.strength.capacity_needs_support": "日主需要扶助",
        "feature.strength.borderline_capacity": "日主强弱近边界",
        "feature.strength.supported_capacity": "日主有支撑",
        "feature.ten_god.visible_relation": "明透十神",
        "feature.ten_god.hidden_relation": "藏干十神",
        "feature.branch.visible_relation": "地支关系",
        "feature.branch.relation_quiet": "地支相对安静",
        "feature.wealth.visible_material": "财星明透可见",
        "feature.wealth.hidden_material": "财星仅在藏干",
        "feature.wealth.material_not_visible": "财星材料不显",
        "feature.pattern.review_index": "格局复核",
        "feature.useful_god.candidate_paths": "用神候选路径",
        "feature.useful_god.evidence_gate": "用神证据门槛",
        "feature.element.balance_distribution": "五行分布",
    }
    if feature_id in exact:
        return exact[feature_id]
    for prefix, labels in (
        ("feature.ten_god.focus.", _TEN_GOD_LABELS),
        ("feature.branch.relation_type.", _BRANCH_RELATION_LABELS),
        ("feature.element.prominent.", _ELEMENT_LABELS),
        ("feature.element.weak.", _ELEMENT_LABELS),
    ):
        if feature_id.startswith(prefix):
            value = feature_id.removeprefix(prefix)
            if prefix == "feature.ten_god.focus.":
                return f"十神:{labels.get(value, value)}"
            if prefix == "feature.branch.relation_type.":
                return f"地支:{labels.get(value, value)}"
            if prefix == "feature.element.prominent.":
                return f"五行偏显:{labels.get(value, value)}"
            return f"五行偏弱:{labels.get(value, value)}"
    return feature_id.replace("feature.", "").replace("_", " ")


_TEN_GOD_LABELS = {
    "bi_jian": "比肩",
    "jie_cai": "劫财",
    "shi_shen": "食神",
    "shang_guan": "伤官",
    "pian_cai": "偏财",
    "zheng_cai": "正财",
    "qi_sha": "七杀",
    "zheng_guan": "正官",
    "pian_yin": "偏印",
    "zheng_yin": "正印",
}

_BRANCH_RELATION_LABELS = {
    "clash": "冲",
    "harmony": "合",
    "harm": "害",
    "break": "破",
    "punishment": "刑",
    "three_harmony": "三合",
    "three_meeting": "三会",
}

_ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}


def _hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(f"[v20-rule-split] {message}")
