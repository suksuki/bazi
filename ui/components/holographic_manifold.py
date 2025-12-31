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
    [V2.0] 渲染全息星图流形 (3D Tensor Crystal)
    将5维张量映射为3D空间中的五角星体能量场
    """
    # 1. 定义5维轴在3D空间中的向量 (Fibonacci Sphere Distribution)
    # 使用斐波那契球面算法在球面上生成数学级均匀分布的5个点
    # 彻底实现“立体空间五个均分的分叉”，无极性，全方位辐射
    import math
    AXES = {}
    axis_keys = ['E', 'O', 'M', 'S', 'R']
    
    phi = math.pi * (3. - math.sqrt(5.))  # 黄金角
    
    for i, key in enumerate(axis_keys):
        # y 从 1 (顶) 降到 -1 (底)
        y = 1 - (i / float(len(axis_keys) - 1)) * 2 
        radius = math.sqrt(1 - y * y)
        theta = phi * i
        
        x = math.cos(theta) * radius
        z = math.sin(theta) * radius
        
        # 调整坐标系：让第一个点(i=0, y=1)对应Z轴向上
        # 原算法生成的y轴对应我们的Z轴
        AXES[key] = np.array([x, z, y]) 
    
    # 2. 计算点位
    def get_points(tensor):
        pts = []
        for key in axis_keys:
            vector = AXES[key]
            val = abs(tensor.get(key, 0.0))
            # 缩放: 调整为原尺寸的 30%
            # 原公式: 0.2 + val * 1.5
            # 新公式: (0.2 + val * 1.5) * 0.3 = 0.06 + val * 0.45
            scaled_val = 0.06 + val * 0.45
            pts.append(vector * scaled_val)
        return np.array(pts)

    curr_pts = get_points(current_tensor)
    center = np.array([0, 0, 0])
    
    fig = go.Figure()

    # 绘制坐标轴 (Glowing Axes) - 从原点射出的光束
    for key, vec in AXES.items():
        fig.add_trace(go.Scatter3d(
            x=[0, vec[0]*1.4], y=[0, vec[1]*1.4], z=[0, vec[2]*1.4],
            mode='lines+text',
            text=["", f"<b>{key}</b>"],
            line=dict(color='rgba(255,255,255,0.2)', width=2),
            textfont=dict(color='#40e0d0', size=12),
            showlegend=False
        ))

    # 3. 绘制标准/参考格局 (Wireframe Hull)
    if reference_tensor:
        ref_pts = get_points(reference_tensor)
        # 使用 Mesh3d 的 alphahull=0 来绘制凸包轮廓
        fig.add_trace(go.Mesh3d(
            x=ref_pts[:, 0], y=ref_pts[:, 1], z=ref_pts[:, 2],
            alphahull=0, # 凸包
            color='rgba(64, 224, 208, 0.1)',
            opacity=0.1,
            name=f'标准 {pattern_name} 场域',
            showscale=False
        ))

    # 4. 绘制用户命运晶体 (Fate Crystal - Solid Hull)
    # 将中心点加入点云，确保晶体是有核心的实体
    all_verts = np.vstack([center, curr_pts])
    
    # 根据状态选择颜色
    color_map = {
        'CRYSTALLIZED': '#FFD700', # Gold
        'COLLAPSED': '#FF4B4B',    # Red
        'STABLE': '#40E0D0',       # Turquoise
        'ACTIVATED': '#F0F',       # Purple
        'STANDARD': '#40E0D0',     # Turquoise (Same as stable)
        'SINGULARITY': '#FFD700',  # Gold (X1 Singularity)
        'MARGINAL': '#888',        # Grey
        'BROKEN': '#333'           # Dark Grey
    }
    main_color = color_map.get(pattern_state, '#40E0D0')

    fig.add_trace(go.Mesh3d(
        x=all_verts[:, 0], y=all_verts[:, 1], z=all_verts[:, 2],
        alphahull=0, # 自动计算包含所有点(含中心)的凸包
        opacity=0.8,
        color=main_color,
        name='当前命运张量 (Fate Tensor)',
        flatshading=True,
        lighting=dict(ambient=0.5, diffuse=1, specular=1, roughness=0.1),
        hoverinfo='skip'
    ))

    # 添加颗粒顶点强化 (Dimensional Particles with unique colors)
    # E: White, O: Gold, M: Green, S: Red, R: Blue
    dim_colors = ['#ffffff', '#ffd700', '#00ff7f', '#ff4b4b', '#4169e1']
    
    fig.add_trace(go.Scatter3d(
        x=curr_pts[:, 0], y=curr_pts[:, 1], z=curr_pts[:, 2],
        mode='markers',
        marker=dict(
            size=3, 
            color=dim_colors,
            symbol='circle',
            line=dict(color='rgba(255,255,255,0.8)', width=1)
        ),
        showlegend=False,
        hovertemplate="维度: %{text}<br>强度: %{y:.2f}<extra></extra>",
        text=['E (能级)', 'O (秩序)', 'M (物质)', 'S (应力)', 'R (关联)']
    ))

    # 5. 布局优化
    fig.update_layout(
        scene=dict(
            xaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False, title=""),
            yaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False, title=""),
            zaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False, title=""),
            camera=dict(eye=dict(x=1.5, y=1, z=1.5)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=1)
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(yanchor="top", y=0.9, xanchor="left", x=0.1, font=dict(color="white"))
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

