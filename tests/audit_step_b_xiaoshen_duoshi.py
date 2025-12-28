"""
[QGA V25.0 格局审计] Step B: 动态因子层级注入仿真 (RSS-V1.2规范)
任务: [02-枭神夺食] 生物能通联与彻底寂灭测试

RSS-V1.2 规范:
- 大运注入: 注入场能，观察晶格变形
- 流年触发: 注入高频脉冲。若系统稳定性 S < 0.15，判定为"逻辑坍缩" (Logic Collapse)
- 地理调优: 注入地理阻尼。修正值必须限制在大运与流年叠加后的稳定性值的 ±15% 以内

对Step A筛选出的3个样本施加"一命二运三风水"的动态压力:
- 大运 (Luck - 静态场能)
- 流年 (Year - 能量脉冲)
- 地理 (Geo - 阻尼修正)

监控指标:
- system_stability 的波动曲线
- 动量比（Yin/Shi Ratio）的动态变化
- 生物能寂灭态触发点（稳定性 < 0.15）
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.subjects.neural_router.execution_kernel import NeuralRouterKernel
from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
from core.trinity.core.nexus.definitions import BaziParticleNexus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StepBDynamicSimulation:
    """Step B: 动态因子层级注入仿真器（枭神夺食专用）"""
    
    def __init__(self):
        self.kernel = NeuralRouterKernel()
        self.vectorizer = FeatureVectorizer()
        logger.info("✅ Step B 动态仿真器初始化完成（枭神夺食专用）")
    
    def parse_bazi_string(self, bazi_str: str) -> Tuple[List[Tuple[str, str]], str]:
        """
        解析八字字符串，例如 "甲子 戊辰 丙寅 甲午"
        
        Returns:
            (chart, day_master)
        """
        parts = bazi_str.split()
        if len(parts) != 4:
            raise ValueError(f"八字格式错误: {bazi_str}")
        
        chart = []
        for part in parts:
            if len(part) != 2:
                raise ValueError(f"干支格式错误: {part}")
            chart.append((part[0], part[1]))
        
        day_master = chart[2][0]  # 日柱天干
        return chart, day_master
    
    def calculate_momentum_ratio(self, chart: List[Tuple[str, str]], day_master: str) -> float:
        """计算动量比（Yin/Shi Ratio）"""
        yin_count = 0.0
        shi_count = 0.0
        
        for gan, zhi in chart:
            shi_shen = BaziParticleNexus.get_shi_shen(gan, day_master)
            if shi_shen in ['正印', '偏印']:
                yin_count += 1.0
            elif shi_shen in ['食神', '伤官']:
                shi_count += 1.0
        
        if shi_count == 0:
            return float('inf') if yin_count > 0 else 0.0
        
        return yin_count / shi_count
    
    def generate_luck_pillar(self, chart: List[Tuple[str, str]], day_master: str, 
                           test_type: str) -> Tuple[str, str]:
        """
        生成大运干支
        
        Args:
            chart: 八字四柱
            day_master: 日主
            test_type: 测试类型
                - "extinction": 强印大运（彻底寂灭）
                - "rescue": 强财大运（财星破枭）
                - "neutral": 中性大运
        
        Returns:
            (gan, zhi) 大运干支
        """
        if test_type == "extinction":
            # 强印大运：甲寅（强木，增强枭神）
            return ('甲', '寅')  # 甲寅，强木
        elif test_type == "rescue":
            # 强财大运：庚申（强金，财星破枭）
            return ('庚', '申')  # 庚申，强金
        else:
            # 中性大运：与日主同五行
            day_element = self._get_element_from_gan(day_master)
            if day_element == 'wood':
                return ('甲', '寅')
            elif day_element == 'fire':
                return ('丙', '午')
            elif day_element == 'earth':
                return ('戊', '辰')
            elif day_element == 'metal':
                return ('庚', '申')
            else:  # water
                return ('壬', '子')
    
    def generate_year_pillar(self, chart: List[Tuple[str, str]], day_master: str,
                            test_type: str) -> Tuple[str, str]:
        """
        生成流年干支
        
        Args:
            chart: 八字四柱
            day_master: 日主
            test_type: 测试类型
                - "cai": 财星流年（能量管道恢复）
                - "shi": 食伤流年（能量脉冲，可能憋爆）
                - "yin": 枭神流年（增强拦截）
                - "neutral": 中性流年
        
        Returns:
            (gan, zhi) 流年干支
        """
        if test_type == "cai":
            # 财星流年：庚申（强金）
            return ('庚', '申')
        elif test_type == "shi":
            # 食伤流年：戊午（强土，食神）
            return ('戊', '午')
        elif test_type == "yin":
            # 枭神流年：甲寅（强木，偏印）
            return ('甲', '寅')
        else:
            # 中性流年：与日主同五行
            day_element = self._get_element_from_gan(day_master)
            if day_element == 'wood':
                return ('甲', '寅')
            elif day_element == 'fire':
                return ('丙', '午')
            elif day_element == 'earth':
                return ('戊', '辰')
            elif day_element == 'metal':
                return ('庚', '申')
            else:  # water
                return ('壬', '子')
    
    def _get_element_from_gan(self, gan: str) -> str:
        """从天干获取五行元素"""
        element_map = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water'
        }
        return element_map.get(gan, 'earth')
    
    def run_simulation(self, sample: Dict[str, Any], 
                      test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个样本的动态仿真
        
        Args:
            sample: Step A筛选出的样本
            test_config: 测试配置
                - luck_type: 大运类型
                - year_type: 流年类型
                - geo_info: 地理信息
        
        Returns:
            仿真结果
        """
        bazi_str = sample['bazi']
        chart, day_master = self.parse_bazi_string(bazi_str)
        
        # 生成大运和流年
        luck_pillar = self.generate_luck_pillar(chart, day_master, test_config.get('luck_type', 'neutral'))
        year_pillar = self.generate_year_pillar(chart, day_master, test_config.get('year_type', 'neutral'))
        geo_info = test_config.get('geo_info', '中央')
        
        logger.info(f"🔬 仿真配置:")
        logger.info(f"   八字: {bazi_str}")
        logger.info(f"   大运: {luck_pillar[0]}{luck_pillar[1]} ({test_config.get('luck_type', 'neutral')})")
        logger.info(f"   流年: {year_pillar[0]}{year_pillar[1]} ({test_config.get('year_type', 'neutral')})")
        logger.info(f"   地理: {geo_info}")
        
        # 计算原局动量比
        original_momentum_ratio = sample.get('yin_momentum', 0) / (sample.get('shi_momentum', 0) + 0.1)
        
        # 提取特征向量
        feature_vector = self.vectorizer.vectorize_bazi(
            chart=chart,
            day_master=day_master,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            geo_info=geo_info,
            micro_env=None,
            synthesized_field={
                "friction_index": int(sample.get('stress_tensor', 0.5) * 100),
                "coherence_index": 50,
                "micro_env": []
            }
        )
        
        # 计算动态动量比（考虑大运和流年的影响）
        # 简化：基于大运和流年的十神
        luck_shi_shen = BaziParticleNexus.get_shi_shen(luck_pillar[0], day_master)
        year_shi_shen = BaziParticleNexus.get_shi_shen(year_pillar[0], day_master)
        
        dynamic_yin_momentum = sample.get('yin_momentum', 0)
        dynamic_shi_momentum = sample.get('shi_momentum', 0)
        
        # 大运影响
        if luck_shi_shen in ['正印', '偏印']:
            dynamic_yin_momentum += 0.3  # 大运增强印星
        elif luck_shi_shen in ['食神', '伤官']:
            dynamic_shi_momentum += 0.2  # 大运增强食伤
        elif luck_shi_shen in ['正财', '偏财']:
            # 财星破枭：降低印星动量
            dynamic_yin_momentum = max(0.0, dynamic_yin_momentum - 0.2)
        
        # 流年影响
        if year_shi_shen in ['正印', '偏印']:
            dynamic_yin_momentum += 0.2  # 流年增强印星
        elif year_shi_shen in ['食神', '伤官']:
            dynamic_shi_momentum += 0.3  # 流年增强食伤（能量脉冲）
        elif year_shi_shen in ['正财', '偏财']:
            # 财星破枭：降低印星动量
            dynamic_yin_momentum = max(0.0, dynamic_yin_momentum - 0.15)
        
        dynamic_momentum_ratio = dynamic_yin_momentum / (dynamic_shi_momentum + 0.1)
        
        # 构建激活格局（枭神夺食）
        active_patterns = [{
            "id": "XIAO_SHEN_DUO_SHI",
            "name": "枭神夺食",
            "weight": 0.8,
            "base_strength": 0.7,
            "sai": sample.get('stress_tensor', 0.5) * 100
        }]
        
        # 调用LLM_Neural_Router
        result = self.kernel.process_bazi_profile(
            active_patterns=active_patterns,
            synthesized_field={
                "friction_index": int(sample.get('stress_tensor', 0.5) * 100),
                "coherence_index": 50,
                "micro_env": []
            },
            profile_name=f"样本_{sample.get('bazi', 'unknown')}",
            day_master=day_master,
            force_vectors=feature_vector['elemental_fields_dict'],
            year=2025,  # 假设年份
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            geo_info=geo_info
        )
        
        return {
            'sample': sample,
            'test_config': test_config,
            'luck_pillar': f"{luck_pillar[0]}{luck_pillar[1]}",
            'year_pillar': f"{year_pillar[0]}{year_pillar[1]}",
            'geo_info': geo_info,
            'result': result,
            'energy_state': result.get('energy_state_report', {}),
            'system_stability': result.get('energy_state_report', {}).get('system_stability', 0.0),
            'logic_collapse': result.get('logic_collapse', {}),
            'persona': result.get('persona', ''),
            'momentum_analysis': {
                'original_yin_momentum': sample.get('yin_momentum', 0),
                'original_shi_momentum': sample.get('shi_momentum', 0),
                'original_ratio': original_momentum_ratio,
                'dynamic_yin_momentum': dynamic_yin_momentum,
                'dynamic_shi_momentum': dynamic_shi_momentum,
                'dynamic_ratio': dynamic_momentum_ratio,
                'ratio_change': dynamic_momentum_ratio - original_momentum_ratio
            }
        }


