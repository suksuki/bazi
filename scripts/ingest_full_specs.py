"""
FDS-LKV 完整规范注入脚本
========================
执行首批规范文档的完整注入，建立合规性拦截器基准。

使用方法:
    source venv/bin/activate && python scripts/ingest_full_specs.py
"""

import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.vault_manager import VaultManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """主函数：执行完整规范注入"""
    logger.info("=" * 60)
    logger.info("📜 FDS-LKV 完整规范注入开始")
    logger.info("=" * 60)
    
    # 初始化 VaultManager
    try:
        vault = VaultManager()
        logger.info(f"✅ VaultManager 初始化成功")
    except Exception as e:
        logger.error(f"❌ VaultManager 初始化失败: {e}")
        return
    
    # 定义要注入的规范文档
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    
    specs_to_ingest = [
        {
            "file": "FDS_MODELING_SPEC_v3.0.md",
            "version": "3.0",
            "type": "modeling_spec"
        },
        {
            "file": "FDS_LKV_SPEC.md",
            "version": "1.0",
            "type": "lkv_spec"
        }
    ]
    
    total_stats = {"total": 0, "injected": 0, "updated": 0, "errors": 0}
    
    for spec in specs_to_ingest:
        file_path = os.path.join(docs_dir, spec["file"])
        
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ 规范文档不存在，跳过: {spec['file']}")
            continue
        
        logger.info(f"\n📄 注入规范: {spec['file']}")
        
        try:
            stats = vault.auto_ingest_protocol(
                file_path=file_path,
                version=spec["version"],
                doc_type=spec["type"]
            )
            
            # 累加统计
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
                
        except Exception as e:
            logger.error(f"❌ 注入失败: {e}")
            total_stats["errors"] += 1
    
    # 汇总统计
    logger.info("\n" + "=" * 60)
    logger.info("📊 注入汇总统计")
    logger.info("=" * 60)
    logger.info(f"   - 总分片数: {total_stats['total']}")
    logger.info(f"   - 新增: {total_stats['injected']}")
    logger.info(f"   - 更新: {total_stats['updated']}")
    logger.info(f"   - 错误: {total_stats['errors']}")
    
    # 显示当前知识库状态
    stats = vault.get_vault_stats()
    logger.info(f"\n📚 当前知识库状态:")
    logger.info(f"   - 语义库文档数: {stats['semantic_count']}")
    logger.info(f"   - 奇点库样本数: {stats['singularity_count']}")
    
    # 测试合规性检查
    logger.info("\n🧪 测试合规性检查...")
    test_config = {
        "pattern_id": "A-03",
        "weight_matrix": {"E": 0.5, "O": 0.3, "M": -0.2, "S": 0.4, "R": 0.1},
        "gating": {"weak_self_limit": 0.45}
    }
    
    result = vault.check_physics_compliance(test_config)
    logger.info(f"   - 合规状态: {'✅ 通过' if result['compliant'] else '❌ 违规'}")
    logger.info(f"   - 匹配公理: {len(result['matched_axioms'])} 条")
    
    if result['recommendations']:
        logger.info(f"   - 建议: {result['recommendations']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 完整规范注入完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
