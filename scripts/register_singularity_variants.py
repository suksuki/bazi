#!/usr/bin/env python3
"""
注册奇点变体为独立子格局
将 [A-03-X1] 和 [A-03-X2] 注册为独立的子格局条目
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

def register_singularity_variants():
    """注册奇点变体为独立子格局"""
    
    registry_file = project_root / "core" / "subjects" / "holographic_pattern" / "registry.json"
    
    with open(registry_file, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # 注册 [A-03-X1] 聚变临界型
    variant_x1 = {
        "id": "A-03-X1",
        "name": "羊刃聚变临界型",
        "name_cn": "羊刃聚变临界型",
        "name_en": "Fusion Critical State",
        "category": "A",
        "subject_id": "A-03-X1",
        "parent_pattern": "A-03",
        "icon": "⚛️",
        "version": "1.0",
        "active": True,
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "description": "托卡马克装置模型 - 能量极度溢出，如同被磁场约束的高温等离子体。稍有不慎即发生热核爆炸（暴亡），若能导出则为无限能源（极贵）",
        "semantic_seed": {
            "description": "地支三刃以上，能量极度溢出态。这不是普通的强，这是'切尔诺贝利反应堆'。普通的平衡算法对它们无效，它们需要专门的'防爆公式'。",
            "physical_image": "托卡马克装置 (Tokamak Plasma) - 能量极度溢出，如同被磁场约束的高温等离子体",
            "source": "ai_analyst_gemini",
            "updated_at": datetime.now().strftime('%Y-%m-%d'),
            "classical_meaning": {
                "三刃": "能量极度溢出，极易暴亡或大贵",
                "聚变临界": "反应堆过热，需要专门的冷却机制"
            }
        },
        "tensor_operator": {
            "weights": {
                "E": 0.50,
                "O": 0.10,
                "M": 0.05,
                "S": 0.30,
                "R": 0.05
            },
            "weight_description": {
                "E": "能级轴：0.50 - 爆表。生命能量极大，甚至表现为多动、狂躁、破坏欲",
                "O": "秩序轴：0.10 - 极难建立秩序，除非有极强的'宣泄口'",
                "M": "物质轴：0.05 - 视金钱如粪土，或极度挥霍",
                "S": "应力轴：0.30 - 极不稳定。自身就是不稳定的能量源",
                "R": "关联轴：0.05 - 对六亲有极强的辐射伤害"
            },
            "activation_function": {
                "type": "critical_explosion",
                "description": "聚变临界判定：当能量密度突破临界值时，发生自发性爆炸",
                "parameters": {
                    "critical_threshold": 0.95,
                    "explosion_trigger": "合刃（如地支三合局）"
                }
            },
            "normalized": True,
            "core_equation": "E_critical = E_blade_count * 3.0",
            "equation_description": "三刃能量 = 单刃能量 × 3.0，能量密度突破临界值"
        },
        "kinetic_evolution": {
            "trigger_operators": [
                {
                    "type": "combination",
                    "description": "合刃（如地支三合局）：三刃再逢合，能量密度突破临界值 → 自发性爆炸（心脏、血液、猝死）",
                    "example": "地支三午（羊刃），再逢未（午未合）"
                }
            ],
            "gain_operators": [
                {
                    "type": "discharge",
                    "description": "食伤泄能：反应堆过热时，打开冷却塔（食伤）进行能量排放"
                }
            ],
            "geo_damping": 0.8,
            "dynamic_simulation": {
                "scenario": "聚变临界事件 (Fusion Critical Event)",
                "description": "能量极度溢出，需要专门的泄能机制。不喜印（生），最喜食伤（泄）"
            },
            "favorable_gods": {
                "喜": "食伤（泄能，打开冷却塔）",
                "忌": "印星（生刃，相当于加燃料，会导致爆炸）"
            }
        },
        "audit_trail": {
            "coverage_rate": 0.0,
            "hit_rate": 0.0,
            "sai_baseline": 0.0,
            "sai_description": "待拟合",
            "data_selection_criteria": {
                "singularity_criteria": "地支羊刃数量 >= 3",
                "sample_count": 25,
                "source": "Tier X奇点集"
            },
            "version_history": [
                {
                    "version": "1.0",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "source": "ai_analyst_gemini",
                    "description": "从A-03奇点集中提取并注册为独立子格局",
                    "parent_pattern": "A-03"
                }
            ]
        },
        "singularity_type": "X1-聚变临界型",
        "status": "✅ 已封卷 (Active)",
        "last_updated": datetime.now().strftime('%Y-%m-%d')
    }
    
    # 注册 [A-03-X2] 结构高压型
    variant_x2 = {
        "id": "A-03-X2",
        "name": "结构高压屈服型",
        "name_cn": "结构高压屈服型",
        "name_en": "Structural Yield Stress",
        "category": "A",
        "subject_id": "A-03-X2",
        "parent_pattern": "A-03",
        "icon": "💎",
        "version": "1.0",
        "active": True,
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "description": "液压机下的钻石模型 - 外部约束场（杀）强度远超核心支撑力。系统终身处于'咯吱作响'的金属疲劳状态",
        "semantic_seed": {
            "description": "天干透出2个或以上七杀，且四柱无食神（制）无印星（化）。这不是普通的压力，这是'万米深海潜水艇'。它们的结构一直处于屈服极限（Yield Point）边缘。",
            "physical_image": "液压机下的钻石 (Diamond under Press) - 外部约束场强度远超核心支撑力",
            "source": "ai_analyst_gemini",
            "updated_at": datetime.now().strftime('%Y-%m-%d'),
            "classical_meaning": {
                "众杀": "七杀攻身无制，压力极大",
                "结构高压": "一生处于极高应力下，精神或身体的极限测试"
            }
        },
        "tensor_operator": {
            "weights": {
                "E": 0.10,
                "O": 0.20,
                "M": 0.05,
                "S": 0.60,
                "R": 0.05
            },
            "weight_description": {
                "E": "能级轴：0.10 - 底气极虚，处于透支状态",
                "O": "秩序轴：0.20 - 虽然有权力的可能性，但代价是消耗生命",
                "M": "物质轴：0.05 - 财多则党杀，财是催命符",
                "S": "应力轴：0.60 - 绝对主导。一生都在对抗压力，健康与精神时刻紧绷",
                "R": "关联轴：0.05 - 六亲无靠，孤军奋战"
            },
            "activation_function": {
                "type": "structural_collapse",
                "description": "结构坍塌判定：当外部压力过大且无缓冲时，系统发生结构断裂",
                "parameters": {
                    "yield_point": 0.90,
                    "collapse_trigger": "财流年（财星滋生七杀同时克制印星）"
                }
            },
            "normalized": True,
            "core_equation": "S_yield = E_killings / (E_resource + E_output)",
            "equation_description": "当七杀能量远超印比能量时，系统处于屈服极限边缘"
        },
        "kinetic_evolution": {
            "trigger_operators": [
                {
                    "type": "wealth_year",
                    "description": "财流年：财星滋生七杀（加大压力）同时克制印星（移除缓冲） → 结构坍塌（过劳死、意外、绝症）",
                    "example": "原局众杀攻身无制，流年财星透出"
                }
            ],
            "gain_operators": [
                {
                    "type": "buffer",
                    "description": "印星化杀：引入缓冲液（印星）将压力转化为支撑力"
                }
            ],
            "geo_damping": 0.9,
            "dynamic_simulation": {
                "scenario": "结构高压事件 (Structural Stress Event)",
                "description": "外部压力过大，必须引入缓冲机制。最忌食伤（制），最喜印星（化）"
            },
            "favorable_gods": {
                "喜": "印星（化杀，引入缓冲液）",
                "忌": "食伤（制杀，硬碰硬会导致结构碎裂）、财星（党杀，加大压力）"
            }
        },
        "audit_trail": {
            "coverage_rate": 0.0,
            "hit_rate": 0.0,
            "sai_baseline": 0.0,
            "sai_description": "待拟合",
            "data_selection_criteria": {
                "singularity_criteria": "天干透出2个或以上七杀，且四柱无食神（制）无印星（化）",
                "sample_count": 76,
                "source": "Tier X奇点集"
            },
            "version_history": [
                {
                    "version": "1.0",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "source": "ai_analyst_gemini",
                    "description": "从A-03奇点集中提取并注册为独立子格局",
                    "parent_pattern": "A-03"
                }
            ]
        },
        "singularity_type": "X2-结构高压型",
        "status": "✅ 已封卷 (Active)",
        "last_updated": datetime.now().strftime('%Y-%m-%d')
    }
    
    # 添加到注册表
    registry['patterns']['A-03-X1'] = variant_x1
    registry['patterns']['A-03-X2'] = variant_x2
    
    # 更新元数据
    registry['metadata']['total_patterns'] = len(registry['patterns'])
    
    # 保存注册表
    with open(registry_file, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print("=" * 70)
    print("✅ 奇点变体注册完成")
    print("=" * 70)
    print()
    
    print("【注册的子格局】")
    print("-" * 70)
    print("1. [A-03-X1] 羊刃聚变临界型")
    print("   • 样本数: 25 个")
    print("   • 物理原型: 托卡马克装置 (Tokamak Plasma)")
    print("   • 核心算法: 泄能优先算法（最喜食伤）")
    print()
    
    print("2. [A-03-X2] 结构高压屈服型")
    print("   • 样本数: 76 个")
    print("   • 物理原型: 液压机下的钻石 (Diamond under Press)")
    print("   • 核心算法: 抗压优先算法（最喜印星）")
    print()
    
    print("【算法路由确认】")
    print("-" * 70)
    print("✅ 遇到 [A-03] 标准型 → 使用'平衡算法'")
    print("✅ 遇到 [A-03-X1] → 自动切换到'泄能优先算法'")
    print("✅ 遇到 [A-03-X2] → 自动切换到'抗压优先算法'")
    print()
    
    print("=" * 70)
    print("🎉 奇点变体已正式注册为独立子格局！")
    print("=" * 70)
    print()
    print(f"📄 注册表文件: {registry_file}")
    print()

if __name__ == '__main__':
    register_singularity_variants()

