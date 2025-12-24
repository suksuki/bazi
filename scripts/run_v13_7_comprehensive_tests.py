#!/usr/bin/env python3
"""
[V13.7] 全面自动化测试脚本
==========================

运行所有 V13.7 相关的测试，包括：
1. 注册验证测试
2. 引擎功能测试
3. 集成测试
4. 回归测试

使用方法：
    python scripts/run_v13_7_comprehensive_tests.py
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 项目根目录
project_root = Path(__file__).parent.parent


def run_test_suite(test_file: str, description: str) -> dict:
    """运行单个测试套件"""
    print(f"\n{'='*60}")
    print(f"运行测试: {description}")
    print(f"文件: {test_file}")
    print(f"{'='*60}\n")
    
    test_path = project_root / test_file
    
    if not test_path.exists():
        return {
            "status": "SKIPPED",
            "reason": f"测试文件不存在: {test_file}",
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
    
    try:
        # 尝试使用 pytest，如果失败则使用 unittest
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
        except FileNotFoundError:
            # 如果 pytest 不可用，使用 unittest
            test_module = str(test_path).replace(str(project_root) + "/", "").replace("/", ".").replace(".py", "")
            result = subprocess.run(
                [sys.executable, "-m", "unittest", test_module, "-v"],
                capture_output=True,
                text=True,
                timeout=300
            )
        
        # 解析输出
        output = result.stdout + result.stderr
        
        # 简单统计
        passed = output.count("PASSED") + output.count("passed")
        failed = output.count("FAILED") + output.count("failed")
        errors = output.count("ERROR") + output.count("error")
        
        return {
            "status": "PASSED" if result.returncode == 0 else "FAILED",
            "returncode": result.returncode,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "output": output[:1000]  # 只保存前1000字符
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "reason": "测试超时（>5分钟）",
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "reason": str(e),
            "passed": 0,
            "failed": 0,
            "errors": 0
        }


def main():
    """主函数"""
    print("="*60)
    print("V13.7 全面自动化测试")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目根目录: {project_root}")
    print()
    
    # 测试套件列表
    test_suites = [
        {
            "file": "tests/test_v13_7_registration_comprehensive.py",
            "description": "V13.7 注册验证测试（新增注册项）"
        },
        {
            "file": "tests/test_influence_bus_injection_verification.py",
            "description": "InfluenceBus 注入验证测试"
        },
        {
            "file": "tests/test_real_01_rooting_gain_verification.py",
            "description": "REAL_01 通根增益验证测试"
        },
        {
            "file": "tests/test_real_01_full_lifespan_retrospective.py",
            "description": "REAL_01 全生命周期回溯测试"
        },
        {
            "file": "tests/test_wealth_logic.py",
            "description": "财富逻辑测试"
        },
        {
            "file": "tests/test_phase36_38_relationship_gravity.py",
            "description": "情感引力测试"
        },
        {
            "file": "tests/test_sanity.py",
            "description": "基础功能测试"
        }
    ]
    
    results = []
    total_passed = 0
    total_failed = 0
    total_errors = 0
    
    # 运行所有测试套件
    for suite in test_suites:
        result = run_test_suite(suite["file"], suite["description"])
        result["description"] = suite["description"]
        result["file"] = suite["file"]
        results.append(result)
        
        # 统计
        total_passed += result.get("passed", 0)
        total_failed += result.get("failed", 0)
        total_errors += result.get("errors", 0)
        
        # 显示结果
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        print(f"{status_icon} {suite['description']}: {result['status']}")
        if result.get("passed", 0) > 0:
            print(f"   通过: {result['passed']}")
        if result.get("failed", 0) > 0:
            print(f"   失败: {result['failed']}")
        if result.get("errors", 0) > 0:
            print(f"   错误: {result['errors']}")
        if result.get("reason"):
            print(f"   原因: {result['reason']}")
    
    # 生成报告
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总通过: {total_passed}")
    print(f"总失败: {total_failed}")
    print(f"总错误: {total_errors}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 保存报告
    report_path = project_root / "docs" / "V13.7_COMPREHENSIVE_TEST_REPORT.json"
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_errors": total_errors,
            "total_suites": len(test_suites)
        },
        "results": results
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存到: {report_path}")
    
    # 返回状态码
    return 0 if total_failed == 0 and total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

