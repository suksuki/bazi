from __future__ import annotations

import argparse
from copy import deepcopy
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.mingli_agent.phase0_governance import load_json, validate_phase0_assets
from scripts.v50_prepare_vnext_phase0_g1 import ASSET_PATHS


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "vnext_phase0_expert_reference_authoring_policy_v1.json"
TAXONOMY_PATH = ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v2.json"
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "expert-reference-workspace-v1"


def prepare_workspace(*, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    policy = load_json(POLICY_PATH)
    validation = _validation()
    manifest = load_json(ASSET_PATHS["formal_manifest"])
    taxonomy = load_json(TAXONOMY_PATH)
    fixtures = {row["case_id"]: row for row in taxonomy["cases"]}
    source = load_json(ASSET_PATHS["expert_reference"])
    source_rows = {row["chart_id"]: row for row in source["references"]}
    references = []
    for case in manifest["cases"]:
        case_id = case["case_id"]
        birth = fixtures[case_id]["birth_input"]
        row = source_rows[case_id]
        references.append(
            {
                "chart_id": case_id,
                "chart_fact_hash": validation["chart_fact_hashes"][case_id],
                "reference_version": row.get("reference_version", "v1"),
                "benchmark_role": case["benchmark_role"],
                "pillars": [
                    birth["year_pillar"],
                    birth["month_pillar"],
                    birth["day_pillar"],
                    birth["hour_pillar"],
                ],
                "status": "draft_human_authoring",
                **{field: [] for field in policy["required_semantic_fields"]},
                "author": "",
                "frozen_at": "",
                "human_signature": "",
                "revision_history": [],
            }
        )
    workspace = {
        "version": "deepbazi.vnext_phase0.expert_reference_authoring_workspace.v1",
        "status": "draft_human_authoring",
        "human_authorship_required": True,
        "semantic_item_contract": policy["semantic_item_contract"],
        "references": references,
        "boundaries": {
            "reality_evidence_allowed": False,
            "model_or_lane_output_allowed": False,
            "llm_semantic_authorship_allowed": False,
            "machine_format_validation_allowed": True,
        },
    }
    workspace_path = output_dir / "EXPERT_REFERENCE_AUTHORING_WORKSPACE.json"
    _write_json(workspace_path, workspace)
    (output_dir / "EXPERT_REFERENCE_AUTHORING_GUIDE.md").write_text(
        _guide(workspace=workspace), encoding="utf-8"
    )
    _write_json(
        output_dir / "EXPERT_REFERENCE_ERRATUM_TEMPLATE.json",
        {
            "version": "deepbazi.vnext_phase0.expert_reference_erratum.v1",
            "status": "draft_human_signoff",
            "erratum_id": "",
            "base_reference_sha256": "",
            "target_version": "",
            "reason": "",
            "changes": [
                {
                    "chart_id": "",
                    "field": "",
                    "old_value_sha256": "",
                    "new_value": [],
                    "reason": "",
                    "source_refs": [],
                }
            ],
            "author": "",
            "signed_at": "",
            "human_signature": "",
        },
    )
    status = validate_workspace(workspace=workspace, require_frozen=False)
    _write_json(output_dir / "EXPERT_REFERENCE_WORKSPACE_VALIDATION.json", status)
    return {
        "status": "workspace_ready_for_human_authoring",
        "workspace_path": str(workspace_path),
        "chart_count": len(references),
        "fact_hashes_present": all(bool(row["chart_fact_hash"]) for row in references),
        "semantic_content_authored_by_machine": False,
    }


def validate_workspace(*, workspace: dict[str, Any], require_frozen: bool) -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    validation = _validation()
    expected_ids = set(validation["formal_ids"])
    rows = workspace.get("references", [])
    row_ids = {row.get("chart_id") for row in rows}
    errors: list[str] = []
    warnings: list[str] = []
    if row_ids != expected_ids:
        errors.append("workspace_chart_ids_do_not_match_formal_manifest")
    forbidden_hits = sorted(_find_forbidden_fields(workspace, set(policy["forbidden_recursive_fields"])))
    if forbidden_hits:
        errors.append(f"forbidden_fields_present:{','.join(forbidden_hits)}")

    for row in rows:
        chart_id = str(row.get("chart_id") or "unknown")
        if row.get("chart_fact_hash") != validation["chart_fact_hashes"].get(chart_id):
            errors.append(f"chart_fact_hash_mismatch:{chart_id}")
        for field in policy["required_semantic_fields"]:
            values = row.get(field)
            if not isinstance(values, list):
                errors.append(f"semantic_field_not_list:{chart_id}:{field}")
                continue
            if require_frozen and not values:
                errors.append(f"semantic_field_empty:{chart_id}:{field}")
            for index, item in enumerate(values):
                errors.extend(_semantic_item_errors(chart_id=chart_id, field=field, index=index, item=item, policy=policy))
        if require_frozen:
            if row.get("status") != "frozen":
                errors.append(f"reference_not_frozen:{chart_id}")
            for key in ("author", "frozen_at", "human_signature"):
                if not str(row.get(key) or "").strip():
                    errors.append(f"freeze_metadata_missing:{chart_id}:{key}")
        elif row.get("status") == "draft_human_authoring":
            warnings.append(f"human_content_pending:{chart_id}")

    status = "passed" if not errors and (not require_frozen or not warnings) else "pending" if not errors else "failed"
    return {
        "version": "deepbazi.vnext_phase0.expert_reference_workspace_validation.v1",
        "status": status,
        "require_frozen": require_frozen,
        "chart_count": len(rows),
        "errors": _unique(errors),
        "warnings": _unique(warnings),
        "forbidden_field_hits": forbidden_hits,
        "llm_semantic_authorship_checked": False,
        "human_attestation_required": require_frozen,
    }


def freeze_candidate(*, workspace_path: Path, output_path: Path) -> dict[str, Any]:
    workspace = load_json(workspace_path)
    validation = validate_workspace(workspace=workspace, require_frozen=True)
    if validation["status"] != "passed":
        raise ValueError(f"expert_reference_freeze_rejected:{','.join(validation['errors'])}")
    candidate = {
        "version": "deepbazi.vnext_phase0.expert_reference_space.v2",
        "round": "round1_prior_reading",
        "status": "frozen",
        "human_authorship_required": True,
        "references": [
            {key: value for key, value in row.items() if key != "pillars"}
            for row in workspace["references"]
        ],
        "boundaries": {
            "single_canonical_answer_required": False,
            "reality_evidence_allowed": False,
            "llm_authorship_allowed": False,
            "silent_edits_after_freeze_allowed": False,
            "errata_must_be_versioned": True,
        },
        "freeze_metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workspace_sha256": sha256(workspace_path.read_bytes()).hexdigest(),
            "machine_semantic_authorship": False,
        },
    }
    _write_json(output_path, candidate)
    return {
        "status": "frozen_candidate_written",
        "path": str(output_path),
        "sha256": sha256(output_path.read_bytes()).hexdigest(),
        "chart_count": len(candidate["references"]),
    }


