"""自进化：因果基因库、组合空间扫描；批次 Worker 请从 `worker` 子模块导入。"""

from app.core.evolution.combination_space import TOTAL_BAZI_COMBINATION_SPACE, four_pillars_from_linear_index
from app.core.evolution.dna_registry import (
    RuleGene,
    apply_dna_overlay,
    gene_maturity_heatmap,
    is_evolution_admitted_to_mainnet,
    load_rule_genes,
    merge_evolved_physics_from_dna,
    save_rule_genes,
    set_evolution_admission,
    upsert_rule_gene,
)

__all__ = [
    "TOTAL_BAZI_COMBINATION_SPACE",
    "four_pillars_from_linear_index",
    "RuleGene",
    "load_rule_genes",
    "save_rule_genes",
    "upsert_rule_gene",
    "apply_dna_overlay",
    "merge_evolved_physics_from_dna",
    "is_evolution_admitted_to_mainnet",
    "set_evolution_admission",
    "gene_maturity_heatmap",
]
