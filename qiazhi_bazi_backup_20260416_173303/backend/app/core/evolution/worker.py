"""
静默演化调度器：在 518K 设计空间随机抽样，做参数扰动与 Abs 对比。

不依赖 HTTP；可由管理 API 或 cron 触发 `EvolutionaryBatchRunner.run_once()`。
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config.physics_settings import resolve_physics_settings
from app.core.evolution.combination_space import TOTAL_BAZI_COMBINATION_SPACE, four_pillars_from_linear_index
from app.core.evolution.dna_registry import load_rule_genes
from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FlowState
from app.core.scanner import Scanner
from app.services.helpers.interaction_pipeline import evaluate_interactions
from app.skills.physics_engine import PhysicsInferenceSkill


def _backend_data_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data"


def _abs_proxy(tensor: Dict[str, Any]) -> float:
    meta = tensor.get("meta") if isinstance(tensor.get("meta"), dict) else {}
    ge = meta.get("global_entropy_metrics") if isinstance(meta.get("global_entropy_metrics"), dict) else {}
    v = ge.get("clash_abs_loss_total")
    if isinstance(v, (int, float)):
        return float(v)
    ent = meta.get("global_entropy")
    if isinstance(ent, (int, float)):
        return float(ent)
    return 0.0


def _historical_abs_median_from_feedback(max_lines: int = 200) -> Optional[float]:
    """从 skill_feedback.jsonl 粗估历史裁决轨迹（若有 line_preview 则略过，仅用 rating 计数代理）。"""
    p = _backend_data_dir() / "skill_feedback.jsonl"
    if not p.is_file():
        return None
    vals: List[float] = []
    try:
        lines = p.read_text(encoding="utf-8").splitlines()[-max_lines:]
    except OSError:
        return None
    for ln in lines:
        try:
            o = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if not isinstance(o, dict):
            continue
        if o.get("rating") != "precise":
            continue
        # 占位：精确反馈记 1.0 权重，用于与 delta 对齐度的弱代理
        vals.append(1.0)
    if not vals:
        return None
    vals.sort()
    return float(vals[len(vals) // 2])


@dataclass
class EvolutionBatchResult:
    samples: List[Dict[str, Any]]
    summary: Dict[str, Any]


class EvolutionaryBatchRunner:
    """随机抽取若干种子：基线 physics vs 扰动 physics 的 Abs 代理对比。"""

    def __init__(self, *, rng: Optional[random.Random] = None) -> None:
        self._rng = rng or random.Random()

    def run_once(
        self,
        *,
        n_seeds: int = 100,
        perturb_keys: Optional[List[str]] = None,
        perturb_scale: float = 0.06,
        log_path: Optional[Path] = None,
    ) -> EvolutionBatchResult:
        keys = perturb_keys or ["L1_OP_PROD_ETA", "L1_OP_DEST_ETA", "L1_OP_CONN_ETA"]
        skill = PhysicsInferenceSkill.instance()
        hist = _historical_abs_median_from_feedback()
        samples: List[Dict[str, Any]] = []
        closer = 0
        for _ in range(max(1, min(500, int(n_seeds)))):
            idx = self._rng.randrange(0, TOTAL_BAZI_COMBINATION_SPACE)
            pillars = four_pillars_from_linear_index(idx)
            matrix = Scanner().scan(pillars)
            meta = BaziMetadata(
                pillars=pillars,
                conflict_matrix=matrix,
                flow_state=FlowState.UNKNOWN,
                notes="evolution_batch",
            )
            base_cfg: Dict[str, Any] = {}
            consumed = skill.consume({"metadata": meta, "physics_config": base_cfg, "session_id": None})
            tensor_b = skill.produce(consumed)
            evaluate_interactions(
                physics_tensor=tensor_b,
                metadata=meta,
                interaction_params=skill.get_interaction_params(),
                physics_config=base_cfg,
            )
            abs_b = _abs_proxy(tensor_b)

            base_resolved = resolve_physics_settings(base_cfg)
            perturbed = dict(base_resolved)
            for k in keys:
                if k not in perturbed:
                    continue
                delta = float(perturbed[k]) * float(perturb_scale) * (self._rng.random() * 2.0 - 1.0)
                perturbed[k] = max(0.0, float(perturbed[k]) + delta)
            # 将扰动写入 physics_config 覆盖项（不经 DNA 准入，纯实验）
            p_cfg = {k: perturbed[k] for k in keys if k in perturbed}
            consumed_p = skill.consume({"metadata": meta, "physics_config": p_cfg, "session_id": None})
            tensor_p = skill.produce(consumed_p)
            evaluate_interactions(
                physics_tensor=tensor_p,
                metadata=meta,
                interaction_params=skill.get_interaction_params(),
                physics_config=p_cfg,
            )
            abs_p = _abs_proxy(tensor_p)
            diff = round(abs_p - abs_b, 6)
            align_hint = None
            if hist is not None:
                align_hint = round(1.0 / (1.0 + abs(abs_p - hist)), 4)
                if abs(abs_p - hist) < abs(abs_b - hist):
                    closer += 1
            samples.append(
                {
                    "linear_index": idx,
                    "abs_baseline": abs_b,
                    "abs_perturbed": abs_p,
                    "delta": diff,
                    "perturb_keys": keys,
                    "historical_alignment_hint": align_hint,
                }
            )

        summary = {
            "n": len(samples),
            "mean_delta": round(sum(s["delta"] for s in samples) / max(1, len(samples)), 6),
            "closer_to_feedback_proxy": closer,
            "dna_gene_count": len(load_rule_genes()),
        }
        out_path = log_path or (_backend_data_dir() / "evolution_batch_runs.jsonl")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        row = {"summary": summary, "samples_head": samples[:20], "full_count": len(samples)}
        with out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

        return EvolutionBatchResult(samples=samples, summary=summary)