def main():
    """主函数"""
    print("=" * 80)
    print("🔬 [02-枭神夺食] Step B: 动态因子层级注入仿真（RSS-V1.2规范）")
    print("=" * 80)
    print("")
    
    # 加载Step A筛选结果
    selection_file = Path('logs/step_a_xiaoshen_duoshi_selection.json')
    if not selection_file.exists():
        print("❌ 未找到Step A筛选结果文件")
        return
    
    with open(selection_file, 'r', encoding='utf-8') as f:
        selection_data = json.load(f)
    
    samples = selection_data.get('samples', [])
    if len(samples) < 3:
        print(f"❌ Step A筛选结果不足3个样本，当前只有{len(samples)}个")
        return
    
    print(f"✅ 加载Step A筛选结果: {len(samples)}个样本")
    print("")
    
    simulator = StepBDynamicSimulation()
    
    # 定义测试配置（RSS-V1规范）
    test_configs = [
        {
            'name': '样本1-财星大运+流年财星（能量管道恢复）',
            'sample_idx': 0,
            'luck_type': 'rescue',  # 强财大运（财星破枭）
            'year_type': 'cai',  # 财星流年
            'geo_info': '中央'
        },
        {
            'name': '样本2-枭神大运+南方木火环境（生物能寂灭态）',
            'sample_idx': 1,
            'luck_type': 'extinction',  # 强印大运（彻底寂灭）
            'year_type': 'yin',  # 枭神流年
            'geo_info': '南方'  # 木火地
        },
        {
            'name': '样本3-食伤脉冲（非线性应力爆发）',
            'sample_idx': 2,
            'luck_type': 'neutral',  # 中性大运
            'year_type': 'shi',  # 食伤流年（能量脉冲）
            'geo_info': '东南'  # 木火地
        }
    ]
    
    simulation_results = []
    
    for test_config in test_configs:
        print("=" * 80)
        print(f"🧪 {test_config['name']}")
        print("=" * 80)
        print("")
        
        sample = samples[test_config['sample_idx']]
        
        try:
            result = simulator.run_simulation(sample, test_config)
            simulation_results.append(result)
            
            # 输出关键指标
            print(f"✅ 仿真完成")
            print(f"   系统稳定性: {result['system_stability']:.4f}")
            print(f"   临界状态: {result['energy_state'].get('critical_state', 'N/A')}")
            print(f"   能量流向: {result['energy_state'].get('energy_flow_direction', 'N/A')}")
            print(f"   应力张量: {result['energy_state'].get('stress_tensor', 0.0):.4f}")
            print("")
            
            # 输出动量比分析
            momentum = result['momentum_analysis']
            print(f"【动量比分析】")
            print(f"   原局动量比: {momentum['original_ratio']:.3f} (印星={momentum['original_yin_momentum']:.3f} / 食伤={momentum['original_shi_momentum']:.3f})")
            print(f"   动态动量比: {momentum['dynamic_ratio']:.3f} (印星={momentum['dynamic_yin_momentum']:.3f} / 食伤={momentum['dynamic_shi_momentum']:.3f})")
            print(f"   动量比变化: {momentum['ratio_change']:+.3f}")
            print("")
            
            # RSS-V1.2规范：逻辑坍缩判定（S < 0.15）
            if result['system_stability'] < 0.15:
                print("⚠️  【逻辑坍缩】检测到生物能寂灭态（Extinction State）！")
                print(f"   系统稳定性降至: {result['system_stability']:.4f} < 0.15 (RSS-V1.2规范：逻辑坍缩阈值)")
                print(f"   临界状态: {result['energy_state'].get('critical_state', 'N/A')}")
                print("")
            elif result['system_stability'] < 0.3:
                print("⚠️  系统接近生物能寂灭态")
                print(f"   系统稳定性: {result['system_stability']:.4f}")
                print("")
            
        except Exception as e:
            logger.error(f"❌ 仿真失败: {e}", exc_info=True)
            print(f"❌ 仿真失败: {e}")
            print("")
    
    # 保存结果
    output_file = Path('logs/step_b_xiaoshen_duoshi_simulation.json')
    output_file.parent.mkdir(exist_ok=True)
    
    result_data = {
        'task': '[02-枭神夺食] Step B: 动态因子层级注入仿真（RSS-V1.2规范）',
        'specification': 'RSS-V1.2',
        'timestamp': datetime.now().isoformat(),
        'simulations': [
            {
                'test_name': r['test_config']['name'],
                'sample': r['sample'],
                'luck_pillar': r['luck_pillar'],
                'year_pillar': r['year_pillar'],
                'geo_info': r['geo_info'],
                'system_stability': r['system_stability'],
                'energy_state': r['energy_state'],
                'logic_collapse': r['logic_collapse'],
                'persona': r['persona'],
                'momentum_analysis': r['momentum_analysis']
            }
            for r in simulation_results
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print("=" * 80)
    print("✅ Step B 动态仿真完成！")
    print("=" * 80)
    print("")
    print(f"📁 结果已保存: {output_file}")
    print("")
    
    # 生成摘要报告
    print("=" * 80)
    print("📊 仿真摘要报告")
    print("=" * 80)
    print("")
    
    for i, result in enumerate(simulation_results, 1):
        print(f"【仿真 {i}】{result['test_config']['name']}")
        print(f"  原局稳定性: {result['sample'].get('stress_tensor', 0.0):.3f}")
        print(f"  动态稳定性: {result['system_stability']:.4f}")
        print(f"  稳定性变化: {result['system_stability'] - result['sample'].get('stress_tensor', 0.0):.4f}")
        print(f"  临界状态: {result['energy_state'].get('critical_state', 'N/A')}")
        
        momentum = result['momentum_analysis']
        print(f"  原局动量比: {momentum['original_ratio']:.3f}")
        print(f"  动态动量比: {momentum['dynamic_ratio']:.3f}")
        print(f"  动量比变化: {momentum['ratio_change']:+.3f}")
        
        # RSS-V1.2规范：逻辑坍缩判定（S < 0.15）
        if result['system_stability'] < 0.15:
            print(f"  ⚠️  【逻辑坍缩】触发生物能寂灭态！(S={result['system_stability']:.4f} < 0.15)")
        elif result['system_stability'] < 0.3:
            print(f"  ⚠️  接近生物能寂灭态 (S={result['system_stability']:.4f})")
        print("")
    
    print("=" * 80)
    print("🎯 下一步: Step C - 语义对撞与奇点标注")
    print("=" * 80)


if __name__ == "__main__":
    main()

