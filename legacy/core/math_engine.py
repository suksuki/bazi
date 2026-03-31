"""
QGA 数学内核引擎 (Math Engine)
封装所有数学计算函数，支持向量化操作

基于FDS-V3.0规范 (Pure Logic Edition)
所有数值参数应从 core.config 读取，严禁硬编码
"""

import numpy as np
import math
from typing import Optional, Union, Dict, List, Any, Tuple


def sigmoid_variant(x: Union[float, np.ndarray], k: float = 1.0, x0: float = 0.0) -> Union[float, np.ndarray]:
    """
    Sigmoid激活函数（支持向量化输入）
    
    公式: 1 / (1 + exp(-k * (x - x0)))
    
    Args:
        x: 输入值（可以是标量或numpy数组）
        k: 陡峭度参数（默认1.0）
        x0: 中心点偏移（默认0.0）
        
    Returns:
        Sigmoid输出值（与输入同类型）
        
    Example:
        >>> sigmoid_variant(0.0, k=1.0, x0=0.0)
        0.5
        >>> sigmoid_variant([0.0, 1.0, 2.0], k=1.0, x0=0.0)
        array([0.5, 0.731..., 0.880...])
    """
    if isinstance(x, np.ndarray):
        return 1.0 / (1.0 + np.exp(-k * (x - x0)))
    else:
        return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def tensor_normalize(vector: Dict[str, float]) -> Dict[str, float]:
    """
    张量归一化（单位向量约束）
    
    确保权重向量满足归一化原则：∑|w_i| = 1
    
    公式: w_i_new = w_i_old / ∑|w_i|
    
    Args:
        vector: 权重字典，如 {'E': 0.3, 'O': 0.5, 'M': 0.1, 'S': 0.05, 'R': 0.05}
        
    Returns:
        归一化后的权重字典
        
    Example:
        >>> tensor_normalize({'E': 0.3, 'O': 0.5, 'M': 0.1, 'S': 0.05, 'R': 0.05})
        {'E': 0.3, 'O': 0.5, 'M': 0.1, 'S': 0.05, 'R': 0.05}  # 已经归一化
        >>> tensor_normalize({'E': 0.6, 'O': 0.8, 'M': 0.2})
        {'E': 0.375, 'O': 0.5, 'M': 0.125}  # 归一化后
    """
    total = sum(abs(v) for v in vector.values())
    
    if total == 0:
        return vector  # 避免除零
    
    return {k: round(v / total, 4) for k, v in vector.items()}


def check_normalized(vector: Dict[str, float], tolerance: float = 0.01) -> bool:
    """
    检查权重向量是否已归一化
    
    Args:
        vector: 权重字典
        tolerance: 容差（默认0.01）
        
    Returns:
        是否归一化（在容差范围内）
    """
    total = sum(abs(v) for v in vector.values())
    return abs(total - 1.0) < tolerance


def phase_change_determination(
    energy: float,
    threshold: float = 0.8,
    trigger: bool = False
) -> str:
    """
    相变判定（基于FDS-V1.1规范）
    
    判断系统处于哪种状态：
    - TUNNELING: 能量爆发（能量高且触发）
    - COLLAPSE: 结构坍塌（能量低且触发）
    - STABLE: 稳定态
    
    Args:
        energy: 能量值（归一化到0-1）
        threshold: 临界阈值（默认0.8）
        trigger: 是否有外部触发（如冲、合）
        
    Returns:
        相变状态字符串：'TUNNELING', 'COLLAPSE', 'STABLE'
    """
    if energy > threshold and trigger:
        return 'TUNNELING'  # 隧穿效应：能量爆发
    elif energy < threshold and trigger:
        return 'COLLAPSE'   # 结构坍塌：能量湮灭
    else:
        return 'STABLE'     # 稳定态


def calculate_s_balance(e_blade: float, e_kill: float) -> float:
    """
    计算平衡度（核心方程）
    
    公式: S_balance = E_blade / E_kill
    
    Args:
        e_blade: 羊刃能量
        e_kill: 七杀能量
        
    Returns:
        平衡度值
        
    Note:
        - S_balance ≈ 1.0 → 共振态（大贵）
        - S_balance > 1.2 → 能量溢出（破财）
        - S_balance < 0.8 → 场强压垮（夭折）
    """
    if e_kill == 0:
        return float('inf') if e_blade > 0 else 0.0
    
    return e_blade / e_kill


