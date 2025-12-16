#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 V79 优化器的错误诊断"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88

# 加载案例
cases_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "calibration_cases.json")
if os.path.exists(cases_path):
    with open(cases_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    print(f"✅ 加载了 {len(cases)} 个校准案例")
    
    # 测试第一个案例
    if cases:
        case = cases[0]
        print(f"\n测试案例: {case.get('id', 'Unknown')}")
        print(f"案例键: {list(case.keys())}")
        
        # 构建 case_data
        bazi = case.get('bazi', [])
        day_master = case.get('day_master', '')
        
        case_data = {
            'year': bazi[0] if len(bazi) > 0 else '',
            'month': bazi[1] if len(bazi) > 1 else '',
            'day': bazi[2] if len(bazi) > 2 else '',
            'hour': bazi[3] if len(bazi) > 3 else '',
            'day_master': day_master,
            'gender': case.get('gender', 1),
            'case_id': case.get('id', 'Unknown')
        }
        
        print(f"\ncase_data: {case_data}")
        
        # 加载配置
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 创建引擎
        engine = EngineV88(config=config)
        
        # 计算
        d_ctx = {"year": "2024", "luck": "default"}
        try:
            result = engine.calculate_energy(case_data, d_ctx)
            print(f"\n✅ 计算成功")
            print(f"结果键: {list(result.keys())}")
            print(f"career: {result.get('career', 'N/A')}")
            print(f"wealth: {result.get('wealth', 'N/A')}")
            print(f"relationship: {result.get('relationship', 'N/A')}")
        except Exception as e:
            print(f"\n❌ 计算失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
else:
    print(f"❌ 案例文件不存在: {cases_path}")

