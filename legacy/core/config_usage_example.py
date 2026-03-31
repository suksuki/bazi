"""
层级化配置系统使用示例 (Cascading Configuration Usage Examples)

此文件演示如何在代码中使用新的层级化配置系统，支持参数继承和重写。
"""

from core.config import config, get_pattern_param, get_pattern_weights


def example_basic_usage():
    """示例1: 基础使用 - 获取格局特异性参数"""
    pattern_id = "A-03"
    
    # 获取Precision Score相关参数
    sigma = get_pattern_param(pattern_id, 'precision_gaussian_sigma')
    energy_k = get_pattern_param(pattern_id, 'precision_energy_gate_k')
    weights = get_pattern_weights(pattern_id)
    
    print(f"Pattern: {pattern_id}")
    print(f"  Gaussian Sigma: {sigma}")
    print(f"  Energy Gate K: {energy_k}")
    print(f"  Weights: {weights}")
    
    # 输出：
    # Pattern: A-03
    #   Gaussian Sigma: 2.2  (L3特异性值，重写了L1的2.5)
    #   Energy Gate K: 0.35  (L3特异性值，重写了L1的0.4)
    #   Weights: {'similarity': 0.5, 'distance': 0.5}


def example_inheritance():
    """示例2: 参数继承 - 如果格局没有重写，自动使用L1默认值"""
    pattern_id = "UNKNOWN-PATTERN"
    
    # 未知格局会回退到L1全局默认值
    sigma = get_pattern_param(pattern_id, 'precision_gaussian_sigma')
    global_default = config.physics.precision_gaussian_sigma
    
    print(f"Pattern: {pattern_id}")
    print(f"  Sigma: {sigma} (继承自L1全局默认值)")
    print(f"  Global Default: {global_default}")
    assert sigma == global_default  # 应该相等


def example_pattern_specific_params():
    """示例3: 获取格局特定的业务参数"""
    pattern_id = "A-03"
    a03_config = config.patterns.a03
    
    # 直接访问格局配置对象
    print(f"Pattern: {pattern_id} 业务参数")
    print(f"  min_killer_energy: {a03_config.min_killer_energy}")
    print(f"  standard_e_min: {a03_config.standard_e_min}")
    print(f"  standard_s_min: {a03_config.standard_s_min}")
    print(f"  mahalanobis_threshold: {a03_config.mahalanobis_threshold}")


def example_fitting_script_usage():
    """
    示例4: 在拟合脚本中使用（模拟场景）
    
    这是拟合脚本中应该如何使用的示例
    """
    def calculate_precision_score(tensor_vector, mean_vector, cov_matrix, pattern_id):
        """计算Precision Score，使用格局特异性参数"""
        import numpy as np
        from core.math_engine import (
            calculate_cosine_similarity,
            calculate_mahalanobis_distance
        )
        
        # 1. 获取格局特异性参数（自动继承）
        sigma = get_pattern_param(pattern_id, 'precision_gaussian_sigma')
        energy_k = get_pattern_param(pattern_id, 'precision_energy_gate_k')
        weights = get_pattern_weights(pattern_id)
        
        # 2. 计算基础指标
        similarity = calculate_cosine_similarity(tensor_vector, mean_vector)
        m_dist = calculate_mahalanobis_distance(tensor_vector, mean_vector, cov_matrix)
        sai = np.mean(tensor_vector)
        
        # 3. 使用格局特异性参数计算Precision Score
        # 高斯衰减函数：exp(-m_dist^2 / (2 * sigma^2))
        gaussian_decay = np.exp(-(m_dist ** 2) / (2 * (sigma ** 2)))
        
        # 加权组合
        precision = (
            weights['similarity'] * similarity +
            weights['distance'] * gaussian_decay
        )
        
        # 4. 能量门控（使用格局特异性阈值）
        if sai < energy_k:
            precision *= 0.5  # 身弱惩罚
        
        return precision, similarity, m_dist, sai
    
    # 模拟使用
    print("模拟拟合计算:")
    pattern_id = "A-03"
    # ... 实际的计算代码 ...
    print(f"使用 {pattern_id} 的参数配置进行计算")


def example_comparison_different_patterns():
    """示例5: 对比不同格局的参数差异"""
    patterns = ["A-03", "A-01", "D-02"]
    
    print("\n不同格局的参数对比:")
    print(f"{'Pattern':<10} {'Sigma':<8} {'Energy K':<10} {'Weights (sim/dist)'}")
    print("-" * 60)
    
    for pattern_id in patterns:
        sigma = get_pattern_param(pattern_id, 'precision_gaussian_sigma')
        energy_k = get_pattern_param(pattern_id, 'precision_energy_gate_k')
        weights = get_pattern_weights(pattern_id)
        
        weights_str = f"{weights['similarity']:.1f}/{weights['distance']:.1f}"
        print(f"{pattern_id:<10} {sigma:<8.2f} {energy_k:<10.2f} {weights_str}")
    
    # 输出示例：
    # Pattern    Sigma    Energy K   Weights (sim/dist)
    # ------------------------------------------------------------
    # A-03       2.20     0.35       0.5/0.5
    # A-01       1.80     0.45       0.8/0.2
    # D-02       3.00     0.30       0.7/0.3


if __name__ == "__main__":
    print("=" * 80)
    print("层级化配置系统使用示例")
    print("=" * 80)
    
    print("\n[示例1] 基础使用")
    example_basic_usage()
    
    print("\n[示例2] 参数继承")
    example_inheritance()
    
    print("\n[示例3] 格局特定业务参数")
    example_pattern_specific_params()
    
    print("\n[示例4] 拟合脚本使用")
    example_fitting_script_usage()
    
    print("\n[示例5] 不同格局参数对比")
    example_comparison_different_patterns()
    
    print("\n" + "=" * 80)
    print("✅ 所有示例演示完成")
    print("=" * 80)