def calculate_flow_factor(s_base: float, e_seal: float) -> float:
    """
    计算通关因子（Flow Factor）
    
    公式: S_risk = S_base / (1 + E_seal)
    
    物理意义：印星的存在作为分母上的安全系数，印星越有力，风险越小
    
    Args:
        s_base: 基础应力值
        e_seal: 印星能量
        
    Returns:
        修正后的应力值
    """
    return s_base / (1.0 + e_seal)


def calculate_cosine_similarity(
    vec_a: Union[Dict[str, float], List[float]],
    vec_b: Union[Dict[str, float], List[float]]
) -> float:
    """
    计算两个5维能量矢量的余弦相似度
    
    公式: similarity = (A · B) / (||A|| × ||B||)
    
    物理意义：夹角越小，说明八字的能量结构与"完美模型"越共振
    
    Args:
        vec_a: 归一化向量 A，格式为 {'E': float, 'O': float, 'M': float, 'S': float, 'R': float} 
               或 [E, O, M, S, R]
        vec_b: 归一化向量 B，格式同上
        
    Returns:
        similarity (0.0 - 1.0)，1.0表示完全一致，0.0表示正交
        
    Raises:
        ValueError: 如果向量维度不匹配或为零向量
        
    Example:
        >>> vec1 = {'E': 0.3, 'O': 0.4, 'M': 0.1, 'S': 0.15, 'R': 0.05}
        >>> vec2 = {'E': 0.25, 'O': 0.45, 'M': 0.1, 'S': 0.15, 'R': 0.05}
        >>> calculate_cosine_similarity(vec1, vec2)
        0.998...
    """
    # 转换为列表格式（统一处理）
    if isinstance(vec_a, dict):
        vec_a_list = [vec_a.get('E', 0.0), vec_a.get('O', 0.0), 
                      vec_a.get('M', 0.0), vec_a.get('S', 0.0), vec_a.get('R', 0.0)]
    else:
        vec_a_list = list(vec_a)
        if len(vec_a_list) != 5:
            raise ValueError(f"向量A维度必须为5，当前为{len(vec_a_list)}")
    
    if isinstance(vec_b, dict):
        vec_b_list = [vec_b.get('E', 0.0), vec_b.get('O', 0.0), 
                      vec_b.get('M', 0.0), vec_b.get('S', 0.0), vec_b.get('R', 0.0)]
    else:
        vec_b_list = list(vec_b)
        if len(vec_b_list) != 5:
            raise ValueError(f"向量B维度必须为5，当前为{len(vec_b_list)}")
    
    # 转换为numpy数组
    a = np.array(vec_a_list)
    b = np.array(vec_b_list)
    
    # 计算点积
    dot_product = np.dot(a, b)
    
    # 计算模长
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # 零向量保护
    if norm_a == 0.0 or norm_b == 0.0:
        # 如果两个都是零向量，返回1.0（完全一致）
        if norm_a == 0.0 and norm_b == 0.0:
            return 1.0
        # 否则返回0.0（正交）
        return 0.0
    
    # 计算余弦相似度
    similarity = dot_product / (norm_a * norm_b)
    
    # 确保结果在[0, 1]范围内（由于浮点误差可能略超出）
    similarity = max(0.0, min(1.0, similarity))
    
    return float(similarity)


def calculate_centroid(samples: List[Dict[str, float]]) -> Dict[str, float]:
    """
    计算5维质心向量（基于Step 3规范）
    
    算法: T_ref = (1/N) * Σ v_i
    
    目的：计算出该格局在5D空间中的几何中心，即"标准特征锚点" (Standard Anchor)
    
    Args:
        samples: 样本列表，每个样本是归一化的5维向量
                格式: [{'E': float, 'O': float, 'M': float, 'S': float, 'R': float}, ...]
        
    Returns:
        归一化后的质心向量（强制归一化，确保∑v_i = 1.0）
        
    Raises:
        ValueError: 如果样本列表为空
        
    Example:
        >>> samples = [
        ...     {'E': 0.3, 'O': 0.4, 'M': 0.1, 'S': 0.15, 'R': 0.05},
        ...     {'E': 0.25, 'O': 0.45, 'M': 0.1, 'S': 0.15, 'R': 0.05},
        ...     {'E': 0.28, 'O': 0.42, 'M': 0.1, 'S': 0.14, 'R': 0.06}
        ... ]
        >>> centroid = calculate_centroid(samples)
        >>> sum(centroid.values())  # 应该约等于1.0
        1.0
    """
    if not samples:
        raise ValueError("样本列表不能为空")
    
    # 计算平均值
    centroid = {
        'E': sum(s.get('E', 0.0) for s in samples) / len(samples),
        'O': sum(s.get('O', 0.0) for s in samples) / len(samples),
        'M': sum(s.get('M', 0.0) for s in samples) / len(samples),
        'S': sum(s.get('S', 0.0) for s in samples) / len(samples),
        'R': sum(s.get('R', 0.0) for s in samples) / len(samples)
    }
    
    # 强制归一化（根据AI设计师裁定）
    return tensor_normalize(centroid)


