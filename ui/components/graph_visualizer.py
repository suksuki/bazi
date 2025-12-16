"""
Graph Network Topology Visualizer
==================================

用于可视化图网络引擎的拓扑结构和能量流动。

使用 Plotly 或 streamlit-agraph 进行网络图渲染。
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import Dict, List, Any, Optional
import networkx as nx


def _calculate_ten_god(day_master: str, char: str, is_stem: bool = True) -> Optional[str]:
    """
    计算十神（根据日主和字符）。
    
    Args:
        day_master: 日主天干
        char: 天干或地支字符
        is_stem: 是否为天干（True）或地支（False）
    
    Returns:
        十神名称或None
    """
    if not day_master or not char:
        return None
    
    # 十神映射表（基于日主）
    ten_gods_map = {
        "甲": {"甲": "BiJian", "乙": "JieCai", "丙": "ShiShen", "丁": "ShangGuan", 
               "戊": "PianCai", "己": "ZhengCai", "庚": "QiSha", "辛": "ZhengGuan", 
               "壬": "PianYin", "癸": "ZhengYin"},
        "乙": {"乙": "BiJian", "甲": "JieCai", "丁": "ShiShen", "丙": "ShangGuan", 
               "己": "PianCai", "戊": "ZhengCai", "辛": "QiSha", "庚": "ZhengGuan", 
               "癸": "PianYin", "壬": "ZhengYin"},
        "丙": {"丙": "BiJian", "丁": "JieCai", "戊": "ShiShen", "己": "ShangGuan", 
               "庚": "PianCai", "辛": "ZhengCai", "壬": "QiSha", "癸": "ZhengGuan", 
               "甲": "PianYin", "乙": "ZhengYin"},
        "丁": {"丁": "BiJian", "丙": "JieCai", "己": "ShiShen", "戊": "ShangGuan", 
               "辛": "PianCai", "庚": "ZhengCai", "癸": "QiSha", "壬": "ZhengGuan", 
               "乙": "PianYin", "甲": "ZhengYin"},
        "戊": {"戊": "BiJian", "己": "JieCai", "庚": "ShiShen", "辛": "ShangGuan", 
               "壬": "PianCai", "癸": "ZhengCai", "甲": "QiSha", "乙": "ZhengGuan", 
               "丙": "PianYin", "丁": "ZhengYin"},
        "己": {"己": "BiJian", "戊": "JieCai", "辛": "ShiShen", "庚": "ShangGuan", 
               "癸": "PianCai", "壬": "ZhengCai", "乙": "QiSha", "甲": "ZhengGuan", 
               "丁": "PianYin", "丙": "ZhengYin"},
        "庚": {"庚": "BiJian", "辛": "JieCai", "壬": "ShiShen", "癸": "ShangGuan", 
               "甲": "PianCai", "乙": "ZhengCai", "丙": "QiSha", "丁": "ZhengGuan", 
               "戊": "PianYin", "己": "ZhengYin"},
        "辛": {"辛": "BiJian", "庚": "JieCai", "癸": "ShiShen", "壬": "ShangGuan", 
               "乙": "PianCai", "甲": "ZhengCai", "丁": "QiSha", "丙": "ZhengGuan", 
               "己": "PianYin", "戊": "ZhengYin"},
        "壬": {"壬": "BiJian", "癸": "JieCai", "甲": "ShiShen", "乙": "ShangGuan", 
               "丙": "PianCai", "丁": "ZhengCai", "戊": "QiSha", "己": "ZhengGuan", 
               "庚": "PianYin", "辛": "ZhengYin"},
        "癸": {"癸": "BiJian", "壬": "JieCai", "乙": "ShiShen", "甲": "ShangGuan", 
               "丁": "PianCai", "丙": "ZhengCai", "己": "QiSha", "戊": "ZhengGuan", 
               "辛": "PianYin", "庚": "ZhengYin"},
    }
    
    if day_master not in ten_gods_map:
        return None
    
    # 对于天干，直接查表
    if is_stem and char in ten_gods_map[day_master]:
        return ten_gods_map[day_master][char]
    
    # 对于地支，需要找到藏干的主气来判断（简化处理：使用第一个藏干）
    # 这里简化处理，如果找不到就返回None，使用五行颜色
    return None


def _get_ten_god_color(ten_god: str, element: str) -> tuple:
    """
    根据十神和五行返回颜色。
    正神用柔和颜色，偏神用强烈颜色。
    
    Returns:
        (节点颜色, 边框颜色) 元组
    """
    # 五行基础颜色
    element_base_colors = {
        'wood': {'light': '#66FF99', 'vivid': '#00FF88', 'border': '#00FFAA'},      # 绿色系
        'fire': {'light': '#FF9999', 'vivid': '#FF4444', 'border': '#FF6666'},      # 红色系
        'earth': {'light': '#FFE066', 'vivid': '#FFD700', 'border': '#FFEB3B'},     # 金色系
        'metal': {'light': '#E0E0E0', 'vivid': '#FFFFFF', 'border': '#CCCCCC'},     # 白色系
        'water': {'light': '#66CCFF', 'vivid': '#00AAFF', 'border': '#00CCFF'},     # 蓝色系
    }
    
    base = element_base_colors.get(element.lower(), element_base_colors['earth'])
    
    # 正神：柔和颜色（light），偏神：强烈颜色（vivid）
    is_zheng = ten_god in ['ZhengYin', 'BiJian', 'ShiShen', 'ZhengCai', 'ZhengGuan']
    
    if is_zheng:
        return (base['light'], base['border'])
    else:
        return (base['vivid'], base['border'])


def render_topology_graph(adjacency_matrix: np.ndarray, nodes: List[Dict], 
                         node_energies: List[float], node_labels: List[str] = None,
                         day_master: Optional[str] = None):
    """
    渲染图网络拓扑结构。
    
    Args:
        adjacency_matrix: 邻接矩阵 [N x N]
        nodes: 节点信息列表
        node_energies: 节点的能量值列表
        node_labels: 节点标签列表（可选）
    
    Returns:
        Plotly Figure 对象
    """
    N = len(nodes)
    
    # 数据验证
    if N == 0:
        # 返回空图
        fig = go.Figure()
        fig.add_annotation(text="暂无节点数据", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    if len(node_energies) != N:
        # 如果能量数量不匹配，使用默认值
        node_energies = node_energies[:N] if len(node_energies) > N else node_energies + [0.0] * (N - len(node_energies))
    
    # 创建 NetworkX 图
    G = nx.DiGraph()
    
    # 添加节点
    for i, node in enumerate(nodes):
        node_label = node_labels[i] if node_labels and i < len(node_labels) else f"{node.get('char', f'Node{i}')}"
        G.add_node(i, label=node_label, energy=node_energies[i] if i < len(node_energies) else 0.0, **node)
    
    # 添加边（只添加权重较大的边，避免图过于复杂）
    threshold = 0.1  # 只显示权重绝对值 > 0.1 的边
    
    # 验证邻接矩阵
    if adjacency_matrix is not None and adjacency_matrix.size > 0:
        # 确保矩阵是二维的
        if adjacency_matrix.ndim == 1:
            adjacency_matrix = adjacency_matrix.reshape(int(np.sqrt(len(adjacency_matrix))), -1)
        
        # 确保矩阵大小匹配
        matrix_size = min(adjacency_matrix.shape[0], adjacency_matrix.shape[1], N)
        
        for i in range(matrix_size):
            for j in range(matrix_size):
                try:
                    weight = float(adjacency_matrix[i][j])
                    if abs(weight) > threshold:
                        G.add_edge(j, i, weight=weight)
                except (IndexError, ValueError, TypeError):
                    continue
    
    # 使用分层布局（年 -> 月 -> 日 -> 时）
    # 天干在上，地支在下，按柱排列
    pos = {}
    for i, node in enumerate(nodes):
        # 获取柱索引，默认为 0（如果没有则根据节点ID推断）
        pillar_idx = node.get('pillar_idx', i // 2 if i < 8 else 3)
        # 确保 pillar_idx 在有效范围内 (0-3)
        pillar_idx = max(0, min(3, pillar_idx))
        
        # 节点类型：'branch' 或 'stem'，兼容 'type' 字段
        node_type = node.get('node_type') or node.get('type', 'stem')
        # 天干在上 (y=1)，地支在下 (y=-1)
        node_type_offset = 1.0 if node_type == 'stem' else -1.0
        
        # X坐标：按柱索引排列，每柱间距3个单位
        # Y坐标：天干在上，地支在下
        pos[i] = (pillar_idx * 3, node_type_offset)
    
    # 创建边的轨迹 - 带箭头显示方向
    edge_traces = []
    edge_annotations = []  # 用于存储箭头注释
    
    for edge in G.edges(data=True):
        src_idx, tgt_idx = edge[0], edge[1]
        x0, y0 = pos[src_idx]
        x1, y1 = pos[tgt_idx]
        weight = edge[2].get('weight', 0)
        
        # 计算箭头位置（在目标节点附近，但不重叠）
        dx = x1 - x0
        dy = y1 - y0
        dist = np.sqrt(dx**2 + dy**2)
        
        # 如果距离太短，跳过箭头
        if dist > 0.1:
            # 箭头起点（从源节点边缘）
            # 节点半径大约是节点大小的一半（像素转坐标单位）
            node_size_ratio = 0.15  # 大约的节点半径比例
            arrow_start_x = x0 + (dx / dist) * node_size_ratio
            arrow_start_y = y0 + (dy / dist) * node_size_ratio
            
            # 箭头终点（到目标节点边缘）
            arrow_end_x = x1 - (dx / dist) * node_size_ratio
            arrow_end_y = y1 - (dy / dist) * node_size_ratio
            
            # 根据权重设置颜色和宽度
            if weight > 0:
                edge_color = f'rgba(0, 255, 128, {min(0.8, abs(weight))})'
            else:
                edge_color = f'rgba(255, 100, 50, {min(0.8, abs(weight))})'
            
            edge_width = max(2, abs(weight) * 4)
            
            # 创建边线
            edge_trace = go.Scatter(
                x=[arrow_start_x, arrow_end_x, None], 
                y=[arrow_start_y, arrow_end_y, None],
                line=dict(width=edge_width, color=edge_color),
                hoverinfo='none',
                mode='lines',
                showlegend=False
            )
            edge_traces.append(edge_trace)
            
            # 添加箭头注释（箭头从终点指向源的反方向）
            # 箭头起点（稍微偏移以避免与节点重叠）
            arrow_offset = 0.25
            arrow_start_annot_x = arrow_end_x - (dx / dist) * arrow_offset
            arrow_start_annot_y = arrow_end_y - (dy / dist) * arrow_offset
            
            # 提取RGB颜色（用于箭头）
            if 'rgba' in edge_color:
                # 提取rgb部分
                rgb_part = edge_color.split('(')[1].split(')')[0]
                rgb_vals = rgb_part.split(',')[:3]
                arrow_color = f"rgb({','.join(rgb_vals)})"
            else:
                arrow_color = edge_color
            
            # 添加箭头注释
            edge_annotations.append(dict(
                ax=arrow_start_annot_x,
                ay=arrow_start_annot_y,
                axref='x',
                ayref='y',
                x=arrow_end_x,
                y=arrow_end_y,
                xref='x',
                yref='y',
                showarrow=True,
                arrowhead=2,  # 箭头样式：2表示三角形箭头
                arrowsize=1.5 + abs(weight) * 2,  # 箭头大小
                arrowwidth=max(1, edge_width * 0.6),
                arrowcolor=arrow_color,
                opacity=min(0.9, abs(weight) * 1.2)
            ))
    
    # 如果没有边，创建一个空的边轨迹
    if not edge_traces:
        edge_trace = go.Scatter(x=[], y=[], mode='lines', hoverinfo='none', showlegend=False)
        edge_traces = [edge_trace]
    
    # 创建节点轨迹 - 更大更酷炫
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    node_line_color = []
    node_opacity = []
    
    # 改进的五行颜色（备用，当没有日主时使用）
    element_colors_fallback = {
        'wood': '#00FF88',
        'fire': '#FF4444',
        'earth': '#FFD700',
        'metal': '#FFFFFF',
        'water': '#00AAFF'
    }
    element_border_colors_fallback = {
        'wood': '#00FFAA',
        'fire': '#FF6666',
        'earth': '#FFEB3B',
        'metal': '#CCCCCC',
        'water': '#00CCFF'
    }
    
    for i, node in enumerate(nodes):
        x, y = pos[i]
        node_x.append(x)
        node_y.append(y)
        
        energy = node_energies[i] if i < len(node_energies) else 0.0
        node_label = (node_labels[i] if node_labels and i < len(node_labels) 
                     else node.get('char', f'Node{i}'))
        
        element = node.get('element', 'earth')
        char = node.get('char', '')
        node_type = node.get('node_type') or node.get('type', 'stem')
        is_stem = (node_type == 'stem')
        
        # 尝试根据十神设置颜色
        ten_god = None
        if day_master and char:
            ten_god = _calculate_ten_god(day_master, char, is_stem)
        
        if ten_god:
            node_color_val, node_line_color_val = _get_ten_god_color(ten_god, element)
            node_text.append(f"<b>{node_label}</b><br>能量: {energy:.2f}<br>十神: {ten_god}<br>元素: {element}")
        else:
            # 使用五行颜色
            node_color_val = element_colors_fallback.get(element, '#888888')
            node_line_color_val = element_border_colors_fallback.get(element, '#FFFFFF')
            node_text.append(f"<b>{node_label}</b><br>能量: {energy:.2f}<br>元素: {element}")
        
        node_color.append(node_color_val)
        node_line_color.append(node_line_color_val)
        
        # 节点大小与能量成正比 - 临时存储能量值，后面统一映射
        node_size.append(energy)
        
        # 根据能量设置不透明度（能量越高越亮）
        node_opacity.append(0.7 + min(0.3, energy * 0.1))
    
    # 统一映射节点大小：将能量值线性映射到像素大小范围
    # 找到能量的最小值和最大值
    if node_size and len(node_size) > 0:
        min_energy = min(node_size)
        max_energy = max(node_size)
        energy_range = max_energy - min_energy if max_energy > min_energy else 1.0
        
        # 节点大小范围：最小30像素，最大120像素
        min_size = 30
        max_size = 120
        
        # 线性映射：size = min_size + (energy - min_energy) / energy_range * (max_size - min_size)
        if energy_range > 0:
            node_size = [
                min_size + (energy - min_energy) / energy_range * (max_size - min_size)
                for energy in node_size
            ]
        else:
            # 如果所有能量相同，使用中等大小
            node_size = [(min_size + max_size) / 2] * len(node_size)
    
    # 创建主节点轨迹
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[(node_labels[i] if node_labels and i < len(node_labels) 
               else nodes[i].get('char', f'N{i}')) for i in range(N)],
        textposition="middle center",
        textfont=dict(size=20, color='white', family='Arial Black'),  # 更大更清晰的文字
        hovertext=node_text,
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.8)',
            bordercolor='white',
            font_size=14,
            font_family='Arial'
        ),
        marker=dict(
            size=node_size,
            color=node_color,
            opacity=node_opacity,
            line=dict(
                width=4,  # 更粗的边框
                color=node_line_color
            ),
            # 添加发光效果（通过多个层实现）
        ),
        showlegend=False
    )
    
    # 添加发光层（更大的半透明节点作为光晕效果）- 先添加，这样会在节点下方
    glow_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='skip',
        marker=dict(
            size=[s * 1.8 for s in node_size],  # 发光层更大
            color=node_color,
            opacity=[o * 0.15 for o in node_opacity],  # 非常透明
            line=dict(width=0),
        ),
        showlegend=False
    )
    
    # 创建图表 - 组合所有轨迹（顺序：边 -> 发光层 -> 节点层）
    fig_data = edge_traces + [glow_trace, node_trace]
    
    fig = go.Figure(
        data=fig_data,
        layout=go.Layout(
            title=dict(
                text='⚛️ 图网络拓扑结构 (Graph Network Topology) ⚛️',
                font=dict(size=24, color='#FFFFFF', family='Arial Black'),
                x=0.5,
                xanchor='center'
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=40, l=40, r=40, t=80),
                        annotations=[dict(
                            text="🔵 节点大小 = 能量值 | 颜色 = 十神(正神柔和/偏神鲜艳) | 箭头 = 能量传导方向",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.5, y=-0.05,
                            xanchor="center", yanchor="top",
                            font=dict(color="#AAAAAA", size=13, family='Arial')
                        )] + edge_annotations,  # 添加箭头注释
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-2, 11],
                visible=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-2.5, 2.5],
                visible=False
            ),
            height=700,  # 更大的高度
            plot_bgcolor='rgba(15, 23, 42, 0.95)',  # 深色背景
            paper_bgcolor='rgba(15, 23, 42, 1)',  # 深色纸张背景
        )
    )
    
    return fig


def render_energy_flow_comparison(initial_energy: List[float], final_energy: List[float],
                                  node_labels: List[str]):
    """
    渲染能量流动对比图（初始 vs 最终）。
    
    Args:
        initial_energy: 初始能量向量
        final_energy: 最终能量向量
        node_labels: 节点标签列表
    
    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=node_labels,
        y=initial_energy,
        name='初始能量 (H⁰)',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        x=node_labels,
        y=final_energy,
        name='最终能量 (H^final)',
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='能量流动对比 (Energy Flow Comparison)',
        xaxis_title='节点 (Nodes)',
        yaxis_title='能量 (Energy)',
        barmode='group',
        height=400
    )
    
    return fig


def render_adjacency_heatmap(adjacency_matrix: np.ndarray, node_labels: List[str]):
    """
    渲染邻接矩阵热图。
    
    Args:
        adjacency_matrix: 邻接矩阵 [N x N]
        node_labels: 节点标签列表
    
    Returns:
        Plotly Figure 对象
    """
    fig = px.imshow(
        adjacency_matrix,
        labels=dict(x="目标节点 (Target)", y="源节点 (Source)", color="权重 (Weight)"),
        x=node_labels,
        y=node_labels,
        color_continuous_scale='RdBu',
        color_continuous_midpoint=0,
        aspect="auto",
        title="邻接矩阵 (Adjacency Matrix) - 红色=正权重(生/合), 蓝色=负权重(克/冲)"
    )
    
    fig.update_layout(height=500)
    
    return fig

