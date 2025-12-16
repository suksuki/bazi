"""
V89.0 任务 135：Level 3 动态修正算法逻辑审计
==========================================
目标：诊断 Level 3 SpacetimeCorrector 算法失效的原因，并获取其计算过程的中间值，
      以验证 0.6/0.4 动态权重是否被正确应用。

策略：
1. 检查 SpacetimeCorrector 的激活状态和配置
2. 追踪 C15（李嘉诚 1958年）案例的 Level 3 计算过程
3. 获取中间计算值：静态得分、大运修正项、流年修正项、最终修正系数
"""

import sys
import os
import json
import io
from typing import Dict, List, Tuple, Any, Optional
from copy import deepcopy
from datetime import datetime

# Fix encoding issue
import locale
try:
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except:
    pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88


class V89Level3Auditor:
    """
    V89.0 Level 3 算法逻辑审计器
    
    追踪 SpacetimeCorrector 的计算过程
    """
    
    def __init__(self, config_path: str):
        """
        初始化审计器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        
        # 加载配置
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        print(f"✅ Level 3 审计器初始化完成")
    
    def check_spacetime_config(self) -> Dict:
        """
        检查 SpacetimeCorrector 的配置状态
        
        Returns:
            配置状态字典
        """
        print("=" * 80)
        print("步骤一：SpacetimeCorrector 配置状态检查")
        print("=" * 80)
        
        physics_config = self.config.get('physics', {})
        spacetime_config = physics_config.get('SpacetimeCorrector', {})
        
        config_status = {
            'enabled': spacetime_config.get('Enabled', False),
            'corrector_base_factor': spacetime_config.get('CorrectorBaseFactor', 1.0),
            'luck_pillar_weight': spacetime_config.get('LuckPillarWeight', 0.6),
            'annual_pillar_weight': spacetime_config.get('AnnualPillarWeight', 0.4),
            'exclusion_list': spacetime_config.get('ExclusionList', []),
            'case_specific_corrector': spacetime_config.get('CaseSpecificCorrectorFactor', {})
        }
        
        print(f"\nSpacetimeCorrector 配置:")
        print(f"  Enabled: {config_status['enabled']}")
        print(f"  CorrectorBaseFactor: {config_status['corrector_base_factor']}")
        print(f"  LuckPillarWeight: {config_status['luck_pillar_weight']}")
        print(f"  AnnualPillarWeight: {config_status['annual_pillar_weight']}")
        print(f"  ExclusionList: {config_status['exclusion_list']}")
        print(f"  CaseSpecificCorrectorFactor: {config_status['case_specific_corrector']}")
        
        return config_status
    
    def _calculate_birth_date_from_bazi(self, bazi_list: List[str]) -> Optional[Dict]:
        """
        从八字反推出生年月日时
        
        Args:
            bazi_list: 八字列表，格式如 ['丁', '卯', '未', '辰', '庚', '辰', '庚', '辰']
                      或 ['丁卯', '丁未', '庚辰', '庚辰']
        
        Returns:
            出生日期信息字典，包含 datetime 对象
        """
        try:
            from lunar_python import Lunar, Solar
            import re
            
            # 处理不同的输入格式
            if len(bazi_list) == 4:
                # 格式：['丁卯', '丁未', '庚辰', '庚辰']
                year_pz = bazi_list[0]
                month_pz = bazi_list[1]
                day_pz = bazi_list[2]
                hour_pz = bazi_list[3]
            elif len(bazi_list) == 8:
                # 格式：['丁', '卯', '未', '辰', '庚', '辰', '庚', '辰']
                year_pz = bazi_list[0] + bazi_list[1]
                month_pz = bazi_list[2] + bazi_list[3]
                day_pz = bazi_list[4] + bazi_list[5]
                hour_pz = bazi_list[6] + bazi_list[7]
            else:
                return None
            
            # 天干地支映射
            GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            
            # 年柱反推年份
            year_gan = year_pz[0]
            year_zhi = year_pz[1]
            gan_idx = GAN.index(year_gan) if year_gan in GAN else -1
            zhi_idx = ZHI.index(year_zhi) if year_zhi in ZHI else -1
            
            if gan_idx == -1 or zhi_idx == -1:
                return None
            
            # 在合理范围内查找匹配的年份（1920-2020）
            birth_year = None
            for base_year in range(1920, 2020):
                if (base_year - 4) % 10 == gan_idx and (base_year - 4) % 12 == zhi_idx:
                    birth_year = base_year
                    break
            
            if birth_year is None:
                return None
            
            # 月柱反推月份（简化：假设月支对应农历月份）
            month_zhi = month_pz[1]
            zhi_to_month = {
                '寅': 2, '卯': 3, '辰': 4, '巳': 5, '午': 6, '未': 7,
                '申': 8, '酉': 9, '戌': 10, '亥': 11, '子': 12, '丑': 1
            }
            birth_month = zhi_to_month.get(month_zhi, 6)
            
            # 假设日期为15日（月中）
            birth_day = 15
            
            # 时柱反推时辰
            hour_zhi = hour_pz[1] if len(hour_pz) > 1 else '午'
            zhi_to_hour = {
                '子': 0, '丑': 2, '寅': 4, '卯': 6, '辰': 8, '巳': 10,
                '午': 12, '未': 14, '申': 16, '酉': 18, '戌': 20, '亥': 22
            }
            birth_hour = zhi_to_hour.get(hour_zhi, 12)
            
            birth_date = datetime(birth_year, birth_month, birth_day, birth_hour, 0)
            
            return {
                'date': birth_date,
                'year': birth_year,
                'month': birth_month,
                'day': birth_day,
                'hour': birth_hour
            }
        except Exception as e:
            print(f"⚠️  反推出生日期失败: {e}")
            return None
    
    def _calculate_luck_and_annual_pillars(self, birth_date, target_year: int, gender: int) -> Tuple[Optional[str], Optional[str]]:
        """
        计算大运和流年柱
        
        Args:
            birth_date: 出生日期 (datetime 对象)
            target_year: 目标年份
            gender: 性别（1=男，0=女）
        
        Returns:
            (luck_pillar, annual_pillar)
        """
        try:
            from core.bazi_profile import BaziProfile
            from core.engines.luck_engine import LuckEngine
            
            # 创建 BaziProfile 计算大运
            profile = BaziProfile(birth_date, gender)
            luck_pillar = profile.get_luck_pillar_at(target_year)
            
            # 使用 LuckEngine 计算流年
            luck_engine = LuckEngine()
            annual_pillar = luck_engine.get_year_ganzhi(target_year)
            
            return luck_pillar, annual_pillar
        except Exception as e:
            print(f"⚠️  计算大运和流年失败: {e}")
            return None, None
    
    def trace_c15_calculation(self) -> Dict:
        """
        追踪 C15（李嘉诚 1958年）案例的 Level 3 计算过程
        
        Returns:
            计算过程追踪结果
        """
        print("\n" + "=" * 80)
        print("步骤二：C15 案例动态修正过程追踪")
        print("=" * 80)
        
        # C15: 李嘉诚 - 1958年（戊戌流年）财富爆发
        # 八字：丁卯 丁未 庚辰 庚辰
        bazi_list = ['丁', '卯', '丁', '未', '庚', '辰', '庚', '辰']
        case_data = {
            'year': '丁',
            'month': '卯',
            'day': '未',
            'hour': '辰',
            'day_master': '庚',
            'gender': 1,
            'case_id': 'C15'
        }
        
        # 从八字反推出生日期
        birth_info = self._calculate_birth_date_from_bazi(bazi_list)
        if not birth_info:
            print("⚠️  无法从八字反推出生日期")
            return {}
        
        birth_date = birth_info['date']
        print(f"\n反推的出生日期: {birth_date.strftime('%Y-%m-%d %H:%M')}")
        
        # 计算大运和流年
        target_year = 1958
        luck_pillar, annual_pillar = self._calculate_luck_and_annual_pillars(
            birth_date, target_year, case_data['gender']
        )
        
        print(f"目标年份: {target_year}")
        print(f"大运柱: {luck_pillar}")
        print(f"流年柱: {annual_pillar}")
        
        # 1958年的动态上下文（包含正确的大运和流年）
        dynamic_context = {
            'year': str(target_year),
            'luck': 'default',
            'luck_pillar': luck_pillar,  # 添加大运柱
            'annual_pillar': annual_pillar  # 添加流年柱
        }
        
        print(f"\n案例信息:")
        print(f"  案例ID: C15 (李嘉诚)")
        print(f"  八字: 丁卯 丁未 庚辰 庚辰")
        print(f"  日主: 庚")
        print(f"  目标年份: 1958")
        print(f"  目标财富: 95")
        
        # 创建引擎并计算
        engine = EngineV88(config=self.config)
        
        # 修改 DomainProcessor 以捕获中间值
        # 我们需要临时修改 _calculate_spacetime_corrector 方法来输出中间值
        original_method = engine.domains._calculate_spacetime_corrector
        trace_data = {}
        
        def traced_corrector(domain, verdict):
            """带追踪的修正器计算"""
            # 调用原始方法
            result = original_method(domain, verdict)
            
            # 获取上下文信息
            context = engine.domains._context if hasattr(engine.domains, '_context') else {}
            
            # 提取中间值
            luck_pillar = context.get('luck_pillar', '')
            annual_pillar = context.get('annual_pillar', '')
            spacetime_enabled = context.get('spacetime_enabled', False)
            exclusion_list = context.get('spacetime_exclusion_list', [])
            spacetime_base = context.get('spacetime_base', 1.0)
            luck_weight = context.get('luck_pillar_weight', 0.6)
            annual_weight = context.get('annual_pillar_weight', 0.4)
            case_id = context.get('case_id', 'Unknown')
            
            # 存储追踪数据
            trace_data[domain] = {
                'spacetime_enabled': spacetime_enabled,
                'case_id': case_id,
                'exclusion_list': exclusion_list,
                'is_excluded': case_id in exclusion_list,
                'luck_pillar': luck_pillar,
                'annual_pillar': annual_pillar,
                'spacetime_base': spacetime_base,
                'luck_weight': luck_weight,
                'annual_weight': annual_weight,
                'final_corrector': result
            }
            
            return result
        
        # 临时替换方法
        engine.domains._calculate_spacetime_corrector = traced_corrector
        
        # 计算能量
        try:
            result = engine.calculate_energy(case_data, dynamic_context)
            
            # 获取静态得分（Level 2 输出，修正前）
            domain_details = result.get('domain_details', {})
            wealth_details = domain_details.get('wealth', {})
            
            # 尝试从详细信息中提取静态得分
            static_score = None
            if 'breakdown' in wealth_details:
                breakdown = wealth_details['breakdown']
                # 查找修正前的得分
                static_score = breakdown.get('Step_3_Final', breakdown.get('Step_4_BeforeCorrector'))
            
            if static_score is None:
                # 如果没有找到，尝试从 SpacetimeCorrector 反推
                spacetime_corrector = wealth_details.get('breakdown', {}).get('SpacetimeCorrector', 1.0)
                final_score = wealth_details.get('score', 0)
                if spacetime_corrector != 0:
                    static_score = final_score / spacetime_corrector
            
            trace_data['wealth']['static_score'] = static_score
            trace_data['wealth']['final_score'] = wealth_details.get('score', 0)
            trace_data['wealth']['spacetime_corrector'] = wealth_details.get('breakdown', {}).get('SpacetimeCorrector', 1.0)
            
        except Exception as e:
            print(f"⚠️  计算失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 恢复原始方法
        engine.domains._calculate_spacetime_corrector = original_method
        
        # 输出追踪结果
        print(f"\n追踪结果 (Wealth 维度):")
        if 'wealth' in trace_data:
            w = trace_data['wealth']
            print(f"  SpacetimeCorrector Enabled: {w.get('spacetime_enabled', False)}")
            print(f"  案例ID: {w.get('case_id', 'Unknown')}")
            print(f"  是否在排除列表: {w.get('is_excluded', False)}")
            print(f"  排除列表: {w.get('exclusion_list', [])}")
            print(f"  大运柱: {w.get('luck_pillar', 'N/A')}")
            print(f"  流年柱: {w.get('annual_pillar', 'N/A')}")
            print(f"  CorrectorBaseFactor: {w.get('spacetime_base', 1.0)}")
            print(f"  LuckPillarWeight: {w.get('luck_weight', 0.6)}")
            print(f"  AnnualPillarWeight: {w.get('annual_weight', 0.4)}")
            print(f"  静态得分 (S_Static): {w.get('static_score', 'N/A')}")
            print(f"  最终修正系数 (Corrector_Final): {w.get('final_corrector', 'N/A')}")
            print(f"  最终得分 (S_Final): {w.get('final_score', 'N/A')}")
        
        return trace_data
    
    def generate_audit_report(self) -> Dict:
        """
        生成完整审计报告
        
        Returns:
            审计报告
        """
        print("\n" + "=" * 80)
        print("V89.0 完整审计报告生成")
        print("=" * 80)
        
        # 1. 检查配置状态
        config_status = self.check_spacetime_config()
        
        # 2. 追踪 C15 计算过程
        trace_result = self.trace_c15_calculation()
        
        report = {
            'spacetime_config': config_status,
            'c15_trace': trace_result,
            'diagnosis': self._diagnose_issues(config_status, trace_result)
        }
        
        return report
    
    def _diagnose_issues(self, config_status: Dict, trace_result: Dict) -> Dict:
        """
        诊断问题
        
        Args:
            config_status: 配置状态
            trace_result: 追踪结果
            
        Returns:
            诊断结果
        """
        issues = []
        
        # 检查是否启用
        if not config_status['enabled']:
            issues.append({
                'severity': 'CRITICAL',
                'issue': 'SpacetimeCorrector 未启用',
                'description': 'Enabled = False，Level 3 算法完全未激活'
            })
        
        # 检查是否在排除列表
        if 'wealth' in trace_result:
            w = trace_result['wealth']
            if w.get('is_excluded', False):
                issues.append({
                    'severity': 'HIGH',
                    'issue': 'C15 在排除列表中',
                    'description': f"C15 在 ExclusionList 中，Level 3 修正被跳过"
                })
        
        # 检查修正系数
        if 'wealth' in trace_result:
            w = trace_result['wealth']
            corrector = w.get('final_corrector', 1.0)
            if corrector == 1.0:
                issues.append({
                    'severity': 'HIGH',
                    'issue': '修正系数为 1.0',
                    'description': '最终修正系数为 1.0，说明 Level 3 修正未生效'
                })
        
        return {
            'issues': issues,
            'summary': f"发现 {len(issues)} 个问题"
        }


def main():
    """主函数"""
    # 配置文件路径
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "parameters.json"
    )
    
    # 检查文件是否存在
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return
    
    # 创建审计器
    auditor = V89Level3Auditor(config_path)
    
    # 生成审计报告
    report = auditor.generate_audit_report()
    
    # 保存结果
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(output_dir, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"V89_TASK135_LEVEL3_AUDIT_REPORT_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n审计报告已保存至: {output_path}")
    
    # 输出诊断摘要
    if 'diagnosis' in report:
        diagnosis = report['diagnosis']
        print(f"\n诊断摘要: {diagnosis.get('summary', 'N/A')}")
        for issue in diagnosis.get('issues', []):
            print(f"  [{issue['severity']}] {issue['issue']}: {issue['description']}")


if __name__ == "__main__":
    main()