def apply_erratum(*, base_path: Path, erratum_path: Path, output_path: Path) -> dict[str, Any]:
    base = load_json(base_path)
    erratum = load_json(erratum_path)
    base_validation = validate_workspace(workspace=base, require_frozen=True)
    if base_validation["status"] != "passed":
        raise ValueError(f"erratum_base_not_frozen:{','.join(base_validation['errors'])}")
    errors: list[str] = []
    if erratum.get("status") != "human_signed":
        errors.append("erratum_not_human_signed")
    for key in ("erratum_id", "base_reference_sha256", "target_version", "reason", "author", "signed_at", "human_signature"):
        if not erratum.get(key):
            errors.append(f"erratum_metadata_missing:{key}")
    actual_base_hash = sha256(base_path.read_bytes()).hexdigest()
    if erratum.get("base_reference_sha256") != actual_base_hash:
        errors.append("erratum_base_hash_mismatch")
    policy = load_json(POLICY_PATH)
    allowed_fields = set(policy["required_semantic_fields"])
    rows = {row["chart_id"]: row for row in base["references"]}
    if not erratum.get("changes"):
        errors.append("erratum_changes_empty")
    for index, change in enumerate(erratum.get("changes", [])):
        chart_id = change.get("chart_id")
        field = change.get("field")
        prefix = f"change:{index}"
        if chart_id not in rows:
            errors.append(f"erratum_unknown_chart:{prefix}")
            continue
        if field not in allowed_fields:
            errors.append(f"erratum_field_not_semantic:{prefix}")
            continue
        old_value = rows[chart_id][field]
        if change.get("old_value_sha256") != _canonical_hash(old_value):
            errors.append(f"erratum_old_value_hash_mismatch:{prefix}")
        if not change.get("reason") or not change.get("source_refs"):
            errors.append(f"erratum_change_rationale_missing:{prefix}")
        new_value = change.get("new_value")
        if not isinstance(new_value, list) or not new_value:
            errors.append(f"erratum_new_value_empty:{prefix}")
            continue
        for item_index, item in enumerate(new_value):
            errors.extend(
                _semantic_item_errors(
                    chart_id=chart_id,
                    field=field,
                    index=item_index,
                    item=item,
                    policy=policy,
                )
            )
    forbidden_hits = _find_forbidden_fields(erratum, set(policy["forbidden_recursive_fields"]))
    if forbidden_hits:
        errors.append(f"erratum_forbidden_fields:{','.join(sorted(forbidden_hits))}")
    if errors:
        raise ValueError(f"expert_reference_erratum_rejected:{','.join(_unique(errors))}")

    updated = deepcopy(base)
    updated["version"] = erratum["target_version"]
    updated["freeze_metadata"] = {
        **updated.get("freeze_metadata", {}),
        "previous_reference_sha256": actual_base_hash,
        "latest_erratum_id": erratum["erratum_id"],
        "latest_erratum_sha256": sha256(erratum_path.read_bytes()).hexdigest(),
    }
    updated_rows = {row["chart_id"]: row for row in updated["references"]}
    for change in erratum["changes"]:
        row = updated_rows[change["chart_id"]]
        row[change["field"]] = change["new_value"]
        row["reference_version"] = erratum["target_version"]
        row.setdefault("revision_history", []).append(
            {
                "erratum_id": erratum["erratum_id"],
                "field": change["field"],
                "reason": change["reason"],
                "author": erratum["author"],
                "signed_at": erratum["signed_at"],
                "human_signature": erratum["human_signature"],
            }
        )
    _write_json(output_path, updated)
    final_validation = validate_workspace(workspace=updated, require_frozen=True)
    if final_validation["status"] != "passed":
        output_path.unlink(missing_ok=True)
        raise ValueError(f"expert_reference_erratum_output_invalid:{','.join(final_validation['errors'])}")
    return {
        "status": "versioned_erratum_candidate_written",
        "path": str(output_path),
        "target_version": erratum["target_version"],
        "sha256": sha256(output_path.read_bytes()).hexdigest(),
    }


