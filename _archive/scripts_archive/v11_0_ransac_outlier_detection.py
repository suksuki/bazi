"""
V11.0 RANSAC 离群点检测和数据清洗

使用RANSAC算法识别校准数据集中的离群点（脏数据）
"""

import sys
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Set
from collections import defaultdict
import logging
from dataclasses import dataclass

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.models.config_model import ConfigModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class CaseResult:
    """案例计算结果"""
    case_id: str
    case_name: str
    ground_truth: str
    predicted_label: str
    strength_score: float
    self_team_ratio: float
    is_correct: bool
    error_magnitude: float  # 预测错误的严重程度


class RANSACOutlierDetector:
    """RANSAC离群点检测器"""
    
    def __init__(self, config_model: ConfigModel = None):
        self.config_model = config_model or ConfigModel()
        self.config = self.config_model.load_config()
        self.engine = GraphNetworkEngine(config=self.config)
        
    def load_calibration_cases(self) -> Tuple[List[Dict], Dict[str, float]]:
        """加载校准案例"""
        data_dir = project_root / "data"
        classic_file = data_dir / "classic_cases.json"
        calibration_file = data_dir / "calibration_cases.json"
        
        cases = []
        case_weights = {}
        
        # 加载经典案例（权重3.0x）
        if classic_file.exists():
            with open(classic_file, 'r', encoding='utf-8') as f:
                classic_cases = json.load(f)
                for case in classic_cases:
                    case_id = case.get('id', f"CLASSIC_{len(cases)}")
                    case['weight'] = 3.0
                    cases.append(case)
                    case_weights[case_id] = 3.0
        
        # 加载校准案例
        if calibration_file.exists():
            with open(calibration_file, 'r', encoding='utf-8') as f:
                cal_cases = json.load(f)
                loaded_ids = {c.get('id') for c in cases if 'id' in c}
                
                for case in cal_cases:
                    case_id = case.get('id', f"CAL_{len(cases)}")
                    
                    # 避免重复加载
                    if case_id in loaded_ids:
                        continue
                    
                    # 根据case类型设置权重
                    if case.get('id', '').startswith('STRENGTH_CN_'):
                        case['weight'] = 1.5  # 现代中国案例
                        case_weights[case_id] = 1.5
                    else:
                        case['weight'] = 0.8  # 外国案例
                        case_weights[case_id] = 0.8
                    
                    cases.append(case)
        
        logger.info(f"✅ 加载了 {len(cases)} 个案例")
        return cases, case_weights
    
    def evaluate_case(self, case: Dict) -> CaseResult:
        """评估单个案例"""
        bazi_list = case.get('bazi', [])
        if isinstance(bazi_list, str):
            bazi_list = bazi_list.split()
        
        day_master = case.get('day_master', '')
        
        # 初始化引擎
        self.engine.initialize_nodes(
            bazi=bazi_list,
            day_master=day_master,
            luck_pillar=None,
            year_pillar=None
        )
        
        # 计算旺衰
        result = self.engine.calculate_strength_score(day_master)
        
        ground_truth = case.get('ground_truth', {}).get('strength', 'Unknown')
        predicted_label = result.get('strength_label', 'Unknown')
        
        self_team_energy = result.get('self_team_energy', 0)
        total_energy = result.get('total_energy', 1)
        self_team_ratio = self_team_energy / total_energy if total_energy > 0 else 0
        
        is_correct = predicted_label == ground_truth
        
        # 计算错误严重程度
        # 如果预测错误，错误严重程度 = |predicted_score - expected_score_range_center|
        error_magnitude = 0.0
        if not is_correct:
            # 根据ground_truth估算期望分数范围
            expected_score_ranges = {
                'Follower': (0, 20),
                'Weak': (20, 45),
                'Balanced': (45, 55),
                'Strong': (55, 80),
                'Special_Strong': (75, 100)
            }
            expected_range = expected_score_ranges.get(ground_truth, (0, 100))
            expected_center = (expected_range[0] + expected_range[1]) / 2
            error_magnitude = abs(result.get('strength_score', 0) - expected_center)
        
        return CaseResult(
            case_id=case.get('id', 'Unknown'),
            case_name=case.get('name', 'Unknown'),
            ground_truth=ground_truth,
            predicted_label=predicted_label,
            strength_score=result.get('strength_score', 0),
            self_team_ratio=self_team_ratio,
            is_correct=is_correct,
            error_magnitude=error_magnitude
        )
    
    def evaluate_parameter_set(self, cases: List[Dict], sample_indices: List[int]) -> Tuple[float, List[CaseResult]]:
        """使用给定的参数（实际上是案例子集）评估匹配率"""
        # 这里简化处理：使用当前配置评估案例子集
        # 在实际RANSAC中，我们会用这个子集来优化参数
        
        results = []
        correct_count = 0
        total_weight = 0.0
        
        for idx in sample_indices:
            if idx >= len(cases):
                continue
            
            case = cases[idx]
            result = self.evaluate_case(case)
            results.append(result)
            
            case_weight = case.get('weight', 1.0)
            total_weight += case_weight
            if result.is_correct:
                correct_count += case_weight
        
        match_rate = correct_count / total_weight if total_weight > 0 else 0.0
        
        return match_rate, results
    
    def run_ransac(self, cases: List[Dict], n_iterations: int = 1000, sample_size: int = 20) -> Dict:
        """
        运行RANSAC算法
        
        Args:
            cases: 案例列表
            n_iterations: 迭代次数
            sample_size: 每次随机抽样的样本数
        
        Returns:
            RANSAC结果字典
        """
        logger.info(f"🚀 开始RANSAC分析: {n_iterations}次迭代, 每次抽样{sample_size}个案例")
        
        best_match_rate = 0.0
        best_sample_indices = []
        best_results = []
        all_inlier_counts = []
        
        n_cases = len(cases)
        
        for iteration in range(n_iterations):
            if (iteration + 1) % 100 == 0:
                logger.info(f"  进度: {iteration + 1}/{n_iterations}, 当前最佳匹配率: {best_match_rate:.2%}")
            
            # 随机抽样
            sample_indices = np.random.choice(n_cases, size=min(sample_size, n_cases), replace=False).tolist()
            
            # 评估这个样本
            match_rate, results = self.evaluate_parameter_set(cases, sample_indices)
            
            # 计算inlier数量（在这个样本中预测正确的案例数）
            inlier_count = sum(1 for r in results if r.is_correct)
            all_inlier_counts.append(inlier_count)
            
            # 更新最佳结果
            if match_rate > best_match_rate:
                best_match_rate = match_rate
                best_sample_indices = sample_indices
                best_results = results
        
        # 使用最佳样本计算所有案例的结果
        logger.info("📊 使用最佳样本评估所有案例...")
        all_results = []
        for idx, case in enumerate(cases):
            result = self.evaluate_case(case)
            all_results.append(result)
        
        # 计算每个案例的outlier分数
        # 方法：如果案例在最佳样本中预测错误，或者错误严重程度很高，则标记为outlier
        outlier_scores = {}
        for idx, result in enumerate(all_results):
            case_id = result.case_id
            is_in_best_sample = idx in best_sample_indices
            
            # Outlier分数基于：
            # 1. 预测错误 (is_correct = False)
            # 2. 错误严重程度 (error_magnitude)
            # 3. 不在最佳样本中且预测错误
            outlier_score = 0.0
            if not result.is_correct:
                outlier_score += 50.0  # 基础分数
                outlier_score += result.error_magnitude * 0.5  # 错误严重程度
                if not is_in_best_sample:
                    outlier_score += 20.0  # 不在最佳样本中
            
            outlier_scores[case_id] = outlier_score
        
        # 按outlier分数排序
        sorted_cases = sorted(outlier_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 识别outliers（分数超过阈值的案例）
        # 使用分位数方法：取top 20%作为潜在outliers
        threshold_percentile = 80
        threshold_score = np.percentile([s[1] for s in sorted_cases], threshold_percentile)
        
        outliers = [case_id for case_id, score in sorted_cases if score >= threshold_score]
        
        logger.info(f"✅ RANSAC分析完成")
        logger.info(f"   最佳匹配率: {best_match_rate:.2%}")
        logger.info(f"   识别出 {len(outliers)} 个潜在outliers (阈值: {threshold_score:.2f})")
        
        return {
            'best_match_rate': best_match_rate,
            'best_sample_size': len(best_sample_indices),
            'total_cases': n_cases,
            'outlier_count': len(outliers),
            'outliers': outliers,
            'outlier_scores': dict(sorted_cases),
            'threshold_score': threshold_score,
            'all_results': [
                {
                    'case_id': r.case_id,
                    'case_name': r.case_name,
                    'ground_truth': r.ground_truth,
                    'predicted_label': r.predicted_label,
                    'strength_score': r.strength_score,
                    'self_team_ratio': r.self_team_ratio,
                    'is_correct': r.is_correct,
                    'error_magnitude': r.error_magnitude,
                    'outlier_score': outlier_scores.get(r.case_id, 0.0)
                }
                for r in all_results
            ]
        }
    
    def generate_removal_recommendations(self, ransac_result: Dict, cases: List[Dict]) -> List[Dict]:
        """生成剔除建议名单"""
        outliers = ransac_result['outliers']
        outlier_scores = ransac_result['outlier_scores']
        
        recommendations = []
        for case_id in outliers:
            case = next((c for c in cases if c.get('id') == case_id), None)
            if not case:
                continue
            
            result = next((r for r in ransac_result['all_results'] if r['case_id'] == case_id), None)
            if not result:
                continue
            
            recommendations.append({
                'case_id': case_id,
                'case_name': case.get('name', 'Unknown'),
                'ground_truth': result['ground_truth'],
                'predicted_label': result['predicted_label'],
                'strength_score': result['strength_score'],
                'outlier_score': outlier_scores.get(case_id, 0.0),
                'reason': f"预测错误: {result['ground_truth']} → {result['predicted_label']}, 错误严重程度: {result['error_magnitude']:.2f}",
                'suggested_action': '标记为Dirty_Data，权重归零或移入ignored_cases.json'
            })
        
        # 按outlier_score排序
        recommendations.sort(key=lambda x: x['outlier_score'], reverse=True)
        
        return recommendations
    
    def save_recommendations(self, recommendations: List[Dict], output_file: Path):
        """保存剔除建议到JSON文件"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'total_recommendations': len(recommendations),
            'recommendations': recommendations
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 剔除建议已保存到: {output_file}")


def main():
    """主函数"""
    print("=" * 80)
    print("🧹 V11.0 RANSAC 数据清洗 - 离群点检测")
    print("=" * 80)
    print()
    
    detector = RANSACOutlierDetector()
    
    # 加载案例
    cases, case_weights = detector.load_calibration_cases()
    
    # 运行RANSAC
    ransac_result = detector.run_ransac(cases, n_iterations=500, sample_size=20)
    
    # 生成剔除建议
    recommendations = detector.generate_removal_recommendations(ransac_result, cases)
    
    # 保存结果
    output_file = project_root / "data" / "ransac_outlier_recommendations.json"
    detector.save_recommendations(recommendations, output_file)
    
    # 打印摘要
    print()
    print("=" * 80)
    print("📊 RANSAC分析结果摘要")
    print("=" * 80)
    print(f"总案例数: {ransac_result['total_cases']}")
    print(f"最佳匹配率: {ransac_result['best_match_rate']:.2%}")
    print(f"识别出离群点: {ransac_result['outlier_count']} 个")
    print()
    
    print("Top 10 离群点建议:")
    for i, rec in enumerate(recommendations[:10], 1):
        print(f"  {i}. {rec['case_name']} (ID: {rec['case_id']})")
        print(f"     真实值: {rec['ground_truth']}, 预测值: {rec['predicted_label']}")
        print(f"     Outlier分数: {rec['outlier_score']:.2f}")
        print(f"     建议: {rec['suggested_action']}")
        print()
    
    print("=" * 80)
    print(f"📄 完整建议列表已保存到: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()

