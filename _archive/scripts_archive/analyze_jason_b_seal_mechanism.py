#!/usr/bin/env python3
"""
Jason B (身弱用印) 印星帮身机制深度分析
====================================

分析为何"印星帮身"机制在当前配置下未被充分激活

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import sys
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.bazi_profile import BaziProfile
import copy


class JasonBSealMechanismAnalyzer:
    """
    Jason B 印星帮身机制分析器
    """
    
    def __init__(self):
        """初始化分析器"""
        self.case_data = self._load_jason_b_case()
        logger.info(f"✅ 加载 Jason B 案例: {self.case_data['name']}")
    
    def _load_jason_b_case(self) -> dict:
        """加载 Jason B 案例数据"""
        case_file = project_root / "calibration_cases.json"
        if case_file.exists():
            with open(case_file, 'r', encoding='utf-8') as f:
                cases = json.load(f)
                for case in cases:
                    if case.get('id', '').startswith('JASON_B'):
                        return case
        
        # 使用默认数据
        return {
            'id': 'JASON_B_T1964_0910',
            'name': 'Jason B (身弱用印)',
            'bazi': ['甲辰', '癸酉', '己亥', '戊辰'],
            'day_master': '己',
            'gender': '男',
            'birth_date': '1964-09-10',
            'timeline': [
                {'year': 1999, 'ganzhi': '己卯', 'dayun': '丁丑', 'real_magnitude': 100.0},
                {'year': 2007, 'ganzhi': '丁亥', 'dayun': '戊寅', 'real_magnitude': 70.0},
                {'year': 2014, 'ganzhi': '甲午', 'dayun': '己卯', 'real_magnitude': 100.0}
            ]
        }
    
    def analyze_strength_determination(self, year: int, year_pillar: str, luck_pillar: str):
        """
        分析旺衰判定过程
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 分析 {year} 年旺衰判定过程")
        logger.info(f"{'='*80}")
        
        config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        engine = GraphNetworkEngine(config=config)
        
        # 分析八字
        result = engine.analyze(
            bazi=self.case_data['bazi'],
            day_master=self.case_data['day_master'],
            luck_pillar=luck_pillar,
            year_pillar=year_pillar
        )
        
        strength_score = result.get('strength_score', 0.0)
        strength_normalized = strength_score / 100.0
        strength_label = result.get('strength_label', 'Unknown')
        
        logger.info(f"身强分数: {strength_score:.2f} / 100.0")
        logger.info(f"归一化值: {strength_normalized:.4f}")
        logger.info(f"身强标签: {strength_label}")
        
        # 检查印星
        day_master = self.case_data['day_master']
        resource_element = self._get_resource_element(day_master)
        
        logger.info(f"\n印星分析:")
        logger.info(f"  日主: {day_master}")
        logger.info(f"  印星元素: {resource_element}")
        
        # 检查八字中的印星
        seal_count = 0
        seal_details = []
        for pillar in self.case_data['bazi']:
            if len(pillar) >= 2:
                stem = pillar[0]
                branch = pillar[1]
                stem_element = self._get_element(stem)
                branch_element = self._get_element(branch)
                
                if stem_element == resource_element:
                    seal_count += 1
                    seal_details.append(f"天干 {stem} ({stem_element})")
                if branch_element == resource_element:
                    seal_count += 1
                    seal_details.append(f"地支 {branch} ({branch_element})")
        
        logger.info(f"  原局印星数量: {seal_count}")
        for detail in seal_details:
            logger.info(f"    - {detail}")
        
        # 检查流年和大运中的印星
        year_stem = year_pillar[0] if len(year_pillar) >= 2 else ''
        year_branch = year_pillar[1] if len(year_pillar) >= 2 else ''
        luck_stem = luck_pillar[0] if len(luck_pillar) >= 2 else ''
        luck_branch = luck_pillar[1] if len(luck_pillar) >= 2 else ''
        
        year_seal = False
        luck_seal = False
        
        if self._get_element(year_stem) == resource_element:
            year_seal = True
            logger.info(f"  ✅ 流年天干 {year_stem} 是印星")
        if self._get_element(year_branch) == resource_element:
            year_seal = True
            logger.info(f"  ✅ 流年地支 {year_branch} 是印星")
        if self._get_element(luck_stem) == resource_element:
            luck_seal = True
            logger.info(f"  ✅ 大运天干 {luck_stem} 是印星")
        if self._get_element(luck_branch) == resource_element:
            luck_seal = True
            logger.info(f"  ✅ 大运地支 {luck_branch} 是印星")
        
        if not year_seal and not luck_seal:
            logger.info(f"  ⚠️  流年和大运中未发现印星")
        
        return {
            'strength_score': strength_score,
            'strength_normalized': strength_normalized,
            'strength_label': strength_label,
            'seal_count': seal_count,
            'year_seal': year_seal,
            'luck_seal': luck_seal
        }
    
    def analyze_wealth_calculation(self, year: int, year_pillar: str, luck_pillar: str, real_wealth: float):
        """
        分析财富计算过程
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"💰 分析 {year} 年财富计算过程")
        logger.info(f"{'='*80}")
        
        config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        engine = GraphNetworkEngine(config=config)
        
        # 计算财富指数
        result = engine.calculate_wealth_index(
            bazi=self.case_data['bazi'],
            day_master=self.case_data['day_master'],
            gender=self.case_data['gender'],
            luck_pillar=luck_pillar,
            year_pillar=year_pillar
        )
        
        if isinstance(result, dict):
            predicted_wealth = result.get('wealth_index', 0.0)
            details = result.get('details', [])
        else:
            predicted_wealth = float(result)
            details = []
        
        error = abs(predicted_wealth - real_wealth)
        
        logger.info(f"预测值: {predicted_wealth:.2f}")
        logger.info(f"真实值: {real_wealth:.2f}")
        logger.info(f"误差: {error:.2f}")
        
        logger.info(f"\n计算详情:")
        for detail in details[:10]:  # 只显示前10条
            logger.info(f"  - {detail}")
        
        return {
            'predicted_wealth': predicted_wealth,
            'real_wealth': real_wealth,
            'error': error,
            'details': details
        }
    
    def _get_resource_element(self, day_master: str) -> str:
        """获取印星元素"""
        # 己土的印星是火（火生土）
        resource_map = {
            '甲': 'water', '乙': 'water',  # 木的印星是水
            '丙': 'wood', '丁': 'wood',    # 火的印星是木
            '戊': 'fire', '己': 'fire',    # 土的印星是火
            '庚': 'earth', '辛': 'earth',  # 金的印星是土
            '壬': 'metal', '癸': 'metal'    # 水的印星是金
        }
        return resource_map.get(day_master, 'earth')
    
    def _get_element(self, char: str) -> str:
        """获取字符的五行元素"""
        stem_elements = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water'
        }
        branch_elements = {
            '子': 'water', '丑': 'earth', '寅': 'wood', '卯': 'wood',
            '辰': 'earth', '巳': 'fire', '午': 'fire', '未': 'earth',
            '申': 'metal', '酉': 'metal', '戌': 'earth', '亥': 'water'
        }
        return stem_elements.get(char, branch_elements.get(char, 'earth'))
    
    def generate_analysis_report(self) -> dict:
        """
        生成完整的分析报告
        """
        logger.info("\n" + "=" * 80)
        logger.info("🎯 开始生成 Jason B (身弱用印) 印星帮身机制分析报告")
        logger.info("=" * 80)
        
        report = {
            'case_id': self.case_data['id'],
            'case_name': self.case_data['name'],
            'bazi': self.case_data['bazi'],
            'day_master': self.case_data['day_master'],
            'analysis_results': []
        }
        
        for event in self.case_data['timeline']:
            year = event.get('year')
            year_pillar = event.get('ganzhi', '')
            luck_pillar = event.get('dayun', '')
            real_wealth = event.get('real_magnitude', 0.0)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"分析 {year} 年事件")
            logger.info(f"{'='*80}")
            
            # 分析旺衰判定
            strength_result = self.analyze_strength_determination(year, year_pillar, luck_pillar)
            
            # 分析财富计算
            wealth_result = self.analyze_wealth_calculation(year, year_pillar, luck_pillar, real_wealth)
            
            # 合并结果
            event_result = {
                'year': year,
                'year_pillar': year_pillar,
                'luck_pillar': luck_pillar,
                'real_wealth': real_wealth,
                **strength_result,
                **wealth_result
            }
            
            report['analysis_results'].append(event_result)
        
        # 保存报告
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / "jason_b_seal_mechanism_analysis.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✅ 报告已保存到: {report_file}")
        
        return report


def main():
    """主函数"""
    analyzer = JasonBSealMechanismAnalyzer()
    report = analyzer.generate_analysis_report()
    
    # 输出总结
    print("\n" + "=" * 80)
    print("📊 Jason B (身弱用印) 印星帮身机制分析总结")
    print("=" * 80)
    
    for result in report['analysis_results']:
        print(f"\n{result['year']} 年:")
        print(f"  身强分数: {result['strength_score']:.2f} ({result['strength_label']})")
        print(f"  原局印星数: {result['seal_count']}")
        print(f"  流年印星: {'是' if result['year_seal'] else '否'}")
        print(f"  大运印星: {'是' if result['luck_seal'] else '否'}")
        print(f"  预测值: {result['predicted_wealth']:.2f}")
        print(f"  真实值: {result['real_wealth']:.2f}")
        print(f"  误差: {result['error']:.2f}")
    
    print("\n✅ 分析完成！")


if __name__ == '__main__':
    main()

