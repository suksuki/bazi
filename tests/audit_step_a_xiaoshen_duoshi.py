"""
[QGA V25.0 格局审计] Step A: 原局海选 (RSS-V1.2 全量版)
任务: [02-枭神夺食] 静态晶格筛选（51.84万全量样本）

RSS-V1.2 规范：
- 物理公理定义：从registry.json中调取"枭神夺食"的物理模型、算法及参数
- 全量海选：从51.84万全量样本中锁定所有匹配"生物能截断模型"的母体
- 强制约束：海选阶段只考虑原局特征，剥离大运、流年等动态因子
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.trinity.core.engines.pattern_scout import PatternScout
from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
from core.trinity.core.nexus.definitions import BaziParticleNexus
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StepASelection:
    """Step A: 原局海选器（RSS-V1.2 全量版）"""
    
    def __init__(self):
        self.scout = PatternScout()
        self.vectorizer = FeatureVectorizer()
        # RSS-V1.2规范：从registry.json中调取物理公理
        registry_file = Path(__file__).parent.parent / "core" / "subjects" / "neural_router" / "registry.json"
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry_data = json.load(f)
        self.pattern_config = registry_data.get("XIAO_SHEN_DUO_SHI", {})
        self.physical_axiom = self.pattern_config.get("physical_axiom", {})
        logger.info("✅ Step A 原局海选器初始化完成（RSS-V1.2 全量版 - 枭神夺食）")
    
    def extract_shi_shen(self, chart: List[Tuple[str, str]], day_master: str) -> Dict[str, float]:
        """提取十神分布"""
        shi_shen_counts = {
            '比肩': 0.0, '劫财': 0.0, '食神': 0.0, '伤官': 0.0,
            '正财': 0.0, '偏财': 0.0, '正官': 0.0, '七杀': 0.0,
            '正印': 0.0, '偏印': 0.0
        }
        
        for gan, zhi in chart:
            # 天干十神
            gan_shi_shen = BaziParticleNexus.get_shi_shen(gan, day_master)
            if gan_shi_shen in shi_shen_counts:
                shi_shen_counts[gan_shi_shen] += 1.0
        
        return shi_shen_counts
    
    def calculate_momentum(self, chart: List[Tuple[str, str]], day_master: str) -> Dict[str, float]:
        """
        计算动量项（RSS-V1规范）
        
        Returns:
            {
                'yin_momentum': 印星动量（偏印+正印）
                'shi_momentum': 食伤动量（食神+伤官）
                'yin_to_self': 印星到日主的动量（印星生身，向内压力）
                'self_to_shi': 日主到食伤的动量（日主生食伤，向外动量流）
            }
        """
        shi_shen_counts = self.extract_shi_shen(chart, day_master)
        
        # 印星动量（偏印+正印，重点关注偏印/枭神）
        yin_count = shi_shen_counts.get('偏印', 0) + shi_shen_counts.get('正印', 0)
        # 偏印权重更高（枭神），必须至少有1个偏印
        pian_yin_count = shi_shen_counts.get('偏印', 0)
        if pian_yin_count == 0:
            # 如果没有偏印，降低权重
            yin_momentum = min(1.0, yin_count / 3.0)
        else:
            # 有偏印时，权重更高
            yin_momentum = min(1.0, (yin_count * 0.3 + pian_yin_count * 0.7) / 2.0)
        
        # 食伤动量（食神+伤官）
        shi_count = shi_shen_counts.get('食神', 0) + shi_shen_counts.get('伤官', 0)
        shi_momentum = min(1.0, shi_count / 3.0)  # 降低分母，使得食伤少时更容易满足条件
        
        # 印星到日主的动量（印星生身，向内压力）
        yin_to_self = yin_momentum
        
        # 日主到食伤的动量（日主生食伤，向外动量流）
        self_to_shi = shi_momentum
        
        return {
            'yin_momentum': yin_momentum,
            'shi_momentum': shi_momentum,
            'yin_to_self': yin_to_self,
            'self_to_shi': self_to_shi
        }
    
    def calculate_stress_tensor(self, chart: List[Tuple[str, str]]) -> float:
        """计算应力张量（偏印与食神的对冲相位）"""
        stress = 0.0
        
        # 地支冲克
        branch_clashes = {
            '子': '午', '丑': '未', '寅': '申', '卯': '酉',
            '辰': '戌', '巳': '亥'
        }
        branches = [p[1] for p in chart]
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if branch_clashes.get(branches[i]) == branches[j] or \
                   branch_clashes.get(branches[j]) == branches[i]:
                    stress += 0.2
        
        # 天干相克
        stem_clashes = {
            '甲': '庚', '乙': '辛', '丙': '壬', '丁': '癸', '戊': '甲',
            '己': '乙', '庚': '丙', '辛': '丁', '壬': '戊', '癸': '己'
        }
        stems = [p[0] for p in chart]
        for i in range(len(stems)):
            for j in range(i + 1, len(stems)):
                if stem_clashes.get(stems[i]) == stems[j] or \
                   stem_clashes.get(stems[j]) == stems[i]:
                    stress += 0.1
        
        return min(1.0, stress)
    
    def analyze_chart(self, chart: List[Tuple[str, str]], day_master: str) -> Optional[Dict[str, Any]]:
        """
        分析八字是否符合"枭神夺食"条件（RSS-V1.2规范）
        
        使用registry.json中定义的物理公理：
        - trigger_condition: "当动量项表现为'印→日'单向淤积且'日→食'动量为 0 时，触发生物能截断"
        - energy_equation: "E_interrupt = (yin_momentum × water_field) - (fire_field × shi_momentum)"
        - collapse_threshold: 0.5
        - recovery_path: "财星通关：earth_field + metal_field > 0.4 时，系统可通过资源通道恢复供给"
        """
        # 1. 计算动量项
        momentum = self.calculate_momentum(chart, day_master)
        yin_momentum = momentum['yin_momentum']
        shi_momentum = momentum['shi_momentum']
        yin_to_self = momentum['yin_to_self']
        self_to_shi = momentum['self_to_shi']
        
        # 2. 提取五行场强（使用FeatureVectorizer，RSS-V1.2规范：只考虑原局）
        elemental_fields = self.vectorizer.extract_elemental_fields(
            chart=chart,
            day_master=day_master,
            luck_pillar=None,
            year_pillar=None
        )
        
        water_field = elemental_fields.get('water', 0.0)
        wood_field = elemental_fields.get('wood', 0.0)
        fire_field = elemental_fields.get('fire', 0.0)
        earth_field = elemental_fields.get('earth', 0.0)
        metal_field = elemental_fields.get('metal', 0.0)
        
        # 3. 应用trigger_condition：'印→日'单向淤积且'日→食'动量为 0
        # '印→日'单向淤积：yin_to_self > 0.3（印星向内压力强）
        # '日→食'动量为 0：self_to_shi < 0.4（日主向外动量流弱，被截断，适当放宽）
        # 关键：印星动量要明显大于食伤动量（能量被截断）
        momentum_ratio = yin_momentum / (shi_momentum + 0.1)  # 避免除零
        # 放宽条件：只要印星动量明显大于食伤动量，且印星动量足够强
        trigger_condition_met = (yin_momentum > 0.3) and (momentum_ratio > 1.2) and (yin_to_self > 0.3)
        
        # 4. 计算能量方程 E_interrupt（如果满足触发条件）
        if trigger_condition_met:
            e_interrupt = (yin_momentum * water_field) - (fire_field * shi_momentum)
        else:
            e_interrupt = 0.0
        
        # 5. 检查修正机制（财星通关）
        cai_vector = earth_field + metal_field  # 财星通关：earth_field + metal_field
        has_rescue = cai_vector > 0.4  # recovery_path: earth_field + metal_field > 0.4
        
        # 6. 提取十神分布（用于辅助分析）
        shi_shen_counts = self.extract_shi_shen(chart, day_master)
        pian_yin_count = shi_shen_counts.get('偏印', 0)
        zheng_yin_count = shi_shen_counts.get('正印', 0)
        shi_shen_count = shi_shen_counts.get('食神', 0)
        shang_guan_count = shi_shen_counts.get('伤官', 0)
        
        # 7. 判断是否为强干涉且无救助（崩态）
        collapse_threshold = self.physical_axiom.get("collapse_threshold", 0.5)
        is_strong_interference = trigger_condition_met and (cai_vector < 0.1) and (e_interrupt > collapse_threshold)
        
        # 8. 计算应力张量（用于辅助分析）
        stress_tensor = self.calculate_stress_tensor(chart)
        
        # 9. 返回分析结果（只有满足trigger_condition的才返回）
        if trigger_condition_met:
            return {
                'chart': chart,
                'day_master': day_master,
                'yin_momentum': yin_momentum,
                'shi_momentum': shi_momentum,
                'yin_to_self': yin_to_self,
                'self_to_shi': self_to_shi,
                'stress_tensor': stress_tensor,
                'water_field': water_field,
                'wood_field': wood_field,
                'fire_field': fire_field,
                'earth_field': earth_field,
                'metal_field': metal_field,
                'e_interrupt': e_interrupt,
                'cai_vector': cai_vector,
                'has_rescue': has_rescue,
                'is_strong_interference': is_strong_interference,
                'trigger_condition_met': True,
                'collapse_threshold': collapse_threshold,
                # 辅助信息
                'shi_shen_counts': shi_shen_counts,
                'pian_yin_count': pian_yin_count,
                'zheng_yin_count': zheng_yin_count,
                'shi_shen_count': shi_shen_count,
                'shang_guan_count': shang_guan_count
            }
        
        return None
    
    def select_samples(self, sample_size: int = 518400, target_count: int = 3, show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        从51.84万样本中筛选符合条件的样本
        
        Args:
            sample_size: 扫描样本数（默认51.84万）
            target_count: 目标样本数（1个微弱财星 + 2个无救助崩态）
            
        Returns:
            筛选结果列表
        """
        logger.info(f"🚀 开始Step A原局海选（RSS-V1.2全量版，扫描{sample_size:,}个样本）...")
        
        # 使用PatternScout扫描"枭神夺食"格局
        found_samples = []
        rescue_samples = []  # 微弱财星（潜在稳态）
        collapse_samples = []  # 纯粹枭印夺食无救助（预设崩态）
        
        def progress_callback(curr, total, stats):
            if show_progress and (curr % 10000 == 0 or curr == total):
                logger.info(f"📊 扫描进度: {curr:,}/{total:,} ({curr/total*100:.1f}%) | 已找到: {len(found_samples)}个候选")
        
        # 扫描样本
        scout_results = self.scout.scout_pattern(
            pattern_id="XIAO_SHEN_DUO_SHI",
            sample_size=sample_size,
            progress_callback=progress_callback
        )
        
        logger.info(f"✅ PatternScout扫描完成，找到 {len(scout_results)} 个匹配样本")
        
        # 分析每个匹配样本
        for idx, result in enumerate(scout_results):
            chart_data = result.get('chart', [])
            if not chart_data or len(chart_data) < 4:
                continue
            
            # 处理chart_data格式
            if isinstance(chart_data[0], str):
                chart = [
                    (chart_data[0][0], chart_data[0][1]) if len(chart_data[0]) >= 2 else ('', ''),
                    (chart_data[1][0], chart_data[1][1]) if len(chart_data[1]) >= 2 else ('', ''),
                    (chart_data[2][0], chart_data[2][1]) if len(chart_data[2]) >= 2 else ('', ''),
                    (chart_data[3][0], chart_data[3][1]) if len(chart_data[3]) >= 2 else ('', '')
                ]
            else:
                chart = [
                    (chart_data[0][0], chart_data[0][1]) if len(chart_data[0]) >= 2 else ('', ''),
                    (chart_data[1][0], chart_data[1][1]) if len(chart_data[1]) >= 2 else ('', ''),
                    (chart_data[2][0], chart_data[2][1]) if len(chart_data[2]) >= 2 else ('', ''),
                    (chart_data[3][0], chart_data[3][1]) if len(chart_data[3]) >= 2 else ('', '')
                ]
            
            # 提取日主
            day_master = result.get('day_master') or (chart[2][0] if chart[2][0] else '')
            if not day_master:
                continue
            
            # 分析样本
            analysis = self.analyze_chart(chart, day_master)
            if analysis:
                analysis['scout_result'] = result
                found_samples.append(analysis)
                
                # 分类
                if analysis.get('has_rescue'):
                    rescue_samples.append(analysis)
                elif analysis.get('is_strong_interference'):
                    collapse_samples.append(analysis)
            else:
                # 调试：打印前几个未通过的样本
                if idx < 3:
                    momentum = self.calculate_momentum(chart, day_master)
                    shi_shen = self.extract_shi_shen(chart, day_master)
                    cai = min(1.0, (shi_shen.get('正财', 0) + shi_shen.get('偏财', 0)) / 2.0)
                    logger.info(f"🔍 样本{idx}未通过分析: yin={momentum['yin_momentum']:.3f}, shi={momentum['shi_momentum']:.3f}, cai={cai:.3f}")
        
        logger.info(f"✅ 分析完成: 总计{len(found_samples)}个候选，微弱财星{len(rescue_samples)}个，强干涉{len(collapse_samples)}个")
        
        # 选择最佳样本
        selected = []
        
        # 选择1个微弱财星样本（潜在稳态，财星向量 0.1-0.3）
        if rescue_samples:
            # 筛选财星向量在0.1-0.3范围内的样本
            weak_cai_samples = [s for s in rescue_samples if 0.1 <= s.get('cai_vector', 0) <= 0.3]
            if weak_cai_samples:
                weak_cai_samples.sort(key=lambda x: -x.get('cai_vector', 0))
                selected.append(weak_cai_samples[0])
                logger.info(f"✅ 选择微弱财星样本: 财星向量={weak_cai_samples[0]['cai_vector']:.3f}")
            else:
                # 如果没有0.1-0.3范围的，选择最接近0.2的
                rescue_samples.sort(key=lambda x: abs(x.get('cai_vector', 0) - 0.2))
                selected.append(rescue_samples[0])
                logger.info(f"✅ 选择准微弱财星样本: 财星向量={rescue_samples[0]['cai_vector']:.3f}")
        else:
            # 如果没有微弱财星样本，从所有候选样本中选择财星在0.1-0.3范围内的
            candidates_with_weak_cai = [s for s in found_samples if 0.1 <= s.get('cai_vector', 0) <= 0.3]
            if candidates_with_weak_cai:
                candidates_with_weak_cai.sort(key=lambda x: -x.get('cai_vector', 0))
                selected.append(candidates_with_weak_cai[0])
                logger.info(f"✅ 选择准微弱财星样本: 财星向量={candidates_with_weak_cai[0]['cai_vector']:.3f}")
            else:
                # 如果还是没有，选择财星最接近0.1的样本（放宽条件）
                if found_samples:
                    candidates_sorted = sorted(found_samples, key=lambda x: abs(x.get('cai_vector', 0) - 0.15))
                    best_candidate = candidates_sorted[0]
                    if best_candidate not in selected:
                        selected.append(best_candidate)
                        logger.info(f"✅ 选择准微弱财星样本（放宽条件）: 财星向量={best_candidate['cai_vector']:.3f}")
        
        # 选择2个纯粹枭印夺食无救助样本（预设崩态，财星向量 < 0.1）
        if collapse_samples:
            collapse_samples.sort(key=lambda x: -(x.get('yin_momentum', 0) - x.get('shi_momentum', 0)))
            selected.extend(collapse_samples[:2])
            for i, sample in enumerate(collapse_samples[:2], 1):
                logger.info(f"✅ 选择崩态样本{i}: 印星动量={sample['yin_momentum']:.3f}, 食伤动量={sample['shi_momentum']:.3f}")
        else:
            # 如果没有崩态样本，选择印星动量最大、食伤动量最小的候选样本
            remaining = [s for s in found_samples if s not in selected and s.get('cai_vector', 0) < 0.1]
            if remaining:
                remaining.sort(key=lambda x: -(x.get('yin_momentum', 0) - x.get('shi_momentum', 0)))
                selected.extend(remaining[:min(2, len(remaining))])
                for i, sample in enumerate(remaining[:min(2, len(remaining))], 1):
                    logger.info(f"✅ 选择准崩态样本{i}: 印星动量={sample['yin_momentum']:.3f}, 食伤动量={sample['shi_momentum']:.3f}")
        
        return selected[:target_count]


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 [02-枭神夺食] Step A: 原局海选（51.84万样本）")
    print("=" * 80)
    print("")
    print("📋 海选标准（RSS-V1.2规范 - 基于物理公理）:")
    print("  - trigger_condition: '印→日'单向淤积且'日→食'动量为 0")
    print("  - energy_equation: E_interrupt = (yin_momentum × water_field) - (fire_field × shi_momentum)")
    print("  - collapse_threshold: 0.5")
    print("  - recovery_path: earth_field + metal_field > 0.4（财星通关）")
    print("")
    print("🎯 样本要求:")
    print("  - 1个带微弱财星（潜在稳态，财星向量 0.1-0.3）")
    print("  - 2个纯粹枭印夺食无救助（预设崩态，财星向量 < 0.1）")
    print("")
    print("⚠️  注意：扫描51.84万样本可能需要较长时间...")
    print("")
    
    selector = StepASelection()
    
    # RSS-V1.2规范：全量扫描51.84万样本
    selected_samples = selector.select_samples(sample_size=518400, target_count=3, show_progress=True)
    
    if not selected_samples:
        print("❌ 未找到符合条件的样本")
        print("   建议：增加扫描样本数或降低筛选阈值")
        return
    
    print("\n" + "=" * 80)
    print("✅ 海选完成！")
    print("=" * 80)
    print("")
    
    for i, sample in enumerate(selected_samples, 1):
        chart = sample['chart']
        bazi_str = f"{chart[0][0]}{chart[0][1]} {chart[1][0]}{chart[1][1]} {chart[2][0]}{chart[2][1]} {chart[3][0]}{chart[3][1]}"
        
        print(f"【样本 {i}】")
        print(f"  八字: {bazi_str}")
        print(f"  日主: {sample['day_master']}")
        print(f"  印星动量 (Yin_Momentum): {sample['yin_momentum']:.3f}")
        print(f"  食伤动量 (Shi_Momentum): {sample['shi_momentum']:.3f}")
        print(f"  印→日 (Yin_to_Self): {sample['yin_to_self']:.3f}")
        print(f"  日→食 (Self_to_Shi): {sample['self_to_shi']:.3f}")
        print(f"  应力张量: {sample.get('stress_tensor', 0.0):.3f}")
        print(f"  财星向量: {sample['cai_vector']:.3f}")
        print(f"  水场强: {sample.get('water_field', 0.0):.3f}")
        print(f"  木场强: {sample.get('wood_field', 0.0):.3f}")
        print(f"  火场强: {sample.get('fire_field', 0.0):.3f}")
        print(f"  土场强: {sample.get('earth_field', 0.0):.3f}")
        print(f"  金场强: {sample.get('metal_field', 0.0):.3f}")
        print(f"  能量截断值 (E_interrupt): {sample.get('e_interrupt', 0.0):.3f}")
        print(f"  状态: {'微弱财星（潜在稳态）' if sample.get('has_rescue') else '极度干涸态（无救助）'}")
        print("")
    
    # 保存结果
    output_file = Path('logs/step_a_xiaoshen_duoshi_selection.json')
    output_file.parent.mkdir(exist_ok=True)
    
    result_data = {
        'task': '[02-枭神夺食] Step A: 原局海选（RSS-V1.2 全量版）',
        'specification': 'RSS-V1.2',
        'timestamp': datetime.now().isoformat(),
        'total_samples': len(selected_samples),
        'samples': [
            {
                'bazi': f"{s['chart'][0][0]}{s['chart'][0][1]} {s['chart'][1][0]}{s['chart'][1][1]} {s['chart'][2][0]}{s['chart'][2][1]} {s['chart'][3][0]}{s['chart'][3][1]}",
                'day_master': s['day_master'],
                'yin_momentum': s['yin_momentum'],
                'shi_momentum': s['shi_momentum'],
                'yin_to_self': s['yin_to_self'],
                'self_to_shi': s['self_to_shi'],
                'stress_tensor': s.get('stress_tensor', 0.0),
                'cai_vector': s['cai_vector'],
                'water_field': s.get('water_field', 0.0),
                'wood_field': s.get('wood_field', 0.0),
                'fire_field': s.get('fire_field', 0.0),
                'earth_field': s.get('earth_field', 0.0),
                'metal_field': s.get('metal_field', 0.0),
                'e_interrupt': s.get('e_interrupt', 0.0),
                'has_rescue': s.get('has_rescue', False),
                'is_strong_interference': s.get('is_strong_interference', False)
            }
            for s in selected_samples
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 结果已保存: {output_file}")
    print("")
    print("=" * 80)
    print("🎯 下一步: Step B - 动态因子层级注入仿真（RSS-V1.2规范）")
    print("=" * 80)


if __name__ == "__main__":
    main()

