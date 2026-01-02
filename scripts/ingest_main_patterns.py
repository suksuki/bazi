"""
主格局全量注入脚本 (Main Pattern Full Ingestion)
===============================================
将所有已拟合格局的流形特征和语义公理注入知识库：
1. 物理层：流形特征 (mean_vector, covariance) 存入 singularity_vault
2. 语义层：格局公理 (古典逻辑) 存入 semantic_vault

使用方法:
    source venv/bin/activate && python scripts/ingest_main_patterns.py
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.vault_manager import VaultManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 主格局语义公理定义
# 这些是基于古典命理学的物理逻辑，用于吻合度审计
PATTERN_AXIOMS = {
    "B-01": {
        "display_name": "食神格",
        "english_name": "Eating God",
        "category": "OUTPUT",
        "classical_logic": """
食神格物理公理 (B-01):

【核心定义】
食神者，日主所生之物，泄秀之神也。食神格成立需：
- 月令透食神或藏食神
- 食神有财星引化（食神生财）

【五维物理映射】
- E (能量): 食神泄身，E轴需有适度消耗
- O (秩序): 食神与七杀相克，若见杀则需制
- M (财富): 食神生财，M轴与Output正相关
- S (应力): 枭神夺食为忌，S轴受枭印负面影响
- R (关联): 食神主温和，R轴偏中性

【成格条件】
1. 食神有力：月令食神透出或得地
2. 财星引化：食神生财，财星有力
3. 无枭神夺食：忌见偏印夺食

【破格条件】
1. 枭神夺食：偏印透干克制食神
2. 比劫争财：身旺比劫夺财
3. 官杀混杂：七杀无制反克日主
""",
        "physical_rules": [
            {"rule": "食神生财", "axis": "M", "effect": "positive", "condition": "shi_shen > 0.3 AND zheng_cai > 0.2"},
            {"rule": "枭神夺食", "axis": "S", "effect": "negative", "condition": "pian_yin > 0.4"},
            {"rule": "食神泄秀", "axis": "E", "effect": "drain", "condition": "shi_shen > 0.4"},
        ]
    },
    
    "A-03": {
        "display_name": "羊刃格",
        "english_name": "Yang Ren Jia Sha",
        "category": "POWER",
        "classical_logic": """
羊刃格物理公理 (A-03):

【核心定义】
羊刃者，日主之极旺刃锋也。羊刃架杀成立需：
- 日主身旺有刃
- 七杀透出制刃

【五维物理映射】
- E (能量): 极高，羊刃为日主之刃锋
- O (秩序): 七杀制刃，权力与控制
- M (财富): 较低，能量流向权力而非财富
- S (应力): 中高，内部压力但结构完整
- R (关联): 中等，取决于七杀控制程度

【成格条件】
1. 身旺有刃：日主坐刃或刃临旺地
2. 七杀有力：七杀透干制刃
3. 刃杀两停：刃与杀力量均衡

【破格条件】
1. 杀轻刃重：七杀无力制刃
2. 印化杀弱：印星化杀泄刃之力
3. 刃逢冲破：羊刃被冲或被合
""",
        "physical_rules": [
            {"rule": "刃杀两停", "axis": "E", "effect": "balanced", "condition": "parallel > 0.5 AND power > 0.4"},
            {"rule": "杀轻刃重", "axis": "S", "effect": "stress", "condition": "parallel > 0.6 AND power < 0.3"},
            {"rule": "七杀制刃", "axis": "O", "effect": "positive", "condition": "qi_sha > 0.4"},
        ]
    },
    
    "D-02": {
        "display_name": "偏财格",
        "english_name": "Indirect Wealth",
        "category": "WEALTH",
        "classical_logic": """
偏财格物理公理 (D-02):

【核心定义】
偏财者，日主所克之外财也。偏财格成立需：
- 月令透偏财或藏偏财
- 日主有力能任财

【五维物理映射】
- E (能量): 中等，需有力任财
- O (秩序): 偏财喜官护财
- M (财富): 极高，偏财主大财横财
- S (应力): 比劫争财为忌
- R (关联): 偏财主人缘，R轴较高

【成格条件】
1. 偏财有力：月令偏财透出
2. 日主能任：身强能任财
3. 官星护财：有官星制比劫

