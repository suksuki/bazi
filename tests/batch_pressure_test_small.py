"""
[QGA V25.0 Phase 5.2] 小规模压力测试（快速验证）
先运行10个样本验证流程，确认无误后再运行完整1000样本测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.batch_pressure_test_v25 import BatchPressureTest

def main():
    """运行小规模测试（10个样本）"""
    print("🧪 QGA V25.0 Phase 5.2: 小规模压力测试（10样本）")
    print("   用于快速验证流程，确认无误后再运行完整测试")
    print("")
    
    # 创建测试实例（10个样本，2个并发线程）
    tester = BatchPressureTest(sample_count=10, max_workers=2)
    
    # 运行测试
    report = tester.run_batch_test()
    
    print("\n✅ 小规模测试完成！")
    print("   如果结果正常，可以运行 tests/batch_pressure_test_v25.py 进行完整1000样本测试")

if __name__ == "__main__":
    main()

