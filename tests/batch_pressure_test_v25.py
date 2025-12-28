"""
[QGA V25.0 Phase 5.2] 1000样本压力测试
大规模逻辑稳健性审计：验证神经矩阵路由系统在处理复杂复合冲突态时的稳定性
"""

import sys
from pathlib import Path
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.pattern_lab import generate_synthetic_bazi, PATTERN_TEMPLATES
from core.subjects.neural_router.execution_kernel import NeuralRouterKernel
from core.subjects.neural_router.feature_vectorizer import FeatureVectorizer
# from core.models.pattern_engine import get_pattern_registry  # 暂时不需要

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/batch_pressure_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 确保logs目录存在
Path('logs').mkdir(exist_ok=True)


class BatchPressureTest:
    """批量压力测试类"""
    
    def __init__(self, sample_count: int = 1000, max_workers: int = 4):
        """
        初始化批量测试
        
        Args:
            sample_count: 测试样本数量
            max_workers: 并发线程数
        """
        self.sample_count = sample_count
        self.max_workers = max_workers
        self.kernel = NeuralRouterKernel()
        self.vectorizer = FeatureVectorizer()
        # self.pattern_registry = get_pattern_registry()  # 暂时不需要
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'outliers': 0,
            'weight_normalization_errors': 0,
            'semantic_healing_errors': 0,
            'api_errors': 0,
            'processing_times': [],
            'token_estimates': []
        }
        
        # 离群样本
        self.outliers = []
        
        logger.info(f"✅ 批量压力测试初始化完成: {sample_count}个样本, {max_workers}个并发线程")
    
    def generate_complex_samples(self) -> List[Dict[str, Any]]:
        """
        生成1000个复杂样本（包含复合冲突态）
        
        Returns:
            样本列表，每个样本包含八字、格局、环境等信息
        """
        logger.info("🚀 开始生成复杂样本...")
        
        samples = []
        pattern_ids = list(PATTERN_TEMPLATES.keys())
        
        # 环境配置（用于创建复合冲突态）
        geo_environments = [
            ("北方/北京", ["近水"]),  # 水旺环境
            ("南方/深圳", []),  # 火旺环境
            ("东方/上海", ["近水"]),  # 木旺环境
            ("西方/西安", []),  # 金旺环境
            ("中央/郑州", []),  # 土旺环境
        ]
        
        # 生成单格局样本（70%）
        single_pattern_count = int(self.sample_count * 0.7)
        for i in range(single_pattern_count):
            pattern_id = random.choice(pattern_ids)
            geo_info, micro_env = random.choice(geo_environments)
            
            try:
                virtual_profile = generate_synthetic_bazi(
                    pattern_id=pattern_id,
                    use_hardcoded=True
                )
                # 添加profile_name字段
                if virtual_profile:
                    virtual_profile['name'] = f"压力测试样本_{i+1}"
                
                if virtual_profile:
                    samples.append({
                        'sample_id': i + 1,
                        'pattern_id': pattern_id,
                        'pattern_name': PATTERN_TEMPLATES[pattern_id].get('name', pattern_id),
                        'virtual_profile': virtual_profile,
                        'geo_info': geo_info,
                        'micro_env': micro_env,
                        'complexity': 'single',
                        'year': random.randint(2020, 2025)
                    })
            except Exception as e:
                logger.warning(f"⚠️ 生成样本 {i+1} 失败: {e}")
        
        # 生成复合冲突态样本（30%）
        dual_pattern_count = self.sample_count - len(samples)
        conflict_patterns = [
            ('SHANG_GUAN_JIAN_GUAN', 'YANG_REN_JIA_SHA'),  # 伤官见官 + 羊刃架杀
            ('XIAO_SHEN_DUO_SHI', 'JIAN_LU_YUE_JIE'),  # 枭神夺食 + 建禄月劫
            ('HUA_HUO_GE', 'GUAN_YIN_XIANG_SHENG'),  # 化火格 + 官印相生
            ('CONG_ER_GE', 'XIAO_SHEN_DUO_SHI'),  # 从儿格 + 枭神夺食
        ]
        
        for i in range(dual_pattern_count):
            pattern1_id, pattern2_id = random.choice(conflict_patterns)
            geo_info, micro_env = random.choice(geo_environments)
            
            try:
                # 使用第一个格局生成基础八字
                virtual_profile = generate_synthetic_bazi(
                    pattern_id=pattern1_id,
                    use_hardcoded=True
                )
                # 添加profile_name字段
                if virtual_profile:
                    virtual_profile['name'] = f"复合冲突样本_{len(samples)+1}"
                
                if virtual_profile:
                    samples.append({
                        'sample_id': len(samples) + 1,
                        'pattern_id': f"{pattern1_id}+{pattern2_id}",
                        'pattern_name': f"{PATTERN_TEMPLATES[pattern1_id].get('name', pattern1_id)} + {PATTERN_TEMPLATES[pattern2_id].get('name', pattern2_id)}",
                        'virtual_profile': virtual_profile,
                        'geo_info': geo_info,
                        'micro_env': micro_env,
                        'complexity': 'dual',
                        'year': random.randint(2020, 2025),
                        'secondary_pattern': pattern2_id
                    })
            except Exception as e:
                logger.warning(f"⚠️ 生成复合样本 {len(samples)+1} 失败: {e}")
        
        logger.info(f"✅ 样本生成完成: {len(samples)}个样本（单格局: {single_pattern_count}, 复合: {dual_pattern_count}）")
        return samples
    
    def process_single_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个样本
        
        Args:
            sample: 样本数据
            
        Returns:
            处理结果
        """
        sample_id = sample['sample_id']
        start_time = time.time()
        
        try:
            virtual_profile = sample['virtual_profile']
            
            # 提取八字信息
            chart_pillars = None
            
            # 方法1: 从hardcoded_pillars提取（优先）
            hardcoded = virtual_profile.get('_hardcoded_pillars', {})
            if hardcoded:
                chart_pillars = [
                    (hardcoded['year'][0], hardcoded['year'][1]),
                    (hardcoded['month'][0], hardcoded['month'][1]),
                    (hardcoded['day'][0], hardcoded['day'][1]),
                    (hardcoded['hour'][0], hardcoded['hour'][1])
                ]
            
            # 方法2: 从bazi_data提取（备用）
            if not chart_pillars:
                bazi_data = virtual_profile.get('bazi_data', {})
                if bazi_data and 'year' in bazi_data:
                    # bazi_data格式: {"year": "戊戌", "month": "己未", "day": "丙午", "hour": "戊戌"}
                    chart_pillars = [
                        (bazi_data['year'][0], bazi_data['year'][1]),
                        (bazi_data['month'][0], bazi_data['month'][1]),
                        (bazi_data['day'][0], bazi_data['day'][1]),
                        (bazi_data['hour'][0], bazi_data['hour'][1])
                    ]
            
            if not chart_pillars:
                raise ValueError("无法提取八字信息")
            
            day_master = virtual_profile.get('_day_master', '')
            if not day_master:
                raise ValueError("无法提取日主")
            
            # 构建激活格局列表
            active_patterns = [{
                "id": sample['pattern_id'].split('+')[0],  # 主格局
                "name": sample['pattern_name'].split(' + ')[0],
                "weight": 0.8,
                "base_strength": 0.75
            }]
            
            # 如果是复合格局，添加第二个格局
            if sample.get('complexity') == 'dual' and 'secondary_pattern' in sample:
                active_patterns.append({
                    "id": sample['secondary_pattern'],
                    "name": PATTERN_TEMPLATES[sample['secondary_pattern']].get('name', sample['secondary_pattern']),
                    "weight": 0.6,
                    "base_strength": 0.7
                })
            
            # 先使用FeatureVectorizer提取特征向量
            feature_vector = self.vectorizer.vectorize_bazi(
                chart=chart_pillars,
                day_master=day_master,
                luck_pillar=None,
                year_pillar=None,
                geo_info=sample['geo_info'],
                micro_env=sample['micro_env'],
                synthesized_field={
                    "friction_index": random.randint(20, 80),  # 随机摩擦指数
                    "micro_env": sample['micro_env']
                }
            )
            
            # 从特征向量中提取五行场强作为force_vectors
            force_vectors = feature_vector.get("elemental_fields_dict", {})
            
            # 执行神经矩阵路由
            result = self.kernel.process_bazi_profile(
                active_patterns=active_patterns,
                synthesized_field={
                    "friction_index": random.randint(20, 80),  # 随机摩擦指数
                    "micro_env": sample['micro_env']
                },
                profile_name=f"样本_{sample_id}",
                day_master=day_master,
                force_vectors=force_vectors,  # 使用提取的特征向量
                year=sample['year'],
                luck_pillar=None,
                year_pillar=None,
                geo_info=sample['geo_info']
            )
            
            processing_time = time.time() - start_time
            
            # 验证结果
            validation_result = self._validate_result(result, sample)
            
            return {
                'sample_id': sample_id,
                'success': True,
                'result': result,
                'validation': validation_result,
                'processing_time': processing_time,
                'error': None
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ 样本 {sample_id} 处理失败: {e}", exc_info=True)
            
            return {
                'sample_id': sample_id,
                'success': False,
                'result': None,
                'validation': None,
                'processing_time': processing_time,
                'error': str(e)
            }
    
    def _validate_result(self, result: Dict[str, Any], sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证处理结果
        
        Args:
            result: 处理结果
            sample: 原始样本
            
        Returns:
            验证结果
        """
        validation = {
            'weight_normalization_ok': False,
            'semantic_healing_ok': False,
            'api_ok': False,
            'is_outlier': False,
            'issues': []
        }
        
        # 1. 验证权重归一化
        logic_collapse = result.get('logic_collapse', {})
        if logic_collapse:
            total_weight = sum(logic_collapse.values())
            if 0.95 <= total_weight <= 1.05:
                validation['weight_normalization_ok'] = True
            else:
                validation['issues'].append(f"权重归一化异常: {total_weight:.4f}")
                self.stats['weight_normalization_errors'] += 1
        
        # 2. 验证语义自愈（稳定性 < 0.2 时应识别为崩态）
        energy_state = result.get('energy_state_report', {})
        if energy_state:
            system_stability = energy_state.get('system_stability', 1.0)
            critical_state = energy_state.get('critical_state', '')
            
            if system_stability < 0.2:
                if '崩态' in critical_state or '不稳定' in critical_state or '冲突' in critical_state:
                    validation['semantic_healing_ok'] = True
                else:
                    validation['issues'].append(f"语义自愈失败: 稳定性{system_stability:.3f}但未识别为崩态")
                    self.stats['semantic_healing_errors'] += 1
            else:
                validation['semantic_healing_ok'] = True  # 非崩态，无需验证
        
        # 3. 验证API健壮性（检查是否有错误）
        if 'error' in result:
            validation['issues'].append(f"API错误: {result['error']}")
            self.stats['api_errors'] += 1
        else:
            validation['api_ok'] = True
        
        # 4. 判断是否为离群样本
        if validation['issues'] or not result.get('persona') or not result.get('logic_collapse'):
            validation['is_outlier'] = True
            self.stats['outliers'] += 1
        
        return validation
    
    def run_batch_test(self) -> Dict[str, Any]:
        """
        运行批量测试
        
        Returns:
            测试结果摘要
        """
        logger.info("=" * 80)
        logger.info("🚀 启动1000样本压力测试")
        logger.info("=" * 80)
        
        # 1. 生成样本
        samples = self.generate_complex_samples()
        self.stats['total'] = len(samples)
        
        # 2. 并发处理
        logger.info(f"📊 开始并发处理 {len(samples)} 个样本...")
        start_time = time.time()
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_sample = {
                executor.submit(self.process_single_sample, sample): sample
                for sample in samples
            }
            
            completed = 0
            for future in as_completed(future_to_sample):
                completed += 1
                if completed % 100 == 0:
                    logger.info(f"📈 进度: {completed}/{len(samples)} ({completed*100/len(samples):.1f}%)")
                
                result = future.result()
                results.append(result)
                
                # 更新统计
                if result['success']:
                    self.stats['success'] += 1
                    self.stats['processing_times'].append(result['processing_time'])
                    
                    # 估算Token消耗（简化：基于Prompt长度）
                    if result['result'] and 'neural_router_metadata' in result['result']:
                        prompt_length = result['result']['neural_router_metadata'].get('inline_prompt_length', 0)
                        # 粗略估算：1字符 ≈ 0.25 token
                        token_estimate = prompt_length * 0.25
                        self.stats['token_estimates'].append(token_estimate)
                else:
                    self.stats['failed'] += 1
                    self.stats['api_errors'] += 1
                
                # 收集离群样本
                if result['validation'] and result['validation'].get('is_outlier'):
                    self.outliers.append({
                        'sample_id': result['sample_id'],
                        'sample': future_to_sample[future],
                        'result': result['result'],
                        'validation': result['validation']
                    })
        
        total_time = time.time() - start_time
        
        # 3. 生成报告
        report = self._generate_report(results, total_time)
        
        # 4. 保存离群样本
        self._save_outliers()
        
        logger.info("=" * 80)
        logger.info("✅ 批量压力测试完成")
        logger.info("=" * 80)
        
        return report
    
    def _generate_report(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """生成测试报告"""
        
        avg_processing_time = sum(self.stats['processing_times']) / len(self.stats['processing_times']) if self.stats['processing_times'] else 0
        avg_token_estimate = sum(self.stats['token_estimates']) / len(self.stats['token_estimates']) if self.stats['token_estimates'] else 0
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_samples': self.stats['total'],
                'success_count': self.stats['success'],
                'failed_count': self.stats['failed'],
                'success_rate': self.stats['success'] / self.stats['total'] * 100 if self.stats['total'] > 0 else 0,
                'outlier_count': self.stats['outliers'],
                'outlier_rate': self.stats['outliers'] / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
            },
            'validation_metrics': {
                'weight_normalization_errors': self.stats['weight_normalization_errors'],
                'semantic_healing_errors': self.stats['semantic_healing_errors'],
                'api_errors': self.stats['api_errors']
            },
            'performance_metrics': {
                'total_time_seconds': total_time,
                'avg_processing_time_seconds': avg_processing_time,
                'throughput_samples_per_second': self.stats['total'] / total_time if total_time > 0 else 0,
                'avg_token_estimate': avg_token_estimate,
                'total_token_estimate': sum(self.stats['token_estimates'])
            },
            'outliers': len(self.outliers)
        }
        
        # 打印报告
        print("\n" + "=" * 80)
        print("📊 批量压力测试报告")
        print("=" * 80)
        print(f"\n【测试摘要】")
        print(f"  总样本数: {report['summary']['total_samples']}")
        print(f"  成功: {report['summary']['success_count']} ({report['summary']['success_rate']:.2f}%)")
        print(f"  失败: {report['summary']['failed_count']}")
        print(f"  离群样本: {report['summary']['outlier_count']} ({report['summary']['outlier_rate']:.2f}%)")
        
        print(f"\n【验证指标】")
        print(f"  权重归一化错误: {report['validation_metrics']['weight_normalization_errors']}")
        print(f"  语义自愈错误: {report['validation_metrics']['semantic_healing_errors']}")
        print(f"  API错误: {report['validation_metrics']['api_errors']}")
        
        print(f"\n【性能指标】")
        print(f"  总耗时: {report['performance_metrics']['total_time_seconds']:.2f}秒")
        print(f"  平均处理时间: {report['performance_metrics']['avg_processing_time_seconds']:.3f}秒/样本")
        print(f"  吞吐量: {report['performance_metrics']['throughput_samples_per_second']:.2f}样本/秒")
        print(f"  平均Token估算: {report['performance_metrics']['avg_token_estimate']:.1f}")
        print(f"  总Token估算: {report['performance_metrics']['total_token_estimate']:.0f}")
        
        print("\n" + "=" * 80)
        
        return report
    
    def _save_outliers(self):
        """保存离群样本"""
        if not self.outliers:
            logger.info("✅ 无离群样本")
            return
        
        outliers_file = Path('logs/outliers_v25.json')
        outliers_data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(self.outliers),
            'outliers': self.outliers
        }
        
        with open(outliers_file, 'w', encoding='utf-8') as f:
            json.dump(outliers_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 离群样本已保存: {outliers_file} ({len(self.outliers)}个)")


def main():
    """主函数"""
    print("🧬 QGA V25.0 Phase 5.2: 1000样本压力测试")
    print("   此测试将验证神经矩阵路由系统在大规模复杂样本下的稳定性")
    print("")
    
    # 创建测试实例
    tester = BatchPressureTest(sample_count=1000, max_workers=4)
    
    # 运行测试
    report = tester.run_batch_test()
    
    # 保存报告
    report_file = Path('logs/batch_pressure_test_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 测试报告已保存: {report_file}")
    print("\n🎉 Phase 5.2 压力测试完成！")


if __name__ == "__main__":
    main()