【破格条件】
1. 比劫争财：身旺比劫夺财
2. 财多身弱：财旺身弱难任
3. 枭神夺财：偏印夺食破财
""",
        "physical_rules": [
            {"rule": "财旺身强", "axis": "M", "effect": "positive", "condition": "wealth > 0.4 AND parallel > 0.3"},
            {"rule": "比劫争财", "axis": "S", "effect": "negative", "condition": "bi_jian > 0.4 OR jie_cai > 0.4"},
            {"rule": "官星护财", "axis": "O", "effect": "positive", "condition": "zheng_guan > 0.3"},
        ]
    },
    
    "A-01": {
        "display_name": "正官格",
        "english_name": "Direct Officer",
        "category": "POWER",
        "classical_logic": """
正官格物理公理 (A-01):

【核心定义】
正官者，克我而正者也。正官格成立需：
- 月令透正官或藏正官
- 正官清纯无杂

【五维物理映射】
- E (能量): 官星克日主，E轴受约束
- O (秩序): 极高，正官主权威秩序
- M (财富): 财生官，M轴与O轴联动
- S (应力): 官杀混杂为忌
- R (关联): 正官主名誉，R轴中上

【成格条件】
1. 正官清纯：月令正官，无七杀混杂
2. 印星护官：有印化杀护官
3. 财星生官：财旺生官有力

【破格条件】
1. 官杀混杂：七杀与正官同透
2. 伤官见官：伤官透干克官
3. 刑冲破害：正官被刑冲
""",
        "physical_rules": [
            {"rule": "官清印护", "axis": "O", "effect": "positive", "condition": "zheng_guan > 0.4 AND zheng_yin > 0.2"},
            {"rule": "财生官", "axis": "O", "effect": "positive", "condition": "zheng_cai > 0.3 AND zheng_guan > 0.3"},
            {"rule": "伤官见官", "axis": "S", "effect": "negative", "condition": "shang_guan > 0.4 AND zheng_guan > 0.3"},
        ]
    },
    
    "D-01": {
        "display_name": "正财格",
        "english_name": "Direct Wealth",
        "category": "WEALTH",
        "classical_logic": """
正财格物理公理 (D-01):

【核心定义】
正财者，日主所克而正者也。正财格成立需：
- 月令透正财或藏正财
- 日主有力能任财

【五维物理映射】
- E (能量): 中等，需有力任财
- O (秩序): 财生官，O轴受财影响
- M (财富): 高，正财主稳定财源
- S (应力): 比劫争财为忌
- R (关联): 正财主正缘，R轴稳定

【成格条件】
1. 正财有力：月令正财透出
2. 日主能任：身强能任财
3. 食伤生财：有食伤引化

【破格条件】
1. 比劫争财：身旺比劫夺财
2. 财多身弱：财旺身弱难任
3. 劫财夺位：劫财透干
""",
        "physical_rules": [
            {"rule": "财旺身强", "axis": "M", "effect": "positive", "condition": "zheng_cai > 0.4 AND parallel > 0.3"},
            {"rule": "食伤生财", "axis": "M", "effect": "positive", "condition": "shi_shen > 0.3 AND zheng_cai > 0.3"},
            {"rule": "比劫争财", "axis": "S", "effect": "negative", "condition": "bi_jian > 0.5"},
        ]
    },
}


def load_registry_patterns() -> Dict[str, Any]:
    """从 registry.json 加载格局配置"""
    registry_path = Path(__file__).parent.parent / "core" / "subjects" / "holographic_pattern" / "registry.json"
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    return registry.get("patterns", {})


def ingest_pattern_axioms(vault: VaultManager) -> Dict[str, int]:
    """注入格局语义公理到语义库"""
    stats = {"success": 0, "error": 0}
    
    for pattern_id, axiom_data in PATTERN_AXIOMS.items():
        try:
            # 构建语义内容
            content = f"""
# {axiom_data['display_name']} ({axiom_data['english_name']})
格局ID: {pattern_id}
类别: {axiom_data['category']}

