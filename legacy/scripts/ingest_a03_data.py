"""
A-03 (羊刃架杀) 数据注入脚本
============================
将 FDS v3.0 规范内容和 A-03 样本数据注入到 FDS-Knowledge-Vault

使用方法:
    source venv/bin/activate && python scripts/ingest_a03_data.py
"""

import os
import sys
import json
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.vault_manager import VaultManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_fds_spec_content():
    """
    从 FDS_MODELING_SPEC_v3.0.md 提取关键规范内容
    按 Step 分割
    """
    spec_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "docs", "FDS_MODELING_SPEC_v3.0.md"
    )
    
    if not os.path.exists(spec_path):
        logger.error(f"❌ 规范文档不存在: {spec_path}")
        return {}
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取关键章节内容
    specs = {}
    
    # Step 2: 样本分层与海选
    step2_content = """
    Step 2: 样本分层与海选 (Census & Stratification)
    
    1. L1 逻辑普查 (Classical Census)：[强制执行]
       - 记录格局在 518,400 样本库中的绝对命中数 N_hit
       - 算法：古典海选丰度 = N_hit / 518,400 × 100%
       - 此丰度值作为 Step 6 调校的法定参考值 (Ground Truth)
    
    2. L2 交叉验证：匹配样本的人生轨迹真值 y_true
    
    3. L3 提纯 (Tier A)：锁定 500+ 例黄金种子样本
    """
    specs["Step_2_Census"] = step2_content.strip()
    
    # Step 5: 全息封卷与协议植入
    step5_content = """
    Step 5: 全息封卷与协议植入 (Assembly & Protocols) [CRITICAL]
    
    1. 安全门控植入 (Safety Gate Injection)：[强制执行]
       - 身旺门控 (E-Gating)：强制植入 @config.gating.weak_self_limit
       - 排他门控 (R-Gating)：强制植入 @config.gating.max_relation
    
    2. 元数据标准化 (Metadata)：
       - category：必须枚举为 WEALTH, POWER, TALENT, SELF
       - display_name：英文索引名
       - chinese_name：中文展示名
    
    3. 奇点样本存证 (Singularity Benchmarking)：[强制执行]
       - 奇点判定：马氏距离 D_M >> threshold，且样本数量 N < min_samples
       - 存证内容：5D 特征张量 [E, O, M, S, R] 和样本唯一标识符 Case_ID
    """
    specs["Step_5_Assembly"] = step5_content.strip()
    
    # 五维张量定义
    tensor_def = """
    五维命运张量定义 (T_fate):
    
    | 维度轴 | 物理定义 | 命理意象 |
    |--------|----------|----------|
    | E (Energy) | 能级/振幅 | 生命力、抗压阈值、根基深浅 |
    | O (Order) | 熵减/有序度 | 权力、社会阶层、管理能力 |
    | M (Material) | 物质/做功 | 财富总量、资产控制力 |
    | S (Stress) | 应力/剪切力 | 风险、灾难、内耗、突发意外 |
    | R (Relation) | 纠缠/相干性 | 情感连接、人际网络、六亲缘分 |
    """
    specs["Tensor_Definition"] = tensor_def.strip()
    
    # A-03 羊刃架杀格特定规范
    a03_spec = """
    A-03 羊刃架杀格 (Yang Ren Jia Sha):
    
    物理定义：受控核聚变状态 - 高能等离子体（羊刃）被强磁场（七杀）完美约束
    
    典型特征：
    - E (Energy) 极高：强大的生命力和抗压底气
    - O (Order) 高：权力和社会地位
    - M (Material) 低：重名轻利，能量流向权力而非财富
    - S (Stress) 中高：内部压力大，但因结构完整对外表现稳定
    - R (Relation) 中等：人际关系取决于七杀的控制程度
    
    子格局：
    - SP_A03_ALLIANCE (联盟型)：E >= 0.6, S >= 0.5, R >= 0.5
    - SP_A03_STANDARD (标准型)：E >= 0.6, S >= 0.5, O <= 0.35
    """
    specs["A03_Specification"] = a03_spec.strip()
    
    return specs


