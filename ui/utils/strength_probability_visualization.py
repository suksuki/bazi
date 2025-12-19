"""
旺衰概率波函数可视化 (Strength Probability Wave Visualization)
===========================================================

绘制V10.0的Sigmoid激活曲线，展示旺衰判定的概率分布。

作者: Antigravity Team
版本: V10.0
日期: 2025-01-17
"""

import numpy as np
import plotly.graph_objects as go
from typing import Optional


def sigmoid(x: float, center: float, width: float) -> float:
    """
    Sigmoid 函数
    
    Args:
        x: 输入值（能量占比）
        center: 中心点（阈值）
        width: 宽度参数（控制曲线陡峭程度，值越小越陡）
    
    Returns:
        Sigmoid 输出值 [0, 1]
    """
    # 使用标准的 sigmoid 函数：1 / (1 + exp(-k * (x - center)))
    # width 越大，k 越小，曲线越平缓
    k = 10.0 / width  # 控制陡峭度
    return 1.0 / (1.0 + np.exp(-k * (x - center)))


def plot_strength_probability_curve(
    energy_threshold_center: float = 2.89,
    phase_transition_width: float = 10.0,
    current_case_energy: Optional[float] = None,
    energy_range: tuple = (0.0, 10.0),
    num_points: int = 200
) -> go.Figure:
    """
    绘制旺衰概率波函数（Sigmoid曲线）
    
    Args:
        energy_threshold_center: 能量阈值中心点（相变临界点）
        phase_transition_width: 相变宽度（控制曲线陡峭程度）
        current_case_energy: 当前案例的能量值（用于标记）
        energy_range: 能量范围（min, max）
        num_points: 点数
    
    Returns:
        Plotly Figure 对象
    """
    energy_values = np.linspace(energy_range[0], energy_range[1], num_points)
    probability_values = [sigmoid(e, energy_threshold_center, phase_transition_width) for e in energy_values]
    
    fig = go.Figure()
    
    # Sigmoid 曲线
    fig.add_trace(go.Scatter(
        x=energy_values,
        y=probability_values,
        mode='lines',
        name='身强概率 (Probability of Strong)',
        line=dict(color='#3498DB', width=3),
        hovertemplate='能量: %{x:.2f}<br>身强概率: %{y:.2%}<extra></extra>',
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.2)'
    ))
    
    # 标记当前案例的能量位置
    if current_case_energy is not None:
        current_prob = sigmoid(current_case_energy, energy_threshold_center, phase_transition_width)
        fig.add_trace(go.Scatter(
            x=[current_case_energy],
            y=[current_prob],
            mode='markers',
            name='当前案例',
            marker=dict(
                color='#E74C3C',
                size=15,
                symbol='star',
                line=dict(color='white', width=2)
            ),
            hovertemplate=f'当前案例<br>能量: {current_case_energy:.2f}<br>身强概率: {current_prob:.2%}<extra></extra>'
        ))
        
        # 添加垂直参考线
        fig.add_vline(
            x=current_case_energy,
            line_dash="dot",
            line_color="#E74C3C",
            annotation_text=f"当前案例: {current_case_energy:.2f}",
            annotation_position="top right"
        )
    
    # 阈值中心线
    threshold_prob = sigmoid(energy_threshold_center, energy_threshold_center, phase_transition_width)
    fig.add_vline(
        x=energy_threshold_center,
        line_dash="dash",
        line_color="#F39C12",
        annotation_text=f"临界点: {energy_threshold_center:.2f}",
        annotation_position="top left"
    )
    
    # 添加概率50%的水平线
    fig.add_hline(
        y=0.5,
        line_dash="dot",
        line_color="#95A5A6",
        annotation_text="50%概率线",
        annotation_position="right"
    )
    
    # 标注区域
    # 身弱区域 (概率 < 0.5)
    fig.add_annotation(
        x=energy_range[0] + (energy_threshold_center - energy_range[0]) / 2,
        y=0.25,
        text="身弱区域<br>(Weak Zone)",
        showarrow=False,
        font=dict(color='#E74C3C', size=12),
        bgcolor='rgba(231, 76, 60, 0.1)',
        bordercolor='#E74C3C',
        borderwidth=1,
        borderpad=4
    )
    
    # 身强区域 (概率 > 0.5)
    fig.add_annotation(
        x=energy_threshold_center + (energy_range[1] - energy_threshold_center) / 2,
        y=0.75,
        text="身强区域<br>(Strong Zone)",
        showarrow=False,
        font=dict(color='#27AE60', size=12),
        bgcolor='rgba(39, 174, 96, 0.1)',
        bordercolor='#27AE60',
        borderwidth=1,
        borderpad=4
    )
    
    fig.update_layout(
        title=f"旺衰概率波函数 (Strength Probability Wave Function)<br>临界点: {energy_threshold_center:.2f}, 带宽: {phase_transition_width:.1f}",
        xaxis_title="日主能量占比 (Day Master Energy Ratio)",
        yaxis_title="身强概率 (Probability of Strong)",
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        height=450,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=100)
    )
    
    return fig

