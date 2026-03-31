"""
pytest 配置和 fixtures
=====================

为 V10.0 元学习调优体系测试提供共享 fixtures

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import numpy as np
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


@pytest.fixture
def default_config():
    """提供默认配置"""
    return DEFAULT_FULL_ALGO_PARAMS.copy()


@pytest.fixture
def jason_d_case_data():
    """提供 Jason D 案例数据"""
    return {
        'id': 'JASON_D_T1961_1010',
        'name': 'Jason D (财库连冲)',
        'bazi': ['辛丑', '丁酉', '庚辰', '丙戌'],
        'day_master': '庚',
        'gender': '男',
        'timeline': [
            {'year': 1999, 'real_magnitude': 50.0, 'ganzhi': '己卯', 'dayun': '戊戌'},
            {'year': 2015, 'real_magnitude': 100.0, 'ganzhi': '乙未', 'dayun': '壬辰'},
            {'year': 2021, 'real_magnitude': 100.0, 'ganzhi': '辛丑', 'dayun': '壬辰'}
        ]
    }


@pytest.fixture
def sample_attention_weights():
    """提供示例注意力权重"""
    return {
        (0, 1): 0.5,
        (1, 2): 0.3,
        (2, 3): 0.15,
        (3, 4): 0.05
    }


@pytest.fixture
def sample_energy_paths():
    """提供示例能量路径"""
    return [
        {'0->1': 0.5},
        {'1->2': 0.3},
        {'2->3': 0.15},
        {'3->4': 0.05}
    ]


@pytest.fixture
def sample_timeline_data():
    """提供示例时间线数据"""
    return [
        {'year': 1999, 'energy': 50.0},
        {'year': 2015, 'energy': 100.0},
        {'year': 2021, 'energy': 100.0}
    ]


@pytest.fixture
def parameter_bounds():
    """提供参数边界"""
    return {
        'strength_beta': (5.0, 15.0),
        'clash_k': (3.0, 7.0),
        'trine_boost': (0.1, 0.5),
        'tunneling_factor': (0.05, 0.2)
    }
