"""
因果基因库持久化 + DnaOverlay：演化参数覆盖 physics_settings。

- 默认文件：`backend/data/dna_registry.json`
- 准入：仅当 `evolution_admission.json` 中 `admit_evolved_to_mainnet=true`（或环境变量显式放行）时，
  高 `fitness_score` 的基因才覆盖运行时物理键。
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional, Set

from app.core.config.physics_settings import DEFAULT_PHYSICS_SETTINGS
from app.plugins.base_physics.skill_manifest_loader import list_base_physics_skills, load_base_physics_skill_manifest

_lock = threading.RLock()

_MIN_FITNESS_FOR_OVERLAY = 0.12
_ALLOWED_PHYSICS_KEYS: Set[str] = set()


def _allowed_physics_keys() -> Set[str]:
    global _ALLOWED_PHYSICS_KEYS
    if _ALLOWED_PHYSICS_KEYS:
        return _ALLOWED_PHYSICS_KEYS
    keys: Set[str] = set(DEFAULT_PHYSICS_SETTINGS.keys())
    for row in list_base_physics_skills():
        if not isinstance(row, dict):
            continue
        k = str(row.get("physics_setting_key") or "").strip()
        if k:
            keys.add(k)
    _ALLOWED_PHYSICS_KEYS = keys
    return keys


def _default_registry_path() -> Path:
    raw = os.environ.get("QIAZHI_DNA_REGISTRY_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parents[3] / "data" / "dna_registry.json"


def _admission_file_path() -> Path:
    raw = os.environ.get("QIAZHI_EVOLUTION_ADMISSION_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parents[3] / "data" / "evolution_admission.json"


def is_evolution_admitted_to_mainnet() -> bool:
    """裁决人「演化准入」：为真时才将 DNA 覆盖并入 L1/L2 物理主网。"""
    env = os.environ.get("QIAZHI_EVOLUTION_ADMIT", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    if env in ("0", "false", "no", "off"):
        return False
    p = _admission_file_path()
    if not p.is_file():
        return False
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(raw, dict):
        return False
    return bool(raw.get("admit_evolved_to_mainnet"))


def set_evolution_admission(admit: bool, path: Optional[Path] = None) -> Path:
    p = path or _admission_file_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "admit_evolved_to_mainnet": bool(admit)}
    with _lock:
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


@dataclass
class RuleGene:
    skill_id: str
    evolved_parameters: Dict[str, float] = field(default_factory=dict)
    fitness_score: float = 0.0
    generation_id: int = 0
    # 兼容旧版 JSON / 文档字段
    current_weight: float = 0.0

    def to_json(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> Optional["RuleGene"]:
        try:
            skill_id = str(row.get("skill_id") or "").strip()
            if not skill_id:
                return None
            ep_raw = row.get("evolved_parameters")
            evolved_parameters: Dict[str, float] = {}
            if isinstance(ep_raw, dict):
                for k, v in ep_raw.items():
                    try:
                        evolved_parameters[str(k)] = float(v)
                    except (TypeError, ValueError):
                        continue
            fitness = float(row.get("fitness_score", row.get("confidence_score", 0.0)))
            generation_id = int(row.get("generation_id", 0))
            current_weight = float(row.get("current_weight", 0.0))
            gene = RuleGene(
                skill_id=skill_id,
                evolved_parameters=evolved_parameters,
                fitness_score=fitness,
                generation_id=generation_id,
                current_weight=current_weight,
            )
            if not gene.evolved_parameters and row.get("evolved_weight") is not None:
                pk = _skill_id_to_physics_key().get(skill_id)
                if pk:
                    gene.evolved_parameters[pk] = float(row["evolved_weight"])
            return gene
        except (TypeError, ValueError):
            return None


def _skill_id_to_physics_key() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in list_base_physics_skills():
        if not isinstance(row, dict):
            continue
        sid = str(row.get("id") or "").strip()
        key = str(row.get("physics_setting_key") or "").strip()
        if sid and key:
            out[sid] = key
    return out


def _operator_skill_ids() -> frozenset[str]:
    manifest = load_base_physics_skill_manifest()
    m = manifest.get("operator_to_skill") if isinstance(manifest, dict) else None
    if not isinstance(m, dict):
        return frozenset()
    return frozenset(str(v) for v in m.values() if v)


def load_rule_genes(path: Optional[Path] = None) -> List[RuleGene]:
    p = path or _default_registry_path()
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = raw.get("genes") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return []
    genes: List[RuleGene] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        g = RuleGene.from_dict(item)
        if g:
            genes.append(g)
    return genes


def save_rule_genes(genes: List[RuleGene], path: Optional[Path] = None) -> Path:
    p = path or _default_registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 2, "genes": [g.to_json() for g in genes]}
    with _lock:
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def upsert_rule_gene(gene: RuleGene, path: Optional[Path] = None) -> Path:
    p = path or _default_registry_path()
    existing = {g.skill_id: g for g in load_rule_genes(p)}
    existing[gene.skill_id] = gene
    return save_rule_genes(list(existing.values()), p)


def apply_dna_overlay(settings: Dict[str, float]) -> Dict[str, float]:
    """
    DnaOverlay：在已 resolve 的 physics_settings 上叠演化参数。

    - 未准入主网：原样返回。
    - 仅处理 operator_to_skill 中的 L1 skill_id；fitness_score 低于阈值跳过。
    - 仅写入白名单物理键（DEFAULT + skill_manifest 声明键）。
    """
    out = dict(settings)
    if not is_evolution_admitted_to_mainnet():
        return out
    allowed = _allowed_physics_keys()
    op_skills = _operator_skill_ids()
    for gene in load_rule_genes():
        if gene.skill_id not in op_skills:
            continue
        if gene.fitness_score < _MIN_FITNESS_FOR_OVERLAY:
            continue
        for pkey, val in gene.evolved_parameters.items():
            pk = str(pkey).strip()
            if not pk or pk not in allowed:
                continue
            out[pk] = float(val)
    return out


def merge_evolved_physics_from_dna(settings: Dict[str, float]) -> Dict[str, float]:
    """兼容旧名：等同 `apply_dna_overlay`。"""
    return apply_dna_overlay(settings)


def gene_maturity_heatmap(genes: Optional[List[RuleGene]] = None) -> List[Dict[str, Any]]:
    """供仪表盘：粗粒度「基因剧烈程度」= 参数条目数 × fitness × 代际因子。"""
    rows: List[Dict[str, Any]] = []
    for g in genes or load_rule_genes():
        n = max(1, len(g.evolved_parameters))
        gen_boost = 1.0 + 0.07 * max(0, int(g.generation_id))
        raw = min(1.5, float(g.fitness_score) * n * 0.15 * gen_boost)
        rows.append(
            {
                "skill_id": g.skill_id,
                "maturity": round(min(1.0, raw), 4),
                "fitness_score": round(float(g.fitness_score), 4),
                "generation_id": int(g.generation_id),
                "parameter_count": len(g.evolved_parameters),
            }
        )
    rows.sort(key=lambda x: -float(x["maturity"]))
    return rows


def append_routing_audit_item(physics_tensor: MutableMapping[str, Any], routing_package: Dict[str, Any]) -> None:
    """
    因果脉冲：在 audit_items 语义下追加路由决策，供进化引擎与排障阅读。

    写入 `physics_tensor.audit_log.causal_routing_audit_items[]`，每条含 `routing_decision` 长文案；
    同包写入 `meta.causal_routing` 供 LLM 侧读取主权排序。
    """
    audit = physics_tensor.setdefault("audit_log", {})
    if not isinstance(audit, MutableMapping):
        return
    items = list(audit.get("causal_routing_audit_items") or [])
    rd = str(routing_package.get("routing_decision") or "").strip()[:900]
    merged = routing_package.get("merged_impact") if isinstance(routing_package.get("merged_impact"), dict) else {}
    head = dict(list(merged.items())[:10]) if merged else {}
    items.append(
        {
            "id": f"causal-routing-{len(items) + 1}",
            "role": "CausalRouter",
            "routing_decision": rd,
            "strategy_applied": routing_package.get("strategy_applied"),
            "conflict_event_count": len(routing_package.get("conflict_events") or []),
            "merged_impact_preview": head,
        }
    )
    audit["causal_routing_audit_items"] = items
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["causal_routing"] = routing_package
