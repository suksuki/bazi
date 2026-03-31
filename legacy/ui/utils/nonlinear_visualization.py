"""
非线性响应曲线可视化 (Nonlinear Response Curve Visualization)
==========================================================

绘制非线性参数的响应曲线，帮助用户直观理解参数对输出曲线的影响。

作者: Antigravity Team
版本: V10.0
日期: 2025-01-17
"""

import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional


def plot_nonlinear_damping_curve(
    threshold: float = 80.0,
    damping_rate: float = 0.3,
    max_value: float = 100.0,
    input_range: tuple = (-100, 100),
    num_points: int = 200
) -> go.Figure:
    """
    绘制非线性阻尼响应曲线
    
    Args:
        threshold: 阻尼阈值
        damping_rate: 阻尼率（0-1，值越大阻尼越强）
        max_value: 最大允许值（硬上限）
        input_range: 输入范围（min, max）
        num_points: 点数
    
    Returns:
        Plotly Figure 对象
    """
    input_energy = np.linspace(input_range[0], input_range[1], num_points)
    output_index = []
    
    for energy in input_energy:
        if energy > threshold:
            # 超过阈值后应用阻尼
            excess = energy - threshold
            damped_excess = excess * (1 - damping_rate)
            output = threshold + damped_excess
            output = min(output, max_value)  # 硬上限
        else:
            # 未超过阈值，线性输出
            output = energy
        output_index.append(output)
    
    fig = go.Figure()
    
    # 阻尼曲线
    fig.add_trace(go.Scatter(
        x=input_energy,
        y=output_index,
        mode='lines',
        name='Damped Curve',
        line=dict(color='#FF6B6B', width=3),
        hovertemplate='输入: %{x:.1f}<br>输出: %{y:.1f}<extra></extra>'
    ))
    
    # 线性参考线（无阻尼）
    fig.add_trace(go.Scatter(
        x=input_energy,
        y=input_energy,
        mode='lines',
        name='Linear (No Damping)',
        line=dict(color='#95A5A6', width=2, dash='dash'),
        hovertemplate='输入: %{x:.1f}<br>输出: %{y:.1f}<extra></extra>'
    ))
    
    # 阈值线
    fig.add_vline(
        x=threshold,
        line_dash="dot",
        line_color="#3498DB",
        annotation_text=f"阈值: {threshold}",
        annotation_position="top right"
    )
    
    # 最大上限线
    if max_value < input_range[1]:
        fig.add_hline(
            y=max_value,
            line_dash="dot",
            line_color="#E74C3C",
            annotation_text=f"上限: {max_value}",
            annotation_position="top left"
        )
    
    fig.update_layout(
        title="非线性阻尼响应曲线 (Nonlinear Damping Response Curve)",
        xaxis_title="输入能量 (Input Energy)",
        yaxis_title="输出指数 (Output Index)",
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def plot_seal_multiplier_curve(
    seal_bonus: float = 43.76,
    seal_multiplier: float = 0.8538,
    input_range: tuple = (-100, 100),
    num_points: int = 200
) -> go.Figure:
    """
    绘制印星乘数响应曲线
    
    Args:
        seal_bonus: 印星帮身直接加成
        seal_multiplier: 印星帮身乘数
        input_range: 输入范围
        num_points: 点数
    
    Returns:
        Plotly Figure 对象
    """
    input_energy = np.linspace(input_range[0], input_range[1], num_points)
    output_index = []
    
    for energy in input_energy:
        # 先加 bonus，再乘 multiplier
        output = (energy + seal_bonus) * seal_multiplier
        output_index.append(output)
    
    fig = go.Figure()
    
    # 印星修正曲线
    fig.add_trace(go.Scatter(
        x=input_energy,
        y=output_index,
        mode='lines',
        name='Seal Corrected',
        line=dict(color='#9B59B6', width=3),
        hovertemplate='输入: %{x:.1f}<br>输出: %{y:.1f}<br>加成: {seal_bonus:.1f}<br>乘数: {seal_multiplier:.4f}<extra></extra>'
    ))
    
    # 原始曲线（无修正）
    fig.add_trace(go.Scatter(
        x=input_energy,
        y=input_energy,
        mode='lines',
        name='Original (No Correction)',
        line=dict(color='#95A5A6', width=2, dash='dash'),
        hovertemplate='输入: %{x:.1f}<br>输出: %{y:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"印星乘数响应曲线 (Seal Multiplier Response Curve)<br>Bonus: {seal_bonus:.2f}, Multiplier: {seal_multiplier:.4f}",
        xaxis_title="输入能量 (Input Energy)",
        yaxis_title="输出指数 (Output Index)",
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def plot_opportunity_scaling_curve(
    opportunity_scaling: float = 1.8952,
    base_opportunity: float = 40.0,
    input_range: tuple = (-100, 100),
    num_points: int = 200
) -> go.Figure:
    """
    绘制机会缩放响应曲线
    
    Args:
        opportunity_scaling: 机会加成缩放比例
        base_opportunity: 基础机会加成
        input_range: 输入范围
        num_points: 点数
    
    Returns:
        Plotly Figure 对象
    """
    input_energy = np.linspace(input_range[0], input_range[1], num_points)
    output_index = []
    
    for energy in input_energy:
        # 应用机会缩放
        opportunity_bonus = base_opportunity * opportunity_scaling
        output = energy + opportunity_bonus
        output_index.append(output)
    
    fig = go.Figure()
    
    # 机会缩放曲线
    fig.add_trace(go.Scatter(
        x=input_energy,
        y=output_index,
        mode='lines',
        name='Opportunity Scaled',
        line=dict(color='#F39C12', width=3),
        hovertemplate='输入: %{x:.1f}<br>输出: %{y:.1f}<br>加成: {opportunity_bonus:.1f}<extra></extra>'
    ))
    
    # 原始曲线
    fig.add_trace(go.Scatter(
        x=input_energy,
        y=input_energy,
        mode='lines',
        name='Original (No Scaling)',
        line=dict(color='#95A5A6', width=2, dash='dash'),
        hovertemplate='输入: %{x:.1f}<br>输出: %{y:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"机会缩放响应曲线 (Opportunity Scaling Response Curve)<br>Scaling: {opportunity_scaling:.4f}, Base: {base_opportunity:.1f}",
        xaxis_title="输入能量 (Input Energy)",
        yaxis_title="输出指数 (Output Index)",
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