def _semantic_item_errors(
    *, chart_id: str, field: str, index: int, item: Any, policy: dict[str, Any]
) -> list[str]:
    prefix = f"{chart_id}:{field}:{index}"
    if not isinstance(item, dict):
        return [f"semantic_item_not_object:{prefix}"]
    errors = [
        f"semantic_item_missing:{prefix}:{key}"
        for key in policy["semantic_item_contract"]["required_fields"]
        if not item.get(key)
    ]
    if item.get("evidence_basis") not in policy["semantic_item_contract"]["evidence_basis_enum"]:
        errors.append(f"semantic_item_invalid_evidence_basis:{prefix}")
    if not isinstance(item.get("source_refs"), list) or not item.get("source_refs"):
        errors.append(f"semantic_item_source_refs_empty:{prefix}")
    return errors


def _find_forbidden_fields(value: Any, forbidden: set[str]) -> set[str]:
    hits: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                hits.add(key)
            hits.update(_find_forbidden_fields(child, forbidden))
    elif isinstance(value, list):
        for child in value:
            hits.update(_find_forbidden_fields(child, forbidden))
    return hits


def _validation() -> dict[str, Any]:
    return validate_phase0_assets(
        taxonomy_path=TAXONOMY_PATH,
        development_path=ASSET_PATHS["development_set"],
        model_selection_path=ASSET_PATHS["model_selection_set"],
        formal_manifest_path=ASSET_PATHS["formal_manifest"],
        expert_reference_path=ASSET_PATHS["expert_reference"],
        reality_evidence_path=ASSET_PATHS["reality_evidence"],
    )


def _guide(*, workspace: dict[str, Any]) -> str:
    sample = {
        "statement": "写明一个可接受的专业判断，不写唯一标准答案",
        "reason": "说明为何该判断在这张原局上成立或值得保留",
        "evidence_basis": "structural",
        "source_refs": ["使用工作区内确认过的命盘事实引用"],
    }
    return "\n".join(
        [
            "# Phase 0 Human Expert Reference Authoring Guide",
            "",
            f"- Charts: `{len(workspace['references'])}`",
            "- Semantic author: human Mingli expert only",
            "- LLM semantic authorship: prohibited",
            "- Reality Evidence and Lane outputs: prohibited",
            "",
            "每个语义字段至少填写一条。每条必须同时写判断、理由、证据类型和命盘事实引用：",
            "",
            "```json",
            json.dumps(sample, ensure_ascii=False, indent=2),
            "```",
            "",
            "完成后把每张记录设为 `frozen`，填写 `author`、ISO 时间 `frozen_at` 和人工签名 `human_signature`，再运行严格校验。机器只能检查完整性、哈希和禁区，不能决定专业内容。",
            "",
        ]
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or validate the human Expert Reference workspace.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--validate", default="")
    parser.add_argument("--require-frozen", action="store_true")
    parser.add_argument("--freeze-candidate", default="")
    parser.add_argument("--apply-erratum", default="")
    parser.add_argument("--base-frozen", default="")
    parser.add_argument("--erratum-output", default="")
    args = parser.parse_args()
    if args.apply_erratum:
        if not args.base_frozen or not args.erratum_output:
            raise ValueError("erratum_requires_base_frozen_and_output")
        result = apply_erratum(
            base_path=Path(args.base_frozen),
            erratum_path=Path(args.apply_erratum),
            output_path=Path(args.erratum_output),
        )
    elif args.validate:
        path = Path(args.validate)
        if args.freeze_candidate:
            result = freeze_candidate(workspace_path=path, output_path=Path(args.freeze_candidate))
        else:
            result = validate_workspace(workspace=load_json(path), require_frozen=args.require_frozen)
    else:
        result = prepare_workspace(output_dir=Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] not in {"failed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
