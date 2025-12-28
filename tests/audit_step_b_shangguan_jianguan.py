"""
[QGA V25.0 格局审计] Step B: 动态因子层级注入仿真
任务: [01-伤官见官] 时空受力测试

对Step A筛选出的3个样本施加"一命二运三风水"的动态压力：
- 大运 (Luck - 静态场能)
- 流年 (Year - 能量脉冲)
- 地理 (Geo - 阻尼修正)

监控指标：
- system_stability 的波动曲线
- 应力阈值触发点（逻辑坍缩奇点）
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
from core.bazi_profile import BaziProfile
from core.trinity.core.nexus.definitions import BaziParticleNexus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StepBDynamicSimulation:
    """Step B: 动态因子层级注入仿真器"""
    
    def __init__(self):
        self.kernel = NeuralRouterKernel()
        self.vectorizer = FeatureVectorizer()
        logger.info("✅ Step B 动态仿真器初始化完成")
    
    def parse_bazi_string(self, bazi_str: str) -> Tuple[List[Tuple[str, str]], str]:
        """
        解析八字字符串，例如 "甲子 丙寅 癸酉 戊午"
        
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
    
    def get_shi_shen_for_pillar(self, gan: str, zhi: str, day_master: str) -> str:
        """获取干支的十神（简化：只取天干）"""
        return BaziParticleNexus.get_shi_shen(gan, day_master)
    
    def generate_luck_pillar(self, chart: List[Tuple[str, str]], day_master: str, 
                           test_type: str) -> Tuple[str, str]:
        """
        生成大运干支
        
        Args:
            chart: 八字四柱
            day_master: 日主
            test_type: 测试类型
                - "high_pressure": 强官杀大运（高压）
                - "rescue": 强印星大运（解救）
                - "neutral": 中性大运
        
        Returns:
            (gan, zhi) 大运干支
        """
        if test_type == "high_pressure":
            # 强官杀大运：庚金（正官）或辛金（七杀）
            return ('庚', '申')  # 庚申，强金
        elif test_type == "rescue":
            # 强印星大运：壬水（正印）或癸水（偏印）
            return ('壬', '子')  # 壬子，强水
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
                - "trigger": 与原局伤官同频的流年（引动）
                - "high_pressure": 强官流年
                - "neutral": 中性流年
        
        Returns:
            (gan, zhi) 流年干支
        """
        if test_type == "trigger":
            # 与原局伤官同频：如果日主是木，伤官是火，流年用火
            # 简化：使用丁火（伤官）
            return ('丁', '巳')  # 丁巳，强火
        elif test_type == "high_pressure":
            # 强官流年：庚金
            return ('庚', '申')  # 庚申，强金
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
        
        # 构建激活格局（伤官见官）
        active_patterns = [{
            "id": "SHANG_GUAN_JIAN_GUAN",
            "name": "伤官见官",
            "weight": 0.8,
            "base_strength": 0.75,
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
            profile_name=f"样本_{sample.get('profile_id', 'unknown')}",
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
            # RSS-V1.2规范：逻辑坍缩判定（S < 0.15）
            'is_logic_collapse': result.get('energy_state_report', {}).get('system_stability', 1.0) < 0.15
        }


def main():
    """主函数"""
    print("=" * 80)
    print("🔬 [01-伤官见官] Step B: 动态因子层级注入仿真")
    print("=" * 80)
    print("")
    
    # 加载Step A筛选结果（优先使用v1.2版本）
    selection_file = Path('logs/step_a_shangguan_jianguan_v1.2_selection.json')
    if not selection_file.exists():
        selection_file = Path('logs/step_a_shangguan_jianguan_v1.1_selection.json')
    if not selection_file.exists():
        selection_file = Path('logs/step_a_shangguan_jianguan_selection.json')
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
    
    # 定义测试配置
    test_configs = [
        {
            'name': '样本1-稳态-流年大耗测试',
            'sample_idx': 0,
            'luck_type': 'neutral',  # 中性大运
            'year_type': 'trigger',  # 引动流年
            'geo_info': '中央'
        },
        {
            'name': '样本2-崩态1-南方火地+强官流年',
            'sample_idx': 1,
            'luck_type': 'high_pressure',  # 强官杀大运
            'year_type': 'high_pressure',  # 强官流年
            'geo_info': '南方'  # 火地
        },
        {
            'name': '样本3-崩态2-强印大运解救',
            'sample_idx': 2,
            'luck_type': 'rescue',  # 强印大运
            'year_type': 'neutral',  # 中性流年
            'geo_info': '北方'  # 水地
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
            
            # RSS-V1.2规范：逻辑坍缩判定（S < 0.15）
            if result.get('system_stability', 1.0) < 0.15:
                print(f"   ⚠️  逻辑坍缩 (Logic Collapse): 稳定性 < 0.15，触发奇点诊断")
            print("")
            
            # RSS-V1.2规范：逻辑坍缩判定（S < 0.15）
            if result.get('system_stability', 1.0) < 0.15:
                print("⚠️  逻辑坍缩 (Logic Collapse): 稳定性 < 0.15，触发奇点诊断")
                print(f"   系统稳定性: {result['system_stability']:.4f}")
                print(f"   临界状态: {result['energy_state'].get('critical_state', 'N/A')}")
                print("")
            
        except Exception as e:
            logger.error(f"❌ 仿真失败: {e}", exc_info=True)
            print(f"❌ 仿真失败: {e}")
            print("")
    
    # 保存结果
    output_file = Path('logs/step_b_shangguan_jianguan_simulation.json')
    output_file.parent.mkdir(exist_ok=True)
    
    result_data = {
        'task': '[01-伤官见官] Step B: 动态因子层级注入仿真',
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
                'persona': r['persona']
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
        if result['system_stability'] < 0.3:
            print(f"  ⚠️  触发逻辑坍缩奇点！")
        print("")
    
    print("=" * 80)
    print("🎯 下一步: Step C - 奇点标注")
    print("=" * 80)


if __name__ == "__main__":
    main()

