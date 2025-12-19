"""
V11.9 黄金矩阵数据生成器 (Golden Matrix Data Generator)
空投物资：直接提供300个精心设计的"黄金标准数据"

这组数据的精髓在于覆盖"真假专旺"和"真假从格"的边界情况，
确保模型能够学会区分：
- Score=85 的真专旺 vs Score=85 的假专旺（Strong）
- Score=25 的真从格 vs Score=25 的假从格（Weak）
"""

import numpy as np
import pandas as pd
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# 设置随机种子确保可复现性
np.random.seed(42)


def get_golden_synthetic_data(n_samples: int = 300) -> pd.DataFrame:
    """
    直接返回 300 个高质量的合成特征向量。
    
    特征顺序: [strength_score, self_team_ratio, is_month_command,
              main_root_count, clash_count, day_master_polarity, is_yangren]
    
    Args:
        n_samples: 目标样本数（默认300）
    
    Returns:
        DataFrame包含特征向量和标签
    """
    data = []
    labels = []
    
    # 1. 真专旺 (True Special Strong) - 60例
    # 特征：极高分，高占比，得令，多根，无冲，阳干为主
    logger.info("   🏆 生成真专旺数据 (60例)...")
    for i in range(60):
        score = np.random.uniform(92.0, 100.0)  # 分数 > 92
        ratio = np.random.uniform(0.85, 1.0)
        # 偶尔混入一点噪声，但总体完美
        row = [
            score,
            ratio,
            1.0,  # 得令
            np.random.choice([2, 3, 4]),  # 强根
            0,  # 无冲
            np.random.choice([1.0, 0.0], p=[0.8, 0.2]),  # 多为阳干
            np.random.choice([1.0, 0.0], p=[0.6, 0.4])  # 常坐阳刃
        ]
        data.append(row)
        labels.append('Special_Strong')
    
    # 2. 真从格 (True Follower) - 60例
    # 特征：极低分，极低占比，失令，无根，多冲/克
    logger.info("   🏆 生成真从格数据 (60例)...")
    for i in range(60):
        score = np.random.uniform(0.0, 15.0)  # 分数 < 15
        ratio = np.random.uniform(0.0, 0.15)
        row = [
            score,
            ratio,
            0.0,  # 失令
            0,  # 无根
            np.random.randint(1, 4),  # 多冲克
            np.random.choice([1.0, 0.0], p=[0.3, 0.7]),  # 多为阴干
            0.0
        ]
        data.append(row)
        labels.append('Follower')
    
    # 3. 假专旺/身强 (Fake Special -> Strong) - 60例
    # 关键边界：分数很高(75-88)，但不得令，或有冲。这是区分杜月笙的关键！
    logger.info("   🏆 生成假专旺/身强数据 (60例)...")
    for i in range(60):
        score = np.random.uniform(75.0, 88.0)  # 分数很高
        ratio = np.random.uniform(0.60, 0.75)
        row = [
            score,
            ratio,
            np.random.choice([0.5, 0.0]),  # 失令或平
            np.random.choice([1, 2]),  # 根不深
            np.random.randint(1, 3),  # 有冲!!!
            np.random.choice([1.0, 0.0]),
            0.0
        ]
        data.append(row)
        labels.append('Strong')  # 虽然分高，但判为 Strong，不是 Special
    
    # 4. 假从格/身弱 (Fake Follower -> Weak) - 60例
    # 关键边界：分数很低(18-30)，但有微根或印。这是区分极弱的关键。
    logger.info("   🏆 生成假从格/身弱数据 (60例)...")
    for i in range(60):
        score = np.random.uniform(18.0, 35.0)
        ratio = np.random.uniform(0.15, 0.30)
        row = [
            score,
            ratio,
            0.0,
            1,  # 有一个微根!!!
            np.random.randint(1, 3),
            1.0,  # 阳干不从
            0.0
        ]
        data.append(row)
        labels.append('Weak')  # 有根不能从
    
    # 5. 标准中和 (Balanced) - 60例
    logger.info("   🏆 生成标准中和数据 (60例)...")
    for i in range(60):
        score = np.random.uniform(40.0, 60.0)
        ratio = np.random.uniform(0.4, 0.6)
        row = [
            score, ratio, 0.5, 1, 0, np.random.choice([1.0, 0.0]), 0.0
        ]
        data.append(row)
        labels.append('Balanced')
    
    # 转 DataFrame
    cols = ['strength_score', 'self_team_ratio', 'is_month_command',
            'main_root_count', 'clash_count', 'day_master_polarity', 'is_yangren']
    df = pd.DataFrame(data, columns=cols)
    df['label'] = labels
    df['case_id'] = [f'GOLDEN_{i+1:03d}' for i in range(len(df))]
    df['source'] = 'Golden_Synthetic'  # 护身符标签
    df['synthetic'] = True
    df['category'] = 'synthetic'
    df['golden'] = True  # 标记为黄金数据
    
    logger.info(f"   ✅ 生成了 {len(df)} 个黄金合成数据")
    logger.info(f"      - Special_Strong: {sum(labels == 'Special_Strong' for labels in labels)} 个")
    logger.info(f"      - Follower: {sum(labels == 'Follower' for labels in labels)} 个")
    logger.info(f"      - Strong: {sum(labels == 'Strong' for labels in labels)} 个")
    logger.info(f"      - Weak: {sum(labels == 'Weak' for labels in labels)} 个")
    logger.info(f"      - Balanced: {sum(labels == 'Balanced' for labels in labels)} 个")
    
    return df


def convert_golden_data_to_cases(df: pd.DataFrame) -> List[Dict]:
    """
    将黄金数据的DataFrame转换为案例字典列表
    
    Args:
        df: 黄金数据DataFrame
    
    Returns:
        案例字典列表，格式与synthetic_factory生成的案例一致
    """
    cases = []
    
    for _, row in df.iterrows():
        case = {
            'id': row['case_id'],
            'name': f'[黄金] {row["label"]}',
            'bazi': ['甲子', '甲子', '甲子', '甲子'],  # 占位符，实际不使用
            'day_master': '甲',  # 占位符
            'gender': '男',
            'ground_truth': {'strength': row['label']},
            'characteristics': f'[黄金数据-{row["label"]}] 精心设计的边界案例，用于训练模型区分真假格局',
            'synthetic': True,
            'synthetic_type': 'golden',
            'source': 'Golden_Synthetic',
            'category': 'synthetic',
            'weight': 2.0,
            'verified': True,
            'golden': True,
            # V11.9: 直接存储特征向量（用于特征提取时直接使用）
            'golden_features': [
                row['strength_score'],
                row['self_team_ratio'],
                row['is_month_command'],
                int(row['main_root_count']),
                int(row['clash_count']),
                row['day_master_polarity'],
                row['is_yangren']
            ]
        }
        cases.append(case)
    
    return cases

