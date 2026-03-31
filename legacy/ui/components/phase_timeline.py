"""
全息格局动态时间轴组件
显示O轴和S轴在时间序列中的变化，并标记相变事件
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
import streamlit as st


def render_phase_timeline(
    timeline_data: List[Dict],
    show_alpha: bool = True,
    show_projection: bool = True
) -> go.Figure:
    """
    渲染动态时间轴
    
    Args:
        timeline_data: 时间序列数据，每个元素包含：
            - year: int
            - year_pillar: str
            - alpha: float
            - pattern_state: dict with 'state' key
            - projection: dict with 'O' and 'S' keys
        show_alpha: 是否显示Alpha曲线
        show_projection: 是否显示O轴和S轴曲线
        
    Returns:
        plotly.graph_objects.Figure
    """
    # 提取数据
    years = [d['year'] for d in timeline_data]
    year_pillars = [d.get('year_pillar', '') for d in timeline_data]
    alphas = [d.get('alpha', 0.0) for d in timeline_data]
    o_values = [d.get('projection', {}).get('O', 0.0) for d in timeline_data]
    s_values = [d.get('projection', {}).get('S', 0.0) for d in timeline_data]
    states = [d.get('pattern_state', {}).get('state', 'STABLE') for d in timeline_data]
    
    # 创建子图
    num_subplots = sum([show_alpha, show_projection])
    if num_subplots == 0:
        num_subplots = 1
    
    # 构建subplot_titles列表（只包含非None的标题）
    subplot_titles_list = []
    if show_alpha:
        subplot_titles_list.append('结构完整性 Alpha')
    if show_projection:
        subplot_titles_list.append('五维投影：秩序轴 (O) vs 应力轴 (S)')
    
    # 如果没有标题，使用None
    if not subplot_titles_list:
        subplot_titles_list = None
    
    fig = make_subplots(
        rows=num_subplots,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=subplot_titles_list
    )
    
    subplot_idx = 1
    
    # 1. Alpha曲线（如果启用）
    if show_alpha:
        fig.add_trace(
            go.Scatter(
                x=years,
                y=alphas,
                mode='lines+markers',
                name='Alpha (完整性)',
                line=dict(color='#2196F3', width=3),
                marker=dict(size=8, color='#2196F3'),
                hovertemplate='<b>%{x}年</b><br>Alpha: %{y:.4f}<extra></extra>'
            ),
            row=subplot_idx,
            col=1
        )
        
        # 添加Alpha阈值线
        fig.add_hline(
            y=0.45,
            line_dash="dash",
            line_color="red",
            annotation_text="破格阈值 (0.45)",
            annotation_position="right",
            row=subplot_idx,
            col=1
        )
        
        subplot_idx += 1
    
    # 2. O轴和S轴曲线（如果启用）
    if show_projection:
        # O轴（秩序轴）- 金色
        fig.add_trace(
            go.Scatter(
                x=years,
                y=o_values,
                mode='lines+markers',
                name='秩序轴 (O)',
                line=dict(color='#FFD700', width=3),
                marker=dict(size=8, color='#FFD700'),
                hovertemplate='<b>%{x}年</b><br>O轴: %{y:.4f}<extra></extra>'
            ),
            row=subplot_idx,
            col=1
        )
        
        # S轴（应力轴）- 红色
        fig.add_trace(
            go.Scatter(
                x=years,
                y=s_values,
                mode='lines+markers',
                name='应力轴 (S)',
                line=dict(color='#F44336', width=3),
                marker=dict(size=8, color='#F44336'),
                hovertemplate='<b>%{x}年</b><br>S轴: %{y:.4f}<extra></extra>'
            ),
            row=subplot_idx,
            col=1
        )
    
    # 标记相变事件
    for i, (year, state) in enumerate(zip(years, states)):
        if state == 'COLLAPSED':
            # 红色竖线标记破格
            fig.add_vline(
                x=year,
                line_dash="dash",
                line_color="red",
                line_width=2,
                annotation_text="⚡ COLLAPSED",
                annotation_position="top",
                annotation=dict(
                    bgcolor="rgba(244, 67, 54, 0.8)",
                    bordercolor="red",
                    font=dict(color="white", size=10)
                )
            )
        elif state == 'CRYSTALLIZED':
            # 金色竖线标记成格
            fig.add_vline(
                x=year,
                line_dash="dash",
                line_color="#FFD700",
                line_width=2,
                annotation_text="💎 CRYSTALLIZED",
                annotation_position="top",
                annotation=dict(
                    bgcolor="rgba(255, 215, 0, 0.8)",
                    bordercolor="#FFD700",
                    font=dict(color="black", size=10)
                )
            )
        elif state == 'MUTATED':
            # 紫色竖线标记变异
            fig.add_vline(
                x=year,
                line_dash="dash",
                line_color="#9C27B0",
                line_width=2,
                annotation_text="🔮 MUTATED",
                annotation_position="top",
                annotation=dict(
                    bgcolor="rgba(156, 39, 176, 0.8)",
                    bordercolor="#9C27B0",
                    font=dict(color="white", size=10)
                )
            )
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text='动态演化时间轴 (2024-2035)',
            x=0.5,
            font=dict(size=18)
        ),
        height=600 if num_subplots > 1 else 400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    # 更新x轴
    fig.update_xaxes(
        title_text="年份",
        tickmode='linear',
        tick0=years[0],
        dtick=1
    )
    
    # 更新y轴标签
    if show_alpha:
        fig.update_yaxes(title_text="Alpha值", range=[0, 1.1], row=1, col=1)
    if show_projection:
        fig.update_yaxes(title_text="投影值", row=subplot_idx, col=1)
    
    return fig


def render_simple_timeline(
    years: List[int],
    o_values: List[float],
    s_values: List[float],
    critical_events: Optional[List[Dict]] = None
) -> go.Figure:
    """
    简化版时间轴（只显示O和S轴）
    
    Args:
        years: 年份列表
        o_values: O轴值列表
        s_values: S轴值列表
        critical_events: 关键事件列表，每个元素包含 {'year': int, 'type': str, 'label': str}
        
    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()
    
    # O轴曲线
    fig.add_trace(go.Scatter(
        x=years,
        y=o_values,
        mode='lines+markers',
        name='秩序轴 (O)',
        line=dict(color='#FFD700', width=3),
        marker=dict(size=8)
    ))
    
    # S轴曲线
    fig.add_trace(go.Scatter(
        x=years,
        y=s_values,
        mode='lines+markers',
        name='应力轴 (S)',
        line=dict(color='#F44336', width=3),
        marker=dict(size=8)
    ))
    
    # 标记关键事件
    if critical_events:
        for event in critical_events:
            year = event.get('year')
            event_type = event.get('type', '')
            label = event.get('label', '')
            
            color_map = {
                'COLLAPSED': 'red',
                'CRYSTALLIZED': '#FFD700',
                'MUTATED': '#9C27B0'
            }
            color = color_map.get(event_type, 'gray')
            
            fig.add_vline(
                x=year,
                line_dash="dash",
                line_color=color,
                line_width=2,
                annotation_text=label,
                annotation_position="top"
            )
    
    fig.update_layout(
        title='五维投影时间轴',
        xaxis_title='年份',
        yaxis_title='投影值',
        hovermode='x unified',
        height=400
    )
    
    return fig

