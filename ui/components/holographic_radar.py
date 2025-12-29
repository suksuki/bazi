"""
全息格局五维雷达图组件
显示当前张量与标准格局质心的对比
"""

import plotly.graph_objects as go
from typing import Dict, Optional, List
import streamlit as st


def render_5d_radar(
    current_tensor: Dict[str, float],
    reference_tensor: Optional[Dict[str, float]] = None,
    pattern_state: str = "STABLE",
    pattern_name: str = "A-03"
) -> go.Figure:
    """
    渲染五维雷达图
    
    Args:
        current_tensor: 当前5维张量 {'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
        reference_tensor: 参考质心（标准格局质心），可选
        pattern_state: 格局状态 ('STABLE', 'COLLAPSED', 'CRYSTALLIZED', 'MUTATED')
        pattern_name: 格局名称
        
    Returns:
        plotly.graph_objects.Figure
    """
    """
    渲染五维雷达图
    
    Args:
        current_tensor: 当前5维张量 {'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
        reference_tensor: 参考质心（标准格局质心），可选
        pattern_state: 格局状态 ('STABLE', 'COLLAPSED', 'CRYSTALLIZED', 'MUTATED')
        pattern_name: 格局名称
        
    Returns:
        plotly.graph_objects.Figure
    """
    # 五维轴标签
    categories = ['能级轴 (E)', '秩序轴 (O)', '物质轴 (M)', '应力轴 (S)', '关联轴 (R)']
    axes = ['E', 'O', 'M', 'S', 'R']
    
    # 提取当前张量值
    current_values = [current_tensor.get(axis, 0.0) for axis in axes]
    
    # 根据格局状态选择颜色
    color_map = {
        'STABLE': '#4CAF50',      # 绿色 - 稳定
        'CRYSTALLIZED': '#FFD700',  # 金色 - 成格
        'COLLAPSED': '#F44336',     # 红色 - 破格
        'MUTATED': '#9C27B0',       # 紫色 - 变异
        'CRITICAL': '#FF9800'       # 橙色 - 临界
    }
    user_color = color_map.get(pattern_state, '#2196F3')
    
    # 创建雷达图
    fig = go.Figure()
    
    # 1. 绘制参考质心（背景阴影，如果提供）
    if reference_tensor:
        ref_values = [reference_tensor.get(axis, 0.0) for axis in axes]
        fig.add_trace(go.Scatterpolar(
            r=ref_values,
            theta=categories,
            fill='toself',
            name=f'{pattern_name} 标准质心',
            line=dict(color='rgba(128, 128, 128, 0.3)', width=1),
            fillcolor='rgba(128, 128, 128, 0.1)',
            opacity=0.5
        ))
    
    # 2. 绘制当前张量（前景实线）
    # 将hex颜色转换为rgba格式（添加透明度）
    def hex_to_rgba(hex_color, alpha=0.5):
        """将hex颜色转换为rgba格式"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
    
    fig.add_trace(go.Scatterpolar(
        r=current_values,
        theta=categories,
        fill='toself',
        name='当前状态',
        line=dict(color=user_color, width=3),
        fillcolor=hex_to_rgba(user_color, alpha=0.5),  # 使用rgba格式
        opacity=0.7
    ))
    
    # 3. 设置布局
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-0.5, 0.7],  # 根据实际数据范围调整
                showline=True,
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.3)',
                tickmode='linear',
                tick0=-0.5,
                dtick=0.2
            ),
            angularaxis=dict(
                rotation=90,  # 从顶部开始
                direction='counterclockwise'
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        title=dict(
            text=f'五维全息投影 | 格局状态: {pattern_state}',
            x=0.5,
            font=dict(size=16)
        ),
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


# 兼容性别名（用于quantum_lab.py）
def render_holographic_radar(
    resonance: Optional[Dict] = None,
    unified_metrics: Optional[Dict] = None,
    remedy: Optional[Dict] = None,
    verdict_oracle: Optional[Dict] = None
) -> go.Figure:
    """
    兼容性函数：用于quantum_lab.py的旧接口
    
    Args:
        resonance: 共振数据（可选）
        unified_metrics: 统一指标（可选）
        remedy: 补救措施（可选）
        verdict_oracle: 判词（可选）
        
    Returns:
        plotly.graph_objects.Figure
    """
    # 从unified_metrics或resonance中提取5维张量
    current_tensor = {}
    
    if unified_metrics:
        # 尝试从unified_metrics中提取5维数据
        current_tensor = {
            'E': unified_metrics.get('E', 0.0),
            'O': unified_metrics.get('O', 0.0),
            'M': unified_metrics.get('M', 0.0),
            'S': unified_metrics.get('S', 0.0),
            'R': unified_metrics.get('R', 0.0)
        }
    elif resonance:
        # 尝试从resonance中提取
        current_tensor = {
            'E': resonance.get('E', 0.0),
            'O': resonance.get('O', 0.0),
            'M': resonance.get('M', 0.0),
            'S': resonance.get('S', 0.0),
            'R': resonance.get('R', 0.0)
        }
    else:
        # 默认值
        current_tensor = {'E': 0.0, 'O': 0.0, 'M': 0.0, 'S': 0.0, 'R': 0.0}
    
    # 确定格局状态
    pattern_state = "STABLE"
    if verdict_oracle:
        verdict = verdict_oracle.get('verdict', '')
        if '破格' in verdict or '崩' in verdict:
            pattern_state = "COLLAPSED"
        elif '成格' in verdict or '贵' in verdict:
            pattern_state = "CRYSTALLIZED"
    
    # 调用主函数
    return render_5d_radar(
        current_tensor=current_tensor,
        reference_tensor=None,
        pattern_state=pattern_state,
        pattern_name="格局分析"
    )


def render_radar_comparison(
    tensors: List[Dict[str, float]],
    labels: List[str],
    reference_tensor: Optional[Dict[str, float]] = None
) -> go.Figure:
    """
    渲染多个张量的对比雷达图（用于时间序列对比）
    
    Args:
        tensors: 多个5维张量列表
        labels: 对应的标签列表
        reference_tensor: 参考质心
        
    Returns:
        plotly.graph_objects.Figure
    """
    categories = ['能级轴 (E)', '秩序轴 (O)', '物质轴 (M)', '应力轴 (S)', '关联轴 (R)']
    axes = ['E', 'O', 'M', 'S', 'R']
    
    fig = go.Figure()
    
    # 绘制参考质心
    if reference_tensor:
        ref_values = [reference_tensor.get(axis, 0.0) for axis in axes]
        fig.add_trace(go.Scatterpolar(
            r=ref_values,
            theta=categories,
            fill='toself',
            name='标准质心',
            line=dict(color='rgba(128, 128, 128, 0.3)', width=1),
            fillcolor='rgba(128, 128, 128, 0.1)',
            opacity=0.5
        ))
    
    # 绘制多个张量
    def hex_to_rgba(hex_color, alpha=0.5):
        """将hex颜色转换为rgba格式"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
    
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0']
    for i, (tensor, label) in enumerate(zip(tensors, labels)):
        values = [tensor.get(axis, 0.0) for axis in axes]
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=label,
            line=dict(color=color, width=2),
            fillcolor=hex_to_rgba(color, alpha=0.25),  # 使用rgba格式
            opacity=0.6
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-0.5, 0.7],
                showline=True,
                showgrid=True,
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            angularaxis=dict(
                rotation=90,
                direction='counterclockwise'
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        title=dict(
            text='五维张量对比',
            x=0.5,
            font=dict(size=16)
        ),
        height=500
    )
    
    return fig
