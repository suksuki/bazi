"""
全息命运流形组件 (5D Hyper-Manifold Visualization)
3D+2D视觉模型：将五维张量映射为悬浮在宇宙中的"发光天体"

维度映射：
- X轴：M (物质/财富) - 宽度
- Y轴：O (秩序/权力) - 高度
- Z轴：R (关联/人脉) - 深度
- 大小：E (能级/寿命) - 体积/半径
- 颜色：S (应力/灾难) - 温度/颜色
"""

import plotly.graph_objects as go
from typing import Dict, Optional, List
import numpy as np


def render_5d_manifold(
    current_tensor: Dict[str, float],
    reference_tensor: Optional[Dict[str, float]] = None,
    pattern_state: str = "STABLE",
    pattern_name: str = "A-03"
) -> go.Figure:
    """
    渲染五维超流形（3D天体模型）
    
    Args:
        current_tensor: 当前5维张量 {'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
        reference_tensor: 参考质心（标准格局质心），可选
        pattern_state: 格局状态 ('STABLE', 'COLLAPSED', 'CRYSTALLIZED', 'MUTATED')
        pattern_name: 格局名称
        
    Returns:
        plotly.graph_objects.Figure
    """
    # 提取5维值
    E = current_tensor.get('E', 0.0)  # 能级/寿命 - 大小
    O = current_tensor.get('O', 0.0)  # 秩序/权力 - Y轴高度
    M = current_tensor.get('M', 0.0)  # 物质/财富 - X轴宽度
    R = current_tensor.get('R', 0.0)  # 关联/人脉 - Z轴深度
    S = current_tensor.get('S', 0.0)  # 应力/灾难 - 颜色
    
    # 归一化到[0, 1]范围（如果值在[-1, 1]范围内）
    def normalize_to_01(value):
        """将值归一化到[0, 1]范围"""
        if value < 0:
            return 0.0
        elif value > 1:
            return 1.0
        return value
    
    E_norm = normalize_to_01(abs(E))
    O_norm = normalize_to_01(abs(O))
    M_norm = normalize_to_01(abs(M))
    R_norm = normalize_to_01(abs(R))
    S_norm = normalize_to_01(abs(S))
    
    # 创建3D图形
    fig = go.Figure()
    
    # 1. 绘制参考质心（如果提供）- 半透明云状点
    if reference_tensor:
        ref_E = normalize_to_01(abs(reference_tensor.get('E', 0.0)))
        ref_O = normalize_to_01(abs(reference_tensor.get('O', 0.0)))
        ref_M = normalize_to_01(abs(reference_tensor.get('M', 0.0)))
        ref_R = normalize_to_01(abs(reference_tensor.get('R', 0.0)))
        ref_S = normalize_to_01(abs(reference_tensor.get('S', 0.0)))
        
        # 参考质心使用较小的点和半透明
        fig.add_trace(go.Scatter3d(
            x=[ref_M],
            y=[ref_O],
            z=[ref_R],
            mode='markers',
            name=f'{pattern_name} 标准质心',
            marker=dict(
                size=ref_E * 50,  # 较小的大小
                color=ref_S,
                colorscale='RdYlBu_r',  # 反向：蓝(低S) -> 黄(中S) -> 红(高S)
                colorbar=dict(title="应力 (S)", x=1.15),
                opacity=0.3,
                line=dict(width=1, color='rgba(128, 128, 128, 0.5)')
            ),
            hovertemplate=f'<b>{pattern_name} 标准质心</b><br>' +
                         f'M(财富): {ref_M:.3f}<br>' +
                         f'O(权力): {ref_O:.3f}<br>' +
                         f'R(人脉): {ref_R:.3f}<br>' +
                         f'E(能级): {ref_E:.3f}<br>' +
                         f'S(应力): {ref_S:.3f}<extra></extra>'
        ))
    
    # 2. 绘制用户天体（主数据点）
    marker_size = E_norm * 100 + 20  # 基础大小 + E值缩放（20-120）
    
    # 根据格局状态调整颜色映射
    if pattern_state == 'CRYSTALLIZED':
        # 成格：金色/橙色（贵气）
        color_value = max(0.3, S_norm * 0.7)  # 降低红色，偏向金色
        colorscale = 'YlOrRd'  # 黄-橙-红
    elif pattern_state == 'COLLAPSED':
        # 破格：深红/紫色（危险）
        color_value = min(1.0, S_norm * 1.2)
        colorscale = 'Reds'
    else:
        # 稳定/其他：标准映射
        color_value = S_norm
        colorscale = 'RdYlBu_r'  # 反向：蓝(低S) -> 黄(中S) -> 红(高S)
    
    fig.add_trace(go.Scatter3d(
        x=[M_norm],
        y=[O_norm],
        z=[R_norm],
        mode='markers',
        name='当前状态',
        marker=dict(
            size=marker_size,
            color=color_value,
            colorscale=colorscale,
            colorbar=dict(title="应力 (S)", x=1.15),
            opacity=0.9,
            line=dict(width=3, color='white'),
            symbol='circle'
        ),
        hovertemplate='<b>当前状态</b><br>' +
                     f'M(财富): {M_norm:.3f}<br>' +
                     f'O(权力): {O_norm:.3f}<br>' +
                     f'R(人脉): {R_norm:.3f}<br>' +
                     f'E(能级): {E_norm:.3f}<br>' +
                     f'S(应力): {S_norm:.3f}<br>' +
                     f'状态: {pattern_state}<extra></extra>'
    ))
    
    # 3. 绘制投影线（从天体到地面Y=0，显示"高度"）
    fig.add_trace(go.Scatter3d(
        x=[M_norm, M_norm],
        y=[0, O_norm],  # 从地面到天体高度
        z=[R_norm, R_norm],
        mode='lines',
        name='高度投影',
        line=dict(
            color='rgba(200, 200, 200, 0.5)',
            width=2,
            dash='dash'
        ),
        showlegend=False,
        hovertemplate='<b>高度投影</b><br>权力高度: {y:.3f}<extra></extra>'
    ))
    
    # 4. 绘制地面网格（参考平面）
    ground_size = 1.2
    ground_x = [-ground_size, ground_size, ground_size, -ground_size, -ground_size]
    ground_z = [-ground_size, -ground_size, ground_size, ground_size, -ground_size]
    ground_y = [0, 0, 0, 0, 0]
    
    fig.add_trace(go.Scatter3d(
        x=ground_x,
        y=ground_y,
        z=ground_z,
        mode='lines',
        name='地面',
        line=dict(color='rgba(100, 100, 100, 0.3)', width=1),
        showlegend=False,
        hovertemplate='地面 (Y=0)<extra></extra>'
    ))
    
    # 5. 设置布局
    fig.update_layout(
        title=dict(
            text=f'🪐 全息命运流形 | {pattern_name} | 状态: {pattern_state}',
            x=0.5,
            font=dict(size=18)
        ),
        scene=dict(
            xaxis=dict(
                title='M (物质/财富)',
                range=[-0.1, 1.1],
                backgroundcolor='rgba(20, 20, 30, 0.1)',
                gridcolor='rgba(100, 100, 100, 0.2)',
                showbackground=True
            ),
            yaxis=dict(
                title='O (秩序/权力)',
                range=[-0.1, 1.1],
                backgroundcolor='rgba(20, 20, 30, 0.1)',
                gridcolor='rgba(100, 100, 100, 0.2)',
                showbackground=True
            ),
            zaxis=dict(
                title='R (关联/人脉)',
                range=[-0.1, 1.1],
                backgroundcolor='rgba(20, 20, 30, 0.1)',
                gridcolor='rgba(100, 100, 100, 0.2)',
                showbackground=True
            ),
            aspectmode='cube',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5),
                center=dict(x=0, y=0, z=0)
            )
        ),
        height=700,
        margin=dict(l=0, r=0, t=50, b=0),
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        )
    )
    
    return fig