{axiom_data['classical_logic']}
"""
            
            # 注入语义库
            vault.add_specification(
                step_name=f"AXIOM_{pattern_id}",
                content=content,
                metadata={
                    "type": "pattern_axiom",
                    "pattern_id": pattern_id,
                    "category": axiom_data["category"],
                    "display_name": axiom_data["display_name"]
                }
            )
            
            stats["success"] += 1
            logger.info(f"✅ 语义公理注入: {pattern_id} ({axiom_data['display_name']})")
            
        except Exception as e:
            stats["error"] += 1
            logger.error(f"❌ 语义公理注入失败 ({pattern_id}): {e}")
    
    return stats


def ingest_pattern_manifolds(vault: VaultManager, registry_patterns: Dict) -> Dict[str, int]:
    """注入格局流形特征到物理库"""
    stats = {"success": 0, "error": 0}
    
    for pattern_id, pattern_data in registry_patterns.items():
        try:
            # 提取 feature_anchors
            feature_anchors = pattern_data.get("feature_anchors", {})
            standard_manifold = feature_anchors.get("standard_manifold", {})
            
            # 获取均值向量
            mean_vector = standard_manifold.get("mean_vector", {})
            if not mean_vector:
                # 尝试从子格局获取
                subs = pattern_data.get("sub_patterns_registry", []) or pattern_data.get("sub_patterns", [])
                for sub in subs:
                    if "STANDARD" in sub.get("id", "").upper():
                        manifold_data = sub.get("manifold_data", {}) or sub.get("manifold_stats", {})
                        mean_vector = manifold_data.get("mean_vector", {})
                        break
            
            if not mean_vector:
                logger.warning(f"⚠️ {pattern_id} 无均值向量，跳过")
                continue
            
            # 转换为 5D 张量
            tensor_5d = [
                mean_vector.get("E", 0.2),
                mean_vector.get("O", 0.2),
                mean_vector.get("M", 0.2),
                mean_vector.get("S", 0.2),
                mean_vector.get("R", 0.2)
            ]
            
            # 获取丰度和描述
            meta_info = pattern_data.get("meta_info", {})
            abundance = standard_manifold.get("abundance", 0.0)
            
            # 构建元数据
            metadata = {
                "pattern_id": pattern_id,
                "type": "main_pattern_manifold",
                "display_name": meta_info.get("display_name", pattern_id),
                "category": pattern_data.get("category", "UNKNOWN"),
                "abundance": abundance,
                "is_standard": True,
                "description": f"主格局流形中心: {pattern_id}"
            }
            
            # 注入物理库 (使用特殊 ID 前缀区分主格局)
            case_id = f"MANIFOLD_{pattern_id}"
            vault.add_singularity(
                case_id=case_id,
                tensor_5d=tensor_5d,
                metadata=metadata
            )
            
            stats["success"] += 1
            logger.info(f"✅ 流形特征注入: {pattern_id} -> {tensor_5d}")
            
        except Exception as e:
            stats["error"] += 1
            logger.error(f"❌ 流形特征注入失败 ({pattern_id}): {e}")
    
    return stats


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("📜 主格局全量注入开始")
    logger.info("=" * 60)
    
    # 1. 初始化 VaultManager
    try:
        vault = VaultManager()
        logger.info(f"✅ VaultManager 初始化成功")
        logger.info(f"   当前语义库文档数: {vault.semantic_vault.count()}")
        logger.info(f"   当前奇点库样本数: {vault.singularity_vault.count()}")
    except Exception as e:
        logger.error(f"❌ VaultManager 初始化失败: {e}")
        return
    
    # 2. 注入语义公理
    logger.info("\n📚 Phase 1: 注入格局语义公理...")
    axiom_stats = ingest_pattern_axioms(vault)
    logger.info(f"   成功: {axiom_stats['success']}, 失败: {axiom_stats['error']}")
    
    # 3. 加载 registry 并注入流形特征
    logger.info("\n⚛️ Phase 2: 注入格局流形特征...")
    registry_patterns = load_registry_patterns()
    manifold_stats = ingest_pattern_manifolds(vault, registry_patterns)
    logger.info(f"   成功: {manifold_stats['success']}, 失败: {manifold_stats['error']}")
    
    # 4. 验证
    final_stats = vault.get_vault_stats()
    logger.info(f"\n📊 最终知识库状态:")
    logger.info(f"   语义库文档数: {final_stats['semantic_count']}")
    logger.info(f"   奇点库样本数: {final_stats['singularity_count']}")
    
    # 5. 测试语义检索
    logger.info("\n🧪 测试语义检索...")
    test_queries = [
        "食神格成格条件",
        "羊刃格物理公理",
        "偏财格破格条件"
    ]
    
    for query in test_queries:
        results = vault.query_semantics(query, n_results=1)
        if results["ids"]:
            logger.info(f"   '{query}' -> {results['ids'][0]}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 主格局全量注入完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
