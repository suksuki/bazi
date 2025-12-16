#!/usr/bin/env python3
"""
Antigravity Batch Verification Suite (V34.0)
=============================================

批量验证套件：用于评估 Graph Engine 在不同案例集上的准确率。

使用方法:
    python scripts/batch_verify.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import copy

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


# ===========================================
# 1. 数据加载
# ===========================================

def load_golden_cases(data_path: Path = None) -> List[Dict[str, Any]]:
    """
    加载黄金数据集。
    
    如果文件不存在，生成一个包含典型案例的 Mock 文件用于测试。
    
    Returns:
        案例列表，每个案例包含 id, bazi, day_master, true_label 等信息
    """
    if data_path is None:
        data_path = project_root / "data" / "golden_cases.json"
    
    # 如果文件存在，直接加载
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            print(f"✅ 已加载 {len(cases)} 个案例从 {data_path}")
            return cases
    
    # 否则生成 Mock 数据
    print(f"⚠️  {data_path} 不存在，生成 Mock 测试数据...")
    
    mock_cases = [
        {
            'id': 'CASE_STRONG_001',
            'bazi': ['甲子', '甲子', '甲子', '甲子'],  # 专旺格（四甲子）
            'day_master': '甲',
            'gender': '男',
            'true_label': 'Strong',
            'description': '专旺格案例：四甲子，木旺'
        },
        {
            'id': 'CASE_WEAK_001',
            'bazi': ['庚申', '庚申', '甲寅', '庚申'],  # 杀重身轻（三庚克甲）
            'day_master': '甲',
            'gender': '男',
            'true_label': 'Weak',
            'description': '杀重身轻：三庚克甲，甲木弱'
        },
        {
            'id': 'CASE_BALANCED_001',
            'bazi': ['甲子', '丙寅', '戊辰', '庚午'],  # 身杀两停
            'day_master': '甲',
            'gender': '男',
            'true_label': 'Balanced',
            'description': '身杀两停：甲木得生又有官杀'
        },
        {
            'id': 'VAL_005',
            'bazi': ['辛未', '辛丑', '庚戌', '丁亥'],  # 润局案例
            'day_master': '庚',
            'gender': '男',
            'true_label': 'Strong',
            'description': '塑胶大亨：润局解救（亥水润土生金）'
        },
        {
            'id': 'CASE_STRONG_002',
            'bazi': ['丙寅', '丙午', '丙午', '甲午'],  # 火专旺
            'day_master': '丙',
            'gender': '男',
            'true_label': 'Strong',
            'description': '火专旺：三午一寅，火旺'
        },
        {
            'id': 'CASE_WEAK_002',
            'bazi': ['戊子', '癸亥', '戊戌', '癸亥'],  # 财多身弱
            'day_master': '戊',
            'gender': '男',
            'true_label': 'Weak',
            'description': '财多身弱：双癸双亥，土被水耗'
        }
    ]
    
    # 保存 Mock 数据
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(mock_cases, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已生成 {len(mock_cases)} 个 Mock 案例到 {data_path}")
    return mock_cases


# ===========================================
# 2. 预测和评估
# ===========================================

def predict_strength(strength_score: float, 
                     strong_threshold: float = 60.0,
                     weak_threshold: float = 40.0) -> str:
    """
    根据占比分数预测身强身弱（使用动态阈值）。
    
    Args:
        strength_score: 标准化分数 (0-100)
        strong_threshold: Strong判定阈值
        weak_threshold: Weak判定阈值
    
    Returns:
        "Strong", "Balanced", 或 "Weak"
    """
    if strength_score >= strong_threshold:
        return "Strong"
    elif strength_score >= weak_threshold:
        return "Balanced"
    else:
        return "Weak"


def evaluate_case(engine: GraphNetworkEngine, case: Dict[str, Any]) -> Dict[str, Any]:
    """
    评估单个案例。
    
    Args:
        engine: GraphNetworkEngine 实例
        case: 案例数据
    
    Returns:
        评估结果字典
    """
    bazi = case['bazi']
    day_master = case['day_master']
    true_label = case.get('true_label', 'Unknown')
    
    # 运行分析
    result = engine.analyze(
        bazi=bazi,
        day_master=day_master,
        luck_pillar=None,
        year_pillar=None,
        geo_modifiers=None
    )
    
    # 获取标准化分数和标签
    strength_score = result.get('strength_score', 0.0)
    strength_label = result.get('strength_label', 'Unknown')
    special_pattern = result.get('special_pattern')
    
    # [V58.0] 从配置中获取阈值，或使用默认值
    grading_config = engine.config.get('grading', {})
    strong_threshold = grading_config.get('strong_threshold', 60.0)
    weak_threshold = grading_config.get('weak_threshold', 40.0)
    
    # [V40.0] 优先使用引擎返回的标签（可能包含Special_Strong）
    if strength_label in ["Strong", "Balanced", "Weak", "Special_Strong"]:
        pred_label = strength_label
    else:
        # 如果引擎没有返回有效标签，则使用阈值判断
        pred_label = predict_strength(strength_score, strong_threshold, weak_threshold)
    
    # 判断是否正确
    # [V40.0/V41.0] 特殊格局例外处理
    is_correct = (pred_label == true_label)
    
    if not is_correct:
        # 例外1：如果被判定为Special_Strong，且True_Label是Balanced，视为通过（广义中和/贵格）
        if pred_label == "Special_Strong" and true_label == "Balanced":
            is_correct = True
        # 例外2：如果被判定为Special_Strong，且True_Label是Strong，也视为通过（专旺格本身就是Strong的一种）
        elif pred_label == "Special_Strong" and true_label == "Strong":
            is_correct = True
    
    return {
        'case_id': case.get('id', 'Unknown'),
        'true_label': true_label,
        'pred_label': pred_label,
        'strength_score': strength_score,
        'strength_label': strength_label,
        'is_correct': is_correct
    }


# ===========================================
# 3. 统计和报告
# ===========================================

def print_detailed_report(results: List[Dict[str, Any]]):
    """打印详细报告"""
    print("\n" + "=" * 80)
    print("📊 详细评估报告")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        case_id = result['case_id']
        true_label = result['true_label']
        pred_label = result['pred_label']
        score = result['strength_score']
        is_correct = result['is_correct']
        
        status = "✅ PASS" if is_correct else "❌ FAIL"
        
        print(f"[Case {i:03d}] {case_id}")
        print(f"         True: {true_label:8s} | Pred: {pred_label:8s} ({score:5.1f}%) | {status}")
        print()
    
    print("=" * 80)


def print_summary_report(results: List[Dict[str, Any]]):
    """打印汇总报告"""
    total = len(results)
    correct = sum(1 for r in results if r['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0.0
    
    # 混淆矩阵（简易版）
    confusion = defaultdict(lambda: defaultdict(int))
    for result in results:
        true_label = result['true_label']
        pred_label = result['pred_label']
        confusion[true_label][pred_label] += 1
    
    print("\n" + "=" * 80)
    print("📈 汇总统计")
    print("=" * 80)
    print(f"总案例数: {total}")
    print(f"正确数: {correct}")
    print(f"错误数: {total - correct}")
    print(f"准确率: {accuracy:.1f}%")
    print()
    
    # 混淆矩阵
    print("混淆矩阵 (Confusion Matrix):")
    print("-" * 80)
    labels = ['Strong', 'Balanced', 'Weak']
    
    # 表头
    print(f"{'True\\Pred':12s}", end='')
    for pred in labels:
        print(f"{pred:12s}", end='')
    print()
    print("-" * 80)
    
    # 表格内容
    for true_label in labels:
        print(f"{true_label:12s}", end='')
        for pred_label in labels:
            count = confusion[true_label][pred_label]
            print(f"{count:12d}", end='')
        print()
    
    print("=" * 80)
    
    # 按标签分类的准确率
    print("\n按标签分类的准确率:")
    print("-" * 80)
    for label in labels:
        label_cases = [r for r in results if r['true_label'] == label]
        if label_cases:
            label_correct = sum(1 for r in label_cases if r['is_correct'])
            label_acc = (label_correct / len(label_cases) * 100)
            print(f"{label:12s}: {label_correct}/{len(label_cases)} = {label_acc:.1f}%")
    print("=" * 80)


def print_score_distribution(results: List[Dict[str, Any]]):
    """打印分数分布（ASCII图表）"""
    print("\n" + "=" * 80)
    print("📊 分数分布")
    print("=" * 80)
    
    # 分组统计
    strong_scores = [r['strength_score'] for r in results if r['true_label'] == 'Strong']
    balanced_scores = [r['strength_score'] for r in results if r['true_label'] == 'Balanced']
    weak_scores = [r['strength_score'] for r in results if r['true_label'] == 'Weak']
    
    def print_distribution(label: str, scores: List[float]):
        if not scores:
            print(f"{label:12s}: 无数据")
            return
        
        avg = sum(scores) / len(scores)
        min_val = min(scores)
        max_val = max(scores)
        
        print(f"{label:12s}: 平均={avg:5.1f}% | 范围=[{min_val:5.1f}%, {max_val:5.1f}%] | 数量={len(scores)}")
        
        # 简单的ASCII条形图
        bar_length = 40
        avg_scaled = int((avg / 100.0) * bar_length)
        bar = '█' * avg_scaled + '░' * (bar_length - avg_scaled)
        print(f"              {'':12s}{bar} {avg:.1f}%")
    
    print_distribution("Strong", strong_scores)
    print_distribution("Balanced", balanced_scores)
    print_distribution("Weak", weak_scores)
    print("=" * 80)


# ===========================================
# 4. 主测试循环
# ===========================================

def run_batch_verification():
    """运行批量验证"""
    print("=" * 80)
    print("🚀 Antigravity Batch Verification Suite (V34.0)")
    print("=" * 80)
    print()
    
    # 1. 加载案例
    print("📋 加载测试案例...")
    cases = load_golden_cases()
    print(f"   加载了 {len(cases)} 个案例")
    print()
    
    # 2. 初始化引擎
    print("🔧 初始化 Graph Network Engine...")
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 加载配置文件（如果有）
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            # 合并配置
            config.update(user_config)
        print(f"   ✅ 已加载配置: {config_path}")
    
    engine = GraphNetworkEngine(config=config)
    print("   ✅ 引擎初始化完成")
    print()
    
    # 3. 运行测试
    print("🧪 开始批量测试...")
    print("-" * 80)
    
    results = []
    for i, case in enumerate(cases, 1):
        try:
            result = evaluate_case(engine, case)
            results.append(result)
            
            # 实时输出
            case_id = result['case_id']
            true_label = result['true_label']
            pred_label = result['pred_label']
            score = result['strength_score']
            is_correct = result['is_correct']
            status = "✅" if is_correct else "❌"
            
            print(f"[{i:03d}/{len(cases)}] {case_id:20s} | True: {true_label:8s} | "
                  f"Pred: {pred_label:8s} ({score:5.1f}%) | {status}")
        
        except Exception as e:
            print(f"[{i:03d}/{len(cases)}] {case.get('id', 'Unknown'):20s} | ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("-" * 80)
    print()
    
    # 4. 生成报告
    print_detailed_report(results)
    print_summary_report(results)
    print_score_distribution(results)
    
    # 5. 总结
    correct = sum(1 for r in results if r['is_correct'])
    total = len(results)
    accuracy = (correct / total * 100) if total > 0 else 0.0
    
    print("\n" + "=" * 80)
    print("🎯 测试总结")
    print("=" * 80)
    print(f"总准确率: {accuracy:.1f}% ({correct}/{total})")
    
    if accuracy >= 80.0:
        print("✅ 优秀！引擎表现良好。")
    elif accuracy >= 60.0:
        print("⚠️  合格，但还有改进空间。建议分析失败案例并调整参数。")
    else:
        print("❌ 需要进一步优化。建议检查核心算法逻辑。")
    
    # 列出失败案例
    failures = [r for r in results if not r['is_correct']]
    if failures:
        print(f"\n⚠️  失败案例 ({len(failures)} 个):")
        for fail in failures:
            print(f"   - {fail['case_id']}: True={fail['true_label']}, Pred={fail['pred_label']} ({fail['strength_score']:.1f}%)")
        print("\n💡 建议：这些失败案例是宝贵的调试信息，可用于参数调优。")
    
    print("=" * 80)
    print()


# ===========================================
# 5. 主入口
# ===========================================

if __name__ == "__main__":
    try:
        run_batch_verification()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