def get_a03_sample_data():
    """
    获取 A-03 羊刃架杀格的示例奇点数据
    基于 FDS v3.0 规范中的 benchmarks 格式
    """
    # 示例奇点样本（基于规范中的参考值）
    samples = [
        {
            "case_id": "A03_BENCHMARK_001",
            "tensor": [0.72, 0.18, 0.05, 0.85, 0.12],  # E, O, M, S, R
            "metadata": {
                "pattern_id": "A-03",
                "sub_pattern": "SP_A03_STANDARD",
                "distance_to_manifold": 3.45,
                "abundance": 0.00543,
                "description": "高能量、极高剪切力的标准型羊刃架杀"
            }
        },
        {
            "case_id": "A03_BENCHMARK_002",
            "tensor": [0.68, 0.22, 0.08, 0.78, 0.15],
            "metadata": {
                "pattern_id": "A-03",
                "sub_pattern": "SP_A03_STANDARD",
                "distance_to_manifold": 3.12,
                "abundance": 0.00421,
                "description": "中高能量、高剪切力的标准型"
            }
        },
        {
            "case_id": "A03_BENCHMARK_003",
            "tensor": [0.65, 0.25, 0.10, 0.55, 0.52],
            "metadata": {
                "pattern_id": "A-03",
                "sub_pattern": "SP_A03_ALLIANCE",
                "distance_to_manifold": 2.85,
                "abundance": 0.00312,
                "description": "联盟型羊刃架杀，R轴较高"
            }
        }
    ]
    
    return samples


def main():
    """主函数：执行数据注入"""
    logger.info("=" * 60)
    logger.info("🚀 FDS-Knowledge-Vault 数据注入开始")
    logger.info("=" * 60)
    
    # 初始化 VaultManager
    try:
        vault = VaultManager()
        logger.info(f"✅ VaultManager 初始化成功")
    except Exception as e:
        logger.error(f"❌ VaultManager 初始化失败: {e}")
        return
    
    # ========== Phase 1: 注入规范文档到语义库 ==========
    logger.info("\n📚 Phase 1: 注入规范文档到语义库...")
    
    specs = extract_fds_spec_content()
    for step_name, content in specs.items():
        try:
            vault.add_specification(step_name, content)
            logger.info(f"   ✓ {step_name} 注入成功")
        except Exception as e:
            logger.error(f"   ✗ {step_name} 注入失败: {e}")
    
    # ========== Phase 2: 注入奇点样本到奇点库 ==========
    logger.info("\n⚛️ Phase 2: 注入奇点样本到奇点库...")
    
    samples = get_a03_sample_data()
    for sample in samples:
        try:
            vault.add_singularity(
                case_id=sample["case_id"],
                tensor_5d=sample["tensor"],
                metadata=sample["metadata"]
            )
            logger.info(f"   ✓ {sample['case_id']} 注入成功")
        except Exception as e:
            logger.error(f"   ✗ {sample['case_id']} 注入失败: {e}")
    
    # ========== 验证 ==========
    logger.info("\n🔍 验证注入结果...")
    stats = vault.get_vault_stats()
    logger.info(f"   - 语义库文档数: {stats['semantic_count']}")
    logger.info(f"   - 奇点库样本数: {stats['singularity_count']}")
    
    # 测试奇点检索
    logger.info("\n🧪 测试奇点检索...")
    test_tensor = [0.70, 0.20, 0.06, 0.80, 0.13]  # 类似 BENCHMARK_001
    results = vault.query_singularities(test_tensor, n_results=2)
    logger.info(f"   - 查询张量: {test_tensor}")
    logger.info(f"   - 最近邻: {results['ids']}")
    logger.info(f"   - 距离: {[f'{d:.4f}' for d in results['distances']]}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 数据注入完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
