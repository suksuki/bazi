
import os
import sys
import json
import logging
from datetime import datetime

# 加载项目路径
project_root = "/home/jin/bazi_predict"
sys.path.append(project_root)

from core.trinity.core.engines.pattern_scout import PatternScout
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.logic_registry import LogicRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Testing_V4.2.6")

def run_automated_audit():
    logger.info("🧪 [V4.2.6] 全平台自动化审计开始...")
    
    scout = PatternScout()
    engine = SyntheticBaziEngine()
    registry = LogicRegistry()
    
    # 模拟生成 500 个样本
    sample_size = 500
    bazi_gen = engine.generate_all_bazi()
    samples = [next(bazi_gen) for _ in range(sample_size)]
    
    # 获取所有注册的物理模型 (MOD_101 - MOD_114)
    active_mods = registry.get_logic_routing().keys()
    
    results_summary = {}
    
    for mod_prefix in active_mods:
        logger.info(f"🛰️ 正在扫描 ID: {mod_prefix} ...")
        captures = 0
        samples_scanned = 0
        
        # 验证 Registry ID 解析
        full_reg_id, logic_list = registry.resolve_logic_id(mod_prefix)
        
        for chart in samples:
            # 执行审计
            res = scout._deep_audit(chart, mod_prefix)
            if res:
                captures += 1
                # 随机抽取一个样本检查注入字段
                if captures == 1:
                    if "registry_id" not in res or "logic_version" not in res:
                        logger.error(f"❌ {mod_prefix} 缺少元数据注入!")
                    else:
                        logger.info(f"✅ {mod_prefix} 元数据注入校验通过: {res['registry_id']} | V{res['logic_version']}")

            samples_scanned += 1
            
        rate = (captures / samples_scanned) * 100
        results_summary[mod_prefix] = {
            "captures": captures,
            "rate": f"{rate:.2f}%",
            "status": "✅ PASS" if captures > 0 else "❌ ZERO_CAPTURE"
        }

    # 打印最终报告
    print("\n" + "="*50)
    print("📋 [V4.2.6] 自动化审计最终报告")
    print("="*50)
    print(f"{'MOD_ID':<15} | {'捕获率':<10} | {'状态'}")
    print("-" * 50)
    for mod, data in results_summary.items():
        print(f"{mod:<15} | {data['rate']:<10} | {data['status']}")
    print("="*50)

    # 验证关键修复
    critical_mods = ["MOD_109", "MOD_107", "MOD_110"]
    for cm in critical_mods:
        if results_summary[cm]["captures"] == 0:
            logger.error(f"🚨 警告: 关键修复模型 {cm} 仍存在零捕获!")
        else:
            logger.info(f"✨ 关键修复确认: {cm} 已恢复生命力 (Rate: {results_summary[cm]['rate']})")

if __name__ == "__main__":
    run_automated_audit()
