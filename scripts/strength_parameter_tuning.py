#!/usr/bin/env python3
"""
旺衰判定参数调优脚本
====================

功能：
1. 参数敏感度分析
2. 自动化参数搜索
3. 回归检查
4. 生成调优报告

使用方法：
    python3 scripts/strength_parameter_tuning.py --mode sensitivity  # 敏感度分析（自动生成可视化图表）
    python3 scripts/strength_parameter_tuning.py --mode optimize     # 参数优化（包含从格阈值调优）
    python3 scripts/strength_parameter_tuning.py --mode test         # 测试当前参数

[V10.0 核心分析师建议] 新增功能：
    1. 从格阈值 (follower_threshold) 调优：解决"乔丹从格"误判问题
    2. 参数鲁棒性可视化：生成响应曲线图，识别平顶区（鲁棒性好的参数）
    3. 自动从格阈值网格搜索：optimize模式自动包含follower_threshold (0.1~0.2)调优
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import copy
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.quantum_lab_controller import QuantumLabController
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.engine_graph import GraphNetworkEngine


class StrengthParameterTuner:
    """旺衰判定参数调优器（V10.0 结构感知调优）"""
    
    def __init__(self):
        self.controller = QuantumLabController()
        self.cases, self.case_weights = self._load_calibration_cases()
        self.base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    def _load_calibration_cases(self) -> Tuple[List[Dict], Dict[str, float]]:
        """
        加载校准案例（带权重系统）
        
        Returns:
            (cases_list, weights_dict) 元组
        """
        cases_path = project_root / "data" / "calibration_cases.json"
        classic_cases_path = project_root / "data" / "classic_cases.json"
        
        all_cases = []
        case_weights = {}
        
        # 1. 加载经典案例（锚定案例，权重3.0x）
        if classic_cases_path.exists():
            with open(classic_cases_path, 'r', encoding='utf-8') as f:
                classic_data = json.load(f)
            for case in classic_data:
                case_id = case.get('id', '')
                weight = case.get('weight', 3.0)  # 默认权重3.0
                case_weights[case_id] = weight
                all_cases.append(case)
            print(f"✅ 加载了 {len(classic_data)} 个经典案例（权重3.0x）")
        else:
            print(f"⚠️  未找到经典案例文件: {classic_cases_path}")
        
        # 2. 加载校准案例
        if cases_path.exists():
            with open(cases_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 只加载旺衰相关的案例
            strength_cases = [
                case for case in data 
                if case.get('target_focus') == 'STRENGTH' and case.get('ground_truth', {}).get('strength')
            ]
            
            # 分配权重（根据类别）
            classic_case_ids = {c.get('id') for c in all_cases}  # 已加载的经典案例ID集合
            # 建立经典案例名称到ID的映射（用于识别重复案例）
            classic_names = {c.get('name') for c in all_cases if c.get('name')}
            
            for case in strength_cases:
                case_id = case.get('id', '')
                case_name = case.get('name', '')
                geo_country = case.get('geo_country', 'Unknown')
                
                # 如果ID或名称已在经典案例中，跳过（避免重复）
                if case_id in classic_case_ids or case_name in classic_names:
                    continue
                
                # 根据国家/地区分配权重
                if geo_country == 'China':
                    # 现代中国案例：权重1.5x
                    weight = 1.5
                elif geo_country != 'Unknown':
                    # 外国人案例：权重0.8x
                    weight = 0.8
                else:
                    # 未知：默认权重1.0x
                    weight = 1.0
                
                case_weights[case_id] = weight
                all_cases.append(case)
            
            print(f"✅ 加载了 {len(strength_cases)} 个校准案例")
        
        # 统计权重分布
        weight_dist = {}
        for case_id, weight in case_weights.items():
            weight_key = f"{weight}x"
            weight_dist[weight_key] = weight_dist.get(weight_key, 0) + 1
        
        print(f"📊 权重分布: {weight_dist}")
        
        return all_cases, case_weights
    
    def evaluate_parameter_set(self, config: Dict, use_bayesian_penalty: bool = True) -> Dict:
        """
        评估参数配置的性能（V10.0 结构感知 + 贝叶斯正则化）
        
        Args:
            config: 参数配置
            use_bayesian_penalty: 是否使用贝叶斯正则化惩罚
        
        Returns:
            {
                'match_rate': 加权匹配率,
                'total_cases': 总案例数,
                'matched_cases': 匹配案例数,
                'weighted_score': 加权得分,
                'penalty': 贝叶斯惩罚项,
                'case_results': [...]
            }
        """
        # 更新Controller配置
        self.controller.update_config(config)
        
        total_weight = 0.0
        matched_weight = 0.0
        case_results = []
        
        for case in self.cases:
            case_id = case.get('id', 'Unknown')
            bazi_list = case.get('bazi', ['', '', '', ''])
            day_master = case.get('day_master')
            gt_strength = case.get('ground_truth', {}).get('strength', 'Unknown')
            
            if not day_master or not all(bazi_list):
                continue
            
            # 获取案例权重
            weight = self.case_weights.get(case_id, 1.0)
            
            try:
                # 评估旺衰
                ws_label, ws_score = self.controller.evaluate_wang_shuai(day_master, bazi_list)
                
                # 匹配检查
                is_match = self._check_match(ws_label, gt_strength)
                if is_match:
                    matched_weight += weight
                total_weight += weight
                
                case_results.append({
                    'id': case_id,
                    'name': case.get('name', 'Unknown'),
                    'predicted': ws_label,
                    'ground_truth': gt_strength,
                    'score': ws_score,
                    'match': is_match,
                    'weight': weight
                })
            except Exception as e:
                print(f"⚠️ 案例 {case_id} 评估失败: {e}")
                continue
        
        # 计算加权匹配率
        weighted_match_rate = (matched_weight / total_weight * 100) if total_weight > 0 else 0.0
        
        # [V10.0 核心分析师建议] 贝叶斯正则化惩罚
        penalty = 0.0
        if use_bayesian_penalty:
            penalty = self._calculate_bayesian_penalty(config)
        
        # 最终得分 = 加权匹配率 - 惩罚项
        final_score = weighted_match_rate - penalty
        
        return {
            'match_rate': weighted_match_rate,  # 加权匹配率
            'weighted_score': final_score,      # 最终得分（含惩罚）
            'penalty': penalty,                 # 贝叶斯惩罚项
            'total_cases': len(case_results),
            'matched_cases': sum(1 for r in case_results if r['match']),
            'total_weight': total_weight,
            'matched_weight': matched_weight,
            'case_results': case_results
        }
    
    def _calculate_bayesian_penalty(self, config: Dict) -> float:
        """
        计算贝叶斯正则化惩罚项
        
        惩罚不合理参数组合（如 Hour_Weight > Month_Weight）
        
        Args:
            config: 参数配置
            
        Returns:
            惩罚值（会从match_rate中减去）
        """
        penalty = 0.0
        lambda_reg = 5.0  # 正则化系数（核心分析师建议：5.0）
        
        # 检查1: pillarWeights - 月令权重应该大于时柱权重
        physics = config.get('physics', {})
        pillar_weights = physics.get('pillarWeights', {})
        month_weight = pillar_weights.get('month', 1.2)
        hour_weight = pillar_weights.get('hour', 0.9)
        
        if hour_weight > month_weight:
            # 惩罚：如果时柱权重大于月令权重，给予惩罚
            penalty += lambda_reg * (hour_weight - month_weight) * 10.0
            # 例如：如果 hour_weight=1.3, month_weight=1.2，惩罚 = 5.0 * 0.1 * 10 = 5.0
        
        # 检查2: structure - 通根权重应该在合理范围内
        structure = config.get('structure', {})
        rooting_weight = structure.get('rootingWeight', 1.0)
        same_pillar_bonus = structure.get('samePillarBonus', 1.2)
        
        # 通根权重不应该过大（超过3.0被认为不合理）
        if rooting_weight > 3.0:
            penalty += lambda_reg * (rooting_weight - 3.0) * 2.0
        
        # 同柱加成不应该过大（超过2.5被认为不合理）
        if same_pillar_bonus > 2.5:
            penalty += lambda_reg * (same_pillar_bonus - 2.5) * 2.0
        
        return penalty
    
    def _check_match(self, predicted: str, ground_truth: str) -> bool:
        """检查预测结果是否与真实值匹配"""
        if ground_truth == "Unknown":
            return False
        
        # 精确匹配
        if predicted == ground_truth:
            return True
        
        # 包含匹配（处理"Special_Strong" vs "Strong"等情况）
        if ground_truth in predicted or predicted in ground_truth:
            return True
        
        # Follower特殊处理
        if "Follower" in ground_truth and "Follower" in predicted:
            return True
        
        return False
    
    def sensitivity_analysis(self, param_path: str, param_range: Tuple[float, float], steps: int = 10, save_plot: bool = True) -> List[Dict]:
        """
        参数敏感度分析（增强版：支持可视化）
        
        Args:
            param_path: 参数路径，如 'strength.energy_threshold_center'
            param_range: 参数范围 (min, max)
            steps: 扫描步数
            save_plot: 是否保存可视化图表
        
        Returns:
            敏感度分析结果列表
        """
        print(f"\n🔍 开始敏感度分析: {param_path}")
        print(f"   范围: {param_range[0]} ~ {param_range[1]}, 步数: {steps}")
        
        results = []
        min_val, max_val = param_range
        step_size = (max_val - min_val) / steps
        
        for i in range(steps + 1):
            value = min_val + i * step_size
            
            # 创建测试配置
            test_config = copy.deepcopy(self.base_config)
            self._set_nested_param(test_config, param_path, value)
            
            # 评估
            eval_result = self.evaluate_parameter_set(test_config)
            
            results.append({
                'param_value': value,
                'match_rate': eval_result['match_rate'],
                'weighted_score': eval_result.get('weighted_score', eval_result['match_rate']),
                'penalty': eval_result.get('penalty', 0.0),
                'matched_cases': eval_result['matched_cases'],
                'total_cases': eval_result['total_cases']
            })
            
            # 显示加权匹配率和最终得分
            match_rate = eval_result['match_rate']
            final_score = eval_result.get('weighted_score', match_rate)
            penalty = eval_result.get('penalty', 0.0)
            if penalty > 0:
                print(f"   {value:.3f}: 加权匹配率 {match_rate:.1f}% (得分: {final_score:.1f}, 惩罚: -{penalty:.2f})")
            else:
                print(f"   {value:.3f}: 加权匹配率 {match_rate:.1f}% ({eval_result['matched_cases']}/{eval_result['total_cases']})")
        
        # [V10.0 核心分析师建议] 生成参数-匹配率响应曲线图
        if save_plot:
            self._plot_sensitivity_curve(param_path, results)
        
        return results
    
    def _plot_sensitivity_curve(self, param_path: str, results: List[Dict]):
        """
        绘制参数-匹配率响应曲线（判断参数鲁棒性）
        
        Args:
            param_path: 参数路径
            results: 敏感度分析结果
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端
            import matplotlib.pyplot as plt
            import numpy as np
            
            param_values = [r['param_value'] for r in results]
            match_rates = [r['match_rate'] for r in results]
            
            plt.figure(figsize=(10, 6))
            plt.plot(param_values, match_rates, 'b-o', linewidth=2, markersize=6)
            plt.xlabel(f'参数值: {param_path}', fontsize=12)
            plt.ylabel('匹配率 (%)', fontsize=12)
            plt.title(f'参数敏感度分析: {param_path}', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            
            # 找出最优值和最高匹配率
            best_idx = np.argmax(match_rates)
            best_param = param_values[best_idx]
            best_rate = match_rates[best_idx]
            best_result = results[best_idx]
            penalty_at_best = best_result.get('penalty', 0.0)
            match_rate_at_best = best_result.get('match_rate', best_rate)
            
            # 标记最优点
            if penalty_at_best > 0:
                label = f'最优值: {best_param:.3f} (得分: {best_rate:.1f}%, 匹配率: {match_rate_at_best:.1f}%, 惩罚: -{penalty_at_best:.2f})'
            else:
                label = f'最优值: {best_param:.3f} (匹配率: {best_rate:.1f}%)'
            plt.plot(best_param, best_rate, 'r*', markersize=20, label=label)
            plt.legend(fontsize=10)
            
            # 添加平顶区检测提示
            # 计算匹配率的标准差，如果标准差小，说明曲线较平缓（鲁棒性好）
            if len(match_rates) > 5:
                std_dev = np.std(match_rates)
                if std_dev < 5.0:  # 标准差小于5%，说明曲线较平缓
                    plt.text(0.02, 0.98, f'✅ 参数鲁棒性好（标准差: {std_dev:.2f}%）', 
                            transform=plt.gca().transAxes, fontsize=10, 
                            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
                elif std_dev > 10.0:  # 标准差大于10%，说明曲线较陡峭
                    plt.text(0.02, 0.98, f'⚠️ 参数敏感度高（标准差: {std_dev:.2f}%）', 
                            transform=plt.gca().transAxes, fontsize=10, 
                            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
            
            # 保存图表
            reports_dir = project_root / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理参数路径，用于文件名
            safe_param_name = param_path.replace('.', '_').replace('/', '_')
            plot_path = reports_dir / f"sensitivity_curve_{safe_param_name}.png"
            
            plt.tight_layout()
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"\n📊 响应曲线已保存: {plot_path}")
            if penalty_at_best > 0:
                print(f"   ✅ 最优参数值: {best_param:.3f} (得分: {best_rate:.1f}%, 匹配率: {match_rate_at_best:.1f}%, 惩罚: -{penalty_at_best:.2f})")
            else:
                print(f"   ✅ 最优参数值: {best_param:.3f} (匹配率: {best_rate:.1f}%)")
            
            # 分析鲁棒性
            if len(match_rates) > 5:
                std_dev = np.std(match_rates)
                if std_dev < 5.0:
                    print(f"   ✅ 参数鲁棒性好（标准差: {std_dev:.2f}%），建议使用最优值")
                elif std_dev > 10.0:
                    print(f"   ⚠️ 参数敏感度高（标准差: {std_dev:.2f}%），建议谨慎调优")
                else:
                    print(f"   ℹ️ 参数敏感度中等（标准差: {std_dev:.2f}%）")
        except ImportError:
            print("   ⚠️ matplotlib 未安装，跳过可视化")
        except Exception as e:
            print(f"   ⚠️ 生成图表失败: {e}")
    
    def _set_nested_param(self, config: Dict, path: str, value: float):
        """设置嵌套参数值"""
        keys = path.split('.')
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def grid_search(self, param_grid: Dict[str, Tuple[float, float, int]], 
                   include_follower_threshold: bool = True,
                   focus_structure_params: bool = True) -> Dict:
        """
        网格搜索最优参数（增强版：支持从格阈值调优）
        
        Args:
            param_grid: {参数路径: (min, max, steps), ...}
            include_follower_threshold: 是否包含从格阈值调优（核心分析师建议）
        
        Returns:
            最优参数配置和结果
        """
        print(f"\n🔎 开始网格搜索...")
        print(f"   参数数量: {len(param_grid)}")
        
        # [V10.0 核心分析师建议] 如果启用，自动添加从格阈值调优
        if include_follower_threshold and 'strength.follower_threshold' not in param_grid:
            param_grid = copy.deepcopy(param_grid)
            param_grid['strength.follower_threshold'] = (0.1, 0.2, 5)  # 范围 0.1~0.2, 5步
            print(f"   ✅ 已添加从格阈值调优: strength.follower_threshold (0.1~0.2, 5步)")
        
        best_match_rate = 0.0
        best_config = None
        best_result = None
        
        # 生成参数组合（简化版本：只搜索前2个参数，避免组合爆炸）
        param_names = list(param_grid.keys())[:2]  # 限制为2个参数
        if len(param_names) < len(param_grid):
            print(f"   ⚠️ 警告：参数过多，只搜索前2个参数")
        
        param1_name, param1_range = param_names[0], param_grid[param_names[0]]
        param2_name, param2_range = param_names[1] if len(param_names) > 1 else None, param_grid.get(param_names[1], None) if len(param_names) > 1 else None
        
        min1, max1, steps1 = param1_range
        step1 = (max1 - min1) / steps1
        
        total_combinations = steps1 + 1
        if param2_range:
            min2, max2, steps2 = param2_range
            step2 = (max2 - min2) / steps2
            total_combinations *= (steps2 + 1)
        
        print(f"   总组合数: {total_combinations}")
        
        count = 0
        for i in range(steps1 + 1):
            val1 = min1 + i * step1
            
            if param2_range:
                for j in range(steps2 + 1):
                    val2 = min2 + j * step2
                    count += 1
                    
                    test_config = copy.deepcopy(self.base_config)
                    self._set_nested_param(test_config, param1_name, val1)
                    self._set_nested_param(test_config, param2_name, val2)
                    
                    eval_result = self.evaluate_parameter_set(test_config)
                    
                    if eval_result['match_rate'] > best_match_rate:
                        best_match_rate = eval_result['match_rate']
                        best_config = copy.deepcopy(test_config)
                        best_result = eval_result
                    
                    print(f"   [{count}/{total_combinations}] {param1_name}={val1:.3f}, {param2_name}={val2:.3f}: {eval_result['match_rate']:.1f}%")
            else:
                count += 1
                
                test_config = copy.deepcopy(self.base_config)
                self._set_nested_param(test_config, param1_name, val1)
                
                eval_result = self.evaluate_parameter_set(test_config)
                
                final_score = eval_result.get('weighted_score', eval_result['match_rate'])
                if final_score > best_match_rate:
                    best_match_rate = final_score
                    best_config = copy.deepcopy(test_config)
                    best_result = eval_result
                
                match_rate = eval_result['match_rate']
                penalty = eval_result.get('penalty', 0.0)
                if penalty > 0:
                    print(f"   [{count}/{total_combinations}] {param1_name}={val1:.3f}: {match_rate:.1f}% (得分: {final_score:.1f}, 惩罚: -{penalty:.2f})")
                else:
                    print(f"   [{count}/{total_combinations}] {param1_name}={val1:.3f}: {match_rate:.1f}%")
        
        return {
            'best_config': best_config,
            'best_match_rate': best_match_rate,
            'best_result': best_result
        }
    
    def generate_report(self, results: Dict, output_path: Optional[Path] = None):
        """生成调优报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_path is None:
            output_path = project_root / "reports" / f"strength_tuning_report_{timestamp}.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'timestamp': timestamp,
            'total_cases': results['total_cases'],
            'matched_cases': results['matched_cases'],
            'match_rate': results['match_rate'],
            'case_results': results['case_results']
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 报告已保存: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description='旺衰判定参数调优工具')
    parser.add_argument('--mode', choices=['sensitivity', 'optimize', 'test'], 
                       default='test', help='运行模式')
    parser.add_argument('--param', type=str, help='参数路径（用于敏感度分析）')
    parser.add_argument('--min', type=float, help='参数最小值')
    parser.add_argument('--max', type=float, help='参数最大值')
    parser.add_argument('--steps', type=int, default=10, help='扫描步数')
    parser.add_argument('--output', type=str, help='输出报告路径')
    
    args = parser.parse_args()
    
    tuner = StrengthParameterTuner()
    
    if args.mode == 'test':
        print("\n🧪 测试当前参数配置...")
        result = tuner.evaluate_parameter_set(tuner.base_config)
        print(f"\n✅ 当前配置性能:")
        print(f"   匹配率: {result['match_rate']:.1f}%")
        print(f"   匹配案例: {result['matched_cases']}/{result['total_cases']}")
        
        # 显示详细结果
        print(f"\n📋 详细结果:")
        for case_result in result['case_results']:
            status = "✅" if case_result['match'] else "❌"
            print(f"   {status} {case_result['name']}: {case_result['predicted']} (GT: {case_result['ground_truth']}, Score: {case_result['score']:.1f})")
        
        if args.output:
            tuner.generate_report(result, Path(args.output))
    
    elif args.mode == 'sensitivity':
        if not args.param or args.min is None or args.max is None:
            print("❌ 敏感度分析需要指定 --param, --min, --max 参数")
            return
        
        results = tuner.sensitivity_analysis(args.param, (args.min, args.max), args.steps)
        
        # 找出最佳值（使用最终得分，而非仅匹配率）
        best_result = max(results, key=lambda x: x.get('weighted_score', x['match_rate']))
        print(f"\n🎯 最佳参数值: {best_result['param_value']:.3f}")
        print(f"   加权匹配率: {best_result['match_rate']:.1f}%")
        if best_result.get('penalty', 0.0) > 0:
            print(f"   最终得分: {best_result.get('weighted_score', best_result['match_rate']):.1f}% (惩罚: -{best_result.get('penalty', 0.0):.2f})")
    
    elif args.mode == 'optimize':
        print("\n🔎 开始参数优化（网格搜索）...")
        print("   [V10.0 新数据集调优] 基于91个案例的参数优化")
        
        # 基于敏感度分析结果，优化关键参数
        param_grid = {
            'strength.energy_threshold_center': (4.0, 4.4, 5),  # 能量阈值中心点：4.1时达到47.1%
            'structure.samePillarBonus': (1.5, 2.2, 8)  # 同柱加成：1.6时达到48.1%
        }
        
        # [V10.0 核心分析师建议] 自动添加从格阈值调优（但当前数据集显示不敏感）
        result = tuner.grid_search(param_grid, include_follower_threshold=False, focus_structure_params=True)
        
        print(f"\n🎯 最优配置找到:")
        print(f"   匹配率: {result['best_match_rate']:.1f}%")
        print(f"\n📋 最优参数:")
        print(f"   energy_threshold_center: {result['best_config']['strength']['energy_threshold_center']:.3f}")
        print(f"   phase_transition_width: {result['best_config']['strength']['phase_transition_width']:.3f}")
        if 'follower_threshold' in result['best_config'].get('strength', {}):
            print(f"   follower_threshold: {result['best_config']['strength']['follower_threshold']:.3f}")


if __name__ == '__main__':
    main()