def get_manifold_description(
    tensor: Dict[str, float],
    pattern_state: str = "STABLE"
) -> Dict[str, str]:
    """
    生成流形描述文本（用于UI显示）
    
    Returns:
        包含描述信息的字典
    """
    E = abs(tensor.get('E', 0.0))
    O = abs(tensor.get('O', 0.0))
    M = abs(tensor.get('M', 0.0))
    R = abs(tensor.get('R', 0.0))
    S = abs(tensor.get('S', 0.0))
    
    # 能级质量描述
    if E > 0.7:
        mass_desc = "巨大 (Big Planet)"
    elif E > 0.4:
        mass_desc = "中等 (Medium)"
    else:
        mass_desc = "较小 (Small)"
    
    # 社会高度描述
    if O > 0.7:
        altitude_desc = "平流层 (Stratosphere)"
    elif O > 0.4:
        altitude_desc = "中空 (Mid-Air)"
    else:
        altitude_desc = "贴地 (Ground Level)"
    
    # 核心温度描述
    if S > 0.7:
        temp_desc = "极热 (Critical)"
    elif S > 0.4:
        temp_desc = "温热 (Warm)"
    else:
        temp_desc = "凉爽 (Cool)"
    
    # 形态描述
    if O > 0.7 and M < 0.3:
        shape_desc = "方尖碑/利剑 (Obelisk)"
    elif M > 0.7 and O < 0.3:
        shape_desc = "飞碟/巨盘 (Flatbed)"
    elif R > 0.7:
        shape_desc = "球体 (Sphere)"
    else:
        shape_desc = "不规则体 (Irregular)"
    
    return {
        'mass': mass_desc,
        'altitude': altitude_desc,
        'temperature': temp_desc,
        'shape': shape_desc,
        'energy': f"{E:.3f}",
        'order': f"{O:.3f}",
        'matter': f"{M:.3f}",
        'resonance': f"{R:.3f}",
        'stress': f"{S:.3f}"
    }