def project_tensor_with_matrix(
    input_vector: Dict[str, float],
    transfer_matrix: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    使用转换矩阵计算5维投影（FDS-V1.4）
    
    公式: T_output = Transfer_Matrix × V_input
    
    物理意义：将十神频率向量通过5x5转换矩阵映射到五维命运张量
    
    Args:
        input_vector: 十神频率向量，格式为 {
            "parallel": float,    # 比劫
            "resource": float,   # 印枭
            "power": float,      # 官杀
            "wealth": float,     # 财星
            "output": float      # 食伤
        }
        transfer_matrix: 5x5转换矩阵，格式为 {
            "E_row": {"parallel": float, "resource": float, ...},
            "O_row": {"parallel": float, "resource": float, ...},
            "M_row": {...},
            "S_row": {...},
            "R_row": {...}
        }
        
    Returns:
        5维投影向量 {"E": float, "O": float, "M": float, "S": float, "R": float}
        
    Example:
        >>> input_vec = {"parallel": 1.0, "resource": 0.5, "power": 0.8, "wealth": 0.2, "output": 0.1}
        >>> matrix = {
        ...     "E_row": {"parallel": 1.2, "resource": 0.8, "wealth": -0.5, "output": -0.2, "power": -0.1},
        ...     "O_row": {"power": 0.9, "parallel": 0.3, "resource": 0.4, "wealth": 0.0, "output": 0.1},
        ...     ...
        ... }
        >>> result = project_tensor_with_matrix(input_vec, matrix)
        >>> result
        {'E': 1.35, 'O': 1.12, 'M': 0.18, 'S': 0.45, 'R': 0.12}
    """
    # 初始化输出向量
    output = {axis: 0.0 for axis in ["E", "O", "M", "S", "R"]}
    
    # 矩阵乘法：每个维度 = 对应行的权重 × 输入向量
    for axis in output.keys():
        row_key = f"{axis}_row"
        if row_key not in transfer_matrix:
            continue
        
        row = transfer_matrix[row_key]
        axis_value = 0.0
        
        # 计算该维度的投影值
        for ten_god, weight in row.items():
            if ten_god in input_vector:
                axis_value += weight * input_vector[ten_god]
        
        output[axis] = axis_value
    
    return output

def apply_saturation_layer(val: float, k: float = 3.0) -> float:
    """
    [V1.4 Saturation]
    Non-linear mapping for high-energy inputs.
    """
    return k * math.tanh(val / k)

def project_tensor_with_saturated_matrix(
    input_vector: Dict[str, float],
    transfer_matrix: Dict[str, Dict[str, float]],
    k_saturation: float = 3.0
) -> Dict[str, float]:
    """
    [Internal/Training] 使用转换矩阵计算5维投影，并应用饱和层。
    """
    # 1. 对输入向量应用饱和处理
    saturated_vector = {
        k: apply_saturation_layer(v, k_saturation) 
        for k, v in input_vector.items()
    }
    return project_tensor_with_matrix(saturated_vector, transfer_matrix)

def calculate_mahalanobis_distance(
    vec: Union[Dict[str, float], np.ndarray],
    centroid: Union[Dict[str, float], np.ndarray],
    covariance_matrix: Optional[np.ndarray] = None,
    inverse_covariance: Optional[np.ndarray] = None
) -> float:
    """
    [V1.5 Precision Physics]
    计算马氏距离 (Mahalanobis Distance)
    
    公式: D_M = sqrt((x - mu)^T * S^-1 * (x - mu))
    
    物理意义：衡量当前张量是否落在格局的"协方差椭球"内。
    """
    # 统一转换为 numpy 数组 (5D: E, O, M, S, R)
    axes = ["E", "O", "M", "S", "R"]
    if isinstance(vec, dict):
        x = np.array([vec.get(a, 0.0) for a in axes])
    else:
        x = vec
        
    if isinstance(centroid, dict):
        mu = np.array([centroid.get(a, 0.0) for a in axes])
    else:
        mu = centroid
        
    delta = x - mu
    
    try:
        if inverse_covariance is not None:
            inv_cov = inverse_covariance
        elif covariance_matrix is not None:
            # 计算逆矩阵 (或者使用伪逆以增加稳定性)
            inv_cov = np.linalg.pinv(covariance_matrix)
        else:
            return float(np.linalg.norm(delta))

        dist_sq = delta.T @ inv_cov @ delta
        return float(np.sqrt(max(0.0, dist_sq)))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"马氏距离计算失败: {e}")
        # 回退到欧式距离
        return float(np.linalg.norm(delta))

def calculate_precision_score(
    similarity: float,
    mahalanobis_dist: float,
    sai: float,
    k_pdf: float = None
) -> float:
    """
    [FDS-V3.0 Precision Score - 增强版算法]
    基于统计流形的精密评分算法
    
    增强版公式（Vector Field + Probability Cloud 双重验证）:
    $$ Score = (W_{sim} \\cdot CosSim + W_{dist} \\cdot e^{-D_M^2 / 2\\sigma^2}) \\cdot Gating(SAI) $$
    
    其中:
    - CosSim: 余弦相似度 (Cosine Similarity) - "方向正确" (The Shape)
      * 物理意义: 五行力量的比例关系，衡量"像不像"
      * 例子: "日主=10, 七杀=20" 和 "日主=1, 七杀=2" 的余弦相似度是1.0
    
    - D_M: 马氏距离 (Mahalanobis Distance) - "位置精准" (The Position)
      * 物理意义: 样本相对于标准模型的偏离程度和概率密度，衡量"真不真"
      * 作用: 区分能量强弱、流形中心与边缘
    
    - G_sai: SAI能量门控 = tanh(SAI / k) - "能量充足" (The Energy)
      * 物理意义: 确保样本有足够的结构总能量
    
    - W_{sim}: 余弦相似度权重 (默认0.7，V3.0提升以更重视形状匹配)
    - W_{dist}: 高斯衰减权重 (默认0.3，V3.0降低以缓解"高分真空")
    - σ: 高斯衰减参数 (默认3.5，V3.0从2.0放宽以允许合理波动)
    - k: SAI门控阈值 (默认0.3，V3.0从0.5放宽)
    
    物理意义：
    - 距离=0 → 分数=1.0 (完美匹配)
    - 距离=2.0 → 分数≈0.8 (可接受偏移)
    - 距离=4.0 → 分数≈0.3 (明显偏离)
    
    Note: [V3.0] 所有参数从 core.config 读取，符合零硬编码原则
    """
    # [FDS-V3.0] 从配置中心读取参数（零硬编码）
    from core.config import config
    
    # 获取权重配置
    weights = config.physics.precision_weights
    w_sim = weights.similarity
    w_dist = weights.distance
    
    # 获取其他参数
    sigma = config.physics.precision_gaussian_sigma
    sai_threshold = config.physics.precision_energy_gate_k
    
    # 1. 高斯核衰减 (Gaussian Kernel)
    # V3.0: σ=3.5，允许真实样本在保持形状相似的前提下有一定的距离波动
    gaussian_decay = math.exp(-(mahalanobis_dist ** 2) / (2 * sigma ** 2))
    
    # 2. 能量门控 (SAI Gate)
    # V3.0: k=0.3，当SAI>=0.6时门控接近1.0，不再惩罚中等能量样本
    # 公式: G_sai = tanh(SAI / k)
    energy_gate = min(1.0, math.tanh(sai / sai_threshold))
    
    # 3. 结构融合 (平衡余弦相似度和高斯衰减)
    # 增强版：方向正确 (Cosine) + 位置精准 (Gaussian) + 能量充足 (Gating)
    score = (w_sim * similarity + w_dist * gaussian_decay) * energy_gate
    
    return float(max(0.0, min(1.0, score)))
